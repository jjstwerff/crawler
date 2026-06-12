# PLAN-RENDER.md — the showcase renderer, step by step

Phasing + verification for **RENDER.md** (R4–R9 + the `graphics` substrate flow-back).
Design lives in RENDER.md — this plan does not restate it; each step says what to
build, in what order, and **how to see quickly that it works**. Effort: S/M/L.

## The analysis channels (investigated 2026-06-12 — use these, in this order)

1. **Headless logic gate** (`make test`, a `src/<x>test.loft` per step — the standing
   convention). Most of this plan is CPU-side DATA: mesh floats, instance records,
   pack rectangles, batch-merge decisions, cache keys, scene versions. Test those as
   values — no GL, runs in the normal gate, fastest feedback.
2. **Pixel probes** (`make probe`, new): render under Xvfb → `gl_screenshot` → PNG →
   `tools/probe.py` asserts. **`gl_screenshot` is the RELIABLE capture** (a GL
   framebuffer read — `gpushot.loft` proved render→PNG; the "positionally off"
   caveat in CLAUDE.md is about `make shot`'s X11 window grab via xdotool, which no
   probe uses). probe.py emits a draw.py-style report: per-probe PASS/FAIL + deltas
   — exact judgment moved off the eye, the PNG still Read-able for the qualitative
   look.
3. **Golden parity diffs** (probe.py `diff` mode): when a step REPLACES a render path
   with an equivalent one (P2, P5, P6), capture before/after frames of the same seed
   + camera and assert pixel diff ≈ 0 (per-channel tolerance; diff image written for
   inspection). The strongest possible check, nearly free.
4. **Python blueprint plots** (PIL, throwaway or kept beside probe.py): for the
   exact-invariant math (capsule SDF coverage, miter joins, skyline packing) PLOT the
   concrete end-result first and pin the construction — the DESIGN-PROTOCOL rule;
   the loft code then ports a verified picture, not a guess.
5. **User visual pass** (`make play` / noVNC): theme + feel only — never the
   correctness channel.

## Steps

### P0 — probe harness (S) — infrastructure, do first

- **Build:** `tools/probe.py` (PIL): reads a PNG + a small text spec —
  `probe x y r g b [tol]` (point color), `ramp x1 y1 x2 y2 expect=mono-dec` (sampled
  line, monotonicity/range), `diff a.png b.png [tol] [out=diff.png]` — prints a
  PASS/FAIL report with deltas (the draw.py stats model). `make probe` target:
  Xvfb-runs each `src/*probe.loft` (the gpushot pattern: build scene →
  `gl_screenshot` → exit), then probe.py against its spec; exit 1 on any FAIL.
- **Verify:** self-test — probe a synthetic PNG written by probe.py itself.
- **Done when:** `make probe` runs gpushot's scene and asserts 3 known pixels
  (a lit floor hex, a wall-dark hex, the cleared background).

### P1 — Tier-0 idle skip (S) — biggest efficiency win, zero deps

- **Build:** a scene version in `story.loft` (bump on input / `sim_tick` / animation
  / page toggles); unchanged → skip render AND swap (RENDER.md → Frame reuse).
- **Verify (headless):** `src/idletest.loft` — version bumps exactly on the bumping
  events, holds otherwise (pure logic).
- **Analysis:** a debug counter (frames rendered / loop iterations) printed on Esc —
  idling must show rendered ≪ iterations.
- **Done when:** gate green; counter confirms idle frames render zero.

### P2 — R4 tint bake (S)

- **Build:** pre-compose `kind_tint` into the floor VBO colors at `build_world_mesh`;
  delete the per-frame wash loop (RENDER.md → R4).
- **Verify (headless):** `src/meshtest.loft` (new, this step's home for all
  world-mesh asserts): for known tiles, vertex color == `mix(floor, tint, a)` exact;
  vertex count invariant `18·lw·lh` holds.
- **Verify (probe):** overland frame — hex-center probes for expected blended colors;
  remembered-vs-visible dimming ratio at two probes.
- **Parity note:** NOT pixel-exact vs the old wash (square→hexagon is the point);
  probe colors are computed from the bake formula, not from the old frame.
- **Done when:** wash loop deleted, gate + probe green.

### P3 — R5 SDF wall strokes (M) — blueprint first

- **Blueprint (Python, before any loft):** plot ONE wall segment + one corner as the
  capsule-SDF coverage image; pin: center alpha 1.0, edge ramp width, the corner
  join continuous (no notch, no overlap-darkening). This plot IS the probe spec.
- **Build:** wall-quad VBO from `wallgeo` segments (visUV in the normal slot, the
  floor's pattern), capsule fragment shader, delete `draw_segment`'s stipple.
- **Verify (headless):** wall-VBO builder in `meshtest` — quad corners at
  centerline ± (w/2 + AA margin) exact; visUV per segment correct.
- **Verify (probe):** stroke-center probe = wall color; cross-stroke `ramp` =
  monotonic falloff; off-stroke = floor; a corner probe = same alpha as mid-segment
  (join continuity); a remembered-region wall dimmed by the vis ratio.
- **Done when:** stipple gone, probes match the blueprint plot, user confirms look.

### P4 — R6 post-fx light cone + vignette (M)

- **Build:** FBO chain (`gl_create_framebuffer` + `gl_draw_fullscreen_quad`),
  forward-biased falloff over the vis set, vignette (RENDER.md → R6).
- **Verify (probe):** `ramp` along the facing ray = monotonic-decreasing; forward
  ray brighter than backward at equal distance; corners darker than center
  (vignette); FOV gating unchanged (unseen still discards — reuse P0's probes).
- **Done when:** probes green; user judges the feel (this step is MOSTLY feel).

### P5 — substrate flow-back in `graphics` (M, lib repo, its own gate)

- **Build:** EXTRACTION.md §6(a): `gl_draw_instanced` + instance attributes,
  `gl_update_vertices`, `gl_set_uniform_vec2/vec4`, EBO upload, sampler control,
  texture sub-upload, `gl_scissor`. Per the lib change loop (EXTRACTION.md).
- **Verify:** the lib's own `loft test` + one GL smoke per entry point (lib-side);
  crawler consumes via dev `--lib` and re-runs gate + probes (no behavior change
  expected — pure additions).
- **Done when:** lib CI green, crawler gate green against the dev lib.

### P6 — R7 instanced floor (S, after P5)

- **Build:** one 18-vert hexagon + per-instance (center, color, visUV) records.
- **Verify (headless):** instance records in `meshtest` — count `lw·lh`, each
  record's center/color equal to the old per-hex derivation (same formula, exact).
- **Verify (probe):** **golden parity** — old-VBO frame vs instanced frame, same
  seed + camera: pixel diff ≈ 0. Same geometry, so this is exact; any diff is a bug.
- **Done when:** parity green, fat VBO path deleted.

### P7 — R8 sprite batch + auto-atlas (M)

- **Blueprint (Python):** skyline-pack the actual `assets/sprites/*.png` set; pin the
  pack layout (rects, no overlap, 1px padding) as data — the loft packer must
  reproduce it.
- **Build:** atlas pages packed at load (premultiply + pad + extrude), ONE instanced
  draw for all sprites/glyphs; absorb `draw_texture_rot` (RENDER.md → R8 + API
  point 4).
- **Verify (headless):** `src/atlastest.loft` — packer reproduces the blueprint
  layout exact; no-overlap + padding invariants; oversize-bypass + page-chain
  heuristics on synthetic sizes.
- **Verify (probe):** golden parity vs the per-call sprite path (same scene);
  rotated-sprite edge probes = no dark fringe (premultiply correctness: edge pixels
  never darker than both neighbours); draw-count assertion once frame-stats exists
  (P8), parity meanwhile.
- **Done when:** parity + fringe probes green; per-call sprite path deleted.

### P8 — painter frame-stats (S) — the introspection principle, pulled early

- **Build:** the stats call (RENDER.md → API point 6): draws, batch breaks + reasons,
  atlas occupancy — crawler-side counters now, flows back with painter v2.
- **Verify (headless):** known scene → known counts ("sprite layer = 1 draw" becomes
  an assert, not a hope).
- **Done when:** `make probe` prints the stats line per probe scene; P7's one-draw
  claim is asserted.

### P9 — R9 layer caches (M, profile-gated — do when HUD/map grows)

- **Build:** `make_layer`/`invalidate`/`draw_layer` over FBOs; HUD layer on dirty
  flag; world-space world layer (RENDER.md → Frame reuse, Tiers 2–3).
- **Verify (probe):** two identical frames → cached HUD texture byte-identical
  (diff = 0); bump HP → exactly the HUD region changes; world-layer parity vs live
  render within AA tolerance; scissored partial redraw (needs P5's `gl_scissor`)
  changes ONLY the damage rect.
- **Done when:** parity probes green AND the frame-stats show the cached path's draw
  count drop — otherwise the layer isn't earning its complexity; defer again.

## Order + status

P0 → P1 → P2 → P3 → P4 (no upstream deps, each independently shippable, gate-green)
→ P5 (lib) → P6 → P7 → P8 → P9 (gated). Painter v2's full canvas surface
(EXTRACTION.md §6(b)) is paced separately by lib consumers — this plan ships crawler
proof pieces (P3's stroke shader, P7's batcher/atlas) that flow back into it.

| Step | Effort | Status |
|---|---|---|
| P0 probe harness | S | — |
| P1 idle skip | S | — |
| P2 tint bake (R4) | S | — |
| P3 SDF walls (R5) | M | — |
| P4 light cone (R6) | M | — |
| P5 substrate flow-back | M (lib) | — |
| P6 instanced floor (R7) | S | — |
| P7 sprite batch + atlas (R8) | M | — |
| P8 frame-stats | S | — |
| P9 layer caches (R9) | M | gated on profiling |
