"""Artemis III aday bölgeleri (USGS poligonları) ve bölge içi ızgara."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .projeksiyon import enlemboylam_xy, xy_enlemboylam

# Bölge adı -> kısa kimlik. NASA duyurusu (28 Ekim 2024) sırasıyla.
BOLGE_KIMLIK = {
    "Peak Near Cabeus B": "peak_near_cabeus_b",
    "Haworth": "haworth",
    "Malapert Massif": "malapert_massif",
    "Mons Mouton Plateau": "mons_mouton_plateau",
    "Mons Mouton": "mons_mouton",
    "Nobile Rim 1": "nobile_rim_1",
    "Nobile Rim 2": "nobile_rim_2",
    "de Gerlache Rim 2": "de_gerlache_rim_2",
    "Slater Plain": "slater_plain",
}


def _ad_bul(ozellik: dict) -> str:
    """GeoJSON özelliklerinden bölge adını bulur (alan adı kaynağa göre değişebilir)."""
    hedef = {k.lower().replace(" ", ""): k for k in BOLGE_KIMLIK}
    for v in ozellik.values():
        if isinstance(v, str):
            anahtar = v.lower().replace(" ", "").replace("_", "")
            for h, ad in hedef.items():
                if anahtar == h.replace("_", ""):
                    return ad
    raise KeyError(f"Bölge adı bulunamadı: {ozellik}")


def _halkalar(geom: dict) -> list[np.ndarray]:
    if geom["type"] == "Polygon":
        return [np.asarray(geom["coordinates"][0], float)]
    if geom["type"] == "MultiPolygon":
        return [np.asarray(p[0], float) for p in geom["coordinates"]]
    raise ValueError(geom["type"])


def bolgeleri_oku(yol: Path) -> list[dict]:
    veri = json.loads(Path(yol).read_text(encoding="utf-8"))
    sonuc = []
    for f in veri["features"]:
        ad = _ad_bul(f["properties"])
        halkalar = _halkalar(f["geometry"])  # (lon, lat) dizileri
        xy = [np.column_stack(enlemboylam_xy(h[:, 1], h[:, 0])) for h in halkalar]
        alan = sum(_alan(p) for p in xy)
        merkez = _agirlik_merkezi(max(xy, key=_alan))
        mlat, mlon = xy_enlemboylam(*merkez)
        sonuc.append(
            {
                "id": BOLGE_KIMLIK[ad],
                "ad": ad,
                "halkalar_lonlat": [h.tolist() for h in halkalar],
                "halkalar_xy": xy,
                "alan_km2": round(alan / 1e6, 1),
                "merkez_lat": float(mlat),
                "merkez_lon": float(mlon),
            }
        )
    sira = list(BOLGE_KIMLIK.values())
    return sorted(sonuc, key=lambda b: sira.index(b["id"]))


def _alan(p: np.ndarray) -> float:
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _agirlik_merkezi(p: np.ndarray) -> tuple[float, float]:
    x, y = p[:, 0], p[:, 1]
    c = x * np.roll(y, -1) - np.roll(x, -1) * y
    a = c.sum() / 2
    return float(((x + np.roll(x, -1)) * c).sum() / (6 * a)), float(((y + np.roll(y, -1)) * c).sum() / (6 * a))


def icinde_mi(px: np.ndarray, py: np.ndarray, halka: np.ndarray) -> np.ndarray:
    """Işın atma ile çokgen içi testi (harita koordinatlarında)."""
    x, y = halka[:, 0], halka[:, 1]
    x2, y2 = np.roll(x, -1), np.roll(y, -1)
    ic = np.zeros(px.shape, bool)
    for a, b, c, d in zip(x, y, x2, y2):
        kes = ((b > py) != (d > py)) & (px < (c - a) * (py - b) / (d - b + 1e-12) + a)
        ic ^= kes
    return ic


def izgara(bolge: dict, aralik_m: float, en_cok: int = 1000) -> tuple[np.ndarray, np.ndarray]:
    """Bölge içinde düzenli ızgara (x, y). Çok büyük bölgelerde aralık büyütülür."""
    aralik = max(aralik_m, float(np.sqrt(bolge["alan_km2"] * 1e6 / en_cok)))
    tum = np.vstack(bolge["halkalar_xy"])
    xs = np.arange(tum[:, 0].min(), tum[:, 0].max(), aralik) + aralik / 2
    ys = np.arange(tum[:, 1].min(), tum[:, 1].max(), aralik) + aralik / 2
    X, Y = np.meshgrid(xs, ys)
    X, Y = X.ravel(), Y.ravel()
    ic = np.zeros(X.shape, bool)
    for h in bolge["halkalar_xy"]:
        ic |= icinde_mi(X, Y, h)
    return X[ic], Y[ic]
