# Ay İniş Navigatörü · Lunar Landing Navigator

NASA Space Apps Challenge 2026. Pick a landing point and a date near the lunar
south pole and see the mission's power and communication story: when the Sun is
above the real terrain horizon, and when Earth is.

**Status: event prototype (14 November 2026). Numbers are preliminary.**

## Why real terrain

At the pole the Sun circles only a degree or two above the horizon, so a flat
horizon gives wrong answers. We compute the actual horizon of each point from
LRO/LOLA elevation data, and compare the result with NASA's published average
visibility maps (PGDA product 69): under the maps' own conditions (observer on the
surface, terrain data at the map's resolution, any part of the disc, 18.6 years,
54 points) the method agrees with them to a mean absolute difference of 2.0
percentage points for the Sun and 1.6 for Earth. The app's own numbers use the
20 m terrain data and a 2 m observer, so they differ from the maps (3.6 and 1.9
points on average). See `docs/validation/avgvisib_comparison.md`.

Terms: "sunlit time" is the share of time any part of the solar disc is above the
terrain horizon (`sun_any_pct`); the time-averaged visible fraction of the disc is
the "solar energy fraction" (`sun_energy_pct`).

## Layout

- `src/lunar_nav/` – tested Python core (projection, DEM access, horizon profiles)
- `config/assumptions.toml` – every modelling assumption, with its source
- `config/regions.toml` – the nine Artemis III candidate regions (**provisional coordinates**)
- `scripts/` – one-off runs and figures
  - `spice_check.py` – reproduce the shipped 2027 series with SPICE/DE440 and print the differences
  - `export_years.py` – more years of hourly series for the prototype (DE440, `MOON_ME`)
  - `export_heights.py` – 0 m and 10 m horizon profiles for the package points
  - `validate_avgvisib.py`, `diag_resolution.py` – comparison with NASA's AVGVISIB maps (`docs/validation/avgvisib_comparison.md`)
- `src/lunar_nav/localdata.py` – the local raw-data folder (DE440 kernels, AVGVISIB IMG/LBL, `LOLA_DEM/`); new computations read raw inputs only from there (`LUNAR_NAV_DATA` overrides the path)
- `src/lunar_nav/spice_ephem.py` – Sun/Earth vectors from the DE440 kernels with spiceypy (the older `ephemeris.py` path uses skyfield + DE421)
- `data/` – downloaded inputs, not committed (see `data/README.md`)

## Run

```
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m pytest
.venv/Scripts/python scripts/horizon_point.py --lat -85.98 --lon -1.67 --name "Mons Malapert"
```

## Data and credits

- LOLA south pole DEMs: Barker et al. 2023, PSJ 4:183, PGDA product 90
- Artemis III candidate regions: NASA (Oct 2024); George et al., LPSC 2026 (NTRS 20250011660)
- Feature coordinates: IAU/USGS Gazetteer of Planetary Nomenclature

## License

MIT
