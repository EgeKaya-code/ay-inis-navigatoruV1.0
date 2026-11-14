// ===== descent: iniş sekansı (kamera alçalır, HUD panelleri sırayla açılır) =====
const Descent = (() => {
  const DUR = 9; // saniye
  let active = false, timers = [], handle = null, finish = null;

  const fmtAlt = (m) => (m >= 1000 ? Fmt.num(m / 1000, m >= 20000 ? 0 : 1) + ' ' + t('unit.km') : Math.round(m) + ' ' + t('unit.m'));

  // o: { name, linkUp, use3d } → Promise (bitince ya da atlanınca çözülür)
  function play(o) {
    const cp = $('cockpit'), box = $('descent'), log = $('dLog');
    const panels = [...cp.querySelectorAll('[data-boot]')].sort((a, b) => a.dataset.boot - b.dataset.boot);
    active = true;
    cp.dataset.boot = 'seq';
    panels.forEach((p) => p.classList.remove('on'));
    log.innerHTML = '';
    box.hidden = false;
    setText($('dAlt'), o.use3d ? fmtAlt(120000) : '—');
    const say = (key, vars) => { const li = document.createElement('li'); li.textContent = t(key, vars); log.appendChild(li); };
    const open = (n) => panels.filter((p) => Number(p.dataset.boot) <= n).forEach((p) => p.classList.add('on'));
    const k = o.use3d ? 1 : 0.35; // 3D yoksa kısa tut
    const at = (sec, fn) => timers.push(setTimeout(fn, sec * k * 1000));

    return new Promise((resolve) => {
      finish = () => {
        if (!active) return;
        active = false;
        timers.forEach(clearTimeout); timers = [];
        panels.forEach((p) => p.classList.add('on'));
        cp.dataset.boot = 'done';
        box.hidden = true;
        handle = null;
        resolve();
      };
      say('descent.s1', { name: o.name });
      at(2.2, () => say('descent.s2'));
      at(4.6, () => { say('descent.s3'); open(2); });
      at(5.8, () => { say('descent.s4'); open(3); });
      at(7.0, () => { say(o.linkUp ? 'descent.s5up' : 'descent.s5down'); open(5); });
      at(8.1, () => { say('descent.s6'); open(6); });
      if (o.use3d) handle = Scene.startDescent(DUR - 0.6, (alt) => setText($('dAlt'), fmtAlt(alt)), () => {});
      at(DUR, finish);
    });
  }

  function skip() {
    if (!active) return;
    if (handle) handle.skip();
    if (finish) finish();
  }

  return { play, skip, get active() { return active; } };
})();
