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

## Current state (2026-06-10)

- **Classes**: half-migrated — `kind:"character"` bundles exist for `warrior`, `mage`,
  `explorer` (loadout `activate` script + `bundle.json` stats/gold/kit), but the **8
  `ClassDef` rows still live in `src/classes.loft`**. No bundle for priest/rogue/ranger/
  paladin/druid/necromancer. `explorer` is script-only (no `ClassDef`).
- **Races**: fully engine-side (`src/races.loft`, 10 rows + `RF_*` vocab). No `kind:"race"`,
  no bundles, **not applied** (`sim.loft` doesn't even `use races`).
- **HP**: `hero_maxhp(clevel) + ac` — ignores the hit-die. **SP**: no pool (sidebar SP row is
  repurposed to status pips). **Spells**: no data, no system.
- **Casters** (owe SP + spells): mage·priest·rogue·ranger·paladin·druid·necromancer.
  **Martial** (HP only): warrior. Realms: arcane (mage/rogue/necro), divine (priest/paladin),
  nature (ranger/druid); spell-stat int (arcane/nature-int) / wis (divine/druid).
- Only consumer of the tables today: `src/deftest.loft` (tiny blast radius).

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

- `use` flattens transitive pub names → **each bundle's def fn needs a UNIQUE name**
  (e.g. `warrior_class_defs()`, `dwarf_race_defs()`), called qualified in the generated
  aggregator — mirror `bundle_defs.loft`/`ds_enemies::monster_defs()`.
- Keep `&Sim`-mutating helpers in `sim.loft` (C4). Never hold many large `Sim`s live (C22).
- Base table → merged catalog is a prefix; defids stay valid.

---

## Phase A — Engine seam (generic merge; no per-bundle references)

- [ ] `gen_bundles.py`: scan `kind:"character"` for a `"class"` def module → emit
      `src/class_defs_gen.loft` exposing `bundle_classes()` (mirror `gen_world_defs`).
- [ ] `gen_bundles.py`: add a `kind:"race"` scanner → emit `src/race_defs_gen.loft`
      exposing `bundle_races()`.
- [ ] `catalog.loft` (or new `creation_catalog.loft`): add `class_catalog()` / `race_catalog()`
      = merged bundle defs (+ `class_none()`/`race_none()` fallback for "not chosen").
- [ ] `make check` clean; gate green (deftest still passes against the catalog accessors).

## Phase B — Apply to play (HP / SP / stats / skills)

- [ ] `Sim` gains a chosen **class key** + **race key** (carried across descend/respawn).
- [ ] `hero_maxhp` factors the **hit-die** (`c_hd + r_hd`) and CON; both Sim literals + level-up.
- [ ] Race+class **stat block** applied onto `start_stats()` at creation.
- [ ] **Skill mods** (`*_melee/bow/device/disarm/stealth/save`) folded into `sim_skill_*`.
- [ ] **XP factor** (`c_xp`·`r_xp`) applied to the level curve (`xp_for_level`).
- [ ] **SP pool** on the `Sim`: `sp`/`spmax` derived from realm + spell-stat + level (0 if
      `realm == none`); sidebar SP row shows real SP (un-repurpose when a caster).
- [ ] `applytest.loft`: a warrior vs a mage differ in HP/SP/stats as authored. Wire to gate.

## Phase C — Spell system (engine MECHANISM only; spells are bundle content)

The engine owns the *mechanism*; **the spells themselves are a section of the owning
class/race bundle** (Phase D/E), merged generically — never an engine table.

- [ ] `SpellDef` struct + `spell_none()` in the engine (vocabulary): owner/realm key · name ·
      min-level · SP cost · **effect routine id** · desc. No spell *rows* in `src/`.
- [ ] SP pool on the `Sim` + regeneration over the clock (per-tick, like poison/ward).
- [ ] `gen_bundles.py`: scan a `"spells"` section on `kind:"character"` **and** `kind:"race"`
      bundles → emit `src/spell_defs_gen.loft` exposing `bundle_spells()`; `spell_catalog()`
      merges them. (Each bundle's `spell_defs()` uniquely named — `use`-flatten constraint.)
- [ ] **Effect dispatch by routine id** — resolve a spell's effect through the **routine pool**
      (the binding ships in the owning bundle, like `potion_detect_monsters::apply`), NOT a
      hardcoded engine ladder. The engine exposes only effect **primitives** (heal/blink/bolt/
      detect/status via the Player + `sim_*` API). *(Fold item effects toward this same scanned
      index so items and spells share one extensible path.)*
- [ ] **Cast** verb (active slot **E** / a small cast list) — pick a known spell, spend SP,
      refuse if low-SP / under-level.
- [ ] `casttest.loft`: cast a bundle-authored spell → its routine fires + SP spent; under-level/
      low-SP refused. Wire to gate.

## Phase D — Classes → bundles (each *fully done* per the DoD above)

Each class's spell list — **defs + effect routines — ships in its own bundle** (the Phase C
mechanism dispatches them by id). Order by spell-debt so the system fills in incrementally:

- [ ] **warrior** — ClassDef → `bundles/warrior/` (`warrior_class_defs()`); HP applied; no
      spells (realm none). Reconcile `bundle.json` stats/gold/kit vs the ClassDef (one source).
- [ ] **rogue** — bundle + HP/SP; arcane starter spell(s) implemented (e.g. detect, blink).
- [ ] **ranger** — bundle + HP/SP; nature starter spell(s) implemented.
- [ ] **paladin** — bundle + HP/SP; divine starter spell(s) implemented.
- [ ] **mage** — bundle (exists: add ClassDef) + HP/SP; arcane starters (magic bolt, phase,
      detect, light) implemented.
- [ ] **priest** — bundle + HP/SP; divine starters (cure, bless, detect) implemented.
- [ ] **druid** — bundle + HP/SP; nature starters implemented.
- [ ] **necromancer** — bundle + HP/SP; arcane/necro starters implemented.
- [ ] **explorer** — decide: give it a `ClassDef` (a real starter class) or retire it to a
      demo. Resolve the script-only special case.
- [ ] Remove the 8 `ClassDef` rows from `src/classes.loft` (keep struct + vocab + `class_none`
      + `class_find`); `class_table()` gone/empty.

## Phase E — Races → bundles (each *fully done*)

A race is finished only when its `RF_*` abilities are wired. Build the small supporting
systems first; **free-action already has a system** (this session's gaze paralysis). A race
with a unique innate **spell** (none of the 10 base races carry one, but a custom race may)
ships that spell — def + effect routine — in **its own `bundles/<race>/`**, via Phase C.

Supporting systems (build, then wire):
- [ ] **free-action** → gate the gaze paralysis (EXISTS — just wire `RF_FREE_ACTION`).
- [ ] **sustain-stat** → block `sim_drain_stat` when `RF_SUST_*` (stat-drain already exists).
- [ ] **regeneration** → faster HP regen-rate when `RF_REGEN`.
- [ ] **resist-blind / blindness** → a blindness status + `RF_RES_BLIND` immunity.
- [ ] **see-invisible / resist light / resist dark** → as their hazards land (dormant-but-
      tracked until then; a race carrying only these is *gated*, not silently inert).

Races (bundle + stat/HP applied + flags wired):
- [ ] **human** (no flags) · [ ] **half_elf** (none) — finishable immediately after Phase A/B.
- [ ] **gnome** (free-action) · [ ] **halfling** (free-action + sust-dex).
- [ ] **dwarf** (res-blind + sust-con) · [ ] **highborn** (sust-con) · [ ] **half_troll**
      (regen + sust-str).
- [ ] **elf** (res-light) · [ ] **half_orc** (res-dark) · [ ] **high_elf** (see-invis +
      res-light) — gated on their hazard systems.
- [ ] Remove the 10 `RaceDef` rows from `src/races.loft` (keep struct + `RF_*` + `race_none`
      + `race_find` + `race_has_flag`); `race_table()` gone/empty.

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
