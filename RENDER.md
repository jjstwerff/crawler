# RENDER.md — the showcase-grade 2D GPU renderer

**Doctrine (2026-06-12): crawler showcases the best 2D primitives possible on a modern
GPU setup.** Not merely "optimize the immediate mode away" — the 2D renderer is a
first-class deliverable (DESIGN §7a) and the demo of what loft's `graphics` lib can do
in 2D: retained meshes, SDF shapes with analytic anti-aliasing, instanced batches,
and a post-fx chain. The same techniques transfer to the moros 3D path (instanced
foliage, SDF UI, the framebuffer chain), so none of it is 2D-only investment.

The stages split cleanly: **R4–R6 need nothing upstream** (every primitive is in the
installed `graphics` lib today); **R7–R8 are gated on small `graphics` flow-backs**
(EXTRACTION.md → "GPU 2D primitives"). HUD/overlay text stays painter-immediate —
a showcase demonstrates judgment too; immediate mode is the right tool there.

## Current state

- **World floor = a real retained mesh, live** (R1+R3): one per-level stride-10 VBO
  (pos·visUV-in-normal·color), one `gl_draw`, FOV from a tiny per-hex visibility
  texture sampled in the fragment shader (discards unseen, dims remembered).
- **Tints baked into the mesh** (R4 ✅), **walls = one capsule-SDF draw** (R5 ✅),
  **the world composites through the light-cone + vignette pass** (R6 ✅) — every
  world pixel is GPU-computed; details per stage below.
- **Still immediate, queued:** mobs/items/glyphs (`draw_texture_at` / the
  hand-rolled `draw_texture_rot` per entity → R8, gated on the P5 substrate).
- **Deliberately immediate, stays:** sidebar/HUD/overlay pages (bars, labels, text).

## The primitives (what `graphics` has / lacks)

Present and proven in crawler: `gl_upload_vertices(data, stride) -> vao` (persistent
VBO), `gl_draw` / `gl_draw_mode` / `gl_draw_elements`, `gl_create_shader` + mat4/vec3/
int/float uniforms, `gl_load_texture` / `gl_upload_canvas` / `gl_bind_texture`,
`SpriteSheet` + `draw_sprite_at`, framebuffers (`gl_create_framebuffer`,
`gl_framebuffer_texture`, `gl_draw_fullscreen_quad`).

Missing for the instanced tier (the EXTRACTION.md flow-backs; crawler is the consumer
pressure that drives the lib's 2D API):

| Gap | Unlocks |
|---|---|
| `gl_draw_instanced` + per-instance attributes (divisor) | R7 instanced floor, R8 one-call sprite batch |
| `gl_update_vertices` (buffer sub-data / orphaning) | per-frame dynamic buffers without create+delete |
| `gl_set_uniform_vec2` / `gl_set_uniform_vec4` | SDF params, tint uniforms |
| an EBO upload entry (`gl_draw_elements` exists, no index upload) | indexed meshes, smaller buffers |
| texture sampler control on upload (linear/nearest, mipmaps) | RGBA-quality sprite minification, atlas filtering |
| texture sub-region upload (`glTexSubImage2D`-style) | incremental auto-atlas packing without full re-upload |
| `gl_scissor(x, y, w, h)` | partial in-layer damage redraw (frame-reuse Tier 3) |
| `gl_wait_events_timeout(ms)` (blocking event poll) | the idle skip's CPU half — without swap nothing vsync-blocks, idle spins ~1k Hz |

(Premultiplied-alpha compositing needs no gap — `BLEND_ONE` +
`BLEND_ONE_MINUS_SRC_ALPHA` already exist; premultiplication happens at atlas-bake
time.)

Note `gl_line_width` is NOT the wall answer — core-profile GL caps line width at 1px on
modern drivers; wide anti-aliased strokes are an SDF fragment-shader job (R5).

## FOV on the GPU

The **kernel** (`sim_compute_fov` + `sim_hex_state`) computes the visibility *set* —
**renderer-agnostic**. The GPU renderer consumes it as a per-hex visibility texture
(R = brightness, refreshed per frame, sampled by the visUV baked into each vertex's
normal slot); the fragment shader **dims** remembered hexes and **discards** unseen
ones. The kernel stays the visibility authority; shaders only present it.

**Directed light.** Sight is *directional*: full `VISION_RADIUS` straight ahead,
falling off (forward-biased) to `NEAR_RADIUS` behind — a forward-pointed lamp. So
**turning aims your light** (a real tactical choice, extra reason to turn). Later the
radius comes from the equipped light item; the soft light-cone gradient + coloured/
animated falloff is the R6 post-fx job — the kernel just yields the boolean
visible/seen set.

## Staged plan

**Step plan with per-step verification channels: PLAN-RENDER.md** (P0 probe harness →
P1 idle skip → R4→R6 → lib flow-back → R7/R8 → frame-stats → R9).

### Done

- **R1 — World mesh.** ✅ **LIVE in `view_draw`**: the terrain draws from the per-level
  VBO + FOV texture (one `gl_draw`); `story.loft` builds the shader once and the VBO per
  level (freed + rebuilt on descend/respawn), the vis-texture created+freed each frame.
  Proven first in `src/gpushot.loft` (render → `gl_screenshot` → read PNG). **Stride-10
  vertex layout** (pos=loc0, visUV-in-normal=loc1, color=loc2 — the native
  `gl_upload_vertices` convention).
- **R2 — Sprite atlas.** ✅ **Pipeline proven** (`src/gpuatlas.loft`): `canvas` +
  `draw_text` per cell → `create_sprite_sheet` → `draw_sprite_at(sheet, …, index)` —
  all 16 token glyphs from ONE atlas texture. The live wiring is **subsumed by R8**
  (the instanced batch draws by atlas index; don't wire the per-call path first).
- **R3 — Shader FOV.** ✅ **LIVE** (with R1): per-hex visibility texture sampled in the
  fragment shader — discards unseen, dims remembered; only the small texture updates
  per frame.

### Showcase tier A — no lib changes, do now (in this order)

- **R4 — Tint bake. ✅ SHIPPED (P2, 2026-06-12).** The mesh builder moved KERNEL-side
  (`worldmesh.loft` — no graphics import, per the architecture invariant) with
  `mix(floor_rgb, kind_tint_rgb, tint_a)` pre-composed into vertex colors; the
  per-frame wash loop (lw×lh iterations, an axis-aligned square over a hexagonal
  cell) is deleted. Remembered dimming folds into the R3 vis multiply — uniform over
  floor and tint (probed at exactly ×0.451). Verified: meshtest (headless exact
  colors vs hardcoded oracles) + worldprobe/world_r4.probe (grass/remembered/road/
  untinted-wall, all dmax=0 through the real pipeline).
- **R5 — SDF wall strokes. ✅ SHIPPED (P3, 2026-06-12).** Blueprint-first
  (`tools/blueprints/wall_sdf.py` — the shader's exact coverage formula plotted in
  Python: interior pure, ~1px AA ramps, joins continuous with ZERO gap pixels; the
  per-segment fringe over-blend at joins was measured at 14/255 and consciously
  re-pinned as a one-sided invariant — never below ideal coverage, overshoot ≤21
  toward the wall color, the benign direction every NanoVG-class stroke renderer
  shares). `worldmesh::build_wall_mesh` emits self-describing expanded quads
  (loc1 = capsule-local u/v/len, loc2 = visUV/halfw/aa — no per-wall uniforms);
  the view's capsule shader draws ALL segments in one call with the floor's camera
  + vis texture (remembered strokes dim at exactly ×0.451, probed). The
  13-squares-per-segment stipple and `draw_segment` are DELETED, and the
  per-segment `sim_hex_state_at` CPU check moved to the GPU. Verified: meshtest
  (exact corners/locals/visUV) + world_r5.probe (interior dmax=0, remembered
  stroke, monotonic edge ramp).
- **R6 — Post-fx chain. ✅ SHIPPED (P4, 2026-06-12).** The world layers render into
  an offscreen FBO; one fullscreen pass composites them through the **directed
  light cone** (fixed in screen space — the egocentric view keeps facing up, so no
  heading uniform: radius 520px ahead, 240 behind, floor 0.35) + a gentle vignette;
  the HUD draws after, unlit. The kernel FOV stays authoritative (vis texture
  discards/dims first; the cone only softens). Constants live in the shader AND in
  `tools/blueprints/light_cone.py`, which generates the probe expectations —
  retune there first. Verified: post_r6.probe on a uniform gray scene (anchor 127,
  ahead150 117 > behind150 73, corner 38, monotonic ahead ray — all dmax=0).
  Optional later: coloured/animated light.

After R4–R6, every world-layer pixel is GPU-computed; the painter draws only HUD.

### Showcase tier B — gated on the `graphics` flow-backs (EXTRACTION.md)

- **R7 — Instanced floor.** Upload ONE 18-vert hexagon; per-instance records
  (center, color, visUV) drawn with a single instanced call. Replaces the fat VBO that
  duplicates the hexagon lw×lh times (~1.8M floats on overland → 18 verts + ~10k small
  records). The canonical modern-GPU 2D technique, and the floor is its cleanest demo.
- **R8 — Instanced sprite batch.** ONE quad + a per-frame instance buffer of
  (pos, rotation, scale, atlas-index, tint): every mob, item, glyph, and stair marker
  on screen in **one draw call**. Absorbs R2's live wiring AND `draw_texture_rot`
  (which today reaches into `Painter2D` internals to build a rotated MVP per sprite —
  per-sprite uniform+draw, 6 verts each). Atlas-building reuses the proven R2 pipeline;
  PNG sprites pack into the atlas beside the glyph cells. Needs `gl_draw_instanced` +
  `gl_update_vertices`.
- **R9 — Frame reuse (idle skip + layer caches).** See "Frame reuse" below. The idle
  skip (Tier 0) has no lib gaps and can land any time — even before R4. The layer
  caches (Tier 2: HUD first, world-space world layer profile-gated) use the existing
  framebuffer entry points; partial in-layer damage redraw (Tier 3) waits on the
  `gl_scissor` flow-back.

### Out of scope

- **HUD/overlays** stay painter-immediate (bars, labels, inventory/char/crystal pages).
- **3D/moros** — separate track; this doc's techniques are its groundwork, not its plan.

## The API layer — a Cairo-class canvas + sprites, GPU behind the curtain

**The target (stated 2026-06-12): Cairo-like drawing primitives, plus 2D sprites with
full RGBA-quality compositing — and behind the curtain the GPU used as efficiently as
possible.** The proven architecture for exactly this is the **NanoVG class** (a
Cairo/HTML5-canvas-style context API rendered on the GPU) — Vello/Skia are the
heavyweight versions; NanoVG is the right scale for loft. A programmer writes Cairo's
mental model in pixel space and never meets a VAO, shader, or instance buffer.

**The surface:**
- Stateful context: `save`/`restore` (transform + state stack), `translate`/`rotate`/
  `scale`, scissor/clip, global alpha.
- Paths: `begin_path` · `move_to`/`line_to`/`bezier_to`/`arc`/`rect`/`rounded_rect`/
  `circle` · `close_path`, then `fill(paint)` / `stroke(paint, width)` — paints are
  solid RGBA or linear/radial gradients. Strokes carry the Cairo trio of styles —
  **join** (miter/bevel/round) and **cap** (butt/round/square) — plus **per-point
  width** (taper) and **arc-length UV** baked into the stroke geometry (see the world
  fit-check below: constructed 24-dir walls demand sharp miters, rivers demand taper,
  roads/flow-animation demand distance-along-path UV — all cheap at build time,
  painful to retrofit).
- **Sprites first-class:** `img = load_image(path)` → `draw_sprite(img, x, y)` +
  rotated/scaled/RGBA-tinted variants — full alpha compositing, not cutouts. The word
  "atlas" never appears in the API (see backend point 4).
- Text rides the existing font/glyph path.

**Behind the curtain (the efficiency contract):**

1. **Accumulate, merge adjacent, flush — NEVER reorder.** 2D correctness is painter's
   algebra: overlapping translucent draws must composite in call order, so the batcher
   merges *consecutive* state-compatible calls and breaks the batch on a state change
   — it does not sort (sorting would visibly corrupt alpha compositing). This is
   sufficient because points 2 and 4 make almost every call compatible: one SDF
   ubershader + one shared atlas means nearly all consecutive calls merge, and a frame
   of Cairo-style calls still becomes a handful of GPU draws. None of Cairo's per-call
   CPU rasterization.
2. **Two-tier shapes.** The common cases (line, circle, ring, rect, rounded rect) are
   **SDF fast paths** — one quad shader, per-instance params, real stroke width, round
   caps/joins, analytic AA at any zoom; they never tessellate. **Arbitrary paths**
   flatten + tessellate on the CPU **once and are cached** (keyed by path identity +
   scale bucket — most paths are static frame-to-frame), then redraw as cached
   triangles. This sidesteps GTK's hardest problem (per-frame GPU path rendering) by
   caching instead of solving it.
3. **RGBA quality = premultiplied alpha.** The load-bearing sprite detail: straight-
   alpha blending dark-fringes rotated/scaled sprite edges. Sprites live in a
   **premultiplied-alpha atlas**, composite with `(ONE, ONE_MINUS_SRC_ALPHA)`, get 1px
   atlas padding (no linear-filter bleed) and mipmaps when minified. That's what makes
   a sprite composite correctly at any rotation/scale.
4. **The sprite atlas builds itself (stated 2026-06-12: no programmer direction).**
   The painter owns atlas pages (~2048²); each image is **skyline/shelf-packed** into
   a page **at `load_image` time** (the natural off-frame point — packing on first
   *draw* would hitch the hot frame; first-draw packing remains only as the fallback
   for dynamic content like glyphs) — premultiplied, padded, extruded at insert (the
   point-3 rules applied automatically). Instance records carry the UV rect, so every
   sprite on a page draws in ONE call without anyone arranging it; glyphs share the
   same pages, so text batches with sprites. Heuristics replace direction: oversized
   images (> ~¼ page) bypass to their own texture; a full page opens the next
   (batches split per page); glyph-style dynamic entries get LRU eviction. Needs the
   texture sub-region upload gap (incremental packing without full re-upload). For
   crawler this keeps the by-name sprite workflow ("drop the PNG in") and upgrades it
   to a one-draw batch for free.
5. **Static content = the same verbs, recorded.** A display-list model: record the
   verbs once into a batch handle, replay per frame under an MVP
   (`record … → draw_batch(batch, mvp)`). A level's walls record once at build time
   and redraw in one call with the camera matrix — static-geometry performance without
   teaching anyone a second API.
6. **Introspection — automatic must stay debuggable.** The price of "behind the
   curtain" is that when the magic degrades (a full atlas page silently splitting
   batches, a scale-animated path re-tessellating every frame, a layer invalidating
   per frame), the programmer sees slowness with no handle. One frame-stats call
   answers it: draw count, batch breaks **with the reason for each**, atlas-page
   occupancy, tessellation-cache hit rate. That keeps the no-burden promise honest
   under failure, not just on the happy path.

Power stays opt-in by layer, each an escape hatch below the last: **the canvas** (most
game code, HUD) → **mesh/VBO + own shader** (crawler's floor; custom vertex layouts
like stride-10 visUV) → **raw `gl_*`** (post-fx framebuffers). Nothing about the simple
layer blocks dropping down — and no escape hatch points at CPU rasterization.

## Fit check — the 24-direction world (evaluated 2026-06-12)

How the stack maps onto the world's feature classes (WALLS.md, OVERLAND.md,
loft-libs-world/CONVERGENCE.md), one shader family + the filled-path tier:

- **Carved dungeon walls** (wallgeo outlines): R5 round-join capsule strokes — the
  organic paradigm, as staged.
- **Constructed 24-dir walls** (WALLS.md bands — castles, houses): "straight + SHARP"
  → `stroke(width=thickness, join=miter, cap=butt)` over the centerline, or the
  mitered band polygon through the cached-tessellation fill tier. The triangle band
  stays KERNEL-side as collision truth; the painter renders only the derived face
  lines (a door = a gap = two sub-strokes). The capsule default alone would round
  every castle corner — this is why strokes carry join/cap styles.
- **Roads**: constant-width strokes on the 24-dir set; crisp (miter/butt) or soft
  (round) per road kind; dashes/ruts/banking ride the arc-length UV.
- **Rivers/waterlines**: curved courses with flow-scaled width = **per-point-width**
  capsule chains (round-cone SDF); flow animation = a texture scrolled along the
  arc-length UV (R6). Shorelines are region BOUNDARIES — `wallgeo` is really
  "smoothed outline extraction from hex regions" (not wall-specific); its Tier-2
  extraction should generalize it to coastlines/forest edges. Lake/sea interiors stay
  R4 hex-tint at world zoom.
- **Maps**: the layer-cache case par excellence — render the known world's vector
  content once into an FBO layer, pan/zoom as one quad, exploration overlay via the
  vis-texture mechanism; SDF content keeps the map **crisp at every zoom** (the
  analytic-AA payoff a baked bitmap can't give).
- **Towers**: round towers = SDF rings/discs — same shader family, so a wall band
  meeting a tower unions seamlessly in one batch (painter-order overdraw); oriented
  structures (gatehouses) are rotated instances. Per-instance rotation is continuous,
  so the 24-dir quantization is world-model policy — the renderer never quantizes,
  and 15° steps cost nothing (no pre-rotated frames).

## Frame reuse — render only what changed

**The goal (stated 2026-06-12): reuse as much of the previous frame's drawing as
possible in the next.** First the constraint that shapes everything: **after a buffer
swap, core GL leaves the backbuffer undefined** — "keep drawing over last frame" is
not a thing. Reuse means OWNING the pixels: render into FBO textures you keep, and
composite them to the window each frame. Four tiers, by what gets reused:

- **Tier 0 — idle skip (reuse: everything; the biggest win). ✅ SHIPPED (P1,
  2026-06-12):** `framekey.loft` digests every frame-relevant observable (Sim +
  overlay scalars — the ONE chokepoint for stale-frame bugs); the loop redraws only
  on a key change. Measured under Xvfb: 6s idle = **1 frame drawn**. Idle GPU
  cost = zero — and since K1 (PLAN-KERNEL) the kernel loop idles between
  drift-free ticks, so the old busy-spin gap is CLOSED: idle CPU = 60 Hz ticks
  at ~150 µs each plus kernel sleeps. Render-on-demand + vsync-on-draw is also
  exactly the cadence VRR/adaptive-sync displays want (PLAN-KERNEL § Frame
  rates).
- **Tier 1 — retained encoding (reuse: all CPU-side work; this IS R1–R8).** Resident
  VBOs, recorded batches, cached tessellation: per frame the GPU re-executes a handful
  of draws, the CPU re-builds nothing. `gl_update_vertices` refines it — a
  mostly-unchanged instance buffer updates only the records that moved (gridmesh's
  dirty-region model applied to draw data).
- **Tier 2 — layer caches (reuse: rasterized pixels), split by change frequency.**
  - *HUD layer*: changes only on HP/message/inventory events — render to an FBO
    texture, redraw on a dirty flag, composite as one quad.
  - *World layer*: the camera moves every frame but the CONTENT doesn't — render
    floor+tints(+walls) once into a **world-space** texture; per frame draw that one
    quad under the camera mat4. The R3 split is what makes this valid: **FOV lives in
    the separate vis texture applied at composite time, so movement never invalidates
    the cached world layer** — it invalidates only on level change / terrain edits.
  - *Sprite layer*: genuinely dynamic — stays live (one instanced draw after R8;
    caching it would cost more than it saves).
- **Tier 3 — partial redraw inside a cached layer.** Scissored damage-rect redraw
  (only the HP-bar region of the HUD texture re-renders). Needs `gl_scissor` (gap).

**The honest dial — cached pixels vs analytic crispness:** sampling a world-space
texture under a rotating camera trades the SDF strokes' analytic AA for texture
filtering (softness; shimmer under magnification). Mitigations: render the cache at
~2×, re-render on zoom change, or keep the wall-stroke layer live (one draw) and cache
only floor+tints. Because the trade-off is real, **caching is a per-layer choice in
the painter API, never a global mode**: the canvas grows
`layer = make_layer(w, h)` / draw-into-layer / `invalidate(layer)` /
`draw_layer(layer, mvp)` — the same verbs, targeted at an owned texture.

**Worth-it order:** Tier 0 now (largest win, zero cost); Tier 1 is the existing plan;
Tier 2 HUD when the HUD grows; Tier 2 world-layer only when profiling says so (after
R4–R8 a full redraw is already ~5 resident draws — the world cache buys scaling
headroom and battery, not frame rate); Tier 3 last. This also refines the GTK
divergence note above: damage tracking DOES return — at *layer* granularity, where
content is axis-aligned and mostly static, never at node granularity.

crawler's role: prove each piece here first, then flow it back — R5's capsule shader
becomes the lib's stroke shader, R8's sprite batch becomes the painter's internal
batcher, `draw_texture_rot` dissolves into the rotated-sprite verb.

**Prior art (GNOME's three attempts at this exact tension):** *Cairo* = the verb
ergonomics to imitate (user-space coords, transform save/restore, productive in
minutes) but all-CPU — simple verbs without the power, the half we already have.
*Clutter/Cogl* = the overcorrection — a retained GPU scene graph as the USER-facing
model; the simple case got harder and it never displaced Cairo. *GSK/GtkSnapshot*
(GTK4, the 4.14+ unified GPU renderer) = the synthesis that validates this design:
simple snapshot verbs RECORD typed render nodes, the renderer batches them with
glyph/texture atlases and evaluates rounded rects/borders/shadows analytically in
fragment shaders — verbs-as-surface + shader-backed shapes + recording, independently
converged. Two deliberate divergences for a game renderer: (1) no node TREE — GTK
diffs mostly-static UI for damage regions; a rotating-camera roguelike redraws the
full viewport every frame, so flat instance buffers win and per-node tree-building
overhead buys nothing; (2) no silent CPU fallback — GTK4's `append_cairo` escape
hatch quietly drops a subtree to CPU raster + re-upload (a notorious perf trap); our
escape hatches point DOWN the GPU stack (mesh/VBO → raw `gl_*`), and `Canvas` stays
an authoring tool (atlas/glyph bakes), never a runtime fallback.

## The moros bridge

The retained `Vertex`/`Triangle` model *is* `moros_render`'s (`emit_hex_surface`,
`emit_wall_quad`) — a 2D world mesh is the same architecture, a 2D projection. R5's
wall quads, R7's instancing, and R6's framebuffer chain all carry over. Library
vocabulary note: `mesh3d`'s `Vertex` is pos+normal+uv (stride 6/8 flatteners) — no
color channel, which crawler's stride-10 layout needs. Keep the local emit helpers for
now; a color-carrying `mesh_to_floats` variant is a candidate `mesh3d` flow-back when
the wall mesh lands (EXTRACTION.md).

### 2.5D — the intermediate tier (evaluated 2026-06-12)

The stack serves height-aware top-down/oblique worlds (terrain relief, wall faces,
depth-sorted objects) largely AS-IS — 2.5D is a waypoint on the same data path, not
a fork:

- **The z slot exists**: stride-10 is `pos.xyz` (z=0 today); a 2.5D camera is the
  same mat4 plus a shear term (screen-y ∝ height); terrain relief = per-vertex z
  from `hex_terrain` through the existing floor path.
- **The order-preserving batcher IS 2.5D compositing**: painter's algorithm
  back-to-front — emit in y-sorted order (near-free on a hex grid) and the
  "never reorder" doctrine does the rest. The 2D-correctness decision doubles as
  the 2.5D enabler.
- **The extrusion data is the face data**: the classic 2.5D wall = top face +
  darker vertical band offset downward — exactly the WALLS.md outer face polyline
  + height, rendered as flat quads under the shear camera (no mesh3d needed yet);
  cliffs via the generalized region-outline machinery.
- **Layers with per-layer MVPs = parallax planes**; instanced billboards with a
  height→y-offset are the standard 2.5D object model unchanged.
- **Spec delta**: per-instance **2×3 affine** (instead of pos/rot/scale) — skew
  shadows are a sheared dark re-emission of the same atlas entry; blob shadows are
  free SDF ellipses.
- **Honest cost**: y-sorted emission interleaves materials → more batch breaks than
  layer-grouped 2D; the shared atlas + ubershader mitigate, frame-stats (P8)
  measures it. Translucency-vs-depth resolves the standard way: world objects =
  opaque + alpha-test, true alpha stays in overlays.

### Extrusion — the 2D base lines become the 3D constructions (evaluated 2026-06-12)

**What extrudes is the KERNEL geometry (bands, centerlines, footprints) — never the
2D render.** SDF strokes are a fragment trick on flat quads; the extruder consumes the
same renderer-agnostic data the painter consumes (`wallgeo` segments, WALLS.md band
polygons, tower footprint circles) — the kernel/view seam is what lets the 3D path
plug in BESIDE the 2D painter. Per element:

- **Side faces**: the WALLS.md band already carries explicit inner/outer face lines
  (centerline ± half-thickness, 24-dir miters) — face polyline × height = the wall's
  vertical strips, no new derivation. The finite 24-dir normal set gives crisp,
  coherent lighting.
- **Top (flat)**: the 2D stroke tessellation (quad strip + miter wedges) lifted to
  `z = wall_top` IS the cap / wall-walk mesh — per-segment, no polygon-with-holes
  triangulation needed. The canvas tessellator doubles as the cross-section generator.
- **Bottom (non-flat terrain — the one genuinely new problem)**: densify the base
  polyline by arc length, sample `hex_terrain` per-point height per vertex, and sink
  a **skirt/plinth** below the surface — robust against base-vs-terrain tessellation
  mismatch (exact edge-conformity is precision work for no visible gain; a sunk
  plinth is also how real walls meet ground). Roads/rivers are the inverse: they
  DRAPE (conform along arc length; riverbeds inset down).
- **Roofs**: flat caps free; gable/hip = straight skeleton, which the 24-dir set
  collapses to a finite corner-configuration table — ridge roofs on rectangular
  footprints first, the skeleton later.
- **Towers ("pointed circle")**: footprint circle → cylinder shell + cone to the
  apex (`mesh3d` needs trivial `cylinder`/`cone` builders beside `sphere`).
  Battlements are PERIODIC IN ARC LENGTH — the same parameterization serving 2D
  dashes and river flow indexes the merlons.
- **Doors/gates**: the extruder takes **per-segment z-intervals** (not one global
  height) — a doorway = full-height + gap + lintel segments. Design it in now.

New work, all kernel/lib-side: the extrusion operator (band + z-intervals → `Mesh`;
gridmesh/hex_walls territory), the terrain skirt, `cylinder`/`cone`, the
(24-dir-simplified) roof skeleton — deferred until the 3D track opens, but the 2D
stroke geometry should keep arc-length UV + per-segment decomposition because the
extruder consumes exactly those.

The **3D pipeline uses the `glb` lib** — unused while we're 2D, but **load-bearing the
moment 3D is enabled**. It builds cleanly — forward-insurance so the moros 3D bridge
won't hit a silent native-build failure when we turn it on.
