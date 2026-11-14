"""src/ içindeki parçaları tek bir index.html dosyasında birleştirir (build.mjs'in Python eşdeğeri;
Node kurulu olmayan makineler için). Kullanım: python build.py

Sözlükler: strings.tr.json (zorunlu) ve varsa strings.<dil>.json. Hepsi sayfaya gömülür.
"""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf8")
from pathlib import Path

here = Path(__file__).resolve().parent
src = here / "src"
read = lambda p: Path(p).read_text(encoding="utf8")

strings = {}
for f in sorted(here.glob("strings.*.json")):
    strings[f.name.split(".")[1]] = json.loads(read(f))
css = read(src / "styles.css")
markup = read(src / "markup.html")
js_files = sorted(p for p in (src / "js").glob("*.js"))
js = "\n".join(read(p) for p in js_files)
if "/*__STRINGS__*/ {}" not in js:
    sys.exit("00-core.js içinde /*__STRINGS__*/ {} yer tutucusu yok")
js = js.replace("/*__STRINGS__*/ {}", json.dumps(strings, ensure_ascii=False))


def has(d, key):
    for k in key.split("."):
        if not isinstance(d, dict) or k not in d:
            return False
        d = d[k]
    return True


# sözlük denetimi: kodda geçen her anahtar her sözlükte olmalı
keys = set(re.findall(r"\bt\('([\w.]+)'", js + markup)) | set(re.findall(r'data-t(?:-title)?="([\w.]+)"', markup))
for lang, d in strings.items():
    missing = sorted(k for k in keys if not k.endswith(".") and not has(d, k))
    if missing:
        print(f"EKSİK METİN ANAHTARI ({lang}):", ", ".join(missing))

# Varsayılan: internetsiz çalışma. three.js 0.160.0 ve yazı tipleri vendor/ altındaki yerel kopyalardan yüklenir
# (serve.py sunar); sayfa localhost dışına istek yapmaz.
# "python build.py --cdn": eski davranış (CDN adresleri), yalnız tek dosyanın vendor/ olmadan yayımlanacağı durum için.
if "--cdn" in sys.argv:
    FONTS = "https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
    THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"
else:
    FONTS, THREE = "vendor/fonts.css", "vendor/three.min.js"
    for f in (FONTS, THREE):
        if not (here / f).exists():
            sys.exit(f"{f} yok")
html = f"""<title>Ay İniş Navigatörü</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="{FONTS}">
<style>
{css}
</style>
{markup}
<script src="{THREE}"></script>
<script>
(() => {{
'use strict';
{js}
}})();
</script>
"""
(here / "index.html").write_text(html, encoding="utf8", newline="\n")
print(f"index.html yazıldı: {len(html) / 1024:.0f} KB, {len(js_files)} js dosyası, diller: {', '.join(strings)}, "
      f"three.js ve yazı tipleri: {'CDN' if '--cdn' in sys.argv else 'yerel (vendor/)'}")
