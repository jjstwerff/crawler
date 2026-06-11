# PLAN-BUNDLES.md — ALL content moves into THEME bundles (build-your-own-game)

Goal (user direction): the engine ships with ZERO game content of its own. The
bestiary (deep monsters and all), their items, lairs/buildings and placement move
into **self-contained THEME bundles** (undead, ghosts, per-biome, …) that anyone
adds or removes at will to compose their own game — plus a per-bundle
**difficulty knob** so a player can soften (or sharpen) one theme's mobs without
touching its defs.

Anchors: **BUNDLE.md** (the seam law + the standing check), `tools/gen_bundles.py`
(the scanner/merger), `catalog.loft` (the merge points), `bundles/desert_surprise/`
(the proven theme-bundle prototype: enemies + items + stencils + placement),
`bundles/world_classic/` (the dungeon as a world bundle).

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

## Phase A — the TRAIT seam (engine de-keyed; content not moved yet)

`MonsterDef` gains two data columns (integers — bitmasks, no text in hot paths):
- `m_habitat`: bit k = lives on terrain kind k (forest/meadow/scree/snow/swamp/
  sand/grass…). Replaces the `habitat_key()` branch table verbatim.
- `m_tags`: placement roles — `TAG_RUIN_NEST`, `TAG_RUIN_BOSS`, `TAG_CAVE_ROOST`,
  `TAG_TOWER_DWELLER`, `TAG_GRAVE` … (one bit each).

Engine call sites convert to catalog queries (rarity/depth-weighted like
`mon_choose`, deterministic roll in, graceful EMPTY out — no candidates means the
nest stays silent, never a crash):
- `habitat_key(kind, tier, pick)` → `mon_choose_habitat(tbl, kind, tier, roll)`
- ruins `goblin`/`goblin_leader` → `TAG_RUIN_NEST` / `TAG_RUIN_BOSS`
- dead-city `skeleton`/`zombie` → `TAG_GRAVE`
- cave-mouth `giant_bat` → `TAG_CAVE_ROOST`
- abandoned tower `skeleton` → `TAG_TOWER_DWELLER`

Gate: behaviour-identical spawns this phase (the tags reproduce today's table —
assert a fixed-seed surface spawns the same census before/after); plus a
grep-test in `bundledeftest`: **no `mon_find("` literal in `src/` outside
`spawn_crystal`**. The standing BUNDLE.md seam check runs at every phase end.

## Phase B — the `theme` bundle kind + the canary (undead)

`gen_bundles.py` learns `kind: "theme"`: scans `monsters`/`items` def modules
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
- `gen_bundles.py` bakes `effective = bundle.difficulty × tuning[key]` into the
  generated merge; the catalog applies it at merge time:
  `hp' = max(1, round(hp·d))`, `dam' = max(1, round(dam·d))`,
  `xp' = max(1, round(xp·(0.5 + 0.5·d)))` — softer mobs still pay (half-)way,
  harder mobs pay extra. Uniques scale like the rest of their bundle.
- Test: knob 0.5 on a theme halves a sampled mob's hp/dam in the merged catalog;
  knob absent = identity; tuning.json overrides bundle default.

## Phase F — the removal MATRIX (the "own game" guarantee)

A new gate target `make bundles-matrix` (not in the default gate — it's a
combinatorial sweep): builds + headlessly boots/walks/descends with
(1) all themes, (2) NO themes (the empty world: walkable, spawnless, valid),
(3) each theme solo. Asserts: gen never crashes, every spawn site tolerates
empty, every theme is self-contained (its defs reference no other bundle's
keys — `gen_bundles.py` verifies cross-references at build time and fails loud).

## Phase G — buildings & lairs per theme (gated on the stencil milestone)

Buildings split the same way the monsters did: the STAMP mechanisms
(`stamp_house`, `stamp_round_tower`, the stencil executor) are engine; the
SHAPES are content. Theme bundles gain `stencils` + `placement` sections (the
`ds_stencils`/`ds_placement` pattern, generalized): undead places a graveyard
stencil near ruins; ghosts haunt abandoned towers; biome themes claim their
windows by terrain tags. ALSO: bundles carry their own SPRITES
(`bundles/<name>/sprites/<key>.png`); the build stages them beside
`assets/sprites/` and the view's by-name resolution picks them up — a theme
drops in art-complete. This phase lands after PLAN-GEOMETRY Track 1 (outlines)
so themed structures inherit doors/jambs/round forms.

## Order & risks

- A → B → C → (D ∥ E) → F; G last (stencil + geometry dependency).
- All new def columns are integers (loft#336: no text tables); merged catalogs
  build at apply-time only (the rc_*/store-pressure habit); generated merge code
  keeps the globally-unique-fn-name style.
- The seam law is re-evaluated EVERY phase (BUNDLE.md standing check) — the
  trait queries are the one new engine surface; they must stay key-blind.
- Difficulty multiplies at MERGE, not in combat math — one place, no per-hit cost.
