# SCRIPTING.md — bundle scripting & the path to a mod platform

How crawler lifts its modding ceiling from *"set the flags the engine defined"* to *"ship
mechanics the engine never imagined"* — without breaking the determinism / multiplayer /
performance invariants. Companion to **BUNDLE.md** (the bundle architecture + standing check)
and **BUNDLE-MIGRATION.md** (classes/races/spells → bundles). Goal alignment: the
*everything-is-a-reusable-library* direction.

## The ceiling, stated exactly

**Mod expressiveness = the richness of the engine's vocabulary.** A bundle can *set* an
existing flag/primitive (`MF_GAZE`, `RF_FREE_ACTION`, `IF_KNOWN`) but cannot *invent* a new
mechanic; anything outside the vocabulary is an engine change. This doc dissolves most of that
ceiling.

## Diagnosis — scripting already exists; it is *starved*, not *absent*

Bundles already run real loft (the explorer's `potion_detect_monsters::apply`, the class
`activate` scripts). So the limit is not "can bundles run code." Measured against the code
(2026-06-10), routines are starved on three axes:

- **Narrow write surface** — **16** `Player` write-verbs vs **126** `sim_*` read accessors.
  The *read* half is already rich; *changing* the world is the bottleneck.
- **Almost nowhere to attach** — routines fire at exactly **2** hardcoded points (item-use via
  `itemfx::item_effect`, class-activate via generated `bundle_activate`). There is **no event
  system**; the only "trigger" is a hardcoded `infest_trigger == "boss_slain"` string check.
- **Fixed state** — a routine can only touch the engine's fixed `Sim` fields; a new mechanic
  cannot carry its own data.

Widen those three and the flag-enum ceiling largely dissolves: a flag stops being an enum the
engine knows and becomes a behavior a bundle ships.

## The five levers (priority order)

1. **Event/hook bus — the keystone.** The engine fires named events at each junction; bundles
   bind routines by id. This is what turns "set `MF_GAZE`" into "ship a gaze behavior."
   Surface: `on_tick · on_player_move · on_attack · on_hit · on_take_damage · on_kill ·
   on_death · on_pickup · on_use · on_cast · on_enter_level · on_spawn`. Today there is nowhere
   to bind this — it is the piece that does not exist.
2. **A general, deterministic modding API (~40 primitives).** Promote the 16 verbs into
   composable ones: `modify_hp/sp/stat`, `deal_damage(target, n, type)`, `set_status(kind,
   dur)`, `teleport`, `spawn(key, q, r)`, `transform(target, key)`, `move_force`,
   `emit_message`, `play_effect`, `query_*`, and a **seeded RNG handle**. ~40 general verbs
   cover a combinatorial space far larger than 40 features.
3. **Flags-as-behaviors.** Keep a few perf-hot flags hardcoded; let the long tail of
   `MF_*/RF_*/IF_*` become `(event → routine)` bindings the bundle ships. A modder writes new
   abilities the same way the engine writes built-ins — no engine flag required.
4. **Extensible state.** A per-entity property bag (key→int/text) so new mechanics carry their
   own data, plus **status-as-data** (kind + duration + a per-tick routine) instead of the
   fixed `ST_*` enum.
5. **Runtime-loaded bundles, via loft's dynamic compilation.** loft is built for exactly this,
   on a **three-tier ladder** so a mod is *portable everywhere* yet *fast where it matters*,
   with no friction:
   - **Interpret** — the universal fallback (`loft --interpret`): a dropped-in bundle set runs
     anywhere, instantly, no build step. Best for assembling and iterating a loadout.
   - **Auto optimized-WASM** — when a compiler is present on the host (e.g. a server), loft
     compiles and loads optimized WASM automatically.
   - **Local opt-in compile** — once a local player has slotted in their chosen set of bundles,
     they can **opt-in to compile the game** (engine + that bundle set) into an optimized build
     — bake a settled loadout to full speed.
   This is the path from *developer* modding to *end-user* modding, and the ladder removes the
   usual "but interpreted hot paths are slow" objection: iterate interpreted, then auto- or
   opt-in compile for speed.

## Non-negotiable constraints (the acceptance fences)

Power must be fenced by the invariants the project already holds:

- **Determinism** — scripts get the engine's **seeded RNG only**; no wall-clock, no ambient
  randomness. Required by the distance-clock, the MP-shaped tick, replay, and the headless gate.
- **MP-safe clock** — the API must never let a script make `sim_tick` depend on one player's
  volition (the invariant that unlocked multiplayer).
- **Performance** — dispatch only events that have subscribers; budget per-tick routine work.
  The core loop, FOV, and generation stay compiled/hot; scripts ride *events*, they do not
  replace the loop. Runtime-loaded routines are covered by loft's **dynamic compilation**
  (interpret as fallback, auto-compile to optimized WASM where a compiler is on the host), so
  "interpreted hot paths are slow" is not the blocker it would normally be.
- **Safety / sandbox** — compiled-in routines have full access (fine for trusted/co-op). An
  untrusted public ecosystem needs a capability-limited API (no FS/net) or the interpreted
  sandbox (lever 5).
- **Versioned API** — the script surface is a contract; pair with a bundle **schema/version**
  (loft silently defaults missing struct fields, so unversioned changes break mods *quietly*).

## What stays engine-side (by design)

The **core sim loop, energy/clock model, FOV, and the generation algorithm** (performance +
determinism + MP), plus the **primitive set** itself — new primitives remain engine work, but
~40 general ones make that rare.

---

## Staged epic (checkable — each stage has a proof move + a gate test)

### Stage 1 — Event/hook bus *(the keystone)*
- [ ] Define the event surface + an `EventCtx` (the deterministic, MP-safe handle a routine
      receives: actor/target ids, seeded RNG, the API).
- [ ] Dispatch only fires events with ≥1 subscriber (perf); routines bound by id from bundles.
- [ ] `gen_bundles.loft` scans bundle event-bindings → generated subscriber registry (no engine
      reference to a specific bundle).
- [ ] **Proof:** a content-only bundle adds a monster that does something new `on_hit` (e.g.
      steals gold) with zero `src/` edits. `eventtest.loft` in the gate.

### Stage 2 — General deterministic API
- [ ] Generalize the 16 `Player` verbs into the ~40-primitive surface above; document it as the
      modding API (the contract).
- [ ] Seeded RNG handle exposed to routines; no `Math.random`/wall-clock reachable.
- [ ] **Proof:** rewrite an existing effect (e.g. phase-door) purely on the general API.
      `apitest.loft` asserts determinism (same seed → same outcome).

### Stage 3 — Flags-as-behaviors
- [ ] Re-express `MF_GAZE` and `RF_FREE_ACTION` as `(event → routine)` bindings shipped in a
      bundle; keep a short hardcoded perf-hot list.
- [ ] **Proof:** the gaze + free-action behave identically via routines (`specialtest` still
      green); a *new* monster ability ships with no engine flag.

### Stage 4 — Extensible state
- [ ] Per-entity property bag (key→int/text) on monsters/items/player; carried across
      descend/respawn like the other state.
- [ ] Status-as-data: `(kind, duration, per-tick routine)` replacing the fixed `ST_*` enum
      (slow/stun/poison/ward become instances).
- [ ] **Proof:** a bundle adds a build-up mechanic ("corruption rises, erupts at 100") entirely
      bundle-side. `statetest.loft` in the gate.

### Stage 5 — Runtime-loaded, sandboxed bundles (via loft dynamic compilation)
- [ ] Engine loads bundle routines at startup; loft **interprets as fallback and auto-loads
      optimized WASM when a compiler is on the host** — no manual rebuild to add a mod.
- [ ] **Local opt-in compile** — a player who has slotted in a bundle set can compile that
      engine+bundles combination into an optimized build (settled loadout → full speed).
- [ ] Capability-limited API surface for untrusted bundles (no FS/net); trusted bundles opt
      into more.
- [ ] Bundle **schema/version** gate: mismatched bundles are rejected loudly, not defaulted
      silently.
- [ ] **Proof:** drop a mod folder into an installed build and play it without recompiling —
      runs interpreted with no compiler, auto-optimizes to WASM where one exists, and a player
      can opt-in to compile their assembled set to full speed.

## Verdict

The limit is mitigable, and cheaply — the seeds exist (routine pool, a 16-verb API, 126 read
accessors, a working bundle-routine call). The one missing keystone is the **event bus**; add
that plus a broadened deterministic API and bundles cross from *recombining* the engine's
vocabulary to *extending* it, while the determinism / MP / performance fences keep it honest.
The mod-platform goal — runtime-loaded, sandboxed bundles — is closer than "reach" implies:
loft's **dynamic compilation** gives runtime-loaded mods data-like distribution *without* the
interpreted-perf penalty, on a three-tier ladder — **interpret** anywhere, **auto optimized-WASM**
where a compiler is on the host, and **local opt-in compile** of a settled bundle set to full
speed. That is what turns crawler from content-moddable into a genuine **mod platform**, and it
is in range precisely because the toolchain is built for exactly this — assemble freely
interpreted, then compile when you've chosen your set.
