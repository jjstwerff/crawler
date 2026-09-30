# geometry-pin.md — I-GEO worked instance (S0)

**Status: PINNED ✓ (2026-06-15)** — `python3 ortler_import.py geo` → exit 0.

The exact-invariant the design protocol says to *recover* before fetching: cell ↔ lat/lon
must round-trip exactly with correct odd-r parity, and the fetcher must share the renderer's
geometry. Achieved by consulting `overland_blueprint.Overland.center()` as the **single
source** (no re-stated odd-r formula in `ortler_import.py`).

## Construction

- Home cell = grid center `(20,20)` ≙ the Ortler summit `46.5089 N, 10.5446 E`.
- `cell_to_latlon`: `(c,r) → center(c,r)` world-metres → offset from home → equirectangular
  (row increases southward). `M_PER_DEG_LAT=111320`, `M_PER_DEG_LON=111320·cos(46.5089°)`.
- `latlon_to_cell`: invert to world, then `r=round(wy/VS)`, `c=round(wx/HW − ½·(r&1))` —
  the **same** odd-r stagger, so the inverse is exact for cell centers.

## Verified output

```
[parity] odd-row x-shift = 750.000 m (want 750.000); even-row align = 0.000 (want 0);
         row pitch = 1299.038 (want 1299.038)  -> OK
[round-trip even-row] (10,10) -> 46.625594,10.348816 -> (10, 10)
[round-trip odd-row] (11,11) -> 46.613925,10.378184 -> (11, 11)
[round-trip] mismatches over 1600 cells = 0  -> OK
[home] cell (20,20) -> 46.508900,10.544600; summit -> (20, 20)  -> OK
[corners] (km from summit):
   ( 0, 0) -> 46.74229,10.15303    39.7 km
   (39, 0) -> 46.74229,10.91659    38.6 km
   ( 0,39) -> 46.28718,10.16282    38.3 km
   (39,39) -> 46.28718,10.92638    38.3 km
[bbox] lat 46.2872..46.7423   lon 10.1530..10.9264
```

## Reality check (sanity, not a gate)

bbox lat 46.287–46.742, lon 10.153–10.926 — a ~60 km window over the Ortler Alps: Stelvio
pass (~10.45 E) inside the west, the Vinschgau/Adige to the north (~46.6–46.7 N), extending
east toward Laas/Meran (~10.9 E). The summit sits one cell west of dead-center (col 20 of
0..39); acceptable, revisit if 80×80.

## Gate

Parity exact · 0 round-trip mismatches · home↔summit exact · corners bracket the region →
**S1 (elevation fetch) is unblocked.**
