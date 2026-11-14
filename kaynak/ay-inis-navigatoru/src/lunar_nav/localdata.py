"""The local raw-data folder: the only source of raw inputs for new computations.

Holds the DE440 SPICE kernels, the NASA AVGVISIB maps (PDS IMG + LBL) and, under
LOLA_DEM/, the LOLA DEM files the horizon profiles were made from (the whole 80 m
DEM and one 20 m crop per region: polygon bounding box plus a 10.5 km margin).
Override the location with the LUNAR_NAV_DATA environment variable.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .dem import DemLayer, read_layer

DATA = Path(os.environ.get("LUNAR_NAV_DATA", r"C:\Users\Ege\Desktop\Nasa_Space APP_Veri"))
DEM_DIR = DATA / "LOLA_DEM"
FAR_DEM = DEM_DIR / "LDEM_80S_80MPP_ADJ.TIF"
# the prototype's data folder (tasarim/veri), next to this repository
VERI = Path(os.environ.get("LUNAR_NAV_VERI", Path(__file__).resolve().parents[3] / "tasarim" / "veri"))


def far_layer() -> DemLayer:
    return read_layer(FAR_DEM, name="far_80m")


def region_layer(region_id: str) -> DemLayer:
    """The 20 m crop of one region (covers every package point plus the horizon margin)."""
    # the id is followed by the four bounds; "mons_mouton" must not match "mons_mouton_plateau"
    pat = re.compile(rf"ldem20_region_{re.escape(region_id)}(_-?\d+){{4}}\.tif$")
    hits = sorted(f for f in DEM_DIR.glob("ldem20_region_*.tif") if pat.match(f.name))
    if len(hits) != 1:
        raise FileNotFoundError(f"expected one 20 m crop for {region_id} in {DEM_DIR}, found {len(hits)}")
    return read_layer(hits[0], name="near_20m")


def package_points() -> list[dict]:
    """Every point that has a full data package (horizon + series + terrain) in the prototype."""
    cand = json.loads((VERI / "candidates.json").read_text(encoding="utf8"))
    out = []
    for r in cand["regions"]:
        for c in r["candidates"]:
            if c["package"]:
                out.append({"id": c["id"], "region_id": r["id"], "region": r["region"], "legacy": c["legacy"],
                            "rank": c["rank"], "lat": c["lat"], "lon": c["lon"],
                            "ground_height_m": c["ground_height_m"], "nasa_map": r["nasa_map"],
                            "dir": VERI / c["package"]})
    return out


def update_manifest(**fields) -> dict:
    """years.json: what the web app may load (years with series, observer heights with horizon profiles, validation)."""
    path = VERI / "years.json"
    doc = json.loads(path.read_text(encoding="utf8")) if path.exists() else {}
    doc.update(fields)
    doc.setdefault("years", [2027])
    doc.setdefault("observer_heights_m", [2])
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + chr(10), encoding="utf8")
    return doc


def available_years() -> list[int]:
    """Years for which every package point has a series file."""
    pts = package_points()
    years = sorted(int(f.stem.split("_")[1]) for f in pts[0]["dir"].glob("series_*.json"))
    return [y for y in years if all((p["dir"] / f"series_{y}.json").exists() for p in pts)]


def available_heights() -> list[float]:
    """Observer heights for which every package point has a horizon profile (2 m is horizon.json)."""
    pts = package_points()
    hs = {2.0} | {float(f.stem.split("_")[1][:-1]) for f in pts[0]["dir"].glob("horizon_*m.json")}
    ok = [h for h in sorted(hs) if h == 2.0 or all((p["dir"] / f"horizon_{h:g}m.json").exists() for p in pts)]
    return [int(h) if h == int(h) else h for h in ok]
