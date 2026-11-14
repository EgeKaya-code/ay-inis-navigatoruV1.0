// Brifing kartlarındaki rakamları tasarim/veri/candidates.json ile karşılaştırır.
// Uygulamanın kodunu kullanmaz: en iyi / ortanca ve sıralama burada baştan hesaplanır.
//
//   1) sayfa açıkken, tarayıcıda check-cards.dom.js içeriğini çalıştır (agent-browser eval), çıktıyı dosyaya yaz
//   2) node check-cards.mjs <o-dosya.json>
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const veri = join(here, '..', 'veri');
const cand = JSON.parse(readFileSync(join(veri, 'candidates.json'), 'utf8'));
let dom = JSON.parse(readFileSync(process.argv[2], 'utf8'));
if (typeof dom === 'string') dom = JSON.parse(dom); // agent-browser eval sonucu tırnak içinde gelebilir

const nf = new Intl.NumberFormat('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const median = (a) => { const v = [...a].sort((x, y) => x - y), h = Math.floor(v.length / 2); return v.length % 2 ? v[h] : (v[h - 1] + v[h]) / 2; };
const darkScore = (d) => 100 - (Math.min(d, 30) / 30) * 100;

const expected = new Map(cand.regions.map((r) => {
  const m = r.candidates.map((c) => c.metrics['2m']);
  const sun = m.map((x) => x.terrain.sun_energy_pct), earth = m.map((x) => x.terrain_antenna_1deg.earth_pct), dark = m.map((x) => x.terrain.longest_dark_days);
  const score = m.map((x) => (x.terrain.sun_energy_pct + x.terrain_antenna_1deg.earth_pct + darkScore(x.terrain.longest_dark_days)) / 3);
  return [r.id, {
    n: m.length,
    sun: [Math.max(...sun), median(sun)], earth: [Math.max(...earth), median(earth)], dark: [Math.min(...dark), median(dark)],
    key: { power: Math.max(...sun), comm: Math.max(...earth), dark: -Math.min(...dark), balanced: Math.max(...score) },
  }];
}));

let checked = 0;
const bad = [];
for (const [sort, cards] of Object.entries(dom)) {
  const order = [...expected.entries()].sort((a, b) => b[1].key[sort] - a[1].key[sort]).map(([id]) => id);
  const got = cards.map((c) => c.id);
  checked++;
  if (got.join() !== order.join()) bad.push(`sıralama (${sort}): beklenen ${order.join(' ')} · ekranda ${got.join(' ')}`);
  for (const c of cards) {
    const e = expected.get(c.id);
    if (!e) { bad.push(`${c.id}: candidates.json'da yok`); continue; }
    for (const k of ['sun', 'earth', 'dark']) {
      const want = [(k === 'dark' ? '' : '%') + nf.format(e[k][0]), '/ ' + (k === 'dark' ? '' : '%') + nf.format(e[k][1])];
      for (const i of [0, 1]) {
        checked++;
        if (c[k][i] !== want[i]) bad.push(`${sort} · ${c.id} · ${k} ${i ? 'ortanca' : 'en iyi'}: beklenen "${want[i]}" · ekranda "${c[k][i]}"`);
      }
    }
  }
}
console.log(`${checked} karşılaştırma (${Object.keys(dom).length} sıralama × ${expected.size} bölge), ${bad.length} uyuşmazlık`);
bad.forEach((b) => console.log('  ✗ ' + b));
process.exit(bad.length ? 1 : 0);
