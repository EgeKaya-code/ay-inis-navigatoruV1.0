// ===== skyplot: gökyüzü radarı (ufuk çevresi büyütülmüş kutup grafiği) =====
// Yarıçap = yükseklik açısı, doğrusal değil (asinh): −8° dış kenar, +15° iç halka. Kuzey yukarıda, doğu sağda.
const SkyPlot = (() => {
  const E_MIN = -8, E_MAX = 15, S = 1.5, TRAIL_H = 720;
  const u = (e) => Math.asinh(e / S), U0 = u(E_MIN), U1 = u(E_MAX);
  let cv, ctx, base, bctx, baseKey = '', hatch = null;
  let W = 300, cx = 150, cy = 150, R0 = 120, R1 = 30, dpr = 1;

  const rOf = (e) => R0 - clamp((u(e) - U0) / (U1 - U0), 0, 1) * (R0 - R1);
  const pt = (az, e) => { const r = rOf(e), a = az * D2R; return [cx + r * Math.sin(a), cy - r * Math.cos(a)]; };

  function init(canvas) {
    cv = canvas; ctx = cv.getContext('2d');
    cv.setAttribute('aria-label', t('sky.alt'));
    base = document.createElement('canvas'); bctx = base.getContext('2d');
    const h = document.createElement('canvas'); h.width = h.height = 6;
    const hc = h.getContext('2d');
    hc.fillStyle = '#343c39'; hc.fillRect(0, 0, 6, 6);
    hc.strokeStyle = '#5b6562'; hc.lineWidth = 1;
    hc.beginPath(); hc.moveTo(-1, 7); hc.lineTo(7, -1); hc.moveTo(-1, 1); hc.lineTo(1, -1); hc.moveTo(5, 7); hc.lineTo(7, 5); hc.stroke();
    hatch = h;
  }

  function layout() {
    const d = fitCanvas(cv);
    dpr = d.dpr; W = d.w;
    cx = W / 2; cy = d.h / 2;
    R0 = Math.min(d.w, d.h) / 2 - 17; R1 = R0 * 0.2;
    if (base.width !== cv.width || base.height !== cv.height) { base.width = cv.width; base.height = cv.height; baseKey = ''; }
  }

  // değişmeyen katman: arazi maskesi, ızgara, pusula, Dünya'nın yıllık izi
  function drawBase(site, flatK, mask) {
    const c = bctx, hz = site.horizon, se = site.series;
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.clearRect(0, 0, W, W * 2);
    const line = cssVar('--line'), earth = cssVar('--earth');
    // gökyüzü diski
    c.fillStyle = '#000'; c.beginPath(); c.arc(cx, cy, R0, 0, Math.PI * 2); c.fill();
    // arazi maskesi: dış kenardan ufuk çizgisine kadar dolu
    const hAt = (az) => lerp(Sim.horizonAt(hz, az), 0, flatK);
    c.beginPath(); c.arc(cx, cy, R0, 0, Math.PI * 2);
    for (let az = 360; az >= 0; az -= 0.5) { const [x, y] = pt(az, hAt(az)); if (az === 360) c.moveTo(x, y); else c.lineTo(x, y); }
    c.closePath();
    c.fillStyle = c.createPattern(hatch, 'repeat'); c.fill('evenodd');
    c.beginPath();
    for (let az = 0; az <= 360; az += 0.5) { const [x, y] = pt(az, hAt(az)); if (az === 0) c.moveTo(x, y); else c.lineTo(x, y); }
    c.closePath(); c.strokeStyle = flatK > 0.5 ? cssVar('--warn') : line; c.lineWidth = 1.4; c.stroke();
    // düz ufuk modunda gerçek ufuk hayalet çizgi olarak kalsın
    if (flatK > 0.02) {
      c.beginPath();
      for (let az = 0; az <= 360; az += 0.5) { const [x, y] = pt(az, Sim.horizonAt(hz, az)); if (az === 0) c.moveTo(x, y); else c.lineTo(x, y); }
      c.closePath(); c.setLineDash([2, 3]); c.strokeStyle = 'rgba(201,210,205,0.55)'; c.lineWidth = 1; c.stroke(); c.setLineDash([]);
    }
    // yükseklik halkaları
    c.font = '500 10px "IBM Plex Mono", monospace'; c.textAlign = 'left'; c.textBaseline = 'middle';
    for (const e of [-5, 0, 5, 10]) {
      c.beginPath(); c.arc(cx, cy, rOf(e), 0, Math.PI * 2);
      c.strokeStyle = e === 0 ? 'rgba(238,242,238,0.5)' : 'rgba(201,210,205,0.2)'; c.lineWidth = 1;
      if (e === 0) c.setLineDash([5, 4]);
      c.stroke(); c.setLineDash([]);
      if (e === 10) continue;
      const [x, y] = pt(135, e);
      c.fillStyle = 'rgba(0,0,0,0.75)'; c.fillRect(x + 1, y - 6, e === 0 ? 14 : 22, 12);
      c.fillStyle = e === 0 ? '#eef2ee' : 'rgba(201,210,205,0.8)';
      c.fillText((e > 0 ? '+' : e < 0 ? '−' : '') + Math.abs(e) + '°', x + 2, y);
    }
    // pusula çentikleri ve yönler
    c.strokeStyle = line; c.lineWidth = 1;
    for (let az = 0; az < 360; az += 10) {
      const a = az * D2R, l = az % 90 === 0 ? 7 : az % 30 === 0 ? 5 : 3;
      c.beginPath(); c.moveTo(cx + R0 * Math.sin(a), cy - R0 * Math.cos(a)); c.lineTo(cx + (R0 + l) * Math.sin(a), cy - (R0 + l) * Math.cos(a)); c.stroke();
    }
    c.beginPath(); c.arc(cx, cy, R0, 0, Math.PI * 2); c.stroke();
    c.font = '600 14px "Barlow Condensed", sans-serif'; c.textAlign = 'center'; c.fillStyle = line;
    [['n', 0], ['e', 90], ['s', 180], ['w', 270]].forEach(([k, az]) => {
      const a = az * D2R; c.fillText(t('compass.' + k), cx + (R0 + 12) * Math.sin(a), cy - (R0 + 12) * Math.cos(a) + 0.5);
    });
    // Dünya'nın yıl boyunca izi (çok silik) ve anten maskesi çizgisi (Dünya'nın dolaştığı yönlerde)
    c.beginPath();
    for (let i = 0; i < se.n; i += 6) { const [x, y] = pt(se.earthAz[i], se.earthAlt[i]); if (i) c.lineTo(x, y); else c.moveTo(x, y); }
    c.strokeStyle = 'rgba(90,165,255,0.2)'; c.lineWidth = 1; c.stroke();
    if (mask > 0) {
      let s = 0, k = 0;
      for (let i = 0; i < se.n; i += 24) { s += Math.sin(se.earthAz[i] * D2R); k += Math.cos(se.earthAz[i] * D2R); }
      const mid = Math.atan2(s, k) / D2R;
      c.beginPath();
      for (let d = -22; d <= 22; d += 0.5) { const [x, y] = pt(mid + d, hAt(mid + d) + mask); if (d === -22) c.moveTo(x, y); else c.lineTo(x, y); }
      c.setLineDash([4, 3]); c.strokeStyle = earth; c.lineWidth = 1.4; c.stroke(); c.setLineDash([]);
    }
    // iç halka: +15° üstü kullanılmıyor
    c.beginPath(); c.arc(cx, cy, R1, 0, Math.PI * 2); c.fillStyle = '#0e1112'; c.fill(); c.strokeStyle = 'rgba(201,210,205,0.35)'; c.stroke();
    c.beginPath(); c.moveTo(cx - 4, cy); c.lineTo(cx + 4, cy); c.moveTo(cx, cy - 4); c.lineTo(cx, cy + 4); c.strokeStyle = 'rgba(201,210,205,0.5)'; c.stroke();
  }

  function trail(c, az, alt, tH, color) {
    const i1 = Math.floor(tH), i0 = Math.max(0, i1 - TRAIL_H), parts = 6;
    for (let p = 0; p < parts; p++) {
      const a = i0 + Math.floor(((i1 - i0) * p) / parts), b = i0 + Math.floor(((i1 - i0) * (p + 1)) / parts);
      c.beginPath();
      for (let i = a; i <= b; i++) { const [x, y] = pt(az[i], alt[i]); if (i === a) c.moveTo(x, y); else c.lineTo(x, y); }
      c.globalAlpha = 0.18 + (0.72 * (p + 1)) / parts;
      c.strokeStyle = color; c.lineWidth = 1.4; c.stroke();
    }
    c.globalAlpha = 1;
  }

  function label(c, text, x, y, color) {
    c.font = '600 13px "Barlow Condensed", sans-serif';
    const left = x > cx; // etiketi merkeze doğru yaz ki kenardan taşmasın
    c.textAlign = left ? 'right' : 'left'; c.textBaseline = 'middle';
    const tx = x + (left ? -12 : 12);
    c.lineWidth = 3; c.strokeStyle = 'rgba(0,0,0,0.9)'; c.strokeText(text, tx, y);
    c.fillStyle = color; c.fillText(text, tx, y);
  }

  // o: { site, now, tH, flatK, mask, view: {mode, yaw, fov, aspect} | null }
  function draw(o) {
    if (!cv || !o.site) return;
    layout();
    if (W < 20) return;
    const key = [o.site.id, o.flatK.toFixed(3), o.mask, cv.width, cv.height].join('|');
    if (key !== baseKey) { drawBase(o.site, o.flatK, o.mask); baseKey = key; }
    const c = ctx, se = o.site.series, now = o.now;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, cv.width, cv.height);
    c.drawImage(base, 0, 0);
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const sun = cssVar('--sun'), earth = cssVar('--earth'), warn = cssVar('--warn');

    // bakış yönü (astronot gözü / panorama)
    if (o.view) {
      const half = o.view.hfov / 2;
      c.beginPath();
      for (const s of [-1, 1]) { const a = (o.view.yaw + s * half) * D2R; c.moveTo(cx + R1 * Math.sin(a), cy - R1 * Math.cos(a)); c.lineTo(cx + (R0 + 8) * Math.sin(a), cy - (R0 + 8) * Math.cos(a)); }
      c.strokeStyle = 'rgba(238,242,238,0.75)'; c.lineWidth = 1; c.stroke();
      c.beginPath(); c.arc(cx, cy, R0 + 8, (o.view.yaw - half - 90) * D2R, (o.view.yaw + half - 90) * D2R); c.lineWidth = 2; c.stroke();
    }

    trail(c, se.sunAz, se.sunAlt, o.tH, sun);
    trail(c, se.earthAz, se.earthAlt, o.tH, earth);

    // Dünya: ⊕ ; bağlantı yoksa içi boş ve çizgili
    const [ex, ey] = pt(now.earthAz, now.earthAlt);
    c.lineWidth = 1.8; c.strokeStyle = earth; c.fillStyle = now.linkUp ? earth : '#000';
    c.beginPath(); c.arc(ex, ey, 7, 0, Math.PI * 2); c.fill(); c.stroke();
    c.strokeStyle = now.linkUp ? '#04101f' : warn;
    c.beginPath();
    if (now.linkUp) { c.moveTo(ex - 7, ey); c.lineTo(ex + 7, ey); c.moveTo(ex, ey - 7); c.lineTo(ex, ey + 7); }
    else { c.moveTo(ex - 5, ey - 5); c.lineTo(ex + 5, ey + 5); c.moveTo(ex + 5, ey - 5); c.lineTo(ex - 5, ey + 5); }
    c.stroke();
    // iki işaret yakınsa etiketleri düşeyde ayır
    const [sx, sy] = pt(now.sunAz, now.sunAlt);
    const near = Math.abs(sy - ey) < 16 && Math.abs(sx - ex) < 110, split = near ? (ey <= sy ? -9 : 9) : 0;
    label(c, t('sky.earth').toLocaleUpperCase(LOCALE) + ' ' + Fmt.deg(now.earthAlt, 1), ex, ey + split, earth);

    // Güneş: ☉ ; görünmüyorsa içi boş
    const lit = now.sunFrac > 0;
    c.lineWidth = 1.8; c.strokeStyle = sun; c.fillStyle = lit ? sun : '#000';
    c.beginPath(); c.arc(sx, sy, 6, 0, Math.PI * 2); c.fill(); c.stroke();
    c.fillStyle = lit ? '#2a1c00' : sun;
    c.beginPath(); c.arc(sx, sy, 1.8, 0, Math.PI * 2); c.fill();
    label(c, t('sky.sun').toLocaleUpperCase(LOCALE) + ' ' + Fmt.deg(now.sunAlt, 1), sx, sy - split, sun);
  }

  function legend(el) {
    el.innerHTML = [
      `<li>${icon('sun', 'sun')}${esc(t('sky.sun'))}</li>`,
      `<li>${icon('earth', 'earth')}${esc(t('sky.earth'))}</li>`,
      `<li><span class="sw sw-terrain"></span>${esc(tp('sky.terrain'))}</li>`,
      `<li><span class="sw sw-trail-s"></span><span class="sw sw-trail-e"></span>${esc(t('sky.trail'))}</li>`,
      `<li><span class="sw sw-mask"></span>${esc(tp('sky.maskLine'))}</li>`,
    ].join('');
  }

  return { init, draw, legend, invalidate() { baseKey = ''; } };
})();
