"""Compute and plot the horizon profile of one point, and time it.

    python scripts/horizon_point.py --lat -85.98 --lon -1.67 --name "Mons Malapert"
"""

from __future__ import annotations

import argparse
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lunar_nav.config import DATA_DIR, ROOT, load_assumptions
from lunar_nav.dem import near_crop, read_layer
from lunar_nav.horizon import Band, horizon_profile


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--name", default="")
    p.add_argument("--height", type=float, default=2.0, help="observer height above ground, m")
    args = p.parse_args()

    cfg = load_assumptions()
    near_cfg, far_cfg = cfg["horizon"]["layers"]

    t = time.perf_counter()
    near = near_crop(args.lat, args.lon, near_cfg["max_dist_m"] + 500.0)
    far = read_layer(DATA_DIR / "raw" / "LDEM_80S_80MPP_ADJ.TIF", name="far_80m")
    t_load = time.perf_counter() - t

    bands = [Band(near, near_cfg["min_dist_m"], near_cfg["max_dist_m"]),
             Band(far, far_cfg["min_dist_m"], far_cfg["max_dist_m"])]
    t = time.perf_counter()
    prof = horizon_profile(args.lat, args.lon, bands, args.height, cfg["horizon"]["azimuth_step_deg"])
    t_prof = time.perf_counter() - t

    print(f"ground height {prof.ground_height_m:.1f} m; load {t_load:.1f} s; profile {t_prof:.2f} s")
    print(f"horizon elevation: min {prof.elevation_deg.min():.2f}, max {prof.elevation_deg.max():.2f}, "
          f"mean {prof.elevation_deg.mean():.2f} deg")
    i = int(np.argmax(prof.elevation_deg))
    print(f"highest horizon at az {prof.azimuth_deg[i]:.1f} deg, {prof.distance_m[i]:.0f} m away")
    far_share = np.mean(prof.distance_m > near_cfg["max_dist_m"])
    print(f"share of azimuths whose horizon is set by terrain beyond {near_cfg['max_dist_m'] / 1e3:.0f} km: "
          f"{far_share:.0%}")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 6), sharex=True, height_ratios=[3, 1])
    a1.fill_between(prof.azimuth_deg, -5, prof.elevation_deg, color="#555")
    a1.axhline(0, color="k", lw=0.5)
    a1.set_ylim(-2, max(4, prof.elevation_deg.max() + 0.5))
    a1.set_ylabel("horizon elevation (deg)")
    a1.set_title(f"Horizon at {args.name or ''} ({args.lat:.3f}, {args.lon:.3f}), observer {args.height:g} m")
    a2.semilogy(prof.azimuth_deg, prof.distance_m / 1e3, ".", ms=1)
    a2.set_ylabel("distance (km)")
    a2.set_xlabel("azimuth (deg from north; 180 = towards the pole)")
    a2.set_xlim(0, 360)
    out = ROOT / "docs" / "img" / f"horizon_{args.lat:.2f}_{args.lon:.2f}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
