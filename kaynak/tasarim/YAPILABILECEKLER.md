# Yapılabilecekler

> **13 Kasım 2026 akşamı:** aşağıdaki listeden şunlar yapıldı: iki/üç senaryoyu yan yana karşılaştırma, 10 m panel seçeneği (0 / 2 / 10 m gözlemci seçici), İngilizce, 2028 verisi (ayrıca 2026), NASA karşılaştırması (0 m koşulunda, 54 nokta). "Brifteki rakamları düzelt" maddesi için `DEMO_AKISI.md` yeniden yazıldı. Hâlâ açık: organizatör sorusu, Vite + TypeScript taşıması, kritik pay ölçüsünün kartlara taşınması, bölge içi nokta ızgarası, paylaşılabilir senaryo bağlantısı, `check-cards` denetiminin yeni kartlara uyarlanması.

*13 Kasım 2026 · etkinlik 14–15 Kasım. Prototipin durumu ve ayrıntılar: `DEVIR_NOTU.md`, demo: `DEMO_AKISI.md`.*

Yayımlanan prototip: https://claude.ai/artifact/83EXm55TnPFvXs97h6uMro

## Döndüğünde ilk 10 dakika

- [ ] **Artifact'i aç ve dene.** Yayımlanan sayfayı ben açamadım (oturum istiyor); yalnız yerelde denedim. Bakılacaklar: brifing haritası ve kartlar geliyor mu, Malapert'e iniş 3D açılıyor mu, konsolda hata var mı.
- [ ] **Takımla paylaş.** Sayfa özel; Share menüsünden iki arkadaşına aç.
- [ ] **Otomatik turu bir kez izle** (sahnenin altındaki tuş, 45 sn). Beğenmediğin adımı ya da altyazıyı söyle.

## Etkinlikten önce (bugün)

| # | İş | Neden | Kim |
|---|---|---|---|
| 1 | ~~NASA doğrulaması~~ **Yapıldı (13 Kasım):** 54 noktada, haritanın ölçüsüyle (diskin herhangi bir kısmı). Yöntem, NASA'nın ortalama görünürlük haritalarıyla aynı çözünürlükte ve aynı koşulda (0 m gözlemci, 54 nokta, 18,6 yıl) ortalama 2,0 puan (Güneş) ve 1,6 puan (Dünya) içinde uyumludur. Uygulamadaki rakamlar 20 m arazi verisi ve 2 m gözlemci kullandığı için haritadan farklıdır (ortalama mutlak fark Güneş'te 3,6, Dünya'da 1,9 puan). Rakamlar: `ay-inis-navigatoru/docs/validation/avgvisib_comparison.md`. | Rozet hâlâ "ön sonuç": uygulamanın gösterdiği 2 m / 20 m rakamları haritanın koşulu değil | Ben yapabilirim, internet gerekli |
| 2 | **Organizatöre sor:** önceden yazılmış kod/veri kullanılabilir mi, yapay zekâ kullanımı nasıl beyan edilecek | Cevaba göre prototip "deneme" sayılır ya da doğrudan kullanılır | Sen |
| 3 | **Vite + TypeScript iskeleti:** prototipin modüllerini taşı, `Sim` için birim testleri yaz | Etkinlikte sıfırdan başlamamak; beklenen değerler `DEVIR_NOTU.md`'de hazır | Ben yapabilirim |
| 4 | **Brifteki rakamları düzelt:** sunum ve `ILERLEME.md`'de "18 gün" ve "Malapert Dünya %100" geçiyor; bu noktanın (Malapert örnek nokta) verisi: en uzun karanlık 14,3 gün; Dünya 0° maskeyle %81,6 (2026–2030), 2027'de %78,8 | Sunumda yanlış rakam söylenmesin | Sen onayla, ben düzeltirim |
| 5 | **Demo provası:** `DEMO_AKISI.md`'yi 3 dakikada bir kez oyna, 1920×1080'de | Süre ve kare hızı gerçek donanımda hiç ölçülmedi | Takım |

## Ürüne eklenebilecekler

Etkisi yüksek olandan düşüğe:

- [ ] **İki bölgeyi yan yana karşılaştırma.** Şeritler ve üç rakam alt alta; "neden Mons Mouton, neden Malapert değil" sorusunu cevaplar.
- [x] **10 m panel seçeneği.** Yapıldı: 0 / 2 / 10 m gözlemci seçici. Malapert örnek nokta, 2027: güneşli zaman %68,1 → %84,6, güneş enerjisi oranı %64,7 → %81,2.
- [ ] **Kritik pay ölçüsünü kartlara taşı.** Kokpitte "görünür sürenin %9'unda pay 1°'den az" var; kart için `export_proto.py`'nin aynı ölçüyü 2026–2030 için üretmesi gerek (Python tarafı, sende).
- [ ] **Bölge içinde nokta ızgarası.** Tek örnek nokta yerine haritada ısı haritası; Haworth ve Mons Mouton Plateau uyarılarını da çözer. Büyük iş, hesap tarafı gerekli.
- [ ] **İngilizce.** `strings.tr.json` tek sözlük; çevirisi ve dil tuşu yarım saatlik iş.
- [ ] **İniş penceresini 2028'e uzat.** Şu an veri 31 Aralık 2027'de bittiği için yıl sonuna yakın inişler "dayanır" görünüyor. `series_2028.json` üretilirse düzelir.
- [ ] **Düşey abartı (1×/2×) tuşu.** Brifte isteğe bağlıydı, eklemedim.
- [ ] **Paylaşılabilir senaryo.** Bölge + tarih + batarya ayarı bağlantıya yazılsın (Artifact'te yalnız basit `#etiket` çalışıyor; Vite uygulamasında serbest).

## Yapay zekâ ile

Kural: rakamı model üretmez, `Sim` üretir; model yalnız soruyu fonksiyona çevirir ve sonucu anlatır.

- [ ] **Görev danışmanı.** "Mart'ta inersek hangi batarya yeter?" gibi sorulara cevap; model kaydırıcıları ve zaman çizgisini kendisi ayarlar. İniş penceresi ve en küçük batarya hesabı hazır, yani modelin çağıracağı fonksiyonlar var.
- [ ] **Otomatik bölge brifingi.** Seçilen bölge için 3–4 cümlelik özet; sade modda öğretmen/öğrenci düzeyi.
- [ ] **Olay anlatıcısı.** Zaman oynarken olayları bağlayan tek satırlık yorum.

Gereken: API anahtarı ve küçük bir sunucu (anahtar tarayıcıya konmaz); internet kesilince demo çökmemeli, yani ek katman olarak kalmalı.

## Sunum ve teslim

- [ ] Demo videosu: otomatik tur ekran kaydıyla çekilebilir (H tuşu panelleri gizler).
- [ ] Slaytlar: sorun, "neden biz" (düz ufuk karşılaştırması), yöntem, sınırlar, kaynaklar.
- [ ] README ve proje sayfası metni.
- [ ] Doğrulama gelirse "bizim % – NASA %" grafiği.

## Bilinen eksikler (düzeltilebilir)

- 880 px'ten kısa ekranda kokpitin sol sütunu kaydırılıyor.
- Brifingde 810 px yükseklikte beş kart görünüyor, gerisi kaydırılıyor.
- Kamera 3–5 km yükseklikteyken arazi karesi boşlukta duruyor.
- Aracın gölgesi ve yüzeydeki küçük kraterler temsili (veri değil); Veri penceresinde yazıyor.
- Dokunmatik kontroller hiç denenmedi.
