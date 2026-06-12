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
- **K2 — the observer slice (M)**: the first networked crawler — a second process
  connects via `run_client` and renders a read-only live view (spectator/map page);
  the deterministic Sim broadcasts input intents + seeds, the observer replays.
  Exercises lanes end-to-end with crawler data (events = messages, sync = player
  pose) without touching gameplay.
- **K3 — live-reload dev mode (S, after K1)**: run crawler under the kernel with
  `LOFT_LIVE_RELOAD=1` — edit a bundle routine or a view fn while the game runs.
  Pairs with the debugger's in-game breakpoints (@PLN16 6c) — the loft-debug skill
  documents the agent surface.
- **K4 — MP proper (L, gated on a design pass)**: deterministic lockstep over the
  kernel's classes (the loft-netgame-debug evaluation: ship input intents; the G4
  save format rides @PLN11 store serialization so one format serves save + replay +
  net sync). Needs the K1 fixed-tick quantization landed first.

## Order + status

| Step | Effort | Status |
|---|---|---|
| K0 consumable smoke | S | DONE 2026-06-12 (gate `[kernel]`) |
| K1 frame loop on the kernel | M | blocked: upstream seam (idle/windowed host role) |
| K2 observer slice | M | — |
| K3 live-reload dev mode | S | after K1 |
| K4 MP lockstep | L | gated on K1 + a design pass |
