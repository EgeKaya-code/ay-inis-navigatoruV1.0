import numpy as np
import pytest

from lunar_nav.dem import DemLayer
from lunar_nav.sites import highest_flat_point, slope_deg
from lunar_nav.visibility import PointSeries, longest_run, summarize


@pytest.mark.parametrize("mask,expected", [
    ([], 0), ([0, 0], 0), ([1], 1), ([1, 1, 0, 1], 2), ([0, 1, 1, 1, 0, 1, 1], 3), ([1, 1, 1], 3),
])
def test_longest_run(mask, expected):
    assert longest_run(np.array(mask, bool)) == expected


def test_summarize():
    frac = np.array([1.0, 0.5, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0])
    margin = np.array([1.0, 1.0, 1.0, -1.0, -1.0, 1.0, -1.0, 1.0])
    z = np.zeros_like(frac)
    m = summarize(PointSeries(z, z, frac, z, z, margin), step_hours=24.0)
    assert m["sun_energy_pct"] == pytest.approx(100 * 3.5 / 8)
    assert m["sun_any_pct"] == pytest.approx(50.0)
    assert m["earth_pct"] == pytest.approx(62.5)
    assert m["sun_and_earth_pct"] == pytest.approx(37.5)
    assert m["longest_dark_days"] == pytest.approx(3.0)
    assert m["longest_no_earth_days"] == pytest.approx(2.0)


def test_slope_of_tilted_plane():
    n, res = 50, 20.0
    plane = np.tile(np.arange(n) * res * np.tan(np.radians(10.0)), (n, 1)).astype(np.float32)
    s = slope_deg(DemLayer(plane, 0.0, n * res, res))
    np.testing.assert_allclose(s[1:-1, 1:-1], 10.0, atol=1e-3)


def test_highest_flat_point_skips_steep_peak():
    n, res = 101, 20.0
    h = np.zeros((n, n), np.float32)
    h[20:40, 20:40] = 100.0  # flat-topped mesa: flat inside, cliffs at the edges
    h[70, 70] = 500.0  # a single spike: highest but steep
    layer = DemLayer(h, -n * res / 2, n * res / 2 + 60000.0, res)  # somewhere near the pole
    cx, cy = 0.0, 60000.0
    lat, lon, height, slope = highest_flat_point(layer, cx, cy, 5000.0, 5.0)
    assert height == pytest.approx(100.0)
    assert slope < 5.0
