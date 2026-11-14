"""Kaydedilmiş Malapert sahnesini pencerede açınca: kamera görünümüne geç, Dünya'nın göründüğü kareye git.

    blender malapert_sahne.blend -P sahne_goster.py -- [--frame 255] [--rendered]

Sahne dosyası şöyle üretilir (render almaz, kareler zaten varsa atlar):
    blender -b -P malapert_render.py -- --frames-dir <kareler> --frames 1 --save-blend malapert_sahne.blend <diğer ayarlar>
"""

import argparse
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--frame", type=int, default=255)
p.add_argument("--rendered", action="store_true", help="görünümü Cycles önizlemesiyle aç (GPU)")
args = p.parse_args(argv)


def show():
    scene = bpy.context.scene
    scene.frame_set(args.frame)
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != "VIEW_3D":
                continue
            space = area.spaces.active
            space.clip_start, space.clip_end = 1.0, 4.0e6  # sahne 300 km genişliğinde
            space.region_3d.view_perspective = "CAMERA"
            if args.rendered:
                space.shading.type = "RENDERED"
    return None  # zamanlayıcı bir kez çalışsın


# pencere hazır olduktan sonra çalışsın
bpy.app.timers.register(show, first_interval=0.5)
