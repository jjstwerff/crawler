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

- [x] **1. Surface place (depth 0 = the desert).** Special-case `sim_new_gen` at depth 0: an
  all-floor open expanse, player at centre, no rooms/corridors. Reuses the tile grid + FOV.
  *Test:* depth 0 generates open, player placed.
- [x] **2. The entrance.** Place a **down-stair** a few hexes from the player; walking onto it
  descends `0 → 1` into the classic beginner dungeon. Reuses walk-onto-stairs + `sim_descend`
  (persistence already works). *Test:* descend 0→1 lands in the dungeon.
- [x] **3. The spawning crystal.** A crystal feature beside the player. **Rough v1: pre-place a
  small knot of weak monsters around it at gen** (reads as "the crystal's spawn"; reuses placement;
  **zero runtime growth**). *Test:* the crystal's monsters are present on the surface.
  - *v1.1 (later):* a live ticking spawner needs the enemy array to become a fixed-cap + count
    store (a C18-safe refactor) before it can grow at runtime.
- [x] **4. Open on the surface.** `story.loft` / `sim_new` starts the player at **depth 0** with
  the crystal + entrance (instead of dungeon depth 1); the chosen character bundle still applies
  its kit. *Verify:* `make play` opens on the surface.
- [x] **5. Ship it.** Confirm `make game` → `story.html` builds and the loop plays end-to-end
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

## Status — SHIPPABLE ✅
All 5 steps done. `make game` builds `story.html` (~2.9 MB, the WebGL single-file). Headless
`surfacetest` proves the surface (open, crystal+knot of 5, entrance) + descend into the populated
dungeon; the whole gate stays green.

- **Build note:** the WebGL build (`--html`) compiles with the rustup-default toolchain (rustc
  1.96), so loft's wasm `libloft.rlib` must be built with the same — loft2 pins `stable` (1.95),
  so rebuild it with `cargo +1.96.0 build --release --target wasm32-unknown-unknown --lib
  --no-default-features --features random` in `../loft2` if `make game` ever hits E0514 again.
- **Visual check is the user's:** the sandbox can't reliably screenshot the GL frame — the
  headless logic is proven; how the desert / crystal / entrance actually *look* in `make play` /
  `story.html` is yours to confirm.
- **Principle — content stays faithful; build SYSTEMS to realize it** (CLAUDE.md). Things that
  look "inert" are SYSTEM gaps, never content to nerf: the floating eye keeps `dam 0` + its gaze —
  we build the gaze (special-attacks), we do NOT give it a bite; a Scroll of Teleport stays a
  teleport — we build the use-effect path, we do NOT make it do nothing. So the backlog below is
  *systems*, and every monster/item is authored to its true Angband design now.
- **v1.1 follow-ups (all SYSTEMS):** the full use-item effect dispatch + its supporting systems
  (heal/teleport/detect exist; speed→haste, restore→restore_stat next; identify/recall/mapping/food
  need ID/recall/mapping/hunger); monster special attacks (gaze/cast/breath/drain → realizes the
  floating eye + the casters); player status conditions; the live ticking crystal spawner (needs the
  enemy array as a fixed-cap store); the world-bundle link.

## Beyond the slice — making the full Angband experience functional

The slice proves the loop; these turn it into the full game. Each item notes what EXISTS vs what
is NEEDED, so it stays an honest backlog. (Cross-refs the DESIGN §18a backlog.)

### Tier 1 — depth on the existing loop (the four to do first)
- **Levelling.** ◑ KERNEL DONE: max HP grows per level (`hero_maxhp`), and each level-up **banks a
  stat-growth point** (`stat_pts`) the player spends by choice (`sim_raise_stat` / `Player.raise_stat`)
  — never forced, **deferrable** (hoard + time a raise), capped to **once per `STAT_COOLDOWN` (3)
  levels per stat** so no dumping. (Faithful to Angband: stats don't auto-grow; potions are the
  other path.) NEED: the in-game **level-up choice prompt** (browser UI — pick a stat / defer) +
  "you reached level N" feedback. Skill bumps fold in with the passive-skills item.
  - **Pairs with → item STAT REQUIREMENTS + BONUSES** (the common RPG system → an emergent PUZZLE):
    items both *gate* on a minimum stat (heavy blade needs STR, spellbook needs INT…) **and** *grant*
    +stat while worn (gloves +2 STR…). Effective stat = current + temp + **equipment** — a 4th layer
    in `refresh_stats`; a requirement checks the *effective* value. So a +STR item can satisfy
    another item's STR gate: the player **juggles gear** (wear the +STR ring to wield the STR-locked
    sword), while banked stat points let them break a dependency *permanently*. Build after passive
    skills. Edge to handle: removing the enabler while the gated item is still worn.
- **Inventory.** HAVE: the data model (fixed array, slots, `give_item`/`equip`, floor pickup).
  NEED: the in-game inventory *screen* — browse / select / wield / drop / examine — plus item
  stacking (weight/encumbrance optional).
- **Use item.** HAVE: `use_item` + the effect-script dispatch + 2 effects (heal, detect).
  NEED: effects for the whole usable set (potions, scrolls, wands/staves, food) and the
  select-from-inventory UI to invoke them live.
- **Passive skills.** HAVE: `grant_skill` / `grant_save` API — but STUBS (no store).
  NEED: a real per-player skill store + derivation (class/level/stat) and the skills *feeding
  outcomes*: to-hit / to-dam (melee), saving throw, stealth (aggro range), device, disarm.
  The biggest of the four — currently nothing is backed. *(Melee skill shipped: `sim_skill_melee`.)*

### The Character Page — explain + level up (one shared-view screen)
One page, opened any time (e.g. `C`), is the home for **three things at once**: the **character
sheet**, the **glossary** (a one-line explanation beside every term), and the **stat level-up**
(spend banked points here — never a forced prompt; you open it when you choose). Lives in
`view.loft`/`story.loft`, so **native GL *and* WebGL both get it**. Kernel API is ready:
`sim_stat_points`, `sim_can_raise_stat`, `sim_raise_stat`, + the stat/skill/save accessors.
*View build (render + `C`-to-open + select/raise input) is the next step — user-verified in-browser.*

**Starter one-liners (the content the page renders — accurate to what's built):**
- *Level / XP* — "Kill monsters for XP; each level grows max HP and banks one stat point."
- *Stat points* — "Spend to raise a stat by +1. Never forced — save them and raise when you need it."
- *Stat cap* — "A stat rises at most once per 3 character levels (so you can't dump one stat)."
- *STR* — "Sharpens melee damage." · *CON* — "Raises your saving throw (and HP with level)."
  · *INT/WIS/DEX/CHR* — "spells / devices / accuracy / prices — as those systems land."
- *Saving throw* — "% chance to resist magic/elemental damage; grows with level, CON, armour; never 100%."
- *Melee skill* — "A flat bonus to melee damage, from your level and STR."
- *Item effects* — heal "restores HP" · detect "reveals nearby monsters through walls a while" ·
  buff/drain "temporarily raises/lowers a stat" · teleport "moves you across the level."
- *Slow* "acts at half pace" · *Stun* "frozen — banks no actions."
- *Weapon* "melee damage" · *Armour* "AC: more HP + damage reduction" · *Light* "vision radius"
  · *Potion/Scroll/Food* "use from inventory."

### The Quick-slot bar — streamlined item use (1-9 + Q/E)
Replaces Angband's per-type use-commands (q/r/a/u/z/f/v) with ONE uniform model: a bar of **11
quick-slots — `1`-`9` plus two ACTIVE slots `Q`/`E`** — each holding a usable item; pressing the key
activates it via the right kernel action (consumable → `use_item`, launcher → `sim_fire`, spell →
cast later). The actions exist + are tested; this is the input/HUD layer over them.

- **Auto-slot on first pickup** (good first experience): the first time you grab a usable item it
  fills the next free slot — no manual assignment to start. `Q`/`E` are the two "active" slots for
  the repeated-action items (the launcher, a spell). Manual re-slotting (from the inventory screen)
  is a later nicety.
- **Side-bar HUD** shows the 11 slots + their items. Room is fine — stats live in the top corners,
  so a bottom hot-bar (1-9 then Q E, left-to-right) or a right-edge column fits 800×600.
- **Reconciles today's 1-9 use:** number keys become quick-use in normal play; the Character Page
  keeps 1-6 for *spend* (menu-local); the Inventory screen becomes *assign / re-slot*.
- **Build:** a per-player slot array + auto-assign on pickup (`sim_pickup`/`sim_give_item`) + the
  press-to-use dispatch + the side-bar render (shared view → both platforms; look is user-verified).
  Kernel actions ready: `use_item`, `sim_fire`.

### Tier 2 — threat & survival (the dungeon gets teeth)
- **Monster special attacks.** Casters cast; breath, drain (stat/XP), steal, paralyse, poison —
  per-monster *blows* with effect + element. Today melee-only; `MF_CASTER` is decorative, the
  floating eye inert. Reuses the status system + `damage(kind)` + the perception query.
  **Single biggest leap in feel; most scaffolding already built.**
- **Player status conditions.** poison / fear / confusion / blindness / paralysis / cut / stun +
  slow / haste / bless. The timed-status system exists (player→monster); wire monster→player.
- **Per-element damage + resistances.** `damage(amount, kind)` exists; make `kind` real
  (fire/cold/acid/elec/poison) with resist / immunity / vulnerability.
- **Hunger + light.** eat / starve; mortal torches burn down + refuel (Everbright stays infinite);
  rest + HP/SP regen.

### Tier 3 — Angband breadth
- **Ranged + magic.** fire bow+ammo, throw, cast from spellbooks + mana/SP, targeting (the
  reserved E/Q layer; `sim_los_to` is ready).
- **Item depth.** identification (unknown items), ego items / artifacts, enchantment
  (+hit/+dam/+AC), curses (sticky gear), per-monster loot tables.
- **World.** shops / town / Word of Recall; doors / traps / secret-search / digging; the
  world-bundle link (the proper desert→dungeon) + quests/overlays (the serpent scenario).

### Suggested order
**Tier 1** first — it makes what already exists *deep and usable* (highest felt quality per unit
work, and the four named). Then **Tier 2** (the dungeon becomes dangerous — start with monster
special attacks). Then **Tier 3** breadth. Throughout: kernel = mechanism, content = bundles.
