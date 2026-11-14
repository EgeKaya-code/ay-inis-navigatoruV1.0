"""Compare our Sun and Earth visibility with NASA's LOLA average illumination maps.

    python scripts/validate_pgda.py --sites ../tasarim/veri/sites.json

Reference: PGDA product 69 (Mazarico et al. 2011, 2016 update), AVGVISIB_*_201608.
Each pixel is the fraction of hourly timesteps over one lunar nutation cycle
(~18.6 years) in which ANY part of the solar (or Earth) disc clears the terrain.
So the matching metrics are:
  Sun:   sun_any_pct (not the energy-weighted one)
  Earth: any part of the Earth disc above the terrain, i.e. margin > -earth radius
We compute ours over the same length of time (18.6 years) and at 0 m and 2 m,
and read the NASA map at the site pixel and its 3x3 neighbourhood.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio

from lunar_nav.config import DATA_DIR, ROOT, load_assumptions
from lunar_nav.dem import near_crop, read_layer
from lunar_nav.geo import latlon_to_ps
from lunar_nav.horizon import Band, horizon_profile
from lunar_nav.visibility import Ephemeris, build_ephemeris, point_series

CROP_HALF_M = 10500.0
EARTH_RADIUS_M = 6_371_000.0
NUTATION_START, NUTATION_END = (2026, 1, 1), (2044, 8, 1)  # ~18.6 years, DE421 is valid to 2050
PGDA = DATA_DIR / "raw" / "pgda"
MAPS = [  # finest first; a site uses the first map that contains it
    ("85S_060M", PGDA / "AVGVISIB_85S_060M_201608.TIF", PGDA / "AVGVISIB_85S_060M_201608_EARTH.TIF"),
    ("75S_120M", PGDA / "AVGVISIB_75S_120M_201608.TIF", PGDA / "AVGVISIB_75S_120M_201608_EARTH.TIF"),
]


def nutation_ephemeris() -> Ephemeris:
    path = DATA_DIR / "cache" / "ephem_2026_2044-08_1h.npz"
    if path.exists():
        return Ephemeris.load(path)
    eph = build_ephemeris(NUTATION_START, NUTATION_END, 1.0)
    eph.save(path)
    return eph


def sample_map(path: Path, x: float, y: float) -> tuple[float, float, float] | None:
    """(pixel, 3x3 min, 3x3 max) in percent, or None if the point is off the map."""
    with rasterio.open(path) as ds:
        b = ds.bounds
        if not (b.left < x < b.right and b.bottom < y < b.top):
            return None
        row, col = ds.index(x, y)
        win = ds.read(1, window=((row - 1, row + 2), (col - 1, col + 2))).astype(float)
        win[win == ds.nodata] = np.nan
        win *= ds.scales[0] * 100.0
        return float(win[1, 1]), float(np.nanmin(win)), float(np.nanmax(win))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sites", type=Path, required=True)
    p.add_argument("--out", type=Path, default=ROOT / "docs" / "validation")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    cfg = load_assumptions()
    sites = json.loads(args.sites.read_text(encoding="utf-8"))["sites"]
    eph = nutation_ephemeris()
    earth_r = np.degrees(np.arcsin(EARTH_RADIUS_M / np.linalg.norm(eph.earth, axis=1)))
    far = read_layer(DATA_DIR / "raw" / "LDEM_80S_80MPP_ADJ.TIF", name="far_80m")

    rows = []
    for s in sites:
        t = time.perf_counter()
        x, y = latlon_to_ps(s["lat"], s["lon"])
        for name, sun_map, earth_map in MAPS:
            nasa_sun = sample_map(sun_map, x, y)
            if nasa_sun is not None:
                nasa_earth = sample_map(earth_map, x, y)
                break
        else:
            raise SystemExit(f"{s['id']}: not on any PGDA map")

        near = near_crop(s["lat"], s["lon"], CROP_HALF_M)
        ours = {}
        for h in (0.0, 2.0):
            prof = horizon_profile(s["lat"], s["lon"], [Band(near, 0.0, CROP_HALF_M - 500.0),
                                                        Band(far, CROP_HALF_M - 500.0, 300000.0)],
                                   h, cfg["horizon"]["azimuth_step_deg"])
            ps = point_series(prof, eph)
            ours[f"{h:g}m"] = {
                "sun_any_pct": 100.0 * float(np.mean(ps.sun_fraction > 0.0)),
                "earth_any_pct": 100.0 * float(np.mean(ps.earth_margin > -earth_r)),
            }
        row = {"id": s["id"], "region": s["region"], "lat": s["lat"], "lon": s["lon"], "nasa_map": name,
               "nasa_sun_pct": nasa_sun, "nasa_earth_pct": nasa_earth, "ours": ours}
        rows.append(row)
        o = ours["0m"]
        print(f"{s['region']:<22} sun  ours {o['sun_any_pct']:5.1f}  NASA {nasa_sun[0]:5.1f} "
              f"[{nasa_sun[1]:5.1f}-{nasa_sun[2]:5.1f}]   earth ours {o['earth_any_pct']:5.1f}  "
              f"NASA {nasa_earth[0]:5.1f} [{nasa_earth[1]:5.1f}-{nasa_earth[2]:5.1f}]  ({name}, "
              f"{time.perf_counter() - t:.0f} s)")

    sun_d = np.array([r["ours"]["0m"]["sun_any_pct"] - r["nasa_sun_pct"][0] for r in rows])
    earth_d = np.array([r["ours"]["0m"]["earth_any_pct"] - r["nasa_earth_pct"][0] for r in rows])
    summary = {
        "period_ours": f"{NUTATION_START} to {NUTATION_END} UTC, hourly (~18.6 years)",
        "reference": "PGDA product 69, AVGVISIB_*_201608 (Mazarico et al. 2011)",
        "metric": "fraction of time any part of the disc clears the terrain, percent",
        "sun_diff_0m": {"mean": float(sun_d.mean()), "mean_abs": float(np.abs(sun_d).mean()),
                        "max_abs": float(np.abs(sun_d).max())},
        "earth_diff_0m": {"mean": float(earth_d.mean()), "mean_abs": float(np.abs(earth_d).mean()),
                          "max_abs": float(np.abs(earth_d).max())},
        "sites": rows,
    }
    (args.out / "pgda_comparison.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False),
                                                   encoding="utf-8")
    print(f"\nSun   ours-NASA (0 m): mean {sun_d.mean():+.1f}, mean |d| {np.abs(sun_d).mean():.1f}, "
          f"max |d| {np.abs(sun_d).max():.1f} points")
    print(f"Earth ours-NASA (0 m): mean {earth_d.mean():+.1f}, mean |d| {np.abs(earth_d).mean():.1f}, "
          f"max |d| {np.abs(earth_d).max():.1f} points")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, key, nkey, title in ((axes[0], "sun_any_pct", "nasa_sun_pct", "Sun visible (any part), %"),
                                 (axes[1], "earth_any_pct", "nasa_earth_pct", "Earth visible (any part), %")):
        nasa = np.array([r[nkey][0] for r in rows])
        lo = np.array([r[nkey][1] for r in rows])
        hi = np.array([r[nkey][2] for r in rows])
        ours0 = np.array([r["ours"]["0m"][key] for r in rows])
        ours2 = np.array([r["ours"]["2m"][key] for r in rows])
        ax.plot([0, 100], [0, 100], color="0.7", lw=1)
        ax.errorbar(nasa, ours0, xerr=[nasa - lo, hi - nasa], fmt="o", color="C0", capsize=3,
                    label="ours, 0 m (bar: NASA 3x3 pixel range)")
        ax.plot(nasa, ours2, "^", color="C1", ms=5, label="ours, 2 m")
        for r, xv, yv in zip(rows, nasa, ours0):
            ax.annotate(r["region"], (xv, yv), fontsize=7, xytext=(4, -3), textcoords="offset points")
        ax.set(xlabel="NASA PGDA map", ylabel="ours (LOLA 20/80 m horizon + SPICE)", title=title)
        ax.legend(fontsize=8, loc="upper left")
        ax.set_aspect("equal")
        m0 = min(nasa.min(), ours0.min()) - 5
        ax.set_xlim(max(0, m0), 100)
        ax.set_ylim(max(0, m0), 100)
    fig.tight_layout()
    fig.savefig(args.out / "pgda_comparison.png", dpi=150)
    print(f"-> {args.out / 'pgda_comparison.png'}")


if __name__ == "__main__":
    main()
