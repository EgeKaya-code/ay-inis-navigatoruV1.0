"""Bir noktadan Güneş/Dünya'nın görünüp görünmediği ve özet metrikler."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import ay_yaricapi_m, varsayimlar
from .projeksiyon import yerel_eksenler
from .ufuk import ufuk_yuksekligi


def yerel_azimut_yukseklik(lat: float, lon: float, yukseklik_m: float, hedef_km: np.ndarray):
    """Ay merkezli hedef vektörlerinden yerel azimut/yükseklik açısı (derece) ve uzaklık (km)."""
    dogu, kuzey, yukari = yerel_eksenler(lat, lon)
    p = yukari * (ay_yaricapi_m() + yukseklik_m) / 1000.0
    v = hedef_km - p
    uz = np.linalg.norm(v, axis=1)
    el = np.degrees(np.arcsin((v @ yukari) / uz))
    az = np.mod(np.degrees(np.arctan2(v @ dogu, v @ kuzey)), 360.0)
    return az, el, uz


def disk_gorunen_kesir(u: np.ndarray) -> np.ndarray:
    """Merkezi ufkun u yarıçap üstünde olan diskin görünen alan kesri."""
    u = np.clip(u, -1.0, 1.0)
    return 1.0 - (np.arccos(u) - u * np.sqrt(1.0 - u**2)) / np.pi


@dataclass
class Seriler:
    gunes_az: np.ndarray
    gunes_el: np.ndarray
    gunes_ufuk: np.ndarray
    gunes_kesir: np.ndarray  # 0..1 diskin görünen alanı
    dunya_az: np.ndarray
    dunya_el: np.ndarray
    dunya_ufuk: np.ndarray

    @property
    def gunes_var(self):
        return self.gunes_kesir > 0.0

    @property
    def dunya_var(self):
        pay = varsayimlar()["gorunurluk"]["dunya_min_pay_derece"]
        return self.dunya_el > self.dunya_ufuk + pay


def seriler(lat, lon, zemin_m, gozlemci_m, az_profil, ufuk, gunes_km, dunya_km) -> Seriler:
    h = zemin_m + gozlemci_m
    gaz, gel, guz = yerel_azimut_yukseklik(lat, lon, h, gunes_km)
    daz, del_, _ = yerel_azimut_yukseklik(lat, lon, h, dunya_km)
    r_gunes = np.degrees(np.arcsin(varsayimlar()["gunes"]["yaricap_km"] / guz))
    gu = ufuk_yuksekligi(az_profil, ufuk, gaz)
    du = ufuk_yuksekligi(az_profil, ufuk, daz)
    kesir = disk_gorunen_kesir((gel - gu) / r_gunes)
    return Seriler(gaz, gel, gu, kesir, daz, del_, du)


def en_uzun_ardisik(maske: np.ndarray) -> int:
    """True değerlerin en uzun ardışık dizisinin uzunluğu (adım sayısı)."""
    if not maske.any():
        return 0
    m = np.concatenate([[0], maske.astype(np.int8), [0]])
    d = np.diff(m)
    basla = np.flatnonzero(d == 1)
    bitir = np.flatnonzero(d == -1)
    return int((bitir - basla).max())


def ozet(s: Seriler, adim_saat: float = 1.0) -> dict:
    return {
        "gunes_yuzde": round(100.0 * float(s.gunes_var.mean()), 1),
        "enerji_yuzde": round(100.0 * float(s.gunes_kesir.mean()), 1),
        "dunya_yuzde": round(100.0 * float(s.dunya_var.mean()), 1),
        "en_uzun_karanlik_saat": en_uzun_ardisik(~s.gunes_var) * adim_saat,
        "en_uzun_iletisimsiz_saat": en_uzun_ardisik(~s.dunya_var) * adim_saat,
    }
