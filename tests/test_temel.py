"""Hesap çekirdeği için temel testler (ağ ve büyük veri gerektirmez)."""
import numpy as np
import pytest

from aynav.dem import DEM
from aynav.gorunurluk import disk_gorunen_kesir, en_uzun_ardisik, yerel_azimut_yukseklik
from aynav.projeksiyon import enlemboylam_xy, harita_yonleri, xy_enlemboylam
from aynav.ufuk import ufuk_profili, ufuk_yuksekligi


def test_izdusum_gidis_donus():
    lat = np.array([-89.9, -85.0, -80.5, -83.6])
    lon = np.array([0.0, 45.0, -120.0, 179.0])
    x, y = enlemboylam_xy(lat, lon)
    la, lo = xy_enlemboylam(x, y)
    assert np.allclose(la, lat, atol=1e-9)
    assert np.allclose(lo, lon, atol=1e-9)


def test_izdusum_pyproj_ile_ayni():
    pyproj = pytest.importorskip("pyproj")
    crs = pyproj.CRS.from_proj4("+proj=stere +lat_0=-90 +lon_0=0 +k=1 +R=1737400 +units=m")
    t = pyproj.Transformer.from_crs(crs.geodetic_crs, crs, always_xy=True)
    for lat, lon in [(-85.99, -0.24), (-83.64, -68.75), (-88.2, 120.0)]:
        x1, y1 = t.transform(lon, lat)
        x2, y2 = enlemboylam_xy(lat, lon)
        assert abs(x1 - x2) < 0.01 and abs(y1 - y2) < 0.01


def test_harita_yonleri_gercek_kuzey():
    # Kuzey yönünde küçük adım enlemi artırmalı, doğu yönünde boylamı.
    lat, lon = -86.0, 30.0
    x, y = enlemboylam_xy(lat, lon)
    k, d = harita_yonleri(lon)
    la, _ = xy_enlemboylam(x + 100 * k[0], y + 100 * k[1])
    _, lo = xy_enlemboylam(x + 100 * d[0], y + 100 * d[1])
    assert la > lat and lo > lon


def test_disk_kesri():
    assert disk_gorunen_kesir(np.array([0.0]))[0] == pytest.approx(0.5)
    assert disk_gorunen_kesir(np.array([1.5]))[0] == pytest.approx(1.0)
    assert disk_gorunen_kesir(np.array([-1.0]))[0] == pytest.approx(0.0)


def test_en_uzun_ardisik():
    assert en_uzun_ardisik(np.array([0, 1, 1, 0, 1, 1, 1, 0], bool)) == 3
    assert en_uzun_ardisik(np.zeros(5, bool)) == 0


def test_tepe_dogrudan_yukarida():
    az, el, _ = yerel_azimut_yukseklik(-90.0, 0.0, 0.0, np.array([[0.0, 0.0, -400000.0]]))
    assert el[0] == pytest.approx(90.0, abs=1e-6)


def test_ufuk_aradeger_dairesel():
    az = np.arange(0, 360, 90.0)
    u = np.array([0.0, 1.0, 2.0, 3.0])
    assert ufuk_yuksekligi(az, u, 315.0) == pytest.approx(1.5)


def _sentetik_dem(z):
    n = z.shape[0]
    p = 80.0
    return DEM(z.astype(np.float32), -n / 2 * p, n / 2 * p, p)


def test_duz_kure_ufku_negatif():
    # Düz (küresel) yüzeyde 2 m yükseklikteki gözlemcinin ufku hafif negatiftir.
    dem = _sentetik_dem(np.zeros((400, 400)))
    _, u = ufuk_profili(dem, -89.5, 0.0, gozlemci_m=2.0, adim_derece=10.0)
    assert np.all(u < 0) and np.all(u > -0.2)


def test_duvar_ufku():
    # Gözlemciden ~4 km uzakta 700 m'lik bir duvar: ufuk ~ atan(700/4000) ~ 10°.
    n = 400
    z = np.zeros((n, n))
    lat, lon = -89.85, 0.0
    x0, y0 = enlemboylam_xy(lat, lon)
    xs = (np.arange(n) + 0.5) * 80.0 - n / 2 * 80.0
    X, Y = np.meshgrid(xs, -xs)
    r = np.hypot(X - x0, Y - y0)
    z[(r > 4000) & (r < 4400)] = 700.0
    dem = _sentetik_dem(z)
    _, u = ufuk_profili(dem, lat, lon, gozlemci_m=0.0, adim_derece=30.0)
    assert np.all(np.abs(u - np.degrees(np.arctan(700 / 4000))) < 1.5)
