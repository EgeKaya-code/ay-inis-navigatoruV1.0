"""NASA ham verilerini data/raw/ altına indirir (hesapları yeniden çalıştırmak için).

Kullanım:  python scripts/veri_indir.py          # eksik olanları indirir
           python scripts/veri_indir.py --hepsi  # 85°G doğrulama dosyaları dahil

Arayüz bu dosyalara ihtiyaç duymaz. Ayrıntılar: data/README.md.
"""
import sys, urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parents[1] / "data" / "raw"
NAIF = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/"
PGDA = "https://pgda.gsfc.nasa.gov/data/"

DOSYALAR = [
    ("LDEM_80S_80MPP_ADJ.TIF", PGDA + "LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF"),
    ("pgda/AVGVISIB_75S_120M_201608.TIF", PGDA + "MoonIllumination/AVGVISIB_75S_120M_201608.TIF"),
    ("pgda/AVGVISIB_75S_120M_201608_EARTH.TIF", PGDA + "MoonIllumination/AVGVISIB_75S_120M_201608_EARTH.TIF"),
    ("kernels/de440s.bsp", NAIF + "spk/planets/de440s.bsp"),
    ("kernels/moon_pa_de440_200625.bpc", NAIF + "pck/moon_pa_de440_200625.bpc"),
    ("kernels/moon_de440_250416.tf", NAIF + "fk/satellites/moon_de440_250416.tf"),
    ("kernels/naif0012.tls", NAIF + "lsk/naif0012.tls"),
    ("nasa/artemis-iii-landing-region-candidates.jpg",
     "https://www.nasa.gov/wp-content/uploads/2024/10/artemis-iii-landing-region-candidates.jpg"),
]
EK = [
    ("pgda/AVGVISIB_85S_060M_201608.TIF", PGDA + "MoonIllumination/AVGVISIB_85S_060M_201608.TIF"),
    ("pgda/AVGVISIB_85S_060M_201608_EARTH.TIF", PGDA + "MoonIllumination/AVGVISIB_85S_060M_201608_EARTH.TIF"),
]


def indir(ad, url):
    hedef = KOK / ad
    if hedef.exists() and hedef.stat().st_size > 0:
        print(f"var      {ad}")
        return True
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(hedef.suffix + ".part")
    print(f"iniyor   {ad}  <- {url}")
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(gecici, "wb") as f:
            while blok := r.read(1 << 20):
                f.write(blok)
        gecici.replace(hedef)
        return True
    except Exception as e:
        gecici.unlink(missing_ok=True)
        print(f"  HATA: {e}")
        return False


def main():
    liste = DOSYALAR + (EK if "--hepsi" in sys.argv else [])
    hatali = [ad for ad, url in liste if not indir(ad, url)]
    if hatali:
        print("\nİnemeyenler (adres değişmiş olabilir; data/README.md'deki ürün sayfalarından elle indirin):")
        for ad in hatali:
            print("  -", ad)
        print("  PGDA ürün 90: https://pgda.gsfc.nasa.gov/products/90")
        print("  PGDA ürün 69: https://pgda.gsfc.nasa.gov/products/69")
        sys.exit(1)
    print("\nTamam. Bölge sınırları için: python scripts/00_bolgeler.py")


if __name__ == "__main__":
    main()
