# Arayüz yenilikleri (14 Kasım 2026)

Bu sürümde arayüze eklenenler ve nasıl birleştirildikleri. Çalıştırmak için `BASLAT.bat` (http://localhost:8767).
Kaynakta değişiklik yaptıktan sonra `python build.py` ile `index.html` yeniden üretilir; `index.html` elle düzenlenmez.

## Yeni

**Açılış ekranı: dönen Ay** (`src/js/65-globe.js`, `src/js/67-home.js`)
- three.js ile çizilen Ay kendi ekseninde yavaşça döner (hızlandırılmış Ay günü, 1 sn ≈ 12 saat). Fareyle sürükleyince
  kamera Ay'ın çevresinde dolaşır, tekerlek yaklaştırır; yaklaştıkça dönüş durur.
- Küre dokusu: NASA SVS CGI Moon Kit (LROC renk, LOLA yükseklikten üretilmiş kabartma; `vendor/moon_4k.jpg`,
  `vendor/moon_normal_4k.jpg`, 4096×2048). Ekran kartı 4K dokuyu desteklemezse `vendor/moon_1024.jpg` kullanılır.
- 80°G'nin güneyi bu projenin kutup haritası (`veri/polar_map.png`) ve `veri/regions.json` sınırlarıyla, aynı
  stereografik izdüşümde çizilir.
- Uzaktan dokuz bölge tek bir "yaklaş" halkasıdır; yaklaşınca her bölge kodu ve adıyla tıklanır. İpucunda bölgenin
  1. adayının güneşli zamanı, Dünya (1° pay) ve en uzun karanlığı, veri döneminin ortalaması olarak yazar.
- Bir bölgeye tıklayınca kamera ~6 sn'de noktanın ~130 km üstüne iner (Esc: vazgeç), ardından kokpitin iniş sekansı
  sürer. Kokpitteki "Ay" tuşu geri çıkarır.
- Kenarlarda küçük tuşlar: Sunum, Video, Liste (eski brifing ekranı), Karşılaştır, dil, ⓘ; iniş tarihi; bölge listesi.

**Sunum modu** (`src/js/68-present.js`; açılışta P ya da "Sunum")
Sekiz sahne: kutupta Güneş, dokuz bölge, en iyi ve en kötü bölge, düz ufuk ile gerçek arazi, 2 m ile 10 m panel,
"görev 2 hafta kayarsa?", NASA doğrulaması, "şimdi siz seçin". Rakamlar `veri/` dosyalarından okunur.
"Görev 2 hafta kayarsa?" sahnesi Malapert Massif örnek noktası ile 1. adayını, 1 Mart 2027 ve 15 Mart 2027 inişlerinin
ilk 30 günü için tarayıcıda hesaplar (`Sim.windowStats`, anten payı 1°; karşılaştırma ekranıyla aynı hesap).

**Kokpit**
- Gün batımına ve Dünya batımına (ya da doğuşuna) büyük geri sayımlar.
- Panel başlığına tıklayınca panel katlanır; üstteki ▥ tuşu hepsini katlar.
- "Uzman" tuşu: batarya ve belirsizlik kaydırıcıları, Pareto etiketleri ve ağırlık ayarları yalnız açıkken görünür.
- Alt şeritteki sarı uyarı cümlesi yerine ince bir ⓘ tuşu (yöntem ve doğrulama penceresini açar).
- Panorama Güneş ile Dünya'yı birlikte gösterecek şekilde kendiliğinden ortalanır; sürükleyince serbest, çift tık yeniden ortalar.
- Özet rakamlarının yanında dönem (· 2027), karşılaştırma satırlarında "· ilk 30 gün".
- Liste ekranında, harita boyutsuzken yapılan sığdırma yüzünden haritanın siyah açılması düzeltildi.

## Birleştirme notları
- Bu projeye özgü değişiklikler korundu: tanıtım videosu (`btnVideo`, `videoDlg`), `years.json`'daki doğrulama alan adları
  (`sun_0m`, `earth_0m`), metinlerdeki 2026–2028 dönemi ve 80 m arazi ifadeleri.
- Sunumdaki doğrulama sahnesi `sun_0m` / `earth_0m` alanlarını okur.
- Sunum metinleri bu projenin verisine göre yazıldı: arazi çözünürlüğü ve "aynı çözünürlükte karşılaştırma" ifadesi geçmez.
- `BASLAT.bat` artık 8767 portunu kullanır; önceki sürümlerin 8765'te açık kalmış sunucularıyla karışmaz.

## Sınırlar
- Küredeki ışık yönü Ay evresinden yaklaşık hesaplanır (librasyon ve ±1,5° Güneş enlemi yok sayıldı). Ekrandaki rakamların
  hiçbiri küreden gelmez.
- Yaklaştıkça kutup kapağı harita gibi aydınlatılır (görselleştirme tercihi, hesap değil).
- Yalnız yazılımsal WebGL ile denendi; gerçek ekran kartında kare hızı ölçülmedi.
