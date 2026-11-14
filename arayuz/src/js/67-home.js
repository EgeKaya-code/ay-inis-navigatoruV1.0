// ===== home: açılış ekranının arayüzü (küre üstündeki işaretler, ipucu, bölge listesi, tarih, yaklaşma göstergesi) =====
// Ekranda yalnız Ay ve dokuz bölge durur; işlevler küçük ve kenarlarda: araç çubuğu (sağ üst), tarih ve ışık (sol alt),
// bölge listesi (sağ alt, kapalı başlar). Ayrıntılı tablo ve harita "Liste" ekranında (eski brifing) kalır.
const Home = (() => {
  let idx, S, cb = {};
  let marks = [], hover = null, cluster = false, hot = new Set(), lastUser = 0, approaching = null;
  const SYN_H = 29.530588853 * 24;

  // her bölgede inilecek nokta: 1. aday (iniş paketi varsa), yoksa örnek nokta (brifing kartlarıyla aynı nokta)
  const pointOf = (s) => (s.top && s.top.landable ? s.top : s);
  const nameOf = (c) => (c.legacy ? t('cand.legacy') : t('cand.title', { n: c.rank }));

  function trio(c, cls = '') {
    const m = c.m;
    return `<span class="h-trio${cls}">
      <span class="sun">${icon('sun', 'sun')}<b>${Fmt.pct(m.terrain.sun_any_pct)}</b><small>${esc(t('home.m.sun'))}</small></span>
      <span class="earth">${icon('earth', 'earth')}<b>${Fmt.pct(m.terrain_antenna_1deg.earth_pct)}</b><small>${esc(t('home.m.earth'))}</small></span>
      <span class="dark">${icon('dark', 'dark')}<b>${Fmt.num(m.terrain.longest_dark_days, 1)}</b><small>${esc(t('home.m.dark'))}</small></span>
    </span>`;
  }

  function buildMarks() {
    const box = $('gMarks');
    box.innerHTML = '';
    marks = idx.sites.map((s) => {
      const p = pointOf(s), el = document.createElement('button');
      el.type = 'button'; el.className = 'gm'; el.dataset.id = s.id;
      el.setAttribute('aria-label', t('home.landOn', { name: s.region }));
      el.innerHTML = `<i></i><span class="gm-code">${esc(s.reg ? s.reg.code : '')}</span><span class="gm-name">${esc(s.region)}</span>`;
      el.addEventListener('pointerenter', () => setHover(s));
      el.addEventListener('pointerleave', () => setHover(null));
      el.addEventListener('focus', () => setHover(s));
      el.addEventListener('blur', () => setHover(null));
      el.addEventListener('click', () => land(s));
      box.appendChild(el);
      return { s, p, el, x: 0, y: 0, front: false };
    });
  }

  function buildList() {
    const list = idx.sites.slice().sort((a, b) => pointOf(b).m.terrain.sun_any_pct - pointOf(a).m.terrain.sun_any_pct);
    $('hRegList').innerHTML = `<li class="h-reg-head">${esc(t('home.listHead', { period: periodLabel(idx.period) }))}</li>` + list.map((s) => `<li><button type="button" class="h-reg" data-id="${s.id}">
        <span class="h-reg-code">${esc(s.reg ? s.reg.code : '')}</span><span class="h-reg-name">${esc(s.region)}</span>${trio(pointOf(s), ' mini')}</button></li>`).join('');
    const ol = $('hRegList');
    ol.onclick = (e) => { const b = e.target.closest('.h-reg'); if (b) land(idx.sites.find((x) => x.id === b.dataset.id)); };
    ol.onpointerover = (e) => { const b = e.target.closest('.h-reg'); setHover(b ? idx.sites.find((x) => x.id === b.dataset.id) : null, true); };
    ol.onpointerleave = () => setHover(null);
    const tg = $('hRegToggle');
    tg.onclick = () => { const open = tg.getAttribute('aria-expanded') !== 'true'; tg.setAttribute('aria-expanded', String(open)); ol.hidden = !open; };
  }

  function setHover(s, fromList) {
    hover = s;
    marks.forEach((m) => m.el.classList.toggle('on', m.s === s));
    const tip = $('hTip');
    if (!s || approaching) { tip.hidden = true; return; }
    const p = pointOf(s);
    tip.innerHTML = `<strong><span class="code">${esc(s.reg ? s.reg.code : '')}</span>${esc(s.region)}</strong>
      <small>${esc(nameOf(p))} · ${esc(Fmt.latlon(p.lat, p.lon))}</small>
      ${trio(p)}
      <small class="period">${esc(t('home.tipPeriod', { period: periodLabel(idx.period) }))}</small>
      <em>${esc(t(fromList ? 'home.tipClickList' : 'home.tipClick'))}</em>`;
    tip.hidden = false;
    tip.dataset.list = fromList ? 'true' : 'false';
    placeTip();
  }
  function placeTip() {
    const tip = $('hTip');
    if (tip.hidden || !hover) return;
    const m = marks.find((x) => x.s === hover), box = $('home').getBoundingClientRect();
    if (tip.dataset.list === 'true' || !m || !m.front || cluster) {
      tip.style.transform = `translate(${Math.max(16, box.width - tip.offsetWidth - 300)}px, ${Math.max(70, box.height - tip.offsetHeight - 90)}px)`;
      return;
    }
    let x = m.x + 18, y = m.y - tip.offsetHeight / 2;
    if (x + tip.offsetWidth > box.width - 16) x = m.x - 18 - tip.offsetWidth;
    y = clamp(y, 64, box.height - tip.offsetHeight - 70);
    tip.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
  }

  // ---------- iniş ----------
  async function land(s) {
    if (!s || approaching || Globe.flying) return;
    const p = pointOf(s);
    if (!p.landable) return;
    approaching = s;
    setHover(null);
    Present.stop(true);
    const home = $('home');
    home.dataset.mode = 'approach';
    setText($('haName'), s.region);
    setText($('haPoint'), nameOf(p) + ' · ' + Fmt.latlon(p.lat, p.lon));
    $('hApproach').hidden = false;
    cb.preload && cb.preload(p);
    const done = await Globe.approach(p);
    if (!done) { home.dataset.mode = ''; $('hApproach').hidden = true; approaching = null; return; }
    home.dataset.mode = 'fade';
    await new Promise((r) => setTimeout(r, 520));
    try { await cb.onLand(p); } finally {
      $('hApproach').hidden = true;
      approaching = null;
    }
  }
  function cancel() { if (approaching && Globe.flying) Globe.cancel(); }

  // kokpitten açılış ekranına dönüş: siyahtan açılır, kamera geri çıkar
  function returnTo() {
    const home = $('home');
    home.dataset.mode = 'fade';
    requestAnimationFrame(() => requestAnimationFrame(() => { home.dataset.mode = ''; }));
    syncDate();
    if (Globe.landedFrom) Globe.depart();
  }

  // ---------- tarih ve ışık ----------
  function syncDate() {
    setText($('hDateV'), Fmt.date(S.landing, true) + ' · ' + Fmt.time(S.landing) + ' ' + t('top.utc'));
    const el = $('hDate');
    if (document.activeElement !== el) el.value = Fmt.toInput(S.landing);
    Globe.setLightHour(S.landing);
  }
  function bindDate() {
    const el = $('hDate');
    el.min = Fmt.toInput(0); el.max = Fmt.toInput(idx.hours - 1);
    $('hDateBtn').onclick = () => { const f = $('hDateField'); f.hidden = !f.hidden; if (!f.hidden) el.focus(); };
    el.onchange = () => {
      const h = Fmt.fromInput(el.value);
      if (h == null) return;
      cb.onDate(clamp(h, 0, idx.hours - 1));
      syncDate();
    };
    const sp = $('hSpin');
    sp.onclick = () => {
      const on = Globe.paused;
      Globe.setSpin(on);
      sp.setAttribute('aria-pressed', String(on));
      sp.querySelector('use').setAttribute('href', on ? '#i-pause' : '#i-play');
      sp.setAttribute('aria-label', t(on ? 'home.spinPause' : 'home.spinPlay'));
    };
    sp.setAttribute('aria-label', t('home.spinPause'));
  }
  // ışık, inişten sonraki Ay gününde döner (ekranda o günün tarihi)
  function onLight(h) {
    if (h > S.landing + SYN_H) Globe.setLightHour(S.landing + ((h - S.landing) % SYN_H));
    setText($('hLightV'), Fmt.date(Globe.lightH, true));
  }

  // ---------- her kare ----------
  function edge(el, p, pad) {
    const box = $('home').getBoundingClientRect(), cx = box.width / 2, cy = box.height / 2;
    let dx = p.x - cx, dy = p.y - cy;
    const sx = (cx - pad) / Math.max(1e-6, Math.abs(dx)), sy = (cy - pad - 40) / Math.max(1e-6, Math.abs(dy)), k = Math.min(1, sx, sy);
    const x = clamp(cx + dx * k, pad, box.width - pad), y = clamp(cy + dy * k, 78, box.height - 110);
    el.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
    el.querySelector('i').style.transform = `rotate(${Math.atan2(dy, dx)}rad)`;
  }

  function update() {
    if (!Globe.ok) return;
    let minD = Infinity, spread = 0;
    const front = [], pole = Globe.projectPole();
    for (const m of marks) {
      const q = Globe.projectSite(m.p);
      m.x = q.x; m.y = q.y; m.front = q.front;
      if (q.front) { front.push(m); spread = Math.max(spread, Math.hypot(q.x - pole.x, q.y - pole.y)); }
    }
    for (let i = 0; i < front.length; i++) for (let j = i + 1; j < front.length; j++) minD = Math.min(minD, Math.hypot(front[i].x - front[j].x, front[i].y - front[j].y));
    // uzaktan dokuz nokta üst üste biner: tek bir "yaklaş" halkası; yakındayken tek tek tıklanır
    const wantCluster = front.length > 1 && spread < 95;
    if (wantCluster !== cluster) { cluster = wantCluster; $('home').dataset.cluster = String(cluster); }
    const showNames = !cluster && minD > 120 && Globe.dist < 1.9;
    for (const m of marks) {
      m.el.hidden = !m.front;
      if (m.front) m.el.style.transform = `translate(${m.x.toFixed(1)}px, ${m.y.toFixed(1)}px)`;
      m.el.classList.toggle('hot', hot.has(m.s.id));
      m.el.classList.toggle('named', showNames || hot.has(m.s.id));
      m.el.tabIndex = cluster ? -1 : 0;
    }
    const cl = $('gCluster');
    cl.hidden = !(cluster && pole.front) || !!approaching;
    if (!cl.hidden) cl.style.transform = `translate(${pole.x.toFixed(1)}px, ${pole.y.toFixed(1)}px)`;
    edge($('gSun'), Globe.sunScreen(), 34);
    edge($('gEarth'), Globe.earthScreen(), 34);
    placeTip();
    if (approaching) {
      const alt = Globe.altitudeKm();
      setText($('haAlt'), alt >= 1000 ? Fmt.num(alt / 1000, 1) + ' ' + t('home.thousandKm') : Fmt.num(alt, 0) + ' ' + t('unit.km'));
    }
  }

  function setHot(ids) { hot = new Set(ids || []); }

  function onUser() {
    const now = performance.now();
    if (now - lastUser < 400) return;
    lastUser = now;
    if (!$('hHint').classList.contains('gone')) { $('hHint').classList.add('gone'); Store.set('homeHint', true); }
  }

  function init(index, state, callbacks) {
    idx = index; S = state; cb = callbacks || {};
    const ok = Globe.init($('globe'), idx, { onUser, onLight });
    $('home').dataset.gl = String(ok);
    if (!ok) { setText($('hNoGl'), t('home.noGl')); $('hNoGl').hidden = false; }
    buildMarks(); buildList(); bindDate();
    $('gCluster').onclick = () => { onUser(); Globe.flyTo(Globe.POLE, 2200); };
    setText($('gClusterL'), t('home.cluster', { n: idx.sites.length }));
    $('hPresent').onclick = () => Present.start();
    $('hList').onclick = () => cb.openList();
    $('hVideo').onclick = () => { Present.stop(true); $('btnVideo').click(); }; // tanıtım videosu (Blender)
    $('hInfo').onclick = () => $('dataDlg').showModal();
    $('hOverview').onclick = () => Globe.flyTo(Globe.OVERVIEW, 1800);
    $('hPole').onclick = () => Globe.flyTo(Globe.POLE, 2000);
    $('haCancel').onclick = cancel;
    if (Store.get('homeHint', false)) $('hHint').classList.add('gone');
    const langs = Object.keys(STRINGS), ls = $('hLang');
    if (langs.length > 1) {
      ls.hidden = false;
      ls.innerHTML = langs.map((l) => `<option value="${l}"${l === LANG ? ' selected' : ''}>${esc(l.toUpperCase())}</option>`).join('');
      ls.setAttribute('aria-label', t('langLabel'));
      ls.onchange = () => { Store.set('lang', ls.value); location.reload(); };
    }
    document.addEventListener('keydown', (e) => {
      if (S.scene !== 'home' || $('dataDlg').open || $('videoDlg').open || e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
      if (e.key === 'Escape') { if (approaching) cancel(); }
      else if ((e.key === 'p' || e.key === 'P') && !Present.active && !approaching) Present.start();
    });
    syncDate();
  }

  return { init, update, land, cancel, returnTo, syncDate, setHot, pointOf, get approaching() { return approaching; } };
})();
