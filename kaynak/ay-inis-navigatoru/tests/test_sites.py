import numpy as np

from lunar_nav.dem import DemLayer
from lunar_nav.sites import highest_flat_point, inside_polygon, pick_spaced, pixel_centres


def test_pick_spaced_keeps_best_and_respects_spacing():
    # a row of points 100 m apart, score falling off from the middle
    x = np.arange(21) * 100.0
    y = np.zeros(21)
    score = 100.0 - np.abs(x - 1000.0) / 10.0
    idx = pick_spaced(x, y, score, n=3, min_dist_m=300.0)
    assert idx[0] == 10  # the best point always survives
    d = np.abs(x[idx][:, None] - x[idx][None, :])
    assert d[~np.eye(3, dtype=bool)].min() >= 300.0
    assert list(score[idx]) == sorted(score[idx], reverse=True)
    assert set(idx[1:]) == {7, 13}


def test_pick_spaced_tiebreak_nan_and_short_supply():
    x = np.array([0.0, 10.0, 5000.0, 9000.0])
    y = np.zeros(4)
    score = np.array([50.0, 50.0, np.nan, 40.0])
    idx = pick_spaced(x, y, score, n=5, min_dist_m=300.0, tiebreak=[3.0, 1.0, 0.0, 0.0])
    assert list(idx) == [1, 3]  # flatter of the tied pair, NaN skipped, fewer than n available


def test_inside_polygon_selects_only_interior_pixels():
    layer = DemLayer(np.zeros((10, 10), np.float32), left=0.0, top=1000.0, res=100.0)
    x, y = pixel_centres(layer)
    # a diamond around (500, 500): rotated like the USGS regions, so a bounding box would be wrong
    # (half-diagonal 390 m, so no pixel centre sits exactly on an edge)
    ring = [(500, 890), (890, 500), (500, 110), (110, 500), (500, 890)]
    inside = inside_polygon(x, y, ring)
    assert inside.shape == (10, 10)
    assert inside[4, 4] and inside[5, 5]
    assert not inside[0, 0] and not inside[9, 9] and not inside[1, 8]
    assert np.array_equal(inside, np.abs(x - 500) + np.abs(y - 500) < 390)


def test_highest_flat_point_ignores_steep_peak():
    h = np.zeros((40, 40), np.float32)
    h[10, 10] = 500.0  # a spike: highest, but steep
    h[25:32, 25:32] = 50.0  # a mesa: flat on top
    layer = DemLayer(h, left=0.0, top=800.0, res=20.0)
    lat, lon, height, slope = highest_flat_point(layer, 400.0, 400.0, 1000.0, 5.0)
    assert height == 50.0 and slope == 0.0
