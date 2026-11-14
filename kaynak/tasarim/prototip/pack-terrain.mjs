// Artifact yayımı ikili (.bin) dosya sunmuyor. Bu betik her terrain.bin dosyasını kayıpsız olarak
// base64 metne çevirir: yayin/veri/sites/<id>/terrain.b64.txt (float32 baytları aynen korunur).
// tasarim/veri klasörüne dokunmaz. Kullanım: node pack-terrain.mjs
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const sites = join(here, '..', 'veri', 'sites');
for (const id of readdirSync(sites)) {
  const out = join(here, 'yayin', 'veri', 'sites', id);
  mkdirSync(out, { recursive: true });
  const b64 = readFileSync(join(sites, id, 'terrain.bin')).toString('base64');
  writeFileSync(join(out, 'terrain.b64.txt'), b64);
  console.log(id, (b64.length / 1e6).toFixed(2) + ' MB');
}
