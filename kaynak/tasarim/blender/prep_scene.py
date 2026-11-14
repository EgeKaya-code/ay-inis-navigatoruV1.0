"""Blender sahnesi için veri hazırlığı (Blender'ın Python'unda rasterio yok; bunu venv Python'u çalıştırır).

    C:\\Users\\umutc\\.venvs\\ay-inis-navigatoru\\Scripts\\python prep_scene.py [--site malapert_massif] [--out work]

Yazdıkları (--out klasörüne):
  core.npy, near.npy, mid.npy, far.npy
                     noktanın çevresinde yerel doğu/kuzey ızgarasında yükseklikler (float32, m).
                     terrain.bin ile aynı kural: 0. satır kuzey, 0. sütun batı, nokta merkezde,
                     z = LOLA yüksekliği - noktanın zemini - d^2 / 2R (Ay eğriliği).
                     near ve core: terrain.bin'in kaynağı olan 20 m DEM, kübik ara değerle 10 m'ye (±10 km)
                     ve 2 m'ye (±600 m) inceltilmiş. Ara değer yeni ayrıntı eklemez, yalnız yüzeyi pürüzsüz
                     örnekler. Neden: 1° yükseklikteki Güneş'te 40 m'lik (terrain.bin) ve 20 m'lik düz yüzler
                     gölge sınırında üçgen üçgen sahte gölge ve ızgara deseni verdi.
  scene.json         seçilen an (Güneş/Dünya açıları), ızgara ölçüleri, dosya yolları
  horizon_check.json bu ağlardan 2 m gözle hesaplanan ufuk ile horizon.json'ın farkı
Hiçbir şey uydurulmaz: yükseklikler LDEM_80S_80MPP_ADJ.TIF'ten, açılar series_2027.json'dan gelir.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from lunar_nav.config import DATA_DIR
from lunar_nav.dem import near_crop, read_layer
from lunar_nav.geo import R_MOON, latlon_to_ps

HERE = Path(__file__).resolve().parent
VERI = HERE.parent / "veri"
FAR_DEM = DATA_DIR / "raw" / "LDEM_80S_80MPP_ADJ.TIF"
CROP_HALF_M = 10500.0  # export_proto.py ile aynı kırpıntı (önbellekte hazır)
CORE = (600.0, 2.0)      # yarı kenar, aralık (m); 20 m DEM'den kübik ara değer
NEAR = (10080.0, 10.0)   # 20 m DEM'den kübik ara değer; kenarı 240 m'lik ağın çizgilerine denk gelir
BLEND_M = {"core": 40.0, "near": 480.0, "mid": 1200.0}  # iç ağın kenarında dış ağa yumuşak geçiş bandı
MID = (60000.0, 240.0)
FAR = (150000.0, 600.0)  # horizon.json'daki en uzak ufuk noktası ~129 km
EYE_M = 2.0
SUN_DIAMETER_DEG, EARTH_DIAMETER_DEG = 0.53, 1.9
# an seçme kuralı: Güneş tam görünür ve alçak, Dünya açıkta, ikisi arasında kamera dönüşüne yetecek açı
SUN_ALT_RANGE, SUN_ALT_TARGET = (0.5, 1.5), 1.0
EARTH_MIN_MARGIN_DEG = 1.0
SUN_EARTH_AZ_RANGE = (60.0, 100.0)


def local_grid(layer, lat, lon, ground, half, res, order=1):
    """export_proto.local_tile ile aynı yerel ızgara, başka boyutta. order=3: kübik ara değer."""
    x0, y0 = latlon_to_ps(lat, lon)
    lam = np.radians(lon)
    north = np.array([np.sin(lam), np.cos(lam)])
    east = np.array([np.cos(lam), -np.sin(lam)])
    n = int(round(2 * half / res)) + 1
    s = np.linspace(-half, half, n)
    e, nn = np.meshgrid(s, s[::-1])
    x, y = x0 + e * east[0] + nn * north[0], y0 + e * east[1] + nn * north[1]
    if order == 1:
        h = layer.sample(x, y)
    else:
        col, row = (x - layer.left) / layer.res - 0.5, (layer.top - y) / layer.res - 0.5
        h = map_coordinates(layer.height, [row, col], order=order, mode="nearest")
    return (h - ground - (e ** 2 + nn ** 2) / (2.0 * R_MOON)).astype(np.float32)


def stitch(inner, half_i, res_i, outer, half_o, res_o, band):
    """İç ağın kenar bandını dış ağın yüzeyine yaklaştırır; tam kenarda ikisi aynı yüzeydir.
    Yoksa iki ağ arasında birkaç metrelik basamak kalır ve 1° yükseklikteki Güneş'te o basamak
    yüzlerce metrelik sahte gölge düşürür."""
    n = inner.shape[0]
    s = np.linspace(-half_i, half_i, n)
    e, nn = np.meshgrid(s, s[::-1])
    on_outer = map_coordinates(outer, [(half_o - nn) / res_o, (e + half_o) / res_o], order=1, mode="nearest")
    k = np.clip(1.0 - (half_i - np.maximum(np.abs(e), np.abs(nn))) / band, 0.0, 1.0)
    k = k * k * (3.0 - 2.0 * k)
    return (inner * (1.0 - k) + on_outer * k).astype(np.float32)


def pick_hour(series):
    g = lambda k: np.array(series[k])
    sun_alt, sun_az, frac = g("sun_alt_deg"), g("sun_az_deg"), g("sun_visible_fraction")
    earth_az, margin = g("earth_az_deg"), g("earth_margin_deg")
    sep = np.abs((sun_az - earth_az + 180.0) % 360.0 - 180.0)
    ok = ((frac >= 0.999) & (margin >= EARTH_MIN_MARGIN_DEG)
          & (sun_alt >= SUN_ALT_RANGE[0]) & (sun_alt <= SUN_ALT_RANGE[1])
          & (sep >= SUN_EARTH_AZ_RANGE[0]) & (sep <= SUN_EARTH_AZ_RANGE[1]))
    idx = np.flatnonzero(ok)
    if not idx.size:
        raise SystemExit("kurala uyan saat yok")
    return int(idx[np.argmin(np.abs(sun_alt[idx] - SUN_ALT_TARGET))]), int(idx.size)  # eşitlikte en erken saat


def mesh_horizon(grids, az_deg, eye=EYE_M):
    """Ağların (iç içe, en ince önce) 2 m gözden görünen ufku: her azimutta ışın boyunca en büyük yükseklik açısı.
    grids: [(z, half, res, d_min, d_max)]; z çift doğrusal okunur, yani Blender'daki üçgen yüzeye çok yakın."""
    az = np.radians(az_deg)[:, None]
    best = np.full(az_deg.size, -np.inf)
    best_d = np.zeros(az_deg.size)
    for z, half, res, d0, d1 in grids:
        d = np.arange(max(d0, res / 4), d1, res / 4)[None, :]
        col = (d * np.sin(az) + half) / res
        row = (half - d * np.cos(az)) / res
        h = map_coordinates(z, [row, col], order=1, mode="constant", cval=np.nan)
        ang = np.degrees(np.arctan2(h - eye, d))
        ang = np.where(np.isnan(ang), -np.inf, ang)
        j = np.argmax(ang, axis=1)
        a = ang[np.arange(az_deg.size), j]
        better = a > best
        best, best_d = np.where(better, a, best), np.where(better, d[0, j], best_d)
    return best, best_d


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site", default="malapert_massif")
    p.add_argument("--out", type=Path, default=HERE / "work")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    site = next(s for s in json.loads((VERI / "sites.json").read_text(encoding="utf-8"))["sites"] if s["id"] == args.site)
    site_dir = VERI / "sites" / args.site
    lat, lon = site["lat"], site["lon"]
    near = near_crop(lat, lon, CROP_HALF_M)
    ground = float(near.sample(*latlon_to_ps(lat, lon)))
    assert abs(ground - site["ground_height_m"]) < 1e-6
    far_dem = read_layer(FAR_DEM, name="far_80m")

    assert np.isfinite(near.height).all(), "20 m kırpıntıda boşluk var: kübik ara değer için doldurulmalı"
    core = local_grid(near, lat, lon, ground, *CORE, order=3)
    near20 = local_grid(near, lat, lon, ground, *NEAR, order=3)
    mid = local_grid(far_dem, lat, lon, ground, *MID)
    far = local_grid(far_dem, lat, lon, ground, *FAR)
    assert not np.isnan(mid).any() and not np.isnan(far).any()
    mid = stitch(mid, MID[0], MID[1], far, FAR[0], FAR[1], BLEND_M["mid"])
    near_raw = near20
    near20 = stitch(near20, NEAR[0], NEAR[1], mid, MID[0], MID[1], BLEND_M["near"])
    core = stitch(core, CORE[0], CORE[1], near20, NEAR[0], NEAR[1], BLEND_M["core"])
    for name, grid in (("core", core), ("near", near20), ("mid", mid), ("far", far)):
        np.save(args.out / f"{name}.npy", grid)

    series = json.loads((site_dir / "series_2027.json").read_text())
    hour, n_ok = pick_hour(series)
    when = dt.datetime.fromisoformat(series["start_utc"].replace("Z", "+00:00")) + dt.timedelta(hours=hour * series["step_hours"])

    # terrain.bin ile aynı yüzey mi: 40 m'lik düğümlerde near.npy ile fark (kübik ile çift doğrusal ara değerin farkı)
    tmeta = json.loads((site_dir / "terrain.json").read_text())
    tile = np.fromfile(site_dir / "terrain.bin", dtype="<f4").reshape(tmeta["height"], tmeta["width"])
    # terrain.bin ±10 km; near ±10,08 km (40 m'lik düğümler 8 hücre içeriden başlar)
    d = near_raw[8:-8:4, 8:-8:4] - tile
    tile_diff, tile_rms = float(np.abs(d).max()), float(np.sqrt(np.mean(d ** 2)))
    stitch_shift = float(np.abs(near20 - near_raw).max())

    # ufuk kontrolü: sahnedeki dört ağ (2 / 10 / 240 / 600 m) ile horizon.json (20 m + 80 m, tam küresel geometri)
    hz = json.loads((site_dir / "horizon.json").read_text())
    az = np.arange(0.0, 360.0, 1.0)
    ours, ours_d = mesh_horizon([(core, CORE[0], CORE[1], 0.0, CORE[0]),
                                 (near20, NEAR[0], NEAR[1], CORE[0], NEAR[0]),
                                 (mid, MID[0], MID[1], NEAR[0], MID[0]),
                                 (far, FAR[0], FAR[1], MID[0], FAR[0])], az)
    step = int(round(1.0 / hz["azimuth_step_deg"]))
    ref, ref_d = np.array(hz["elevation_deg"])[::step], np.array(hz["distance_km"])[::step]
    diff = ours - ref
    far_field = ref_d > 2.0  # ufku uzak arazinin belirlediği yönler
    check = {
        "what": "horizon elevation from the scene meshes (eye 2 m) minus horizon.json, per 1 deg azimuth",
        "near_vs_terrain_bin_m": {"max_abs": tile_diff, "rms": tile_rms},
        "near_edge_blend_max_shift_m": stitch_shift,
        "all": {"mean": float(diff.mean()), "mean_abs": float(np.abs(diff).mean()), "max_abs": float(np.abs(diff).max())},
        "horizon_beyond_2km": {"n_azimuths": int(far_field.sum()), "mean": float(diff[far_field].mean()),
                               "mean_abs": float(np.abs(diff[far_field]).mean()),
                               "max_abs": float(np.abs(diff[far_field]).max())},
        "horizon_within_2km": {"n_azimuths": int((~far_field).sum()), "mean": float(diff[~far_field].mean()),
                               "mean_abs": float(np.abs(diff[~far_field]).mean()),
                               "max_abs": float(np.abs(diff[~far_field]).max())},
        "azimuth_deg": az.tolist(), "scene_deg": np.round(ours, 3).tolist(), "horizon_json_deg": ref.tolist(),
        "scene_distance_km": np.round(ours_d / 1e3, 2).tolist(), "horizon_json_distance_km": ref_d.tolist(),
    }
    (args.out / "horizon_check.json").write_text(json.dumps(check))
    sun_az = series["sun_az_deg"][hour]
    i_sun = int(round(sun_az)) % 360

    scene = {
        "site": args.site, "region": site["region"], "lat": lat, "lon": lon, "ground_height_m": ground,
        "axes": "x = east, y = north, z = up (three.js sahnesinde x = doğu, y = yukarı, z = -kuzey; aynı yön kuralı)",
        "hour_index": hour, "utc": when.strftime("%Y-%m-%d %H:%M"), "hours_matching_rule": n_ok,
        "rule": f"sun_visible_fraction >= 0.999, earth_margin >= {EARTH_MIN_MARGIN_DEG} deg, sun_alt in {SUN_ALT_RANGE}, "
                f"Sun-Earth azimuth separation in {SUN_EARTH_AZ_RANGE} deg, sun_alt closest to {SUN_ALT_TARGET}; first on ties",
        "sun_alt_deg": series["sun_alt_deg"][hour], "sun_az_deg": sun_az,
        "sun_visible_fraction": series["sun_visible_fraction"][hour],
        "earth_alt_deg": series["earth_alt_deg"][hour], "earth_az_deg": series["earth_az_deg"][hour],
        "earth_margin_deg": series["earth_margin_deg"][hour],
        "earth_illuminated_fraction": series["earth_illuminated_fraction"][hour],
        "sun_diameter_deg": SUN_DIAMETER_DEG, "earth_diameter_deg": EARTH_DIAMETER_DEG, "eye_height_m": EYE_M,
        "horizon_at_sun_az_deg": {"scene": float(ours[i_sun]), "horizon_json": float(ref[i_sun])},
        "core": {"npy": str(args.out / "core.npy"), "n": int(core.shape[0]), "half_m": CORE[0], "res_m": CORE[1]},
        "near": {"npy": str(args.out / "near.npy"), "n": int(near20.shape[0]), "half_m": NEAR[0], "res_m": NEAR[1]},
        "mid": {"npy": str(args.out / "mid.npy"), "n": int(mid.shape[0]), "half_m": MID[0], "res_m": MID[1]},
        "far": {"npy": str(args.out / "far.npy"), "n": int(far.shape[0]), "half_m": FAR[0], "res_m": FAR[1]},
        "sources": {"core": "LOLA 20 m DEM, kübik ara değerle 2 m (yeni ayrıntı yok)",
                    "near": "LOLA 20 m DEM, kübik ara değerle 10 m (terrain.bin'in kaynağı)",
                    "mid_far": "LDEM_80S_80MPP_ADJ.TIF (LOLA 80 m DEM)", "angles": "series_2027.json (DE421, saatlik)"},
    }
    (args.out / "scene.json").write_text(json.dumps(scene, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{site['region']}: {scene['utc']} UTC (saat {hour}, kurala uyan {n_ok} saat)")
    print(f"  Güneş alt {scene['sun_alt_deg']:.2f} az {scene['sun_az_deg']:.1f} · Dünya alt {scene['earth_alt_deg']:.2f} "
          f"az {scene['earth_az_deg']:.1f} · evre {scene['earth_illuminated_fraction']:.2f}")
    print(f"  core {core.shape} · near {near20.shape} (terrain.bin ile fark: en büyük {tile_diff:.2f} m, RMS {tile_rms:.3f} m; kenar geçişinde en çok {stitch_shift:.1f} m kaydı) · "
          f"mid {mid.shape}, NaN {np.isnan(mid).mean() * 100:.1f}% · far {far.shape}, NaN {np.isnan(far).mean() * 100:.1f}%")
    for k in ("all", "horizon_beyond_2km", "horizon_within_2km"):
        c = check[k]
        print(f"  ufuk farkı ({k}): ort {c['mean']:+.3f}°, ort |fark| {c['mean_abs']:.3f}°, en çok {c['max_abs']:.3f}°")


if __name__ == "__main__":
    main()
