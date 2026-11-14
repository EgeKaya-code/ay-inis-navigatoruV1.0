# kaynak/: önceki çalışmanın kaynak dosyaları

Bu klasör, bu projenin temel aldığı önceki çalışmanın (`Nasa_Space_Mokap`) kaynak dosyalarını içerir.
`kaynaklari_ekle.bat` ile robocopy kullanılarak kopyalandı; dosyaların **orijinal tarihleri korunmuştur**.
Uygulama (`arayuz/`) ve bu projenin hesapları (`src/aynav`, `scripts/`) bu klasörü okumaz. Klasör, neyin nereden
geldiğini göstermek ve önceki hesapları yeniden üretebilmek için burada.

## Neler var

| Klasör | İçerik | Dosya tarihleri |
|---|---|---|
| `ay-inis-navigatoru/` | Önceki Python hesap projesi (`lunar_nav`): ufuk, efemeris, görünürlük, aday tarama, NASA doğrulaması, testler, belgeler | 9–14 Kasım 2026 |
| `ay-inis-navigatoru/data/cache/` | Bölge başına 20 m/piksel LOLA arazi parçaları ve saatlik efemeris önbellekleri (bu projede yok; buradaki 80 m arazinin daha ince karşılığı) | 9–13 Kasım 2026 |
| `tasarim/` | Önceki arayüz projesi: tasarım ve devir notları, demo akışı, rakam denetimi (`prototip/check_numbers.py`) | 12–14 Kasım 2026 |
| `tasarim/prototip/src/` | Arayüzün, bu projedeki `arayuz/src`'nin türetildiği ilk hali | 12–14 Kasım 2026 |
| `tasarim/veri/` | Önceki veri seti: 20 m arazi ve USGS resmi bölge sınırlarıyla hesaplanmış 54 nokta, 2026–2028 | 12–14 Kasım 2026 |
| `tasarim/blender/` | Tanıtım videosunun Blender betikleri, sahne verisi ve kareleri (videonun kendisi `arayuz/medya/` altında) | 13 Kasım 2026 |
| `tasarim/dogrulama_1311/`, `dogrulama_1411/` | Arayüzün 13 ve 14 Kasım tarihli ekran görüntüleri | 13–14 Kasım 2026 |

NASA ham verileri ayrıca `data/raw/` altına kopyalandı (bkz. `data/README.md`).

## Geçmiş

Önceki çalışmanın git geçmişi `Nasa_Space_Mokap` klasöründe duruyor (buraya kopyalanmadı). Özeti:

**ay-inis-navigatoru** (hesap)
| Tarih | Yazar | Commit |
|---|---|---|
| 09.11.2026 23:13 | Umutcan Kırımlı | Python core: DEM access, horizon profiles, Sun/Earth ephemeris |
| 10.11.2026 00:00 | Umutcan Kırımlı | Point metrics: sunlight, Earth visibility, longest dark and comm gap |
| 13.11.2026 11:58 | Umutcan Kırımlı | Regions from USGS polygons; prototype data exporter |
| 13.11.2026 12:11 | Umutcan Kırımlı | Validate against NASA LOLA average illumination maps (PGDA 69) |
| 13.11.2026 13:31 | Umutcan Kırımlı | Candidate landing points per region: NASA map screening + own model |
| 13.11.2026 13:52 | Umutcan Kırımlı | export_candidates: write after every region, --missing to resume |
| 13.11.2026 17:44 | Ege | Yedek: teslim alınan çalışma ağacındaki commit edilmemiş değişiklikler |
| 13.11.2026 22:58 | Ege | DE440/SPICE ephemeris, extra years, 0 m and 10 m horizons, AVGVISIB comparison |
| 14.11.2026 13:36 | Ege | README and docs/validation: validation result, sunlit time vs solar energy fraction |

**tasarim** (arayüz)
| Tarih | Yazar | Commit |
|---|---|---|
| 13.11.2026 17:44 | Ege | Yedek: prototipin teslim alındığı hali (13 Kasım 2026) |
| 13.11.2026 22:43 | Ege | Senaryo karşılaştırma ekranı, ortak pencere, tarih davranışı, kart rakamları |
| 13.11.2026 22:58 | Ege | Çok yıllı veri (2026–2028, DE440), gözlemci yüksekliği, sade mod, İngilizce |
| 14.11.2026 13:30 | Ege | three.js ve yazı tipleri yerel; 3D astronot görünümü ve otomatik tur düzeltmeleri |
| 14.11.2026 13:36 | Ege | Rakamlar ve metinler: yeni "güneşli zaman" tanımı ve doğrulama ifadesi |

## Kopyalanmayanlar

- İki git geçmişi (`.git`), Python sanal ortamı (`.venv`) ve önbellekler: yeniden kurulabilir ya da Mokap'ta duruyor.
- Google Drive zip'leri (projenin kendi kopyası) ve iki eski prototip yedeği (`prototip_yedek_1311`, `1311b`).
- `tasarim/prototip/vendor`, `prototip/yayin`, `prototip/index.html` (derlenmiş çıktı ve kütüphane kopyaları; karşılıkları `arayuz/` altında).
