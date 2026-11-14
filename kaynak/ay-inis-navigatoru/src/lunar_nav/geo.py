"""Spherical geometry and the south polar stereographic projection of the LOLA DEMs.

Angles are in degrees at the public interface. The projection matches the DEM
CRS ("Moon (2015) - Sphere / Ocentric / South Polar", scale 1 at the pole).
"""

from __future__ import annotations

import numpy as np

R_MOON = 1737400.0


def latlon_to_ps(lat, lon, radius: float = R_MOON):
    """Planetocentric lat/lon (deg, +East) -> polar stereographic x, y (m)."""
    phi = np.radians(lat)
    lam = np.radians(lon)
    rho = 2.0 * radius * np.tan(np.pi / 4.0 + phi / 2.0)
    return rho * np.sin(lam), rho * np.cos(lam)


def ps_to_latlon(x, y, radius: float = R_MOON):
    """Polar stereographic x, y (m) -> planetocentric lat/lon (deg, +East)."""
    rho = np.hypot(x, y)
    lat = np.degrees(2.0 * np.arctan(rho / (2.0 * radius)) - np.pi / 2.0)
    lon = np.degrees(np.arctan2(x, y))
    return lat, lon


def destination(lat, lon, azimuth, distance, radius: float = R_MOON):
    """Point reached from (lat, lon) along a great circle.

    azimuth: degrees clockwise from local north; distance: metres along the
    surface. Inputs broadcast against each other.
    """
    phi1 = np.radians(lat)
    lam1 = np.radians(lon)
    az = np.radians(azimuth)
    delta = np.asarray(distance) / radius
    sin_phi2 = np.sin(phi1) * np.cos(delta) + np.cos(phi1) * np.sin(delta) * np.cos(az)
    phi2 = np.arcsin(np.clip(sin_phi2, -1.0, 1.0))
    lam2 = lam1 + np.arctan2(
        np.sin(az) * np.sin(delta) * np.cos(phi1),
        np.cos(delta) - np.sin(phi1) * sin_phi2,
    )
    return np.degrees(phi2), (np.degrees(lam2) + 180.0) % 360.0 - 180.0


def haversine(lat1, lon1, lat2, lon2, radius: float = R_MOON):
    """Great-circle distance in metres."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2.0 * radius * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
