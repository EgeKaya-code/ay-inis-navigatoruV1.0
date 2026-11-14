// ===== sim: tarayıcıdaki gerçek hesap (saf fonksiyonlar, DOM yok) =====
const Sim = (() => {
  const SUN_R = 0.267;      // Güneş açısal yarıçapı (°)
  const EARTH_R = 0.95;     // Dünya açısal yarıçapı (°)
  const MERGE_H = 6;        // bundan kısa durumlar komşusuyla birleştirilir
  const LONG_DARK_H = 72;   // bundan uzun karanlıklar vurgulanır
  const DARK_CAP_DAYS = 30; // dengeli puanda karanlığın 0 puan aldığı süre

  // yarıçapı r olan diskin, düz ufkun (0°) üstünde kalan alan oranı
  function discAbove(alt, r = SUN_R) {
    if (alt >= r) return 1;
    if (alt <= -r) return 0;
    const x = alt / r;
    return 0.5 + (x * Math.sqrt(1 - x * x) + Math.asin(x)) / Math.PI;
  }

  function horizonAt(hz, az) {
    const n = hz.elev.length;
    const x = (((az % 360) + 360) % 360) / hz.step;
    const i = Math.floor(x), f = x - i;
    return hz.elev[i % n] + (hz.elev[(i + 1) % n] - hz.elev[i % n]) * f;
  }
  function horizonDistAt(hz, az) {
    const n = hz.dist.length;
    return hz.dist[Math.round((((az % 360) + 360) % 360) / hz.step) % n];
  }

  // Dosyadaki seri 2 m gözlemci için hesaplanmıştır. Başka bir gözlemci yüksekliğinin ufuk profili seçilince
  // Güneş'in görünen oranı ve Dünya payı aynı alt/az serisinden, o profille yeniden hesaplanır (Güneş ve Dünya'nın
  // yönü birkaç metrelik yükseklik farkıyla değişmez). Güneş yarıçapı burada sabit 0,267° alınır.
  function forHorizon(site, hz) {
    if (hz.observer === site.series.observer) return { sunFrac: site.series.sunFrac, margin: site.series.earthMargin };
    if (!hz.calc || hz.calc.n !== site.series.n) {
      const s = site.series, n = s.n, sunFrac = new Float32Array(n), margin = new Float32Array(n);
      for (let i = 0; i < n; i++) {
        sunFrac[i] = discAbove(s.sunAlt[i] - horizonAt(hz, s.sunAz[i]));
        margin[i] = s.earthAlt[i] - horizonAt(hz, s.earthAz[i]);
      }
      hz.calc = { n, sunFrac, margin };
    }
    return hz.calc;
  }

  // seçilen ufuk modeli (gerçek arazi / düz) ve anten maskesi için saatlik diziler.
  // sunUp: Güneş diskinin herhangi bir kısmı görünür; both: Güneş görünür VE Dünya bağlantısı var.
  function buildModel(site, flat, mask) {
    const s = site.series, n = s.n;
    let sunFrac, margin;
    if (flat) {
      sunFrac = new Float32Array(n); for (let i = 0; i < n; i++) sunFrac[i] = discAbove(s.sunAlt[i]);
      margin = s.earthAlt;
    } else ({ sunFrac, margin } = forHorizon(site, site.horizon));
    const sunUp = new Uint8Array(n), linkUp = new Uint8Array(n), both = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      sunUp[i] = sunFrac[i] > 0 ? 1 : 0;
      linkUp[i] = margin[i] > mask ? 1 : 0;
      both[i] = sunUp[i] & linkUp[i];
    }
    return { n, flat, mask, sunFrac, margin, sunUp, linkUp, both };
  }

  function runsOf(flags) {
    const out = [];
    let start = 0;
    for (let i = 1; i <= flags.length; i++) {
      if (i === flags.length || flags[i] !== flags[start]) { out.push({ start, len: i - start, on: !!flags[start] }); start = i; }
    }
    return out;
  }

  // kısa durumları at, aynı durumdaki komşuları birleştir; sonuç yılı boşluksuz kaplar
  function mergeRuns(runs, n, minLen = MERGE_H) {
    let kept = runs.filter((r) => r.len >= minLen);
    if (!kept.length) kept = [runs.reduce((a, b) => (b.len > a.len ? b : a))];
    const out = [];
    for (const r of kept) {
      if (out.length && out[out.length - 1].on === r.on) continue;
      out.push({ start: r.start, on: r.on, len: 0 });
    }
    out[0].start = 0;
    out.forEach((r, i) => { r.len = (i + 1 < out.length ? out[i + 1].start : n) - r.start; r.open = i + 1 === out.length; });
    return out;
  }

  // [a, b) aralığında flags'in 0 olduğu en uzun kesintisiz süre (saat)
  function longestOff(flags, a = 0, b = flags.length) {
    let run = 0, best = 0;
    for (let i = a; i < b; i++) { if (!flags[i]) { run++; if (run > best) best = run; } else run = 0; }
    return best;
  }

  // [a, b) saat aralığının özeti. sunPct: Güneş diskinin herhangi bir kısmının göründüğü ZAMAN yüzdesi
  // ("güneşli zaman"); sunEnergyPct: diskin görünen oranının ortalaması ("güneş enerjisi oranı").
  function stats(model, a = 0, b = model.n) {
    let energy = 0, sun = 0, link = 0, both = 0, vis = 0, low = 0;
    for (let i = a; i < b; i++) {
      energy += model.sunFrac[i]; sun += model.sunUp[i]; link += model.linkUp[i]; both += model.both[i];
      if (model.margin[i] > 0) { vis++; if (model.margin[i] < 1) low++; }
    }
    const n = Math.max(1, b - a);
    return {
      hours: b - a,
      lowMarginPct: vis ? (low / vis) * 100 : 0, // Dünya göründüğü zamanın ne kadarında pay 1°'nin altında
      sunPct: (sun / n) * 100,
      sunEnergyPct: (energy / n) * 100,
      earthPct: (link / n) * 100,
      bothPct: (both / n) * 100,
      longestDarkH: longestOff(model.sunUp, a, b),
      longestGapH: longestOff(model.linkUp, a, b),
    };
  }

  // flags[from] durumunun değişmesine kalan saat; veri sonuna dek değişmiyorsa null
  function untilChange(flags, from) {
    for (let i = from + 1; i < flags.length; i++) if (flags[i] !== flags[from]) return i - from;
    return null;
  }

  // Karşılaştırma ekranının hesabı: startHour'da inen bir görevin ilk `hours` saati (inişe hizalı pencere).
  // Pencere veri sonunu aşarsa kırpılır (clipped). model verilmezse site + mask'ten kurulur (gerçek arazi).
  function windowStats(site, startHour, hours, mask, model) {
    const m = model || buildModel(site, false, mask), s = site.series;
    const a = clamp(Math.round(startHour), 0, m.n - 1), b = Math.min(m.n, a + hours);
    const st = stats(m, a, b);
    const sunHz = m.flat ? 0 : horizonAt(site.horizon, s.sunAz[a]);
    return Object.assign(st, {
      start: a, end: b, asked: hours, clipped: b - a < hours,
      landing: {
        sunAlt: s.sunAlt[a], sunAz: s.sunAz[a], sunMargin: s.sunAlt[a] - sunHz, disc: m.sunFrac[a],
        earthAlt: s.earthAlt[a], earthAz: s.earthAz[a], earthMargin: m.margin[a],
        sunUp: !!m.sunUp[a], linkUp: !!m.linkUp[a],
        sunChangeH: untilChange(m.sunUp, a), linkChangeH: untilChange(m.linkUp, a),
      },
      model: m,
    });
  }

  // her saat: batarya += panel·güneş_oranı·1h − tüketim·1h, 0 ile kapasite arasında
  function battery(model, cfg, startHour) {
    const n = model.n, level = new Float32Array(n + 1).fill(NaN);
    let e = cfg.cap, dead = -1, min = cfg.cap;
    const s0 = clamp(Math.round(startHour), 0, n - 1);
    level[s0] = e;
    for (let i = s0; i < n; i++) {
      e = clamp(e + cfg.panel * model.sunFrac[i] - cfg.load, 0, cfg.cap);
      level[i + 1] = e;
      if (e < min) min = e;
      if (e <= 0 && dead < 0) dead = i + 1;
    }
    return { level, start: s0, deadHour: dead, minPct: (min / cfg.cap) * 100 };
  }

  // start saatinde dolu bataryayla inen araç kaç saat dayanır? −1 = veri sonuna kadar
  function lifeFrom(model, cfg, start) {
    let e = cfg.cap;
    for (let i = start; i < model.n; i++) {
      e += cfg.panel * model.sunFrac[i] - cfg.load;
      if (e > cfg.cap) e = cfg.cap;
      if (e <= 0) return i + 1 - start;
    }
    return -1;
  }
  // iniş penceresi: verinin her günü için "o gün inilseydi" görev süresi.
  // Dolu bataryayla daha geç inmek hiçbir zaman daha kötü olmaz; bu yüzden safeDay'den sonrası hep güvenlidir.
  function landingScan(model, cfg) {
    const days = Math.floor(model.n / 24), life = new Float32Array(days), open = new Uint8Array(days);
    let safeDay = -1;
    for (let d = 0; d < days; d++) {
      const L = lifeFrom(model, cfg, d * 24);
      if (L < 0) { open[d] = 1; life[d] = (model.n - d * 24) / 24; if (safeDay < 0) safeDay = d; } else life[d] = L / 24;
    }
    return { life, open, safeDay };
  }
  // verilen iniş günü, panel ve tüketimle veri sonuna kadar dayanan en küçük kapasite (10 kWh adım, en çok 600)
  function minBattery(model, cfg, start) {
    for (let cap = 10; cap <= 600; cap += 10) if (lifeFrom(model, { cap, panel: cfg.panel, load: cfg.load }, start) < 0) return cap;
    return null;
  }

  // t (saat, kesirli) anındaki geometri; saatlik veriler arasında doğrusal ara değer
  function at(site, model, tH) {
    const s = site.series, n = s.n;
    const tt = clamp(tH, 0, n - 1), i = Math.min(Math.floor(tt), n - 2), f = tt - i;
    const L = (a) => a[i] + (a[i + 1] - a[i]) * f;
    const A = (a) => { let d = a[i + 1] - a[i]; if (d > 180) d -= 360; else if (d < -180) d += 360; return (a[i] + d * f + 360) % 360; };
    const sunAlt = L(s.sunAlt), sunAz = A(s.sunAz), earthAlt = L(s.earthAlt), earthAz = A(s.earthAz);
    const sunFrac = model.flat ? discAbove(sunAlt) : L(model.sunFrac);
    const margin = model.flat ? earthAlt : L(model.margin);
    return {
      sunAlt, sunAz, sunFrac, earthAlt, earthAz, margin,
      sunMargin: sunAlt - (model.flat ? 0 : horizonAt(site.horizon, sunAz)), // Güneş merkezinin arazi ufkuna göre payı
      illum: L(s.earthIllum),
      linkUp: margin > model.mask,
      blockKm: model.flat ? 30 : horizonDistAt(site.horizon, earthAz),
    };
  }

  function runAt(runs, tH) {
    for (let i = runs.length - 1; i >= 0; i--) if (tH >= runs[i].start) return runs[i];
    return runs[0];
  }

  // olay akışı: birleştirilmiş Güneş ve bağlantı durumları + iniş + batarya
  function buildFeed(sunRuns, linkRuns, landing, batt) {
    const ev = [];
    sunRuns.forEach((r, i) => { if (i) ev.push({ hour: r.start, k: r.on ? 'sun_on' : 'sun_off', durH: r.len, open: r.open, long: !r.on && r.len > LONG_DARK_H }); });
    linkRuns.forEach((r, i) => { if (i) ev.push({ hour: r.start, k: r.on ? 'link_on' : 'link_off', durH: r.len, open: r.open }); });
    ev.push({ hour: landing, k: 'landing' });
    if (batt.deadHour >= 0) ev.push({ hour: batt.deadHour, k: 'dead' });
    const order = { landing: 0, sun_off: 1, sun_on: 1, link_off: 2, link_on: 2, dead: 3 };
    return ev.sort((a, b) => a.hour - b.hour || order[a.k] - order[b.k]);
  }

  // bir nokta + ayarlar için bütün türetilmiş sonuçlar. opt.range = [a, b): özet rakamlarının dönemi (seçili yıl).
  // Olaylar saatlik seriden çıkarılır (events_YYYY.json ile aynı eşikler: Güneş oranı > 0, Dünya payı > maske).
  function derive(site, opt) {
    const model = buildModel(site, opt.flat, opt.mask);
    const sunRuns = mergeRuns(runsOf(model.sunUp), model.n), linkRuns = mergeRuns(runsOf(model.linkUp), model.n);
    const batt = battery(model, opt.batt, opt.landing);
    const [a, b] = opt.range || [0, model.n];
    return {
      model, stats: stats(model, a, b), range: [a, b], sunRuns, linkRuns, batt, feed: buildFeed(sunRuns, linkRuns, batt.start, batt),
      scan: landingScan(model, opt.batt), minCap: minBattery(model, opt.batt, batt.start),
    };
  }

  // brifing: dengeli puan (sabit ölçekli normalizasyon; formül ekranda yazıyor)
  function darkScore(days) { return 100 - (Math.min(days, DARK_CAP_DAYS) / DARK_CAP_DAYS) * 100; }
  function balanced(m) {
    return (m.terrain.sun_energy_pct + m.terrain_antenna_1deg.earth_pct + darkScore(m.terrain.longest_dark_days)) / 3;
  }

  // aynı puan, ölçülere ağırlık vererek; w = { sun, earth, dark }. Ağırlıklar eşitken balanced() ile aynı.
  function weighted(m, w) {
    const sum = w.sun + w.earth + w.dark;
    if (!(sum > 0)) return balanced(m);
    return (w.sun * m.terrain.sun_energy_pct + w.earth * m.terrain_antenna_1deg.earth_pct + w.dark * darkScore(m.terrain.longest_dark_days)) / sum;
  }

  // Pareto: üç ölçüde (Güneş ↑, Dünya 1° ↑, en uzun karanlık ↓) hiçbir noktanın baskılamadığı noktalar.
  // Dönen dizi: i. noktayı baskılayan (hiçbir ölçüde daha kötü olmayan, en az birinde daha iyi) noktanın
  // sırası, yoksa −1. Birden çok baskılayan varsa dengeli puanı en yüksek olan.
  function pareto(ms) {
    const v = ms.map((m) => [m.terrain.sun_energy_pct, m.terrain_antenna_1deg.earth_pct, -m.terrain.longest_dark_days, balanced(m)]);
    return v.map((b, i) => {
      let best = -1;
      v.forEach((a, j) => {
        if (j === i || a[0] < b[0] || a[1] < b[1] || a[2] < b[2]) return;
        if (a[0] === b[0] && a[1] === b[1] && a[2] === b[2]) return;
        if (best < 0 || a[3] > v[best][3]) best = j;
      });
      return best;
    });
  }

  // Dolu bataryayla start saatinde inen aracın yıl sonuna kadar gördüğü en derin açık (kWh).
  // Kapasite bundan büyükse araç dayanır (lifeFrom ile aynı kural, kapasiteyi denemeden).
  function requiredCap(model, panel, load, start) {
    let d = 0, max = 0;
    for (let i = start; i < model.n; i++) {
      d += load - panel * model.sunFrac[i];
      if (d < 0) d = 0; else if (d > max) max = d;
    }
    return max;
  }
  function mulberry32(a) {
    return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let x = Math.imul(a ^ (a >>> 15), 1 | a); x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x; return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
  }
  // Belirsizlik altında batarya: tüketim ve panel gücü birbirinden bağımsız, ±u oranında düzgün dağılımlı
  // (varsayım; gerçek araç verisi değil). n deneme, tohum sabit: aynı ayar hep aynı sonucu verir.
  // Dönen: her denemenin gerektirdiği kapasite, küçükten büyüğe.
  function uncertainty(model, cfg, start, u, n = 1000) {
    const rnd = mulberry32(20261114), need = new Float32Array(n);
    const s0 = clamp(Math.round(start), 0, model.n - 1);
    for (let k = 0; k < n; k++) {
      const load = cfg.load * (1 + u * (2 * rnd() - 1)), panel = cfg.panel * (1 + u * (2 * rnd() - 1));
      need[k] = requiredCap(model, panel, load, s0);
    }
    return need.sort();
  }
  // kapasite cap iken dayanan denemelerin yüzdesi, ve denemelerin en az %q'sunun dayandığı en küçük kapasite (10 kWh adım)
  function survival(need, cap, q = 95) {
    let ok = 0;
    while (ok < need.length && need[ok] < cap) ok++;
    const worst = need[Math.min(need.length - 1, Math.ceil((q / 100) * need.length) - 1)];
    return { pct: (ok / need.length) * 100, capQ: Math.floor(worst / 10) * 10 + 10 };
  }

  return { SUN_R, EARTH_R, LONG_DARK_H, discAbove, horizonAt, horizonDistAt, buildModel, runsOf, mergeRuns, stats, longestOff, windowStats, battery, at, runAt, derive, balanced,
    weighted, pareto, requiredCap, uncertainty, survival };
})();
