// ===== present: sunum modu — tek tuşla ilerleyen rehberli tur (açılış ekranındaki kürenin üstünde) =====
// Her sahnede büyük bir başlık, tek cümle ve gerekiyorsa iki-üç büyük rakam. Rakamlar veriden gelir:
// 2026–2030 özetleri sites.json / candidates.json'dan, "görev kayarsa" sahnesi tarayıcıda canlı hesaplanır
// (karşılaştırma ekranıyla aynı hesap: Sim.windowStats, ilk 30 gün, 1° anten payı).
// Tuşlar: → / Boşluk / PageDown ilerle, ← / PageUp geri, Esc çık.
const Present = (() => {
  let idx, S, cb = {}, i = 0, active = false, token = 0, wasPaused = false;
  const SLIP_SITE = 'malapert_massif', PLAN = '2027-03-01T00:00', SLIP_DAYS = 14, WIN_DAYS = 30, MASK = 1;

  const byId = (id) => idx.sites.find((s) => s.id === id);
  const kmBetween = (a, b) => Math.hypot(a.ps_km[0] - b.ps_km[0], a.ps_km[1] - b.ps_km[1]);
  const fig = (v, label, cls = '') => `<div class="pr-fig ${cls}"><b>${v}</b><span>${esc(label)}</span></div>`;
  const sign = (v, d = 1) => (v > 0 ? '+' : v < 0 ? '−' : '±') + Fmt.num(Math.abs(v), d);

  // ---------- sahneler ----------
  const scenes = [
    { key: 'pole', enter() {
      Home.setHot([]);
      Globe.setSpin(true);
      return Globe.flyTo({ az: 168, el: -24, dist: 3.9, tx: 0, ty: -0.25, tz: 0, fov: 30 }, 2600);
    } },
    { key: 'regions', enter() {
      Globe.setSpin(false);
      Home.setHot(idx.sites.map((s) => s.id));
      return Globe.flyTo(Globe.POLE, 2600);
    } },
    { key: 'contrast', enter() {
      Globe.setSpin(false);
      const list = idx.sites.slice().sort((a, b) => Home.pointOf(b).m.terrain.sun_any_pct - Home.pointOf(a).m.terrain.sun_any_pct);
      const best = list[0], worst = list[list.length - 1], pb = Home.pointOf(best), pw = Home.pointOf(worst);
      Home.setHot([best.id, worst.id]);
      setLine('contrast', { best: best.region, worst: worst.region, km: Fmt.num(kmBetween(pb, pw), 0) });
      setFigs(fig(Fmt.pct(pb.m.terrain.sun_any_pct), best.region, 'sun') + fig(Fmt.pct(pw.m.terrain.sun_any_pct), worst.region, 'dim'),
        t('present.periodSun', { period: periodLabel(idx.period) }));
      return Globe.flyTo(Globe.POLE, 1800);
    } },
    { key: 'flat', enter() {
      Globe.setSpin(false);
      const s = byId(SLIP_SITE) || idx.sites[0], m = s.m;
      Home.setHot([s.id]);
      setLine('flat', { name: s.region });
      setFigs(
        `<div class="pr-vs"><div><small>${esc(t('present.flatCol'))}</small>${fig(Fmt.pct(m.flat_horizon.sun_any_pct), t('home.m.sun'), 'dim')}${fig(Fmt.num(m.flat_horizon.longest_dark_days, 1), t('present.darkDays'), 'dim')}</div>`
        + `<div class="pr-arrow">→</div><div><small>${esc(t('present.terrainCol'))}</small>${fig(Fmt.pct(m.terrain.sun_any_pct), t('home.m.sun'), 'sun')}${fig(Fmt.num(m.terrain.longest_dark_days, 1), t('present.darkDays'), 'dark')}</div></div>`,
        t('present.periodSample', { period: periodLabel(idx.period) }));
      return Globe.flyTo(Globe.poseAbove(s, 1.22, 7), 2400);
    } },
    { key: 'height', enter() {
      Globe.setSpin(false);
      const s = byId(SLIP_SITE) || idx.sites[0], a = s.metrics['2m'], b = s.metrics['10m'];
      Home.setHot([s.id]);
      if (!b) { setLine('heightNone', {}); setFigs(''); return Promise.resolve(); }
      setLine('height', { name: s.region, d: sign(b.terrain.sun_any_pct - a.terrain.sun_any_pct) });
      setFigs(`<div class="pr-vs">${fig(Fmt.pct(a.terrain.sun_any_pct), t('present.h2'), 'dim')}<div class="pr-arrow">→</div>${fig(Fmt.pct(b.terrain.sun_any_pct), t('present.h10'), 'sun')}</div>`,
        t('present.periodSample', { period: periodLabel(idx.period) }));
      return Globe.flyTo(Globe.poseAbove(s, 1.1, 4), 1800);
    } },
    { key: 'slip', enter: slipScene },
    { key: 'valid', enter() {
      Globe.setSpin(true);
      Home.setHot([]);
      // doğrulama özeti years.json'dan: bu veri setinde sun_0m / earth_0m (eski sette *_0m_map_res)
      const val = idx.validation || {}, v = val.sun_0m || val.sun_0m_map_res, ve = val.earth_0m || val.earth_0m_map_res;
      if (v && ve) setLine('valid', { n: val.n, sun: Fmt.num(v.mean_abs, 1), earth: Fmt.num(ve.mean_abs, 1) });
      else setLine('validNone', {});
      setFigs(v && ve ? fig(Fmt.num(v.mean_abs, 1), t('present.validSun'), 'sun') + fig(Fmt.num(ve.mean_abs, 1), t('present.validEarth'), 'earth') : '',
        v && ve ? t('present.validNote', { period: val.period }) : '');
      return Globe.flyTo(Globe.OVERVIEW, 2600);
    } },
    { key: 'try', enter() {
      Globe.setSpin(false);
      Home.setHot(idx.sites.map((s) => s.id));
      return Globe.flyTo(Globe.POLE, 2200);
    } },
  ];

  // "Görev 2 hafta kayarsa?": A = örnek nokta, plan tarihi; B = aynı nokta +14 gün; C = bölgenin 1. adayı, +14 gün
  async function slipScene() {
    Globe.setSpin(false);
    const s = byId(SLIP_SITE) || idx.sites[0], c1 = Home.pointOf(s);
    Home.setHot([s.id]);
    const h0 = Fmt.fromInput(PLAN), h1 = h0 + SLIP_DAYS * 24, my = token;
    setLine('slipWait', { name: s.region });
    setFigs(`<p class="pr-wait">${esc(t('present.computing'))}</p>`);
    const fly = Globe.flyTo(Globe.poseAbove(s, 1.16, 5), 2000);
    try {
      const [a, c] = await Promise.all([cb.core(s.id), c1 === s ? null : cb.core(c1.id)]);
      if (my !== token) return;
      const A = Sim.windowStats(a, h0, WIN_DAYS * 24, MASK), B = Sim.windowStats(a, h1, WIN_DAYS * 24, MASK);
      const C = c ? Sim.windowStats(c, h1, WIN_DAYS * 24, MASK) : null;
      const km = c ? kmBetween(s, c1) : 0;
      setLine(C ? 'slip' : 'slipNoCand', { name: s.region, dB: sign(B.bothPct - A.bothPct), dC: C ? sign(C.bothPct - A.bothPct) : '', km: Fmt.num(km, 1),
        d0: Fmt.date(h0, true), d1: Fmt.date(h1) });
      const col = (st, title, sub, cls) => `<div class="pr-col ${cls}"><small>${esc(title)}</small><em>${esc(sub)}</em>${fig(Fmt.pct(st.bothPct), t('present.both'), 'both')}${fig(Fmt.num(st.longestDarkH / 24, 1), t('present.darkDays'), 'dark')}</div>`;
      setFigs(`<div class="pr-cols">${col(A, 'A · ' + t('present.plan'), t('cand.legacy') + ' · ' + Fmt.date(h0), 'dim')}${col(B, 'B · ' + t('present.slipped'), t('cand.legacy') + ' · ' + Fmt.date(h1), 'dim')}`
        + (C ? col(C, 'C · ' + t('present.moved'), nameOf(c1) + ' · ' + Fmt.date(h1), 'win') : '') + '</div>',
      t('present.periodSlip', { n: WIN_DAYS, mask: Fmt.num(MASK, 0) }));
    } catch (e) {
      console.warn('sunum: hesap yapılamadı', e);
      if (my === token) { setLine('slipError', { name: s.region }); setFigs(''); }
    }
    return fly;
  }
  const nameOf = (c) => (c.legacy ? t('cand.legacy') : t('cand.title', { n: c.rank }));

  // ---------- görünüm ----------
  function setLine(key, vars) { setText($('prLine'), t('present.s.' + key + '.line', vars)); }
  function setFigs(html, note) { $('prFigs').innerHTML = html || ''; setText($('prNote'), note || ''); }

  function show(n) {
    i = clamp(n, 0, scenes.length - 1);
    token++;
    const sc = scenes[i], box = $('present');
    box.dataset.scene = sc.key;
    box.classList.remove('in'); void box.offsetWidth; box.classList.add('in');
    setText($('prKick'), t('present.kicker', { i: i + 1, n: scenes.length }));
    setText($('prTitle'), t('present.s.' + sc.key + '.title'));
    setLine(sc.key, {});
    setFigs('');
    $('prDots').querySelectorAll('li').forEach((li, k) => li.classList.toggle('on', k === i));
    $('prPrev').disabled = i === 0;
    setText($('prNextL'), t(i === scenes.length - 1 ? 'present.finish' : 'present.next'));
    sc.enter();
  }

  function start() {
    if (active || Home.approaching) return;
    active = true;
    wasPaused = Globe.paused;
    $('present').hidden = false;
    $('home').dataset.present = 'on';
    if (innerWidth > 900) Globe.setShift(0.2);
    $('prDots').innerHTML = scenes.map(() => '<li></li>').join('');
    show(0);
  }
  function stop(silent) {
    if (!active) return;
    active = false; token++;
    $('present').hidden = true;
    $('home').dataset.present = 'off';
    Globe.setShift(0);
    Globe.setSpin(!wasPaused);
    Home.setHot([]);
    if (!silent) Globe.flyTo(Globe.POLE, 1800);
  }
  const next = () => (i >= scenes.length - 1 ? stop() : show(i + 1));
  const prev = () => show(i - 1);

  function init(index, state, callbacks) {
    idx = index; S = state; cb = callbacks || {};
    $('prNext').onclick = next; $('prPrev').onclick = prev; $('prExit').onclick = () => stop();
    document.addEventListener('keydown', (e) => {
      if (!active || S.scene !== 'home' || $('videoDlg').open) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') { e.preventDefault(); next(); }
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') { e.preventDefault(); prev(); }
      else if (e.key === 'Escape') { e.preventDefault(); stop(); }
    });
  }

  return { init, start, stop, get active() { return active; } };
})();
