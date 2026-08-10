# CRAFTING.md — the settlement makes things; the hero makes that possible

> **Design, 2026-08-09** (user direction). Tracked by
> [plan #17](plans/17-safe-supply/). ⚠ This doc owns the design; the plan owns the
> schedule and the step status.

## The inversion

The usual RPG crafting loop is *hero gathers → hero crafts → hero equips*, and it ends in a
menu. This one runs the other way:

> **The materials are mostly not heroic.** Ore, hides, herbs, grain — the village and city
> NPCs mine and gather them. **The heroes have to keep them safe to do so.**
> — user, 2026-08-09

So the player never gathers and never crafts. They do the one thing they already do — make
somewhere less dangerous — and the settlement's output follows.

> ## I-SAFE — a settlement's output is a function of the danger around it, and the hero's only lever on it is the one they already hold.
>
> Nothing the player learns is new. **Zero new keys**, no crafting screen, no recipe list,
> no material inventory. The depth is entirely in the derivation.

⚠ **That is the whole justification under `DESIGN.md` §3a pillar 0** (bounded simulation —
*depth in the derivation, shallow at the interface*). A crafting system that added a verb
would have to displace one; this one adds **none**, because the player's input is combat
they were already doing. It is the same trade `SCRIPTING.md` makes: derive as deep as you
like, but ask of every mechanic — *does this add something the player must learn?*

## What already exists — measured 2026-08-09

⚠ **Most of this system is built.** The parts below are shipped, and reading them first is
what keeps this design from re-inventing a town that already lives.

| | shipped today |
|---|---|
| **gatherers** | role **9** rugged travellers fetch alchemist ingredients from scree/meadow picking grounds, camping where dusk finds them, shunning the deep mountains (`OVERLAND.md` §13c). ⚠ **Shipped as CODE, absent from the MAP** — measured 2026-08-09: no gatherer spawns in the home world, because a picking ground needs scree-or-meadow ≥14 hexes from a town centre and meadow is **0.3 ‰** world-wide. The cause is an ordering defect in `ov_kind_at`, written up in [plan #1](plans/1-ortler-worldgen-fixture/). A system can be complete, tested, and never execute |
| **gathering is real, not narrative** | a gatherer adjacent to a **wild thing** (role 12) takes it: `w9.alive = false; // trapped: ingredients for the factory` (`sim.loft`) |
| **other producers** | farmers cycle home → field → stalls *carrying the crops*; fishers fish; boats and ships work the water and anchor at the harbour |
| **distribution** | merchant carts run multi-day road routes with weight caps and two slots; merchant ships land goods from beyond the window; road stops at day intervals |
| **the workshops** | seven producer kinds on a day/week rotation — forge weapon/armour, alchemy (3 days of 7, one type, a batch of 5), scriptorium scroll/book, town craft, import |
| **the repertoires are content** | `BUNDLE.md`'s `production` section: the rotation is engine **mechanism**, *what* each workshop makes is bundle-owned (`I-PROD`) |

**What is missing is exactly one thing: consequence.**

| | today | why it matters |
|---|---|---|
| **danger is invisible to a worker** | `npc_passable` knows walls and water; it knows nothing about hostiles. A gatherer walks past a monster as if it were scenery | nothing can be avoided, so nothing can be made safe |
| **there is no safety category at all** | no per-area state anywhere says *unsafe* | the player has no target to flip |
| **production consumes no input** | workshops produce on the clock regardless | supply cannot fall, so protection cannot pay |

⚠ Note what is NOT missing: civilians being invulnerable is **fine and stays that way**.
Under avoidance, nothing has to be able to die for the loop to close.

⚠ **THE LOOP IS OPEN AT BOTH ENDS AND CLOSING IT IS THE DESIGN.** Not new content: a
danger, a stock, and the arithmetic joining them.

## The loop

```
   a source sends something  ──►  an area turns unsafe  ──►  its workers stay away
            ▲                                                        │
            │                                                        ▼
   the hero goes at the SOURCE  ◄──  thinner stalls, worse gear  ◄──  stock and output fall
```

⚠ **The left edge is what makes it a world rather than a chore**: the hero's move is
against the *cause*, not a periodic re-clearing of the same ground (`D`).

Read the other way round it is the reward: clear a valley, and a week later the forge has
something you want. ⚠ **The delay is the point** — an immediate reward would make this a
quest-giver, and a quest-giver is a schedule (`SCRIPTING.md`: *nothing is scheduled,
everything is eligible*).

### The hero's lever grows — the militia (user, 2026-08-09)

⚠ **The left edge does not stay one hero with a sword.** Once a player has earned **standing**
with a settlement — *locally*, and they do not begin with it — they can **kick-start a local
militia**, which enlarges the safe area without them. It advances where it can hold and
**stalls at the tough spots**, and the player returns to break those.

That keeps `I-SAFE` exactly as written, because **the lever is still the one they already
hold**: standing is earned by the acts they were already doing, and the petition is
`sim_talk_to` — bumping a civilian, already built and already carrying the town's quest lines.
**Zero new keys still.**

⚠ **AND IT IS THE CAMPAIGN'S ADVANCEMENT AXIS**, not a side system: *"players will migrate to
be bigger heroes during the campaign this way"* (user). The hero grows in **what they can
cause**, not in what they can press — the only kind of growth that spends nothing from the
interface budget. Designed in full as [plan #17 `S7`](plans/17-safe-supply/#s7--standing-and-the-militia-it-raises-designed).

## The three pieces to build

### `A` — a worker will not enter an unsafe area

⚠ **They avoid it; they do not die in it** (user, 2026-08-09). A miner, farmer, fisher,
gatherer or merchant simply **does not go** where it is unsafe — the field is not worked,
the picking ground is not picked, the route is not walked. **The players have to get an
area into the SAFE category first.**

**This is one term on one predicate.** `npc_passable(s, role, q, r)` already decides where
each role may walk — bounds, walls, water by role — and site selection already **shuns**
(the alchemist's gatherer avoids the deeper mountains by construction). Safety is the same
kind of clause, in the same place.

⚠ **AND THAT IS WHY THIS MECHANISM IS THE RIGHT ONE, not just the kinder one.** Compare
what the alternative cost. *Killing* gatherers needs NPC damage, some notion of NPC
survival, a corpse or a disappearance, a replacement rule so a settlement cannot die out,
and a story for a player who never sees any of it happen. **Avoidance needs a term in a
function that every working NPC already calls** — the re-assertion count is **one**, and
forgetting it is loud (a worker visibly standing in a dangerous field), not silent.

⚠ **Guards must matter or the town has no agency.** Guards already patrol day and night;
their presence is a term in the same expression. The player is one input to safety, never
the only one — otherwise the settlement is scenery waiting to be rescued.

### `B` — a workshop needs its inputs

Production draws from a per-settlement **stock**, raised by gatherers arriving home and
drawn down by making. Empty stock, no output that day. ⚠ **Stock is a NUMBER PER
PRODUCER, not an item inventory** — the moment it becomes items, somebody wants a UI for
it, and the interface budget is spent.

**The seam is `I-PROD`'s, unchanged:** the rotation and the arithmetic are engine
mechanism; which material a producer draws and which item it yields is **bundle content**,
declared beside the `production` repertoire it already owns.

### `D` — and safety is LOST again: monsters, wars, raiders

⚠ **Safety is not a ratchet** (user, 2026-08-09). An area that is safe today can stop
being safe: monsters spread, a war moves a front, raiders take a road. Without this the
game has an end state — clear the map once, and the world is solved furniture.

⚠ **BUT THE OBVIOUS IMPLEMENTATION IS THE ONE THAT RUINS IT.** *Decay* — every cleared
area slowly reverting on a timer — turns the whole design into a treadmill: the same valley,
re-cleared forever, which is a chore wearing a system's clothes. The distinction is worth
stating as a rule:

| | what the player experiences |
|---|---|
| ⚠ **uniform decay** | *"my work rots on a timer"* — no cause to address, no decision to make, and the only counter-play is to keep redoing it |
| ✅ **incursion from a SOURCE** | *"something came from somewhere"* — a den that was never cleared, a warband on a road, a front that moved. **There is a cause, and a player can go at the cause instead of the symptom** |

So pressure **arrives**; it does not accumulate. And because it arrives *from* somewhere,
the map keeps a structure the player can read and act on: the valley is unsafe **because**
of the thing over the ridge.

⚠ **AND IT IS ELIGIBILITY, NOT SCHEDULE.** `SCRIPTING.md`'s rule holds here exactly: a
raid is not due at day 30, it becomes **possible** when the conditions are true (a road
unwatched, a den grown, a war nearby) — and if the conditions never arrive, it never
happens and nothing is owed. That is also what keeps it from feeling like a punishment for
progress.

**What the player's investment buys, so it is not futile:** the counters are already in the
world — guards patrol, walls ring the big towns, roads carry carts. ⚠ **A cleared source
stays cleared**; what returns is a *new* thing from a *new* place. Durable enough to be
worth doing, contested enough to stay alive.

### `C` — the settlement says so, in the world

No panel. The stalls thin out, the forge's rotation skips, a gatherer's route stops being
walked, the innkeeper says the roads are bad. ⚠ **The player must be able to read the
state without being told it** — that is the `SCRIPTING.md` *no markers* rule, and it is
the difference between a living town and a resource meter.

## Handiness — repairs and improvised gear, NOT crafting

> **Handiness gates repairs and improvised gear, not crafting.** — user, 2026-08-09

That resolves the axis question and keeps `I-SAFE` intact: the hero still never *makes*
anything the settlement makes. They **keep what they have working**, and **make do** in the
field. Two halves, and measuring them found they cost very differently.

| | state today | cost |
|---|---|---|
| **improvised gear** | ✅ **already designed** — `Ingenuity` (Hand·Will), *"improvise a weapon/tool mid-scene"* (`CATALOG.md` §1), and races already carry it (Badgers, Beavers) | **none.** It is a **card**, priced in an action under §6.3's economy. No new verb, no new system |
| **repairs** | ⚠ nothing exists — no condition or damaged state in `items.loft`/`sim.loft`, and `sim_damage` branches on `"physical"` only | **small** — one item state, caused by events, ✅ **no running degradation** (below) |

### ⚠ NO RUNNING DEGRADATION — damage is an EVENT, and my scepticism was aimed at the wrong mechanic

> **There is no running durability degradation, but there can be problems that are the
> result of failures or special circumstances that can degrade an item until it is
> repaired.** — user, 2026-08-09

Two mechanics wear the word *durability* and they are not the same thing:

| | what the player does | interface cost |
|---|---|---|
| ⚠ **wear per use** | watches a meter, maintains gear on a schedule, repairs *because time passed* | **high** — a maintenance chore, invisible until it bites, and the thing §3a's friendly-tuning clause is right to refuse |
| ✅ **damage from an EVENT** | notices *something happened*, and gets it fixed | **small** — one state on one item, and the **event itself teaches the rule** |

⚠ **AND THE SECOND IS ANGBAND'S ACTUAL MODEL**, which settles it under `CLAUDE.md`'s
faithfulness rule rather than as a preference. Angband has no wear-per-swing: it has acid
damaging armour, fire burning scrolls, specific attacks ruining specific things. So this is
the **faithful** design, and the durability I was sceptical of is a mechanic Angband does
not have either.

**What it needs, and it is small:** one damaged state per item (the `IF_*` bitmask has
room, or a small condition integer), set by a *cause* the player can see — a failure, an
elemental hit, a special circumstance — and cleared by a smith, or in the field with
`Handiness` setting how well.

⚠ **THE CAUSES DO NOT EXIST YET AND THAT IS FINE.** `sim_damage` branches on `"physical"`
alone; there are no elemental types to burn a scroll with. The state can land first with a
single honest cause, and gain more as the damage model grows — but ⚠ **each cause must be
legible in play**, or this becomes wear-per-use wearing an event's clothes: gear that
degrades for reasons the player cannot attribute is a meter with extra steps.

**Why it earns its place:** it is what gives the player a *personal* stake in `I-SAFE`.
Without it the supply loop improves the stalls — someone else's gear. With it, an unsafe
valley eventually means **your** sword stays chipped and the forge you protected is the one
that fixes it. The loop closes on the player, not only on the town.

**The cheap form, if it is taken:** condition is a small integer on an equipped item,
degraded by use, restored by a smith — or in the field, worse and slower, with `Handiness`
setting how well. ⚠ **No repair kits, no material cost to the player, no menu**: the moment
it needs an inventory of parts it is crafting, which is the thing this design says the hero
does not do.

### Handiness is a DEGREE, never a KEY

> **Handiness is still very useful for a crafter, but learned skills are the gate there.**
> — user, 2026-08-09

⚠ **So the axis never grants permission — anywhere.** It says *how well*, not *whether*:

| | the gate (permission) | Handiness (degree) |
|---|---|---|
| **crafting** | a **learned skill** | how good the result is |
| **repairs** | a smith, or the field option | how much condition returns, how fast |
| **improvised gear** | the `Ingenuity` **card** — learned or innate by race | what the improvisation is worth |

**This is already the adopted economy's own shape, not a new rule.** `CATALOG.md` §6.3
gates a spell *"by stat **and mastery** instead of a fail-roll"* — mastery is the learned
half, the stat is the degree. Crafting reads identically: **skill permits, Handiness
qualifies.**

⚠ **AND IT KEEPS `I-SAFE` HONEST WITHOUT LOCKING A DOOR.** The hero does not craft because
they have not *learned* to — not because a stat forbids it. That is a content decision a
bundle could revisit, and it would still not add a verb: a crafting skill would be a
learned thing priced like every other learned thing. What the hero must never become is the
*supplier*, because then the settlement stops mattering and `I-SAFE` is dead.

**For `#16` `M3` this is the statable thing a race's Handiness means:** *how good this
people are at fixing and making do* — and, for the NPC smiths a settlement holds, why one
forge turns out better work than another. Not a permission anywhere.

## Failure paths

| | how it breaks | the answer |
|---|---|---|
| **F1** | it becomes a fetch quest — "clear the mine, get the sword" | eligibility, never a schedule. Nobody asks; the world just gets better or worse |
| **F2** | it becomes a management screen | stock is a number the player never sees; §3a pillar 0 |
| **F3** | the player cannot tell why the forge stopped | `C` — and avoidance makes it nearly free: **an empty field IS the signal.** The absence of the worker is the readout, in the world, with no panel |
| **F4** | grinding: farm hostiles to pump output | output is capped by the workshop's rotation, which is a *clock*, not a counter. Safety removes a brake; it is not a throttle you can spin |
| **F5** | ~~a settlement dies unrecoverably~~ | ✅ **dissolved by avoidance.** Nobody is lost, so there is no attrition and no death spiral — a shunned settlement is idle, not dying, and resumes the day the area is safe |
| **F6** | the player never notices any of it | ⚠ the real risk, and the one to measure first. If the loop cannot be seen in a session, it is a simulation nobody plays |
| **F7** | ⚠ **the treadmill** — cleared ground reverts on a timer and the player re-clears the same valley forever | `D`: pressure **arrives from a source**, it does not accumulate. A cleared source stays cleared; what returns is a new thing from a new place, and the counter-play is to go at the cause |
| **F8** | it reads as a punishment for progress — the better you do, the more arrives | eligibility, not schedule (`SCRIPTING.md`): conditions, never a difficulty dial keyed to the player. And the world's own counters (guards, walls, roads) hold ground the player is not standing on |

## What this design does NOT add

- **No crafting verb, screen, recipe list, or material inventory.** Zero new keys.
- **No hero gathering.** Materials are *not heroic* — that is the premise, not a limitation.
- **No new content type.** Materials and yields are rows beside the `production` repertoires
  a bundle already declares.
- **No change to the spell economy.** `CATALOG.md` §6.3's cards-and-Tension is the
  *advancement* economy and is untouched; this is the *material* one. They meet only where
  a crafted item is a card's cost, which is out of scope here.

## Open questions

1. **Does the hero ever hold a material?** The premise says materials are not heroic — but a
   boss dropping the one heroic ingredient, carried to a smith, is the classic beat. Allowing
   it costs an inventory item and no new verb; forbidding it keeps the inversion pure.
2. **Is stock per settlement or per producer?** Per producer is simpler and lets a forge
   starve while the bakery runs; per settlement is one number and reads more like a place.
3. **What is the safety expression?** Guards, distance from the walls, hostiles alive nearby,
   time since the player cleared something — and it must be **derivable and cheap**, since it
   runs per NPC per day.
4. ✅ **RESOLVED 2026-08-09 — `Handiness` gates repairs and improvised gear, not crafting**
   (see the section above). [Plan #16](plans/16-eight-statistics/) `M3` is unblocked: a
   race's Handiness is a bet on *keeping gear working and making do*, which is a statable
   thing. ⚠ **One sub-decision remains**: improvisation is free (it is already the
   `Ingenuity` card), **repairs need a durability mechanic that does not exist** and that
   charges the interface budget. Decide that before `M3` writes 18 values, or the numbers
   are again a bet on something undesigned. ⚠ Note the axis is a **degree, never a key**
   (above), so `M3` can proceed on the *meaning* even while the durability call is open.

## See also

- `OVERLAND.md` §13b (the daily loop), §13c (trade, the gatherers, the alchemist-factory)
- `BUNDLE.md` → *The `production` section* — `I-PROD`, the seam this extends
- `DESIGN.md` §3a pillar 0 — the interface budget this design spends nothing from
- `SCRIPTING.md` — *nothing is scheduled, everything is eligible*; the *no markers* rule
- `CATALOG.md` `OW2` — the economy decision this answers the crafting half of
