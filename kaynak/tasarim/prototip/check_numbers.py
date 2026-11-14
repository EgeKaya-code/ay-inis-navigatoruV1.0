"""Belgelerde geçen rakamları veriden yeniden hesaplar (arayüzden bağımsız bir Python hesabı) ve
tasarim/RAKAMLAR.md dosyasını yazar. Belgelere elle rakam yazılmaz: buradan alınır.

    python check_numbers.py            # RAKAMLAR.md'yi yeniden üret
    python check_numbers.py --check    # ayrıca DEMO_AKISI.md'deki her yüzde / gün rakamının burada üretildiğini denetle

Hesap, src/js/20-sim.js ile aynı kuralları izler (saatlik seri, 2 m dosyası; başka yükseklikte ufuk profili +
sabit 0,267° Güneş yarıçapı; olaylarda 6 saatten kısa durumlar birleştirilir; batarya saatlik enerji dengesi).
Tanımlar: "güneşli zaman" = diskin herhangi bir kısmının göründüğü zaman yüzdesi; "güneş enerjisi oranı" =
diskin görünen oranının ortalaması.
"""
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf8")
here = Path(__file__).resolve().parent
tas = here.parent
veri = tas / "veri"
repo_val = tas.parent / "ay-inis-navigatoru" / "docs" / "validation"
man = json.loads((veri / "years.json").read_text(encoding="utf8"))
YEARS = man["years"]
EPOCH = datetime(YEARS[0], 1, 1, tzinfo=timezone.utc)
SUN_R, MERGE_H = 0.267, 6
AY = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

num = lambda v, d=1: f"{v:.{d}f}".replace(".", ",").replace("-", "−")
pct = lambda v, d=1: "%" + num(v, d)
gun = lambda v: num(v) + " gün"
hour_of = lambda y, m, d, h=0: int((datetime(y, m, d, h, tzinfo=timezone.utc) - EPOCH).total_seconds() // 3600)
def date_of(h):
    t = datetime.fromtimestamp(EPOCH.timestamp() + h * 3600, tz=timezone.utc)
    return f"{t.day} {AY[t.month - 1]} {t.year}"


class Site:
    def __init__(self, sid):
        self.id, d = sid, veri / "sites" / sid
        ys = [json.loads((d / f"series_{y}.json").read_text()) for y in YEARS]
        cat = lambda k: np.concatenate([np.asarray(s[k], np.float32) for s in ys])
        self.sun_alt, self.sun_az, self.sun_frac = cat("sun_alt_deg"), cat("sun_az_deg"), cat("sun_visible_fraction")
        self.earth_alt, self.earth_az, self.earth_margin = cat("earth_alt_deg"), cat("earth_az_deg"), cat("earth_margin_deg")
        self.n, self.dir = self.sun_alt.size, d

    def horizon(self, h):
        hz = json.loads((self.dir / ("horizon.json" if h == 2 else f"horizon_{h}m.json")).read_text())
        assert hz["observer_height_m"] == h
        return np.asarray(hz["elevation_deg"], np.float32), hz["azimuth_step_deg"]

    def model(self, mask=1.0, flat=False, height=2):
        """20-sim.js buildModel: sunFrac, margin, sunUp, linkUp, both"""
        if flat:
            frac, margin = disc_above(self.sun_alt), self.earth_alt
        elif height == 2:
            frac, margin = self.sun_frac, self.earth_margin
        else:
            el, step = self.horizon(height)
            frac = disc_above(self.sun_alt - horizon_at(el, step, self.sun_az))
            margin = self.earth_alt - horizon_at(el, step, self.earth_az)
        sun_up, link_up = frac > 0, margin > np.float32(mask)
        return dict(frac=frac.astype(np.float32), margin=margin, sun=sun_up, link=link_up, both=sun_up & link_up, n=self.n)


def disc_above(alt, r=SUN_R):
    x = np.clip(np.asarray(alt, np.float64) / r, -1, 1)
    return np.where(alt >= r, 1.0, np.where(alt <= -r, 0.0, 0.5 + (x * np.sqrt(1 - x * x) + np.arcsin(x)) / math.pi)).astype(np.float32)


def horizon_at(el, step, az):
    x = (np.mod(np.asarray(az, np.float64), 360.0)) / step
    i = np.floor(x).astype(int)
    f = (x - i).astype(np.float32)
    n = el.size
    return el[i % n] + (el[(i + 1) % n] - el[i % n]) * f


def longest_off(flags):
    best = run = 0
    for v in flags:
        run = 0 if v else run + 1
        best = max(best, run)
    return best


def stats(m, a=0, b=None):
    b = m["n"] if b is None else b
    n = max(1, b - a)
    # işlem sırası arayüzle aynı: (sayı / n) * 100 (yuvarlama sınırındaki değerler aynı çıksın)
    f = lambda x: (float(x) / n) * 100
    return dict(sun=f(m["sun"][a:b].sum()), energy=f(m["frac"][a:b].astype(np.float64).sum()),
                earth=f(m["link"][a:b].sum()), both=f(m["both"][a:b].sum()),
                dark=longest_off(m["sun"][a:b]) / 24, gap=longest_off(m["link"][a:b]) / 24)


def until_change(flags, i):
    for j in range(i + 1, flags.size):
        if flags[j] != flags[i]:
            return j - i
    return None


def window(site, start, days, mask=1.0, height=2):
    """20-sim.js windowStats: inişten sonraki pencere"""
    m = site.model(mask, height=height)
    a = start
    b = min(m["n"], a + days * 24)
    st = stats(m, a, b)
    el, step = site.horizon(height)
    st.update(clipped=b - a < days * 24, sun_up=bool(m["sun"][a]), link_up=bool(m["link"][a]), disc=float(m["frac"][a]),
              sun_margin=float(site.sun_alt[a] - horizon_at(el, step, site.sun_az[a:a + 1])[0]), earth_margin=float(m["margin"][a]),
              sun_change=until_change(m["sun"], a), link_change=until_change(m["link"], a))
    return st


def merged_runs(flags):
    """20-sim.js runsOf + mergeRuns: 6 saatten kısa durumlar atılır, komşular birleşir. Dönen: [(başlangıç, durum)]"""
    edges = np.flatnonzero(np.diff(flags.astype(np.int8))) + 1
    starts = np.concatenate([[0], edges])
    lens = np.diff(np.concatenate([starts, [flags.size]]))
    out = []
    for s, ln in zip(starts, lens):
        if ln >= MERGE_H and (not out or out[-1][1] != bool(flags[s])):
            out.append((int(s), bool(flags[s])))
    out[0] = (0, out[0][1])
    return out


def battery(m, cap, panel, load, start):
    e, dead, lo = cap, -1, cap
    for i in range(start, m["n"]):
        e = min(cap, max(0.0, e + panel * float(m["frac"][i]) - load))
        lo = min(lo, e)
        if e <= 0 and dead < 0:
            dead = i + 1
    return dead, 100 * lo / cap


def survives(m, cap, panel, load, start):
    e = cap
    for i in range(start, m["n"]):
        e = min(cap, e + panel * float(m["frac"][i]) - load)
        if e <= 0:
            return False
    return True


def main():
    L = []  # RAKAMLAR.md satırları
    vals = set()  # belgelerde kullanılabilecek biçimlenmiş değerler

    def v(s):
        vals.add(s)
        return s

    P, G = (lambda x: v(pct(x))), (lambda x: v(gun(x)))
    cand = json.loads((veri / "candidates.json").read_text(encoding="utf8"))
    L += ["# Belgelerde kullanılan rakamlar", "",
          "Üreten: `prototip/check_numbers.py` (arayüzden bağımsız Python hesabı; elle değiştirmeyin, yeniden üretin). "
          f"Veri: `veri/` · yıllar {', '.join(map(str, YEARS))} · varsayılan gözlemci 2 m, anten payı 1°.", "",
          "Tanımlar: **güneşli zaman** = Güneş diskinin herhangi bir kısmının göründüğü zaman yüzdesi; **güneş enerjisi oranı** = "
          "diskin görünen oranının ortalaması; **Dünya** = merkezi arazi ufkunun anten payı kadar üstünde; "
          "**ortak** = Güneş görünür ve Dünya bağlantısı var.", ""]

    # 1. brifing kartları
    L += ["## 1. Brifing kartları (2026–2030, 2 m; kaynak `candidates.json`, her bölgenin 1. adayı)", "",
          "\"En çok güç\" sırası (1. adayın güneş enerjisi oranına göre):", "",
          "| Sıra | Bölge | Güneşli zaman | Dünya · 1° | En uzun karanlık | Enerji oranı |", "|---|---|---|---|---|---|"]
    tops = []
    for r in cand["regions"]:
        c = next(c for c in r["candidates"] if c["rank"] == 1)
        m = c["metrics"]["2m"]
        tops.append((m["terrain"]["sun_energy_pct"], r["region"], m["terrain"]["sun_any_pct"], m["terrain_antenna_1deg"]["earth_pct"], m["terrain"]["longest_dark_days"]))
    for i, (en, name, sun, earth, dark) in enumerate(sorted(tops, reverse=True), 1):
        L.append(f"| {i} | {name} · aday 1 | {P(sun)} | {P(earth)} | {G(dark)} | {P(en)} |")

    # 2. karşılaştırma senaryoları
    def scen(sid, y, mo, d, days=30):
        return window(Site(sid), hour_of(y, mo, d), days)

    demo = [("A", "Malapert Massif · örnek nokta · 1 Mar 2027", scen("malapert_massif", 2027, 3, 1)),
            ("B", "Malapert Massif · örnek nokta · 15 Mar 2027", scen("malapert_massif", 2027, 3, 15)),
            ("C", "Malapert Massif · aday 1 · 15 Mar 2027", scen("malapert_massif__c1", 2027, 3, 15)),
            ("–", "Mons Mouton Plateau · aday 1 · 15 Mar 2027", scen("mons_mouton_plateau__c1", 2027, 3, 15)),
            ("–", "de Gerlache Rim 2 · aday 1 · 15 Mar 2027", scen("de_gerlache_rim_2__c1", 2027, 3, 15)),
            ("–", "Malapert Massif · örnek nokta · 10 Ara 2028", scen("malapert_massif", 2028, 12, 10))]
    rel = lambda x: v(num(abs(x), 2) + "°") + (" üstünde" if x >= 0 else " altında")
    dur = lambda h: "değişmiyor" if h is None else (v(f"{h} saat") if h < 48 else G(h / 24))
    L += ["", "## 2. Karşılaştırma ekranı (inişten sonraki 30 gün, 2 m, 1° pay; kaynak `series_YYYY.json`, `horizon.json`)", "",
          "| | Senaryo | Güneşli zaman | Dünya görünür | Güneş + Dünya | En uzun karanlık | En uzun bağlantısız | İnişte Güneş | İnişte Dünya |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, name, s in demo:
        sun0 = f"ufkun {rel(s['sun_margin'])}, disk {v(pct(s['disc'] * 100, 0))}; " + ("karanlığa " if s["sun_up"] else "karanlık, ışığa ") + dur(s["sun_change"])
        e0 = f"ufkun {rel(s['earth_margin'])}; " + ("bağlantı var, kesilmeye " if s["link_up"] else "bağlantı yok, bağlantıya ") + dur(s["link_change"])
        clip = " (pencere kırpıldı)" if s["clipped"] else ""
        L.append(f"| {k} | {name}{clip} | {P(s['sun'])} | {P(s['earth'])} | {P(s['both'])} | {G(s['dark'])} | {G(s['gap'])} | {sun0} | {e0} |")
    A, B, C = demo[0][2], demo[1][2], demo[2][2]
    L += ["", f"Özet cümlesi (A, B, C): en yüksek ortak pencere C. C − A = {v(num(C['both'] - A['both']))} puan ({P(C['both'])} ↔ {P(A['both'])}); "
              f"en uzun karanlık farkı {v(num(abs(C['dark'] - A['dark'])))} gün ({'daha kısa' if C['dark'] < A['dark'] else 'daha uzun'}). "
              f"B − A = {v(num(B['both'] - A['both']))} puan.",
          f"Kırpılan pencere örneği: 10 Ara 2028 inişinde 30 günün {v(num((hour_of(YEARS[-1] + 1, 1, 1) - hour_of(2028, 12, 10)) / 24))} günü var."]
    reg = next(r for r in cand["regions"] if r["id"] == "malapert_massif")
    p0, p1 = next(c for c in reg["candidates"] if c["legacy"]), next(c for c in reg["candidates"] if c["rank"] == 1)
    hav = lambda a, b: 2 * 1737.4 * math.asin(math.sqrt(math.sin(math.radians(b["lat"] - a["lat"]) / 2) ** 2 + math.cos(math.radians(a["lat"]))
                                                       * math.cos(math.radians(b["lat"])) * math.sin(math.radians(b["lon"] - a["lon"]) / 2) ** 2))
    L += [f"Malapert Massif örnek nokta ↔ aday 1 arası uzaklık: {v(num(hav(p0, p1)))} km (kaynak `candidates.json` enlem/boylam, R = 1737,4 km)."]

    # 3. kokpit: Malapert örnek nokta
    ma = Site("malapert_massif")
    yr = lambda y: (hour_of(y, 1, 1), hour_of(y + 1, 1, 1))
    L += ["", "## 3. Kokpit: Malapert Massif örnek nokta (seçili yılın tamamı; kaynak `series_YYYY.json`, `horizon*.json`)", "",
          "| Yıl | Gözlemci | Anten payı | Güneşli zaman | Enerji oranı | Dünya | Ortak | En uzun karanlık | En uzun kesinti |", "|---|---|---|---|---|---|---|---|---|"]
    for y, h, mk in [(2027, 2, 1), (2027, 2, 0), (2027, 2, 2), (2026, 2, 1), (2028, 2, 1), (2027, 0, 1), (2027, 10, 1)]:
        s = stats(ma.model(mk, height=h), *yr(y))
        L.append(f"| {y} | {h} m | {mk}° | {P(s['sun'])} | {P(s['energy'])} | {P(s['earth'])} | {P(s['both'])} | {G(s['dark'])} | {G(s['gap'])} |")
    f0, t0 = stats(ma.model(0, flat=True), *yr(2027)), stats(ma.model(0), *yr(2027))
    L += ["", "Düz ufuk ↔ gerçek arazi kartı (2027, 2 m, ikisi de 0° maske):", "",
          "| | Düz ufuk | Gerçek arazi | Fark |", "|---|---|---|---|",
          f"| Güneşli zaman | {P(f0['sun'])} | {P(t0['sun'])} | {v(num(t0['sun'] - f0['sun']))} puan |",
          f"| Dünya görünür | {P(f0['earth'])} | {P(t0['earth'])} | {v(num(t0['earth'] - f0['earth']))} puan |",
          f"| En uzun karanlık | {G(f0['dark'])} | {G(t0['dark'])} | {v(num(t0['dark'] - f0['dark']))} gün |"]

    # olaylar ve batarya: iniş 1 Ocak 2027 00:00, örnek batarya 100 kWh / 2 kW / 0,5 kW
    m1 = ma.model(1)
    land = hour_of(2027, 1, 1)
    sun_runs, link_runs = merged_runs(m1["sun"]), merged_runs(m1["link"])
    first_rise = next(s for s, on in sun_runs if on and s > land)
    first_dark = next(s for s, on in sun_runs if not on and s > land)
    first_link = next(s for s, on in link_runs if on and s > land)
    dead, _ = battery(m1, 100, 2, 0.5, land)
    mincap = next(c for c in range(10, 601, 10) if survives(m1, c, 2, 0.5, land))
    _, lo200 = battery(m1, 200, 2, 0.5, land)
    days = m1["n"] // 24
    safe = next((d for d in range(days) if survives(m1, 100, 2, 0.5, d * 24)), None)
    y27 = yr(2027)
    darks = [(s, (sun_runs[i + 1][0] if i + 1 < len(sun_runs) else m1["n"]) - s) for i, (s, on) in enumerate(sun_runs) if not on and y27[0] <= s < y27[1]]
    ld = max(darks, key=lambda x: x[1])
    L += ["", "Olaylar ve örnek batarya (iniş 1 Oca 2027 00:00 UTC; 100 kWh, panel 2 kW, tüketim 0,5 kW; inişte dolu):", "",
          f"- İniş anında Dünya payı {v(num(float(m1['margin'][land]), 2) + '°')} (bağlantı yok); Güneş merkezi {v(num(float(ma.sun_alt[land]), 2) + '°')}.",
          f"- İlk olaylar: Gün {(first_dark - land) // 24 + 1} Güneş arazinin arkasına girdi · Gün {(first_link - land) // 24 + 1} Dünya bağlantısı kuruldu · "
          f"**Gün {(first_rise - land) // 24 + 1} Güneş doğdu**.",
          f"- 2027'de başlayan en uzun karanlık (olay akışı, birleştirilmiş): {date_of(ld[0])} tarihinde başlar, {G(ld[1] / 24)}.",
          f"- 100 kWh: batarya {v(num((dead - land) / 24))} gün sonra biter → **Gün {(dead - land) // 24 + 1} görev durdu**.",
          f"- Veri sonuna ({date_of(m1['n'] - 1)}) kadar dayanan en küçük kapasite: **{mincap} kWh** ({mincap - 10} kWh yetmez). 200 kWh'de en düşük düzey {v(pct(lo200, 0))}.",
          f"- \"Güvenli iniş penceresi\" (100 kWh): {date_of(safe * 24) if safe is not None else 'yok'} ve sonrası."]
    mp = Site("mons_mouton_plateau")
    a, b = stats(mp.model(0), *yr(2027)), stats(mp.model(1), *yr(2027))
    L += ["", f"Mons Mouton Plateau örnek nokta, 2027, 2 m: Dünya 0° maskeyle {P(a['earth'])}, 1° payla {P(b['earth'])}; en uzun kesinti {G(a['gap'])} → {G(b['gap'])}."]

    # 4. doğrulama
    cmp_ = json.loads((repo_val / "avgvisib_comparison.json").read_text(encoding="utf8"))
    dg = json.loads((repo_val / "avgvisib_resolution_diagnostic.json").read_text(encoding="utf8"))["summary_ours_minus_nasa"]
    S = cmp_["summary_ours_minus_nasa"]
    row = lambda name, s: f"| {name} | {v(num(s['mean']))} | {v(num(s['mean_abs']))} | {v(num(s['max_abs']))} |"
    legacy = [p for p in cmp_["points"] if p["point"] == "sample"]
    ma_ = lambda key, ref: float(np.mean([abs(p[key] - p[ref]) for p in legacy]))
    L += ["", "## 4. NASA AVGVISIB haritalarıyla karşılaştırma (kaynak `ay-inis-navigatoru/docs/validation/avgvisib_comparison.json`, "
              "`avgvisib_resolution_diagnostic.json`)", "",
          f"{cmp_['ours']['period']}; {len(cmp_['points'])} nokta; ölçü: diskin herhangi bir kısmı. Fark = bizim − NASA, puan.", "",
          "| Koşul | ort. fark | ort. mutlak fark | en büyük mutlak fark |", "|---|---|---|---|",
          row("Güneş · 0 m gözlemci, arazi verisi harita çözünürlüğünde (60/120 m)", dg["sun_0m_coarse_dem"]),
          row("Dünya · 0 m gözlemci, arazi verisi harita çözünürlüğünde", dg["earth_0m_coarse_dem"]),
          row("Güneş · 0 m gözlemci, 20 m arazi verisi", S["sun_0m"]), row("Dünya · 0 m gözlemci, 20 m arazi verisi", S["earth_0m"]),
          row("Güneş · 2 m gözlemci, 20 m arazi verisi (uygulamanın gösterdiği)", S["sun_2m"]), row("Dünya · 2 m gözlemci, 20 m arazi verisi", S["earth_2m"]),
          "", "Doğrulama cümlesi: yöntem, NASA haritasıyla aynı çözünürlükte ve aynı koşulda (0 m) ortalama "
              f"{v(num(dg['sun_0m_coarse_dem']['mean_abs']))} (Güneş) ve {v(num(dg['earth_0m_coarse_dem']['mean_abs']))} (Dünya) puan içinde uyumludur. "
              "Uygulamadaki rakamlar 20 m arazi verisi ve 2 m gözlemci kullandığı için haritadan farklıdır "
              f"(ortalama mutlak fark Güneş {v(num(S['sun_2m']['mean_abs']))}, Dünya {v(num(S['earth_2m']['mean_abs']))} puan).",
          "", f"Yalnız dokuz örnek nokta, 0 m gözlemci, 20 m arazi verisi: ortalama mutlak fark Güneş {v(num(ma_('sun_0m', 'nasa_sun_pct')))}, "
              f"Dünya {v(num(ma_('earth_0m', 'nasa_earth_pct')))} puan (önceki turdaki \"2,4 / 4,4 puan\" ifadesinin bu veriyle karşılığı; "
              "o ifade 0 m içindi ve arayüzdeki 2 m rakamlarının yanında gösterilmemeliydi).",
          "", "## 5. SPICE (DE440) ↔ mevcut 2027 serileri (kaynak `scripts/spice_check.py --points all` çıktısı)", "",
          "54 nokta: en büyük fark yükseklikte 0,0005°, azimutta 0,005°, Dünya payında 0,001°, Güneş'in görünen oranında 0,0017. "
          "Bu bölüm betik çıktısından aktarılmıştır; bu dosya onu yeniden hesaplamaz.", ""]
    (tas / "RAKAMLAR.md").write_text("\n".join(L), encoding="utf8", newline="\n")
    print(f"RAKAMLAR.md yazıldı ({len(vals)} farklı değer)")

    if "--check" in sys.argv:
        doc = (tas / "DEMO_AKISI.md").read_text(encoding="utf8")
        toks = set(re.findall(r"%\d+(?:,\d)?", doc)) | set(re.findall(r"\d+,\d gün", doc))
        plain = {t for t in vals} | {t.replace(" gün", "") for t in vals}
        ok_pct = {t for t in toks if t in plain or t.replace(" gün", "") in plain or t.rstrip("0").rstrip(",") in plain}
        # tam sayıya yuvarlanmış yüzdeler (ör. %13) ve "X,Y gün" biçimleri
        ints = {"%" + num(float(t[1:].replace(",", ".")), 0) for t in plain if t.startswith("%")}
        missing = sorted(t for t in toks if t not in ok_pct and t not in ints)
        print("DEMO_AKISI.md:", len(toks), "rakam;", "hepsi RAKAMLAR.md'de üretiliyor" if not missing else "ÜRETİLMEYEN: " + ", ".join(missing))
        sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
