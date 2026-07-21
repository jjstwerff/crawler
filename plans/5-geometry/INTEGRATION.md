# Integration plan — geometry into loft, with the junction matrix

> How the design in `DESIGN.md` becomes working, gated loft. Phases are ordered by what
> unblocks what; every phase names its gate. Nothing here is built unless it says so.
>
> The hard part is not any single shape — it is **where two shapes meet**. That is where
> seams, collision arbitration and the matcher all fail at once, so the junction matrix
> (§3) is the real deliverable and the phases exist to make it testable.

## 1. Where we are

| built + gated | not built |
|---|---|
| `hexform.loft` — chunked `HexSet`, tracer, validator, exact integer `VecMap` | the §7.3 minimisation (canonical-dir index, `u16`/`u8`) |
| `hexway.loft` — `Track`, offsets, `way_stamp` one-pass rasteriser **(P1)** | the way *profiles* (rails/ruts/lane lines) on top of `Track` |
| `hexmatch.loft` — line/arc fits, greedy segmentation, `tag_edges` **(P2)** | junctions (P3) — the matcher assumes ONE part per loop |
| `hexedge.loft` — `EdgeSet`, `Surfaces` (straight/arc), `Materials`, `collide()` | the matcher (cells → surfaces) |
| `formtest.loft` — 18 forms / 900 points vs the Python golden; chunk-locality | junctions of any kind |
| `edgetest.loft` — 24/24 blocking, exact normals, materials, footprint | region cache, `vm_surf`, features |

## 2. Phases

### P1 — surfaces from curves ✅ **SHIPPED 2026-07-21**
`src/hexway.loft` + `src/waytest.loft`, gated in `make test` as `[ways]`.

A `Track` is a flat 6-float record per segment (straight or arc — no `vector<vector<>>`),
with `track_offset`, `offset_legal`, and `track_distance`. The load-bearing piece is
**`way_stamp`: one walk of the centreline writes the cells, the blocked edges AND the
surface ids together** — which is precisely why no lookup index is ever needed to answer
"which wall segment did I hit?". `nearest_seg` is the P3 arbitration rule in embryo
(nearest wins, ties to the lower index).

Measured by the gate:

| invariant | result |
|---|---|
| **I-EQUI** worst \|dist − d\| over 4 offsets | **1.8e-15** (float noise — exact) |
| **I-CURV** `d=3` / `d=R` / `d=R+1` | legal / **rejected** / **rejected** |
| **flattening** sagitta vs `c²/(8R)` at 4/8/12/16 chords | 0.10475 ≤ 0.10495 · 0.02622 ≤ 0.02624 · 0.01166 ≤ 0.01166 · 0.006559 ≤ 0.006559 |
| **one pass** boundary edges tagged | **74 of 74**, 0 untagged, 0 bad normals |
| vector map of the same footprint | 1 loop, validator 0 |

The flattening row is the useful one: the sagitta sits just *under* the theoretical bound
at every density, so `chord = √(8·R·tol)` is a usable design rule rather than an estimate.

### P2 — the matcher: cells → surfaces ✅ **SHIPPED 2026-07-21**
`src/hexmatch.loft` + `src/matchtest.loft`, gated as `[match]`. Greedy segmentation of a
traced loop into straights (total-least-squares) and arcs (Kasa + mean-radius
refinement), then `tag_edges` attaches the recovered surface **nearest** each boundary
edge — the same arbitration hexway uses, so cell-authored and curve-authored content
behave identically downstream.

**The tolerance is not tuned.** A boundary vertex is a hex *corner*, so it sits at most
one circumradius — exactly **1.0 world unit** — from the true surface. That is the
quantisation scale measured throughout this plan, so it *is* the tolerance: big enough to
absorb the zigzag (worst measured residual on a straight wall, 0.81), small enough that a
real corner never fits inside it. Pinned in the Python oracle first
(`plans/5-geometry/matcher.py`) — below 1.0 a tower over-segments into 9–11 line runs.

| gate | result |
|---|---|
| round tower r=8.4, 85 cells | **1 run, 1 arc, fitted r = 8.390** (error 0.01) |
| hexagon N=6, 127 cells | **6 runs, 6 straights** — exactly its 6 flat sides |
| worst fit residual, all runs | 0.952 ≤ tolerance 1.0 |
| tower boundary edges | 66 tagged, **0 untagged**, 0 bad normals, **66 of 66 radial** |
| punch a door, re-match | still **1 run** — body intact |

**A door cannot fragment the body, by construction.** In the edge model a door does not
change the footprint at all — it makes edges passable. So the traced boundary is
identical and FORMS.md's "a feature is an annotation on a continuous body, never a break
in it" is satisfied *structurally* rather than by careful handling. That invariant was the
motivation for the whole body/features split; the edge model gives it for free.

### P3 — junctions as first-class objects
Today two surfaces meeting at one edge is **first-writer-wins** — arbitrary and
order-dependent. Replace with a stated rule.

> **Arbitration: the surface whose geometry is NEAREST the edge's contact point wins;
> ties break to the lower surface id.** Deterministic, order-independent, and it matches
> what a ball should bounce off.

A `Junction` records the participating surfaces, the intended continuity (G1 smooth vs a
deliberate corner), and the arbitration outcome.

**Gate** `src/jointest.loft` ✅ **SHIPPED 2026-07-21** — gated as `[join]`.

| check | result |
|---|---|
| tower + wall built A-then-B vs B-then-A | 268 blocked edges, **268 identical, 0 differ** |
| blocked edges with no surface | **0** |
| tangential join, `G1` intended | G0 exact ✓, continuity honoured ✓ |
| wall↔wall, `∠` corner intended | G0 exact ✓, corner honoured ✓ |

**The gate caught two real defects, neither of them arbitration:**

1. **A PHASE bug.** `way_stamp` marked cells *and* cut edges per part. When a later part
   added cells, edges the earlier part had blocked became *interior* — and were never
   cleared. The stale set depended on which part ran first (22 of 266 edges differed).
   Fix: **two phases — `way_mark` every part, then `cut_arb` once** over the finished
   footprint. Order-independent by construction, because the cut never looks at what was
   stamped when.
2. **A wrong test scene.** The wall left the tower rim at `(6,0)`, where the tower's
   tangent is *vertical* — a 90° meet, not a tangential one. The G1 check was right and
   my scene was wrong; the wall must depart at `(0,6)` where the tangent already runs east.

### P3b — WALL TYPE as a matcher hint *(user direction, 2026-07-21)*

Tag a wall as `ROUND` or `STRAIGHT` at authoring time and let it **constrain** the
matcher. Measured benefit:

- **It is the only thing that can work at small sizes.** Below 37 cells hexdisk, circle
  and octagon rasterise to *byte-identical* cell sets (7 and 19 cells at N=1,2) — no
  amount of geometry can separate them. A tag can.
- **It removes the line-vs-arc guess.** Free inference shatters a round tower into 10
  runs at tol 0.6 and 7 at tol 0.8; with a `ROUND` tag it is **1 arc, r = 8.390** at every
  tolerance. So the matcher stops depending on the tolerance being exactly right.
- **A type change marks a run boundary explicitly**, so a wall→tower junction is *stated*
  in the data rather than inferred from a fit residual.

Design: the tag is a **hint, not a replacement**. Cell-authored content with no tags
(a hand-drawn footprint) still falls back to inference, so nothing regresses; tagged
content simply gets an unambiguous, tolerance-independent answer.

### P3c — the SAME tag for ways, and the 15° rule it exposes *(user direction)*

Ways need it more than walls do, because a railway junction is usually exactly the hard
case: **a rounded centreline meeting a straight one**. Under 24 directions that is not
merely ambiguous — it is often *impossible* to join smoothly, and the tag is what makes
the constraint checkable.

A straight is one of 24 headings (15° apart). An arc's tangent varies **continuously**.
So a tangential join only exists where the arc's end tangent lands exactly on the
24-grid:

| arc sweep | end tangent | nearest 24-dir | kink |
|---|---|---|---|
| 10° | 10° | 15° | **5.00°** |
| 15° | 15° | 15° | 0 — on-grid |
| 37.5° | 37.5° | 30° | **7.50°** |
| 45° | 45° | 45° | 0 — on-grid |
| 60° | 60° | 60° | 0 — on-grid |

Worst case is **7.5°** — half a step — which is plainly visible on a rail and a real
lurch to ride.

> **THE RULE: an arc that joins a 24-direction straight tangentially must have a sweep
> that is a multiple of 15°** (given an on-grid start tangent). There are exactly 24 legal
> departure points around any circle.

**Corollary for railways:** G2 already requires a clothoid between straight and arc, and a
clothoid's whole job is to rotate the tangent while ramping curvature — so the same 15°
quantisation must hold at **both** of its ends, not just one. That makes the transition
length a *derived* quantity (the sweep it must absorb), not a free parameter.

This belongs in the P1 way builder as a validation, not in P4: an illegal arc should be
rejected where it is authored, not discovered at the junction.

### P4 — the junction matrix *(the real deliverable — §3)*

### P5 — features: doors and windows ✅ **SHIPPED 2026-07-21**
`Features` in `hexedge.loft` + `src/feattest.loft`, gated as `[feat]`. A feature is an
**interval on the surface** `[s0,s1]` with a **vertical extent** `(z0,z1)`, pointing at
its own **material**.

| gate | result |
|---|---|
| plain wall | 70 blocked edges, **0 passable** |
| door width 1.0 | 4 passable |
| door width 2.6 — **double door** | **8 passable**, 62 still sealed |
| door width 7.0 — gateway | 16 passable |
| window | solid ✓ (blocks movement), see-through ✓ (opacity 0.1) |
| window sill..head | 1.0…2.0 inside a wall of height 2.5 |
| wall with 3 features | matcher: **2 runs — same as the plain wall** |

**Pointing at a material solves L4 without inventing a per-term override.** A door's
material has `solid=false`; a window's has `solid=true` with low `opacity`/`sound`. "Which
subset does this feature change?" is answered by *which material it names*.

**L3 confirmed and fixed**: `Materials.height` is a scalar and can only say "a wall of
height h", so a window's sill..head is inexpressible there. The feature carries `(z0,z1)`.

**The door quantum is NOT the edge length — measured.** For a one-row wall the boundary
edges cluster at ±0.433 around each hex centre, and centres are **1.732** apart, so a door
only gains edges when the interval reaches the *next hex*: widths 1.0 and 2.2 open exactly
the same edges. The earlier 1.0-unit figure was measured on a *cut* (the edge-model thin
wall), where edges run along the wall ~1.0 apart. **So the quantum depends on the wall
model** — another place the cell/edge choice shows through:

| wall model | door quantum |
|---|---|
| edge-model cut | ~1.0 (one cut edge) |
| cell-model one-row footprint | **1.732** (hex spacing) |

*Two of my own test expectations were wrong here and the gate caught both: the quantum
above, and a counter that visited every shared edge twice (once per side), silently
doubling every figure. Fixed with the canonical direction set `{0,2,3}`.*

### P6 — minimisation ✅ **PARTIALLY SHIPPED 2026-07-21** (cache still open)

**The index change shipped, and it was the bigger half.** `EdgeSet` now stores by
`(cell, canonical direction)` — a hex's 6 edges form 3 opposite pairs `{0,1} {2,5} {3,4}`,
so the canonical set `{0,2,3}` gives exactly 3 slots per cell and every edge is owned
once. A one-cell halo covers boundary edges whose canonical owner sits outside the chunk.
The doubled-midpoint key remains the **canonical identity** (symmetric, portable); it is
simply no longer the storage index — two different jobs that were conflated.

**Measured, not estimated** (`size` in the gate):

| | bytes / 32×32 chunk |
|---|---|
| before | 440 592 |
| after the reindex | **27 744** — **15.9×** |
| theoretical, with `u16`+`u8` | 10 404 |

**The remaining 2× is blocked upstream.** `vector<u16>` / `vector<u8>` exist and can be
appended to and read, but loft **cannot index-assign into them** (`Cannot assign to
attribute on type 'OpGetShortRaw'`) — and this layer is written by index. Filed as
**LOFT-HANDOFF.md → H3**. Workaround in place: keep `vector<integer>` and **pack** the
surface id and material into one element (`surf * 256 + mat`), which recovers about half
of what the narrow types would have given.

**Still open: the region cache** and its `(chunk, world_version)` key. The derivation is
already a pure function of an L1 region and provably order-independent (P3/P4), so the
cache is bookkeeping rather than new geometry — but it is not built.

## 3. The junction matrix

Every cell is a test. `G0` = no gap, `G1` = no kink, `∠` = a deliberate corner.

| | straight wall | curved wall | round tower | octagonal tower | road / rail |
|---|---|---|---|---|---|
| **straight wall** | collinear join · **T-junction** (inner wall) · **∠ corner** | tangent meet `G1` | **tangential** `G0+G1` | onto a **flat face** `G1`; onto a **corner** `∠` | wall crosses road: gate/arch |
| **curved wall** | — | arc↔arc, equal or opposed curvature | concentric or tangential | rarely tangential — expect `∠` | — |
| **round tower** | — | — | two towers touching / overlapping | mixed-family adjacency | — |
| **octagonal tower** | — | — | — | face-to-face vs corner-to-corner | — |
| **road / rail** | — | — | — | — | **crossing** · **merge** `G1` · **railway points** · roundabout |

### What every junction must satisfy

1. **G0** — the surfaces share the seam exactly (integer lattice, so this is exact).
2. **G1 or an intended corner** — never an accidental kink. Ways additionally need **G2**.
3. **Topology** — the traced outline still validates: closed loops, correct winding, and
   `Σ shoelace == 12 × cells` still holds *across* the junction.
4. **Collision arbitration** — deterministic and order-independent (P3).
5. **No leak** — the flood test still fails to cross a joined wall run.
6. **Matcher survival** — the parts are still individually recoverable after joining.

### The cases most likely to break, and why

- **Inner wall T-junction** — the inner wall *ends* at the outer wall. Its last edge is
  shared, so arbitration decides which surface a ball bounces off in the corner. Also the
  first case where a cell has walls on more than one of its 3 canonical directions.
- **Wall onto an octagonal corner** — 8-fold against 6-fold: the tangent cannot be
  continuous, so this must be an explicit `∠`, and the octagon's canonical orientation
  decides which walls can meet it cleanly at all. Expect a *rule*, not a fix.
- **Two towers overlapping** — the union's boundary is not either tower's boundary; the
  matcher must still recover two towers, or explicitly report a merged form.
- **Railway points** — one centreline becomes two with `G2` through the divergence. This
  is the hardest way-junction and should come last.
- **Road crossing a wall** — the collision layers disagree by design (the road is
  passable, the wall is not). Whichever wins must be *stated*, not emergent.

## 4. Doors and windows — the limitations are real

The user's suspicion is correct, and the first limitation is hard.

### L1 — the 1.0 unit is a QUANTUM, not a cap *(corrected)*

An earlier draft of this section claimed a straight opening could never exceed 1.0 unit.
**That was wrong**, and it mattered — it would have ruled out double doors.

What is true: on a traced cell boundary the longest **collinear** run of edges is 1, in
every one of the 24 headings, because the outline turns at every vertex. But that only
constrains an opening *cut from the cell outline*. In the edge model a wall is a **cut**,
and each cut edge is a unit segment running **along** the wall — so an opening is simply a
run of consecutive cut edges, and widening on both sides is exactly the mechanism.

Measured, opening `k` adjacent cut edges (all passable, wall still sealed elsewhere):

| edges opened | 0° | 30° | 45° | |
|---|---|---|---|---|
| 1 | 1.0 | 1.0 | 1.0 | single door |
| **2** | **1.9** | **1.8** | **1.6** | **double door — works** |
| 3 | 2.7 | 2.5 | 2.4 | triple |
| 4 | 3.6 | 3.2 | 3.1 | gateway / arch |

And the *visual* opening is straight regardless, because the door is an interval on the
**surface** (§L1b), not a hole cut in the cell outline. The zigzag never reaches the
render or the mesh.

### L1b — features are intervals on the SURFACE

A door is `[s0, s1]` along an exact straight or arc, so it is straight because the surface
is, at any width and any position. The cell/edge layer only answers *which edges that
interval opens*. Standing rule again: never derive a smooth thing from cells.

### L2 — the residual limits are the quantum and its anisotropy

Two real constraints remain, both bounded:

- **Collision quantises to whole cut edges.** A door of 1.5 edges cannot be expressed —
  an edge is passable or not. Fix if it ever matters: an **aperture fraction** per edge
  (how much of it is open), which is a genuine extension rather than a tweak.
- **The quantum varies ~19% with heading** — one edge projects to 1.0 along the wall at
  0°, but ~0.8 at 45°, because the cut zigzags. So "a double door" is 1.6–1.9 units
  depending on which way the wall runs. Same anisotropy family as everything else here,
  and the same fix if it matters: pick the edge count per heading to hit a target width,
  exactly as §7.3's phase knob does for wall width.

### L3 — `Materials.height` is a SCALAR; a window needs an interval

A window is `sill..head`, and the current model can only say "wall of height h". A window
therefore cannot be expressed at all today. Features need their own `(z0, z1)`.

### L4 — a door and a window modulate DIFFERENT terms

A door changes `solid` (and nothing else when shut vs open). A window changes `opacity`,
`sound_db`, `permeability` — and **not** `solid`, since you cannot walk through it. So a
feature must **override a subset** of the material's terms, not replace the material.

### L5 — features must not fragment the body

FORMS.md's invariant: a wall with three doors and a loophole still matches as **one**
wall. A feature is an annotation on a continuous body, never a break in it — so features
must be stored *beside* the surface, never by deleting cells or edges from it. (Today
`stamp_house` punches a door by clearing a whole hex — exactly the thing this forbids.)

### L6 — a feature at a junction

A doorway in a corner belongs to two surfaces. Arbitration (P3) decides, and the feature
interval must be expressed on the winning surface.

**Gate** `src/feattest.loft`: a door interval yields exactly the intended passable edges ·
**a double door (2 adjacent cut edges) is passable and the wall still seals elsewhere** ·
a window blocks movement but not sight · a wall with three features still matches as one
wall · features survive the surface round-trip · door width per heading is within the
stated ~19% band, or the edge count is chosen to hit a target width.

## 5. Order, and why

```
P1 surfaces from curves
      └─► P2 matcher (cells → surfaces)
                └─► P3 junction arbitration
                          └─► P4 junction matrix   ← the deliverable
                          └─► P5 features (needs surfaces + arbitration)
P6 minimisation + cache — independent, any time
```

P2 before P3 because a junction between two cell-authored parts has no surfaces to
arbitrate until the matcher exists. P5 after P3 because a feature at a junction needs the
arbitration rule. P6 is orthogonal and can be done whenever the footprint starts to hurt.

**Do not start P4 before P3 is green** — an unstated arbitration rule makes every junction
test order-dependent, and the matrix would encode the bug rather than catch it.
