"""Varsayımlar dosyasını okur (config/varsayimlar.toml)."""
from __future__ import annotations

import os
import tomllib
from functools import lru_cache
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def varsayimlar() -> dict:
    with open(PROJE_KOKU / "config" / "varsayimlar.toml", "rb") as f:
        return tomllib.load(f)


def ham_veri_klasoru() -> Path:
    """Ham NASA verilerinin klasörü (AYNAV_VERI ortam değişkeni ile değiştirilebilir)."""
    return Path(os.environ.get("AYNAV_VERI", PROJE_KOKU / "data" / "raw"))


def islenmis_klasoru() -> Path:
    p = PROJE_KOKU / "data" / "islenmis"
    p.mkdir(parents=True, exist_ok=True)
    return p


def ay_yaricapi_m() -> float:
    return float(varsayimlar()["ay"]["yaricap_m"])
