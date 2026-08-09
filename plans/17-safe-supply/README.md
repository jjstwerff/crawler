# `17` — A settlement's output is a function of the danger around it

**Issue:** [`jjstwerff/crawler#17`](https://github.com/jjstwerff/crawler/issues/17) ·
**Value:** `G` · **Effort:** `M`

## Status

**`status:active` from 2026-08-09** (user), taking `#12`'s slot — the roster is
`#11`/`#13`/`#17`, still at the cap of three. `S0` is shipped: the design (`CRAFTING.md`)
and the measurement of what already exists, which turned out to be most of it. `S1`–`S6`
are **designed, not built**, and each is written out below.

**Why it earns the slot:** it is the design everything else now queues behind. `#16` waits
on it by construction (`M3` authors 18 Handiness values against this system), and its own
first steps are small — `S1`/`S2` are one predicate and one category, against machinery
that already exists.

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
| **`S1`** — a safety category over the surface | S | `make test` (`safetytest`) | ✅ **Shipped** |
| **`S2`** — workers refuse to ENTER unsafe ground | S | `make test` (`safetytest`) | ✅ **Shipped** |
| **`S3`** — stock: workers raise it, workshops draw it | M | `make test` (extend `producttest`) | Blocked on `S2` |
| **`S4`** — the world shows it, with no panel | M | `make play`, a user read | Blocked on `S3` |
| **`S5`** — safety is CONTESTED: sources send incursions | M | `make test` + a `scripts/*.play` session | Blocked on `S2` |
| **`S6`** — item damage as an EVENT (no running wear) + repair | S | `make test` + a `scripts/*.play` session | **Designed, not built** |
| **`S7`** — standing, and the militia it raises | M | `make test` + a `scripts/*.play` session | **Designed, not built** |

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

## What `S1`/`S2` turned up — measured 2026-08-09

Both shipped. `hex_safe(s, q, r)` is the category (`THREAT_R = 6`, `GUARD_R = 4`); a living
hostile spoils ground, a guard within reach holds it. `npc_may_enter` is the term, and
`safetytest` gates four claims with each seen **both ways**.

⚠ **THE GATE FOUND A DESIGN ERROR ON ITS FIRST RUN, and it was in the obvious term.**
Keyed on `awake` — which is what "a dangerous monster" means everywhere else in this engine
— the predicate reported a freshly generated level as **entirely safe: 416 open hexes, 0
unsafe**. Monsters sleep until they perceive the **player**.

That is backwards for `I-SAFE`. **A sleeping monster in the woods is exactly why nobody goes
into the woods.** `awake` describes a monster's reaction to the *hero*; a farmer's danger
does not wait for the hero to arrive. Keyed on **presence** instead: 87 safe, 329 unsafe on
the same level. ⚠ The lesson generalises past this row — this system asks *"is it dangerous
to a civilian"*, and every existing danger signal in the engine answers *"is it dangerous
to the player"*.

⚠ **AND THE ASYMMETRY IS LOAD-BEARING, not a nicety.** `npc_step` freezes an NPC when no
neighbour is passable, so a symmetric rule would **trap** a worker in newly-dangerous ground
instead of keeping it out. The rule is therefore *enter, never leave*: safety blocks a step
**into** danger and anyone already standing in it may always move. `safetytest` asserts both
halves, and finding a genuine **safe→unsafe border** to assert them on was itself the fiddly
part — on a level that is 329/416 unsafe, any hex adjacent to an unsafe one is usually
unsafe too, so the first version of that row failed for a reason that had nothing to do with
the code.

**Found while measuring:** guards are exempt by construction (walking toward trouble is the
job) and so are wild things — and `npc_step` is only ever called for `role != 0`, so
hostiles never reach the predicate at all.

⚠ **Not yet measured: cost.** `hex_safe` scans the enemy list per call and is asked for up
to six neighbours per NPC per step. The gate's own timing line is the instrument; if
`safetytest` or the town tests move, `S3` should carry a cheaper form before it adds more
callers.

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

### `S7` — standing, and the militia it raises, designed

The player's push **out**, where `S5` is the world's push **in** — the two halves of contested
safety, and they meet in one predicate. `hex_safe`'s second term is *a guard within
`GUARD_R`*, so **a militia is guards the settlement would not otherwise have posted**: no new
safety mechanism at all, one new *source* of role-3 actors. `S1` bought this without knowing
it.

Four rulings (user, 2026-08-09): a player can raise a local militia and it enlarges the safe
area · **they must kick-start it themselves** · they **return later** for the tough spots the
militia cannot take · and **they do not begin with the standing to ask — it is earned
locally.**

⚠ **THE VERB IS ALREADY BUILT, AND SO IS THE FICTION.** `sim_talk_to` — bumping a civilian
speaks — already carries the town's quest lines, and `guard_master` already runs a bounty
chain (`q_poster` 0→1→2→3: hear the posting, bring the head, be paid) whose closing line is
*"The roads breathe easier."* **The settlement already says its safety changed; there is just
no number behind it.** So petitioning costs **zero keys** — bump-to-petition, beside
bump-to-open and attack-on-push (`DESIGN.md` §3a pillar **#7**, *lean inputs*) — and
`I-SAFE`'s zero-new-keys claim survives a system that grows the hero's reach.

**Standing is per settlement, and a CATEGORY, never a bar.** The same argument as `S1`: a
threshold the player can cross and see crossed, not a float that slides. *Stranger → known →
trusted.* Earned by acts within that settlement's reach — the kind `q_poster` already counts.
⚠ **Local, never global karma.** It must be possible to be a hero in one valley and a stranger
in the next, or the campaign has a single reputation number and every settlement after the
first is scenery.

**The militia advances by POSTING PICKETS, and it stalls at a cause.** A picket is a guard
posted outside the walls; it holds `GUARD_R` around itself, so the pickets *are* the frontier.
It advances into ground it can hold and stops where an `S5` source out-weighs it. ⚠ **That is
what makes "come back later" a world state rather than a timer** — the militia is not a
progress bar filling while the player is away (`F7`, the treadmill). It is stalled at a
legible place *because of a legible thing*, and it moves again when the player kills the
cause. **Eligibility, never a schedule** (`SCRIPTING.md`) — the rule `S5` already runs on.

**And this is the campaign's advancement axis** (user: *"players will migrate to be bigger
heroes during the campaign this way"*). The hero grows in **what they can cause**, not in what
they can press: levels and gear scale the arm, standing scales the reach. ⚠ **It is the one
advancement axis that costs the interface budget nothing** — which is how a hero gets big in a
game that means to stay at 15 keys.

#### What `S7` turned up before a line was written

⚠ **`DESIGN.md` §3a pillar #6 is STALE, and this is its second departure.** The pillar reads
*"No factions / NPCs … never a social sim"*; the recorded relaxation is the co-op ally faction
alone. But the settlement NPCs this entire plan stands on — farmers, gatherers, carts, a guard
master with a quest chain — **already relaxed it, and nobody wrote it down.** The guard rail
that keeps `S7` from being the social sim the pillar means to forbid: standing is **one number
per settlement, earned by acts, read as a category, with exactly ONE consumer** (the militia).
No dialogue tree, no disposition matrix, no per-NPC relations. **A second consumer is the
moment to re-check**, not a free extension.

**`Politics` finally has a mechanism.** `CATALOG.md` §1 authors *Politics* (Char·Perc) —
*"faction/parley (overland-side)"* — a one-line power with nothing behind it anywhere in the
tree. Standing is what it is **for**: it should move the *rate* or the *threshold*, and ⚠
**never be required**, or a utility power becomes a gate on the campaign's advancement axis.
It also makes **Char** a second consumer, which is [#16](../16-eight-statistics/)'s business.

**The moros anchor** (`MOROS.md`): moros' standing is per-NPC **and per-PLACE**, earned by
acts, and it gates access — *"reference cards … earned when the party reaches the standing each
card describes"*, and *"cards reward engagement, not exposure"* (`doc/claude/RULES.md`). crawler
takes the **shape** — local, earned, gating — not the cards.

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

5. **Do pickets cost the settlement anything?** If a militia is drawn from the same people
   `S3` counts, then safety and output trade against each other and the player picks the
   balance — richer, and a real risk of **starving the loop it was raised to feed**.
6. **Can standing fall?** `S5` says safety is not a ratchet; the symmetric question is whether
   *standing* is. ⚠ Falling standing is where this stops being one number and starts wanting a
   social sim — the pillar-#6 guard rail above is what that decision has to clear.

## See also

`CRAFTING.md` · `CATALOG.md` `OW2` (the decision this answers the crafting half of) ·
[plan #16](../16-eight-statistics/) (which waits on question 4)
