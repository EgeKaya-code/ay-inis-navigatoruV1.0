"""Güney kutup stereografik izdüşümü (küre, R = 1737.4 km).

LOLA kutup DEM'leri bu izdüşümdedir: x = rho*sin(lon), y = rho*cos(lon),
rho = 2R*tan(pi/4 + lat/2)  (lat negatif, kutupta rho = 0).
Enlem/boylam derece, gezegen-merkezli, +Doğu.
"""
from __future__ import annotations

import numpy as np

from .config import ay_yaricapi_m


def enlemboylam_xy(lat_deg, lon_deg, R: float | None = None):
    R = ay_yaricapi_m() if R is None else R
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    rho = 2.0 * R * np.tan(np.pi / 4.0 + lat / 2.0)
    return rho * np.sin(lon), rho * np.cos(lon)


def xy_enlemboylam(x, y, R: float | None = None):
    R = ay_yaricapi_m() if R is None else R
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    rho = np.hypot(x, y)
    lat = 2.0 * np.arctan(rho / (2.0 * R)) - np.pi / 2.0
    lon = np.arctan2(x, y)
    return np.degrees(lat), np.degrees(lon)


def birim_vektor(lat_deg, lon_deg):
    """Ay merkezli birim vektör (MOON_ME çerçevesi)."""
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    return np.stack(
        [np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=-1
    )


def yerel_eksenler(lat_deg, lon_deg):
    """Yerel Doğu, Kuzey, Yukarı birim vektörleri (küre üzerinde)."""
    lat = np.radians(lat_deg)
    lon = np.radians(lon_deg)
    dogu = np.array([-np.sin(lon), np.cos(lon), 0.0])
    kuzey = np.array([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)])
    yukari = np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
    return dogu, kuzey, yukari


def harita_yonleri(lon_deg):
    """Harita düzleminde yerel Kuzey ve Doğu birim yönleri.

    Güney kutup izdüşümünde kuzey, kutuptan dışarı doğru radyal yöndür.
    """
    lon = np.radians(lon_deg)
    kuzey = np.array([np.sin(lon), np.cos(lon)])
    dogu = np.array([np.cos(lon), -np.sin(lon)])
    return kuzey, dogu
