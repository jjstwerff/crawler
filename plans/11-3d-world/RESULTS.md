# Plan 11 — what each phase found

> The **plan** (status, phases, order, risks) is [`README.md`](README.md); the **design**
> (the seven invariants and their arithmetic) is [`DESIGN.md`](DESIGN.md). This file is the
> third concern: what each phase actually *discovered*, which is neither intent nor design and
> was crowding both.

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
