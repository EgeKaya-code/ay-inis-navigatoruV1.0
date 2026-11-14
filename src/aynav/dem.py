"""LOLA yükseklik haritasını (GeoTIFF) belleğe alır ve çift-doğrusal örnekler."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates


@dataclass
class DEM:
    yukseklik: np.ndarray  # metre, float32, satır = y azalır
    x0: float  # sol kenar (piksel köşesi)
    y0: float  # üst kenar (piksel köşesi)
    piksel: float  # metre/piksel

    @classmethod
    def oku(cls, yol: Path, kucult: int = 1) -> "DEM":
        import rasterio

        with rasterio.open(yol) as src:
            t = src.transform
            if kucult > 1:
                h = src.height // kucult
                w = src.width // kucult
                z = src.read(1, out_shape=(h, w), resampling=rasterio.enums.Resampling.average)
                piksel = t.a * src.width / w
            else:
                z = src.read(1)
                piksel = t.a
            nod = src.nodata
        z = z.astype(np.float32)
        if nod is not None:
            z[z == nod] = np.nan
        # LOLA PGDA DEM'leri km değil metre; ölçek yoksa olduğu gibi.
        return cls(z, float(t.c), float(t.f), float(piksel))

    def satir_sutun(self, x, y):
        sutun = (np.asarray(x) - self.x0) / self.piksel - 0.5
        satir = (self.y0 - np.asarray(y)) / self.piksel - 0.5
        return satir, sutun

    def ornekle(self, x, y) -> np.ndarray:
        """Çift-doğrusal yükseklik; harita dışı NaN."""
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        satir, sutun = self.satir_sutun(x, y)
        h, w = self.yukseklik.shape
        disarida = (satir < 0) | (sutun < 0) | (satir > h - 1) | (sutun > w - 1)
        z = map_coordinates(
            self.yukseklik, [satir.ravel(), sutun.ravel()], order=1, mode="nearest"
        ).reshape(x.shape)
        z = z.astype(np.float64)
        z[disarida] = np.nan
        return z

    def egim_derece(self) -> np.ndarray:
        gy, gx = np.gradient(self.yukseklik, self.piksel)
        return np.degrees(np.arctan(np.hypot(gx, gy)))
