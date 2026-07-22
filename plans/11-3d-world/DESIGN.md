# Plan 11 — the design: seven invariants and what they cost

> The **plan** (status, phases, order, risks) is [`README.md`](README.md). This file holds
> the design it executes: the invariants, the arithmetic that fixes their reach, and the
> long-horizon axis the design must not foreclose. Split out when the README passed its
> line budget — reference content belongs beside the plan, not inside it.

## The invariants

Seven, because this plan has seven distinct exact-invariant surfaces — the seam, the camera,
the two-scale world, and the four that make the far field cheap, continuous and paintable.
Each phase in [`README.md`](README.md) names which one it asserts. They are listed in
dependency order: a later one is worthless if an earlier one is false.

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

