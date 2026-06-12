# PLAN-KERNEL.md — crawler on the games kernel (@PLN18 engine_host)

The user's direction (2026-06-12): **start using the new games kernel for crawler.**
The kernel (loft @PLN18 — `../loft/lib/engine_host` + in-binary natives, verified
present in the installed loft) is the engine host built for networked, live-editable
loft games: drain → tick → idle loop, three traffic classes (events / state-sync /
bulk), wire-schema-as-data, UDP fast path beside WS, live function reload
(`LOFT_LIVE_RELOAD=1`), whole-build swap under a running world. Effort: S/M/L.

## What adoption means for crawler

(The original "one mismatch" — no windowed host role — was resolved upstream the
same day it was named: loft#343 → `run_local`, then the K2 trio made the windowed
LISTENER viable too.) Today crawler IS the kernel's windowed host: `story.loft`
runs `engine_host::run(STORY_PORT, …)` — drift-free 60 Hz ticks, idle backoff,
the debug/swap endpoints — serving observers while playing. Adoption was staged
outside-in exactly as planned; the staging record lives in the Steps + status
table below.

## The interleave (the K1 loop shape, pinned 2026-06-12)

The kernel loop and crawler's loop map one-to-one — K1 is a restructuring, not a
rewrite:

| Kernel slot | Crawler occupant |
|---|---|
| `pump()` | `gl_poll_events()` + key sampling (the window IS the socket; input = the events class, local transport) |
| `on_event` | edge-triggered actions — grab/wait/page toggles/quick-slots (today's `*_was` flags dissolve into events) |
| `on_tick` | `sim_step` at FIXED quanta (held keys sampled per tick — the float-dt lockstep fix), then the scene-key check → `view_draw` + swap only on change |
| `idle(2ms)` | replaces P1's busy-spin — fires when no input, no tick due, nothing drawn |

Two load-bearing observations: (1) **`tick_due` and the scene key are the same
predicate on two axes** — time-driven sim work vs state-driven render work; the
kernel's "did any work happen" counter treats a draw as work, so P1's mechanism
slots in unchanged, and everything P0–P3 built (view_draw, VBOs, probes) stays a
tick-side consumer. (2) **Two clocks coexist**: ticks on the drift-free grid,
vsync only on frames that draw; the grid absorbs render jitter (late ticks fire
immediately), worst case = standard fixed-timestep catch-up. K2/K4 then add real
sockets to the SAME pump — remote inputs as events applied at ticks, poses
broadcast after on_tick, the renderer a pure function of Sim behind the scene key.

## Frame rates (evaluated 2026-06-12)

K1 separates the three rates that used to be one tangle: the sim quantum
(`FIXED_DT`, DERIVED from `TICK_US` — one source of truth), the render cadence
(the scene key — draw only on change), and display sync (vsync blocks only
frames that draw). Against the modern options:

- **60 Hz fixed (default)**: measured 59.97 Hz grid, ~150 µs tick body — huge
  headroom even interpreted.
- **120/144/240 fixed**: ONE constant (`TICK_US`); pacing identical (speeds are
  per-second). The constraint is DETERMINISM, not perf: a 60 Hz recording does
  not replay at 144 — the rate rides the replay header / MP server config,
  never re-derived.
- **VRR / adaptive (G-Sync, FreeSync, LTPO)**: render-on-demand + vsync-on-draw
  is exactly the client VRR wants — irregular cadence, panel adapts. The idle
  skip doubles as the modern-display answer.
- **Render > sim (144 Hz panel, 60 Hz sim)**: the one unsupported option —
  the kernel has ONE grid (one tick = one frame on a GL host). The seam if
  wanted: lerp the CAMERA (px/py/heading) between the last two sim states
  under a faster frame callback (`frame_due` beside `tick_due` — an
  engine_host ask) + an alpha into `world_cam_mat4`. Parked: enemies are
  hex-locked, only the camera moves continuously — genre says low priority.
- **Browser**: the upstream browser kernel frames on rAF already;
  the logical grid rides on top — same one-constant model.
- **Input**: polled at tick rate (≤1 tick latency — fine; sub-16 ms synthetic
  taps ARE missed, the smoke proved it with xdotool). The structural upgrade
  is the kernel events class (input-as-events), already named in the
  interleave table.

## Steps

- **K0 — consumable smoke (S). ✅ DONE 2026-06-12**: `src/kerneltest.loft` —
  `use engine_host` resolves via `--lib ../loft/lib/`, the in-binary natives answer
  (`default_host()`), the wire-schema table accepts lane declarations pre-listen,
  client accessors are sane with no socket. Gate step `[kernel]` (skips where the
  sibling checkout is absent — the dep stays opt-in until registry publication).
- **K1 — the frame loop on the kernel (M, DONE — see the status table)**: story's
  loop became the kernel loop (drain → tick → idle): P1's Tier-0 win completed AND
  the float-dt lockstep hazard fixed (fixed quanta). Since K2 the role is `run`
  (the windowed HOST), not `run_local`.
- **K2 — the observer slice (M, UNBLOCKED 2026-06-12)**: the first networked
  crawler — a second process connects via `run_client` and renders a read-only
  live view (spectator/map page); the deterministic Sim broadcasts input intents
  + seeds, the observer replays. Exercises lanes end-to-end with crawler data
  (events = messages, sync = player pose) without touching gameplay. Upstream
  `5f517c01` shipped the trio this needs: `post()` (local input as events-class
  messages, cid -1 — ALSO the structural fix for tick-rate polling losing
  sub-16 ms taps; an optional K1 refinement), listener `stop()`, and the
  listener frame yield — so crawler-as-HOST (the player's windowed game runs
  `run()`) is the natural shape.
- **K3 — live-reload dev mode (S; the onion is in the status table)**: edit a
  bundle routine or a view fn while the game runs. Two upstream layers fixed
  same-day (#346/#347); two remain filed (#350 lib resolution, #351 module
  watching). `src/reloadprobe.loft` + the pixel smoke stand ready.
- **K4 — MP proper (L, gated on a design pass)**: deterministic lockstep over the
  kernel's classes (the loft-netgame-debug evaluation: ship input intents; the G4
  save format rides @PLN11 store serialization so one format serves save + replay +
  net sync). Needs the K1 fixed-tick quantization landed first.

## Boot responsiveness (evaluated 2026-06-12 — a FLAW, not unavoidable)

The cold-boot input gap decomposes into two fixable flaws (boot LATENCY is
unavoidable; UNRESPONSIVENESS is not):

1. **Polled input has no memory** — `gl_key_pressed` reads current state; any
   press-and-release inside a gap vanishes (boot = the biggest gap; the 60 Hz
   tick blind spot = the same flaw smaller). OWNERSHIP SPLIT (2026-06-12): the
   transport (`post()`/events) is engine work, SHIPPED; the missing piece is the
   window-side EVENT SOURCE — graphics exposes only polled state, no key-event
   queue — filed as loft#353 (gl_key_events(), or the local role pumping +
   posting natively). Crawler-side post()-from-polls would only dissolve the
   edge flags, not the blind spots.
2. **The window never pumps during boot** — `gl_create_window` then 4-5
   interpreted seconds with zero `gl_poll_events`: a frozen black window real
   compositors flag "not responding". Crawler-side sequencing bug. Fix (S):
   a loading frame + `gl_poll_events()` between boot phases (gen → walls →
   HUD → VBOs). The native tier later shrinks the latency itself, but any
   unpumped gap reproduces the flaw at smaller scale.

The smokes' repeated-press workaround treats symptom 1 for automation and stays
valid regardless (synthetic taps are sub-16 ms even against a healthy loop).

**Start-time budget (measured 2026-06-12, interpreted on the dev VM):** parse
522 ms · genesis (depth-0 wilderness) 4766 ms · walls+meshes 794 ms · HUD/GL
~1 s. End-user tiers drop the dominant costs: a NATIVE binary cold-starts est.
0.3–0.7 s (parse gone, genesis ÷30–100); a WASM page is download-dominated,
est. 1.5–4 s to playable, <1 s cached (re-verify `make game` — the 2026-06-11
codegen breakage may be fixed by #341). Levers when needed: a SEED-KEYED world
cache (genesis is deterministic; @PLN11 serialization = the same machinery G4
saves want → ~100 ms warm starts every tier), lazy genesis (hex_terrain's
window-independence invariant exists for this), and the shipped boot pump for
whatever remains. Multipliers estimated, not yet measured on this workload — the env class is
CLEARED (matched toolchain via the repo binary) and the remaining blocker is a
REAL codegen bug: loft#354 (block-split variable loss, 51 errors on sim; the
same family that breaks make game). Rerun the boot probe natively when it lands.

## Shipping distance (evaluated 2026-06-12)

Native builds for Linux/macOS/Windows are NOT a port problem: the graphics
native crate sits on glutin/winit 0.30 (all three platforms first-class), the
shaders are #version 330 core (inside macOS's GL 4.1 ceiling), and upstream
already runs Windows CI. The distance = one bug + release engineering:

1. **loft#354** (block-split codegen) gates EVERY native build — filed with the
   recipe; rerun the boot probe + `make game` when it lands.
2. Program-relative asset paths (the in-flight `fix-255-program-relative-font`
   upstream branch) — a shipped binary must find sprites/font.
3. `engine_host` registry publication (no sibling-checkout dep in a release).
4. Packaging: Linux tarball/AppImage days after #354; Windows = a focused week
   (toolchain-on-platform discipline; SO_REUSEPORT is swap-only, not on the
   single-player path); macOS = a focused week, mostly signing/notarization.
5. crawler-side: the N-key restart needs a 3-line relauncher (or loft#352);
   save-dir conventions wait for G4.

Estimate: #354 + 2–4 focused weeks to a presentable Linux build; Windows/macOS
each ~a week behind, parallelizable. **Separate per-platform builds are the
accepted model** (user, 2026-06-12) — and deliberately so: one codebase + one
kernel producing four artifacts (three natives + the wasm page) IS the
cross-platform statement; a release CI matrix is the registry flow's
reproducible-build pattern one level up.

## Order + status

| Step | Effort | Status |
|---|---|---|
| K0 consumable smoke | S | DONE 2026-06-12 (gate `[kernel]`) |
| K1 frame loop on the kernel | M | **DONE 2026-06-12** — story.loft runs on `engine_host::run_local`: `GameWorld` struct (the #314 pattern, closures capture one link + the immutables), `game_tick` = poll → input → fixed-quanta `sim_step` (FIXED_DT derived from TICK_US — the lockstep fix) → scene-key-gated draw. Measured: 59.97 Hz grid, ~150 µs body, idle = 1 frame drawn + kernel idles between ticks (the P1 busy-spin is GONE). Lesson: sub-16 ms synthetic key taps fall between 60 Hz polls (smoke uses keydown/sleep/keyup); input-as-events is the future fix |
| K2 observer slice | M | **DONE 2026-06-12** — crawler is the HOST (`run(STORY_PORT)`; `host_event` serves the intent log to joiners); every Sim mutation routes through `gameflow` intents (genesis/`flow_move`/`flow_action` + the S/T/A wire codec), logged + broadcast; `src/observe.loft` = the spectator (replica + the FULL renderer). Verified: replaytest (gate 39 — 92-step replica identity incl. the codec) AND the live two-process smoke (`tools/k2_smoke.sh`): host key == observer key after driven play. Bug found by the smoke and fixed at the chokepoint: the observer's genesis missed the class KIT → `flow_genesis` is now the ONE shared boot. Known quirks: observer redraw cadence batches under llvmpipe (eyeball on real display); idle host = zero wire traffic (the distance clock) |
| K3 live-reload dev mode | S | peeling the onion (2026-06-12): #346 (stdlib) + #347 (warnings) FIXED upstream same-day — story.loft now WATCHES; the next two layers found by the probe smoke and filed: loft#350 (the shadow session lacks registry/--lib resolution — 'Unknown library graphics' on any real consumer; sev:medium, no workaround) and loft#351 (only the ENTRY file is watched — view/bundle edits never noticed). `src/reloadprobe.loft` + the pixel smoke stand ready; rerun on the next fix |
| K4 MP lockstep | L | gated on a design pass (K1/K2 shipped the foundations) |
| K5 "next world" — in-game bundle reload | M | **v1 SHIPPED 2026-06-12** — press **N** in-game: `genbundles::regen_bundles()` re-scans the manifests in-process (drop-ins wired), the new seed rides `.story_next`, `stop()` exits, and `make play`'s restart loop relaunches — verified live: seed 1337 → N → RELAUNCH → seed 1338 with the registries regenerated. The scanner is `src/genbundles.loft` (module + program). The true in-process swap stays gated on loft#352 (local-role handover); the rebuild arc itself is verified (~280 ms to a cached artifact). Lesson (twice now): cold boot eats brief key presses — smokes press repeatedly|
