"""Sun and Earth vectors in the Moon-fixed MOON_ME frame from the DE440 SPICE kernels (spiceypy).

Same geometry as ephemeris.MoonFrame (skyfield + DE421): position of the body seen from the
Moon's centre, light-time corrected only (no stellar aberration), expressed in the Moon's mean
Earth / polar axis frame at the observation epoch. In moon_de440_250416.tf, MOON_ME is an alias
of MOON_ME_DE440_ME421, i.e. the DE421 mean-Earth frame the LOLA products use. IAU_MOON is not used.

Kernels are read from the local raw-data folder only (localdata.DATA).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import spiceypy as sp

from .localdata import DATA
from .visibility import Ephemeris

KERNELS = ("naif0012.tls", "de440.bsp", "moon_pa_de440_200625.bpc", "moon_de440_250416.tf")
FRAME = "MOON_ME"
ABCORR = "LT"
_loaded = False


def load_kernels(kernel_dir: Path | None = None) -> None:
    global _loaded
    if _loaded:
        return
    for k in KERNELS:
        path = (kernel_dir or DATA) / k
        if not path.exists():
            raise FileNotFoundError(path)
        sp.furnsh(str(path))
    _loaded = True


def ephemeris_table(start_utc: str, n_steps: int, step_hours: float = 1.0, chunk: int = 20000) -> Ephemeris:
    """Hourly (or coarser) Sun/Earth vectors, metres, from `start_utc` (e.g. '2027-01-01T00:00:00')."""
    load_kernels()
    et = sp.str2et(start_utc) + np.arange(n_steps) * step_hours * 3600.0
    sun = np.empty((n_steps, 3))
    earth = np.empty((n_steps, 3))
    for i in range(0, n_steps, chunk):
        sl = slice(i, i + chunk)
        sun[sl] = np.asarray(sp.spkpos("SUN", et[sl], FRAME, ABCORR, "MOON")[0]) * 1e3
        earth[sl] = np.asarray(sp.spkpos("EARTH", et[sl], FRAME, ABCORR, "MOON")[0]) * 1e3
    jd_tt = 2451545.0 + et / 86400.0  # TDB; differs from TT by < 2 ms, irrelevant at hourly steps
    return Ephemeris(jd_tt, sun, earth, step_hours)


def year_table(year: int, step_hours: float = 1.0) -> Ephemeris:
    """One calendar year (UTC), end exclusive: 8760 or 8784 hourly steps."""
    load_kernels()
    hours = (sp.str2et(f"{year + 1}-01-01T00:00:00") - sp.str2et(f"{year}-01-01T00:00:00")) / 3600.0
    return ephemeris_table(f"{year}-01-01T00:00:00", int(round(hours / step_hours)), step_hours)
