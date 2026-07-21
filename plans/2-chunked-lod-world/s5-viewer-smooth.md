# S5 viewer — the smooth-running plan (native throughput + responsive loop)

> The viewer is functionally complete (`s5-viewer-design.md`) but **unusable interactively**: a
> ~38 s black/frozen startup, then a multi-second freeze on every pan. This doc is the full,
> gated plan to make it **smooth**. It supersedes the ad-hoc checklist in `s5-viewer-hardening.md`
> (those items survive here as V4/V5). Design-protocol shape: measured facts → the two levers →
> gated steps → the native decision → open questions.
> Branch: combat · Part of plan #2 · Audit + measurements: 2026-06-16.

## Measured facts (the evidence — all reproduced on this host)

| measurement | interpret | native | note |
|---|---|---|---|
| `overland_new` | 97.9 ms | 16.1 ms | via `ticks()` |
| **one `detail_chunk`** (1024 `ov_sample`) | **1024 ms** | **45.8 ms** | **~22× native** |
| viewer startup (36 builds, blocking) | **37.8 s** | ~1.7 s | the whole frame is baking |
| a pan (3 chunks × 4 neighbours = 12 builds) | ~12 s | ~0.55 s | still a visible hitch even native |
| 36 builds vs 16 unique | — | — | 2.25× redundant (no cache) |

- **`--native` is loft's default; `make viewer` forces `--interpret`** (`Makefile:258`). The
  interpreter is the blocker, exactly as suspected.
- **The startup blocks for 38 s before the first frame.** Xvfb timestamped run: window created at
  `0.09 s`, first `gl_clear`/`gl_swap_buffers`/`gl_poll_events` at `38.30 s`. The whole window is
  baked at `viewer.loft:222-226` *before* the loop's first draw or event poll → an undecorated
  black, "unresponsive" window (the user's report). Each chunk-crossing pan re-blocks the same way.
- **Native GL is real but not wired for consumers — TWO upstream blockers, both pinned.** The
  crystal-demo projector compiles+runs native (`loft … projector.loft`, RC=0) because it lives in
  the loft repo where `make rebuild-native-cdylibs` registers `lib/*/native` under one `Cargo.lock`.
  For crawler-as-consumer:
  1. **P269 registration.** With graphics from the registry (crawler's `loft.toml` pin) or a bare
     `--lib`, the `loft_gl_*` natives never enter `native_packages` → loft bakes `compile_error!`
     into each GL body ("no implementation in any registered native crate"). **Cleared** by
     resolving graphics from loft's native-registered `lib/graphics` with **no crawler `loft.toml`**
     in the tree (verified: P269 gone).
  2. **`cfg_if` StableCrateId collision.** Once registered, the rustc link fails:
     `found crates (cfg_if and cfg_if) with colliding StableCrateId values` — the graphics native
     crate's transitive deps vs loft's own aren't deduped for a consumer build (the hazard
     `add_native_extern_flags` only partly guards). The in-repo projector dodges it via a unified
     lockfile. So whole-program `--native` for a consumer is blocked **upstream**, in two places —
     a hand-rolled rustc build wouldn't escape #2 (same colliding deps).
- **`gl_clear` clears depth too** (`COLOR|DEPTH_BUFFER_BIT`) — a stale-depth theory was ruled out.
- loft **steady-state model (C71 / BROADENING.md)**: *native libraries (dlopen'd cdylibs) +
  interpreted scripts*. The auto-native-cdylib path for `use`d libs exists but currently **falls
  back to interpret on this host** (`hex_grid`/`hex_terrain`: "libloft.rlib not found for this
  build") — the same toolchain-refresh gap as `make game`'s E0514.
- **LANDED (merged to loft `main`, 2026-06-16): `LOFT_REQUIRE_NATIVE=1`** (`main.rs:4856`) — turns
  every native→interpreter fallback into a **hard error naming the reason** (refuses to silently run
  the 22×-slower interpreter). This is the Phase-B de-risker / the "require native" gate (prove no
  library quietly dropped to interpret; actionable error instead of the vague "libloft.rlib not
  found" warning). **Not yet usable here:** the *installed* loft is a broken/stale build (loft-doctor:
  binary STALE + stale stdlib leftover `02_images.loft` → panics on its own stdlib). Refresh first
  (`sudo rm -f /usr/local/share/loft/default/02_images.loft && cd ../loft2 && make install`), then
  Phase B gates adopt `LOFT_REQUIRE_NATIVE=1`.

## The two levers (both required for "smooth")

1. **Throughput — run native** (the user's directive). 22× on the hot path; startup 38 s → ~1.7 s.
   Necessary but **not sufficient**: a native pan still blocks ~0.55 s on the main thread.
2. **Responsiveness — never block the loop.** Paint before baking; stream chunks a few per frame;
   don't rebuild what's cached. Makes the window appear instantly and pans stay live *regardless*
   of per-bake cost. Necessary even when native, sufficient for "doesn't freeze."

Smooth = lever 1 (each bake cheap) **×** lever 2 (no bake ever blocks the frame).

## Gated steps (each independently verifiable; gate must be green before checking)

### Phase A — responsive on the interpreter (works TODAY, no toolchain risk)

- [x] **V1 — paint + poll a frame before the startup bake** (was R0a). **DONE 2026-06-16 (verified:
  window paints before the camera-framing build; golden held at 459 px).** Before the initial
  `window_update` (`viewer.loft:222`): `gl_viewport`+`gl_clear`+`gl_swap_buffers`+one
  `gl_poll_events`, optionally a "loading" clear colour. *Gate (Xvfb):* first `gl_swap_buffers`
  at < 0.5 s, not 38 s; the window paints + the WM decorates immediately.

- [ ] **V2 — `DetailChunk` cache** (was E1). **DEPRIORITISED 2026-06-17 — premise largely
  superseded.** The "startup 38 s → 17 s" prize is gone: V1/V3 removed the freeze, and the two
  default views don't stream `ov_sample`-built chunks at all — the **Ortler** default (V10) reads
  **baked-in arrays** (no `ov_sample`; 9 chunks ×2 panes in ~420 ms, then pure draw), and the
  **overworld** default bakes **one** chunk once. The cache's remaining value is the **opt-in
  detail-streaming path** (`VIEWER_DETAIL`, 4 `detail_chunk` builds/frame) and the **future
  zoom-to-detail LOD** — real, but no longer on the default hot path. Keep the design for when the
  LOD tier lands. If revived: **blueprint-first** (exact invariant — pin **cached build == fresh
  build, byte-identical**), mind loft#392 (don't route `vector<single>` through a returning helper)
  and the loft#320-safe slot index-write. **V2b** (drop the camera double-build) is similarly minor
  now — only the opt-in overworld view rebuilds chunk (0,0) for its height span.

- [x] **V3 — incremental streaming** (was R0b). **DONE 2026-06-16 (verified: interactive loop start
  38.2 s → 1.25 s; `window_evict`/`window_bake_one` split, ≤`STREAM_PER_FRAME` bakes/frame; smoke
  keeps the one-shot full bake so the golden is unchanged).** `window_update` enqueues newly-dirty chunks; the
  loop bakes at most **K per frame** and keeps clearing/drawing/swapping/polling. Terrain pops in
  while the window stays live. *Gate:* a scripted pan never blocks the loop for more than one
  chunk-bake; loop keeps iterating; partial terrain renders mid-stream.

- [x] **V9 — full-landscape default view** (overworld tier). **DONE 2026-06-16 (verified headlessly:
  `VIEWER_OVSHOT=1` → `/tmp/viewer_overworld.png`, the whole 9×7 world in frame; golden held at
  459 px).** The interactive default was a ~140 m DETAIL slice (3×3 chunks) — high detail, tiny
  area. Now the default renders the **overworld tier**: `chunk_mesh_ov` samples the whole world into
  **one** coarse 32×32-hex chunk (1.5 km cells), framed at build_mvp's fixed 3/4 angle (zoom 18000,
  focal a quarter up the relief). **One** bake, then the loop is **pure draw** — instant *and* never
  re-bakes on pan/zoom (the chunk stays (0,0)), so it's both *quicker* and the *full view*. The old
  detail slice is kept behind **`VIEWER_DETAIL=1`** (still the dual model|talus split, `VIEWER_TALUS=1`
  for the B-pane); the golden smoke path is untouched (still the dual detail frame). New library fn
  `overworld_chunk_of` (chunk.loft) parallels `detail_chunk_of`; new headless gate env `VIEWER_OVSHOT`.
  Time-to-first-frame ~2.15 s on the interpreter (loft startup + GL init + the single bake). *Gate:*
  `make viewer-gold` 459 px (unchanged); `VIEWER_OVSHOT` frame shows the full island landscape.
  *Future:* zoom-driven LOD — swap to the detail tier as you zoom into a region (the real S5 LOD).

- [x] **V10 — real Ortler source + fly camera + size-following viewport** (the DEFAULT view).
  **DONE 2026-06-16 (verified headlessly: `VIEWER_ORTSHOT=1` → `/tmp/viewer_ortler.png`, the real
  massif dual screen; golden held at 459 px).** `make viewer` now defaults to the real **80×80
  Ortler** (plan #1) as the dual screen: **LEFT = real OSM landcover** (A, ground truth) | **RIGHT =
  our model's elevation bands** (B) over the SAME real DEM — the plan #1 adequacy comparison, live in
  3D. Pipeline: a Python exporter (`plans/1-ortler-worldgen-fixture/export_ortler_loft.py`) bakes
  the npz into `src/ortlerdata.loft` (numeric literals, parse ~0.2 s — no file I/O); `src/ortlergen.loft`
  builds DetailChunks (`ortler_chunk`, A/B classifiers) fed through the **efficient overworld mesh
  routine** (`bake_ortler` → `chunk_mesh_ov`) since the Ortler shares the moros odd-r 1500 m
  convention; framed to the **visual area** (summit-centred), **6× vertical exaggeration** at
  mesh-build (so ~3.7 km of real relief reads as mountains; applied after the base+0.1 m encoding
  to dodge the 6553 m offset cap). 9 chunks × 2 panes bake in **~420 ms** (interpreter), then pure
  draw. Introduced the `FlyCam` (interactive controls evolved → see **V11** for the current scheme);
  the **viewport follows the live window size** (`gl_window_width/height` each frame, re-splits the
  dual panes — handles resize/fullscreen). Procedural views are now opt-in: **VIEWER_OVERWORLD=1**
  (full landscape), **VIEWER_DETAIL=1** (detail slice). Smoke/golden untouched. *Next:* port the
  model's `material_contest` (slope-aware) for a faithful B; re-export hook in `make`.

- [x] **V11 — free-look camera** (the Ortler default). **DONE 2026-06-17 (verified headlessly:
  initial-vista frame; golden held at 0 px).** A simple, **non-realistic free-fly** cam: the mouse
  looks around, WASD pans, Shift/Space change speed. dt-scaled via `ticks()` (frame-rate
  independent). A **soft terrain floor** samples the Ortler height under the eye and keeps
  `FLY_CLEAR` above it. The camera **starts still** at a fixed vista — nothing moves until you press
  WASD.

  | input | action |
  |---|---|
  | mouse (relative motion) | look around — yaw + pitch, no roll/banking |
  | W / S · A / D | pan forward-back · strafe left-right (look-relative) |
  | Shift · Space | faster · brake (slower) |
  | Esc | quit |

  Mouse-look is **delta-based** (`prev_mx/my`), not absolute — so there is no startup snap and
  big cursor jumps (window re-entry) are ignored. Tuning (`FREE_SPEED/BOOST/BRAKE`, `LOOK_SENS`,
  `FLY_CLEAR`) is one const block. Keyboard-only fly kept behind **`VIEWER_FLYKEYS=1`** (A/D yaw,
  W/S pitch, Q/E move). The `FlyCam` keeps a `roll` field (held 0 here) so `build_mvp_fly`'s banked
  horizon is available if a flight mode returns.

  *Design note — why not the airplane model.* An earlier pass built a realistic flight cam
  (bank-to-turn, tilting horizon, coordinated yaw, continuous airspeed). Two problems killed it:
  (1) with no GL cursor-lock the absolute-cursor "stick" read the startup cursor position as full
  deflection → it flew to the sky with no input; (2) the realism wasn't wanted for a terrain
  *viewer*. Replaced by the free-look cam above. The banked-horizon math survives in `build_mvp_fly`
  for later. *Open:* look sensitivity / pan speed are first-pass, tune by feel; cursor-lock (if the
  graphics lib gains it) would remove the mouse-look edge limit.

*After Phase A the viewer is **usable** on the interpreter: instant window, no freeze, the full
landscape is up in ~2 s (overworld default), and the detail slice streams in over a few seconds.*

### Phase B — native throughput (the 22×; resolves the upstream gap)

- [x] **V0 — spike ANSWERED: native works end-to-end against the coherent ../loft tree**
  (2026-06-16). Building the viewer with **../loft's binary + `--path ../loft/ --lib ../loft/lib/
  --lib ../loft-libs-world/`** compiles clean (`--check --native` → ok) AND renders correctly
  (`--native-release` smoke → `/tmp/viewer_s5e.png`, **459 px golden match**, ~8.5 s vs ~41 s
  interpret). **Both P269 and `cfg_if` vanish** because one coherent tree gives matching shared-dep
  SVHs (#274 fix present) and `--lib lib/graphics` registers the native package (no P269). ../loft
  left **unmodified** (read-only; the `src/parser/objects.rs` edit there is the loft agent's
  concurrent WIP, not this build). The remaining gap (#396) is about the *registry/installed-loft*
  path: a normal `make viewer` (registry graphics) still P269s; the ../loft route sidestepped it.
  **UPDATE (2026-06-16, after the toolchain refresh):** both native routes are currently blocked —
  (a) **#396 confirmed still open** on the *real* build (`--native-release` → P269; note `--check
  --native` **false-passes** it, so it's a bad probe — `viewer-release` now runs `--native-release`
  directly); (b) the **../loft coherent route now hits E0514** — the prebuilt `loft_graphics_native`
  rlib was built by rustc 1.94.1 but the refreshed loft uses 1.96.0; it needs `make
  rebuild-native-cdylibs` (or `cargo clean && cargo build --release` in `lib/graphics/native`) in
  ../loft to recompile against the current rustc. So: native works once **either** #396 lands
  **or** ../loft's graphics cdylib is rebuilt (then `viewer-release` against ../loft). `make
  viewer-release` is now **native-only** (LOFT_REQUIRE_NATIVE=1, no interpreter fallback).

- [x] **V0-file — upstream issues filed/identified** (2026-06-16). **P269 = loft#396** (filed,
  `sev:medium`/`wa:partial`/`area:native`,`area:packages`/`hit-by:crawler`, verified standalone
  repro). **`cfg_if` collision = loft#274** (closed, `wa:clean`). **Fix verified present** in the
  installed loft (2026.6.0): `auto_build_native` sets `RUSTFLAGS=env!("LOFT_BUILD_RUSTFLAGS")`
  (`extensions.rs:2545`). The collision I hit is a **stale pre-fix artifact** — the
  `loft/lib/graphics` rlib is from **May 30** (before the Jun-7 fix) with two `cfg_if` rlibs in its
  `deps/`, linked as-is via the `--lib` workaround. So **#274 is not a residual code blocker**; it
  needs (a) #396 fixed so a registry consumer reaches the fixed auto-build path, and (b) a coherent
  native-cdylib rebuild (`make rebuild-native-cdylibs`). Its end-to-end verification (the #274
  author's open ask) is **gated by #396**. **Net: the live blocker is #396; #274 should fall out
  once #396 lands + a fresh native build.** Procedure: FILING.md. Phase A continues on `--interpret`.

- [x] **V4-stage — `make viewer-release` target landed** (2026-06-16). Opt-in native-release viewer
  that probes the native build (`--check --native`) and runs `--native-release` if clean, else
  reports the upstream gap and falls back to the interpreter — so it works today and **auto-upgrades
  to the 22× the moment V0 lands**, no Makefile change needed. Verified: probe catches P269, falls
  back, window opens.
- [ ] **V4 — switch `make viewer` / `viewer-gold` to native** once V0 is green. Drop `--interpret`;
  resolve graphics the registered way; keep an `--interpret` fallback when the native toolchain is
  absent (E0514 / libloft.rlib). *Gate:* `viewer-gold` golden byte-identical; wall-time 41 s → ~2 s;
  first-run rustc compile (~1 min) cached so re-runs are instant; fallback prints a clear message;
  once available, a CI run with the **require-native flag** confirms the hot path is genuinely
  native (no silent interpreter fallback hiding the 22× regression).

- [ ] **V5 — (stretch) native the world libs** (was E2). Get `hex_grid`/`hex_terrain` (and, if
  extracted, `overland`/`chunk` per the C71 steady-state) to build their native cdylibs instead of
  the "libloft.rlib not found" interpret-fallback — the last slice of per-call cost. Depends on a
  loft toolchain refresh; track with EXTRACTION.md. The incoming **require-native flag** is the
  driver here: run with fallback disabled, read its clear error, fix the named cause (libloft.rlib
  mismatch). *Gate:* `viewer-gold` passes with the **fallback disabled** (no library silently
  interpreted); per-`detail_chunk` drops below 46 ms.

### Phase C — robustness + test coverage (independent of native)

- [x] **V6 — guard `gl_create_shader`** (was R1). **DONE 2026-06-17.** `gl_create_shader` is now
  checked like `gl_create_window`: `if shader == 0 { println("FAIL: gl_create_shader …"); return; }`
  — a failed compile/link exits with a loud FAIL instead of a blank render.

- [x] **V7 — fail loud on a failed VAO upload** (was R2). **DONE 2026-06-17.** Both bake fns log a
  loud `FAIL: gl_upload_vertices returned 0 (chunk …)` and return a **−1 sentinel** instead of 0.
  The slot machinery reads −1 as *occupied* (no silent infinite re-bake — a 0 read as an empty
  slot), and draw/delete now guard `vv > 0` so the sentinel is never drawn or `gl_delete_vao`'d.
  *Gate met:* the 0-return no longer loops; it's visible. (golden held at 0 px.)

- [x] **V8 — cover the talus pane + re-baseline the golden** (was R3+R4). **DONE 2026-06-17.** New
  `make viewer-gold-talus` (`VIEWER_SMOKE=1 VIEWER_TALUS=1`, own golden `viewer_s5e_talus.png`)
  gates `talus_chunk` (relax + `flow_accumulate`) — adopted golden shows the bare-rock faces +
  the `flow_accumulate` scree channels. Both goldens **re-baselined on this VM → 0 px** (was 459 px
  for the model; the 800 px threshold is no longer load-bearing). *Gate met:* both targets green at
  0 px.

## Ordering / dependencies

```
V1 ─┐
V2 ─┼─► (usable interpreter viewer)        ← ship Phase A first; no toolchain risk
V3 ─┘
V0 ─► V0-file ─► V4 ─► V5                   ← native track; V4 needs V0 green
V6, V7, V8 independent (do alongside)
V2 strengthens V3 (cache makes per-frame bakes cheap); V4 multiplies everything by 22×.
```

**Recommended sequence:** V1 → V2 → V3 (smooth on interpret, today) ‖ V0 spike in parallel; if V0
unblocks, V4 lands the 22×; V5 is the long-tail. V6/V7/V8 fold in opportunistically.

## Open questions (resolve cheapest-first, blueprint-style)

1. **V0 unblock route** — is there a consumer-side way to register the graphics native cdylib for
   `--native`, or is it a genuine upstream gap? (The spike answers this; the projector proves the
   in-repo path works.)
2. **Steady-state vs whole-program native** — do we want `overland`/`chunk` extracted to native
   *libraries* (C71 model: interpret the GL script, dispatch hot calls to native libs — sidesteps
   the GL P269 entirely) instead of whole-program `--native`? Converges with EXTRACTION.md; heavier
   but more reusable. Decide after the V0 spike.
3. **Streaming K** — chunks baked per frame in V3 (1 keeps the loop smoothest; higher fills faster).
   Tune against the post-V4 native per-bake cost.

## Status

- **2026-06-16** — plan authored from the audit + measurements (interpreter-is-blocker proven,
  native 22× proven, native-GL P269 consumer gap identified, projector-native verified). Phase A is
  buildable now; Phase B gated on the V0 spike / upstream.
- **2026-06-16** — native **proven** against the coherent ../loft tree (V0: clean compile + 459 px
  render, ~8.5 s). Decision: **don't wire the transient ../loft dev-tree route into the Makefile** —
  the ../loft fixes (incl. the #396 registry-registration path) **PR into main soon**; we wait for
  that + `make install`. On install, `make viewer-release` auto-upgrades to native (it already
  probes `--check --native`), no crawler change. **When it lands, verify:** (1) `make viewer-release`
  picks native (no P269/`cfg_if`); (2) 459 px golden holds; (3) startup ~1.7 s; (4) if the
  fallback-optional flag shipped, gate with require-native (V5) to confirm no silent interpret drop.
- **2026-06-16** — upstream coordination: the user asked the ../loft agent to make the
  interpreter-fallback **optional + clearly-diagnosed**. Tracks as the Phase-B de-risker (the
  "require-native" gate). **Crawler action:** hand the loft agent the two concrete fallback repros —
  (1) the `--native` graphics `loft_gl_*` **P269** hard error, (2) the `use hex_grid` "libloft.rlib
  not found → interpreting it" **silent** fallback — so its new error text covers our cases.
