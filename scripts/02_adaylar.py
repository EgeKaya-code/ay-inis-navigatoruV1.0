"""Her Artemis III bölgesinde aday iniş noktalarını tarar ve en iyi 5 noktayı seçer.

Adımlar
1. Bölge poligonu içinde ızgara noktaları (data/raw/usgs/*.geojson).
2. Her noktada 2 m gözlemci için kaba ufuk (0.5°) ve metrik yılı için Güneş/Dünya yüzdeleri.
3. Eğim sınırını geçen noktalardan: Dengeli, En çok güç, En uzun iletişim + 2 yedek.
4. Seçilen noktalar için ince ufuk (0.25°) – 2 m ve 10 m gözlemci.

Çıktılar (data/islenmis/):
  adaylar.json – bölgeler, ızgara metrikleri, seçilen noktalar ve metrikleri
  ufuklar.npz  – seçilen noktaların ufuk profilleri
"""
import json
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aynav.bolgeler import bolgeleri_oku, izgara  # noqa: E402
from aynav.config import ham_veri_klasoru, islenmis_klasoru, varsayimlar  # noqa: E402
from aynav.dem import DEM  # noqa: E402
from aynav.gorunurluk import ozet, seriler  # noqa: E402
from aynav.projeksiyon import xy_enlemboylam  # noqa: E402
from aynav.ufuk import isin_mesafeleri, ufuk_profili  # noqa: E402

V = varsayimlar()
_DEM: DEM | None = None
_EGIM: np.ndarray | None = None
_G = _D = None
_MES = None


def _yil_maskesi(zaman_unix, yil, adim=1):
    b = datetime(yil, 1, 1, tzinfo=timezone.utc).timestamp()
    s = datetime(yil + 1, 1, 1, tzinfo=timezone.utc).timestamp()
    idx = np.flatnonzero((zaman_unix >= b) & (zaman_unix < s))
    return idx[::adim]


def _tara(args):
    lat, lon = args
    z0 = float(_DEM.ornekle(*_xy(lat, lon))[0])
    az, u = ufuk_profili(_DEM, lat, lon, 2.0, V["ufuk"]["tarama_adim_derece"], _MES)
    s = seriler(lat, lon, z0, 2.0, az, u, _G, _D)
    o = ozet(s, adim_saat=2.0)
    return z0, o


def _xy(lat, lon):
    from aynav.projeksiyon import enlemboylam_xy

    x, y = enlemboylam_xy(lat, lon)
    return np.array([x]), np.array([y])


def _egim(lat, lon):
    r, c = _DEM.satir_sutun(*_xy(lat, lon))
    return float(_EGIM[int(round(r[0])), int(round(c[0]))])


def _sec(noktalar, en_az_aralik, n):
    """Dengeli / güç / iletişim için bölgenin en iyi noktaları + yedekler.

    Bir nokta birden çok ölçütte en iyiyse etiketleri birleşir (ör. "dengeli+guc").
    Yedekler, seçilenlerden en az `en_az_aralik` uzaktaki en dengeli noktalardır.
    """
    kriterler = [
        ("dengeli", lambda p: p["enerji_yuzde"] + p["dunya_yuzde"]),
        ("guc", lambda p: (p["enerji_yuzde"], -p["en_uzun_karanlik_saat"])),
        ("iletisim", lambda p: (p["dunya_yuzde"], -p["en_uzun_iletisimsiz_saat"])),
    ]
    secilen = []
    for etiket, anahtar in kriterler:
        en = max(noktalar, key=anahtar)
        var = next((q for q in secilen if q["x"] == en["x"] and q["y"] == en["y"]), None)
        if var:
            var["etiket"] += "+" + etiket
        else:
            secilen.append({**en, "etiket": etiket})

    def uygun(p):
        return all(np.hypot(p["x"] - q["x"], p["y"] - q["y"]) >= en_az_aralik for q in secilen)

    for p in sorted(noktalar, key=kriterler[0][1], reverse=True):
        if len(secilen) >= n:
            break
        if uygun(p):
            secilen.append({**p, "etiket": "yedek"})
    return secilen


def main():
    global _DEM, _EGIM, _G, _D, _MES
    t0 = time.time()
    ham = ham_veri_klasoru()
    _DEM = DEM.oku(ham / "LDEM_80S_80MPP_ADJ.TIF")
    _EGIM = _DEM.egim_derece()
    _MES = isin_mesafeleri(_DEM.piksel)
    ef = np.load(islenmis_klasoru() / "efemeris.npz")
    yil = V["aday"]["metrik_yili"]
    idx = _yil_maskesi(ef["zaman_unix"], yil, adim=2)
    _G, _D = ef["gunes_km"][idx], ef["dunya_km"][idx]
    print(f"DEM {_DEM.yukseklik.shape}, {yil} için {len(idx)} adım (2 saat)")

    geo = sorted((ham / "bolgeler").glob("*.geojson"))[0]
    bolgeler = bolgeleri_oku(geo)
    a = V["aday"]
    tum_secilen, izgaralar = [], {}
    with Pool() as havuz:
        for b in bolgeler:
            X, Y = izgara(b, a["izgara_m"])
            la, lo = xy_enlemboylam(X, Y)
            sonuc = havuz.map(_tara, list(zip(la.tolist(), lo.tolist())), chunksize=8)
            noktalar = []
            for x, y, lat, lon, (z0, o) in zip(X, Y, la, lo, sonuc):
                eg = _egim(lat, lon)
                noktalar.append({"x": float(x), "y": float(y), "lat": float(lat), "lon": float(lon),
                                 "zemin_m": round(z0, 1), "egim_derece": round(eg, 1), **o})
            izgaralar[b["id"]] = noktalar
            uygunlar = [p for p in noktalar if p["egim_derece"] <= a["en_buyuk_egim_derece"]]
            sec = _sec(uygunlar, a["en_az_aralik_m"], a["bolge_basina"])
            for i, p in enumerate(sec, 1):
                p["id"] = f"{b['id']}__{i}"
                p["bolge"] = b["id"]
                tum_secilen.append(p)
            print(f"  {b['ad']:<22} {len(noktalar):5d} nokta, {len(uygunlar):5d} eğim uygun, "
                  f"en iyi enerji %{max(p['enerji_yuzde'] for p in uygunlar):.1f} "
                  f"dünya %{max(p['dunya_yuzde'] for p in uygunlar):.1f}  ({time.time()-t0:.0f} s)")

    # İnce ufuklar: 0.25°, 2 m ve 10 m; tüm efemeris aralığı için metrikler.
    adim = V["ufuk"]["ince_adim_derece"]
    yukseklikler = V["ufuk"]["gozlemci_yukseklikleri_m"]
    ufuklar = np.zeros((len(tum_secilen), len(yukseklikler), int(360 / adim)), np.float32)
    yillar = sorted({datetime.fromtimestamp(int(t), timezone.utc).year for t in ef["zaman_unix"]})
    yillar = [y for y in yillar if len(_yil_maskesi(ef["zaman_unix"], y)) > 8000]
    for i, p in enumerate(tum_secilen):
        p["metrik"] = {}
        for j, h in enumerate(yukseklikler):
            az, u = ufuk_profili(_DEM, p["lat"], p["lon"], h, adim, _MES)
            ufuklar[i, j] = u
            for y in yillar:
                k = _yil_maskesi(ef["zaman_unix"], y)
                s = seriler(p["lat"], p["lon"], p["zemin_m"], h, az, u, ef["gunes_km"][k], ef["dunya_km"][k])
                p["metrik"][f"{y}_{int(h)}m"] = ozet(s)
    print(f"İnce ufuklar tamam ({time.time()-t0:.0f} s)")

    cikti = {
        "olusturma": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metrik_yili_tarama": yil,
        "yillar": yillar,
        "gozlemci_yukseklikleri_m": yukseklikler,
        "ufuk_adim_derece": adim,
        "bolgeler": [{k: v for k, v in b.items() if k != "halkalar_xy"} for b in bolgeler],
        "izgara": {k: [[round(p["lat"], 5), round(p["lon"], 5), p["enerji_yuzde"], p["dunya_yuzde"],
                        p["egim_derece"]] for p in v] for k, v in izgaralar.items()},
        "noktalar": tum_secilen,
    }
    (islenmis_klasoru() / "adaylar.json").write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
    np.savez_compressed(islenmis_klasoru() / "ufuklar.npz", ufuk=ufuklar,
                        kimlik=np.array([p["id"] for p in tum_secilen]))
    print(f"Bitti: {len(tum_secilen)} nokta ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
