// ===== hud: kokpit panelleri (güç, iletişim, özet, olay akışı, karşılaştırma, sade mod) =====
const HUD = (() => {
  let S, act, feedIdx = -2, feedBtns = [], feedSig = '', many = false;
  const UP = (s) => s.toLocaleUpperCase(LOCALE);

  function seg(el, items, cur, onPick, label) {
    el.setAttribute('aria-label', label);
    el.innerHTML = items.map(([v, text]) => `<button type="button" data-v="${v}" aria-pressed="${String(v) === String(cur)}">${esc(text)}</button>`).join('');
    el.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b && !b.disabled) onPick(b.dataset.v); });
  }
  function setSeg(el, cur) { el.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === String(cur)))); }
  const withUnit = (v, unit) => `${v}<small>${esc(unit)}</small>`;

  function init(state, actions) {
    S = state; act = actions;
    many = S.index.years.length > 1;
    seg($('viewSeg'), [['orbit', t('top.view.orbit')], ['astro', t('top.view.astro')], ['pano', t('top.view.pano')]], S.view, act.setView, t('top.viewLabel'));
    seg($('modeSeg'), [['terrain', t('top.mode.terrain')], ['flat', t('top.mode.flat')]], 'terrain', (v) => act.setFlat(v === 'flat'), t('top.modeLabel'));
    seg($('speedSeg'), [[1, t('time.speed.h')], [24, t('time.speed.d')], [168, t('time.speed.w')]], S.speed, (v) => act.setSpeed(Number(v)), t('time.speedLabel'));

    seg($('zoomSeg'), (many ? [['all', t('time.zoom.all')]] : []).concat([['year', t('time.zoom.year')], ['90', t('time.zoom.d90')], ['30', t('time.zoom.d30')]]), S.zoom, act.setZoom, t('time.zoomLabel'));
    const ys = $('yearSel');
    ys.innerHTML = S.index.years.map((y) => `<option value="${y}">${y}</option>`).join('');
    ys.setAttribute('aria-label', t('time.yearLabel'));
    ys.hidden = !many;
    ys.onchange = () => act.setYear(Number(ys.value));
    const hs = $('heightSel');
    hs.innerHTML = S.index.heights.map((h) => `<option value="${h}">${Fmt.num(h, 0)} m</option>`).join('');
    $('heightRow').hidden = S.index.heights.length < 2;
    hs.onchange = () => act.setHeight(Number(hs.value));
    const cd = $('cDate');
    cd.min = Fmt.toInput(0); cd.max = Fmt.toInput(S.index.hours - 1);
    cd.onchange = () => { const h = Fmt.fromInput(cd.value); if (h != null) act.seek(h); };
    const vv = S.index.validation, vm = vv && vv.sun_0m_map_res ? { sun: Fmt.num(vv.sun_0m_map_res.mean_abs, 1), earth: Fmt.num(vv.earth_0m_map_res.mean_abs, 1) } : null;
    if (vm) setText($('badgeText'), t('badge.validated', vm));
    $('btnBack').onclick = act.back;
    $('btnSimple').onclick = () => act.setSimple(!S.simple);
    $('btnPlay').onclick = () => act.setPlaying(!S.playing);
    $('btnNext').onclick = act.nextEvent;
    $('btnLanding').onclick = act.setLandingNow;
    $('lookSun').onclick = () => act.look('sun');
    $('lookEarth').onclick = () => act.look('earth');
    $('lookLander').onclick = () => act.look('lander');
    $('btnTour').onclick = act.tour;
    $('ansCap').onclick = act.applyMinCap;
    $('ansLand').onclick = act.goSafeLanding;
    $('ansCap').title = t('ans.capTitle');
    $('ansLand').title = t('ans.landTitle');
    $('btnData').onclick = () => $('dataDlg').showModal();
    $('dlgClose').onclick = () => $('dataDlg').close();
    $('slCap').addEventListener('input', (e) => act.setBatt('cap', Number(e.target.value)));
    $('slPanel').addEventListener('input', (e) => act.setBatt('panel', Number(e.target.value)));
    $('slLoad').addEventListener('input', (e) => act.setBatt('load', Number(e.target.value)));
    $('slUnc').addEventListener('input', (e) => act.setUnc(Number(e.target.value) / 100));
    $('slMask').addEventListener('input', (e) => act.setMask(Number(e.target.value)));
    $('feed').addEventListener('click', (e) => { const b = e.target.closest('.ev'); if (b) act.seek(Number(b.dataset.h)); });
    SkyPlot.legend($('skyLegend'));

    const li = (arr) => '<ul>' + arr.map((s) => `<li>${esc(s)}</li>`).join('') + '</ul>';
    const val = S.index.validation;
    const f1 = (o, k) => Fmt.num(o[k], 1);
    const status = val && val.sun_0m_map_res ? t('data.statusVal', { n: val.n, period: val.period,
      sunC: f1(val.sun_0m_map_res, 'mean_abs'), sunCMax: f1(val.sun_0m_map_res, 'max_abs'), earthC: f1(val.earth_0m_map_res, 'mean_abs'), earthCMax: f1(val.earth_0m_map_res, 'max_abs'),
      sun: f1(val.sun_0m, 'mean_abs'), sunMax: f1(val.sun_0m, 'max_abs'), earth: f1(val.earth_0m, 'mean_abs'), earthMax: f1(val.earth_0m, 'max_abs'),
      sun2: f1(val.sun_2m, 'mean_abs'), earth2: f1(val.earth_2m, 'mean_abs') }) : t('data.status');
    $('dlgBody').innerHTML = `<p class="status">${icon('warn')}<span>${esc(status)}</span></p>
      <h4>${esc(t('data.methodTitle'))}</h4>${li(t('data.method'))}
      <h4>${esc(t('data.candTitle'))}</h4>${li(t('data.cand'))}
      <h4>${esc(t('data.glossTitle'))}</h4>${li(t('data.gloss'))}
      <h4>${esc(t('data.limitsTitle'))}</h4>${li(t('data.limits'))}
      <h4>${esc(t('data.sourcesTitle'))}</h4>${li(t('data.sources'))}
      <h4>${esc(t('data.keysTitle'))}</h4><p>${esc(t('time.keys'))}</p>`;

    $('cmpBody').innerHTML = [['Sun', 'sun', 'compare.rowSun'], ['Earth', 'earth', 'compare.rowEarth'], ['Dark', 'dark', 'compare.rowDark']]
      .map(([k, ic, key]) => `<tr><td>${icon(ic, ic)}${esc(t(key))}</td><td class="flat" id="cmpF${k}"></td><td class="arrow">→</td><td id="cmpT${k}"></td><td class="diff" id="cmpD${k}"></td></tr>`).join('');
  }

  // bölge değişince
  function site() {
    const s = S.site;
    setText($('siteCode'), s.reg.code);
    setText($('siteName'), s.region);
    setText($('siteCoord'), Fmt.latlon(s.lat, s.lon) + ' · ' + Fmt.num(s.ground_height_m, 0) + ' m · ' + (s.legacy ? t('brief.sampleShort') : t('cand.short', { n: s.rank })));
    $('cAddCmp').disabled = !s.landable;
    feedSig = ''; feedIdx = -2;
  }

  function evHTML(e) {
    const day = e.hour >= S.landing ? t('events.day', { n: Math.floor((e.hour - S.landing) / 24) + 1 }) : Fmt.date(e.hour);
    const when = `<span class="when"><b>${esc(day)}</b><small>${esc(Fmt.date(e.hour, many) + ' ' + Fmt.time(e.hour))}</small></span>`;
    let ic, title, sub = '', tag = '';
    const dur = (key) => t(key, { d: Fmt.dur(e.durH) }) + (e.open ? ' · ' + t('events.openEnded') : '');
    if (e.k === 'sun_off') { ic = 'dark'; title = t(S.flat ? 'events.sunOffFlat' : 'events.sunOff'); sub = dur('events.durDark'); if (e.long) tag = `<span class="tag">${esc(t('events.longDark'))}</span>`; }
    else if (e.k === 'sun_on') { ic = 'sun'; title = t('events.sunOn'); sub = dur('events.durLight'); }
    else if (e.k === 'link_off') { ic = 'cut'; title = t('events.linkOff'); sub = dur('events.durNoLink'); }
    else if (e.k === 'link_on') { ic = 'earth'; title = t('events.linkOn'); sub = dur('events.durLink'); }
    else if (e.k === 'landing') { ic = 'next'; title = t('events.landing'); }
    else { ic = 'warn'; title = UP(t('events.dead')); }
    return `<li><button type="button" class="ev${e.long ? ' long' : ''}" data-k="${e.k}" data-h="${e.hour}" title="${esc(t('events.jump'))}">${when}${icon(ic)}<span class="tx">${esc(title)}${sub ? `<small>${esc(sub)}</small>` : ''}${tag}</span></button></li>`;
  }

  // Kokpitteki bütün özet rakamları tek dönemden gelir: seçili yılın canlı hesabı (S.D.stats).
  // 2026–2030 özetleri yalnız brifing ekranında gösterilir.
  function summaryValues() {
    const st = S.D.stats;
    return { sun: st.sunPct, energy: st.sunEnergyPct, earth: st.earthPct, both: st.bothPct, dark: st.longestDarkH / 24 };
  }
  // düz ufuk ↔ gerçek arazi kartı için: seçili yıl, ikisi de 0° maske
  let cmpKey = '', cmpVal = null;
  function flatVsTerrain() {
    const key = [S.data.id, S.height, S.year].join('|');
    if (key !== cmpKey) {
      const [a, b] = S.D.range;
      cmpVal = { flat: Sim.stats(Sim.buildModel(S.data, true, 0), a, b), terrain: Sim.stats(Sim.buildModel(S.data, false, 0), a, b) };
      cmpKey = key;
    }
    return cmpVal;
  }

  // model yeniden hesaplanınca (bölge, ufuk modeli, maske, batarya, iniş günü)
  function derived(animate) {
    const D = S.D, m = S.site.m, ms = animate ? 800 : 0;
    $('slCap').value = S.batt.cap; $('slPanel').value = S.batt.panel; $('slLoad').value = S.batt.load; $('slMask').value = S.mask;
    setText($('outCap'), Fmt.num(S.batt.cap, 0) + ' ' + t('unit.kwh'));
    setText($('outPanel'), Fmt.num(S.batt.panel, 1) + ' ' + t('unit.kw'));
    setText($('outLoad'), Fmt.num(S.batt.load, 2) + ' ' + t('unit.kw'));
    setText($('outMask'), Fmt.num(S.mask, 1) + '°');
    $('slUnc').value = Math.round(S.unc * 100);
    setText($('outUnc'), '±' + Fmt.pct(S.unc * 100, 0));

    // özet: seçili yılın canlı hesabı (tek dönem); düz ufuk modunda aynı yıl, düz ufukla
    const v = summaryValues();
    $('pSummary').dataset.flat = String(S.flat);
    setText($('sumTag'), S.year + ' · ' + t(S.flat ? 'summary.flat' : 'summary.terrain'));
    setText($('sumEarthL'), tp('summary.earthMask', { v: Fmt.num(S.mask, 1) }));
    Counter.run($('sumSun'), v.sun, (x) => Fmt.pct(x), ms);
    Counter.run($('sumEarth'), v.earth, (x) => Fmt.pct(x), ms);
    Counter.run($('sumBoth'), v.both, (x) => Fmt.pct(x), ms);
    Counter.run($('sumDark'), v.dark, (x) => withUnit(Fmt.num(x, 1), t('unit.day')), ms);
    setText($('sumEnergy'), t('summary.energy', { v: Fmt.pct(v.energy) }));
    $('heightSel').value = String(S.height);
    setText($('sumHeight'), t(S.index.heights.length > 1 ? 'summary.heightNote' : 'summary.heightFixed', { h: Fmt.num(S.height, 0) }));
    $('yearSel').value = String(S.year);
    setText($('eventsSub'), t('events.sub'));

    // iletişim: aynı yıl, seçili anten maskesiyle
    setText($('cmLiveEarthL'), t('comm.liveEarth', { y: S.year }));
    setText($('cmLiveGapL'), t('comm.liveGap', { y: S.year }));
    Counter.run($('cmLivePct'), D.stats.earthPct, (x) => Fmt.pct(x), animate ? 350 : 0);
    Counter.run($('cmLiveGap'), D.stats.longestGapH / 24, (x) => withUnit(Fmt.num(x, 1), t('unit.day')), animate ? 350 : 0);
    const crit = !S.flat && D.stats.lowMarginPct > 0;
    $('cmCrit').hidden = !crit;
    if (crit) $('cmCrit').innerHTML = icon('warn') + '<span>' + esc(t('comm.crit', { p: Fmt.pctLoc(D.stats.lowMarginPct) })) + '</span>';

    // batarya hükmü
    const b = D.batt, vd = $('pwVerdict');
    if (b.deadHour >= 0) { vd.dataset.s = 'dead'; setText(vd, t('power.verdictDead', { n: Fmt.num((b.deadHour - b.start) / 24, 1) })); }
    else { vd.dataset.s = 'ok'; setText(vd, t('power.verdictAlive', { end: dataEnd() }) + ' ' + t('power.verdictMin', { v: Fmt.num(b.minPct, 0) })); }

    // belirsizlik: tüketim ve panel gücü ±oran oynarsa yılı çıkarma olasılığı
    const rk = $('pwRisk');
    rk.hidden = !S.risk;
    if (S.risk) setText(rk, t('power.risk', { u: Fmt.pct(S.unc * 100, 0), n: Fmt.num(S.risk.n, 0), p: Fmt.pct(S.risk.pct, 0), cap: Fmt.num(S.risk.capQ, 0) }));

    // hızlı cevaplar: bu ayarlarla yılı çıkaran en küçük batarya ve güvenli iniş penceresi
    setText($('ansCapV'), D.minCap == null ? t('ans.capNone') : Fmt.num(D.minCap, 0) + ' ' + t('unit.kwh'));
    const sd = D.scan.safeDay;
    setText($('ansLandV'), sd < 0 ? '—' : sd === 0 ? t('ans.landAll') : t('ans.landFrom', { d: Fmt.date(sd * 24, many) }));
    $('ansCap').title = t('ans.capTitle', { end: dataEnd() });
    $('ansLand').title = t('ans.landTitle', { end: dataEnd() });

    // olay akışı
    const sig = D.feed.map((e) => e.k + e.hour + ':' + (e.durH || 0)).join(',') + S.flat + S.landing;
    if (sig !== feedSig) {
      feedSig = sig; feedIdx = -2;
      $('feed').innerHTML = D.feed.map(evHTML).join('');
      feedBtns = [...$('feed').querySelectorAll('.ev')];
    }

    compare(animate);
    simple();
  }

  function compare(animate) {
    const box = $('compare');
    const show = S.flat && !S.simple;
    const was = !box.hidden;
    box.hidden = !show;
    if (!show) return;
    const { flat: f, terrain: r } = flatVsTerrain();
    setText($('cmpSub'), t('compare.sub', { name: S.site.region, y: S.year }));
    const rows = [
      ['Sun', f.sunPct, r.sunPct, (x) => Fmt.pct(x), t('compare.points')],
      ['Earth', f.earthPct, r.earthPct, (x) => Fmt.pct(x), t('compare.points')],
      ['Dark', f.longestDarkH / 24, r.longestDarkH / 24, (x) => withUnit(Fmt.num(x, 1), t('unit.day')), t('unit.day')],
    ];
    for (const [k, fv, rv, fn, unit] of rows) {
      const fe = $('cmpF' + k);
      if (!was && animate) Counter.set(fe, rv); // gerçek arazi değerinden düz ufuk değerine aksın
      Counter.run(fe, fv, fn, animate ? 1100 : 0);
      $('cmpT' + k).innerHTML = fn(rv);
      const d = rv - fv;
      setText($('cmpD' + k), (d > 0 ? '+' : d < 0 ? '−' : '') + Fmt.num(Math.abs(d), 1) + ' ' + unit);
    }
    const dSun = r.sunPct - f.sunPct;
    setText($('cmpNote'), t(dSun >= 0 ? 'compare.noteMore' : 'compare.noteLess', { v: Fmt.num(Math.abs(dSun), 1) }));
    setText($('cmpNote2'), t('compare.sceneNote'));
  }

  function simple() {
    const box = $('simple');
    box.hidden = !S.simple;
    if (!S.simple) return;
    const v = summaryValues();
    $('simTag').hidden = !S.flat;
    setText($('simTag'), t('simple.flatTag'));
    Counter.run($('simSun'), v.sun, (x) => Fmt.pct0(x), 700);
    Counter.run($('simEarth'), v.earth, (x) => Fmt.pct0(x), 700);
    Counter.run($('simDark'), v.dark, (x) => withUnit(String(Math.round(x)), t('unit.day')), 700);
    setText($('simSentence'), t('simple.sentence', { sun: Fmt.pctLoc(v.sun), earth: Fmt.pctLoc(v.earth), dark: Math.round(v.dark) }));
  }

  const remain = (run, tH) => (run.open ? t('power.untilYearEnd') : Fmt.dur(Math.max(0, run.start + run.len - tH)));
  // Olay akışı 6 saatten kısa durumları birleştirir; Güneş ufku sıyırırken anlık durum (ör. "ışıkta") birleştirilmiş
  // durumla ("karanlık") çelişebilir. O zaman etiket anlık duruma göre yazılır, kalan süre saatlik seriden sayılır.
  function remainNow(run, flags, on, tH) {
    if (run.on === on) return remain(run, tH);
    const i0 = clamp(Math.floor(tH), 0, flags.length - 1);
    for (let i = i0 + 1; i < flags.length; i++) if (!!flags[i] !== on) return Fmt.dur(Math.max(0, i - tH));
    return t('power.untilYearEnd');
  }
  const dataEnd = () => Fmt.date(S.index.hours - 1, true);
  const aboveBelow = (v) => t(v >= 0 ? 'geo.above' : 'geo.below', { v: Fmt.num(Math.abs(v), 2) });

  // her karede
  function tick() {
    const D = S.D, now = S.now, tH = S.t, mg0 = now.margin;
    setText($('clockDate'), Fmt.date(tH, true) + ' · ' + Fmt.time(tH) + ' ' + t('top.utc'));
    const cd = $('cDate');
    if (document.activeElement !== cd) { const v = Fmt.toInput(tH); if (cd.value !== v) cd.value = v; }
    setText($('clockDay'), tH >= S.landing
      ? t('top.missionDay', { n: Math.floor((tH - S.landing) / 24) + 1 })
      : t('top.preLanding', { n: Math.ceil((S.landing - tH) / 24) }));

    // güç
    const b = D.batt, pw = $('pPower'), chip = $('pwState');
    const sunRun = Sim.runAt(D.sunRuns, tH), lit = now.sunFrac > 0;
    let state = 'ok';
    if (tH < b.start) {
      state = 'wait';
      setText($('pwBatt'), '—'); setText($('pwKwh'), t('power.startFull'));
      $('pwMeter').firstElementChild.style.width = '0%';
      chip.dataset.s = 'off'; setText(chip, t('power.waiting'));
    } else {
      const i = Math.min(Math.floor(tH), D.model.n - 1), f = tH - i;
      const lvl = lerp(b.level[i], b.level[Math.min(i + 1, D.model.n)], f);
      const dead = b.deadHour >= 0 && tH >= b.deadHour;
      const pct = dead ? 0 : (lvl / S.batt.cap) * 100;
      state = dead ? 'dead' : pct < 20 ? 'low' : 'ok';
      setText($('pwBatt'), Fmt.pct0(pct));
      setText($('pwKwh'), dead ? t('power.deadSince', { date: Fmt.date(b.deadHour, many) }) : Fmt.num(lvl, 1) + ' / ' + Fmt.num(S.batt.cap, 0) + ' ' + t('unit.kwh'));
      $('pwMeter').firstElementChild.style.width = pct.toFixed(1) + '%';
      if (dead) { chip.dataset.s = 'warn'; setText(chip, t('power.dead')); }
      else { chip.dataset.s = lit ? 'ok' : 'off'; setText(chip, t(lit ? 'power.lit' : 'power.dark')); }
    }
    if (pw.dataset.state !== state) pw.dataset.state = state;
    setText($('pwIn'), Fmt.num(S.batt.panel * now.sunFrac, 2) + ' ' + t('unit.kw'));
    setText($('pwDisc'), t('power.sunDisc', { v: Fmt.pct0(now.sunFrac * 100) }));
    // sayısal okuma: ham yükseklik ve azimut + arazi ufkuna göre pay
    setText($('pwGeo'), t('geo.sun', { alt: Fmt.deg(now.sunAlt, 2), az: Fmt.az(now.sunAz), rel: aboveBelow(now.sunMargin), h: t(S.flat ? 'geo.flatH' : 'geo.terrainH') }));
    setText($('cmGeo'), t('geo.earth', { alt: Fmt.deg(now.earthAlt, 2), az: Fmt.az(now.earthAz), rel: aboveBelow(mg0), h: t(S.flat ? 'geo.flatH' : 'geo.terrainH') }));
    setText($('pwCountL'), t(lit ? 'power.toDark' : 'power.toLight'));
    setText($('pwCount'), remainNow(sunRun, D.model.sunUp, lit, tH));

    // iletişim: pay 1°'nin altında sarı, 0'ın altında kırmızı
    const cm = $('pComm'), cchip = $('cmState'), mg = now.margin, linkRun = Sim.runAt(D.linkRuns, tH);
    const cs = now.linkUp ? (mg < 1 ? 'low' : 'ok') : mg > 0 ? 'mask' : 'blocked';
    if (cm.dataset.state !== cs) cm.dataset.state = cs;
    setText($('cmMargin'), Fmt.deg(mg, 2));
    setText($('cmWhy'), tp({ ok: 'comm.stateOk', low: 'comm.stateLow', mask: 'comm.stateMask', blocked: S.flat ? 'comm.stateBelow' : 'comm.stateBlocked' }[cs]));
    cchip.dataset.s = cs === 'ok' ? 'ok' : cs === 'blocked' ? 'warn' : 'caution';
    setText(cchip, t(now.linkUp ? 'comm.linkUp' : 'comm.linkDown'));
    setText($('cmCountL'), t(now.linkUp ? 'comm.toLoss' : 'comm.toLink'));
    setText($('cmCount'), remainNow(linkRun, D.model.linkUp, now.linkUp, tH));

    // olay akışında şimdiki yer
    let idx = -1;
    for (let i = 0; i < D.feed.length; i++) { if (D.feed[i].hour <= tH) idx = i; else break; }
    if (idx !== feedIdx) {
      feedIdx = idx;
      feedBtns.forEach((el, i) => { el.classList.toggle('future', i > idx); el.classList.toggle('current', i === idx); });
      const cur = feedBtns[Math.max(0, idx)], feed = $('feed');
      if (cur) feed.scrollTop = Math.max(0, cur.parentElement.offsetTop - feed.offsetTop - feed.clientHeight * 0.3);
    }

    if (S.simple) {
      setText($('simNow'), t('simple.now') + ': ' + t(lit ? 'simple.nowLit' : 'simple.nowDark') + ' · ' + t(now.linkUp ? 'simple.nowLink' : 'simple.nowNoLink'));
    }
  }

  function controls() {
    setSeg($('viewSeg'), S.view); setSeg($('modeSeg'), S.flat ? 'flat' : 'terrain'); setSeg($('speedSeg'), S.speed);
    $('btnSimple').setAttribute('aria-pressed', String(S.simple));
    $('playUse').setAttribute('href', S.playing ? '#i-pause' : '#i-play');
    $('btnPlay').setAttribute('aria-label', t(S.playing ? 'time.pause' : 'time.play'));
    $('cockpit').dataset.view = S.view; $('cockpit').dataset.flat = String(S.flat); $('cockpit').dataset.simple = String(S.simple);
    setText($('viewHint'), t({ orbit: 'scene.hintOrbit', astro: 'scene.hintAstro', pano: 'scene.hintPano' }[S.view]));
    $('viewSeg').querySelectorAll('button').forEach((b) => { b.disabled = !S.has3d && b.dataset.v !== 'pano'; });
    setSeg($('zoomSeg'), S.zoom);
    $('yearSel').value = String(S.year); $('heightSel').value = String(S.height);
  }

  // sade moda girip çıkarken kokpitteki sabit etiketleri (data-t) yeniden yaz
  function relabel() {
    $('cockpit').querySelectorAll('[data-t]').forEach((el) => { el.textContent = tp(el.dataset.t); });
    SkyPlot.legend($('skyLegend'));
  }

  function message(text) { const el = $('viewMsg'); el.hidden = !text; if (text) setText(el, text); }

  return { init, site, derived, tick, controls, message, relabel, flatVsTerrain };
})();
