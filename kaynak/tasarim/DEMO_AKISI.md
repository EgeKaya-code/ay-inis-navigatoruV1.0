# Jüri demosu

*Güncellendi: 14 Kasım 2026. Buradaki her rakam `RAKAMLAR.md` dosyasından alınmıştır (üreten `prototip/check_numbers.py`, arayüzden bağımsız hesap; `python check_numbers.py --check` bu belgedeki rakamların orada üretildiğini denetler) ve tarayıcıda ekranla karşılaştırılmıştır. Koşul: 2 m gözlemci, 1° anten payı.*

"Güneşli zaman" = Güneş diskinin herhangi bir kısmının göründüğü zaman yüzdesi. Diskin görünen oranının ortalaması ayrı bir rakamdır: "güneş enerjisi oranı".

Hazırlık: `tasarim\prototip` klasöründe `python serve.py` → http://localhost:8765, tam ekran (F11), 1920×1080 ideal. **İnternet gerekmez:** three.js ve yazı tipleri `vendor/` altında, sayfa localhost dışına istek yapmaz. "Karşılaştır" ekranında **Temizle**'ye basıp boş başlayın. Sayfayı önceden bir kez açıp Malapert'e inin ki veriler önbelleğe girsin.

Tek cümle: **"Görev kayarsa hangi tarih, hangi nokta? Bunu gerçek arazi ufkuyla, bir dakikada cevaplıyoruz."**

---

## A. Bir dakikalık akış: "Görev 2 hafta kaydı, hangi alternatif daha iyi?"

Senaryo: iniş Malapert Massif'in örnek noktasına, 1 Mart 2027'de planlıydı. Görev iki hafta kaydı.

| # | Süre | Tıkla | Söyle |
|---|---|---|---|
| 1 | 0:00–0:15 | Brifing → **MA · Malapert Massif** kartı → aday çubuğunda **ÖRNEK** → "İniş tarihi" alanına **01.03.2027 00:00** → **KARŞILAŞTIRMAYA EKLE** (tuş "A olarak eklendi" der). | "Planımız bu: Malapert, 1 Mart. Senaryo üç şeyden oluşuyor: nokta, iniş tarihi, anten payı." |
| 2 | 0:15–0:30 | Üstteki **KARŞILAŞTIR (1)** → A sütununun altında **Kopyala … 14 gün +**. | "Görev iki hafta kaydı. Aynı noktanın 15 Mart'ı tek tıkla ikinci sütun oldu." B sütununu gösterin: "İnişte karanlık, ışığa 12 saat var." |
| 3 | 0:30–0:45 | **BRİFİNG** → aday çubuğunda **1**'e basın (bölge seçili kaldığı için çubukta "Örnek" seçili durur) → iniş tarihi **15.03.2027 00:00** → **KARŞILAŞTIRMAYA EKLE** → **KARŞILAŞTIR (3)**. | "Alternatif: 11,8 km ötedeki 1. aday, yine 15 Mart." |
| 4 | 0:45–1:00 | Üstteki cümleyi okuyun, yeşil rakamları ve en alttaki yeşil "birlikte" şeridini gösterin. Fareyi bir şeridin üstünde gezdirin. | "Araç tek cümleyle cevap veriyor: **C, Güneş + Dünya ortak penceresinde A'dan 19,7 puan önde (%46,4 ↔ %26,7). En uzun karanlığı 1,6 gün daha kısa.** Tarihi kaydırmak bir şey kazandırmadı (%28,2); noktayı değiştirmek kazandırdı." |

İlk 30 günün rakamları (ekranda görünen):

| | A · örnek nokta · 1 Mar | B · örnek nokta · 15 Mar | C · aday 1 · 15 Mar |
|---|---|---|---|
| Güneşli zaman | %56,9 | %53,2 | %59,6 |
| Dünya görünür (1° pay) | %69,3 | %75,0 | %86,8 |
| Güneş + Dünya birlikte | %26,7 | %28,2 | **%46,4** |
| En uzun karanlık | 12,9 gün | 13,5 gün | **11,3 gün** |
| En uzun bağlantısız süre | 7,5 gün | 7,5 gün | **4,0 gün** |
| İniş anında Güneş | arazi ufkunun 1,19° üstünde, disk %100; karanlığa 38 saat | ufkun 0,80° altında; karanlık, ışığa 12 saat | ufkun 2,24° altında; karanlık, ışığa 20 saat |
| İniş anında Dünya | ufkun 0,58° altında; bağlantı yok, bağlantıya 41 saat | ufkun 11,82° üstünde; bağlantı var, kesilmeye 7,4 gün | ufkun 13,51° üstünde; bağlantı var, kesilmeye 9,2 gün |

Devamı için (isteğe bağlı): **C sütununa tıklayın** → senaryo kokpitte açılır (iniş sekansı olmadan), aynı tarih ve anten payıyla. Pencere seçicide **90 GÜN**'e basıp sonucun değişip değişmediğini gösterin.

Başka bir bölgeyle aynı soru (15 Mart 2027, 30 gün): Mons Mouton Plateau aday 1 ortak pencerede %49,7; de Gerlache Rim 2 aday 1 güneşli zamanda %71,0 ama Dünya %54,3, ortak pencere %28,7, en uzun bağlantısız süre 13,7 gün.

---

## B. Üç dakikalık akış (kokpit)

Bölge: **Malapert Massif, örnek nokta**, iniş 1 Ocak 2027 (varsayılan tarih). Kokpitteki bütün özet rakamları seçili yılın (2027) canlı hesabıdır.

| # | Süre | Tıkla | Söyle |
|---|---|---|---|
| 1 | 0:00–0:20 | Brifing açık. Haritadaki kutuları gösterin, "En uzun iletişim" ve "Dengeli" sıralamalarına birer kez basın. | "Artemis III'ün 9 aday bölgesi. Her kart tek bir noktanın, bölgenin 1. adayının üç rakamı: güneşli zaman, Dünya'nın göründüğü zaman, en uzun karanlık." İlk kart de Gerlache Rim 2 (güneşli zaman %83,3). |
| 2 | 0:20–0:40 | **MA** kartı → çubukta **ÖRNEK** → **İNİŞE BAŞLA**. İlk inişte sekans oynar (9 sn). | "Bu arazi NASA'nın LOLA yükseklik verisi, gerçek ölçekte. Dünya şu an görünmüyor: 1 Ocak'ta ufkun 0,65° altında." GÜÇ panelindeki satırı gösterin: yükseklik, azimut ve "arazi ufkunun … üstünde". |
| 3 | 0:40–1:15 | Olay akışında **"Gün 10 · Güneş doğdu"** → **ASTRONOT GÖZÜ** → **GÜNEŞ'E BAK** → tekerlekle yakınlaş → hız **1 SAAT/SN** → oynat. | "Güneş doğmuyor, ufku sıyırıyor. Panel, diskin görünen kısmı kadar güç alır. Sağdaki gökyüzü radarı nedenini gösteriyor: taralı alan arazi." Sonra **DÜNYA'YA BAK**. |
| 4 | 1:15–1:45 | **YÖRÜNGE** → hız **1 HAFTA/SN** → oynat. Alt şeritte üç satırı gösterin. **"Gün 41 · GÖREV DURDU"** satırına tıklayın. | "Sarı şerit Güneş, mavi Dünya, yeşil ikisinin birlikte olduğu zaman. 2027'de güneşli zaman %68,1, ortak pencere %45,7, en uzun karanlık 14,3 gün. Örnek 100 kWh batarya 41. günde bitiyor." |
| 5 | 1:45–2:05 | GÜÇ panelinde **Kapasite** 100 → 200 kWh (ya da "Dayanan en küçük batarya: 180 KWH" kutusu). | "200 kWh ile araç veri sonuna, 31 Aralık 2028'e kadar dayanıyor, en düşük %13. 170 yetmiyor, 180 yetiyor." |
| 6 | 2:05–2:30 | İLETİŞİM panelinde **Anten maskesi** 1° → 0° → 2°. | "Malapert'te 0° ile %78,8, 1° payla %71,9, 2° ile %66,0. Mons Mouton Plateau örnek noktasında fark daha sert: %99,4'ten %81,1'e." |
| 7 | 2:30–2:55 | Üstte **DÜZ UFUK**, 3 saniye bekleyin, sonra **GERÇEK ARAZİ**. | "Ufku düz sayan hesap bu nokta için güneşli zaman %51,0, Dünya %67,6, en uzun karanlık 17,7 gün der. Gerçek araziyle %68,1, %78,8 ve 14,3 gün: güneşli zamanda 17,1 puan fark." |
| 8 | 2:55–3:00 | **SADE MOD**. | "Aynı ekran, terimsiz: gökyüzü haritası ve olay akışı duruyor, yalnız etiketler sadeleşiyor." |

## Kullanılabilecek diğer özellikler

- **Yıl seçici** (alt şerit): 2026, 2027, 2028. İniş ve imleç aynı takvim gününe taşınır. Malapert örnek noktada 2028: güneşli zaman %70,0, Dünya %76,2, ortak %50,5.
- **Pencere**: Tümü / Yıl / 90 gün / 30 gün; şeridin üstünde tekerlek yakınlaştırır.
- **Saat alanı** (üstte): tarih ve saat yazarak o ana gidilir. **İNİŞİ BU ANA AL**: iniş anını imlecin olduğu yere taşır.
- **Gözlemci yüksekliği** (Nokta özeti): 0 / 2 / 10 m. Malapert örnek nokta, 2027, güneşli zaman: %54,0 / %68,1 / %84,6. 2 m dışında 3D sahnenin üstünde "sahne 2 m gözlemciyi çizer" notu çıkar; rakamlar, radar ve panorama seçilen yüksekliğe göredir.
- **OTOMATİK TUR**: altı adımlı, altyazılı, kendi kendine oynayan tur, yaklaşık 45 saniye (demo videosu için). 14 Kasım'da üç nokta, üç yıl, üç yükseklik ve iki dilde baştan sona denendi. Altyazıdaki rakamlar seçili yılın canlı hesabıdır. Esc durdurur.
- **Dil**: sağ alttaki seçici (Türkçe / English).
- **H** tuşu panelleri gizler.

## Yedek planlar

- **3D açılmazsa** uygulama 2B panoramaya geçer; karşılaştırma ekranı 3D'ye hiç ihtiyaç duymaz.
- **Soru: "Bu doğru mu?"** "Güneş/Dünya konumları NASA SPICE'tan (DE440), arazi LOLA'dan. NASA'nın 18,6 yıllık görünürlük haritalarıyla 54 noktada karşılaştırdık. Yöntemimiz haritayla aynı çözünürlükte ve aynı koşulda ortalama 2,0 puan (Güneş) ve 1,6 puan (Dünya) içinde uyumlu. Ekranda gördüğünüz rakamlar ise 20 m'lik daha ince arazi verisi ve 2 m yükseklikteki panel/anten için; bu yüzden haritadan farklı (ortalama 3,6 ve 1,9 puan). Farkı düzeltmedik, raporladık." (Sağ alttaki "Veri ve kaynaklar"; tablo `ay-inis-navigatoru/docs/validation/avgvisib_comparison.md`.)
- **Soru: "Nokta resmi iniş noktası mı?"** "Hayır. Adaylar eğimi 5°'den az hücrelerden NASA haritasıyla tarandı; örnek nokta bölge merkezine 6 km içindeki en yüksek düz nokta."
- **Soru: "Neden 2 m?"** "Araç üstündeki panel ve anten için tipik bir yükseklik. Seçiciden 0 ve 10 m de bakılabilir; fark büyük, o yüzden açıkça yazıyoruz."

## Bilinen sınırlar (demoda sorulursa)

- "Güvenli iniş penceresi" artık veri sonuna (31 Aralık 2028) kadar dayanmayı ölçüyor; varsayılan 100 kWh ile cevap "19 Tem 2028 ve sonrası". Veri sonuna yakın inişler doğal olarak "dayanır" görünür.
- Karşılaştırma penceresi veri sonunu aşarsa sütunda kırpıldığı yazılır (örnek: 10 Aralık 2028 inişi, 30 günün 22 günü).
- Yalnız tam veri paketi olan 54 nokta (her bölgede örnek nokta + ilk 5 aday) karşılaştırılabilir.

## Klavye

Boşluk: oynat/durdur · ← →: 1 saat · Shift + ← →: 1 gün · N: sonraki olay · H: panelleri gizle/göster · Esc: turu durdur · şeritte tekerlek: yakınlaş.
