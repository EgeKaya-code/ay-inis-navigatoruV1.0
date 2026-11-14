// ===== briefing: kutup haritası + bölge kartları + bölge içi aday noktalar =====
const Briefing = (() => {
  const R_MOON = 1737.4;
  const SORTS = ['power', 'comm', 'dark', 'balanced'];
  const LABEL_ANCHOR = { nobile_rim_1: 'br', mons_mouton_plateau: 'tr', mons_mouton: 'tl' };
  const CAND_KK = 7;   // px/km: haritada bundan uzaktayken aday noktaları üst üste biner, çizilmez
  const RING_KK = 45;  // px/km: iniş hatası halkaları (100 m ve 300 m) ancak bu kadar yakından seçilir
  const SPAN_MIN = 3;  // km: adaylar arası 300 m seçilebilsin diye
  let idx, cv, ctx, cb = {};
  let sort = 'power', selected = null, hover = null;
  let pick = null, hoverCand = null; // seçili bölgede inilecek nokta ve farenin üstündeki aday
  const weights = { sun: 1, earth: 1, dark: 1 }; // dengeli puanın ağırlıkları (eşitken veri dosyasındaki sırayla aynı)
  let moreOpen = window.innerHeight >= 1000;      // ayrıntı satırları: kısa ekranda kapalı başlar, kartlara yer kalsın
  const view = { cx: 0, cy: 60, span: 480 }, goal = { cx: 0, cy: 60, span: 480 };
  let raf = 0, dims = { w: 1, h: 1, dpr: 1 };

  // Her kart TEK bir noktanın kendi rakamlarını gösterir: bölgenin 1. adayı (dengeli puanı en yüksek nokta);
  // "Dengeli" sıralamada ağırlıklar değişince o ağırlıklarla en yüksek puanlı nokta. Sıralama da o noktaya göre.
  const cardPoint = (s) => (sort === 'balanced' ? bestWeighted(s).c : s.top);
  const val = {
    power: (s) => s.top.m.terrain.sun_energy_pct,
    comm: (s) => s.top.m.terrain_antenna_1deg.earth_pct,
    dark: (s) => -s.top.m.terrain.longest_dark_days,
    balanced: (s) => bestWeighted(s).score,
  };
  // seçili ağırlıklarla bölgenin en yüksek puanlı noktası
  function bestWeighted(s) {
    let best = null;
    for (const c of s.cands) { const score = Sim.weighted(c.m, weights); if (!best || score > best.score) best = { c, score }; }
    return best;
  }
  const sorted = () => idx.sites.slice().sort((a, b) => val[sort](b) - val[sort](a));
  const cur = () => idx.sites.find((x) => x.id === selected);
  const candName = (c) => (c.legacy ? t('cand.legacy') : t('cand.title', { n: c.rank }));

  // ---------- kartlardaki mini şerit: 2027'de Güneş (üst) ve Dünya, 1° payla (alt); bölgenin 1. adayı ----------
  const BINS = 180, strips = new Map();
  function stripData(se) {
    const sf = se.sun_visible_fraction, em = se.earth_margin_deg, n = sf.length, sun = new Float32Array(BINS), earth = new Float32Array(BINS);
    for (let b = 0; b < BINS; b++) {
      const a = Math.floor((b / BINS) * n), e = Math.floor(((b + 1) / BINS) * n);
      let s = 0, k = 0;
      for (let i = a; i < e; i++) { s += sf[i]; if (em[i] > 1) k++; }
      sun[b] = s / (e - a); earth[b] = k / (e - a);
    }
    return { sun, earth };
  }
  function drawStrip(el) {
    const d = strips.get(el.dataset.id);
    if (!d) return;
    const f = fitCanvas(el), c = el.getContext('2d'), bw = f.w / BINS;
    c.setTransform(f.dpr, 0, 0, f.dpr, 0, 0);
    c.clearRect(0, 0, f.w, f.h);
    for (let b = 0; b < BINS; b++) {
      if (d.sun[b] > 0.01) { c.globalAlpha = 0.2 + 0.8 * d.sun[b]; c.fillStyle = cssVar('--sun'); c.fillRect(b * bw, 0, bw + 0.4, 3); }
      if (d.earth[b] > 0.01) { c.globalAlpha = 0.2 + 0.8 * d.earth[b]; c.fillStyle = cssVar('--earth'); c.fillRect(b * bw, 4, bw + 0.4, 3); }
    }
    c.globalAlpha = 1;
  }
  const drawStrips = () => document.querySelectorAll('#cards .ministrip').forEach(drawStrip);
  async function preloadStrips() {
    for (const s of sorted()) {
      if (strips.has(s.id)) continue;
      try { strips.set(s.id, stripData(await Data.loadYear(s.top.id, idx.defaultYear))); drawStrips(); } catch (e) { /* şerit olmadan da kart çalışır */ }
    }
  }

  // ---------- kartlar ----------
  function renderSortBar() {
    const bar = $('sortBar');
    bar.setAttribute('aria-label', t('brief.sortLabel'));
    bar.innerHTML = SORTS.map((k) => `<button type="button" data-v="${k}" aria-pressed="${k === sort}">${esc(t('brief.sort.' + k))}</button>`).join('');
    bar.onclick = (e) => {
      const b = e.target.closest('button'); if (!b) return;
      sort = b.dataset.v; renderSortBar(); renderCards();
    };
    setText($('sortNote'), t('brief.sortNote.' + sort));
    renderWeights();
  }

  // dengeli sıralamada üç ölçünün ağırlığı (0–5); hepsi eşitken puan değişmez
  function renderWeights() {
    const bar = $('weightBar');
    bar.hidden = sort !== 'balanced';
    if (bar.hidden) return;
    const equal = weights.sun === weights.earth && weights.earth === weights.dark;
    bar.innerHTML = `<span class="wb-l">${esc(t('brief.weights'))}</span>` + [['sun', 'sun'], ['earth', 'earth'], ['dark', 'dark']].map(([k, ic]) =>
      `<label class="wb">${icon(ic, ic)}<span>${esc(t('brief.weight.' + k))}</span><input type="range" min="0" max="5" step="1" value="${weights[k]}" data-k="${k}" aria-label="${esc(t('brief.weights') + ': ' + t('brief.weight.' + k))}"><output>${weights[k]}</output></label>`).join('')
      + `<button type="button" class="btn btn-sm" id="weightReset"${equal ? ' disabled' : ''}>${esc(t('brief.weightReset'))}</button>`;
  }
  function bindWeights() {
    const bar = $('weightBar');
    bar.addEventListener('input', (e) => {
      const k = e.target.dataset.k; if (!k) return;
      weights[k] = Number(e.target.value);
      e.target.nextElementSibling.textContent = e.target.value;
      $('weightReset').disabled = weights.sun === weights.earth && weights.earth === weights.dark;
      renderCards(); renderDetail();
    });
    bar.addEventListener('click', (e) => {
      if (!e.target.closest('#weightReset')) return;
      weights.sun = weights.earth = weights.dark = 1;
      renderWeights(); renderCards(); renderDetail();
    });
  }

  function renderCards() {
    const list = sorted();
    const head = `<li class="cards-head" aria-hidden="true"><span></span><span></span><span>${esc(t(idx.hasCandidates ? 'brief.headPoint' : 'brief.sampleShort'))}</span><span>${esc(t('brief.metric.sun'))}</span><span>${esc(t('brief.metric.earth1'))}</span><span>${esc(t('brief.metric.dark'))}</span></li>`;
    $('cards').innerHTML = head + list.map((s, i) => {
      const many = s.stat.n > 1, c = cardPoint(s), m = c.m;
      // üç rakam da aynı noktanın (alt satırda adı yazan nokta) kendi rakamlarıdır
      const sun = m.terrain.sun_any_pct, earth = m.terrain_antenna_1deg.earth_pct, dark = m.terrain.longest_dark_days;
      const dk = (d) => Math.min(100, (d / 30) * 100);
      const flag = !many && s.search_note ? `<span class="flag">${icon('warn')}${esc(t('brief.searchNote'))}</span>` : '';
      const who = c.legacy ? t('brief.sampleShort') : t('cand.short', { n: c.rank });
      const sub = who + ' · ' + (sort === 'balanced' ? t('brief.metric.score') + ' ' + Fmt.num(Sim.weighted(m, weights), 1) : t('brief.energyShort', { v: Fmt.pct(m.terrain.sun_energy_pct) }))
        + (many ? ' · ' + t('brief.nPoints', { n: s.stat.n }) : '');
      return `<li><button type="button" class="card" data-id="${s.id}" aria-pressed="${s.id === selected}">
        <span class="rank">${String(i + 1).padStart(2, '0')}</span>
        <span class="code">${esc(s.reg.code)}</span>
        <span class="nm"><b>${esc(s.region)}</b>${flag}</span>
        <span class="met met-sun"><span class="v">${icon('sun')}<span data-f="best">${Fmt.pct(sun)}</span></span><span class="bar"><i style="width:${sun.toFixed(1)}%"></i></span></span>
        <span class="met met-earth"><span class="v">${icon('earth')}<span data-f="best">${Fmt.pct(earth)}</span></span><span class="bar"><i style="width:${earth.toFixed(1)}%"></i></span></span>
        <span class="met met-dark"><span class="v">${icon('dark')}<span data-f="best">${Fmt.num(dark, 1)}</span><small>${esc(t('unit.day'))}</small></span><span class="bar"><i style="width:${dk(dark).toFixed(1)}%"></i></span></span>
        <small class="subline">${esc(sub)}</small><canvas class="ministrip" data-id="${s.id}" aria-hidden="true"></canvas>
      </button></li>`;
    }).join('');
    drawStrips();
  }

  // ---------- seçili nokta: ayrıntı, aday çubuğu ----------
  const trio = (c) => `${icon('sun', 'sun')}<b>${Fmt.pct(c.m.terrain.sun_any_pct)}</b> ${icon('earth', 'earth')}<b>${Fmt.pct(c.m.terrain_antenna_1deg.earth_pct)}</b> ${icon('dark')}<b>${Fmt.days(c.m.terrain.longest_dark_days)}</b>`;
  const trioText = (c) => `${t('brief.metric.sun')} ${Fmt.pct(c.m.terrain.sun_any_pct)} · ${t('brief.metric.earth1')} ${Fmt.pct(c.m.terrain_antenna_1deg.earth_pct)} · ${t('brief.metric.dark')} ${Fmt.days(c.m.terrain.longest_dark_days)}`;

  function renderCandBar() {
    const s = cur(), bar = $('candBar');
    if (!s || s.cands.length < 2) { bar.hidden = true; bar.innerHTML = ''; return; }
    bar.hidden = false;
    bar.setAttribute('aria-label', t('cand.barLabel'));
    const chip = (c) => `<button type="button" class="cand${c.landable ? ' full' : ''}${c.legacy ? ' legacy' : ''}${c.pareto ? ' par' : ''}" data-i="${s.cands.indexOf(c)}" aria-pressed="${c === pick}" title="${esc(candName(c) + (c.pareto ? ' · ' + t('cand.pareto') : '') + ' · ' + trioText(c))}">${esc(c.legacy ? t('cand.legacyChip') : String(c.rank))}</button>`;
    bar.innerHTML = s.cands.filter((c) => c.legacy).concat(s.cands.filter((c) => !c.legacy)).map(chip).join('');
  }

  function renderDetail() {
    const s = cur(), c = pick;
    const box = $('siteDetail');
    renderCandBar();
    if (!s || !c) { box.innerHTML = ''; $('btnLand').disabled = true; $('bAddCmp').disabled = true; return; }
    const mm = c.m, score = Fmt.num(Sim.weighted(mm, weights), 1);
    // iniş hatası: hedefin r metre çevresindeki halkada en kötü üç rakam ve eğim sınırını aşan nokta sayısı
    const ring = (r) => `<div class="sd-ring${r.steep ? ' steep' : ''}"><span>${esc(t('cand.ring', { r: Fmt.num(r.radius_m, 0) }))}</span>`
      + `<span class="sd-trio" title="${esc(t('cand.ringEnergy'))}">${icon('sun', 'sun')}<b>${Fmt.pct(r.worst.sun_energy_pct)}</b> ${icon('earth', 'earth')}<b>${Fmt.pct(r.worst.earth_1deg_pct)}</b> ${icon('dark')}<b>${Fmt.days(r.worst.longest_dark_days)}</b></span>`
      + `<span>${esc(r.steep ? t('cand.ringSteep', { k: r.steep, n: r.n }) : t('cand.ringFlat', { n: r.n }))}</span></div>`;
    const rings = c.sens ? c.sens.rings : [];
    const top = [
      `<div class="sd-h"><b>${esc(s.reg.code)} · ${esc(s.region)}</b><span>${Fmt.latlon(c.lat, c.lon)}</span></div>`,
      `<div class="sd-pt" title="${esc(c.legacy ? t('cand.legacyLine') : t('cand.rankLine', { of: s.cands.filter((x) => !x.legacy).length }))}"><b>${esc(candName(c))}</b>${c.pareto ? `<i class="tag" title="${esc(t('cand.paretoLong'))}">${esc(t('cand.pareto'))}</i>` : ''}<span class="sd-trio">${trio(c)}</span></div>`,
    ];
    if (rings.length) top.push(ring(rings[0]));
    const more = rings.slice(1).map(ring).concat([
      `<div>${esc(t('brief.height', { v: Fmt.num(c.ground_height_m, 0) }))} · ${esc(t('brief.slope', { v: Fmt.num(c.slope_deg, 1) + '°' }))} · ${esc(t('brief.area', { v: Fmt.num(s.reg.area_km2, 0) }))} · ${esc(t('cand.score', { score }))}</div>`,
      `<div>${esc(t('brief.energyLong', { v: Fmt.pct(mm.terrain.sun_energy_pct), any: Fmt.pct(mm.terrain.sun_any_pct) }))} · ${esc(t('brief.bothLong', { v: Fmt.pct(mm.terrain_antenna_1deg.sun_and_earth_pct) }))}</div>`,
      `<div>${esc(t('brief.metric.earth'))}: ${esc(t('brief.antenna1'))} <b>${Fmt.pct(mm.terrain_antenna_1deg.earth_pct)}</b> · ${esc(t('brief.antenna0', { v: Fmt.pct(mm.terrain.earth_pct) }))} · ${esc(t('brief.noEarth', { v: Fmt.days(mm.terrain_antenna_1deg.longest_no_earth_days) }))}</div>`,
    ]);
    if (c.dominator) more.push(`<div>${esc(t('cand.dominated', { name: candName(c.dominator) }))}</div>`);
    if (c.nasaSun != null) more.push(`<div class="sd-nasa">${esc(t('cand.nasa', { sun: Fmt.pct(c.nasaSun), earth: Fmt.pct(c.nasaEarth), ours: Fmt.pct(mm.terrain.sun_any_pct) }))}</div>`);
    if (mm.min_earth_margin_deg < 0.5) more.push(`<div class="warnline">${icon('warn')}<span>${esc(t('brief.criticalLong', { v: Fmt.num(mm.min_earth_margin_deg, 2) + '°' }))}</span></div>`);
    if (c.legacy && s.search_note) more.push(`<div class="warnline">${icon('warn')}<span>${esc(t(s.cands.length > 1 ? 'cand.legacyNote' : 'brief.searchNoteLong', { area: Fmt.num(s.reg.area_km2, 0) }))}</span></div>`);
    box.innerHTML = top.join('') + `<details class="sd-more"${moreOpen ? ' open' : ''}><summary>${esc(t('cand.more'))}</summary>${more.join('')}</details>`;
    box.querySelector('.sd-more').addEventListener('toggle', (e) => { moreOpen = e.target.open; });
    $('btnLand').disabled = !c.landable;
    // yalnız tam veri paketi (saatlik seri) olan noktalar karşılaştırmaya eklenebilir
    $('bAddCmp').disabled = !c.landable;
    $('bAddCmp').title = c.landable ? '' : t('cmp.noPack');
    setText($('landHint'), c.landable ? t('brief.landHint', { name: s.region + ' · ' + candName(c) }) : t('cand.noPack'));
  }

  // bölge seç. Varsayılan iniş noktası kartta rakamları gösterilen noktadır (1. aday); çubuktan başka aday seçilebilir.
  function select(id, o = {}) {
    if (id !== selected || !pick) { const s0 = idx.sites.find((x) => x.id === id) || null; pick = s0 ? (cardPoint(s0).landable ? cardPoint(s0) : s0) : null; }
    selected = id;
    const s = cur();
    setHoverCand(null);
    document.querySelectorAll('#cards .card').forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.id === id)));
    if (o.scroll) { const c = document.querySelector(`#cards .card[data-id="${id}"]`); if (c) c.scrollIntoView({ block: 'nearest' }); }
    if (s) Data.loadHeat(s, draw);
    renderDetail(); renderLegend();
    if (o.zoom && s) zoomRegion(s); else draw();
    if (cb.onSelect && pick) cb.onSelect(pick);
  }
  // iniş tarihi alanı uygulama durumundaki iniş anını gösterir
  function syncDate() {
    const el = $('bDate');
    if (el && cb.state && document.activeElement !== el) el.value = Fmt.toInput(cb.state.landing);
  }
  function pickCand(c) {
    pick = c;
    renderDetail(); draw();
    if (cb.onSelect) cb.onSelect(c);
  }

  // ---------- harita ----------
  const k = () => Math.min(dims.w, dims.h) / view.span;
  const sx = (x) => dims.w / 2 + (x - view.cx) * k();
  const sy = (y) => dims.h / 2 - (y - view.cy) * k();
  const latR = (lat) => 2 * R_MOON * Math.tan(((90 - Math.abs(lat)) / 2) * D2R);

  function bboxOf(poly) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const [x, y] of poly) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    return { x0, y0, x1, y1 };
  }
  // b kutusu haritaya sığacak şekilde hedef görünüm
  function frame(b, pad, minSpan) {
    dims = fitCanvas(cv);
    const w = (b.x1 - b.x0) * pad, h = (b.y1 - b.y0) * pad, short = Math.min(dims.w, dims.h);
    goal.cx = (b.x0 + b.x1) / 2; goal.cy = (b.y0 + b.y1) / 2;
    goal.span = Math.max(minSpan, w * (short / dims.w), h * (short / dims.h));
  }
  function fitAll(instant) {
    let x0 = 0, y0 = 0, x1 = 0, y1 = 0; // kutup (0,0) hep görünsün
    for (const s of idx.sites) { const b = bboxOf(s.reg.polygon_ps_km); x0 = Math.min(x0, b.x0); y0 = Math.min(y0, b.y0); x1 = Math.max(x1, b.x1); y1 = Math.max(y1, b.y1); }
    frame({ x0, y0, x1, y1 }, 1.22, SPAN_MIN);
    if (instant) Object.assign(view, goal);
    animate();
  }
  function zoomRegion(s) { frame(bboxOf(s.reg.polygon_ps_km), 1.3, SPAN_MIN); animate(); }
  function zoomCands() {
    const s = cur();
    if (!s) return;
    frame(bboxOf(s.cands.map((c) => c.ps_km)), 1.5, 5);
    animate();
  }
  // seçili noktaya, iniş hatası halkaları seçilecek kadar yaklaş
  function zoomPick() {
    if (!pick) return;
    goal.cx = pick.ps_km[0]; goal.cy = pick.ps_km[1]; goal.span = SPAN_MIN;
    animate();
  }
  // inişe geçerken noktaya yaklaş (zaten daha yakınsa uzaklaşma)
  function zoomTo(site, ms = 900) {
    if (!site) return Promise.resolve();
    goal.cx = site.ps_km[0]; goal.cy = site.ps_km[1]; goal.span = Math.min(goal.span, 46);
    animate();
    return new Promise((res) => setTimeout(res, ms));
  }
  function animate() {
    if (raf) return;
    const step = () => {
      raf = 0;
      let moving = false;
      for (const key of ['cx', 'cy', 'span']) {
        const d = goal[key] - view[key];
        if (Math.abs(d) > (key === 'span' ? 0.05 : 0.02) * Math.min(1, view.span / 40)) { view[key] += d * 0.14; moving = true; } else view[key] = goal[key];
      }
      draw();
      if (moving) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }

  const showCands = (s) => s && s.id === selected && s.cands.length > 1 && k() >= CAND_KK;

  function diamond(px, py, r) {
    ctx.beginPath(); ctx.moveTo(px, py - r); ctx.lineTo(px + r, py); ctx.lineTo(px, py + r); ctx.lineTo(px - r, py); ctx.closePath();
  }

  // seçili noktanın iniş hatası halkaları (yalnız çok yakından): halka kesik çizgi, üstündeki hesap noktaları
  // düzse küçük nokta, eğim sınırını aşıyorsa uyarı renginde çarpı. Harita kuzeyi yukarıda değil; yön enlem/boylamdan.
  function drawRings(c, px, py, line) {
    const warn = cssVar('--warn'), kk = k();
    for (const r of c.sens.rings) {
      ctx.setLineDash([3, 3]); ctx.lineWidth = 1; ctx.strokeStyle = line;
      ctx.beginPath(); ctx.arc(px, py, (r.radius_m / 1000) * kk, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([]);
      for (const o of r.offsets) {
        const rho = latR(o.lat), a = o.lon * D2R, ox = sx(rho * Math.sin(a)), oy = sy(rho * Math.cos(a));
        if (o.flat) { ctx.fillStyle = line; ctx.beginPath(); ctx.arc(ox, oy, 2, 0, Math.PI * 2); ctx.fill(); }
        else { ctx.strokeStyle = warn; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(ox - 3, oy - 3); ctx.lineTo(ox + 3, oy + 3); ctx.moveTo(ox + 3, oy - 3); ctx.lineTo(ox - 3, oy + 3); ctx.stroke(); }
      }
    }
  }

  // aday noktalar: iniş paketi olanlar dolu, yalnız rakamı olanlar içi boş, eski örnek nokta eşkenar dörtgen
  function drawCands(s, line) {
    const order = s.cands.slice().sort((a, b) => (a === pick) - (b === pick) || a.landable - b.landable);
    for (const c of order) {
      const px = sx(c.ps_km[0]), py = sy(c.ps_km[1]), on = c === pick, hov = c === hoverCand;
      ctx.lineWidth = 3.4; ctx.strokeStyle = 'rgba(0,0,0,0.8)';
      if (c.legacy) { diamond(px, py, 5.5); ctx.stroke(); ctx.lineWidth = 1.6; ctx.strokeStyle = on || hov ? '#fff' : line; ctx.stroke(); }
      else {
        ctx.beginPath(); ctx.arc(px, py, 3.6, 0, Math.PI * 2); ctx.stroke();
        if (c.landable) { ctx.fillStyle = on || hov ? '#fff' : line; ctx.fill(); }
        else { ctx.lineWidth = 1.4; ctx.strokeStyle = on || hov ? '#fff' : line; ctx.stroke(); }
      }
      if (on || hov) {
        ctx.lineWidth = 3.4; ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.beginPath(); ctx.arc(px, py, on ? 12 : 8.5, 0, Math.PI * 2); ctx.stroke();
        ctx.lineWidth = on ? 2 : 1.2; ctx.strokeStyle = '#fff'; ctx.stroke();
      }
      if (on && c.sens && k() >= RING_KK) drawRings(c, px, py, line);
      if (c.landable && !c.legacy) {
        ctx.font = '500 11px "IBM Plex Mono", monospace'; ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
        ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.strokeText(String(c.rank), px + 6, py - 4);
        ctx.fillStyle = '#fff'; ctx.fillText(String(c.rank), px + 6, py - 4);
      }
    }
  }

  function draw() {
    if (!ctx) return;
    dims = fitCanvas(cv);
    const { w, h, dpr } = dims;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#050607'; ctx.fillRect(0, 0, w, h);
    const b = idx.map.bounds, kk = k();
    if (idx.map.image) {
      ctx.globalAlpha = 0.8;
      ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(idx.map.image, sx(b[0]), sy(b[3]), (b[2] - b[0]) * kk, (b[3] - b[1]) * kk);
      ctx.globalAlpha = 1;
      ctx.fillStyle = 'rgba(6,9,10,0.38)'; ctx.fillRect(0, 0, w, h);
    }
    const line = cssVar('--line'), earth = cssVar('--earth');
    ctx.font = '500 11px "IBM Plex Mono", monospace';

    // seçili bölgede NASA aydınlanma haritası (poligon dışı saydam); yakında harita pikselleri olduğu gibi görünür
    const selS = cur(), heat = selS && selS.heat && selS.heat.image ? selS.heat : null;
    if (heat) {
      const hb = heat.bounds;
      ctx.imageSmoothingEnabled = ((hb[2] - hb[0]) * kk) / heat.image.width < 4;
      ctx.globalAlpha = 0.9;
      ctx.drawImage(heat.image, sx(hb[0]), sy(hb[3]), (hb[2] - hb[0]) * kk, (hb[3] - hb[1]) * kk);
      ctx.globalAlpha = 1; ctx.imageSmoothingEnabled = true;
    }

    // enlem çemberleri ve boylamlar
    ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(201,210,205,0.22)'; ctx.fillStyle = 'rgba(201,210,205,0.7)';
    for (const lat of [88, 86, 84, 82]) {
      const r = latR(lat) * kk;
      ctx.beginPath(); ctx.arc(sx(0), sy(0), r, 0, Math.PI * 2); ctx.stroke();
      ctx.textAlign = 'left'; ctx.textBaseline = 'bottom';
      ctx.fillText(lat + '° ' + t('compass.s'), sx(0) + r * Math.SQRT1_2 + 3, sy(0) + r * Math.SQRT1_2);
    }
    for (let lon = 0; lon < 360; lon += 30) {
      const a = lon * D2R, r0 = latR(89) * kk, r1 = latR(80) * kk;
      ctx.beginPath(); ctx.moveTo(sx(0) + Math.sin(a) * r0, sy(0) - Math.cos(a) * r0); ctx.lineTo(sx(0) + Math.sin(a) * r1, sy(0) - Math.cos(a) * r1); ctx.stroke();
    }
    // kutup
    ctx.strokeStyle = line; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.moveTo(sx(0) - 7, sy(0)); ctx.lineTo(sx(0) + 7, sy(0)); ctx.moveTo(sx(0), sy(0) - 7); ctx.lineTo(sx(0), sy(0) + 7); ctx.stroke();
    ctx.fillStyle = line; ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    ctx.font = '600 13px "Barlow Condensed", sans-serif';
    ctx.fillText(t('brief.mapPole').toLocaleUpperCase(LOCALE), sx(0) + 9, sy(0) + 5);
    // Dünya yönü: 0° boylam
    const ex = sx(0), ey = Math.max(26, sy(latR(80.6)));
    ctx.strokeStyle = earth; ctx.fillStyle = earth; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(ex, ey + 20); ctx.lineTo(ex, ey); ctx.moveTo(ex - 5, ey + 7); ctx.lineTo(ex, ey); ctx.lineTo(ex + 5, ey + 7); ctx.stroke();
    ctx.textBaseline = 'middle';
    ctx.fillText(t('brief.mapEarth').toLocaleUpperCase(LOCALE), ex + 9, ey + 8);

    // bölgeler
    const order = idx.sites.slice().sort((a, c) => c.reg.area_km2 - a.reg.area_km2);
    for (const s of order) {
      const sel = s.id === selected, hov = s.id === hover, poly = s.reg.polygon_ps_km;
      ctx.beginPath();
      poly.forEach(([x, y], i) => (i ? ctx.lineTo(sx(x), sy(y)) : ctx.moveTo(sx(x), sy(y))));
      ctx.closePath();
      if (sel && !heat) { ctx.fillStyle = 'rgba(238,242,238,0.14)'; ctx.fill(); }
      ctx.lineWidth = sel ? 2.4 : hov ? 1.8 : 1.1;
      ctx.strokeStyle = sel || hov ? '#ffffff' : line;
      ctx.stroke();
    }
    // iniş noktaları ve etiketler: uzaktan bölge başına tek işaret, yakında seçili bölgenin bütün adayları
    for (const s of order) {
      const sel = s.id === selected;
      if (showCands(s)) drawCands(s, line);
      else {
        const p = sel && pick ? pick : s, px = sx(p.ps_km[0]), py = sy(p.ps_km[1]);
        ctx.strokeStyle = sel ? '#fff' : line; ctx.lineWidth = sel ? 2 : 1.2;
        diamond(px, py, sel ? 6 : 3.5); ctx.stroke();
        if (sel) { ctx.beginPath(); ctx.arc(px, py, 13, 0, Math.PI * 2); ctx.stroke(); }
      }
      const bb = bboxOf(s.reg.polygon_ps_km), anchor = LABEL_ANCHOR[s.id] || 'tl';
      const label = sel || kk > 3.2 ? s.reg.code + ' · ' + s.region.toLocaleUpperCase(LOCALE) : s.reg.code;
      ctx.font = (sel ? '700 16px' : '600 14px') + ' "Barlow Condensed", sans-serif';
      let lx, ly;
      if (anchor === 'br') { ctx.textAlign = 'right'; ctx.textBaseline = 'top'; lx = sx(bb.x1); ly = sy(bb.y0) + 4; }
      else if (anchor === 'tr') { ctx.textAlign = 'right'; ctx.textBaseline = 'bottom'; lx = sx(bb.x1); ly = sy(bb.y1) - 3; }
      else { ctx.textAlign = 'left'; ctx.textBaseline = 'bottom'; lx = sx(bb.x0); ly = sy(bb.y1) - 3; }
      ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.strokeText(label, lx, ly);
      ctx.fillStyle = sel ? '#fff' : line; ctx.fillText(label, lx, ly);
    }
    // ölçek çubuğu
    const barKm = [200, 100, 50, 20, 10, 5, 2, 1, 0.5].find((v) => v * kk < 150) || 0.5;
    ctx.strokeStyle = line; ctx.fillStyle = line; ctx.lineWidth = 1.2;
    const bx = 14, by = 20;
    ctx.beginPath(); ctx.moveTo(bx, by - 4); ctx.lineTo(bx, by); ctx.lineTo(bx + barKm * kk, by); ctx.lineTo(bx + barKm * kk, by - 4); ctx.stroke();
    ctx.font = '500 11px "IBM Plex Mono", monospace'; ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    ctx.fillText(Fmt.num(barKm, barKm < 1 ? 1 : 0) + ' km', bx, by + 4);
    $('mapCands').hidden = !(selS && selS.cands.length > 1);
    $('mapPick').hidden = !(pick && pick.sens);
  }

  // harita açıklaması: ısı haritasının ölçeği ve nokta işaretleri (yalnız aday verisi olan bölgede)
  function renderLegend() {
    const s = cur(), el = $('mapLegend');
    el.hidden = !(s && s.heat);
    if (el.hidden || el.dataset.done) return;
    el.dataset.done = '1';
    el.innerHTML = `<span class="lg-h">${esc(t('cand.legendHeat'))}</span>
      <span class="lg-ramp"><small>${Fmt.pct(0, 0)}</small><i></i><small>${Fmt.pct(100, 0)}</small></span>
      <span class="lg-k"><i class="dot full"></i>${esc(t('cand.legendFull'))}</span>
      <span class="lg-k"><i class="dot"></i>${esc(t('cand.legendNum'))}</span>
      <span class="lg-k"><i class="dia"></i>${esc(t('cand.legendLegacy'))}</span>`;
  }

  function hit(px, py) {
    const x = view.cx + (px - dims.w / 2) / k(), y = view.cy - (py - dims.h / 2) / k();
    let best = null;
    for (const s of idx.sites) {
      const poly = s.reg.polygon_ps_km;
      let inside = false;
      for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
        const [xi, yi] = poly[i], [xj, yj] = poly[j];
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
      }
      const near = Math.hypot(s.ps_km[0] - x, s.ps_km[1] - y) * k() < 12;
      if ((inside || near) && (!best || s.reg.area_km2 < best.reg.area_km2)) best = s;
    }
    return best;
  }
  // fareye en yakın aday (9 px içinde); yalnız adaylar çizilirken
  function hitCand(px, py) {
    const s = cur();
    if (!showCands(s)) return null;
    let best = null, bd = 9;
    for (const c of s.cands) {
      const d = Math.hypot(sx(c.ps_km[0]) - px, sy(c.ps_km[1]) - py);
      if (d < bd) { bd = d; best = c; }
    }
    return best;
  }

  // adayın üç rakamı ve NASA değeri: fareyle üstüne gelince (ya da aday çubuğunda)
  function setHoverCand(c, px, py) {
    const tip = $('mapTip');
    if (c !== hoverCand) {
      hoverCand = c;
      if (c) {
        tip.innerHTML = `<b>${esc(candName(c))}</b><span class="tip-trio">${trio(c)}</span>`
          + (c.nasaSun != null ? `<span>${esc(t('cand.nasaShort', { sun: Fmt.pct(c.nasaSun) }))}</span>` : '')
          + `<small>${esc(t(c.landable ? 'cand.tipLand' : 'cand.tipNoPack'))}</small>`;
      }
      tip.hidden = !c;
      draw();
    }
    if (c && px != null) {
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      tip.style.left = clamp(px + 14 + tw > dims.w ? px - 14 - tw : px + 14, 4, Math.max(4, dims.w - tw - 4)) + 'px';
      tip.style.top = clamp(py + 14 + th > dims.h ? py - 14 - th : py + 14, 4, Math.max(4, dims.h - th - 4)) + 'px';
    }
  }

  function bindMap() {
    let drag = null;
    const pos = (e) => { const r = cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    cv.addEventListener('pointerdown', (e) => { cv.setPointerCapture(e.pointerId); const [x, y] = pos(e); drag = { x, y, cx: view.cx, cy: view.cy, moved: false }; });
    cv.addEventListener('pointermove', (e) => {
      const [x, y] = pos(e);
      if (drag) {
        if (Math.hypot(x - drag.x, y - drag.y) > 4) drag.moved = true;
        if (drag.moved) { setHoverCand(null); goal.cx = view.cx = drag.cx - (x - drag.x) / k(); goal.cy = view.cy = drag.cy + (y - drag.y) / k(); draw(); }
      } else {
        const c = hitCand(x, y);
        setHoverCand(c, x, y);
        const s = c ? null : hit(x, y), id = s ? s.id : null;
        cv.style.cursor = c || (id && id !== selected) ? 'pointer' : '';
        if (id !== hover) { hover = id; draw(); }
      }
    });
    cv.addEventListener('pointerup', (e) => {
      const [x, y] = pos(e);
      if (drag && !drag.moved) {
        const c = hitCand(x, y);
        if (c) pickCand(c);
        else { const s = hit(x, y); if (s && s.id !== selected) select(s.id, { scroll: true, zoom: true }); }
      }
      drag = null;
    });
    cv.addEventListener('pointercancel', () => { drag = null; });
    cv.addEventListener('pointerleave', () => { if (!drag) setHoverCand(null); });
    cv.addEventListener('wheel', (e) => {
      e.preventDefault();
      const [x, y] = pos(e);
      const wx = view.cx + (x - dims.w / 2) / k(), wy = view.cy - (y - dims.h / 2) / k();
      const span = clamp(view.span * Math.exp(e.deltaY * 0.0015), SPAN_MIN, 700);
      view.span = goal.span = span;
      goal.cx = view.cx = wx - (x - dims.w / 2) / k(); goal.cy = view.cy = wy + (y - dims.h / 2) / k();
      setHoverCand(null);
      draw();
    }, { passive: false });
    $('mapFit').onclick = () => fitAll(false);
    $('mapCands').onclick = zoomCands;
    $('mapPick').onclick = zoomPick;
    new ResizeObserver(() => { dims = fitCanvas(cv); draw(); }).observe(cv);
  }

  function bindCandBar() {
    const bar = $('candBar'), at = (e) => { const b = e.target.closest('.cand'), s = cur(); return b && s ? s.cands[Number(b.dataset.i)] : null; };
    bar.addEventListener('click', (e) => { const c = at(e); if (c) pickCand(c); });
    // çubukta gezinirken haritadaki nokta da işaretlensin
    bar.addEventListener('pointerover', (e) => { const c = at(e); if (c) { hoverCand = c; $('mapTip').hidden = true; draw(); } });
    bar.addEventListener('pointerleave', () => { hoverCand = null; draw(); });
  }

  function init(index, callbacks) {
    idx = index; cb = callbacks || {};
    cv = $('mapCanvas'); ctx = cv.getContext('2d');
    cv.setAttribute('aria-label', t('brief.mapAlt'));
    renderSortBar(); renderCards();
    // karta tıklayınca harita o bölgeye yaklaşır: ısı haritası ve adaylar görünür
    $('cards').addEventListener('click', (e) => { const c = e.target.closest('.card'); if (c) select(c.dataset.id, { zoom: true }); });
    $('btnLand').addEventListener('click', () => { if (pick && pick.landable && cb.onLand) cb.onLand(pick); });
    bindMap(); bindCandBar(); bindWeights();
    const bd = $('bDate');
    bd.min = Fmt.toInput(0); bd.max = Fmt.toInput(idx.hours - 1);
    bd.onchange = () => { const h = Fmt.fromInput(bd.value); if (h != null && cb.onDate) cb.onDate(clamp(h, 0, idx.hours - 1)); syncDate(); };
    syncDate();
    dims = fitCanvas(cv);
    fitAll(true);
    select(sorted()[0].id);
    new ResizeObserver(drawStrips).observe($('cards'));
    setTimeout(preloadStrips, 500);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
  }

  return { init, select, pickCand, zoomTo, fitAll, draw, syncDate, get selected() { return selected; }, get pick() { return pick; } };
})();
