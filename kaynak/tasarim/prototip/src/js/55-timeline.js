// ===== timeline: zaman şeritleri (Güneş, Dünya, ikisi birlikte, batarya, iniş penceresi) + kaydırıcı =====
// Şerit verinin bir penceresini [v0, v1] gösterir: bütün veri, bir yıl, 90 gün ya da 30 gün. Tekerlek yakınlaştırır.
const Timeline = (() => {
  const PAD = 8;            // kaydırıcı başının yarı genişliği: şerit ile başlık hizalı kalsın
  const ROW = 13, GAP = 3;  // CSS'teki .t-labels ile aynı
  const NROW = 5;
  const LIFE_CAP = 60;      // iniş penceresi satırında çubuğun dolduğu görev süresi (gün)
  const MIN_SPAN = 7 * 24;
  let cv, ctx, track, cursor, landMark, slider, tip, n = 8760, W = 100, last = null;
  let v0 = 0, v1 = 8759, onView = null, landing = 0;

  const xOf = (h) => PAD + ((h - v0) / Math.max(1, v1 - v0)) * (W - 2 * PAD);
  const hOf = (x) => clamp(v0 + ((x - PAD) / Math.max(1, W - 2 * PAD)) * (v1 - v0), v0, v1);

  function init(onSeek, onViewChange) {
    cv = $('strips'); ctx = cv.getContext('2d'); track = $('track'); cursor = $('cursor'); landMark = $('landMark'); slider = $('slTime'); tip = $('tTip');
    onView = onViewChange;
    slider.setAttribute('aria-label', t('time.slider'));
    slider.addEventListener('input', () => onSeek(Number(slider.value)));
    slider.addEventListener('pointermove', showTip);
    slider.addEventListener('pointerleave', () => { tip.hidden = true; });
    // tekerlek: farenin altındaki an sabit kalacak şekilde yakınlaş / uzaklaş
    track.addEventListener('wheel', (e) => {
      e.preventDefault();
      const x = e.clientX - track.getBoundingClientRect().left, hAt = hOf(x), f = (hAt - v0) / Math.max(1, v1 - v0);
      const span = clamp((v1 - v0) * Math.exp(e.deltaY * 0.0015), MIN_SPAN, n - 1);
      setView(hAt - f * span, hAt - f * span + span, true);
    }, { passive: false });
    new ResizeObserver(() => { if (last) draw(last.D, last.cap); }).observe(track);
  }

  // gösterilen pencere; veri sınırlarına sıkıştırılır
  function setView(a, b, user) {
    const span = clamp(b - a, Math.min(MIN_SPAN, n - 1), n - 1);
    a = clamp(a, 0, n - 1 - span);
    v0 = Math.round(a); v1 = Math.round(a + span);
    slider.min = v0; slider.max = v1;
    if (last) draw(last.D, last.cap);
    if (onView) onView(v0, v1, !!user);
  }
  // imleç pencerenin dışına çıkarsa pencereyi sayfa sayfa kaydır
  function follow(tH) {
    if (tH > v1) setView(Math.min(tH, v1), Math.min(tH, v1) + (v1 - v0));
    else if (tH < v0) setView(tH - (v1 - v0) * 0.1, tH + (v1 - v0) * 0.9);
  }

  // fare şeridin üstündeyken: o saatin durumu ve "o gün inilseydi" sonucu
  function showTip(e) {
    if (!last) return;
    const x = e.clientX - track.getBoundingClientRect().left, h = Math.round(hOf(x));
    const m = last.D.model, sc = last.D.scan, day = Math.min(sc.life.length - 1, Math.floor(h / 24));
    tip.textContent = [
      Fmt.date(h, true) + ' ' + Fmt.time(h),
      t('tip.sun', { v: Fmt.pct0(m.sunFrac[h] * 100) }),
      t(m.linkUp[h] ? 'tip.link' : 'tip.noLink'),
      sc.open[day] ? t('tip.lifeOpen') : t('tip.life', { d: Fmt.days(sc.life[day]) }),
    ].join(' · ');
    tip.hidden = false;
    const half = tip.offsetWidth / 2 + 4;
    tip.style.left = clamp(x, half, Math.max(half, W - half)).toFixed(0) + 'px';
  }

  function ruler(c, ry) {
    const span = v1 - v0, months = t('months');
    c.strokeStyle = 'rgba(201,210,205,0.55)'; c.fillStyle = cssVar('--ink-2'); c.lineWidth = 1;
    c.font = '500 10.5px "IBM Plex Mono", monospace'; c.textBaseline = 'top'; c.textAlign = 'left';
    const d0 = Fmt.hourToDate(v0), d1 = Fmt.hourToDate(v1);
    const pxPerDay = ((W - 2 * PAD) / span) * 24;
    if (pxPerDay < 6) {
      // ay çentikleri; uzun pencerede yalnız çeyrekler etiketlenir, Ocak'ta yıl yazılır
      const pxPerMonth = pxPerDay * 30.4, every = pxPerMonth > 46 ? 1 : pxPerMonth > 24 ? 2 : pxPerMonth > 15 ? 3 : 6;
      for (let y = d0.getUTCFullYear(), mo = d0.getUTCMonth(); ; mo++) {
        if (mo > 11) { mo = 0; y++; }
        const h = Fmt.hourOfMs(Date.UTC(y, mo, 1));
        if (h > v1) break;
        if (h < v0) continue;
        const x = Math.round(xOf(h)) + 0.5;
        c.beginPath(); c.moveTo(x, ry - 1); c.lineTo(x, ry + (mo === 0 ? 9 : 6)); c.stroke();
        if (mo % every === 0) c.fillText(mo === 0 ? String(y) : months[mo], x + 3, ry + 1);
      }
      if (pxPerDay * 5 > 5) {
        c.strokeStyle = 'rgba(201,210,205,0.25)';
        for (let h = Math.ceil(v0 / 120) * 120; h <= v1; h += 120) { const x = Math.round(xOf(h)) + 0.5; c.beginPath(); c.moveTo(x, ry - 1); c.lineTo(x, ry + 2); c.stroke(); }
      }
    } else {
      // gün çentikleri; etiket aralığı piksel yoğunluğuna göre
      const every = pxPerDay > 64 ? 1 : pxPerDay > 34 ? 2 : pxPerDay > 13 ? 5 : 10;
      for (let h = Math.ceil(v0 / 24) * 24; h <= v1; h += 24) {
        const d = Fmt.hourToDate(h), x = Math.round(xOf(h)) + 0.5, lab = d.getUTCDate() === 1 || (d.getUTCDate() - 1) % every === 0;
        c.strokeStyle = lab ? 'rgba(201,210,205,0.55)' : 'rgba(201,210,205,0.25)';
        c.beginPath(); c.moveTo(x, ry - 1); c.lineTo(x, ry + (lab ? 6 : 2)); c.stroke();
        if (lab && x < W - 34) c.fillText(d.getUTCDate() + ' ' + months[d.getUTCMonth()], x + 3, ry + 1);
      }
    }
    void d1;
  }

  function draw(D, cap) {
    last = { D, cap };
    const d = fitCanvas(cv), c = ctx, m = D.model;
    W = d.w;
    if (n !== m.n) { n = m.n; if (v1 > n - 1 || v1 <= v0) { v0 = 0; v1 = n - 1; slider.min = v0; slider.max = v1; } }
    c.setTransform(d.dpr, 0, 0, d.dpr, 0, 0);
    c.clearRect(0, 0, d.w, d.h);
    const sun = cssVar('--sun'), earth = cssVar('--earth'), both = cssVar('--both'), line = cssVar('--line'), warn = cssVar('--warn');
    const x0 = PAD, x1 = W - PAD, cols = Math.max(1, Math.round(x1 - x0)), span = v1 - v0;
    const rows = []; for (let i = 0; i < NROW; i++) rows.push(i * (ROW + GAP));
    c.fillStyle = '#171b1c';
    rows.forEach((y) => c.fillRect(x0, y, x1 - x0, ROW));
    const hA = (px) => v0 + (px / cols) * span;

    // Güneş (görünen oran → opaklık), Dünya (bağlantı var oranı), ikisi birlikte
    for (let px = 0; px < cols; px++) {
      const a = clamp(Math.floor(hA(px)), 0, n - 1), b = clamp(Math.max(a + 1, Math.floor(hA(px + 1))), a + 1, n);
      let s = 0, e = 0, k = 0;
      for (let i = a; i < b; i++) { s += m.sunFrac[i]; e += m.linkUp[i]; k += m.both[i]; }
      s /= b - a; e /= b - a; k /= b - a;
      if (s > 0.003) { c.globalAlpha = 0.25 + 0.75 * s; c.fillStyle = sun; c.fillRect(x0 + px, rows[0], 1.05, ROW); }
      if (e > 0.003) { c.globalAlpha = 0.25 + 0.75 * e; c.fillStyle = earth; c.fillRect(x0 + px, rows[1], 1.05, ROW); }
      if (k > 0.003) { c.globalAlpha = 0.25 + 0.75 * k; c.fillStyle = both; c.fillRect(x0 + px, rows[2], 1.05, ROW); }
    }
    c.globalAlpha = 1;

    // batarya düzeyi; bittiği andan sonra kırmızı taralı
    const lv = D.batt.level, dead = D.batt.deadHour, yb = rows[3];
    c.fillStyle = line;
    for (let px = 0; px < cols; px++) {
      const i = clamp(Math.floor(hA(px + 0.5)), 0, n);
      if (Number.isNaN(lv[i]) || (dead >= 0 && i >= dead)) continue;
      const hgt = Math.max(1, (lv[i] / cap) * ROW);
      c.globalAlpha = 0.85; c.fillRect(x0 + px, yb + ROW - hgt, 1.05, hgt);
    }
    c.globalAlpha = 1;
    if (dead >= 0 && dead < v1) {
      const xd = Math.max(x0, xOf(dead));
      c.save(); c.beginPath(); c.rect(xd, yb, x1 - xd, ROW); c.clip();
      c.fillStyle = '#3a0d1c'; c.fillRect(xd, yb, x1 - xd, ROW);
      c.strokeStyle = warn; c.lineWidth = 1;
      for (let x = xd - ROW; x < x1; x += 5) { c.beginPath(); c.moveTo(x, yb + ROW); c.lineTo(x + ROW, yb); c.stroke(); }
      c.restore();
      if (dead >= v0) { c.fillStyle = warn; c.fillRect(xd - 1, yb - 1, 2, ROW + 2); }
    }

    // iniş penceresi: o gün inen araç ne kadar dayanır? dolu = veri sonuna dek dayanır, kısa kırmızı çubuk = erken biter
    const sc = D.scan, yl = rows[4];
    for (let px = 0; px < cols; px++) {
      const day = clamp(Math.floor(hA(px + 0.5) / 24), 0, sc.life.length - 1);
      if (sc.open[day]) { c.fillStyle = line; c.globalAlpha = 0.85; c.fillRect(x0 + px, yl, 1.05, ROW); }
      else {
        const hgt = Math.max(1.5, (Math.min(sc.life[day], LIFE_CAP) / LIFE_CAP) * (ROW - 3));
        c.fillStyle = warn; c.globalAlpha = 0.85; c.fillRect(x0 + px, yl + ROW - hgt, 1.05, hgt);
      }
    }
    c.globalAlpha = 1;

    ruler(c, NROW * (ROW + GAP));
    setLanding(D.batt.start);
  }

  function setCursor(tH) {
    const inView = tH >= v0 && tH <= v1;
    cursor.hidden = !inView;
    cursor.style.left = xOf(tH).toFixed(1) + 'px';
    const v = String(Math.round(tH));
    if (slider.value !== v && !slider.matches(':active')) slider.value = v;
  }
  function setLanding(h) {
    landing = h;
    landMark.hidden = h < v0 || h > v1;
    landMark.style.left = xOf(h).toFixed(1) + 'px';
  }

  return { init, draw, setCursor, setLanding, setView, follow, get view() { return [v0, v1]; } };
})();
