# 11 — 3D world view: the hex field becomes the world you stand in

**Issue:** [`jjstwerff/crawler#11`](https://github.com/jjstwerff/crawler/issues/11) ·
**Value:** `G` · **Effort:** `VH` · **Depends on:** #5, #9, #10 (all built), #2 (the far field)

## Status

**ACTIVE — blueprint phase, nothing built.** Today the playing path (`story` → `view` →
`sim`) renders a top-down 2D world from `Sim.tiles` + `wallgeo` + `worldmesh`, and
**imports none of** `hexform` / `hexedge` / `hexway` / `hexcanopy` / `hexprim`: the
plan #5/#9/#10 stack is consumed only by the offline GLB scenes (`scene1`, `land`). This
plan makes the field the world the player stands in, in first-person 3D.

Decisions taken with the user (2026-07-22): **first-person at eye height**; **3D replaces
the 2D view** once it reaches parity; **one front view per actor**, loader ready for
`_r0..r7`; **boards carry the existing top-down PNGs for now** (wrong-looking, accepted —
actors were never the focus); **boards are a waypoint** toward animated meshes; **the
background and air box render from the hex world**, not from a backdrop; and **normal
gameplay defaults to the parallax sky-box** — the full terrain projection is a flight/fall
regime, so the displaced raster (**I-DISPLACE**) leaves the normal-play path entirely and
travels with the flight/orbit pass.

## Goal

The player walks around inside the hex field in first-person 3D — near architecture,
far terrain and sky all derived from the same hex world — with actors drawn through a
presentation seam that today emits camera-facing boards and later emits animated meshes.

## Anchors

`SCALE.md` + `src/scale.loft` (one grid, two readings — the contract this plan leans on
hardest) · `PROPS.md` · `plans/5-geometry/INTEGRATION.md` (the field's phases; **Track 2**
there is the layer axis this plan's P5 inherits) · `plans/9-canopy-trees/TREES.md` ·
`plans/2-chunked-lod-world/` (the far field: `src/viewer.loft` already renders overland
terrain in 3D with LOD chunks) · `RENDER.md` + `plans/7-render/` (the GL substrate and the
verification channels) · `EXTRACTION.md` (the package split, and **§ The editor as the second consumer** — the
contract this plan's P3 must satisfy).

Source: `src/sim.loft`, `src/hexedge.loft`, **`hex_field`** (LIB — was `src/hexform.loft`,
extracted 2026-07-22), `src/scenemesh.loft`,
`src/view.loft`, `src/viewer.loft`, `src/worldmesh.loft`, `src/wallgeo.loft`.

## The design

Seven invariants, in **[`DESIGN.md`](DESIGN.md)** — the seam (**I-TRUTH**), the camera
(**I-STAND**), the two-scale world (**I-HORIZON**), and the four that make the far field
cheap, continuous and paintable (**I-PARALLAX**, **I-DISPLACE**, **I-AGREE**, **I-PAINT**).
That file also holds the arithmetic fixing their reach, and the flight/orbit axis this
design must not foreclose. They are listed in dependency order: a later one is worthless if
an earlier one is false.

## Blueprint gate

| Phase | Concrete plotted end-result | Invariant pinned | Medium |
|---|---|---|---|
| **P0** | **the** target frame: first-person at eye 1.6 m at the plan #10 village gate — a round tower that is *round*, a door in its opening, a board 4 m ahead — with a metre table beside it (tower radius, door clear width/height, board apparent height at 4 m) | all seven, as the picture they must reproduce | `tools/glbview.py` at eye height — **no engine code** |
| **P1** | the passability call graph, before/after, with the 13 sites named | I-TRUTH (chokepoint form) | a grep table in the phase commit |
| **P2** | for one seeded world: every `(hex, direction)` answer from the old model beside the new one | I-TRUTH (equality form) | a differential harness in `src/fieldtest.loft` |
| **P3** | a hex centre projected to a pixel, unprojected back to the same hex | I-STAND | pure-math headless test — **no GL needed** |
| **P3b** | one field/wood boundary drawn into the world texture, beside the traced loop it came from and the geometry under it | I-PAINT | rasterise the traced loop, diff against the loop — **exact, both sides are integer** |
| **P4** | a board of height *h* m and a wall of height *h* m at the same distance, side by side | I-STAND (metric parity) | a GL frame + pixel span assertion (`make probe`) |
| **P6** | the boundary ring sampled from both readings, heights diffed | I-HORIZON | headless numeric test + a rendered horizon |
| **P6b** | for a walk of known length: which layers re-rendered, and the worst parallax error each frame | I-PARALLAX | headless numeric test (pure camera math) + a pop-free walk |
| **P6d** | the same structure crossing the near/sky-box switch, frame by frame | I-AGREE | silhouette diff + a walk-through with no pop and no ghost |

Phases **P5, P7, P8, P9** have no new exact-invariant surface of their own — they reuse
gates that already exist (the matcher's arc recovery, the props/canopy gates, the sprite
recognition bar, the full suite as a regression net). Stated explicitly, because silence
would read as "gate done" rather than "gate N/A".

**Every phase carries a negative control** (the plan #10 P9 lesson — three green checks
once stood over questionable images): corrupt the input by one hex, or one unit, and the
check must go red.

## Phases

| Phase | Effort | Verify | Status |
|---|---|---|---|
| **P0** — the target frame + its metre table | S | `glbview.py` PNG + the table; user confirms or amends | **MEASURED** — awaiting your confirm/amend |
| **P1** — one passability predicate (pure refactor) | S | `make test` unchanged; the site table | Blocked on P0 |
| **P2** — the field under the kernel | M | `src/fieldtest.loft` differential: old ≡ new over every (hex,dir) | Blocked on P1 |
| **P3** — the 3D view: camera + world | MH | projection round-trip test; user visual in `make play` | Blocked on P2 |
| **P3b** — the world texture: appearance off the mesh, derived from traced boundaries | MH | loop-vs-raster diff; the tint bake in `worldmesh` retires | Blocked on P3 |
| **P4** — boards, through the presentation seam | M | metric-parity probe; one instanced draw call | Blocked on P3 |
| **P5** — the derived world: the overland's settlements BUILT by the geometry stack | MH | the matcher gate on a *live* world (1 arc, r≈radius); door clear width in metres; a village placed by score, not by hand | Blocked on P2 |
| **P6** — the horizon: far field + air box from the hex world | MH | boundary-ring height diff; rendered horizon | Blocked on P3 |
| **P6b** — parallax layers: cache the air box, re-project it | M | re-render counts + worst per-frame parallax error; a pop-free walk | Blocked on P6 |
| **P6d** — the blend band where near geometry meets the sky-box | M | silhouette agreement at the switch distance; no pop, no ghost | Blocked on P6 |
| **P7** — props + trees in the live world | M | existing plan #9/#10 gates, now on generated worlds | Blocked on P5 |
| **P8** — sprites redrawn side-on | H | the sprite recognition bar (CLAUDE.md), re-stated for elevation views | Blocked on P4 |
| **P9** — 2D retires; docs reconciled | S | `make test` green without `view.loft` | Blocked on P3–P6 |

**The playable milestone is P4.** P0–P4 is "the game is 3D and you can play it"; everything
after enriches it. That ordering is deliberate — *a functional game first*.

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

## Order + risks

**Order:** P0 → P1 → P2, strictly (the differential harness in P2 is worthless if P1 hasn't
collapsed the sites first). Then P3 → P4 for the playable milestone. P5 branches off P2 and
can run beside P3/P4. P3b and P6 both need P3; **P3b before P6**, because the far layers
each want the world texture at their own resolution, and building them against baked vertex
colour would be building them twice. P7–P9 are the tail.

**The actor presentation seam (P4) is a design constraint, not a rendering detail.** Because
boards are explicitly a waypoint toward animated meshes, the renderer must ask *"how is this
actor presented?"* through one seam whose implementation is swappable. Today it answers with
a camera-facing quad + a texture; later with a mesh + animation state. If P4 lets billboard
assumptions leak into the frame loop, the mesh phase pays for it — so the seam is P4's real
deliverable and the boards are just its first implementation.

**Risks and traps:**

- **loft#392 — a `fn(...) -> vector<single>` whose result goes to `gl_upload_vertices`
  silently aborts the program** (no output, no PNG, exit 0). P3/P4 build vertex and instance
  buffers; **inline the buffer-building loop in the caller**, never route it through a
  returning helper. This is the single most likely way this plan loses an afternoon to a
  silent failure.
- **loft#496 — `vec += [f(struct_temp)]` nulls every element but the first** (interpreter
  only). Hoist the call into a local first. P4's per-frame instance records are exactly this
  shape.
- **Native GL is upstream-gated** (loft#396 / E0514 — `make viewer-release` fails by design).
  The 3D game runs on the default/interpreted path until that clears, so **P3 measures frame
  cost rather than assuming it**. The design's defence is structural: static world VBOs
  uploaded once, actors as one instanced call, so per-frame CPU work in loft stays near zero.
- **`xvfb` is not installed**, so `make probe` — the channel P4 and P6 want — cannot run yet.
  `glbview.py` needs nothing, which is why P0 uses it. Installing is one line
  (`sudo apt install xvfb`) and unblocks the GL pixel channel for the whole plan.
- **Store pressure:** the field lands in `Sim`, already the biggest struct in the repo. Keep
  the survival guide's habits (one `Sim` live, index-write idiom for hot collections, no thin
  arity-reducing pub wrappers).
- **The seam law** (BUNDLE.md → *Standing check*) is re-checked every phase: mechanism
  engine-side, content bundle-side. P5 and P7 touch it directly.
- **Extraction is now on the critical path, not the tail** (user, 2026-07-22: an in-world
  editor built outside crawler by a second agent). Without packages the editor must copy
  crawler's source, which the DoD forbids. Sequencing is **build new, extract settled** — new
  routines (stencils, the document format) land package-side now; crawler's settled modules
  migrate after **P2**, when the kernel has shown what it needs. The contract is
  `EXTRACTION.md` → *The editor as the second consumer*.
- **P3 builds the renderer as a PACKAGE (`hexscene`), not as crawler-internal `view3d`.** The
  editor is in-world and outside crawler, so a crawler-private renderer would be written
  twice and diverge. `scenemesh` is already renderer-agnostic; only the GL half is new.

## Open design questions

1. **Does `Sim.tiles` survive as a derived cache, or is it deleted?** Decide *in P2*, with
   the differential harness in hand — informed, not now. (`tile_at` has read-only consumers
   in `view`, `worldmesh` and several tests; a derived cache may be the cheap answer.)
2. **When does the layer axis enter?** The field has levels (bridges, tunnels, ramparts);
   the kernel has depth only. `plans/5-geometry/INTEGRATION.md` Track 2 already blueprints
   this (GATING / LINKS / ROUND-TRIP / L1-DEFAULT). Probably after P3 — a first-person
   camera makes a rampart worth having.
3. **What is the air box a function of?** Zone, depth, time of day, weather — resolved in
   P6. The constraint is fixed: it derives from the hex world, never from a fixed backdrop.
4. **Does the 2D view survive as the automap?** P9 retires it as *the* renderer; whether a
   plan view returns as a map/editor screen is a separate, later call.
5. **Where do the switch distances sit, and are they one dial or several?** For normal play
   it is near geometry → cards → cached layers: three representations, two switches (the
   displaced raster is a third switch only in the flight regime). The *rule* is fixed — a
   representation is used where its smallest meaningful feature is at least one sample,
   `resolvable_m()` — and the *distances* fall out of it once P6d measures what the eye
   actually accepts. Resist tuning them independently: dials that drift apart is how a world
   stops agreeing with itself.
6. **How many air-box layers, at what distances?** The validity rule (I-PARALLAX) is fixed;
   the *number* of layers is a cost trade — more layers means more textures but rarer
   re-renders each. Settle it in P6b by measuring re-render counts on a real walk, not by
   picking a number now. Note the mechanism is a flow-back candidate: it is the same
   per-layer cache (`make_layer` / `invalidate` / `draw_layer`) already specified for the
   painter in `EXTRACTION.md` §6(b), one dimension up.

## See also

Reference docs: `SCALE.md` (the two readings) · `PROPS.md` · `RENDER.md` · `BUNDLE.md`.
Sibling plans: **#5** (the field; Track 2 is P5's ancestor), **#9** (canopy), **#10**
(props), **#2** (the far field + the native-GL blocker), **#7** (the GL substrate and the
probe channels), **#4** (Phase G unblocks once P5 lands real doors and round forms).
Upstream: loft#392, loft#396, loft#496 — worked around here, never blocked on.
