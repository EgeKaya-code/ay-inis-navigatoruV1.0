"""Step 1 of the DE440/SPICE migration: regenerate one year of Sun/Earth geometry for package points
with spiceypy and compare it with the series the prototype already ships (skyfield + DE421).

    python scripts/spice_check.py [--year 2027] [--points malapert_massif haworth__c1 ...]

Prints the largest absolute differences. Stored series are rounded (angles 3 decimals, azimuths 2),
so differences below ~0.005 deg in azimuth and ~0.0005 deg in elevation are rounding.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from lunar_nav.horizon import HorizonProfile
from lunar_nav.localdata import package_points
from lunar_nav.spice_ephem import year_table
from lunar_nav.visibility import point_series

sys.stdout.reconfigure(encoding="utf8")


def profile_of(p: dict, name: str = "horizon.json") -> HorizonProfile:
    hz = json.loads((p["dir"] / name).read_text())
    az = np.arange(len(hz["elevation_deg"])) * hz["azimuth_step_deg"]
    return HorizonProfile(p["lat"], p["lon"], hz["observer_height_m"], p["ground_height_m"], az,
                          np.array(hz["elevation_deg"]), np.array(hz["distance_km"]) * 1e3)


def wrap(d):
    return (np.asarray(d) + 180.0) % 360.0 - 180.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2027)
    ap.add_argument("--points", nargs="*", default=["malapert_massif"])
    args = ap.parse_args()
    eph = year_table(args.year)
    pts = {p["id"]: p for p in package_points()}
    ids = list(pts) if args.points == ["all"] else args.points
    worst = {}
    for pid in ids:
        p = pts[pid]
        old = json.loads((p["dir"] / f"series_{args.year}.json").read_text())
        s = point_series(profile_of(p), eph)
        d = {
            "sun_alt_deg": np.abs(s.sun_alt - old["sun_alt_deg"]).max(),
            "sun_az_deg": np.abs(wrap(s.sun_az - old["sun_az_deg"])).max(),
            "sun_az_on_sky_deg": np.abs(wrap(s.sun_az - old["sun_az_deg"]) * np.cos(np.radians(s.sun_alt))).max(),
            "earth_alt_deg": np.abs(s.earth_alt - old["earth_alt_deg"]).max(),
            "earth_az_deg": np.abs(wrap(s.earth_az - old["earth_az_deg"])).max(),
            "earth_margin_deg": np.abs(s.earth_margin - old["earth_margin_deg"]).max(),
            "sun_visible_fraction": np.abs(s.sun_fraction - old["sun_visible_fraction"]).max(),
            "sun_state_flips_h": int(np.sum((s.sun_fraction > 0) != (np.array(old["sun_visible_fraction"]) > 0))),
            "earth_state_flips_h": int(np.sum((s.earth_margin > 0) != (np.array(old["earth_margin_deg"]) > 0))),
        }
        for k, v in d.items():
            worst[k] = max(worst.get(k, 0), v)
        if len(ids) <= 6:
            print(pid, {k: (round(float(v), 5) if not isinstance(v, int) else v) for k, v in d.items()})
    print(f"WORST over {len(ids)} point(s), {args.year}, n={len(eph.jd_tt)}:")
    for k, v in worst.items():
        print(f"  {k:24s} {v:.5f}" if not isinstance(v, int) else f"  {k:24s} {v}")


if __name__ == "__main__":
    main()
