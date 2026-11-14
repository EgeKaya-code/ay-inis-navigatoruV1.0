"""Web uygulaması için veri paketini üretir ve tek dosyalık web/index.html'i derler.

Girdi: data/islenmis/{efemeris.npz, adaylar.json, ufuklar.npz}, docs/dogrulama.json, LOLA DEM
Çıktı: web/index.html (veri gömülü, sunucu gerektirmez)
"""
import base64
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))
from aynav import __version__  # noqa: E402
from aynav.config import ham_veri_klasoru, islenmis_klasoru  # noqa: E402
from aynav.dem import DEM  # noqa: E402

HARITA_YARI_M = 200_000.0  # haritanın kutuptan uzanımı
HARITA_PIKSEL = 900

KAYNAKLAR = [
    {"ad": "LOLA güney kutbu yükseklik haritası (LDEM_80S_80MPP_ADJ)",
     "atif": "Barker, M. K. vd. 2023, PSJ 4:183, doi:10.3847/PSJ/acf3e1; PGDA ürün 90",
     "url": "https://pgda.gsfc.nasa.gov/products/90", "indirilme": "2026-11-14"},
    {"ad": "Ortalama Güneş ve Dünya görünürlük haritaları (AVGVISIB_75S_120M_201608)",
     "atif": "Mazarico, E. vd. 2011, Icarus 211:1066; PGDA ürün 69",
     "url": "https://pgda.gsfc.nasa.gov/products/69", "indirilme": "2026-11-14"},
    {"ad": "Efemeris ve Ay yönelimi (de440s.bsp, moon_pa_de440_200625.bpc, moon_de440_250416.tf, naif0012.tls)",
     "atif": "NASA/JPL NAIF SPICE genel kernel'leri; Park vd. 2021, AJ 161:105",
     "url": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/", "indirilme": "2026-11-14"},
    {"ad": "Artemis III aday bölgeleri",
     "atif": "NASA, 28 Ekim 2024 duyurusu; McClernan 2024, USGS veri yayını, doi:10.5066/P1MEQ6UK",
     "url": "https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/",
     "indirilme": "2026-11-14"},
]


def b64(a: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()


def golgeli_kabartma(dem: DEM) -> tuple[str, float, float]:
    n = int(HARITA_YARI_M / dem.piksel)
    r0 = int((dem.y0 - HARITA_YARI_M) / dem.piksel)
    c0 = int((-HARITA_YARI_M - dem.x0) / dem.piksel)
    z = dem.yukseklik[r0:r0 + 2 * n, c0:c0 + 2 * n].astype(np.float64)
    z = np.nan_to_num(z, nan=np.nanmean(z))
    gy, gx = np.gradient(z, dem.piksel)
    # Işık: alçak açılı, kutup bölgesine özgü yalayan aydınlatma.
    az, el = np.radians(135.0), np.radians(25.0)
    egim = np.arctan(np.hypot(gx, gy))
    yon = np.arctan2(-gx, gy)
    h = np.sin(el) * np.cos(egim) + np.cos(el) * np.sin(egim) * np.cos(az - yon)
    h = np.clip(h, 0, 1)
    g = (h * 205 + 20).astype(np.uint8)
    img = Image.fromarray(g, "L").resize((HARITA_PIKSEL, HARITA_PIKSEL), Image.LANCZOS)
    tampon = io.BytesIO()
    img.save(tampon, "PNG", optimize=True)
    x0 = dem.x0 + c0 * dem.piksel
    y0 = dem.y0 - r0 * dem.piksel
    return "data:image/png;base64," + base64.b64encode(tampon.getvalue()).decode(), x0, y0


def main():
    isl = islenmis_klasoru()
    ef = np.load(isl / "efemeris.npz")
    ad = json.loads((isl / "adaylar.json").read_text(encoding="utf-8"))
    uf = np.load(isl / "ufuklar.npz")
    ufuk = {k: u for k, u in zip(uf["kimlik"], uf["ufuk"])}
    dog_yol = KOK / "docs" / "dogrulama.json"
    dog = json.loads(dog_yol.read_text(encoding="utf-8")) if dog_yol.exists() else None
    if dog:
        dog.pop("noktalar", None)

    dem = DEM.oku(ham_veri_klasoru() / "LDEM_80S_80MPP_ADJ.TIF")
    png, hx0, hy0 = golgeli_kabartma(dem)

    noktalar = []
    for p in ad["noktalar"]:
        u = ufuk[p["id"]]
        noktalar.append({
            "id": p["id"], "bolge": p["bolge"], "etiket": p["etiket"],
            "lat": round(p["lat"], 5), "lon": round(p["lon"], 5),
            "zemin_m": p["zemin_m"], "egim_derece": p["egim_derece"],
            "metrik": p["metrik"],
            "ufuk": [b64(np.round(u[j] * 100).astype(np.int16)) for j in range(u.shape[0])],
        })

    veri = {
        "surum": __version__,
        "olusturma": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "varsayilan_baslangic": "2026-11-14",
        "yukseklikler": ad["gozlemci_yukseklikleri_m"],
        "efemeris": {"t0_unix": int(ef["zaman_unix"][0]), "n": int(len(ef["zaman_unix"])),
                     "gunes": b64(ef["gunes_km"].astype(np.float32).ravel()),
                     "dunya": b64(ef["dunya_km"].astype(np.float32).ravel())},
        "harita": {"png": png, "x0": hx0, "y0": hy0, "genislik_m": 2 * HARITA_YARI_M},
        "bolgeler": ad["bolgeler"],
        "izgara": ad["izgara"],
        "noktalar": noktalar,
        "dogrulama": dog,
        "kaynaklar": KAYNAKLAR,
    }
    sablon = (KOK / "web" / "sablon.html").read_text(encoding="utf-8")
    metin = json.dumps(veri, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = sablon.replace("/*VERI*/", metin)
    (KOK / "web" / "index.html").write_text(html, encoding="utf-8")
    print(f"web/index.html: {len(html)/1e6:.2f} MB, {len(noktalar)} nokta")


if __name__ == "__main__":
    main()
