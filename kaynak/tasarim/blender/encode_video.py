"""PNG karelerini H.264 MP4 yapar (Blender'ın kendi video düzenleyicisiyle; ayrıca ffmpeg gerekmez).

    blender -b -P encode_video.py -- --frames D:/kareler_yazili --out malapert_acilis.mp4
"""

import argparse
import sys
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--frames", type=Path, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--fps", type=int, default=30)
args = p.parse_args(argv)

files = sorted(args.frames.glob("f_*.png"))
if not files:
    raise SystemExit("kare yok: " + str(args.frames))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
img = bpy.data.images.load(str(files[0]))
w, h = img.size
r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = w, h, 100, args.fps
scene.frame_start, scene.frame_end = 1, len(files)

se = scene.sequence_editor_create()
strips = se.strips if hasattr(se, "strips") else se.sequences  # 4.4'te ad değişti
strip = strips.new_image(name="kareler", filepath=str(files[0]), channel=1, frame_start=1)
for f in files[1:]:
    strip.elements.append(f.name)

# kareler zaten görüntü dönüşümünden geçti; ikinci kez uygulanmasın
scene.view_settings.view_transform = "Standard"
if hasattr(r.image_settings, "media_type"):  # 5.0+
    r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"
r.ffmpeg.codec = "H264"
r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.ffmpeg_preset = "GOOD"
r.ffmpeg.gopsize = args.fps
r.ffmpeg.audio_codec = "NONE"
r.use_file_extension = False
r.filepath = str(args.out)
args.out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.render.render(animation=True)
print("yazıldı:", args.out, "·", len(files), "kare ·", w, "x", h)
