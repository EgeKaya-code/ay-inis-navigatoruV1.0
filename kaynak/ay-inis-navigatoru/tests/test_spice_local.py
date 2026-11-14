"""DE440/SPICE ephemeris and the local-data helpers. Kernel tests are skipped when the local data folder is absent."""

import sys
from pathlib import Path

import numpy as np
import pytest

from lunar_nav.dem import DemLayer
from lunar_nav.localdata import DATA

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
needs_kernels = pytest.mark.skipif(not (DATA / "de440.bsp").exists(), reason="local SPICE kernels not present")


@needs_kernels
def test_year_table_lengths_and_distances():
    from lunar_nav.spice_ephem import year_table

    leap, common = year_table(2028, step_hours=24.0), year_table(2027, step_hours=24.0)
    assert len(leap.jd_tt) == 366 and len(common.jd_tt) == 365
    earth_km = np.linalg.norm(common.earth, axis=1) / 1e3
    sun_au = np.linalg.norm(common.sun, axis=1) / 1.495978707e11
    assert 355_000 < earth_km.min() and earth_km.max() < 407_500
    assert 0.98 < sun_au.min() and sun_au.max() < 1.02


@needs_kernels
def test_earth_stays_near_the_sub_earth_direction():
    """In MOON_ME the Earth librates around +x (lon 0, lat 0): within about 8 deg in both angles."""
    from lunar_nav.spice_ephem import year_table

    e = year_table(2027, step_hours=6.0).earth
    lon = np.degrees(np.arctan2(e[:, 1], e[:, 0]))
    lat = np.degrees(np.arcsin(e[:, 2] / np.linalg.norm(e, axis=1)))
    assert np.abs(lon).max() < 8.5 and np.abs(lat).max() < 7.0


def test_coarsen_block_average_is_aligned_to_the_coarse_grid():
    from diag_resolution import coarsen

    h = np.arange(12 * 12, dtype=np.float32).reshape(12, 12)
    layer = DemLayer(h, left=-40.0, top=140.0, res=20.0)  # edges not on multiples of 60
    c = coarsen(layer, 3)
    assert c.res == 60.0 and c.left % 60.0 == 0.0 and c.top % 60.0 == 0.0
    r0, c0 = int((layer.top - c.top) / 20), int((c.left - layer.left) / 20)
    assert c.height[0, 0] == pytest.approx(h[r0:r0 + 3, c0:c0 + 3].mean())
    assert c.sample(c.left + 30.0, c.top - 30.0) == pytest.approx(c.height[0, 0])
