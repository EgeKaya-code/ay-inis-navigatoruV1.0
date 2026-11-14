"""Sun and Earth visibility over time at one point, and the summary metrics.

Inputs: a horizon profile and hourly Sun/Earth vectors in MOON_ME. Output per
time step: visible fraction of the solar disk and whether Earth clears the
terrain; then illumination %, Earth visibility %, and the longest dark spell
and communication gap.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .ephemeris import SUN_RADIUS_M, MoonFrame, alt_az, sun_visible_fraction
from .horizon import HorizonProfile


@dataclass
class Ephemeris:
    jd_tt: np.ndarray  # (N,) Julian date, TT
    sun: np.ndarray  # (N, 3) m, MOON_ME, from the Moon's centre
    earth: np.ndarray  # (N, 3)
    step_hours: float

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(path, jd_tt=self.jd_tt, sun=self.sun, earth=self.earth,
                            step_hours=self.step_hours)

    @classmethod
    def load(cls, path: Path) -> "Ephemeris":
        z = np.load(path)
        return cls(z["jd_tt"], z["sun"], z["earth"], float(z["step_hours"]))


def build_ephemeris(start: tuple, end: tuple, step_hours: float = 1.0,
                    frame: MoonFrame | None = None) -> Ephemeris:
    frame = frame or MoonFrame()
    t = frame.hourly(start, end, step_hours)
    t = t[:-1]  # end exclusive, so years have whole numbers of steps
    return Ephemeris(t.tt, frame.body_vectors(t, "sun"), frame.body_vectors(t, "earth"), step_hours)


@dataclass
class PointSeries:
    sun_alt: np.ndarray
    sun_az: np.ndarray
    sun_fraction: np.ndarray  # 0..1 of the solar disk above the terrain
    earth_alt: np.ndarray
    earth_az: np.ndarray
    earth_margin: np.ndarray  # Earth elevation minus terrain horizon, deg


def point_series(prof: HorizonProfile, eph: Ephemeris) -> PointSeries:
    h = prof.ground_height_m + prof.observer_height_m
    sun_alt, sun_az = alt_az(prof.lat, prof.lon, h, eph.sun)
    earth_alt, earth_az = alt_az(prof.lat, prof.lon, h, eph.earth)
    sun_r = np.degrees(np.arcsin(SUN_RADIUS_M / np.linalg.norm(eph.sun, axis=1)))
    frac = sun_visible_fraction(sun_alt, prof.elevation_at(sun_az), sun_r)
    margin = earth_alt - prof.elevation_at(earth_az)
    return PointSeries(sun_alt, sun_az, frac, earth_alt, earth_az, margin)


def longest_run(mask: np.ndarray) -> int:
    """Length of the longest run of consecutive True values."""
    m = np.concatenate([[False], np.asarray(mask, bool), [False]])
    edges = np.flatnonzero(np.diff(m.astype(np.int8)))
    return int((edges[1::2] - edges[::2]).max()) if edges.size else 0


def summarize(s: PointSeries, step_hours: float, earth_min_margin_deg: float = 0.0) -> dict:
    lit = s.sun_fraction > 0.0
    earth = s.earth_margin > earth_min_margin_deg
    return {
        "sun_energy_pct": 100.0 * float(np.mean(s.sun_fraction)),
        "sun_any_pct": 100.0 * float(np.mean(lit)),
        "earth_pct": 100.0 * float(np.mean(earth)),
        "sun_and_earth_pct": 100.0 * float(np.mean(lit & earth)),
        "longest_dark_days": longest_run(~lit) * step_hours / 24.0,
        "longest_no_earth_days": longest_run(~earth) * step_hours / 24.0,
    }
