# crawler — Design Document

**Status:** In development. M0 vertical slice + data foundations built; the
2D game runs; procedural world generation underway. (Repo: `crawler`; loft
package: `story`; final in-world name TBD.)
**Last updated:** 2026-06-03

---

## 1. Summary

A **clean-room, ZAngband-style roguelike** written in the **loft** language.
It plays in **2D today** and is built to become a **3D browser game** later,
driven by the *same* renderer-agnostic **simulation kernel**.

Defining twist: the player moves and turns **smoothly and continuously**,
enemies live on a **hex grid**, and the game clock is **driven by how far the
player travels**, not by wall-clock time.

---

## 2. Relationship to moros — same world, *generated* not authored

The world model here — a **hex world** with per-hex height + stacked layers,
materials, items, and walls/buildings/castles/towers/roads/rock-faces — is the
**same rich system `moros` already details**, *but `moros` builds it by hand
through an editor* (a long content/tooling tail). **`crawler` is the
anti-moros:** it shares that world model (and reuses `moros_map`/`moros_render`)
yet reaches a **working, playable foundation much faster by *generating* the
world procedurally** instead of authoring it. Same destination world; code- and
generation-driven path to a working game, with no editor dependency.

Consequence that recurs throughout: **everything is procedural** (dungeons,
buildings, towns, roads, terrain), and the engine favors a solid generated core
over hand-authored content.

---

## 3. Goals & Non-Goals

**Goals**
- A **playable** roguelike — open it, drive around, fight, lose.
- A **renderer-agnostic simulation kernel**: all rules/state, zero rendering;
  2D and future 3D are interchangeable front-ends.
- **2D now → 3D browser later** with no kernel rewrite.
- **Deterministic** simulation (testing, replay, world-keyed generation).
- **Procedural** content throughout; **no IP risk** (§4).

**Non-Goals (for now)**
- Reproducing ZAngband's exact content/balance — we clone *mechanics*.
- Multiplayer, mods — later, if ever.
- A bespoke 3D renderer — reuse `moros_render`.
- A hand-authoring editor — that's moros's path, deliberately not ours.

---

## 4. Intellectual property — clean-room

Game mechanics/systems aren't copyrightable; names, art, and specific lore are.
We clone the **systems** and invent the **fiction**.

- **Banned:** any Tolkien name (Angband, Morgoth, Sauron, balrog, Nazgûl, ent,
  Shelob, the One Ring, "hobbit", …) and any Zelazny/Amber name (Oberon,
  Amberites, the Pattern, Trumps, Serpent of Chaos). Use **"halfling"** not
  "hobbit".
- **Free to reuse:** depth progression, XP/leveling, stats/HP, resistances,
  ego-items/artifacts and monster "uniques" *as concepts*, spell schools,
  bump-to-attack, inventory; generic D&D race/class scaffolding.
- Angband/ZAngband are **GPL**, so reading their source to reproduce formulas is
  legitimate (crawler is LGPL-3.0-or-later, GPL-compatible). All original
  content lives in swappable data files. (The `moros_*` libs contain zero such
  names — verified.)

---

## 5. Architecture — kernel / view split

```
            ┌─────────────────────────────────────────────┐
            │  kernel  (pure loft, NO graphics dependency) │
            │  hex world · continuous player · hex-locked  │
            │  enemies · distance clock · collision ·      │
            │  combat · FOV · items · world generation     │
            │  → exposes read-only state + step(intent)    │
            └───────────────┬─────────────────┬───────────┘
                            │                 │
             ┌──────────────▼──────┐   ┌──────▼───────────────────┐
             │  view-2d (NOW)      │   │  view-3d (LATER)         │
             │  graphics package;  │   │  moros_render;           │
             │  world rotates to   │   │  camera_follow behind    │
             │  player heading;    │   │  the player; SAME kernel │
             │  cells/glyphs, HUD  │   │  state, 3D meshes         │
             └─────────────────────┘   └──────────────────────────┘
```

**Hard rule:** the kernel never calls a draw/window/input API. It takes an
**input intent** + frame delta, advances state, and exposes **read-only state**.
Swapping renderers requires zero kernel changes. (The `hexgeo`/`sim`/`gen`/data
modules import no graphics; `view`/`story` are the swappable front-end.)

**Reused from moros:** `moros_map` (hex world store, JSON, no graphics) and
`moros_render` (hex→3D mesh→GLB→WebGL, `camera_follow`, thick walls, curved
walls, cylinder posts, raised surfaces). We do **not** depend on `moros_sim`
(it imports graphics) — the small continuous/hex collision we need is
reimplemented graphics-free in the kernel.

---

## 6. World model — hex terrain

- **Coordinates:** axial `(q, r)` for hexes; continuous `(x, y)` for the player.
- **Hex layout = moros's default:** `HEX_WIDTH = √3`, `HEX_ROW_HEIGHT = 1.5`.
  *Caveat:* the geometry is **pointy-top** (vertex up/down, flat edges
  left/right) despite moros's comments mislabeling it "flat-top" — defer to the
  function. (`hexgeo.loft` works in clean axial coords; converts to moros offset
  coords at the moros_map boundary.)
- **"Hex length" `L = √3`** (all 6 neighbors equidistant) = the unit of the
  game clock (§11). The clock accrues **path length travelled** (wiggling costs
  time).
- **Two collision-level wall kinds** (moros's model): **solid full-hex walls**
  (non-walkable cells — Angband granite) and **edge walls** (thin barriers on a
  hex edge, stored on the 3 canonical edges N/NE/SE; the other 3 belong to the
  neighbor). A move A→B is blocked if **B is solid** or the **shared edge** is
  walled — `is_blocked_move`, with axis-separated **sliding** + a **collision
  radius** (already built in `sim.loft`).

---

## 7. Height & layers (mirrors `moros_map`)

The terrain is ultimately a **stack of layers (`cy`)** with a **per-hex centre
height (`h_height`)** — exactly `moros_map`'s shape, so the kernel carries the
fields and `moros_render` draws them (`y = h_height·HEIGHT_SCALE`, slopes via
`emit_slope_face`, layers stacked). Additive terrain data, 1:1 with `moros_map`
→ free 3D hand-off. **Height deltas between adjacent hexes are slopes/cliffs**
(→ rock faces, §9). Surfaced for later: step-up limit + climb cost vs. the
clock; height-aware FOV; layer traversal (stairs); the 2D view shows one layer
at a time (height as shading).

---

## 8. World structure — wilderness overworld + dungeons

A **wilderness overworld** (a large surface hex map — terrain, height, towns,
dungeon entrances) you travel across continuously, plus **dungeons** (separate
descending hex maps) entered from it. The overworld *is* a `moros_map`;
`moros_render` draws both in 3D. The kernel gains a **current map** +
**transitions** (enter/descend/ascend/recall); the view treats overworld and
dungeon identically.

- **World-keyed + persistent.** Every place is generated **deterministically
  from a position-seed** (`gen.world_key_seed(wx,wy,depth)`); once visited, its
  **state is persisted** (monsters/items/changes) so re-entry restores it —
  rewarding travel. Same machinery for overworld and dungeons; persistence via
  `moros_map` JSON per visited level.
- **Zone-based difficulty + shallow dungeons.** Each region has a **zone
  difficulty** (ZAngband's "law"); dungeons are **shallow**, monsters drawn at
  **effective level = zone difficulty + sub-level** (not pure descent).
  Progression is mainly **horizontal** (travel to harder zones). Preserves
  Angband monster-selection (`monsters.loft` `m_depth` + `mon_for_depth`, fed
  the zone-derived level) and fixes ZAngband's "no incentive to travel" weakness.

---

## 9. Feature overlays — walls, buildings, castles, roads, rock faces

The hex terrain (§6–7) is the simulation truth. Walls/buildings/roads/rock-faces
are **one outline engine** producing **render geometry** over that terrain.

**One processor, parameterized per feature:**
- **Input** — run/polylines, either *placed* (houses, roads, walls) or
  *derived from terrain* (rock faces = layer-boundary silhouettes; organic caves
  = solid/floor silhouette).
- **Knobs** — **direction resolution** (snap to **12** = 30° or **24** = 15°)
  and **junction policy** (**sharp-miter** / **rounded-arc** / **semi-rounded** /
  **round-tower**).
- **Output** — render geometry only (segments / arcs / towers / raised surfaces)
  → 2D now, `moros_render` in 3D.

| Feature | Source | Dir | Junction / outline |
|---|---|---|---|
| Houses/buildings | placed (square local, `gridgeo`) | 12 | sharp 90° |
| Roads | placed | 24 | rounded (smooth turns) |
| Town/castle walls | placed | 24 | sharp curtains + **round towers** at corners |
| Rock faces | terrain layer boundary | 24 | road-rounded **now** → **semi-rounded later** |

- **Buildings** are laid out in a **local square grid** (`gridgeo.loft`) so
  corners are clean 90° by construction, then oriented to one of **12 directions**
  (k×30°: the hex lattice's 6 edges + 6 vertices) and placed at a hex anchor.
- **Castle curtain walls are 2 hexes wide** → a **walkable rampart top** +
  **battlements** (parapet). A castle wall is therefore a **height feature**
  (§7): solid at ground, walkable on the elevated top (reached by stairs/gate
  tower); **round towers** rise to wall-walk height and link the rampart runs.
- **Both wall experiments have homes:** the parked Douglas–Peucker **straightener
  → buildings & castle walls** (sharp); the active averaging/Laplacian `wallgeo`
  **→ roads & (for now) rock faces** (rounded). The three geometries map 1:1 onto
  `moros_render` primitives that already exist — `emit_wall_quad` (straight),
  `emit_thick_curved_wall` (arc), `emit_cylinder_post` (round tower/post),
  raised surfaces (ramparts) — so the 3D side is largely free.

**Collision stays on the hex grid; the overlay is render-only.** Towers keep
their own **hex**; walls use the **3 canonical hex edge-walls** (`h_wall_*`);
2-hex castle walls + cliffs use **height**. The continuous player collides
against **hex cells / edges / height**, never the pretty overlay segments.
**Kernel = hex collision truth; view = pretty overlay derived from it.**

---

## 10. Actors

- **Player (continuous):** float `(x,y)` + heading θ; derived *current hex* is
  used for combat/adjacency.
- **Enemies (hex-locked):** logical position is a hex centre; move **one hex per
  tick**, animate smoothly between centres (interpolation keyed to the player's
  accrued distance); attack into the **whole hex** the player occupies.

---

## 10a. Monster AI, placement & level structure

Three meshing layers, all in the kernel (no graphics), Angband-faithful and
adapted to the hex grid + distance clock. They join at **"a monster is spawned
asleep on a level whose difficulty is set by where it is."**

### Difficulty model — one number
`effective_level = zone_danger(wx,wy) + dungeon_depth`. Feeds monster selection
and loot. Difficulty is mostly **horizontal** (travel to nastier zones); descent
adds on top. Dungeons stay **shallow** (per-zone `max_depth` ≈ 3–8), so the
deepest content lives in far dungeons, not 100 floors down (§8).

### Level & world structure
- **Identity & keying:** a level is `(wx,wy,depth,kind)`, generated
  deterministically from `gen.world_key_seed(wx,wy,depth)`. Same key → same level.
- **Persistence:** first visit realizes + stores the level (map + monster roster
  + items + your carnage); revisit **restores** it (Angband regenerates on leave —
  we persist, to reward travel). Bound storage: keep recent + always-special
  (town, unique sites); evicted ordinary levels re-derive from seed.
- **Connectivity (stairs):** overworld entrance → depth 1; `>` descends, `<`
  ascends; ascending from depth 1 exits to the overworld cell. Connected stairs:
  you arrive on the matching stair. Bottom level (`max_depth`) has a guardian +
  reward and no down stair. Stairs are **tile features** (extend `0 floor / 1
  wall` with `2 down / 3 up`).
- **Level kinds / profiles** (rolled, weighted by `effective_level`): overworld
  (wilderness surface — terrain/towns/entrances), town (safe hub), dungeon
  (room+corridor → cavern → maze → lake), special rooms (pit/nest/vault). Aligns
  with the moros multi-layer/height target (§7): depth ≈ layer index later.
- **State model:** `World{ cur(wx,wy,depth), hero, persisted-levels store, global
  unique flags }`; `Level{ tiles, features, monsters, items }`; transition = save
  current → resolve key → restore-or-generate → place hero on the arrival stair.
  `sim_new_gen` generalizes to `level_load(world, wx, wy, depth)`.

### Placement (`get_mon_num` + `place_monster`)
- **Budget:** `N = LEVEL_MONSTER_MIN + rand(1..8)` per level (Angband ≈ 14+d8),
  scaled to map size — a *spread*, not one species.
- **Selection `get_mon_num(effective_level)`:** candidate pool = races with
  `m_depth ≤ effective_level`; probability ∝ `1/m_rarity`; **deepen bias** (keep
  the deepest of a few draws); small **out-of-depth** chance boosts the level for
  a nastier surprise; **uniques** gated to `depth ≥ m_depth`, once per game
  (world-state), never in random groups.
- **Where:** random passable, unoccupied floor (rooms *and* corridors); **never
  in LOS / within ~a screen of the player start**; retry-capped, `log` shortfalls.
- **Groups & escorts:** `MF_GROUP` places a cluster of the race (size scales with
  depth); unique escorts (future `MF_ESCORT`) bring a themed retinue.
- **Initial state:** spawned **asleep** (sleep depth from new `m_sleep`, else
  derived from `m_vision`) — the input to awareness below.

### Behavior (`process_monster` pipeline)
Per monster action:
```
energy += gain(speed); while energy>=100 { act; energy-=100 }   # speed/energy
wake check (if asleep): roll vs distance & player noise/stealth  # awareness
if asleep: stop
acquire target: player if perceived (LOS + m_vision) else last-seen / scent
decide: afraid? -> FLEE | caster+in range? -> CAST | adjacent? -> MELEE
        | can move? -> STEP via noise flow-field
breeder? -> maybe multiply (free neighbour, under cap)
```
- **Speed/energy:** one world tick = the player spent one hex (one player turn).
  `gain(speed)` via Angband's `extract_energy`, normalized so `m_speed=0` → +100/
  tick (parity with the player), `+10` ≈ ×2, `-5` ≈ ×0.66; leftover carries. The
  hook for player haste/slow (scale the distance clock).
- **Awareness:** spawn asleep; each tick within range, roll to wake (closer +
  louder player vs stealth ⇒ wakes). Kills "the whole level swarms at t=0."
- **Perception:** hex LOS (walk the hex line, blocked by solid) + `m_vision`.
  Loses sight → head to last-seen, then scent, then give up.
- **Pathfinding (the real fix):** a **noise flow-field** — Dijkstra cost grid from
  the player's hex over walkable cells, recomputed on player hex-change; each
  monster steps to the lowest-cost neighbour ⇒ **routes around walls**, no clump /
  stuck (greedy `best_step` can't). Scent = decaying timestamps for out-of-LOS
  tracking.
- **Modifiers/flags:** `MF_NEVER_MOVE` (attack-only), `MF_ERRATIC` (random step
  X%; split into `RAND_25/50` for fidelity), fear/flee (step *up* the gradient),
  `MF_GROUP` surround, `MF_BREEDER` multiply. Future: `PASS_WALL/KILL_WALL`,
  doors, `MOVE_BODY/KILL_BODY`, `SMART/STUPID`.
- **Casters (`MF_CASTER`):** cast-frequency roll; in range + LOS → pick from the
  realm/spell pool (bolt/ball/breath/summon/heal/blink) — the §13 ZAngband hook.
- **Melee:** Angband to-hit vs `m_ac`, blow dice/effects (expand `m_dam` → dice +
  a blow list later); big hits can trigger fear.

### Data additions
- `MonsterDef`: `m_sleep` (sleep depth). Existing `m_rarity / m_depth / m_speed /
  m_vision / m_ac / m_flags` already feed the above.
- New flags: `MF_SMART, MF_STUPID, MF_COWARD/MF_FEARLESS, MF_RAND_25/MF_RAND_50,
  MF_PASS_WALL/MF_KILL_WALL, MF_OPEN_DOOR/MF_BASH_DOOR, MF_MOVE_BODY/MF_KILL_BODY,
  MF_FRIENDS, MF_MULTIPLY (= BREEDER)`; a separate **spell-flag bitmask** for casters.
- `Enemy` (per-instance): copy `speed / vision / ac / flags` off the def + dynamic
  `energy, awake/alert, fear, seen_q/seen_r`.
- `Sim`/`World`: noise flow grid (+ optional scent grid), `player_hex` cache,
  `player_noise/stealth` scalar, persisted-levels store, global unique flags.

### Testing — three tiers (mirrors modern Angband)
Angband ships `src/tests/` (unit incl. data-file parser tests, `make test`, CI),
`main-stats` (`-m stats`: thousands of generated levels for balance
distributions), and the **Borg** (an automated player). We mirror all three:
- **Unit** (our `*test.loft` pattern): deterministic seeded assertions —
  `aitest` (sleeper stays put until approached; `NEVER_MOVE` never moves; monster
  routes around an L-wall; fast monster closes on a fleeing player; afraid flees;
  caster fires at range), `placetest` (same seed → identical roster; none in
  start LOS/radius; counts in `[N_min,N_max]`; `MF_GROUP` clusters; unique once &
  not below depth; restore reproduces hp/positions), `leveltest` (descend→ascend
  returns the persisted level; stairs reachable; `effective_level` = zone+depth;
  bottom has a guardian, no down stair).
- **Stats** (`placestats`, `main-stats`-style): run many `world_key_seed`s and
  assert the monster **distribution** matches the `effective_level` curve + OOD
  rate — the right tool for the probabilistic parts a single seed can't prove.
- **Borg** (later): a headless goal policy driving `sim_step` to descend/fight
  over long runs, surfacing emergent AI / transition bugs.

### Phasing
- **L1** stairs + real depth (deterministic per-depth gen; roster persistence
  next). **A1** budgeted weighted `get_mon_num` scatter with start-safety
  (replaces room-center). **P1** awareness + `m_vision` + `NEVER_MOVE`. *←
  foundation slice (in progress).*
- **A2 / P2** groups + OOD; noise flow-field pathing.
- **P3** speed/energy. **P4** erratic / fear / group-surround / breeder.
- **A3 / L2** unique-once + roster persistence; `effective_level = zone+depth`.
- **P5** casters + spell pool. **P6** melee depth (AC / to-hit / dice).
- **L3** overworld surface + town. **L4** profiles + pit/nest/vault. **L5**
  bottom-guardian + final boss. **L6** multi-layer height.

---

## 11. The distance-driven clock

The player's accumulated **travel distance** is the master clock. Every **`L`
(one hex-length)** travelled fires **one world tick** (enemies act, status/regen
advance). **Turning covers zero distance ⇒ zero ticks** ("turning is free");
standing still freezes the world. Enemy glide interpolation = `(accrued mod L)/L`
→ fully deterministic, no wall-clock dependence. A **wait** action advances one
tick in place. A turn engine wearing a real-time coat.

---

## 12. Controls, camera, FOV

**Controls** (analog/held; release stops immediately, no inertia):
`W`/`S` glide forward/back (cost time), `A`/`D` turn (free), `.`/`Space` wait,
bump-forward-into-enemy = melee. Heading is a continuous float (the "30°" is
turn *feel*, not quantization).

**Camera — egocentric, forward-biased:** the world rotates around the player so
heading is always "up"; player anchored **~70% down** the screen (rear-visibility
margin). 3D later = `moros_render::camera_follow`.

**FOV:** wide forward arc + short all-around radius — directional, tense
exploration; distant flankers unseen, point-blank rear always seen.

---

## 12a. HUD sidebar, character stats & levelling

A persistent **left sidebar** (Angband's character column) plus a **bottom status
line**, drawn screen-space over the egocentric view (like the HP bar — fixed, does
not rotate). Backed by a runtime **`Hero`** model (kernel data, graphics-free; the
sidebar is its view). Uses the existing `classes/races/items` tables (6 stats:
STR/INT/WIS/DEX/CON/CHR; class `c_hd`/`c_xp`/`c_spell_stat`/`c_realm`; race
`r_hd`/`r_xp`/`r_infra`; per-skill `*_melee/bow/device/disarm/stealth/save`) and
monster `m_xp`.

### `Hero` model (M2)
- **Identity:** name, race idx, class idx, **title** (by class + level).
- **Progression:** `clevel` (1–50), `xp`, `gold`.
- **Stats:** the 6, stored Angband-style (3–18 then 18/01..18/220 percentile),
  **cur + max** (max = drain ceiling). `effective = base(rolled) + race_mod +
  class_mod` (+ equip/effects).
- **Derived (recomputed from stats+level+equip):** `maxhp/hp`, `maxsp/sp`
  (casters), `ac`, `speed`, the six **skills**, infravision, carry weight.
- **Conditions/timers:** food/hunger clock, poisoned/afraid/confused/blind/
  stunned/hasted/…; inventory + equipment slots (`items.loft` `SLOT_*`).
- The kernel's current `Sim.php/phpmax` are **subsumed** into `Hero.hp/maxhp`.

### Levelling (Angband formulas)
- **XP needed:** `player_exp[clevel]` base table × **total exp factor**
  `(r_xp × c_xp)/100` ⇒ next-level threshold (warrior cheap, mage dear).
- **XP per kill:** `gained = m_xp × monster_level ÷ clevel` (scaled down as you
  out-level prey; `monster_level` from `m_depth`).
- **On level-up:** `clevel++`; add a **hit-die roll** (`c_hd + r_hd` base) + CON
  per-level bonus → `maxhp`; recompute `maxsp` + learnable spells (casters);
  refresh **title**. HP rolls come from a deterministic per-character table so a
  given seed levels identically (testable).
- **SP/casters:** from the **spell stat** (`c_spell_stat`: INT=arcane,
  WIS=divine) + `clevel`; spell fail-rate from stat + level vs spell level.
- **AC:** equipment + DEX + class; **speed:** equipment/effects; **skills**:
  `race + class + level + stat` (the to-hit / device / disarm / stealth / save
  numbers).

### Sidebar layout (left column, ~13 chars wide)
```
Name
Race  Class           <- e.g. "Halfling Mage"
Title               <- class+level title
LEVEL   n
EXP     n  (next: m)
GOLD    n
                    <- blank
STR  18/50
INT  15
WIS  10
DEX  16
CON  14
CHR  11             <- drained stat shown dim/yellow (cur<max)
                    <- blank
AC      n
HP   cur/max        <- plus the coloured bar, ratio-tinted
SP   cur/max        <- casters only
SPEED   +n
                    <- blank
L1  (50')           <- depth / location
```
- **Bottom status line** (Angband's): hunger (Hungry/Weak/Faint), then condition
  flags (Afraid, Poison, Conf, Blind, Stun, Fast/Slow…), and — when targeting —
  the **target monster's name + health bar**.
- **Render:** reuse `build_hud`'s font; bake static labels once; changing values
  (HP/SP/XP/gold/stats) via digit composition (`draw_number`) or re-bake-on-change
  (cache keyed by value) — all through the text bridge, square/text fallback-safe.
- **Layout:** sidebar claims the left ~130 px; the egocentric view re-centres into
  the remaining width (shift `CX`), so the player stays centred in the *play area*,
  not the window. Sidebar + status line never rotate.

### Phasing
- **H1** minimal `Hero` (promote `php`→`hero.hp`; clevel/xp/gold + the 6 stats
  from a fixed starting race/class) + **XP-on-kill** + **level-up HP growth**.
- **H2** render the sidebar (name/race/class/level/xp/gold/stats/AC/HP/depth).
- **H3** SP + casters, conditions + status line, hunger clock.
- **H4** character-creation screen (pick race/class, roll/point-buy stats).
- **H5** monster health bar / look-targeting on the status line.

### Testing
`herotest.loft`: same seed → identical level-up HP curve; XP-to-next matches
`player_exp × factor`; kill XP = `m_xp × mlvl ÷ clevel`; effective stat =
base+race+class; drained stat (cur<max) flagged; derived AC/SP/skills recompute
correctly. (Sidebar render verified via the `shot.loft` frame, like the HUD.)

---

## 12b. Items — generation, drops, pickup & inventory

Built on `items.loft` (cats `IT_*`, slots `SLOT_*`, dice `i_dd/i_ds`, `i_ac`,
`i_depth/i_rarity/i_weight/i_cost`, `i_power`, `IF_STACKABLE`, glyph+colour). Same
world-keyed determinism + persistence as monsters: **floor items live in the
`Level`**, carried/worn items live on the **`Hero`**.

### Item instances
A floor/inventory item is an **`ItemInst`** (not the static def): `{ def idx, qty,
to_hit, to_dam, to_ac, ego idx, art idx, flags(known/ID'd), charges, timeout }`.
Static stats from `ItemDef`; per-instance magic from `apply_magic`.

### Generation & drops (Angband `get_obj_num` + `apply_magic`)
- **Floor objects at level-gen:** a small budget placed in rooms (vaults richer),
  each via `get_obj_num(effective_level)` — pool = items with `i_depth ≤ level`,
  prob ∝ `1/i_rarity`. Same `effective_level = zone + depth` as monsters.
- **Monster drops:** on death, roll **gold** (level-scaled pile) and/or **items**.
  Add Angband drop flags to `MonsterDef`: `DROP_60/DROP_90`, `DROP_1D2/2D2`,
  `ONLY_GOLD/ONLY_ITEM`, `DROP_GOOD/DROP_GREAT`; items rolled via
  `get_obj_num(monster_level [+good/great boost])`.
- **Quality tiers / `apply_magic(item, level)`:** normal → **good** (plusses) →
  **great/ego** (ego pool) → **artifact** (rare, once each), enchant rolls scaling
  on `level`. Deferred past the basic drop.

### Pickup / drop
- On a hex with item(s): **gold auto-collects**; items grabbed with **`g`** (or an
  auto-pickup option). Stacks (`IF_STACKABLE`: potions/scrolls/ammo) merge by
  def+ego. Inventory ≈ Angband's ~23 slots; **weight** over the STR-derived carry
  limit **slows** you (speed penalty — ties into the AI speed model).
- **`d`** drops onto the current hex → `Level.floor_items` (persisted). Items render
  on the map as their **glyph in colour** (reuse the text-bridge glyph system: `$`
  gold, `!` potion, `?` scroll, `/` wand, `-` ring/amulet, …).

### Inventory & equipment model
- **`Hero.inventory`:** `vector<ItemInst>`, letter-indexed (a–w), category-sorted.
- **`Hero.equip`:** one slot each `SLOT_*` (weapon, bow, body, shield, head, hands,
  feet, cloak, light, **ring×2**, amulet). Wield/wear **`w`**, take off **`t`**;
  equipped items feed the Hero's **derived** AC / to-hit+dam / stat mods / resists /
  speed (the §12a recompute).
- **Identification:** unidentified items show by **flavour** ("a blue potion"); ID
  by use / scroll / sensing; ego/artifact properties hidden until known. (Later.)
- **Use/consume:** quaff (potion), read (scroll), aim (wand), use (staff), zap
  (rod), eat (food), fire (ammo via bow) — effects from the def (`i_power` + flags).

### Inventory screen (UI)
- A **modal overlay** — the distance clock **freezes** while open (consistent with
  "standing still freezes the world"). Toggle **`i`** inventory / **`e`** equipment.
- **Inventory view:** category-grouped rows — `letter) name (qty)   weight` (name in
  known/flavoured form; ego/artifact shown once ID'd).
- **Equipment view:** the slot list with each worn item (or "(nothing)").
- **Select a letter** → action menu: **wield/wear · take off · use/quaff/read · drop
  · inspect**; **inspect** opens a detail panel (description, dice/AC, known plusses
  & properties, weight, value).
- **Render:** text-bridge rows (reuse `build_hud` font) over a dimmed backdrop;
  fallback-safe like the sidebar.

### Data additions
- `ItemInst` struct; `Hero.inventory` + `Hero.equip`; `Level.floor_items`
  (`{hex, ItemInst}` list, persisted).
- `MonsterDef` drop fields/flags; a new `objects.loft` with `get_obj_num(level)` +
  `apply_magic(item, level)` (mirrors `monsters.loft` + the placement pass).

### Phasing
- **I1** floor gold + simple monster-death item drop (chance/quality from `m_depth`)
  + **pickup `g`** (auto-gold) + items as map glyphs.
- **I2** inventory `i` / equipment `e` screens + wield/wear/takeoff + AC/stat
  recompute + **drop `d`**.
- **I3** level-gen objects (`get_obj_num`) + quality tiers / `apply_magic` (ego).
- **I4** identification + flavours + use/consume effects.
- **I5** artifacts; monster drop flags; weight → encumbrance.

### Testing
`itemtest.loft`: same seed → identical floor/drops; pickup adds to inventory &
clears the floor hex; stack merge; wield updates AC/to-hit; takeoff reverts; drop
adds to (persisted) `Level.floor_items`; `get_obj_num` honours depth/rarity; over-
weight applies the speed penalty.

---

## 13. Source of truth for logic — hybrid

- **Modern Angband (4.2.x)** for the **core engine + monster/object rules/data**
  (`monster.txt`/`object.txt` flags, resistances, ego/affixes; combat to-hit/
  damage, stats, HP, XP/leveling, FOV, monster AI) — cleanest to reproduce
  faithfully.
- **ZAngband** for **world structure & flavor:** wilderness overworld (§8),
  **realm-based magic + the full spell pool** (~7 realms × 4 books × 8 spells;
  classes pick 1–2 realms), mutations later.
- **Spells ↔ monster/object rules are compatible:** every spell resolves as an
  effect/projection the target resists + saves against; ZAngband supplies the
  spell catalog, modern Angband the execution machinery. A small effect-type map
  + a few ZAngband-unique effects (Chaos/Trump/Death) bridge them.
- **Skills** = derived Angband values (not a skill tree).
- The placeholder values in the data tables (§14) will be **re-derived from the
  real source** as each system lands. Reproduce logic faithfully; only names are
  clean-room.

---

## 14. Content — data tables + procedural generation

Static catalogs are **loft data modules** (struct + table builder + helpers);
the runtime character is a struct; saves are JSON (loft struct round-trip).

- **`monsters.loft`** — 32 monsters (depth 1–25) + 4 original uniques (final boss
  *Maug*); stat/AI-flag fields. *(placeholder → align to `monster.txt`.)*
- **`classes.loft`** (8), **`races.loft`** (10, halfling-not-hobbit + original
  "highborn"), **`items.loft`** (54 base kinds across all categories).
- **`gen.loft`** — procedural dungeon generator (rooms + corridors, connectivity
  verified, deterministic LCG, `world_key_seed`). Grows: room types, vaults,
  buildings, towns, wilderness.
- **`gridgeo.loft`** — square basis for 90° building/wall layouts (§9).
- **To build:** `spells.loft` (ZAngband realm pool), a `Hero` struct + character
  creation, the feature-overlay processor (§9), combat/FOV/HUD.

---

## 15. Package layout (actual)

```
crawler/  (loft package "story")
├── loft.toml · loft.lock · Makefile · README.md · DESIGN.md
├── patches/            # parked diffs (wallgeo Douglas–Peucker) + README w/ hashes
├── tools/snap.sh       # Xvfb screenshot helper (make shot)
└── src/                # flat; kernel modules import NO graphics
    ├── hexgeo.loft     # hex geometry (axial)            — kernel
    ├── gridgeo.loft    # square geometry for 90° walls   — kernel
    ├── sim.loft        # world + player + enemies + clock + collision — kernel
    ├── gen.loft        # procedural dungeon generator     — kernel
    ├── monsters/classes/races/items.loft  # data tables   — kernel
    ├── wallgeo.loft    # wall outline (rounded active; DP parked) — derived geo
    ├── view.loft       # 2D egocentric renderer           — view
    ├── story.loft      # entry: window + loop + input      — view
    └── *test.loft      # selftest/montest/deftest/gentest/gridtest (headless)
```

`use <name>;` imports a dependency or sibling module. **No `kernel/` tree
imports graphics** — the invariant that keeps 2D/3D interchangeable.

---

## 16. Build & run

loft toolchain at `loft/target/release/loft`; deps resolved via
`--lib …/loft/lib/`. Use the loft-style **Makefile** (LOFT_REPO defaults to
`../loft`):

```sh
make play     # run in a window          make test   # headless self-tests + compile gate
make game     # single-HTML browser build make check  # quiet parse+bytecode gate
make shot     # Xvfb screenshot           make help   # all targets
```

(`--path` must end in `/`. Sandbox here can't grab the GL window — the user is
the visual verifier; headless logic is fully testable.)

---

## 17. Current state — what's built

- **M0 vertical slice** runs: generated hex map, continuous WASD with the
  rotating egocentric view, one hex-locked enemy ticking on travel distance,
  **collision with sliding + radius**, quit on Esc.
- **Data foundations:** monsters / classes / races / items tables (clean-room,
  tested, warning-clean).
- **Combat:** bump-melee, player/enemy HP, enemy-attacks-when-adjacent, death +
  game-over (`combattest`).
- **Procedural dungeon WIRED** (`sim_new_gen`): rooms + corridors populated with
  monsters from the DB by depth; monsters render as **glyph letters in colour**
  (`@` = player) on soft-black discs, with an HP readout + "YOU DIED" via the text
  bridge (font bundled in `assets/`). `gen.loft` itself is connectivity-verified +
  world-keyed.
- **Design specced** for **monster AI, placement & level structure** (§10a), the
  **HUD sidebar / stats / levelling** (§12a) and **items — drops / pickup /
  inventory** (§12b). Building the **foundation slice**: L1 stairs + real depth,
  A1 weighted placement, P1 awareness/vision/NEVER_MOVE.
- **Walls:** active `wallgeo.loft` = averaged/rounded silhouette (runs; the game
  is playable). The Douglas–Peucker straightener is **parked** at
  `patches/wallgeo-douglas-peucker.diff` (compiles, runtime-broken in the current
  loft interpreter — a nested-vector store panic — pending loft master fixes;
  base `60d523c`, source `8fcedc3`, replay in `patches/README.md`).
- **Headless tests** all green (`make test` = self-test + combat + wiring +
  compile; plus gentest, gridtest, deftest, montest).

---

## 18. Milestones

- **M0 — vertical slice** ✅ (built; visual confirm pending from user).
- **M1 — combat loop:** bump-melee, HP/death, wait, HUD, facing-cone FOV,
  game-over. Wire `gen` into the live game; spawn from `monsters` by zone level.
- **M2 — progression & world:** `Hero` struct + character creation (race/class/
  stats), inventory/equip from `items`; stairs + world-keyed multi-level
  descent; the feature-overlay processor (houses → roads → castles).
- **M3 — systems:** ZAngband realm magic (`spells.loft`), resistances,
  ego-items/artifacts, detection kit, monster speed; rock faces (semi-rounded).
- **M4 — 3D browser:** swap in `moros_render::camera_follow` (+ thick walls /
  towers / raised ramparts) over the unchanged kernel; ship single-HTML WebGL.

(Two threads wait on the loft master merge: the `wallgeo` runtime fix, then
intersection-based building corners.)

---

## 18a. TODO — ordered backlog

The canonical execution order (interleaves the per-section phases P*/A*/L*/H*/I*
by dependency + playability). Tiers are rough priority bands, ordered top→bottom.

### Done
- [x] **M0** vertical slice — continuous movement, rotating egocentric view, hex
  collision with slide + radius.
- [x] **Combat** — bump-melee, player/enemy HP, death + game-over.
- [x] **Dungeon wired** — `sim_new_gen` builds gen + spawns DB monsters; glyph
  rendering (`@`/letters in colour on backdrop discs), HP bar + numeric HP,
  "YOU DIED".
- [x] **P1** awareness — monsters spawn asleep, wake on `m_vision` + LOS,
  `NEVER_MOVE` holds.
- [x] **A1** placement — budgeted scatter, `get_mon_num` (rarity/depth/deepen/OOD,
  uniques excluded), `MF_GROUP` clusters, start-safe.
- [x] **L1** stairs + real depth — `>`/`<` features, deterministic per-depth
  descent (HP carry, arrival stair), `E` to use stairs, DEPTH readout.

### Now — make it feel like a roguelike
- [ ] **P2** noise flow-field pathing — Dijkstra-from-player so monsters route
  around walls (kills the greedy `best_step` wall-stick/clump). *Biggest AI gap.*
- [ ] **H1** Hero model + **XP on kill** + level-up (HP growth); promote
  `Sim.php` → `Hero`. *The core RPG loop.*
- [ ] **I1** floor gold + monster-death item drops + pickup (`g`); items as map
  glyphs.
- [ ] **FOV** — facing-cone field of view / fog of war.
- [ ] **Wait** action (`.`/Space advances one tick in place).

### Next — depth & UI
- [ ] **H2** character **sidebar** (name/race/class/level/xp/gold/6 stats/AC/HP/
  depth) + bottom status line.
- [ ] **I2** inventory `i` / equipment `e` screens; wield/wear/takeoff (+ AC &
  stat recompute); drop `d`.
- [ ] **P3** monster **speed/energy** (fast monsters run you down).
- [ ] **P4** movement modifiers — erratic, **fear/flee**, group-surround, breeder
  multiply.
- [ ] **Persistence** — unique-once (world-state) + **roster persistence on
  revisit** (cleared stays cleared; descent currently regenerates fresh).
- [ ] **Combat depth** — AC / to-hit / blow dice (expand `m_dam`); fear from a big
  hit.

### Later — systems & world
- [ ] **P5** casters + ZAngband **realm spell pool** (bolt/ball/breath/summon/
  heal/blink).
- [ ] **I3/I4** level-gen objects (`get_obj_num`) + quality tiers / `apply_magic`
  (ego); identification + flavours + use/consume effects.
- [ ] **H3** player SP/casting, conditions + status line, hunger clock.
- [ ] **L2** zone difficulty (`effective_level = zone + depth`).
- [ ] **L3** wilderness **overworld** surface + town (enter/exit dungeons).
- [ ] **L4** level profiles (cavern/maze) + special rooms (pit/nest/vault).
- [ ] **L5** bottom-level guardians + final boss.
- [ ] **P7 / A2 / H4 / H5 / I5** — smart/pack/doors/wall-pass; unique escorts;
  character creation; monster health-bar/look; artifacts + encumbrance.

### Eventually
- [ ] **L6** multi-layer height model (§7); the feature-overlay processor
  (houses → roads → castles), incl. the parked Douglas–Peucker straightener.
- [ ] **M4** 3D browser — `moros_render::camera_follow` over the unchanged kernel;
  single-HTML WebGL. *Blocked by `E0514` — see `LOFT_ISSUES.md` C15.*
- [ ] **Testing tiers** — `placestats` (main-stats-style distribution harness),
  Borg-style headless auto-player.
- [ ] Pick a final **game title + world name** (replace the placeholders).

---

## 19. Open questions

- Backward glide (`S`) speed; on-screen scale; exact FOV shape.
- Monster turn order within a tick (simultaneous vs. sequenced).
- "Current hex" tie-break on hex boundaries; save/determinism seed boundary.
- Naming: pick an original game title + world name (replaces "Angband/Amber"
  slots); `story`/`crawler` are placeholders.
