# Belgelerde kullanılan rakamlar

Üreten: `prototip/check_numbers.py` (arayüzden bağımsız Python hesabı; elle değiştirmeyin, yeniden üretin). Veri: `veri/` · yıllar 2026, 2027, 2028 · varsayılan gözlemci 2 m, anten payı 1°.

Tanımlar: **güneşli zaman** = Güneş diskinin herhangi bir kısmının göründüğü zaman yüzdesi; **güneş enerjisi oranı** = diskin görünen oranının ortalaması; **Dünya** = merkezi arazi ufkunun anten payı kadar üstünde; **ortak** = Güneş görünür ve Dünya bağlantısı var.

## 1. Brifing kartları (2026–2030, 2 m; kaynak `candidates.json`, her bölgenin 1. adayı)

"En çok güç" sırası (1. adayın güneş enerjisi oranına göre):

| Sıra | Bölge | Güneşli zaman | Dünya · 1° | En uzun karanlık | Enerji oranı |
|---|---|---|---|---|---|
| 1 | de Gerlache Rim 2 · aday 1 | %83,3 | %52,7 | 6,6 gün | %79,9 |
| 2 | Mons Mouton Plateau · aday 1 | %72,1 | %82,8 | 10,8 gün | %70,1 |
| 3 | Nobile Rim 1 · aday 1 | %68,0 | %72,5 | 11,7 gün | %66,6 |
| 4 | Haworth · aday 1 | %70,3 | %54,5 | 14,0 gün | %65,8 |
| 5 | Malapert Massif · aday 1 | %66,3 | %87,2 | 12,0 gün | %64,7 |
| 6 | Slater Plain · aday 1 | %65,7 | %40,9 | 14,0 gün | %63,5 |
| 7 | Mons Mouton · aday 1 | %58,7 | %80,9 | 15,4 gün | %57,1 |
| 8 | Peak Near Cabeus B · aday 1 | %56,4 | %79,3 | 14,6 gün | %55,5 |
| 9 | Nobile Rim 2 · aday 1 | %51,9 | %68,4 | 15,7 gün | %50,7 |

## 2. Karşılaştırma ekranı (inişten sonraki 30 gün, 2 m, 1° pay; kaynak `series_YYYY.json`, `horizon.json`)

| | Senaryo | Güneşli zaman | Dünya görünür | Güneş + Dünya | En uzun karanlık | En uzun bağlantısız | İnişte Güneş | İnişte Dünya |
|---|---|---|---|---|---|---|---|---|
| A | Malapert Massif · örnek nokta · 1 Mar 2027 | %56,9 | %69,3 | %26,7 | 12,9 gün | 7,5 gün | ufkun 1,19° üstünde, disk %100; karanlığa 38 saat | ufkun 0,58° altında; bağlantı yok, bağlantıya 41 saat |
| B | Malapert Massif · örnek nokta · 15 Mar 2027 | %53,2 | %75,0 | %28,2 | 13,5 gün | 7,5 gün | ufkun 0,80° altında, disk %0; karanlık, ışığa 12 saat | ufkun 11,82° üstünde; bağlantı var, kesilmeye 7,4 gün |
| C | Malapert Massif · aday 1 · 15 Mar 2027 | %59,6 | %86,8 | %46,4 | 11,3 gün | 4,0 gün | ufkun 2,24° altında, disk %0; karanlık, ışığa 20 saat | ufkun 13,51° üstünde; bağlantı var, kesilmeye 9,2 gün |
| – | Mons Mouton Plateau · aday 1 · 15 Mar 2027 | %65,3 | %84,4 | %49,7 | 10,4 gün | 4,7 gün | ufkun 1,55° üstünde, disk %100; karanlığa 13,6 gün | ufkun 12,73° üstünde; bağlantı var, kesilmeye 8,8 gün |
| – | de Gerlache Rim 2 · aday 1 · 15 Mar 2027 | %71,0 | %54,3 | %28,7 | 6,2 gün | 13,7 gün | ufkun 0,21° üstünde, disk %94; karanlığa 2,8 gün | ufkun 7,34° üstünde; bağlantı var, kesilmeye 4,7 gün |
| – | Malapert Massif · örnek nokta · 10 Ara 2028 (pencere kırpıldı) | %66,5 | %79,2 | %54,5 | 7,4 gün | 4,6 gün | ufkun 1,94° üstünde, disk %100; karanlığa 2,6 gün | ufkun 0,87° altında; bağlantı yok, bağlantıya 4,6 gün |

Özet cümlesi (A, B, C): en yüksek ortak pencere C. C − A = 19,7 puan (%46,4 ↔ %26,7); en uzun karanlık farkı 1,6 gün (daha kısa). B − A = 1,5 puan.
Kırpılan pencere örneği: 10 Ara 2028 inişinde 30 günün 22,0 günü var.
Malapert Massif örnek nokta ↔ aday 1 arası uzaklık: 11,8 km (kaynak `candidates.json` enlem/boylam, R = 1737,4 km).

## 3. Kokpit: Malapert Massif örnek nokta (seçili yılın tamamı; kaynak `series_YYYY.json`, `horizon*.json`)

| Yıl | Gözlemci | Anten payı | Güneşli zaman | Enerji oranı | Dünya | Ortak | En uzun karanlık | En uzun kesinti |
|---|---|---|---|---|---|---|---|---|
| 2027 | 2 m | 1° | %68,1 | %64,7 | %71,9 | %45,7 | 14,3 gün | 8,0 gün |
| 2027 | 2 m | 0° | %68,1 | %64,7 | %78,8 | %50,5 | 14,3 gün | 6,1 gün |
| 2027 | 2 m | 2° | %68,1 | %64,7 | %66,0 | %41,8 | 14,3 gün | 9,5 gün |
| 2026 | 2 m | 1° | %70,4 | %66,9 | %71,7 | %47,2 | 14,2 gün | 8,1 gün |
| 2028 | 2 m | 1° | %70,0 | %66,1 | %76,2 | %50,5 | 14,3 gün | 7,4 gün |
| 2027 | 0 m | 1° | %54,0 | %51,8 | %68,9 | %36,9 | 16,8 gün | 8,7 gün |
| 2027 | 10 m | 1° | %84,6 | %81,2 | %77,9 | %63,0 | 11,5 gün | 6,4 gün |

Düz ufuk ↔ gerçek arazi kartı (2027, 2 m, ikisi de 0° maske):

| | Düz ufuk | Gerçek arazi | Fark |
|---|---|---|---|
| Güneşli zaman | %51,0 | %68,1 | 17,1 puan |
| Dünya görünür | %67,6 | %78,8 | 11,2 puan |
| En uzun karanlık | 17,7 gün | 14,3 gün | −3,4 gün |

Olaylar ve örnek batarya (iniş 1 Oca 2027 00:00 UTC; 100 kWh, panel 2 kW, tüketim 0,5 kW; inişte dolu):

- İniş anında Dünya payı −0,65° (bağlantı yok); Güneş merkezi 0,39°.
- İlk olaylar: Gün 5 Güneş arazinin arkasına girdi · Gün 7 Dünya bağlantısı kuruldu · **Gün 10 Güneş doğdu**.
- 2027'de başlayan en uzun karanlık (olay akışı, birleştirilmiş): 29 Nis 2027 tarihinde başlar, 14,3 gün.
- 100 kWh: batarya 40,2 gün sonra biter → **Gün 41 görev durdu**.
- Veri sonuna (31 Ara 2028) kadar dayanan en küçük kapasite: **180 kWh** (170 kWh yetmez). 200 kWh'de en düşük düzey %13.
- "Güvenli iniş penceresi" (100 kWh): 19 Tem 2028 ve sonrası.

Mons Mouton Plateau örnek nokta, 2027, 2 m: Dünya 0° maskeyle %99,4, 1° payla %81,1; en uzun kesinti 1,2 gün → 5,5 gün.

## 4. NASA AVGVISIB haritalarıyla karşılaştırma (kaynak `ay-inis-navigatoru/docs/validation/avgvisib_comparison.json`, `avgvisib_resolution_diagnostic.json`)

2026-01-01 + 18.6 years, hourly; 54 nokta; ölçü: diskin herhangi bir kısmı. Fark = bizim − NASA, puan.

| Koşul | ort. fark | ort. mutlak fark | en büyük mutlak fark |
|---|---|---|---|
| Güneş · 0 m gözlemci, arazi verisi harita çözünürlüğünde (60/120 m) | −1,0 | 2,0 | 8,1 |
| Dünya · 0 m gözlemci, arazi verisi harita çözünürlüğünde | −0,8 | 1,6 | 13,2 |
| Güneş · 0 m gözlemci, 20 m arazi verisi | −5,4 | 6,0 | 25,9 |
| Dünya · 0 m gözlemci, 20 m arazi verisi | −7,2 | 7,4 | 29,1 |
| Güneş · 2 m gözlemci, 20 m arazi verisi (uygulamanın gösterdiği) | 3,4 | 3,6 | 17,3 |
| Dünya · 2 m gözlemci, 20 m arazi verisi | 1,6 | 1,9 | 17,6 |

Doğrulama cümlesi: yöntem, NASA haritasıyla aynı çözünürlükte ve aynı koşulda (0 m) ortalama 2,0 (Güneş) ve 1,6 (Dünya) puan içinde uyumludur. Uygulamadaki rakamlar 20 m arazi verisi ve 2 m gözlemci kullandığı için haritadan farklıdır (ortalama mutlak fark Güneş 3,6, Dünya 1,9 puan).

Yalnız dokuz örnek nokta, 0 m gözlemci, 20 m arazi verisi: ortalama mutlak fark Güneş 2,5, Dünya 3,6 puan (önceki turdaki "2,4 / 4,4 puan" ifadesinin bu veriyle karşılığı; o ifade 0 m içindi ve arayüzdeki 2 m rakamlarının yanında gösterilmemeliydi).

## 5. SPICE (DE440) ↔ mevcut 2027 serileri (kaynak `scripts/spice_check.py --points all` çıktısı)

54 nokta: en büyük fark yükseklikte 0,0005°, azimutta 0,005°, Dünya payında 0,001°, Güneş'in görünen oranında 0,0017. Bu bölüm betik çıktısından aktarılmıştır; bu dosya onu yeniden hesaplamaz.
