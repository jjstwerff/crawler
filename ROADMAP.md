# ROADMAP.md — the path to a working game

The through-line from the design to a game you can actually play. This is the
*synthesis* layer; the detail lives elsewhere and this points at it:

- **Identity / pillars:** DESIGN.md **§3a** (accessible action-roguelite — "Angband
  bones, friendly tuning"; Zelda exploration + Souls challenge, no permadeath).
- **Ordered backlog:** DESIGN.md **§18a** (the per-task list these milestones group).
- **Authored content / 3D (future):** BUNDLE.md, STENCILS.md (moros-side).

## What "a working game with the features we want" means

One coherent run: you **explore** a dungeon with fog-of-war, **fight** with
attack-on-push, **find and equip gear that defines your playstyle** (lateral
progression) on a **gentle** level curve, and on death **respawn at a save point**
(your class's home/bed) instead of permadeath. That core — **M-Core** below — is the
spine; open-world zones, authored content, 3D, and multiplayer all build on it.

## Done — the foundation

- **Design identity locked** — §3a's 10 pillars.
- **Build order re-sequenced** (§18a).
- **Sprite pipeline + crawler's own `tools/draw.py`** (transparent rendering) validated;
  **first spider integrated** (compiles + `make test` 9/9; *visual verify still pending
  in `make play`*).
- The **rotation + scale placement primitive** (`view::draw_texture_rot`, 12/24-direction)
  — the moros placement model, proven in 2D.

## Phase 1 — the core loop → **M-Core** (this *is* "a working game with progression")

Build in order; each is small + headless-tested where it's kernel logic.

1. **G1 — nice walls** *(graphics cleanup, do first)* — land the parked Douglas–Peucker
   straightener directly (the loft bugs it was parked on are fixed). Palette
   is already warm-stone floor / dark walls.
2. **G2 — gentle curve** — flatten the level curve + cap the player↔monster ratio both
   ways (§3a #2). `curvetest`.
3. **G3 — equipment + starting loadout** *(the linchpin)* — wield/effects so **items are
   the progression** (§3a #3/#4); first lateral-item tuning of `items.loft`; the loadout
   seeds the class-as-kit (BUNDLE.md).
4. **G4 — save points + respawn** — home/bed = first save point; death keeps the
   character (XP/items), loses the dive (§3a #5). `savetest`.
5. **FOV** — facing-cone fog-of-war on `hex_los`.

→ **M-Core: a real game** — explore · fight · gear-up · gently level · respawn.
**Stop and playtest here.** This is the spine everything else hangs on.

## Phase 2 — texture & feel → **M-Feel** (make M-Core good)

- **Doors** (bump-open / locked / jammed; block LOS+move).
- **Combat juice** — knockback on hit + **fear/flee** via the flow field (no new buttons).
- **H2 sidebar** + **I2 inventory/equip UI** + **P3 monster speed**.
- **Onboarding pass** (§3a #8) — seed each early floor with **one mechanic "first"** (a
  door, a capability item, a fleeing pack, a save point, a hazard) so the early game
  *teaches itself* instead of being filler — a novelty curve, not just a difficulty one.
- **Persistence** — cleared-stays-cleared on revisit (distinct from G4 respawn).
- **Full-GPU 2D renderer** (**RENDER.md**) — world VBO + sprite atlas + shader FOV
  replace per-frame immediate emission; folds in the `tools/draw.py` atlas and is the
  `moros_render` 3D-bridge groundwork. One focused task, *after* the kernel FOV (which is
  renderer-agnostic and feeds both paths). All primitives confirmed present in
  `graphics.loft` (`gl_upload_vertices`, `SpriteSheet`/`draw_sprite`, `gl_load_texture`,
  shaders + `mat4` uniforms).

## Phase 3 — the world → **M-World** (player-chosen difficulty, §3a #9)

- **L2** zone difficulty (`effective_level = zone + depth`).
- **L3** wilderness overworld + town (home base / save points placed in the world).

→ gentle ↔ harsh zones you navigate at your own pace — open, skill-gated difficulty.

## Phase 4 — depth & content

- **Combat depth** (AC / to-hit / blow dice), **casters + spells** (P5), movement
  modifiers (P4).
- **Lateral items + their system hooks** — lantern→FOV, crowbar→doors, weapon-weight→
  knockback; more monsters/items as lateral variety.
- **Mass sprites** *(bonus / parallel art track)* — replace glyphs across the catalog via
  the validated `tools/draw.py` pipeline (real-world recognition bar, dark silhouettes +
  eye-glints, rotated/scaled), when you want the visual upgrade. *Eventually a sprite-sheet
  atlas for efficiency.*

## Phase 5 — authored content · 3D · multiplayer (moros / future)

- **Authored content** — the bundle/stencil/quest/castle/motif architecture (BUNDLE.md,
  STENCILS.md): pool → stencils → sets → places → quests → motifs. moros-side.
- **M4 — 3D** (`moros_render`): the validated rotation/scale/12-24-direction model goes
  native; the renderer-agnostic kernel drives it unchanged.
- **Multiplayer** — the door §3a deliberately left open (persistent characters,
  seed-deterministic shared world, flat-curve co-op, `loft-libs-net`).

## The path in one line

Finish **Phase 1 (G1 → FOV) = M-Core**, playtest, then layer **feel → world → depth**,
with **authored content + 3D** as the moros future.

**Immediate next step: G1 — nice walls**, then straight down Phase 1.
