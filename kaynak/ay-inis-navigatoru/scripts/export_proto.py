"""Export real data for the UI prototype: regions, per-site metrics, 3D terrain tiles,
horizon profiles, one year of hourly Sun/Earth geometry and an event list.

    python scripts/export_proto.py --out ../tasarim/veri

One site per region: the highest flat point within SEARCH_RADIUS_M of the centroid of
the official USGS region polygon (McClernan 2024). Needs the USGS GeoJSON in
data/raw/usgs_regions/ and internet for the 20 m DEM crops (cached afterwards).
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
import rasterio
from matplotlib.path import Path as MplPath
from PIL import Image

from lunar_nav.config import DATA_DIR, load_assumptions
from lunar_nav.dem import near_crop, read_layer
from lunar_nav.geo import R_MOON, latlon_to_ps, ps_to_latlon
from lunar_nav.horizon import Band, horizon_profile
from lunar_nav.sites import highest_flat_point
from lunar_nav.visibility import Ephemeris, point_series, summarize

GEOJSON = DATA_DIR / "raw" / "usgs_regions" / "A3_9regions-lonlat-simplified.geojson"
FAR_DEM = DATA_DIR / "raw" / "LDEM_80S_80MPP_ADJ.TIF"
CROP_HALF_M = 10500.0
SEARCH_RADIUS_M = 6000.0  # stays inside every polygon (inscribed radius >= 8 km)
TILE_HALF_M = 10000.0
TILE_RES_M = 40.0
SERIES_YEAR = 2027  # ephemeris starts 2026-01-01 00:00 UTC, hourly
ANTENNA_MASK_DEG = 1.0


def slug(name: str) -> str:
    return name.lower().replace("'", "").replace(" ", "_")


def load_ephemeris(cfg) -> Ephemeris:
    e = cfg["ephemeris"]
    return Ephemeris.load(DATA_DIR / "cache" / f"ephem_{e['start'][0]}_{e['end'][0]}_{e['step_hours']:g}h.npz")


def earth_illuminated_fraction(eph: Ephemeris) -> np.ndarray:
    """Lit fraction of Earth's disk seen from the Moon (phase)."""
    to_sun = eph.sun - eph.earth
    to_moon = -eph.earth
    c = np.sum(to_sun * to_moon, axis=1) / (np.linalg.norm(to_sun, axis=1) * np.linalg.norm(to_moon, axis=1))
    return (1.0 + c) / 2.0


def local_tile(layer, lat, lon, ground_h):
    """Heights on a local east/north grid centred on the site, relative to the site's
    ground and lowered by the sphere's curvature, so the scene can be a flat plane with
    z = local up. Row 0 is the north edge, column 0 the west edge."""
    x0, y0 = latlon_to_ps(lat, lon)
    lam = np.radians(lon)
    north = np.array([np.sin(lam), np.cos(lam)])  # away from the pole
    east = np.array([np.cos(lam), -np.sin(lam)])
    n = int(round(2 * TILE_HALF_M / TILE_RES_M)) + 1
    s = np.linspace(-TILE_HALF_M, TILE_HALF_M, n)
    e, nn = np.meshgrid(s, s[::-1])
    x = x0 + e * east[0] + nn * north[0]
    y = y0 + e * east[1] + nn * north[1]
    h = layer.sample(x, y) - ground_h - (e ** 2 + nn ** 2) / (2.0 * R_MOON)
    return h.astype(np.float32), n


def events(sun_frac, earth_margin, start_hour=0):
    """State changes of sunlight and Earth line of sight, with the length of each new state."""
    out = []
    for kind, on in (("sun", sun_frac > 0.0), ("earth", earth_margin > 0.0),
                     ("earth_1deg", earth_margin > ANTENNA_MASK_DEG)):
        edges = np.flatnonzero(np.diff(on.astype(np.int8))) + 1
        bounds = np.concatenate([[0], edges, [on.size]])
        for a, b in zip(bounds[:-1], bounds[1:]):
            if a == 0:
                continue  # state already running at the start of the year
            out.append({"hour": int(a + start_hour), "type": f"{kind}_{'on' if on[a] else 'off'}",
                        "duration_h": int(b - a), "runs_past_year_end": bool(b == on.size)})
    return sorted(out, key=lambda ev: ev["hour"])


def polar_map(out: Path, size: int = 1024) -> dict:
    """Hillshade of the whole 80 m DEM (to 80 S) for the 2D map background."""
    with rasterio.open(FAR_DEM) as ds:
        h = ds.read(1, out_shape=(size, size)).astype(np.float32)
        b = ds.bounds
    res = (b.right - b.left) / size
    gy, gx = np.gradient(h, res)
    az, alt = np.radians(315.0), np.radians(30.0)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    shade = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    img = np.clip(shade * 255, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(out / "polar_map.png", optimize=True)
    return {"file": "polar_map.png", "bounds_km": [b.left / 1e3, b.bottom / 1e3, b.right / 1e3, b.top / 1e3],
            "note": "south polar stereographic, x right, y up, pole at (0, 0); image row 0 = top (max y)"}


def with_retry(read, tries=4):
    """The 20 m DEM is read over HTTP; PGDA occasionally returns a short read."""
    for i in range(tries):
        try:
            return read()
        except rasterio.errors.RasterioIOError:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def crop_with_retry(lat, lon):
    return with_retry(lambda: near_crop(lat, lon, CROP_HALF_M))


def r1(a, nd=2):
    return np.round(np.asarray(a, float), nd).tolist()


def site_profile(near, far, lat, lon, h_obs, cfg):
    """Horizon profile from a 20 m layer that covers CROP_HALF_M around the point, plus the far DEM."""
    return horizon_profile(lat, lon, [Band(near, 0.0, CROP_HALF_M - 500.0),
                                      Band(far, CROP_HALF_M - 500.0, 300000.0)],
                           h_obs, cfg["horizon"]["azimuth_step_deg"])


def site_metrics(prof, eph):
    """The summary block of one observer height, and the time series it came from."""
    s = point_series(prof, eph)
    flat = point_series(replace(prof, elevation_deg=np.zeros_like(prof.elevation_deg)), eph)
    step = eph.step_hours
    return {
        "terrain": summarize(s, step, 0.0),
        "terrain_antenna_1deg": summarize(s, step, ANTENNA_MASK_DEG),
        "flat_horizon": summarize(flat, step, 0.0),
        "min_earth_margin_deg": float(s.earth_margin.max() if (s.earth_margin <= 0).all()
                                      else s.earth_margin[s.earth_margin > 0].min()),
    }, s


def series_year_slice(eph) -> slice:
    i0 = int((SERIES_YEAR - 2026) * 365 * 24 / eph.step_hours)  # 2026 is not a leap year
    return slice(i0, i0 + int(365 * 24 / eph.step_hours))


def write_site_package(site_dir: Path, prof, s, near, ground, eph, earth_illum, cfg):
    """Everything the cockpit loads for one point: horizon, one year of series, events, terrain tile."""
    site_dir.mkdir(parents=True, exist_ok=True)
    sl = series_year_slice(eph)
    (site_dir / "horizon.json").write_text(json.dumps({
        "observer_height_m": prof.observer_height_m, "azimuth_step_deg": cfg["horizon"]["azimuth_step_deg"],
        "elevation_deg": r1(prof.elevation_deg, 3), "distance_km": r1(prof.distance_m / 1e3, 2),
    }))
    (site_dir / "series_2027.json").write_text(json.dumps({
        "start_utc": f"{SERIES_YEAR}-01-01T00:00:00Z", "step_hours": eph.step_hours,
        "observer_height_m": prof.observer_height_m,
        "sun_alt_deg": r1(s.sun_alt[sl], 3), "sun_az_deg": r1(s.sun_az[sl], 2),
        "sun_visible_fraction": r1(s.sun_fraction[sl], 3),
        "earth_alt_deg": r1(s.earth_alt[sl], 3), "earth_az_deg": r1(s.earth_az[sl], 2),
        "earth_margin_deg": r1(s.earth_margin[sl], 3), "earth_illuminated_fraction": r1(earth_illum[sl], 3),
    }))
    (site_dir / "events_2027.json").write_text(json.dumps(
        events(s.sun_fraction[sl], s.earth_margin[sl]), indent=0))
    tile, n = local_tile(near, prof.lat, prof.lon, ground)
    tile.tofile(site_dir / "terrain.bin")
    (site_dir / "terrain.json").write_text(json.dumps({
        "file": "terrain.bin", "dtype": "float32 little-endian", "width": n, "height": n,
        "spacing_m": TILE_RES_M, "half_size_m": TILE_HALF_M,
        "layout": "row-major; row 0 = north edge, column 0 = west edge; site at the centre",
        "z": "metres relative to the site's ground, curvature included (local up)",
        "min_m": float(np.nanmin(tile)), "max_m": float(np.nanmax(tile)),
    }))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    out = args.out
    (out / "sites").mkdir(parents=True, exist_ok=True)

    cfg = load_assumptions()
    eph = load_ephemeris(cfg)
    earth_illum = earth_illuminated_fraction(eph)
    far = read_layer(FAR_DEM, name="far_80m")
    gj = json.loads(GEOJSON.read_text())

    regions, sites = [], []
    for f in gj["features"]:
        props = f["properties"]
        name, sid = props["Region"], slug(props["Region"])
        ring = np.array(f["geometry"]["coordinates"][0])
        px, py = latlon_to_ps(ring[:, 1], ring[:, 0])
        cx, cy = px[:-1].mean(), py[:-1].mean()
        clat, clon = ps_to_latlon(cx, cy)

        crop = crop_with_retry(float(clat), float(clon))
        lat, lon, ground, slope = highest_flat_point(crop, cx, cy, SEARCH_RADIUS_M, cfg["sites"]["max_slope_deg"])
        assert MplPath(np.c_[px, py]).contains_point(latlon_to_ps(lat, lon)), name
        near = crop_with_retry(lat, lon)  # centred on the site for the horizon and the tile
        ground = float(near.sample(*latlon_to_ps(lat, lon)))

        metrics = {}
        profiles = {}
        for h_obs in cfg["horizon"]["observer_heights_m"]:
            prof = site_profile(near, far, lat, lon, h_obs, cfg)
            metrics[f"{h_obs:g}m"], s = site_metrics(prof, eph)
            profiles[h_obs] = (prof, s)

        prof, s = profiles[cfg["horizon"]["observer_heights_m"][0]]
        write_site_package(out / "sites" / sid, prof, s, near, ground, eph, earth_illum, cfg)

        regions.append({"id": sid, "name": name, "code": props["RegionCode"], "area_km2": props["Area_km2"],
                        "polygon_lonlat": ring.tolist(),
                        "polygon_ps_km": np.round(np.c_[px, py] / 1e3, 3).tolist(),
                        "centroid": {"lat": float(clat), "lon": float(clon)}})
        sx, sy = latlon_to_ps(lat, lon)
        note = None
        if props["Area_km2"] > (2 * CROP_HALF_M / 1e3) ** 2:
            note = (f"Region is {props['Area_km2']:.0f} km2 but only the central "
                    f"{2 * CROP_HALF_M / 1e3:.0f}x{2 * CROP_HALF_M / 1e3:.0f} km was searched; "
                    "the point may not represent the region's best ground.")
        sites.append({"id": sid, "region": name, "lat": lat, "lon": lon, "ps_km": [sx / 1e3, sy / 1e3],
                      "ground_height_m": ground, "slope_deg": slope, "search_note": note, "metrics": metrics})
        m = metrics["2m"]
        print(f"{name:20s} ({lat:.3f}, {lon:.3f}) {ground:5.0f} m  sun {m['terrain']['sun_energy_pct']:4.1f}% "
              f"earth {m['terrain']['earth_pct']:5.1f}% / {m['terrain_antenna_1deg']['earth_pct']:5.1f}% (1 deg)  "
              f"flat {m['flat_horizon']['sun_energy_pct']:4.1f}/{m['flat_horizon']['earth_pct']:4.1f}  "
              f"dark {m['terrain']['longest_dark_days']:.1f} d")

    (out / "regions.json").write_text(json.dumps({"map": polar_map(out), "regions": regions}, indent=1))
    (out / "sites.json").write_text(json.dumps({
        "period": "2026-01-01 to 2030-12-31 UTC, hourly",
        "site_rule": f"highest point with slope < {cfg['sites']['max_slope_deg']:g} deg (3x3) within "
                     f"{SEARCH_RADIUS_M / 1e3:g} km of the USGS region polygon centroid",
        "metric_notes": {
            "sun_energy_pct": "time-averaged visible fraction of the solar disk",
            "sun_any_pct": "time with any part of the Sun above the terrain",
            "earth_pct": "time Earth's centre is above the terrain (+ mask)",
            "longest_dark_days": "longest spell with no part of the Sun visible",
            "flat_horizon": "same Sun/Earth geometry, horizon assumed flat (0 deg)",
        },
        "sites": sites,
    }, indent=1))


if __name__ == "__main__":
    main()
