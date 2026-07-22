# Plan 11 — the design: eight invariants and what they cost

> The **plan** (status, phases, order, risks) is [`README.md`](README.md). This file holds
> the design it executes: the invariants, the arithmetic that fixes their reach, and the
> long-horizon axis the design must not foreclose. Split out when the README passed its
> line budget — reference content belongs beside the plan, not inside it.

## The invariants

Eight, because this plan has eight distinct exact-invariant surfaces — the seam, **what a
wall stops**, the camera, the two-scale world, and the four that make the far field cheap,
continuous and paintable. Each phase in [`README.md`](README.md) names which one it asserts.
They are listed in dependency order: a later one is worthless if an earlier one is false.

**I-TRUTH — the field is the only passability truth.** One predicate answers *"can this
happen here"*; swapping the implementation under it changes **no answer** in any existing
world.

> The field's primitive is the **edge**, not the cell. A cell being solid is a *derived*
> reading of it (all its boundaries impassable), which is why the predicate's domain is
> `(hex, direction)` and `DIR_HEX` is the convenience arm, not the truth. I-CROSS below is
> why that ordering matters rather than being a matter of taste.

**I-CROSS — a wall stops you because your PATH crossed it, never because you were found
inside it.** (User ruling, 2026-07-22.) Passability is a property of the **trajectory**
between two positions, not of either position. We never ask *"is the character inside an
object"* — we ask *"does the path it took cross a boundary it may not cross"*.

Two consequences, and the second is the one with teeth:

1. **"Inside a wall" stops being a state to detect and recover from.** It becomes a state
   that cannot be *reached*, because reaching it requires a crossing, and the crossing is
   what we measure. There is no push-out, no un-stick, no "if embedded, nudge to the
   nearest open hex" — that whole family of corrections exists only to serve a model that
   asks the wrong question.
2. **The answer must not depend on `dt`.** Dropping frames must not change which walls stop
   you; neither must moving fast — *falling* is the case that matters, and it is exactly
   when a wall most needs to hold. **This is not an optimisation and not robustness
   hardening: it is whether a wall is a wall.** A test whose verdict changes with frame rate
   has not answered the question, it has sampled it.

> *Measured on the current model before adopting this (a fine 200-substep march as the
> oracle, over 26 028 paths from open hexes on the depth-0 surface):*
>
> | step | frame it stands for | paths a trajectory blocks | **missed by today's point-sample** |
> |---|---|---|---|
> | 0.10 u | 60 fps | 0 | 0 |
> | 0.60 u | 10 fps | 0 | 0 |
> | 1.00 u | — | 1892 | 0 |
> | 1.50 u | a 4 fps hitch | 2261 | **361 — 16 %** |
> | 3.00 u | a fall | 2696 | **1443 — 54 %** |
>
> The zero rows are **not** evidence of correctness: from a hex centre a 0.6 u move usually
> crosses no boundary at all (the apothem is 0.866 u), so there is nothing to miss. The
> comparison only becomes meaningful once the step can cross an edge — and from there the
> miss rate climbs with step length, which is the dependence I-CROSS forbids. At a fall,
> **more than half** the walls in the player's way stop nothing.

### Why this invariant exists: thin geometry is where physics engines die

(User, 2026-07-22.) Fences, thin walls and stairs are notoriously fickle for physics
engines — *see the old Bethesda games* — and getting them wrong does not produce one bug, it
produces breakage all over the world. The failure is structural, and it has three parts that
all share a root: **the model treats a barrier as a thin volume and asks whether you are
inside it.**

| what breaks | why | in a volume-and-penetration model |
|---|---|---|
| **tunnelling** | a fence rail is thinner than one timestep's travel | the step lands past it; nothing was between the samples |
| **jitter, then clip-through** | thin geometry has near-zero penetration depth, so the push-out is tiny and its **direction ambiguous** | the recovery resolves to the *wrong side* — the mechanism meant to fix the bug is what puts you through the fence |
| **stairs catching** | a flight is a stack of thin ledges and risers; a swept capsule snags on every nosing | papered over with a step-up teleport hack, which then has its own failure modes |

**The lattice is what makes this tractable, and it only pays if the primitive is the edge.**
A wall here is a **1-D boundary on the exact-integer lattice**, not a thin solid: there is no
thickness to be smaller than the timestep, and "did this segment cross this edge" is an exact
predicate with no epsilon. Push-out never has to be written, because *inside* is unreachable
— so the whole failure column above is **unrepresentable rather than handled**. Stairs escape
it twice over: height is a per-cell scalar (`Heights`, plan #5 P12), so a flight is a plane
move plus a height lookup with no ledges to snag on, and the double-riser discontinuity that
would break a step is already excluded by the minimum-tread closed form and gated by
`stairtest`'s monotonicity check. A *domestic* staircase never enters the field at all — its
going is below one hex step, so `SCALE.md` already rules it an object.

This is the over-engineering test passing cleanly (`CLAUDE.md`): thin-geometry collision is a
hard part, every consumer of `hex_field` needs it, and a small team cannot afford to debug
physics jank. Solve it once in the lattice and no one downstream pays it again.

### The specific mechanism: an over-reduced point, and two corrections that compose

(User, 2026-07-22.) *A person normally gets reduced to a single point where they stand, and
moving against a wall **and** a step easily brings that point outside normal geometry.*

That is the whole bug in one sentence, and the conjunction is doing the work. Each correction
is individually small and individually defensible — the wall's push-out shifts the position a
little, the step's ground resolution snaps it a little — but they fire in the **same frame**,
on a position that has been reduced to one point, and **neither correction is checking the
constraint the other one maintains**. Their composition lands the point on the far side of a
boundary that nothing was watching. The wall-and-step corner is where two thin features meet,
which is exactly why that corner is the classic place to leave the world.

Two structural properties answer it, and both are already true here:

- **Nothing corrects the position, so corrections cannot compose.** Under I-CROSS a position
  changes only by a move that was *accepted*; a rejected crossing means the move does not
  happen, or is clamped **to the boundary it failed to cross**. There is no second,
  independent nudge with its own opinion. The failure needs two corrections to interact; the
  model has zero.
- **The plane is a PARTITION, not a mesh — so there is no outside to get to.** `px_to_hex`
  is total (pure arithmetic and rounding, verified: no failure case, no "off the mesh"), so
  every point in the plane is in exactly one hex, and beyond the map `tile_at` answers **1 —
  rock, not void**. A triangle mesh has cracks between faces and a region outside itself; a
  lattice partition has neither. *There is nowhere for "outside normal geometry" to be.*

> **The bar is normal play, not impossibility** (user: *"I do not despise speed runners,
> however normal players should not fall through the world all the time"*). So this is
> deliberately **not** a mandate to build clamping, anti-cheat or out-of-bounds recovery
> machinery — that machinery is the composing-corrections failure, reintroduced. Getting out
> of the world should stay possible and *earned*; what must never happen is the ordinary
> player leaving it by walking into a corner. Which is the testable form: **the failure must
> require deliberate effort, not arise from a walk.** P2b's dt sweep is that test — a player
> who drops frames is not trying to escape.

> **Found while writing this down: the fence is currently a FILLED CELL.** Both placements
> write `tiles[i] = 5` — the farmers' fences along the roads (`sim.loft:3015`) and the
> livestock pen (`sim.loft:3656`). At 1.5 m per hex that is a 1.5 m thick barrier: not a
> fence, a wall of blocks. **The thin thing was thickened until the point-sample model could
> see it** — which is `CLAUDE.md`'s content rule inverted, geometry nerfed to fit a
> half-built engine. It also explains why fences were the site of *both* bugs found today
> (the ungated solidity arm, and blink landing inside one).
>
> Under the edge primitive a fence is an **edge feature**, sitting between two hexes — and
> the kernel already has that structure: `s.walls` stores 3 canonical edges per hex, and
> plan #5 P5's `Features` intervals are how an edge carries an opening (the gate gap). So
> this is a re-pointing in P2, not new machinery. **Gate it by measurement, not by eye:** a
> fence must be thinner than a hex, so after P2 the fence occupies zero cells and *n* edges.

> **Still open — the VERTICAL crossing.** I-CROSS as stated is planar: a path crossing hex
> edges. Height is a separate per-cell field, and nothing yet says what a path may do
> *vertically* — today the plane test would happily walk you up a 3 m riser. The companion
> rule (a step is crossable only within a step-up bound, else the boundary is impassable)
> belongs with the layer axis, open question 2. **Do not read I-CROSS as covering stairs
> yet — it covers the plane, and the plane is what P2 builds.**
>
> The partition argument does carry upward, though, and it is the reason *falling through the
> world* is the tractable half: falling needs a **hole in the floor's domain**, and a per-cell
> height over a total partition has none — every point in the plane has exactly one hex, and
> that hex has a height. So the vertical work is about **which steps may be crossed**, not
> about plugging voids. That is a much smaller question than the one Bethesda was answering.

**Where the current model asks the wrong question:** `pos_blocked` / `sim_step`
(`sim.loft`) advance the player by sampling **one probe point** per axis, one radius ahead,
and asking `is_blocked_move(hex(centre), hex(probe))`. Both the axis separation and the
single probe are point tests, and `is_blocked_move` **skips the edge check entirely** when
the two hexes are not adjacent (`hex_neighbor_dir < 0`) — so a long step is not merely
approximated, it is unchecked. That is the site P2/P3 replace with a segment-versus-boundary
test. What stays legitimate is the *discontinuous* case: a **teleport** has no trajectory,
so `field_blocked(.., DIR_HEX)` is the only question available to it and the right one
(`sim_blink`). Hex-locked AI (`compute_flow` / `flow_step`) is likewise a genuine cell-and-
edge graph walk, not a swept body.

> *Estimated before designing (protocol step 2 — count the re-assertion sites):*
> `is_blocked_move` **5** call sites all in `sim.loft`; `is_wall` **6** in `sim` + **2** in
> `wallgeo`; `tile_at` broader but read-only — 13 in all. **P1 measured it: 32**, because
> the estimate counted no test sites, missed `tile_solid` entirely (7 sites), and — the
> part that mattered — the solidity rule was written out **three times**, one of them
> disagreeing. Corrected graph and the two negative controls: [`RESULTS.md`](RESULTS.md)
> → *P1 result*. The conclusion survives the correction (N is small and local) but the
> estimate itself did not, which is the reason P1 ran before P2 rather than beside it.
>
> `Sim` also already stores 3 canonical edge walls per hex (`s.walls` / `edge_wall_raw`),
> so `EdgeSet` is a *richer version of a structure the kernel already has*, not a foreign
> model bolted alongside it.
>
> **P1 landed the chokepoint:** `field_blocked(s, q, r, dir)` in `sim.loft` — `dir =
> DIR_HEX` asks about the hex, `0..5` about the step out of it. Its domain is exactly what
> P2's differential harness enumerates.

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

### The two regimes, decided by I-PARALLAX alone

**Normal gameplay defaults to the parallax sky-box. The full terrain projection is a
flight/fall regime** (user, 2026-07-22) — and this needs **no new rule and no mode flag**,
because I-PARALLAX already computes it. The cache-validity time is `pixel_angle · d / speed`:

| layer | walking (1.5 m/s) | flying (100 m/s) | orbit (7800 m/s) |
|---|---|---|---|
| 2 km | 0.6 s | 8 ms | 0.1 ms |
| 10 km | 2.8 s | 42 ms | 0.5 ms |
| 50 km | 13.9 s | 208 ms | 2.7 ms |

Walking, a cached layer holds for **seconds**, so the sky-box is **faithful rather than a
cheat**: from 1.6 m of eye height, distant terrain genuinely *is* a slowly-changing
silhouette, and a layer is an honest sampling of it. Flying, the same cache dies every
frame — caching is then pointless, and the real geometry must be projected. One criterion,
two regimes, and nothing to keep in sync.

**Consequence for the order of work:** the displaced raster below is *not* on the
normal-gameplay path. A person standing on the ground never needs it, so it travels with the
flight/orbit pass, and normal play needs only the near field, the world texture and the
cached layers.

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

So the *structures* half is sound by construction. The *trees* half looked like the claim to
falsify — a heightfield can never resolve a 0.3 m trunk, nor overhang a crown past it — until
the framing corrected it (user, 2026-07-22): **a tree is mostly its canopy, and a trunk is
only ever seen on a stand-alone tree or at the side of a wood.** That dissolves both
objections instead of working around them, because:

- **A closed canopy IS a height function.** The overhang a heightfield cannot express is
  *interior* to the wood, and interior is exactly what you never see from outside it. Better:
  plan #9 already stores it that way — `canopy_heights(..., top, base)` fills a per-cell
  `top` **Heights** raster, gated by `canopyvoltest`. The far field's canopy layer is not
  built, it is *read*.
- **The boundary only says WHICH TREES are exposed — it is an indicator, not geometry.** The
  traced edge of the canopy set (`trace(s: HexSet)`, plan #5) plus its isolated components
  selects the stand-alone and wood-edge trees; the partition's `Labels` map each such cell to
  its owning tree, and **that tree's trunk is then drawn from its own skeleton** — the
  position `Trees` already assigned it (which is under its crown, not at the boundary cell),
  the radius from T5's pipe model, the lean from T3. So the pass is *select, then emit what
  the tree already knows*, and the interior trees keep their skeletons unrendered. Trunks
  stay optional in the other direction too: past the range where even an edge trunk is
  sub-pixel, the selector drops it and only the canopy surface remains.

> **The trunk set must be derived from the FIELD, never from the view.** "Draw a trunk where
> you can see the silhouette" is the natural formulation and it is wrong: it makes the trunk
> set camera-dependent, so every rotation invalidates the cached layers and **I-PARALLAX
> collapses** — the exact motion that was supposed to be free becomes the most expensive.
> Deriving it from `trace()` is view-independent, so it caches. This is the one place where
> two invariants in this plan can quietly destroy each other.

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


**I-PAINT — the world's appearance is a texture derived from the same field as its
geometry.** Landcover — fields, woods, rock, snow, water, roads — is carried in a **world
texture** sampled across the terrain, not in vertex colours, so **appearance resolution is
chosen independently of triangle count**. Both are generated from the field, so a boundary
in the texture and the geometry under it cannot disagree.

*Why not the demo's way.* The Alps demo (`src/realworld/trimesh.loft`, `make viewer`) carries
landcover in **geometry**: 18 triangles per hex over 19 vertices (centre + 6 corners + 12
edge-thirds), one OSM class per triangle, watertight by construction, stride-6
`(x,h,z,r,g,b)`. That is the right instrument for its job — a per-triangle *adequacy
comparison* against ground truth (plan #1). It is the wrong one for a world, because
crispness costs subdivision and subdivision costs triangles **per unit area** — precisely
backwards at distance, where area explodes and visible detail collapses. A texture inverts
that: the mesh stays coarse, the boundary stays sharp.

*Where the content comes from — and why this is nearly free.* The shapes are already exact.
`trace(s: HexSet) -> VecMap` (plan #5) emits **exact integer boundary loops** of any
labelled region — a field, a wood, a lake — already validated and golden-gated. Rasterise
those loops into the texture with the **scanline polygon fill crawler already built and
gated** (`src/sprite_draw.loft`, `[13/14] SPRITE OK`). So the world texture is *derived, not
authored*, from the same loops the geometry uses — which is **I-AGREE at texture level**,
and is the same "derived, never authored" discipline as props, placement and tree skeletons.
(Two small truths: those rasteriser functions are currently module-private, so they need
exporting; and the vertex format moves off baked colour — `worldmesh.loft`'s R4 tint bake
into vertex colours is exactly what this replaces.)

*The honest constraint — one texture is impossible.* The overland window is 101×101 hexes of
1500 m ≈ 151 km across; at 1 m per texel that is ~23 **giga**texels. So "a texture for the
world" is necessarily **tiled with LOD** — a clipmap, resident per layer at that layer's
resolution, not one image.

> **Do not fuse the ladders.** Texture LOD and the I-PARALLAX cache layers are both distance
> ladders driven by the same angular-pixel criterion, and it is tempting to make them one
> ladder. Resist: mip levels want ~2× steps, cache layers want rungs where re-render cost
> balances. **Same criterion, rungs chosen independently** — fusing them is the elegant
> absorption this plan keeps having to refuse.

## Provides for: flight, and landing from orbit

Named as a design axis by the user (2026-07-22) — **not** to be built here, and each pass
needs its own plan. Recorded now because an axis named before a design commits is nearly
free, and named after it is a rewrite. The honest split:

**Already provided for, structurally.** The switch-distance ladder plus **I-AGREE** means
orbit is *more rungs of the same structure*, not a new mechanism. **I-PARALLAX** is a
computed threshold rather than a tuned distance, so it self-adjusts at any altitude. And
the layers earn a second payoff nobody designed them for: **they are also the depth-range
partition.** One depth buffer cannot span 0.5 m to 600 km — the standard answer is
per-range passes composited together, which is what the layers already are. `viewer.loft`
already runs a 600 km far plane, so the range itself is not speculative.

**Two constraints to honour NOW, or the axis closes.** Both cost nothing today:

1. **Vertex buffers stay chunk-local; the world offset rides the matrix.** loft `float` is
   f64 on the CPU but GL takes `single` (f32), and world-absolute f32 coordinates jitter
   visibly at planetary range. Uploading chunk-local — which P3 does anyway, per chunk —
   keeps the precision. Uploading world-absolute is the difference between *more rungs* and
   *rewriting the upload path*.
2. **`SCALE.md`'s "one grid, two readings" wants to be a ladder, not a pair.** 1.5 m and
   15 m are two rungs of a sequence that orbit extends. Check the contract generalises to N
   readings before it hardens around two.

**One genuinely open question — do not decide it here.** **Hexes cannot tile a sphere:**
Euler forces exactly **12 pentagons** on any hex-dominant closed surface. So the
exact-integer `(k,m)` lattice — this repo's most load-bearing asset, the thing that made
the tracer, the area round-trip, the rotations and the stencils exact — is inherently a
**local chart**, and a planet is an atlas of them. The resolution to *evaluate* when that
pass comes: keep the simulation on the flat chart, treat curvature as a **far-field
rendering** concern, and let the planet-as-sphere be the outermost layer, so the 12
pentagons fall where nothing is simulated. That preserves the lattice, which is the asset
worth preserving.

**And flight is a bigger simulation change than a rendering one.** The player is
`px, py, heading` — **no z, no pitch** — collision is 2D hex-and-edge, and the clock is
*distance-driven* (every `HEX_LEN` travelled = one `sim_tick`), which flying at speed would
spam. So flight needs an altitude axis, a 3D collision answer, and a travel-mode clock:
kernel work, its own plan, and a sibling of the layer axis in `plans/5-geometry/` Track 2.

