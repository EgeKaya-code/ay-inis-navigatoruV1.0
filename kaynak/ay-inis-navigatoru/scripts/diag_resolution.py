"""Diagnostic (NOT a correction): does DEM resolution explain the 0 m gap to NASA's AVGVISIB maps?

    python scripts/diag_resolution.py

NASA's maps were computed on LDEM_85S_060M / LDEM_75S_120M (60 m and 120 m grids). Our horizon profiles
use the 20 m DEM for the first 10 km. A surface-level (0 m) observer is very sensitive to the nearest
cells, so the same "0 m" means something different on a 20 m and on a 60 m grid. Here the 20 m crop is
block-averaged to the resolution of the NASA map each point is compared with (aligned to the map's
pixel grid), the 0 m profile is recomputed on it, and the 18.6-year any-part-of-disc averages are
compared with the map again. The app's data is not changed; results go to
docs/validation/avgvisib_resolution_diagnostic.json and are appended to avgvisib_comparison.md.
"""

from __future__ import annotations

import json
import sys
import warnings

import numpy as np

from validate_avgvisib import START, YEARS, any_part, stats

from lunar_nav.config import ROOT
from lunar_nav.dem import DemLayer
from lunar_nav.horizon import Band, horizon_profile
from lunar_nav.localdata import VERI, far_layer, package_points, region_layer, update_manifest
from lunar_nav.spice_ephem import ephemeris_table

sys.stdout.reconfigure(encoding="utf8")


def coarsen(layer: DemLayer, k: int) -> DemLayer:
    """Block-average a 20 m layer by k x k, with block edges on multiples of k * res (the NASA map grid)."""
    res = layer.res * k
    right, bottom = layer.left + layer.height.shape[1] * layer.res, layer.top - layer.height.shape[0] * layer.res
    left, top = np.ceil(layer.left / res) * res, np.floor(layer.top / res) * res
    c0, r0 = int(round((left - layer.left) / layer.res)), int(round((layer.top - top) / layer.res))
    nc, nr = int((right - left) // res), int((top - bottom) // res)
    h = layer.height[r0:r0 + nr * k, c0:c0 + nc * k].reshape(nr, k, nc, k)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return DemLayer(np.nanmean(h, axis=(1, 3)).astype(np.float32), float(left), float(top), float(res), f"near_{res:g}m", layer.crs)


def main():
    vdir = ROOT / "docs" / "validation"
    base = {r["id"]: r for r in json.loads((vdir / "avgvisib_comparison.json").read_text(encoding="utf8"))["points"]}
    eph = ephemeris_table(START, int(round(YEARS * 365.25 * 24)))
    far = far_layer()
    cache, rows = {}, []
    for p in package_points():
        b = base[p["id"]]
        k = 3 if b["nasa_map"] == "85S_060M" else 6
        key = (p["region_id"], k)
        if key not in cache:
            cache = {key: coarsen(region_layer(p["region_id"]), k)}
        near = cache[key]
        prof = horizon_profile(p["lat"], p["lon"], [Band(near, 0.0, 10000.0), Band(far, 10000.0, 300000.0)], 0.0, 0.1)
        s, e, _ = any_part(prof, eph.sun, eph.earth)
        rows.append({"id": p["id"], "nasa_map": b["nasa_map"], "dem_res_m": near.res, "nasa_sun_pct": b["nasa_sun_pct"],
                     "nasa_earth_pct": b["nasa_earth_pct"], "sun_0m_20m_dem": b["sun_0m"], "earth_0m_20m_dem": b["earth_0m"],
                     "sun_0m_coarse_dem": s, "earth_0m_coarse_dem": e})
        print(f"{p['id']:28s} {near.res:4.0f} m  Sun NASA {b['nasa_sun_pct']:5.1f}  20m {b['sun_0m']:5.1f}  coarse {s:5.1f}   "
              f"Earth NASA {b['nasa_earth_pct']:5.1f}  20m {b['earth_0m']:5.1f}  coarse {e:5.1f}", flush=True)
    summary = {
        "sun_0m_20m_dem": stats([r["sun_0m_20m_dem"] - r["nasa_sun_pct"] for r in rows]),
        "sun_0m_coarse_dem": stats([r["sun_0m_coarse_dem"] - r["nasa_sun_pct"] for r in rows]),
        "earth_0m_20m_dem": stats([r["earth_0m_20m_dem"] - r["nasa_earth_pct"] for r in rows]),
        "earth_0m_coarse_dem": stats([r["earth_0m_coarse_dem"] - r["nasa_earth_pct"] for r in rows]),
    }
    (vdir / "avgvisib_resolution_diagnostic.json").write_text(json.dumps({
        "what": "0 m observer; near-field DEM block-averaged from 20 m to the NASA map's resolution (60 m or 120 m); diagnostic only",
        "summary_ours_minus_nasa": summary, "points": rows}, indent=1), encoding="utf8")
    md = (vdir / "avgvisib_comparison.md").read_text(encoding="utf8").split("\n## Tanı: DEM çözünürlüğü")[0].rstrip("\n")
    f = lambda s: f"{s['mean']:+.1f} | {s['mean_abs']:.1f} | {s['max_abs']:.1f}"
    md += "\n\n## Tanı: DEM çözünürlüğü\n\n" \
          "Üreten: `scripts/diag_resolution.py`. Bu bir düzeltme değil, tanıdır; uygulamanın verisi değişmedi. NASA haritaları 60 m ve 120 m " \
          "ızgaralarda hesaplanmıştır; bizim profiller ilk 10 km için 20 m DEM kullanır. Burada 20 m DEM, karşılaştırılan haritanın çözünürlüğüne " \
          "(haritanın piksel ızgarasına hizalı blok ortalamasıyla) indirildi ve 0 m profili onunla yeniden hesaplandı.\n\n" \
          "| 0 m gözlemci | ort. fark | ort. mutlak fark | en büyük mutlak fark |\n|---|---|---|---|\n" \
          f"| Güneş, 20 m DEM | {f(summary['sun_0m_20m_dem'])} |\n| Güneş, harita çözünürlüğünde DEM | {f(summary['sun_0m_coarse_dem'])} |\n" \
          f"| Dünya, 20 m DEM | {f(summary['earth_0m_20m_dem'])} |\n| Dünya, harita çözünürlüğünde DEM | {f(summary['earth_0m_coarse_dem'])} |\n"
    (vdir / "avgvisib_comparison.md").write_text(md, encoding="utf8")
    val = json.loads((VERI / "years.json").read_text(encoding="utf8")).get("validation", {})
    val["sun_0m_map_res"] = {k: round(v, 2) for k, v in summary["sun_0m_coarse_dem"].items()}
    val["earth_0m_map_res"] = {k: round(v, 2) for k, v in summary["earth_0m_coarse_dem"].items()}
    update_manifest(validation=val)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
