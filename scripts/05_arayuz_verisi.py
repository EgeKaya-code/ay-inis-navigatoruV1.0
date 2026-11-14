"""Arayüzün (arayuz/) okuduğu veri paketini bu projenin hesaplarından üretir.

Girdi : LOLA DEM, NASA AVGVISIB haritaları, data/islenmis/{efemeris.npz, adaylar.json},
        data/raw/bolgeler/*.geojson
Çıktı : arayuz/veri/
  regions.json, polar_map.png, sites.json, candidates.json, sensitivity.json, years.json,
  heat/<bölge>.png,
  sites/<nokta>/{horizon.json (2 m), horizon_0m.json, horizon_10m.json,
                 series_<yıl>.json, terrain.json, terrain.bin, terrain.b64.txt}

Nokta seçimi (her bölge):
  örnek nokta : bölge merkezine en yakın, eğimi sınırın altındaki ızgara noktası (kimlik = bölge kimliği)
  adaylar     : tarama ızgarasında eğimi uygun noktalardan, (enerji + Dünya)/2 tarama puanı en yüksek 20 nokta
                (aralarında en az 1 km); bizim modelle 2026–2028 için yeniden hesaplanır ve dengeli puana göre
                sıralanır. İlk 5'in tam veri paketi vardır (<bölge>__c1 … __c5).
Dengeli puan  = (Güneş enerjisi % + Dünya % (1° pay) + karanlık puanı) / 3,
karanlık puanı = 100 − min(en uzun karanlık gün, 30) / 30 × 100.
"""
import base64
import io
import json
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))
from aynav.bolgeler import bolgeleri_oku  # noqa: E402
from aynav.config import ay_yaricapi_m, ham_veri_klasoru, islenmis_klasoru, varsayimlar  # noqa: E402
from aynav.dem import DEM  # noqa: E402
from aynav.gorunurluk import disk_gorunen_kesir, en_uzun_ardisik, yerel_azimut_yukseklik  # noqa: E402
from aynav.projeksiyon import enlemboylam_xy, harita_yonleri, xy_enlemboylam  # noqa: E402
from aynav.ufuk import isin_mesafeleri, ufuk_profili, ufuk_yuksekligi  # noqa: E402

CIKTI = KOK / "arayuz" / "veri"
YILLAR = [2026, 2027, 2028]
DONEM = "2026-01-01 to 2028-12-31 UTC, hourly"
YUKSEKLIKLER = [0, 2, 10]
ADIM = 0.25  # ufuk azimut adımı
KOD = {"peak_near_cabeus_b": "CB", "haworth": "HW", "malapert_massif": "MA", "mons_mouton_plateau": "MP",
       "mons_mouton": "MM", "nobile_rim_1": "N1", "nobile_rim_2": "N2", "de_gerlache_rim_2": "G2",
       "slater_plain": "SP"}
N_TARAMA, N_PAKET, ARALIK_M = 20, 5, 1000.0
HALKALAR_M, HALKA_AZ = [100.0, 300.0], [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
SUN_R_KM = varsayimlar()["gunes"]["yaricap_km"]

_DEM = _EGIM = _G = _D = _MES = None


def r(x, n=3):
    return [round(float(v), n) for v in x]


def karanlik_puani(gun):
    return 100.0 - min(gun, 30.0) / 30.0 * 100.0


def dengeli(m):
    return (m["terrain"]["sun_energy_pct"] + m["terrain_antenna_1deg"]["earth_pct"]
            + karanlik_puani(m["terrain"]["longest_dark_days"])) / 3.0


def _metrik(kesir, dunya_var):
    gunes_var = kesir > 0
    return {
        "sun_energy_pct": 100.0 * float(kesir.mean()),
        "sun_any_pct": 100.0 * float(gunes_var.mean()),
        "earth_pct": 100.0 * float(dunya_var.mean()),
        "sun_and_earth_pct": 100.0 * float((gunes_var & dunya_var).mean()),
        "longest_dark_days": en_uzun_ardisik(~gunes_var) / 24.0,
        "longest_no_earth_days": en_uzun_ardisik(~dunya_var) / 24.0,
    }


def geometri(lat, lon, zemin, h):
    gaz, gel, guz = yerel_azimut_yukseklik(lat, lon, zemin + h, _G)
    daz, del_, _ = yerel_azimut_yukseklik(lat, lon, zemin + h, _D)
    rg = np.degrees(np.arcsin(SUN_R_KM / guz))
    return gaz, gel, rg, daz, del_


def metrikler(lat, lon, zemin, h, az, u):
    gaz, gel, rg, daz, del_ = geometri(lat, lon, zemin, h)
    gk = disk_gorunen_kesir((gel - ufuk_yuksekligi(az, u, gaz)) / rg)
    pay = del_ - ufuk_yuksekligi(az, u, daz)
    duz_gk = disk_gorunen_kesir(gel / rg)
    gorunur = pay[pay > 0]
    return {
        "terrain": _metrik(gk, pay > 0),
        "terrain_antenna_1deg": _metrik(gk, pay > 1.0),
        "flat_horizon": _metrik(duz_gk, del_ > 0),
        "min_earth_margin_deg": float(gorunur.min()) if len(gorunur) else 0.0,
    }


def nokta_kaydi(lat, lon):
    x, y = enlemboylam_xy(lat, lon)
    z0 = float(_DEM.ornekle(np.array([x]), np.array([y]))[0])
    rr, cc = _DEM.satir_sutun(x, y)
    eg = float(_EGIM[int(round(float(rr))), int(round(float(cc)))])
    return {"lat": float(lat), "lon": float(lon), "ps_km": [round(float(x) / 1000, 3), round(float(y) / 1000, 3)],
            "ground_height_m": z0, "slope_deg": eg}


def _tam_metrik(args):
    lat, lon, yukseklikler = args
    k = nokta_kaydi(lat, lon)
    sonuc = {}
    for h in yukseklikler:
        az, u = ufuk_profili(_DEM, lat, lon, float(h), ADIM, _MES)
        sonuc[f"{int(h)}m"] = metrikler(lat, lon, k["ground_height_m"], float(h), az, u)
    k["metrics"] = sonuc
    return k


def _halka(args):
    lat, lon = args
    k = nokta_kaydi(lat, lon)
    az, u = ufuk_profili(_DEM, lat, lon, 2.0, ADIM, _MES)
    m = metrikler(lat, lon, k["ground_height_m"], 2.0, az, u)
    return k, m


def kaydir(lat, lon, mesafe_m, az_deg):
    x, y = enlemboylam_xy(lat, lon)
    kuzey, dogu = harita_yonleri(lon)
    a = np.radians(az_deg)
    d = kuzey * np.cos(a) + dogu * np.sin(a)
    la, lo = xy_enlemboylam(x + d[0] * mesafe_m, y + d[1] * mesafe_m)
    return float(la), float(lo)


def nasa_degeri(yol, lat, lon):
    import rasterio

    x, y = enlemboylam_xy(lat, lon)
    with rasterio.open(yol) as s:
        t = s.transform
        c = int((x - t.c) / t.a)
        rr = int((y - t.f) / t.e)
        return float(s.read(1, window=((rr, rr + 1), (c, c + 1)))[0, 0]) * s.scales[0] * 100.0


def isi_haritasi(bolge, hedef):
    """NASA ortalama Güneş haritasının bölge kutusu: koyu → turuncu."""
    import rasterio

    xy = np.vstack(bolge["halkalar_xy"])
    pad = 1000.0
    with rasterio.open(ham_veri_klasoru() / "pgda" / "AVGVISIB_75S_120M_201608.TIF") as s:
        t = s.transform
        c0 = int(np.floor((xy[:, 0].min() - pad - t.c) / t.a))
        c1 = int(np.ceil((xy[:, 0].max() + pad - t.c) / t.a))
        r0 = int(np.floor((xy[:, 1].max() + pad - t.f) / t.e))
        r1 = int(np.ceil((xy[:, 1].min() - pad - t.f) / t.e))
        v = s.read(1, window=((r0, r1), (c0, c1))).astype(np.float64) * s.scales[0] * 100.0
        sinir = [(t.c + c0 * t.a) / 1000, (t.f + r1 * t.e) / 1000, (t.c + c1 * t.a) / 1000, (t.f + r0 * t.e) / 1000]
    f = np.clip(v / 100.0, 0, 1)[..., None]
    a, b = np.array([0x0A, 0x0C, 0x0D]), np.array([0xFF, 0xB2, 0x1E])
    img = (a + (b - a) * f).astype(np.uint8)
    Image.fromarray(img, "RGB").save(hedef, optimize=True)
    return {"file": f"heat/{hedef.name}", "bounds_km": [round(x, 3) for x in sinir], "width": int(c1 - c0),
            "height": int(r1 - r0), "pixel_m": 120.0, "scale_pct": [0.0, 100.0], "colors": ["#0a0c0d", "#ffb21e"],
            "min_pct": float(v.min()), "median_pct": float(np.median(v)), "max_pct": float(v.max())}


def kutup_haritasi(hedef):
    z = _DEM.yukseklik.astype(np.float64)
    z = np.nan_to_num(z, nan=float(np.nanmean(z)))
    gy, gx = np.gradient(z, _DEM.piksel)
    az, el = np.radians(135.0), np.radians(30.0)
    egim = np.arctan(np.hypot(gx, gy))
    yon = np.arctan2(-gx, gy)
    h = np.clip(np.sin(el) * np.cos(egim) + np.cos(el) * np.sin(egim) * np.cos(az - yon), 0, 1)
    Image.fromarray((h * 225 + 15).astype(np.uint8), "L").resize((1024, 1024), Image.LANCZOS).save(hedef, optimize=True)


def arazi(lat, lon, zemin, klasor):
    """Noktanın çevresinde ±10 km, 80 m aralıklı yerel arazi (z: zemine göre, eğrilik dahil)."""
    yari, aralik = 10000.0, 80.0
    n = int(2 * yari / aralik) + 1
    x0, y0 = enlemboylam_xy(lat, lon)
    kuzey, dogu = harita_yonleri(lon)
    e = np.linspace(-yari, yari, n)
    nn = np.linspace(yari, -yari, n)  # satır 0 = kuzey
    E, N = np.meshgrid(e, nn)
    X = x0 + dogu[0] * E + kuzey[0] * N
    Y = y0 + dogu[1] * E + kuzey[1] * N
    z = _DEM.ornekle(X, Y) - zemin - (E**2 + N**2) / (2 * ay_yaricapi_m())
    z = z.astype("<f4")
    z.tofile(klasor / "terrain.bin")
    (klasor / "terrain.b64.txt").write_text(base64.b64encode(z.tobytes()).decode())
    meta = {"file": "terrain.bin", "dtype": "float32 little-endian", "width": n, "height": n, "spacing_m": aralik,
            "half_size_m": yari, "layout": "row-major; row 0 = north edge, column 0 = west edge; site at the centre",
            "z": "metres relative to the site's ground, curvature included (local up); LOLA 80 m DEM, bilinear",
            "min_m": float(np.nanmin(z)), "max_m": float(np.nanmax(z))}
    (klasor / "terrain.json").write_text(json.dumps(meta))


def _paket(args):
    """Bir noktanın ufukları, yıllık serileri ve arazisi."""
    kimlik, lat, lon, zemin, zaman = args
    klasor = CIKTI / "sites" / kimlik
    klasor.mkdir(parents=True, exist_ok=True)
    ufuk2 = None
    for h in YUKSEKLIKLER:
        az, u, d = ufuk_profili(_DEM, lat, lon, float(h), ADIM, _MES, mesafe_dondur=True)
        kayit = {"observer_height_m": float(h), "azimuth_step_deg": ADIM, "elevation_deg": r(u, 3), "distance_km": r(d, 2)}
        metin = json.dumps(kayit, separators=(",", ":"))
        # 2 m profili horizon.json'dur (arayüz varsayılanı); diğer yükseklikler horizon_<h>m.json
        (klasor / ("horizon.json" if h == 2 else f"horizon_{h}m.json")).write_text(metin)
        if h == 2:
            ufuk2 = (az, u)
    az, u = ufuk2
    gaz, gel, rg, daz, del_ = geometri(lat, lon, zemin, 2.0)
    gk = disk_gorunen_kesir((gel - ufuk_yuksekligi(az, u, gaz)) / rg)
    pay = del_ - ufuk_yuksekligi(az, u, daz)
    # Dünya'nın aydınlık kesri (evre): Dünya'dan Güneş'e ve Ay'a bakan vektörler arasındaki açı.
    es = _G - _D
    em = -_D
    cosa = np.einsum("ij,ij->i", es, em) / (np.linalg.norm(es, axis=1) * np.linalg.norm(em, axis=1))
    aydinlik = (1 + cosa) / 2
    for y in YILLAR:
        b = datetime(y, 1, 1, tzinfo=timezone.utc).timestamp()
        s = datetime(y + 1, 1, 1, tzinfo=timezone.utc).timestamp()
        k = (zaman >= b) & (zaman < s)
        seri = {"start_utc": f"{y}-01-01T00:00:00Z", "step_hours": 1.0, "observer_height_m": 2.0,
                "sun_alt_deg": r(gel[k]), "sun_az_deg": r(gaz[k], 2), "sun_visible_fraction": r(gk[k]),
                "earth_alt_deg": r(del_[k]), "earth_az_deg": r(daz[k], 2), "earth_margin_deg": r(pay[k]),
                "earth_illuminated_fraction": r(aydinlik[k])}
        (klasor / f"series_{y}.json").write_text(json.dumps(seri, separators=(",", ":")))
    arazi(lat, lon, zemin, klasor)
    return kimlik


def main():
    global _DEM, _EGIM, _G, _D, _MES
    t0 = time.time()
    V = varsayimlar()
    ham = ham_veri_klasoru()
    _DEM = DEM.oku(ham / "LDEM_80S_80MPP_ADJ.TIF")
    _EGIM = _DEM.egim_derece()
    _MES = isin_mesafeleri(_DEM.piksel)
    ef = np.load(islenmis_klasoru() / "efemeris.npz")
    zaman = ef["zaman_unix"]
    k = (zaman >= datetime(YILLAR[0], 1, 1, tzinfo=timezone.utc).timestamp()) & \
        (zaman < datetime(YILLAR[-1] + 1, 1, 1, tzinfo=timezone.utc).timestamp())
    zaman = zaman[k]
    _G, _D = ef["gunes_km"][k], ef["dunya_km"][k]
    assert len(zaman) == 26304, len(zaman)

    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / "heat").mkdir(exist_ok=True)
    bolgeler = bolgeleri_oku(sorted((ham / "bolgeler").glob("*.geojson"))[0])
    tarama = json.loads((islenmis_klasoru() / "adaylar.json").read_text(encoding="utf-8"))["izgara"]
    sinir = V["aday"]["en_buyuk_egim_derece"]

    kutup_haritasi(CIKTI / "polar_map.png")
    regions = {"map": {"file": "polar_map.png", "bounds_km": [-304.0, -304.0, 304.0, 304.0],
                       "note": "south polar stereographic, x right, y up, pole at (0, 0); image row 0 = top (max y)"},
               "regions": []}
    secim = {}
    for b in bolgeler:
        halka = b["halkalar_lonlat"][0]
        regions["regions"].append({
            "id": b["id"], "name": b["ad"], "code": KOD[b["id"]], "area_km2": b["alan_km2"],
            "polygon_lonlat": halka,
            "polygon_ps_km": [[round(v / 1000, 3) for v in p] for p in b["halkalar_xy"][0].tolist()],
            "centroid": {"lat": b["merkez_lat"], "lon": b["merkez_lon"]}})
        noktalar = [p for p in tarama[b["id"]] if p[4] <= sinir]
        mx, my = enlemboylam_xy(b["merkez_lat"], b["merkez_lon"])
        xy = {i: enlemboylam_xy(p[0], p[1]) for i, p in enumerate(noktalar)}
        ornek = min(range(len(noktalar)), key=lambda i: np.hypot(xy[i][0] - mx, xy[i][1] - my))
        sirali = sorted(range(len(noktalar)), key=lambda i: -(noktalar[i][2] + noktalar[i][3]))
        aday = []
        for i in sirali:
            if all(np.hypot(xy[i][0] - xy[j][0], xy[i][1] - xy[j][1]) >= ARALIK_M for j in aday):
                aday.append(i)
            if len(aday) == N_TARAMA:
                break
        secim[b["id"]] = (noktalar[ornek], [noktalar[i] for i in aday])
    (CIKTI / "regions.json").write_text(json.dumps(regions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"bölgeler ve harita ({time.time()-t0:.0f} s)")

    with Pool() as havuz:
        # örnek noktalar (2 m ve 10 m) ve adaylar (2 m)
        ornekler = havuz.map(_tam_metrik, [(o[0], o[1], [2, 10]) for o, _ in secim.values()])
        aday_listesi = [(b, p) for b, (_, ps) in secim.items() for p in ps]
        aday_sonuc = havuz.map(_tam_metrik, [(p[0], p[1], [2]) for _, p in aday_listesi], chunksize=4)
        print(f"metrikler: {len(ornekler)} örnek, {len(aday_sonuc)} aday ({time.time()-t0:.0f} s)")

        sites = {"period": DONEM,
                 "site_rule": f"grid point nearest to the region centroid with slope < {sinir:g} deg (LOLA 80 m)",
                 "metric_notes": {"sun_energy_pct": "time-averaged visible fraction of the solar disk",
                                  "sun_any_pct": "time with any part of the Sun above the terrain",
                                  "earth_pct": "time Earth's centre is above the terrain (+ mask)",
                                  "longest_dark_days": "longest spell with no part of the Sun visible",
                                  "flat_horizon": "same Sun/Earth geometry, horizon assumed flat (0 deg)"},
                 "sites": []}
        cand = {"period": DONEM, "observer_height_m": 2.0,
                "rule": {"screen": f"800 m grid inside the region polygon, slope < {sinir:g} deg on LOLA 80 m; "
                                   "screen score = (2027 sun energy % + 2027 Earth %) / 2; best 20 at least 1 km apart",
                         "rank": "our model 2026-2028, balanced score = (sun_energy_pct + earth_pct with 1 deg mask + "
                                 "dark score) / 3, dark score = 100 - min(longest_dark_days, 30) / 30 * 100",
                         "full_package": "best 5 by rank, plus the sample point",
                         "legacy": f"grid point nearest to the region centroid with slope < {sinir:g} deg",
                         "n_screen": N_TARAMA, "n_full": N_PAKET, "min_spacing_m": ARALIK_M, "max_slope_deg": sinir},
                "nasa": {"product": "NASA PGDA product 69, LOLA average visibility maps AVGVISIB_75S_120M_201608 (Mazarico et al. 2011)",
                         "metric": "Sun: average visible fraction of the solar disc; Earth: share of time any part of the disc clears the terrain; ~18.6 years",
                         "maps": {"75S_120M": ["AVGVISIB_75S_120M_201608.TIF", "AVGVISIB_75S_120M_201608_EARTH.TIF"]}},
                "regions": []}
        paketler = []
        pg = ham / "pgda" / "AVGVISIB_75S_120M_201608.TIF"
        pd = ham / "pgda" / "AVGVISIB_75S_120M_201608_EARTH.TIF"
        for b, o in zip(bolgeler, ornekler):
            o.update({"id": b["id"], "region": b["ad"]})
            sites["sites"].append(o)
            paketler.append((b["id"], o["lat"], o["lon"], o["ground_height_m"], zaman))
            adaylar = [c for (bid, _), c in zip(aday_listesi, aday_sonuc) if bid == b["id"]]
            adaylar.sort(key=lambda c: -dengeli(c["metrics"]["2m"]))
            liste = [{"id": b["id"], "legacy": True, "nasa_sun_pct": nasa_degeri(pg, o["lat"], o["lon"]),
                      "nasa_earth_pct": nasa_degeri(pd, o["lat"], o["lon"])}]
            for i, c in enumerate(adaylar, 1):
                kim = f"{b['id']}__c{i}"
                ns, ne = nasa_degeri(pg, c["lat"], c["lon"]), nasa_degeri(pd, c["lat"], c["lon"])
                liste.append({"id": kim, "rank": i, "legacy": False,
                              "package": f"sites/{kim}" if i <= N_PAKET else None,
                              "lat": c["lat"], "lon": c["lon"], "ps_km": c["ps_km"],
                              "nasa_sun_pct": ns, "nasa_earth_pct": ne, "nasa_score": (ns + ne) / 2,
                              "ground_height_m": c["ground_height_m"], "slope_deg": c["slope_deg"],
                              "metrics": {"2m": c["metrics"]["2m"]}})
                if i <= N_PAKET:
                    paketler.append((kim, c["lat"], c["lon"], c["ground_height_m"], zaman))
            cand["regions"].append({"id": b["id"], "region": b["ad"], "nasa_map": "75S_120M",
                                    "heat": isi_haritasi(b, CIKTI / "heat" / f"{b['id']}.png"),
                                    "candidates": liste})
        (CIKTI / "sites.json").write_text(json.dumps(sites, indent=1), encoding="utf-8")
        (CIKTI / "candidates.json").write_text(json.dumps(cand, indent=1), encoding="utf-8")

        # iniş hatası halkaları: paketli her nokta için 100 m ve 300 m, sekiz yön
        isler, anahtar = [], []
        for kim, lat, lon, _, _ in paketler:
            for rr in HALKALAR_M:
                for a in HALKA_AZ:
                    isler.append(kaydir(lat, lon, rr, a))
                    anahtar.append((kim, rr, a))
        halka_sonuc = havuz.map(_halka, isler, chunksize=8)
        print(f"halkalar: {len(isler)} nokta ({time.time()-t0:.0f} s)")
        merkez = {s["id"]: s["metrics"]["2m"] for s in sites["sites"]}
        for reg in cand["regions"]:
            for c in reg["candidates"]:
                if not c["legacy"]:
                    merkez[c["id"]] = c["metrics"]["2m"]

        def ozet(m):
            return {"sun_energy_pct": m["terrain"]["sun_energy_pct"],
                    "earth_1deg_pct": m["terrain_antenna_1deg"]["earth_pct"],
                    "longest_dark_days": m["terrain"]["longest_dark_days"], "score": dengeli(m)}

        sens = {"period": DONEM, "observer_height_m": 2.0, "radii_m": HALKALAR_M, "azimuths_deg": HALKA_AZ,
                "note": "same model and metrics as candidates.json, at points displaced from each packaged point; "
                        f"worst = lowest Sun, lowest Earth (1 deg mask), longest dark, lowest balanced score among the ring points under the slope limit; "
                        f"steep = ring points with slope {sinir:g} deg or more", "regions": {}}
        for kim, _, _, _, _ in paketler:
            bolge = kim.split("__")[0]
            halkalar = []
            for rr in HALKALAR_M:
                ofs = []
                for (kk, r_, a), (kay, m) in zip(anahtar, halka_sonuc):
                    if kk == kim and r_ == rr:
                        ofs.append({"az_deg": a, "lat": kay["lat"], "lon": kay["lon"], "slope_deg": kay["slope_deg"],
                                    "flat": kay["slope_deg"] < sinir, **ozet(m)})
                # en kötü: inilebilecek (eğimi sınırın altındaki) halka noktaları arasında; hiç yoksa hepsi
                duz = [o for o in ofs if o["flat"]] or ofs
                worst = {"sun_energy_pct": min(o["sun_energy_pct"] for o in duz),
                         "earth_1deg_pct": min(o["earth_1deg_pct"] for o in duz),
                         "longest_dark_days": max(o["longest_dark_days"] for o in duz),
                         "score": min(o["score"] for o in duz)}
                med = {k2: float(np.median([o[k2] for o in duz])) for k2 in worst}
                halkalar.append({"radius_m": rr, "worst": worst, "median": med,
                                 "steep": sum(not o["flat"] for o in ofs), "n": len(ofs), "offsets": ofs})
            sens["regions"].setdefault(bolge, {})[kim] = {"center": ozet(merkez[kim]), "rings": halkalar}
        (CIKTI / "sensitivity.json").write_text(json.dumps(sens), encoding="utf-8")

        havuz.map(_paket, paketler, chunksize=1)
        print(f"veri paketleri: {len(paketler)} nokta ({time.time()-t0:.0f} s)")

    dog = json.loads((KOK / "docs" / "dogrulama.json").read_text(encoding="utf-8"))
    years = {"years": YILLAR, "observer_heights_m": YUKSEKLIKLER,
             "validation": {"n": dog["nokta_sayisi"], "period": dog["donem_kisa"],
                            **{k2: dog["ozet"][k2] for k2 in ("sun_0m", "earth_0m", "sun_2m", "earth_2m")}}}
    (CIKTI / "years.json").write_text(json.dumps(years, indent=1), encoding="utf-8")
    print(f"Bitti ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
