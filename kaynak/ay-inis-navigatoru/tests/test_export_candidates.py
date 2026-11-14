import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_candidates import balanced_score, max_abs_diff, pixel_value, regions_to_run, snap_out, sub_layer  # noqa: E402
from lunar_nav.dem import DemLayer  # noqa: E402

ORDER = ["a", "b", "c", "d"]


def test_regions_to_run_all_only_and_missing():
    assert regions_to_run(ORDER, set(), set(), False) == ORDER
    assert regions_to_run(ORDER, {"a", "b"}, set(), False) == ORDER  # a plain run recomputes everything
    assert regions_to_run(ORDER, {"a", "c"}, set(), True) == ["b", "d"]  # resume after a stopped run
    assert regions_to_run(ORDER, {"a"}, {"d", "a"}, True) == ["a", "d"]  # --only wins, file order kept
    assert regions_to_run(ORDER, set(ORDER), set(), True) == []


def test_balanced_score_matches_ui_formula():
    m = {"terrain": {"sun_energy_pct": 65.4, "longest_dark_days": 14.3}, "terrain_antenna_1deg": {"earth_pct": 74.3}}
    assert balanced_score(m) == pytest.approx((65.4 + 74.3 + (100 - 14.3 / 30 * 100)) / 3)
    m["terrain"]["longest_dark_days"] = 194.5  # capped: 30 days or more scores zero
    assert balanced_score(m) == pytest.approx((65.4 + 74.3 + 0.0) / 3)


def test_pixel_value_reads_the_containing_pixel():
    # 3x2 map with 60 m pixels, top-left corner at (600, 1200)
    layer = DemLayer(np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], np.float32), left=600.0, top=1200.0, res=60.0)
    assert pixel_value(layer, 601.0, 1199.0) == 1.0
    assert pixel_value(layer, 659.0, 1141.0) == 1.0  # still the first pixel: no interpolation
    assert pixel_value(layer, 661.0, 1139.0) == 5.0
    assert list(pixel_value(layer, np.array([779.0, 610.0]), np.array([1081.0, 1100.0]))) == [6.0, 4.0]


def test_snap_out_and_sub_layer():
    assert snap_out((-10.0, 5.0, 61.0, 119.0), 60.0) == (-60.0, 0.0, 120.0, 120.0)
    layer = DemLayer(np.arange(100, dtype=np.float32).reshape(10, 10), left=0.0, top=200.0, res=20.0)
    sub = sub_layer(layer, layer.height, (40.0, 100.0, 100.0, 160.0))
    assert sub.height.shape == (3, 3) and sub.height[0, 0] == 22.0
    assert sub.bounds == (40.0, 100.0, 100.0, 160.0)


def test_max_abs_diff_walks_nested_metrics():
    a = {"terrain": {"x": 1.0, "y": 2.0}, "m": 0.5}
    b = {"terrain": {"x": 1.0, "y": 2.25}, "m": 0.4}
    assert max_abs_diff(a, b) == pytest.approx(0.25)


def test_ring_points_distance_and_direction():
    from export_sensitivity import ring_points
    from lunar_nav.geo import haversine

    lat, lon = -86.0, 2.0
    pts = ring_points(lat, lon, 300.0, 8)
    assert [a for a, _, _ in pts] == [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
    for _, p, q in pts:
        assert haversine(lat, lon, p, q) == pytest.approx(300.0, abs=0.01)
    assert pts[0][1] > lat and pts[4][1] < lat  # az 0 = north (away from the south pole), az 180 = south
    assert pts[2][2] > lon and pts[6][2] < lon  # az 90 = east


def test_ring_summary_takes_the_bad_end_of_each_metric():
    from export_sensitivity import summarise

    offsets = [
        {"sun_energy_pct": 60.0, "earth_1deg_pct": 80.0, "longest_dark_days": 12.0, "score": 66.0, "flat": True},
        {"sun_energy_pct": 40.0, "earth_1deg_pct": 85.0, "longest_dark_days": 20.0, "score": 52.0, "flat": False},
        {"sun_energy_pct": 55.0, "earth_1deg_pct": 70.0, "longest_dark_days": 14.0, "score": 59.0, "flat": True},
    ]
    s = summarise(offsets)
    assert s["worst"] == {"sun_energy_pct": 40.0, "earth_1deg_pct": 70.0, "longest_dark_days": 20.0, "score": 52.0}
    assert s["median"]["sun_energy_pct"] == 55.0 and s["median"]["longest_dark_days"] == 14.0
    assert s["steep"] == 1 and s["n"] == 3
