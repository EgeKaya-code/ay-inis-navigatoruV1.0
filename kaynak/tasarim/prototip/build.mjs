// src/ içindeki parçaları tek bir index.html dosyasında birleştirir (Artifact olarak yayımlanan dosya).
// Kullanım: node build.mjs
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, 'src');
const read = (p) => readFileSync(p, 'utf8');

const strings = JSON.parse(read(join(here, '..', 'strings.tr.json')));
const css = read(join(src, 'styles.css'));
const markup = read(join(src, 'markup.html'));
const jsFiles = readdirSync(join(src, 'js')).filter((f) => f.endsWith('.js')).sort();
let js = jsFiles.map((f) => read(join(src, 'js', f))).join('\n');
js = js.replace('/*__STRINGS__*/ {}', JSON.stringify(strings));

// sözlük denetimi: kodda geçen her anahtar strings.tr.json içinde olmalı
const has = (key) => key.split('.').reduce((o, k) => (o == null ? o : o[k]), strings) != null;
const keys = new Set();
for (const m of (js + markup).matchAll(/\bt\('([\w.]+)'/g)) keys.add(m[1]);
for (const m of markup.matchAll(/data-t="([\w.]+)"/g)) keys.add(m[1]);
const missing = [...keys].filter((k) => !k.endsWith('.') && !has(k));
if (missing.length) console.warn('EKSİK METİN ANAHTARI:', missing.join(', '));

const FONTS = 'https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap';
const THREE = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js';

const html = `<title>Ay İniş Navigatörü</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="${FONTS}">
<style>
${css}
</style>
${markup}
<script src="${THREE}"></script>
<script>
(() => {
'use strict';
${js}
})();
</script>
`;
writeFileSync(join(here, 'index.html'), html);
console.log('index.html yazıldı:', (html.length / 1024).toFixed(0) + ' KB,', jsFiles.length, 'js dosyası');
