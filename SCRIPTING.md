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

## What rides on the bus: ELIGIBILITY, not scripts

The diagnosis above says there is no event system. It does not say what the events should
*carry*, and that is the more consequential question — a bus carrying scripted quest chains
buys modding power and spends the design. The answer comes from the sibling project
(**`../crew_punk/BLOCKS.md` § The campaign is a trigger system, not a plot**, and
`SESSIONS.md` §3), adopted here:

> **Nothing is scheduled. Everything is *eligible*.** A piece of content does not happen at
> depth nine; it happens **when its conditions are true** — which may be depth nine, depth
> thirty, or never. *Nobody decides what happens next; the system evaluates what has become
> possible.*

**The load-bearing property**, and the reason it stays coherent as content accumulates:

| the world holds | content holds |
|---|---|
| **what happened** — the past, entirely visible | **conditions** — never a schedule |

The engine joins them at play time **and discards the join**. Nothing stores what a past
event *enabled*; eligibility is recomputed, never bookkept.

**Four rules this imposes, and each one is already crawler's philosophy elsewhere:**

1. **A trigger tests what HAPPENED — never a stat, level or rating.** *"A gate that tests
   capability is a locked door wearing a skill check."* §3a pillar 2 already forbids
   stat-gated *difficulty*; this is the same rule applied to *content*.
2. **A trigger may only test a named world fact.** If content needs a condition the world does
   not record, either the world gains that fact **or the content is testing something
   imaginary.** So the trigger vocabulary is explicit and **small** — small not for memory
   (the machine reads it) but so content stays authorable, testable, and honest.
3. **No markers.** *"A trigger that tells you it exists is a quest marker"* — the Zelda
   exploration pillar in mechanical form.
4. **Eligible ≠ due.** Flooding is the failure mode: when many things qualify at once, one
   fires and **the rest stay eligible.** Select and constrain, never synthesise.

**Depth arrives as a by-product of history.** Early triggers are simple because the world has
no past yet; late ones can be precise — *you cleared that shrine, you carried the thing out,
and the roster remembers*. Nothing about that curve needs designing.

**And the same mechanism runs at three scales** — run, level, moment — which is what makes it
one system instead of three: a wandering line from an NPC and a run's late reveal are the same
object, both waiting on conditions, both simply missed if the conditions never arrive.

### Why this lets creators author RICHLY — and still dodges the AAA trap

**The trap is not authored content. It is *scheduled* authored content** (user, 2026-07-22).
Big studios cut simulation because a simulated world breaks a scripted one: a quest needs that
NPC alive, in that room, at that hour, and an economy that lets him move — or starve — breaks
it. Oblivion's Radiant AI shipped neutered for exactly this reason. So the studio keeps the
script and guts the simulation, and everyone gets a world that looks alive and is not.

**Remove the schedule and the conflict disappears.** A condition-gated scene cannot be broken
by simulation, because nothing was ever promised: if the world stops making it true, it simply
does not fire, and no repair is owed. Which means a creator can write the most specific,
richest, most hand-made thing they like — *the feeling lives in the whole authored scene* — and
ship it into a fully simulated world without the two fighting.

So both units ship, and they are different sizes on purpose:

| unit | size | why |
|---|---|---|
| **the authored scene** | whole | that is where the feeling is — do not dissolve it into parts |
| **the brick** | smaller than a scene, portable | so one good thing produces many usable ones |

**That is the whole prize:** rich authored content *and* deep simulation, which the industry
treats as a trade-off because it only ever tried to have both **on a schedule**.

### The price of admission: the Dark Souls ethos

**Most players will never see most of it, and that has to be fine** (user, 2026-07-22). A
trigger system whose conditions may never arrive *guarantees* missed content — that is not a
side effect to mitigate, it is the mechanism working.

**This is the part a studio structurally cannot adopt**, and the reason is a metric: AAA
measures **content utilisation** and cuts what too few players reach. Optimise for *everyone
sees everything* and you are forced back onto a schedule — and the schedule is what killed the
simulation. FromSoftware's real radicalism was never difficulty; it was building Ash Lake, the
silent questline failures, and lore almost nobody reads, and **not counting that as waste**.

**What it buys, and neither is designed in:**

- **Replayability without content cost.** A large eligible pool plus conditions means each run
  surfaces a different subset. Nothing had to be authored *as* a variant.
- **Discovery becomes social.** Players tell each other what they found. For a small team with
  no marketing budget, that is the distribution channel — and it only exists if finding
  something is *possible to miss*.

> **The failure mode, and the rule that prevents it.** Eligibility layered over a complete
> spine reads as **depth**; eligibility *as* the spine reads as **emptiness** — a game where
> most players find little and conclude there is little. Dark Souls survives it because the
> critical path is dense and the missable content sits on top.
>
> **So: the core loop must be whole on its own, and everything eligible is layered above it.**
> For crawler that spine is M-Core (explore · fight · gear · level · respawn), which is exactly
> why *"a functional game first"* is not just sequencing — it is the precondition that makes
> missable content readable as generosity rather than as absence.

**The seam stays where BUNDLE.md put it:** the *evaluator* is engine mechanism; the *eligible
content and its conditions* are bundle content. This replaces today's single hardcoded
`infest_trigger == "boss_slain"` string check with the general form.

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

## Plan — run bundles under @PLN86 sandboxing (the crawler dogfood)

loft's **@PLN86 sandbox** (loft2 branch `tuxedo-work`, v1 safety model COMPLETE, landing via a
PR soon) is the concrete mechanism for Stage 5's "capability-limited API surface". It is built
*for crawler to dogfood*: the @PLN86 README hands the consuming role to "the crawler agent" —
crawler switches a `[sandbox]` policy on over its bundle surface, finds where it is **too tight**
to express a mod, and **adversarially tries to break out**; findings route back as loft language
work. This is the execution plan for that.

### Is this worth doing? — evaluation for games

**Verdict: yes, and games are arguably its best domain.** Games are the canonical "a stranger
ships code that runs on my machine" case, they are perf-critical, and many are deterministic /
multiplayer — and this sandbox is unusually well-matched to all three. The value hinges on one
tunable (expressiveness vs. strictness) and one precondition (a real mod ecosystem + the loft
runtime); it is a strong feature for a specific, valuable niche, not a universal win.

**What makes it better than what games ship today** — not "a sandbox" (everyone has one) but
*which*:
- **Same-process, full-speed.** Sandboxed content runs in-process at native `DbRef` speed, host
  code unrestricted. Almost every game sandbox today (a separate Lua/JS/WASM VM with marshalling)
  pays a boundary tax that is the reason mods stay shallow. Removing it is the standout property.
- **Load-time admission, not runtime trapping.** A mod is *proven* safe at load — no per-call
  permission checks in the hot loop, and you know before running whether it is safe.
- **Totality — can't hang, can't fault, bounded cost.** Kills the two worst modding-support
  nightmares ("a mod froze my game", "a mod crashed the client") by construction.
- **Determinism preserved by construction.** The `clock`/`rng` fences mean untrusted content
  *cannot* desync a lockstep multiplayer game — a mostly-unsolved problem (it is *why* RTS/lockstep
  titles usually ban code mods). Close to novel.

The closest real comparables — Roblox's Luau (years of work to lock Lua down for UGC) and
Factorio's restricted-Lua API — are hand-built, game-specific versions of exactly this; a
language-level, capability-based, load-proven, same-process sandbox is a stronger, more general
form. The common bad path — native/Java mods (Skyrim, Minecraft) = full RCE — bites in practice
(the 2023 "fractureiser" Minecraft-mod malware; data-stealing WoW addons).

**An underrated second use:** even with *no* public modding, "this content module provably can't
crash, hang, or desync the engine" is valuable for **large teams** (a designer's script can't take
down the build) and **live-ops hot-loading** (with loft dynamic compilation: ship content that
can't break the running game).

**The honest costs / risks:**
- **The expressiveness ceiling is the decisive risk.** v1 totality is acyclic (no recursion,
  bounded loops). Lua's *looseness* is why it won modding — a too-strict sandbox doesn't get safer
  mods, it gets *no* mods (or modders routing around it into an unsafe tier). This is make-or-break,
  and it is exactly what Step 5's dogfood is built to find — a point in the feature's favour
  (validated against a real consumer, not designed in a vacuum).
- **The fences cut off whole categories** (no I/O / clock ⇒ no live-API / own-timing mods); those
  need a separate trusted tier — the sandbox is the wrong tool for them, by design.
- **Host-side burden:** the engine must carve + capability-tag its API (the design below), and
  mis-tuned granularity is unsafe (too coarse) or annoying (too fine).
- **Preconditions:** value ≈ (untrusted-content surface) × (perf sensitivity), and it applies only
  to engines on the loft runtime — a language feature, not drop-in middleware.

**For crawler specifically: near-ideal fit** — the whole premise is "a stranger drops a bundle in
and plays", it is deterministic + MP-aspirational + loft-native, and its current bundles admit
almost trivially (tiny call surface, no loops, no raw writes — verified). About as clean a dogfood
target as exists, which is why @PLN86 routes its consumer role here.

**Bottom line:** genuinely useful and differentiated where it counts (same-process speed; the
determinism / no-hang guarantees the mainstream Lua/Workshop/native-mod paths don't give). What
decides *adoption* over mere *soundness* is whether loft can relax totality to "bounded but
expressive" without losing the guarantees. If it can, it is a real competitive advantage for any
moddable, deterministic, perf-sensitive game; if it stays too strict, it is a correct safety
feature for a mod ecosystem that never forms.

**The model (from loft2 `doc/claude/SANDBOX.md` + `plans/86-sandbox-subset-flag/README.md`).** The
HOST designates subsets (a script can't opt itself out); designated defs run under prove-it-safe-
at-load admission — **deny-by-default**, **interpret-only** (refuses `--native`), **total**
(acyclic — v1 rejects recursion), **no raw writes to host data**, **no fs/net/env/FFI**, with a
space/complexity budget — all checked at load via `Parser::sandbox_admission_errors`. Same process,
shares the store at full `DbRef` speed. Config in `loft.toml`: `[sandbox]` maps file/function globs
to a `[profile.<name>]`; a reachable trusted symbol admits iff its **library ∈ `allow_libs`**
(wholesale) OR its declared `group#right` capability ∈ `allow` — else a compile error naming the
offender. Library-first: vet a whole module in as a unit; use capabilities only to split one.

**Why crawler is a clean fit (verified 2026-06-25).** Bundles are exactly the "stranger drops it
in" surface BUNDLE.md describes — the untrusted code the sandbox is for. And today's bundle
routines admit almost trivially: the **entire engine call-surface from `bundles/*/*.loft` is
`sim_log`, `sim_bolt`, `sim_blink`** (3 symbols); **no `while` loops** (totality-clean under v1's
acyclic rule); **no raw `s.field =`/`p.field =` host writes** (all mutation goes through kernel
APIs). So v1 admission should pass with a tiny allow-list — the dogfood starts from green, then
probes the edges.

### Gating dependency
The sandbox lives in **loft2**, not the installed loft (which tracks the `../loft` @PLN85 line).
Steps 1–4 are buildable now (inventory + policy authoring); **run-verification (5–6) waits on the
loft2 sandbox PR landing + `make install` from loft2**. Note the sandbox forces **interpret-only**
— already crawler's `make test` mode — so it sidesteps the native-cdylib path (loft#460); but the
gate still needs the store-lifetime SIGSEGV (loft#462) resolved to reach `questtest`.

### Steps (each a verifiable move)
1. [ ] **Pin the allow-list (the load-bearing invariant).** Enumerate EVERY engine symbol the
   bundle-**reachable** set calls — across all routine kinds (spell/item effects, placement,
   stencils, quest hooks), not just today's three. Classify each: pure-query · world-mutate ·
   log/UI. *This set IS the capability surface.* **Verify:** the admission walk reports exactly
   these as the trusted leaves (`loft introspect` / the admission error list names no surprises).
2. [ ] **Designate the subset.** `loft.toml` `[sandbox]` glob over `bundles/**/*.loft` →
   `profile = "bundle"`. **Pin the one design risk first:** `genbundles` generates registries
   (`spell_defs_gen`, `rooms_gen`, …) that *embed/dispatch* bundle routines — confirm the glob
   tags the defs where they actually compile (bundle source vs the generated dispatch). Verify the
   intended defs are tagged before writing the profile; if the indirection drops the tag, designate
   the generated files (or add `#sandbox("bundle")` at the routine sites).
3. [ ] **Define `[profile.bundle]`.** `native_ffi = false`; `allow_libs` = the bundle-facing kernel
   API module(s) wholesale (library-first), nothing else. Deny fs/net/env/raw-store/other-bundle
   internals by omission. **Verify:** a bundle calling only allow-listed APIs admits; a probe
   bundle calling `files`/`env` is rejected at load naming the group.
4. [ ] **Declare crawler's OWN bundle-API capabilities** (§3 "projects declare+link their own
   code") — only where wholesale is too broad. Carve the seam: e.g. `capability world` with
   `world#mutate` on `sim_bolt`/`sim_blink`, `log#write` on `sim_log`, so a bundle's grant is
   explicit + minimal. Start wholesale (step 3), refine to caps as the dogfood shows what to gate.
5. [ ] **Adversarial dogfood (the @PLN86 ask).** (a) *Too-tight:* find a legitimate mod the
   allow-list or totality rejects — a routine needing an un-allowed API, or the loops/recursion a
   richer mod wants but v1's acyclic rule bans — and route it back to @PLN86 as language work.
   (b) *Break-out:* author a hostile bundle that tries to read a file, reach env/net, call native
   FFI, raw-mutate host state, reach another bundle's data, or infinite-loop / deep-recurse / blow
   the space budget — confirm each is **rejected at load or bounded**. Report both streams upstream.
6. [ ] **Make it the standing guarantee.** Once the policy holds and break-out is clean, commit the
   `[sandbox]` policy into `loft.toml` so `make test`/`make play` always run bundles sandboxed —
   turning BUNDLE.md's "a stranger drops a bundle in and plays" from aspiration into an enforced
   property. Update BUNDLE.md's **standing check** ("bundles run sandboxed") and this Stage 5.

### Known tensions to carry
- **Totality v1 = acyclic only.** Fine today (no bundle loops/recursion), but the richer-mod
  ambition above (event handlers, general API) will want bounded loops — that relaxation is exactly
  the kind of dogfood finding @PLN86 wants pushed back.
- **The capability surface grows with the mod vocabulary.** As Stages 1–4 broaden the bundle API,
  each new bundle-callable verb is a new allow-list/capability decision — keep the seam's
  capability declarations co-located with the API (BUNDLE.md standing check territory).

### The bundle API surface — the allow-list, by capability (Step 1 design)

The detailed design of *what a bundle is allowed to call*. It has **two faces**: a **data-
definition** API (pure — bundles return typed records; no host effect, always admits) and a
**behavior** API (the functions routines call to read/affect the world — the part the sandbox
gates). Capability names below are the proposed `group#right` links crawler would **declare on its
own seam** (§3 of the plan); the engine ships them, a `[profile.bundle]` grants a subset.

**A. Data-definition API (pure — no capability).** A bundle provides content as `pub fn`
routines returning typed vectors; the scanner (`genbundles`) merges them. These call no engine
verbs — they construct records and return them, which the sandbox treats as a pure leaf. The
record **types** and the **constants** their fields use are a wholesale-allowed, declaration-only
module (no behavior to gate):

| Provider routine | Returns | Notes |
|---|---|---|
| `item_defs()` | `vector<ItemDef>` | items: category, effect-id, flags (`IF_*`) |
| `monster_defs()` | `vector<MonsterDef>` | stats, `MF_*`/`RF_*` flags, tags, glyph/colour |
| `<x>_class_defs()` / `<x>_race_defs()` | `vector<ClassDef>`/`vector<RaceDef>` | stat blocks, hit-die, skills, realm |
| `<x>_spells_defs()` | `vector<SpellDef>` | name, SP cost, **effect-id** → a routine (face B) |
| `room_stencils()` | `vector<RoomStencil>` | room paint masks |
| `place_rules()` | `Placement` | budget / weighting / start-safe |
| (world) | `RoomDef` + `room_connect_*` | `world`-kind registry |

Allow wholesale: a `kerneldefs` surface = the `*Def`/`RoomStencil`/`Placement`/`RoomDef` **types** +
the `MF_*`/`RF_*`/`IF_*`/`TAG_*`/`K_*` (tile-kind) **constants**. Declaration-only ⇒ no risk.

**B. Behavior API (capability-gated).** Behavior routines receive a fixed **dispatch context** and
return a result the engine acts on — they never hold the loop:

| Routine kind | Signature | Where the generator finds it | Returns |
|---|---|---|---|
| class/race onboarding | `activate(s: &Sim, p: Player)` | the bundle's `entry` | — |
| spell effect | `fx_<effect_id>(s: &Sim, p: Player, power: integer) -> boolean` | scanned in the `spells` module | did-fire |
| **item effect** | `apply(s: &Sim, p: Player)` | **`bundles/<b>/items/<item_key>.loft` — the FILE NAME is the key** | — (dispatch reports fired) |
| quest hook | `on_<event>(s: &Sim, …)` | — | per-event |

⚠ **The two effect kinds are found differently, and the difference is not cosmetic.** A spell's
routine is keyed by an **effect id** the def names (`s_effect`), so several spells may share one
routine. An item's is keyed by the **item key itself**, taken from the file name — because
`ItemDef` has no effect-id field and adding one would mean touching ~88 struct literals. One
file per usable item is the cheaper spelling of the same seam, and it makes def-and-routine
drift impossible. Both emit a generated dispatch (`spell_defs_gen`, `item_fx_gen`); in neither
case does the engine name the content. See **BUNDLE.md → "A usable item's routine"**.

Within those, the callable engine surface (today ~165 `sim_*` + the `Player` method sugar +
`random`) splits into capability groups. **The split is by EFFECT, and it encodes crawler's two
hard fences (MP-safe clock, no raw host writes) as deny-by-default capability gaps:**

| Group | Right | Representative members | Profile default |
|---|---|---|---|
| `query` | read | `sim_player_*`, `sim_stat*`, `sim_enemy_*`, `sim_floor_*`, `sim_inv_*`/`sim_item_*`, `sim_tile_kind`, `sim_hex_state*`, `sim_los_to`, `sim_compute_fov`, `sim_depth`, `sim_gold`, `sim_window` (the ~126 read accessors) | **allow** (no mutation, safe-broad) |
| `rng` | — | the seeded `random` package, `sim_roll`, `sim_frac` | **allow** (deterministic — MP-safe) |
| `ui` | log | `sim_log`, `sim_msg_at` | **allow** (player-visible text only) |
| `player` | mutate | `sim_heal`, `sim_blink`, `sim_buff_stat`/`drain_stat`/`grant_stat`/`raise_stat`/`restore_stat`, `sim_cure_venom`, `sim_award_xp`, `sim_grant_gold`/`skill`/`save`, `sim_give_item`, `sim_equip`/`equip_by_key`/`unequip`, `sim_consume_inv`, `sim_spend_sp`, `sim_identify*` — and the `Player` sugar (`p.equip`/`give_item`/`heal`/`buff_stat`/`grant_gold`/`grant_stat`/`reveal_monsters`) | **grant** (gated — a self/loadout-affecting mod opts in) |
| `world` | mutate | `sim_bolt`, `sim_damage`, `sim_afflict_enemy`, `sim_make_gaze`/`make_glow`, `sim_set_awake`/`set_speed`, `sim_teleport`, `sim_respawn` | **grant** (gated — combat/world-affecting effects) |
| `detect` | reveal | `sim_reveal_map`/`reveal_monsters`, `sim_monster_sense`, `sim_detect_active` | **grant** (gated — info-reveal effects) |
| `clock` | — | `sim_tick`, `sim_step`, `sim_wait`, `sim_travel`, `sim_descend` | **DENY (never grantable to a bundle)** — advancing the clock from a routine breaks the distance-driven, MP-safe clock (the §"Non-negotiable" fence). The engine drives the clock; routines only react. |
| `lifecycle` | — | `sim_new`/`new_gen*`, `sim_set_class`/`set_race`, `sim_starting_loadout`, `sim_shrine_*` | **DENY** — world/character construction is engine-only. |
| (host fs/net/env, native FFI) | — | loft `files`/`env`, any cdylib bridge | **DENY** — `native_ffi = false`; never in a bundle profile. |

So a typical `[profile.bundle]` is: `allow_libs = ["kerneldefs", "random"]` (the pure data
surface + deterministic RNG) **+** `allow = ["query#read", "ui#log"]` always, **+** whichever of
`player#mutate` / `world#mutate` / `detect#reveal` the bundle's declared kind needs — and
**nothing reaches `clock`/`lifecycle`/fs/net/FFI**, by omission. A spell bundle grants
`world#mutate`; a class-onboarding bundle grants `player#mutate`; a pure content pack (just the
data-def routines) needs only the wholesale `kerneldefs`.

**Why this shape is right (not just expedient):** the deny-by-default gaps are crawler's existing
*acceptance fences* made mechanical — `clock` denied = the MP-safe-clock fence; fs/net/FFI denied =
the "no FS/net" fence; `query` open / `*mutate` gated = "read freely, change deliberately." The
sandbox doesn't add a new policy; it *enforces the one SCRIPTING.md already states* at load time.

**The one structural requirement this puts on the engine seam:** every bundle-callable verb must
be reachable **only** through these declared-capability functions — a routine must not be handed a
raw `&Sim`/`Player` it can mutate fields on directly (that is a "raw write to host data" the
sandbox forbids, and rightly: it would bypass the capability split). Today's routines already obey
this (no raw `s.field =` in any bundle — verified), because they go through `sim_*`/`Player`
methods. Keeping it true as the API grows is the BUNDLE.md standing-check item for this seam: **new
bundle-facing state changes ship as a capability-tagged verb, never as a mutable field handed to a
routine.**

**Gaps for the richer-mod stages (1–4).** The event bus (Stage 1) adds a new routine kind —
`on_<event>(ctx: EventCtx)` — whose `EventCtx` is the *only* capability handle (no bare `&Sim`);
its methods carry the same `query`/`*mutate` groups. Extensible state (Stage 4) needs a
`state#read`/`state#write` capability over a bundle's own namespaced store. Each new verb from
Stages 2–3 is one capability-tag decision at the seam — the table above is the v1 baseline the
dogfood (Step 5) stress-tests and grows.

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
