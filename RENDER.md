# RENDER.md — 2D rendering & the full-GPU optimization path

How crawler draws today, and the staged path to a **fully GPU-resident 2D renderer**
(world mesh + sprite atlas + shader FOV). All primitives below are confirmed present in
`graphics.loft`; nothing is missing — this is a *when*, not a *whether*.

## Current — immediate mode

`view.loft` redraws every frame on the CPU: per-hex `draw_rect_at` (floor), wall
segments, per-sprite `draw_texture_at` (mobs / items / glyphs / HUD). The world rotates
around the player (heading = up). Simple and fine at the current scale, but the geometry
and every sprite are re-emitted each frame.

## The retained-mode primitives (all in `graphics.loft`)

- **Geometry:** `gl_upload_vertices(data: vector<single>, stride) -> vao` (persistent VBO
  on the GPU), `gl_draw(vao, n)` / `gl_draw_elements(vao, n, mode)`, `gl_create_shader`,
  `gl_set_uniform_mat4/vec/int/float`.
- **Textures (PNG already shipping):** `gl_load_texture(path) -> tex` (PNG → GPU texture;
  `view.loft` already loads sprite PNGs), `gl_upload_canvas(data,w,h)` (CPU image → tex —
  glyph/HUD bake), `gl_bind_texture`, `gl_create_color_texture`, framebuffers +
  `gl_draw_fullscreen_quad` (post-fx).
- **Sprite atlas:** `SpriteSheet` (cols×rows grid) + `draw_sprite(sheet, mvp, idx)` /
  `draw_sprite_at(...)` — one atlas texture, draw any sprite **by index** with an MVP.

## The optimized renderer (full GPU 2D)

| Layer                | Static / dynamic        | Primitive |
|----------------------|-------------------------|-----------|
| World floor + walls  | static, upload once/level | `gl_upload_vertices` VBO + camera `mat4` |
| Mobs / items         | dynamic                 | `SpriteSheet` atlas + `draw_sprite` (by index/MVP) |
| Glyphs / HUD / text  | static-ish              | `gl_upload_canvas` / `create_text_texture` |
| FOV                  | per move/turn           | visibility texture/attribute, dimmed/discarded in the shader |

Per frame: a handful of GPU draw calls, near-zero CPU geometry/texture churn.

## FOV on the GPU

The **kernel** (`sim_compute_fov` + `sim_hex_state`) computes the visibility *set* —
**renderer-agnostic**. The GPU renderer consumes it as a per-hex visibility texture
(sampled by hex-id) or a per-vertex attribute, refreshed only on move/turn; the fragment
shader **dims** remembered hexes and **discards** unseen ones. Immediate mode consumes
the same set via `sim_hex_state` per hex. So the kernel FOV is built once, reused by both.

**Directed light.** Sight is *directional*: full `VISION_RADIUS` straight ahead, falling
off (forward-biased) to `NEAR_RADIUS` behind — a forward-pointed lamp. So **turning aims
your light** (a real tactical choice, extra reason to turn). Later the radius comes from
the equipped light item; coloured/animated falloff + a soft light-cone gradient is a
shader job (R4 post-fx) — the kernel just yields the boolean visible/seen set.

## The moros bridge

This retained `Vertex`/`Triangle` model *is* `moros_render`'s (`emit_hex_surface`,
`emit_wall_quad`). A 2D world mesh now is the same architecture, a 2D projection — the
step toward the 3D/WebGL build (the stated goal). Not throwaway.

## Staged plan (a focused task **after** the kernel FOV)

- **R1 — World mesh.** ✅ **Proven** (`src/gpushot.loft`): the depth-1 dungeon renders as
  one VBO + one shader + one `gl_draw`, the camera `mat4` folding `world_to_screen`
  (rotate-by-π/2−heading · scale 26 · centre 400/420 · px→NDC), captured to PNG. Verified
  loop = render → `gl_screenshot` → read PNG. **Stride-10 vertex layout** (pos=loc0,
  normal=loc1, **color=loc2** — the native `gl_upload_vertices` convention).
  **✅ Now LIVE in `view_draw`** — the terrain draws from the per-level VBO + FOV texture
  (one `gl_draw`); `story.loft` builds the shader once and the VBO per level (freed +
  rebuilt on descend/respawn), the vis-texture is created+freed each frame (no leaks).
  Painter draws stairs/walls/sprites/HUD on top — verified at parity with the immediate
  renderer. **Only R2 (sprite atlas) remains.**
- **R2 — Sprite atlas.** Pack mob/item sprites (the `tools/draw.py` atlas — already on its
  roadmap) into one `SpriteSheet`; `draw_sprite` by index. Replaces per-sprite
  `draw_texture_at`.
- **R3 — Shader FOV.** ✅ **Proven** (`src/gpushot.loft`): a per-hex visibility texture
  (`lw×lh`, R = brightness from `sim_hex_state`, uploaded via `gl_upload_canvas`) sampled
  in the fragment shader — **discards unseen, dims remembered**. The static VBO bakes each
  hex's visibility-UV into the unused **normal slot (loc1)**, so only the small texture
  updates per frame. Captured to PNG: fog gates correctly. (R2 sprite-atlas + the live
  `view_draw` swap remain.)
- **R4 — (optional) post-fx.** Framebuffer + `gl_draw_fullscreen_quad` for lighting /
  vignette / the light-radius falloff.

R1–R3 share the shader + VBO plumbing, so they're **one focused task**. The kernel FOV
(the visibility set) lands first (M-Core) and feeds both the current immediate renderer
and this one — nothing wasted.
