# `17` — A settlement's output is a function of the danger around it

**Issue:** [`jjstwerff/crawler#17`](https://github.com/jjstwerff/crawler/issues/17) ·
**Value:** `G` · **Effort:** `M`

## Status

**`status:active` from 2026-08-09** (user), taking `#12`'s slot — the roster is
`#11`/`#13`/`#17`, still at the cap of three. `S0` is shipped: the design (`CRAFTING.md`)
and the measurement of what already exists, which turned out to be most of it. `S1`–`S3` and
**`S5`** are **shipped, armed and closed** — `I-SAFE` holds end to end as of 2026-08-10;
`S4`, `S6`, `S7` are designed, and each is written out below.

> ## ✅ `I-SAFE` IS CLOSED END TO END (2026-08-10)
>
> On the **shipped** world (`story.loft`'s `GEN_SEED`), four days with the den alive against
> four with it cleared: **0 deliveries against 3**, and the store never holds anything at all
> under pressure. The settlement's output is now a function of the danger around it, gated by
> `stocktest` row 7 as an A/B and verified able to go red.
>
> ⚠ **And the cause `S5` recorded was wrong on both counts** — the trapping arm fired **zero**
> times, and what actually raised output was `npc_may_enter`'s escape hatch. → *`S5`'s
> diagnosis was wrong, and the measurement that found it*, below.
>
> ✅ **And the town holds its own centre now** (user, 2026-08-10): the guard master's beat is
> the centre and the market seat rather than a **duplicated** ring leg, so both sit inside
> `GUARD_R` continuously — 215/400 ticks unsafe → **0**. The mine stays 400/400, which is the
> plan's designed lever, not a defect. → *the site veto gave two OLD numbers a consumer*.
>
> **→ NEXT: `S4`** (the world says it, with no panel), then `S6`/`S7`.

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
| **`S3`** — stock: workers raise it, workshops draw it | M | `make test` (`stocktest`) | ✅ **Shipped and ARMED** |
| **`S4`** — the world shows it, with no panel | M | `make test` (`safetytest` row 8) + a user read | ✅ **Shipped** — `I-SAY`, and `F6` measured at **tick 19** |
| **`S5`** — safety is CONTESTED: sources send incursions | M | `make test` (`incursiontest`, `stocktest`) | ✅ **Shipped, ARMED and CLOSED** — `I-SAFE` holds end to end |
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
⚠ **The second half shipped a day late and was the load-bearing one** — see *the real
mechanism*, below: the step term alone leaves a worker free to live inside danger.
⚠ **Guards are a term in the safety expression, not spectators**, or the settlement is
scenery waiting to be rescued.

### `S3` — stock, designed

A **number per producer**, raised on arrival home and drawn on making; empty means no
output that day. ⚠ **Never an item inventory** — the moment it is items somebody wants a
screen for it, and the interface budget is spent (`F2`). Which material a producer draws
and which item it yields is **bundle content**, declared beside the `production` repertoire
that bundle already owns — `I-PROD`'s seam, unchanged.

### ✅ `S3` is BUILT, ARMED and GATED — and it took three defects, all measured 2026-08-10

The arithmetic: `prod_stock` (a number per producer, indexed by `items.loft`'s
`producer_index`), `prod_raise` / `prod_draw`, `sim_prod_stock`. **I-STOCK: stock == raised −
drawn at every tick**, both discrete events; `stocktest` asserts the conservation directly,
including that asking for more draws than there is stock is refused rather than going negative.

**`desert_surprise` declares the first real `production` section** — `"alchemy":
["naga_antivenin"]`. That closes a finding worth its own line: **the merge's bundle arm had
never executed.** `producttest` walked a `0..bundle_production_len` loop that ran zero
iterations, so `I-PROD`'s bundle half was gated only in the sense that it compiled.

⚠ **Arming it required fixing three separate defects, and each was hidden by the one before
it.** All three were invisible to every existing gate, because the symptom of all three is
*stock stays 0* — which reads exactly like "the town is at peace".

| # | the defect | how it looked | the fix |
|---|---|---|---|
| 1 | the gatherer's schedule alternated between the picking ground and a **second far point**, so it never came home | a worker wandering the wilds forever | the **bag steers**: empty → picking ground, full → home (`carry`) |
| 2 | civilians stepped **greedily** — a neighbour had to be *strictly* closer — so they froze at the first concave obstacle | frozen 13 hexes out, permanently | civilians get the **flow field** monsters have had since the AI landed, one per (destination, movement class), built once and kept |
| 3 | the picking ground was sited **nearest-first with no reachability check**, and only meadow/scree counted | `path home→pick = ∞`; of 9801 hexes the town can walk to **498**, and they are 467 grass + 31 road — no meadow, scree or forest at all | site from a **flood fill** (`walk_reach`), and rank the terrain (`pick_rank`: alpine shelves → woodland → grass) |

⚠ **So role 9 had been decorative since the day it was added** — the gatherer that df7a359
celebrated as "finally existing" was placed, walked, and had never once gathered. Its "picking
grounds ≥14 hexes out: 0 → 124" counted hexes **without checking any of them could be walked
to**; none could.

**Then the tuning, which is also measured.** With a reachable ground the gatherer runs ~2.5
round trips a day against an alchemist brewing three days in seven. Uncapped, **stock reached
120 in 16 days and simply grew** — and a store that is never empty gates nothing, so the plan's
claim would have been true in the code and false in the game. So:

- **`GATHER_LOAD = 1`** — a trip brings one load.
- **`PROD_STOCK_MAX = 8`** — a store has walls, so it fills in peace and *drains* when the
  gatherer stops. The cap is the load-bearing number, not the load.
- **one draw per POTION, not per day** — a half-supplied alchemist makes a **short batch**
  rather than nothing, so the stall thins before it empties. That is `S4`'s readable signal
  arriving for free, with no interface spent.

**Measured after arming:** stock oscillates 2..8 rather than pinning; 27 potions over 16 days
against 30 unarmed, so a safe town runs near-normally and the mechanism only bites when supply
stops. `stocktest`'s live row watches a week and requires deliveries to arrive **and** the
store to be drawn down — both failure modes (stuck at 0, stuck at the cap) are named.

⚠ **What is still NOT gated end-to-end: hostiles → no output.** The two links are each gated
separately — `safetytest` proves a worker will not enter unsafe ground, `stocktest` proves no
supply means no output — but nothing yet places hostiles on a picking ground and measures the
stalls thinning. **That composition is `S5`'s**, which is where contested safety is built.

### `S4` — the world says it, designed

Thinner stalls, a skipped rotation, an unwalked route, an innkeeper's line. ⚠ **`F6` is the
real risk and this step is the answer to it**: if the loop cannot be *seen in one session*,
it is a simulation nobody plays. Measure that before polishing anything else.

### ✅ `S4` is BUILT and GATED — and three of its four signals were already shipped

**I-SAY: what a worker says about its work is read from the same term that decides whether it
goes.** No flag, no schedule, no second state — so the line cannot drift from the world, and a
settlement can never claim a trouble it does not have.

| the design's four signals | |
|---|---|
| thinner stalls | ✅ already shipped — `S3` draws **once per potion**, so a half-supplied workshop makes a short batch |
| a skipped rotation | ✅ already shipped — an empty store refuses the whole brewing day |
| an unwalked route | ✅ already shipped — `S2`'s site veto keeps the worker at home |
| **an innkeeper's line** | **this step** |

⚠ **And the fourth is the only one a player can read WITHOUT A BASELINE**, which is why the
other three did not close `F6` on their own. Measured over three days, den alive vs cleared:
the stall difference is **2 potions against 1**. One item is not something a player who has
never seen the other number can read, and an idle worker is indistinguishable from a worker
who is simply idle.

> The rugged traveler shakes their head: 'A goblin on the picking ground,
> north-west of here. I'll not go while it stands.' The stills will run dry.

**Creature and bearing are derived at the moment of asking**, never authored — so the line is
*produced, not stored*, and stays true as the world moves. It names the **cause**, which is
what makes it actionable: *"something is wrong"* is a mood, *"an ogre at the ore face, west of
here"* is somewhere to go.

⚠ **Zero new keys** — bumping a civilian already talks (DESIGN §3a pillar #7). ⚠ **And a
person speaking is not a marker**: `SCRIPTING.md`'s *no markers* rule forbids the UI pointing
at things, while the design's own list of four ends with *"the innkeeper says the roads are
bad"*.

**The gate is the invariant, not an example** (`safetytest` row 8): across the whole town,
*"says why it is idle"* and *"its work site is unsafe"* must be the **same set** — both sides
non-empty, and the named creature actually standing there. A row that watched one talkative
miner would pass equally against a line that is always spoken, or never. Two negative controls,
each landing on its own assertion: made unconditional it reports *"6 workers' words disagree
with what they actually do"*; with the name stubbed, *"names no creature that is actually
there"*.

#### ✅ The `F6` measurement the plan asked for, on the world players actually start in

⚠ **The row ticks 100 times first, and that is not a convenience.** The shipped world is
**safe at genesis** — 0 workers with an unsafe site — and the trouble **arrives**, because
that is `S5`'s whole design. A row reading genesis would be reading the town before its story
begins, find nothing said, and conclude the mechanism was broken.

**On `story.loft`'s own `GEN_SEED`, the first worker reports a trouble at tick 19, and is
still reporting it at tick 599.** The signal is there before a player has crossed the square,
and it does not blink out. That is the `F6` answer.

#### ✅ And the whole plan now measures the world players start in

⚠ **Every measurement in this plan was taken on world 777 while the game ships 1337**
(`story.loft`'s `GEN_SEED`) — so every number it published described a world nobody plays.
Switched 2026-08-10: `stocktest` and `incursiontest` run 1337; `safetytest` already did. The
overland is a **fixed contract wilderness**, so the *town* is identical either way — what a
seed varies is **monster placement**, which is this plan's entire subject.

**It was not a find-and-replace, because the thresholds had to be re-derived:**

| four days | at peace | under pressure |
|---|---|---|
| **1337** (shipped) | 3 deliveries, stock 0..1 | **0 deliveries, stock 0..0** |
| 777 (as published) | 7 deliveries, stock 0..4 | 1 delivery, stock 0..1 |

⚠ **The A/B separates MORE sharply on the shipped seed — the store never holds anything at
all under pressure. What falls is PEACE**, and the cause is measured rather than guessed: the
gatherer spends **1023 of 1600 daylight ticks frozen mid-route**, stalled at safety borders
while ambient wildlife drifts across an unescorted 14-hex walk. On 777 it is 887, so this is a
difference of **degree, not kind** — the shipped world's peacetime supply is simply marginal.

**That is the design working, not a defect to tune here.** An unescorted civilian crossing
monster country is slow, and **`S7`'s pickets are its designed answer** — a militia posts
guards, guards hold ground, held ground is ground a worker crosses without stopping. It is
worth noticing that `S7` now has a *measured* thing to improve, which it did not before.

So the gate's peaceful bar is **2 against a measured 3**, and the margin is thin **on
purpose**: the reason it is 3 is a property of the shipped world, not slack in the row, so a
drop to 1 is a real regression and must go red rather than be absorbed. A separate
`peace_hi > 0` names *"the store never held anything"* apart from *"too few trips"*.

⚠ **Re-verified able to go red on the new seed**, which is the check that matters whenever a
gate changes worlds: with the veto off it reports **3 under pressure against 3 at peace** and
fails on the 2× margin. `incursiontest`'s preconditions all hold on 1337 unchanged — source
present, one raider on the first dawn, 12 → 3 hexes in 15 ticks, the cap binding at 2, and row
7's safe/unsafe/safe still reading three ways.

#### ✅ `questtest` switched too — and switching it found a defect

⚠ **It went red, which was the useful part.** The infestation row asserted `inf1 > inf2` on
`count_glyph(level, "J")` — but that counts **every** snake on the level, and normal
generation places snakes too. On 777 depth 2 happened to hold 4 natural snakes, so `4 + 4`
brood `= 8` against depth 1's `11 + 0 = 11`, and it passed. On the shipped world depth 2 holds
**7**, both totals come out at **11**, and a perfectly healthy mechanism reads as broken.
*The assertion was never about the brood; it was about the brood plus whatever else the seed
put there.*

Subtracting each depth's **boss-not-slain population** cancels the wildlife, and what is left
is exact: **brood 11 at depth 1 and 4 at depth 2** — precisely `desert_surprise`'s declared
`infest_d1: 11, infest_d2: 4`. So the row now asks for an **identity** rather than for
"enough", and reads the expectation from `world_placement()` instead of copying it, so a
bundle that re-authors its infestation moves the test with it rather than quietly failing an
engine gate. Verified red: +3 to the depth-2 count reports *"the brood is 11/7 against the
bundle's declared 11/4"*.

⚠ **Still on 777, and deliberately**: `cavetest`, `effecttest`, and `fieldtest` — the last
sweeps 777's surface *and* two dungeon depths as a **sample of worlds**, which is a different
kind of claim from "this is what a player gets".

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

### Cost, and the town — measured 2026-08-09

`S1` left cost unmeasured and named the gate's timing line as the instrument. ⚠ **That
instrument is invalid on this box and the reading it gave was pure noise.** An A/B of
`traveltest` said 27.7 s with the safety term and 65–70 s without — a 2.5× *speed-up* from
doing more work, which should have been disqualifying on its face. `uptime` explains it:
**load average ~20**, because this machine runs several agents. Re-running the identical
no-safety build gave **34 s, 44 s and 51 s**. ⚠ **Wall-clock A/B is not available here** —
any cost claim needs an operation count, not a stopwatch.

The **behavioural** measurement is load-independent, and it is the one that answers the
question. Over 40 ticks in the town, with the safety term and with it stubbed to `true`:
**19 civilians moved, 4 frozen — identical both ways.** So the term is not currently costing
the town its liveness, and it is not currently changing it either.

⚠ **And rows 1–4 had been proving the predicate on a level with no civilians on it.** A role
census settles it: `flow_genesis(1337, 1)` is **16 hostiles and nothing else**. The town is a
different world — **23 civilians in 11 trades**, and open ground that is **82 % safe** (4 940
/ 1 064) against the dungeon's 21 %. `safetytest` row 5 now gates the town directly, because a
town that generated entirely safe would leave every step from `S3` on **inert while still
passing its own tests**.

**The number `S3` has to answer to: right now exactly 2 civilian neighbour-steps are
refused.** The rule has territory — 1 064 unsafe hexes — but it barely touches anyone yet,
because nothing downstream consumes the avoidance.

⚠ **Which sharpens `S3`: the global ratio is the wrong measure. What matters is whether the
unsafe ground is where the WORK is.** A settlement whose unsafe 18 % is empty hillside loses
nothing and the loop stays invisible (`F6`). Stock must be measured against **fields, picking
grounds and routes**, not area — and if the overlap turns out to be near zero, that is a
placement problem to fix in `overland`'s scorer, not a number to tune.

## The overlap, measured 2026-08-09 — and it is ONE MINE

Every civilian carries its own work site (`wq2`/`wr2` — *"the field / fishing spot / patrol
leg A"*), so the overlap is **countable, not estimable**. ⚠ `ov_seed` is hard-coded to **7**
(`overland.loft:945`) — the depth-0 surface is the *example world authored as data*
(`OVERLAND.md` §12) — so a seed sweep varies **monster placement only**, never the town. Eight
placements, one town:

| | | |
|---|---|---|
| open ground unsafe | **14–20 %** | the number that means least |
| civilian work sites unsafe | **0–3 of 22** | ~9 % — already well under the area figure |
| **producer** sites unsafe | **0 or 2 of 5** | and always the *same* two |

**The five producers, and why three of them can never be starved:**

| producer | work site | from home | unsafe |
|---|---|---|---|
| farmer ×2 | fields `68,50` / `68,52` | ~12 | **0 of 8** |
| fisher | `44,67` | ~10 | **0 of 8** |
| **miner ×2** | **the mine `25,8`** | **~45** | **5 of 8** |

⚠ **THE FIELDS ARE SAFE BY CONSTRUCTION, NOT BY LUCK.** They sit inside the ring the guards
already hold (guard posts at `65,50` ×2, `43,61`, `42,39`, `GUARD_R = 4`), so making a field
unsafe needs a monster standing exactly where safety already denies. **The food supply is not
the lever and cannot be made into one** — which is not a defect: you put your fields where you
can defend them.

**The lever is the mine** — 45 hexes out, unsafe in five placements of eight. That is the
correct shape for `I-SAFE`, and today it is the loop's *entire* surface: **one site, two
workers.** ⚠ `safetytest` row 6 now gates the structure behind it (a producer must work beyond
guard+threat reach), because if a change ever pulls every producer inside the ring, safety
stops being able to touch production and every step from `S3` on goes **inert while still
passing its own tests**.

### ⚠ And the home town has no picking ground — for a reason no terrain fix reaches

⚠ **CORRECTION to the first version of this section, which claimed there were no picking
grounds *anywhere*.** That over-generalised from the home window. Measured per town: **2 of
the 4 towns have a picking ground in reach** (22 and 25 scree hexes in the 210–750 m annulus
the gatherer searches). The home town is not one of them.

**The chain is exact, and it ends somewhere terrain cannot help:**

1. `sim.loft:3139` — `intown = wwx == 0 && wwy == 0`. **Town life (houses, people, harbour,
   industry) belongs to the home window ONLY**; the land's own features place by world
   coordinates in whichever window holds them.
2. The home window anchors at `ov_towns[0]` (`sim.loft:3127`).
3. `ov_towns[0]` sits at `11316,6688`, window heights **−112 … 88 m** — a coastal lowland.
4. The gatherer's spawn is gated on `intown`, and its picking ground needs scree or meadow.
5. → **No gatherer can spawn in any world, ever.** Towns 2 and 3 *have* the terrain and get
   **no people at all**, because they are not the home window.

⚠ **So this was never a terrain-rarity problem — it is `ov_towns[0]`.** Fixing the alpine
bands (below) was right on its own evidence and changed this **not at all**: the town-by-town
count is identical before and after.

### ✅ The home window is anchored at the alpine town (user, 2026-08-09)

`ov_home_town(o)` replaces the literal `ov_towns[0]` at both sites that meant *the home town*
(the window anchor and the desert-gate reference). It picks **the town with the greatest height
reach in its window** — a property of the world rather than a magic index, so changing the
example world moves the home town with it. The reason is the one measured above: the home
window is the only window with people, so it must be the town whose surroundings can carry a
**whole** economy — valley fields *and* high ground for a mine and a picking ground. It selects
town **3**.

**What it bought — the gatherer exists:**

| | before (coastal) | after (alpine) |
|---|---|---|
| picking ground ≥14 hexes out | **0** | **124** (meadow 99, scree 25) |
| **role 9 gatherer** | **absent in every world** | **1**, working 50 hexes out |
| producers | 5 | **6** |
| producer sites unsafe | 2 of 5, in 5 of 8 placements | 2 of 6, in 3 of 8 |

⚠ **What it cost, and both are real.** **(1) The sea economy is gone**: roles **5 boat, 6 ship,
8 merchant ship** no longer spawn and the harbour with them, so *"goods from BEYOND the map"*
(`OVERLAND.md` §584) is not in the starting town any more. A fisher remains, on the river.
**(2) The starting neighbourhood is harder** — at the hex `surfacetest` used as its safe
vantage, the nearest hostile went from a **jackal (mlvl 1) 43 hexes away** to a **gnoll (mlvl
6) 8 hexes away**, and a level-1 hero standing there died on tick 13. That is `DESIGN.md` §3a
pillar **#8**'s (engaging onboarding, gentle curve) business and is **not addressed here**.

### ⚠ Four tests had the old world's geography written into them as literals

Moving the anchor did not break behaviour — it broke **constants**, and every one failed for a
reason unrelated to what its row tested:

| test | the literal | what it now does |
|---|---|---|
| `surfacetest` | `sim_teleport(surf, 75, 75)` — "watch from afar" | searches for open ground ≥20 hexes out that **`hex_safe`** calls safe (plan #17's own predicate) |
| `questtest` | wizard's window `(-3, -2)` | `sim_wizard_tower()` → `sim_window_of()` |
| `questtest` | ruin nest's window `(-1, -4)` | walks the world's ruin list until a window holds a `TAG_RUIN_BOSS` |
| `traveltest` | the gate is in the window the walk lands in, `(0, -2)` | `sim_desert_gate_world()` → `sim_window_of()`; the crossing half is untouched |
| `meshtest` | a sand hex on the home surface | generates the **gate's** window — the alpine home has no sand, so the row was silently checking nothing |

⚠ **`meshtest` is the one worth remembering: it did not fail loudly, it found no sand hex and
reported `sand-exact=false`** — a row that had been asserting a colour was, the moment the
world moved, asserting nothing. New kernel accessors: `sim_window_of`, `sim_wizard_tower`,
`sim_ruin_count`/`sim_ruin_pos`, `sim_desert_gate_world`.

⚠ **Cost: the gate went ~5 min → ~7 min**, because three tests now generate extra windows to
find what they used to assume. Worth it — but if it grows again, the answer is to cache a
generated window, not to put the literals back.

### The alpine bands were also wrong — fixed against the real data

The alchemist's gatherer (role **9**) needs **scree or meadow ≥14 hexes from the town
centre**. Terrain census of the home window: **grass 2 686 · field 1 805 · sea 5 588 · sand
31** — and **zero scree, zero meadow**. So no gatherer spawns, and the home town is a coastal
lowland.

Widening to the **whole 13 500 × 9 100 overland** (48 600 samples) does not rescue it:

| kind | share | |
|---|---|---|
| sea | 424 ‰ | |
| forest | 208 ‰ | |
| grass | 167 ‰ | |
| stone face | 93 ‰ | impassable |
| **scree** | **26 ‰** | exists — but up in the mountains, and no town window sampled has it |
| **meadow** | **0.3 ‰** (15 of 48 600) | ⚠ **effectively does not exist in this world** |

⚠ **So `CRAFTING.md`'s "shipped: gatherers with real gathering" is true of the CODE and false
of this MAP.** The spawn needs scree-or-meadow *and* `tsize >= 3` *and* `bfar > 12`
simultaneously, and meadow is 15 samples world-wide. The alchemist half of the economy is
written, gated by nothing, and unreachable in play. **That is the `F6` failure arriving early
and in the one place nobody was watching** — a system can be complete, tested, and never
execute.

### Why meadow is 0.3 ‰ — an exact defect in `ov_kind_at`, not a tuning choice

⚠ **Widening what counts as a picking ground was never an option**: `CLAUDE.md` forbids
nerfing content to fit a half-built system — *"build SYSTEMS to realize it"*. Meadow being
rarer than **swamp, river and glacier ice**, in a world whose premise is Ortler alpine terrain,
is a generator defect. It is, and the mechanism is exact.

Two rules were written independently, and **the earlier one silently voids the later one**:

```
overland.loft:1280   if h >= SNOWL || (steep > 20.0 && h >= SNOWL - 870.0 && slope < 0.46) {
                       … return (h, K_SNOW);              // "snow crouches far down"
overland.loft:1285   if steep > 20.0 {
                       // the alpine zone: meadows claim the gentle ground
overland.loft:1287     if h >= TREEL { … return (h, K_MEADOW); }
```

`TREEL = 2150`, `SNOWL = 3100`, so the snow branch reaches down to **2230 m** and runs
**first**. Meadow's comments describe treeline→snowline — **950 m** — and the code leaves it
`2150..2230`: **80 m, 8 % of the intended zone.**

Measured over 194 400 samples, bucketed by height:

| band | samples | meadow | what is there instead |
|---|---|---|---|
| **A** `2150–2230` — all meadow may occupy | 769 | **72** | scree 165, face 531 |
| **B** `2230–3100` — treeline→snowline | **7 723** | **0** | **snow 1 749**, scree 1 656, face 3 944, ice 369 |
| **C** `3100+` — above the snow line | 2 313 | 0 | snow 2 140 — correct here |

⚠ **Band B is ten times band A and holds no meadow at all.** The 3 944 `face` in it are
genuinely steep (`slope > 0.55`) and the scree is the `band < 0.10` arm — both correct. **The
stolen ground is the 1 749 `snow`**: gentle land *below the snow line*, between the treeline
and the snow line, which the alpine branch two lines later exists to make meadow. Freeing it
multiplies meadow by roughly **25×**, and puts scree-or-meadow within reach of a town window —
which is all the gatherer ever needed.

⚠ **FIXED 2026-08-09, and it was never an aesthetic call** (user: *"we have data from the real
alps and there is plenty of alpine meadows there"*). It is a **fit-to-data** question, and the
data has been in the repo since 2026-06-15 — `plans/1-ortler-worldgen-fixture/tuned-defaults.md`,
derived from real OSM classes + EU-DEM, ending in a **"Next: apply these"** that never
happened. The engine took two of the four derived bands (`TREEL`, `SNOWL`) and skipped the two
that carve the middle (`ALPINE_TOP = 2500`, `ROCK = 2800`).

⚠ **And the study's headline finding condemns the code that was there:** *"at 1.5 km, terrain
type is an ELEVATION function, not slope — per-class slope p50 is 17–22° for EVERY class."*
The alpine branch was separating meadow from scree **by slope**, which by that measurement
separates nothing. It is banded by height now, with faces still cutting through.

Result, one sweep of 48 600 samples, before → after:

| | before | after |
|---|---|---|
| meadow, world-wide | **0.3 ‰** | **5 ‰** (~17×) |
| band `2150–2500` | 0 % meadow | **33 % meadow, 65 % face** — essentially all *walkable* ground |
| band `2500–2800` | mixed snow/scree | **39 % scree**, 52 % face |
| band `3100+` | snow | **91 % snow** — unchanged, correct |

⚠ **`face` at 52–65 % of the alpine bands is untouched by this and still looks too high** —
that is `@PLN1`'s own open gap (*"bare walkable rock vs cliff — `K_FACE` is impassable-only"*),
not something this change introduced.

⚠ **This fixes the world and does NOT fix the gatherer** — the block is `ov_towns[0]`, not
terrain, and the town-by-town picking-ground count is **identical before and after**. Until
that moves, the home town's only lever is **the mine**, and `S3` must be honest that the
loop's visible surface is one site and two workers.

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

### ✅ `S5` is BUILT, ARMED and GATED — and it took five defects, each hidden by the last

Shipped 2026-08-10. `raid` on `Enemy`, `send_incursions` at each dawn, `raider_step` down the
same path field the civilians use, `raid_objective`, worldgen's **den over the ridge**, and
`incursiontest` (7 rows, in `NATIVE_TESTS` — 30 s interpreted, **2.1 s** compiled).

**I-SOURCE holds as designed:** a source sends when it is alive and has fewer than `RAID_CAP`
out, and that is the *entire* condition. No timer anywhere. The gate leans on that directly —
`sim_dawn` runs ten dawns back to back with no time between them and the cap still binds,
which is only a faithful stand-in *because* the rule does not read the calendar. One row still
ticks the world for its send, or nothing would prove the dawn is wired at all.

⚠ **Every one of the five defects looked exactly like a raid that was never sent.** That is
the repo's standing failure mode (STATE.md lesson 3) arriving five more times in one step.

| # | the defect | how it looked | the fix |
|---|---|---|---|
| 1 | `raider_step` refused an **occupied** neighbour — but a raider spawns inside its own den, where the one improving neighbour is a sleeping kinsman, and sleepers never move | held position 26 hexes out, forever | drop the occupancy test. `occupied_hex` is the **civilian** rule; `flow_step` (the chase) has none, so one actor had two contradictory occupancy rules across its two states |
| 2 | **no source anywhere could reach a settlement.** All three ruins sit in windows with 0 guards and 0 civilians; the home window (4 guards, 24 civilians, the gatherer, the economy) held no tagged monster at all | a green gate over a mechanism the shipped world could never fire | worldgen sites a **den** at the far end of the ground the town can walk |
| 3 | the objective was the **square** — which is where the guards are, and `hex_safe`'s second term is a guard within `GUARD_R` | 7 days with the den alive: picking ground unsafe **0 ticks**, deliveries **4** — identical to the den cleared | aim at the settlement's most exposed **work**, over ground the source can cross (the first version handed a den a field 45 hexes out with no path; the raider held for a week, 32 hexes short) |
| 4 | the den landed in a **cul-de-sac** — farthest-reachable is the deepest hex of a pocket, so it has the fewest ways out | one free neighbour, three sleepers took it, the source fielded **one** raider for seven days | require four walkable neighbours. ⚠ `RAID_CAP` was never the binding constraint; the geometry was |
| 5 | a raider **broke formation** for any hero it saw | both raiders parked beside a hero standing near the town; the mechanism had become "monsters walk at the player" | a raid fights what blocks it (`d <= 1`) and otherwise keeps marching. ⚠ Pressure that only lands while nobody watches is pressure nobody can act on — `F8` from the other side |

**Row 7 is the joint** `safetytest` and `stocktest` could not make between them: the gatherer's
ground is **safe at genesis**, **unsafe under the raid *with a raider on it***, and **safe
again** once the cause and its camp are gone. ⚠ The attribution term is load-bearing — 15
unrelated hostiles share that window, so *"is it unsafe now"* passes on a wandering jackal and
would have passed against all five broken versions above.

### ⚠ `S5` did NOT close the output coupling — and its diagnosis of WHY was wrong

`S5` measured the gap correctly and then named the wrong cause, on the strength of reading
the code rather than instrumenting it. What it recorded:

> Danger *raised* the stock. The cause is `npc_gather`'s first arm: **trapping a wild thing
> fills the bag anywhere**, so supply has a second path that nothing can make unsafe.

**Both halves of that are false, and one measurement settles it.** Attribute every bag-fill
to the place it happened — the instrument `S5` never built — and the trapping arm reports
**0 fills in both arms of the week**. It could not have been the second supply path, because
it was not a supply path at all: no wild thing ever came within a hex of the gatherer.

| measured over 7 days, world 777 | den alive | den cleared |
|---|---|---|
| picking ground unsafe | 2454 / 2800 ticks | 0 |
| fills **at the picking ground** | **31** | **17** |
| fills **anywhere else** (the trapping arm) | **0** | **0** |
| potions brewed | 14 | 12 |

### The real mechanism: being in danger exempts you from avoiding danger

⚠ **`npc_may_enter` has an escape hatch, it is unavoidable, and on its own it swallows the
whole rule.** A worker already standing in unsafe ground may enter any neighbour — otherwise
`npc_step` freezes it and a raid *traps* the people the rule exists to keep out (the plan's
own "enter, never leave" asymmetry, and it is right). But the consequence was never followed
through: **a large connected unsafe region is therefore freely traversable by anyone caught
inside it.**

Traced tick by tick, the gatherer at peace stalls constantly at safety borders — a wandering
hostile makes the one flow-improving neighbour unsafe and it waits, so a 13-hex leg takes ~75
ticks. Swallowed by the raid, its own hex is unsafe, every neighbour is therefore enterable,
and the same leg takes **17**. It ran its route at full speed *because* of the danger, and
picked with raiders standing on the ground.

**So `S5`'s number had nothing to do with supply paths. Danger was buying the gatherer a
faster commute.**

### ✅ Closed by two terms, and they answer different questions

| | |
|---|---|
| `npc_gather` | the bag fills **at the work site** and only while that ground is **safe**. Avoidance governs where a worker *goes*; this governs what the ground *gives*. Trapping folds into the same branch — the same load, not a second one — so supply has a **place** danger can press on |
| `npc_target` | **nobody travels to work that is unsafe.** `S2`'s second half — designed in this very file (*"the same term in site selection"*) and never built |

⚠ **The first alone is not enough, and the measurement says why.** With only the work term the
gatherer stopped commuting and simply **camped on its unsafe picking ground for 935 of 2800
ticks**, waiting out the gaps and pocketing **21** loads — still more than the 17 it managed
at peace. A rule about what ground yields cannot fix a worker who lives on it.

**Both terms, measured over the same week.** ⚠ **These are the DIAGNOSTIC numbers, on world
777** — the world every measurement above was taken in, kept because they are what the
diagnosis was read off. The plan's *current* figures are on the shipped seed and are in *the
whole plan now measures the world players start in*, below:

| | picking ground unsafe | deliveries | potions | stock by day |
|---|---|---|---|---|
| den **alive** | 2477 / 2800 | **1** | **1** | 1 0 0 0 0 0 0 |
| den **cleared** | 0 | **17** | **11** | 3 1 5 0 3 3 6 |

The store drains to empty and stays there; peace runs a working economy. `stocktest` row 7 is
now that A/B — see below.

### ⚠ The row that was passing on a starved town

`stocktest` row 7 ran **one arm** (the contested one) and asserted only *"a delivery
arrived"*. The moment the coupling closed it went on passing at **one delivery and one potion
in a week** — a starved town clearing a bar written for a healthy one. It is re-derived as an
A/B: the *same* world with one dead leader as the only difference, peace must look like a
working economy (≥5 deliveries in four days), pressure must not (a 2× margin), the picking
ground must be **measurably unsafe** in the contested arm (or a collapse is some other defect
wearing this row's clothes), and the store must not reach its cap under pressure.

⚠ **Verified able to go red**: with the veto disabled it prints *"12 deliveries under pressure
against 10 at peace"*. Four days per arm rather than seven — the arms separate by day 3, and a
surface tick is the most expensive thing in the gate. Cost: `stocktest` **15 s → 48 s**, now
the gate's tail (99 rows, 1m49s).

### ⚠ Open, and the user's call: the site veto gave two OLD numbers a consumer

`npc_target`'s veto is the first thing in the engine that ever *read* `hex_safe` about a work
site, and it immediately surfaced two facts that were true before it and inert. **Measured at
`HEAD` as well as after, with the den cleared, so neither is caused by this change or by the
raid:**

| work site | unsafe, per day | why |
|---|---|---|
| **the mine** `(7,49)` — 2 miners | **400 / 400 ticks** | an ogre camped on it, **40 hexes** from the nearest guard |
| **the market square** `(50,50)` — 6 villagers | **143 / 400** at `HEAD`, **215 / 400** after | a jackal wanders within `THREAT_R`; the guards' patrol legs sit at **radius 15** and only ever *transit* the centre, so `GUARD_R = 4` almost never covers it |

**The mine is the plan's own designed lever working** (*"the lever is the mine"*) and it reads
well in play: kill the ogre, the mine reopens. **The market was the one to decide**, because a
market shut half of every day, forever, from ambient wildlife is not a signal — and it landed
squarely on `S1`'s own guard rail, *"guards are a term in the safety expression, not
spectators, or the settlement is scenery waiting to be rescued."* They were close to
spectators: posted to a ring **outside** the town they defend.

#### ✅ Resolved (user, 2026-08-10): give a guard leg the town seat

The **guard master's beat is now the two hexes the town lives on** — the centre where the
villagers work and the market seat where the makers set out the day's goods. They are 2 hexes
apart, so **both stay inside `GUARD_R` from every point of the walk**: the square is held
*continuously* rather than whenever a patrol happens by, and he still moves, so the post reads
as a watch and not as a statue.

⚠ **The ring loses nothing, and that is arithmetic rather than a judgement call.** Legs are
`gd2 * 120°` and its opposite, and `gd2` runs `0..ngd` — so at `ngd = 4` guard 3 walks 360°,
which is guard 0's leg exactly. The senior guard was patrolling a **duplicate**, and the
duplicate is what this spends.

| measured over a day, den cleared | before | after |
|---|---|---|
| villagers' work site `(50,50)` | 215 / 400 unsafe | **0 / 400** |
| market seat `(52,48)` | 215 / 400 unsafe | **0 / 400** |
| civilian-ticks with a workable site | 4710 / 6800 | **6000 / 6800** |
| the mine | 400 / 400 unsafe | 400 / 400 — the lever, unchanged |

The 800 unworkable civilian-ticks that remain are exactly the two miners. And it puts the
guard master where the fiction already said he was: the watch's bounties are claimed from him
**in person**, and until now he was never at the seat to ask — `questtest`'s poster chain still
resolves, and now against someone you can find. ⚠ **`stocktest`'s A/B is untouched, as it had
to be**: the picking ground is 14 hexes out, far beyond `GUARD_R`, so 7 deliveries at peace
against 1 under pressure — a guard at the seat must not be able to quietly un-arm `I-SAFE`.

⚠ **The second-order effect this dissolved, kept on the record because the shape will recur**:
vetoed civilians idled at home, `occupied_hex` then blocked the guards more often near the
centre, coverage fell, and the square went **143 → 215**. *Crowding degraded the very term
that would have uncrowded it.* A guard posted at the seat stands inside that crowd instead of
trying to walk into it, so the loop no longer closes — but watch for it if the veto ever grows
a second consumer.

#### ✅ Also found while measuring, and fixed: the dead were holding ground

`occupied_hex` did not test `alive`, and a slain actor keeps its `cur_q`/`cur_r` forever —
nothing clears them, because the corpse is what the level's dead list is drawn from. **So
every kill left a permanent roadblock.**

⚠ **It is the worst shape a blocker can have.** A monster moves on; a wall is in the flow
field the movers descend. A corpse does neither — invisible to the field, causeless to the
player, unclearable by anything. `npc_step` only ever takes a strictly-improving neighbour, so
**one corpse in a one-hex gap freezes a worker for the rest of the game**, and the symptom is
*a civilian standing still* — the same symptom as five other defects this plan has already
chased. It is also a slow leak rather than an event: the map holds a little less ground after
every fight.

Inert for one of the two callers, which is worth stating: worldgen's placement dedup runs
while everything it has placed is alive, so only the **runtime** callers change (civilian
stepping and the incursion's spawn pick). Gated as `safetytest` row 7, and it needs **both
directions on the same hex** or it gates nothing — a living actor must still block (or the fix
has merely turned occupancy off and everyone walks through everyone) and a corpse must not.
Verified red with the `alive` test removed.

### ⚠ Open, and the user's call: the starting town is now under pressure from day 1

The den is real, its raiders camp on the only picking ground, and the answer is to go and
clear it — a **goblin leader, mlvl 5, 17 hexes from town**. That is a strong, legible opening
(*the alchemist has nothing; goblins are on the slope*) and it is the first danger in the game
with a **cause the player can end**. It also lands on top of a curve STATE.md already records
as unowned — a gnoll (mlvl 6) 8 hexes from the vantage, a level-1 hero dead on tick 13
— and is **DESIGN §3a pillar #8's business**. Shipped as designed, flagged here rather than
decided: the levers are the den's distance, its `mon_pick_tag` tier, and `RAID_CAP`.

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
2. ✅ **RESOLVED 2026-08-10 by building it — BOTH, and they were never alternatives.** The
   stock belongs to the *settlement* (it lives on the `Sim`, not on a worker or an item), and
   within it there is one number *per producer* — `CRAFTING.md` §B says exactly this once read
   closely ("a per-settlement stock … ⚠ stock is a NUMBER PER PRODUCER"), so the question was
   phrased as a fork that the design had already closed. Per producer is what lets a forge
   starve while the bakery runs, which is the readable behaviour; per settlement is the scope
   that owns it. ⚠ **A third reading is the one to refuse**: stock is *not* per material — the
   moment it is, it is an inventory, and `F2` is spent.
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
