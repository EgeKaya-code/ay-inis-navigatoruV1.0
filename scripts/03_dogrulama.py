"""Yöntemimizi NASA'nın ortalama görünürlük haritalarıyla karşılaştırır (PGDA ürün 69).

Haritalar (Mazarico vd. 2011, güncel sürüm 201608): 18.6 yıllık, saatlik ortalama
  AVGVISIB_75S_120M_201608.TIF        – Güneş diskinin herhangi bir kısmının görünme oranı
  AVGVISIB_75S_120M_201608_EARTH.TIF  – Dünya diskinin herhangi bir kısmının görünme oranı
Ölçek: GeoTIFF'teki scale (4e-5) uygulanır.

Karşılaştırma koşulları haritalarınkine yaklaştırılır: gözlemci yüzeyde (0 m), 18.6 yıl,
3 saatlik adım, Dünya disk olarak (herhangi bir kısmı görünürse "görünür").
Fark: biz 80 m/piksel DEM kullanıyoruz, haritalar 120 m/piksel.

Çıktı: docs/dogrulama.json ve docs/dogrulama.md
"""
import json
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))
from aynav.config import ham_veri_klasoru  # noqa: E402
from aynav.dem import DEM  # noqa: E402
from aynav.efemeris import kernelleri_yukle, konumlar, saatlik_zamanlar  # noqa: E402
from aynav.gorunurluk import disk_gorunen_kesir, yerel_azimut_yukseklik  # noqa: E402
from aynav.projeksiyon import enlemboylam_xy, xy_enlemboylam  # noqa: E402
from aynav.ufuk import isin_mesafeleri, ufuk_profili, ufuk_yuksekligi  # noqa: E402

DUNYA_YARICAP_KM = 6371.0
GUNES_YARICAP_KM = 695700.0
_DEM = _G = _D = _MES = None


def _harita_degeri(yol, x, y):
    import rasterio

    with rasterio.open(yol) as s:
        olcek = s.scales[0]
        t = s.transform
        c = np.floor((np.asarray(x) - t.c) / t.a).astype(int)
        r = np.floor((np.asarray(y) - t.f) / t.e).astype(int)
        return np.array([float(s.read(1, window=((ri, ri + 1), (ci, ci + 1)))[0, 0]) * olcek
                         for ri, ci in zip(r, c)])


def _hesapla(p):
    """0 m ve 2 m gözlemci için: Güneş enerji kesri, Güneş'in herhangi bir kısmı, Dünya (disk, herhangi bir kısmı)."""
    lat, lon = p
    x, y = enlemboylam_xy(lat, lon)
    z0 = float(_DEM.ornekle(np.array([x]), np.array([y]))[0])
    sonuc = []
    for h in (0.0, 2.0):
        az, u = ufuk_profili(_DEM, lat, lon, h, 0.25, _MES)
        gaz, gel, guz = yerel_azimut_yukseklik(lat, lon, z0 + h, _G)
        daz, del_, duz = yerel_azimut_yukseklik(lat, lon, z0 + h, _D)
        rg = np.degrees(np.arcsin(GUNES_YARICAP_KM / guz))
        rd = np.degrees(np.arcsin(DUNYA_YARICAP_KM / duz))
        gk = disk_gorunen_kesir((gel - ufuk_yuksekligi(az, u, gaz)) / rg)
        dk = disk_gorunen_kesir((del_ - ufuk_yuksekligi(az, u, daz)) / rd)
        sonuc += [float(gk.mean()), float((gk > 0).mean()), float((dk > 0).mean())]
    return sonuc


def _istatistik(fark):
    return {"mean": round(float(fark.mean()), 2), "mean_abs": round(float(np.abs(fark).mean()), 2),
            "max_abs": round(float(np.abs(fark).max()), 2), "n": int(len(fark))}


def main():
    global _DEM, _G, _D, _MES
    t0 = time.time()
    ham = ham_veri_klasoru()
    _DEM = DEM.oku(ham / "LDEM_80S_80MPP_ADJ.TIF")
    _MES = isin_mesafeleri(_DEM.piksel)
    egim = _DEM.egim_derece()
    kernelleri_yukle()
    z = saatlik_zamanlar("2010-01-01T00:00:00", "2028-08-08T00:00:00", 3.0)  # 18.6 yıl
    _G, _D = konumlar(z)

    rng = np.random.default_rng(20261114)
    rho_max = 2 * 1737400 * np.tan(np.radians(3.0))  # 84°G'ye kadar
    noktalar = []
    while len(noktalar) < 160:
        x, y = rng.uniform(-rho_max, rho_max, 2)
        if np.hypot(x, y) > rho_max:
            continue
        r, c = _DEM.satir_sutun(x, y)
        if egim[int(round(float(r))), int(round(float(c)))] > 10:
            continue
        lat, lon = xy_enlemboylam(x, y)
        noktalar.append((float(lat), float(lon)))

    with Pool() as havuz:
        biz = havuz.map(_hesapla, noktalar, chunksize=4)
    biz = np.array(biz)
    X, Y = enlemboylam_xy(np.array([p[0] for p in noktalar]), np.array([p[1] for p in noktalar]))
    nasa_g = _harita_degeri(ham / "pgda" / "AVGVISIB_75S_120M_201608.TIF", X, Y)
    nasa_d = _harita_degeri(ham / "pgda" / "AVGVISIB_75S_120M_201608_EARTH.TIF", X, Y)

    # biz[:, 0..2] = 0 m (enerji, herhangi, Dünya); biz[:, 3..5] = 2 m
    fg = 100 * (biz[:, 1] - nasa_g)  # NASA Güneş haritası: diskin herhangi bir kısmı
    fd = 100 * (biz[:, 2] - nasa_d)
    sonuc = {
        "olusturma": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "nokta_sayisi": len(noktalar),
        "donem": "2010-01-01 – 2028-08-08 (18.6 yıl), 3 saat adım",
        "donem_kisa": "2010–2028",
        "gozlemci_m": 0.0,
        "gunes_ort_mutlak_fark_puan": round(float(np.abs(fg).mean()), 2),
        "gunes_ort_fark_puan": round(float(fg.mean()), 2),
        "gunes_korelasyon": round(float(np.corrcoef(biz[:, 1], nasa_g)[0, 1]), 3),
        "dunya_ort_mutlak_fark_puan": round(float(np.abs(fd).mean()), 2),
        "dunya_ort_fark_puan": round(float(fd.mean()), 2),
        "dunya_korelasyon": round(float(np.corrcoef(biz[:, 2], nasa_d)[0, 1]), 3),
        "ozet": {
            "sun_0m": _istatistik(fg), "earth_0m": _istatistik(fd),
            "sun_0m_energy": _istatistik(100 * (biz[:, 0] - nasa_g)),
            "sun_2m": _istatistik(100 * (biz[:, 4] - nasa_g)), "earth_2m": _istatistik(100 * (biz[:, 5] - nasa_d)),
        },
        "noktalar": [
            {"lat": round(p[0], 4), "lon": round(p[1], 4), "biz_gunes": round(100 * b[1], 1),
             "nasa_gunes": round(100 * g, 1), "biz_dunya": round(100 * b[2], 1), "nasa_dunya": round(100 * d, 1),
             "biz_gunes_2m": round(100 * b[4], 1), "biz_dunya_2m": round(100 * b[5], 1)}
            for p, b, g, d in zip(noktalar, biz, nasa_g, nasa_d)
        ],
    }
    (KOK / "docs").mkdir(exist_ok=True)
    (KOK / "docs" / "dogrulama.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    _grafik(biz, nasa_g, nasa_d, sonuc)
    print({k: v for k, v in sonuc.items() if k != "noktalar"}, f"({time.time()-t0:.0f} s)")


def _grafik(biz, nasa_g, nasa_d, s):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 2, figsize=(10, 4.6))
    for a, b, n, ad, ort in [
        (ax[0], biz[:, 1], nasa_g, "Güneş (diskin herhangi bir kısmı görünür)", s["gunes_ort_mutlak_fark_puan"]),
        (ax[1], biz[:, 2], nasa_d, "Dünya (diskin herhangi bir kısmı görünür)", s["dunya_ort_mutlak_fark_puan"]),
    ]:
        a.plot([0, 100], [0, 100], color="#888", lw=0.8)
        a.scatter(100 * n, 100 * b, s=12, color="#2b5d8a")
        a.set_xlabel("NASA PGDA haritası, %")
        a.set_ylabel("Ay İniş Navigatörü, %")
        a.set_title(f"{ad}\nort. mutlak fark {ort} puan", fontsize=10)
        a.set_aspect("equal")
    fig.suptitle(f"{s['nokta_sayisi']} rastgele nokta, 84°G–90°G, 18.6 yıl", fontsize=10)
    fig.tight_layout()
    fig.savefig(KOK / "docs" / "dogrulama.png", dpi=130)


if __name__ == "__main__":
    main()
