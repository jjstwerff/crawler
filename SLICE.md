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

## What's still missing IN THE BUILT SLICE (reachable now — surface + depth 1-3)

Grounded in what the player can ACTUALLY hit in the current build: the items that drop at
`i_depth ≤ 3`, the monsters that spawn at `m_depth ≤ 3`, and the screens you can open. Deeper
content (casters from d9+, the lich, recall/town/etc.) is correctly out of scope and lives in the
Tier backlog below — NOT here. Each line says what exists, what's missing, and the build size.

### 1. Finish the item UI — the Inventory hub (reachable: press `I`)
The quick-slot bar + `1`-`9`/`Q`/`E` use are DONE (gate 22/22). The other half is unbuilt; the `I`
screen is still the old flat list.
- [ ] **Equipped-locations column** beside the carried list (every `SLOT_*` + its item or `-`).
- [ ] **2nd ring slot** `SLOT_RING2` (kernel: `NUM_SLOTS` 12→13, the L/R pair) — the only multi-location case.
- [ ] **Enter-equips** the highlighted carried item to its `item_slot` (ring → first free L/R; both full → swap).
- [ ] **WASD reslot** — highlight an item, press `1`-`9`/`Q`/`E` to `sim_qs_bind` it (kernel primitive ready).
- [ ] **drop / examine** the highlighted item.

### 2. Use-item effects for the drops that REACH depth 1-3 (reachable: you find these)
Today `use_item` fires only 2 of 20 usables (cure-light heal, detect-monsters). At slice depth these
also drop and currently do NOTHING when used:
- [ ] **scroll_phase_door** (d1) → short random teleport. **Buildable NOW** — `Player.teleport` exists.
- [ ] **A device use-path** — wands/staves aren't even ROUTED to a use verb (auto-slot routes only
  POTION/SCROLL/FOOD). Add device use (charges + aim), then:
  - [ ] **staff_detection** (d3) → detect monsters (reuse `Player.reveal_monsters`). Buildable once routed.
  - [ ] **staff_light** (d1) → illuminate a radius (needs a light pulse).
  - [ ] **wand_magic_bolt** (d3) → aimed bolt damage (reuse `sim_fire`'s auto-aim + capped damage).
- [ ] **Inert-until-system drops (still appear at d1-3)** — must at least not fail silently (→ §3):
  scroll_identify (d1, needs the unknown-item/ID system), ration_of_food (d1, needs hunger),
  the 3 spellbooks (d1, need spellcasting + a casting class). Build the systems later; **message now.**

### 3. A message / notification log (reachable: EVERY action)
There is **no message system at all** — no "you hit", "you found …", "you reached level N", and
crucially no **"nothing happens"** when an inert item is used. Smallest system, biggest clarity win;
it is the prerequisite that makes §2's deferred items honest instead of silently dead.
- [ ] A rolling message line/area (shared view) + a `sim_msg`-style kernel queue (fixed-cap, C18-safe).
- [ ] Wire the obvious events: hit/kill, pickup, level-up, item-used / nothing-happens, fire / no-target.

### 4. Monster mechanics that SPAWN at depth 0-3 (reachable: these appear)
The only special-mechanic monsters in range — everything deeper is out of scope:
- [ ] **floating_eye paralysing gaze** (d3, `MF_CASTER`, `dam 0`, currently inert). Needs the
  **monster→player status direction** — the timed-status engine exists only player→monster today.
  This is the slice's one real "special attack" + unlocks player status conditions.
- [ ] **`MF_BREEDER` actually breeds** — giant_rat / white_mouse / grey_mold (d1-2) + Skarn the unique.
  The flag is decorative now; breeding needs the enemy array's fixed-cap spawn path (same store the
  crystal needs).
- [ ] **spawn_crystal runtime spawning** (d0 surface — the "Crystal Descent" centerpiece). v1 is a
  static blob; it should periodically emit weak monsters from its knot.
- [ ] **`MF_ERRATIC` movement** — giant_bat (d1) moves erratically; the flag is ignored today. (Minor.)

### 5. Levelling feedback (reachable: you level up)
The deferrable banked stat-choice works; what's missing is the *cue*:
- [ ] **"you reached level N"** (uses §3's message log).
- [ ] An in-browser hint that a stat point is bankable (the spend is silent now) — e.g. a `+` on the
  Character-Page glyph / a sidebar pip.

### 6. (Needs shallow CONTENT to manifest) Item stat requirements + bonuses
The gear-juggling puzzle (Tier-1 design) **cannot occur yet** — no current item carries a req or a
+stat. To make it reachable in the slice: add `i_req_stat`/`i_req_val` + `i_stat`/`i_stat_bonus`
fields, a **4th equipment layer** in `refresh_stats` (effective stat = cur + temp + equipment), a
requirement check on the *effective* value, and at least one shallow **STR-gated weapon** + one
**+STR ring** so the juggle actually shows up. Edge: removing the enabler while the gated item is worn.

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

- **Type-routed auto-slot on first pickup** (confirmed model): a **consumable** (potion/scroll/food)
  fills the next free numeric slot `1`-`9` in pickup order; a **launcher** auto-equips to the bow slot
  and binds **FIRE to active slot `Q`** (a **spell** → `E` later); **ammo** is the bow's fuel, not a
  slot of its own. So one pickup = ready to use — `1` drinks, `Q` fires.
- **Manual reslot** (in the inventory screen): move the cursor to an item with **WASD**, then press a
  slot key (`1`-`9` or `Q`/`E`) to **bind that item to the slot** — the slot's previous occupant is
  unbound. A given item lives in **at most one slot**, so re-binding *moves* it (clears its old slot)
  rather than duplicating. Auto-slot and manual-reslot share one kernel primitive: `bind(slot, def)`.
- **`Q` shows the bow by name with arrows-left behind it** — e.g. `Q: Short Bow (4)`, the count being
  the matching ammo carried; it ticks down as you fire and reads empty (`(0)`) when the quiver is dry.
- **Left-sidebar HUD** (Angband's known location): one left column = the familiar character bar —
  **HP on top (with room reserved for SP/spell-points), then the base stats, then the quick-slots**
  (`1`-`9` then `Q`/`E`, top-to-bottom). Stats + slots + vitals share the one left column; the game
  view takes the rest of the width.
- **Reconciles today's 1-9 use:** number keys become quick-use in normal play; the Character Page
  keeps 1-6 for *spend* (menu-local); the Inventory screen becomes *assign / re-slot*.
- **Build:** a per-player slot array (`defidx+1`, 0=empty, mirroring `eq[]`) + the `bind(slot, def)`
  primitive (used by auto-assign on `sim_pickup`/`sim_give_item` *and* manual reslot) + the press-to-use
  dispatch (`sim_use_slot` → `use_item` / `sim_fire`) + the side-bar render (shared view → both
  platforms; look is user-verified). Slot bindings persist across descents like inventory.
  Kernel actions ready: `use_item`, `sim_fire`.

### The Inventory screen — carried + equip + reslot (one hub)
The `I` screen is the single item hub (confirmed layout). **Carried items list on the LEFT** (WASD
moves the cursor); the **EQUIPPED locations list on the RIGHT** — every worn location + its item (or
`-`): Weapon, Bow, Body, Shield, Head, Hands, Feet, Cloak, Light, **Ring L / Ring R**, Amulet. The
equipped column always shows ALL locations (empty = `-`) so the player sees what can be filled.
- **Enter equips** the highlighted carried item to its `item_slot` location. A **ring fills the first
  free of L/R** (both full → swaps the worn one) — so the only multi-location case is visible +
  chooseable on the one screen.
- **`1`-`9` / `Q` / `E` bind** the highlighted item to that quick-slot (the manual reslot, same
  `bind(slot, def)` primitive as auto-slot).
- **Two ring locations** (faithful Angband): the kernel gains a second ring slot (`SLOT_RING2`, the
  L/R pair); the rest of `eq[]` is unchanged.
- **For-now vs later:** the labeled two-column list is chosen because it **reads the clearest** for the
  slice; a richer equip view (a paper-doll silhouette with items placed on the body) is a later
  upgrade — a natural fit for the 2D-sprite-library goal, layered on the same kernel `eq[]` state.

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
