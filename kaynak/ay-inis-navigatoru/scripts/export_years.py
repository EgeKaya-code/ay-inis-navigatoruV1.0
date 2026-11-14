"""More years of hourly Sun/Earth geometry for every package point, from the DE440 SPICE kernels.

    python scripts/export_years.py --years 2026 2028

Writes series_<year>.json and events_<year>.json next to the existing 2027 files, in the same format
(export_proto.write_site_package), using each point's existing horizon.json (2 m observer).
Run scripts/spice_check.py first: it shows the SPICE/DE440 geometry reproduces the 2027 files.
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from export_proto import earth_illuminated_fraction, events, r1
from spice_check import profile_of

from lunar_nav.localdata import available_heights, available_years, package_points, update_manifest
from lunar_nav.spice_ephem import year_table
from lunar_nav.visibility import point_series

sys.stdout.reconfigure(encoding="utf8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    args = ap.parse_args()
    pts = package_points()
    for year in args.years:
        eph = year_table(year)
        illum = earth_illuminated_fraction(eph)
        for p in pts:
            prof = profile_of(p)
            s = point_series(prof, eph)
            (p["dir"] / f"series_{year}.json").write_text(json.dumps({
                "start_utc": f"{year}-01-01T00:00:00Z", "step_hours": eph.step_hours,
                "observer_height_m": prof.observer_height_m,
                "ephemeris": "NAIF SPICE DE440, MOON_ME (= MOON_ME_DE440_ME421), light-time corrected",
                "sun_alt_deg": r1(s.sun_alt, 3), "sun_az_deg": r1(s.sun_az, 2),
                "sun_visible_fraction": r1(s.sun_fraction, 3),
                "earth_alt_deg": r1(s.earth_alt, 3), "earth_az_deg": r1(s.earth_az, 2),
                "earth_margin_deg": r1(s.earth_margin, 3), "earth_illuminated_fraction": r1(illum, 3),
            }))
            (p["dir"] / f"events_{year}.json").write_text(json.dumps(events(s.sun_fraction, s.earth_margin), indent=0))
        print(f"{year}: {len(eph.jd_tt)} hours x {len(pts)} points written", flush=True)

    print("years.json:", update_manifest(years=available_years())["years"])

if __name__ == "__main__":
    main()
