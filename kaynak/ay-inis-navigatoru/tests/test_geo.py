import numpy as np
import pytest
from pyproj import CRS, Transformer

from lunar_nav.geo import R_MOON, destination, haversine, latlon_to_ps, ps_to_latlon

# CRS string of LDEM_80S_*_ADJ.TIF, so our formulas are checked against the data's own projection
DEM_CRS = CRS.from_proj4(f"+proj=stere +lat_0=-90 +lon_0=0 +k=1 +x_0=0 +y_0=0 +R={R_MOON} +units=m +no_defs")
GEO_CRS = CRS.from_proj4(f"+proj=longlat +R={R_MOON} +no_defs")


@pytest.mark.parametrize("lat,lon", [(-90, 0), (-89.67, 129.78), (-84.6, 31.0), (-82.26, -54.58), (-80, 180)])
def test_projection_matches_pyproj(lat, lon):
    x, y = latlon_to_ps(lat, lon)
    px, py = Transformer.from_crs(GEO_CRS, DEM_CRS, always_xy=True).transform(lon, lat)
    assert x == pytest.approx(px, abs=1e-3)
    assert y == pytest.approx(py, abs=1e-3)


def test_projection_roundtrip():
    lat = np.array([-89.9, -87.45, -85.0, -80.1])
    lon = np.array([-170.0, -5.17, 53.27, 111.29])
    la, lo = ps_to_latlon(*latlon_to_ps(lat, lon))
    np.testing.assert_allclose(la, lat, atol=1e-9)
    np.testing.assert_allclose(lo, lon, atol=1e-9)


def test_dem_extent_is_80_south():
    # LDEM_80S_20MPP: 30400 px * 20 m = 608 km wide, i.e. +-304 km from the pole
    lat, _ = ps_to_latlon(304000.0, 0.0)
    assert lat == pytest.approx(-80.0, abs=0.01)


def test_destination_distance_and_direction():
    lat, lon = -85.98, -1.67
    for az in (0, 45, 90, 200):
        la, lo = destination(lat, lon, az, 25000.0)
        assert haversine(lat, lon, la, lo) == pytest.approx(25000.0, rel=1e-9)
    la, _ = destination(lat, lon, 180.0, 10000.0)  # due south = towards the pole
    assert la < lat


def test_destination_over_the_pole():
    la, lo = destination(-89.9, 0.0, 180.0, np.radians(0.2) * R_MOON)
    assert la == pytest.approx(-89.9, abs=1e-6)
    assert abs(lo) == pytest.approx(180.0, abs=1e-6)
