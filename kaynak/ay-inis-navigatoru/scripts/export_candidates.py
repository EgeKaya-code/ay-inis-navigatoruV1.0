"""Candidate landing points inside each Artemis III region, instead of one sample point.

    python scripts/export_candidates.py --out ../tasarim/veri [--only haworth,mons_mouton] [--missing]

Two passes per region:
  1. Screen with NASA's maps. Every 20 m DEM pixel inside the USGS polygon whose 3x3
     neighbourhood is flatter than max_slope_deg gets the NASA average Sun and Earth
     visibility (PGDA product 69) of the map pixel it falls in. Score = their mean.
     Keep the best N_SCREEN, no two closer than MIN_SPACING_M.
  2. Run our own model (same metrics as export_proto.py, 2 m observer, 2026-2030) on
     those, rank them by the balanced score the UI uses, and write the full cockpit
     package for the best N_FULL.
The point export_proto.py picked stays in the list, flagged "legacy", with the numbers
already in sites.json. Writes candidates.json (after every region), sites/<region>__c<N>/ and
heat/<region>.png; never touches sites.json, regions.json or sites/<region>/.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

from export_proto import (ANTENNA_MASK_DEG, CROP_HALF_M, FAR_DEM, GEOJSON, earth_illuminated_fraction,
                          load_ephemeris, site_metrics, site_profile, slug, with_retry, write_site_package)
from lunar_nav.config import DATA_DIR, load_assumptions
from lunar_nav.dem import LDEM_20M, DemLayer, read_layer, write_layer
from lunar_nav.geo import latlon_to_ps, ps_to_latlon
from lunar_nav.sites import inside_polygon, neighbourhood_slope_deg, pick_spaced, pixel_centres, slope_deg

N_SCREEN = 20
N_FULL = 5
MIN_SPACING_M = 300.0
DEM_RES_M = 20.0
BLOCK_M = 20480.0  # HTTP reads of the 20 m DEM are split into blocks this size
DARK_CAP_DAYS = 30.0  # same as the UI's balanced score (tasarim/prototip/src/js/20-sim.js)
HEAT_DARK, HEAT_SUN = (10, 12, 13), (255, 178, 30)  # --bg -> --sun
PGDA = DATA_DIR / "raw" / "pgda"
MAPS = [  # finest first; a region uses the first map that contains its whole polygon
    ("85S_060M", PGDA / "AVGVISIB_85S_060M_201608.TIF", PGDA / "AVGVISIB_85S_060M_201608_EARTH.TIF"),
    ("75S_120M", PGDA / "AVGVISIB_75S_120M_201608.TIF", PGDA / "AVGVISIB_75S_120M_201608_EARTH.TIF"),
]


def region_dem(sid: str, bounds) -> DemLayer:
    """20 m DEM over `bounds` (left, bottom, right, top; multiples of the pixel size), cached."""
    left, bottom, right, top = bounds
    path = DATA_DIR / "cache" / f"ldem20_region_{sid}_{int(left)}_{int(bottom)}_{int(right)}_{int(top)}.tif"
    if path.exists():
        return read_layer(path, name="near_20m")
    rows = []
    for y1 in np.arange(top, bottom, -BLOCK_M):
        row = []
        for x0 in np.arange(left, right, BLOCK_M):
            b = (x0, max(y1 - BLOCK_M, bottom), min(x0 + BLOCK_M, right), y1)
            row.append(with_retry(lambda: read_layer(LDEM_20M, b, name="near_20m")))
        rows.append(row)
    first = rows[0][0]
    layer = DemLayer(np.block([[blk.height for blk in row] for row in rows]), first.left, first.top,
                     first.res, "near_20m", first.crs)
    assert np.allclose(layer.bounds, bounds), (layer.bounds, bounds)
    write_layer(layer, path)
    return layer


def sub_layer(layer: DemLayer, values: np.ndarray, bounds) -> DemLayer:
    """`values` (same grid as `layer`) cut to the pixels inside `bounds`."""
    left, bottom, right, top = bounds
    c0, c1 = int(round((left - layer.left) / layer.res)), int(round((right - layer.left) / layer.res))
    r0, r1 = int(round((layer.top - top) / layer.res)), int(round((layer.top - bottom) / layer.res))
    return DemLayer(values[r0:r1, c0:c1], layer.left + c0 * layer.res, layer.top - r0 * layer.res, layer.res)


def read_map(path: Path, bounds) -> DemLayer:
    """The pixels of a PGDA average-visibility map that touch `bounds`, as percent of time
    (DN x scale x 100)."""
    with rasterio.open(path) as ds:
        scale, res = ds.scales[0], ds.res[0]
    layer = read_layer(path, snap_out(bounds, res), name=path.stem)
    layer.height *= scale * 100.0
    return layer


def pixel_value(layer: DemLayer, x, y) -> np.ndarray:
    """Value of the pixel each (x, y) falls in (no interpolation: the map's own number)."""
    col = np.floor((np.asarray(x) - layer.left) / layer.res).astype(int)
    row = np.floor((layer.top - np.asarray(y)) / layer.res).astype(int)
    return layer.height[row, col]


def snap_out(bounds, res):
    left, bottom, right, top = bounds
    return (np.floor(left / res) * res, np.floor(bottom / res) * res,
            np.ceil(right / res) * res, np.ceil(top / res) * res)


def balanced_score(m: dict) -> float:
    dark = 100.0 - min(m["terrain"]["longest_dark_days"], DARK_CAP_DAYS) / DARK_CAP_DAYS * 100.0
    return (m["terrain"]["sun_energy_pct"] + m["terrain_antenna_1deg"]["earth_pct"] + dark) / 3.0


def heat_png(sun: DemLayer, ring_xy, path: Path) -> dict:
    """NASA Sun map inside the polygon as a small RGBA image, dark -> Sun colour over 0-100 %."""
    x, y = pixel_centres(sun)
    v = np.where(inside_polygon(x, y, ring_xy), sun.height, np.nan)
    k = np.clip(np.nan_to_num(v) / 100.0, 0.0, 1.0)[..., None]
    rgb = np.array(HEAT_DARK) * (1.0 - k) + np.array(HEAT_SUN) * k
    alpha = np.where(np.isfinite(v), 255, 0)[..., None]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.concatenate([rgb, alpha], axis=2).round().astype(np.uint8), "RGBA").save(path, optimize=True)
    left, bottom, right, top = sun.bounds
    return {"file": f"heat/{path.name}", "bounds_km": [left / 1e3, bottom / 1e3, right / 1e3, top / 1e3],
            "width": int(v.shape[1]), "height": int(v.shape[0]), "pixel_m": sun.res,
            "scale_pct": [0.0, 100.0], "colors": ["#%02x%02x%02x" % HEAT_DARK, "#%02x%02x%02x" % HEAT_SUN],
            "min_pct": float(np.nanmin(v)), "median_pct": float(np.nanmedian(v)), "max_pct": float(np.nanmax(v))}


def max_abs_diff(a, b) -> float:
    """Largest difference between the numbers of two equally shaped nested dicts."""
    if isinstance(a, dict):
        return max(max_abs_diff(a[k], b[k]) for k in a)
    return abs(a - b)


def region_candidates(feature, legacy, out: Path, far, eph, earth_illum, cfg) -> dict:
    props = feature["properties"]
    name, sid = props["Region"], slug(props["Region"])
    ring = np.array(feature["geometry"]["coordinates"][0])
    px, py = latlon_to_ps(ring[:, 1], ring[:, 0])
    ring_xy = np.c_[px, py]
    bbox = snap_out((px.min(), py.min(), px.max(), py.max()), DEM_RES_M)
    max_slope = cfg["sites"]["max_slope_deg"]
    h_obs = cfg["horizon"]["observer_heights_m"][0]
    t0 = time.perf_counter()

    # 20 m DEM over the polygon plus the margin every horizon and terrain tile needs
    dem = region_dem(sid, (bbox[0] - CROP_HALF_M, bbox[1] - CROP_HALF_M, bbox[2] + CROP_HALF_M, bbox[3] + CROP_HALF_M))
    slope = sub_layer(dem, slope_deg(dem), bbox)
    slope3 = sub_layer(dem, neighbourhood_slope_deg(dem), bbox)
    height = sub_layer(dem, dem.height, bbox)
    x, y = pixel_centres(height)
    inside = inside_polygon(x, y, ring_xy)
    flat = inside & (slope3.height < max_slope) & np.isfinite(height.height)

    for map_name, sun_path, earth_path in MAPS:
        with rasterio.open(sun_path) as ds:
            b = ds.bounds
        if b.left <= bbox[0] and b.bottom <= bbox[1] and b.right >= bbox[2] and b.top >= bbox[3]:
            break
    else:
        raise SystemExit(f"{name}: polygon not on any PGDA map")
    sun_map, earth_map = read_map(sun_path, bbox), read_map(earth_path, bbox)
    xf, yf, hf, sf = x[flat], y[flat], height.height[flat], slope.height[flat]
    nasa_sun, nasa_earth = pixel_value(sun_map, xf, yf), pixel_value(earth_map, xf, yf)
    picked = pick_spaced(xf, yf, (nasa_sun + nasa_earth) / 2.0, N_SCREEN, MIN_SPACING_M, tiebreak=slope3.height[flat])
    print(f"{name}: {int(inside.sum())} px inside, {int(flat.sum())} flat (< {max_slope:g} deg), NASA map {map_name}, "
          f"DEM ready in {time.perf_counter() - t0:.0f} s", flush=True)

    def entry(cx, cy):
        lat, lon = (float(v) for v in ps_to_latlon(cx, cy))
        return {"lat": lat, "lon": lon, "ps_km": [float(cx) / 1e3, float(cy) / 1e3],
                "nasa_sun_pct": float(pixel_value(sun_map, cx, cy)),
                "nasa_earth_pct": float(pixel_value(earth_map, cx, cy))}

    def model(lat, lon):
        prof = site_profile(dem, far, lat, lon, h_obs, cfg)
        metrics, series = site_metrics(prof, eph)
        return prof, series, metrics

    found = []
    for i in picked:
        c = entry(xf[i], yf[i])
        c["nasa_score"] = (c["nasa_sun_pct"] + c["nasa_earth_pct"]) / 2.0
        c["ground_height_m"] = float(hf[i])
        c["slope_deg"] = float(sf[i])
        prof, series, metrics = model(c["lat"], c["lon"])
        c["metrics"] = {f"{h_obs:g}m": metrics}
        c["score"] = balanced_score(metrics)
        found.append((c, prof, series))
        m = metrics
        print(f"  NASA {c['nasa_sun_pct']:5.1f}/{c['nasa_earth_pct']:5.1f}  ours sun {m['terrain']['sun_energy_pct']:5.1f} "
              f"(any {m['terrain']['sun_any_pct']:5.1f})  earth {m['terrain']['earth_pct']:5.1f}/"
              f"{m['terrain_antenna_1deg']['earth_pct']:5.1f}  dark {m['terrain']['longest_dark_days']:5.1f} d  "
              f"score {c['score']:5.1f}", flush=True)

    found.sort(key=lambda f: -f[0]["score"])
    candidates = []
    for rank, (c, prof, series) in enumerate(found, start=1):
        cid = f"{sid}__c{rank}"
        package = None
        if rank <= N_FULL:
            package = f"sites/{cid}"
            write_site_package(out / "sites" / cid, prof, series, dem, c["ground_height_m"], eph, earth_illum, cfg)
        candidates.append({"id": cid, "rank": rank, "legacy": False, "package": package, **c})

    # the point export_proto.py picked: keep it, with the numbers the old demo shows
    _, _, again = model(legacy["lat"], legacy["lon"])
    lx, ly = latlon_to_ps(legacy["lat"], legacy["lon"])
    old = entry(lx, ly)
    old.update({"lat": legacy["lat"], "lon": legacy["lon"], "ps_km": legacy["ps_km"]})
    old["nasa_score"] = (old["nasa_sun_pct"] + old["nasa_earth_pct"]) / 2.0
    key = f"{h_obs:g}m"
    candidates.append({"id": sid, "rank": None, "legacy": True, "package": f"sites/{sid}", **old,
                       "ground_height_m": legacy["ground_height_m"], "slope_deg": legacy["slope_deg"],
                       "metrics": {key: legacy["metrics"][key]}, "score": balanced_score(legacy["metrics"][key])})
    drift = max_abs_diff(legacy["metrics"][key], again)
    print(f"  legacy point recomputed from the region DEM: max |diff| to sites.json = {drift:.2e}", flush=True)

    return {"id": sid, "region": name, "nasa_map": map_name,
            "pixels_inside": int(inside.sum()), "pixels_flat": int(flat.sum()),
            "legacy_recompute_max_abs_diff": drift,
            "heat": heat_png(sun_map, ring_xy, out / "heat" / f"{sid}.png"),
            "candidates": candidates}


def document(regions: list, sites_json: dict, cfg: dict) -> dict:
    return {
        "period": sites_json["period"],
        "observer_height_m": cfg["horizon"]["observer_heights_m"][0],
        "rule": {
            "screen": f"20 m DEM pixels inside the USGS polygon with 3x3 slope < {cfg['sites']['max_slope_deg']:g} deg; "
                      f"score = mean of NASA average Sun and Earth visibility; best {N_SCREEN} at least "
                      f"{MIN_SPACING_M:g} m apart",
            "rank": "our model, balanced score = (sun_energy_pct + earth_pct with "
                    f"{ANTENNA_MASK_DEG:g} deg mask + dark score) / 3, dark score = 100 - min(longest_dark_days, "
                    f"{DARK_CAP_DAYS:g}) / {DARK_CAP_DAYS:g} * 100",
            "full_package": f"best {N_FULL} by rank, plus the legacy point",
            "legacy": sites_json["site_rule"],
            "n_screen": N_SCREEN, "n_full": N_FULL, "min_spacing_m": MIN_SPACING_M,
            "max_slope_deg": cfg["sites"]["max_slope_deg"],
        },
        "nasa": {
            "product": "NASA PGDA product 69, LOLA average visibility maps AVGVISIB_*_201608 (Mazarico et al. 2011)",
            "metric": "percent of time any part of the solar (Earth) disc clears the terrain, over ~18.6 years",
            "maps": {name: [sun.name, earth.name] for name, sun, earth in MAPS},
        },
        "regions": regions,
    }


def regions_to_run(order: list[str], done: set[str], only: set[str], missing: bool) -> list[str]:
    """Which regions this run computes. --only names them; --missing takes those not in
    candidates.json yet; with neither, all of them."""
    if only:
        return [sid for sid in order if sid in only]
    return [sid for sid in order if not (missing and sid in done)]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--only", default="", help="comma-separated region ids; the rest is kept from candidates.json")
    p.add_argument("--missing", action="store_true", help="only regions not in candidates.json yet (resume a stopped run)")
    args = p.parse_args()
    out = args.out
    only = {s for s in args.only.split(",") if s}

    cfg = load_assumptions()
    features = {slug(f["properties"]["Region"]): f for f in json.loads(GEOJSON.read_text())["features"]}
    sites_json = json.loads((out / "sites.json").read_text(encoding="utf-8"))
    legacy = {s["id"]: s for s in sites_json["sites"]}
    target = out / "candidates.json"
    keep = (only or args.missing) and target.exists()
    done = {r["id"]: r for r in json.loads(target.read_text(encoding="utf-8"))["regions"]} if keep else {}
    todo = regions_to_run(list(features), set(done), only, args.missing)
    if not todo:
        print("nothing to do")
        return

    eph = load_ephemeris(cfg)
    earth_illum = earth_illuminated_fraction(eph)
    far = read_layer(FAR_DEM, name="far_80m")
    for sid in todo:
        t0 = time.perf_counter()
        done[sid] = region_candidates(features[sid], legacy[sid], out, far, eph, earth_illum, cfg)
        # written after every region, so a stopped run loses one region at most
        regions = [done[k] for k in features if k in done]
        target.write_text(json.dumps(document(regions, sites_json, cfg), indent=1), encoding="utf-8")
        print(f"  {sid}: {time.perf_counter() - t0:.0f} s · candidates.json has {len(regions)}/{len(features)} regions", flush=True)
    print(f"-> {target}")


if __name__ == "__main__":
    main()
