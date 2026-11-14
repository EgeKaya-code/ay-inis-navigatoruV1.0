"""Arazi ufku: bir noktadan her azimutta arazinin yaptığı en büyük yükseklik açısı.

Yöntem: gözlemciden her azimut yönünde harita düzleminde ışın atılır, ışın boyunca
yükseklik çift-doğrusal örneklenir. Her örnek için Ay küresinin eğriliği hesaba
katılarak yükseklik açısı bulunur:

    açı = atan2(r_t*cos(θ) - r_o, r_t*sin(θ))

r_o = R + h_gözlemci, r_t = R + h_örnek, θ = iki nokta arasındaki merkez açı.
Ufuk = ışın boyunca en büyük açı. Azimut kuzeyden saat yönünde (Kuzey=0, Doğu=90).
"""
from __future__ import annotations

import numpy as np

from .config import ay_yaricapi_m, varsayimlar
from .dem import DEM
from .projeksiyon import birim_vektor, enlemboylam_xy, harita_yonleri, xy_enlemboylam


def isin_mesafeleri(piksel_m: float) -> np.ndarray:
    u = varsayimlar()["ufuk"]
    yakin = np.arange(piksel_m, u["yakin_alan_m"], piksel_m)
    n = int(np.ceil(np.log(u["uzak_alan_m"] / u["yakin_alan_m"]) / np.log(u["uzak_alan_oran"])))
    uzak = u["yakin_alan_m"] * u["uzak_alan_oran"] ** np.arange(n + 1)
    return np.concatenate([yakin, uzak])


def ufuk_profili(
    dem: DEM,
    lat: float,
    lon: float,
    gozlemci_m: float = 2.0,
    adim_derece: float = 0.25,
    mesafeler: np.ndarray | None = None,
    mesafe_dondur: bool = False,
):
    """(azimutlar_derece, ufuk_yukseklik_derece) döndürür.

    mesafe_dondur=True ise üçüncü değer olarak ufku oluşturan arazinin uzaklığı (km) da döner.
    """
    R = ay_yaricapi_m()
    az = np.arange(0.0, 360.0, adim_derece)
    d = isin_mesafeleri(dem.piksel) if mesafeler is None else mesafeler

    x0, y0 = enlemboylam_xy(lat, lon)
    h0 = float(dem.ornekle(np.array([x0]), np.array([y0]))[0])
    r_o = R + h0 + gozlemci_m

    kuzey, dogu = harita_yonleri(lon)
    a = np.radians(az)[:, None]
    yon_x = kuzey[0] * np.cos(a) + dogu[0] * np.sin(a)
    yon_y = kuzey[1] * np.cos(a) + dogu[1] * np.sin(a)
    xs = x0 + yon_x * d[None, :]
    ys = y0 + yon_y * d[None, :]

    h = dem.ornekle(xs, ys)
    la, lo = xy_enlemboylam(xs, ys)
    u_o = birim_vektor(lat, lon)
    u_t = birim_vektor(la, lo)
    cos_t = np.clip(u_t @ u_o, -1.0, 1.0)
    sin_t = np.sqrt(1.0 - cos_t**2)
    r_t = R + h
    aci = np.degrees(np.arctan2(r_t * cos_t - r_o, r_t * sin_t))
    aci = np.where(np.isnan(aci), -90.0, aci)
    if mesafe_dondur:
        i = aci.argmax(axis=1)
        return az, aci[np.arange(len(az)), i], d[i] / 1000.0
    return az, aci.max(axis=1)


def ufuk_yuksekligi(az_profil: np.ndarray, ufuk: np.ndarray, az_sorgu) -> np.ndarray:
    """Profili verilen azimutlarda doğrusal (dairesel) aradeğerler."""
    adim = az_profil[1] - az_profil[0]
    i = np.mod(np.asarray(az_sorgu), 360.0) / adim
    i0 = np.floor(i).astype(int) % len(ufuk)
    i1 = (i0 + 1) % len(ufuk)
    f = i - np.floor(i)
    return ufuk[i0] * (1 - f) + ufuk[i1] * f
