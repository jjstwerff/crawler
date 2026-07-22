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

Six, because this plan has six distinct exact-invariant surfaces — the seam, the camera,
the two-scale world, and the three that make the far field cheap and continuous. Every
phase below names which one it asserts. They are listed in dependency order: a later one is
worthless if an earlier one is false.

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

**I-DISPLACE — a vertical face is made by moving points sideways, and the mesh never
folds.** The far field is a height raster whose vertices are displaced *horizontally* onto
feature lines, so a wall becomes a vertical quad with no extra geometry: real depth, real
occlusion, real parallax, one draw call per chunk — everything an impostor cannot do. The
exact invariant is non-inversion: **every triangle keeps positive signed area**, which
bounds displacement to half the sample spacing and makes a vertex serve exactly one
arbitrated feature (*nearest wins, ties to the lower id* — the plan #5 P3 rule, reused
rather than reinvented).

Its reach is fixed by arithmetic already in the repo, not by taste:

```
   detail cell   1.46484375 m   (OV_TILE_M/1024, src/chunk.loft)
   hex step      1.5        m   (M_PER_HEX_STEP, src/scale.loft)
   ⇒ a structure WALL is exactly one sample — resolvable by construction, at Nyquist
   ⇒ a tree TRUNK (~0.3 m) is 5x below the sample — never resolvable, at ANY distance
     (both shrink together, so the ratio does not improve with range)
```

So the *structures* half is sound and the *trees* half is the claim to falsify first: the
displaced field can only ever give a tree its **mass**, never its trunk. That is adequate
only past the range where the trunk goes sub-pixel (~1000 m at 1080p/0.8 rad, where the
trunk is 0.72 px); nearer than that the trunk is visible and unrepresentable, and plan #9's
**canopy cards** carry the band. Heightfields also cannot overhang, which is the same
statement from the other side: a crown wider than its trunk is not a height function.

> **This is the third appearance of one rule** — plan #5's resolution floor, plan #9 T8's
> `R > 2√3` field/object fork, and now this. `src/scale.loft` already exposes it as
> `resolvable_m()`. Settle it in **one** form (the BUNDLE.md precedent: a rule that shows up
> three times gets answered once), rather than growing a third private copy.

**I-AGREE — representations agree where they meet; the blend hides residue, it does not
create agreement.** Near geometry, displaced far field and each parallax layer must produce
the **same silhouette at their switch distance** (sub-pixel), because a cross-fade between
two *different* worlds reads as ghosting and doubled edges, not as a transition. Blending is
therefore a finishing pass over an already-agreeing pair — the tempting inversion ("the
blend will cover it") is exactly the elegant absorption this plan is trying not to make.
Falsifiable: render one structure at its switch distance both ways and diff the silhouettes;
**negative control** — offset one representation by a single cell and the diff must go red.

> **The trap that makes this silent:** 1.46484 m and 1.5 m *look* like the same grid. They
> are not. The exact relation is **125 hex steps = 128 detail cells = 187.5 m** — rational,
> so the resample is exact and periodic if written in that form, and drifts **24 cells per
> overworld tile** if assumed 1:1. The symptom is distant structures sliding off their
> foundations in proportion to distance from the origin: a `val:S` silent-corruption shape,
> which is why the ratio is stated here rather than discovered later.

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
| **P6c** | one distant building **and** one distant tree from the same displaced raster, plotted beside the near geometry at the switch distance | I-DISPLACE (+ the trees claim, to break) | a Python probe — **the cheapest medium, before any loft** |
| **P6d** | the same structure crossing its switch distance, frame by frame | I-AGREE | silhouette diff + a walk-through with no pop and no ghost |

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
| **P6c** — displaced height raster: vertical walls from a heightfield | MH | Python probe first; then triangle-area (no-fold) + silhouette gates | Blocked on P6 |
| **P6d** — the blend band between representations | M | silhouette agreement at the switch distance, then a pop-free, ghost-free crossing | Blocked on P6c |
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
5. **Where do the switch distances sit, and are they one dial or several?** Near geometry →
   cards → displaced raster → cached layers is four representations and three switches. The
   *rule* is fixed (a representation is used where its smallest meaningful feature is at
   least one sample — `resolvable_m()`); the *distances* fall out of it once P6c measures
   what the eye actually accepts. Resist tuning them independently: three dials that drift
   apart is how a world stops agreeing with itself.
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
