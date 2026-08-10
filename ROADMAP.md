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
- **Showcase 2D GPU renderer** (**RENDER.md**) — doctrine: crawler showcases the best
  2D primitives possible on a modern GPU. **Tier A is SHIPPED** (world VBO + shader
  FOV + tint bake R4 + SDF wall strokes R5 + light-cone post-fx R6 — every world
  pixel GPU-computed, probe-verified); next the instanced tier (floor R7, one-call
  sprite batch R8 — absorbs the sprite atlas) behind
  the `graphics` flow-backs (EXTRACTION.md § GPU 2D primitives, which also carries the
  simple-verbs-over-batched-backend painter API). `moros_render` 3D-bridge groundwork.
  Step plan + verification channels: **plans/7-render/**.
- **The platform track** (crosscutting, largely SHIPPED 2026-06-12): the games
  kernel owns the loop (drift-free ticks, idle backoff), crawler hosts a live
  spectator (`observe.loft`, bit-identical replica), N = next world re-scans
  bundles, and shipping distance is mapped — **plans/6-games-kernel/**.

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
- **Multiplayer** — the foundations SHIPPED with the platform track (K1 fixed
  quanta + K2's intent wire: a live observer renders a bit-identical replica
  today); MP proper = K4 in plans/6-games-kernel/ (intents flow both ways; the G4 save
  format doubles as the net/replay snapshot).

## The path in one line

**M-Core shipped** (commit `d1ecc56`, "FOV … M-Core complete") and much of Phase 2–4 with
it — sprites, the inventory hub, quests, ranged, quickslots, classes/races, the shrine, the
overland, caves, travel, persistence, the games-kernel host and a live replica observer. The
per-item checkboxes in `DESIGN.md` §18a lag reality; treat the gate in `tools/run_tests.sh`
as the truth.

**The active roster is three, decided 2026-08-09 from evidence** — `#11` 3D world · `#13`
scoped identity · `#17` safe supply (`plans/README.md` → *The active roster*; the cap is
three). ⚠ **This section named plan #11 as "the immediate next step" until 2026-08-10**; the
work is currently in **`#17`**, whose `S0`–`S2` are shipped. What is being worked *right now*
is **[STATE.md](STATE.md)**, not this file — ROADMAP is the through-line, not the schedule.

**Plan #11 — the 3D world view** remains the structural decision (2026-07-22): the hex FIELD
built by plans #5/#9/#10 becomes the world the player stands in, first-person, and 3D
replaces the 2D view. That reorders Phase 5's "3D as the moros future" into the present, and
it absorbs the remaining renderer work: `RENDER.md`'s showcase-2D doctrine and plan #7's
instanced tier apply to a renderer being retired, so only its **substrate flow-backs** into
`graphics` still earn their keep. Its next piece is a `hexbody` job, not a crawler one.

An **in-world editor**, built outside crawler, rides the same decision — which puts library
**extraction on the critical path** rather than after the game. Extraction has since largely
*happened*: `hex_grid`/`hex_field`/`hex_edge`/`hex_way`/`hex_roof` are consumed from the
registry and the crawler forks are deleted. Contract: `EXTRACTION.md` → *The editor as the
second consumer*.

Plan + the seven invariants: **plans/11-3d-world/**.
