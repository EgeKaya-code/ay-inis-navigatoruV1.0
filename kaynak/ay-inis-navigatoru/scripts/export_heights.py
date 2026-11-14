"""Horizon profiles at other observer heights (0 m and 10 m) for every package point.

    python scripts/export_heights.py [--heights 0 10]

Writes tasarim/veri/sites/<id>/horizon_<h>m.json in the same format as horizon.json (which is the
2 m profile and is left untouched). DEM: the local copies under <data>/LOLA_DEM (20 m region crops
to 10 km, 80 m DEM from 10 to 300 km), the same layers and distances export_proto.py used.
Before writing anything it recomputes the 2 m profile of each point and checks it against horizon.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import numpy as np

from lunar_nav.horizon import Band, horizon_profile
from lunar_nav.localdata import far_layer, available_heights, available_years, package_points, update_manifest, region_layer

sys.stdout.reconfigure(encoding="utf8")
NEAR_MAX_M = 10000.0  # export_proto.CROP_HALF_M - 500
FAR_MAX_M = 300000.0
STEP_DEG = 0.1


def r1(a, nd):
    return np.round(np.asarray(a, float), nd).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--heights", nargs="*", type=float, default=[0.0, 10.0])
    ap.add_argument("--skip-check", action="store_true")
    args = ap.parse_args()
    far = far_layer()
    pts = package_points()
    near, near_id = None, None
    t0 = time.perf_counter()
    for k, p in enumerate(pts):
        if all((p["dir"] / f"horizon_{h:g}m.json").exists() for h in args.heights):
            continue  # already done (resume after an interruption)
        if p["region_id"] != near_id:
            near, near_id = region_layer(p["region_id"]), p["region_id"]
        bands = [Band(near, 0.0, NEAR_MAX_M), Band(far, NEAR_MAX_M, FAR_MAX_M)]
        if not args.skip_check:
            ref = json.loads((p["dir"] / "horizon.json").read_text())
            again = horizon_profile(p["lat"], p["lon"], bands, ref["observer_height_m"], STEP_DEG)
            d = float(np.abs(again.elevation_deg - np.array(ref["elevation_deg"])).max())
            if d > 0.002:
                raise SystemExit(f"{p['id']}: recomputed 2 m profile differs from horizon.json by {d:.4f} deg; "
                                 "the DEM here is not the one the profiles were made from")
        for h in args.heights:
            prof = horizon_profile(p["lat"], p["lon"], bands, h, STEP_DEG)
            (p["dir"] / f"horizon_{h:g}m.json").write_text(json.dumps({
                "observer_height_m": h, "azimuth_step_deg": STEP_DEG,
                "elevation_deg": r1(prof.elevation_deg, 3), "distance_km": r1(prof.distance_m / 1e3, 2),
            }))
        print(f"{k + 1:2d}/{len(pts)} {p['id']:28s} {time.perf_counter() - t0:6.0f} s", flush=True)

    print("years.json:", update_manifest(observer_heights_m=available_heights())["observer_heights_m"])

if __name__ == "__main__":
    main()
