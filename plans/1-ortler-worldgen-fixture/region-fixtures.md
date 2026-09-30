# Region fixtures — N real references in one format

> **PLANNED — not implemented.** This is design only; nothing here is built yet.

Detail doc for plan **#1**. The Ortler fixture gives us one landform family (a young
alpine range) but its importer is written *around* that one region. The design goal here
is **flexibility**: a fixture system that takes **any** region, so a new real reference
is a data entry rather than new code. Wales is the second instance and the one that
motivates it — it is not a special case.

**Design rule: no per-region code.** A region is a **record** (name, anchor, extent, tile
size, which layers to fetch); the importer, the dumper, and the loft side all take it as
input. Adding a third region must touch **data only**. The loft side already works this
way (`REGION=` + `src/regions/<name>.loft`); the Python side is what needs lifting.

**Why Wales / western Britain is the second one.** It is the natural contrast case:

| Landform | Ortler | Wales |
|---|---|---|
| young alpine relief, glacial troughs | ✅ the reference | — |
| **coastline** — rias, estuaries, headlands | absent (landlocked) | ✅ drowned valleys are textbook |
| **sea cliffs / hills → cliffs** | rock faces at altitude | ✅ cliffs at low elevation |
| **mature, eroded upland** | — | ✅ rounded massifs, wide valleys |
| dense settlement in valleys | sparse | ✅ towns/roads answer terrain |

So it is the ground truth for plan #8's F2 (rivers → coastlines) and F3 (hills →
cliffs), and a second opinion on F1 — an *old* range next to a *young* one, which is
what stops "resembles the Alps" from collapsing into "resembles this one seed".

## What already exists (do not rebuild)

The **loft-side region pipeline is already multi-region and its documented worked example
is literally Wales** (Makefile):

```
#   2. `make region-bin REGION=wales` writes data/regions/wales.bin.
#   3. `make region     REGION=wales` writes src/regions/wales.loft.
REGION ?= ortler
```

- `src/realworld/` — `region.loft`, `region_io.loft`, `hydro.loft`, `trimesh.loft`,
  `rivers.loft`: all region-agnostic already.
- `make region-bin` / `make region` / `hydro-test` / `trimesh-test` / `rivers-test` all
  take `REGION=`.
- `src/regions/ortler.loft` is the only materialized region.

## What actually needs doing

The gap is **Python-side**: the importer is written around one region.

1. **Lift the anchor into a region record.** `ortler_import.py` anchors on module-level
   `SUMMIT_LAT` / `SUMMIT_LON`, with `world_to_latlon` / `cell_to_latlon` built around
   them. Make the region an explicit record — `{name, anchor_lat, anchor_lon, cols, rows,
   tile_m, layers}` — passed in, so the same code fetches anything. **Keep the records in
   a data file** (one entry per region), not in code: that is what makes region three
   free. The I-GEO round-trip gate (S0) must re-pass **per region** — a new anchor is
   exactly what could break parity, so it becomes a per-region gate rather than a
   one-time one.
2. **Make the dumper table-driven.** `dump_region_bin.py` has `REGION_DUMPERS =
   {"ortler": dump_ortler}` — a per-region function. It should dispatch off the region
   record instead, so no new function is needed per region.
3. **Make the layer set part of the record.** The Ortler needs
   `natural=glacier|bare_rock|scree|wood|water` + `landuse=…`; a coastal region also
   needs **`natural=coastline`** plus a land/sea mask, so cells seaward of it read as sea
   rather than "height 0 land". Rather than special-casing coasts, let each region
   **declare which layers it wants** — an inland region simply omits the coastline layer.
   This is the flexibility that matters: the coastline is F2's ground truth, but it must
   arrive as *a layer*, not as a fork in the importer.
4. **Pin the sea datum, once, as a format convention** (MSL / LAT / HAT) and carry an
   explicit **intertidal mask** rather than collapsing the alternating zone to one state.
   It is a property of the *format*, so it belongs beside the schema, not in a region
   entry. See *Why this window* -> *The datum still has to be pinned*.
5. **The window is chosen and pinned: the Severn / Bristol Channel** (user direction) —
   the estuary as the basis, **upper Cornwall to the south**, **ordinary sea coast to the
   west**, widened so Pembroke is on the map. Exact extent under *Scale*; the landforms it
   buys under *Why this window*.

## Scale — the window is PINNED (decided 2026-07-21)

The Ortler fixture is **80×80 cells at `TILE_M=1500` ≈ a 120 km square**, centred on the
summit. That box **cannot** hold this region: Pembrokeshire (5.36 W) and the inner Severn
at Avonmouth (2.60 W) are **188 km apart**, so an Alps-scale box must drop one of them —
shifted west it gains Pembroke but loses the inner estuary, which is the feature that
motivated the region in the first place.

**Decision: widen the window rather than lose the estuary.**

| | value |
|---|---|
| **longitude** | 5.36 W … 2.60 W |
| **latitude** | 50.75 N … 51.95 N |
| **extent** | 192 km × 134 km |
| **grid** | **128 × 89 cells** at `TILE_M=1500` (11 392 cells) |
| **anchor** | 51.35 N, 3.98 W — the geometric centre (open water in the Bristol Channel), *not* a landmark like the Ortler summit |
| **cost** | 1.8× the Ortler's cells; ~114 DEM calls at 100 locations/request |

**On the map:** St Davids Head, Pembroke, Milford Haven, Tenby, Gower, Swansea, Cardiff,
**Avonmouth (the inner Severn funnel)**, Exmoor, Ilfracombe, Bude (north Cornwall),
Brecon Beacons.
**Off the map:** Tintagel, Newquay, Dartmoor.

The one continuous drainage from the Brecon uplands out through the estuary to the open
Celtic Sea is the reason to keep this as **one** region rather than splitting it — F2 is
about the coast being *drainage-derived*, so cutting the drainage in half would defeat it.

**Consequences for the region record** — both are exactly the flexibility this design is
for, so neither is a special case:

1. `COLS, ROWS = 80, 80` become **per-region** fields, and the grid must be allowed to be
   **non-square** (128 × 89).
2. The anchor is no longer semantically "the summit"; it is just a geometric origin. The
   record should not assume the anchor means anything.

## Why this window — the coastal features it supplies

The tide is the *reason* for much of the richness, not merely a complication: the
Severn's convergent funnel amplifies one of the largest tidal ranges in the world, and
that range is what builds the flats and marshes. Within the pinned box, F2 and F3 get an
unusually complete set of coastal landforms in **one continuous drainage**:

| Feature | Where | What it references |
|---|---|---|
| **ria / drowned valley** — the textbook case | **Milford Haven** | F2's core claim: drowned valleys become inlets. This is the single most on-target feature in the window. |
| **estuary funnel + extreme tidal range** | Severn → Avonmouth | the `os_ws` taper; convergence amplifying tide |
| **intertidal mud/sand flats, salt marsh** | Bridgwater Bay, Gwent Levels | sediment deposition at high-`acc` mouths |
| **limestone sea cliffs + tidal island** | Gower (Worms Head), Stackpole | F3 at low elevation |
| **very high hogback coastal cliffs** | Exmoor (Lynton / Countisbury) | F3 where upland meets the sea directly |
| **folded-strata cliffs + wave-cut platforms** | Bude / north Cornwall | F3 structural variety |
| **headland-and-bay** | Pembrokeshire coast | the ordinary-coast baseline |
| **large dune systems** | Kenfig, Merthyr Mawr | depositional counterpart to the erosional cases |
| **mature upland feeding it all** | Brecon Beacons, Exmoor | F1's *old* range, contrasting the young Ortler |

**The user knows this coast first-hand.** That matters concretely: plan #1's acceptance
test is a **cold-read recognition** on the rendered drawing (κ is ruled out), so a judge
who knows the real coastline can say "that is not what the Haven looks like" — which is
exactly the signal a per-cell metric cannot give. Record that as the intended review
path, not an afterthought.

### The datum still has to be pinned

Accepting the tide does not settle the encoding. A large fraction of this estuary is
*alternately* land and sea, so "sea = 0, negatives reserved for sub-sea structure" is not
neutral: which state the fixture records **is** the coastline F2 gets judged against.

Pin it beside the schema — lowest astronomical tide, mean sea level, or highest — and
**record which**. The Ortler never had to care, so this is a new format-level decision,
and left implicit it silently biases every coastal comparison. A defensible default is
**MSL for `h` plus an explicit intertidal mask** from the OSM `natural=coastline` +
tidal-flat tagging, so the alternating zone is *represented* rather than collapsed to one
state — but that is a proposal, not a decision.

## The region record — sketch

Data, not code. The two entries below are the whole point: `ortler` must round-trip
byte-identically through this shape (the refactor's gate), and `severn` must then be
addable without touching Python.

```
ortler:  anchor 46.5089 N  10.5446 E   cols  80  rows 80   tile_m 1500
         layers: dem, landcover, waterways
         note:   anchor == the summit == grid centre

severn:  anchor 51.35   N   3.98   W   cols 128  rows 89   tile_m 1500
         layers: dem, landcover, waterways, COASTLINE
         note:   anchor is a geometric centre (open water), not a landmark
         datum:  <pin before fetching — MSL + intertidal mask proposed>
```

Everything that differs between them is a field. Nothing that differs is a branch.

## Sources — same as the Ortler, one addition

- **Elevation** — OpenTopoData `eudem25m` (EU-DEM 25 m). Covers the UK.
- **Landcover** — OSM via Overpass, same tag set.
- **Water directions** — OSM `waterway=river|stream`, oriented downstream by the DEM.
- **NEW: `natural=coastline`** + a land/sea mask.

## Verification — the same two drawings

Identical acceptance shape to the Ortler: **two same-scale drawings**, (A) real data,
(B) our model, same projection/extent/cell layout. The gap between them is the adequacy
verdict for this landform family.

Per plan #1's standing findings, do **not** reach for κ as the referee on the fine tier
(falsified there); gate on invariants and the cold-read recognition test.

## Open questions

1. ~~Window extent~~ — **RESOLVED 2026-07-21**: 128 × 89 at 1.5 km, 5.36 W…2.60 W /
   50.75 N…51.95 N. See *Scale*.
2. **Does the 14-kind taxonomy survive a coast?** Plan #1's goal-1 question asked of a
   new landform: is a `K_SEA` / tidal / cliff-foot distinction missing? A second region
   is precisely how you find a kind the first region never needed — and it is the reason
   to build the flexible version rather than hardcode two.
3. **How far does "flexible" go?** A region record covers anchor/extent/layers. It does
   *not* yet cover a different **projection** (the current equirectangular anchoring is
   fine for mid-latitude Europe, but not everywhere) or a non-EU-DEM elevation source.
   Worth deciding whether those are in scope now or explicitly deferred — cheap to leave
   a seam for, expensive to retrofit.
4. **Ordering.** The flexible importer is a prerequisite for Wales, but Wales is the only
   thing that proves it flexible. Build the record for the Ortler first (it must keep
   producing byte-identical output — that is the refactor's gate), then add Wales as pure
   data.

## See also

- Plan **#8** (`plans/8-landform-morphogenesis/`) — the consumer: F2 coastlines, F3 hills→cliffs.
- `README.md` § Open work — the cliff-face gap this fixture also feeds.
- `Makefile` — `region-bin` / `region` / `hydro-test` / `trimesh-test` / `rivers-test`.
