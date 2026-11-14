# Görev: "Ay İniş Navigatörü" canlı görev simülasyonu prototipi

Bu dosyayı baştan sona oku, sonra **durmadan** uygula. Bana soru sorma; emin olmadığın
yerde makul bir karar ver ve DEVIR_NOTU.md'ye "varsayım" diye yaz. 45–60 dakika
çalışabilirsin. İşin sonunda tek bir yayımlanmış Artifact linki ve birkaç dosya olacak
(bkz. §9).

---

## 1. Bağlam

NASA Space Apps Challenge 2026, 14–15 Kasım, 48 saat, 3 kişilik takım. Konu: Ay güney
kutbunda, Artemis III'ün 9 aday iniş bölgesinde, bir iniş noktası ve tarih için
**güç (Güneş)** ve **Dünya'ya doğrudan iletişim (Dünya'nın görünmesi)**.

Kutupta Güneş ufkun sadece 1–2° üstünde/altında dolaşır; Dünya da ufukta inip çıkar.
Bu yüzden sonuç tamamen **gerçek arazi ufkuna** bağlıdır. Biz bu ufku NASA'nın LOLA
yükseklik verisinden hesaplıyoruz. Ufku düz sayan bir hesap tamamen farklı sonuç verir:
bu fark ürünün "neden biz" argümanı.

**Esin kaynakları (kopyalama, esinlen):**
- NASA SVS 5228 "Lunar South Pole Illumination with Earth and Sun": gerçek arazide
  ufku sıyıran Güneş, araziyi süpüren uzun gölgeler, ufukta inip çıkan Dünya. Ama o
  **önceden çekilmiş tek bir video**. Biz aynı sahneyi **canlı, her bölgede, her
  tarihte** yapıyoruz. Jüriye cümlemiz bu.
- Elite Dangerous / Evochron: **kokpit göstergeleri (HUD) dili**, yarı saydam paneller,
  gökyüzü radarı, görev brifingi panosu. Sadece görsel dil; uçuş, gemi kontrolü, oyun
  mekaniği YOK. Kullanıcı bir pilot değil, **görev kontrolcüsü**.
- Safran/Skydel GNSS simülatörleri: **sky plot** (gökyüzü kutup grafiği) ve "what-if"
  senaryo mantığı: parametreyi değiştir, sonucu anında gör.

Hesap çekirdeği Python'da, bitmiş ve testli. Senin işin **görünen ürün**. Python
koduna dokunma, GitHub'a hiçbir şey gönderme.

---

## 2. Önce oku

Klasör: `C:\Users\umutc\OneDrive\Desktop\projeler\NASASPACE`

1. `ILERLEME.md`: proje durumu ve ilk sonuçlar
2. `tasarim/veri/README.md`: **gerçek veri dosyaları ve formatları** (en önemlisi)
3. `tasarim/veri/sites.json`: 9 noktanın gerçek sonuçları
4. `ay-inis-navigatoru/docs/img/*.png`: mevcut grafikler

---

## 3. Ürün kurgusu: üç sahne, tek zaman çizgisi

### Sahne 1: Görev Brifingi (açılış ekranı)
- Kutup haritası: `polar_map.png` arka plan, üstünde 9 bölge poligonu ve her bölgedeki
  iniş noktası. Kutup (0,0) merkezde.
- Elite görev panosu gibi **bölge kartları**: ad, güneşli %, Dünya % (1° anten payıyla),
  en uzun karanlık (gün). Sıralama seçenekleri: "En çok güç", "En uzun iletişim",
  "En kısa karanlık", "Dengeli" (dengeli = normalize edilmiş üçünün ortalaması,
  formülü ekranda küçük yaz).
- Kart seçince "İNİŞE BAŞLA" tuşu.

### Sahne 2: İniş sekansı (8–10 sn, kullanıcı kontrol etmez)
- Kamera yörünge yüksekliğinden seçili noktaya doğru alçalır, arazi belirir, iniş
  aracının yanında durur. HUD panelleri sırayla açılır ("GÜÇ ÇEVRİMİÇİ", "DÜNYA
  BAĞLANTISI ARANIYOR…"). Atla tuşu olsun.

### Sahne 3: Görev Kokpiti (ana ekran)
**3D sahne (three.js):**
- **Arazi:** `terrain.bin`, 501×501, 40 m aralık, 20×20 km, nokta merkezde. Düzlem mesh,
  z = yükseklik. Gri-bej regolit malzemesi, dikey abartı yok (gerçek ölçek; istersen
  1×/2× tuşu, varsayılan 1×).
- **Uzak dağlar:** `horizon.json`'daki 360° ufuk profilinden bir **siluet halkası**.
  Noktanın etrafında sabit bir yarıçapta (ör. 30 km), her azimutta yükseklik =
  R·tan(ufuk açısı). Bu, gözlemcinin noktasından bakınca gerçek ufku verir.
  Kuşbakışı kamerada halka duvar gibi görünür: kamera yükselince soldur.
- **Güneş:** DirectionalLight, yönü saatlik verideki `sun_alt_deg`/`sun_az_deg`'den.
  Gökte görünen disk de çiz (açısal yarıçap ~0.27°, bloom/parlama hafif).
  Gölgeler açık; düşük açıda uzun gölgeler ana görsel etki. Shadow camera'yı 20 km
  araziye göre ayarla, mapSize 4096, bias'ları düşük açı için ayarla.
- **Işığın doğruluğu:** 3D gölge haritası sadece 20 km'lik araziyi bilir, uzak dağları
  bilmez. Bu yüzden **noktanın ışıkta olup olmadığı veriden gelir**
  (`sun_visible_fraction`). Güneş ışığının şiddetini bu değerle çarp (0 → tamamen
  karanlık, 0.5 → yarı). Böylece HUD ile sahne birbirini yalanlamaz.
- **Dünya:** gerçek yönde (`earth_alt_deg`/`earth_az_deg`), açısal yarıçap ~0.95°, mavi
  küre. **Aynı Güneş ışığıyla aydınlansın**, evresi (hilal/dolunay) kendiliğinden doğru
  çıkar; `earth_illuminated_fraction` ile kontrol edebilirsin. Dünya'nın gökte küçük
  bir halka/sekiz çizerek salınması (librasyon) gerçek veride var: izini silik çiz,
  güzel bir detay.
- **İniş aracı:** prosedürel basit model (gövde, 4 bacak, güneş paneli, çanak anten).
  Harici model dosyası yok. Panel ışık aldıkça parlasın. Dünya görünürken antenden
  Dünya'ya ince bir **iletişim ışını**; arazi araya girince kesilsin, kırmızı uyarı.
- **Kameralar:** (a) yörünge/kuşbakışı (OrbitControls), (b) **"Astronot gözü"**:
  noktada 2 m yükseklikte birinci şahıs, fareyle etrafına bak. Güneş'in ufku sıyırıp
  Dünya'nın dağın arkasından doğduğunu burada görürüz. En güçlü an bu.
- **Gökyüzü:** siyah, çok soluk yıldızlar (abartı yok, Ay'da Güneş varken yıldız
  pek görünmez).

**Koordinatlar:** x = doğu, y = kuzey, z = yukarı (three.js'e çevirirken dikkat).
Gök cismi yönü: `(cos(alt)·sin(az), cos(alt)·cos(az), sin(alt))`, az kuzeyden saat
yönünde. Ufuk profili de aynı azimut kuralını kullanıyor.

**HUD (Elite esintili, 3D'nin üstünde):**
- **GÜÇ:** batarya %, anlık panel girişi, "karanlığa kalan süre / ışığa kalan süre".
- **İLETİŞİM:** Dünya bağlantısı VAR/YOK, ufkun kaç derece üstünde (`earth_margin_deg`).
  Pay 1°'nin altına inince sarı, 0'ın altında kırmızı. "Bağlantının kesilmesine kalan
  süre".
- **GÖKYÜZÜ RADARI (sky plot):** kutup grafiği; merkez = başucu değil, **ufka yakın
  bölge büyütülmüş** olsun (ör. yükseklik −5°…+15° arası, doğrusal değil). Ufuk
  profili dolu bir "arazi maskesi" olarak çizili; üstünde Güneş ve Dünya'nın anlık
  konumu ve son 30 günlük izi. Bu grafik HUD'un kalbi: neden karanlık olduğunu tek
  bakışta açıklar.
- **GÖREV SAATİ:** tarih (UTC) ve "GÖREV GÜNÜ n".
- **OLAY AKIŞI:** `events_2027.json`'dan, Türkçe cümlelerle ("Gün 41 · Güneş dağın
  arkasına girdi · 14.3 gün karanlık"). Uzun karanlıklar vurgulu. Güneş ufku
  sıyırırken 1–2 saatlik aç/kapa titreşimleri var: 6 saatten kısa durumları
  birleştir (bkz. veri/README.md).

**Zaman kontrolü (alt şerit):**
- Oynat/durdur, hız (1 saat/sn, 1 gün/sn, 1 hafta/sn), kaydırıcı (2027 tüm yıl),
  "sonraki olaya atla".
- Kaydırıcının üstünde iki ince yıllık şerit: Güneş görünür (sarı), Dünya görünür (mavi).
  Uzun karanlıklar şeritte okunur.
- Görev başlangıcı seçilebilsin: kaydırıcıda "iniş günü" işareti; batarya oradan başlar.

### Canlı "what-if" panelleri (Safran mantığı, gerçek hesap tarayıcıda)
- **Anten maskesi** kaydırıcısı (0°–3°): Dünya görünür % ve en uzun kesinti,
  `earth_margin_deg > maske` ile **canlı yeniden hesaplanır**. Malapert'te 0° → %100,
  1° → çok daha düşük: bu jüriye gösterilecek en dürüst an.
- **Batarya simülasyonu:** üç kaydırıcı: kapasite (kWh), panel gücü (kW), tüketim
  (kW). Her saat: `batarya += panel·sun_visible_fraction·1h − tüketim·1h`, 0 ile
  kapasite arasında kırp. Sıfıra inerse olay akışına "GÖREV DURDU" düşer, HUD kırmızı.
  Sonuç: "Bu ayarlarla görev X gün sonra durur / yıl boyu hayatta kalır".
  **Gerçek bir aracın değerlerini bilmiyoruz:** varsayılanları yuvarlak sayılar seç
  ve panelde açıkça "örnek değer, gerçek araç verisi değil" yaz. 18 günlük karanlığın
  bataryayı bitirdiğini gösterecek kadar küçük bir varsayılan kapasite seç.

### "Düz ufuk / Gerçek arazi" tuşu (kanıt anı)
- Basınca: ufuk maskesi 0°'ye iner, siluet halkası ve arazi gölgeleri kalkar, tüm
  rakamlar `sites.json` → `flat_horizon` değerlerine geçer. Yan yana büyük karşılaştırma
  kartı: "Düz ufuk: Güneş %X · Dünya %Y → Gerçek arazi: …" (değerler `sites.json`'dan).
  Rakamlar sayaç gibi aksın.
- Not: düz ufuk modunda da Güneş/Dünya serileri aynı; sadece ufuk 0°. Batarya ve
  anten hesabını bu modda `sun_alt`/`earth_alt`'tan yap (ufuk = 0).

### Sade mod
Bir tuşla HUD sadeleşir: terim yok, 3 büyük rakam ve 1 cümle ("Bu noktada araç yılın
%66'sında güneş alır ama bir kerede 18 gün karanlıkta kalır."). Halk/öğretmen sunumu
için.

---

## 4. Görsel yön

- Önce `visual-identity` skill'ini kullan; 2 yön düşün, **birini seç ve uygula**
  (durup bana sorma). İkincisini DEVIR_NOTU.md'ye kısaca yaz.
- Anlamsal renkler sabit: Güneş/güç = sıcak sarı-turuncu (yalnız Güneş'e ayrılmış),
  Dünya/iletişim = mavi, uyarı = kırmızı/magenta, HUD çizgileri = soğuk renk
  (açık camgöbeği ya da kırık beyaz). **HUD turuncu olmasın**, Güneş'le karışır.
- Renk körlüğü: bilgi sadece renkle verilmesin (ikon, desen, etiket).
- Koyu tema. Projeksiyonda okunmalı: kritik rakamlar büyük, ince yazı az.
- Kaçın: neon, cam efekti, yıldız bulutlu arka plan, "AI uzay şablonu" görünümü,
  Elite'in logosu/fontu/varlıkları.
- Font: Google Fonts'tan, HUD için dar/teknik bir aile + gövde için okunaklı bir aile.

## 5. Dil

- Bütün arayüz metinleri **Türkçe**. Hepsini tek bir sözlükte topla
  (`strings.tr.json` içeriği; prototipte sayfaya gömülü bir JS nesnesi olarak da
  olabilir, ama tek yerde). Global aşamada İngilizce sadece bu sözlüğe eklenecek.

## 6. Dürüstlük kuralları (ihlal etme)

- **Rakam uydurma.** Bütün bilimsel rakamlar `tasarim/veri/` dosyalarından gelir.
- Ekranın bir köşesinde sabit küçük rozet: "Ön sonuç · NASA aydınlanma haritasıyla
  doğrulama sürüyor". "NASA ile doğrulandı" yazma.
- Dünya için ana rakam **1° anten paylı** değer; 0° değerini ikincil göster. Pay
  çok küçükse (`min_earth_margin_deg` < 0.5) "kritik pay" uyarısı.
- Batarya değerleri "örnek" etiketli.
- Noktalar "örnek iniş noktası" (bölge merkezi çevresindeki en yüksek düz nokta), resmi
  iniş noktası değil. Bunu bölge kartında küçük yaz.
- `sites.json`'da `search_note` dolu olan bölgelerde (Haworth, Mons Mouton Plateau)
  kartta "nokta bölgeyi temsil etmeyebilir" uyarısı göster.
- `ILERLEME.md`'deki eski Malapert rakamları (Dünya %100) başka bir noktaya ait.
  **Sadece `tasarim/veri/` rakamlarını kullan.**
- Kaynaklar (küçük bir "Veri" penceresi): NASA LRO/LOLA (Barker vd. 2023, PGDA ürün 90),
  USGS Artemis III bölgeleri (McClernan 2024, doi:10.5066/P1MEQ6UK), NASA/JPL NAIF
  SPICE (DE421), esin: NASA SVS 5228.

## 7. Teknik

- **Tek HTML Artifact** + yanında veri dosyaları. Önce `artifact-design` skill'ini (veya
  Artifact quickstart'ı) yükle ve kurallarına uy: harici script sadece izinli CDN'lerden
  ve **sabit sürümle** (ör. three.js 0.160.0 cdnjs/jsdelivr), font sadece Google Fonts.
- Veri dosyalarını Artifact'e `files` ile ekle, sayfa göreli yolla `fetch` etsin:
  `veri/regions.json`, `veri/polar_map.png`, `veri/sites.json`,
  `veri/sites/<id>/{horizon.json, series_2027.json, events_2027.json, terrain.json,
  terrain.bin}`. `terrain.bin` için contentType `application/octet-stream`.
  Oturum `NASASPACE` klasöründe çalışıyorsa `files` eşlemesi şöyle:
  `{"veri/regions.json": "tasarim/veri/regions.json", "veri/sites/malapert_massif/terrain.bin":
  {"from": "tasarim/veri/sites/malapert_massif/terrain.bin", "contentType": "application/octet-stream"}, …}`
  (9 bölge × 5 dosya + 3 dosya ≈ 48 dosya, ~14 MB).
  Okuma: `new Float32Array(await (await fetch(url)).arrayBuffer())`.
- Toplam boyut sınırlara uygun (veri ~15–20 MB). Gerekirse sadece seçilen bölgenin
  dosyalarını yükle (tembel yükleme), hepsini baştan değil.
- 3D'de NaN yükseklik olabilir (veri boşluğu): komşu ortalamasıyla doldur.
- Performans: 501×501 mesh rahat. 60 fps hedefle; düşük donanımda gölge kalitesini
  düşür.
- **Yedek:** WebGL açılmazsa (ya da 3D hata verirse) uygulama çökmesin; Brifing, sky
  plot, şeritler ve rakamlar 2D olarak çalışmaya devam etsin. Etkinlikte asıl ürün de bu
  mantıkla yapılacak.
- Telefonda bozulmasın (en azından Brifing ve rakamlar), ama öncelik masaüstü ve
  projeksiyon.
- Etkinlikteki asıl uygulama Vite + TypeScript olacak; kodu modüler fonksiyonlara böl
  (veri yükleme, sahne, HUD, zaman, simülasyon) ki taşınması kolay olsun.

## 8. Çalışma sırası ve kendi kontrolün

1. Oku (§2), görsel yönü seç (§4).
2. Veri yükleme + Brifing ekranı + kutup haritası. Yayımla (ara sürüm).
3. 3D sahne: arazi, siluet halkası, Güneş ışığı ve gölge, Dünya, araç, kameralar.
4. HUD, zaman çizgisi, olay akışı, sky plot.
5. What-if panelleri (anten, batarya), "Düz ufuk / Gerçek arazi" tuşu, sade mod.
6. İniş sekansı ve cilalama. Son yayım.
7. **Kontrol:** tarayıcı otomasyonu varsa (`agent-browser` skill) sayfayı aç, konsol
   hatalarına bak, Brifing / Kokpit / Astronot gözü / Düz ufuk ekranlarının ekran
   görüntülerini al ve gözle kontrol et. Hata varsa düzelt, tekrar yayımla.
   Rakamların `sites.json` ile birebir aynı olduğunu kontrol et.

Ara yayımlar aynı dosya yoluyla yapılsın (aynı link güncellenir).

## 9. Teslim

`NASASPACE/tasarim/` içine:
- `prototip/index.html` (+ gerekiyorsa ayrı js/css), yayımlanmış Artifact linki
- `strings.tr.json`
- `DEMO_AKISI.md`: 3 dakikalık jüri demosu, 6–8 adım: neye tıklanır, ne söylenir, "vay"
  anı nerede (öneri sırası: Brifing → Malapert'e iniş → astronot gözüyle Güneş'in ufku
  sıyırması → zaman atlaması ve 18 günlük karanlık → batarya biter → anten maskesi
  1° → "Düz ufuk" tuşu ile kanıt).
- `DEVIR_NOTU.md`: seçilen görsel yön ve alternatifi, tasarım tokenları (CSS
  değişkenleri), bileşen listesi ve her birinin kullandığı veri alanları, verdiğin
  varsayımlar, bilinen eksikler, "48 saatte kesin / vakit kalırsa" listesi.

Bitince kısa bir özet ver: link, ne çalışıyor, ne çalışmıyor, neyi doğrulayamadın.
