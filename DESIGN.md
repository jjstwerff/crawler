# `story` — Design Document

**Status:** Draft / pre-implementation
**Working name:** `story` (final game + world name TBD — see §13)
**Last updated:** 2026-06-02

---

## 1. Summary

`story` is a **clean-room, ZAngband-style roguelike** written in the **loft**
language. It plays in **2D today** and is designed to become a **3D browser
game** later, driven by the *same* renderer-agnostic **simulation kernel**.

Its defining twist is the control + time model: the player moves and turns
**smoothly and continuously**, enemies live on a **hex grid**, and the game
clock is **driven by how far the player travels** — not by wall-clock time.

---

## 2. Goals & Non-Goals

### Goals
- A **playable** roguelike — not a tech demo or a library. Something you can
  open, drive around, fight in, and lose.
- A **renderer-agnostic simulation kernel**: all rules/state, zero rendering.
  The 2D view and the future 3D view are interchangeable front-ends over it.
- **2D now → 3D browser later** with no rewrite of the kernel.
- **Deterministic** simulation (drives testing, replay, and netcode later).
- **No intellectual-property risk** (see §3).

### Non-Goals (for now)
- Faithfully reproducing ZAngband's exact content, balance, or square-grid feel.
  We clone *mechanics*, not the game.
- Multiplayer, persistence/save-scumming policy, mod support — later, if ever.
- A bespoke 3D renderer — we reuse `moros_render` (see §4).

---

## 3. Intellectual Property — clean-room policy

**Game mechanics and systems are not copyrightable; names, art, text, and
specific lore are.** So we copy the *systems* freely and invent all the
*fiction*.

**Banned (third-party IP):** any Tolkien name (Angband, Morgoth, Sauron,
balrog, Nazgûl/ringwraith, ent, Shelob, the One Ring, "hobbit", …) and any
Zelazny/Amber name (Oberon, Amberites, the Pattern, Trumps, Serpent of Chaos,
Courts of Chaos). Use **"halfling"** not "hobbit".

**Safe to reuse verbatim:** depth-based dungeon progression, XP/leveling,
stats/HP, resistance grids, ego-items/artifacts-as-a-concept, monster
"uniques" as a concept, spell schools, the bump-to-attack convention, the
inventory model. The D&D-generic class/race scaffolding (warrior/mage/priest/
rogue/ranger; human/elf/dwarf/gnome/halfling) is fine.

All original content lives in data files so it is auditable and swappable.
*(The existing `moros_*` libraries were checked and contain zero such names.)*

---

## 4. Foundation — reuse the `moros` stack

The `moros_*` loft libraries (`/home/jurjen/workspace/loft/lib/`) are a **3D
hex-world editor stack**, not a roguelike. We reuse the parts that are already
renderer-agnostic and 3D-capable, and build the missing simulation on top.

| Library | What it is | Our use |
|---|---|---|
| `moros_map` | Hex world model: per-hex height/material/walls/items, q/r/cy chunks, JSON. **No graphics dependency.** | **Reuse** as the terrain/world store. Each dungeon level = one map (or layer). |
| `moros_render` | Hex world → 3D mesh → GLB → WebGL; `camera_follow` (third-person behind a facing player). | **Reuse later** as the 3D front-end. |
| `moros_editor` | Undo/redo + stencils on a map. No graphics. | Optional, for authoring levels. |
| `moros_sim` | Continuous `Player` (`pl_facing`) + `resolve_move` continuous-vs-hex collision — **real-time**, and **imports graphics**. | **Do not depend on** (it pulls graphics). Reimplement the small bit of continuous/hex collision we need, graphics-free, in the kernel. |
| `moros_ui` | 2D editor toolbar/panels. | Not used. |

**Missing — i.e. what we build:** turn/clock engine, actors with stats+HP,
combat, field-of-view, inventory/items, dungeon generation, and the game loop.
That is *the kernel*.

---

## 5. Architecture — kernel / presentation split

```
            ┌─────────────────────────────────────────────┐
            │  story-kernel   (pure loft, NO graphics dep) │
            │  hex world (moros_map) · continuous player · │
            │  hex-locked enemies · distance clock ·       │
            │  combat · FOV · items · dungeon gen          │
            │  → exposes read-only state + step(input)     │
            └───────────────┬─────────────────┬───────────┘
                            │                 │
             ┌──────────────▼──────┐   ┌──────▼───────────────────┐
             │  view-2d (NOW)      │   │  view-3d (LATER)         │
             │  graphics package:  │   │  moros_render:           │
             │  rotate world to    │   │  camera_follow behind    │
             │  player heading,    │   │  the player; same kernel │
             │  glyphs/tiles, HUD  │   │  state, 3D meshes         │
             └─────────────────────┘   └──────────────────────────┘
```

**Hard rule:** the kernel never references a draw call, window, or input
device. It takes an **input intent** (turn rate, move intent, action) plus a
frame delta, advances state, and exposes **read-only state** (player pose,
visible hexes, actor list with interpolation, log messages). Swapping renderers
must require zero kernel changes.

**Spatial model:** the kernel works in a **continuous 2D plane over an axial
hex grid**. Player position is a float `(x, y)` on that plane + a heading
angle. Height (the 3rd dimension) is **purely a rendering concern** pulled from
`moros_map` by the 3D view; the kernel is 2D. The kernel needs a small
**graphics-free hex-geometry module** (axial/cube coords, neighbors, distance,
`world↔hex`, hex line) — written in pure loft, not borrowed from the
graphics-dependent `moros_render`.

---

## 6. World model

- A dungeon **level** is a `moros_map` populated by the generator (§11): floor
  hexes, wall edges, doorways, stairs down/up, items, spawn points.
- Coordinates: **axial `(q, r)`** for hexes; continuous `(x, y)` for the player.
- **Hex layout = moros's default.** Reuse its constants and mappings verbatim so
  the kernel and `moros_render` agree: offset-rows at unit size, with
  `HEX_WIDTH = √3`, `HEX_ROW_HEIGHT = 1.5`, `x = q·√3 + (r mod 2)·(√3/2)`,
  `z = r·1.5`, and moros's 6 axial neighbor offsets. *Caveat:* the geometry is
  actually **pointy-top** (a vertex points up/down, flat edges left/right) —
  moros's own comments mislabel it "flat-top"; defer to `hex_to_world`, not the
  label.
- **"Hex length" `L`** = center-to-center distance between adjacent hexes
  `= HEX_WIDTH = √3` (all 6 neighbors equidistant). `L` is the unit of the game
  clock (§8), and the clock accrues **path length travelled** — wiggling costs
  time; net displacement is irrelevant.
- **Two kinds of wall** (moros's model, both supported):
  1. **Solid full-hex wall** — a non-walkable hex cell (the classic Angband
     granite block); this is the primary, original-game look.
  2. **Edge walls** — thin barriers on a hex *edge* (doorways, railings).
     Stored on 3 canonical edges per hex (N/NE/SE); the other 3 edges belong
     to the neighbour (so each physical edge is stored once).
  A move A→B is blocked if **B is solid** *or* the **shared A–B edge** carries
  a wall — this is moros's `blocked_by_wall` collision, applied to the
  continuous player as it crosses a hex boundary.
- 3D later: full-hex walls become raised hex columns; edge walls feed
  `moros_render`'s `emit_wall_quad` along the edge. 2D now: full-hex walls are
  filled cells; edge walls are short segments between the edge's two corners.

### 6a. Full world model (target — mirrors `moros_map`)

The terrain is ultimately a **stack of layers (`cy`) with a per-hex centre
height (`h_height`)**, exactly `moros_map`'s shape — so the kernel just carries
the fields and `moros_render` draws them (`y = h_height * HEIGHT_SCALE`, slopes
via `emit_slope_face`, layers stacked). This grows the *terrain* data
(height + layer index), but it's additive and 1:1 with `moros_map` (free 3D
hand-off). Walls are the **silhouette of solid hex regions** (Angband's
carved-from-rock model): trace the solid/open boundary per layer, straighten
the contour to the 12 directions (averaging the per-hex wobble, mitring real
corners — a pure mesh-layer pass, **no wall-data change**), and extrude each
face from its floor height to the ceiling. Height *deltas* between adjacent
floor hexes are slopes/cliffs, not walls. The 12-direction straightening is a
2D op per layer; height only sets the y-extrusion.

Surfaced for later milestones: step-up limit + climb cost vs. the distance
clock; height-aware FOV (tall hexes block sight); layer traversal (stairs) and
what the 2D view shows (one layer at a time, height as shading).

### 6b. World structure — wilderness overworld + dungeons (ZAngband-style)

The world is a **wilderness overworld** — a large surface hex map (terrain,
height, towns, dungeon entrances) you travel across continuously — plus
**dungeons** (separate hex maps of descending levels) entered from points on it.
This matches `moros_map` directly: the overworld *is* a `moros_map` and can be
**hand-authored in the moros editor + loaded as JSON** (hand-crafted overworld +
procedural dungeons), and `moros_render` draws both in 3D. The continuous-player
+ distance-clock model applies on the overworld too (glide across terrain,
distance ticks the clock, wilderness encounters). The kernel gains a **current
map** + **transitions** (enter dungeon, descend/ascend, recall) — additive over
the world model; the view treats overworld and dungeon identically, only the map
swaps. This is an M2/M3 system; M0/M1 stay on a single dungeon test map.

**Source-of-truth for logic (decided):** **hybrid** — **modern Angband (4.2.x)**
for the core engine *and* the **monster & object rules/data** (`monster.txt` /
`object.txt` flag sets, resistances, ego/affixes, combat, AI, stats, HP,
XP/leveling, FOV — cleanest to reproduce faithfully); **ZAngband** for **world
structure & flavor** (wilderness now; realm-based magic + the full ZAngband
**spell pool**; mutations later). Mechanics are GPL/free to clone; only names
stay clean-room (§3).

**Spell ↔ monster/object compatibility:** compatible. Both are Angband-derived,
so every spell (player or monster) resolves as an *effect/projection* the
target resists and saves against, and that can affect objects. ZAngband
supplies the spell **catalog** (realms × books × spells + mana/fail/level +
each spell's effect); execution runs through modern Angband's
effect/projection/resistance/save machinery. Work needed: map ZAngband's
element/effect types → modern projections, and implement the few ZAngband-unique
effects (Chaos/Trump/Death). Monster casting stays modern; the player's magic is
the ZAngband realm system; they meet at the shared effect layer. Consequence:
the current `monsters.loft`/`items.loft` are placeholders to **align to modern
Angband's `monster.txt`/`object.txt`** — which is also what makes them
spell-ready (resist/type flags are what spells query).

---

## 7. Actors

### Player — continuous
- State: continuous position `(x, y)`, continuous heading θ, plus derived
  *current hex* (the hex containing `(x, y)`).
- Moves and rotates **smoothly** (see §9). Occupies whichever hex contains its
  position; combat/adjacency use that hex, not the sub-hex offset.

### Enemies — hex-locked
- Logical position is always a **hex center** `(q, r)`. They move **one hex per
  tick** and **animate smoothly** between centers.
- They **attack into the whole hex** the player currently occupies — you cannot
  dodge a melee by hugging a hex edge.
- Smooth glide is **keyed to the player's accrued distance**, not wall-clock
  (see §8): as the player covers a hex-length, each moving enemy slides one hex.

---

## 8. The distance-driven clock — core mechanic

**The player's accumulated travel distance is the master clock.**

- Maintain `accrued` = total path distance the player has translated.
- Each time `accrued` crosses a multiple of `L` (one hex-length), fire **one
  world tick**: every enemy decides and commits one hex step / attack, status
  effects advance, regen ticks, etc.
- **Turning covers zero distance ⇒ advances zero ticks.** That is precisely why
  "turning is free in time." Standing still (or only turning) **freezes** the
  world.
- The fractional progress `frac = (accrued mod L) / L ∈ [0,1)` drives enemy
  glide interpolation, so the player and enemies animate in lockstep with **no
  wall-clock dependence** → fully deterministic.
- **Wait** action advances exactly one tick in place (needed for regen / luring
  monsters, since standing still otherwise stops time).

This makes the sim a turn engine wearing a real-time coat: smooth to play,
discrete and deterministic underneath.

---

## 9. Controls & camera

### Controls (all analog / held; release stops **immediately** — no inertia)
| Key | Action | Costs time? |
|---|---|---|
| `W` | glide forward along heading | yes (distance ticks the clock) |
| `S` | glide backward (no turn) | yes |
| `A` | turn left, continuous | **no** |
| `D` | turn right, continuous | **no** |
| `.` / `Space` | wait one tick in place | yes (1 tick) |
| *(bump)* | glide forward into an enemy's hex = melee attack | yes (1 tick) |

Heading is a **continuous float at any angle** — there is no 30° quantization;
the "30°" we discussed is just turn *rate/feel*. Turning rate and glide speed
are real-time (for animation); only **distance** advances the game clock.

### Camera — egocentric, forward-biased
- The **world rotates around the player** so the player's heading is always
  "up" the screen. The player never visually spins; the world does.
- The player is anchored **~70% down the screen** (not the bottom edge) so
  there is a margin of **rear visibility** — something creeping up behind you
  can be seen.
- 3D later: this is exactly `moros_render::camera_follow` (third-person behind
  the facing player). Same model, different projection.

### Field of view
- **Wide forward arc** (you see far ahead) **+ a short all-around radius** (you
  always see immediately adjacent hexes, including behind). Net effect:
  exploration is directional and tense; a distant enemy can flank you unseen,
  but cannot pounce from point-blank without warning.

---

## 10. Combat, FOV & initial defaults

Decisions made to keep the first build moving; revisit during tuning:
- **Bump-to-melee:** moving forward into an occupied enemy hex is the attack.
- **Monster speed:** everyone moves 1 hex/tick to start. Add an Angband-style
  speed multiplier later (fast monsters cover >1 hex per player hex-length).
- **FOV:** forward arc + small all-around radius, recomputed per tick (and
  visually per frame from the player's continuous pose).
- **Combat math:** placeholder (attack vs. AC + damage roll) in the first
  slice; the real stat/resistance system lands with §11.

---

## 11. Roguelike systems (clean-room, roadmap-level)

Cloned ZAngband-style systems, all original-named and data-driven:
- **Descent:** numbered dungeon levels of increasing depth; stairs up/down;
  depth scales danger and loot.
- **Stats & progression:** core attributes, HP/mana, XP and levels, classes,
  races (generic D&D scaffolding).
- **Items:** weapons/armor/consumables, ego-items and artifacts (original
  names + effects), identify, inventory & equip slots.
- **Monsters:** a data table of monster types with stats/behaviors and
  original "unique" bosses; spawn by depth.
- **Magic:** spell schools / spellbooks, resistances and elements.
- **Detection/utility:** mapping, detection, teleport — classic roguelike kit.

These are explicitly *later* milestones; the kernel is structured so each plugs
in as a system over the same state.

---

## 12. Loft package layout

A loft package (`loft.toml` + `src/*.loft`), run against the loft toolchain
with `--lib /home/jurjen/workspace/loft/lib/` for `moros_map` / `graphics`.

```
story/
├── loft.toml                 # [dependencies] moros_map, graphics (view only)
├── DESIGN.md
└── src/
    ├── story.loft            # entry: window + game loop, wires kernel↔view
    ├── kernel/               # NO graphics import anywhere under here
    │   ├── hexgeo.loft       # axial/cube hex math, world↔hex, line, neighbors
    │   ├── world.loft        # level state over moros_map; FOV
    │   ├── player.loft       # continuous pose + distance accrual
    │   ├── actors.loft       # hex-locked enemies, stats/HP, AI step
    │   ├── clock.loft        # distance→tick driver
    │   ├── combat.loft       # attack/damage resolution
    │   ├── items.loft        # inventory/equip (later)
    │   └── gen.loft          # dungeon generation
    └── view2d/
        └── render2d.loft     # graphics: world-rotation, glyphs/tiles, HUD, input→intent
```

`use <name>;` imports a dependency or sibling module; `use` lines precede all
other declarations. **The `kernel/` tree must not `use graphics;`** — that is
the invariant that keeps 2D and 3D interchangeable.

---

## 13. Build & run

Toolchain is prebuilt at `loft/target/release/loft`.

```sh
# 2D, native:
loft --native-release --path /home/jurjen/workspace/loft/ \
     --lib /home/jurjen/workspace/loft/lib/  story/src/story.loft

# 2D, single-HTML for the browser:
loft --html story.html --path /home/jurjen/workspace/loft/ \
     --lib /home/jurjen/workspace/loft/lib/  story/src/story.loft
```

(`--path` must end in `/`. See loft's Makefile `play`/`game` targets; the
brick-buster game at `loft/tools/brick-buster/` is the reference.)

**Naming TODO:** pick an original game title and a world name (replaces every
"Angband/Amber"-shaped slot). Until then, `story` is the placeholder.

---

## 14. Milestones

- **M0 — Vertical slice (first build):** generated hex room/corridor map;
  hold `W`/`A`/`D` to glide and rotate the world around you (player anchored
  ~70% down); one hex-locked enemy that ticks forward each hex-length you
  travel; collision with walls; quit on Escape. Proves the kernel↔view split
  and the distance clock end-to-end.
- **M1 — Combat loop:** bump-to-melee, HP/death, the wait action, a HUD, FOV
  (forward arc + rear radius), game-over.
- **M2 — Roguelike depth:** stairs + multi-level descent, a monster data table,
  basic items + inventory, stat/XP/leveling.
- **M3 — Systems:** magic/resistances, ego-items/artifacts, detection kit,
  monster speed multiplier.
- **M4 — 3D browser:** swap in `moros_render::camera_follow` over the unchanged
  kernel; ship a single-HTML WebGL build.

---

## 15. Open questions / deferred decisions

- **Backward glide (`S`):** same speed as forward, or slower? Does it tick the
  clock identically? (Assumed: yes, identical.)
- **On-screen scale:** pixels per hex in the 2D view (view-only tuning).
- **FOV exact shape:** arc half-angle, forward range, rear radius — tuning.
- **Monster turn order** within a single tick (simultaneous vs. sequenced).
- **Diagonal-of-continuous-movement:** what "current hex" means exactly on hex
  boundaries (tie-break rule).
- **Save/determinism boundary:** seed handling for reproducible runs.
