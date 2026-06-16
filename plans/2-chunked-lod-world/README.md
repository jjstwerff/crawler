# @PLN2 — Chunked LOD world + loft WebGL viewer

**Status:** active (S0–S5 done — full LOD viewer; aesthetic sign-off + S6 left) · **Issue:** [jjstwerff/crawler#2](https://github.com/jjstwerff/crawler/issues/2) · **Branch:** combat · **Follows:** @PLN1

## Context

@PLN1 concluded the terrain investigation: the 14 kinds suffice, the real-metre transition
defaults are derived (`../1-ortler-worldgen-fixture/tuned-defaults.md`), and the loft engine is
being moved to those defaults. It also showed the open frontier is **sub-hex detail** — cliffs,
real stream channels, sharp rock/scree — which 1.5 km can't resolve and which need a
**level-of-detail** structure. This plan builds that: a **chunked LOD world** fed by real
terrain, with a **loft-scripted WebGL viewer** to inspect real ranges (the dual view).

## Why loft now (handoff from @PLN1)

@PLN1's python prototype hit its ceiling: its spatial-agreement metric (κ=+0.45) showed the
elevation-driven types place well (rock 71%, forest 77%) but the rest place poorly (field 23%,
grass 30%, glacier-tongues 44%) — because the simplified model has **no town/river/field
system**. The **loft engine already has it** (`overland.loft`: `ov_towns`/`ov_roads`, `ov_sides`
with `os_acc`+`os_w` = sized rivers, farmers'-rule `K_FIELD` near towns, confluence swamps), so
the chunked world builds on the rich engine instead of re-deriving those in python.

**Validation in loft:** primary = *statistical* (synthetic worlds look alpine + the
town/river/field systems work) — the right target for a generator; the @PLN1 defaults are
already validated against real data. Optional = carry the per-triangle **spatial-κ** by feeding
real heights (`overland_from_seed`) if we want to keep diffing against the real Ortler.

## Goal

- **32×32 chunks**, two tiers: an **overworld map** (coarse, 1.5 km hexes) and a **detailed
  map** (fine), zoomable from a whole range down to cliffs/channels.
- **Detail chunks** = a **base height (the chunk's lowest point)** + per-cell **0.1 m relative
  offsets** (`u16`), compact + precise.
- **WebGL viewer in loft scripts**: **WASD** move, **QE** zoom (= descend the LOD), the **same
  dual view** (real vs our model). Renderer *follows the chunk data* (@PLN1 architecture rule).

## Building blocks — chunks already exist in the libraries (reuse), one piece is new

The chunking-landscape survey (file:line) found 32×32 chunks are **not net-new**:

- **`loft-libs-world/hex_world.loft`** — the **32×32 chunk pattern verbatim**: `Chunk{ck_cx,
  ck_cz, ck_cells: vector<Cell>}` (1024 cells), addressing `chunk_idx_32(v)=floor(v/32)` /
  `hex_idx_32(v)=v mod 32`, sparse storage + GC of empty chunks, `Cell{c_color:u8, c_height:u8,
  c_age:u16}`. **Drop-in** for the chunk grid + addressing.
- **moros `wall.loft`** — 32×32 chunks with **height + multi-layer** precedent: `Layer{x,y
  (mult of 32), layer:u8, tiles}`, `Tile{material:u8, …, height:u16}`. The **u16-height + tier**
  reference.
- **`gridmesh`** (loft-libs-graphics) — the **chunked batched-mesh pipeline** the audience demo
  scaled with: `SegMesh` (narrowed `u8`/`single` buffers), `build_index`/`idx_at` spatial index,
  `seg_mesh_append`, `group_vbos_upsert` (one VBO per render-group), + audience_crystal's
  `CrystalIncr` dirty-rebuild engine. **Adopt wholesale for the terrain mesh** (see Mesh build).
- **`hex_terrain.loft`** — seamless kernel-blend overland sampling (float m, `tr_h`/`tr_mat`/
  `tr_flow`/`tr_acc`): **reuse to fill chunk cells** deterministically.
- **crawler `sim.loft` windows** — `win_x`/`win_y`, stateless regenerate-on-revisit (`sim_travel`):
  the **deterministic-per-coordinate** model the chunk gen copies.

**NEW (found nowhere):** the **base-height + 0.1 m relative-offset** detail encoding, the
**two-tier overworld↔detail LOD mapping**, **deterministic per-chunk** generation, and the
**loft WebGL viewer**.

## Design protocol — exact invariants (pin before building)

- **I-SEAM — chunk borders are watertight.** A cell/vertex shared by adjacent chunks resolves to
  **one** absolute height regardless of which chunk computes it (the @PLN1 I-MESH extended across
  chunk borders). With base+offset this is the load-bearing claim: `baseA + offA·0.1 ==
  baseB + offB·0.1` at the shared border — so the **absolute height is the single source**, bases
  are per-chunk bookkeeping. *Cure:* derive every height from world position (or share the border
  row), and a round-trip assert at the seam.
- **I-HEIGHT — base+offset round-trip is exact.** `absolute_m = base_h + offset·0.1`, and
  `quantize(absolute) → (base, offset) → dequantize` reproduces it to 0.1 m. base = chunk min;
  offset = `round((h − base)·10)` ∈ `u16` (covers base+6553.5 m — far past any chunk's relief).
- **I-DET — deterministic per-chunk generation.** `gen_chunk(seed, tier, cx, cz)` reproduces a
  chunk's cells identically from the seed alone (stateless, like crawler windows) — no global
  order dependence; neighbouring chunks agree on shared data by construction.
- **I-LOD — tiers are consistent.** A detail chunk **aggregates to its overworld parent** (the
  parent hex's height/kind = a defined reduction of its detail cells), so QE-zoom is seamless —
  no pop between levels.

## Concrete hierarchy (pin in P0 — propose)

A **chunk = 32×32 cells** (library pattern). Two 32× LOD steps span the @PLN1 1.5 km → 1.5 m range:

| Tier | cell size | chunk span | source |
|------|-----------|------------|--------|
| **overworld** | 1.5 km hex (`OV_TILE`) | 32 hexes ≈ **48 km** | the overland sampler (coarse), real-metre defaults |
| **detail** | ≈ **1.5 m** (1.5 km / 32 / 32) | 32 cells ≈ **47 m** | finer sampling + the real DEM seed (@PLN1) |

So **one overworld hex ↔ 32×32 detail chunks ↔ 32×32 cells each** = 1024× (1.5 km → 1.5 m). The
exact ratios + the seam construction are P0's plotted concrete instance (cheapest medium first).

## Mesh build — reuse `gridmesh` (the audience-demo optimization)

The audience demo proved a chunked batched-mesh pipeline that stays **O(dirty), flat per
segment to 100s of cells** (its `crystal_stress` asserts "us/seg not flat" fails if it isn't).
`gridmesh` *is* that pipeline — adopt it instead of building meshes per cell/frame:

- **Per-chunk cached `SegMesh`, rebuilt only when dirty.** A `ChunkField` tracks a dirty set;
  `collect_dirty_inputs` returns **O(dirty)** chunks; unchanged chunks keep their cached mesh.
  Editing/streaming a cell touches its chunk + halo (≤9), never the whole world.
- **One VBO per render-group; re-upload only dirty groups** (`group_vbos_upsert`). The demo's
  group = 2×2 of 16×16 chunks = 32×32 cells per VBO — i.e. **our 32×32 chunk == one VBO group**;
  use 16×16 sub-chunks for dirty granularity. **One draw call per group**, not per cell/chunk.
- **Group assembly = concat of cached chunk meshes** (`seg_mesh_append`) — no recompute.
- **Narrowed buffers** — `SegMesh` uses `u8`/`single` (f32), ~2× denser than i64/f64 → smaller
  uploads, better cache. Fits our base+0.1 m `u16` offsets (compact by design).
- **Spatial index once per rebuild** — `build_index`/`idx_at`: O(N) build, O(1) neighbour reads
  (not O(N²) rescans). Our chunk-fill neighbour reads (slope, flow, **seam**) use it.
- **Build-once + GPU-side animation** — vertices carry an anchor + state; the shader animates
  (the demo blooms each cell from its centre by age) → **zero per-frame CPU rebuild**. For us:
  bake the chunk mesh once; LOD/QE-zoom morphs and any water/grass motion ride the shader.

Net: terrain edits + LOD streaming cost **O(dirty chunks)**, render is **one draw per 32×32
group** — the renderer-follows-data rule with the demo's proven scaling.

## Verifiable build steps (each gated — Build / Check / Gate; don't pass until green)

Data steps verify headlessly in `make test` (a `*test.loft` per step); the viewer verifies by
**headless golden image** (`gl_screenshot` + Mesa llvmpipe, or headless-Chrome for WebGL — the
loft `crystal_editor_gold`/brick-buster method; PLAN-RENDER channels 2/6). Renderer-follows-data
throughout: every step produces/consumes chunk DATA; the renderer never enriches.

**S0 — chunk encoding (base + 0.1 m). ✓ DONE.**
*Build:* `src/chunk.loft` `DetailChunk` + `chunk_build`/`chunk_height`/`chunk_quant`/`dk_cell_idx`.
*Check/Gate:* `chunktest` → I-HEIGHT round-trip ≤0.05 m, base = lowest point, u16 fit, **I-SEAM
d=0** (integer-metre bases ⇒ globally-aligned 0.1 m grid ⇒ watertight), 32×32 addressing.
**CHUNK OK in `make test`.**

**S1 — tier hierarchy + coordinate mapping. ✓ DONE.**
*Build:* the two-tier map in `chunk.loft`: `overworld_center`/`overworld_hex_of` (reuse
`hex_grid` odd-r × `OV_SCALE`=OV_TILE/HEX_LEN → metres, the I-GEO single source);
`detail_chunk_of`/`detail_local_of`/`detail_cell_center` (global square raster, `DETAIL_CHUNK_M`
46.875 m, `DETAIL_CELL_M` 1.465 m); `overworld_detail_range`.
*Result:* `chunkgeotest` → tier sizes correct, overworld hex round-trip exact (odd-r parity),
detail-cell round-trip exact, one overworld hex spans **33×37 detail chunks** (~32 across).
**CHUNKGEO OK in `make test`.**

**S2 — overworld chunk generation from the loft engine. ✓ DONE.**
*Build:* `src/chunkgen.loft` `overworld_chunk(ov, cx, cz)` — fills a 32×32 chunk; per cell (=
overworld hex `cx*32+hx, cz*32+hz`) height+kind from `ov_sample` at the hex centre
(towns/roads/sized-rivers/fields free from the engine). `chunk.loft` gained `dk_kind` + a kinds
arg to `chunk_build`. Pure function of `(overland, cx, cz)`.
*Result:* `chunkgentest` → **faithful** (each cell == `ov_sample`, height ≤0.05 m + kind exact)
and **deterministic** (regen identical). **CHUNKGEN OK in `make test`.** (I-DET ✓.)

**S3 — detail chunk generation (the LOD tier). ✓ DONE.**
*Build:* `chunkgen.loft` `detail_chunk(ov, dcx, dcz)` — samples the SAME engine at the ≈1.5 m
detail-cell positions (`ov_sample`'s fbm gives sub-hex detail); base+0.1 m encode. (Real-DEM
detail later via `overland_from_seed`.)
*Result:* `detailtest` (over the mountain hex (5,3), chunk base 2889 m) → **I-HEIGHT** round-trip
≤0.05 m, **I-DET** identical, **I-SEAM d=0** (watertight across the two chunks' bases), **I-LOD
diff = 1.54 m** (detail surface passes through the overworld hex centre — same field, no pop).
**DETAIL OK in `make test`.**

**S4 — chunk → heightfield mesh. ✓ DONE (mesh data; gridmesh batching → S5).**
*Build:* `src/chunkmesh.loft` `chunk_mesh(ch, ch_e, ch_s, ch_se)` — a 33×33 vertex heightfield
(stride 6: x, height, z, r,g,b), the chunk's 32×32 cells + a **shared right/bottom edge from the
E/S/SE neighbours** so adjacent meshes share boundary vertices exactly. Colour from kind.
(`gridmesh` has only a *segment* mesh, not a surface, so the triangle buffer is ours; gridmesh's
`ChunkField`/group-VBO/dirty machinery is adopted at S5 where GL is involved.)
*Result:* `meshchunktest` → count 6534 (33×33×6), mesh **follows data** (vertex == chunk_height),
**watertight** (right edge == east neighbour's cell-0 column), deterministic, 2048 tris.
**MESHCHUNK OK in `make test`.**

**S5 — the loft viewer (dual view, WASD/QE). ✓ DONE** (native GL; sub-steps in
**`s5-viewer-design.md`**). **S5a** (one chunk → indexed heightfield → headless still),
**S5b** (`ViewerCam` + WASD pan / QE zoom + `--smoke` capture), **S5c** (3×3 chunk window + dirty
streaming, watertight, deterministic), **S5d** (Q/E LOD tier switch detail↔overworld via
`chunk_mesh_ov`; no-pop 2.4 m), **S5e** (dual split detail‖overworld via `gl_viewport`; `make
viewer` + `make viewer-gold` golden gate, green at 0 px). The browser/WebGL build waits on
loft#354 (native GL is the path). Filed **loft#392** along the way (silent abort on fn-returned
`vector<single>`→FFI). **Pending: user aesthetic sign-off** on the dual frame.
*Build (full target):* a loft program that streams chunks by tier, bakes via `gridmesh`,
uploads group VBOs; **WASD** pans, **QE** zooms = descend/ascend the LOD (dirty-streams the new
tier), **A|B** dual view (real-from-seed vs model). A `--smoke` mode scripts fixed camera/zoom
ticks for capture.
*Check:* **headless golden** — native `gl_screenshot` under `xvfb`+llvmpipe diffed vs golden
(tol max-16/mean-2) for fixed scenes; WebGL build gated by headless-Chrome (`html_render_check.mjs`)
non-blank + no-error; QE actually loads finer chunks (assert tier change); user signs off aesthetics.
*Gate:* golden match (native) / non-blank+no-error (WebGL) + WASD/QE functional.

**S6 — sub-hex content at the 1.5 m tier. IN PROGRESS (talus model) — see `s6-subhex-finding.md`.**
The original "per-triangle slope → cliff, validated by κ" premise was **falsified** (`s6_cliffs.py`:
at ~350 m real resolution forest is as steep as rock; +0.000 κ; and the loft world is synthetic, so
there's no real sub-hex reference). Pivoted (user's steer) to a **neighbour-coupled TALUS model**
generation, gated by invariants not κ: bedrock + weathering rubble; rubble slides to lower neighbours
(angle of repose); stripped steep bedrock → `K_FACE`, piled rubble → `K_SCREE`; cliff placement/height
= the inter-cell step; combined with the engine's coarse (ZAngband-style) zones. **Done:** S6.0 (1-D
pin), S6.1 (2-D + weathering, `s6_talus2d.py`), **S6.2** (`src/talus.loft` faces+scree, `talustest`
in `make test`: rubble conserved / repose / deterministic / watertight; viewer `VIEWER_TALUS=1`),
**S6.3** (flow-accumulation `K_RIVER` channels; `flow_accumulate` + `T_CHANNEL`; engine major rivers
preserved + fine tributaries carved; gated by the I3 downhill echo). **Left:** cliff-angle visual
tuning (the user's call — the 50° threshold reads ~80% face on the steepest chunk).

## Library patches / gaps (evaluated 2026-06-15; patch later, when everything functions)

S5 (the viewer) can be built **natively now without any lib patch** — `graphics` already has the
full GL+shader set: `gl_create_shader`/`gl_use_shader`, **`gl_set_uniform_mat4`** (app supplies the
MVP → camera/WASD/QE in-app), `gl_upload_vertices(vector<single>, stride)`, `gl_draw_elements`,
`gl_depth_mask`/`gl_enable`, `gl_screenshot`, window. With the custom `chunk_mesh` buffer that's
enough for the native render + headless golden gate.

- **BLOCKER (upstream, not ours): loft#354** — `make game` (`loft --html` WASM/WebGL) fails on
  block-split codegen (~51 rustc errors). So the **browser** dual-view waits for #354; S5 uses the
  **native `gl_screenshot` + Mesa-llvmpipe** path meanwhile (what `make probe` uses).
- **gridmesh flow-back (deferred):** it has only a *segment* mesh (`SegMesh`) + the
  `ChunkField`/group-VBO/dirty machinery — **no surface/triangle mesh**. Add a triangle/surface
  accumulator + triangle group-VBO so terrain batching reuses gridmesh instead of our custom
  `chunk_mesh`. (Until then `chunk_mesh` + a custom per-group upload is fine.)
- **graphics flow-back (deferred, convenience):** a camera/projection helper
  (`perspective`/`look_at` → mat4) so the viewer doesn't hand-roll the MVP.
- **chunk extraction (deferred):** `DetailChunk` (base+0.1 m) → `hex_world` / a chunk lib
  (EXTRACTION.md), reusable for moros too.

None of the deferred items block S5 natively; they're done "when everything functions".

## Extract to proper shared libraries (broader reuse — converge with dryopea Plan 07)

These primitives are **not crawler-specific** — dryopea and moros need the same, and already have
a **"shared world substrate" plan** (dryopea Plan 07: `gridmesh` + `moros_map` world model +
`moros_render` 3D + `moros_sim`). So they should become **proper shared libraries** — not crawler
`src/` — so all three games run one substrate. Extract (deferred until proven + the blockers clear):

- **chunk model** — `DetailChunk` (base+0.1 m), the two-tier geometry, `chunk_build`/`chunk_height`/
  `chunk_quant` → a shared **chunk/world lib**, converging with **`moros_map`** (`Map`/`Chunk`/`Hex`,
  height/material/walls/items). The base+0.1 m height encoding is our contribution.
- **heightfield surface mesh** — `chunk_mesh` (watertight neighbour edges) → into **`gridmesh`**
  (today only a *segment* mesh) and/or **`moros_render`** (surfaces/walls/slopes/stairs).
- **camera + input** — the pan/zoom + per-action `InputState` + pure-tick pattern (dryopea's
  `camera.loft` is the reference) → a shared **camera/input lib**; the 3D fly camera is the new bit.
- **golden harness** — canvas→png→byte-exact, deterministic, no GL (dryopea's `golden.loft`) → a
  shared **test/golden lib**, reusable for crawler's render gates too.

Track in **EXTRACTION.md**; converge with dryopea **Plan 07** rather than duplicating. **Gated by**
the same loft bugs that block the substrate today: `use`-namespacing ("Double structure type", blocks
adopting `moros_map`), the native struct-with-hash return bug (keeps everyone on `--interpret`), and
loft#354 (WebGL). Do the extraction once those clear and the primitives are proven in crawler.

### Concrete homes + sources (surveyed 2026-06-15)

The reuse survey (audience-demo + moros + the cloned `jjstwerff/dryopea`) pinned where each
library should live and the *working* code to extract it from:

- **chunk/world model** → **`loft-libs-world/hex_terrain`** is the existing convergence home
  (per `loft-libs-world/CONVERGENCE.md`, which already unifies the `hex_*` basis across
  crawler/dryopea/moros; `hex_grid` is the shared geometry crawler already consumes). The
  `moros_map` `Map/Chunk/Hex` is the richer end-state once `use`-namespacing unblocks it.
- **heightfield surface mesh** → **`gridmesh`** (today only a *segment* mesh — this is the
  missing surface primitive). Crawler's `chunk_mesh` already emits a stride-6 VBO
  (`x,h,z,r,g,b`) matching the audience-demo's `push_ground_hex` layout exactly — extract it
  as gridmesh's surface-mesh builder.
- **camera + input** → a shared **camera lib**, extracted from the audience-demo's **`AutoCam`**
  (`loft/tools/audience-demo/projector.loft` ~502–691: position/rotation lerp, distance-tilt,
  `build_view_matrix` via `math::mat4_look_at`) — the production fly-camera; dryopea's
  `EditorCamera`/`InputState` is the simpler editor variant of the same shape.
- **golden harness** → a shared **test/golden lib**, extracted from dryopea's `golden.loft`
  (`assert_golden`: canvas→png→byte-exact, deterministic, no GL window).
- **dirty render loop** → already a stable `graphics` primitive (`group_vbos_*`); the version-bump
  pattern (audience-demo `projector.loft` ~217–222, 946–1002) is the reuse template, not new lib code.

Naming: the **`jjstwerff/dryopea`** repo (cloned to `../dryopea`) has real camera/chunks/render/golden
code on `--interpret`; the loft-internal **Plan 46 "dryopea"** is the stalled design stub. Both name
the same game; the cloned repo is the live source.

## Files (anticipated)

- `loft-libs-world/hex_world.loft` (or a new `chunk` module) — `DetailChunk` + base/offset
  (extraction candidate; see EXTRACTION.md).
- `src/chunk.loft` — the two-tier mapping + `gen_chunk` (or in the lib).
- `src/chunkview.loft` — the loft WebGL viewer (WASD/QE, dual view).
- `src/chunktest.loft` — the invariant gate.
- consumes `../1-ortler-worldgen-fixture/` data for the real-terrain seed.

## Verification

- `chunktest.loft` in `make test`: I-HEIGHT round-trip, I-SEAM watertight borders, I-DET
  determinism, I-LOD tier-aggregate.
- **Viewer = headless golden gate (self-verifiable), two paths** — the sandbox *can* screenshot
  (deps present: `xvfb-run`, `chromium`, `node`, `convert`):
  - **native GL**: a `--smoke` mode scripts deterministic camera/zoom ticks, then
    `graphics::gl_screenshot(w,h,path)`; run under `xvfb-run -s "-screen 0 WxHx24"` with
    `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe` (deterministic software GL) → diff vs a
    golden PNG (tolerance max-16/mean-2, like loft's `crystal_editor_gold`). This is the
    **reliable framebuffer-read path crawler already uses in `make probe`**.
  - **WebGL**: `loft --html viewer.html …` → serve → `loft/tools/html_render_check.mjs` drives
    headless Chrome (CDP screenshot + canvas color-count gate).
- A human look stays welcome for aesthetics, but **correctness is gated headlessly** (golden
  images of the dual view at fixed scenes/zoom levels).

## Open questions

- **Tier scale ratios** — confirm the 32×/32× (1.5 km → 47 m → 1.5 m) hierarchy in P0, or a
  different split (e.g. a mid tier).
- **Where the chunk code lands** — extend the world library (`hex_world.loft`, reusable for
  moros too) vs crawler-first then extract.
- **Real-data seed** — how the @PLN1 Ortler data feeds detail chunks (the `overland_from_seed`).
- **Streaming policy** — which chunks load/unload around the viewer camera per tier.

## See also

- `s5-viewer-design.md` — the worked S5 viewer design; `s5-viewer-smooth.md` — the post-S5
  smooth-running plan (native throughput + responsive loop; the 38 s-freeze diagnosis, native
  22× measurement, the consumer `--native` gap, and gated steps V0–V8; audit 2026-06-16).
- @PLN1 `../1-ortler-worldgen-fixture/` — the real-terrain pipeline, derived defaults, I-MESH.
- `loft-libs-world/hex_world.loft`, moros `wall.loft` — the 32×32 chunk + height precedents.
- `gridmesh` (loft-libs-graphics) + `loft/tools/audience-demo` (`crystal_render.loft`,
  `crystal_stress.loft`) + audience_crystal `CrystalIncr` — the chunked batched-mesh pipeline
  (per-chunk cached `SegMesh`, dirty rebuild, one-VBO-per-group, build-once+GPU-anim) to reuse.
- `src/overland.loft` (real-metre defaults), `src/worldmesh.loft`, EXTRACTION.md.
