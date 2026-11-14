# Validation files

| File | What | Status |
|---|---|---|
| `avgvisib_comparison.md`, `.json` | 54 package points against NASA's AVGVISIB maps, 18.6 years hourly, DE440; 0 m and 2 m observer on the 20 m DEM; DEM-resolution diagnostic appended | **current** (`scripts/validate_avgvisib.py`, `scripts/diag_resolution.py`) |
| `avgvisib_resolution_diagnostic.json` | the same 0 m comparison with the DEM block-averaged to the map's resolution | **current** |
| `pgda_comparison.json`, `.png` | first comparison (12 Nov): the nine sample points only, DE421, 0 m and 2 m | superseded; kept as a record |

How to read them: the method agrees with NASA's maps to about 2 points (mean absolute difference 2.0 Sun, 1.6 Earth)
when the conditions match (observer on the surface, terrain data at the map's 60 m / 120 m resolution). The numbers the
app shows use the 20 m terrain data and a 2 m observer and therefore differ from the maps (3.6 Sun, 1.9 Earth on average;
6.0 and 7.4 for a 0 m observer on the 20 m data). The old statement "mean difference 2.4 points (Sun), 4.4 (Earth)" came
from `pgda_comparison.json`: nine sample points, 0 m observer. It must not be quoted next to the app's 2 m numbers.
