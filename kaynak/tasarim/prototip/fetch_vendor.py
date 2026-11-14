"""Prototipin internetten yüklediği kaynakların yerel kopyasını vendor/ altına indirir (bir kez çalıştırılır).

    python fetch_vendor.py

- three.js 0.160.0, modülsüz derleme (three.min.js): prototipin kullandığı sürümün aynısı.
- Yazı tipleri (Google Fonts): Barlow Condensed 500/600/700, IBM Plex Mono 400/500, IBM Plex Sans 400/500/600;
  yalnız latin ve latin-ext alt kümeleri (Türkçe karakterler latin-ext içinde). vendor/fonts.css yerel dosyalara bakar.

Sayfa bundan sonra localhost dışına istek yapmaz (build.py vendor/ yollarını kullanır, serve.py sunar).
"""
import hashlib
import re
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf8")
here = Path(__file__).resolve().parent
vendor = here / "vendor"
THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.min.js"
FONTS = ("https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700"
         "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
KEEP = {"latin", "latin-ext"}


def get(url: str) -> bytes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            print("  yeniden deneniyor:", e)
    raise RuntimeError(url)


def main():
    (vendor / "fonts").mkdir(parents=True, exist_ok=True)
    three = vendor / "three.min.js"
    if not three.exists():
        three.write_bytes(get(THREE))
    m = re.search(rb'REVISION\s*=\s*"(\d+)"|="(\d+)";"undefined"!=typeof __THREE_DEVTOOLS__', three.read_bytes())
    print(f"three.min.js {three.stat().st_size} bayt, sha256 {hashlib.sha256(three.read_bytes()).hexdigest()[:16]}…, sürüm r{(m.group(1) or m.group(2)).decode() if m else '?'}")

    css = get(FONTS).decode("utf8")
    out, n = [], 0
    # her blok: /* alt küme */ @font-face { ... src: url(...) format('woff2'); ... }
    for subset, block in re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{[^}]*\})", css):
        if subset not in KEEP:
            continue
        fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
        wgt = re.search(r"font-weight:\s*(\d+)", block).group(1)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
        name = f"{fam.replace(' ', '')}-{wgt}-{subset}.woff2"
        path = vendor / "fonts" / name
        if not path.exists():
            path.write_bytes(get(url))
        n += 1
        out.append(f"/* {fam} {wgt} · {subset} */\n" + block.replace(url, f"fonts/{name}"))
    (vendor / "fonts.css").write_text("/* Google Fonts'tan indirildi (fetch_vendor.py); SIL Open Font License. */\n" + "\n".join(out) + "\n",
                                      encoding="utf8", newline="\n")
    total = sum(f.stat().st_size for f in (vendor / "fonts").glob("*.woff2"))
    print(f"{n} yazı tipi dosyası, {total / 1024:.0f} KB; vendor/fonts.css yazıldı")


if __name__ == "__main__":
    main()
