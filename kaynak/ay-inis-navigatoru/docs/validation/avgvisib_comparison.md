# NASA AVGVISIB haritalarıyla karşılaştırma

Üreten: `scripts/validate_avgvisib.py`. Dönem (bizim): 2026-01-01 + 18.6 years, hourly (163048 adım). Ölçü: diskin **herhangi bir kısmının** arazi ufkunun üstünde olduğu zaman yüzdesi (NASA haritasının tanımı).

NASA haritası 0 m gözlemci içindir. **0 m** sütunu gözlemci yüksekliği bakımından eşleşen koşuldur (arazi verisinin çözünürlüğü haritadan ince: aşağıdaki tanıya bakın); **2 m** sütunu uygulamanın gösterdiği profildir ve haritanın koşulu değildir. Fark = bizim − NASA (puan). Hiçbir düzeltme uygulanmadı.

## Özet (54 nokta)

| | ort. fark | ort. mutlak fark | en büyük mutlak fark |
|---|---|---|---|
| Güneş, 0 m (eşleşen koşul) | -5.4 | 6.0 | 25.9 |
| Güneş, 2 m | +3.4 | 3.6 | 17.3 |
| Dünya, 0 m (eşleşen koşul) | -7.2 | 7.4 | 29.1 |
| Dünya, 2 m | +1.6 | 1.9 | 17.6 |

## Güneş (%)

| Nokta | Harita | NASA | Bizim 0 m | Fark 0 m | Bizim 2 m | Fark 2 m |
|---|---|---|---|---|---|---|
| Nobile Rim 2 · candidate 1 | 75S_120M | 50.6 | 48.1 | -2.5 | 51.9 | +1.3 |
| Nobile Rim 2 · candidate 2 | 75S_120M | 50.2 | 49.4 | -0.8 | 50.1 | -0.1 |
| Nobile Rim 2 · candidate 3 | 75S_120M | 49.4 | 48.5 | -0.9 | 49.3 | -0.1 |
| Nobile Rim 2 · candidate 4 | 75S_120M | 48.9 | 47.9 | -1.0 | 48.9 | -0.0 |
| Nobile Rim 2 · candidate 5 | 75S_120M | 48.9 | 45.6 | -3.3 | 48.8 | -0.1 |
| Nobile Rim 2 · sample | 75S_120M | 50.6 | 49.2 | -1.4 | 51.7 | +1.1 |
| Mons Mouton · candidate 1 | 85S_060M | 57.9 | 51.6 | -6.3 | 58.6 | +0.7 |
| Mons Mouton · candidate 2 | 85S_060M | 52.1 | 50.7 | -1.4 | 55.0 | +3.0 |
| Mons Mouton · candidate 3 | 85S_060M | 53.2 | 50.8 | -2.4 | 54.9 | +1.7 |
| Mons Mouton · candidate 4 | 85S_060M | 56.4 | 51.8 | -4.5 | 58.0 | +1.7 |
| Mons Mouton · candidate 5 | 85S_060M | 52.4 | 49.2 | -3.2 | 53.5 | +1.1 |
| Mons Mouton · sample | 85S_060M | 59.3 | 56.5 | -2.8 | 68.8 | +9.6 |
| Malapert Massif · candidate 1 | 85S_060M | 58.4 | 56.1 | -2.3 | 66.3 | +7.9 |
| Malapert Massif · candidate 2 | 85S_060M | 58.3 | 57.8 | -0.5 | 65.9 | +7.5 |
| Malapert Massif · candidate 3 | 85S_060M | 68.4 | 53.4 | -15.0 | 77.0 | +8.6 |
| Malapert Massif · candidate 4 | 85S_060M | 58.5 | 53.8 | -4.7 | 60.5 | +1.9 |
| Malapert Massif · candidate 5 | 85S_060M | 58.1 | 44.9 | -13.1 | 58.5 | +0.5 |
| Malapert Massif · sample | 85S_060M | 55.5 | 55.1 | -0.4 | 68.9 | +13.5 |
| de Gerlache Rim 2 · candidate 1 | 85S_060M | 73.5 | 80.3 | +6.8 | 82.9 | +9.4 |
| de Gerlache Rim 2 · candidate 2 | 85S_060M | 70.1 | 57.2 | -13.0 | 76.1 | +5.9 |
| de Gerlache Rim 2 · candidate 3 | 85S_060M | 74.5 | 48.5 | -25.9 | 78.5 | +4.0 |
| de Gerlache Rim 2 · candidate 4 | 85S_060M | 67.0 | 61.2 | -5.8 | 70.0 | +3.0 |
| de Gerlache Rim 2 · candidate 5 | 85S_060M | 63.0 | 62.2 | -0.8 | 70.1 | +7.0 |
| de Gerlache Rim 2 · sample | 85S_060M | 45.7 | 49.5 | +3.7 | 63.1 | +17.3 |
| Mons Mouton Plateau · candidate 1 | 75S_120M | 61.0 | 59.4 | -1.7 | 72.2 | +11.1 |
| Mons Mouton Plateau · candidate 2 | 75S_120M | 57.0 | 49.6 | -7.4 | 58.1 | +1.1 |
| Mons Mouton Plateau · candidate 3 | 75S_120M | 61.8 | 52.2 | -9.6 | 62.8 | +0.9 |
| Mons Mouton Plateau · candidate 4 | 75S_120M | 58.6 | 52.8 | -5.8 | 58.2 | -0.4 |
| Mons Mouton Plateau · candidate 5 | 85S_060M | 62.0 | 48.3 | -13.7 | 65.1 | +3.1 |
| Mons Mouton Plateau · sample | 75S_120M | 52.1 | 51.3 | -0.8 | 52.8 | +0.7 |
| Slater Plain · candidate 1 | 85S_060M | 62.2 | 57.8 | -4.4 | 65.5 | +3.4 |
| Slater Plain · candidate 2 | 85S_060M | 65.8 | 51.9 | -13.9 | 66.9 | +1.1 |
| Slater Plain · candidate 3 | 85S_060M | 59.9 | 54.7 | -5.3 | 64.0 | +4.1 |
| Slater Plain · candidate 4 | 85S_060M | 63.6 | 56.2 | -7.5 | 66.4 | +2.7 |
| Slater Plain · candidate 5 | 85S_060M | 57.8 | 49.6 | -8.3 | 59.7 | +1.9 |
| Slater Plain · sample | 85S_060M | 60.4 | 62.7 | +2.3 | 66.7 | +6.3 |
| Peak Near Cabeus B · candidate 1 | 75S_120M | 55.6 | 51.9 | -3.7 | 56.2 | +0.6 |
| Peak Near Cabeus B · candidate 2 | 75S_120M | 55.5 | 53.5 | -2.0 | 55.2 | -0.3 |
| Peak Near Cabeus B · candidate 3 | 75S_120M | 55.6 | 48.8 | -6.8 | 54.7 | -0.9 |
| Peak Near Cabeus B · candidate 4 | 75S_120M | 51.4 | 50.7 | -0.7 | 54.8 | +3.5 |
| Peak Near Cabeus B · candidate 5 | 75S_120M | 52.7 | 47.3 | -5.3 | 52.0 | -0.7 |
| Peak Near Cabeus B · sample | 75S_120M | 61.4 | 57.2 | -4.3 | 66.0 | +4.6 |
| Nobile Rim 1 · candidate 1 | 85S_060M | 61.0 | 56.4 | -4.6 | 68.0 | +7.0 |
| Nobile Rim 1 · candidate 2 | 85S_060M | 59.7 | 54.4 | -5.3 | 64.0 | +4.3 |
| Nobile Rim 1 · candidate 3 | 85S_060M | 62.5 | 52.4 | -10.0 | 63.5 | +1.0 |
| Nobile Rim 1 · candidate 4 | 85S_060M | 61.0 | 51.2 | -9.8 | 60.1 | -0.9 |
| Nobile Rim 1 · candidate 5 | 85S_060M | 57.1 | 54.5 | -2.6 | 59.8 | +2.7 |
| Nobile Rim 1 · sample | 85S_060M | 63.0 | 66.2 | +3.2 | 68.2 | +5.2 |
| Haworth · candidate 1 | 85S_060M | 66.2 | 54.0 | -12.2 | 69.6 | +3.4 |
| Haworth · candidate 2 | 85S_060M | 57.3 | 45.1 | -12.2 | 57.7 | +0.3 |
| Haworth · candidate 3 | 85S_060M | 49.0 | 44.6 | -4.4 | 52.3 | +3.3 |
| Haworth · candidate 4 | 85S_060M | 56.2 | 41.5 | -14.7 | 55.7 | -0.6 |
| Haworth · candidate 5 | 85S_060M | 61.3 | 44.3 | -17.1 | 63.8 | +2.5 |
| Haworth · sample | 85S_060M | 10.5 | 7.0 | -3.5 | 17.6 | +7.1 |

## Dünya (%)

Uygulamadaki Dünya rakamı disk **merkezine** göredir; NASA haritası diskin herhangi bir kısmına göre. Karşılaştırma sütunları haritanın ölçüsüyle hesaplandı; merkez ölçüsü ayrıca verildi.

| Nokta | Harita | NASA | Bizim 0 m | Fark 0 m | Bizim 2 m | Fark 2 m | Merkez, 2 m |
|---|---|---|---|---|---|---|---|
| Nobile Rim 2 · candidate 1 | 75S_120M | 80.8 | 65.3 | -15.5 | 80.7 | -0.1 | 73.7 |
| Nobile Rim 2 · candidate 2 | 75S_120M | 88.0 | 69.3 | -18.7 | 88.4 | +0.4 | 78.0 |
| Nobile Rim 2 · candidate 3 | 75S_120M | 88.0 | 88.4 | +0.4 | 88.4 | +0.4 | 77.9 |
| Nobile Rim 2 · candidate 4 | 75S_120M | 88.0 | 88.4 | +0.4 | 88.4 | +0.4 | 78.0 |
| Nobile Rim 2 · candidate 5 | 75S_120M | 88.0 | 88.4 | +0.4 | 88.4 | +0.4 | 78.0 |
| Nobile Rim 2 · sample | 75S_120M | 80.8 | 80.7 | -0.1 | 80.7 | -0.0 | 73.7 |
| Mons Mouton · candidate 1 | 85S_060M | 99.9 | 99.9 | +0.0 | 100.0 | +0.0 | 92.4 |
| Mons Mouton · candidate 2 | 85S_060M | 99.0 | 80.1 | -18.9 | 99.8 | +0.8 | 92.5 |
| Mons Mouton · candidate 3 | 85S_060M | 100.0 | 83.2 | -16.8 | 100.0 | +0.0 | 94.0 |
| Mons Mouton · candidate 4 | 85S_060M | 99.7 | 99.6 | -0.1 | 99.7 | -0.0 | 85.9 |
| Mons Mouton · candidate 5 | 85S_060M | 100.0 | 95.5 | -4.5 | 100.0 | +0.0 | 93.9 |
| Mons Mouton · sample | 85S_060M | 82.3 | 76.5 | -5.8 | 100.0 | +17.6 | 89.9 |
| Malapert Massif · candidate 1 | 85S_060M | 100.0 | 99.9 | -0.1 | 100.0 | +0.0 | 100.0 |
| Malapert Massif · candidate 2 | 85S_060M | 99.5 | 100.0 | +0.5 | 100.0 | +0.5 | 100.0 |
| Malapert Massif · candidate 3 | 85S_060M | 90.7 | 69.5 | -21.2 | 100.0 | +9.3 | 100.0 |
| Malapert Massif · candidate 4 | 85S_060M | 100.0 | 87.0 | -13.0 | 100.0 | +0.0 | 100.0 |
| Malapert Massif · candidate 5 | 85S_060M | 100.0 | 100.0 | +0.0 | 100.0 | +0.0 | 100.0 |
| Malapert Massif · sample | 85S_060M | 87.6 | 84.4 | -3.2 | 93.8 | +6.2 | 81.4 |
| de Gerlache Rim 2 · candidate 1 | 85S_060M | 61.6 | 61.6 | -0.0 | 61.6 | +0.0 | 56.9 |
| de Gerlache Rim 2 · candidate 2 | 85S_060M | 61.4 | 46.6 | -14.8 | 61.2 | -0.2 | 56.5 |
| de Gerlache Rim 2 · candidate 3 | 85S_060M | 61.8 | 60.0 | -1.8 | 61.7 | -0.0 | 56.9 |
| de Gerlache Rim 2 · candidate 4 | 85S_060M | 60.3 | 60.1 | -0.2 | 61.3 | +0.9 | 56.5 |
| de Gerlache Rim 2 · candidate 5 | 85S_060M | 57.0 | 55.0 | -2.0 | 59.8 | +2.9 | 55.2 |
| de Gerlache Rim 2 · sample | 85S_060M | 61.7 | 61.8 | +0.0 | 61.8 | +0.1 | 57.0 |
| Mons Mouton Plateau · candidate 1 | 75S_120M | 100.0 | 70.9 | -29.1 | 100.0 | +0.0 | 96.9 |
| Mons Mouton Plateau · candidate 2 | 75S_120M | 100.0 | 100.0 | +0.0 | 100.0 | +0.0 | 100.0 |
| Mons Mouton Plateau · candidate 3 | 75S_120M | 100.0 | 74.9 | -25.1 | 100.0 | +0.0 | 94.3 |
| Mons Mouton Plateau · candidate 4 | 75S_120M | 100.0 | 89.7 | -10.3 | 100.0 | +0.0 | 99.8 |
| Mons Mouton Plateau · candidate 5 | 85S_060M | 85.3 | 76.4 | -8.9 | 100.0 | +14.7 | 94.7 |
| Mons Mouton Plateau · sample | 75S_120M | 87.3 | 89.9 | +2.6 | 100.0 | +12.7 | 91.2 |
| Slater Plain · candidate 1 | 85S_060M | 48.8 | 48.7 | -0.1 | 49.6 | +0.8 | 45.0 |
| Slater Plain · candidate 2 | 85S_060M | 49.8 | 45.9 | -3.9 | 49.7 | -0.1 | 45.2 |
| Slater Plain · candidate 3 | 85S_060M | 48.9 | 45.9 | -3.1 | 48.9 | -0.1 | 44.3 |
| Slater Plain · candidate 4 | 85S_060M | 49.5 | 46.9 | -2.6 | 49.4 | -0.1 | 44.9 |
| Slater Plain · candidate 5 | 85S_060M | 50.0 | 49.9 | -0.1 | 49.9 | -0.1 | 45.4 |
| Slater Plain · sample | 85S_060M | 48.1 | 48.2 | +0.1 | 49.6 | +1.6 | 45.1 |
| Peak Near Cabeus B · candidate 1 | 75S_120M | 96.7 | 85.1 | -11.6 | 99.1 | +2.4 | 90.6 |
| Peak Near Cabeus B · candidate 2 | 75S_120M | 98.4 | 90.4 | -8.0 | 98.2 | -0.3 | 90.0 |
| Peak Near Cabeus B · candidate 3 | 75S_120M | 99.1 | 83.3 | -15.9 | 98.8 | -0.4 | 90.4 |
| Peak Near Cabeus B · candidate 4 | 75S_120M | 92.6 | 75.2 | -17.4 | 93.5 | +0.9 | 82.6 |
| Peak Near Cabeus B · candidate 5 | 75S_120M | 98.7 | 70.6 | -28.1 | 98.4 | -0.3 | 90.0 |
| Peak Near Cabeus B · sample | 75S_120M | 96.8 | 76.4 | -20.5 | 99.3 | +2.5 | 90.7 |
| Nobile Rim 1 · candidate 1 | 85S_060M | 82.2 | 80.4 | -1.8 | 88.0 | +5.8 | 78.8 |
| Nobile Rim 1 · candidate 2 | 85S_060M | 88.1 | 87.0 | -1.2 | 88.3 | +0.2 | 79.0 |
| Nobile Rim 1 · candidate 3 | 85S_060M | 84.8 | 85.5 | +0.7 | 85.7 | +0.9 | 77.3 |
| Nobile Rim 1 · candidate 4 | 85S_060M | 87.2 | 83.0 | -4.2 | 86.9 | -0.3 | 78.1 |
| Nobile Rim 1 · candidate 5 | 85S_060M | 94.1 | 92.8 | -1.4 | 93.9 | -0.2 | 81.5 |
| Nobile Rim 1 · sample | 85S_060M | 72.4 | 72.8 | +0.4 | 75.2 | +2.8 | 69.2 |
| Haworth · candidate 1 | 85S_060M | 59.9 | 47.3 | -12.5 | 63.5 | +3.6 | 58.7 |
| Haworth · candidate 2 | 85S_060M | 80.6 | 58.5 | -22.1 | 79.2 | -1.4 | 72.5 |
| Haworth · candidate 3 | 85S_060M | 75.8 | 62.0 | -13.8 | 74.6 | -1.1 | 68.8 |
| Haworth · candidate 4 | 85S_060M | 79.9 | 62.8 | -17.0 | 74.7 | -5.1 | 68.9 |
| Haworth · candidate 5 | 85S_060M | 76.9 | 76.5 | -0.4 | 80.7 | +3.8 | 73.7 |
| Haworth · sample | 85S_060M | 29.9 | 29.8 | -0.1 | 31.3 | +1.4 | 25.5 |

IMG okuyucu denetimi: aynı haritanın kullanıldığı 53 noktada `candidates.json` içindeki NASA değerleriyle en büyük fark 0.0000 puan.

## Tanı: DEM çözünürlüğü

Üreten: `scripts/diag_resolution.py`. Bu bir düzeltme değil, tanıdır; uygulamanın verisi değişmedi. NASA haritaları 60 m ve 120 m ızgaralarda hesaplanmıştır; bizim profiller ilk 10 km için 20 m DEM kullanır. Burada 20 m DEM, karşılaştırılan haritanın çözünürlüğüne (haritanın piksel ızgarasına hizalı blok ortalamasıyla) indirildi ve 0 m profili onunla yeniden hesaplandı.

| 0 m gözlemci | ort. fark | ort. mutlak fark | en büyük mutlak fark |
|---|---|---|---|
| Güneş, 20 m DEM | -5.4 | 6.0 | 25.9 |
| Güneş, harita çözünürlüğünde DEM | -1.0 | 2.0 | 8.1 |
| Dünya, 20 m DEM | -7.2 | 7.4 | 29.1 |
| Dünya, harita çözünürlüğünde DEM | -0.8 | 1.6 | 13.2 |
