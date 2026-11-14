"""Plot the candidate regions over a LOLA hillshade (sanity check for coordinates).

    python scripts/plot_regions.py
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lunar_nav.config import DATA_DIR, ROOT, load_regions
from lunar_nav.dem import read_layer
from lunar_nav.geo import latlon_to_ps

HALF = 200_000.0  # m around the pole


def hillshade(z, res, azimuth=45.0, altitude=30.0):
    gy, gx = np.gradient(z, res)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(azimuth), np.radians(altitude)
    return np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)


def main():
    layer = read_layer(DATA_DIR / "raw" / "LDEM_80S_80MPP_ADJ.TIF", (-HALF, -HALF, HALF, HALF))
    z = layer.height[::2, ::2]
    left, bottom, right, top = layer.bounds

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(hillshade(np.nan_to_num(z, nan=np.nanmean(z)), layer.res * 2), cmap="gray",
              extent=(left / 1e3, right / 1e3, bottom / 1e3, top / 1e3))
    seen = set()
    for r in load_regions():
        x, y = latlon_to_ps(r["lat"], r["lon"])
        ax.plot(x / 1e3, y / 1e3, "o", ms=7, mfc="none", mec="#ffb000", mew=2)
        if (r["lat"], r["lon"]) not in seen:
            same = [q["name"] for q in load_regions() if (q["lat"], q["lon"]) == (r["lat"], r["lon"])]
            ax.annotate(" / ".join(same), (x / 1e3, y / 1e3), xytext=(6, 6), textcoords="offset points",
                        color="#ffb000", fontsize=9, weight="bold")
            seen.add((r["lat"], r["lon"]))
    ax.plot(0, 0, "+", color="cyan", ms=12)
    ax.set_xlabel("x (km, polar stereographic)")
    ax.set_ylabel("y (km)")
    ax.set_title("Artemis III candidate regions (anchor feature centres, PROVISIONAL)\n"
                 "over LOLA 80 m/px hillshade (Barker et al. 2023)")
    out = ROOT / "docs" / "img" / "regions_overview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
