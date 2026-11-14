"""Compare our Sun/Earth visibility with NASA's LOLA average-visibility maps, under matching conditions.

    python scripts/validate_avgvisib.py

NASA maps (PDS IMG + LBL in the local data folder; Mazarico et al. 2011): fraction of time steps in
which ANY part of the solar (or Earth) disc is visible, averaged over ~18.6 years, for an observer
on the surface (0 m). 60 m/pixel map south of 85 S, 120 m/pixel map north of it.

Ours: the same measure (any part of the disc above the terrain horizon), hourly, over 18.6 years
starting 2026-01-01 (the NASA labels do not state the map's start date), DE440 SPICE geometry, and
each point's 0 m horizon profile (horizon_0m.json, from the same LOLA DEM). The 2 m profile
(horizon.json, what the app shows) is reported in a separate column: it is NOT the map's condition.
Nothing is "corrected" to close a gap.

Writes docs/validation/avgvisib_comparison.{json,md} and the validation block of tasarim/veri/years.json.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

from spice_check import profile_of

from lunar_nav.config import ROOT
from lunar_nav.ephemeris import SUN_RADIUS_M, alt_az
from lunar_nav.geo import latlon_to_ps
from lunar_nav.localdata import DATA, VERI, package_points
from lunar_nav.spice_ephem import ephemeris_table

sys.stdout.reconfigure(encoding="utf8")
EARTH_RADIUS_M = 6_378_137.0
YEARS = 18.6
START = "2026-01-01T00:00:00"
MAPS = {"85S_060M": "AVGVISIB_85S_060M_201608", "75S_120M": "AVGVISIB_75S_120M_201608"}


class PdsMap:
    """A PDS3 polar-stereographic IMG read through its LBL (pixel registration, 16-bit LSB integers)."""

    def __init__(self, stem: str):
        lbl = (DATA / f"{stem}.LBL").read_text()

        def num(key):
            return float(re.search(rf"^\s*{key}\s*=\s*([-+0-9.eE]+)", lbl, re.M).group(1))

        self.lines, self.samples = int(num("LINES")), int(num("LINE_SAMPLES"))
        assert int(num("SAMPLE_BITS")) == 16 and "LSB_INTEGER" in lbl, stem
        self.scale, self.offset = num("SCALING_FACTOR"), num("OFFSET")
        self.res = num("MAP_SCALE")  # m/pixel
        self.l0, self.s0 = num("LINE_PROJECTION_OFFSET"), num("SAMPLE_PROJECTION_OFFSET")
        assert "POLAR STEREOGRAPHIC" in lbl and num("CENTER_LATITUDE") == -90 and num("A_AXIS_RADIUS") == 1737.4
        self.dn = np.memmap(DATA / f"{stem}.IMG", dtype="<i2", mode="r", shape=(self.lines, self.samples))

    def value_pct(self, lat, lon) -> float:
        """Map value (percent) of the pixel containing (lat, lon). Sample 1 is the west edge, line 1 the north (+y) edge;
        pixel (line, sample) is centred at x = (sample - S0 - 1) * res, y = (L0 + 1 - line) * res."""
        x, y = latlon_to_ps(lat, lon)
        col = int(np.floor(x / self.res + self.s0 + 0.5))
        row = int(np.floor(self.l0 + 0.5 - y / self.res))
        if not (0 <= row < self.lines and 0 <= col < self.samples):
            return float("nan")
        return 100.0 * (float(self.dn[row, col]) * self.scale + self.offset)


def any_part(prof, sun, earth):
    """Percent of steps with any part of the solar / Earth disc above the terrain horizon, plus Earth-centre percent."""
    h = prof.ground_height_m + prof.observer_height_m
    s_alt, s_az = alt_az(prof.lat, prof.lon, h, sun)
    e_alt, e_az = alt_az(prof.lat, prof.lon, h, earth)
    s_r = np.degrees(np.arcsin(SUN_RADIUS_M / np.linalg.norm(sun, axis=1)))
    e_r = np.degrees(np.arcsin(EARTH_RADIUS_M / np.linalg.norm(earth, axis=1)))
    s_m = s_alt - prof.elevation_at(s_az)
    e_m = e_alt - prof.elevation_at(e_az)
    return 100 * float(np.mean(s_m > -s_r)), 100 * float(np.mean(e_m > -e_r)), 100 * float(np.mean(e_m > 0))


def stats(d):
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    return {"mean": float(d.mean()), "mean_abs": float(np.abs(d).mean()), "max_abs": float(np.abs(d).max()), "n": int(d.size)}


def main():
    n = int(round(YEARS * 365.25 * 24))
    print(f"ephemeris: {n} hourly steps from {START} ...", flush=True)
    eph = ephemeris_table(START, n)
    maps = {k: (PdsMap(v), PdsMap(v + "_EARTH")) for k, v in MAPS.items()}
    cand = {c["id"]: c for r in json.loads((VERI / "candidates.json").read_text(encoding="utf8"))["regions"] for c in r["candidates"]}

    rows = []
    for p in package_points():
        key = "85S_060M" if p["lat"] < -85.0 else "75S_120M"
        sun_map, earth_map = maps[key]
        nasa_sun, nasa_earth = sun_map.value_pct(p["lat"], p["lon"]), earth_map.value_pct(p["lat"], p["lon"])
        row = {"id": p["id"], "region": p["region"], "point": "sample" if p["legacy"] else f"candidate {p['rank']}",
               "lat": p["lat"], "lon": p["lon"], "nasa_map": key, "nasa_sun_pct": nasa_sun, "nasa_earth_pct": nasa_earth}
        for name, tag in (("horizon_0m.json", "0m"), ("horizon.json", "2m")):
            prof = profile_of(p, name)
            assert prof.observer_height_m == float(tag[:-1]), (p["id"], name)
            s, e, ec = any_part(prof, eph.sun, eph.earth)
            row[f"sun_{tag}"], row[f"earth_{tag}"], row[f"earth_centre_{tag}"] = s, e, ec
        rows.append(row)
        print(f"{p['id']:28s} {key}  Sun NASA {nasa_sun:5.1f}  0m {row['sun_0m']:5.1f}  2m {row['sun_2m']:5.1f}   "
              f"Earth NASA {nasa_earth:5.1f}  0m {row['earth_0m']:5.1f}  2m {row['earth_2m']:5.1f}", flush=True)

    # reader check: candidates.json holds the same map values, read earlier from NASA's GeoTIFF edition by
    # region (a region north of 85 S used the 120 m map throughout). Compare where the same map was used.
    chk = [abs(r["nasa_sun_pct"] - cand[r["id"]]["nasa_sun_pct"]) for r in rows
           if r["nasa_map"] == next(x["nasa_map"] for x in json.loads((VERI / "candidates.json").read_text(encoding="utf8"))["regions"]
                                    if any(c["id"] == r["id"] for c in x["candidates"]))]
    reader = {"points_same_map": len(chk), "max_abs_diff_vs_candidates_json": float(max(chk)) if chk else None}
    print("IMG reader vs candidates.json (same map):", reader)

    summary = {
        "sun_0m": stats([r["sun_0m"] - r["nasa_sun_pct"] for r in rows]),
        "sun_2m": stats([r["sun_2m"] - r["nasa_sun_pct"] for r in rows]),
        "earth_0m": stats([r["earth_0m"] - r["nasa_earth_pct"] for r in rows]),
        "earth_2m": stats([r["earth_2m"] - r["nasa_earth_pct"] for r in rows]),
    }
    period = f"{START[:10]} + {YEARS} years, hourly"
    out = {
        "reference": "NASA PGDA product 69, AVGVISIB_85S_060M_201608 / AVGVISIB_75S_120M_201608 (+ _EARTH), Mazarico et al. 2011; "
                     "0 m observer, ~18.6-year average, any part of the disc",
        "ours": {"period": period, "n_steps": n, "ephemeris": "NAIF SPICE DE440, MOON_ME, light-time corrected",
                 "measure": "percent of steps with any part of the disc above the terrain horizon",
                 "horizons": "horizon_0m.json (matching condition) and horizon.json (2 m, shown in the app)",
                 "dem": "LOLA LDEM_80S_20MPP_ADJ crops (to 10 km) + LDEM_80S_80MPP_ADJ (10-300 km), Barker et al. 2023"},
        "map_rule": "60 m map for points south of 85 S, 120 m map for points north of it",
        "img_reader_check": reader, "summary_ours_minus_nasa": summary, "points": rows,
    }
    vdir = ROOT / "docs" / "validation"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "avgvisib_comparison.json").write_text(json.dumps(out, indent=1), encoding="utf8")

    f1 = lambda v: f"{v:.1f}"
    sg = lambda v: f"{v:+.1f}"
    md = ["# NASA AVGVISIB haritalarıyla karşılaştırma", "",
          f"Üreten: `scripts/validate_avgvisib.py`. Dönem (bizim): {period} ({n} adım). Ölçü: diskin **herhangi bir kısmının** "
          "arazi ufkunun üstünde olduğu zaman yüzdesi (NASA haritasının tanımı).", "",
          "NASA haritası 0 m gözlemci içindir. **0 m** sütunu gözlemci yüksekliği bakımından eşleşen koşuldur (arazi verisinin çözünürlüğü haritadan ince: aşağıdaki tanıya bakın); **2 m** sütunu uygulamanın gösterdiği profildir ve "
          "haritanın koşulu değildir. Fark = bizim − NASA (puan). Hiçbir düzeltme uygulanmadı.", "",
          "## Özet (54 nokta)", "", "| | ort. fark | ort. mutlak fark | en büyük mutlak fark |", "|---|---|---|---|"]
    for k, lab in (("sun_0m", "Güneş, 0 m (eşleşen koşul)"), ("sun_2m", "Güneş, 2 m"), ("earth_0m", "Dünya, 0 m (eşleşen koşul)"), ("earth_2m", "Dünya, 2 m")):
        s = summary[k]
        md.append(f"| {lab} | {sg(s['mean'])} | {f1(s['mean_abs'])} | {f1(s['max_abs'])} |")
    md += ["", "## Güneş (%)", "", "| Nokta | Harita | NASA | Bizim 0 m | Fark 0 m | Bizim 2 m | Fark 2 m |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['region']} · {r['point']} | {r['nasa_map']} | {f1(r['nasa_sun_pct'])} | {f1(r['sun_0m'])} | {sg(r['sun_0m'] - r['nasa_sun_pct'])} | "
                  f"{f1(r['sun_2m'])} | {sg(r['sun_2m'] - r['nasa_sun_pct'])} |")
    md += ["", "## Dünya (%)", "", "Uygulamadaki Dünya rakamı disk **merkezine** göredir; NASA haritası diskin herhangi bir kısmına göre. "
           "Karşılaştırma sütunları haritanın ölçüsüyle hesaplandı; merkez ölçüsü ayrıca verildi.", "",
           "| Nokta | Harita | NASA | Bizim 0 m | Fark 0 m | Bizim 2 m | Fark 2 m | Merkez, 2 m |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['region']} · {r['point']} | {r['nasa_map']} | {f1(r['nasa_earth_pct'])} | {f1(r['earth_0m'])} | {sg(r['earth_0m'] - r['nasa_earth_pct'])} | "
                  f"{f1(r['earth_2m'])} | {sg(r['earth_2m'] - r['nasa_earth_pct'])} | {f1(r['earth_centre_2m'])} |")
    md += ["", f"IMG okuyucu denetimi: aynı haritanın kullanıldığı {reader['points_same_map']} noktada `candidates.json` içindeki "
           f"NASA değerleriyle en büyük fark {reader['max_abs_diff_vs_candidates_json']:.4f} puan.", ""]
    (vdir / "avgvisib_comparison.md").write_text("\n".join(md), encoding="utf8")

    yj = VERI / "years.json"
    y = json.loads(yj.read_text(encoding="utf8")) if yj.exists() else {}
    y["validation"] = {"n": len(rows), "period": "2026–2044", **{k: {a: round(b, 2) for a, b in v.items()} for k, v in summary.items()}}
    yj.write_text(json.dumps(y, ensure_ascii=False, indent=1) + "\n", encoding="utf8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
