# SLICE.md — the publishable vertical slice ("Crystal Descent")

A rough-but-complete cut of the game we can **publish in the current format** (the WebGL
single-file `make game` → `story.html`, plus native `make play`). Goal: a coherent loop someone
can actually play end-to-end — not feature-complete, but it *works*.

## The experience
You open on an **empty desert** — an open, unended expanse — with a **spawning crystal beside
you** and a **dungeon entrance** nearby. Walk in → dive the **classic beginner dungeon** → fight
the bestiary, loot, level up, descend deeper → die → **respawn at the checkpoint** and keep diving.

## Core principle — reuse, build no new big systems
- The **desert is depth 0**: a special *open all-floor* level (the "empty, unended place"), not a
  real overworld. Cheapest possible surface.
- The **entrance is a down-stair** — we already walk onto stairs to descend; `0 → 1` enters the
  dungeon, which already works (generation, persistence, combat, loot, XP, respawn).
- The **world-bundle link** (desert as a `kind:world` place linking to `classic`) is the *proper*
  future home; depth-0-as-surface is the rough shortcut and play won't change when we migrate.

## Steps  (each small, additive, gated, headless-testable — gate stays green throughout)

- [ ] **1. Surface place (depth 0 = the desert).** Special-case `sim_new_gen` at depth 0: an
  all-floor open expanse, player at centre, no rooms/corridors. Reuses the tile grid + FOV.
  *Test:* depth 0 generates open, player placed.
- [ ] **2. The entrance.** Place a **down-stair** a few hexes from the player; walking onto it
  descends `0 → 1` into the classic beginner dungeon. Reuses walk-onto-stairs + `sim_descend`
  (persistence already works). *Test:* descend 0→1 lands in the dungeon.
- [ ] **3. The spawning crystal.** A crystal feature beside the player. **Rough v1: pre-place a
  small knot of weak monsters around it at gen** (reads as "the crystal's spawn"; reuses placement;
  **zero runtime growth**). *Test:* the crystal's monsters are present on the surface.
  - *v1.1 (later):* a live ticking spawner needs the enemy array to become a fixed-cap + count
    store (a C18-safe refactor) before it can grow at runtime.
- [ ] **4. Open on the surface.** `story.loft` / `sim_new` starts the player at **depth 0** with
  the crystal + entrance (instead of dungeon depth 1); the chosen character bundle still applies
  its kit. *Verify:* `make play` opens on the surface.
- [ ] **5. Ship it.** Confirm `make game` → `story.html` builds and the loop plays end-to-end
  (surface → descend → fight/loot/level → die → respawn). Existing HUD + checkpoint-respawn give it
  shape; optional rough **score = deepest depth reached**.

## Deliberately NOT in this slice (defer)
- The **world-bundle link mechanism** (depth-0 surface is the shortcut; migrate later, play unchanged).
- **Monster special attacks** — melee-only is the rough combat; `MF_CASTER` stays decorative for now.
- **Per-monster loot** (generic depth-drop is fine), and the **quest / overlay / serpent** richer scenario.

## Risk notes
- Steps 1, 2, 4 are additive + low-risk (reuse stairs/descend/tiles/FOV).
- Step 3's *live* spawner is the only thing that hits loft's C18 (enemy-array growth) — hence the
  pre-placed-knot v1; the runtime spawner is v1.1.
- All steps keep the determinism-preserving pattern, so the existing gate stays green.

## Ship criterion
`make game` produces a `story.html` where a player can: start on the desert, reach the entrance,
descend, fight + loot + level, die, respawn, and keep going. Rough art (glyphs), melee-only
threat, no surface beyond the open desert — but a real, coherent loop.
