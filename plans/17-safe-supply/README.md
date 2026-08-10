# `17` — A settlement's output is a function of the danger around it

**Issue:** [`jjstwerff/crawler#17`](https://github.com/jjstwerff/crawler/issues/17) ·
**Value:** `G` · **Effort:** `M`

## Status

**`status:active` from 2026-08-09** (user), taking `#12`'s slot — the roster is
`#11`/`#13`/`#17`, still at the cap of three. `S0` is shipped: the design (`CRAFTING.md`)
and the measurement of what already exists, which turned out to be most of it. `S1`–`S3` are
**shipped and armed**; `S4`–`S7` are designed, and each is written out below.

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
| **`S4`** — the world shows it, with no panel | M | `make play`, a user read | **Unblocked** — the short batch already thins the stall |
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
