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
- **Procedural generator** (`gen.loft`): rooms + corridors, connectivity-verified,
  world-keyed — not yet wired into the live game.
- **Walls:** active `wallgeo.loft` = averaged/rounded silhouette (runs; the game
  is playable). The Douglas–Peucker straightener is **parked** at
  `patches/wallgeo-douglas-peucker.diff` (compiles, runtime-broken in the current
  loft interpreter — a nested-vector store panic — pending loft master fixes;
  base `60d523c`, source `8fcedc3`, replay in `patches/README.md`).
- **Headless tests** all green (`make test`, gentest, gridtest, deftest, montest).

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

## 19. Open questions

- Backward glide (`S`) speed; on-screen scale; exact FOV shape.
- Monster turn order within a tick (simultaneous vs. sequenced).
- "Current hex" tie-break on hex boundaries; save/determinism seed boundary.
- Naming: pick an original game title + world name (replaces "Angband/Amber"
  slots); `story`/`crawler` are placeholders.
