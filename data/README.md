# Veri

Ham veriler depoya konmaz (büyükler). Hepsi kamuya açık NASA verisidir ve aşağıdaki
adreslerden yeniden indirilebilir.

**Kopyaların kaynağı ve tarihi.** `kernels/` altındaki DE440 dosyaları, `naif0012.tls` ve `nasa/` görseli bu projede
14 Kasım 2026'da indirildi. Aşağıdakiler önceki çalışmadan (`Nasa_Space_Mokap`) `kaynaklari_ekle.bat` ile kopyalandı;
dosya tarihleri korunmuştur:

| Dosya | Önceki çalışmada indirildiği tarih |
|---|---|
| `LDEM_80S_80MPP_ADJ.TIF` | 9 Kasım 2026 |
| `pgda/AVGVISIB_75S_120M_201608*.TIF`, `pgda/AVGVISIB_85S_060M_201608*` | 13 Kasım 2026 |
| `kernels/de421.bsp`, `kernels/pck00008.tpc` | 9 Kasım 2026 (DE421 kümesi; bu projenin hesapları kullanmaz) |
| `usgs_bolgeler/A3_9regions-lonlat-simplified.*` | USGS resmi bölge poligonları (McClernan 2024, doi:10.5066/P1MEQ6UK; dosya tarihi 3 Aralık 2024) |

`usgs_bolgeler/` bu projenin betiklerine bağlı değildir; `scripts/00_bolgeler.py` hâlâ NASA görselinden sayısallaştırılmış
sınırları kullanır. Resmi poligonlara geçmek, `02`, `04` ve `05` betiklerinin yeniden çalıştırılmasını gerektirir.

`kernels/de440s.bsp` (33 MB) iki projede de yok; `01_efemeris.py`'yi yeniden çalıştırmak için aşağıdaki adresten indirilmelidir.

## data/raw/

| Dosya | Boyut | Kaynak | Ne için |
|---|---|---|---|
| `LDEM_80S_80MPP_ADJ.TIF` | 189 MB | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF (PGDA ürün 90) | Arazi ufku, eğim, harita |
| `pgda/AVGVISIB_75S_120M_201608.TIF` | 83 MB | https://pgda.gsfc.nasa.gov/data/MoonIllumination/ (PGDA ürün 69) | Doğrulama (Güneş) |
| `pgda/AVGVISIB_75S_120M_201608_EARTH.TIF` | 43 MB | aynı | Doğrulama (Dünya) |
| `kernels/de440s.bsp` | 33 MB | https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/ | Güneş/Dünya/Ay konumları |
| `kernels/moon_pa_de440_200625.bpc` | 13 MB | …/generic_kernels/pck/ | Ay'ın yönelimi |
| `kernels/moon_de440_250416.tf` | 19 KB | …/generic_kernels/fk/satellites/ | MOON_ME_DE440_ME421 çerçevesi |
| `kernels/naif0012.tls` | 5 KB | …/generic_kernels/lsk/ | Artık saniyeler |
| `pgda/AVGVISIB_85S_060M_201608*.TIF` (+ `.LBL`) | 59 MB | aynı (60 m, 85°G'nin güneyi) | Önceki çalışmanın doğrulaması |
| `usgs_bolgeler/` | 0.7 MB | https://doi.org/10.5066/P1MEQ6UK | USGS resmi bölge poligonları |
| `nasa/artemis-iii-landing-region-candidates.jpg` | 0.6 MB | https://www.nasa.gov/wp-content/uploads/2024/10/artemis-iii-landing-region-candidates.jpg | Bölge sınırları (sayısallaştırma) |
| `bolgeler/artemis3_nasa_gorsel.geojson` | – | `scripts/00_bolgeler.py` üretir | 9 bölge poligonu |

`kernels/moon_pa_de421_1900-2050.bpc` ve `moon_080317.tf` de indirildi ama kullanılmıyor
(DE421 kümesi; `de421.bsp` NAIF'te artık `a_old_versions/` altında).

## data/islenmis/

| Dosya | Üreten | İçerik |
|---|---|---|
| `efemeris.npz` | `01_efemeris.py` | Saatlik Güneş/Dünya vektörleri, Ay merkezli, km |
| `adaylar.json` | `02_adaylar.py` | Bölgeler, ızgara metrikleri, 45 seçili nokta ve 2027/2028 metrikleri |
| `ufuklar.npz` | `02_adaylar.py` | 45 nokta × (2 m, 10 m) × 1440 azimut ufuk yüksekliği (derece) |

## Biçimler

- DEM yükseklikleri 1737.4 km küresine göre metredir. İzdüşüm: güney kutup stereografik,
  küre R = 1737.4 km, kutupta gerçek ölçek (`+proj=stere +lat_0=-90 +R=1737400`).
- AVGVISIB değerleri int16'dır. Ölçek 4e-5 (GeoTIFF'te `scale`), 0–1 arası kesir.
- Azimut kuzeyden saat yönünde ölçülür. Kutupta "kuzey" kutuptan dışarı doğrudur.

## Atıf (PGDA şartı)

Barker, M. K., et al. (2023). A New View of the Lunar South Pole from the Lunar Orbiter
Laser Altimeter (LOLA). *Planet. Sci. J.* 4, 183. https://doi.org/10.3847/PSJ/acf3e1

Mazarico, E., et al. (2011). Illumination conditions of the lunar polar regions using LOLA
topography. *Icarus* 211, 1066–1081. https://doi.org/10.1016/j.icarus.2010.10.030
