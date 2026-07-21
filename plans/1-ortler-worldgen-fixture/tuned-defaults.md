# tuned-defaults.md — data-derived terrain-transition values (realistic fantasy defaults)

plan #1 goal 3: read the elevations/slopes where terrain types actually change inside a real
range (the Ortler) off the data, so they become realistic world-generation defaults — not
hand-guessed. Source: `ortler_stats.py` on `data/ortler_hexes.npz` (real OSM class + EU-DEM).

## Derived transition values (2026-06-15)

| Band | Elevation | Basis |
|------|-----------|-------|
| valley / settled (farmland, orchard) | < ~1100 m | orchard p50 901 m, farmland p50 968 m |
| montane **forest** | ~1100 – **2150 m** | wood dominant 900–2100 m, wood p90 = 2132 m |
| **alpine meadow** (grass) | ~2150 – **2500 m** | grass dominant 2300–2499 m, grass p50 2316 m |
| **scree** | ~2500 – **2800 m** | scree dominant 2500–2799 m, scree p50 2664 m |
| **bare rock** | ~2800 – **3100 m** | rock dominant 2800–3099 m, rock p50 2818 m |
| **snow / glacier** | ≥ **3100 m** | glacier appears 3100 m+, glacier p10 2970 / p50 3178 m |

**→ realistic real-metre defaults:** `TREELINE = 2150`, `ALPINE_TOP = 2500`,
`ROCK = 2800`, `SNOWLINE = 3100` (vs the engine's compressed `TREEL=520`/`SNOWL=880`).

## Key finding — slope is useless at 1.5 km (cliffs need the LOD)

Per-class slope.p50 is **17–22°** for *every* class; rock/scree only reach p90 = **27°**.
A 1.5 km hex averages real cliff faces (tens of metres wide) to a gentle ramp, so:

- **At 1.5 km, terrain type is an ELEVATION function, not slope.** Tune the bands by height;
  don't expect slope to separate scree/rock/cliff here.
- **`K_FACE` / cliffs are not resolvable at 1.5 km** — this is the concrete case for the
  recursive **1.5 m LOD** (find cliff faces + real channels in the interesting triangles).

## Caveat

OSM "none" coverage is 24–78% per band (bare rock / ice often untagged at altitude), so the
dominant-class signal is noisy but the band ordering + crossovers are clear. Re-derive on
80×80 / a second range to confirm the values generalize before locking fantasy defaults.

## Next

Apply these as the model's real-metre bands (fixes gap-analysis F1), re-render B, compare to A.
