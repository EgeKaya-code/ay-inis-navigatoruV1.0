"""Terrain horizon profiles.

For each azimuth we march along the great circle leaving the observer and keep
the largest apparent elevation angle of the terrain. Curvature is handled
exactly: the observer sits at radius R + h0 + h_obs, a terrain sample at
surface distance d sits at radius R + h and central angle d / R, and the
elevation angle is measured from the observer's local horizontal plane.
(The usual d^2 / 2R drop is the small-angle limit of the same geometry.)

Each DEM layer covers one distance band, so the near field uses 20 m data and
the far field (distant massifs such as Malapert) a coarser DEM.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .dem import DemLayer
from .geo import R_MOON, destination, latlon_to_ps


@dataclass
class Band:
    layer: DemLayer
    min_dist_m: float
    max_dist_m: float


@dataclass
class HorizonProfile:
    lat: float
    lon: float
    observer_height_m: float
    ground_height_m: float
    azimuth_deg: np.ndarray
    elevation_deg: np.ndarray  # horizon elevation per azimuth
    distance_m: np.ndarray  # distance to the terrain point that sets it

    def elevation_at(self, azimuth_deg) -> np.ndarray:
        """Horizon elevation interpolated at arbitrary azimuths (periodic)."""
        az = np.append(self.azimuth_deg, self.azimuth_deg[0] + 360.0)
        el = np.append(self.elevation_deg, self.elevation_deg[0])
        return np.interp(np.mod(azimuth_deg, 360.0), az, el)


def elevation_angle(ground_h, target_h, distance, observer_height, radius: float = R_MOON):
    """Apparent elevation (rad) of a terrain point seen from the observer."""
    theta = np.asarray(distance) / radius
    r_obs = radius + ground_h + observer_height
    r_tgt = radius + np.asarray(target_h)
    return np.arctan2(r_tgt * np.cos(theta) - r_obs, r_tgt * np.sin(theta))


def horizon_profile(lat: float, lon: float, bands: list[Band], observer_height_m: float = 2.0,
                    azimuth_step_deg: float = 0.1, radius: float = R_MOON,
                    chunk: int = 360) -> HorizonProfile:
    """Horizon profile at (lat, lon). bands[0] must contain the observer."""
    x0, y0 = latlon_to_ps(lat, lon, radius)
    ground_h = float(bands[0].layer.sample(x0, y0))
    if np.isnan(ground_h):
        raise ValueError(f"no DEM height at observer ({lat}, {lon})")

    azimuths = np.arange(0.0, 360.0, azimuth_step_deg)
    best = np.full(azimuths.size, -np.inf)
    best_d = np.full(azimuths.size, np.nan)

    for band in bands:
        step = band.layer.res
        d = np.arange(max(band.min_dist_m, step), band.max_dist_m, step)
        for i in range(0, azimuths.size, chunk):
            az = azimuths[i:i + chunk, None]
            lat2, lon2 = destination(lat, lon, az, d[None, :], radius)
            h = band.layer.sample(*latlon_to_ps(lat2, lon2, radius))
            ang = elevation_angle(ground_h, h, d[None, :], observer_height_m, radius)
            ang = np.where(np.isnan(ang), -np.inf, ang)
            j = np.argmax(ang, axis=1)
            a = ang[np.arange(ang.shape[0]), j]
            better = a > best[i:i + chunk]
            best[i:i + chunk] = np.where(better, a, best[i:i + chunk])
            best_d[i:i + chunk] = np.where(better, d[j], best_d[i:i + chunk])

    return HorizonProfile(lat, lon, observer_height_m, ground_h, azimuths,
                          np.degrees(best), best_d)
