# Migration — move all classes & races to bundles (and make them *real*)

Move every **class** and **race** out of the engine data tables (`src/classes.loft`,
`src/races.loft`) into self-contained `bundles/<name>/` folders the engine merges
generically — **and** make each one mechanically live. A class/race is **not "finished"**
by a data-move alone.

## Definition of Done — a class/race may be checked off ONLY when ALL hold

1. **Bundle-owned content** — its `ClassDef`/`RaceDef` row lives in `bundles/<name>/` and is
   merged generically (no `src/` edit, no engine-references-it-by-key).
2. **Applied** — its stat block, **hit-die**, XP factor and skill mods modify the live
   character at creation/level.
3. **HP/SP mutate** — starting **HP** reflects the hit-die (+ CON); starting **SP** reflects
   the realm + spell-stat (0 for non-casters). The sidebar shows the real values.
4. **Its spells/abilities are IMPLEMENTED** — *implement the spell/ability when it pops up*.
   A caster class is unfinished while any of its starter spells are inert; a race is
   unfinished while an `RF_*` ability it carries does nothing. **No nerf, no stand-in**
   (CLAUDE.md cardinal rule): build the system, don't make the content lie. Each spell's
   **effect is a bundle-side routine** (resolved by id), so the spell is content like any
   other — and a custom spell finishes the same way.
5. **Builds green** — `python3 tools/gen_bundles.py` regenerates, `make check` clean,
   `make test LOFT_REPO=../loft2` green.

## Library-like invariant (the standing check — BUNDLE.md)

Engine holds **mechanism + vocabulary** (the `ClassDef`/`RaceDef`/`SpellDef` structs, `RF_*`/
realm vocabulary, the merges, the HP/SP/spell systems + the effect *primitives* each routine
calls). A bundle holds **content** (a def row that *sets* flags/realm, plus its effect
*routine*). A stranger drops a `bundles/lizardfolk/` race in and plays it against an unchanged
game.

### Boundary goal — user-defined classes & races (carrying their spells) are first-class bundles

The whole point of the move: **the library boundary extends cleanly**. A user-authored
class, race, or spell must drop in **exactly like any other bundle** — a folder under
`bundles/`, rebuilt with `gen_bundles.py`, with **zero `src/` edits** — and be selectable/
castable in an unchanged game. Concretely:

- **Spells belong to their owner — not a separate bundle.** There is **no `kind:"spell"`**.
  A spell lives **inside the class/race bundle that owns it**, as a *section* of that bundle
  (just as a world bundle carries enemies/items/stencils sections). A race with a unique
  innate spell ships that spell in `bundles/<race>/`; a class ships its spell list in
  `bundles/<class>/`. Custom spells ride in with the custom class/race that brings them.
- **No closed engine switch.** Spell (and item) *effects* resolve through a **routine bound
  by id**, not a hardcoded `if key == …` ladder in the engine. The effect routine ships in
  the **owning class/race bundle** (the routine-pool / "Routine bindings" leg — the
  explorer's custom `potion_detect_monsters::apply` already proves the shape; the engine
  provides only the **effect primitives** routines call: heal / blink / bolt / detect /
  status via the Player + `sim_*` API).
- **Cross-bundle by key.** A class names its realm (`c_realm`); spells carry their owner/realm
  key; the key→index link pass (already used for monsters/items/quests) wires them. The engine
  never names a specific class/race/spell.
- **Proof = the drop-in test** (Phase F): a throwaway custom race **and** class — the class
  bringing its own spell — appear and work with no engine change. If any needs an `src/` edit,
  the boundary is not clean yet.

## Current state (END OF DAY 2026-06-10 — the migration is essentially DONE)

- **Classes: 8/8 fully migrated** — one bundle each, starter spells implemented via the
  realm-book model (priest owns divine, druid owns nature, mage owns arcane; realm-mates
  share); `class_table()` EMPTY. `explorer` = loadout-only demo (no ClassDef).
- **Races: 10/10 migrated, 6/10 fully done** — dwarf/elf/half_orc/high_elf wait only on
  their hazard systems (blindness / light / dark / invisibility); `race_table()` EMPTY.
- **Applied to play**: stat blocks, stacking hit-dies, race+class XP factors, skills/save
  mods, SP pool + regen + live sidebar bar, natural HP regen, sustains, free-action↔gaze,
  res-poison↔venom. Quick-start = human warrior; the CRYSTAL re-specs race/class in-game.
- **Open**: Phase F (the drop-in proof test), the 4 gated races, deeper per-realm spell
  lists (each class's own bundle, incrementally).
- (The original baseline this plan started from is preserved in git history.)

## Sequencing decision (2026-06-10) — content first, races first

Build the **content into bundles first**, not the scripting epic (**SCRIPTING.md**) first. The
current classes/races/spells touch scripting at exactly one small seam — **routine-by-id effect
dispatch** — not the event bus; the big levers serve *future* content, and designing them before
real consumers is premature (concrete-examples-first). The migration *produces* the cases the
scripting layer is later extracted from.

**Start with races** — they carry **no spell debt** (just stats/HP + two already-wired flags:
free-action ↔ gaze, res-poison ↔ venom), so they land fastest. Classes (7 of 8 casters) follow
once the spell system + routine-by-id dispatch land.

**Guardrail (when spells land):** build spell/ability effects as **routine-by-id from day one**
(bundle routines on the Player/`sim_*` API) — never a hardcoded engine `if key == …` ladder. That
dispatch *is* the embryonic event bus; getting it right makes content-first cost ~zero rework.

**One bundle = one race** (and one = one class — never mix). A modder composes a *limited* game
by including only the race/class bundles they want, so each race is its own drop-in
`bundles/<race>/` (pure data, no per-race script — unlike a class's loadout script). The seam
merges every `kind:"race"` bundle; that one-per-bundle granularity is what lets a stranger ship,
say, a 2-race game by dropping in just those two folders.

## loft constraints (don't get bitten)

- **Each bundle's def fn needs a globally UNIQUE name** (e.g. `dwarf_race_defs()`,
  `warrior_class_defs()`), called qualified in the generated aggregator. *Verified the hard way:*
  the **interpreter tolerates** several modules exporting the same fn name (qualified calls
  resolve), but the **native/WASM backend** compiles each pub fn to a shared global symbol and a
  duplicate name is a hard `E0428` (`loft_shared_n_<fn>` defined twice). So interpret-only
  verification is **not enough** — check the compile path, since modders will. (The world
  bundles' fixed `monster_defs()`/`item_defs()` have the same latent clash once a 2nd world
  bundle adds that section — fix when it lands.)
- Keep `&Sim`-mutating helpers in `sim.loft` (the kernel invariant). Never hold many large
  `Sim`s live (old store-pressure habit, kept as defense-in-depth).
- Base table → merged catalog is a prefix; defids stay valid. A drained engine table must still
  return a **typed** empty (`t: vector<T> = []; t`), not a bare `[]` (infers as void).
- **Never merge a catalog in a hot path.** `race_catalog()`/`class_catalog()` build fresh
  vectors per call — calling them from per-tick/per-roll code (skills, save, xp, regen) is both
  the wrong idiom (the engine caches derived combat numbers: wdam/pac) and needless store
  pressure. Bake derivations onto the Sim at apply time (`rc_*` fields); catalog
  lookups happen ONLY in `apply_creation`.

## Landed so far (2026-06-10) — races

- **Seam (Phase A):** `kind:"race"` scanner in `gen_bundles.py` → `race_defs_gen.loft`;
  `catalog.loft` `race_catalog()` = (empty) `race_table()` + `bundle_races()`.
- **Content (Phase E data-move):** 10 per-race bundles `bundles/<race>/` (one race each, unique
  `<key>_race_defs()`); `races.loft` drained to struct + `RF_*` vocab + helpers.
- **Apply (Phase B core):** a `race` key on the `Sim` (carried across descend/death);
  `sim_set_race` bakes the **stat block**; **hit-die** shifts max HP; **skill + save** mods derive
  live; **free-action ↔ gaze** and **res-poison ↔ venom** gates wired. Tests: `deftest` (DEFS) +
  `racetest` (RACE), gate green.
- **Apply (Phase B finish, races):** `r_xp` scales the level curve (`xp_need` in award + the XP
  bar); **sustains** block drain; **natural regeneration** built (+1 HP/`REGEN_EVERY` ticks,
  poison blocks) with `RF_REGEN` at double pace. **6 of 10 races fully done** (human,
  half_elf, gnome, halfling, highborn, half_troll); dwarf/elf/half_orc/high_elf gated on the
  blindness / light / dark / invisibility hazard systems.
- **Remaining:** the gated hazard systems above; **SP** (rides the spell system, class side);
  then **classes** (Phase D) once the spell system + routine-by-id dispatch land.

## Class track status (2026-06-10) — LANDED

Phase C + the first two Phase-D classes are **implemented and headlessly proven**
(`classtest` 11/11: merge, apply, SP pool, xp factor, re-spec, kernel bolt, quick-cast,
realm gating, the full cast chain via the GENERATED routine-by-id dispatch, SP regen):
warrior + mage in their own bundles (`*_class.loft`, mage's spells + fx routines in
`mage_spells.loft`); `class_catalog()`; SP on the Sim; `sim_bolt`; `castfx`; the E-key
quick-cast; the story quick-start (human warrior + kit). Race/class derivations are CACHED
on the Sim (`rc_*`, the wdam/pac idiom — catalog merges only at apply, never per call).

**Minimal creation UI — BUILT (2026-06-10, gate 33/33):** quick-start = the story boots a
**human warrior + kit**, zero menus. The **spawning crystal** is the re-spec point:
`MF_SHRINE` on `spawn_crystal` → bump = INTERACT (no melee; still arrow-destructible, a
real choice) → the CRYSTAL PAGE: RACE | CLASS columns off the merged catalogs via `sim_*`
roster accessors (dropped-in bundles appear automatically), W/S cursor, A/D column, Enter
reshapes (`sim_shrine_apply`: re-derive + full heal + full mind; inventory untouched — the
kit is a new-game-only grant), Q steps away. `crystaltest` in the gate. The in-window page
look = the user's visual verify (make play). The caster SP sidebar row is in (live mana bar in arcane blue when spmax>0; status pips still win the row; an unbound E shows a dim "cast" hint for casters).

---

## Phase A — Engine seam (generic merge; no per-bundle references)

- [x] `gen_bundles.py`: scan `kind:"character"` for a `"class"` def module → emit
      `src/class_defs_gen.loft` exposing `bundle_classes()` (+ the `"spells"` scan →
      `spell_defs_gen.loft` defs + routine-by-id dispatch).
- [x] `gen_bundles.py`: add a `kind:"race"` scanner → emit `src/race_defs_gen.loft`
      exposing `bundle_races()` (def fns globally unique by style).
- [x] `catalog.loft`: `race_catalog()` + `class_catalog()` (merged; `*_none()` fallbacks).
- [x] `make check` clean; gate green (deftest reads `race_catalog()`, asserts engine base empty).

## Phase B — Apply to play (HP / SP / stats / skills)

- [x] `Sim` gains chosen **race + class keys** (carried across descend/respawn/death).
- [x] Max HP factors BOTH hit-dies (`rc_hd`, level-scaled — race + class stack).
- [x] Race + class **stat blocks** applied onto `start_stats()` (`apply_creation`, idempotent).
- [x] Race + class **skill mods** (cached `rc_*`; class numbers via CLASS_SKILL_DIV).
      [ ] device/disarm (their skills don't exist yet — vocabulary kept).
- [x] **XP factor**: `r_xp` × `c_xp` scale the curve (`xp_need`).
- [x] **SP pool** on the `Sim` (`sp`/`spmax` from realm + spell-stat + level, SP regen on
      the clock, spend gate) — verified at gate. [x] sidebar SP row shows a live mana bar
      for a caster (status pips still win the row); unbound E shows the "cast" hint.
- [x] Apply tests in the gate: `racetest` + `classtest` (incl. warrior-vs-mage HP/SP and
      the realm matrix).

## Phase C — Spell system (engine MECHANISM only; spells are bundle content)

> **STATUS: DONE — verified at the full gate, 2026-06-10.**

The engine owns the *mechanism*; **the spells themselves are a section of the owning
class/race bundle** (Phase D/E), merged generically — never an engine table.

- [x] `SpellDef` struct + `spell_none()` in the engine (vocabulary): owner/realm key · name ·
      min-level · SP cost · **effect routine id** · desc. No spell *rows* in `src/`.
- [x] SP pool on the `Sim` + regeneration over the clock (per-tick, like poison/ward).
- [x] `gen_bundles.py`: scan a `"spells"` section on `kind:"character"` **and** `kind:"race"`
      bundles → emit `src/spell_defs_gen.loft` exposing `bundle_spells()`; `spell_catalog()`
      merges them. (Each bundle's `spell_defs()` uniquely named — `use`-flatten constraint.)
- [x] **Effect dispatch by routine id** — resolve a spell's effect through the **routine pool**
      (the binding ships in the owning bundle, like `potion_detect_monsters::apply`), NOT a
      hardcoded engine ladder. The engine exposes only effect **primitives** (heal/blink/bolt/
      detect/status via the Player + `sim_*` API). *(Fold item effects toward this same scanned
      index so items and spells share one extensible path.)*
- [x] **Cast** verb (active slot **E** / a small cast list) — pick a known spell, spend SP,
      refuse if low-SP / under-level.
- [x] `casttest.loft`: cast a bundle-authored spell → its routine fires + SP spent; under-level/
      low-SP refused. Wire to gate.

## Phase D — Classes → bundles (each *fully done* per the DoD above)

Each class's spell list — **defs + effect routines — ships in its own bundle** (the Phase C
mechanism dispatches them by id). Order by spell-debt so the system fills in incrementally:

- [x] **warrior** — DONE: ClassDef → `bundles/warrior/warrior_class.loft`; hit-die HP
      applied; stats single-sourced in the ClassDef; the story quick-start boots it.
- [x] **mage** — DONE: `mage_class.loft` + `mage_spells.loft` (Magic Dart / Blink / Sense
      Creatures — defs + fx routines, all three implemented); SP 6/6 at start; E quick-casts.
- [x] **priest** — DONE: owns the DIVINE book (`priest_spells.loft`: Mend Wounds heal /
      Blessing CON-ward / Sense Foes reveal — all implemented); mace + litany kit.
- [x] **paladin** — DONE: shares the divine book (realm model); knightly kit.
- [x] **druid** — DONE: owns the NATURE book (`druid_spells.loft`: Thorn Lash bolt /
      Knit Flesh heal / Beast Sense reveal — all implemented); staff + lore kit.
- [x] **ranger** — DONE: shares the nature book; bow + arrows + a dagger (bundletest's
      every-class-arms-a-weapon-and-light invariant caught the knifeless ranger).
- [x] **rogue** — DONE: shares the arcane book (quick-casts magic_dart); stealthy kit.
- [x] **necromancer** — DONE: shares the arcane book (its own grave book is future
      content); frail scholar kit.
- [x] **explorer** — resolved as a LOADOUT-ONLY demo bundle (no `ClassDef`, so it does not
      appear on the crystal page / in class_catalog; it remains the custom-item-script
      exemplar). A real class later if wanted.
- [x] Remove all 8 `ClassDef` rows from `src/classes.loft` (struct + `class_none` +
      `class_find` kept); `class_table()` EMPTY (deftest + classtest assert it).

## Phase E — Races → bundles (each *fully done*)

A race is finished only when its `RF_*` abilities are wired. Build the small supporting
systems first; **free-action already has a system** (this session's gaze paralysis). A race
with a unique innate **spell** (none of the 10 base races carry one, but a custom race may)
ships that spell — def + effect routine — in **its own `bundles/<race>/`**, via Phase C.

Supporting systems (build, then wire):
- [x] **free-action** → gates the gaze paralysis (`sim_player_free_action` in the strike block).
- [x] **sustain-stat** → `sim_drain_stat` fails on a sustained stat ("Your body resists the
      drain."); STR/DEX/CON map to their `RF_SUST_*`.
- [x] **regeneration** → natural regen built (Angband-faithful: +1 HP / `REGEN_EVERY=10` ticks
      for everyone, poison blocks it) with `RF_REGEN` halving the interval.
- [ ] **resist-blind / blindness** → a blindness status + `RF_RES_BLIND` immunity.
- [ ] **see-invisible / resist light / resist dark** → as their hazards land (dormant-but-
      tracked until then; a race carrying only these is *gated*, not silently inert).

Races (bundle + stat/HP/XP applied + flags wired; SP is class-realm-side, n/a to base races):
- [x] **human** (no flags) · [x] **half_elf** (none).
- [x] **gnome** (free-action) · [x] **halfling** (free-action + sust-dex).
- [ ] **dwarf** (sust-con ✓; **res-blind gated** on a blindness system) · [x] **highborn**
      (sust-con) · [x] **half_troll** (regen + sust-str).
- [ ] **elf** (res-light) · [ ] **half_orc** (res-dark) · [ ] **high_elf** (see-invis +
      res-light) — gated on their hazard systems.
- [x] Remove the 10 `RaceDef` rows from `src/races.loft` (struct + `RF_*` + helpers kept);
      `race_table()` empty (deftest asserts it).

## Phase F — Verify the library-like invariant

- [ ] No `src/` file references a class/race by key (engine dispatches generically).
- [ ] Drop-in test: a throwaway custom **class** (bringing its own spell — def + effect
      routine in its bundle) **and** a custom **race** appear, are selectable, and the custom
      spell casts — all with **zero** `src/` edits (mirror `bundledeftest`).
- [ ] `deftest` reads `class_catalog()`/`race_catalog()`; add `creationdeftest`/extend it.
      Gate green.
- [ ] BUNDLE.md: document the `kind:"race"` registry + the class def-section; re-affirm the
      standing check. CLAUDE.md "Where things are" updated.

## Out of scope here (separate work)

Character-**creation UI** (race-select × class-select screens) rides on top once the catalogs
+ application exist (`bundle_keys` is already commented "for a class-select screen, later").
Deeper spell lists extend each class/race's own bundle incrementally (never a separate spell
bundle) — same Phase C mechanism, more content.

The broader extensibility this migration leans on (effect routines bound by id; the event bus,
general script API, flags-as-routines that let bundles add *new mechanics*, not just data) is
its own staged epic: **SCRIPTING.md**. Phase C's "effect dispatch by routine id" is the first
concrete step of it.
