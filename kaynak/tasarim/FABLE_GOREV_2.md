# Fable görevi 2: Bölge başına tek nokta yerine aday noktalar

*13 Kasım 2026. Kullanıcı yok, soru sorma; kararları kendin ver ve sonunda yaz.*

## Amaç

Şu an her Artemis III bölgesinde tek bir örnek nokta var (bölge merkezine 6 km içindeki en yüksek düz nokta). Jüri "bölge" derken bu zayıf kalıyor; Haworth ve Mons Mouton Plateau noktaları bölgeyi temsil etmiyor. Hedef:

1. Her bölgede **aday iniş noktaları** bulmak: önce NASA haritasıyla tara, sonra en iyileri bizim modelle ayrıntılı hesapla.
2. Brifing ekranında: poligon içinde NASA aydınlanma ısı haritası, adaylar tıklanabilir noktalar, kartlarda tek rakam yerine **en iyi / ortanca**.
3. Bir adaya tıklayınca kokpit (3D, panolar, olaylar, batarya) o noktayla açılsın.

## Önce oku

- `tasarim/DEVIR_NOTU.md`: prototipin yapısı, veri alanları, varsayımlar
- `ay-inis-navigatoru/scripts/export_proto.py`: mevcut veri üretimi (bunu genişleteceksin)
- `ay-inis-navigatoru/scripts/validate_pgda.py`: NASA haritasını okuma örneği
- `ay-inis-navigatoru/src/lunar_nav/`: hesap çekirdeği (`sites.py`, `horizon.py`, `visibility.py`)
- `tasarim/prototip/src/js/10-data.js`, `70-briefing.js`, `90-app.js`

## Veri ve ortam

- Python: `C:\Users\umutc\.venvs\ay-inis-navigatoru\Scripts\python` (proje kurulu, `lunar_nav` içe aktarılabilir)
- NASA haritaları (PGDA ürün 69, değer = DN × 4e-5, "diskin herhangi bir kısmı görünür" zaman oranı):
  `ay-inis-navigatoru/data/raw/pgda/AVGVISIB_85S_060M_201608.TIF` (+ `_EARTH`), 85S kapsamı dışı için `AVGVISIB_75S_120M_201608.TIF` (+ `_EARTH`). LOLA DEM ile aynı polar stereografik CRS.
- Bölge poligonları: `ay-inis-navigatoru/data/raw/usgs_regions/A3_9regions-lonlat-simplified.geojson`
- 20 m DEM kırpıntıları internetten okunur ve `data/cache`'e yazılır (~10 sn/kırpıntı, ara sıra kısa okuma hatası: `crop_with_retry` kullan).
- Doğrulama sonucu: bizim Güneş rakamımız NASA haritasıyla ort. 2,4 puan içinde; Dünya ufku sıyırdığı yerlerde konuma çok hassas.

## Adımlar

### 1. Veri (`ay-inis-navigatoru/scripts/export_candidates.py`, yeni dosya)

- Her poligon içinde, 20 m DEM'de eğimi `max_slope_deg`'den (assumptions.toml) az olan noktaları al. Aralarında en az ~300 m olacak şekilde seyrelt.
- NASA Güneş ve Dünya haritasından her birinin değerini oku. Puan: export_proto'daki dengeli puanla aynı mantıkta, Güneş + Dünya ortalaması yeterli. Bölge başına en iyi **20** adayı seç.
- Bu 20 aday için bizim modelle (2 m, 2026–2030, export_proto'daki metriklerin aynısı: `terrain`, `terrain_antenna_1deg`, `flat_horizon`) metrik hesapla. Nokta başına ~4 sn.
- Bizim modelle sıralayıp en iyi **5** aday için kokpitin istediği tam paketi üret (horizon, series_2027, events_2027, terrain tile): export_proto'daki fonksiyonları yeniden kullan, kopyalama.
- Mevcut site (export_proto'nun noktası) her bölgede aday listesinde kalsın ve işaretli olsun ki eski demo bozulmasın.
- Isı haritası: her bölge için poligonun sınır kutusunda NASA Güneş haritasını küçük bir PNG olarak çıkar (poligon dışı saydam). Renk: koyu → `--sun` (#ffb21e).
- Çıktı: `tasarim/veri/candidates.json` + `tasarim/veri/sites/<bolge>__c<N>/...` + `tasarim/veri/heat/<bolge>.png`.
  **Var olan `sites.json`, `regions.json` ve `sites/<bolge>/` dosyalarının üzerine yazma.**
- Her adayda NASA değerini de sakla (`nasa_sun_pct`, `nasa_earth_pct`): arayüzde "NASA haritası: %X" olarak gösterilecek.

### 2. Arayüz (`tasarim/prototip/`)

**Başlamadan önce `tasarim/prototip/` klasörünü `tasarim/prototip_yedek_1311/` olarak kopyala** (bu klasör git'te değil).

- Brifing haritası: seçili bölgede ısı haritası, adaylar küçük noktalar (en iyi 5 dolu, diğerleri içi boş), fareyle üstüne gelince 3 rakam.
- Kartlar: "en iyi / ortanca" (20 adayın üstünden), dönem etiketi korunur. Sıralama düğmeleri en iyi adaya göre çalışsın.
- Tam paketi olan bir adaya tıklayınca "İNİŞE BAŞLA" o adayla açılsın. Paketi olmayanlarda yalnız rakamlar.
- Metinler yalnız `tasarim/strings.tr.json`'a eklenir (tek sözlük kuralı, `build.mjs` eksik anahtarı uyarır). Görsel dil: DEVIR_NOTU §2 (ölçü aleti; renk yalnız anlam taşır; köşe yarıçapı 0).
- "Veri ve kaynaklar" penceresine aday seçme kuralını ve NASA haritasının kaynağını ekle.

### 3. Doğrula

- `node build.mjs` uyarısız, `node serve.mjs` ile aç, agent-browser ile 1440×810 ve 400 px genişlikte ekran görüntüsü al, konsolda hata olmasın.
- `DEMO_AKISI.md`'deki 3 dakikalık akış **aynen** çalışmaya devam etmeli (Malapert'in eski noktası ve rakamları: %65,4 / %81,6 / 14,3 gün).
- Kartlardaki rakamları `candidates.json` ile otomatik karşılaştır.
- `ay-inis-navigatoru` testleri geçmeli; yeni betik için en az bir küçük test (seyreltme ya da poligon içi seçim).

### 4. Bitir

- `ay-inis-navigatoru` reposunda commit (yalnız yerel, **push yok**). Mesajın sonuna:
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
- Artifact'i yeniden **yayımlama**; yerelde çalışsın yeter.
- `tasarim/FABLE_SONUC_2.md` yaz: ne yapıldı, verdiğin kararlar, bölge bölge eski nokta ↔ en iyi aday rakamları, doğrulananlar, doğrulanamayanlar, bilinen eksikler. Kısa ve dürüst; bir şey çalışmadıysa açıkça yaz.

### 5. Blender açılış videosu (1–4 bittikten sonra)

Amaç: demo videosunun başına 15 saniyelik, **gerçek veriden** fotogerçekçi bir Malapert sahnesi. AI ile üretilmiş/stilize görüntü kullanma: argümanımız "gerçek arazi, gerçek Güneş".

- **Kurulum:** Blender kurulu değil. `winget install --id BlenderFoundation.Blender -e --accept-source-agreements --accept-package-agreements`. Olmazsa download.blender.org'dan son kararlı sürümün Windows **portable zip**'ini `C:\Users\umutc\Tools\blender\` altına aç. OneDrive klasörüne kurma.
- **Betik:** `tasarim/blender/malapert_render.py`. Arka planda çalışsın: `blender -b -P malapert_render.py -- <args>`.
  - Yakın arazi: `tasarim/veri/sites/malapert_massif/terrain.json` + `terrain.bin` (float32). NaN hücreleri ağdan çıkar.
  - Uzak arazi: ufuk boş kalmasın diye `ay-inis-navigatoru/data/raw/LDEM_80S_80MPP_ADJ.TIF`'ten noktanın çevresinde ~60 km'lik, seyreltilmiş (ör. 240 m) ikinci bir ağ. Ay eğriliğini uygula (yükseklikten d²/2R düş), yoksa uzak dağlar yanlış yükseklikte görünür. Rasterio için venv Python'unu kullanıp ağı önce `.npy`'ye yaz, Blender o dosyayı okusun.
  - Güneş: `series_2027.json`'dan Güneş'in tam göründüğü (`sun_visible_fraction` ≈ 1) ve alçak (gölgeler uzun) bir saat seç. Gerçek `sun_alt_deg` / `sun_az_deg` ile Sun lamp, açısal çap 0,53°. Dünya: aynı saatin `earth_alt_deg` / `earth_az_deg` değeriyle gökyüzünde doğru açısal boyutta (~1,9°) mavi disk; evresi Güneş yönünden. Yön kuralı: azimut kuzeyden doğuya; sahnede kuzeyin hangi eksen olduğunu `40-scene.js` ile tutarlı tut.
  - Malzeme: regolit gri (#97938c), pürüzlü, Lommel-Seeliger'e yakın görünüm (Principled'da yüksek roughness yeterli). Gökyüzü tam siyah, atmosfer/sis yok. Uydurma arazi ayrıntısı ekleme; küçük ölçekli prosedürel doku olursa sonuç notunda yaz.
  - Kamera: 15 sn, 30 fps. ~3 km yükseklikten iniş noktasına süzül, sonunda 2 m göz hizasında Güneş'e doğru dön. Ufuk çizgisi gerçek arazi siluetiyle uyumlu olmalı (`horizon.json` ile kabaca karşılaştır).
  - Önce 960×540 Eevee önizleme (birkaç kare PNG). Bak, düzelt. Sonra 1920×1080 MP4 (H.264). Eevee headless çalışmazsa Cycles + GPU (OptiX/CUDA), düşük örnek + denoise.
  - Son 3 saniyede alt yazı: "Gerçek NASA LOLA arazisi · JPL efemerisi · <tarih saat UTC>" ve küçük not "AI ile üretilmedi".
- Çıktı: `tasarim/blender/malapert_acilis.mp4` + 3 seçme kare PNG. Render 45 dakikadan uzun sürecekse çözünürlüğü ya da örnek sayısını düşür.
- Sonuç notuna: seçilen an, kullanılan veriler, yön/ölçek kontrolü ve render süresi.

## Kurallar

- Rakam uydurma; her rakam veriden gelsin. Emin olmadığın yeri sonuç notunda belirt.
- Kapsam dışına çıkma (İngilizce yok, Vite'a taşıma yok).
- Zaman kısalırsa sıra: 1. veri → 3. doğrula → 2. arayüz (kartlar, sonra harita, sonra tıklanınca kokpit) → 5. Blender.
