"""Malapert açılış sahnesi: gerçek LOLA arazisi + gerçek Güneş/Dünya konumu. Arka planda çalışır:

    blender -b -P malapert_render.py -- --work work --frames-dir D:/kareler --engine cycles --res 1920x1080

Girdi: prep_scene.py'nin yazdığı work/scene.json ve dört yükseklik ızgarası (core/near/mid/far.npy).
Çıktı: --frames-dir içine PNG kareler (f_0001.png …). Var olan kare yeniden çizilmez (yarıda kalırsa devam eder).

Eksenler: x = doğu, y = kuzey, z = yukarı; azimut kuzeyden doğuya. three.js sahnesiyle (40-scene.js:
x = doğu, y = yukarı, z = -kuzey) aynı kural, yalnız Blender'da yukarı ekseni z.
Uydurma arazi yok: dört ağ da LOLA yüksekliklerinden. Gökyüzü siyah, atmosfer/sis yok.
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

FPS, SECONDS = 30, 15
N_FRAMES = FPS * SECONDS
REGOLITH_HEX = "97938c"
SUN_DISTANCE_M, EARTH_DISTANCE_M = 1.5e6, 1.0e6  # yalnız çizim için; açısal çaplar gerçek
# kamera: süzülüş 0-10 sn, Güneş'e dönüş 10-13,5 sn, sonra neredeyse sabit
T_GLIDE, T_TURN = 10.0, 13.5
START_BACK_M, START_HEIGHT_M = 6000.0, 3000.0


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--work", type=Path, default=here / "work")
    p.add_argument("--frames-dir", type=Path, required=True)
    p.add_argument("--engine", choices=["eevee", "cycles"], default="eevee")
    p.add_argument("--res", default="960x540")
    p.add_argument("--samples", type=int, default=48)
    p.add_argument("--frames", default="", help="yalnız bu kareler (ör. 1,150,300,450); boşsa hepsi")
    p.add_argument("--sun-strength", type=float, default=6.0)
    p.add_argument("--exposure", type=float, default=0.0, help="süzülüş boyunca pozlama (EV)")
    p.add_argument("--exposure-end", type=float, default=None, help="Güneş'e dönünce pozlama (EV); boşsa sabit")
    p.add_argument("--approach-az", type=float, default=None, help="süzülüşte bakış azimutu; boşsa Dünya yönü")
    p.add_argument("--glare", type=float, default=0.0, help="Güneş çevresinde mercek parlaması (0 = yok)")
    p.add_argument("--bump", type=float, default=0.0, help="yordamsal ince doku şiddeti (0 = yok)")
    p.add_argument("--bump-scale", type=float, default=2.5, help="doku sıklığı (1/m)")
    p.add_argument("--glare-type", default="Bloom")
    p.add_argument("--glare-size", type=float, default=0.2)
    p.add_argument("--overscan", type=float, default=1.0,
                   help="kadrajın dışını da çiz (ör. 1.5): Güneş kadraja girmeden parlaması görünsün; "
                        "caption_frames.py ortadaki --res kadar bölümü keser")
    p.add_argument("--terminator", default="0.1,0.0", help="Cycles gölge sınırı düzeltmesi: geometri,gölgeleme ofseti")
    p.add_argument("--save-blend", type=Path, default=None)
    return p.parse_args(argv)


def srgb_to_linear(hexcode):
    out = []
    for i in (0, 2, 4):
        c = int(hexcode[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def direction(alt_deg, az_deg):
    """Yerel yön vektörü: azimut kuzeyden doğuya, yükseklik yataydan."""
    alt, az = math.radians(alt_deg), math.radians(az_deg)
    return Vector((math.cos(alt) * math.sin(az), math.cos(alt) * math.cos(az), math.sin(alt)))


def grid_mesh(name, z, half, hole_half=0.0):
    """Kare yükseklik ızgarasından ağ. 0. satır kuzey, 0. sütun batı. NaN hücreler ağdan çıkarılır.
    hole_half: daha ince ağın kapladığı iç kare (kenarı bu ağın çizgilerine denk gelir); içindeki
    yüzler atılır. İnce ağın kenarı prep_scene.py'de bu ağın yüzeyine oturtuldu, basamak kalmaz."""
    n = z.shape[0]
    s = np.linspace(-half, half, n)
    x, y = np.meshgrid(s, s[::-1])
    ok = np.isfinite(z)
    inside = (np.abs(x) <= hole_half + 1e-3) & (np.abs(y) <= hole_half + 1e-3) if hole_half else np.zeros_like(ok)
    zz = np.where(ok, z, 0.0)
    idx = np.arange(n * n).reshape(n, n)
    a, b, c, d = idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]  # KB, GB, GD, KD: yukarıdan saat yönünün tersi
    keep = ok[:-1, :-1] & ok[1:, :-1] & ok[1:, 1:] & ok[:-1, 1:]
    keep &= ~(inside[:-1, :-1] & inside[1:, :-1] & inside[1:, 1:] & inside[:-1, 1:])
    faces = np.stack([a[keep], b[keep], c[keep], d[keep]], axis=1)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(n * n)
    mesh.vertices.foreach_set("co", np.stack([x, y, zz], axis=2).astype(np.float32).ravel())
    mesh.loops.add(faces.size)
    mesh.loops.foreach_set("vertex_index", faces.ravel().astype(np.int32))
    mesh.polygons.add(len(faces))
    mesh.polygons.foreach_set("loop_start", np.arange(0, faces.size, 4, dtype=np.int32))
    mesh.polygons.foreach_set("loop_total", np.full(len(faces), 4, dtype=np.int32))
    mesh.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
    mesh.update(calc_edges=True)
    mesh.validate()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def node_material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True
    except Exception:
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return mat, nt, out


def regolith_material(bump, bump_scale):
    mat, nt, out = node_material("regolit")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*srgb_to_linear(REGOLITH_HEX), 1.0)
    bsdf.inputs["Roughness"].default_value = 1.0
    for key, v in (("Specular IOR Level", 0.0), ("Specular", 0.0), ("Diffuse Roughness", 1.0)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = v
    if bump > 0:  # yalnız gölgeleme; geometri değişmez. Veri değil, sonuç notunda yazılı.
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = bump_scale  # 20 m verinin göremediği ölçekte taneler
        noise.inputs["Detail"].default_value = 3.0
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
        bmp = nt.nodes.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = bump
        bmp.inputs["Distance"].default_value = 0.05
        nt.links.new(noise.outputs["Fac"], bmp.inputs["Height"])
        nt.links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def camera_only(obj):
    """Yalnız kameraya görünsün: ışık vermesin, gölge düşürmesin."""
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
        if hasattr(obj, attr):
            setattr(obj, attr, False)


def build_sun(sc, strength):
    s = direction(sc["sun_alt_deg"], sc["sun_az_deg"])
    lamp = bpy.data.lights.new("Gunes", "SUN")
    lamp.energy = strength
    lamp.angle = math.radians(sc["sun_diameter_deg"])
    lamp.color = (1.0, 0.97, 0.92)
    obj = bpy.data.objects.new("Gunes", lamp)
    obj.rotation_euler = s.to_track_quat("Z", "Y").to_euler()  # lambanın +Z'si Güneş'e bakar, ışık -Z yönünde gider
    bpy.context.scene.collection.objects.link(obj)

    # görünen disk: doğru açısal çapta, kendisi ışık saçan daire
    r = SUN_DISTANCE_M * math.tan(math.radians(sc["sun_diameter_deg"] / 2))
    mesh = bpy.data.meshes.new("GunesDiski")
    k = 48
    ring = [(r * math.cos(2 * math.pi * i / k), r * math.sin(2 * math.pi * i / k), 0.0) for i in range(k)]
    mesh.from_pydata(ring, [], [list(range(k))])
    disc = bpy.data.objects.new("GunesDiski", mesh)
    disc.location = s * SUN_DISTANCE_M
    disc.rotation_euler = (-s).to_track_quat("Z", "Y").to_euler()
    mat, nt, out = node_material("gunes")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.96, 0.88, 1.0)
    em.inputs["Strength"].default_value = 2000.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    mesh.materials.append(mat)
    bpy.context.scene.collection.objects.link(disc)
    camera_only(disc)
    return s


def build_earth(sc):
    """Doğru yönde ve açısal çapta küre; aynı Güneş lambası aydınlatır, yani evre Güneş yönünden çıkar."""
    e = direction(sc["earth_alt_deg"], sc["earth_az_deg"])
    r = EARTH_DISTANCE_M * math.tan(math.radians(sc["earth_diameter_deg"] / 2))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=r, location=e * EARTH_DISTANCE_M)
    obj = bpy.context.active_object
    obj.name = "Dunya"
    bpy.ops.object.shade_smooth()
    mat, nt, out = node_material("dunya")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (0.10, 0.22, 0.55, 1.0)  # düz mavi: bulut/kara deseni uydurulmadı
    nt.links.new(diff.outputs["BSDF"], out.inputs["Surface"])
    obj.data.materials.append(mat)
    camera_only(obj)
    return e


def smooth(a, b, v):
    x = min(1.0, max(0.0, (v - a) / (b - a)))
    return x * x * (3 - 2 * x)


def wrap(deg):
    return (deg + 180.0) % 360.0 - 180.0


def camera_pose(t_sec, sc, approach_az=None):
    """~3 km'den noktaya süzülür (yaklaşma yönüne, sonra Dünya'ya bakarak), 2 m göz hizasında Güneş'e döner."""
    eye = sc["eye_height_m"]
    earth_az = wrap(sc["earth_az_deg"])
    a0 = earth_az if approach_az is None else earth_az + wrap(approach_az - earth_az)
    turn = wrap(sc["sun_az_deg"] - earth_az)
    u = smooth(0.0, 1.0, min(1.0, t_sec / T_GLIDE))
    back = START_BACK_M * (1.0 - u)
    height = eye + (START_HEIGHT_M - eye) * (1.0 - u) ** 1.6
    az_back = math.radians(a0 + 180.0)  # bakış yönünün tersinden yaklaş
    pos = Vector((back * math.sin(az_back), back * math.cos(az_back), height))
    pitch_site = -math.degrees(math.atan2(height, max(back, 1e-3)))
    w = smooth(0.55, 0.95, u)
    pitch = pitch_site * (1.0 - w) + 1.0 * w
    v = smooth(T_GLIDE, T_TURN, t_sec)
    drift = 1.5 * max(0.0, t_sec - T_TURN) / (SECONDS - T_TURN)  # sonda çok yavaş kayma
    yaw = a0 + (earth_az - a0) * smooth(0.45, 0.9, u)  # süzülüşün sonunda Dünya kadrajın ortasında
    yaw += (turn - math.copysign(8.0, turn)) * v + math.copysign(drift, turn)
    pitch = pitch + (1.6 - 1.0) * v
    return pos, direction(pitch, yaw)


def exposure_at(t_sec, args):
    """Kamera Güneş'e dönerken pozlama açılır (gerçek kameranın otomatik pozlaması gibi; sahne değişmez)."""
    if args.exposure_end is None:
        return args.exposure
    return args.exposure + (args.exposure_end - args.exposure) * smooth(T_GLIDE, T_TURN - 1.0, t_sec)


def add_glare(scene, amount, kind, size):
    """Parlak Güneş diskinin çevresinde mercek parlaması (yalnız görüntü işleme). Sürüm farkında sessizce vazgeçer."""
    try:
        tree = bpy.data.node_groups.new("parlama", "CompositorNodeTree")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = tree.nodes.new("CompositorNodeRLayers")
        glare = tree.nodes.new("CompositorNodeGlare")
        out = tree.nodes.new("NodeGroupOutput")
        for key, v in (("Type", kind), ("Strength", amount), ("Threshold", 4.0), ("Size", size)):
            if key in glare.inputs:
                glare.inputs[key].default_value = v
        tree.links.new(rl.outputs["Image"], glare.inputs["Image"])
        tree.links.new(glare.outputs["Image"], out.inputs["Image"])
        scene.compositing_node_group = tree
        scene.render.use_compositing = True
        print("mercek parlaması: açık,", amount)
        return glare
    except Exception as e:
        print("mercek parlaması eklenemedi, atlandı:", e)
        return None


def glare_factor(look, sc, overscan):
    """Parlama yalnız çizilen görüntüdeki Güneş'ten hesaplanır; Güneş çizilen alana girdiği karede birden
    belirmesin diye şiddet, Güneş çizilen alanın kenarından görünen kadrajın kenarına gelene kadar 0'dan 1'e çıkar."""
    off = abs(wrap(sc["sun_az_deg"] - math.degrees(math.atan2(look.x, look.y))))
    visible = math.degrees(math.atan(18.0 / 28.0))
    drawn = math.degrees(math.atan(18.0 * overscan / 28.0))
    if drawn - visible < 1.0:
        return 1.0
    return 1.0 - smooth(visible, drawn - 0.5, off)


def setup_engine(scene, args):
    r = scene.render
    w, h = (round(int(v) * args.overscan) for v in args.res.lower().split("x"))
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    r.fps = FPS
    r.film_transparent = False
    if args.engine == "cycles":
        r.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = kind
                prefs.get_devices()
                gpus = [d for d in prefs.devices if d.type == kind]
                if gpus:
                    for d in prefs.devices:
                        d.use = d.type == kind
                    scene.cycles.device = "GPU"
                    print("Cycles aygıtı:", kind, [d.name for d in gpus])
                    break
            except Exception as e:
                print("aygıt denenemedi:", kind, e)
        else:
            print("GPU bulunamadı, CPU ile")
        scene.cycles.samples = args.samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.use_denoising = True
        scene.cycles.max_bounces = 4
        scene.cycles.caustics_reflective = scene.cycles.caustics_refractive = False
        try:
            scene.cycles.denoiser = "OPTIX" if scene.cycles.device == "GPU" else "OPENIMAGEDENOISE"
        except Exception:
            pass
    else:
        for name in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
            try:
                r.engine = name
                break
            except TypeError:
                continue
        for attr, v in (("taa_render_samples", args.samples), ("use_shadows", True), ("use_raytracing", True)):
            if hasattr(scene.eevee, attr):
                setattr(scene.eevee, attr, v)
    for transform in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = transform
            break
        except TypeError:
            continue
    scene.view_settings.exposure = args.exposure
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.use_overwrite = False
    r.use_file_extension = True
    print("motor:", r.engine, "·", w, "x", h, "·", scene.view_settings.view_transform)


def main():
    args = parse_args()
    t0 = time.time()
    sc = json.loads((args.work / "scene.json").read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # arazi: 2 m (±600 m) ve 10 m (±10 km), ikisi de 20 m veriden kübik; 240 m (±60 km), 600 m (±150 km); hepsi LOLA
    core, near = np.load(sc["core"]["npy"]), np.load(sc["near"]["npy"])
    mid, far = np.load(sc["mid"]["npy"]), np.load(sc["far"]["npy"])
    mat = regolith_material(args.bump, args.bump_scale)
    for obj in (grid_mesh("cekirdek_2m", core, sc["core"]["half_m"]),
                grid_mesh("yakin_10m", near, sc["near"]["half_m"], hole_half=sc["core"]["half_m"]),
                grid_mesh("orta_240m", mid, sc["mid"]["half_m"], hole_half=sc["near"]["half_m"]),
                grid_mesh("uzak_600m", far, sc["far"]["half_m"], hole_half=sc["mid"]["half_m"])):
        obj.data.materials.append(mat)
        # alçak Güneş + kaba ağ: gölge sınırında üçgen üçgen sahte gölgeler çıkar; Cycles'ın düzeltmesi
        geo, shade = (float(v) for v in args.terminator.split(","))
        for attr, v in (("shadow_terminator_geometry_offset", geo), ("shadow_terminator_shading_offset", shade)):
            if hasattr(obj, attr):
                setattr(obj, attr, v)

    sun_dir = build_sun(sc, args.sun_strength)
    build_earth(sc)

    world = bpy.data.worlds.new("uzay")
    try:
        world.use_nodes = True
    except Exception:
        pass
    bg = world.node_tree.nodes.get("Background") if world.node_tree else None
    if bg:
        bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        bg.inputs["Strength"].default_value = 0.0
    world.color = (0.0, 0.0, 0.0)
    scene.world = world

    cam_data = bpy.data.cameras.new("kamera")
    cam_data.lens, cam_data.sensor_width = 28.0, 36.0 * args.overscan  # ortadaki bölüm aynı kadraj
    cam_data.clip_start, cam_data.clip_end = 0.5, 4.0e6
    cam = bpy.data.objects.new("kamera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, N_FRAMES
    setup_engine(scene, args)
    for f in range(1, N_FRAMES + 1):
        pos, look = camera_pose((f - 1) / FPS, sc, args.approach_az)
        cam.location = pos
        cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    glare = add_glare(scene, args.glare, args.glare_type, args.glare_size) if args.glare > 0 else None
    args.frames_dir.mkdir(parents=True, exist_ok=True)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend))
    print(f"sahne hazır: {time.time() - t0:.1f} sn · Güneş yönü {tuple(round(v, 3) for v in sun_dir)} · {sc['utc']} UTC")

    frames = [int(v) for v in args.frames.split(",") if v] or list(range(1, N_FRAMES + 1))
    t1 = time.time()
    done = 0
    for f in frames:
        path = args.frames_dir / f"f_{f:04d}.png"
        if path.exists():
            continue
        scene.frame_set(f)
        scene.view_settings.exposure = exposure_at((f - 1) / FPS, args)
        if glare and "Strength" in glare.inputs:
            look = camera_pose((f - 1) / FPS, sc, args.approach_az)[1]
            glare.inputs["Strength"].default_value = args.glare * glare_factor(look, sc, args.overscan)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        done += 1
        print(f"kare {f}: toplam {time.time() - t1:.0f} sn, kare başına {(time.time() - t1) / done:.1f} sn", flush=True)
    print(f"bitti: {done} kare, {time.time() - t1:.0f} sn")


if __name__ == "__main__":
    main()
