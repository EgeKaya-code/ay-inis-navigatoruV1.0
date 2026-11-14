// ===== pano: 2B ufuk panoraması (WebGL yokken yedek; ayrıca üçüncü görünüm) =====
// Yatay ve düşey ölçek aynı (piksel/derece): Güneş ve Dünya diskleri gerçek oranda.
const Pano = (() => {
  const TRAIL_H = 720;
  let cv, ctx, center = 0, ppd = 9, W = 100, H = 100, dpr = 1, inited = false;
  // akıllı panorama: kullanıcı sürükleyene ya da yakınlaştırana kadar görünüm Güneş ile Dünya'yı birlikte
  // gösterecek şekilde kendiliğinden ortalanır ve genişler (gerekirse 360°'ye kadar)
  let auto = true;
  let X0 = 0, X1 = 100, Y0 = 0, Y1 = 100; // HUD panellerinin örtmediği alan

  const wrap = (d) => ((d + 540) % 360) - 180;
  const xOf = (az) => (X0 + X1) / 2 + wrap(az - center) * ppd;
  const yOf = (e) => Y0 + (Y1 - Y0) * 0.6 - e * ppd;
  const azAt = (x) => center + (x - (X0 + X1) / 2) / ppd;

  function init(canvas) {
    cv = canvas; ctx = cv.getContext('2d');
    const pts = new Map();
    let pinch = 0;
    cv.addEventListener('pointerdown', (e) => { cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); });
    cv.addEventListener('pointermove', (e) => {
      const p = pts.get(e.pointerId); if (!p) return;
      const dx = e.clientX - p[0]; p[0] = e.clientX; p[1] = e.clientY;
      if (pts.size === 2) { const [a, b] = [...pts.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (pinch) ppd = clamp((ppd * d) / pinch, 2.5, 80); pinch = d; return; }
      center = (center - dx / ppd + 360) % 360;
      if (Math.abs(dx) > 0) auto = false;
    });
    const up = (e) => { pts.delete(e.pointerId); pinch = 0; };
    cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
    cv.addEventListener('wheel', (e) => { e.preventDefault(); auto = false; ppd = clamp(ppd * Math.exp(-e.deltaY * 0.0012), 2.5, 80); }, { passive: false });
    cv.addEventListener('dblclick', () => { auto = true; });
    inited = true;
  }

  function drawEarth(c, x, y, r, illum, ang) {
    c.save(); c.translate(x, y); c.rotate(ang);
    c.beginPath(); c.arc(0, 0, r, 0, Math.PI * 2); c.fillStyle = '#0a1a33'; c.fill();
    const k = clamp(illum, 0, 1);
    c.beginPath(); c.arc(0, 0, r, -Math.PI / 2, Math.PI / 2);
    c.ellipse(0, 0, Math.max(0.01, r * Math.abs(1 - 2 * k)), r, 0, Math.PI / 2, -Math.PI / 2, k < 0.5);
    c.closePath(); c.fillStyle = '#5aa5ff'; c.fill();
    c.restore();
    c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.strokeStyle = 'rgba(90,165,255,0.7)'; c.lineWidth = 1; c.stroke();
  }

  function trail(c, az, alt, tH, color) {
    const i1 = Math.floor(tH), i0 = Math.max(0, i1 - TRAIL_H);
    c.beginPath();
    let px = null;
    for (let i = i0; i <= i1; i++) {
      const x = xOf(az[i]), y = yOf(alt[i]);
      if (px === null || Math.abs(x - px) > W * 0.5) c.moveTo(x, y); else c.lineTo(x, y);
      px = x;
    }
    c.globalAlpha = 0.55; c.strokeStyle = color; c.lineWidth = 1.2; c.stroke(); c.globalAlpha = 1;
  }

  // o: { site, now, tH, flatK, mask }
  function draw(o) {
    if (!inited || !o.site) return;
    const d = fitCanvas(cv); W = d.w; H = d.h; dpr = d.dpr;
    if (W < 20 || H < 20) return;
    const ins = o.inset || { l: 0, t: 0, r: 0, b: 0 };
    X0 = ins.l; X1 = W - ins.r; Y0 = ins.t; Y1 = H - ins.b;
    const c = ctx, hz = o.site.horizon, se = o.site.series, now = o.now;
    if (auto) {
      const sep = wrap(now.earthAz - now.sunAz), mid = now.sunAz + sep / 2;
      const span = clamp(Math.abs(sep) + 60, 80, 360);
      const goalPpd = clamp((X1 - X0) / span, 2.5, 12);
      center = (center + wrap(mid - center) * 0.08 + 360) % 360;
      ppd += (goalPpd - ppd) * 0.08;
    }
    const sun = cssVar('--sun'), earth = cssVar('--earth'), line = cssVar('--line');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.fillStyle = '#000'; c.fillRect(0, 0, W, H);

    // Dünya'nın yıllık izi (silik) ve son 30 günün izleri
    c.beginPath();
    let px = null;
    for (let i = 0; i < se.n; i += 4) { const x = xOf(se.earthAz[i]), y = yOf(se.earthAlt[i]); if (px === null || Math.abs(x - px) > W * 0.5) c.moveTo(x, y); else c.lineTo(x, y); px = x; }
    c.strokeStyle = 'rgba(90,165,255,0.22)'; c.lineWidth = 1; c.stroke();
    trail(c, se.sunAz, se.sunAlt, o.tH, sun);
    trail(c, se.earthAz, se.earthAlt, o.tH, earth);

    // Güneş (parlama + disk) ve Dünya (evreli)
    const sx = xOf(now.sunAz), sy = yOf(now.sunAlt), sr = Math.max(2, Sim.SUN_R * ppd);
    const g = c.createRadialGradient(sx, sy, 0, sx, sy, sr * 9);
    g.addColorStop(0, 'rgba(255,214,130,0.55)'); g.addColorStop(0.25, 'rgba(255,190,90,0.14)'); g.addColorStop(1, 'rgba(255,180,80,0)');
    c.fillStyle = g; c.fillRect(sx - sr * 9, sy - sr * 9, sr * 18, sr * 18);
    c.beginPath(); c.arc(sx, sy, sr, 0, Math.PI * 2); c.fillStyle = '#fff1cf'; c.fill();
    const ex = xOf(now.earthAz), ey = yOf(now.earthAlt), er = Math.max(3, Sim.EARTH_R * ppd);
    drawEarth(c, ex, ey, er, now.illum, Math.atan2(sy - ey, wrap(now.sunAz - now.earthAz) * ppd));

    // arazi maskesi (Güneş ve Dünya'yı örter)
    const hAt = (az) => lerp(Sim.horizonAt(hz, az), 0, o.flatK);
    c.beginPath(); c.moveTo(0, H);
    for (let x = 0; x <= W + 2; x += 2) c.lineTo(x, yOf(hAt(azAt(x))));
    c.lineTo(W, H); c.closePath();
    const tg = c.createLinearGradient(0, yOf(6), 0, H);
    tg.addColorStop(0, '#3a403d'); tg.addColorStop(1, '#141716');
    c.fillStyle = tg; c.fill();
    c.beginPath();
    for (let x = 0; x <= W + 2; x += 2) { const y = yOf(hAt(azAt(x))); if (x) c.lineTo(x, y); else c.moveTo(x, y); }
    c.strokeStyle = o.flatK > 0.5 ? cssVar('--warn') : line; c.lineWidth = 1.3; c.stroke();
    if (o.flatK > 0.02) {
      c.beginPath();
      for (let x = 0; x <= W + 2; x += 2) { const y = yOf(Sim.horizonAt(hz, azAt(x))); if (x) c.lineTo(x, y); else c.moveTo(x, y); }
      c.setLineDash([3, 4]); c.strokeStyle = 'rgba(201,210,205,0.6)'; c.lineWidth = 1; c.stroke(); c.setLineDash([]);
    }
    // anten maskesi
    if (o.mask > 0) {
      c.beginPath();
      for (let x = 0; x <= W + 2; x += 3) { const y = yOf(hAt(azAt(x)) + o.mask); if (x) c.lineTo(x, y); else c.moveTo(x, y); }
      c.setLineDash([5, 4]); c.strokeStyle = earth; c.lineWidth = 1.2; c.stroke(); c.setLineDash([]);
    }

    // etiketler
    c.font = '600 14px "Barlow Condensed", sans-serif'; c.textBaseline = 'middle'; c.textAlign = 'left';
    const tag = (text, x, y, col) => { c.lineWidth = 3; c.strokeStyle = 'rgba(0,0,0,0.9)'; c.strokeText(text, x, y); c.fillStyle = col; c.fillText(text, x, y); };
    tag(t('scene.sunTag', { v: Fmt.deg(now.sunAlt, 1) }).toLocaleUpperCase(LOCALE), sx + sr + 8, sy - 10, sun);
    tag(t('scene.earthTag', { v: Fmt.deg(now.earthAlt, 1) }).toLocaleUpperCase(LOCALE), ex + er + 8, ey - 10, earth);

    if (auto) {
      c.font = '500 10.5px "IBM Plex Mono", monospace'; c.textAlign = 'right'; c.textBaseline = 'bottom'; c.fillStyle = cssVar('--ink-3');
      c.fillText(t('scene.panoAuto', { v: Math.round(Math.min(360, (X1 - X0) / ppd)) }), X1 - 12, Y1 - 58);
    }
    // eksenler: azimut (alt), yükseklik (sol)
    c.font = '500 10.5px "IBM Plex Mono", monospace'; c.fillStyle = cssVar('--ink-2'); c.strokeStyle = 'rgba(201,210,205,0.5)'; c.lineWidth = 1;
    const stepAz = ppd > 20 ? 5 : ppd > 6 ? 10 : 30, names = { 0: 'n', 90: 'e', 180: 's', 270: 'w' };
    const a0 = Math.ceil(azAt(X0 + 20) / stepAz) * stepAz, yb = Y1 - 34;
    c.textAlign = 'center'; c.textBaseline = 'bottom';
    for (let a = a0; a <= azAt(X1 - 20); a += stepAz) {
      const x = (X0 + X1) / 2 + (a - center) * ppd, az = ((a % 360) + 360) % 360;
      c.beginPath(); c.moveTo(x, yb); c.lineTo(x, yb - 6); c.stroke();
      c.fillText(names[az] ? t('compass.' + names[az]) + ' ' + az + '°' : az + '°', x, yb - 8);
    }
    const stepEl = ppd > 20 ? 1 : 5;
    c.textAlign = 'left'; c.textBaseline = 'middle';
    for (let e = -10; e <= 30; e += stepEl) {
      const y = yOf(e); if (y < Y0 + 8 || y > yb - 22) continue;
      c.beginPath(); c.moveTo(X0, y); c.lineTo(X0 + (e === 0 ? 14 : 7), y); c.stroke();
      c.fillText((e > 0 ? '+' : e < 0 ? '−' : '') + Math.abs(e) + '°', X0 + 17, y);
    }
  }

  return {
    init, draw,
    lookAt(az) { auto = false; center = ((az % 360) + 360) % 360; },
    autoCenter() { auto = true; },
    get auto() { return auto; },
    get view() { return { yaw: center, hfov: Math.min(360, (X1 - X0) / ppd) }; },
  };
})();
