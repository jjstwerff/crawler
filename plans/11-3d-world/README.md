# 11 — 3D world view: the hex field becomes the world you stand in

**Issue:** [`jjstwerff/crawler#11`](https://github.com/jjstwerff/crawler/issues/11) ·
**Value:** `G` · **Effort:** `VH` · **Depends on:** #5, #9, #10 (all built), #2 (the far field)

## Status

**ACTIVE — P0–P4 and P3b built AND SEEN** (the frames were rendered headlessly and looked at
once `xvfb` was installed — [`RESULTS.md`](RESULTS.md) → *VERIFIED*). **P3b landed 2026-08-11**:
landcover now rides a world texture derived from the field (`src/worldtex.loft`, sampled in
`view3d`), exact on the shipped world over 488 032 texels — and the measurement there says the
design named the *expensive* construction, which is written up under *P3b plumbing*.
**P6 IS DONE (2026-08-11)**: the ground has height, the two readings agree at exactly 0, and the far field reaches 48 km with its skyline matching the world to 0.77 degrees. The kernel now stands on the field: `sim.loft`
imports `hex_field` and `hexedge`, and **passability is an edge query** (`Sim.field`, an
`EdgeSet`) rather than a lookup in `Sim.tiles` — proved equal to the old model over ~135 000
`(hex, direction)` answers with zero mismatches from any reachable position
([`RESULTS.md`](RESULTS.md) → *P2 result*). `Sim.tiles` survives as **content** (stairs, cave
mouths, quest features), not as passage.

Movement is a **swept path** too (P2b): `sweep_path` walks the segment bisector by
bisector, so the same walk taken in 64 frames, 16 or 4 ends bit-identically — a point
sample walks straight through a thin wall at the coarse step.

What is still 2D is the *view*: `story` → `view` renders top-down from `wallgeo` +
`worldmesh`. P3 makes it the world the player stands in, in first-person 3D.

*(The earlier reading of this section — "the playing path imports none of `hexform` /
`hexedge` / … , the plan #5 stack is consumed only by the offline GLB scenes" — was true when
written and is what P2 ended.)*

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
there is the layer axis this plan's P5 inherits) · `TREES.md` ·
`plans/2-chunked-lod-world/` (the far field: `src/viewer.loft` already renders overland
terrain in 3D with LOD chunks) · `RENDER.md` + `plans/7-render/` (the GL substrate and the
verification channels) · `EXTRACTION.md` (the package split, and **§ The editor as the second consumer** — the
contract this plan's P3 must satisfy).

Source: `src/sim.loft`, `src/hexedge.loft`, **`hex_field`** (LIB — was `src/hexform.loft`,
extracted 2026-07-22), `src/scenemesh.loft`,
`src/view.loft`, `src/viewer.loft`, `src/worldmesh.loft`, `src/wallgeo.loft`.

## The design

Eight invariants, in **[`DESIGN.md`](DESIGN.md)** — the seam (**I-TRUTH**), what a wall
stops (**I-CROSS**), the camera (**I-STAND**), the two-scale world (**I-HORIZON**), and the
four that make the far field cheap, continuous and paintable (**I-PARALLAX**,
**I-DISPLACE**, **I-AGREE**, **I-PAINT**).
That file also holds the arithmetic fixing their reach, and the flight/orbit axis this
design must not foreclose. They are listed in dependency order: a later one is worthless if
an earlier one is false.

## Blueprint gate

| Phase | Concrete plotted end-result | Invariant pinned | Medium |
|---|---|---|---|
| **P0** | **the** target frame: first-person at eye 1.6 m at the plan #10 village gate — a round tower that is *round*, a door in its opening, a board 4 m ahead — with a metre table beside it (tower radius, door clear width/height, board apparent height at 4 m) | all seven, as the picture they must reproduce | `tools/glbview.py` at eye height — **no engine code** |
| **P1** | the passability call graph, before/after, with the 13 sites named | I-TRUTH (chokepoint form) | a grep table in the phase commit — **done; there were 32, not 13** ([`RESULTS.md`](RESULTS.md)) |
| **P2** | for one seeded world: every `(hex, direction)` answer from the old model beside the new one | I-TRUTH (equality form) | a differential harness in `src/fieldtest.loft` |
| **P2b** | one walk, taken at 60 fps and again in four steps and again in one leap — the SAME set of walls stops it | I-CROSS (dt-independence) | headless: replay one path at several step lengths, diff the blocked set |
| **P3** | a hex centre projected to a pixel, unprojected back to the same hex | I-STAND | pure-math headless test — **no GL needed** |
| **P3b** | one field/wood boundary drawn into the world texture, beside the traced loop it came from and the geometry under it | I-PAINT | rasterise the traced loop, diff against the loop — **exact, both sides are integer**. Done twice: a synthetic blob with a hole (`painttest`) and then the shipped world's 9 real landcover classes (`worldtextest`) |
| **P4** | a board of height *h* m and a wall of height *h* m at the same distance, side by side | I-STAND (metric parity) | a GL frame + pixel span assertion (`make probe`) |
| **P6** | the boundary ring sampled from both readings, heights diffed | I-HORIZON | headless numeric test + a rendered horizon. ✅ **RUN 2026-08-11 and green at exactly 0** over 404 ring hexes (`horizontest`), negative control 101/101. The premise had to be built first: there was only ONE reading, and `SCALE.md` now fixes the vertical |
| **P6b** | for a walk of known length: which layers re-rendered, and the worst parallax error each frame | I-PARALLAX | headless numeric test (pure camera math) — ✅ **RUN 2026-08-11**, and its answer is that the cache buys one layer, so the layers are not built (`parallaxtest`) |
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
| **P0** — the target frame + its metre table | S | `glbview.py` PNG + the table; user confirms or amends | **DONE** |
| **P1** — one passability predicate (pure refactor) | S | `make test` unchanged; the site table | **DONE** — `field_blocked(s,q,r,dir)` |
| **P2** — the field under the kernel | M | `src/fieldtest.loft` differential: old ≡ new over every (hex,dir) | **DONE** — 0 mismatches, ~135k answers |
| **P2b** — movement becomes a swept path, not a probe point | M | the same walk at 1/4/16× step length blocks on the same walls | **DONE** — bit-identical |
| **P3** — the 3D view: camera + world | MH | projection round-trip test; user visual in `make play` | ✅ **DONE** — `V` toggles; frames seen |
| **P3b** — the world texture: appearance off the mesh, derived from traced boundaries | MH | loop-vs-raster diff; the tint bake in `worldmesh` retires | ✅ **DONE** — exact on the SHIPPED world (`worldtextest`, 0/488032), texture + sampler live in `view3d`; the `worldmesh` bake retires with its only consumer in **P9** |
| **P4** — boards, through the presentation seam | M | metric-parity probe; one instanced draw call | ✅ **DONE** — the playable milestone; actors are flat colours until P8's atlas |
| **P5** — the derived world: the overland's settlements BUILT by the geometry stack | MH | the seal + agreement gate on the *live* world; door clear width in metres; a village placed by score, not by hand | **STEP A DONE (2026-08-11)** — every tower carries the arc the builder recorded (`hextower`, `towertest`, 8/8 sealed, 752 edges, 0 bad normals, doors 1.18–1.31 m). ⚠ The blueprint's *matcher* gate was measured first and **cannot fire at the size the game builds** — a circle and a hexagon are the same twelve cells at 3 m radius; the gate asks seal + agreement instead. It also found **three towers that were not towers** (two demolished by the town wall, one door opening into a pocket, one door built over) — all fixed. **STEP B DONE** too — an arc edge's corners are pushed onto the recorded circle and drawn as four pieces of it, with one Lambert model for every wall; 1504/1504 corners land to 8.4e-15 wu, and the rendered control diffs the same frame with arcs on/off: **3.86 % of pixels change, in one contiguous region, and every other wall is pixel-identical**. ⚠ Owed: an inspection camera — four hand-picked vantages failed because the world has heights now |
| **P6** — the horizon: far field + air box from the hex world | MH | boundary-ring height diff; rendered horizon | ✅ **DONE** — near reading exact (diff **0** over the 404-hex ring), camera stands on the surface it draws (28 800 points, 7e-15 wu), and the far field is drawn to **48 km** with its skyline matching the world's to **0.77°**. The seam is exact by construction (ring 0 = the window's own boundary hexes, 0 wu over 400 vertices). `SCALE.md` now states the vertical. `horizontest`, 9 rows. ⚠ The **air box** proper is P6b's. [`RESULTS.md`](RESULTS.md) → *P6a*, *P6b-far* |
| **P6b** — parallax layers: cache the air box, re-project it | M | re-render counts + worst per-frame parallax error; a pop-free walk | ✅ **CLOSED — the criterion is built and the machinery is DECLINED** (user ruling, 2026-08-11). `parallax.loft` + `parallaxtest` (pure camera math, no GL) price it: **DESIGN.md's cache table omits the 10x compression, so every lifetime in it is 10x too long**, and priced correctly the cache buys **1 of 4 layers** — the two nearest have budgets under one hex step and must be geometry anyway. **The far field stays geometry.** The criterion stays gated because it is the evidence, and because the flight/orbit regime is where it becomes true |
| **P6d** — the blend band where near geometry meets the sky-box | M | silhouette agreement at the switch distance; no pop, no ghost | ⚠ **ITS PREMISE LARGELY DISSOLVED with P6b's ruling** — there is no sky-box to switch TO, so there is no switch distance and no two representations to agree. I-AGREE's near/far half is satisfied by construction (the skirt's ring 0 IS the window's boundary, gated at 0 wu). What remains is the aerial-perspective blend, which is a look, not an invariant. **Re-scope or close — not closed unilaterally** |
| **P7** — props + trees in the live world | M | existing plan #9/#10 gates, now on generated worlds | Blocked on P5 |
| **P8** — sprites redrawn side-on | H | the sprite recognition bar (SPRITES.md), re-stated for elevation views | Blocked on P4 |
| **P9** — 2D retires; docs reconciled | S | `make test` green without `view.loft` | Blocked on P3–P6 |

**The playable milestone is P4.** P0–P4 is "the game is 3D and you can play it"; everything
after enriches it. That ordering is deliberate — *a functional game first*.

## Phase records

What each phase found — P0's target frame, its metre table and the three defects it
surfaced; P5's correction after reading the code — lives in **[`RESULTS.md`](RESULTS.md)**.

## Order + risks

**Order:** P0 → P1 → P2, strictly (the differential harness in P2 is worthless if P1 hasn't
collapsed the sites first). Then P3 → P4 for the playable milestone. P5 branches off P2 and
can run beside P3/P4. P3b and P6 both need P3; **P3b before P6**, because the far layers
each want the world texture at their own resolution, and building them against baked vertex
colour would be building them twice. P7–P9 are the tail.

**When the seam takes meshes, target glTF HUMANOID (VRM-compatible) — decide it now, it is
free now and expensive later.** VTuber tooling has made real-time performance capture a
consumer commodity, and the valuable part is not the models but the **standard**: VRM is a
glTF extension with a fixed humanoid bone hierarchy, and crawler already emits glTF. Adopting
it inherits an avatar ecosystem, retargeting tools and cheap capture software instead of a
bespoke skeleton nobody else speaks. Their models being *over-detailed* for a 4–20 m framing
is **headroom, not waste** — detail decimates, absence does not.

> **Measured gap:** `glb` is **static-only today** (2 pub fns; no skin/joint/weight/animation
> in either `glb` or `mesh3d`). Skinned actors are real library work — which passes the
> over-engineering test, since every consumer of `hexscene` needs it.

**And the crowd must be procedural, which is the same substitution as everywhere else.** The
capture loop is one-performer/one-camera — you cannot webcam-capture 22 civilians. But a
VTuber rig reads as *alive* on a handful of driven parameters (head pose, a few blend shapes),
which is evidence that **sparse parameters carry a convincing performance**. So: gait derived
from speed, load and mood, not a library of baked clips. Capture is for the player character
and for authoring a small motion library once.

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
- ~~**`xvfb` is not installed**~~ ✅ **it is** — `make probe` and `src/shot3d.loft` both run
  headlessly, and P3/P4's frames were checked that way. ⚠ **But `make probe` itself rots** —
  plan #16 `M4` found it red and hung; see `CLAUDE.md`'s entry before trusting a green from it,
  and note `probes/world_r4`/`world_r5` are *currently failing* against 2026-06-12 goldens.
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
