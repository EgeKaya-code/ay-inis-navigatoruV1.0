"""Güneş ve Dünya'nın Ay merkezine göre konumları (MOON_ME çerçevesi, km).

NAIF SPICE kernel'leri spiceypy ile okunur. MOON_ME, LOLA DEM'lerinin çerçevesidir.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from .config import ham_veri_klasoru, varsayimlar

def kernelleri_yukle(klasor: Path | None = None) -> None:
    import spiceypy as sp

    k = (klasor or ham_veri_klasoru()) / "kernels"
    sp.kclear()
    for ad in varsayimlar()["efemeris"]["kerneller"]:
        sp.furnsh(str(k / ad))


def saatlik_zamanlar(baslangic: str | None = None, bitis: str | None = None, adim_saat: float | None = None):
    e = varsayimlar()["efemeris"]
    b = datetime.fromisoformat(baslangic or e["baslangic"]).replace(tzinfo=timezone.utc)
    s = datetime.fromisoformat(bitis or e["bitis"]).replace(tzinfo=timezone.utc)
    adim = timedelta(hours=adim_saat or e["adim_saat"])
    n = int((s - b) / adim)
    return [b + i * adim for i in range(n)]


def konumlar(zamanlar) -> tuple[np.ndarray, np.ndarray]:
    """(gunes_km[n,3], dunya_km[n,3]) – Ay merkezinden, MOON_ME çerçevesinde."""
    import spiceypy as sp

    e = varsayimlar()["efemeris"]
    et = np.array([sp.str2et(z.strftime("%Y-%m-%dT%H:%M:%S")) for z in zamanlar])
    gunes, _ = sp.spkpos("SUN", et, e["cerceve"], e["duzeltme"], "MOON")
    dunya, _ = sp.spkpos("EARTH", et, e["cerceve"], e["duzeltme"], "MOON")
    return np.asarray(gunes), np.asarray(dunya)
