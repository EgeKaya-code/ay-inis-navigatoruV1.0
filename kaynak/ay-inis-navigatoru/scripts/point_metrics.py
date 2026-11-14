"""Illumination and Earth visibility metrics for the highest flat point near a region anchor.

    python scripts/point_metrics.py --region malapert_massif

Uses the cached 20 m crop around the anchor, so it runs offline once the crop,
the 80 m DEM and the SPICE kernels are on disk.
"""

from __future__ import annotations

import argparse
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lunar_nav.config import DATA_DIR, ROOT, load_assumptions, load_regions
from lunar_nav.dem import near_crop, read_layer
from lunar_nav.geo import latlon_to_ps
from lunar_nav.horizon import Band, horizon_profile
from lunar_nav.sites import highest_flat_point
from lunar_nav.visibility import Ephemeris, build_ephemeris, point_series, summarize

CROP_HALF_M = 10500.0
SEARCH_RADIUS_M = 1000.0


def jd_to_year(jd):
    return 2000.0 + (np.asarray(jd) - 2451545.0) / 365.25


def load_ephemeris(cfg) -> Ephemeris:
    e = cfg["ephemeris"]
    path = DATA_DIR / "cache" / f"ephem_{e['start'][0]}_{e['end'][0]}_{e['step_hours']:g}h.npz"
    if path.exists():
        return Ephemeris.load(path)
    t = time.perf_counter()
    eph = build_ephemeris(tuple(e["start"]), tuple(e["end"]), e["step_hours"])
    eph.save(path)
    print(f"ephemeris: {eph.jd_tt.size} steps in {time.perf_counter() - t:.1f} s -> {path.name}")
    return eph


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--region", default="malapert_massif")
    args = p.parse_args()

    cfg = load_assumptions()
    region = next(r for r in load_regions() if r["id"] == args.region)
    near = near_crop(region["lat"], region["lon"], CROP_HALF_M)
    far = read_layer(DATA_DIR / "raw" / "LDEM_80S_80MPP_ADJ.TIF", name="far_80m")

    ax, ay = latlon_to_ps(region["lat"], region["lon"])
    lat, lon, ground, slope = highest_flat_point(near, ax, ay, SEARCH_RADIUS_M, cfg["sites"]["max_slope_deg"])
    px, py = latlon_to_ps(lat, lon)
    offset = float(np.hypot(px - near.left - CROP_HALF_M, py - near.top + CROP_HALF_M))
    # the 20 m band must stay inside the crop; the 80 m band takes over from there
    split = CROP_HALF_M - offset - 500.0
    print(f"{region['name']}: point ({lat:.4f}, {lon:.4f}), height {ground:.0f} m, slope {slope:.1f} deg, "
          f"{offset:.0f} m from crop centre; 20 m band to {split / 1e3:.1f} km")

    eph = load_ephemeris(cfg)
    margin = cfg["visibility"]["earth_min_margin_deg"]
    years = jd_to_year(eph.jd_tt)
    series = {}
    for h in cfg["horizon"]["observer_heights_m"]:
        prof = horizon_profile(lat, lon, [Band(near, 0.0, split), Band(far, split, 300000.0)], h,
                               cfg["horizon"]["azimuth_step_deg"])
        s = point_series(prof, eph)
        series[h] = s
        m = summarize(s, eph.step_hours, margin)
        print(f"\nobserver {h:g} m, {years[0]:.0f}-{years[-1]:.0f}:")
        print(f"  sunlight (energy-weighted) {m['sun_energy_pct']:5.1f} %   any sunlight {m['sun_any_pct']:5.1f} %")
        print(f"  Earth visible              {m['earth_pct']:5.1f} %   sun AND Earth {m['sun_and_earth_pct']:5.1f} %")
        print(f"  longest darkness {m['longest_dark_days']:.1f} d   longest Earth gap {m['longest_no_earth_days']:.1f} d")
        per_year = [100 * s.sun_fraction[(years >= y) & (years < y + 1)].mean() for y in range(2026, 2031)]
        print("  sunlight by year: " + "  ".join(f"{y}: {v:.0f}%" for y, v in zip(range(2026, 2031), per_year)))

    # one year of the 2 m series, as the dashboard's "strips" will show it
    h0 = cfg["horizon"]["observer_heights_m"][0]
    s = series[h0]
    sel = (years >= 2027) & (years < 2028)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(14, 4), sharex=True)
    a1.fill_between(years[sel], 0, s.sun_fraction[sel], color="#f2a900", step="mid")
    a1.set_ylabel("Sun disk\nvisible")
    a1.set_ylim(0, 1)
    a2.fill_between(years[sel], 0, (s.earth_margin[sel] > margin).astype(float), color="#2d7dd2", step="mid")
    a2.set_ylabel("Earth\nvisible")
    a2.set_yticks([])
    a2.set_xlabel("year")
    a1.set_title(f"{region['name']} ({lat:.3f}, {lon:.3f}), observer {h0:g} m, 2027 — "
                 "PROVISIONAL point (anchor-feature search)")
    out = ROOT / "docs" / "img" / f"strips_{args.region}.png"
    fig.savefig(out, dpi=110, bbox_inches="tight")
    print(f"\n{out}")


if __name__ == "__main__":
    main()
