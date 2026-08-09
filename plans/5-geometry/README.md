# 5 — Geometry: the 24-direction outline engine + multi-layer towers & walls

**Issue:** [`jjstwerff/crawler#5`](https://github.com/jjstwerff/crawler/issues/5) ·
**Value:** `F` · **Effort:** `VH`

**Anchors:** `WALLS.md` · **`FORMS.md`** (the kit-of-parts requirements — DESIGN SESSION,
no geometry pinned) · **`STENCILS.md`** (layered composable stencils → castles; consumed by
this plan's later phases). ⚠ Both are DESIGN docs; their schedule and step status live
here, so progress is never recorded twice.

## Status

**ACTIVE — blueprint phase running** (2026-07-21). `plans/5-geometry/hexforms.py` is the
bench; first results below. Neither loft track has landed, and `wallgeo.loft`'s
corner-graph smoother is still today's stand-in. This plan **blocks the theme-bundles
plan (#4) Phase G**: themed structures need doors, jambs and round forms before their
shapes can move bundle-side.

## The deliverable — a library emitting a VALIDATED vector map

The routines are **library-grade**, not crawler-internal: reusable across games and
editors, so the contract carries no consumer-specific knowledge.

```
   tagged hex cells  ──►  VECTOR MAP (exact loops)  ──►  2D renderer
                                    └───────────────►  mesh / extrusion
```

Three properties make it trustworthy:

**1. Exact integers, not floats.** For pointy-top odd-r with circumradius 1, every hex
centre *and every hex corner* lies on the lattice

```
x = k · √3/2      y = m / 2        (k, m INTEGER)
```

with `centre(c,r) = (2c + (r&1), 3r)` and the six corners at
`(0,±2), (±1,±1)`. So the vector map is stored as integer `(k, m)` pairs — no float
drift, no epsilon compares, and a **golden JSON diff is exact** rather than tolerant.
Consumers multiply by `(√3/2, ½)` once, at the end. (A 2D golden *image* is the usual
route; here the point list is strictly better because it is exact.)

**2. A round-trip invariant that cannot be fudged.** A single hex shoelaces to exactly
`12` in lattice units, so for any cell set:

> **Σ integer shoelace over all loops == 12 × (number of hexes)**, holes negative.

Cell count and traced outline can never disagree — the vector map *provably* describes
the hex set it came from. This is the geometry counterpart of "round-trip = identity".

**3. A validator, because the data fed to a renderer/mesh must be checked.** Before any
consumer sees it: loops closed · every segment an actual hex edge · no zero-length
segment · no repeated vertex (self-touching) · vertices integral (no lattice drift) ·
exactly one outer loop, holes wound opposite · the area round-trip above.

## Blueprint findings (`hexforms.py`, 2026-07-21)

Bench: `python3 plans/5-geometry/hexforms.py` (report + PNG + golden JSON);
`--check` re-runs it as an exact gate. Add a routine = add one lambda.

- **Today's `stamp_round_tower` really does ship a hexagon.** Confirmed visually at
  N=5/6: `hex_distance ≤ N` has six flat sides. FORMS.md's stated contradiction — code
  that wants a circle's *look* but ships a hexagon's *shape* — is real, not theoretical.
- **The families are indistinguishable when small** — FORMS.md predicted this and asked
  for the cutoff `K`; the bench measures it:

  | N | A hex-disk | B circle | C octagon | |
  |---|---|---|---|---|
  | 1 | 7 | 7 | 7 | all identical |
  | 2 | 19 | 19 | 19 | all identical |
  | 3 | 37 | 37 | 35 | octagon separates |
  | 4 | 61 | 73 | 55 | all distinct |

  So **octagonal is not worth offering below N=3**, and round-vs-hexagon is only a real
  choice from **N=4**. Below that, one "small tower" family is the honest model.
- **The annulus works.** Tracing the *wall ring* (not the filled disk) yields exactly
  **2 loops** — outer + inner hole, correctly wound, area round-trip exact. That is the
  form a mesh routine extrudes.
## Is a hexagon still right for BIGGER towers? — measured, not argued

The footprint is reused for the drawn form, for **collision**, and probably for the same
rounding model on **curved roads**. So it is a systems question. `roundness.py` measures
the collision surface (effective radius per approach direction, ray-cast on the emitted
outline) and `deviation.py` measures per-point distance from the ideal circle, in **hex
widths** (1.0 = a whole hex out of place).

| | A hex-disk | B circle | C octagon |
|---|---|---|---|
| anisotropy `r_max/r_min` @N=5 | 1.192 | 1.109 | 1.140 |
| anisotropy @N=10 | **1.170** | **1.080** | 1.184 |
| worst inward error @N=8 | −0.766 | −0.469 | −0.208 |
| worst inward error @N=10 | **−1.037** | −0.427 | −0.458 |
| deviation band @N=10 | **1.541** | 0.887 | 1.562 |

**Verdict: no — not at size.**

1. **A's directional error is a structural constant that never improves.** It converges
   to ≈1.17 and stays: that is the hexagon's circumradius/inradius ratio (2/√3 = 1.1547),
   a property of the *family*, not of the raster. A bigger hexagonal tower is not a
   rounder one. B's anisotropy *falls* with size (1.19 → 1.08) because more cells buy a
   better circle.
2. **A's absolute error grows linearly.** Worst inward deviation goes −0.113 → −0.381 →
   −0.766 → **−1.037** hex widths at N=3/5/8/10. At N=10 the flats sit **a full hex
   inside** the circle it claims to be — you would see and feel the corner-vs-flat
   difference walking around it. B stays bounded (~0.43–0.47).
3. **Roads decide it outright.** `hex_distance ≤ N` is only definable *from a hex centre
   with integer N*. It cannot express "an arc of radius 4.30 centred between two hexes" —
   a road bend. A distance predicate can: centre and radius are free, and the *same*
   routine then measures a tower and a road bend with no code change (verified — `Arc`
   in `deviation.py` scores a rasterised bend at rms 0.351 hex widths). If one model is
   to serve both, A is disqualified by expressiveness, not by degree.

**Recommendation.** Keep **A below N=3** — the families are byte-identical there anyway
(7 and 19 cells), so it is the cheapest correct choice and stays trivially matchable.
Use **B (Euclidean distance predicate) from N=4 up**, and use it for roads. C (octagon)
earns its place only as an authored *architectural* choice, not as a rounding model: it
is erratic on both metrics because 8-fold symmetry fights the 6-fold grid.

This confirms FORMS.md's hypothesis ("A for small N, B once N is large enough") — which
that doc explicitly flagged as *"a hypothesis to plot, not a decision yet"*. Now plotted.

## The objective is BEST COLLISION MATCH — not an exact radius

Sharpened (user direction): we are not trying to reproduce a circle of radius `r`. The
rasterisation threshold is only a knob for generating candidates; what matters is that
the footprint is the best circle a **collision query** can experience. So `r` is an
**output** of the fit, not an input:

- generate candidates by sweeping the threshold, keeping only footprints that pass the
  validity battery (no enclosed gaps, wall one hex thick, nested in the rung below);
- ray-cast the emitted outline for the effective radius `r(θ)` a collision query sees;
- fit `R = mean r(θ)` (which provably minimises `Σ(r−R)²` for a centred shape);
- rank by **worst-case** error `max|r(θ) − R|` — collision is felt at its worst point,
  not on average.

**This killed the formula.** An earlier pass proposed `r(N) ≈ 1.069·N·√3`; that is
withdrawn. Under the collision objective, "radius N" is not a meaningful index for the
round family at all — N=5 and N=6 both optimise to the *same* 121-cell footprint, N=8 and
N=9 both to the same 253-cell one. The honest artifact is a **frozen catalog indexed by
effective radius**, not a formula. (FORMS.md already proposed freezing *octagons* as
authored hex-sets; the measurement says the round family needs the same treatment.)

### The catalog — `golden/tower_catalog.json`

Nested chain, generated by `collision_fit.py`. `R` in hex widths; `worst` = worst-case
collision error in hex widths.

| rung | cells | wall | R (hexw) | worst | aniso | |
|---|---|---|---|---|---|---|
| 1 | 7 | 6 | 1.383 | 0.229 | 1.321 | hex-disk **is** optimal here |
| 2 | 19 | 12 | 2.284 | 0.233 | 1.207 | hex-disk **is** optimal here |
| 3 | 37 | 18 | 3.189 | 0.322 | 1.216 | hex-disk **is** optimal here |
| 4 | 55 | 24 | 3.888 | 0.388 | 1.189 | |
| 5 | 85 | 30 | 4.837 | 0.337 | 1.140 | |
| 6 | 121 | 36 | 5.772 | 0.330 | 1.109 | |
| 7 | 163 | 42 | 6.700 | 0.388 | 1.116 | |
| 8 | 199 | 48 | 7.404 | 0.377 | 1.105 | |
| 9 | 253 | 54 | 8.349 | 0.375 | 1.087 | |

**Worst-case error is BOUNDED at 0.229 … 0.388 across the whole range** — it does not
grow with size. Compare the hex-disk, which does: 0.233 → 0.413 → 0.596 → 0.777 → 0.961
at N=2/4/6/8/10.

**The sharpest result: the hex-disks are the ladder's error MAXIMA.** Every hex-disk
appears as a rung — 37 (0.322), 61 (0.413), 91 (0.505), 127 (0.596) — and from 61 up they
are all *excluded* by the 0.39 threshold. The hexagon is the **worst** circle
approximation among valid footprints of its size. Below 37 cells it is the optimum only
because nothing better exists (the families are byte-identical there).

So the earlier "A below N=3, B from N=4" recommendation survives, now with the actual
frozen hex-sets rather than a fitted curve.

## Road arcs — and the quantisation floor they hit

`road_arcs.py` runs the same collision-match ladder on **bands around an arc**, with the
effective half-width as the fitted output. Deliberately uses **off-lattice centres and
non-integer radii** — the thing `hex_distance` cannot express at all.

- **Bends do not break it.** Width held at ~1.0 hex widths, worst-case error is
  0.569–0.658 across bend radii from 2.0 to 13.0 hex widths — a very tight bend is no
  worse than a gentle one.
- **Off-lattice centres are fine.** Nudging the centre off the lattice in seven steps:
  worst-case 0.454–0.606. Bounded, no degradation. The expressiveness claim is now
  quantified, not just argued.
- **But the error will not go below ~0.5 hex widths.** Unlike the tower catalog
  (0.23–0.39), a band cannot do better, because its two edges quantise *independently*
  while a closed circle fit can re-centre and cancel error.

**Quantisation scale, stated correctly.** A hex corner sits `1/√3 = 0.577` hex widths from
its centre, so an outline vertex lies in `[t−0.577, t+0.577]`; the spread reaches 1.155
and `max|d−W|` is bounded by **1.155, not 0.577**. So 0.577 is the *characteristic* scale,
not a hard bound — an earlier draft of this section claimed it as a bound and the bench
promptly measured 0.658, which is what corrected it.

## The 3-LINE construction — the PRIMARY model for every way type

**Decided:** roads use this too, not just railways (`ways.py`). Do not derive a way from
a rasterised band. Author **one exact centreline**; everything else is an offset of it:

```
    bed_left      centre − bed/2
    rail_left     centre − gauge/2
==> CENTRELINE    the authored truth
    rail_right    centre + gauge/2
    bed_right     centre + bed/2
```

### Tolerance is ASYMMETRIC — rails tight, bed loose

The precision requirement is not uniform (user direction): **the rails must be right; the
stone bed under them does not matter.** That splits the budget and settles which
representation each line gets:

| line | tolerance | representation |
|---|---|---|
| **rails** | tight — gauge must hold | exact offset of the centreline, flattened to a stated tolerance |
| **bed edges** | loose — nobody measures ballast | the rasterised hex band is fine (0.45–0.66 hex widths) |

So the two findings above are not in competition: the band ladder is the right tool for
the bed, and the offset construction is the right tool for the rails.

Two invariants pinned, both verified:

- **I-EQUI — equidistance, stated correctly.** A parallel curve is equidistant *by
  definition* for any smooth centreline, and for straights and circular arcs it is also
  *exactly representable* (the offset is another straight / concentric arc — measured
  deviation 0.0 to float precision). What actually costs accuracy is **flattening** the
  offset to a polyline: the chords cut inside the true curve.
  - An earlier test here claimed exactness across a clothoid too — but it was
    **circular**, measuring each offset point back to the sample that generated it, which
    is `d` by construction. Measuring *along the chords* gives the real number.
  - Convergence is quadratic, `err ≈ c²/(8R)`, confirmed: error falls ~4× per doubling
    (0.694% → 0.179% → 0.046% → 0.011% → 0.003% of gauge at 8/16/32/64/128 segments over
    a 6-unit transition at R=9).
  - **Practical rule: `chord = √(8·R·tol)`.** So "near-exact" is cheap — name a rail
    tolerance and the flattening density follows; the only cost is vertices.
- **I-CURV — an offset degenerates when `|d| ≥ R`.** Tightening the centreline with
  bed = 3.0: R=2.0 → inner 0.50 ok; R=1.5 → inner 0.00 **collapses to a point**;
  R=1.0 → inner −0.50 **folds through the centre**. This is exactly a railway's
  **minimum curve radius**, and it falls out of the geometry rather than being a
  tuning constant: `R > bed/2`.

**This beats the rasterised band by orders of magnitude where it matters** — 0.45–0.66
hex widths becomes ~0.0001 hex widths for the rails at a reasonable flattening density.
The hex cells keep doing collision/occupancy; they stop being the geometry.

### The new seam requirement: G2

FORMS.md's seam law covers **G0** (no gap) and **G1** (no kink). Track needs one more.
Measured at a straight↔arc join: G1 kink is `0.00000°` — perfect — but curvature jumps
`0 → 0.111` (=1/R). On a railway that discontinuity is a lurch, and it is what a
**clothoid / Euler-spiral transition** exists to remove. So:

> **G0 position · G1 tangent · G2 curvature** — track is the first part family that needs
> all three. Worth deciding whether the *road* family wants G2 too before either ships.

### One construction, three way types — the unifying insight

A way PROFILE is just a list of `(offset, kind)`. The observation that unifies the family
(user): **the inner offset pair is the same thing everywhere** — it is rails on a railway,
**wheel ruts** on a dirt track, and lane markings on a modern road. The "gauge" is a rail
gauge, a cart axle, or a lane width. A wagon rut *is* a gauge, which is why equidistance
matters as much on a dirt track as on rail.

| profile | inner pair | outer pair | centre |
|---|---|---|---|
| `railway` | rails @ ±gauge/2 | bed edges | the track centreline |
| `dirt_track` | **wheel ruts** @ ±axle/2 | worn edges | the grass strip between the ruts |
| `modern_road` | lane lines | road edges | the centre marking |

All three verified **EXACT** on I-EQUI with the same code path — the profile is data, not
a branch. This is what makes it library-grade: a new way type is a profile, not a routine.

**The rasterised road band is demoted to a fallback.** The ladder measured earlier
(0.45–0.66 hex widths) is now the quality you get *if you must rasterise* — for the bed,
for collision, for occupancy. It is not the primary representation of a road.

## Push-resistant walls — why the curves are load-bearing (`walls.py`)

For a wall-building game where attacks **push**, "correctly built" has a decidable
geometric meaning, settled before any force or material enters: **can a block be
translated inward without driving into its neighbours?**

A block sits between two joint faces with outward normals `n_i`. Translating by `u`
drives into that neighbour exactly when `u·n_i > 0`. So the block moves iff `u·n_i ≤ 0`
for *every* face — and is **LOCKED** the moment one face objects. With radial joints that
collapses to one scalar: **the signed turn angle across the block**.

| build | result |
|---|---|
| straight wall | faces parallel — block slides straight through, **20/20 pushable** |
| curved, attacker on the **convex** side | faces converge inward, block wedges — **all 18 LOCKED** |
| same wall, attacker on the **concave** side | faces diverge inward, block falls in — **all 18 pushable** |
| **closed ring** (a round tower) | **0 of 47 free** — cannot be pushed in anywhere; it can only *spread* |

**Curvature is the entire mechanism**, which is what makes the curve work load-bearing
rather than decorative. This is the arch principle read in plan view, and it is why a
round tower is the strong form.

### The game rule

The binary verdict turns out to be the wrong number to expose — *any* non-zero curvature
locks geometrically, but a 0.3° wedge is swamped by block irregularity and mortar. The
useful quantity is the **interlock margin**, and it has a closed form, verified against
the measured margin to three decimals across R = 2…200:

> **interlock margin ≈ block_length / (2 · radius)**

Tighter curve and **longer** blocks resist more; a straight wall scores exactly 0. That
is a designer-facing number a game can show and balance against, not a physics sim.

### Deliberately out of scope (flagged, not solved)

- **Global failure** — the ring spreading or forming hinges (classical thrust-line
  analysis). Local interlock proves a block cannot pass *through*; it says nothing about
  the wall opening *up*. A closed ring resists spreading; an open arc needs buttresses.
- **Friction** — a straight wall is not instantly pushable in reality, friction resists
  it. But it has no geometric interlock at all, so its strength degrades to a material
  property — precisely what a "correctly built" wall should not have to rely on.

**Method note.** The first run had the convex/concave convention inverted; the tell was
the closed ring reporting all 47 blocks *free*, which is absurd for a tower under siege.
The fix was to make the API say `attacker_convex` instead of `left`/`right`, so the
caller cannot express the ambiguity.

## 24 directions, and the minimum wall thickness (`directions.py`)

**All 24 headings (k·15°) produce a valid vector map** — representability was never the
question, only cost. A hex grid has 12 natural directions (6 edge-normal, 6 vertex,
30° apart); the other 12 are off-axis. Width-normalised, the cost is three-tiered:

| class | n | worst error (hex widths) | vs edge |
|---|---|---|---|
| **edge** normals | 6 | 0.149 | 1.00× |
| **vertex** directions | 6 | 0.251 | 1.68× |
| **off-axis** (15°) | 12 | 0.532 | 3.56× |

Leaving the lattice costs ~3.5×, which is bounded — prefer edge-normals when the choice
is free, but nothing is unusable.

> *Method note:* before width-normalising, this table appeared to show the **vertex**
> directions as worst of all. Artefact: a fixed nominal halfwidth yields 17/29/19 cells
> by heading, so the raw spread was measuring *width*, not direction. Fitting `W` per
> direction reversed the conclusion.

### A 1-hex wall is only a wall in 6 of the 24 directions

Tested by the property that actually matters — **does it block passage?** (flood the free
cells from one side and see whether they reach the other):

| wall | edge (6) | vertex (6) | off-axis (12) |
|---|---|---|---|
| **1 hex wide** | blocks 6/6 | **blocks 0/6** | **blocks 0/12** |
| **2 hexes wide** | blocks 6/6 | blocks 6/6 | blocks 12/12 |

At 30° a 1-hex "wall" is **5 disconnected cells**; at 45° it fragments into 3 — so under
this model it is not a barrier at all.

*(Correction: an earlier draft called these "vertex-touching". They are not. On a hex grid
two cells that share a vertex are always edge-ADJACENT, because every vertex touches
exactly 3 mutually-adjacent cells. The off-axis chains are simply **disconnected, with a
whole missing cell between links** — a plain gap, not a diagonal squeeze.)*

The geometric validator predicted this perfectly — its "exactly one outer loop" rule
agreed with the blocking test in **24 of 24** cases, so the cheap check catches the
gameplay bug.

### Wall WIDTH is not constant across the 24 headings

"We always start with a full hex" — but a hexagon is not rotationally symmetric at 15°
steps, so a full hex is not a constant thickness. Measured from the real corner geometry
(not cell centres):

**A single isolated hex**, perpendicular to the heading, takes exactly **three** values:

| heading class | width | in hex widths |
|---|---|---|
| vertex (30°, 90°, …) | 1.7321 | 1.000 — flat-to-flat |
| off-axis (15°, 45°, …) | 1.9319 | 1.115 |
| edge (0°, 60°, …) | 2.0000 | 1.155 — vertex-to-vertex |

That is a **15.5% spread**, and it is exactly `2/√3` — the same anisotropy constant that
governs the hexagon's collision error in the tower analysis. It is irreducible: it is the
shape of a hex, not an artefact of any algorithm.

**A one-hex-thick RUN.** A first pass reported vertex 1.732 / edge 2.000 / off-axis
2.172, a 25.4% spread — **that was wrong**, because it measured cell sets that are not
edge-connected. Requiring the run to actually be a connected chain gives a much sharper
and more useful answer:

| class | 1-cell connected run | in hex widths |
|---|---|---|
| edge | 2.000 | 1.15 |
| vertex | 2.598 | 1.50 |
| off-axis | **does not exist** | — |

At one cell across, an off-axis chain is vertex-touching, so there is no connected run at
all; and a vertex heading needs a *wider* envelope than an edge heading just to stay
connected. **A consistent 1-width wall across the 24 headings does not exist in the cell
model** — the phase knob has nothing to work with, because each heading admits exactly
one chain (or none).

That is the strongest argument in the whole section for either the ≥2-hex rule or the
edge model. It also shows why the smallest scale is the right stress test: the anisotropy
is a fixed absolute quantity, so it dominates whatever is thin.

### Optimising for CONSISTENT width — 25.4% spread becomes 1.5%

The goal is not an exact width; it is that the 24 headings read as **roughly the same**
thickness. Treated as an optimisation, that is achievable — the knob previously wasted is
the **perpendicular phase** (where the wall line sits against the lattice), not just the
band threshold. Sweeping both per heading and choosing the footprint nearest a common
target:

| class | optimised width | hex widths |
|---|---|---|
| vertex | 3.464 | 2.00 |
| off-axis | 3.485 – 3.517 | 2.01 – 2.03 |
| edge | 3.500 | 2.02 |

**Spread 1.5%** (3.464…3.517), down from **25.4%** with one fixed threshold. Every
heading blocks, and the wall lands at ≈2.01 hex widths ± 0.02.

Two consequences:

- **The deliverable is a per-heading `(threshold, phase)` table** — 24 entries, frozen
  the way the tower catalog is. Not a formula, and not something to recompute at runtime.
- **It only works at ~2 hex.** A 1-hex wall cannot be made consistent in the cell model
  because it does not block at all in 18 of 24 headings, so there is nothing to tune.
  Consistent width and the blocking rule point at the same minimum.

> *Caveat, honestly:* thicker walls resist a like-for-like comparison. "N hexes across"
> is not a clean notion on an offset lattice — a perpendicular slice picks up alternating
> rows, so a nominal 2-across in an edge heading actually spans three rows. The 1-across
> numbers above are sound; anything thicker needs a better-defined "across" before its
> numbers should be trusted. Two earlier attempts at this table were confounded by using
> a fixed *world* halfwidth, which silently varied the hex count by heading.

### …but that rule is MODEL-DEPENDENT — there are two wall models

The table above assumes **wall-as-CELL** (a wall occupies hexes; you move between free
cells). The alternative is **wall-as-EDGE**: the wall sits on hex *boundaries*, and since
a hex's 6 edges come in **3 orientations**, a wall line runs continuously through hexes
that are not themselves edge-adjacent. Under that model a wall is the **cut** between the
two sides — and a cut separates *by construction*:

| model | 1 unit thick blocks in | why |
|---|---|---|
| wall-as-**cell** | **6 of 24** directions | vertex-touching cells leave a diagonal gap |
| wall-as-**edge** | **24 of 24** directions | every move crosses exactly one edge; a cut has no gap |

Measured: the edge cut blocks in all 24 headings and forms **one continuous chain** in
every one; only its *length* varies with heading (44–63 edges for the same span), which
is the staircase cost, not a validity failure.

So the honest rule is conditional:

> **wall-as-edge:** 1 edge is always enough, any of the 24 headings.
> **wall-as-cell:** 1 hex only along the 6 edge normals; 2 hexes for any other heading.

Crawler is **cell-model today** (`tile_solid` tests a tile), so the 2-hex rule applies to
what is in the engine now. The edge model is the better primitive for *thin* walls and
fences and for collision generally; a thick wall can keep a cell footprint for its body
and features while its **collision** is the edge cut of that footprint. Which model the
kit adopts is an open decision — and it is the same question as FORMS.md's "are walls
full-hex tiles or bands?" (its open question 7), now with numbers attached.

### The hex no-pinch property — and why the tracer now says so out loud

Every boundary vertex has **exactly one** outgoing edge, because a hex vertex touches 3
mutually-adjacent cells: a hex boundary cannot pinch at a vertex the way a square-grid
boundary can. Verified over 412 forms including 400 random blobs — max out-degree 1
everywhere.

The tracer's walk depends on that, and depended on it **silently**: an unbounded
`while True` with an unguarded `pop`, so a violating input would HANG rather than fail.
Both implementations now assert it — Python raises on any out-degree ≠ 1 or an open
boundary, and both carry an explicit step budget (`ne + 1`, since each edge is consumed
once). A property you rely on should be checked, not just true.

## The loft port — Python is the ORACLE, not the destination

The Python here stays as the reference implementation, but it is **not** where this
lives. Two things make the eventual port mechanical rather than a rewrite:

- **The golden JSON is a language-neutral contract.** Because every vertex is an exact
  integer lattice pair, `golden/hexforms.json` is reproducible byte-for-byte by *any*
  implementation. The loft port does not need to re-derive anything — a `src/<x>test.loft`
  asserts it emits the same integers. No float tolerance for the structural half.
- **The float metrics need ε-compare and their own loft assertions.** Anisotropy,
  per-point deviation, and the shoelace-area round-trip must be re-asserted loft-side —
  the round-trip (`Σ shoelace == 12 × cells`) is *integer* and so is exact there too.

**Known data-structure gap to design around.** The prototype leans on Python sets/dicts
keyed by `(col,row)` and `(k,m)` tuples; loft's keyed collections are struct/integer
keyed. Pack a cell as one integer key before porting rather than discovering it mid-port
— and mind the survival-guide idioms (pre-allocated array + index-write for hot
collections, no struct-temp reassign feeding an append).
- **Method note (worth keeping).** The bench falsified its own first property test
  within one run: an `is_thin` check reported *False* for the plainly-correct hex ring,
  because "no interior" was treated as trivially sealed. The instrument earning its keep
  before it ever judged a routine is the argument for building it first.

## Blueprint gate

Exact-invariant work throughout, so CLAUDE.md's design/debug protocol governs every
step: a **concrete plotted end-result** first, then the named invariant, then the loft
port — never the other way round. `tools/wallproto` is the proven medium and the
triangle-wall saga is the cautionary precedent (a small fix behind a large discovery
cost, only pinpointable *after* the Python verify phase).

---

Two big features, planned per the design/debug protocol (exact-invariant work →
BLUEPRINT PHASE in the cheapest medium, a CONCRETE plotted end-result per step,
invariants pinned before the loft port). Anchors that already exist: **WALLS.md**
(the triangle-band wall model, validated in `tools/wallproto`), **DESIGN §9**
(the one-processor outline table: dir-resolution × junction-policy), **STENCILS.md**
(kernel = layered truth, the 2D view renders the current layer, the flood-fill
gating test), `wallgeo.loft` (today's corner-graph smoother).

## The visual-confirmation channel (how Claude verifies, every step)

GL screenshots are unreliable in the sandbox (CLAUDE.md), so geometry is confirmed
by **plotting the kernel's own output to PNG** — the same segments/arcs/layer grids
the view draws, so what Claude confirms is what the renderer consumes:

1. **Blueprint steps (Python)** — the prototype plots PNGs directly
   (`tools/wallproto/out/` pattern, PIL). Claude Reads the PNG and critiques it
   against the pinned target.
2. **Loft steps (the port)** — a headless dump tool `src/geodump.loft` prints the
   outline set / layer planes for a seed as plain text; `tools/plot_geo.py` renders
   that dump to PNG (floor-light/wall-dark palette, per CLAUDE.md readability
   rules). Claude Reads it and compares against the SAME pinned target the
   blueprint used — port fidelity is *visible*, not just asserted.
3. Golden-fixture tests pin coordinates numerically (`*test.loft`, ε-compare);
   the PNG is the semantic check on top (shape, junctions, no gaps/overlaps).
4. **The user stays the live-frame verifier** — composition in the running game
   (`make play`) is the final acceptance; Claude's PNG pass happens first and
   catches geometry errors before a human ever looks.

---

## Track 1 — full 24-angle support + round structures

Goal: walls/roads/fences in **24 directions (k·15°)**; **round structures**
(towers tile 4) rendered as TRUE circles; **attachment** — a circle meets a
straight band tangentially (no gap, no stub); **roads get correct outlines**
(parallel offset faces, rounded junctions); **fences** (tile 5) get the same
angle vocabulary as thin bands.

### Step 1.0 — BLUEPRINT (Python, extends `tools/wallproto`)
Concrete plotted end-results (candidates below are seeded in
`tools/wallproto/out/target_*.png` — **user confirms or amends before any port**):
- **T1 `target_curtain.png`** — a curtain-wall polyline with 15°-snapped legs and
  a **round corner tower at each bend**: the band's faces terminate ON the circle
  at the tangent points (the wall "plugs into" the tower).
- **T2 `target_road.png`** — a road centerline in 24 directions with **parallel
  offset outlines** (±w/2) and **rounded junctions** (arc fillets), plus a fork.
- **T3 `target_fence.png`** — a fence polyline at odd 15° angles attached to a
  building corner (thin band; posts as dots at the snap vertices).
- **T4 `target_door.png`** — a building wall with a DOOR: the gap in the band is
  capped by clean perpendicular JAMBS (engine-rendered — sprites carry no
  architecture, per CLAUDE.md), a door leaf fits the gap exactly (rotated to the
  wall direction), and the SAME gap WITHOUT a leaf still reads as a deliberate
  entrance (capped jambs + threshold), never a ragged hole.

Invariants to pin (each gets an assert in the prototype before the port):
- **SNAP**: every emitted face direction = k·15° exactly.
- **OFFSET**: each face point lies exactly ±w/2 from the centerline (roads, bands).
- **TANGENCY**: circle↔band attach — the face endpoint lies on the circle AND the
  face direction ⟂ the radius at that point (|dot| < ε); no face penetrates the
  circle interior.
- **CLOSURE**: every structure outline is a closed loop (or terminates on another
  structure — attachment is the only legal open end).
- **COLLISION=RENDER**: the triangle band (WALLS.md model) and the rendered faces
  classify the same area (sampled agreement on a fine grid).
- **JAMB**: every band gap (door/entrance) is capped: a segment ⟂ the band's
  centerline joins inner face to outer face at BOTH gap ends; the gap width is
  exact (the leaf must fit); cap directions are in the 24-snap set too.

### Step 1.1 — kernel data model: outline SPECS beside the tiles
Today `stamp_round_tower`/walls/roads write only tiles; the circle is forgotten.
Add a spec record on the Sim (flat arrays + count — the loft#320 idiom):
`feat_kind` (wall/road/fence/tower), `feat_x/y/x2/y2/radius/width`, dir-res +
junction policy per kind (the DESIGN §9 table). gen/sim stamping RECORDS the spec
it stamps (tower → center+radius; town wall → polyline legs; road → centerline;
fence → polyline). Tiles stay the hex-collision truth; specs are the outline
engine's input. Test: every tile-4 ring has a recorded circle; every road tile is
within w/2 of a recorded centerline (`outlinetest.loft`, part 1).

### Step 1.2 — the outline engine (kernel, no graphics): `outline.loft`
Port the blueprint: specs → **segments + arcs**. Band faces from centerlines
(±w/2), **miter** at sharp junctions, **arc fillets** at rounded ones,
**tangent-attach** for circles, full circles for free-standing towers.
**Doors/entrances**: a gap in the band emits its two JAMB cap segments
(inner→outer face, ⟂ centerline) so an opening reads cleanly with or without a
leaf. Output: `OutSeg` (like `WallSeg`) + `OutArc {cx, cy, r, a0, a1}`.
Test: golden fixtures exported by the Python blueprint (same input spec → same
coordinates, ε = 1e-3) + the five invariants re-asserted in loft
(`outlinetest.loft`, part 2). The dungeon's carved-rock outline stays on today's
`wallgeo` path — two paradigms coexist (WALLS.md).

### Step 1.3 — geodump + plot = Claude's eye
`src/geodump.loft` (headless): build a seed's surface, print specs + outline
segments/arcs as text. `tools/plot_geo.py`: dump → PNG. Claude renders the three
target scenes IN-ENGINE (the fortress with its 4 corner towers, the town wall,
a road run, the farmers' fences) and confirms against T1–T3. This artifact is
permanent — every later geometry change re-runs it.

### Step 1.4 — view wiring (the only graphics step)
The view consumes `OutSeg` exactly like `WallSeg` today; **arcs** get a chord-fan
draw (N chords per arc, N by radius — a new small helper beside the segment
draw). Tile-4 hexes STOP emitting hex-boundary wobble (skipped in `wallgeo`) —
the circle replaces them. Roads draw their outline strokes over the tint;
fences draw as thin 24-snapped lines with posts. Doors: the leaf is a sprite
sized/rotated to the gap (the engine's jambs frame it — the sprite carries no
stonework); a doorless entrance renders as the capped opening alone. Verify: `make check`, gate
green, geodump-PNG unchanged (the view consumes, never reshapes), THEN the user
plays a fortress/town/road seed and judges the live frame.

### Step 1.5 — consistency hardening
One test asserting spec↔tile agreement on every generated surface seed of the
gate (no circle without its tile-4 ring, no band face crossing open floor)…
and the fences' gate-gaps + the towers' doors stay open in the outline
(door = a gap in the band, per WALLS.md).

---

## Track 2 — multi-layered towers & walls

Goal: the castle pillar from STENCILS.md — **a tower you climb** (ground →
upper → rampart), **a curtain wall with a walkable top**, content gated by
traversal (sealed at ground, open from above). Kernel carries TRUE stacked
layers (the model `moros_render` will draw); the 2D view renders the player's
current layer.

### Step 2.0 — BLUEPRINT (Python, new `tools/layerproto.py`)
Concrete plotted end-result (candidate seeded as
`tools/wallproto/out/target_layers.png` — user confirms/amends):
- one castle drawn as **two panes**: layer 0 (ground: gate, tower footprints
  solid, keep sealed) and layer 1 (rampart: walkable wall-top floor, tower
  upper floors, parapet edges, the ladder/stair cells marked) + the intended
  traversal path drawn through both panes.
Invariants to pin:
- **GATING**: ground-layer flood-fill does NOT reach the keep interior; the
  rampart-route flood-fill DOES (THE test, straight from STENCILS.md).
- **LINKS**: layer transitions exist ONLY at stair/ladder features; flood-fills
  per layer otherwise independent.
- **ROUND-TRIP**: save/checkpoint of a layered Sim = identity (serialization is
  exact-invariant work — pin it BEFORE the port).
- **L1-DEFAULT**: a single-layer world is bit-identical to today (the entire
  existing gate is the regression net).

### Step 2.1 — the kernel layer axis
Tiles become the STENCILS-pinned flat layout `(L·h + y)·w + x` with `L = 1`
default (today's worlds unchanged); player gains `lay`; `is_wall`/movement/
FOV/collision take the active layer; **ladder/stair-up/down tile codes**
transition `lay` (same feature pattern as `>`/`<`, transitioning layer not
depth). Enemies gain `lay`; adjacency/combat require same layer.
Test: `layertest.loft` — the GATING flood-fill assertion + L1-DEFAULT (a depth-1
dungeon byte-compares against the pre-layer snapshot) + the save ROUND-TRIP.

### Step 2.2 — gen/stamp grows UP
`stamp_round_tower` gains height: ring solid at layer 0, floor + parapet ring at
layer 1, an interior ladder cell; the curtain wall becomes the DESIGN §9 2-hex
band — wall at ground, floor on top, parapet edges; the gate tower carries the
stairs. The fortress + the big town wall upgrade to it. Test: gen-level
assertions (every rampart cell reachable from a gate stair; parapet never
walkable from outside).

### Step 2.3 — actors on layers
Guards' patrol legs (`wq2/aq2`) gain the rampart: wall-top patrol routes are
REAL paths on layer 1 (today they walk beside the wall). Monsters cannot cross
layers without a link; ranged/gaze respects layer (a rampart archer sees down —
gameplay call recorded in the step, default: same-layer only first).
Test: a guard completes a rampart circuit headlessly; a ground monster cannot
reach a rampart NPC without taking the stairs.

### Step 2.4 — the view renders the current layer
View draws the player's layer plane; cells OPEN above ground show the dimmed
ground floor under them (a nicety, not a blocker — STENCILS.md); HUD gains a
layer indicator; ladder/stair sprites (the `draw` skill, per the sprite rules).
geodump gains a `--layer` pane so Claude confirms each plane + the gating path
as PNGs (the 2.0 target re-rendered from the REAL kernel).

### Step 2.5 — outline integration (the tracks meet)
Parapets + tower rims outline through the Track-1 engine (arcs for tower tops,
24-dir parapet edges). The castle scene re-plots as the FINAL target: both
panes, true circles, straight curtains — Claude's last PNG pass, then the
user's live-frame acceptance walk (climb, cross, drop in).

---

## Order & dependencies

- 1.0 → 1.1 → 1.2 → 1.3 → 1.4 → 1.5 (strict).
- 2.0 → 2.1 → 2.2 → 2.3 → 2.4 (strict); 2.5 needs Track 1 done.
- The tracks are independent until 2.5 — interleave at will; suggested: 1.0–1.3
  first (the engine, fully confirmable headlessly), then 2.0–2.1 (the kernel
  axis, biggest regression risk, wants the calmest tree), then alternate.

## Standing risks / loft notes

- All new hot collections: pre-allocated array + count + index-write (loft#320).
- No thin arity-reducing pub wrappers around `Sim`-returning fns (loft#339).
- Text tables as branch-selector fns (loft#336).
- The layered tile array changes `Sim`'s biggest field — watch store pressure
  habits (one Sim live at a time) and keep the save round-trip test FIRST.
- Kernel stays graphics-free: `outline.loft`/layer code import no `graphics::`;
  arcs reach the view as data (the architecture invariant).
