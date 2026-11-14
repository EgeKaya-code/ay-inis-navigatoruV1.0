"""Access to the LOLA south polar DEMs (Barker et al. 2023, PGDA product 90).

The 20 m DEM is ~2.6 GB, so we never download it whole: the files are
cloud-optimised GeoTIFFs and we read only the window we need over HTTP,
caching it under data/cache/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import map_coordinates

from .config import DATA_DIR
from .geo import latlon_to_ps

PGDA_BASE = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/"
LDEM_20M = PGDA_BASE + "LDEM_80S_20MPP_ADJ.TIF"
LDEM_80M = PGDA_BASE + "LDEM_80S_80MPP_ADJ.TIF"

_GDAL_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".TIF")


@dataclass
class DemLayer:
    """A height grid (m above the 1737.4 km sphere) in polar stereographic metres."""

    height: np.ndarray  # rows go from top (max y) to bottom
    left: float  # x of the left edge of column 0
    top: float  # y of the top edge of row 0
    res: float  # pixel size, m
    name: str = ""
    crs: object = None  # rasterio CRS, kept so crops can be written back out

    def sample(self, x, y) -> np.ndarray:
        """Bilinear height at x, y. NaN outside the grid or over missing data."""
        x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
        col = (x.ravel() - self.left) / self.res - 0.5
        row = (self.top - y.ravel()) / self.res - 0.5
        h = map_coordinates(self.height, [row, col], order=1, mode="constant", cval=np.nan)
        return h.reshape(x.shape)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        rows, cols = self.height.shape
        return self.left, self.top - rows * self.res, self.left + cols * self.res, self.top


def _open(src: str):
    if src.startswith("http"):
        src = "/vsicurl/" + src
    return rasterio.open(src)


def read_layer(src: str | Path, bounds=None, name: str = "") -> DemLayer:
    """Read a whole DEM file, or only `bounds` = (left, bottom, right, top) in metres."""
    with rasterio.Env(**_GDAL_ENV), _open(str(src)) as ds:
        if bounds is None:
            window = None
            transform = ds.transform
        else:
            window = from_bounds(*bounds, ds.transform).round_offsets().round_lengths()
            transform = ds.window_transform(window)
        height = ds.read(1, window=window).astype(np.float32)
        if ds.nodata is not None and not np.isnan(ds.nodata):
            height[height == ds.nodata] = np.nan
        crs = ds.crs
    return DemLayer(height, transform.c, transform.f, transform.a, name or Path(str(src)).stem, crs)


def write_layer(layer: DemLayer, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows, cols = layer.height.shape
    profile = dict(
        driver="GTiff", width=cols, height=rows, count=1, dtype="float32", crs=layer.crs,
        transform=rasterio.transform.from_origin(layer.left, layer.top, layer.res, layer.res),
        nodata=np.nan, compress="deflate", predictor=3, tiled=True,
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(layer.height, 1)


def near_crop(lat: float, lon: float, half_size_m: float, src: str = LDEM_20M,
              cache_dir: Path | None = None) -> DemLayer:
    """20 m DEM window centred on (lat, lon), fetched once and cached on disk."""
    x, y = latlon_to_ps(lat, lon)
    res = 20.0
    # snap to the pixel grid so cached crops line up with the source
    cx, cy = np.round(x / res) * res, np.round(y / res) * res
    bounds = (cx - half_size_m, cy - half_size_m, cx + half_size_m, cy + half_size_m)
    cache_dir = cache_dir or DATA_DIR / "cache"
    path = cache_dir / f"ldem20_{int(cx)}_{int(cy)}_{int(half_size_m)}.tif"
    if path.exists():
        return read_layer(path, name="near_20m")
    layer = read_layer(src, bounds, name="near_20m")
    write_layer(layer, path)
    return layer
