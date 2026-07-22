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
