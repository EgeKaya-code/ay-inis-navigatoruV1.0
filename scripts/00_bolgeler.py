"""Artemis III aday bölgelerini NASA'nın duyuru görselinden sayısallaştırır.

Kaynak görsel (indirildi 2026-11-14):
  https://www.nasa.gov/wp-content/uploads/2024/10/artemis-iii-landing-region-candidates.jpg
Görsel güney kutup stereografik izdüşümündedir (0° boylamı yukarı). Ölçek çubuğu
(50 km = 180 piksel) ve Güney Kutbu işareti (yeşil yıldız) ile koordinatlara çevrilir.
Kutuların piksel sınırları görseldeki sarı çizgilerin ortasından ölçüldü.

Doğruluk: görsel 0.28 km/piksel; kutu köşeleri yaklaşık ±1 km. USGS'nin resmi
poligonları (doi:10.5066/P1MEQ6UK) erişilebilir olduğunda data/raw/bolgeler/ altına
konup bunun yerine kullanılmalıdır.

Çıktı: data/raw/bolgeler/artemis3_nasa_gorsel.geojson
"""
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "src"))
from aynav.projeksiyon import xy_enlemboylam  # noqa: E402

PIKSEL_KM = 180.0 / 50.0           # ölçek çubuğu
KUTUP = (745.75, 762.40)           # yeşil yıldızın piksel merkezi

# (sol, üst, sağ, alt) – sarı çizgilerin orta hattı, piksel
KUTULAR = {
    "Peak Near Cabeus B": (66.5, 474.5, 138.5, 547.5),
    "Haworth": (556.5, 383.5, 664.5, 491.5),
    "Malapert Massif": (706.5, 288.5, 783.5, 363.5),
    "Mons Mouton Plateau": (921.5, 127.5, 1197.5, 335.5),
    "Mons Mouton": (979.5, 310.5, 1036.5, 367.5),
    "Nobile Rim 1": (1011.5, 332.5, 1083.0, 403.5),
    "Nobile Rim 2": (1272.5, 384.5, 1345.5, 457.5),
    "de Gerlache Rim 2": (536.5, 642.5, 609.5, 715.5),
    "Slater Plain": (961.5, 904.5, 1033.5, 977.5),
}


def piksel_lonlat(px, py):
    """Piksel konumunu (lon, lat) çiftine çevirir."""
    x_m = (px - KUTUP[0]) / PIKSEL_KM * 1000.0
    y_m = (KUTUP[1] - py) / PIKSEL_KM * 1000.0
    lat, lon = xy_enlemboylam(x_m, y_m)
    return [round(float(lon), 5), round(float(lat), 5)]


def main():
    ozellikler = []
    for ad, (s, u, sg, a) in KUTULAR.items():
        koseler = [(s, u), (sg, u), (sg, a), (s, a)]
        halka = []
        for (x1, y1), (x2, y2) in zip(koseler, koseler[1:] + koseler[:1]):
            for t in [i / 8 for i in range(8)]:
                halka.append(piksel_lonlat(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
        halka.append(halka[0])
        ozellikler.append({
            "type": "Feature",
            "properties": {"name": ad, "kaynak": "NASA görseli (28 Ekim 2024), sayısallaştırma 2026-11-14"},
            "geometry": {"type": "Polygon", "coordinates": [halka]},
        })
    hedef = KOK / "data" / "raw" / "bolgeler"
    hedef.mkdir(parents=True, exist_ok=True)
    yol = hedef / "artemis3_nasa_gorsel.geojson"
    yol.write_text(json.dumps({"type": "FeatureCollection", "features": ozellikler}, indent=1), encoding="utf-8")
    print(f"{len(ozellikler)} bölge -> {yol}")


if __name__ == "__main__":
    main()
