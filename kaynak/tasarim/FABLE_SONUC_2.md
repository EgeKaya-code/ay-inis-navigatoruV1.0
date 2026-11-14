# Fable görevi 2: sonuç notu

> **14 Kasım 2026 notu: bu belge 13 Kasım'ın kaydıdır, güncel değildir.** Buradaki "Güneşli" sütunu o günkü tanımla **güneş enerjisi oranıdır** (diskin görünen oranının ortalaması); arayüzde "güneşli zaman" artık diskin herhangi bir kısmının göründüğü zaman yüzdesidir. "Güneş ort. 2,4; Dünya ort. 4,4, en çok 20 puan" ifadesi yalnız dokuz örnek nokta ve 0 m gözlemci içindi; arayüzdeki 2 m rakamları için söylenemez. Güncel karşılaştırma: `ay-inis-navigatoru/docs/validation/avgvisib_comparison.md`; güncel rakamlar: `RAKAMLAR.md`; güncel demo: `DEMO_AKISI.md`.

*13 Kasım 2026. Beş adımın beşi de bitti. Araya iki kesinti girdi (aşağıda); ikisi de kapandı.*

## Ne yapıldı

| Adım | Sonuç |
|---|---|
| 1. Veri | `candidates.json` dokuz bölge, bölge başına 20 aday + eski örnek nokta; 45 yeni iniş paketi; 9 ısı haritası. |
| 2. Arayüz | Isı haritası, aday noktaları, kartlarda en iyi / ortanca, adaya tıklayınca kokpit. |
| 3. Doğrulama | Kart rakamları: 220 karşılaştırma, 0 uyuşmazlık. Demo akışı eski rakamlarla aynı. 39 test geçiyor. |
| 4. Commit | `ay-inis-navigatoru`, `aday-noktalar` dalı, iki commit (`e357335`, `3e40472`), push yok. |
| 5. Blender | `tasarim/blender/malapert_acilis.mp4` (15 sn, 1920×1080, 30 fps, 8,4 MB) + 3 kare (`kare_1_yaklasma`, `kare_2_dunya`, `kare_3_gunes`). |

**Kesintiler.** Dokuz bölgelik ilk koşu son bölgede, sistem belleği azaldığı için Claude Code tarafından durduruldu; betik o sırada dosyayı en sonda yazdığından sekiz bölge boşa gitti. Betiği her bölgeden sonra yazacak hale getirdim (`--missing` kaldığı yerden sürdürür) ve bölgeleri ön planda yeniden hesapladım: DEM'ler önbellekte olduğu için bölge başına ~42 sn. `winget` ile Blender kurulumu yönetici onayı (UAC) beklediği için iptal oldu; görevdeki ikinci yol olan portable zip kullanıldı: `C:\Users\umutc\Tools\blender\blender-5.3.0-windows-x64\` (sha256 doğrulandı).

## Bölge bölge: eski nokta ↔ adaylar (2 m, 2026–2030)

Sıra: Güneşli / Dünya 1° / en uzun karanlık, parantezde dengeli puan. "1. aday" bizim modelde dengeli puanı en yüksek aday.

| Bölge | Eski örnek nokta | 1. aday | Uzaklık | 21 noktada en iyi / ortanca: Güneş | Dünya 1° | Karanlık |
|---|---|---|---|---|---|---|
| Nobile Rim 2 | %50,5 / %68,4 / 15,7 gün (55,5) | %50,7 / %68,4 / 15,7 gün (55,6) | 0,0 km | %50,7 / %47,8 | %72,0 / %72,0 | 15,7 / 16,3 gün |
| Mons Mouton | %66,0 / %79,8 / 12,5 gün (68,0) | %57,1 / %80,9 / 15,4 gün (62,3) | 0,3 km | %66,0 / %51,0 | %81,4 / %79,8 | 12,5 / 15,9 gün |
| Malapert Massif | %65,4 / %74,3 / 14,3 gün (64,0) | %64,7 / %87,2 / 12,0 gün (70,6) | 11,8 km | %73,1 / %55,6 | %87,5 / %84,4 | 12,0 / 15,5 gün |
| de Gerlache Rim 2 | %59,8 / %52,8 / 15,7 gün (53,5) | %79,9 / %52,7 / 6,6 gün (70,2) | 6,1 km | %79,9 / %59,8 | %52,8 / %51,1 | 6,6 / 15,7 gün |
| Mons Mouton Plateau | %51,6 / %80,4 / 16,0 gün (59,6) | %70,1 / %82,8 / 10,8 gün (72,3) | 23,3 km | %70,1 / %55,9 | %98,4 / %84,8 | 10,8 / 14,6 gün |
| Slater Plain | %64,6 / %40,9 / 14,0 gün (53,0) | %63,5 / %40,9 / 14,0 gün (52,6) | 0,1 km | %64,6 / %56,6 | %41,3 / %39,9 | 13,8 / 16,3 gün |
| Peak Near Cabeus B | %65,1 / %79,4 / 12,4 gün (67,8) | %55,5 / %79,3 / 14,6 gün (62,0) | 1,4 km | %65,1 / %51,4 | %79,4 / %76,7 | 12,4 / 15,6 gün |
| Nobile Rim 1 | %66,5 / %64,5 / 12,5 gün (63,1) | %66,6 / %72,5 / 11,7 gün (66,8) | 1,5 km | %66,6 / %52,0 | %79,7 / %75,7 | 11,7 / 16,6 gün |
| Haworth | %13,9 / %18,3 / 194,5 gün (10,7) | %65,8 / %54,5 / 14,0 gün (57,9) | 5,8 km | %65,8 / %53,2 | %68,9 / %61,8 | 13,8 / 16,9 gün |

Okuma:
- **Haworth ve Mons Mouton Plateau'nun derdi çözüldü.** Haworth %13,9 → %65,8 güneş; Plateau'da Dünya 1° payla %98,4'e çıkan nokta var.
- **Üç bölgede eski nokta 1. adaydan iyi** (Mons Mouton, Peak Near Cabeus B, Slater Plain). NASA taraması "Güneş + Dünya'nın herhangi bir kısmı görünür" ortalamasına bakıyor; bizim dengeli puanımız disk oranına, 1° paya ve karanlığa. İki ölçü aynı noktayı seçmiyor. Eski nokta listede kaldığı için kartlardaki "en iyi" bunu kapsıyor.
- **Ortanca belirgin düşük** (Güneş'te %48–60): en iyi nokta dar bir yerde, bölgenin geneli değil.
- Düz hücre oranı düşük: Peak Near Cabeus B %0,5, Malapert %1,4, en yüksek Slater Plain %12,4.
- 180 adayda bizim `sun_any_pct` (2 m, 5 yıl) − NASA Güneş (18,6 yıl): ort. +1,6, ort. mutlak 2,2, en çok 11,1 puan. Dönem ve yükseklik farklı; kaba bir tutarlılık göstergesi, doğrulama değil.

## Kararlar

- **Aday listesi 21 nokta:** NASA ile seçilen 20 + eski örnek nokta. En iyi / ortanca 21 üzerinden, her ölçü için ayrı (en iyi Güneş ile en iyi Dünya aynı nokta olmayabilir).
- **Varsayılan iniş noktası eski örnek nokta.** Demo akışı bu yüzden aynı; aday ancak tıklanınca değişir.
- **Seyreltme puana göre:** en iyi hücre alınır, 300 m çevresi atılır, tekrar. Eşit puanda eğimi az olan.
- **Bölge başına tek NASA haritası:** poligon 85°G haritasına sığmıyorsa tamamı 120 m haritayla (Nobile Rim 2, Peak Near Cabeus B, Mons Mouton Plateau). Eski doğrulama Plateau noktasını 60 m haritadan okumuştu; o yüzden o noktanın NASA değeri iki yerde farklı.
- **Isı haritası ölçeği sabit %0–100**, bölgeler birbiriyle karşılaştırılabilsin diye.
- **Karttaki ince şerit artık 1. adayın 2027'si.** `DEMO_AKISI.md`'deki "Haworth'un neredeyse boş sarı şeridini gösterin" notu artık geçersiz. Belgeye dokunmadım. Öneri: "Haworth kartına tıklayın: eski örnek nokta %13,9, krater kenarındaki adaylar %65,8."
- **`data.status` metnini değiştirdim:** "karşılaştırma henüz yapılmadı" artık yanlıştı. Yeni rakamlar `pgda_comparison.json`'dan (Güneş ort. 2,4; Dünya ort. 4,4, en çok 20 puan).
- **Kartlardaki "nokta bölgeyi temsil etmeyebilir" bayrağı kalktı**, uyarı eski nokta seçiliyken ayrıntı panelinde duruyor.
- **`serve.mjs`**, `terrain.b64.txt` yoksa `terrain.bin`'den anında üretir (yalnız yerel). Artifact'e aday paketleri gönderilecekse `pack-terrain.mjs` gerekir (+60 MB).
- **Dal:** varsayılan dalda commit yerine `aday-noktalar` açtım. Birleştirmek için `git checkout main && git merge aday-noktalar`.
- **Commit satırı** görevde yazdığı gibi "Claude Fable 5.1"; oturum Fable 5.2 ile çalıştı.

## Doğrulananlar

- `export_proto.py` bölündükten sonra yeniden çalıştırıldı: `sites.json` veri olarak aynı, diğer bütün dosyalar bayt bayt aynı.
- Eski noktalar bölge DEM'inden yeniden hesaplandı: dokuz bölgede `sites.json` ile fark 0.
- `candidates.json` denetimi: her bölgede 20 aday, hepsi poligon içinde, en yakın çift ≥ 300 m, eğim < 5°, sıra puana göre, 5 paket ve dosyaları yerinde.
- Kartlar ↔ `candidates.json`: `check-cards.mjs`, 4 sıralama × 9 bölge, 220 karşılaştırma, 0 uyuşmazlık (en iyi / ortanca ve sıralama uygulama kodundan bağımsız hesaplanır).
- Demo akışı (Malapert, varsayılan nokta): %65,4 / %74,3 (0° ile %81,6) / 14,3 gün; 1 Ocak'ta Dünya −0,65°; Gün 10 Güneş doğdu; Gün 41 görev durdu; 200 kWh'de en düşük %13, 180 yetiyor, 170 yetmiyor; maske 0° %78,8, 1° %71,9; düz ufuk %50,0 / %69,4 / 17,7 gün; sade mod.
- Haworth 1. adayla kokpit 3D açılıyor (%65,8 / %54,5 / 14,0 gün); paketi olmayan adayda İNİŞE BAŞLA kapalı.
- 1440×810 ve 400 px ekran görüntüleri `tasarim/dogrulama_1311/`; 400 px'te yatay taşma yok; konsolda hata yok (yalnız eski three.js sürüm uyarısı).

## Blender videosu

- **An:** 5 Kasım 2027 13:00 UTC. Güneş 1,00° yükseklik, 97,95° azimut, disk tam görünür. Dünya 3,54° / 359,46°, aydınlık oranı 0,57. Kural `prep_scene.py`'de: tam Güneş, Dünya payı ≥ 1°, Güneş 0,5–1,5°, Güneş–Dünya azimut farkı 60–100°, 1,0°'ye en yakın saat (276 saat arasından).
- **Veri:** arazi LOLA 20 m DEM (±10 km) ve 80 m DEM (±150 km), eğrilik d²/2R; açılar `series_2027.json`.
- **Yön/ölçek kontrolü:** sahnedeki ağlardan 2 m gözle hesaplanan ufuk − `horizon.json`: uzak ufukta (81 azimut) ort. mutlak 0,010°, en çok 0,055°; yakın ufukta (279 azimut) ort. 0,042°, en çok 0,23°. Güneş azimutunda sahne −0,66°, `horizon.json` −0,64°. Eksenler x = doğu, y = kuzey, z = yukarı.
- **Süre:** Cycles + OptiX (RTX 4060), 128 örnek. İlk tam geçiş 450 kare 1047 sn (~17,5 dk, kare başına 2,3 sn). Son 120 kare parlama düzeltmesi için 2880×1620 çizilip ortadan kesildi: 718 sn daha. Toplam ~29,5 dk.
- **Süreklilik:** 450 karede ardışık kare farkı sayısal olarak tarandı; ani sıçrama yok (en büyük artış oranı 2,2). İlk sürümde Güneş kadraja girdiği karede parlama birden beliriyordu (370. kare); düzeltildi.

Görevden sapmalar ve veri olmayan şeyler:
- **Yakın arazi `terrain.bin` değil, onun kaynağı olan 20 m DEM.** 40 m'lik yüzler 1° Güneş'te gölge sınırında üçgen üçgen sahte gölge verdi. 20 m veri kübik ara değerle 10 m'ye (±10 km) ve 2 m'ye (±600 m) inceltildi; ara değer ayrıntı eklemez. 40 m düğümlerde `terrain.bin` ile fark RMS 0,13 m, en çok 3,5 m.
- **Ağ kenarlarında yumuşak geçiş.** İç ağın kenar bandı dış ağın yüzeyine oturtuldu (10 km kenarında en çok 15 m kayma), yoksa basamak uzun sahte gölge düşürüyordu.
- **Son kare Eevee değil Cycles.** Eevee arka planda çalıştı (960×540 önizleme alındı) ama gölgeleri Cycles'tan farklıydı; gölge işin özü olduğu için Cycles seçildi.
- **Yordamsal ince doku var** (yalnız gölgeleme, şiddet 0,12, ~5 cm tane). 20 m verinin göremediği ölçekte zemin dümdüz çıkıyordu. Veri değil.
- **Pozlama kamera Güneş'e dönerken +1 → +4,5 EV açılıyor**, Güneş çevresinde mercek parlaması var. İkisi de görüntü işlemi. Parlamanın şiddeti, Güneş kadraja yaklaşırken 0'dan kademeli açılır (elle ayarlanmış geçiş).
- **Dünya düz mavi küre:** bulut/kara deseni uydurulmadı, evre aynı Güneş lambasından geliyor.
- Kamera Dünya'nın tersinden değil 300° azimuta bakarak yaklaşıyor (aydınlık yamaç kadrajı doldursun diye), süzülüşün sonunda Dünya'ya, sonra Güneş'e dönüyor.

Yeniden üretmek için (`tasarim/blender/` içinde; kareler OneDrive dışına):
```
python prep_scene.py
blender -b -P malapert_render.py -- --frames-dir <klasör> --engine cycles --res 1920x1080 --overscan 1.5 --samples 128 --exposure 1.0 --exposure-end 4.5 --bump 0.12 --bump-scale 20 --glare 0.05 --glare-size 0.7 --approach-az 300
python caption_frames.py --frames <klasör> --out <klasör2>
blender -b -P encode_video.py -- --frames <klasör2> --out malapert_acilis.mp4
```
`--overscan 1.5` bütün karelerde kullanılırsa render tahminen ~37 dk sürer (ölçülen: bu boyutta kare başına ~5 sn). Teslim edilen videoda yalnız 331–450. kareler böyle çizildi; öncesinde parlama kaynağı kadraja yakın değil. Yazısız ham kareler `C:/Users/umutc/Tools/blender/malapert_kareler/` altında (0,8 GB): alt yazıyı değiştirmek için yalnız son iki komut yeter; gerekmiyorsa silinebilir.

## Doğrulanamayanlar ve bilinen eksikler

- **Videoyu oynatarak izlemedim.** Kare sayısı, çözünürlük ve fps dosyadan okundu, kareler tek tek ve sayısal süreklilik taramasıyla kontrol edildi; hareketin hızına ve hissine gözle bakılmadı. İlk izlemede dönüşe (10–13,5. sn) ve ince dokuda kareler arası kıpırtıya bakın.
- **810 px yükseklikte aynı anda yaklaşık 3 kart görünüyor** (ayrıntı paneli büyüdü). 1080'de sorun değil. Demo 2. adımda Malapert kartı "En çok güç"te 2. sırada, görünür.
- **Demo 1. adımda ilk kart artık de Gerlache Rim 2** (%79,9), eskiden Nobile Rim 1'di.
- Göz hizasındaki zemin ve Güneş'e bakan son kare sade: 20 m verinin altında ayrıntı yok, Güneş yönündeki uzak dağlar siyah gökyüzüne karşı siyah.
- Adaylar yalnız eğim ve iki NASA haritasıyla tarandı; kaya, iniş elipsi, sıcaklık yok.
- `veri/README.md` ve `DEVIR_NOTU.md` yeni dosyaları (`candidates.json`, `heat/`, `sites/<bölge>__c<N>/`) anlatmıyor; dokunmadım. Biçim `export_candidates.py`'nin başında yazılı.
- Dokunmatik ekranda aday noktasının üstüne gelme yok; onun yerine ayrıntı panelindeki aday çubuğu var.
- Yayımlanan Artifact güncellenmedi (görev gereği).
