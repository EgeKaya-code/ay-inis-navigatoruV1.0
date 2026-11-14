import numpy as np
import pytest

from lunar_nav.config import DATA_DIR
from lunar_nav.ephemeris import KERNELS, alt_az, sun_visible_fraction
from lunar_nav.geo import R_MOON

KERNEL_DIR = DATA_DIR / "raw" / "kernels"
needs_kernels = pytest.mark.skipif(
    not all((KERNEL_DIR / k).exists() for k in KERNELS), reason="SPICE kernels not downloaded"
)


def test_alt_az_cardinal_directions():
    # observer on the equator at lon 0; up = +x, east = +y, north = +z
    far = 1e12
    assert alt_az(0, 0, 0, [far, 0, 0])[0] == pytest.approx(90.0)
    alt, az = alt_az(0, 0, 0, [0, far, 0])
    assert (alt, az) == (pytest.approx(0.0, abs=1e-3), pytest.approx(90.0))
    alt, az = alt_az(0, 0, 0, [0, 0, far])
    assert (alt, az) == (pytest.approx(0.0, abs=1e-3), pytest.approx(0.0))


def test_alt_az_near_pole_points_poleward_at_180():
    # from 1 deg off the pole, the pole (on the surface) lies due "south", az 180,
    # and half the central angle below the horizontal
    alt, az = alt_az(-89.0, 30.0, 0, [0, 0, -R_MOON])
    assert az == pytest.approx(180.0, abs=1e-6)
    assert alt == pytest.approx(-0.5, abs=1e-6)


@pytest.mark.parametrize("u,expected", [(1.0, 1.0), (-1.0, 0.0), (0.0, 0.5)])
def test_sun_visible_fraction_limits(u, expected):
    assert sun_visible_fraction(u * 0.27, 0.0, 0.27) == pytest.approx(expected)


def test_sun_visible_fraction_is_monotonic():
    f = sun_visible_fraction(np.linspace(-0.3, 0.3, 61), 0.0, 0.27)
    assert np.all(np.diff(f) >= 0)


@needs_kernels
def test_alt_az_matches_skyfield_topocentric():
    pytest.importorskip("skyfield")  # legacy DE421 path; the DE440 path is tested in test_spice_local.py
    from lunar_nav.ephemeris import MoonFrame

    mf = MoonFrame(KERNEL_DIR)
    t = mf.hourly((2026, 11, 14), (2026, 11, 16), 6.0)
    lat, lon = -85.98, -1.67
    place = mf.eph["moon"] + mf.pc.build_latlon_degrees(mf.frame, lat, lon)
    for body in ("sun", "earth"):
        ref_alt, ref_az, _ = place.at(t).observe(mf.eph[body]).apparent().altaz()
        alt, az = alt_az(lat, lon, 0.0, mf.body_vectors(t, body))
        # we skip aberration (~0.006 deg) on purpose
        np.testing.assert_allclose(alt, ref_alt.degrees, atol=0.02)
        daz = (az - ref_az.degrees + 180) % 360 - 180
        np.testing.assert_allclose(daz, 0.0, atol=0.05)
