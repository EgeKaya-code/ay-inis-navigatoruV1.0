# Ay İniş Navigatörü

Ay'ın güney kutbunda bir iniş noktası ve tarih seç: Güneş'in ve Dünya'nın gerçek
arazi ufkunun üstünde olup olmadığını saat saat gör. Güç (aydınlanma) ve Dünya ile
doğrudan iletişim pencerelerini karşılaştır.

**Proje başlangıcı: 14 Kasım 2026.** Kod, veri indirmeleri ve tüm hesaplar bu tarihte yapıldı.

## Neden gerçek arazi?

Kutupta Güneş ufkun yalnızca 1–2° üstünde dolaşır. Düz ufuk varsayımı bu yüzden yanlış
sonuç verir. Bu proje her noktanın 360° arazi ufkunu LRO/LOLA yükseklik verisinden,
300 km uzağa kadar ve Ay'ın eğriliğini hesaba katarak çıkarır.

## Doğrulama

160 rastgele noktada (84°G–90°G) yöntem, NASA'nın 18.6 yıllık ortalama görünürlük
haritalarıyla (PGDA ürün 69, Mazarico vd. 2011) aynı koşullarda karşılaştırıldı
(yüzeyde 0 m gözlemci, diskin herhangi bir kısmı görünürse "görünür"):

| | Ortalama mutlak fark | Ortalama fark | Korelasyon |
|---|---|---|---|
| Güneş | 1.14 puan | −0.60 puan | 0.990 |
| Dünya | 0.71 puan | −0.05 puan | 0.997 |

Uygulamadaki rakamlar 2 m gözlemci içindir. Bu koşulda fark Güneş'te 1.77, Dünya'da
0.81 puandır. Ayrıntı: `docs/dogrulama.md`, `docs/dogrulama.png`.

## Klasörler

```
arayuz/                   ANA UYGULAMA (brifing, 3D kokpit, karşılaştırma, tanıtım videosu)
  BASLAT.bat              çift tıkla: yerel sunucuyu açar, tarayıcıda http://localhost:8767
  serve.py, build.py      yerel sunucu ve tek sayfa derleyici
  src/                    arayüz kaynağı (markup, stil, JavaScript)
  strings.tr.json, .en    arayüz metinleri (Türkçe, İngilizce)
  vendor/                 three.js, yazı tipleri ve Ay dokuları (internetsiz çalışma)
  medya/                  Blender tanıtım videosu
  veri/                   bu projenin hesaplarından üretilen veri paketi (05 betiği)
config/varsayimlar.toml   tüm modelleme varsayımları, kaynaklarıyla
kaynak/                   önceki çalışmanın kaynak dosyaları: kod, 20 m arazi, eski veri seti, notlar, Blender (bkz. kaynak/OKU.md)
kaynaklari_ekle.bat       kaynak/ ve data/raw/ klasörlerini Nasa_Space_Mokap'tan doldurur (tarihleri korur)
src/aynav/                testli Python hesap çekirdeği
  projeksiyon.py          güney kutup stereografik izdüşümü
  dem.py                  LOLA DEM okuma, çift-doğrusal örnekleme, eğim
  ufuk.py                 arazi ufku profili
  efemeris.py             Güneş/Dünya konumları (SPICE, DE440)
  gorunurluk.py           görünürlük serileri ve özet metrikler
  bolgeler.py             Artemis III bölgeleri ve bölge içi ızgara
scripts/
  00_bolgeler.py          bölge sınırlarını NASA görselinden sayısallaştırır
  01_efemeris.py          saatlik Güneş/Dünya tablosu (2026-01-01 – 2029-01-01)
  02_adaylar.py           9 bölgede ~6000 noktayı tarar
  03_dogrulama.py         NASA haritalarıyla karşılaştırma
  04_web_paketi.py        web/index.html (tek dosyalık sade sürüm)
  05_arayuz_verisi.py     arayuz/veri/ paketini üretir (54 nokta, 2026–2028)
tests/                    pytest
web/                      tek dosyalık sade sürüm (sunucu gerekmez)
data/                     indirilen ham veri ve ara çıktılar (bkz. data/README.md)
```

## Çalıştırma (Windows)

Uygulamayı açmak: `arayuz\BASLAT.bat` dosyasına çift tıkla (Python yüklü olmalı).

Hesapları baştan üretmek:

```
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
.venv\Scripts\python scripts\00_bolgeler.py
.venv\Scripts\python scripts\01_efemeris.py
.venv\Scripts\python scripts\02_adaylar.py
.venv\Scripts\python scripts\03_dogrulama.py
.venv\Scripts\python scripts\04_web_paketi.py
.venv\Scripts\python scripts\05_arayuz_verisi.py
cd arayuz && ..\.venv\Scripts\python build.py
```

Ham veriler `data/raw/` altında olmalı (bkz. `data/README.md`). Hepsini yeniden üretmek
iki çekirdekli bir makinede yaklaşık 6 dakika sürer.

## Arayüz

- **Açılış: dönen Ay.** Kendi ekseninde yavaşça dönen, fareyle çevrilip tekerlekle yaklaştırılan 3D Ay. Güney kutbu
  bu projenin LOLA kabartma haritası ve 9 bölgenin sınırlarıyla çizilir. Bir bölgeye tıklayınca kamera noktanın ~130 km
  üstüne iner, ardından kokpitin iniş sekansı başlar. Bölge ipucu, bölge listesi, iniş tarihi ve video kenarlarda küçük tuşlarda.
- **Sunum modu** (açılışta P ya da "Sunum"): sekiz sahnelik rehberli anlatım. Rakamların hepsi veri dosyalarından okunur;
  "Görev 2 hafta kayarsa?" sahnesi tarayıcıda karşılaştırma ekranıyla aynı hesapla canlı üretilir.
- **Liste (brifing):** kutup haritasında 9 bölge, NASA ısı haritası ve aday noktalar. Bölge kartları
  güç, iletişim, karanlık ya da dengeli puana göre sıralanır. Her bölgede bir örnek nokta ve
  20 aday vardır. Bunların 5'i tam iniş paketiyle gelir ve 100/300 m iniş hatası halkaları gösterilir.
- **Kokpit:** 3D arazi (yörünge, astronot gözü, panorama), gökyüzü radarı, güç ve batarya
  modeli, iletişim paneli, olay akışı, gerçek arazi ve düz ufuk karşılaştırması, otomatik tur, sade mod.
  Gün batımına ve Dünya batımına büyük geri sayımlar; katlanır paneller; batarya, belirsizlik, Pareto ve ağırlık
  ayarları "Uzman" tuşunun arkasında; panorama Güneş ile Dünya'yı kendiliğinden ortalar.
- **Karşılaştırma:** nokta, iniş tarihi ve anten payından oluşan senaryoları yan yana koyar.
- **Tanıtım videosu:** Malapert Massif üzerinde Blender ile üretilmiş 15 saniyelik açılış.
- Türkçe ve İngilizce.

## Varsayımlar ve sınırlar

- Arazi 80 m/piksel. Kayalar ve küçük krater kenarları ufka yansımaz.
- 80°G'nin kuzeyindeki arazi veri dışında kalır. 84°G civarındaki noktalarda kuzey
  yönünde ufuk ~200 km'de kesilir.
- Dünya, merkezi arazi ufkunun üstündeyse "görünür" sayılır. Gerçek anten maskesi bunu kısar.
- Eğim sınırı 8°'dir (80 m DEM üzerinden). Gerçek iniş eğimleri daha ince ölçekte ölçülmelidir.
- 3D sahnedeki arazi de 80 m verisinden gelir. Yakından bakınca yumuşak görünür.
- **Bölge sınırları yaklaşıktır.** NASA'nın 28 Ekim 2024 duyuru görselinden
  sayısallaştırıldı (±1 km). USGS'nin resmi poligonları (doi:10.5066/P1MEQ6UK)
  bugün ScienceBase'in bot doğrulaması yüzünden indirilemedi. İndirilince
  `data/raw/bolgeler/` altına koyup `02`, `04` ve `05`'i yeniden çalıştırmak yeterli.
- Aday noktalar bu projenin kendi taramasıdır. NASA'nın seçtiği noktalar değildir.

## Veri kaynakları ve atıflar

- LOLA güney kutbu DEM'i: Barker, M. K. vd. (2023), *PSJ* 4:183, doi:10.3847/PSJ/acf3e1, PGDA ürün 90
- Ortalama aydınlanma ve Dünya görünürlüğü: Mazarico, E. vd. (2011), *Icarus* 211:1066, PGDA ürün 69
- Efemeris: NASA/JPL NAIF SPICE genel kernel'leri, DE440 (Park vd. 2021, *AJ* 161:105)
- Artemis III aday bölgeleri: NASA (28 Ekim 2024); McClernan (2024), USGS, doi:10.5066/P1MEQ6UK
- Açılış ekranındaki Ay dokusu: NASA Scientific Visualization Studio, CGI Moon Kit (Ernie Wright, Noah Petro;
  LROC renk ve LOLA yükseklik haritaları), svs.gsfc.nasa.gov/4720. Yedek düşük çözünürlüklü doku: three.js örnekleri (MIT).

## Katkı notu

Arayüz tasarımının ilk hali (`arayuz/src`, metinler) ve Blender tanıtım videosu, izinle kullanılan dış
bir katkıdır ve bu projeden önce hazırlanmıştır. Dönen Ay açılış ekranı, sunum modu, NASA Ay dokuları ve kokpit
düzeltmeleri 14 Kasım 2026'da eklendi (ayrıntı: `arayuz/ARAYUZ_YENI.md`). Arayüzün okuduğu veri paketi ve bütün hesaplar
bu projede, 14 Kasım 2026'da üretildi.

## Lisans

MIT. NASA verileri kamuya açıktır, atıflar yukarıdadır.

## Ekip için: nasıl başlanır

1. Repoyu GitHub Desktop ile klonlayın (File → Clone repository → `EgeKaya-code/ay-inis-navigatoruV1.0`).
2. `arayuz/veri.zip` dosyasını `arayuz/veri/` klasörüne açın (zip'in içindeki dosyalar doğrudan `arayuz/veri/` altına gelmeli). Bu klasör GitHub'a gönderilmez.
3. `arayuz/BASLAT.bat` ile arayüzü açın: http://localhost:8767
4. NASA ham verileri (`data/raw/`, ~370 MB) GitHub'da yok; hesapları yeniden çalıştıracaksanız Ege'den ayrıca alın.

Çalışma düzeni: başlamadan önce **Fetch/Pull**, bitirince **Commit** ve **Push**. Arayüzde yalnız `arayuz/src/` ve `strings.*.json` düzenlenir; sonra `python arayuz/build.py` ile `index.html` yeniden üretilip o da commit edilir.
