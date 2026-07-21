# hex_forms — concrete library design

> Design for the geometry library plan **#5** produces. Written after the blueprint
> measurements, so every number here is measured, not assumed; each decision cites the
> bench that settled it. Companion to **FORMS.md** (the kit-of-parts requirements) and
> `README.md` (the measurements themselves).
>
> **Status: DESIGN — not implemented beyond the prototypes.** `src/hexform.loft` is a
> partial first cut (cells → vector map + validator); everything else is Python bench.

## 1. What it is

A **library**, not crawler code: reusable across games and editors, no consumer-specific
knowledge inside. One job:

```
    tagged hex cells  ──►  VALIDATED VECTOR MAP  ──►  2D renderer
    exact curves      ──►                        └─►  mesh / extrusion
                                                 └─►  collision
```

Two input kinds, deliberately kept apart because their precision differs by orders of
magnitude:

| input | precision | use |
|---|---|---|
| **cell sets** (towers, wall footprints, floor) | quantised, ~0.577 hex widths | footprint, occupancy, collision, matching |
| **curves** (way centrelines + offsets) | exact / any named tolerance | rails, road edges, anything that must look smooth |

**The rule: never derive a smooth thing from cells.** Cells are for what occupies space;
curves are for what must read as continuous. A way has both — a cell footprint for
collision and a curve for its geometry.

## 2. The data model

### 2.1 Exact integer lattice — the whole reason this works

For pointy-top odd-r, circumradius 1, every hex centre **and every corner** lies on

```
    x = k · √3/2        y = m / 2           (k, m INTEGER)
    centre(q,r) = (2q + (r&1), 3r)
    corners     = (0,±2), (±1,±1)
```

So the vector map stores **integers**. No float drift, no epsilon compares, and a golden
JSON diff is exact. Consumers multiply by `(√3/2, ½)` once, at the end.

**Canonical corner order is fixed and NOT ours to choose** — it is `hex_grid::hex_corner_offset`,
mirrored by `worldmesh.loft` `hex_lat_offset`, which the watertight instanced floor
depends on:

```
    CORNER = [(0,2), (-1,1), (-1,-1), (0,-2), (1,-1), (1,1)]
```

*(Verified against `hex_to_px` before porting; an earlier draft started at `(0,-2)` —
canonical index 3 — and was wrong.)*

### 2.2 Chunk, not world

Every routine is **O(chunk)** and never walks an unbounded neighbourhood.

```loft
struct HexSet { hs_q0, hs_r0, hs_w, hs_h: integer, hs_cells: vector<boolean>, hs_count: integer }
```

A chunk anchored at `(q0,r0)`, `w × h` cells — so the same code serves a 32×32 world
chunk (plan #2) and a one-off tower window. Anything spanning chunks is traced per chunk
with a halo and stitched. **Proven, not asserted:** `formtest.loft` builds the same disk
in two chunks anchored 5,4 apart and requires identical traces up to the lattice
translation.

### 2.3 The vector map

Flat arrays plus a start index — not `vector<vector<>>`, which loft handles poorly.

```loft
struct VecMap { vm_k, vm_m: vector<integer>, vm_start: vector<integer>, vm_loops: integer }
```

Loop `i` occupies `[vm_start[i], vm_start[i+1])`. Outer loop wound positive, holes
negative — what a fill rule and a triangulator both need.

**Loops are canonicalised**: each starts at its lexicographically smallest vertex. Without
this the golden is not a contract — two correct implementations disagree on the seed
vertex. *(Found by the loft port disagreeing with Python while every point matched.)*

## 3. API surface

```loft
// construction
hexset_chunk(q0, r0, w, h) -> HexSet
hexset_get / hexset_set / hexset_count

// placement routines — add one, it joins the bench
form_hexdisk(w, n)            // hex-distance disk  (silhouette: hexagon)
form_circle(w, radius)        // euclidean disk     (silhouette: circle)
form_octagon(w, apothem)      // canonical orientation, frozen per size
hexdisk_into(s, cq, cr, n)    // chunk-local fill at any centre

// derivation
trace(HexSet) -> VecMap       // cells -> exact ordered loops
wall_count(HexSet) -> integer
shoelace2(VecMap, i) / shoelace_total(VecMap) -> integer

// the gate
validate(VecMap, cells) -> integer   // 0 = safe to consume
```

### The validator — run before any consumer sees the data

| code | check |
|---|---|
| 1 | no loops emitted |
| 2 | degenerate loop (<3 points) |
| 3 | a segment is not an actual hex edge |
| 4 | **area round-trip**: `Σ shoelace ≠ 12 × cells` |
| 5 | not exactly one outer loop |

**The area round-trip is the load-bearing invariant.** One hex shoelaces to exactly `12`,
holes negative, so cell count and traced outline *cannot* disagree — the vector map
provably describes the hex set. Exact integer arithmetic, so it is equally exact in loft.

Check 5 turned out to double as a gameplay gate: it agreed with the wall blocking test in
**24 of 24** headings.

## 4. Ways — the 3-line construction

```loft
profile = [(offset, kind), …]        // data, not a branch
build_way(centreline, profile) -> [(offset, kind, curve)]
```

| profile | inner pair | outer pair | centre |
|---|---|---|---|
| `railway` | rails @ ±gauge/2 | bed edges | track centreline |
| `dirt_track` | wheel ruts @ ±axle/2 | worn edges | grass strip |
| `modern_road` | lane lines | road edges | centre marking |

A new way type is a **profile**, not a routine. Invariants:

- **I-EQUI** — a parallel curve is equidistant by definition; for straights and arcs it is
  also *exactly representable* (measured deviation 0.0). Flattening is what costs:
  `err ≈ c²/(8R)`, so **`chord = √(8·R·tol)`** — name a tolerance, the density follows.
- **I-CURV** — an offset degenerates when `|d| ≥ R`. That *is* the minimum curve radius,
  derived rather than tuned: `R > bed/2`.
- **G0 / G1 / G2** — FORMS.md's seam law covers position and tangent. Ways are the first
  family needing **curvature** continuity: a straight↔arc join measures a `0.00000°` kink
  but a `0 → 1/R` curvature jump. That is what a clothoid transition removes.

## 5. What the measurements decided

| question | decision | evidence |
|---|---|---|
| tower silhouette | hex-disk below 37 cells (it *is* optimal there); circle above | families identical at N≤2; hexagons are the ladder's error **maxima** from 61 cells up |
| tower sizes | a **frozen catalog** indexed by effective radius — not a formula | "radius N" is meaningless under a collision objective: N=5 and N=6 optimise to the same footprint |
| road sizes | a **catalog**: 2.02 and 2.94 hex widths (1.5% / 3.9% cross-heading spread) | fine sweep of achievable widths; other sizes are far less consistent |
| width consistency | tune band threshold **and perpendicular phase** per heading | 25.4% → **1.5%** spread |
| 24 directions | all usable; cost 1.00× edge / 1.68× vertex / 3.56× off-axis | width-normalised deviation |
| minimum wall | **model-dependent** — see §6 | 1-cell connected runs do not exist off-axis at all |
| push resistance | `interlock margin ≈ block_length / (2·radius)` | matches measurement to 3 decimals, R = 2…200 |

## 6. The one open decision that blocks the rest

**Is a wall a cell footprint or an edge cut?**

| model | 1 unit thick blocks | width |
|---|---|---|
| **cell** | 6 of 24 headings | quantised + anisotropic; consistent only at ≥2 hex |
| **edge** | **24 of 24** | a rendering choice — exact, via the offset construction |

Crawler is cell-model today (`sim.loft` `tile_solid`). The edge model is the better
collision primitive and makes width exact. **They compose**: cell footprint for the body
and its features (doors, windows — FORMS.md's anatomy), edge cut for collision.

This is FORMS.md open question 7 with numbers attached, and it should be settled before
the wall↔tower joins are designed, because the join *is* the seam between the two.

## 7. Verification contract

- **Python is the ORACLE**, `plans/5-geometry/*.py`. It stays; it is not the destination.
- **The golden JSON is language-neutral** — exact integers, canonical loops. The loft port
  re-derives nothing: `src/formtest.loft` asserts it emits the same integers, point for
  point, with no float tolerance. Currently 18 forms / 900 points, in `make test`.
- Float metrics (deviation, anisotropy) need ε-compare; the area round-trip does not.

### Harness rules — learned the hard way

Five conclusions in this plan were overturned by a sharper question. Each time the
instrument was fine and the *framing* was loose, so these are now rules:

1. **Always require `connected`** in any measurement of a run. Measuring disconnected cell
   scatters produced a confident, wrong 25.4% width spread.
2. **Never compare at fixed nominal width** — fit the effective width per case. A fixed
   world halfwidth silently varied the cell count by heading, twice.
3. **Control one variable.** The bend and centre sweeps were meaningless until width was
   pinned.
4. **Watch window/extent coupling.** A wall "failed to block" purely because the flood
   walked around its end inside a larger window.
5. **State bounds as bounds.** "0.577 is irreducible" was wrong (0.658 measured); it is a
   characteristic scale, and `max|d−W|` is bounded by 1.155.

## 8. Next, in order

1. **Settle §6** (wall model) — it gates the joins.
2. **Wall → round tower joins**: the connector seam, G0/G1 across the model boundary.
3. **Octagonal towers**: canonical orientation, frozen per size, minimum size `K` (the
   families are indistinguishable below 37 cells).
4. **Roads at catalog sizes in 24 directions**, then **curves between headings** — arcs of
   turn angle `k·15°`, riding the §4 construction where precision is free.
5. Tighten the harness per §7 before adding measurements.
