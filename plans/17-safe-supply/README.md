# `17` — A settlement's output is a function of the danger around it

**Issue:** [`jjstwerff/crawler#17`](https://github.com/jjstwerff/crawler/issues/17) ·
**Value:** `G` · **Effort:** `M`

## Status

**Designed, not built** — `status:future`, holding no active slot (the roster is
`#11`/`#12`/`#13`). `S0` is shipped: the design (`CRAFTING.md`) and the measurement of what
already exists, which turned out to be most of it.

⚠ **This plan comes BEFORE [#16](../16-eight-statistics/)** (user, 2026-08-09). #16's `M3`
re-authors 18 race blocks with a `Handiness` value each, and under this design the hero
never crafts — so what Handiness is *for* is decided here. Re-authoring first would be
betting 18 blocks on an undesigned system.

## Goal

A worker will not enter an unsafe area, a workshop draws on what its workers bring home, and
the player can see both — without learning a single new key.

## Anchors

`CRAFTING.md` (the design — I-SAFE, the three pieces, the failure paths) ·
`OVERLAND.md` §13b/§13c (the daily loop, the gatherers, the alchemist-factory) ·
`BUNDLE.md` → *The `production` section* (`I-PROD`, the seam this extends) ·
`DESIGN.md` §3a pillar 0 (the interface budget this spends nothing from).

## What `S0` turned up — measured 2026-08-09

⚠ **Most of the system is already built**, which is the finding that sets the effort at `M`
rather than `H`. Shipped: gatherers (role 9) with real gathering (`w9.alive = false;
// trapped: ingredients for the factory`), farmers and fishers carrying their catch, carts
and ships distributing, seven workshops rotating **bundle-owned** repertoires.

**What is missing is one thing, in one place:**

| | |
|---|---|
| **danger is invisible to a worker** | `npc_passable(s, role, q, r)` knows bounds, walls and water-by-role. It knows nothing about hostiles |
| **no safety category exists** | nothing anywhere says an area is unsafe, so the player has no target to flip |
| **production consumes no input** | the workshops rotate regardless of what arrives |

⚠ **AND THE MECHANISM CHANGED DURING THE DESIGN, WHICH IS WORTH RECORDING.** The first
draft had gatherers **killed** by hostiles. The user's correction — *they avoid unsafe
areas, and the players have to first get them in the safe category* — is better on grounds
that only became visible once both were on the page:

| | killing them | avoiding it |
|---|---|---|
| what it needs | NPC damage, NPC survival, corpse-or-vanish, a replacement rule so a settlement cannot die out, and a story for a player who never watches it happen | **one term in a predicate every working NPC already calls** |
| re-assertion sites | several, and omission is silent | **one**, and omission is loud — a worker visibly standing in a dangerous field |
| readability | needs an explicit signal | **free — an empty field IS the signal** |
| failure `F5` (a settlement dies) | must be engineered against | **dissolved**: idle is not dying |

## Steps

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`S0`** — the design + measure what exists | S | `CRAFTING.md` | **Shipped** |
| **`S1`** — a safety category over the surface | S | `make test` + a new `safetytest` | **Designed, not built** |
| **`S2`** — `npc_passable` consults it; workers avoid | S | `make test`; a `scripts/*.play` walk | Blocked on `S1` |
| **`S3`** — stock: workers raise it, workshops draw it | M | `make test` (extend `producttest`) | Blocked on `S2` |
| **`S4`** — the world shows it, with no panel | M | `make play`, a user read | Blocked on `S3` |
| **`S5`** — safety is CONTESTED: sources send incursions | M | `make test` + a `scripts/*.play` session | Blocked on `S2` |
| **`S6`** — item damage as an EVENT (no running wear) + repair | S | `make test` + a `scripts/*.play` session | **Designed, not built** |

### `S1` — the safety category, designed

A per-area answer to *is this safe*, cheap enough to run per worker per day. Terms: awake
hostiles nearby, a guard's reach, distance from the walls. ⚠ **A CATEGORY, NOT A GRADIENT**
(user: *"get them in the safe category"*) — a threshold the player can cross and see
crossed. A float that slides is unreadable in play and untestable in a gate.

### `S2` — workers avoid, designed

One term added to `npc_passable`, plus the same term in site selection (the alchemist's
gatherer already **shuns** the deep mountains by construction — this is the same shape).
⚠ **Guards are a term in the safety expression, not spectators**, or the settlement is
scenery waiting to be rescued.

### `S3` — stock, designed

A **number per producer**, raised on arrival home and drawn on making; empty means no
output that day. ⚠ **Never an item inventory** — the moment it is items somebody wants a
screen for it, and the interface budget is spent (`F2`). Which material a producer draws
and which item it yields is **bundle content**, declared beside the `production` repertoire
that bundle already owns — `I-PROD`'s seam, unchanged.

### `S4` — the world says it, designed

Thinner stalls, a skipped rotation, an unwalked route, an innkeeper's line. ⚠ **`F6` is the
real risk and this step is the answer to it**: if the loop cannot be *seen in one session*,
it is a simulation nobody plays. Measure that before polishing anything else.

### `S5` — contested safety, designed

⚠ **Safety is not a ratchet** (user, 2026-08-09): monsters spread, wars move fronts,
raiders take roads. Without it the world has an end state — cleared once, solved furniture.

⚠ **AND THE OBVIOUS IMPLEMENTATION RUINS IT.** *Decay* — cleared ground reverting on a
timer — is a treadmill (`F7`): the same valley re-cleared forever, a chore in a system's
clothes. The rule instead: **pressure ARRIVES FROM A SOURCE; it does not accumulate.** A
den that was never cleared, a warband on a road, a front that moved. There is a **cause**,
and the player can go at the cause rather than the symptom — which is also what keeps the
map legible: the valley is unsafe *because* of the thing over the ridge.

**Eligibility, never a schedule** (`SCRIPTING.md`): a raid becomes *possible* when its
conditions are true, and if they never arrive it never happens and nothing is owed. ⚠ Not
a difficulty dial keyed to the player, or it reads as punishment for progress (`F8`).

**A cleared source stays cleared** — what returns is a new thing from a new place. Durable
enough that clearing is worth doing, contested enough that the world stays alive. The
counters already exist: guards patrol, walls ring the towns, roads carry carts.

### `S6` — damage is an event, designed

⚠ **Settled 2026-08-09: NO running degradation.** Gear does not wear out with use; a
**failure or a special circumstance** damages an item, and it stays damaged until repaired.

That distinction is the whole cost difference — wear-per-use is a maintenance chore with a
meter behind it, event damage is one state the causing event teaches. ⚠ **And the second is
Angband's actual model** (acid ruins armour, fire burns scrolls), so `CLAUDE.md`'s
faithfulness rule settles it rather than taste.

**Small:** one damaged state per item (the `IF_*` bitmask has room), set by a visible cause,
cleared by a smith — or in the field, worse and slower, with `Handiness` setting how well.

⚠ **The causes do not exist yet, and that is fine**: `sim_damage` branches on `"physical"`
alone. Land the state with one honest cause and grow it with the damage model — but **every
cause must be legible in play**, or this is wear-per-use in an event's clothes.

## What this plan does NOT change

- **The player's verbs.** Zero new keys, no crafting screen, no recipe list, no material
  inventory. That is I-SAFE's whole claim.
- **Civilian invulnerability.** They stay unkillable; under avoidance nothing needs to die.
- **The spell economy.** `CATALOG.md` §6.3's cards-and-Tension is the *advancement* economy
  and is untouched; this is the *material* one.
- **`I-PROD`.** The rotation and the seam are unchanged; this adds an input to them.
- ⚠ **Difficulty.** `S5`'s incursions are condition-driven, never scaled to the player —
  the world pushes where it is weak, not where the player is strong.

## Open questions

Carried from `CRAFTING.md`, and the fourth is the one that blocks `#16`:

1. Does the hero ever hold a material? (A boss dropping the one heroic ingredient is the
   classic beat; allowing it costs an item and no verb.)
2. Stock per producer, or per settlement?
3. What exactly is in the safety expression, and can it be evaluated cheaply per worker?
4. ✅ **RESOLVED 2026-08-09.** `Handiness` gates **repairs and improvised gear, not
   crafting**, and it is a **degree, never a key** — learned skills permit, the stat
   qualifies (the same *stat + mastery* shape `CATALOG.md` §6.3 already uses). `#16` `M3`
   is unblocked. ⚠ Improvisation is free (the `Ingenuity` card exists); **repairs need a
   durability mechanic that does not exist** and charges the interface budget — that call
   is `S6`, and it is now settled: **damage is an EVENT, never running wear** — Angband's
   own model, so it costs one item state rather than a maintenance loop.

## See also

`CRAFTING.md` · `CATALOG.md` `OW2` (the decision this answers the crafting half of) ·
[plan #16](../16-eight-statistics/) (which waits on question 4)
