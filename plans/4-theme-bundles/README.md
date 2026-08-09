# 4 — Theme bundles: ALL content moves out of the engine (build-your-own-game)

**Issue:** [`jjstwerff/crawler#4`](https://github.com/jjstwerff/crawler/issues/4) ·
**Value:** `G` · **Effort:** `VH`

**Anchors:** `BUNDLE.md` (architecture + the standing check) ·
**`BUNDLE-MIGRATION.md`** (this plan's phases B–G in detail: the Definition of Done for a
class/race, and the per-class list) · `SCRIPTING.md` → [plan #15](../15-bundle-scripting/)
for the behaviour ceiling this migration leans on but does not own.

## Status

**Partly shipped.** The two *mechanism* phases are in — **Phase A** (the trait seam
that de-keys the engine from content) and **Phase H's spawn-anchor** — and their
reference content now lives in BUNDLE.md, not here. The content migration itself
(Phases B–G) has **not started**: the bestiary is still engine-side in
`src/monsters.loft`, there is no `theme` bundle kind, no `undead/` bundle, no
difficulty knob and no removal matrix.

Nothing is in flight. Phase B is the next move and it is unblocked; Phase G is the
only phase with a hard dependency (the geometry plan, #5).

## Goal

The engine ships with ZERO game content of its own — the bestiary, its items, lairs
and placement live in self-contained **theme bundles** anyone adds or removes to
compose their own game, plus a per-bundle **difficulty knob** so a player can soften
(or sharpen) one theme without touching its defs.

## Anchors

**BUNDLE.md** (the seam law + the standing check + the shipped trait seam),
`src/genbundles.loft` (the scanner/merger), `src/catalog.loft` (the merge points),
`bundles/desert_surprise/` (the proven theme-bundle prototype: enemies + items +
stencils + placement), `bundles/world_classic/` (the dungeon as a world bundle).

## Phases

| Phase | Effort | Verify | Status |
|---|---|---|---|
| **A** — TRAIT seam (engine de-keyed) | M | `make test` seam gate + `sim_wilds_ok` | ✅ SHIPPED 2026-06-11 → BUNDLE.md |
| **H₀** — bed as SPAWN ANCHOR (mechanism) | S | `make test` (persist) | ✅ SHIPPED 2026-06-11 |
| **B** — `theme` bundle kind + undead canary | M | gate + REMOVAL test | Open — **next**, unblocked |
| **C** — drain the bestiary in waves | H | gate + removal per wave | Blocked on B |
| **D** — items follow their owners | S | gate | Blocked on C |
| **E** — the difficulty knob (`tuning.json`) | M | knob 0.5 halves sampled hp/dam | Open (parallel with D/H) |
| **H** — race `home`, home-site picker, kinfolk enclaves | H | fixed seed → house+bed, affinity match | Open (needs only A's vocabulary) |
| **F** — the removal MATRIX | M | `make bundles-matrix` | Blocked on C |
| **G** — buildings & lairs per theme | H | gate + probe | Blocked on **#5** (geometry Track 1) |

## The law that makes it possible (and the one that must not break)

Bundles stay **library-like**: content bundle-side, mechanism engine-side, and the
engine NEVER references a bundle by key. Today the engine violates the spirit of
this in one direction — `sim.loft` spawns by literal monster key (`mon_find("goblin")`,
`habitat_key()` returning `"wyvern"`, the cave `"giant_bat"`, the tower `"skeleton"`).
That works only because those monsters are engine-side; the moment they move out,
every such call is an engine→bundle key reference. **So the keystone of this plan
is a TRAIT seam: the engine asks the merged catalog for "a monster that fits this
place", never for a name.** After that, content location stops mattering at all.

## Phase 0 — confirm the split (user call, then it's data)

Proposed theme bundles over the current 35-key bestiary (amend freely):

| Bundle | Monsters | Notes |
|---|---|---|
| `verdant` | giant_rat, white_mouse, jackal, centipede, white_snake, giant_spider, giant_ant + **Skarn, Rat King** | field & forest beasts |
| `cavern` | giant_bat, kobold, cave_spider, floating_eye | the shallow dark |
| `marauders` | goblin, goblin_leader, orc, gnoll, ogre, dark_elf | warbands; today's ruins nests |
| `undead` | skeleton, zombie, ghoul, lich + **Grix Gravecaller**, **Vohl, Hollow Crown** | ruins/graves/swamp-tier |
| `ghosts` | wraith + NEW phantoms/banshee | needs the PHASE mechanic (below) |
| `highland` | harpy, wyvern, troll, basilisk, stone_giant | scree/snow/ice tiers |
| `deeps` | **Maug, World-Sunderer** (+ deep escorts) | the bottom of the world |
| `desert_surprise` | (exists) + giant_ant/white_snake sand variants | the biome prototype |

Engine keeps exactly ONE creature: `spawn_crystal` — it is the respawn/shrine
MECHANISM wearing a monster's body, not content. Town NPC roles (villager,
farmer, guard, …, cow, beaver) stay engine for now — they are the daily-loop
mechanism; a `township` bundle can claim their skins in a later pass.

**Ghosts get their FULL design** (content-authored-to-full-design rule): a ghost
walks through walls. That is a new engine MECHANISM (`MF_PHASE`: pathing ignores
wall tiles, FOV/light still applies, never opens doors) built in this plan — we
do not ship wall-respecting "ghosts".

## Phase A — the TRAIT seam (engine de-keyed) — ✅ **SHIPPED 2026-06-11**

**Reference content now lives in BUNDLE.md → *The TRAIT seam*** — the `m_habitat` /
`m_tags` vocabulary, the call-site conversion table, the chooser's distribution
semantics, and the two gates. Read it there; this row is the closure record.

Closure notes worth keeping:

- Landed as designed with one honest refinement — the chooser picks **uniformly over
  candidates in catalog order** (faithful distribution, not a bit-exact census of the
  old `pick % 3` orderings, which carried no design weight), so the gate asserts
  habitat **correctness** instead of a fixed census.
- `habitat_key()` is deleted; ruins/graves/roosts/towers pick by TAG with per-site
  deterministic salts.
- The two jackal entries split honestly: the lone depth-1 jackal roams the near grass,
  the depth-3 pack the far.
- The seam gate (`mon_find("` literals outside `spawn_crystal`) lives in
  `tools/run_tests.sh`, so the de-keying cannot silently regress.

## Phase B — the `theme` bundle kind + the canary (undead)

`gen_bundles.loft` learns `kind: "theme"`: scans `monsters`/`items` def modules
(same shapes as `ds_enemies`/`ds_items`) into the generated merge. `undead` moves
out first — it is the canary because it exercises every seam: ruins tags, the
tower dweller, swamp habitat, two uniques, drop items. Gate green with the bundle
present; then the REMOVAL test: build without `bundles/undead/` → game boots,
ruins stand empty-but-valid, no reference dangles.

## Phase C — drain the bestiary in waves

One theme per wave (verdant → cavern → marauders → highland → deeps → ghosts),
each wave: move defs + their drop items, re-run gate + removal test.
`src/monsters.loft` ends holding `spawn_crystal` + `mon_none()` only. The ghosts
wave carries the `MF_PHASE` mechanic (kernel: pathing/collision exemption for
wall tiles; headless test: a phantom crosses a wall the player cannot).

## Phase D — items follow their owners; the commons stay (for now)

Monster-tied items (drops, theme gear) move with their themes. The ECONOMY's
item base (rations, torches, the forge/scriptorium/alchemist production keys the
town economy references) stays engine-side this plan — those keys are the
town-mechanism's vocabulary; they migrate later inside a `township` bundle that
owns the daily-loop skins AND its wares in one move. (Honest scope cut, recorded
in BUNDLE.md.)

## Phase E — the difficulty knob

- `bundle.json` gains `"difficulty": 1.0` (author's default for the theme).
- A game-local **`tuning.json`** at the repo/game root maps bundle key →
  multiplier (`{"undead": 0.6}`) so a player softens a theme WITHOUT touching
  the bundle (removable, shareable, survives bundle updates).
- `gen_bundles.loft` bakes `effective = bundle.difficulty × tuning[key]` into the
  generated merge; the catalog applies it at merge time:
  `hp' = max(1, round(hp·d))`, `dam' = max(1, round(dam·d))`,
  `xp' = max(1, round(xp·(0.5 + 0.5·d)))` — softer mobs still pay (half-)way,
  harder mobs pay extra. Uniques scale like the rest of their bundle.
- Test: knob 0.5 on a theme halves a sampled mob's hp/dam in the merged catalog;
  knob absent = identity; tuning.json overrides bundle default.

## Phase H — every hero starts HOME (a house, a bed, the right spot)

Every starting character gets a HOUSE where they live — the game opens there,
in their bed — sited where someone like them would actually live. The seam
holds the usual way: the bundle declares WHO they are, the engine finds WHERE
that fits on this map.

- **Bundle side (data):** race bundles gain a `home` section — a terrain
  affinity (the Phase-A habitat bitmask, reused) + a siting hint
  (`in_town` / `town_edge` / `forest_edge` / `by_water` / `foothills` /
  `by_the_fields` / `near_ruins`) + a flavour name. The class bundle may
  refine it (a mage prefers `tower_adjacent`, a necromancer `near_ruins`).
  Proposed defaults: human/halfling in town or by the fields; elf/half-elf at
  the forest edge; dwarf/gnome in the foothills by the mine; half-orc/
  half-troll outside the walls; highborn beside the square; necromancer near
  the dead places, ranger at the wood's edge, druid by the water.
- **Engine side (mechanism):** a home-site picker in the home window — scores
  open ground against the declared affinity (terrain match, distance band from
  the town square per the siting hint), stamps a small `stamp_house` with a
  **BED** (a new furniture tile), door facing the town. The player starts ON
  the bed; the daily loop already gives NPCs homes — now the hero has one too.
- **The bed is a SPAWN ANCHOR** — the generic mechanism is ALREADY LANDED
  (2026-06-11, ahead of this phase): any feature claims the respawn via
  `sim_anchor_here(kind)`; the last claim wins; death regenerates the
  anchor's depth+window and wakes the player on the anchor hex
  (`anc_*` on the Sim, carried through descend/travel/death). The save
  stairs claim it (kind 1), the crystal claims it on touch (kind 2), the bed
  claims kind 3 at game start / on sleeping — Phase H only adds that call.
  Sleeping in it to pass the night is a natural follow-on (optional, noted).
- **KINFOLK — a place in the world for every race (user direction):** the hero
  does not live alone; each race bundle present in the build gets ONE small
  enclave in the world — a handful of homes and **2–5 kin** (villager-role
  NPCs wearing the race's skin, living the daily loop: sleep, wander, tend) —
  sited by the same `home` affinity (the dwarf hold in the foothills by the
  mine, a few elven lodges under the eaves of the forest, halfling burrows by
  the fields, a half-orc camp outside the walls). Deliberately NOT abundant —
  no second town, just enough that meeting your own kind (and the others')
  makes the world feel peopled. Enclaves are world features (an `OvEnclave`
  contract beside towns/forts/towers: scored sites, spacing against towns,
  ruins and each other), so they stamp in whichever WINDOW holds them — some
  races live windows away, and visiting them is a journey. The hero's Phase-H
  house stands IN their race's enclave (class hints nudge it to its edge —
  the necromancer at the unquiet end). The occasional lone WANDERER of another
  race on the roads (one per window at most, gatherer-style) keeps the rest
  of the map from reading empty. Removability: no race bundle → no enclave;
  a race bundle without a `home` section → house-only fallback near town.
- Tests: every shipped race/class combo resolves a home (fixed seed → house
  exists, bed inside, start-on-bed, location matches the affinity — the dwarf
  wakes in the foothills among dwarves, the elf under the trees among elves);
  each present race resolves exactly one enclave with 2–5 kin on the daily
  loop; a race bundle with no `home` section falls back to the town square
  start (removability holds).

## Phase F — the removal MATRIX (the "own game" guarantee)

A new gate target `make bundles-matrix` (not in the default gate — it's a
combinatorial sweep): builds + headlessly boots/walks/descends with
(1) all themes, (2) NO themes (the empty world: walkable, spawnless, valid),
(3) each theme solo. Asserts: gen never crashes, every spawn site tolerates
empty, every theme is self-contained (its defs reference no other bundle's
keys — `gen_bundles.loft` verifies cross-references at build time and fails loud).

## Phase G — buildings & lairs per theme (gated on the stencil milestone)

Buildings split the same way the monsters did: the STAMP mechanisms
(`stamp_house`, `stamp_round_tower`, the stencil executor) are engine; the
SHAPES are content. Theme bundles gain `stencils` + `placement` sections (the
`ds_stencils`/`ds_placement` pattern, generalized): undead places a graveyard
stencil near ruins; ghosts haunt abandoned towers; biome themes claim their
windows by terrain tags. ALSO: bundles carry their own SPRITES
(`bundles/<name>/sprites/<key>.png`); the build stages them beside
`assets/sprites/` and the view's by-name resolution picks them up — a theme
drops in art-complete. This phase lands after plan #5 Track 1 (outlines)
so themed structures inherit doors/jambs/round forms.

## Order & risks

- A → B → C → (D ∥ E ∥ H) → F; G last (stencil + geometry dependency). H needs
  only Phase A's habitat vocabulary; it can land early — it is the most
  player-visible win of the whole plan.
- All new def columns are integers (loft#336: no text tables); merged catalogs
  build at apply-time only (the rc_*/store-pressure habit); generated merge code
  keeps the globally-unique-fn-name style.
- The seam law is re-evaluated EVERY phase (BUNDLE.md standing check) — the
  trait queries are the one new engine surface; they must stay key-blind.
- Difficulty multiplies at MERGE, not in combat math — one place, no per-hit cost.
