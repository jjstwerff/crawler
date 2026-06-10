# BUNDLE.md — content bundles + the shared pool

How world content is packaged and composed: **definitions** (the things),
**placement rules** (where/how they appear), and **routines** (behavior, by id),
all resolving into one **shared pool**. Stencils + layers + castle assembly are one
content type within this — see [STENCILS.md](STENCILS.md). Design only; no
implementation yet.

**Scope — close to the base game (no factions / NPCs).** The entity model stays
Angband's: **monsters · items · dungeon · uniques**. There is no faction, NPC, or
social-simulation tier. Quests and motifs are a *structural* layer that only
**references** the existing pools — they never add a person/faction system. A
"captive" such as a rescued princess is a **special passive monster** (or a carried
**object**), not an NPC. This keeps the design Angband-faithful (CLAUDE.md "follow
Angband logic") and the entity set small.

## What a bundle is

A **bundle** is a coherent unit of game content. The base game is a bundle;
variants / expansions are bundles layered on top. A bundle carries three things:

1. **Definitions** — new keyed records it contributes to the catalogs.
2. **Placement rules** — the data-driven generation config (profiles, spawn/loot
   tables, assembly rules) — i.e. the "scripts for the random generation algorithm".
3. **Routine bindings** — references (by id) to behaviors in the routine pool.

Bundles **compose into one pool**: load base + active bundles, merge by key, resolve
cross-references. A bundle references what's already in the pool *and* extends it.

### Granularity — thematic units; one creation-choice per bundle

A bundle is a **thematic unit**: it may carry **several content types at once** — creatures,
items, spells, room stencils, placement — exactly as the world bundles already do. Different
types **share** a bundle freely when they're thematically linked (a class/race bundle may carry
its own themed items/creatures, and a caster's spell list lives *with* it).

The one hard rule is on the **character-creation axis**: a bundle carries **at most one race or
one class** — never multiple races, never multiple classes, never a mix. That one-per-bundle
granularity is what lets a modder ship a *limited* game by including only the race/class folders
they want (drop in two race folders → a two-race game).

**Direction:** the base game's content gets carved into thematic bundles too — not just quest
overlays, but the base monsters/items reorganized into coherent themed bundles over time.

### Standing check — keep bundles library-like

Every time you touch the **engine↔bundle seam**, *re-evaluate* that bundles still adhere
to their intentional library-like nature — don't assume; it erodes one convenient shortcut
at a time. The invariant: **a stranger can drop a bundle folder in and rebuild without
touching `src/`, and their game is byte-identical.** Concretely:

- **Content/data lives bundle-side** (monsters, items, stencils, placement rules, flavour
  text). The engine holds only generic **mechanism + vocabulary** (the records, the flags,
  routines-by-id, the placer/stamp, the catalog merge).
- **No bundle edits an engine source file** to add its content.
- **The engine never references a bundle by key/name** — it dispatches generically through
  the generated glue + key→index resolution.
- A bundle *setting* an engine flag/record (`IF_KNOWN`, `MF_GAZE`, a `Placement`) is correct:
  the engine *providing* the flag is mechanism, the bundle *using* it is content.

The flip side of this check is the ceiling it implies — a bundle can only *set* vocabulary the
engine defined. How we lift that (an event/hook bus, a general deterministic script API,
flags-as-routines, runtime-interpreted bundles) is its own staged epic: **SCRIPTING.md**.

## Bundles compose — and the entry point is a bundle too

**Bundles link to other bundles via scripts (routines).** A bundle's hooks can
reference content and trigger behaviour in *other* bundles, so bundles form a graph,
not a flat pile — a class bundle hooks into the world bundle; a quest bundle into the
content it gates. (Cross-bundle refs resolve through the same key→index link pass;
the script layer is the routine pool.)

**The starting class is itself a bundle.** A class isn't a special-cased data row —
it's the **entry-point bundle**, packaging:
- its **starting house/bed** — the home base and **first save point** (death returns
  here until deeper save points are found; pillar #5),
- its **starting kit** (lateral items that seed the playstyle — pillars #3/#4),
- a **mild stat tilt**,
- a **starting quest** that onboards the player *from that class's perspective* — the
  novelty-curve onboarding (pillar #8), class-flavoured,
- **script-links** into the world / content bundles.

So "pick a class" = "load a class bundle", using the same machinery as everything
else — the cleanest expression of pillars #4 (class = soft start), #3 (items =
progression) and #8 (engaging onboarding): your opening *is* a bundle.

**Near-term reconciliation (hybrid).** The full class-bundle (starting quest,
script-linking) is the *authored / future* realization (moros-side, like the rest of
this doc). Near-term the build seeds it minimally — a **starting loadout + stat tilt**
(in the equipment slice) shaped to become a class-bundle later — so the entry point is
migratable, not rebuilt.

## World bundles — kinds, linkable places, and scoped overlays

The bundle graph is realized concretely by a **kind-dispatch scanner**
(`tools/gen_bundles.py`): every `bundle.json` carries a `kind`, and the scanner emits a
**per-system generated registry** for each — `character → src/bundles.loft` (`bundle_activate`),
`world → src/rooms_gen.loft` (the rooms section's `RoomDef` table + `room_connect_*`). One
scanner, many kinds, many registries; the kernel stays the *mechanism* and bundles are the
*content/definitions*. This is "**every system in bundles**".

A **world bundle is a linkable PLACE** with named **sections**. `bundles/world_classic` (key
`classic`) is the first: its **rooms** section supplies the default Angband room set + the
corridor connection model; sibling sections (monster spawns, terrain, level features) live here
later. A separate world bundle can carry a **spawn rule** ("build an Angband-style dungeon") and
**link to a place by key** — that link graph *is* the world.

**Composition is mixed, not all-or-nothing — and it is scoped.** A *calling* world can **overlay**
its own content onto a place it spawns: e.g. link the classic dungeon but **inject a special room
at level 3** drawn from the calling world. Overlays are **depth-/location-scoped and bounded —
they do NOT extend deeper**: at the overlay's depth the calling world's content appears; below it,
generation reverts to the pure base place. So a generated level is *base place + scoped overlays*,
and the calling world's reach stops where the overlay's scope ends.

*Concrete-now vs authored-later:* the scanner + the `classic` rooms registry exist today;
`gen.loft` consuming the registry, the link mechanism, and the overlays are the staged next steps.

## Persistence — deterministic base + delta; quest items are death-bound

A place's layout is a pure function of its seed, so it is **never stored** — only the **delta**
(what diverged) is: dead spawns, taken/dropped floor items, opened features, tombstones. On
re-entry, regenerate + replay the delta. Survivors return to their **natural** place (positions
are not persisted by default — cheap; location/HP/effects can join the delta later). The store is
a **compact, per-area, fixed-per-depth block** that expands on entry: pristine areas cost nothing,
re-leaving a depth **overwrites** its block (no growth/compaction), and the whole thing is bounded
by *activity*, not world size — a deeply-cleared dungeon is single-digit KB. *(Proven as a
round-trip = identity invariant in `persisttest`; wiring it through `sim_descend` is the next step.)*

**Floor items:** only **important / quest** items persist; simple loot decays on leave
(Angband-like). Quest items are never pruned from a block (they bump simple ones for a slot).

**Quest items are death-bound (anti-exploit).** A quest item is treated differently from normal
loot: on death it **drops automatically and stays in its origin dungeon** (a never-pruned
`IF_QUEST` floor-delta at the death spot) — checkpoint-respawn carries normal loot but **never** a
quest item. So a player cannot **force into a place they should not be** (e.g. a deep entry from a
dangerous top area, since the entry depth is just a parameter), **grab a crucial item, and suicide
back to a safe checkpoint with it.** The only way to remove a quest item from its dungeon is to
leave **alive, the intended way** (survive the exit / complete the quest). This extends the
souls-stake (gold staked on death, `grave_*`) up to the quest layer.

## Two common pools

The whole design rests on splitting content into a **data pool** and a **behavior
pool** — the data/code seam loft forces, turned into an asset.

### A. The definition pool — pure data, keyed catalogs

Typed catalogs, each a table of records keyed by a descriptive string. **Cross-refs
are by key in source, by integer index at runtime** (resolved once at load — a link
pass, like a symbol table).

| Catalog | Record | Owns | Home |
|---|---|---|---|
| `monsters` | `MonsterDef` | stats, drops, **AI routine id** | `monsters.loft` (exists) |
| `items` | `ItemDef` | category, slot, magic, **use routine id** | `items.loft` (exists) |
| `walls` | `WallBlock` | material, thickness, walkable-top, height range, junction policy (§9) | NEW |
| `doors` | `DoorDef` | state (closed/locked/secret/portcullis), key req, **interact routine id** | NEW |
| `stencils` | `Stencil` | layered grid + **legend** (refs other catalogs by key) | NEW — STENCILS.md |
| `stencil_sets` | `StencilSet` | themed group of stencil keys + assembly params | NEW |
| `materials` / `terrain` | `MaterialDef` | colour, blocks, slope | LATER (→ hex_terrain) |
| `quests` | `QuestDef` | objective, target, requirements, rewards, **routine ids** | NEW — world placement tier |
| `motifs` | `MotifDef` | distribution + node theme + connective topology + payoff | NEW — broadest, world-scale |

A record's **key** is its identity across bundles (e.g. `"goblin"`,
`"curtain_stone"`, `"portcullis"`, `"vault_cross"`). Definitions are serializable
(the loft data model / `show_loft` round-trip) — this is what makes a bundle a
*loadable* thing later.

### B. The routine pool — behavior by integer id, behind kernel dispatchers

A **routine** = an integer id + a kernel dispatcher arm. Defs reference routines by
id; many defs share one id (the *common pool of behaviors*). One dispatcher per
domain:

```
monster_act(routine_id, &sim, idx)        // AI: kite, charge, flee-at-half, breeder…
door_interact(routine_id, &sim, door)     // open, unlock-with-key, portcullis, secret
item_use(routine_id, &sim, slot)          // quaff, read, zap…
stencil_postplace(routine_id, &gen, anchor) // seal doors, place guardian, light room
quest_check(routine_id, &sim, quest)      // RESCUE / RETRIEVE / SLAY — done yet?
motif_reveal(routine_id, &sim, link)      // discover a hidden link; unlock the rest
```

**Why ids, not stored functions:** loft can't safely store function pointers in data
(LOFT_ISSUES C-series; integer flags are the proven-safe shape — C6/C10). So:
- **Referencing** an existing routine from a def is **free data** — the open part.
- **Adding a new** routine is a small **kernel** change (one dispatch arm) — the one
  seam where a bundle isn't pure data.

Bundles compose freely over the existing routine pool; a genuinely new behavior is a
kernel addition. *(Upgrade path: if loft's function-value story matures, routines
could become loadable — noted, not relied on.)*

## Cross-references — the legend + the link pass

A stencil cell isn't "a goblin" — it's a **legend slot** → a key → a pool index.
Example stencil legend:

```
M0 = "goblin"        M1 = "orc_captain"     (monsters)
I0 = "potion_heal"                          (items)
D0 = "portcullis"                           (doors)
W0 = "curtain_stone"                        (walls)
hook = HK_GUARDIAN                          (routine id)
```

The grid's marker cells carry the **slot code** (the `>=16` marker range from
STENCILS.md, now slot-indexed). At **load/link** every key resolves to its catalog
index; a **missing key or dangling routine id is a hard error** (fail loud — no
silent default). After linking, the runtime touches only integers.

## Placement rules — the generation "scripts"

Declarative tables + routine hooks (the locked decision: *profile data + integer
hooks*):

- **Profiles** — per level kind (dungeon / cavern / **castle** / town): builder mix +
  weights, room + monster budget, depth applicability. (Angband `cave_profile`.)
- **Spawn / loot tables** — `get_mon_num` / `get_obj_num`: candidate pool filtered by
  depth, weighted by `1/rarity`, deepen bias, out-of-depth chance. (Already in `sim`
  A1 + `items`.)
- **Assembly rules** (castle) — which tower/building stencils, how to route curtain
  walls in 24 directions, gatehouse placement. (STENCILS.md composition layer.)
- **Hooks** — per stencil / door / level: a routine id for post-place logic.

Everything is **data** except the hooks, which are **routine ids**.

### Stencil sets — themed random assembly

Stencils are grouped into **sets** (`StencilSet`: a theme — "stone castle", "crypt",
"goblin warren" — listing member stencil keys + assembly params: a **centerpiece**,
optional members + count ranges, the wall/door defs to connect with, depth/rarity).
**A bundle ships multiple sets; generation picks one per place and assembles it
randomly.**

For a place: choose a set (weighted by theme / depth / quest), drop its
**centerpiece** (the keep, the throne room), scatter **optional members** at random
counts, route walls + place doors from the set's own defs, fill spawns from the
monster/item tables. Result: **thematic coherence + per-run variety** — one "castle
set" yields a different castle each seed, but always a castle. (Angband's per-profile
room/vault sets, generalised; content original.)

## Quests — content *and* generative structure

A quest is both a **pooled definition** and a **generative force**: it is assigned to
a **place**, and it makes **other places link to it logically** — seeding the world
as a lock-and-key graph. (Original / clean-room content, a tier above the
Angband-faithful core.)

### `QuestDef` (pooled; refs the other pools by key)
- `q_key`, `q_name`
- `q_kind` → picks the objective routine: SLAY / RETRIEVE / REACH / CLEAR / RESCUE
  (reach + free a captive). *(No ESCORT — that wants follow-AI / an NPC.)*
- **target** — what completes it, by key, **from the existing pools (no NPC type)**:
  a monster (`"castle_guardian"`), an item (`"legendary_sword"`), or a place. A
  captive (`"princess"`) is a special passive **monster** or a carried **object**
- **goal placement** — a place-kind (`"castle"`) + the set's goal **legend slot** (the
  keep's `prisoner` slot) — reuses the legend + stencil-set mechanism
- **requirements** — keys / items / sub-quests obtainable *first* (the lock-and-key
  edges)
- **rewards** — items / xp / unlocks on completion
- objective routine id + on-complete routine id (routine pool)

### The place gets the quest → other places link logically
World-gen resolves a bundle's **quest line** into a **place dependency graph**:
1. Each quest **goal** → a place; that place picks the matching **stencil set** and
   the goal is injected into the set's goal slot (princess in the castle keep; sword
   in a deep dungeon vault).
2. Each **requirement** → either an *earlier place* that provides it (the
   sword-dungeon becomes a prerequisite of the castle) or a *gate* (a locked door, or
   the rampart traversal route — STENCILS.md's sealed keep).
3. Generation **wires connectivity** so the key place is reachable *before* the lock
   place (a topological order over the world / stair graph) — the "logical link".
4. Quests **chain**: rescue-the-princess *requires* the legendary-sword quest → the
   castle place depends on the dungeon place; the world is one coherent arc.

Worked: `rescue_princess` (RESCUE, target `"princess"` — a special passive
monster/object, not an NPC — goal = castle keep, requires `"legendary_sword"`) +
`find_legendary_sword` (RETRIEVE, target `"legendary_sword"`,
goal = dungeon vault, reward = the sword). Gen places the sword-dungeon as a
prerequisite of the castle and gates the keep behind the rampart route → "find the
sword, then storm the castle and rescue her" falls out of the graph.

### Solvability — headless-testable
A **solvability invariant**: following the dependency order from the start, every
requirement is obtainable before its consumer → the world is completable. The
world-scale analog of STENCILS.md's connectivity check — a `*test.loft` asserts the
quest graph is acyclic + topologically reachable, no pixels. **No unwinnable worlds
is a test, not a hope.**

## World motifs — bundle-scale macro-structure (a bundle's *profound* effect)

A bundle isn't limited to dropping set-pieces. A **motif** is a world-spanning
pattern: it scatters many thematically-linked places across the landscape and binds
them with a **connective substrate that is often hidden** — the player *discovers*
that the world has a secret coherence.

Canonical example: a dozen **mushroom houses** strewn across the map (each a node of
the `mushroom` stencil set) that are **secretly one organism** — their basements
joined by a **root-tunnel network** on an underlayer, leading to a heart-chamber.

### `MotifDef` (pooled; the broadest tier)
- `mo_key`, `mo_name`
- **distribution** — node count range + spatial rule (scatter / cluster / ring /
  ley-line) across the landscape
- **node theme** — the stencil **set** each node uses, + per-node roles (most houses,
  one **heart**)
- **connective topology** — link type (root-tunnel / sewer / teleport-stone), the
  **layer** it lives on (basement underlayer), **visibility** (secret-until-found vs
  open), and graph shape (mesh / star-to-heart / chain)
- **payoff** — a routine (+ optional quest): the reveal, the heart, the reward/boss;
  how finding one link unlocks the rest

### What it reuses (the satisfying convergence)
A motif is **the layer model + the place graph, at world scale**: the "root system"
is literally a **basement-layer traversal network** linking the basements of
scattered buildings — STENCILS.md layers + the BUNDLE.md place graph, now distributed
and **secret**. Its hidden links are place-graph edges flagged *secret* — a
discoverable bonus/shortcut, distinct from the *required* lock-and-key edges quests
add.

### Discovery-driven vs goal-driven
- **Quests** = *goal-driven* structure (a lock-and-key path you're told to walk).
- **Motifs** = *discovery-driven* structure (hidden coherence you uncover).
They compose: a motif can carry a quest ("trace the roots to the heart"); a quest can
target a motif node.

### Headless-testable
The hidden network must be **consistent + reachable**: every node's link resolves, the
heart is reachable through the network, and secret edges never break the *required*
solvability. A `*test.loft` assertion — **the secret is real and findable**, provable
without pixels.

### Scale ladder — a bundle operates at every scale
`wall-block def → stencil → set → place → quest → MOTIF`. One bundle can reach from a
single door's behavior all the way up to a world-spanning secret organism.

## Pipeline — load → link → world-layout → generate → realize

```
 bundles (base + active)
        │  LOAD   merge catalogs by key (incl. stencil sets, quests)
        ▼
   shared pool  ── definitions (data) ── routines (ids → kernel dispatchers)
        │  LINK   resolve every cross-ref key→index; validate (missing key = error)
        ▼
   WORLD LAYOUT  motifs scatter themed nodes + secret connective topology;
        │         quests assign goals + required edges → one place graph
        │         (assert solvable; assert secrets reachable)
        ▼
   GENERATE  (per place)  pick stencil set (theme, depth, quest/motif) → assemble
        │     randomly (centerpiece + members) → route walls → place doors →
        │     spawn via tables → inject quest goal → run hooks
        ▼
   realized world   places of per-layer tiles + walls + doors + spawn list +
              props + quest state   (renderer-agnostic; routines fire in play)
```

## Now vs later (hybrid; hardcoded tables now)

- **NOW** — the pool = base catalogs as **hardcoded loft tables** (`monsters.loft`,
  `items.loft` + new `walls` / `doors` / `stencils` / routine-id modules). "A bundle"
  = the base game's own tables. A small **link helper** resolves keys→indices. No
  file format, no parser dependency.
- **LATER** — bundles loaded from **files** via the loft own-format serializer
  (`show_loft` / `parse`) — same keyed catalogs, now external + overridable; migrate
  the structs to `lavition_stencil` / `hex_*` (a `use`-swap); editor-authored bundles
  via lavition plugins.

## Seeding content from Angband — reproduce, don't import

Angband's vaults / room-templates / destroyed-level generation are **already
proto-bundles**: a layout grid + a legend mapping glyphs to terrain / monsters /
objects — exactly the stencil + legend format (we modelled it on `vault.txt`). The
base catalogs already work this way: `monsters.loft` / `items.loft` are clean-room
Angband-faithful tables. So "bundles based on the Angband data set" is the path we're
already on.

**But: reproduce the patterns + numbers, author original content — do NOT import the
data files verbatim.** Angband's named content is Tolkien-derived, which is exactly
what CLAUDE.md's clean-room rule excludes. Use Angband as a **spec**: a vault's
dimensions / rarity / depth / content-mix and the generation *logic* are reproduced
faithfully; the glyphs resolve to **our** pool keys (original monsters / items /
lore). Reference, not copy.

### Environmental storytelling — the "aftermath" bundle
The "blown-up floor with evidence of what happened" is a strong first showcase:
- **Faithful basis** — Angband's destroyed-level / cataclysm generation (blast areas,
  rubble): reproduce the mechanic (a per-level chance of a destroyed region) + its
  numbers.
- **Our enrichment** — a stencil whose *contents* imply a past event: scorch / rubble
  terrain + specific **evidence** items placed by the legend (a shattered weapon,
  scattered treasure, a slain creature's drops). The story is **spatial / implicit**,
  read from the arrangement — no text-lore or NPC system (base-game scope). A light
  touch (a dropped scroll) is fine; a dialogue/lore tree is not.
- **Tiers it uses** — a stencil now; an "aftermath" **set** (varied wreckage) and a
  recurring **motif** (one disaster scarring several places) later.

**Build-order fit:** S1-level content — a single-layer stencil with a *specific-key*
legend (S1's link pass already resolves it), plus maybe one new terrain code (scorch
/ rubble). No new machinery; a vivid first bundle once S1 lands.

## loft feasibility — sanity check

**Verdict: feasible.** Every tier decomposes onto shapes already proven in the tree
(`items.loft` tables, the loot floor arrays, `gentest` BFS, `enemies`). The cost is
**discipline + complexity, not feasibility** — no tier needs a loft feature that is
broken. The two things we'd *like* but deliberately avoid both have an established
workaround already in use:
- **stored function pointers** → integer routine ids + a `match` dispatcher (C6/C10);
- **growable struct vector fields** → pre-sized fixed array + int count + index-write
  (C18 — the `enemies` / loot pattern).

| Element | Safe shape | Watch |
|---|---|---|
| Keyed catalogs | build-time local append (`item_table`) | — |
| Read a def | **guarded direct index, no `??`** on a struct | `v[i] ?? structfn()` can SIGSEGV (C1) |
| Link pass (key→index) | resolve into a **separate int table**; don't rewrite struct fields | intern text keys to ints once → hot path is int-only |
| Layered grid | **flat** `vector<integer>`, `(L·h+y)·w+x` | never nested vectors (the wallgeo panic) |
| Stamp into level | index-write into the tile vector | — |
| Accumulators (spawns, placed nodes, graph edges, secret links) | **fixed array + count + index-write** on the struct | struct-field `+= [x]` desyncs (C18) |
| Algorithm scratch (BFS, filter, topo-sort) | **local** vectors — runtime append is fine (`gentest`) | only *struct-field* append is broken, not local |
| Graphs (place deps, motif links) | **parallel flat int arrays** (`from[] to[] kind[] secret[]`) | — |
| Routine dispatch | `match` / if-chain on int id, one per domain | `&Sim`-mutating arms live **in `sim.loft`** (C4) |
| Determinism | all RNG on gen `Rng` / sim LCG | no external RNG |
| **File-loaded** bundles | the own-format serialize/parse round-trip | **gated** on loft serialization maturing → stays in the **LATER** bucket |

## Build order — prove the spine first

Each slice = one `*test.loft` wired into `make test`, warning-clean, branch `combat`;
the user visually verifies the view bits. Front-loads the two scariest unknowns (the
keyed cross-ref, and the layer mechanic in 2D) so everything after is "more of the
same shape".

| # | Slice | Proves | Headless test | Touches |
|---|---|---|---|---|
| **S1** | Keyed stencil → stamp → spawn | link pass end-to-end + stamping + accumulators + connectivity | a known stencil stamps; its legend monster resolves + spawns; level stays connected | `stencils.loft`, link helper, `gen.loft`, `sim`, `stenciltest` |
| **S2** | Layers + ladders + traversal-gating | the layer model + the gameplay pillar **in 2D** (the whole "design now, test now" thesis) | ground flood-fill does NOT reach the sealed keep; the ladder/rampart route DOES | `stencils` (layer axis), `sim` (`current_layer`), `view` (current-layer render), `layertest` |
| **S3** | Stencil sets → random assembly | the theme tier (coherent + varied) | a set assembles a place; centerpiece present; connected every seed | `stencil_sets.loft`, `gen`, `settest` |
| **S4** | Walls + doors (pooled) + 24-dir runs | the castle composition layer | a wall run connects two towers; a sealed building has no ground door; rampart route works | `walls.loft`, `doors.loft`, door routine, `gen` assembly, `wallgeo`, `walltest` |
| **S5** | Place graph + quests + solvability | the world lock-and-key tier | quest assigns goal + requires-edge; graph acyclic + topologically reachable | `quests.loft`, world-layout, `quest_check`, `questtest` |
| **S6** | Motifs + secret edges + discovery | the broadest tier (mushroom-root) | nodes scatter; secret links resolve; heart reachable; secrets don't break required solvability | `motifs.loft`, world-layout, `motif_reveal`, `motiftest` |

**Spine = S1 + S2.** After those, the keyed-pool backbone and the layer mechanic are
proven (2D + headless); S3–S6 bolt tiers onto the same skeleton. S4's *collision* is
kernel-safe today; its *pretty 24-dir geometry* leans on `wallgeo` (rounded active;
the DP straightener is parked on a loft fix — render-only, never blocking the data).

## Open questions

1. **Override policy** — two bundles define the same key: last-wins / explicit
   `override` / error?
2. **Key namespacing** — bare keys, or bundle-scoped (`base:goblin`)? Affects
   collisions + readability.
3. **Routine-id allocation** — the one place bundles aren't pure data. A registry +
   reserved ranges per bundle? How does a bundle declare it needs a new dispatch arm?
4. **Data vs routine boundary** — e.g. is "route a wall" a builder-id (data) or a hook
   (routine)? Draw the line.
5. **Manifest** — bundle id / version / depends-on; load order.
6. **Validation scope** — how much the link pass checks (orphan defs, unreachable
   stencils, legend slots with no grid cell).
7. **Stencil-set assembly** — how much a set fixes vs leaves to chance (centerpiece
   always? member adjacency rules? mixing two sets in one place?).
8. **Quest graph** — authored quest lines vs procedurally composed from a
   quest-grammar; linear chain vs partial-order with multiple solutions.
9. **Requirement → gate mapping** — item-key vs traversal route vs knowledge; who
   decides which gate a requirement becomes.
10. **Place identity** — how a "place" is addressed (`wx,wy,depth,kind`) and bound to
    its quest + assembled set, so revisits stay consistent (ties to L1 persistence).
11. **Motif distribution** — node placement vs world size; can two motifs overlap a
    region; do motifs span zones/depths or stay within one?
12. **Secret-edge model** — how "hidden" is stored + discovered (per-link flag +
    reveal routine), and how a found link persists (ties to L1 persistence).
