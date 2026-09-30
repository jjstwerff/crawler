# S5 — the chunked-LOD terrain viewer (detailed design)

> Detail doc for plan #2 step **S5**. The README has the one-paragraph spec; this file is
> the worked design that fills in as facts land (per the plan rule: iterate details in
> separate `.md` files). Design-protocol shape: concrete end-result → invariants → reuse
> map → gated sub-steps → open questions.

## Concrete end-result (the plotted target)

One native-GL window over the Ortler fixture (`overland_new()`):

- **Split view** (`gl_viewport`): **left = model B** (our generated chunks), **right = A**
  (real-from-seed) — same camera, same frame. (A==B until the real-height seed is wired;
  until then both panes render the model and the split just proves the viewport split works.)
- **Terrain** = the detail-tier heightfield: each visible `DetailChunk` baked to a 33×33
  vertex grid (`chunk_mesh`), per-vertex colour by kind (`kind_rgb`), drawn indexed.
- **WASD** pans the camera focal across the world (metres); **Q/E** zoom = ascend/descend
  the LOD (overworld tier ↔ detail tier), dirty-streaming the newly-visible chunks.
- **`--smoke`** runs a fixed script of camera/zoom ticks then `gl_screenshot`s named frames
  and exits — the headless golden gate.

World units are **metres**: a detail cell ≈ `DETAIL_CELL_M` (1.465 m), a chunk ≈ 46.9 m,
heights 0…~3900 m. The camera/projection must span that (far plane + height scale — see
open Q3).

## Invariants (what S5 must not break)

- **I-MVP-DET** — for a fixed (camera, tier) the MVP is bit-identical run-to-run ⇒ `--smoke`
  frames are reproducible ⇒ golden diff is meaningful. (No `Date/random` in the camera.)
- **I-SEAM-RENDER** — adjacent chunk meshes share boundary vertices exactly (already proven
  in `meshchunktest`: right edge == east neighbour cell-0 column) ⇒ **no cracks** between
  chunks in the rendered surface.
- **I-LOD-NOPOP** — on a Q/E tier switch the surface passes through the same world points
  (both tiers sample the same engine field; `detailtest` I-LOD bounds the centre delta) ⇒
  no visible jump when zooming.
- **I-VIEWPORT** — left and right panes are the same world through the same camera; only the
  data source (B vs A) differs. A==B must render pixel-identical while the seed is unwired.

## Reuse map (concrete sources)

| Need | Reuse | Note |
|---|---|---|
| Window / GL state | `graphics::gl_create_window`, `gl_enable(GL_DEPTH_TEST)`, `gl_clear`, `gl_swap_buffers`, `gl_poll_events` | exactly the projector main() preamble (`projector.loft:800–833`) |
| Split panes | `graphics::gl_viewport(x,y,w,h)` | left `(0,0,w/2,h)`, right `(w/2,0,w/2,h)`; set per pane before draw |
| Mesh upload + draw | `gl_upload_vertices(vector<single>, 6)` + `gl_upload_indices(vao, idx)` + `gl_draw_elements(vao, n, DRAW_TRIANGLES)` | indexed 33×33 grid; **chunk_mesh emits `vector<float>` — must cast to `single`** (open Q1) |
| MVP | `math::mat4_perspective(fov,aspect,near,far)` × `math::mat4_look_at(eye,target,up)` → `gl_set_uniform_mat4(prog,"uMVP", m.m)` | proj×view via `math::mat4_mul`; `mat_look_at` up=`(0,0,-1)` north-up like the projector |
| Camera math | adapt `projector.loft:524–560` `build_view_matrix` eye/focal | **replace** AutoCam auto-record/lerp with **direct WASD/QE input** (the new piece) |
| Input | `graphics::gl_key_pressed(KEY_*)` directly | simplest, no extra dep; the `input` lib (loft2/lib/input: Bindings/InputState/`get_axis`) is the later shared-lib path |
| Golden capture | `graphics::gl_screenshot(w,h,path)` after draws, before `gl_swap_buffers` (reads GL_BACK — headless-safe) | the `make probe` xvfb+GL path is already green on this VM |
| Loop | a plain `while gl_poll_events()` standalone loop | **drop** `engine_host::run_client` — the projector is a *networked spectator*; S5 is standalone (no host) |

## Shaders (stride 6: x,h,z, r,g,b)

```glsl
// vertex
layout(location=0) in vec3 aPos;   // x, height(m), z
layout(location=1) in vec3 aCol;   // r,g,b
uniform mat4 uMVP;
out vec3 vCol;
void main(){ vCol = aCol; gl_Position = uMVP * vec4(aPos, 1.0); }
// fragment
in vec3 vCol; out vec4 frag;
void main(){ frag = vec4(vCol, 1.0); }
```

## Index buffer (the missing half of chunk_mesh)

`chunk_mesh` emits 33×33 vertices but **no indices**. S5 builds the EBO once (topology is
fixed, base-0): for each cell `(i,j)` in `0..32` two triangles over `v=j*33+i`:
`[v, v+1, v+33]` and `[v+1, v+34, v+33]` ⇒ `32*32*2*3 = 6144` indices. Build in loft as
`vector<integer>` and `gl_upload_indices`. (Same EBO reused for every chunk — only vertices
change per chunk.)

## Gated sub-steps (each independently verifiable)

- **S5a — one chunk, fixed camera, headless still.** Window + depth + stride-6 shader; bake
  one `detail_chunk` over the mountain hex via `chunk_mesh`→single; static MVP looking at the
  chunk; `gl_screenshot` one frame under xvfb. *Gate:* non-blank PNG with terrain colours
  (kind palette present, not background). Pins the GL pipeline + mesh upload + MVP.
- **S5b — camera + WASD/QE input.** `ViewerCam{focal_x, focal_z, zoom}` driven by
  `gl_key_pressed`; WASD moves focal in metres, Q/E change `zoom`. *Gate:* a scripted
  pan/zoom in `--smoke` produces a *different* golden than S5a's centred frame (camera
  actually moves), still deterministic across two runs.
- **S5c — multi-chunk streaming + watertight render.** Render the NxN chunk window around the
  focal; rebuild the visible set as the focal moves (dirty: only newly-entered chunks bake).
  *Gate:* golden shows ≥4 chunks seamless (visual I-SEAM-RENDER); no per-frame full rebake
  (assert bake count == newly-entered count).
- **S5d — Q/E LOD tier switch.** Below a zoom threshold render `overworld_chunk` (coarse),
  above it `detail_chunk`. *Gate:* assert the tier actually changes on Q/E (a logged tier
  field) and the centre vertex height matches across the switch (I-LOD-NOPOP, reuse the
  `detailtest` bound).
- **S5e — dual A/B + golden gate wired to make.** Split viewport; right pane = real-from-seed
  (A) once the seed lands, else == B. Add a `make` target (`make viewer` / `make viewergold`)
  running `--smoke` under xvfb + a golden diff (tol max-16/mean-2, the `crystal_editor_gold`
  pattern). *Gate:* golden match on the fixed scenes; user signs off aesthetics.

## Open questions (resolve cheaply, in order)

1. **float→single for the VBO.** ✅ RESOLVED (S5a). `chunk_mesh` returns `vector<float>` (f64);
   `gl_upload_vertices` wants `vector<single>` (f32). The cast loop is **INLINED in `main`** — it
   must NOT be a helper `fn(vector<float>) -> vector<single>`: routing the real `chunk_mesh`
   output through such a helper **silently aborts the whole program** (no stdout, no PNG, exit 0;
   only a store-leak warning). Filed **loft#392** (`sev:high`, `wa:clean` = inline the loop).
   Standalone shrink attempts all pass → context-dependent store-lifetime interaction at the
   native-FFI boundary. `chunk_mesh` stays the tested headless API; the viewer inlines the cast.
2. **Height scale.** Heights to ~3900 m next to 1.5 m cells may look like spikes. Decide in S5a
   whether to render true metres (and just frame the camera far enough) or apply a vertical
   exaggeration/normalisation. Keep enrichment **out of the renderer** (the standing rule) — if
   we scale, scale in the MVP (a view transform), not in the mesh data.
3. **Projection span.** `mat4_perspective(near,far)` must bracket metres-scale geometry; pick
   near≈0.5, far≈ a few km. Confirm in S5a (clipping check in the still).
4. **`overworld_chunk` mesh.** S5d needs a coarse-tier mesh; confirm `chunk_mesh` works on an
   overworld-tier chunk as-is (same 32×32 shape) or needs a coarse variant.

## Status

- **2026-06-15** — design authored; all GL/math/input/headless facts pinned (graphics.api +
  math lib + xvfb present).
- **2026-06-15** — **S5a DONE**: `src/viewer.loft` bakes one detail chunk via `chunk_mesh`,
  uploads the indexed 33×33 heightfield, renders one frame from a fixed camera, `gl_screenshot`
  → `/tmp/viewer_s5a.png` (1089 verts / 2048 tris). Hit + filed **loft#392** (silent abort on
  fn-returned `vector<single>` → FFI; worked around by inlining the cast).
- **2026-06-15** — **S5a framing tuned**: scanned the mountain flank for kind-variety+relief
  (coarse `ov_sample` grid, not full `detail_chunk` builds — 1024-cell builds are too slow to
  scan many). Picked **chunk (143,83)** (below hex 4,3): grass + forest + a **rock FACE** + a
  **river**, ~89 m relief over the 47 m footprint. Camera = steep 3/4 view, distance framed to
  the **footprint** (≈109 m), target weighted to the terrain mass (`minh + 0.35·span`). Reads
  clearly as varied terrain (forest / blue river / grass / grey cliff). No lighting yet → relief
  shows only via silhouette (flat per-vertex colour); GPU lighting (needs normals) is a later
  enhancement.
- **2026-06-15** — **S5b DONE**: replaced the fixed camera with `ViewerCam{focal_x, focal_y,
  focal_z, zoom}`. **WASD** pans the focal (metres, step ∝ zoom), **Q/E** zoom out/in (camera
  distance, clamped 40–2000 m), **Esc** quits — an interactive loop throttled by `gl_swap_buffers`
  vsync, plus a scripted **`VIEWER_SMOKE=1`** capture (3 poses: initial → pan → zoom-in →
  `/tmp/viewer_s5b_0..2.png`, no event wait — the headless path). MVP factored into `build_mvp`
  (lib-struct `Mat4` return, safe) + a void `draw_frame`, shared by both paths. **Gate met:**
  the 3 smoke frames are byte-**identical across two runs** (deterministic — software-GL golden
  holds) and **differ from each other** (0≠1 pan, 1≠2 zoom). Interactive loop compiles + shares
  `draw_frame`; tested on a real display by the user (headless here only runs smoke).
- **2026-06-15** — **S5c DONE**: a multi-chunk **window** (RAD=1 → 3×3) around the focal with
  **dirty streaming**. Loaded set = pre-allocated slots (cap 64, `vao==0`=empty — the engine
  index-write idiom, loft#320-safe); `window_update` evicts slots that left the window (frees the
  VAO) and bakes only those that entered. `bake_chunk(o,cx,cz,idx) -> vao` builds the mesh +
  uploads **inside** the fn (vbuf never crosses the boundary → loft#392-safe). One MVP, draw every
  loaded VAO (chunk verts are global world coords, so adjacent meshes share edges exactly →
  watertight). **Gates met:** initial bakes = **9**, each pan bakes **3** (the new column/row, not
  the full 9 → dirty streaming confirmed); the 9-chunk render is **seamless** (no cracks across
  boundaries — visual I-SEAM-RENDER); **byte-identical across two runs** (deterministic golden);
  frames differ on pan. ~50 s for the smoke (60 `detail_chunk` builds interpreted; the 4× neighbour
  re-build + interpreted cost is the perf tail — a DetailChunk cache / gridmesh batching is the
  optimisation, noted for the lib flow-back, not needed for the gate).
- **2026-06-15** — **S5d DONE**: Q/E LOD **tier switch**. `tier_overworld(zoom)` flips at
  `LOD_T=600 m` camera distance; below → DETAIL (1.46 m cells, 3×3 window), above → OVERWORLD
  (1.5 km hex cells via the new `chunk_mesh_ov` — vertices at `overworld_center`, RAD=0 since one
  32×32-hex chunk covers this 9×7 world). On a tier flip the loaded set is fully cleared
  (`clear_loaded`) then re-streamed (the tiers' chunk coords are different scales). Both tiers read
  the SAME `ov_sample` field. **Gates met:** smoke logs the sequence detail→overworld→detail
  (`changed=true`); **no-pop** — the two tiers' rendered height at the focal hex centre agree to
  **2.4 m** (< the 8 m detailtest I-LOD bound). The overworld view renders the whole continent
  (massif + forested flanks + sea), relief clearly visible at continental scale. `chunk_mesh_ov`
  gated headlessly in `meshchunktest` (count + follows-data).
- **2026-06-15** — **S5e DONE — S5 (viewer) complete.** Dual **split view** via `gl_viewport`:
  **left = detail tier** (the flank chunk close up), **right = overworld tier** (the whole
  continent). Two cameras + two dirty-streamed chunk sets; `render_all` factored into a no-clear
  `draw_pane` called per viewport (clear once at full viewport, then draw each pane). WASD/QE drive
  the detail (left) camera; the overworld pane is a fixed overview. **`make` targets added:**
  `make viewer` (interactive) and `make viewer-gold` (headless — render the dual frame under Xvfb,
  diff vs `tools/golden/viewer_s5e.png` with imagemagick `compare -fuzz 6%`, threshold 800 px; on
  first run with no golden it prints the adopt command). **Gate met:** `viewer-gold` green at **0**
  differing pixels vs the golden. (The original A=real-from-seed / B=model comparison reuses this
  exact split once plan #1's real-height seed is ported into loft; until then the panes show the two
  LODs of the model.) **User aesthetic sign-off pending** (the one thing the agent can't self-judge).
  **S5 done; next is S6** (sub-hex cliffs/channels at the 1.5 m tier — the plan #1 κ re-run).
