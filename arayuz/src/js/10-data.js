// ===== data: veri dosyalarını yükleme (tembel, önbellekli) =====
const Data = (() => {
  const BASE = 'veri/';
  const cache = new Map();
  let index = null;

  async function json(path) {
    const r = await fetch(BASE + path);
    if (!r.ok) throw new Error(path + ' → HTTP ' + r.status);
    return r.json();
  }
  function image(path) {
    return new Promise((res) => {
      const im = new Image();
      im.onload = () => res(im);
      im.onerror = () => res(null); // harita olmadan da çalış
      im.src = BASE + path;
    });
  }

  const median = (a) => { const v = a.slice().sort((x, y) => x - y), h = v.length >> 1; return v.length % 2 ? v[h] : (v[h - 1] + v[h]) / 2; };
  const spread = (a, best) => ({ best: best(...a), median: median(a) });

  // Bir bölgenin aday noktaları (candidates.json). Her aday, kokpitin beklediği "site" kaydıyla aynı
  // biçimdedir; eski örnek nokta (legacy) sites.json kaydının kendisidir, rakamları değişmez.
  function attachCandidates(s, rc, sens) {
    const own = { regionId: s.id, legacy: true, rank: null, landable: true, nasaSun: null, nasaEarth: null };
    Object.assign(s, own, { cands: [s], heat: null });
    if (rc) {
      s.cands = rc.candidates.map((c) => (c.legacy
        ? Object.assign(s, { nasaSun: c.nasa_sun_pct, nasaEarth: c.nasa_earth_pct })
        : {
          id: c.id, regionId: s.id, region: s.region, reg: s.reg, legacy: false, rank: c.rank, landable: !!c.package,
          lat: c.lat, lon: c.lon, ps_km: c.ps_km, ground_height_m: c.ground_height_m, slope_deg: c.slope_deg,
          m: c.metrics['2m'], nasaSun: c.nasa_sun_pct, nasaEarth: c.nasa_earth_pct, search_note: null,
        }));
      if (!s.cands.includes(s)) s.cands.push(s);
      s.heat = { file: rc.heat.file, bounds: rc.heat.bounds_km, map: rc.nasa_map, image: null, asked: false };
    }
    // iniş hatası halkaları (sensitivity.json; yalnız iniş paketi olan noktalar için var)
    s.cands.forEach((c) => { c.sens = (sens && sens[c.id]) || null; });
    // Pareto: baskılanmayan noktalar; baskılananlarda en iyi baskılayan nokta
    const dom = Sim.pareto(s.cands.map((c) => c.m));
    s.cands.forEach((c, i) => { c.dominator = dom[i] < 0 ? null : s.cands[dom[i]]; c.pareto = dom[i] < 0; });
    const of = (f) => s.cands.map(f);
    s.stat = {
      n: s.cands.length,
      sun: spread(of((c) => c.m.terrain.sun_energy_pct), Math.max),
      earth1: spread(of((c) => c.m.terrain_antenna_1deg.earth_pct), Math.max),
      dark: spread(of((c) => c.m.terrain.longest_dark_days), Math.min),
      score: spread(of((c) => Sim.balanced(c.m)), Math.max),
    };
    // kart şeridi ve varsayılan sıralama için: dengeli puanı en yüksek aday
    s.top = s.cands.find((c) => c.rank === 1) || s;
  }

  // regions.json + sites.json + polar_map.png (+ varsa candidates.json: yoksa her bölge tek noktayla çalışır)
  async function loadIndex() {
    if (index) return index;
    const [reg, sites, map, cand, sens, yrs] = await Promise.all([json('regions.json'), json('sites.json'), image('polar_map.png'),
      json('candidates.json').catch(() => null), json('sensitivity.json').catch(() => null), json('years.json').catch(() => null)]);
    const byId = new Map(reg.regions.map((r) => [r.id, r]));
    const candById = new Map(cand ? cand.regions.map((r) => [r.id, r]) : []);
    index = {
      map: { image: map, bounds: reg.map.bounds_km },
      period: sites.period,
      hasCandidates: !!cand,
      sites: sites.sites.map((s) => ({ ...s, reg: byId.get(s.id), m: s.metrics['2m'] })),
    };
    index.sensRadii = sens ? sens.radii_m : [];
    // years.json: hangi yılların serisi ve hangi gözlemci yüksekliklerinin ufuk profili var (yoksa yalnız 2027 ve 2 m)
    index.years = yrs && yrs.years && yrs.years.length ? yrs.years.slice().sort() : [2027];
    index.heights = yrs && yrs.observer_heights_m ? yrs.observer_heights_m : [2];
    index.defaultYear = index.years.includes(2027) ? 2027 : index.years[0];
    index.validation = (yrs && yrs.validation) || null;
    Fmt.setEpoch(Date.UTC(index.years[0], 0, 1));
    index.hours = (Date.UTC(index.years[index.years.length - 1] + 1, 0, 1) - Date.UTC(index.years[0], 0, 1)) / 3600e3;
    index.sites.forEach((s) => attachCandidates(s, candById.get(s.id), sens ? sens.regions[s.id] : null));
    return index;
  }

  // NASA aydınlanma ısı haritası (bölge seçilince iner); gelince onReady çağrılır
  function loadHeat(s, onReady) {
    if (!s.heat || s.heat.asked) return;
    s.heat.asked = true;
    image(s.heat.file).then((im) => { s.heat.image = im; if (im && onReady) onReady(); });
  }

  const f32 = (a) => Float32Array.from(a);

  // Arazi: float32 ızgara. Artifact ikili dosya sunmadığı için önce base64 metin kopyası
  // (terrain.b64.txt, pack-terrain.mjs üretir) denenir; yoksa asıl terrain.bin okunur.
  async function terrainBuffer(dir) {
    try {
      const r = await fetch(BASE + dir + 'terrain.b64.txt');
      if (!r.ok) throw new Error('b64 yok');
      const bin = atob((await r.text()).trim());
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return bytes.buffer;
    } catch (e) {
      const r = await fetch(BASE + dir + 'terrain.bin');
      if (!r.ok) throw new Error('terrain.bin → HTTP ' + r.status);
      return r.arrayBuffer();
    }
  }

  const mkHorizon = (hz) => ({ step: hz.azimuth_step_deg, elev: f32(hz.elevation_deg), dist: f32(hz.distance_km), observer: hz.observer_height_m });
  const FIELDS = { sunAlt: 'sun_alt_deg', sunAz: 'sun_az_deg', sunFrac: 'sun_visible_fraction', earthAlt: 'earth_alt_deg',
    earthAz: 'earth_az_deg', earthMargin: 'earth_margin_deg', earthIllum: 'earth_illuminated_fraction' };
  const hoursIn = (y) => (Date.UTC(y + 1, 0, 1) - Date.UTC(y, 0, 1)) / 3600e3;

  // tek yılın serisi (brifingdeki mini şeritler için; kokpit bütün yılları loadSite ile alır)
  const yearCache = new Map();
  function loadYear(id, year) {
    const key = id + '|' + year;
    if (!yearCache.has(key)) {
      const p = json('sites/' + id + '/series_' + year + '.json');
      yearCache.set(key, p);
      p.catch(() => yearCache.delete(key));
    }
    return yearCache.get(key);
  }

  // bir noktanın dosyaları: ufuk profili (2 m) + eldeki bütün yılların saatlik serisi, uç uca eklenmiş.
  // Saat sayacı ilk yılın 1 Ocak 00:00 UTC'sinden başlar. Arazi ayrı bir söz (promise): gelmese de 2B kısım çalışır.
  function loadSite(id) {
    if (cache.has(id)) return cache.get(id);
    const dir = 'sites/' + id + '/';
    const core = Promise.all([json(dir + 'horizon.json'), ...index.years.map((y) => loadYear(id, y))])
      .then(([hz, ...ys]) => {
        ys.forEach((se, i) => { if (se.sun_alt_deg.length !== hoursIn(index.years[i])) throw new Error(dir + 'series_' + index.years[i] + '.json: beklenmeyen uzunluk'); });
        const n = ys.reduce((a, se) => a + se.sun_alt_deg.length, 0);
        const series = { n, start: ys[0].start_utc, observer: ys[0].observer_height_m };
        for (const k in FIELDS) {
          const out = new Float32Array(n);
          let o = 0;
          for (const se of ys) { out.set(se[FIELDS[k]], o); o += se[FIELDS[k]].length; }
          series[k] = out;
        }
        const h = mkHorizon(hz);
        return { id, horizon: h, horizons: { [h.observer]: h }, series };
      });
    // arazi yalnız istenince iner (brifingdeki mini şeritler için 9 bölgenin serisi yeter)
    let terrainP = null;
    const terrain = () => {
      if (!terrainP) {
        terrainP = Promise.all([json(dir + 'terrain.json'), terrainBuffer(dir)]).then(([meta, buf]) => ({ meta, z: new Float32Array(buf) }));
        terrainP.catch(() => { terrainP = null; });
      }
      return terrainP;
    };
    const entry = { core, terrain };
    // başka gözlemci yüksekliğinin ufuk profili (horizon_0m.json, horizon_10m.json); istenince iner
    entry.horizon = async (h) => {
      const c = await core;
      if (!c.horizons[h]) c.horizons[h] = mkHorizon(await json(dir + 'horizon_' + h + 'm.json'));
      return c.horizons[h];
    };
    cache.set(id, entry);
    core.catch(() => cache.delete(id));
    return entry;
  }

  return { loadIndex, loadSite, loadYear, loadHeat };
})();
