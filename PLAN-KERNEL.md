# PLAN-KERNEL.md — crawler on the games kernel (@PLN18 engine_host)

The user's direction (2026-06-12): **start using the new games kernel for crawler.**
The kernel (loft @PLN18 — `../loft/lib/engine_host` + in-binary natives, verified
present in the installed loft) is the engine host built for networked, live-editable
loft games: drain → tick → idle loop, three traffic classes (events / state-sync /
bulk), wire-schema-as-data, UDP fast path beside WS, live function reload
(`LOFT_LIVE_RELOAD=1`), whole-build swap under a running world. Effort: S/M/L.

## What adoption means for crawler (and the one mismatch)

crawler is today a **single-player windowed** game; `engine_host::run` is
**server-shaped** (listens on a ws port, never returns, no window pump inside) and
`run_client` is the connector half. So adoption is staged from the outside in —
consume what fits now, name the seam that doesn't:

- **Fits now**: the schema-table model (declarative lanes), the connector/client
  machinery for an MP slice, live-reload dev mode, and the kernel's loop
  *discipline* (budgeted drain, tick-due, idle backoff).
- **The mismatch, named**: the kernel's `kernel_idle` backoff is a PRIVATE native;
  the windowed host role (a kernel loop that also pumps a GL window) is
  feature-gated upstream but not surfaced as a loft API yet. Crawler's P1 idle skip
  busy-spins for exactly this reason (PLAN-RENDER P1 caveat). **The first flow-back
  ask is therefore one seam**: expose the idle/wait primitive (or the windowed host
  role) so a local windowed game can run the kernel loop. Until then K1 stays open.

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
- **K1 — the frame loop on the kernel (M, BLOCKED on the named seam)**: story.loft's
  loop adopts the kernel loop (drain → tick → idle) — completing PLAN-RENDER P1's
  Tier-0 win (idle CPU zero) and giving drift-free fixed ticks, which is ALSO the
  dt-quantization fix the MP/replay evaluation called for (the float-dt lockstep
  hazard). Ask upstream: expose idle/wait or the windowed host role.
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
- **K3 — live-reload dev mode (S, after K1)**: run crawler under the kernel with
  `LOFT_LIVE_RELOAD=1` — edit a bundle routine or a view fn while the game runs.
  Pairs with the debugger's in-game breakpoints (@PLN16 6c) — the loft-debug skill
  documents the agent surface.
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

## Order + status

| Step | Effort | Status |
|---|---|---|
| K0 consumable smoke | S | DONE 2026-06-12 (gate `[kernel]`) |
| K1 frame loop on the kernel | M | **DONE 2026-06-12** — story.loft runs on `engine_host::run_local`: `GameWorld` struct (the #314 pattern, closures capture one link + the immutables), `game_tick` = poll → input → fixed-quanta `sim_step` (FIXED_DT derived from TICK_US — the lockstep fix) → scene-key-gated draw. Measured: 59.97 Hz grid, ~150 µs body, idle = 1 frame drawn + kernel idles between ticks (the P1 busy-spin is GONE). Lesson: sub-16 ms synthetic key taps fall between 60 Hz polls (smoke uses keydown/sleep/keyup); input-as-events is the future fix |
| K2 observer slice | M | **DONE 2026-06-12** — crawler is the HOST (`run(STORY_PORT)`; `host_event` serves the intent log to joiners); every Sim mutation routes through `gameflow` intents (genesis/`flow_move`/`flow_action` + the S/T/A wire codec), logged + broadcast; `src/observe.loft` = the spectator (replica + the FULL renderer). Verified: replaytest (gate 39 — 92-step replica identity incl. the codec) AND the live two-process smoke (`tools/k2_smoke.sh`): host key == observer key after driven play. Bug found by the smoke and fixed at the chokepoint: the observer's genesis missed the class KIT → `flow_genesis` is now the ONE shared boot. Known quirks: observer redraw cadence batches under llvmpipe (eyeball on real display); idle host = zero wire traffic (the distance clock) |
| K3 live-reload dev mode | S | peeling the onion (2026-06-12): #346 (stdlib) + #347 (warnings) FIXED upstream same-day — story.loft now WATCHES; the next two layers found by the probe smoke and filed: loft#350 (the shadow session lacks registry/--lib resolution — 'Unknown library graphics' on any real consumer; sev:medium, no workaround) and loft#351 (only the ENTRY file is watched — view/bundle edits never noticed). `src/reloadprobe.loft` + the pixel smoke stand ready; rerun on the next fix |
| K4 MP lockstep | L | gated on a design pass (K1/K2 shipped the foundations) |
| K5 "next world" — in-game bundle reload | M | **v1 SHIPPED 2026-06-12** — press **N** in-game: `genbundles::regen_bundles()` re-scans the manifests in-process (drop-ins wired), the new seed rides `.story_next`, `stop()` exits, and `make play`'s restart loop relaunches — verified live: seed 1337 → N → RELAUNCH → seed 1338 with the registries regenerated. The scanner is `src/genbundles.loft` (module + program). The true in-process swap stays gated on loft#352 (local-role handover); the rebuild arc itself is verified (~280 ms to a cached artifact). Lesson (twice now): cold boot eats brief key presses — smokes press repeatedly|
