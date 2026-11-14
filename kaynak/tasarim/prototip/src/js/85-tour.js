// ===== tour: otomatik tur (kendi kendine oynayan demo; altyazılar veriden doldurulur) =====
const Tour = (() => {
  let active = false, timer = 0, later = 0, idx = 0, steps = [], S = null, act = null, saved = null;

  function build() {
    // altyazıdaki rakamlar kokpitle aynı dönemden: seçili yılın canlı hesabı (düz ufuk kartıyla aynı değerler)
    const D = S.D, feed = D.feed, fv = HUD.flatVsTerrain();
    // tur, iniş anından sonraki bir yıl içinde gezer
    const L = S.landing, end = Math.min(S.data.series.n - 7, L + 8760);
    const rise = feed.find((e) => e.k === 'sun_on' && e.hour > L + 60) || { hour: Math.min(L + 240, end) };
    const longDark = D.sunRuns.filter((r) => !r.on && r.start >= L && r.start < end).reduce((a, b) => (b.len > a.len ? b : a), { start: L, len: 0 });
    // kanıt anı: gerçek arazide Güneş tam görünürken düz ufuk hesabının "battı" dediği bir saat
    const se = S.data.series;
    let proof = -1;
    for (let i = L + 240; i < end && proof < 0; i++) if (se.sunFrac[i] > 0.95 && se.sunAlt[i] < -0.45 && se.sunFrac[i + 6] > 0.95 && se.sunAlt[i + 6] < -0.45) proof = i + 3;
    const cam = Scene.cam || { az: 0 };
    const view = (v) => { if (S.has3d) act.setView(v); };
    const play = (speed) => { act.setSpeed(speed); act.setPlaying(true); };
    return [
      { dur: 7, cap: t('tour.s1', { name: S.site.region }), run() {
        act.setFlat(false); view('orbit'); act.seek(rise.hour + 30); play(24);
        Scene.tween({ az: cam.az + 0.9, pol: 0.95, dist: 9000 }, 6.5);
      } },
      { dur: 9, cap: t('tour.s2'), run() {
        view('astro'); act.seek(rise.hour - 1); play(1);
        const now = Sim.at(S.data, D.model, rise.hour + 3);
        if (S.view === 'pano') Pano.lookAt(now.sunAz); else { Scene.lookAt(now.sunAz, now.sunAlt); Scene.tweenLook(now.sunAz, now.sunAlt, 11, 6); }
      } },
      { dur: 7, cap: t('tour.s3', { earth: Fmt.pctLoc(D.stats.earthPct) }), run() {
        play(24);
        const now = Sim.at(S.data, D.model, S.t);
        if (S.view === 'pano') Pano.lookAt(now.earthAz); else Scene.tweenLook(now.earthAz, Math.max(now.earthAlt, 3), 26, 2.5);
      } },
      { dur: 9, cap: t(D.batt.deadHour >= 0 ? 'tour.s4dead' : 'tour.s4alive', {
        dark: Fmt.days(longDark.len / 24), cap: Fmt.num(S.batt.cap, 0), n: Math.floor((D.batt.deadHour - D.batt.start) / 24) + 1 }), run() {
        view('orbit'); act.seek(Math.max(L, longDark.start - 60)); play(24);
        Scene.tween({ az: cam.az - 0.7, pol: 1.05, dist: 6500 }, 8);
      } },
      { dur: 8, cap: t('tour.s5', { flat: Fmt.pct(fv.flat.sunPct), real: Fmt.pct(fv.terrain.sunPct), y: S.year }), run() {
        act.setPlaying(false); view('orbit');
        if (proof >= 0) act.seek(proof);
        Scene.tween({ pol: 1.2, dist: 1500 }, 2);
        later = setTimeout(() => { if (active) act.setFlat(true); }, 2200);
      } },
      { dur: 5, cap: t('tour.s6'), run() { act.setFlat(false); Scene.tween({ pol: 1.1, dist: 3200 }, 4); } },
    ];
  }

  function show() {
    const st = steps[idx];
    setText($('tourCap'), st.cap);
    setText($('tourStep'), t('tour.step', { i: idx + 1, n: steps.length }));
    st.run();
    timer = setTimeout(() => { idx++; if (idx < steps.length) show(); else stop(); }, st.dur * 1000);
  }

  function start(state, actions) {
    if (active) return;
    S = state; act = actions;
    saved = { t: S.t, speed: S.speed };
    active = true; idx = 0; steps = build();
    $('tour').hidden = false;
    $('cockpit').dataset.tour = 'on';
    setText($('tourBtnLabel'), t('tour.stop'));
    show();
  }

  function stop() {
    if (!active) return;
    active = false;
    clearTimeout(timer); clearTimeout(later);
    $('tour').hidden = true;
    $('cockpit').dataset.tour = 'off';
    setText($('tourBtnLabel'), t('tour.start'));
    act.setPlaying(false); act.setFlat(false); act.setSpeed(saved.speed);
  }

  return { start, stop, toggle(state, actions) { if (active) stop(); else start(state, actions); }, get active() { return active; } };
})();
