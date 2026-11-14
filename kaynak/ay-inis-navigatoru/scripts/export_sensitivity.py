"""What does a landing error cost? Recompute the metrics on rings around each landable point.

    python scripts/export_sensitivity.py --out ../tasarim/veri [--only haworth] [--missing]

For every point that has a cockpit package in candidates.json (the best N_FULL candidates
and the legacy point of each region) the same model as export_candidates.py is run at
points `radii_m` away in `azimuth_count` directions ([landing_error] in assumptions.toml).
Each ring is summarised by its worst and median value per metric and by how many of its
points are steeper than max_slope_deg. Writes sensitivity.json (after every region);
touches nothing else.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from export_candidates import balanced_score, pixel_value, region_dem, regions_to_run, snap_out
from export_proto import CROP_HALF_M, FAR_DEM, GEOJSON, load_ephemeris, site_metrics, site_profile, slug
from lunar_nav.config import load_assumptions
from lunar_nav.dem import DemLayer, read_layer
from lunar_nav.geo import destination, latlon_to_ps
from lunar_nav.sites import neighbourhood_slope_deg

DEM_RES_M = 20.0
KEYS = ("sun_energy_pct", "earth_1deg_pct", "longest_dark_days", "score")
HIGHER_IS_BETTER = {"sun_energy_pct": True, "earth_1deg_pct": True, "longest_dark_days": False, "score": True}


def ring_points(lat: float, lon: float, radius_m: float, count: int) -> list[tuple[float, float, float]]:
    """(azimuth, lat, lon) of `count` points `radius_m` from (lat, lon), starting due north, clockwise."""
    az = np.arange(count) * 360.0 / count
    lat2, lon2 = destination(lat, lon, az, radius_m)
    return [(float(a), float(p), float(q)) for a, p, q in zip(az, lat2, lon2)]


def headline(metrics: dict) -> dict:
    """The three card numbers and the balanced score of one metrics block."""
    return {"sun_energy_pct": metrics["terrain"]["sun_energy_pct"],
            "earth_1deg_pct": metrics["terrain_antenna_1deg"]["earth_pct"],
            "longest_dark_days": metrics["terrain"]["longest_dark_days"],
            "score": balanced_score(metrics)}


def summarise(offsets: list[dict]) -> dict:
    """Worst and median of each metric over the ring, and how many of its points are too steep."""
    out = {"worst": {}, "median": {}, "steep": sum(not o["flat"] for o in offsets), "n": len(offsets)}
    for k in KEYS:
        v = np.array([o[k] for o in offsets])
        out["worst"][k] = float(v.min() if HIGHER_IS_BETTER[k] else v.max())
        out["median"][k] = float(np.median(v))
    return out


def region_sensitivity(feature, region, far, eph, cfg) -> dict:
    sid = region["id"]
    ring = np.array(feature["geometry"]["coordinates"][0])
    px, py = latlon_to_ps(ring[:, 1], ring[:, 0])
    bbox = snap_out((px.min(), py.min(), px.max(), py.max()), DEM_RES_M)
    dem = region_dem(sid, (bbox[0] - CROP_HALF_M, bbox[1] - CROP_HALF_M, bbox[2] + CROP_HALF_M, bbox[3] + CROP_HALF_M))
    slope3 = DemLayer(neighbourhood_slope_deg(dem), dem.left, dem.top, dem.res)
    max_slope = cfg["sites"]["max_slope_deg"]
    h_obs = cfg["horizon"]["observer_heights_m"][0]
    err = cfg["landing_error"]

    points = {}
    for c in region["candidates"]:
        if not c["package"]:
            continue
        rings = []
        for radius in err["radii_m"]:
            offsets = []
            for az, lat, lon in ring_points(c["lat"], c["lon"], radius, err["azimuth_count"]):
                metrics, _ = site_metrics(site_profile(dem, far, lat, lon, h_obs, cfg), eph)
                slope = float(pixel_value(slope3, *latlon_to_ps(lat, lon)))
                offsets.append({"az_deg": az, "lat": lat, "lon": lon, "slope_deg": slope, "flat": slope < max_slope,
                                **headline(metrics)})
            rings.append({"radius_m": radius, "offsets": offsets, **summarise(offsets)})
        points[c["id"]] = {"center": headline(c["metrics"][f"{h_obs:g}m"]), "rings": rings}
        w = [r["worst"] for r in rings]
        print(f"  {c['id']:28s} sun {points[c['id']]['center']['sun_energy_pct']:5.1f} -> "
              + " / ".join(f"{x['sun_energy_pct']:5.1f}" for x in w)
              + f"   earth {points[c['id']]['center']['earth_1deg_pct']:5.1f} -> "
              + " / ".join(f"{x['earth_1deg_pct']:5.1f}" for x in w)
              + f"   dark {points[c['id']]['center']['longest_dark_days']:5.1f} -> "
              + " / ".join(f"{x['longest_dark_days']:5.1f}" for x in w)
              + "   steep " + "/".join(str(r["steep"]) for r in rings), flush=True)
    return points


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--only", default="", help="comma-separated region ids; the rest is kept from sensitivity.json")
    p.add_argument("--missing", action="store_true", help="only regions not in sensitivity.json yet")
    args = p.parse_args()
    only = {s for s in args.only.split(",") if s}

    cfg = load_assumptions()
    features = {slug(f["properties"]["Region"]): f for f in json.loads(GEOJSON.read_text())["features"]}
    cand = json.loads((args.out / "candidates.json").read_text(encoding="utf-8"))
    regions = {r["id"]: r for r in cand["regions"]}
    target = args.out / "sensitivity.json"
    keep = (only or args.missing) and target.exists()
    done = json.loads(target.read_text(encoding="utf-8"))["regions"] if keep else {}
    todo = regions_to_run([sid for sid in features if sid in regions], set(done), only, args.missing)
    if not todo:
        print("nothing to do")
        return

    eph = load_ephemeris(cfg)
    far = read_layer(FAR_DEM, name="far_80m")
    err = cfg["landing_error"]
    for sid in todo:
        t0 = time.perf_counter()
        print(sid, flush=True)
        done[sid] = region_sensitivity(features[sid], regions[sid], far, eph, cfg)
        target.write_text(json.dumps({
            "period": cand["period"],
            "observer_height_m": cand["observer_height_m"],
            "radii_m": err["radii_m"],
            "azimuths_deg": [a for a, _, _ in ring_points(-89.0, 0.0, 1.0, err["azimuth_count"])],
            "note": "same model and metrics as candidates.json, at points displaced from each landable point; "
                    "worst = lowest Sun, lowest Earth (1 deg mask), longest dark, lowest balanced score on the ring; "
                    f"steep = ring points whose 3x3 slope is {cfg['sites']['max_slope_deg']:g} deg or more",
            "regions": {k: done[k] for k in features if k in done},
        }, indent=1), encoding="utf-8")
        print(f"  {sid}: {time.perf_counter() - t0:.0f} s · sensitivity.json has {len(done)}/{len(regions)} regions", flush=True)
    print(f"-> {target}")


if __name__ == "__main__":
    main()
