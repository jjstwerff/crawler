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
background and air box render from the hex world**, not from a backdrop.

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
verification channels) · `EXTRACTION.md` (this plan makes the stack's second consumer the
game itself — see *Order + risks*).

Source: `src/sim.loft`, `src/hexedge.loft`, `src/hexform.loft`, `src/scenemesh.loft`,
`src/view.loft`, `src/viewer.loft`, `src/worldmesh.loft`, `src/wallgeo.loft`.

## The invariants

Three, because this plan has three distinct exact-invariant surfaces. Every phase below
names which one it asserts.

**I-TRUTH — the field is the only passability truth.** One predicate answers *"can this
happen here"*; swapping the implementation under it changes **no answer** in any existing
world.

> *Measured before designing (protocol step 2 — count the re-assertion sites):*
> `is_blocked_move` has **5** call sites, all in `sim.loft`; `is_wall` **6** in `sim` +
> **2** in `wallgeo`; `tile_at` is broader but read-only. So N is small and local — the
> chokepoint is nearly there already, and P1 exists to finish it **before** anything is
> swapped underneath. `Sim` also already stores 3 canonical edge walls per hex
> (`s.walls` / `edge_wall_raw`), so `EdgeSet` is a *richer version of a structure the
> kernel already has*, not a foreign model bolted alongside it.

**I-STAND — everything drawn stands where the kernel says it stands, at its true metric
size.** The renderer holds no world state of its own; screen position is a pure projection
of kernel state.

**I-HORIZON — near and far are one world at two readings.** Architecture at 1.5 m/hex and
terrain at 15 m/hex (`OV_STEP`) sample the *same* hex world; where they meet the ground is
continuous — the same point has the same height from either reading.

**I-PARALLAX — a cached air-box layer is valid exactly while its parallax error is
sub-pixel.** The air box is drawn as several layers at increasing distance, each rendered
once into its own texture and *re-projected* rather than re-rendered. A layer at distance
`d` shifts by `t⊥ / d` radians when the camera translates by `t⊥` across the view; the cache
stays valid while that stays under one pixel's angular size, and must be re-rendered when it
exceeds it:

```
   reuse layer  ⟺  t⊥ / d  <  fov / screen_width
```

So the farthest layer (sky, clouds) re-renders almost never, mountains rarely, near hills
often — and **rotation costs nothing at any distance**, because turning re-samples the
cached layer instead of redrawing it. That matters here specifically: A/D turning is the
most common input in the game, and it is exactly the motion with **zero** parallax.

The rule is a computed threshold, not a tuning knob, which is what makes it checkable —
and it is the same idea as the existing idle-skip digest (`framekey.loft`), one level out:
*don't redraw what could not have changed.*

## Blueprint gate

| Phase | Concrete plotted end-result | Invariant pinned | Medium |
|---|---|---|---|
| **P0** | **the** target frame: first-person at eye 1.6 m at the plan #10 village gate — a round tower that is *round*, a door in its opening, a board 4 m ahead — with a metre table beside it (tower radius, door clear width/height, board apparent height at 4 m) | all three, as the picture they must reproduce | `tools/glbview.py` at eye height — **no engine code** |
| **P1** | the passability call graph, before/after, with the 13 sites named | I-TRUTH (chokepoint form) | a grep table in the phase commit |
| **P2** | for one seeded world: every `(hex, direction)` answer from the old model beside the new one | I-TRUTH (equality form) | a differential harness in `src/fieldtest.loft` |
| **P3** | a hex centre projected to a pixel, unprojected back to the same hex | I-STAND | pure-math headless test — **no GL needed** |
| **P4** | a board of height *h* m and a wall of height *h* m at the same distance, side by side | I-STAND (metric parity) | a GL frame + pixel span assertion (`make probe`) |
| **P6** | the boundary ring sampled from both readings, heights diffed | I-HORIZON | headless numeric test + a rendered horizon |
| **P6b** | for a walk of known length: which layers re-rendered, and the worst parallax error each frame | I-PARALLAX | headless numeric test (pure camera math) + a pop-free walk |

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
| **P0** — the target frame + its metre table | S | `glbview.py` PNG + the table; user confirms or amends | Open — **next** |
| **P1** — one passability predicate (pure refactor) | S | `make test` unchanged; the site table | Blocked on P0 |
| **P2** — the field under the kernel | M | `src/fieldtest.loft` differential: old ≡ new over every (hex,dir) | Blocked on P1 |
| **P3** — the 3D view: camera + world | MH | projection round-trip test; user visual in `make play` | Blocked on P2 |
| **P4** — boards, through the presentation seam | M | metric-parity probe; one instanced draw call | Blocked on P3 |
| **P5** — the stack in the generator: round towers, real doors, heights | M | the matcher gate on a *live* world (1 arc, r≈radius); door clear width in metres | Blocked on P2 |
| **P6** — the horizon: far field + air box from the hex world | MH | boundary-ring height diff; rendered horizon | Blocked on P3 |
| **P6b** — parallax layers: cache the air box, re-project it | M | re-render counts + worst per-frame parallax error; a pop-free walk | Blocked on P6 |
| **P7** — props + trees in the live world | M | existing plan #9/#10 gates, now on generated worlds | Blocked on P5 |
| **P8** — sprites redrawn side-on | H | the sprite recognition bar (CLAUDE.md), re-stated for elevation views | Blocked on P4 |
| **P9** — 2D retires; docs reconciled | S | `make test` green without `view.loft` | Blocked on P3–P6 |

**The playable milestone is P4.** P0–P4 is "the game is 3D and you can play it"; everything
after enriches it. That ordering is deliberate — *a functional game first*.

## Order + risks

**Order:** P0 → P1 → P2, strictly (the differential harness in P2 is worthless if P1 hasn't
collapsed the sites first). Then P3 → P4 for the playable milestone. P5 branches off P2 and
can run beside P3/P4. P6 needs P3. P7–P9 are the tail.

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
- **Extraction interaction:** this plan makes the *game* the stack's second real consumer,
  which is what `EXTRACTION.md`'s per-package DoD clause 4 asks for. Extraction should
  therefore wait for P5 — API cut against a real consumer beats one cut against a demo scene.

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
5. **How many air-box layers, at what distances?** The validity rule (I-PARALLAX) is fixed;
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
