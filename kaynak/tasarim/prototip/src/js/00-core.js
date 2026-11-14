// ===== core: sözlük, biçimlendirme, küçük yardımcılar =====
// STRINGS, build.py tarafından tasarim/strings.<dil>.json dosyalarıyla doldurulur: { tr: {...}, en: {...} }.
const STRINGS = /*__STRINGS__*/ {};
const Store = {
  get(k, d) { try { const v = localStorage.getItem('ayinis.' + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('ayinis.' + k, JSON.stringify(v)); } catch (e) { /* depolama yoksa da çalış */ } },
};
const LANG = STRINGS[Store.get('lang', 'tr')] ? Store.get('lang', 'tr') : 'tr';
const STR = STRINGS[LANG] || {};
const LOCALE = LANG === 'tr' ? 'tr-TR' : 'en-GB';

function t(key, vars) {
  let s = key.split('.').reduce((o, k) => (o == null ? o : o[k]), STR);
  if (s == null && STRINGS.tr) s = key.split('.').reduce((o, k) => (o == null ? o : o[k]), STRINGS.tr); // çeviride yoksa Türkçesi
  if (s == null) { console.warn('eksik metin:', key); return key; }
  if (vars && typeof s === 'string') s = s.replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? vars[k] : m));
  return s;
}

// Sade mod: jargonlu etiketlerin sade karşılığı (sözlükte plain["anahtar"]); yoksa asıl metin.
let PLAIN = false;
function tp(key, vars) {
  const p = PLAIN && STR.plain ? STR.plain[key] : null;
  if (p == null) return t(key, vars);
  return vars ? p.replace(/\{(\w+)\}/g, (m, k) => (vars[k] != null ? vars[k] : m)) : p;
}

const $ = (id) => document.getElementById(id);
const D2R = Math.PI / 180;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, f) => a + (b - a) * f;
const smooth = (a, b, v) => { const x = clamp((v - a) / (b - a), 0, 1); return x * x * (3 - 2 * x); };
const easeInOut = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

const Fmt = (() => {
  const nf = {};
  const num = (v, d = 1) => {
    if (!nf[d]) nf[d] = new Intl.NumberFormat(LOCALE, { minimumFractionDigits: d, maximumFractionDigits: d });
    return nf[d].format(v);
  };
  const pct = (v, d = 1) => (LANG === 'tr' ? '%' + num(v, d) : num(v, d) + '%');
  const days = (v, d = 1) => num(v, d) + ' ' + t('unit.day');
  const deg = (v, d = 2) => (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), d) + '°';
  // süre: 48 saatten kısaysa saat, uzunsa gün
  const dur = (h) => (h < 48 ? Math.round(h) + ' ' + t('unit.hour') : days(h / 24));
  // saat sayacı verinin ilk yılının 1 Ocak 00:00 UTC'sinden başlar (Data.loadIndex ayarlar)
  let epoch = Date.UTC(2027, 0, 1);
  const setEpoch = (ms) => { epoch = ms; };
  const hourToDate = (h) => new Date(epoch + Math.floor(h * 60 + 1e-6) * 60e3);
  const hourOfMs = (ms) => (ms - epoch) / 3600e3;
  const yearStart = (y) => (Date.UTC(y, 0, 1) - epoch) / 3600e3;
  const yearOf = (h) => hourToDate(h).getUTCFullYear();
  // <input type="datetime-local"> değeri (UTC olarak okunur/yazılır)
  const toInput = (h) => hourToDate(Math.round(h)).toISOString().slice(0, 16);
  const fromInput = (v) => { const ms = Date.parse(v + (v.length <= 10 ? 'T00:00' : '') + ':00Z'); return Number.isNaN(ms) ? null : hourOfMs(ms); };
  const p2 = (n) => String(n).padStart(2, '0');
  const date = (h, withYear) => {
    const d = hourToDate(h);
    return d.getUTCDate() + ' ' + t('months')[d.getUTCMonth()] + (withYear ? ' ' + d.getUTCFullYear() : '');
  };
  const time = (h) => { const d = hourToDate(h); return p2(d.getUTCHours()) + ':' + p2(d.getUTCMinutes()); };
  const latlon = (lat, lon) =>
    num(Math.abs(lat), 2) + '° ' + (lat < 0 ? t('compass.s') : t('compass.n')) + ' · ' +
    num(Math.abs(lon), 2) + '° ' + (lon < 0 ? t('compass.w') : t('compass.e'));
  // Türkçe: "%65'inde", "%66'sında" gibi; ek sayının okunuşuna göre değişir (yalnız tr sözlüğü için).
  const trLocSuffix = (n) => {
    n = Math.round(Math.abs(n));
    const ones = ['', "'inde", "'sinde", "'ünde", "'ünde", "'inde", "'sında", "'sinde", "'inde", "'unda"];
    const tens = ['', "'unda", "'sinde", "'unda", "'ında", "'sinde", "'ında", "'inde", "'inde", "'ında"];
    if (n === 0) return "'ında";
    if (n % 10) return ones[n % 10];
    if (n % 100) return tens[(n / 10) % 10];
    return "'ünde";
  };
  const pctLoc = (v) => (LANG === 'tr' ? '%' + Math.round(v) + trLocSuffix(v) : Math.round(v) + '%');
  const pct0 = (v) => (LANG === 'tr' ? '%' + Math.round(v) : Math.round(v) + '%');
  const az = (v) => num(((v % 360) + 360) % 360, 1) + '°';
  return { num, pct, pct0, days, deg, az, dur, date, time, latlon, pctLoc, hourToDate, setEpoch, hourOfMs, yearStart, yearOf, toInput, fromInput };
})();

// sayaç gibi akan rakam
const Counter = (() => {
  const live = new WeakMap();
  function run(el, to, render, ms = 700) {
    const prev = live.get(el);
    const from = prev ? prev.cur : to;
    if (prev && prev.raf) cancelAnimationFrame(prev.raf);
    const st = { cur: from, raf: 0 };
    live.set(el, st);
    if (from === to || matchMedia('(prefers-reduced-motion: reduce)').matches) { st.cur = to; el.innerHTML = render(to); return; }
    const t0 = performance.now();
    const step = (now) => {
      const k = clamp((now - t0) / ms, 0, 1);
      st.cur = lerp(from, to, easeInOut(k));
      el.innerHTML = render(st.cur);
      if (k < 1) st.raf = requestAnimationFrame(step); else { st.cur = to; st.raf = 0; }
    };
    st.raf = requestAnimationFrame(step);
  }
  // animasyonsuz başlangıç değeri (bir sonraki run buradan akar)
  function set(el, v) { const prev = live.get(el); if (prev && prev.raf) cancelAnimationFrame(prev.raf); live.set(el, { cur: v, raf: 0 }); }
  return { run, set };
})();

function setText(el, s) { if (el && el.textContent !== s) el.textContent = s; }
function icon(name, cls) { return '<svg class="ic' + (cls ? ' ' + cls : '') + '"><use href="#i-' + name + '"/></svg>'; }
function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c])); }

function applyStrings(root) {
  root.querySelectorAll('[data-t]').forEach((el) => { el.textContent = t(el.dataset.t); });
  root.querySelectorAll('[data-t-title]').forEach((el) => { el.title = t(el.dataset.tTitle); });
}

// küçük dpr'li canvas yardımcıları
function fitCanvas(cv) {
  const r = cv.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.max(1, Math.round(r.width * dpr)), h = Math.max(1, Math.round(r.height * dpr));
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  return { w: r.width, h: r.height, dpr };
}
const cssVarCache = new Map();
function cssVar(name) {
  if (!cssVarCache.has(name)) cssVarCache.set(name, getComputedStyle(document.documentElement).getPropertyValue(name).trim());
  return cssVarCache.get(name);
}
