"""Sun and Earth positions in the Moon-fixed MOON_ME (DE421) frame.

The LOLA DEMs are in MOON_ME/DE421, so we use the same frame: DE421 for the
planets plus the NAIF lunar orientation kernels. Tables are vectors from the
Moon's centre; the per-point elevation/azimuth is then cheap (see alt_az), which
is what lets the browser app do it for any point without SPICE.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from .config import DATA_DIR
from .geo import R_MOON

KERNELS = ("de421.bsp", "moon_080317.tf", "pck00008.tpc", "moon_pa_de421_1900-2050.bpc")
SUN_RADIUS_M = 695_700_000.0  # IAU 2015 nominal solar radius


class MoonFrame:
    def __init__(self, kernel_dir: Path | None = None):
        # skyfield is only needed for this legacy DE421 path; spice_ephem.py (DE440) does not use it
        from skyfield.api import Loader
        from skyfield.planetarylib import PlanetaryConstants

        self.load = Loader(str(kernel_dir or DATA_DIR / "raw" / "kernels"), verbose=False)
        self.eph = self.load(KERNELS[0])
        self.pc = PlanetaryConstants()
        self.pc.read_text(self.load(KERNELS[1]))
        self.pc.read_text(self.load(KERNELS[2]))
        self.pc.read_binary(self.load(KERNELS[3]))
        self.frame = self.pc.build_frame_named("MOON_ME_DE421")
        self.ts = self.load.timescale()

    def body_vectors(self, t, body: str) -> np.ndarray:
        """Light-time corrected position of `body` seen from the Moon's centre, (N, 3) metres."""
        moon = self.eph["moon"]
        pos = moon.at(t).observe(self.eph[body])
        xyz = pos.frame_xyz(self.frame).m
        return np.asarray(xyz).T.reshape(-1, 3)

    def hourly(self, start: tuple, end: tuple, step_hours: float = 1.0):
        """Time grid from start to end (UTC tuples, e.g. (2026, 1, 1))."""
        t0, t1 = self.ts.utc(*start), self.ts.utc(*end)
        n = int(round((t1.tt - t0.tt) * 24.0 / step_hours)) + 1
        return self.ts.tt_jd(t0.tt + np.arange(n) * step_hours / 24.0)


def surface_point(lat, lon, height=0.0, radius: float = R_MOON) -> np.ndarray:
    """Moon-fixed Cartesian position (m) of a point on/above the reference sphere."""
    phi, lam = np.radians(lat), np.radians(lon)
    r = radius + height
    return np.array([r * np.cos(phi) * np.cos(lam), r * np.cos(phi) * np.sin(lam), r * np.sin(phi)])


def alt_az(lat, lon, height, body_xyz):
    """Elevation and azimuth (deg) of a body seen from a surface point.

    Elevation is above the local horizontal of the reference sphere; azimuth is
    clockwise from local north, the same convention as horizon profiles.
    """
    phi, lam = np.radians(lat), np.radians(lon)
    up = np.array([np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)])
    east = np.array([-np.sin(lam), np.cos(lam), 0.0])
    north = np.cross(up, east)
    v = np.asarray(body_xyz) - surface_point(lat, lon, height)
    e, n, u = v @ east, v @ north, v @ up
    alt = np.degrees(np.arctan2(u, np.hypot(e, n)))
    az = np.degrees(np.arctan2(e, n)) % 360.0
    return alt, az


def sun_visible_fraction(sun_alt, horizon_alt, sun_radius_deg):
    """Fraction of the solar disk above the terrain horizon (flat-horizon approximation over the disk)."""
    u = np.clip((np.asarray(sun_alt) - horizon_alt) / sun_radius_deg, -1.0, 1.0)
    theta = 2.0 * np.arccos(u)  # angle of the hidden circular segment
    return 1.0 - (theta - np.sin(theta)) / (2.0 * np.pi)
