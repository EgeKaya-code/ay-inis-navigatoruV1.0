// ===== app: durum, sahne geçişleri, ana döngü =====
const App = (() => {
  // tek durum nesnesi; modüller okur, yalnız buradaki eylemler değiştirir
  const S = {
    index: null,
    site: null,       // sites.json kaydı (+ bölge)
    data: null,       // horizon + series (bütün yıllar uç uca)
    D: null,          // Sim.derive sonucu
    now: null,        // Sim.at sonucu
    t: 0, landing: 0, playing: false, speed: 24,   // saat; sayaç verinin ilk yılının 1 Ocak'ından başlar
    year: 2027, zoom: 'year',                      // özet rakamlarının ve şeridin yılı; şerit penceresi
    height: 2,                                     // gözlemci (panel/anten) yüksekliği, m
    flat: false, flatK: 0, mask: 1,
    batt: { cap: 100, panel: 2, load: 0.5 }, // örnek değerler; gerçek araç verisi değil
    unc: 0.2, risk: null,                    // tüketim ve panel gücündeki belirsizlik (±oran) ve sonucu
    view: 'orbit', simple: false, gl: false, has3d: false, sceneTried: false,
    scene: 'briefing', prevScene: 'briefing',
    playDescent: Store.get('descent', false), landedOnce: false, // iniş sekansı: ilk inişte oynar, sonra yalnız istenirse
  };
  let last = 0, landBusy = false;

  function loading(msg, soft) {
    const el = $('loading');
    el.hidden = !msg;
    el.classList.toggle('soft', !!soft);
    el.classList.remove('err');
    if (msg) setText($('loadingMsg'), msg);
  }

  const yearRange = (y) => [clamp(Fmt.yearStart(y), 0, S.index.hours), clamp(Fmt.yearStart(y + 1), 0, S.index.hours)];

  function recompute(animate) {
    S.D = Sim.derive(S.data, { flat: S.flat, mask: S.mask, batt: S.batt, landing: S.landing, range: yearRange(S.year) });
    S.risk = riskOf();
    S.now = Sim.at(S.data, S.D.model, S.t);
    HUD.derived(animate);
    Timeline.draw(S.D, S.batt.cap);
    SkyPlot.invalidate();
  }

  // Belirsizlik altında batarya: denemeler kapasiteye bağlı değil, o yüzden kapasite kaydırılırken yeniden koşmaz.
  let riskKey = '', riskNeed = null;
  function riskOf() {
    if (!(S.unc > 0)) return null;
    const key = [S.data.id, S.flat, S.height, S.D.batt.start, S.batt.panel, S.batt.load, S.unc].join('|');
    if (key !== riskKey) { riskKey = key; riskNeed = Sim.uncertainty(S.D.model, S.batt, S.D.batt.start, S.unc); }
    return { n: riskNeed.length, ...Sim.survival(riskNeed, S.batt.cap) };
  }

  // bir noktanın verisi, seçili gözlemci yüksekliğinin ufuk profiliyle (kokpit ve karşılaştırma ortak kullanır)
  async function core(id) {
    const entry = Data.loadSite(id), c = await entry.core;
    try { c.horizon = await entry.horizon(S.height); } catch (e) { console.warn('ufuk profili yok:', id, S.height, e); c.horizon = c.horizons[2]; }
    return c;
  }

  // 3D sahne (arazi, ufuk halkası, astronotun gözü) 2 m gözlemci içindir; başka yükseklik seçiliyken bunu sahnenin üstünde söyle
  function heightNote() {
    if (!S.has3d) return; // 3D yokken "3D açılamadı" iletisi kalsın
    HUD.message(S.height !== 2 && S.view !== 'pano' ? t('scene.heightNote', { h: Fmt.num(S.height, 0) }) : '');
  }

  function show(scene) {
    if (scene !== S.scene) S.prevScene = S.scene;
    S.scene = scene;
    $('briefing').hidden = scene !== 'briefing'; $('cockpit').hidden = scene !== 'cockpit'; $('cmpScene').hidden = scene !== 'compare';
    $('app').dataset.scene = scene;
  }

  function applyZoom() {
    const n = S.index.hours;
    if (S.zoom === 'all') Timeline.setView(0, n - 1);
    else if (S.zoom === 'year') { const [a, b] = yearRange(S.year); Timeline.setView(a, b - 1); }
    else if (S.zoom !== 'custom') { const span = Number(S.zoom) * 24; Timeline.setView(S.t - span * 0.15, S.t + span * 0.85); }
  }

  // ---------- eylemler ----------
  const act = {
    setView(v) {
      if (!S.has3d && v !== 'pano') return;
      S.view = v;
      $('gl').hidden = v === 'pano'; $('pano').hidden = v !== 'pano';
      if (v === 'pano') { Scene.hideMarkers(); Pano.lookAt(S.now ? S.now.earthAz : 0); } else Scene.setView(v);
      heightNote();
      HUD.controls();
    },
    setFlat(on) {
      if (S.flat === on) return;
      S.flat = on;
      Scene.setFlat(on);
      recompute(true);
      HUD.controls();
    },
    setSimple(on) { S.simple = on; PLAIN = on; HUD.controls(); HUD.derived(false); HUD.relabel(); },
    setSpeed(v) { S.speed = v; HUD.controls(); },
    setPlaying(on) {
      if (on && S.t >= S.data.series.n - 1) S.t = S.landing;
      S.playing = on; HUD.controls();
    },
    seek(h) { S.t = clamp(h, 0, S.data ? S.data.series.n - 1 : S.index.hours - 1); if (S.scene === 'cockpit') Timeline.follow(S.t); },
    nextEvent() {
      const e = S.D.feed.find((x) => x.hour > S.t + 0.01 && x.k !== 'landing');
      if (e) act.seek(e.hour);
    },
    setLandingNow() { S.landing = Math.round(S.t); recompute(false); Briefing.syncDate(); },
    // yıl seçimi: imleç ve iniş anı aynı takvim gününe, seçilen yıla taşınır
    setYear(y) {
      const d = Fmt.yearStart(y) - Fmt.yearStart(S.year), n = S.index.hours;
      S.year = y;
      S.t = clamp(S.t + d, 0, n - 1); S.landing = clamp(Math.round(S.landing + d), 0, n - 1);
      if (S.zoom !== 'all') S.zoom = S.zoom === 'custom' ? 'year' : S.zoom;
      if (S.data) { recompute(true); applyZoom(); HUD.controls(); }
      Briefing.syncDate();
    },
    setZoom(z) { S.zoom = z; applyZoom(); HUD.controls(); },
    async setHeight(h) {
      S.height = h;
      if (S.data) { S.data = await core(S.data.id); recompute(true); heightNote(); }
      HUD.controls();
    },
    setMask(v) { S.mask = Math.round(v * 10) / 10; recompute(true); },
    setBatt(key, v) { S.batt[key] = v; recompute(false); },
    setUnc(v) { S.unc = v; recompute(false); },
    applyMinCap() { if (S.D.minCap != null) act.setBatt('cap', S.D.minCap); },
    goSafeLanding() {
      const day = S.D.scan.safeDay;
      if (day < 0) return;
      S.landing = day * 24; S.t = S.landing;
      recompute(false); Timeline.follow(S.t); Briefing.syncDate();
    },
    tour() { Tour.toggle(S, act); },
    look(what) {
      if (what === 'lander') return Scene.lookLander();
      const az = what === 'sun' ? S.now.sunAz : S.now.earthAz, alt = what === 'sun' ? S.now.sunAlt : S.now.earthAlt;
      if (S.view === 'pano') Pano.lookAt(az); else Scene.lookAt(az, alt);
    },
    back() {
      Tour.stop();
      Descent.skip();
      S.playing = false;
      show('briefing');
      Briefing.syncDate();
      Briefing.fitAll(false);
    },
    // o anki nokta + tarih + anten payını karşılaştırmaya ekle
    addScenario(btn) {
      const inCockpit = S.scene === 'cockpit';
      const site = inCockpit ? S.site : Briefing.pick;
      const r = Compare.add(site, Math.round(inCockpit ? S.t : S.landing), S.mask);
      flash(btn, r.ok ? t('cmp.added', { k: r.letter }) : r.reason);
    },
    openCompare() { Tour.stop(); Descent.skip(); S.playing = false; show('compare'); Compare.open(); },
    closeCompare() { show(S.prevScene === 'cockpit' && S.data ? 'cockpit' : 'briefing'); if (S.scene === 'briefing') Briefing.fitAll(false); },
    setPlayDescent(on) { S.playDescent = on; Store.set('descent', on); },
  };

  // tuşun üstünde kısa bir geri bildirim (ör. "A olarak eklendi" ya da neden eklenemediği)
  function flash(btn, text) {
    if (!btn) return;
    const span = btn.querySelector('span') || btn;
    if (!btn.dataset.label) btn.dataset.label = span.textContent;
    span.textContent = text;
    clearTimeout(btn._flash);
    btn._flash = setTimeout(() => { span.textContent = btn.dataset.label; }, 2200);
  }

  // ---------- brifingden (ya da karşılaştırmadan) kokpite ----------
  // site: bölgenin örnek noktası ya da iniş paketi olan bir aday (kayıt biçimi aynı).
  // opt: { hour, mask, skip }: karşılaştırmadan açılan senaryo. Tarih nokta değişirken korunur.
  async function land(site, opt = {}) {
    if (landBusy) return;
    landBusy = true;
    const entry = Data.loadSite(site.id);
    try {
      const fromBrief = S.scene === 'briefing';
      const [c] = await Promise.all([core(site.id), fromBrief ? Briefing.zoomTo(site, 850) : null]);
      loading(t('app.siteLoading', { name: site.region }), true);
      S.site = site; S.data = c;
      if (opt.hour != null) { S.landing = opt.hour; S.t = opt.hour; }
      if (opt.mask != null) S.mask = opt.mask;
      S.t = clamp(S.t, 0, c.series.n - 1); S.landing = clamp(Math.round(S.landing), 0, c.series.n - 1);
      S.year = Fmt.yearOf(S.t);
      S.playing = false; S.flat = false; S.flatK = 0; S.simple = false; PLAIN = false; HUD.relabel();

      show('cockpit');

      // 3D sahne: açılmazsa ya da arazi gelmezse 2B panorama ile devam
      if (!S.sceneTried) {
        S.sceneTried = true;
        S.gl = Scene.init($('gl'), $('viewport'));
        Scene.onLost = () => { S.gl = S.has3d = false; HUD.message(t('scene.no3d')); act.setView('pano'); };
      }
      let use3d = S.gl;
      HUD.message('');
      if (use3d) {
        try {
          const terrain = await entry.terrain();
          Scene.setFlat(false, true);
          Scene.setSite({ site, sites: S.index.sites, map: S.index.map, horizon: c.horizons[2], series: c.series, terrain });
        } catch (e) {
          console.warn('arazi yüklenemedi:', e);
          use3d = false;
          HUD.message(t('scene.terrainMissing'));
        }
      } else HUD.message(t('scene.no3d'));

      HUD.site();
      recompute(false);
      if (S.zoom === 'custom') S.zoom = 'year';
      applyZoom();
      S.has3d = use3d;
      act.setView(use3d ? 'orbit' : 'pano');
      loading('');
      const play = !opt.skip && (S.playDescent || !S.landedOnce);
      S.landedOnce = true;
      if (play) await Descent.play({ name: site.region, linkUp: S.now.linkUp, use3d });
    } catch (e) {
      console.error(e);
      show('briefing');
      loading(t('app.loadError', { msg: e.message }));
      $('loading').classList.add('err');
      setTimeout(() => loading(''), 6000);
    } finally {
      landBusy = false;
    }
  }

  // sahnenin HUD panelleriyle örtülmeyen kısmı (panorama eksenleri buraya çizilir)
  function insets() {
    const v = $('viewport').getBoundingClientRect(), m = $('colMid').getBoundingClientRect();
    if (m.width < 50 || m.bottom < v.top + 40 || m.top > v.bottom - 40) return { l: 0, t: 0, r: 0, b: 0 };
    return { l: Math.max(0, m.left - v.left), t: Math.max(0, m.top - v.top), r: Math.max(0, v.right - m.right), b: Math.max(0, v.bottom - m.bottom) };
  }

  // ---------- ana döngü ----------
  function frame(ts) {
    const dt = Math.min(0.1, (ts - last) / 1000 || 0);
    last = ts;
    if (S.scene === 'cockpit' && S.D) {
      if (S.playing && !Descent.active) {
        S.t += dt * S.speed;
        if (S.t >= S.data.series.n - 1) { S.t = S.data.series.n - 1; S.playing = false; HUD.controls(); }
        Timeline.follow(S.t);
      }
      // imleç başka bir yıla geçtiyse özet o yıla döner
      const y = Fmt.yearOf(S.t);
      if (y !== S.year && S.index.years.includes(y)) { S.year = y; recompute(false); if (S.zoom === 'year') applyZoom(); HUD.controls(); }
      const goal = S.flat ? 1 : 0;
      if (S.flatK !== goal) S.flatK = goal > S.flatK ? Math.min(1, S.flatK + dt / 0.8) : Math.max(0, S.flatK - dt / 0.8);
      S.now = Sim.at(S.data, S.D.model, S.t);
      const o = { site: S.data, now: S.now, tH: S.t, flatK: easeInOut(S.flatK), mask: S.mask, view: null };
      if (S.view === 'pano') {
        o.inset = insets();
        Pano.draw(o);
        o.view = Pano.view;
      } else {
        Scene.update(S.now);
        Scene.render(dt);
        const v = Scene.view;
        if (v.mode === 'astro') o.view = { yaw: v.yaw, hfov: 2 * Math.atan(Math.tan((v.fov * D2R) / 2) * v.aspect) / D2R };
      }
      SkyPlot.draw(o);
      HUD.tick();
      Timeline.setCursor(S.t);
    }
    requestAnimationFrame(frame);
  }

  function bindKeys() {
    document.addEventListener('keydown', (e) => {
      if (S.scene !== 'cockpit' || Descent.active || $('dataDlg').open) return;
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'BUTTON' && e.code === 'Space') return;
      if (e.code === 'Space') { e.preventDefault(); act.setPlaying(!S.playing); }
      else if (e.key === 'ArrowRight') act.seek(S.t + (e.shiftKey ? 24 : 1));
      else if (e.key === 'ArrowLeft') act.seek(S.t - (e.shiftKey ? 24 : 1));
      else if (e.key === 'n' || e.key === 'N') act.nextEvent();
      else if (e.key === 'h' || e.key === 'H') { const c = $('cockpit'); c.dataset.hud = c.dataset.hud === 'off' ? 'on' : 'off'; }
      else if (e.key === 'Escape') Tour.stop();
    });
  }

  async function main() {
    applyStrings(document);
    document.documentElement.lang = LANG;
    loading(t('app.loading'));
    try {
      S.index = await Data.loadIndex();
    } catch (e) {
      $('loading').classList.add('err');
      setText($('loadingMsg'), t('app.loadError', { msg: e.message }));
      return;
    }
    S.year = S.index.defaultYear;
    S.t = S.landing = Fmt.yearStart(S.year);
    HUD.init(S, act);
    SkyPlot.init($('sky'));
    Pano.init($('pano'));
    Timeline.init(act.seek, (a, b, user) => { if (user) { S.zoom = 'custom'; HUD.controls(); } });
    $('btnSkip').onclick = Descent.skip;
    Compare.init(S, { land, core, close: act.closeCompare });
    Briefing.init(S.index, {
      state: S,
      onSelect: (site) => { if (site.landable) Data.loadSite(site.id).terrain(); },
      onLand: land,
      onDate: (h) => { S.landing = Math.round(h); S.t = S.landing; S.year = Fmt.yearOf(S.t); },
    });
    document.querySelectorAll('[data-cmp-open]').forEach((b) => { b.onclick = act.openCompare; });
    $('bAddCmp').onclick = (e) => act.addScenario(e.currentTarget);
    $('cAddCmp').onclick = (e) => act.addScenario(e.currentTarget);
    $('chkDescent').checked = S.playDescent;
    $('chkDescent').onchange = (e) => act.setPlayDescent(e.target.checked);
    const langs = Object.keys(STRINGS), ls = $('langSel');
    if (langs.length > 1) {
      ls.hidden = false;
      ls.innerHTML = langs.map((l) => `<option value="${l}"${l === LANG ? ' selected' : ''}>${esc(STRINGS[l].langName || l)}</option>`).join('');
      ls.setAttribute('aria-label', t('langLabel'));
      ls.onchange = () => { Store.set('lang', ls.value); location.reload(); };
    }
    bindKeys();
    loading('');
    requestAnimationFrame(frame);
  }

  return { main, S, act, land };
})();
window.AyInis = Object.assign(App, { Scene, Briefing, Compare, Sim }); // konsoldan denemek için

App.main();
