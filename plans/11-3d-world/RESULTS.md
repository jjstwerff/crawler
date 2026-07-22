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
