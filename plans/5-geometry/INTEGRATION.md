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

**The region cache shipped too** — `src/hexcache.loft` + `src/cachetest.loft`, gated as
`[cache]`. Keyed by `(chunk_x, chunk_y, world_version)`; an edit bumps the version and
every older entry is simply a miss. Nothing is migrated and nothing is patched in place,
which is exactly why the derivation had to be order-independent (P3/P4) and chunk-local
(formtest) *first*.

| gate | result |
|---|---|
| **cached == freshly derived** | **true**, edge for edge (52 vs 52) |
| second lookup | hit, **no rebuild** |
| same chunk at a newer version | **miss** — the stale entry is not served |
| re-derived at v2 | **differs** from v1, so staleness is detectable, not cosmetic |
| 4 chunks into a cap-3 cache | live 3, 1 eviction (LRU) |
| coarse invalidate before v3 | 3 dropped, live 0 |

**The gate caught a design flaw in claim ordering.** `cache_claim` preferred a *free*
slot over the *stale entry for the same chunk*, so one chunk could occupy two slots and
the cache would fill with stale duplicates of itself. Fixed order: same chunk (any
version) → free → LRU.

Eviction is LRU against a fixed capacity because §7.2 has rendering and simulation
sharing **one** cache: a region is wanted when *either* must touch it, so the residency
policy cannot belong to either alone.

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

## 3b. OCTAGONAL TOWERS — settled 2026-07-21

FORMS.md left three things open (canonical orientation, minimum size `K`, frozen
hex-sets). All three are now measured rather than chosen.

### The orientation is FORCED, not picked

An octagon's 8 face normals sit 45° apart, and **45 is a multiple of 15** — so at a
rotation that is itself a multiple of 15°, every face normal lands on the 24-direction
grid and a wall *can* meet any face tangentially.

| rotation | faces | mean cost |
|---|---|---|
| **0° / 15° / 30°** | e O v O e O v O | **2.45** — all on the 24-dir grid |
| 7.5° / 22.5° / 37.5° | O O O O O O O O | 3.56 — **none** on the grid |

At 22.5° every face sits at `22.5 + 45k`, none a multiple of 15, so **no wall direction
could meet any face tangentially at all**. 0/15/30 are the same octagon on different hex
axes, so **rotation 0 is canonical**.

### The 8 faces are NOT equal quality — and that is inherent

At the canonical rotation the faces split across all three cost tiers measured earlier:
**2 edge-normal (1.00×), 2 vertex (1.68×), 4 off-axis (3.56×)**. That is the 8-fold /
6-fold mismatch made concrete — not a defect to fix, but a fact to expose to whoever
places a wall. A designer attaching a curtain wall should prefer the two edge-normal
faces.

### Minimum size: a small octagon IS a circle

Rasterised below a certain size an octagon is not merely *similar* to a circle — it is
**the identical cell set**. Checked against every circle radius and every hex-disk:

| octagon | verdict |
|---|---|
| 7, 19, 31, 37, 55, 61, 85, 121 cells | **identical to some circle** — the family carries no information |
| 17, 35, 51 cells | distinct, but faces only 1.6–2.9 hex widths — marginal |
| **59 cells and up** | distinct **and** faces ≥ 3 hex widths — reads as flat |

So the rule: **do not offer an octagon below 59 cells** (apothem ≈ 6.7). Below that it
either *is* a circle or its faces are too short to survive quantisation. A face must span
~3 cells before it reads flat at all.

### The catalog — `golden/octagon_catalog.json`

16 distinct rungs, 13 of which read as flat, each frozen as an authored hex-set with its
effective apothem, worst deviation and face length in hex widths. Frozen rather than
formula-generated for the reason FORMS.md gave and the measurements confirm: the
rasterised octagon is not a clean function of its apothem.

### Junction rule, verified in the matrix

Two new matrix scenarios, both passing all six invariants:

- **wall → octagon flat face** — tangential, since the face normal is on the 24-dir grid.
- **wall → octagon corner** — **must be an explicit `∠`**. Tangent continuity is
  impossible at a corner where two faces meet at 135°; there is no wall heading that is
  tangent to both. This is a *rule*, not a fix, exactly as the plan predicted.

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

## 6. Railway points (P7) — the hardest way-junction

A turnout splits a stem into a **through** route and a **diverging** route. It is the
worst case for the 24-direction grid, because P3c forces any arc that rejoins a straight
tangentially to sweep a **multiple of 15°** — so the smallest possible departure angle is
15°, and that is *sharper than any prototype turnout*:

```
  crossing (frog) angle, real practice   OURS
     1:6   =  9.46°                       15.00° = 1:3.7
     1:8   =  7.13°
     1:12  =  4.76°
     1:20  =  2.86°
```

That looks fatal and isn't, because a single divergence was never the right model. Real
track turns out and then **reverse-curves back to parallel**, which is also exactly what
the grid wants: net heading change zero, so *both* ends land on the 24-direction set.

```
  stem ──▶ arc(+15°) ──▶ arc(−15°) ──▶ parallel straight
  lateral offset = 2·R·(1 − cos 15°) = 0.0681·R
```

So the binding constraint is not the angle, it is **length**: separating two tracks by one
hex width (1.732) needs `R ≈ 26`; a normal 2-track spacing needs `R ≈ 51`. **A turnout is a
long object** — it cannot be authored inside a single chunk, which is why way surfaces
were made chunk-local-but-not-chunk-bounded in P1.

The reverse point is also where **G2** bites hardest: curvature swings `+1/R → −1/R`, a
jump of `2/R` — the largest discontinuity anywhere in the way system, and the one place a
clothoid is not optional. Both of its ends inherit the 15°-multiple rule, so the
transition length is derived, never chosen.

**Gate** `src/pointstest.loft`: every arc sweep is a multiple of 15° · G1 continuous at
all four joins (measured kink 0°) · the worst curvature step is exactly `2/R` and sits at
the reverse point · the combined footprint traces to one loop and validates ·
every blocked edge is attributed to a surface · **stamping the two routes in either order
gives the identical field** (the shared stem must not be order-dependent) · the routes
share the stem (12 cells) and are **completely disjoint downstream** (0 shared cells past
the reverse curve) — a turnout that never separates is not a turnout.

## 7. Crossings and double slips (P8)

A crossing is where the 24-direction grid stops fighting and starts helping. **Both routes
are straights**, so any multiple of 15° is exact — the crossing angle costs nothing. And a
double slip's turning curve deflects by *exactly* the crossing angle, so its sweep is a
multiple of 15° **by construction**. Where the turnout needed a reverse curve to get back
on the grid (§6), **the slip inherits legality from the crossing**.

What binds instead is where the switch blade lands. The blade sits `t = R·tan(θ/2)` from
the crossing; the diamond only reaches `h = w/tan(θ/2)` along each track. Blade inside the
diamond means `R·tan(θ/2) ≤ w/tan(θ/2)`:

```
        R_max = w / tan²(θ/2)

   θ      15°     30°     45°     60°     75°     90°
   R_max  57.7w   13.9w   5.8w    3.0w    1.7w    1.0w
```

Real track wants `R ≈ 26–51`, so **only the 15° crossing admits a real double slip** — the
sharpest angle the grid offers is the only one that works. That is not a limitation of the
grid, it is why every prototype double slip is shallow: at 1:8 (7.13°) the bound gives
`258w ≈ 640 m`, comfortably satisfied.

### A double slip is invisible in the footprint

The arc's furthest excursion from either straight is at its midpoint, `R·(1 − cos(θ/2))`.
At the worst legal radius `R = w/tan²(θ/2)`:

```
   (1 − cos u) / tan² u  =  cos² u / (1 + cos u)  ≤  ½        (u = θ/2 ≤ 45°)
```

so a buildable slip never leaves the band by more than `w/2`. **Blade-inside and
footprint-invisible are the same condition** — measured `extra 0` cells at 15°, R=26.

This is the sharpest justification yet for the two-layer split (DESIGN.md §7): a plain
diamond and a double slip are the *identical* set of cells. The route topology lives
**entirely** in the surfaces. Anything reasoning about connectivity from cells alone —
pathfinding, signalling, flow — is reading a layer that cannot represent the difference.

### G2 is not available to a shallow slip

The room for a clothoid at each slip end is the tangent length `R·tan(θ/2)` = 3.4 at
θ=15°, R=26, against the `≈ R/3` a transition wants. There is none. Slips are G1-only —
which again matches practice: slips are slow-speed track and carry no transition curves.

**Gate** `src/crossingtest.loft`: every grid angle 15°–90° traces to one validated loop ·
the crossing is genuinely shared (union < sum of separate footprints, saving 5 cells at 15°
falling to 1 at 90°, as `1/sin θ` predicts) · the closed-form `R_max` agrees with the
direct blade-vs-diamond comparison at every angle · the excursion bound holds at every
angle · both slip sweeps equal the crossing angle · G1 at both tangencies (measured kink
0°) · the slip adds **zero** cells over the plain diamond · four surfaces arbitrate
order-free (372 blocked edges either way) · every blocked edge attributed · and no edge is
cut between two track cells — a crossing is passable, not a wall.

## 8. Level crossings and platforms (P9)

These two are worth doing together because they give **opposite** answers from the same
machinery, which is how you know both are right: a level crossing must have **no** cut edge
between the two ways (it is passable); a platform must **have** one along its face (it is a
drop). Measured 0 and 32 respectively.

### The level crossing — where material stops being decoration

Geometrically it is §7's diamond with unequal bed widths (rail 1.0, road 1.5), so the
overlap is not a rhombus and arbitration settles a genuinely asymmetric contest. What is
new is the **barrier**, the first dynamic object in the system — and it needs no new
machinery: a barrier is an inner wall (P4), a short straight across the road carrying its
own material.

Lowering it flips **one entry in the material table**. Every edge already holds that
material id, so nothing in the geometry layer is written:

```
   barrier down -> up:  surf sum 340 == 340,  mat sum 192 == 192   (zero edge writes)
   L2 cache:            still a HIT — the world version never moved
```

**A barrier toggle does not invalidate the L2 cache.** That is the payoff for making
surface and material separate axes (DESIGN.md §7.2), and it is what makes doors, gates,
portcullises and signals affordable: dynamic state is a table flip, not a re-derivation.
The contrast is gated too — a *real* edit bumps the version and misses.

This added one function, `material_set_solid` — the only API this phase needed.

### The platform — exactness where it is safety-critical

A platform is an **offset** of the centreline, which P1 already gives exactly: the offset
of a straight is a straight, of an arc a concentric arc. Equidistance is never
approximated. That matters more here than anywhere else, because the offset distance is a
**stepping gap a person crosses**, not a rendering nicety.

Building the platform as a **chord** against a curved track — what any polyline- or
mesh-first pipeline does by default — costs `L²/(8R)`:

```
   R=26, L=14.2 chord platform:  gap error 0.937   (L²/8R predicts 0.921)
   concentric platform:          gap error 3.6e-15
```

At R=26 the chord error is **62% of the stepping distance itself**, and grows as `L²`. On a
curve a platform must be concentric — and the surface layer makes the correct version the
free one. A mesh-first pipeline has no way to even express the distinction.

Even a concentric platform is flattened to chords to reach cells, but its tolerance is a
physical gap rather than a visual error, so it needs a **finer chord than the track it
serves**, `c = √(8·R·g)`:

```
   tol 0.5 -> chord 10.20      (rendering)
   tol 0.05 -> chord 3.22      (stepping)     ~3x finer
```

**Gates** `src/levelxtest.loft`: unequal-width crossing traces to one validated loop, is
genuinely shared, has zero cuts between way cells · a barrier toggle changes `solid` while
leaving both edge sums bit-identical · the cache hits after a toggle and misses after a
version bump. `src/platformtest.loft`: straight and concentric offsets exact to float
noise · `offset_legal` on the inside of the curve · the chord platform genuinely fails and
matches `L²/8R` within 15% · the flattening chord respects its tolerance at three scales ·
track and platform are adjacent but disjoint · the platform face cuts against the track ·
one validated loop.

## 9. Signals and signal sighting (P10)

A signal is trivial as an *object* — a point beside the track at an offset, which §8 already
made exact. The engineering is entirely in whether a driver can **see** it, and that is the
first real query against the L2 field. It needed two additions: `hex_at` (the world→cell
inverse) and `sight_clear`.

### Sight is blocked by opacity, not solidity

This is the payoff for materials carrying a *vector* of transmission terms rather than one
flag (DESIGN.md §7.2). Sighting is the first consumer to read one axis while deliberately
ignoring another, and it separates three obstructions no single flag could:

| obstruction | solid | opaque | movement | sight |
|---|---|---|---|---|
| palisade fence | ✓ | ✓ | blocked | **hidden** |
| chain-link fence | ✓ | ✗ | blocked | **visible** |
| hedge | ✗ | ✓ | passable | **hidden** |

A one-bit "wall" cannot express rows 2 or 3, and both are ordinary lineside furniture.

### Height decides by position

The sight line rises from eye to signal head, so an obstruction blocks only while the line
is still below its top — crossover at `t = (h − z_eye)/(z_sig − z_eye)`. With a 3.0 wall,
eye 2.5, head 5.0, the crossover is `t = 0.2`: measured hidden at `t = 0.1` (line at 2.75)
and visible at `t = 0.5` (line at 3.75). **The same wall hides the signal from near and not
from far**, which is the railway sighting problem, and it falls out of the geometry rather
than being special-cased.

### The cutback on a curve is the same chord constant, again

On a curve the sight line is a chord, cutting inside the arc by `R(1 − cos(D/2R))` ≈
`D²/(8R)` — the clearance the inside of the curve must be kept free to. Swept at 0.25
resolution on R=26, D=27.2:

```
   deepest blocking intrusion  4.00
   predicted                   4.08  =  sagitta 3.48  +  halfwidth 0.6
```

The half-width term is not a fudge: the sweep moves the obstruction's *centreline*, but
what fouls the chord is its near **face** — which is also how a real cutback is specified,
clearance to the face of the cutting, never to its middle.

`L²/(8R)` has now set the flattening error (§P1), the platform chord gap (§8) and the
sighting cutback (here). **It is this system's one chord constant**, and three unrelated
questions reduce to it.

### A wrong shape that taught something

The first version of this gate placed the obstruction as a straight **tangent** to the
inner radius, and nothing ever blocked. A tangent at the inner offset is *parallel* to the
chord, so it cannot cross it at any depth. Only a **concentric** obstruction fouls sight —
which is exactly why cuttings and embankments on curves are specified concentrically. The
failing test was right and the scene was wrong.

**Gate** `src/sighttest.loft`: `hex_at` round-trips all 625 cells of a chunk and agrees
with `hex_grid::px_to_hex` on 400 off-centre points (no convention drift) · the three
obstructions above resolve movement and sight independently · the height crossover is
measured either side · the swept cutback boundary lands within 0.1 of sagitta + halfwidth.

## 10. Bridges and tunnels (P11) — the level

Everything before this was flat: a cell is marked or not, an edge blocked or not. A bridge
breaks that outright — the road and the railway occupy the **same cells** and do not
interact at all. This is where the model has to answer whether it was really 2D.

It was not, quite. The answer is a **level**: the topological sheet a way sits on. That is
exactly OSM's `layer` tag, so it is already in the data plan #1/#8 reads. A level is **not
a height** — the actual z comes from the surface/feature interval, which sighting already
uses. Two ways on different levels never arbitrate, the L2 cache gains one key field, and
most of the world (level 0 only) costs nothing extra.

The sharpest statement of the phase is the contrast with §8 — **the same two ways**:

```
   rail alone     25 cells, 204 edges
   same level     73 cells, 384 edges   -> a level crossing
   level 0        25 cells, 204 edges   -> bit-identical to the rail alone
```

Nothing about the ways changed; only the sheet. And the levels genuinely share ground plan
(2 cells occupied at both), so this is not two disjoint things pretending.

**A bridge is not weightless.** The piers do land at level 0 and must clear the running
line's structure gauge — gated at 4 pier cells, 0 fouling.

### Who climbs

Reaching clearance `h` at gradient `g` costs a ramp of `h/g`:

```
   rail 1:100 (mainline)   ramp 500
   rail 1:30  (steep)      ramp 152
   road 1:20               ramp 100
   road 1:10               ramp  50
```

The road ramp is **10× shorter**, so the road climbs and the railway stays level — the
standard arrangement, here as a derived quantity rather than a convention.

### The chord constant, a fourth time

A gradient change `Δg` over vertical radius `Rv` gives `L = Rv·Δg` and offset `L²/(8Rv) =
Rv·Δg²/8`. The same sagitta that sets flattening error, the platform chord gap and the
sighting cutback also sets the **vertical** curve. Four unrelated questions, one constant.

### The tunnel is the same operation with the opposite sign

The bore sits at level −1, the ground above at level 0 untouched — gated bit-identical to
the road derived with no bore present at all. The bore's own walls are opaque, so sight
runs **along** it and not **through** its side (both directions gated), reusing `sight_clear`
unchanged.

**Gate** `src/bridgetest.loft`: the same-level pair interacts and the cross-level pair does
not (edge sets compared bit for bit) · the levels share cells · piers land at level 0 and
foul nothing · the ramp comparison · the vertical-curve identity to 0.1% · sight along vs
across the bore · the ground above the bore is unmarked · the cache holds both levels of
one chunk in distinct slots, both hitting, with an underived level a clean miss.

## 11. Stairs (P12) — the first per-cell height

Stairs are a small feature and a large test. Everything before them got by with height on
the *material* — how tall a wall is. A staircase is different: each step **is** a floor at
a different level, so the height belongs to the **cell**. That is a new structure,
`Heights`, deliberately kept separate from `HexSet` — most of the world is flat and should
not pay for a height it never reads, and a height field is *derived* (from a way, a
contour, a terrace) exactly as the edge field is.

It also needed `way_param`, the arc length from the start of a way to the nearest point on
it. That is the **milepost**: the parameter stations, signals, steps and mileage markers
are all stated in, and nothing before this had a reason to compute it.

### The minimum tread has a closed form — and it contradicts the width result

Two adjacent cells are `√3` apart, and their along-way parameters differ by that separation
projected onto the heading. A double riser (two adjacent cells two steps apart — a trip
hazard, and a discontinuity in the field) needs that difference to exceed one tread, so:

```
   min tread(θ) = √3 · max over the six neighbour directions |cos(θ − 60k°)|
```

Neighbour directions are multiples of 60°, so this ranges only over `√3·cos30° = 1.50` to
`√3 = 1.73`. Measured against the closed form by sweep:

```
     0° edge       1.70   predicted 1.73
    30° vertex     1.40   predicted 1.50
    15° off-axis   1.70   predicted 1.67
    75° off-axis   1.70   predicted 1.67
```

**A spread of 15%.** That is worth stating loudly because it is the *opposite* of the
width result, where bed width varies by 256% across the same 24 headings. Quantisation is
not one property of the grid — it depends entirely on which question is asked of it, and
the direction tiers established for width do **not** transfer to tread. All 24 headings are
clean at tread 2.0 with the worst riser exactly `rise`.

### The nosing line is the sight line

On a staircase every nosing lies on the pitch line by construction. So looking up a flight,
each nosing hides the tread behind it, and a tread is visible only from **above** the pitch
line — which is why you cannot see the back of a tread from the foot of a steep flight.
Gated with `sight_clear` unchanged: eye at z=0.3 (below pitch) cannot see a tread at z=3.0;
eye at z=6.0 (above pitch) can.

**Gate** `src/stairtest.loft`: all 24 headings clean at tread 2.0 with worst riser exactly
`rise` · the minimum clean tread matches the closed form within one sweep step on four
headings · monotonicity along the flight (0 inversions — a flight only ever goes up) · 40
riser edges across 9 step levels · the pitch-line sight test either side.

## 12. Curved and spiral stairs (P13) — and the field's resolution floor

Curving a flight turns the tread from a rectangle into an annular **sector**, so the going
varies across the width: `going(r) = r·dφ`. Two consequences, pulling opposite ways.

### A grand curved stair needs no new machinery

`way_param` already measures arc length at the **centreline** — which is exactly the
walking-line convention a builder uses — so `way_steps` on an arc produces correct sector
treads unchanged. Measured at R=10, width 2: 29 cells, 7 steps, worst riser exactly `rise`.

The taper is `going_outer/going_inner = r_outer/r_inner`, **independent of dφ**: dividing
the stair 2.5× finer leaves the taper at 1.5. So the taper is set by the radius ratio
alone, and keeping it under 2 needs `r_inner ≥ width`.

### The bound is on the narrowest going, and it is the same number

Sweeping the tread at three radii gives three different minimum treads — but converted to
the going **at the inner edge**, they land on one constant:

```
   R=8  (r_in 6)    min tread 2.2   ->  inner going 1.65
   R=12 (r_in 10)   min tread 1.9   ->  inner going 1.58
   R=16 (r_in 14)   min tread 1.8   ->  inner going 1.58
```

That is the same `√3`-ish bound the straight flight measured. **The constraint is always on
the narrowest going, wherever on the tread it occurs** — which is also how building codes
state it.

### A small spiral stair is below the floor — and that is a statement about the model

The narrowest going must clear the grid bound, so `dφ ≥ 1.73/r_inner`. That exceeds a full
turn once `r_inner < 0.276`: **not one tread fits**. A domestic spiral (`r_inner ≈ 0.2`)
needs a 496° sector. Gated exhaustively — of 60 tread values swept, **zero** produce a
clean 4-step stair.

This is the valuable result, because it is not a tuning failure. **The field has a
resolution floor at `r_inner ≥ √3/2π ≈ 0.276`, and a feature below it is not a badly-tuned
field — it is an OBJECT**: one cell carrying a surface, like a tree or a piece of
furniture. Knowing exactly where that floor sits is what tells you which representation a
thing belongs in.

### More than one turn is the bridge problem again

Two revolutions overlap in 120 cells, so one height field cannot hold both — a spiral is a
**stack of levels, one per revolution**, reusing §10 unchanged (three revolutions cached as
three distinct slots). And headroom is the bridge-clearance rule wearing a hat: after one
turn you pass over your own head, so `N·rise ≥ headroom + soffit`.

### A bug this found

`seg_param` wrapped a point sitting just *before* an arc's start into `+2π` and then clamped
it to the arc's **end** — handing the first cell of a flight the height of the last one, a
full-flight riser between two neighbouring cells. The clamp now snaps to the *nearer* end.
Found by the gate, not by inspection; it would have corrupted every arc milepost query.

**Gate** `src/spiraltest.loft`: the grand curved stair is clean with worst riser exactly
`rise` · the taper is invariant under subdivision · the threshold inner going is constant
across three radii · the sub-grid spiral admits no clean tread out of 60 swept and its
required sector exceeds a full turn · two revolutions overlap and cache as distinct levels ·
the headroom rule at three rises.

## 13. Roofs, cones and arches (P14) — the form is the footprint

With a height per cell, "real architecture" is mostly roof profiles — and they are not a
catalogue of cases. Every named form is the same function of a **distance**, with only the
distance *source* changing:

```
   d = |p − c|            a point     ->  cone / pyramid
   d = dist to a line     a line      ->  gable
   d = dist to a SEGMENT  a segment   ->  hip
   d = dist to the FOOTPRINT boundary ->  any of them, correctly (below)
   d = 0                              ->  flat
```

**A hip is a gable with a shorter ridge** — literally the same call with a shorter `Track`,
because `track_distance` clamps to the segment. Gated: 176 cells differ beyond the ridge
ends and **0** between them, which is exactly what hipping means.

### The cone on a round tower — where it goes wrong, and why

The hard case, for a reason that has nothing to do with cones. A round tower's footprint is
a hex *approximation* of a circle, so its boundary cells sit at a spread of true radii —
all of them *inside* the nominal radius. Drive the roof from each cell's own radius and the
eave inherits that spread:

```
   from the ideal circle:   eave spread 0.807  =  slope × 1.009 cells of radius
   from the footprint:      eave spread 0      (4 rings to the apex)
```

That 1.009 is the footprint's **roundness deviation** — the same quantity the tower catalog
measured. Clamping at the nominal radius does *nothing*, because no cell ever exceeds it;
this was the first attempt and it failed silently, with the apex looking perfect and only
the eave wrong.

The fix generalises into the real answer: **drive the roof from the distance to the
FOOTPRINT, not to the ideal shape.** Boundary cells are at ring 0 by definition, whatever
their true radius, so the eave is level by construction. And that single function — a
multi-source BFS inward from the boundary — *is* a hip roof:

```
   round tower (85 cells)     4 rings, eave spread 0, ponds 0   -> a cone
   octagon tower (77 cells)   4 rings, eave spread 0, ponds 0   -> a pyramid
   rectangular hall (247)     6 rings, eave spread 0, ponds 0   -> mitred hip-and-valley
```

**The form is entirely the footprint's shape.** One call produces a cone, a pyramid or a
properly mitred hip-and-valley depending only on what it is given. That is why the list of
roof forms stopped being a list.

The apex is a flat **hex**, not a point — quantisation costs at most `slope × circumradius`
(gated at exactly 1 apex cell).

### Drainage is the roof's correctness invariant

An interior cell all of whose neighbours are strictly higher is a local minimum: water
collects and never leaves. A roof that sheds has none — the analogue of a stair's
monotonicity. Gated 0 on every form above, **with a negative control**: denting one interior
cell must report ponding, and does. Without it the check could pass by never firing.

### Arches — the same mechanism, inverted

A roof is the upper surface of a solid; an arch the lower surface of an opening. Same
function, opposite curvature — which is why a cell wants a floor height *and* a soffit
height rather than one z. A semicircular arch, springing 2.0, half-span 5.0:

```
   admits a 2.5 figure:  27 cells
   admits a 6.0 figure:  17 cells, reaching |x| = 2.60   (predicted √(25−16) = 3)
```

**What can pass depends on where you stand** — the clear height varies continuously between
the pillars, and the tall figure is confined to the middle of the span. The same call with
a flatter radius gives a segmental arch: less headroom at the crown, but the clear height
varies by 1.11 instead of the semicircle's full 5.0.

**Gate** `src/rooftest.loft`: gable/hip differ only past the ridge ends · the ideal-circle
cone's eave genuinely wobbles and the footprint-driven one is dead level · cone, pyramid and
hip-and-valley from one call, all pond-free with level eaves · a single apex cell · the
ponding negative control fires · the arch admits fewer cells to a tall figure than a short
one, within the predicted reach · the segmental profile is flatter than the semicircular.

## 14. Reading the form back out (P15) — draw the cone, not the hexes

Storing a roof as per-cell heights is compact and it composes, but it is **not the shape**.
A renderer that draws the stored cells draws a staircase of hexes wearing a cone. So the
height field needs the service hexmatch already gives a traced 2D boundary: read the values
back, decide the profile, recover its exact parameters, hand the renderer an analytic
surface. Same principle, one dimension up.

The invariant is the design protocol's — **round trip = identity**:

```
   analytic cone in:   centre (0,0)      apex 12.0    slope 0.80
   recovered:          centre (0,0)      apex 12.0    slope 0.80    residual 1.3e-13
   off-centre cone:    (2.31, −1.44)  ->  recovered to 0.0006 / 0.0025
```

The off-centre case is the one that matters: the apex **cell** is only within a circumradius
of the true apex, so a matcher that stopped at the seed would be out by up to 1.0. The
refinement is what makes recovery exact rather than approximately right.

And the negative half matters as much — **the matcher must refuse to name what it does not
know**. A gable's iso-height sets are parallel line pairs, neither circles nor a plane, so
it comes back with a residual of 4.47 against a 0.05 tolerance. A confident wrong shape
would be far worse than an admitted unknown.

### Only the cone needs any of this

A shed, a gable, a hip, a pyramid are made of **flat facets**, and linear interpolation
between stored cell heights reproduces a flat facet *exactly*. For those, storing the cells
**is** storing the shape: interpolate and draw, no matcher, no recovery, no analytic form.
Measured at every adjacent-cell midpoint:

```
   shed  (one plane)     worst 1.8e-15
   gable (two planes)    worst 3.6e-15
   cone  (curved plan)   worst 0.186  at r=1.5   (slope·L²/8r predicts 0.200)
```

The cone is the sole exception because it is curved **in plan**: interpolating between two
neighbours chords a circle, and the error is `slope·L²/(8r)` — the chord constant for the
**fifth** time, after flattening, the platform gap, the sighting cutback and the vertical
curve. It is **worst at the apex**, where `r` is smallest — precisely where a spire's
silhouette is most visible.

One refinement the gate found: a gable is exact everywhere *when its ridge lies on a cell
row*, because then no pair of neighbours straddles the crease. Move the ridge between rows
and the crease costs 0.525 — but still **only at the crease** (4e-16 more than 2 units
away). So a planar roof's accuracy is a question of where its creases sit relative to the
grid, not of whether the grid can represent it.

**The rule: interpolate planar roofs; recover only cones.**

**Gate** `src/roofmatchtest.loft`: analytic cone round-trips to 1e-13 · an off-centre cone
recovers its centre to 0.003 where a seed-only matcher would be out by 1.0 · a shed comes
back a plane with exact coefficients · a gable is refused rather than mis-named · a
boundary-driven hip still reads as a cone with its ring quantisation *reported* not hidden ·
planar interpolation is exact to 1e-15 and the cone's error matches `slope·L²/8r` · the
off-row crease costs only at the crease.

## 15. Domes and vaults (P16) — the table closes

Domes and vaults add no third idea. Every form in this plan is a **profile** applied to a
**distance**, and these fill in the rest of the table:

| distance source | linear profile | circular profile |
|---|---|---|
| point | cone / pyramid | **dome** |
| line | gable | **barrel vault** |
| segment | hip | hipped barrel |
| min of two lines | two gables | **cloister vault** |
| max of two lines | butterfly | **groin vault** |

### The two classical vaults are one operator apart

Same two barrels over the same bay. **Groin takes the max**, so both crown lines stay at
full height and every wall keeps its arch. **Cloister takes the min**, so the vault springs
continuously from all four walls and nothing opens. In code that is `if b > a` versus
`if b < a`; in a building it is whether you can put a window in the wall:

```
   middle of a wall:  groin 9.00    cloister 2.45
   on the diagonal:   groin 8.49    cloister 8.31   (agree to 0.18 — the groin/arris line)
```

The cloister's 2.45 is not a residue of failure: it is exactly `√(9² − 8.66²)` at the last
cell **centre**, which sits inside the wall. The vault really does spring; the number is
where the sample is. Gated against that prediction rather than a chosen threshold.

### The dome has a slope ceiling, as the spiral stair had a resolution floor

A cone's slope is constant; a dome's **diverges** at the springing
(`dz/dr = −r/√(R²−r²)`). Past the 45° point at `r = R/√2` a per-cell height cannot carry
the surface:

```
   inside  r = 5.94:  worst one-cell drop 1.85
   outside r = 5.94:  worst one-cell drop 2.87
```

Outside it, one cell spans more height than a storey — **that band is a wall (a drum), not
a roof.** Which is how domes are actually built. This is the second boundary of the field
model found in this plan, and the pair is worth stating together: a **resolution floor**
(§12, the spiral stair) and a **slope ceiling** (here). Between them the field is the right
representation; outside them the thing is an object or a wall.

### Recovery extends cleanly, and still refuses

The dome fit is linear after one substitution — from `z = base + √(R²−r²)`,
`(z² + r²) = 2·base·z + (R² − base²)`, so regressing `(z²+r²)` on `z` returns base and
radius directly, with the centre refined by the cone's search:

```
   dome:  base 3.000 (vs 3.0), radius 8.400 (vs 8.4), residual 6.5e-14
   cone:  still recovered as a cone, residual 1.3e-13   (the two are not confused)
   groin vault: refused, residual 3.70 against a 0.05 tolerance
```

And the interpolation error goes the *opposite* way from a cone: a cone's peaks at the
**apex**, a dome's at the **springing** (0.098 inside the 45° point, 0.323 outside).
Opposite ends, same conclusion — recover the analytic form, never draw the cells.

**Gate** `src/vaulttest.loft`: the dome is pond-free and its one-cell drop is larger
outside the 45° point than inside · groin and cloister differ at the wall and agree on the
diagonal, with the cloister's wall soffit matching its predicted value to 0.02 · the barrel
crown line is dead level · dome and cone each recover as themselves · a groin vault is
refused · dome interpolation error is worse at the springing than at the apex.


## 16. Trees — moved out

Canopy-first trees were designed here and have moved to their own plan: **#9
(`plans/9-canopy-trees/`)**. They share this plan's substrate completely — same hexes,
chunks, levels, cache, `Heights`, materials — but invert the derivation direction (the
field is primary, the form is derived) and carry their own rendering model (semi-filled
cards, not surfaces). That makes them a *consumer* of this geometry library rather than a
phase of it. This plan stays the library.
