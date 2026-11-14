import numpy as np
import pytest

from lunar_nav.dem import DemLayer
from lunar_nav.geo import R_MOON, latlon_to_ps
from lunar_nav.horizon import Band, elevation_angle, horizon_profile

# Observer off the pole: at exactly -90 deg every azimuth is degenerate.
LAT, LON = -88.0, 40.0


def flat_layer(half=80000.0, res=100.0):
    """Zero-height grid (i.e. the bare sphere) centred on the observer."""
    n = int(2 * half / res)
    x0, y0 = latlon_to_ps(LAT, LON)
    return DemLayer(np.zeros((n, n), np.float32), x0 - half, y0 + half, res, "flat")


def add_ring(layer, lat, lon, radius_m, width_m, height_m):
    """Raise a circular ridge around (lat, lon); same height seen in every direction."""
    x0, y0 = latlon_to_ps(lat, lon)
    n = layer.height.shape[0]
    xs = layer.left + (np.arange(n) + 0.5) * layer.res
    ys = layer.top - (np.arange(n) + 0.5) * layer.res
    r = np.hypot(xs[None, :] - x0, ys[:, None] - y0)
    layer.height[np.abs(r - radius_m) < width_m / 2] = height_m


def test_curvature_drop_matches_small_angle_limit():
    # a 0 m point 10 km away seen from 0 m: depressed by ~d/2R, i.e. drop d^2/2R ~ 29 m
    d = 10000.0
    assert elevation_angle(0.0, 0.0, d, 0.0) == pytest.approx(-d / (2 * R_MOON), rel=1e-6)
    assert d**2 / (2 * R_MOON) == pytest.approx(28.8, abs=0.1)


def test_bare_sphere_horizon_is_geometric_dip():
    # on a smooth sphere the horizon of an observer at h sits at -sqrt(2h/R)
    h = 10.0
    prof = horizon_profile(LAT, LON, [Band(flat_layer(), 0.0, 20000.0)], observer_height_m=h,
                           azimuth_step_deg=30.0)
    dip = -np.degrees(np.sqrt(2 * h / R_MOON))
    np.testing.assert_allclose(prof.elevation_deg, dip, atol=0.005)


def test_ring_ridge_elevation_and_distance():
    layer = flat_layer(res=20.0, half=10000.0)
    add_ring(layer, LAT, LON, 5000.0, 200.0, 500.0)
    prof = horizon_profile(LAT, LON, [Band(layer, 0.0, 9000.0)], observer_height_m=0.0,
                           azimuth_step_deg=15.0)
    expected = np.degrees(elevation_angle(0.0, 500.0, 4900.0, 0.0))  # near edge of the ring
    np.testing.assert_allclose(prof.elevation_deg, expected, atol=0.1)
    np.testing.assert_allclose(prof.distance_m, 4900.0, atol=60.0)


def test_far_band_sees_distant_massif():
    near = flat_layer(half=8000.0, res=20.0)
    far = flat_layer(half=80000.0, res=200.0)
    add_ring(far, LAT, LON, 50000.0, 2000.0, 3000.0)
    bands = [Band(near, 0.0, 5000.0), Band(far, 5000.0, 70000.0)]
    prof = horizon_profile(LAT, LON, bands, observer_height_m=2.0, azimuth_step_deg=45.0)
    expected = np.degrees(elevation_angle(0.0, 3000.0, 49000.0, 2.0))
    np.testing.assert_allclose(prof.elevation_deg, expected, atol=0.1)
    assert np.all(prof.distance_m > 48000.0)


def test_elevation_at_wraps_around_north():
    prof = horizon_profile(LAT, LON, [Band(flat_layer(), 0.0, 1000.0)], azimuth_step_deg=90.0)
    prof.elevation_deg[:] = [1.0, 2.0, 3.0, 4.0]
    assert prof.elevation_at(315.0) == pytest.approx(2.5)
    assert prof.elevation_at(-45.0) == pytest.approx(2.5)
