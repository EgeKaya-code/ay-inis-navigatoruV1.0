# Devir notu: Ay İniş Navigatörü prototipi

> **13 Kasım 2026 akşamı güncellemesi.** Bu notun aşağısı ilk devir halini anlatır; değişenler:
>
> - **Derleme ve sunucu Node istemez:** `python build.py`, `python serve.py` (aynı işi yapan `.mjs` dosyaları duruyor ama `build.mjs` artık güncel değil: sözlükleri `{ tr, en }` olarak gömmüyor).
> - **Yeni modül `src/js/75-compare.js`:** senaryo karşılaştırma ekranı (en fazla 3 sütun; senaryo = nokta + iniş tarihi + anten payı). Hesap `20-sim.js` içindeki saf `windowStats(site, startHour, hours, mask)` fonksiyonunda.
> - **Zaman modeli çok yıllı:** `10-data.js` bir noktanın bütün yıllarını (`veri/years.json`) uç uca ekler; saat sayacı ilk yılın 1 Ocak'ından başlar (`Fmt.setEpoch`). `55-timeline.js` yakınlaştırılabilir bir pencere gösterir (Tümü / Yıl / 90 / 30 gün, tekerlek).
> - **Tek dönem:** kokpitteki bütün rakamlar seçili yılın canlı hesabıdır (`S.D.stats`); 2026–2030 özetleri yalnız brifingde. Aşağıdaki 3. bölümde "Nokta özeti", "Karşılaştırma kartı" ve "Sade mod" satırlarındaki `sites.json` alanları artık kullanılmıyor.
> - **Etiketler:** "Güneşli zaman" = diskin herhangi bir kısmının göründüğü zaman yüzdesi (`sun_any_pct`, canlı hesapta `sunPct`). Disk ağırlıklı değer "güneş enerjisi oranı" (`sun_energy_pct`, `sunEnergyPct`). Dengeli puan enerji oranını kullanmaya devam eder (aday sıra numaraları buna göre üretildi).
> - **Olaylar** artık `events_YYYY.json` dosyasından değil saatlik seriden çıkarılır (aynı eşikler); dosyalar duruyor.
> - **Varsayılan iniş noktası** bölgenin 1. adayı (kartta rakamları görünen nokta); eski örnek nokta çubuktaki "Örnek" tuşunda.
> - **İniş sekansı** yalnız ilk inişte oynar; brifingdeki "İniş sekansını oynat" kutusu her inişte oynatır.
> - **Gözlemci yüksekliği** 0 / 2 / 10 m seçilebilir (Nokta özeti). 3D sahne her zaman 2 m profilini çizer.
> - **Dil:** `strings.en.json` eklendi; sağ alttaki seçici. Çeviride olmayan anahtar Türkçesine düşer. Sade modun sade etiketleri sözlükte `plain` altında.
> - **`check-cards.mjs` artık geçersiz:** kartlar "en iyi / ortanca" yerine tek noktanın rakamlarını gösteriyor; denetim betiği güncellenmedi.
> - **Yayımlanan Artifact güncellenmedi.** Yeni veri dosyaları (2026/2028 serileri, 0 m/10 m profiller) yaklaşık 50 MB ekler.
> - **14 Kasım:** sayfa internetsiz çalışır (three.js 0.160 ve yazı tipleri `prototip/vendor/`; `fetch_vendor.py` indirir, `serve.py` dışarı giden istekleri engelleyen bir kuralla sunar). Belgelerdeki rakamlar `RAKAMLAR.md` dosyasından gelir (`prototip/check_numbers.py`, arayüzden bağımsız hesap).
> - Demo akışı: `DEMO_AKISI.md` (yeniden yazıldı). Doğrulama: `ay-inis-navigatoru/docs/validation/avgvisib_comparison.md`.

*13 Kasım 2026 · prototip, etkinlikteki Vite + TypeScript uygulamasına taşınmak üzere*

**Yayımlanan Artifact:** https://claude.ai/artifact/83EXm55TnPFvXs97h6uMro
(özel; takım arkadaşlarının açabilmesi için sayfanın Share menüsünden paylaşılması gerekir)

---

## 1. Nasıl çalıştırılır

```
cd tasarim/prototip
python fetch_vendor.py  # bir kez: three.js 0.160 ve yazı tiplerini vendor/ altına indirir (sonra internet gerekmez)
python build.py         # src/ → index.html (yerel vendor/ yollarıyla; --cdn: eski CDN adresleri, yayımlanan tek dosya için)
python serve.py         # http://localhost:8765  (veri/ ve vendor/ yollarını sunar; sayfa dışarıya istek yapamaz)
python check_numbers.py # belgelerdeki rakamları veriden yeniden hesaplar → ../RAKAMLAR.md
node pack-terrain.mjs   # terrain.bin → yayin/…/terrain.b64.txt (yalnız Artifact yayımı için; Node gerekir)
```

`index.html` doğrudan `file://` ile açılmaz (fetch çalışmaz); `serve.mjs` kullanın.

| Dosya | İş |
|---|---|
| `strings.tr.json` | Bütün arayüz metinleri (tek sözlük). `build.mjs` sayfaya gömer ve eksik anahtarı uyarır. |
| `prototip/src/markup.html`, `styles.css` | İskelet ve stil |
| `src/js/00-core.js` | `t()`, sayı/tarih biçimleri, Türkçe ek (`%65'inde`), sayaç animasyonu |
| `src/js/10-data.js` | Veri yükleme (tembel, önbellekli) |
| `src/js/20-sim.js` | Tarayıcıdaki hesap: saf fonksiyonlar, DOM yok |
| `src/js/40-scene.js` | three.js sahnesi |
| `src/js/50-skyplot.js`, `55-timeline.js`, `57-pano.js` | 2B çizimler (canvas) |
| `src/js/60-hud.js` | Paneller |
| `src/js/70-briefing.js`, `80-descent.js` | Sahne 1 ve Sahne 2 |
| `src/js/85-tour.js` | Otomatik tur (kendi kendine oynayan demo) |
| `src/js/90-app.js` | Durum nesnesi `S`, eylemler `act`, ana döngü |

Her js dosyası tek bir modül nesnesi döndürür (`Sim`, `Scene`, `HUD`…); Vite'a taşırken her biri bir `.ts` modülü olur. Konsolda `AyInis.S`, `AyInis.act`, `AyInis.Scene` ile denenebilir.

### Yayım tuzağı: ikili dosya sunulmuyor
Artifact `application/octet-stream` (yani `terrain.bin`) kabul etmiyor. Çözüm: `pack-terrain.mjs` float32 baytlarını **kayıpsız** base64 metne çevirir; sayfa önce `terrain.b64.txt`'yi dener, yoksa `terrain.bin`'i okur. `tasarim/veri/` klasörüne dokunulmadı. Vite uygulamasında doğrudan `.bin` kullanılabilir.
Ayrıca 48 dosyayı tek seferde göndermek bağlantıyı kopardı; önce sayfa + Malapert, sonra 4'er bölge gönderildi. Sayfa güncellemesi için yalnız `index.html` yeniden yayımlanır, veri dosyaları yerinde kalır.

---

## 2. Görsel yön

### Seçilen: "Ölçü aleti"
Teodolit, harita kenar çizgisi ve uçuş planı dili. Siyaha yakın soğuk grafit zemin, **kırık beyaz** ince çizgiler, köşe işaretli opak paneller, sıfır köşe yarıçapı, parlama ve cam efekti yok. HUD çizgisi bilerek camgöbeği değil kırık beyaz: camgöbeği Dünya mavisine fazla yakın, anlamı bulandırırdı. Renk yalnız anlam taşır: sarı-turuncu = Güneş/güç, mavi = Dünya/iletişim, kırmızı-macenta = uyarı ve "düz ufuk" modu, limon sarısı taralı = dikkat.
Renk körlüğü: Güneş ☉ (nokta), Dünya ⊕ (artı), karanlık ◐ simgeleri; durumlar yazıyla ("BAĞLANTI YOK"); görünmeyen cisim içi boş ve çarpılı; arazi maskesi taralı; dikkat çipi taralı.
Yazı: **Barlow Condensed** (HUD etiketleri ve büyük rakamlar), **IBM Plex Sans** (gövde), **IBM Plex Mono** (saat, koordinat, eksen). Üçünde de Türkçe karakterler var.

### Alternatif (uygulanmadı): "Kokpit camı"
Elite'e daha yakın: açık camgöbeği çizgiler, kesik köşeli paneller, Saira Condensed ya da Chakra Petch, daha oyunsu. Vazgeçme nedeni: camgöbeği-mavi karışması, neon/"AI uzay şablonu" görünümüne kayma riski, projeksiyonda ince camgöbeği çizgilerin zayıf kalması.

### Tokenlar (`styles.css` → `:root`)
```css
--void:#000000; --bg:#0a0c0d; --panel:#0e1112; --panel-a:rgba(11,14,15,.92); --panel-2:#161a1b;
--rule:#2b3331; --rule-2:#3d4744;                 /* ince çizgiler */
--line:#c9d2cd; --ink:#eef2ee; --ink-2:#a3aeaa; --ink-3:#6f7a76;   /* HUD çizgisi ve yazı */
--sun:#ffb21e;  --earth:#5aa5ff;  --warn:#ff3d6e;  --caution:#e9e04e;
--f-hud:"Barlow Condensed"; --f-body:"IBM Plex Sans"; --f-data:"IBM Plex Mono";
```
Boşluk: 5–10 px panel içi, 8–14 px paneller arası. Köşe yarıçapı 0. Panel = 1 px `--rule` çerçeve + 9 px köşe işaretleri (`--line`; uyarıda `--warn`).
3D malzemeler: regolit `#97938c`, Güneş ışığı `#fff7ea`, Dünya ışığı `#9db8e8`, dolgu `#7f95c0`.

---

## 3. Bileşenler ve kullandıkları veri

| Bileşen | Dosya | Veri alanları |
|---|---|---|
| Kutup haritası | 70-briefing | `regions.json`: `map.bounds_km`, `polygon_ps_km`, `code`, `area_km2`; `sites.json`: `ps_km`; `polar_map.png` |
| Bölge kartları, sıralama | 70-briefing | bölgenin 1. adayı: `terrain.sun_any_pct` (güneşli zaman), `terrain_antenna_1deg.earth_pct`, `terrain.longest_dark_days`; alt satırda `terrain.sun_energy_pct` (güneş enerjisi oranı, "En çok güç" sıralaması bununla) |
| Seçili bölge ayrıntısı | 70-briefing | + `lat`, `lon`, `ground_height_m`, `slope_deg`, `terrain.earth_pct`, `terrain_antenna_1deg.longest_no_earth_days`, `min_earth_margin_deg` |
| İniş sekansı | 80-descent, 40-scene | arazi + harita; panel açılış sırası `data-boot` |
| Arazi ağı | 40-scene | `terrain.json` (`width`, `height`, `spacing_m`), `terrain.bin` |
| Ufuk silueti halkası | 40-scene | `horizon.json`: `elevation_deg`, `distance_km` |
| Güneş diski ve ışığı | 40-scene | `sun_alt_deg`, `sun_az_deg`, şiddet = `sun_visible_fraction` |
| Dünya, evresi, librasyon izi | 40-scene | `earth_alt_deg`, `earth_az_deg`; evre Güneş yönünden çıkar (`earth_illuminated_fraction` ile 0,002 içinde tutuyor) |
| Araç, iletişim ışını | 40-scene | `earth_margin_deg` > maske; kesilme mesafesi `distance_km` |
| Nokta özeti (4 rakam + enerji oranı) | 60-hud, 20-sim (`stats`) | seçili yılın canlı hesabı: güneşli zaman, Dünya (seçili pay), Güneş + Dünya, en uzun karanlık; düz modda aynı yıl düz ufukla |
| GÜÇ paneli | 60-hud, 20-sim | `sun_visible_fraction` (düz modda `sun_alt_deg`'den disk oranı), batarya kaydırıcıları |
| İLETİŞİM paneli | 60-hud, 20-sim | `earth_margin_deg` (düz modda `earth_alt_deg`), maske kaydırıcısı |
| Gökyüzü radarı | 50-skyplot | ufuk profili + Güneş/Dünya alt-az, son 720 saat izi |
| Olay akışı | 60-hud, 20-sim | `events_2027.json` (`sun_*`; maske 0° → `earth_*`, 1° → `earth_1deg_*`); başka maskede ve düz modda seriden üretilir |
| Zaman şeritleri | 55-timeline | saatlik `sunFrac`, `linkUp`, batarya düzeyi |
| Düz ufuk ↔ gerçek arazi kartı | 60-hud (`flatVsTerrain`) | seçili yılın canlı hesabı, ikisi de 0° maske |
| Senaryo karşılaştırma ekranı | 75-compare, 20-sim (`windowStats`) | inişten sonraki 14 / 30 / 90 günün canlı hesabı |
| Sade mod | 60-hud | özetle aynı rakamlar (seçili yıl), tam sayıya yuvarlanmış; etiketler sözlükteki `plain` karşılıklarıyla |
| Kartlardaki mini şerit | 70-briefing | 9 bölgenin `series_2027.json` dosyası (arka planda, sırayla): `sun_visible_fraction`, `earth_margin_deg` > 1 |
| İniş penceresi satırı ve "güvenli iniş" cevabı | 20-sim (`landingScan`), 55-timeline | saatlik Güneş oranı + batarya kaydırıcıları; yılın 365 günü için "o gün inilseydi" |
| "En küçük batarya" cevabı | 20-sim (`minBattery`) | aynı; 10 kWh adımla 600'e kadar |
| Kritik pay satırı | 20-sim (`stats.lowMarginPct`) | `earth_margin_deg`: görünür sürenin yüzde kaçında pay < 1° |
| Şerit ipucu (fareyle) | 55-timeline | o saatin Güneş oranı, bağlantı, iniş penceresi |
| Otomatik tur | 85-tour | olay akışı, en uzun karanlık, düz ufuk / gerçek arazi (seçili yılın canlı hesabı); altyazılar veriden dolar |
| Panorama (yedek) | 57-pano | ufuk profili + alt-az; WebGL gerekmez |

---

## 4. Brif ile veri ayrışan yerler (veri esas alındı)

- **"18 günlük karanlık" yok.** Bu noktada Malapert'in en uzun karanlığı **14,3 gün** (2026–2030 ve 2027'de aynı; 29 Nisan 2027'de başlıyor). 18'e yakın tek rakam düz ufuk varsayımının **17,7 günü**. Demo metni 14,3 ile yazıldı.
- **"Malapert'te 0° → %100" yok.** Malapert'te Dünya 0° maskeyle %81,6, 1° payla %74,3 (2027'de %78,8 → %71,9). "En dürüst an" için doğru bölge **Mons Mouton Plateau**: 2027'de 0° → **%99,4**, 1° → **%81,1**; en uzun kesinti 1,2 → 5,5 gün.
- **Varsayılan batarya** (100 kWh, 2 kW panel, 0,5 kW tüketim) Malapert'te 1 Ocak inişiyle **40,2. günde** biter (1 Şubat'ta başlayan 10,2 günlük karanlıkta). 180 kWh ve üstü veri sonuna (31 Aralık 2028) kadar dayanır (200 kWh'de en düşük %13).
- **Kritik pay uyarısı ayırt etmiyor.** `min_earth_margin_deg` dokuz noktanın hepsinde ≈ 0,00° (Dünya'nın doğup battığı her yerde doğal olarak sıfıra iner), yani uyarı her kartta çıkıyor. Kokpitte bunun yerine ayırt eden bir ölçü gösteriliyor: "görünür sürenin yüzde kaçında pay 1°'den az" (Malapert 2027: %9). Brifing kartında brifteki kural olduğu gibi duruyor; aynı ölçüyü `export_proto.py` 2026–2030 için de üretirse kartlara taşınabilir.

---

## 5. Varsayımlar

1. **Dengeli puan** sabit ölçekli: (güneş enerjisi oranı % + Dünya % (1°) + karanlık puanı) / 3; karanlık puanı = 100 − min(gün, 30)/30 × 100. Dokuz nokta arasında min–max ölçekleme denenmedi çünkü Haworth'un 194 günü diğer sekizini birbirinden ayırt edilemez yapıyor. Formül ekranda yazıyor.
2. **Brifing kartları 2026–2030, kokpit seçili yılın canlı hesabı.** İki dönem birkaç puan ayrışıyor (Malapert örnek nokta, Dünya 1°: %74,3 ve 2027'de %71,9), bu yüzden aynı panelde yan yana gösterilmiyor; "Veri" penceresinde açıklaması var.
3. **Batarya inişte dolu.** İniş günü varsayılan 1 Ocak 2027 00:00; "İnişi bu ana al" ya da tarih alanıyla değişir. Batarya sıfıra inince görev durmuş sayılır (sonra dolsa bile).
4. **Olay birleştirme:** 6 saatten kısa durumlar atılır, aynı durumdaki komşular birleşir; 72 saatten uzun karanlıklar vurgulanır.
5. **Düz ufuk ↔ gerçek arazi kartı** Dünya'yı 0° maskeyle kıyaslar; 1° değeri özet panelinde durur.
6. **Araç**, gözlem noktasının 14 m yanında (Dünya yönünden 35° sağda); astronot gözü tam noktada, 2 m yukarıda. Güneş paneli dikey ve Güneş'in azimutunu izler (kutup için gerçekçi), çanak Dünya'yı izler. Model semboliktir.
7. **Aydınlatmada görünürlük için eklenenler** (fizik değil, projeksiyon için): soluk ortam ışığı, abartılı Dünya ışığı, Güneş yokken soğuk bir dolgu ışığı. Güneş ışığının şiddeti her zaman `sun_visible_fraction`'dan gelir.
8. **Regolit** Lambert + Lommel-Seeliger karışımıyla (%40 / %60) boyanır; yüzey dokusu yordamsaldır (veri değil).
9. **Dünya'nın bulut/kara deseni** temsilidir; evresi gerçektir.
10. **Astronot gözünde** veri "Güneş hiç görünmüyor" diyorsa disk çizilmez (40 m'lik ağ yakın ufku ±0,5° kaçırabiliyor; HUD ile sahne çelişmesin diye).
11. **Düz ufuk modu**: arazi ağı düşeyde 0,0006'ya ezilir, uzak dağ halkası kalkar, düz bir zemin diski gelir.
12. **Büyük veri boşlukları çizilmez.** Sekiz bölgede arazi karesinin köşeleri NaN (%9–13); 3 hücreden derin boşluklar ağdan çıkarıldı (uydurma arazi yerine kesik köşe). Küçük boşluklar komşu ortalamasıyla dolduruldu.
13. **Sayı biçimi Türkçe:** ondalık virgül, yüzde işareti önde (%68,1). İngilizcede 68.1%.
14. **İniş penceresi** her gün için "dolu bataryayla o gün inen araç veri sonuna (31 Aralık 2028) kadar dayanır mı" diye bakar. Dolu bataryayla daha geç inmek hiçbir zaman daha kötü olmadığı için ilk güvenli günden sonrası hep güvenlidir. Sınır: veri sonuna yakın inişler "dayanır" görünür çünkü veri 31 Aralık 2028'de bitiyor.
15. **Aracın gölgesi temsilidir:** Güneş 0,3°'den yüksekken araçtan Güneş'in tersine uzanan, araziye oturan koyu bir şerit (boy = 4,2 m / tan(yükseklik), en çok 450 m). Arazi gölgeleri ise gerçek yükseklik verisinden.
16. **Yüzeydeki küçük kraterler yordamsaldır** (170 m'de bir yinelenen doku); veri değil. 40 m'lik LOLA ağı bu ölçeği göstermez.
17. **Zemin yansıması** (araç gölgede kalan yüzlerinde simsiyah olmasın diye) ve yanıp sönen **işaret ışığı** görsel yardımdır.

---

## 6. Doğrulanan / doğrulanamayan

**14 Kasım 2026 (yerel sunucu, 1440×900; rakamlar `RAKAMLAR.md`):**
- Sayfa internetsiz çalışıyor: three.js 0.160 ve yazı tipleri `vendor/` altında; brifing, karşılaştırma, kokpit ve 3D sahne açıkken 46 ağ isteğinin hepsi localhost.
- Astronot gözü ve otomatik tur üç noktada (Malapert örnek, Haworth aday 1, de Gerlache Rim 2 aday 1), 0 / 2 / 10 m, 2026 / 2027 / 2028 ve iki dilde hatasız; turun altı adımı üç koşuda da tamamlandı.
- Karşılaştırma ekranı ve kokpit rakamları arayüzden bağımsız Python hesabıyla (`check_numbers.py`) aynı.
- Düz ufuk ↔ gerçek arazi kartı (Malapert örnek nokta, 2027, güneşli zaman / Dünya 0° / en uzun karanlık): %51,0 / %67,6 / 17,7 gün ↔ %68,1 / %78,8 / 14,3 gün.
- Malapert örnek nokta, 2027: güneşli zaman %68,1, güneş enerjisi oranı %64,7, Dünya %78,8 (0°) / %71,9 (1°), en uzun karanlık 14,3 gün (343 saat).

**İlk devirde doğrulananlar (12–13 Kasım, eski arayüz; "güneşli" o zaman güneş enerjisi oranıydı):**
- Brifing: 9 kartın 27 rakamı `sites.json` ile birebir (otomatik karşılaştırma). Haworth ve Mons Mouton Plateau uyarıları çıkıyor.
- Kokpit: yörünge, astronot gözü, panorama, düz ufuk, sade mod ekran görüntüleriyle kontrol edildi; konsolda hata yok.
- Karşılaştırma kartı (Malapert, o zamanki tanım: 2026–2030, güneş enerjisi oranı): %50,0 / %69,4 / 17,7 gün ↔ %65,4 / %81,6 / 14,3 gün, `sites.json` ile aynı. Kart artık seçili yılın güneşli zamanını gösteriyor (yukarıda).
- 2027 canlı hesap, bağımsız bir Node hesabıyla aynı: Malapert güneş enerjisi oranı %64,7, Dünya %78,8 (0°) / %71,9 (1°), en uzun karanlık 343 saat.
- Oynatma, boşluk/N kısayolları, olay atlama, iniş günü, batarya ve maske kaydırıcıları, bölge değiştirme.
- WebGL yokken (THREE silinerek denendi) panorama yedeği; 400 px genişlikte yatay taşma yok.
- İkinci tur (13 Kasım): otomatik turun altı adımı, iniş penceresi satırı, iki hızlı cevap (Malapert varsayılanlarıyla 180 kWh ve 31 Temmuz; 180, bağımsız Node hesabıyla aynı; veri 2028 sonuna uzayınca güvenli iniş cevabı "19 Tem 2028 ve sonrası" oldu), kartlardaki mini şeritler, aracın gölgesi. Telefon genişliğinde kokpit panellerinin üst üste binmesi düzeltildi (ilk sürümde vardı, kaydırınca görünüyordu).

**Doğrulanamadı:**
- **Yayımlanan Artifact'in kendisi tarayıcıda açılmadı** (oturum gerekiyor). Yayım başarılı döndü ve dosyalar yüklendi, ama Artifact içinde `veri/` dosyalarının çekildiği ve three.js'in CDN'den geldiği gözle görülmedi. İlk açışta kontrol edin; sorun olursa konsoldaki hata yeterli.
- Gerçek donanımda kare hızı (60 fps hedefi) ve düşük donanım düşürmesi ölçülmedi.
- Dokunmatik kontroller (iki parmakla yakınlaştırma) denenmedi.
- NASA haritalarıyla karşılaştırma sonradan yapıldı (13 Kasım): Yöntem, NASA'nın ortalama görünürlük haritalarıyla aynı çözünürlükte ve aynı koşulda (0 m gözlemci, 54 nokta, 18,6 yıl) ortalama 2,0 puan (Güneş) ve 1,6 puan (Dünya) içinde uyumludur. Uygulamadaki rakamlar 20 m arazi verisi ve 2 m gözlemci kullandığı için haritadan farklıdır (ortalama mutlak fark Güneş'te 3,6, Dünya'da 1,9 puan). Rakamlar: `ay-inis-navigatoru/docs/validation/avgvisib_comparison.md`.

---

## 7. Bilinen eksikler

- Düşey abartı (1×/2×) tuşu yok (brifte isteğe bağlıydı); 2× ufuk verisiyle örtüşmeyeceği için bırakıldı.
- Aracın gölgesi gerçek gölge haritasından değil, temsili bir şeritten geliyor (bkz. varsayım 15): 20 km'lik gölge haritasında bir piksel 1–7 m, araç 3 m.
- Gölge kenarları sığ Güneş açısında yumuşak ve yer yer basamaklı.
- Yakın ufuk (≈ 100 m) 40 m'lik ağda kabaca temsil ediliyor; astronot gözünde Güneş diskinin görünen kısmı veriyle tam örtüşmeyebilir (rakam her zaman veriden).
- Kamera 3 km'den yükseğe çıkınca ufuk halkası söner; 5–24 km arasında kutup haritası belirir. Arada arazi karesi boşlukta durur.
- 880 px'ten kısa ekranda sol sütun kaydırılır (İletişim panelinin alt satırları).
- Telefonda kokpit çalışır ama sıralama basit: sahne, zaman, paneller alt alta.
- `OrbitControls` yerine küçük bir kendi kontrolümüz var (three.js 0.160'ın modülsüz derlemesinde OrbitControls yok). Vite'ta `three/addons` kullanılmalı.
- İngilizce sözlük eklendi (`strings.en.json`); `Fmt.pctLoc` İngilizcede eksiz yüzde yazar.

---

## 8. 48 saat için

**Kesin**
1. Veri köprüsü: `export_proto.py` çıktısı + `10-data.js` (arazi için `.bin` ya da base64 kararı).
2. `20-sim.js`'i TypeScript'e taşı, birim testi yaz (bu dosyadaki Malapert rakamları hazır beklenen değer).
3. Brifing (harita + kartlar) ve 2B çekirdek: gökyüzü radarı, zaman şeritleri, olay akışı, panorama. Bunlar WebGL'siz de ürün.
4. Düz ufuk / gerçek arazi karşılaştırması ve anten maskesi kaydırıcısı (jüri argümanı).
5. Rozet, "Veri" penceresi, uyarılar (dürüstlük kuralları).
6. 3D sahne: arazi + Güneş ışığı/gölge + astronot gözü.

**Vakit kalırsa**
- İniş sekansı, sade mod, batarya simülasyonu, iniş penceresi, otomatik tur (hepsi burada çalışıyor, taşımak kolay). Otomatik tur demo videosu çekmek için de işe yarar.
- Aracın gölgesi, 10 m panel seçeneği (`metrics.10m` hazır), İngilizce sözlük.
- Bölge içinde nokta ızgarası (yalnız tek örnek nokta yerine).
- NASA doğrulaması gelince rozetin metni ve bir "bizim % – NASA %" grafiği.
