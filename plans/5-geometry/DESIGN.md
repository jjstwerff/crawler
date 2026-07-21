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

## 6. SETTLED — collision is the EDGE model

**Decision (2026-07-21): collision is a set of blocked hex EDGES.** Movement from hex A
to B is legal iff their shared edge is not blocked. This answers FORMS.md open question 7.

| model | 1 unit thick blocks | width |
|---|---|---|
| cell | 6 of 24 headings | quantised + anisotropic; consistent only at ≥2 hex |
| **edge** | **24 of 24** | a rendering choice — exact, via the offset construction |

Two properties made the call:

- A cut **separates by construction**, so one edge is always enough, in any heading. The
  cell model cannot even form a connected 1-cell run off-axis.
- Wall **width stops being a collision concern** and becomes geometry, set exactly by the
  §4 offset construction — instead of quantised and 25% anisotropic.

**The edge model subsumes the cell model.** "You cannot enter this cell" is just "every
edge of that cell is blocked", so ONE collision layer serves a thin fence, a thick
curtain wall and a closed tower ring:

```loft
edges_cut(HexSet, EdgeSet)         // thin wall: the boundary cut
edges_solid(HexSet, EdgeSet)       // thick body: cannot be entered
edges_halfplane(EdgeSet, …)        // a straight wall in any heading
passable(EdgeSet, qa,ra, qb,rb)    // THE collision query
```

**The edge key is free**, because the lattice is already integer: an edge is identified
by the **doubled midpoint** of its two cell centres, `(kA+kB, mA+mB)`. Exact, symmetric
in A and B (so no ordering convention), unique per edge — verified 930 edges, 0
collisions.

Verified in `src/edgetest.loft` (in `make test`): a 1-edge wall blocks in **24/24**
headings, a solid body seals, and a ring cut seals its boundary.

### 6.1 Collision must return a NORMAL, so an edge stores a SURFACE

A bounce needs the wall's direction, and **a hex edge has only 6 possible normals** (60°
apart). Measured against the true wall normal across the 24 headings, using the edge's own
normal is wrong by **up to 90°** — a bounce that sends you sideways or backwards. Even the
best-case heading is 30° off. The direction is simply *not recoverable* from the cell grid.

So a blocked edge stores a **surface id**, not a boolean, and the surface carries the exact
geometry:

```loft
surf_straight(sfs, nx, ny, c) -> id     // constant normal — exact for any heading
surf_arc(sfs, cx, cy, r)      -> id     // radial normal — exact at EVERY point, no facets
collide(EdgeSet, Surfaces, qa,ra, qb,rb) -> (blocked, nx, ny)
```

**The hex grid becomes a SPATIAL INDEX, not the geometry.** The edge tells you *that* you
hit something and *which* thing; the surface tells you its exact normal at the contact
point. That is the standing rule again — never derive a smooth thing from cells — applied
to the normal.

Verified in `src/edgetest.loft`: straight-wall normals **exact in all 24 headings**
(worst error 0), and arc normals **radial-exact at every contact point** (worst error 0).

**Why this beats a collision mesh**, which was the alternative: no mesh has to be authored
or stored for a large area, and small organic blockers — a tree, a bush — are described
*better* by a surface (an arc/disc with a true radial normal) than by any low-poly hull.
Storage is one integer per blocked edge.

Open: a surface kind for irregular blockers (a rock outcrop, a hedge run) beyond
straight/arc, and what happens at a corner where two surfaces meet at one edge — today
first-writer-wins.

**What this does NOT change:** the cell footprint stays, for the body, its features
(doors, windows — FORMS.md's anatomy), matching, and rendering. Cells say what *occupies*
space; edges say what *blocks* movement; curves say what it *looks* like.

Crawler's `sim.loft` `tile_solid` is still cell-based — migrating it is a separate piece
of work, not a prerequisite for the joins.

## 7. The DUAL SYSTEM — stored world, derived field

**Decision (2026-07-21).** Two layers, deliberately different in kind:

| | **L1 — WORLD** | **L2 — FIELD** |
|---|---|---|
| what | cells + tags, stencils, bundles | edges → (surface, material) |
| authority | **the truth**; authored, saved, versioned | a **cache**; never saved |
| extent | the whole world, compact | one region, on demand |
| built | by authoring / generation | derived, `O(chunk)`, pure function of L1 |
| serves | matching, editing, persistence, diffing | physics, collision, propagation |

**L2 is a pure function of an L1 region**, which is what makes it safe: it is deterministic,
cacheable, chunk-local (already proven — same shape in two chunks traces identically), and
**cannot drift**, because it is thrown away rather than stored. Key it by
`(chunk, world_version)`; an edit bumps the version and the region is recomputed. Nothing
to migrate, nothing to keep in sync.

That also preserves L1's compactness: the exact positions and normals never enter the saved
world.

### 7.1 The consumers do NOT all want "blocked"

This is the part a boolean cannot carry. Each consumer reads a different property of the
same edge:

| consumer | needs |
|---|---|
| **bouncing balls** | blocked · **normal** · restitution |
| **movement limiters** | blocked · **height** (step over a low wall) |
| **damage decals** | **contact point** · surface parameter · orientation |
| **water flow** | **permeability** · surface **tangent** (water runs *along* a wall) |
| **air flow** | permeability (and gaps a solid wall still leaks through) |
| **sound barriers** | **attenuation in dB** — not binary; a hedge muffles, a wall stops |
| **sight barriers** | **opacity** · height — a low wall blocks movement but not sight |

So an edge carries **two references, not one flag**:

```
    edge  →  (surface_id, material_id)
             surface = GEOMETRY  — normal, tangent, contact point, curvature
             material = PHYSICS  — solid, height, opacity, sound_db, permeability, restitution
```

The split matters because they vary independently: a stone wall and a hedge on the *same*
arc share a surface and differ entirely in material; a wall and a tower of the same stone
share a material and differ entirely in surface.

**Sight and sound fall out of the same structure**: both are propagation across edges, and
both already have their barrier term stored per edge. A shadowcast reads `opacity`, a sound
solver accumulates `sound_db`, a flow solver reads `permeability` — all traversing the same
derived field, none of them needing a mesh or a second spatial structure.

### 7.2 WHEN to build it — L2 is a first pass, not an end product

The tempting reading is that L2 is derived *after* everything, purely to answer physics
queries. That is wrong, and the reason is a bug class rather than a preference.

**The failure mode to design out.** If the mesh is derived from L1, and the collision field
is *also* derived from L1, then the same geometry has been computed twice by two different
routines — and they will disagree. That is the "the wall you see is not the wall you hit"
bug, and it is invisible in unit tests because each derivation is self-consistent. The
design already forbids exactly this shape elsewhere (one home per fact; no part owns a
local frame), and it applies here.

**So the surface layer is the SHARED intermediate**, and it is built before the mesh:

```
   L1 world cells / tags
        │
        ▼
   L2  SURFACES   (exact 2D geometry: centrelines, arcs, offsets)   ← built FIRST
        │                    │
        │                    └─── validate()  — the gate, before any consumer
        ├──────────────► terrain heights ──► GROUND LINES ──► mesh / extrusion
        └──────────────► materials ────────► physics, flow, sight, sound
```

Read that as three claims:

1. **The mesh is built FROM the surfaces, not beside them.** The wall the renderer extrudes
   and the wall the ball bounces off are then the *same* curve by construction — not two
   curves that happen to agree.
2. **Ground lines are `surface × terrain height`.** The surfaces are exact and 2D; draping
   them onto the LOD heights is what produces the ground line. So the surface must exist
   before the ground line can, which settles the ordering the question asked about.
3. **`validate()` sits at that junction** — the earliest point where bad geometry can be
   caught, and before either consumer has spent work on it.

**And L2 is useful with no mesh at all.** Physics, water and air flow, sight and sound need
only L2. A region that is never rendered — off-screen, server-side, a headless test — still
gets correct behaviour, and pays nothing for meshes it does not need. That is the same
argument that ruled meshes out for collision, one level up: the mesh becomes a *rendering*
artifact rather than a simulation prerequisite.

**Cost is not doubled.** L2 is `O(chunk)` and already required for physics; the mesh path
consumes it instead of re-deriving, so building it first is cheaper than the alternative,
not more expensive.

**Lifecycle follows from this.** A region needs L2 when *either* something must simulate
there or something must be drawn there — so it is built on first demand of either, cached
by `(chunk, world_version)`, and dropped when neither holds. Rendering and simulation share
one cache rather than keeping two.

### 7.2b THE GRID *IS* THE INDEX — and that is why L2 is a grid, not a list

**A correction to an earlier draft of this section.** It claimed the surface↔geometry join
was missing outright, because `VecMap` carries no surface id. That over-stated the problem
and mis-read the architecture. The reason L2 was made a **hex grid** rather than a list is
precisely that a grid *is* an in-structure index: it answers **"what is at this position?"
in O(1)**, with no lookup structure to build and nothing to keep in sync.

Sorting the consumers by the question they actually ask makes the split obvious:

| consumer | question | structure | path |
|---|---|---|---|
| bouncing ball | position → what is here? | **GRID** O(1) | edge → surf → normal |
| damage decal | position → what is here? | **GRID** O(1) | edge → surf → point + normal |
| movement limiter | position → passable? | **GRID** O(1) | edge → solid |
| water / air flow | position → permeability? | **GRID** O(1) | edge → material |
| sight / shadowcast | position → opacity? | **GRID** O(1) | edge → material |
| sound | position → attenuation? | **GRID** O(1) | edge → material |
| draw the outline | *iterate* all geometry | LIST O(n) | vector map, sequential |
| build the mesh | *iterate* all geometry | LIST O(n) | vector map, sequential |

Every **random-access** consumer asks "what is at this position?" — that is a grid. Every
**sequential** consumer iterates — that is a list, and it needs no index at all. The two
structures are not rivals; they serve opposite access patterns, and the list is an *output*
rather than a queryable store.

**So the physics path is complete today**: `grid → surface id → exact normal`, verified in
`edgetest.loft`. A decal *can* be placed on the wall it just hit, without the vector map
being involved.

**The one real gap is render-side attribution.** `VecMap` has no `vm_surf`, so a list
segment cannot be traced back to the surface it came from. That matters for drawing a decal
*onto the mesh*, or highlighting a hit segment — not for the simulation. It is a smaller,
render-only gap, and the fix is still to tag segments with the surface id when the vector
map is derived from surfaces (§7.2).

**What survives from the earlier draft, because it is independently true:** cell-authored
content still has no surfaces, so it has no recoverable normal. That makes FORMS.md's
**matcher** load-bearing for physics rather than kit polish — it is what lets cell-authored
and curve-authored content behave identically. Until it exists, cell-authored walls report
`surf 0`: blocked, with `collide()` honestly returning no normal instead of faking one.

### 7.3 Minimising L2 — small integers, and a better index

L2 is a per-region cache, so its size is a real cost. Measured, the current `EdgeSet` is
**~48× larger than it needs to be** for a 32×32 chunk (430 KB vs 9 KB), from two
independent causes.

**Cause 1 — the index wastes ~9× (the bigger problem).** Keying a dense array by the
doubled-midpoint `(K,M)` is sparse: only half the slots are legal at all (parity must be
`(0,0)` or `(1,1)`), and the doubled lattice spans ~4×/6× the cell grid.

| chunk | cells | real edges | slots allocated | waste |
|---|---|---|---|---|
| 16×16 | 256 | 800 | 7 665 | 9.6× |
| 32×32 | 1 024 | 3 136 | 27 537 | 8.8× |
| 64×64 | 4 096 | 12 416 | 104 145 | 8.4× |

**Fix: index by `(cell, canonical direction)` — exactly 3 slots per cell, zero waste.**
Verified: crawler's neighbour encoding pairs opposites as `{0↔1, 2↔5, 3↔4}`, so the
canonical set `[0, 2, 3]` covers **every edge exactly once** (813 edges, 0 duplicates, 0
missed). The doubled-midpoint key stays as the *canonical identity* (it is what makes the
key symmetric and portable); it is just no longer the storage index.

**Cause 2 — 64-bit integers per edge.** Nothing per-edge needs 64 bits:

| field | type | why it is enough |
|---|---|---|
| surface id | `u16` | 65 k distinct surfaces in one region |
| material id | `u8` | 256 materials |
| *(optional)* baked normal | `u8` angle | 360/256 = **1.41°/step, max error 0.70°** — against the 90° error we are avoiding |

**Answer to "small integers or `single`?" — both, in different places.** Per-edge data is
**small integers, no floats at all**. `single` belongs in the *surface table*, which holds
one entry per wall or tower in the region and is therefore not the memory driver; f32's
~7 digits is far more than the geometry needs. **No doubles anywhere in L2.**

Loft supports this directly — `vector<u8>` / `vector<u16>` / `vector<single>` are
declarable, with a checked narrowing cast: `x as u8? ?? 0` (verified).

**Measured with loft's `size`, not estimated** — element costs are integer 8 B, u16 2 B,
u8 1 B, single 4 B, boolean 1 B:

| 32×32 chunk | slots | bytes |
|---|---|---|
| current `ee_surf` + `ee_mat` (`integer`) | 27 537 each | **440 592 B** (430 KB) |
| minimised (cell,dir index; u16 + u8) | 3 072 each | **9 216 B** (9 KB) |
| | | **47× smaller** |

`size(v)` on a vector returns its byte footprint, so this is a fact about the running
structure rather than a hand computation — and it is worth asserting in the test so the
footprint cannot silently regress.

At 9 KB a chunk, keeping many regions resident stops being a concern — which matters,
because §7.2 has rendering and simulation sharing one cache.

### 7.4 What is built and what is not

Built and verified (`src/hexedge.loft`, `src/edgetest.loft` in `make test`):
`EdgeSet` keyed by the exact doubled-midpoint edge key · `Surfaces` with straight and arc
kinds · `Materials` with the six per-consumer terms · `collide()` returning exact normals
(0 error, all 24 headings; radial-exact on arcs).

Not built yet: the region cache and its `(chunk, world_version)` key; the §7.3
minimisation (canonical-direction index + narrow types — the current `EdgeSet` is the
correct-but-fat version); a surface kind for irregular blockers; and corner arbitration
where two surfaces meet at one edge (today first-writer-wins — the wall→tower join work
should settle it).

## 8. Verification contract

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

## 9. Next, in order

1. **Settle §6** (wall model) — it gates the joins.
2. **Wall → round tower joins**: the connector seam, G0/G1 across the model boundary.
3. **Octagonal towers**: canonical orientation, frozen per size, minimum size `K` (the
   families are indistinguishable below 37 cells).
4. **Roads at catalog sizes in 24 directions**, then **curves between headings** — arcs of
   turn angle `k·15°`, riding the §4 construction where precision is free.
5. Tighten the harness per §7 before adding measurements.
