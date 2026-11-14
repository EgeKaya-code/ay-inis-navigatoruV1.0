"""İndirilen gerçek verilerle testler. Veri yoksa atlanır."""
import json

import numpy as np
import pytest

from aynav.config import PROJE_KOKU, ham_veri_klasoru

KERNELLER = ham_veri_klasoru() / "kernels"
BOLGE = PROJE_KOKU / "data" / "raw" / "bolgeler" / "artemis3_nasa_gorsel.geojson"


@pytest.mark.skipif(not (KERNELLER / "de440s.bsp").exists(), reason="kernel yok")
def test_kutupta_gunes_ufka_yakin():
    from aynav.efemeris import kernelleri_yukle, konumlar, saatlik_zamanlar
    from aynav.gorunurluk import yerel_azimut_yukseklik

    kernelleri_yukle()
    z = saatlik_zamanlar("2027-01-01T00:00:00", "2027-02-01T00:00:00", 6.0)
    g, d = konumlar(z)
    _, el, uz = yerel_azimut_yukseklik(-90.0, 0.0, 0.0, g)
    assert np.abs(el).max() < 1.7  # Ay ekseni eğikliği 1.54° + paralaks
    assert 0.98 < uz.mean() / 1.496e8 < 1.02
    _, el_d, uz_d = yerel_azimut_yukseklik(-90.0, 0.0, 0.0, d)
    assert np.abs(el_d).max() < 8.0  # Dünya librasyonla en fazla ~7° oynar
    assert 356000 < uz_d.min() and uz_d.max() < 407000


@pytest.mark.skipif(not BOLGE.exists(), reason="bölge dosyası yok")
def test_bolgeler():
    from aynav.bolgeler import bolgeleri_oku

    b = {x["id"]: x for x in bolgeleri_oku(BOLGE)}
    assert len(b) == 9
    # Malapert Massif bölgesi Mons Malapert'in (IAU: 85.99°G, 0.3°D civarı) üzerinde olmalı.
    assert abs(b["malapert_massif"]["merkez_lat"] + 86.0) < 0.1
    assert abs(b["malapert_massif"]["merkez_lon"]) < 2.0
    assert 300 < b["nobile_rim_1"]["alan_km2"] < 500
