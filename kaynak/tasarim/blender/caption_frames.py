"""Son 3 saniyeye alt yazı basar (venv Python'u, Pillow). Kareleri değiştirmez; --out klasörüne kopyalar.

    python caption_frames.py --frames D:/kareler --out D:/kareler_yazili [--work work] [--size 1920x1080]

--size'tan büyük kareler (malapert_render.py --overscan ile çizilenler) ortadan o boyuta kesilir.

Yazı: "Gerçek NASA LOLA arazisi · JPL efemerisi · <tarih saat UTC>" ve küçük not "AI ile üretilmedi".
Tarih work/scene.json'dan gelir (render edilen anın kendisi).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FPS, SECONDS, CAPTION_SECONDS, FADE_FRAMES = 30, 15, 3, 15
MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
FONTS = [r"C:\Windows\Fonts\bahnschrift.ttf", r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
INK = (238, 242, 238)  # --ink


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit("yazı tipi bulunamadı")


def caption(img: Image.Image, line1: str, line2: str, alpha: float) -> Image.Image:
    w, h = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f1, f2 = font(round(h * 0.034)), font(round(h * 0.024))
    x, y2 = round(w * 0.045), round(h * 0.925)
    y1 = y2 - round(h * 0.05)
    a = round(255 * alpha)
    # okunsun diye yazının arkasında yumuşak olmayan, düz koyu şerit (sahneyi boyamadan)
    d.rectangle([0, y1 - round(h * 0.03), w, h], fill=(0, 0, 0, round(150 * alpha)))
    d.line([x, y1 - round(h * 0.012), x + round(w * 0.06), y1 - round(h * 0.012)], fill=(*INK, a), width=max(1, round(h / 540)))
    d.text((x, y1), line1, font=f1, fill=(*INK, a))
    d.text((x, y2), line2, font=f2, fill=(*INK, round(a * 0.72)))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--frames", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--work", type=Path, default=Path(__file__).resolve().parent / "work")
    p.add_argument("--size", default="1920x1080")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sc = json.loads((args.work / "scene.json").read_text(encoding="utf-8"))
    when = dt.datetime.strptime(sc["utc"], "%Y-%m-%d %H:%M")
    line1 = f"Gerçek NASA LOLA arazisi · JPL efemerisi · {when.day} {MONTHS[when.month - 1]} {when.year} {when:%H:%M} UTC"
    line2 = "AI ile üretilmedi"
    n, first = FPS * SECONDS, FPS * (SECONDS - CAPTION_SECONDS) + 1
    w, h = (int(v) for v in args.size.lower().split("x"))
    for f in range(1, n + 1):
        src, dst = args.frames / f"f_{f:04d}.png", args.out / f"f_{f:04d}.png"
        img = Image.open(src)
        cropped = img.size != (w, h)
        if cropped:
            x0, y0 = (img.width - w) // 2, (img.height - h) // 2
            img = img.crop((x0, y0, x0 + w, y0 + h))
        if f >= first:
            caption(img, line1, line2, min(1.0, (f - first + 1) / FADE_FRAMES)).save(dst)
        elif cropped:
            img.convert("RGB").save(dst)
        else:
            shutil.copyfile(src, dst)
    print(f"{n} kare -> {args.out} · yazı {first}. kareden itibaren: {line1} / {line2}")


if __name__ == "__main__":
    main()
