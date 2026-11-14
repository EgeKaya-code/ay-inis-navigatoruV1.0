// ===== compare: senaryo karşılaştırma ekranı (en fazla 3 sütun; 3D ve iniş sekansı olmadan) =====
// Senaryo = iniş noktası + iniş tarihi + anten payı. Batarya ayarları senaryoya dahil değildir.
// Her sütun, inişten sonraki pencereyi (14 / 30 / 90 gün) Sim.windowStats ile özetler; şeritler inişe hizalıdır.
const Compare = (() => {
  const MAX = 3, LETTERS = 'ABC', WINDOWS = [14, 30, 90];
  const ROW = 15, GAP = 4, RULER = 16, PADX = 1;
  let S, cb, list = [], win = 30, showDiff = true, shift = 14, token = 0, results = [], hoverOff = null;

  const save = () => Store.set('cmp', list.map((x) => ({ id: x.id, ms: Fmt.hourToDate(x.hour).getTime(), mask: x.mask })));
  const siteOf = (id) => { for (const s of S.index.sites) for (const c of s.cands) if (c.id === id) return c; return null; };
  const nameOf = (c) => (c.legacy ? t('cand.legacy') : t('cand.title', { n: c.rank }));
  const letter = (i) => LETTERS[i];

  function init(state, callbacks) {
    S = state; cb = callbacks;
    // önceki oturumdan kalan senaryolar: yalnız bu veride karşılığı olanlar
    list = Store.get('cmp', []).map((x) => ({ id: x.id, hour: Math.round(Fmt.hourOfMs(x.ms)), mask: x.mask }))
      .filter((x) => { const c = siteOf(x.id); return c && c.landable && x.hour >= 0 && x.hour < S.index.hours; }).slice(0, MAX);
    const seg = $('cmpWin');
    seg.setAttribute('aria-label', t('cmp.window'));
    seg.innerHTML = WINDOWS.map((d) => `<button type="button" data-v="${d}" aria-pressed="${d === win}">${esc(t('cmp.days', { n: d }))}</button>`).join('');
    seg.onclick = (e) => { const b = e.target.closest('button'); if (!b) return; win = Number(b.dataset.v); seg.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', String(x === b))); render(); };
    $('cmpDiff').onchange = (e) => { showDiff = e.target.checked; paint(); };
    $('cmpClear').onclick = () => { list = []; save(); count(); render(); };
    $('cmpBack').onclick = () => cb.close();
    const cols = $('cmpCols');
    cols.addEventListener('click', onClick);
    cols.addEventListener('change', onChange);
    cols.addEventListener('pointermove', onMove);
    cols.addEventListener('pointerleave', () => { hoverOff = null; drawAll(); readAll(); });
    new ResizeObserver(() => { if (!$('cmpScene').hidden) drawAll(); }).observe(cols);
    count();
  }

  // üstteki kalıcı "Karşılaştır (n)" tuşları
  function count() {
    document.querySelectorAll('[data-cmp-open]').forEach((b) => {
      b.querySelector('span').textContent = t('cmp.open', { n: list.length });
      b.classList.toggle('has', list.length > 0);
    });
  }

  // o anki nokta + tarih + anten payını sabitle. Dönen: { ok, letter } ya da { ok: false, reason }
  function add(site, hour, mask) {
    if (!site) return { ok: false, reason: t('cmp.noSite') };
    if (!site.landable) return { ok: false, reason: t('cmp.noPackShort') };
    if (list.length >= MAX) return { ok: false, reason: t('cmp.full', { n: MAX }) };
    hour = clamp(Math.round(hour), 0, S.index.hours - 1);
    if (list.some((x) => x.id === site.id && x.hour === hour && x.mask === mask)) return { ok: false, reason: t('cmp.dup') };
    list.push({ id: site.id, hour, mask });
    save(); count();
    if (!$('cmpScene').hidden) render();
    return { ok: true, letter: letter(list.length - 1) };
  }

  function open() {
    setText($('cmpBackL'), t(S.prevScene === 'cockpit' && S.data ? 'cmp.backCockpit' : 'top.back'));
    render();
  }

  // ---------- hesap ----------
  async function render() {
    const my = ++token;
    count();
    $('cmpClear').disabled = !list.length;
    if (!list.length) { results = []; paint(); return; }
    setText($('cmpSummary'), t('app.loading'));
    try {
      const out = [];
      for (const sc of list) {
        const site = siteOf(sc.id), core = await cb.core(sc.id);
        out.push({ sc, site, core, st: Sim.windowStats(core, sc.hour, win * 24, sc.mask) });
      }
      if (my !== token) return;
      results = out;
      paint();
    } catch (e) {
      console.error(e);
      if (my === token) setText($('cmpSummary'), t('app.loadError', { msg: e.message }));
    }
  }

  // satırlar: [anahtar, değer, büyük olan mı iyi, birim]
  const ROWS = [
    ['sun', (st) => st.sunPct, true, 'pct'],
    ['earth', (st) => st.earthPct, true, 'pct'],
    ['both', (st) => st.bothPct, true, 'pct'],
    ['dark', (st) => st.longestDarkH / 24, false, 'day'],
    ['gap', (st) => st.longestGapH / 24, false, 'day'],
  ];
  const fmtV = (v, unit) => (unit === 'pct' ? Fmt.pct(v) : Fmt.days(v));
  const fmtD = (d, unit) => (Math.abs(d) < 0.05 ? '=' : (d > 0 ? '+' : '−') + Fmt.num(Math.abs(d), 1) + (unit === 'pct' ? '' : ' ' + t('unit.day')));

  // tek cümlelik özet: ortak pencerede (Güneş + Dünya) kim önde, en uzun karanlık nasıl değişiyor
  function summary() {
    if (!results.length) return t('cmp.empty');
    if (results.length === 1) return t('cmp.one');
    const both = results.map((r) => r.st.bothPct);
    let best = 0;
    both.forEach((v, i) => { if (v > both[best]) best = i; });
    let ref = 0;
    if (best === 0) { ref = 1; both.forEach((v, i) => { if (i && v > both[ref]) ref = i; }); }
    const d = both[best] - both[ref];
    if (d < 0.05) return t('cmp.sumTie', { v: Fmt.pct(both[best]) });
    const dd = (results[best].st.longestDarkH - results[ref].st.longestDarkH) / 24;
    const dark = Math.abs(dd) < 0.05 ? t('cmp.sumDarkSame') : t(dd < 0 ? 'cmp.sumDarkShorter' : 'cmp.sumDarkLonger', { v: Fmt.num(Math.abs(dd), 1) });
    return t('cmp.sumLead', { a: letter(best), bFrom: t('cmp.from')[letter(ref)], v: Fmt.num(d, 1), av: Fmt.pct(both[best]), bv: Fmt.pct(both[ref]) }) + ' ' + dark;
  }

  function landingHTML(st, sc) {
    const L = st.landing, out = [];
    const rel = (v) => t(v >= 0 ? 'geo.above' : 'geo.below', { v: Fmt.num(Math.abs(v), 2) });
    const until = (h) => (h == null ? t('cmp.noChange') : Fmt.dur(h));
    out.push(`<div>${icon('sun', 'sun')}<span>${esc(t('cmp.landSun', { rel: rel(L.sunMargin), disc: Fmt.pct0(L.disc * 100) }))}<br>${esc(t(L.sunUp ? 'cmp.toDark' : 'cmp.toLight', { d: until(L.sunChangeH) }))}</span></div>`);
    out.push(`<div>${icon('earth', 'earth')}<span>${esc(t('cmp.landEarth', { rel: rel(L.earthMargin), s: t(L.linkUp ? 'comm.linkUp' : 'comm.linkDown').toLocaleLowerCase(LOCALE), m: Fmt.num(sc.mask, 1) }))}<br>${esc(t(L.linkUp ? 'cmp.toLoss' : 'cmp.toLink', { d: until(L.linkChangeH) }))}</span></div>`);
    return out.join('');
  }

  function paint() {
    setText($('cmpSummary'), summary());
    const n = results.length;
    const vals = ROWS.map(([, f]) => results.map((r) => f(r.st)));
    const bestOf = ROWS.map(([, , hi], k) => (n > 1 ? (hi ? Math.max(...vals[k]) : Math.min(...vals[k])) : null));
    const cols = results.map((r, i) => {
      const { sc, site, st } = r;
      const rows = ROWS.map(([key, , , unit], k) => {
        const v = vals[k][i], best = bestOf[k] != null && Math.abs(v - bestOf[k]) < 0.05;
        const diff = showDiff && i > 0 ? `<i class="x-d">${esc(fmtD(v - vals[k][0], unit))}</i>` : '';
        return `<div class="x-row${best ? ' best' : ''}" title="${esc(t('cmp.rowTitle.' + key))}"><span>${icon({ sun: 'sun', earth: 'earth', both: 'both', dark: 'dark', gap: 'cut' }[key])}${esc(t('cmp.row.' + key))}</span><span class="x-v"><b>${fmtV(v, unit)}</b>${diff}</span></div>`;
      }).join('');
      const clip = st.clipped ? `<p class="x-clip">${icon('warn')}<span>${esc(t('cmp.clipped', { got: Fmt.num((st.end - st.start) / 24, 1), want: win, end: Fmt.date(S.index.hours - 1, true) }))}</span></p>` : '';
      return `<article class="x-col panel" data-i="${i}" title="${esc(t('cmp.openTitle'))}">
        <header class="x-ch"><span class="x-let">${letter(i)}</span>
          <div class="x-id"><b>${esc(site.reg.code)} · ${esc(site.region)}</b><small>${esc(nameOf(site))} · ${esc(Fmt.latlon(site.lat, site.lon))}</small></div>
          <button type="button" class="btn btn-sm x-rm" data-act="rm" aria-label="${esc(t('cmp.remove'))}" title="${esc(t('cmp.remove'))}">${icon('cut')}</button></header>
        <div class="x-when"><label class="datefield"><span>${esc(t('cmp.landing'))}</span><input type="datetime-local" class="x-date" step="3600" min="${Fmt.toInput(0)}" max="${Fmt.toInput(S.index.hours - 1)}" value="${Fmt.toInput(sc.hour)}"><small>${esc(t('top.utc'))}</small></label>
          <small class="x-mask">${esc(t('cmp.mask', { v: Fmt.num(sc.mask, 1) }))}</small></div>
        <div class="x-rows">${rows}</div>
        <div class="x-land"><p class="x-lh">${esc(t('cmp.atLanding'))}</p>${landingHTML(st, sc)}</div>
        ${clip}
        <div class="x-strips"><div class="x-sl" aria-hidden="true"><span>${icon('sun', 'sun')}</span><span>${icon('earth', 'earth')}</span><span>${icon('both', 'both')}</span></div><canvas class="x-cv" role="img" aria-label="${esc(t('cmp.stripAlt', { k: letter(i) }))}"></canvas></div>
        <p class="x-read"></p>
        <footer class="x-foot2">
          <span class="x-copy"><span>${esc(t('cmp.copy'))}</span><button type="button" class="btn btn-sm" data-act="copy" data-sign="-1">−</button><input type="number" class="x-n" min="1" max="365" step="1" value="${shift}" aria-label="${esc(t('cmp.copyN'))}"><span>${esc(t('unit.day'))}</span><button type="button" class="btn btn-sm" data-act="copy" data-sign="1">+</button></span>
          <button type="button" class="btn btn-sm" data-act="open">${esc(t('cmp.openCockpit'))}</button>
        </footer>
      </article>`;
    });
    if (n < MAX) cols.push(`<article class="x-col x-empty panel"><p>${esc(t(n ? 'cmp.slot' : 'cmp.empty'))}</p><p class="sub">${esc(t('cmp.how'))}</p></article>`);
    $('cmpCols').innerHTML = cols.join('');
    $('cmpCols').dataset.n = String(cols.length);
    setText($('cmpFoot'), t('cmp.foot', { h: Fmt.num(S.height, 0) }));
    drawAll(); readAll();
  }

  // ---------- şeritler: Güneş (disk oranı), Dünya (bağlantı), ikisi birlikte; x ekseni = inişten sonraki süre ----------
  function drawOne(cv, r) {
    const f = fitCanvas(cv), c = cv.getContext('2d'), m = r.st.model, a0 = r.st.start, span = win * 24;
    const W = f.w - 2 * PADX, cols = Math.max(1, Math.round(W));
    c.setTransform(f.dpr, 0, 0, f.dpr, 0, 0);
    c.clearRect(0, 0, f.w, f.h);
    const colors = [cssVar('--sun'), cssVar('--earth'), cssVar('--both')], rows = [0, ROW + GAP, 2 * (ROW + GAP)];
    c.fillStyle = '#171b1c';
    rows.forEach((y) => c.fillRect(PADX, y, W, ROW));
    for (let px = 0; px < cols; px++) {
      const a = a0 + Math.floor((px / cols) * span), b = Math.max(a + 1, a0 + Math.floor(((px + 1) / cols) * span));
      if (a >= r.st.end) break;
      let s = 0, e = 0, k = 0, cnt = 0;
      for (let i = a; i < Math.min(b, r.st.end); i++) { s += m.sunFrac[i]; e += m.linkUp[i]; k += m.both[i]; cnt++; }
      [s / cnt, e / cnt, k / cnt].forEach((v, j) => { if (v > 0.003) { c.globalAlpha = 0.25 + 0.75 * v; c.fillStyle = colors[j]; c.fillRect(PADX + px, rows[j], 1.05, ROW); } });
    }
    c.globalAlpha = 1;
    // veri sonunu aşan kısım: taralı
    if (r.st.clipped) {
      const xc = PADX + ((r.st.end - a0) / span) * W, hgt = 3 * ROW + 2 * GAP;
      c.save(); c.beginPath(); c.rect(xc, 0, PADX + W - xc, hgt); c.clip();
      c.fillStyle = '#0a0c0d'; c.fillRect(xc, 0, W, hgt);
      c.strokeStyle = cssVar('--rule-2'); c.lineWidth = 1;
      for (let x = xc - hgt; x < PADX + W; x += 6) { c.beginPath(); c.moveTo(x, hgt); c.lineTo(x + hgt, 0); c.stroke(); }
      c.restore();
    }
    // gün cetveli: inişten sonraki gün sayısı
    const ry = 3 * ROW + 2 * GAP + 2, every = win <= 14 ? 2 : win <= 30 ? 5 : 15, minor = win <= 30 ? 1 : 5;
    c.font = '500 10.5px "IBM Plex Mono", monospace'; c.textBaseline = 'top'; c.fillStyle = cssVar('--ink-2');
    for (let dday = 0; dday <= win; dday += minor) {
      const x = Math.round(PADX + (dday / win) * W) + 0.5, lab = dday % every === 0;
      c.strokeStyle = lab ? 'rgba(201,210,205,0.55)' : 'rgba(201,210,205,0.25)';
      c.beginPath(); c.moveTo(x, ry - 1); c.lineTo(x, ry + (lab ? 5 : 2)); c.stroke();
      if (lab) { c.textAlign = dday === 0 ? 'left' : dday === win ? 'right' : 'center'; c.fillText(dday === 0 ? t('cmp.day0') : '+' + dday, x + (dday === 0 ? 2 : dday === win ? -2 : 0), ry + 5); }
    }
    // imleç (bütün sütunlarda aynı "inişten sonraki süre")
    if (hoverOff != null) {
      const x = PADX + (hoverOff / span) * W;
      c.fillStyle = cssVar('--ink'); c.fillRect(x - 0.75, -1, 1.5, 3 * ROW + 2 * GAP + 2);
    }
  }
  function drawAll() {
    document.querySelectorAll('#cmpCols .x-cv').forEach((cv) => { const r = results[Number(cv.closest('.x-col').dataset.i)]; if (r) drawOne(cv, r); });
  }
  // fareyle okuma: o sütunun tarihi/saati ve o andaki durum
  function readAll() {
    document.querySelectorAll('#cmpCols .x-col[data-i]').forEach((col) => {
      const r = results[Number(col.dataset.i)], el = col.querySelector('.x-read');
      if (!r) return;
      if (hoverOff == null) { el.textContent = t('cmp.readHint'); el.classList.add('hint'); return; }
      el.classList.remove('hint');
      const h = r.st.start + Math.round(hoverOff), m = r.st.model;
      if (h >= r.st.end) { el.textContent = t('cmp.readNoData'); return; }
      el.textContent = [
        Fmt.date(h, true) + ' ' + Fmt.time(h) + ' ' + t('top.utc'),
        t('cmp.readDay', { d: Fmt.num(hoverOff / 24, 1) }),
        t('tip.sun', { v: Fmt.pct0(m.sunFrac[h] * 100) }),
        t(m.linkUp[h] ? 'tip.link' : 'tip.noLink') + ' (' + Fmt.deg(m.margin[h], 1) + ')',
      ].join(' · ');
    });
  }
  function onMove(e) {
    const cv = e.target.closest('.x-cv');
    if (!cv) { if (hoverOff != null) { hoverOff = null; drawAll(); readAll(); } return; }
    const r = cv.getBoundingClientRect();
    hoverOff = clamp(((e.clientX - r.left - PADX) / Math.max(1, r.width - 2 * PADX)) * win * 24, 0, win * 24 - 1);
    drawAll(); readAll();
  }

  // ---------- sütun eylemleri ----------
  function onClick(e) {
    const col = e.target.closest('.x-col[data-i]');
    if (!col) return;
    const i = Number(col.dataset.i), r = results[i], btn = e.target.closest('[data-act]');
    if (!r) return;
    if (btn && btn.dataset.act === 'rm') { list.splice(i, 1); save(); render(); return; }
    if (btn && btn.dataset.act === 'copy') {
      const nEl = col.querySelector('.x-n'), nDays = clamp(Math.round(Number(nEl.value) || 0), 1, 365);
      shift = nDays;
      const h = r.sc.hour + Number(btn.dataset.sign) * nDays * 24, why = col.querySelector('.x-read');
      if (h < 0 || h > S.index.hours - 1) { why.textContent = t('cmp.copyOut'); return; }
      const res = add(r.site, h, r.sc.mask);
      if (!res.ok) why.textContent = res.reason;
      return;
    }
    // sütuna tıklamak (alan ve tuşlar dışında) ya da "Kokpitte aç": senaryoyu kokpitte açar
    if ((btn && btn.dataset.act === 'open') || !e.target.closest('button, input, label, canvas, select')) cb.land(r.site, { hour: r.sc.hour, mask: r.sc.mask, skip: true });
  }
  function onChange(e) {
    const col = e.target.closest('.x-col[data-i]');
    if (!col) return;
    const i = Number(col.dataset.i);
    if (e.target.classList.contains('x-date')) {
      const h = Fmt.fromInput(e.target.value);
      if (h == null) return;
      list[i].hour = clamp(Math.round(h), 0, S.index.hours - 1);
      save(); render();
    } else if (e.target.classList.contains('x-n')) shift = clamp(Math.round(Number(e.target.value) || 14), 1, 365);
  }

  return { init, add, open, render, get count() { return list.length; }, get list() { return list; }, get results() { return results; } };
})();
