// Yerel önizleme sunucusu: index.html'i Artifact'in yayım iskeletine benzer bir sayfayla sarar,
// veri/ yolunu tasarim/veri klasörüne bağlar.
// Kullanım: node serve.mjs [port]   →   http://localhost:8765
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, join, normalize, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const veri = join(here, '..', 'veri');
const port = Number(process.argv[2]) || 8765;
const types = { '.json': 'application/json', '.png': 'image/png', '.bin': 'application/octet-stream', '.txt': 'text/plain', '.html': 'text/html; charset=utf-8' };

const shell = (body) => `<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
</head><body>${body}</body></html>`;

createServer(async (req, res) => {
  try {
    const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    if (path === '/' || path === '/index.html') {
      const body = await readFile(join(here, 'index.html'), 'utf8');
      res.writeHead(200, { 'content-type': types['.html'], 'cache-control': 'no-store' });
      return res.end(shell(body));
    }
    if (path.startsWith('/veri/')) {
      const file = normalize(join(veri, path.slice(6)));
      if (!file.startsWith(veri)) throw new Error('yol dışı');
      // base64 arazi kopyaları yayin/ altında durur; orada da yoksa (ör. aday noktalar) terrain.bin'den anında üretilir
      const buf = await readFile(file)
        .catch(() => readFile(normalize(join(here, 'yayin', 'veri', path.slice(6)))))
        .catch(async (e) => {
          if (!file.endsWith('terrain.b64.txt')) throw e;
          return Buffer.from((await readFile(join(dirname(file), 'terrain.bin'))).toString('base64'));
        });
      res.writeHead(200, { 'content-type': types[extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
      return res.end(buf);
    }
    res.writeHead(404); res.end('yok');
  } catch (e) {
    res.writeHead(404); res.end(String(e.message));
  }
}).listen(port, () => console.log('http://localhost:' + port));
