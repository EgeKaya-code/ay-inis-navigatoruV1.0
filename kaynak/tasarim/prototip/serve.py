"""Yerel önizleme sunucusu (serve.mjs'in Python eşdeğeri): index.html'i yayım iskeletine benzer bir
sayfayla sarar, veri/ yolunu tasarim/veri klasörüne bağlar. Kullanım: python serve.py [port]"""
import base64
import sys

sys.stdout.reconfigure(encoding="utf8")
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

here = Path(__file__).resolve().parent
veri = (here.parent / "veri").resolve()
port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
TYPES = {".json": "application/json", ".png": "image/png", ".bin": "application/octet-stream",
         ".txt": "text/plain", ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".woff2": "font/woff2"}
vendor = (here / "vendor").resolve()
SHELL = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!-- internetsiz çalışma güvencesi: sayfa yalnız bu sunucudan kaynak yükleyebilir; dışarı giden her istek tarayıcıda engellenir -->
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'">
<style>:root{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}
body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
</head><body>@@BODY@@</body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="text/plain"):
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("cache-control", "no-store")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        try:
            if path in ("/", "/index.html"):
                body = (here / "index.html").read_text(encoding="utf8")
                return self.send(200, SHELL.replace("@@BODY@@", body).encode("utf8"), TYPES[".html"])
            if path.startswith("/vendor/"):
                # three.js ve yazı tiplerinin yerel kopyaları (internetsiz çalışma)
                file = (vendor / path[8:]).resolve()
                if vendor not in file.parents or not file.is_file():
                    raise FileNotFoundError(path)
                return self.send(200, file.read_bytes(), TYPES.get(file.suffix, "application/octet-stream"))
            if path.startswith("/veri/"):
                rel = path[6:]
                file = (veri / rel).resolve()
                if veri not in file.parents:
                    raise FileNotFoundError("yol dışı")
                alt = here / "yayin" / "veri" / rel
                if file.is_file():
                    buf = file.read_bytes()
                elif alt.is_file():
                    buf = alt.read_bytes()
                elif file.name == "terrain.b64.txt":
                    # base64 kopyası yoksa (ör. aday noktalar) terrain.bin'den anında üretilir
                    buf = base64.b64encode((file.parent / "terrain.bin").read_bytes())
                else:
                    raise FileNotFoundError(rel)
                return self.send(200, buf, TYPES.get(file.suffix, "application/octet-stream"))
            self.send(404, b"yok")
        except Exception as e:  # noqa: BLE001
            self.send(404, str(e).encode("utf8"))


print(f"http://localhost:{port}")
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
