"""Picking candidate landing points on the DEM."""

from __future__ import annotations

import numpy as np
from matplotlib.path import Path as MplPath
from scipy.ndimage import maximum_filter

from .dem import DemLayer
from .geo import ps_to_latlon


def slope_deg(layer: DemLayer) -> np.ndarray:
    gy, gx = np.gradient(layer.height, layer.res)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def neighbourhood_slope_deg(layer: DemLayer) -> np.ndarray:
    """Steepest slope in each pixel's 3x3 neighbourhood: flat means the neighbours are flat too,
    not just one lucky pixel."""
    return maximum_filter(slope_deg(layer), size=3, mode="nearest")


def pixel_centres(layer: DemLayer) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = layer.height.shape
    x = layer.left + (np.arange(cols) + 0.5) * layer.res
    y = layer.top - (np.arange(rows) + 0.5) * layer.res
    xx, yy = np.meshgrid(x, y)
    return xx, yy


def highest_flat_point(layer: DemLayer, x0: float, y0: float, radius_m: float,
                       max_slope_deg: float) -> tuple[float, float, float, float]:
    """Highest pixel within radius_m of (x0, y0) whose 3x3 neighbourhood is flatter than max_slope_deg.

    Returns (lat, lon, height, slope). High flat ground is where polar illumination is best.
    """
    s = slope_deg(layer)
    s3 = neighbourhood_slope_deg(layer)
    x, y = pixel_centres(layer)
    ok = (s3 < max_slope_deg) & (np.hypot(x - x0, y - y0) <= radius_m) & np.isfinite(layer.height)
    if not ok.any():
        raise ValueError("no flat pixel in the search radius")
    h = np.where(ok, layer.height, -np.inf)
    r, c = np.unravel_index(np.argmax(h), h.shape)
    lat, lon = ps_to_latlon(x[r, c], y[r, c])
    return float(lat), float(lon), float(layer.height[r, c]), float(s[r, c])


def inside_polygon(x, y, ring_xy) -> np.ndarray:
    """True where (x, y) lies inside the polygon whose vertices are the rows of ring_xy."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    inside = MplPath(np.asarray(ring_xy, float)).contains_points(np.c_[x.ravel(), y.ravel()])
    return inside.reshape(x.shape)


def pick_spaced(x, y, score, n: int, min_dist_m: float, tiebreak=None) -> np.ndarray:
    """Indices of up to n points, best score first, no two closer than min_dist_m.

    Greedy: take the best remaining point, drop everything within min_dist_m of it, repeat.
    Equal scores are ordered by `tiebreak` (smaller first). NaN scores are never picked.
    """
    x, y, score = (np.asarray(a, float).ravel() for a in (x, y, score))
    valid = np.flatnonzero(np.isfinite(score))
    keys = (-score[valid],) if tiebreak is None else (np.asarray(tiebreak, float).ravel()[valid], -score[valid])
    order = valid[np.lexsort(keys)]
    picked: list[int] = []
    for i in order:
        if len(picked) == n:
            break
        if all(np.hypot(x[i] - x[j], y[i] - y[j]) >= min_dist_m for j in picked):
            picked.append(int(i))
    return np.array(picked, dtype=int)
