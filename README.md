# crawler

A clean-room, ZAngband-style **hex roguelike** written in the
[loft](https://github.com/loft-lang/loft) language — playable in 2D today, and
built so the *same* renderer-agnostic simulation kernel can drive a 3D browser
version later.

(The loft package is named `story`; `crawler` is the project/repo.)

## The world

![The contract wilderness — the game's overworld, rendered by the game's own world code](doc/world_loft.png)

The game's overworld — 13.5 × 9.1 km of contract wilderness, rendered straight
from the loft world code (`src/ovshot.loft` samples `overland.loft` at 10 m/px in
the in-game palette). Twin stone massifs under snow, the crater lake, grasslands,
fields and coastal sands; the markers are towns (ringed), ruins and wizard
towers. The depth-0 surface you walk is a 101×101-hex window of exactly this
map, and `ovmap.loft` prints the same world as a ZAngband-style character map —
one deterministic definition, every renderer agrees.

## Why — the anti-moros

`crawler` shares its world model with **moros** (the hex world + heights/layers +
walls/buildings/castles/roads/rock-faces, via `moros_map`/`moros_render`) — but
where moros builds that world **by hand through an editor** (a long content tail),
`crawler` reaches a **working, playable foundation much faster by *generating*
the world procedurally**. Same destination world; code- and generation-driven,
no editor dependency.

## The idea

- **Egocentric, continuous controls.** You glide and turn smoothly; the *world*
  rotates around you (you stay ~70% down the screen, facing up).
- **Distance-driven clock.** Time advances by how far you *travel* — every
  hex-length you move, the world ticks once. **Turning is free.**
- **Hex terrain + overlay structures.** Collision lives on the hex grid (cells,
  edge-walls, height); walls/buildings (12-dir, sharp 90°), roads (24-dir,
  rounded), castles (2-hex ramparts + round towers) and rock faces are a
  render overlay on top.
- **World-keyed & procedural.** Each place is generated deterministically from
  its world position; once visited its state persists, so re-entering restores
  it — and travelling to harder **zones** (not just deeper) drives difficulty.

The game runs on loft's **games kernel** (`engine_host`): a drift-free 60 Hz
fixed-tick loop, deterministic simulation quanta, and a wire so transparent that
`src/observe.loft` renders a live, bit-identical spectator view of a running game
from its intent stream alone (PLAN-KERNEL.md). The renderer is a probe-verified
GPU showcase — SDF wall strokes, baked-tint terrain mesh, a directed light cone
(RENDER.md / PLAN-RENDER.md).

See **[DESIGN.md](DESIGN.md)** for the full design.

## Controls

| Key | Action |
|---|---|
| `W` / `S` | glide forward / back |
| `A` / `D` | turn left / right (free — no time passes) |
| *(walk onto stairs)* | `>` descend · `<` ascend — no key; step off and back on to re-trigger |
| `.` / `Space` | wait one tick (enemies act, you don't move) |
| `G` | grab the items under you (gold auto-collects) |
| `C` / `I` | character page (spend stat points) / inventory hub |
| `1`-`9`, `Q`, `E` | use the bound quick-slot (potions, the bow, spells) |
| `N` | **next world** — re-scans dropped-in bundles, restarts into a fresh seed |
| `Esc` | quit |

## How to play

You are **`@`**. Glide with `W`/`S` and turn with `A`/`D` — the dungeon rotates
around you. Steer into a monster to attack it (pressing forward into it lands a
hit each tick); you trade blows until one of you dies. Kills earn **XP** — fill
the blue bar under the green HP bar to **level up** (more max HP). Find a **`>`**
down-stair and walk onto it to descend; deeper levels are tougher. The top-left HUD
shows HP, the XP bar + level (`CL`), and the dungeon **DEPTH** (top-right).

On the map:

| Glyph | Meaning |
|---|---|
| `@` (yellow) | you |
| letters (`r` `k` `o` `R` `g` …) | monsters — coloured & lettered by kind (rat, kobold, orc, frog, goblin, …) |
| `>` / `<` | down / up stairs |
| grey cells | rock / walls (the yellow outline traces the cavern edge) |

Monsters spawn **asleep** and wake when you come within sight, so you can
sometimes get the drop on them; once awake they path around walls to reach you.

## Build & run

Needs the **loft toolchain** checked out alongside this repo (defaults to
`../loft`; override with `make play LOFT_REPO=/path/to/loft`).

```sh
make play     # run the game in a window
make test     # headless, deterministic self-tests + compile gate
make game     # build a single self-contained story.html for the browser
make help     # list all targets
```

## Status

**Playable:** descend a procedurally generated, monster-populated dungeon, fight
in melee, gain XP and level up, and take stairs to deeper levels. Built so far:

- **Movement & view** — continuous egocentric glide/turn, distance-driven clock,
  hex collision with sliding + a player radius.
- **Combat** — bump-melee, HP, death / game-over.
- **Procedural dungeon + monsters** — rooms + corridors (world-keyed); monsters
  drawn from the DB by depth (rarity-weighted, packs, spawned asleep), rendered
  as coloured glyph letters on backdrop discs.
- **Monster AI** — awareness (sleep → wake on sight), `NEVER_MOVE`, and
  **flow-field pathing** that routes around walls.
- **Progression** — XP on kill (scaled by monster level), level-up, HP growth;
  HP / XP / level / depth HUD.
- **Levels** — `>` / `<` stairs, real depth, deterministic per-depth descent.

Plus clean-room **monster / class / race / item** data tables. The ordered
roadmap (next: items, the character sidebar, monster speed & fear) is the backlog
in **[DESIGN.md §18a](DESIGN.md)**.

## Layout

```
src/hexgeo.loft   hex geometry (axial)                 — kernel
src/gridgeo.loft  square geometry for 90° walls          — kernel
src/sim.loft      world + player + enemies + combat + AI + XP + stairs — kernel (no graphics)
src/gen.loft      procedural dungeon generator           — kernel
src/monsters|classes|races|items.loft   clean-room data tables — kernel
src/wallgeo.loft  wall outline (rounded active; DP parked in patches/) — derived geometry
src/view.loft     2D egocentric renderer                 — view
src/story.loft    entry: window + game loop + input       — view
src/*test.loft    headless tests
```

The `hexgeo`/`gridgeo`/`sim`/`gen`/data modules import no graphics; `view`/`story`
are the swappable 2D front-end. That invariant is what lets the same kernel drive
a 3D renderer (`moros_render`) later.

## Docs

- **[DESIGN.md](DESIGN.md)** — the full design: architecture (kernel/view split),
  world model, monster AI / placement / level structure, the HUD sidebar & items
  systems, and the ordered **TODO backlog** (§18a) that drives development.

## License

LGPL-3.0-or-later, consistent with the loft ecosystem.
