# Plan 11 — what each phase found

> The **plan** (status, phases, order, risks) is [`README.md`](README.md); the **design**
> (the seven invariants and their arithmetic) is [`DESIGN.md`](DESIGN.md). This file is the
> third concern: what each phase actually *discovered*, which is neither intent nor design and
> was crowding both.

## P1 result — one passability predicate, measured 2026-07-22

Pure refactor. `make test` output is **byte-identical over 1018 lines** except one added
line (the new solidity gate below). The blueprint gate asked for *"the passability call
graph, before/after, with the 13 sites named"* — the graph is below, and **the count was
wrong in three ways**, which is why the phase measured before it moved.

### What the estimate got wrong

`DESIGN.md`'s I-TRUTH note said *"`is_blocked_move` has 5 call sites, all in `sim.loft`;
`is_wall` 6 in `sim` + 2 in `wallgeo`"* — 13 sites. Measured:

| claim | measured | |
|---|---|---|
| `is_blocked_move` — 5, all in `sim.loft` | 5, but **3 in `sim` + 2 in `selftest`** | the tests were never counted |
| `is_wall` — 6 in `sim` | **5** in `sim` | plus **9 in tests**, also uncounted |
| — | — | **`tile_solid` (7 sites) was missed entirely** |

So the real surface was **32 sites**, not 13, and — the finding that mattered — the
solidity rule `t == 1 \|\| t == 4 \|\| t == 5` was written out **three independent times**,
one of which **disagreed** (fixed in the follow-up commit):

| copy | where | rule |
|---|---|---|
| 1 | `is_wall` | `1 \|\| 4 \|\| 5` |
| 2 | `tile_solid` — generation-time, on the bare tile array | `1 \|\| 4 \|\| 5` |
| 3 | `sim_blink` (`sim.loft:1199`) | **`!= 1` only** — blink can land you inside a boulder or a fence post |

### The call graph

**Before** — two data readers, but the *rule* and the *query* both restated per caller:

```
s.tiles ──> tile_at ──┬─> is_wall (rule inline) ──┬─> is_blocked_move ──> pos_blocked, compute_flow, flow_step, selftest×2
                      │                           ├─> wallgeo×2, compute_flow, sim_bolt, npc_passable, tests×9
                      │                           └─> pos_blocked (same-hex branch, redundant)
                      └─> sim_blink  (rule restated as != 1 — DISAGREES)
raw tiles[] ────────────> tile_solid (rule inline, 2nd copy) ──> 7 placement sites
s.walls ──> edge_wall_raw ─┬─> edge_wall ──> is_blocked_move
                           └─> wallgeo (edge GEOMETRY, not passability — left alone)
```

**After** — one rule, one query, everything else a spelling of it:

```
                       solid_kind(t)              <- THE RULE, stated once (2 callers)
                            │
s.tiles ──> tile_at ──> field_blocked(s,q,r,dir)  <- THE PREDICATE (3 callers)
s.walls ──> edge_wall ──────┘                        dir = DIR_HEX -> the hex itself
                            │                        dir = 0..5    -> the step out of it
                            ├─> is_wall          (16 sites, unchanged spelling)
                            └─> is_blocked_move  (5 sites, unchanged spelling)
raw tiles[] ──> tile_solid ──> solid_kind         (7 sites — generation, no Sim exists yet)
```

`field_blocked`'s domain is `(hex, direction)` — deliberately the exact domain **P2's
differential harness enumerates**. P2 swaps this one body and no caller changes.

Also removed: `pos_blocked`'s same-hex branch (`if aq == bq && ar == br { is_wall(bq,br) }`).
It was already redundant — `hex_neighbor_dir(a,a,a,a)` returns `-1`, so
`is_blocked_move(s,a,a,a,a) ≡ is_wall(s,a,a)` exactly.

### The negative controls — one fired, one did NOT, and that was the phase's real finding

| control | expected | result |
|---|---|---|
| drop the edge-wall term from `field_blocked` | red | **red** — `selftest` (kernel self-test) |
| shrink `solid_kind` to `t == 1` | red | **GREEN — the whole suite stayed green** |

The second control passing is the plan's own lesson 3 arriving on schedule: *the failure
mode is never a check that fails, it is one that passes for the wrong reason.* Probed it
instead of assuming — the depth-0 seed-777 surface carries **153 boulders (tile 4) and 79
fence posts (tile 5)**, so the rule's other two arms are live in the very world the tests
generate, and **no gate observed them**. A field model that silently dropped tiles 4 and 5
would have passed P2's differential harness.

Closed in `surfacetest.loft`: every tile-4/5 hex must report `is_wall`, and
`is_blocked_move` must block entry from every open neighbour — with `nsolid > 100` so the
assertion can never pass vacuously. Now `solidity: boulders+posts=232 is-wall=true
blocks-entry=true`, and control 2 goes red.

### The divergent site — split out, then fixed (same day)

`sim_blink` was the one site asking the passability question with a different rule
(`tile_at != 1`). Routing it through the chokepoint **changes behaviour**, so it was held
out of a phase contracted to "`make test` unchanged" and fixed in its own commit, on the
user's ruling.

It was not marginal. The gate stands the player beside the farmers' fences on the depth-0
surface — 6 non-rock solid hexes within blink range — and blinks 300 times:

| rule | blinks that landed inside a solid hex |
|---|---|
| `tile_at != 1` (old) | **96 / 300** |
| `field_blocked(.., DIR_HEX)` (fixed) | **0 / 300** |

Roughly a third of short blinks in fenced country dropped the player inside a fence post
or a boulder. It survived because the only blink gate ran at **depth 1**, and the dungeon
has neither kind — the coverage hole and the bug were the same shape. The new gate carries
its own anti-vacuous guards (`soft_near > 0`, `moved > 200`) so it cannot go quiet if the
world generator stops producing fences.

### Left standing, deliberately

- **`wallgeo`'s `edge_wall_raw`** stays a direct `s.walls` reader. It asks *"what wall
  geometry exists on this canonical edge"*, not *"may I pass"* — the two differ whenever a
  destination hex is solid with no edge wall between. Conflating them would be wrong; it is
  the renderer's concern and belongs to P3/P3b.

## P2 result — the field under the kernel, 2026-07-22

`make test` green. The kernel's passability now comes from an **edge field**; `Sim.tiles` is
no longer read for passage once a `Sim` exists.

### The blueprint found the work already done — in this repo

The plan said P2 would need an `EdgeSet` and I opened by reporting that `hex_field` has none
(true — `validate` demands `shoelace == 12·cells` and one outer loop, so a zero-area barrier
is not a form). **That was the wrong conclusion from a true fact.** `src/hexedge.loft` is a
620-line edge model, gated by `edgetest.loft` in `make test` today, with `passable()`,
`collide()` returning the *exact* surface normal, materials, `apply_features` for openings
and `sight_clear`. It has 27 consumers — and `sim.loft` was not one of them.

Its headline gate is the thin-geometry argument, already proven here before it was raised:
**a one-EDGE-thick wall separates in all 24 headings; a one-CELL-thick wall manages 6.**

So P2 was wiring, not invention. `edges_solid`'s own comment states the bridge: *"the cell
model expressed in the edge primitive — one collision layer serves both."*

> **Third time this session a confident structural claim died on contact with the code**
> (`STATE.md` lesson 4). Worse than the other two: two questions were put to the user about
> sequencing work that already existed. The tell was available and ignored — `hex_field`'s
> own comment says a height field is derived *"exactly as the edge field is"*, which names an
> edge field that the library does not contain, i.e. one that lives somewhere else.

### What landed

`Sim` gains two derived fields, built once at construction from what the generator already
wrote, so no world builder changed:

| | | from |
|---|---|---|
| `Sim.solid` | `HexSet` — cell occupancy | `solid_kind` over `tiles` |
| `Sim.field` | `EdgeSet` — the crossing layer | every edge with a filled/off-map endpoint, plus every stored `walls` edge |

`field_blocked` reads them and nothing else: `DIR_HEX` → `hexset_get` (off-map answers
*rock*, keeping the plane a total partition), `0..5` → `!passable(s.field, …)`. `edge_wall`
had no callers left and is deleted.

**Open question 1 is answered, with data rather than a guess: `Sim.tiles` survives — as
CONTENT.** Its remaining readers ask about stairs, cave mouths, quest features and plain
floor, never about passage. `tile_solid` still reads the bare array during generation,
before a `Sim` exists.

### The differential harness, and the one difference it found

`src/fieldtest.loft` spells the **old** model out from first principles and never calls
`field_blocked` to get it, so it stays the frozen definition of *the answer we had*. Built
and proven green **before** the swap, so its teeth were known.

| world | blocked | open | edge-decided | mismatches | stepping out of a wall |
|---|---|---|---|---|---|
| demo `sim_new()` | 612 | 2034 | **6** | **0** | 232 |
| surface (777,0) | 3182 | 58024 | 0 | **0** | 1382 |
| dungeon (777,1) | 7488 | 2598 | 0 | **0** | 670 |
| dungeon (777,2) | 7614 | 2472 | 0 | **0** | 642 |

**Zero mismatches from any reachable position**, across ~135 000 (hex, direction) answers.

The one difference is characterised, not hidden: an EdgeSet edge has no direction, so it
cannot forbid entering a wall while permitting the step back out — which the old
destination-only predicate did. Every single mismatch had a **solid source hex**; that was
checked by classifying them, not assumed. Under I-CROSS that state is unreachable, so the
new answer is the better one, and the harness *counts and prints* the cases rather than
folding them into the pass.

The demo world is swept first and never dropped: its 3-edge stub on hex (12,7) is the
**only** edge wall in the game — every generated world has zero — so without it the
predicate's edge arm is swept but never exercised. It contributes the 6 edge-decided
answers. The sweep also fails on under 100 blocked *or* under 100 open answers, so it
cannot pass by seeing only one kind.

**Negative controls — all three fire.** Drop the stored edge walls (demo: 6 mismatches) ·
leave the map perimeter unsealed · flip one cell of the solid set.

## P2b result — movement is a swept path, 2026-07-22

`make test` green. Movement no longer samples a probe point; it sweeps the whole segment
and slides along whatever stops it. **The set of walls that stop you no longer depends on
`dt`.**

### `sweep_path` — exact, and with no step size in it

`hexedge::sweep_path(e, x0,y0, x1,y1) -> (fraction, q, r, dir)`. A point's cell is its
**nearest centre**, so a crossing is exactly where the segment meets the bisector between
the current centre and a neighbour's — one linear solve per neighbour:

```
   |P(t) − C|² = |P(t) − N|²   ⟺   t = ((M − P₀)·D) / (V·D),   D = N − C,  V·D > 0
```

Centres come from the exact integer lattice, so nothing accumulates. There is no substep
anywhere: the answer is a function of the **segment**, which is precisely what makes it
dt-independent. Bounded at 256 crossings, and the bound **fails safe** — on exhaustion the
caller is told it may travel only as far as was verified, never that the rest is clear.

### Two real defects, both found by the gate, neither guessed

**1. The sentinel collided with the data.** The first version returned the blocking *cell
pair* with `-1` for "nothing blocked". Hex coordinates are signed, so in any chunk spanning
the origin a wall at `q = -1` reported "no hit" — 146 of 1428 segments. Fixed by signalling
with the **direction** (0..5, `-1` impossible) and never with a coordinate.

**2. Filtering by parameter dropped the first crossing — and that is the NORMAL state.**
The walk skipped crossings at `tt <= t + ε` to avoid re-detecting the edge just crossed.
But stopping at a wall leaves the position **exactly on a bisector**, so the very next
sweep starts on a boundary and silently skipped its first edge. Diagnosed by printing both
walks for one failing segment rather than reasoning about it: start `(0, 1.4)` is
*exactly* equidistant from the centres of `(0,1)` and `(-1,1)`.

Fixed by excluding **the cell we came from** instead of filtering by parameter. That also
makes a corner walk *through* correctly — both of its edges get tested at the same `t` — so
a path cannot slip between two walls that meet, which is the corner-cut exploit.

**3. The slide had no radius back-off**, so the centre landed exactly on a wall boundary
and `px_to_hex` rounded it *into* the wall. Caught by `selftest`'s existing wall-slide
check. Both the primary move and the slide now go through one `swept_advance`.

### The gates

`src/sweeptest.loft` — against an independent 2000-substep march as oracle, over 1428
segments on one-edge-thick walls in 12 headings:

| check | result |
|---|---|
| agreement with the fine march | **1428 agree, 0 disagree** (347 blocked / 1081 clear) |
| soundness — no wall inside the part it permits | **0 violations** |
| subdivision: whole vs 4 pieces vs 16 | **0 differ, worst gap 3.3 × 10⁻¹⁶** |

`src/selftest.loft` — the end-to-end gate, the same walk into the **edge-wall stub on hex
(12,7)**, the only thin barrier in the game:

| walk | ends at | travelled |
|---|---|---|
| 64 × 0.02 s | 22.0666604983954, 10.5 | 5.6122 |
| 16 × 0.08 s | *bit-identical* | 5.6122 |
| 4 × 0.32 s (1.92 units a step) | *bit-identical* | 5.6122 |

**Negative control — and it took two tries to make it honest.** Reverting to a point sample
first appeared to pass, because the walk was aimed at a *solid* wall thick enough that even
an end-point test lands inside it. Re-aimed at the one-edge stub, the control fires exactly:

| | fine | coarse |
|---|---|---|
| swept | 5.6122 | 5.6122 |
| point sample (the old model) | 5.6122 | **7.6800 — the full distance, straight through the stub** |

That near-miss is the phase's lesson: **a negative control aimed at the wrong geometry
passes, and a passing control reads exactly like a working one.** Thick walls hide
tunnelling; only thin ones show it — which is the same reason thin geometry is where
physics engines die.

### Limits, stated rather than implied

- **The sweep tests the CENTRE with a radius back-off, not the player's disc.** A wall
  passing within a radius of the path but not across it is not detected. A true swept disc
  is a Minkowski expansion of the edge set and belongs with the surfaces P5 puts on edges.
- **The slide uses the EDGE normal**, exact here because these walls *are* hex edges (cells
  sealed by `build_field`). When P5 puts real surfaces on edges, `collide` supplies the true
  normal and curved walls stop reading as facets.
- **Enemies and open water stay a destination-cell veto** — they are occupancy, not field
  geometry, and the swept path cannot express them.
- **Still planar.** I-CROSS's vertical half is untouched: nothing yet stops a path walking
  up a 3 m riser.

## P3 + P4 result — the camera, the view, and the presentation seam, 2026-07-22

`make test` green. **The picture itself is still unverified** — this box has no display and
no `xvfb`, so everything below is gated *arithmetic*, not a photograph.

### P3 — what landed

`src/hexscene.loft`: a `Camera` and pure `project` / `unproject_plane` / `horizon_y` /
`cam_mat4`, with **no dependency at all** — not `Sim`, not `graphics`, not even `hex_grid`.
That is what lets I-STAND be gated with no GL context. `src/view3d.loft` draws floor and
wall geometry extruded from `Sim.field`; `story.loft` toggles it with **`V`**.

| gate | result |
|---|---|
| hex → pixel → the same hex (1705 hexes, 12 cameras) | **0 failures**, worst 3.6 × 10⁻¹⁴ |
| a 1-unit post at 8 u vs 16 u | **ratio 2.0000** |
| `cam_mat4` vs `project` (152 points, 8 cameras) | **0 disagreements**, worst 3.2 × 10⁻⁹ px |

The matrix check is the one that matters most and was nearly skipped: **the GPU never runs
`project()`**. Without it the round-trip would be a proof about code the renderer does not
use, which is exactly the second opinion I-STAND forbids.

### P4 — the seam is the deliverable, the boards are its first implementation

`ActorView` + `present_boards` live in **`hexscene`**, not `view3d`, because they take a
`Camera` and nothing else — the library/game line `EXTRACTION.md` draws. `actors_collect`
takes `Sim` and is therefore the **adapter**, game-side.

Boards are upright billboards: width along the camera's right, height along **world** up, so
actors stand up rather than tipping with the camera — which is also what a mesh will do.
Sizes are metric (1.75 m = 2.02 world units). One draw call, buffer re-uploaded in place.

**Textures are deliberately not wired.** A per-actor texture means a draw call per actor;
that wants an atlas, and the atlas rides with **P8**, which re-authors the sprites side-on
anyway. Boards carry the monster's colour meanwhile. `av_tex` is carried through the record
unused, so the seam already has the slot.

### Two controls that were worthless until re-aimed — the same failure twice

| control | first attempt | fixed |
|---|---|---|
| camera perturbation | 0.02 rad → **0 of 172** hexes moved | 0.15 rad → 160/172 |
| board-vs-wall parity | compared `project(d,0,h)` with `project(d,0,0.0+h)` — **two spellings of one expression**, "worst 0px" | reads the corners back out of the buffer `present_boards` actually emitted |

The first failed because **a control must perturb by more than the quantisation it is read
through** — 0.02 rad shifts the ground point ~0.2 units against a hex circumradius of 1.0,
so it rounds back. The second was a plain tautology that would have passed for any
projection whatsoever. Both printed a healthy-looking number.

Counting the P2b near-miss, that is **three controls in one session that passed while
measuring nothing**, each in a different way: wrong geometry, too-small perturbation, and a
tautology. The pattern worth carrying: *a green control deserves the same suspicion as a red
gate — read what it would take for it to go red, and check that is reachable.*

### VERIFIED — the frames, once `xvfb` was installed

`src/shot3d.loft` renders one first-person frame headlessly and writes a PNG. **The world
draws.** A dungeon reads as an enclosed stone room — warm floor, dark faceted walls, sky
above the wall tops; turning 90° gives a different wall layout, so the camera is genuinely
read rather than baked; the surface reads as open green country under sky with actor boards
standing on the ground.

**The prediction I wrote was wrong, and measuring cost less than the hedging.** G1 said depth
might be missing. A 40-line probe — near quad drawn first, far quad drawn second, read one
pixel — came back blue. **Depth works.** Install the instrument before writing the risk.

**What the frames DID find, and it is silent:** `gl_window_height()` reports **576** while the
GL drawable is **541**. Measured three ways: a full-screen NDC quad covers 541 of 576 rows; the
shortfall is a constant 35 px at 400, 576 and 720 px windows; and a ±0.9 quad stops at row 548,
which rules out a capture offset (that would run to 575). So **any camera taking its aspect
from `gl_window_height()` renders the world ~6.5% too tall** — and a stretched world looks
like a world. Exactly the class I-STAND exists to forbid, found only because the frame was
finally looked at. → `LOFT-HANDOFF.md` **G3**.

Also recorded: **G2**, a cross-module struct return failing with `expected Camera, got
Camera`, fixed by qualifying the type. The cost there is the diagnostic, not the fix.

### The aspect, fixed without a magic number

The inset is **window chrome**, established by testing the borderless path: a fullscreen
window reports 2560×1600 and a full-screen NDC quad covers **all 1600 rows — zero missing**.
So `gl_window_*` is exact whenever there is no chrome, and the fix needs no constant:

- **`story.loft`** takes the camera's aspect from the **live** `gl_window_width/height`
  rather than the requested `WIN_W/WIN_H` constants. Exact borderless; a decorated window
  still overstates by its inset until `graphics` reports the framebuffer (G3), and a resized
  window now tracks instead of silently stretching.
- **`shot3d.loft`** renders **borderless fullscreen** deliberately, so the verification
  harness cannot lie about the very thing it verifies. Re-rendered: **0 rows missing** on all
  three frames.

### The ring — measured, and it is correct

The dark ring around the surface frame was recorded as *unexplained* rather than waved
through. Counting solid cells by distance from the player settles it:

| hexes from player | 0–6 | 6–12 | **12–18** | 18–24 | 24–30 | 30+ |
|---|---|---|---|---|---|---|
| solid cells | **0** | 35 | **195** | 45 | 49 | 72 |

Half the world's solid cells sit in one band at 12–18 hexes (21–31 world units) and **none
within 6** — which is `surfacetest`'s cleared start ring with terrain around it. The ring is
the world, not the renderer.

### Still open on the picture

- Actors are **flat colours**, not sprites — the texture atlas rides with P8.
- A decorated window is still ~6.5% tall until `graphics` exposes the drawable (G3).

## P3b — opened 2026-08-11: the exactness is real, and the first two attempts at it were not

**The lattice IS world space, up to one scale per axis — measured, not assumed.** This is the
fact the whole phase is cheap because of:

```
hex_to_px:  x = SQRT3*q + SQRT3/2*(r&1)      lattice_k = 2q + (r&1)
            y = 1.5*r                        lattice_m = 3r
  =>        x = (SQRT3/2) * k                y = 0.5 * m
```

Verified on real hexes: hex (3,4) has centre lattice (6,12) and its six corners land on
**exactly** (6,14) (5,13) (5,11) (6,10) (7,11) (7,13). A hex is a lattice hexagon 2 wide and
4 tall. So at an integer *S* texels per lattice unit, every `trace` boundary vertex is an
exact integer texel corner and **no rounding enters the raster at all** — which is what lets
`I-PAINT` claim *exact* rather than *within tolerance*.

### The gate, and why it is deliberately RED and out of `make test`

`src/painttest.loft` compares two independent paths that meet only at the field:

| side | path |
|---|---|
| raster | labels → `trace` → integer polygon → scanline fill → texel |
| truth | texel → its centre in world units → `px_to_hex` → `hexset_get` |

Testing the fill against a point-in-polygon routine instead would compare one scanline rule
with another and prove nothing. The blob under test **has a hole**, and that is not decoration.

**It has already failed twice, with different causes, and that is the phase working:**

| | mismatches | cause |
|---|---|---|
| first run | **912** (over=886) | ⚠ `fill_polygon` called **once per loop**. `trace` emits an enclosed region as a second loop wound the other way, and filling loops separately **paints the hole solid**. Even-odd is only even-odd if every contour lands in ONE crossing list. Fixed: `sprite_draw::fill_polygons` |
| second | **54** (over=25, under=29) | ⚠ **not a rasterisation error at all** — see the localisation below |
| now | **0** over 20160 texels, 0 ties | ✅ **`PAINT OK`**, wired into `make test` (row 105) |

### Localising the 54 — and why it was not a bug

The instrument added one column: for each mismatch, does the texel's centre lie **exactly on a
polygon edge**? (Computed independently of `sprite_draw` — reusing the code under test would
have made the answer true by construction.) The result was unambiguous:

```
LOCALISED: on-edge ties total=240, of which disagree=54; mismatches NOT on an edge=0
```

**Every single mismatch was a texel centre sitting exactly on the boundary**, and 240 such ties
existed — the two sides simply happened to agree on 186 of them. So the raster was never wrong.
**I-PAINT was under-specified**: it says a boundary in the texture and the geometry under it
cannot disagree, and says nothing about a sample lying *on* that boundary. Both sides then broke
the tie by their own rule — the fill by `(x + 0.5) as integer`, the field by `px_to_hex`'s cube
rounding — and disagreed a fifth of the time.

### The fix: make the tie class EMPTY, rather than pick a winner

A stated tie-break would have worked and would have been a rule to remember forever. The
arithmetic offers better. Lattice edges are only ever `(dk,dm) ∈ {(±1,±1), (0,±2)}`, so with
**`TEX_SX = 2·TEX_SY`**:

- a slope-1 edge crosses row `y = py+0.5` at `x = x1 ± (2·py + 1 − 2·y1)` — an **integer**;
- a vertical edge crosses at an integer too;
- texel centres are **half-integers**.

So no texel centre can lie on a lattice edge, ever. Ties went 240 → **0** and mismatches 54 → 0,
by construction rather than by tolerance. ⚠ **And the tie-free scale is also the more
world-square one**: 1 lattice `k` is `√3/2` world and 1 `m` is `1/2`, so a 2:1 texel grid has
aspect **0.866** where an isotropic grid has 1.73. The constraint and the quality choice point
the same way, which is the tell that it is the right frame rather than a trick.

⚠ **This is a constraint on the whole texture stack, not a setting in one test.** Any layer that
rasterises a traced region — P6's cached layers at their own resolutions, the editor — must keep
the 2:1 ratio between its axis scales, or it re-admits the tie class at that resolution.

### What this already changes for the rest of the plan

- **A region with a hole is the NORMAL case** — a clearing in a wood, a lake in a field — so
  the multi-contour fill is not a corner case handled early; it is the base case. Anything
  downstream that rasterises a traced region (P6's layers at their own resolutions, the
  editor) must use `fill_polygons`, never a per-loop call.
- `fill_polygon`/`fill_polygons` are now `pub` in `sprite_draw`. ⚠ **Exported rather than
  copied on purpose** — a second scanline fill for the world would be a fork of a gated one.
- **The exactness is settled and gated**; what remains for P3b is the plumbing: the actual
  texture (tiles + LOD — *one* texture is impossible at ~23 gigatexels), the sampler in
  `view3d`, and retiring `worldmesh.loft`'s R4 vertex-colour tint bake.
- ⚠ **The blob is synthetic.** It was chosen to force the hard cases (a hole, both edge
  orientations) and it did. Re-running the same diff against a **real traced landcover region**
  from a generated world is worth doing when the texture lands — the arithmetic says it must
  pass, and that is exactly the kind of claim this plan has learned to check rather than assume.
  ✅ **Done, and it passed** — see the plumbing section below.

## P3b plumbing (2026-08-11): the design named the expensive construction, and the measurement says so

The exactness was settled; what remained was the texture itself, the sampler, and the LOD
question. Three things came out of building it, and two of them narrow claims already written
down above.

### 1. The synthetic blob's exactness DOES hold on the world players start in

`src/worldtextest.loft` runs the same two-independent-paths diff on **seed 1337, depth 0** —
9 landcover classes, 124 traced loops, an `812×604` texture — and reports **0 mismatches over
488 032 in-window texels**. That closes the open item this file recorded in writing. The blob
was a fair proxy after all, which is worth knowing precisely because it was not assumed.

### 2. `trace` + `fill` is NOT the cheap way to a raster — the direct construction is 13× cheaper

`DESIGN.md` names the mechanism as `trace` the region → `fill_polygons` its loops, and calls
it *"nearly free"*. Measured per level on that world, with the phases timed **in-program**:

| per level, 812×604 texels | native | interpreted |
|---|---|---|
| worldgen (for scale) | 585 ms | 14 646 ms |
| **point-sample** — texel centre → `px_to_hex` → kind | **44 ms** | **1244 ms** |
| `trace` (9 classes, 5724 edges) | 203 ms | 209 ms |
| `fill_polygons` (9 classes) | 386 ms | 3808 ms |

**13× native, 3.2× interpreted** — and interpreted is the path the game runs on while native
GL is upstream-gated (loft#396). Both rasters are byte-identical, so the choice is cost alone.
So `worldtex.loft` point-samples, and **trace+fill stays as the test's independent ORACLE**
rather than the producer — which is a better job for it than being the producer was.

⚠ **`fill` is the pole, not `trace` — the opposite of the prediction.** The O(ne²) reading of
`trace`'s linear-scan walk is real but small (5724 edges is nothing); the fill is O(rows ×
edges) with a sort per row, and it is *crawler* code, so it is the only one of the three that
the interpreter slows down 10×. Note `trace` costs the **same in both modes** (203 vs 209 ms):
registry libraries run native under `--interpret`, which is worth remembering the next time a
profile looks impossible.

⚠ **Two claims above narrow, and neither is retired:**

- **The 2:1 axis-ratio constraint is a property of the FILL**, which must break a tie when a
  texel centre lands exactly on a boundary. Point-sampling has no tie to break — `px_to_hex`
  answers everywhere, and its answer *is* the definition. So the constraint still binds
  anything that rasterises a traced loop (P6's cached layers, the editor) and does not bind
  the world texture. It reads as a whole-stack constraint above; it is a whole-*fill*-stack one.
- **`trace` is not retired and must not be.** The loops are what geometry and silhouettes
  (I-AGREE) are built from. What is measured here is only that a **raster** does not need them.

### 3. LOD and tiling are P6's, and the near field never needed them

The *"one texture is impossible — ~23 gigatexels"* arithmetic is about the 151 km overland at
1 m/texel. The **level window** is 101×101 hexes ≈ 151 m across: at `TEX_SX=4 / TEX_SY=2` that
is 812×604 = **0.49 Mtexel, 2 MB**, one texture, no tiles and no clipmap. So P3b ships a single
resident texture per level and the ladder stays exactly where the design put it — in **P6**,
where the far field actually needs it. Stated rather than silently skipped.

### What shipped, and the one link the gate cannot reach

`src/worldtex.loft` is kernel-side and emits **terrain kinds, not colours** — the palette lives
in `view3d::kind_rgb3`. That is not tidiness: the gate then compares *classes*, and two kinds
sharing a tone cannot hide a mismatch behind an equal colour. The floor buffer went stride 6 →
**8** (the graphics library's `pos/loc1/UV` layout), floor vertices carry uv from
`world_tex_uv` — the same function `worldtextest` row 2 round-trips, so the mapping has one
owner — and **walls carry `(-1,-1)`**, which is the floor/wall discriminator: a floor uv is
always inside `[0,1]`, so no second attribute has to be kept in step with the first.

⚠ **The upload convention and the sampler are GL's, and no headless CPU gate reaches them.** A
vertically flipped texture satisfies every check in `worldtextest` and still puts the wrong
landcover under your feet. Closed by reading the rendered frame: `shot3d` prints the kind of
the hex the camera stands on, and the PNG's bottom-centre band (where the fog fade is ~0) is
that ground — **surface kind 0 read (107,132,76) against the palette's (107,133,76); dungeon
kind −1 read (182,173,140) against (184,173,140)**, i.e. equal to within 8-bit rounding.

Sampling is **linear + mipmapped**, deliberately: the raster is exact *at texel centres*, which
is what the gate asserts, and a linear sampler blends across at most one texel — 0.19 m of
world at this scale. Nearest would keep the claim literal at every fragment and show 19 cm
blocks underfoot. The blend is the better picture and the bound is stated rather than hidden.

**Still owed by P3b:** retiring `worldmesh.loft`'s R4 vertex-colour tint bake. It feeds
`view.loft`, the **2D** renderer, which plan #11 **P9** deletes — so the bake retires *with its
only consumer*, and plumbing a world texture into a renderer that is about to be removed would
be work done to be thrown away. Recorded as a decision, not an oversight.

## P6 opened (2026-08-11): the near reading does not exist, and switching it on is a gameplay decision

I-HORIZON says *near and far are one world at two readings — the same point has the same height
from either*. P6's gate is "the boundary ring sampled from both readings, heights diffed". You
cannot diff two readings when there is only one, and there is only one.

**Measured, not read off the docs** (`src/horizonprobe.loft`): `sim.loft`'s surface generator
already fetches the height and **throws it away** —

```loft
(_, okind) = ov_sample(ovw, ax + hx3 - cwx, ay + hy3 - cwy);   // sim.loft:4896
```

— and `Sim` carries no height field at all. The near field is a flat plane at `z = 0` in both
renderers. The far reading (`ov_height`, in natural metres) is the only one implemented. So
P6's first step is not the diff; it is deciding what the near reading's vertical *means*, and
`SCALE.md` — which pins the horizontal twice over — **is silent on the vertical**.

### The vertical reading follows from SCALE.md, and it is not the interesting part

One walked hex is 1.5 m of architecture and stands for 15 natural m of terrain, so the walked
world is 1/10 of natural scale. To keep a hillside's *true* slope, heights divide by 10 as well
— rise and run take the same compression. Call that **reading B**; leaving heights natural
(reading A) multiplies every slope by ten and gives a mean gradient of 10.5 across the home
window, i.e. walls. Reading B is simply correct, and its numbers *are* the real terrain's.

### What the measurement actually found: the rule that picks the starting town selects for unwalkable ground

At reading B, over the 55 018 hex-to-hex steps of **passable** ground in the home window
(K_FACE / lake / sea excluded, since those are already impassable and a cliff there costs
nothing):

| slope band | steps |
|---|---|
| < 0.125 (a gentle ramp) | 3 813 |
| 0.125–0.25 (a steep road) | 4 286 |
| 0.25–0.5 (a hard climb) | 8 618 |
| 0.5–1.0 (up to 45°) | 15 547 |
| 1.0–2.0 (45–63°) | 16 451 |
| > 2.0 (a cliff) | 6 303 |

**Mean 1.02 — 45.6° on average, with 7 % of steps gentler than a wheelchair ramp.**

⚠ **And the control is what makes it a finding rather than a panic.** `ov_home_town` picks the
town with the **greatest height reach**, so the window measured above is the steepest in the
world *by construction*; a claim drawn from it alone would be a claim about the outlier. Every
town, same method:

| town | relief over 1500 m | mean walkable slope |
|---|---|---|
| 0 | 232 m | **0.077** |
| 1 | 218 m | **0.088** |
| 2 | 655 m | **0.386** |
| **3 — the home window** | **2320 m** | **0.903** |

**The world at large is walkable country. The starting window is a mountainside, and it is the
starting window *because* of it.** Height reach within a 1500 m window is not a proxy for "can
carry a whole economy" — at that footprint it *is* mean slope, so the selection rule and
"steepest possible start" are the same rule. For scale: 2320 m of relief over 1500 m is a mean
gradient of 1.55, steeper than the Ortler north face (~1400 m over ~1.5 km ≈ 0.9) across an
entire window.

⚠ **This is the SAME trade already on the record, arriving on a second axis.** `STATE.md`
records that the alpine anchor bought the gatherer (picking grounds need scree or meadow, which
do not occur at sea level — plan #17) and cost the onboarding curve (a gnoll at mlvl 6 eight
hexes from the vantage). It also costs the *terrain*, and that third cost was invisible only
because the ground renders flat.

### Why this stops P6 rather than being worked around inside it

The moment the near field gets its height, the town the game starts in becomes a 42°-average
mountainside — and no vertical reading fixes that, because reading B is already the true one.
The levers are all outside this plan: the home-town rule (`overland.loft`), the height field's
horizontal scale, `OV_STEP`, or a walkability constraint on the site scorer. **`overland` owns
settlement placement and this plan integrates with it rather than rewriting it** (`CLAUDE.md`),
so P6 records the number and does not reach for the dial.

> **OPEN, and the user's call** — it is a gameplay question, not an engineering one:
> **should the starting window be walkable, and which lever pays for it?** Candidates, in
> ascending order of blast radius: (a) `ov_home_town` scores *reachable high ground within a
> walkable neighbourhood* instead of raw height reach — town 2 (655 m, slope 0.39) reads like
> the intended shape and still carries a mine; (b) the height field's horizontal scale, or
> `OV_STEP`, so 2320 m of relief gets the ~5 km it needs; (c) accept a mountain town and let
> the near field clamp what it draws. **(a) is the narrowest and is the one to try first**, and
> it is squarely plan #1 / the overland's area, not plan #11's.

### The lever was pulled, and the world refused it (2026-08-11)

`ov_home_town` now scores what its own comment always said it wanted, and the correction is
worth stating on its own: **height reach is a CONSTRAINT, not an OBJECTIVE.** Inside a 1500 m
window "reaches highest" *is* "steepest", so maximising it selected for the one property that
makes terrain unwalkable. The rule is now: reach `ALPINE_MIN` (so scree/meadow can exist) **and**
have rock within a working day (so a mine can exist) — then among those, **the most walkable
window wins**. Gradient is measured on a 13×13 grid of `ov_height`; against a 10201-point
reference the four means come out within 6 % with the same ordering, on 1/60th of the samples.

⚠ **`ALPINE_MIN` is now a named constant shared with `ov_kind_at`**, because a home-town rule
and a classifier disagreeing about where alpine ground begins is a starting town whose economy
has nowhere to stand.

⚠ **And the rock test asks `ov_kind_at` rather than predicting K_FACE from slope.** It looks
like a slope threshold and is not — the sub-treeline arm also wants `band <= 0.34`. Measured, a
slope-only proxy reports **50** face-like samples within a day's walk of town 2 where the real
classifier puts its **nearest face 46 hexes out**. That proxy would have been a second
classifier that disagrees with the first.

**Dropping the walkability objective alone gives a far better world** — the start moves from
town 3 to town 2:

| | town 3 (old) | town 2 |
|---|---|---|
| mean walkable slope | 1.02 | **0.403** |
| cliff steps (> 2.0) | 6303 | **36** |
| 45–63° steps | 16451 | **2079** |
| gentle-ramp steps | 3813 | **13451** |
| gentle alpine hexes | 0 | **20** |

⚠ **But town 2 has no mine, and the gate said so on the first run.** Its window holds 33 K_FACE
hexes and the nearest is **46 hexes from the centre — zero within `WORK_MAX_D` = 22**, so the
mine falls through to the "no rock in this window" branch that puts the mouth at the window
EDGE. `stocktest` went red exactly where it should: *"1 delivery in four peaceful days — the
supply loop is dead, and the pressure arm below then proves nothing."* The herb chain measured
9 deliveries and healthy, so the failure is the ore trade alone.

⚠ **Removing that edge fallback — which `sim.loft`'s own comment argues for in writing (*"SO A
VALLEY TOWN SIMPLY HAS NO MINE, and that is the honest answer"*) — makes it worse, and that is
the finding.** With no mine at all, `stocktest` loses its pressed chain *and* **`militiatest`
fails too**: plan #17 `S7`'s claim is literally about the ore face (*"the picket did not make
the ore face safer"*). The mining economy is load-bearing in two gates, so a mine-less valley
start is a plan #17 rewrite, not a side effect to absorb here.

**So the rule shipped is the correct one, and in this example world it still selects town 3** —
because no town has both gentle ground and rock within a day's walk. The four towns are: two
sea-level (no alpine at all), one gentle valley with distant rock, one mountainside with rock.
**The walkable start is not available in this world without a second decision**, and all three
candidates are outside plan #11:

> **OPEN, the user's call, now priced.**
> **(a)** Accept a mine-less valley start and re-derive plan #17's gates onto the herb chain —
> `stocktest` and `militiatest` both key on the ore face today. Biggest blast radius, and it
> gives up the "protect the forge that mends your gear" loop `S6` closed on the player.
> **(b)** Test whether a **distant** mine actually works: plan #17 already moved the furnace
> beside the mine and posted a guard on the works, so the 90-tick leg flip may no longer bind
> at 46 hexes. One gate run answers it, and if it passes, town 2 becomes eligible and nothing
> else changes. **Cheapest, and the one to try first.**
> **(c)** Give worldgen a town with both — the example world simply offers none.

Until it resolves, P6 can still build the parts that do not depend on the answer: the boundary
ring's geometry, the two-reading sampling seam, and the diff harness itself — all of which need
a height *function*, not a particular one. The instrument is `src/horizonprobe.loft`, which is
deliberately **not** in `make test`: it measures a world rather than asserting an invariant,
and the invariant it wants to assert (*the starting window is walkable*) would go red today.

## P5 tail — the blueprint PINNED, after reading the four layers (2026-07-22, second pass)

The section below stands, with **two corrections found by reading the source instead of the
table**. Both make the phase smaller and safer than it was described.

**1. Nothing needs inventing — the machinery is already built and gated.** The table reads
like four layers of new work. It is three wiring points:

| already exists | gated by |
|---|---|
| `hexmatch` recovers arcs from cells — a round tower collapses to ~1 arc at the right radius | `matchtest` (plan #5 P2) |
| `tag_edges(s, f, first_surf, e, mat)` writes fitted surfaces onto an `EdgeSet` | `matchtest` |
| `surf_arc(sf, cx, cy, r)` — exact radial normals, no facets | `edgetest`, `jointest` |
| `edge_block_arb` — nearest-surface arbitration where two parts meet | `jointest` (order-free) |

What is actually missing: `Sim` carries no `Surfaces` (`grep -c` → **0**), `build_field`
(`sim.loft:325`) calls bare `edge_block` so it never learns WHICH thing blocks, and `view3d`
(`view3d.loft:110`) extrudes a flat quad per blocked edge from `hex_edge_corners`.

**2. RECORD, do not infer — and the matcher becomes the CHECK.** The builder knows its centre
and radius exactly (`stamp_round_tower(…, cx, cy, rad)`), so it records them via `surf_arc`.
Fitting them back out of cells would be inference where exact parameters are in hand, which
is precisely the approximation an exact-invariant domain forbids. The matcher then earns a
better job: an **independent second derivation** that must agree with the recorded one.

**3. The claim "no verifiable midpoint until the renderer" is wrong, and that de-risks this.**
There is no *visible* midpoint — a recorded arc still draws as six flat quads — but there is a
**checkable** one: *the recorded arc and the matcher-fitted arc agree*. That is gateable with
no renderer at all, which means the phase HAS a safe stopping point after step A.

### The invariant

> **A tower built at radius `r` is recovered as ONE arc surface of radius `r`, and is drawn
> from that surface rather than from its cells.**

### The plotted end-result, in the units the gate will use

`rad = 2` hexes. `SCALE.md`: one hex step = 1.5 m, so the radius is **3.0 m** — and in world
units `2·√3 = 3.464`, since one hex step is `√3` world units. The door is **one hex gap** at
`(cx, cy + rad)` — the only ring cell with `tq == cx` and `tr > cy` (verified by walking the
builder's loop, not by reading its comment). Its clear width in metres is what P5 owes.

### Steps, each with what would have to break

| | step | gate | the negative control that must FIRE |
|---|---|---|---|
| **A1** | `stamp_round_tower` appends `(cq, cr, rad)` to a flat `vector<integer>` | existing gates stay green | — (pure addition) |
| **A2** | `build_field(solid, walls, w, h, towers, sf)` creates an arc per tower and tags its ring edges with `edge_block_arb` **before** the generic pass, so first-writer-wins leaves them alone | `towertest`: recorded r == fitted r | perturb the recorded radius by 10% → the agreement check must go RED |
| **A3** | `Sim` carries `surfs: Surfaces` (+ `feats: Features`) | full gate green | — |
| **B** | `view3d` reads `edge_surf`; an arc edge draws as curve, not facet | eye-height render at 8 m | a straight wall must NOT curve — render a wall and a tower in one frame |

**Ordering note that is load-bearing:** arcs must be tagged **before** the generic
`edge_block` pass. `edge_block` is first-writer-wins, so it will leave real surfaces alone;
the reverse order would let `SURF_NONE` claim the ring and the arcs would win only by the
accident that `surf_distance` returns 1e6 for an out-of-range id. Correct by construction
beats correct by accident.

**The B-step control is the one to design carefully.** "The tower curves" is not enough — a
renderer that curves *everything* passes it. The frame must contain a straight wall and a
tower, and the straight must stay straight. That is the P4 tautology lesson applied before
the fact rather than after.

## P5 — what remains, blueprinted rather than half-built (2026-07-22)

Two items are left: **towers are hexagons** and **doors are gaps**. Both look like finishing
touches and are not. Measured before stopping:

| layer | today | needed |
|---|---|---|
| builder | `stamp_round_tower` writes tile 4 on `hex_distance == rad` — a hex RING; the door is one `v = 0` cell | record the arc (centre, radius) and the opening as an interval |
| `Sim` | **zero** references to `Surfaces` or `Features` | carries both tables |
| `build_field` | `edge_block(e, …)` only — no surface id | `edge_block_surf` with the arc's id, then `apply_features` |
| renderer | `view3d` extrudes a flat quad per blocked edge from `hex_edge_corners` | consume the surface: an arc edge draws as curve, not facet |

**The trap that makes this one phase, not four commits:** stopping after layer 3 changes
nothing visible — a recorded arc still renders as six flat quads — so the work has no
verifiable midpoint until the renderer consumes surfaces. Anything less is a change that
gates green and looks identical, which this plan has been punished for three times already.

### The concrete plotted end-result to start from

A `tsize >= 2` town's lookout tower, `rad = 2` hexes = 3.0 m radius, rendered at eye height
from 8 m: its silhouette is a **circular arc**, not six flat facets, and the matcher recovers
**1 arc with r ≈ 3.0 m** from the built cells. The door below it has a **measured clear width
in metres** (the plan's stated gate) rather than being one open hex.

### Why this is also the EdgeSet convergence

`EXTRACTION.md` parks the crawler/`hex_field` edge merge on *"which layer owns `Surfaces`"*.
This phase answers it by force: whichever structure `Sim` ends up carrying the arc in **is**
the answer. So do the merge and this together, or do the merge first — not this first, or it
will be redone.

## P5, restated — the seam that has never been connected

**CORRECTED 2026-07-22, by reading the code instead of trusting the description.** My first
statement of this — "both halves exist and have never met" — was **wrong**. `sim.loft` already
integrates them: it reads `ovw.ov_towns[0]`, takes `ot_size`, and derives `nhouse = 3 +
tsize*2` houses in a ring with doors facing the square, round towers at `tsize >= 2`, and a
town wall with road-gates at `tsize >= 3` (`sim.loft:3005-3030`). The seam is wired and gated
by `traveltest` / `surfacetest` / `overlandtest`.

So P5 is **not** connecting two unconnected halves — it is **replacing the builder half of a
working integration**, which is a smaller job with a stronger regression net and a different
risk. What is primitive is the builder, not the seam:

| | overland says | `sim` builds today | the stack would build |
|---|---|---|---|
| where | scored site, spacing, size | ✓ consumed | unchanged — **it stays the authority** |
| houses | `ot_size` → count | tile stamp, rectangle, no height | walls, real eaves, 45° roofs, props |
| doors | — | a **gap** in the wall (`v = 0`) | a `Features` interval — a real opening |
| towers | — | `stamp_round_tower` = **a hexagon** | the matcher's true arc |
| fields | `ot_fld`, `K_FIELD` | tile kinds | worked ground, the orchard in the ring |

**Two consequences the earlier text missed:**

1. **P5 is coupled to P2.** Today's builder writes into `Sim.tiles` — exactly what P2 replaces
   with the field. P5 swaps a builder whose *substrate is changing underneath it*, so P5
   strictly follows P2 and its first act is to re-point the existing builder, not to write a
   new one.
2. **The live generator is cramped in metres too.** `hrad = 6.0 + 3.5·…` hexes puts 5–9 houses
   in a **9–14 m radius** with ~7.5 × 6 m houses; real villages space houses 10–20 m apart. The
   same correction just applied to `land.loft` is owed to the generator — and *that* one the
   player walks through.

The original (partly wrong) framing, kept because the WHERE/WHAT split is still the right way
to see it:

- **`overland.loft` decides WHERE.** A scored settlement list with a formation threshold
  (`bs = 1.2` — below it no town forms), enforced spacing, size from score, **`ot_fld`, the
  farmers' cut** (a field radius per town), roads between towns, roadside waystations, the
  keep sited *above* its town, and **ruins derived from the scorer's runners-up** — the sites
  the living world rejected, which were inhabited once. It renders as map characters.
- **Plans #5/#9/#10 decide WHAT.** Walls, roofs, arches, vaults, doors and windows as surface
  intervals, props derived from buildings, canopy-first trees. Demonstrated only on a
  **hand-placed** village in `land.loft`.

So P5 is not "add round towers" — it is **connecting the scorer to the builder**, so a village
exists because the terrain supports one, and is *made of* the geometry stack at real
measurements. The pieces that make this cheap: `ot_fld` already gives the ring the fields and
the orchard belong in; the roads already exist as `K_ROAD`; and plan #10 P5 already
demonstrated *derived* furnishing ("a village furnishes itself" — one door per opening).

> **We do NOT write that system — we integrate with it** (user, 2026-07-22). `overland` stays
> the sole authority on *where* a settlement is, how big, and what ground it claims. The
> geometry stack is a **consumer of its output**, never a second opinion about placement.
> No settlement logic moves into the field model; no second scorer is written; the seam is
> one-directional.
>
> This is the kernel/view split one level out, and it takes the same two checks:
> **the builder is a pure function of the overland's output** — the same `OvTown` yields the
> same village, every time — and the **negative control**: delete the builder entirely and the
> overland's own output must be *bit-identical*, because nothing downstream may feed back into
> placement. `overlandtest` is the regression net that proves it, unchanged.

The check that matters is the one a hand-placed scene cannot pass: **the same seed must
produce the same village, and a village must appear only where the score allows one.**

## P0 result — measured 2026-07-22

Rendered from `build/land.glb` with `tools/glbview.py`, eye at **1.6 m** above the terrain,
level camera (pitch 0), fov 60°, 1024×576. No engine code, as specified.

```sh
# a village door at 4 m                                    (p0_eye.png)
python3 tools/glbview.py build/land.glb out.png --eye 37.60,-29.68,-7.05 \
    --target 34.84,-25.98,-7.05 --fov 60 --size 1024x576 --sun 0.4,-0.7,0.6 --shadow 640
# the castle tower at 12 m                                 (p0_tower.png)
python3 tools/glbview.py build/land.glb out.png --eye=-0.69,-16.09,6.62 \
    --target=-9.00,-5.00,11.24 --fov 60 --size 1024x576 --sun 0.4,-0.7,0.6 --shadow 640
```

### The metre table

| feature | authored | at 4 m subtends |
|---|---|---|
| eye height | **1.60 m** | — |
| figure (`figure.loft`) | **1.75 m** | — |
| village cottage — door leaf | 1.45 m × 1.05 m | 20.6° · 181 px of 576 |
| village cottage — **eaves** | **1.51 m** | 21.4° · 188 px |
| village cottage — ridge | 4.55 m | 59.3° |
| hamlet cottage — door / eaves | 1.70 m / 1.77 m | — |
| keep — radius / height | 8.4 m / 13.0 m | — |
| tower — radius / height | 4.2 m / 11.0 m | — |
| **board** (0.9 m actor) | — | 12.8° · **112 px** at 4 m; 56 px at 8 m; 28 px at 16 m |

The board row is the **I-STAND metric-parity target**: a 0.9 m board and a 0.9 m wall at the
same distance must cover the *same* pixel span. It is computed here so P4 has a number to
hit rather than an impression to match.

### What the frame found

1. **The world is authored below human scale, and only an eye-height camera shows it.** A
   village cottage has **1.51 m eaves and a 1.45 m door** against a **1.75 m** figure: you
   must stoop 0.30 m to enter and cannot stand at any wall. The hamlet is better and still
   short (1.70 m door). `wallh = hgt * 0.52` (`land.loft:128`) is the source — the comment
   above it says a cottage is mostly roof, which is true, but it was achieved by shrinking
   the *wall* below head height rather than raising the ridge. **This is CLAUDE.md's content
   rule in miniature — geometry nerfed to fit, instead of the system built to carry it.**
   It also retro-explains plan #10 P9's unexplained door failure: the eave hid the door from
   a raised camera *because the wall is tiny*, not because the camera was wrong.
2. **A door is not an opening.** The wall is a solid cube and the door a leaf pasted on its
   face — there is nothing to walk through. That is exactly what plan #5 P5's `Features` /
   `apply_features` provides (intervals that make edges passable) and it has never been wired
   into a scene. **P5's job, now with a picture of why.**
3. **The round tower reads as round** at eye height — the 12-segment drum needs no work. One
   of the three target elements passes as-is.
4. **There is no actor to board.** The scene has a figure *mesh*; nothing camera-facing
   exists. So the target frame as written **cannot be fully plotted yet** — two of its three
   elements do not exist. That is a legitimate P0 outcome: the blueprint found what is
   missing before any code was written for it.

### Corrected the same day (user ruling: measurements are real by default)

`SCALE.md` → *The default is REAL — stylisation is the implementer's choice*. The scene now
carries the dimensions of the actual things, and the corrections were **derived, not tuned**:

| | was | now |
|---|---|---|
| cottage eaves | 1.51 m | **2.40 m** (wall plate, single-storey vernacular) |
| cottage ridge | 4.55 m | **4.49 m** — now *derived*: 45° pitch over the roof depth |
| door leaf | 1.45 × 1.05 m | **1.95 × 0.85 m** — 0.20 m head clearance for the figure |
| landscape tree | 7–11 m, 6–9 m spread | **13–20 m**, crown radius **0.42 × h**, trunk **h/22** |
| orchard | — | **5–7 m on a 9.5 m grid**, crown radius 0.46 × h |

**The orchard needs no new mechanism, which is the interesting part.** A trunk is an item in a
hex and the canopy is a field above it (plan #9), so *trunks on a regular lattice have
uncontested canopies* — no competition, hence no lean, equal crowns, uniform bole — while
scattered trunks contest their cells and the partition produces the lean and raised bole that
read as grown. **Planted vs grown is a placement pattern, not a second routine.** The scene
still uses stand-in geometry for both; P7 wires plan #9's real model behind them.

### One process note, kept because it nearly bit

I first read the village frame as *"the camera is looking down at the roof"* and was about to
correct the camera. The arithmetic said the framing was right: the house floor sits 0.21 m
below eye level and the eaves 1.30 m above it — the bright foreground is downhill terrain,
not a downward tilt. **Scored by eye, that frame fails; measured, it passes.** Which is the
plan #10 P9 lesson arriving before the damage instead of after.
