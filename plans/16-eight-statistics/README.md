# `16` — The eight the powers are authored against are the eight the engine answers

**Issue:** [`jjstwerff/crawler#16`](https://github.com/jjstwerff/crawler/issues/16) ·
**Value:** `F` · **Effort:** `MH`

## Status

**`status:active` from 2026-08-10** (user: *"start #16"*), taking the slot [#17](../17-safe-supply/)
freed by finishing — the roster is `#11`/`#13`/`#16`, still capped at three.

**ALL FIVE STEPS ARE SHIPPED** (`M0`–`M4`, the last two on 2026-08-11): the measurements, the
scope ruling, the engine answering the eight, **the 18 bundles re-authored as a set**, and
**six of the eight axes keyed to a derived number**. Full gate green, **104 rows**
(`derivetest` is new). The old six-stat vocabulary is **gone from the tree**: no `r_str`, no
`c_int`, no legacy alias arm, no `RF_SUST_STR`.

**→ The one thing still owed is a judgement, not a step: the `make play` read.** The plan's own
verify line for `M4` is *"`make test`, `make play`"*, and whether the spread feels right in
motion — Speed especially — is the user's call. The numbers are tabled under `M4` for it.

⚠ **Two axes deliberately drive NOTHING**: Charisma waits on a party or a priced transaction,
Handiness on the durability call. Neither is a derivation, so `M4` refused to invent one —
see *the finding* under `M4`.

⚠ **The plan closed three defects it was not looking for**, and all three are the same shape —
*a check nobody runs is not a check*: `M3` found the sidebar baking six stat labels against
eight values; `M4` found a temporary stat potion permanently inflating max SP, and `make probe`
red at HEAD. Each is written up where it was found.

## Goal

`sim`/`gameflow` answer the eight — Might, Endurance, Dexterity, Perception, Speed, Will,
Charisma, Handiness — and `CATALOG.md` §12a, the 37 powers and `RESOLUTION.md` §5a describe
a system that exists.

## Why

§0 adopted the eight on **2026-06-27** and the engine has answered Angband's six ever
since. That gap is not neutral: three documents specify a game against eight axes while
the code offers six, so a reader implementing from them builds against something that is
not there. The decision was always crawler's alone (`MOROS.md` — moros has nothing to
write for this; the stat set was *seeded* here in June).

## What `M0` turned up — measured 2026-08-09

| | finding |
|---|---|
| **the engine today** | `str/int/wis/dex/con/chr` — `gameflow::stat_name`, `sim::stat_index`. Six weeks after the decision, the eight appear in **no code path** |
| ✅ **not a save break** | persistence is *"deterministic base + a stored death delta"* (dead-spawn indices). **No stat vector is in any save path** — so growing the axis count breaks no stored world |
| ✅ **engine storage is cheap** | `stat_max` / `stat_cur` / `stat_tmp` / `stat_tmp_t` / `stat_grown_at` are all `vector<integer>`: the axis count is a **length**, not a struct shape |
| ⚠ **the content is not** | `RaceDef` and `ClassDef` carry **named** fields (`r_str…r_chr`, `c_str…c_chr`), and **18 bundles** hold blocks written against them |
| | 7 engine files · 16 `stat_index`/`stat_name` sites |

⚠ **AND IT IS NOT A RENAME, WHICH IS THE FINDING THAT SETS THE EFFORT.** The six do not map
onto the eight: **Perception and Speed are new axes** with no predecessor, and Handiness is
not `int`. So every one of the 18 bundles needs its values **re-authored** — a content
judgement per race and per class — not rewritten by a script. A migration that mapped
`str→Might, con→Endurance, …` and defaulted the rest to 0 would compile, pass the gate, and
quietly flatten every race's identity.

**Found while measuring:** the risk everyone would have assumed — a save-format break —
does not exist, and the risk nobody would have named — that this is content work wearing a
refactor's clothes — is the whole cost. That asymmetry is why `M0` came first.

## Steps

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`M0`** — measure the axis change: storage, saves, blast radius | XS | this file | **Shipped** |
| **`M1`** — settle the SCOPE: the eight only, or the economy too | XS | decided below | ✅ **Shipped — the axes only** |
| **`M2`** — the engine answers eight | S | `make test` green (103 rows) | ✅ **Shipped 2026-08-10** — `I-AXIS`; and it cost **zero new keys** |
| **`M3`** — re-author 18 bundles' stat blocks | **M/H** | `make test` + a user read of the roster | ✅ **Shipped 2026-08-11** — the roster is below, for that read |
| **`M4`** — re-key the derived stats and the character page | M | `make test`, `make play` | ✅ **Shipped 2026-08-11** — six axes keyed, `derivetest` (row 104); the `make play` read is the user's |

### `M1` — the scope, ✅ settled 2026-08-09

**This plan is the AXES ONLY** (user: *"the axes only"*). `M3` re-authors stat blocks and
nothing else.

⚠ **The economy is adopted too, and it is NOT this plan.** *"…and the economy, we will
expand it though with far more crafting"* — `CATALOG.md` §6.3's replacement of Angband's
SP / fail-rate / spell-levels with card-plus-action-plus-Tension, gated by stat and
mastery, plus a crafting expansion beyond it. That is a system this repo does not have, on
a different axis from a stat count, and it is tracked as `CATALOG.md` `OW2` until it is
designed enough to earn a directory.

**Why the split is real and not bookkeeping:** `M3`'s cost is re-authoring 18 stat blocks
as a *set*; the economy's cost is designing a system from nothing. Merging them would put
a content pass and a green-field design behind one status line, and the first would be
held hostage by the second.

### `M2` — the engine answers eight, designed

`stat_index`/`stat_name` grow to eight; the five `vector<integer>` layers follow by length.
⚠ **Behaviour-preserving is NOT the gate here** — adding axes changes derived values by
construction, so `M2`'s gate is *green*, not *identical*, and `M4` is where the numbers are
judged.

#### ⚠ The seam with `M3`, re-measured 2026-08-10 — and it moves one line of this step

**`RaceDef`/`ClassDef` do NOT change in `M2`**, against what this step said before measuring.
The 18 bundles are not data files, they are **`.loft` struct literals with named fields**
(`RaceDef { r_str: 4, r_int: -4, … }`), and loft *defaults an omitted field to zero*. So the
two shapes of this change are:

| | what happens |
|---|---|
| **replace** the six fields with eight | all 18 bundles fail to COMPILE — loud, but the tree is red until `M3` finishes, and `M3` is the `M/H` step |
| **add** eight beside the six | every bundle compiles, every race scores **0** on every new axis, the gate stays green — **the exact failure `M0` named**: *compile, pass, and quietly flatten every race's identity* |

Neither is acceptable, and the resolution is that this was never `M2`'s business. **The field
rename and the re-authoring are the same edit** — per bundle, the names and the values change
together — so both belong to `M3`, and `M2` stops at the engine's own vocabulary. That keeps
each step's own rule: `M2` leaves the tree green, `M3` is compile-enforced and cannot be
silently half-done.

#### `I-AXIS`, and the three calls `M2` makes

**I-AXIS: the engine's stat vocabulary is the eight of `CATALOG.md` §0, in that order, and
every layer follows by LENGTH — `NUM_STATS` is the only thing that knows the count.**

1. **Order and keys** — `might · endu · dex · perc · speed · will · char · hand`, indices 0–7,
   exactly §0's table order.
2. **The three indices the engine actually consumes re-point by §0's own role table**, not by
   a fresh judgement: `ST_STR → ST_MIGHT` (damage), `ST_CON → ST_ENDU` (mitigation/HP),
   `ST_DEX` (crit/precision) from 3 to 2.
3. **A PLACEHOLDER mapping carries the six authored fields onto their axes**, and it is named
   as one in the code so `M3` deletes it rather than inherits it. ⚠ **`r_int` has no axis**:
   under the eight there is one casting axis, Will, so *which races cast well* is a judgement
   about the set — `M3`'s, by construction. `M2` publishes what dropping it costs rather than
   hiding it behind a fudge.

⚠ **The legacy keys stay resolvable for exactly one step.** `c_spell_stat` says `"int"`/`"wis"`
in six class bundles and item effects restore stats by key; without an alias arm the tree goes
red for a reason that has nothing to do with axes. The arm is marked as `M3`'s to delete.

#### ✅ `M2` is BUILT and GATED — and the two axes cost no keys at all

`NUM_STATS = 8`, `stat_index`/`stat_name` answer the eight in §0's order, `ST_STR/ST_CON`
became `ST_MIGHT/ST_ENDU` and `ST_DEX` moved 3→2. Full gate green, **103 rows**.

| what was expected to cost something | what it actually cost |
|---|---|
| **new keys for two more spendable stats** | **nothing.** The front-end already read keys 1–9 and merely gated `sd < 6`; it reads `sd < NUM_STATS` now. The budget was always spent on the ROW, not on the axis — so the character page went from six spendable stats to eight without touching `DESIGN.md` §3a's 15 |
| **the casting chain** | **nothing — `classtest` is green in every row**, SP pool, cast, spend and regen included |
| **the save format** | nothing, as `M0` measured: the axis count is a vector LENGTH |

⚠ **THE ONE THING THAT DID COST A DECISION: a class declares which axis it casts on, so its
casting mod follows the declaration and not the field name.** `c_spell_stat` already says
`"int"` or `"wis"`; under the eight there is one casting axis, so *whichever of the two a class
named* **is** its Will. Without that, every arcane caster would lose its casting-stat bonus for
a whole step — a real regression with no design behind it, and one nobody would have noticed
because it lands on SP rather than on anything visible. A RACE makes no such declaration, so
its Will is `r_wis` and `r_int` goes nowhere; **which races cast well is a judgement about the
roster, which is `M3`'s by construction.**

**And the gate had to say the new thing rather than the old one.** `racetest` row 1 asserted
`int == 13` — the row is now `might 18 / char 13 / will 18`, and the comment says why the
change is not a rename: there is no Intelligence axis, and arcane and divine both key off Will.
A test left asserting the old vocabulary would have been the only thing in the tree still
claiming six.

### `M3` — the 18 bundles, designed

✅ **UNBLOCKED 2026-08-09 — `Handiness` has a meaning to author against.** It *"gates
repairs and improvised gear, not crafting"*, and it is a **degree, never a key**: learned
skills permit, the stat qualifies (`CRAFTING.md` → *Handiness is a DEGREE, never a KEY*).
So a race's value states **how good this people are at fixing and making do** — a statable
thing, not a bet on an undesigned system, which is why [#17](../17-safe-supply/) was
designed first.

⚠ **One sub-decision is still open and it only affects half the axis**: improvisation is
free (it is already the `Ingenuity` card), **repairs need a durability mechanic that does
not exist**. `M3` can author the meaning regardless; if durability is declined, Handiness
keeps the improvisation half and the values still stand.

The expensive step and the one that must not be automated. Each race and class states what
it is on the new axes: a half-troll's Might is not its old `r_str`, and its Speed and
Perception have never been written down. ⚠ **Author, then read the roster as a set** — the
races only mean anything relative to each other.

#### ✅ `M3` is BUILT and GATED — 2026-08-11, full gate green (103 rows)

**What changed, mechanically:** `RaceDef`/`ClassDef` replaced the six named fields with eight
(`r_might…r_hand`, `c_might…c_hand`, in `stat_name`'s order); all 18 bundles were re-authored;
every caster declares `c_spell_stat: "will"`; `RF_SUST_STR/CON` became `RF_SUST_MIGHT/ENDU`;
and both one-step shims from `M2` — the `stat_index` legacy arm and the `apply_creation`
placeholder — are **deleted**. `stat_index("str")` now returns `-1`, like any other typo,
which is the point: an unknown stat key must be an error, not a quiet redirect.

**Two construction calls worth keeping:**

1. **NAMED fields, not a `vector<integer>` indexed by axis.** A vector would make `NUM_STATS`
   the only thing that knows the count on the content side too — tidier, and wrong: a ninth
   axis would zero-pad 18 bundles *silently*, which is `M0`'s named failure. Named fields make
   it a compile error in all 18. **The field name IS the stat key** (`r_will` ↔ `"will"`), so
   the row and `sim_stat` cannot drift apart.
2. **`c_spell_stat` stays a declaration** even though every caster in the tree now says the
   same word. Collapsing it to `c_realm != "none"` would save a field and cost a bundle the
   ability to author a class that casts off another axis — a seer off Perception — without
   touching the engine. Mechanism engine-side, content bundle-side (`BUNDLE.md`).

#### The roster, for the read — races

Σ is the eight-axis total; `xp%` is unchanged by this step and is what the sheet costs.

| race | Mig | End | Dex | Per | Spd | Wil | Cha | Han | Σ | xp% |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **High-Elf** | 1 | -1 | 3 | **4** | 1 | 3 | 1 | -1 | 11 | 145 |
| **Halfling** | -2 | 1 | **4** | 2 | **3** | -1 | 1 | 1 | 9 | 110 |
| **Highborn** | 2 | 2 | 1 | 0 | -1 | 2 | **4** | -1 | 9 | 145 |
| **Gnome** | -1 | 0 | 2 | 2 | 1 | 1 | -2 | **4** | 7 | 115 |
| **Elf** | -1 | -2 | 2 | 3 | 1 | 2 | 1 | 0 | 6 | 120 |
| **Dwarf** | 2 | **3** | -2 | 1 | -1 | 2 | -3 | 3 | 5 | 120 |
| **Half-Elf** | -1 | -1 | 1 | 1 | 0 | 1 | 2 | 0 | 3 | 110 |
| **Half-Orc** | 3 | 2 | 0 | -1 | 0 | -1 | -4 | 1 | 0 | 110 |
| **Human** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 100 |
| **Half-Troll** | **5** | **4** | -4 | -3 | -2 | -2 | -6 | -3 | -11 | 137 |

#### The roster, for the read — classes

| class | Mig | End | Dex | Per | Spd | Wil | Cha | Han | Σ | xp% |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Ranger** | -1 | 1 | 2 | **4** | **2** | 2 | -1 | 0 | 9 | 130 |
| **Rogue** | 1 | -1 | **3** | 2 | 1 | 1 | -1 | **2** | 8 | 125 |
| **Paladin** | 3 | 2 | -1 | -1 | -1 | 2 | **3** | 0 | 7 | 135 |
| **Warrior** | **3** | **2** | 2 | -1 | 1 | -2 | 0 | 1 | 6 | 100 |
| **Druid** | -1 | 1 | 0 | 3 | 0 | 3 | 0 | -1 | 5 | 125 |
| **Priest** | -1 | 0 | -1 | 1 | -1 | 3 | **3** | 0 | 4 | 120 |
| **Mage** | -4 | -2 | 1 | 1 | -1 | **4** | -1 | 0 | -2 | 130 |
| **Necromancer** | -4 | -2 | 1 | 2 | -2 | 3 | -3 | 1 | -4 | 135 |

#### The two rules the authoring held to, and why they are the anti-flattening

`M0` warned that a mapping migration would *"compile, pass the gate, and quietly flatten every
race's identity."* A gate cannot catch that — the numbers would all be legal. So the discipline
was stated up front and is checkable by eye against the tables above:

1. **Every axis spans a real range.** Races: Might -2..5, Endu -2..4, Dex -4..4, **Perc -3..4**,
   **Speed -2..3**, Will -2..3, Char -6..4, **Hand -3..4**. The three axes with no predecessor
   (Perception, Speed, Handiness) have spreads as wide as the inherited ones — a dead axis
   would show as a column of zeros, and there is none.
2. **Everything but Human is bad at something** (≥ 2 negative axes; Human is the zero baseline
   by construction). This is what makes an axis *earn its place*: Highborn's `Hand -1` — a
   noble has never repaired anything — says something the six could not say at all.

#### ⚠ The finding: the axis change RE-RANKS the roster, and it re-ranks it toward the flat

Rank order survives almost intact, with two deliberate movers, and both have the **same cause**:

| | old Σ (six) | new Σ (eight) | why |
|---|--:|--:|---|
| **Dwarf** | -2 | **+5** | paid -3 Int and -3 Chr, two taxes on axes a miner has no use for. **Handiness** is the axis that repays it |
| **Gnome** | +2 | **+7** | same shape: already authored with the tree's best disarm (10) and second device (8) — the axis finally names what the skills said |
| **Rogue** | +4 | +8 (passes Paladin) | **both new axes land on it** — Perception to read the room, Speed to leave it |

The races and classes the six left *flat* are exactly the ones the eight repay, because
Angband's six taxed them on axes their playstyle never used. That is what "it is not a rename"
means in practice — and it is the argument for the whole plan, arriving as a measurement rather
than as a claim.

#### ⚠ What `M3` found: I-AXIS was asserted at the draw site and not at the bake site

Sweeping for prose that still named the six turned up a **live rendering defect**, shipped by
`M2` and invisible to 103 gate rows: `build_hud` baked stat labels with

```loft
snames = ["STR", "INT", "WIS", "DEX", "CON", "CHR"];
for si in 0..6 { statlbl[si] = create_text_texture(...); }
```

while `draw_sidebar` — 400 lines away, and correct — drew **eight** rows. So the running game
showed six labels naming axes the engine no longer had, against eight values, with two blank
rows under them (`sb_text` returns early on `tex == 0`, so the missing labels were silent).

**The mechanism, not the typo:** `M2`'s own comment at the draw site says *"Driven by the
ARRAY's length, not a literal count, so the sidebar follows the axis set (I-AXIS)"* — and it
was true **there**. A length-driven invariant rots at the site that BUILDS the array, because
that site can satisfy a different length and nothing compares them. The fix is a chokepoint:
`stat_abbrevs()` now owns the names and both sites read it, so a ninth axis changes one line.

⚠ **The gate could not have caught this** and still cannot — there is no probe on the sidebar.
`make probe` exists for exactly this class (`probes/*.probe`), and the honest statement is that
this defect argues for a sidebar probe in `M4`, when the page is judged in `make play` anyway.

#### The open sub-decision, and what shipped under it

`CRAFTING.md` question 4 left one half of Handiness open: improvisation is free (the `Ingenuity`
card), **repairs need a durability mechanic that does not exist**. That did not block the
authoring, exactly as designed — a race's Handiness states *how good this people are at fixing
and making do*, and the improvisation half is already real. If durability is declined, every
value above still stands and only reads narrower. ⚠ **No value in the roster is a bet on
durability** — the dwarf's +3 and the gnome's +4 are backed by `r_device`/`r_disarm` that
already exist.

### `M4` — derived stats and the page, designed

`RESOLUTION.md` §2a re-keys: Might→damage, Endurance→mitigation/HP, Dex→crit,
Perception→the perception action, Speed→the distance clock, Will→Tension-resist. The
character page (§12a) lists eight. This is where the tuning is judged, in `make play`.

#### ✅ `M4` is BUILT and GATED — 2026-08-11, full gate green (**104 rows**, `derivetest` is new)

**Six of the eight axes now drive something. Two do not, and saying which is the finding.**

| axis | before `M4` | after |
|---|---|---|
| **Might** | melee skill → `wdam` | unchanged — it already held §0's role |
| **Endurance** | the saving throw | **the max-HP pool** (§0's *soak*) |
| **Dexterity** | stealth **and** shooting | stealth only |
| **Perception** | — | **the shooting skill** (§0's *ranged accuracy*) |
| **Speed** | — | **the distance clock**, via `tick_span()` |
| **Will** | the SP pool | the SP pool **and the saving throw** |
| **Charisma** | — | **still nothing** — see below |
| **Handiness** | — | **still nothing** — see below |

⚠ **Two of these are swaps, not additions**, and that is what needed gating: the saving throw
moved Endurance→Will and the shooting skill moved Dexterity→Perception. A gate asserting only
*"Will raises the save"* would still pass if Endurance raised it too, so `derivetest`'s matrix
asserts **both directions** — the new axis moves the number and **the old one no longer does**.

⚠ **Dexterity came out of `M4` with FEWER consumers than it went in with**, and that is
correct rather than a regression to fix. §0 gives it *crit / precision / evasion*; crawler has
**no crit channel** — `RESOLUTION.md` §2a's two-tailed crit engine is designed and unbuilt — so
Dex keeps stealth and hands ranged accuracy to the axis §0 assigns it to. Padding Dex with a
replacement consumer to keep it "worth as much" would be tuning by bookkeeping. It gets its
second half when the crit engine lands, not before.

#### ⚠ The finding: two axes have no consumer, and `M4` refused to invent one

`M4` could re-key everything §0 names except the last two, and the honest reason is that they
are not derivations at all:

- **Charisma** — §0 gives it *leadership / calling* (`PARTY.md` §5b) and *prices*. crawler has
  **no party** and **no priced transaction**: gold is found, auto-collected and staked on death,
  and it is never spent *at a price*. Both are systems.
- **Handiness** — §0 gives it *disarm / device / repair*. ⚠ **`r_device` and `r_disarm` are
  authored on all 10 races and consumed NOWHERE in the tree** — measured, not assumed — and
  #17's mending is the **smith's** act, not the player's. It waits on `CRAFTING.md` q4's
  durability call.

**Building either would be a new system, not a re-key** — and under §3a pillar 0 a new system
must earn its place against the 15-key budget rather than be smuggled in as tuning. So the
character page says *(later)* on exactly those two rows and names the real consumer on the other
six. ⚠ **A page that said "leadership" beside a number nothing reads would be the lie** — this
is the same standard `M2` set when it refused to fudge `r_int`.

#### `I-POOL`, and the defect that was already there

**I-POOL: a STORED pool derives only from the PERMANENT stat layers; the temporary layer is a
live-read overlay that never enters stored state.**

`refresh_stats` writes `phpmax`/`spmax` *into* the Sim, so whatever it reads is frozen there
until something else re-derives — and `sim_buff_stat` pointedly does **not** re-derive, which is
what made the temporary layer live-only. But `refresh_stats` read `stat_eff` for the SP pool,
which **includes** the overlay. Measured with a 15-line probe:

```
spmax: base=7  after-buff=7  after-unrelated-refresh=11  after-expiry=11
```

A temporary Will potion, then **any** unrelated re-derive — equip a helmet, gain a level — and
the potion's points are baked into `spmax` **permanently**. Not reachable by drinking alone,
which is exactly why it sat there unnoticed.

⚠ **The probe is the reason this is in the plan at all.** The first hypothesis was *"expiry
never re-derives, so add a refresh hook"* — and the probe **refuted it** in about a minute:
`sim_buff_stat` doesn't store anything, so there was nothing stale to refresh. The real defect
needed the *second* event, and the real fix is the opposite of the first idea — `stat_perm` at
the one site that stores, so the overlay never reaches stored state. Had `M4` acted on the
fluent explanation it would have added an expiry hook that fixed nothing and hidden the
mechanism. **Keying Endurance into max HP would have added a second instance of this defect**,
which is how it came to be measured at all.

#### Speed and the clock — one owner, and a clamp that is load-bearing

The clock is distance-driven: a span of travel is one `sim_tick`, and the span **was** the
literal `HEX_LEN`. It is now `tick_span(s)` = `HEX_LEN × (1 ± 5 %/point)`, clamped to
`[0.5×, 2×]`.

⚠ **The span is read at FIVE sites** — two `while` loops, `sim_frac`, and the enemy
interpolation — so it went behind one owner immediately. This is `M3`'s sidebar lesson applied
before it could bite: a length-driven quantity rots at whichever site forgets to ask, and the
enemy-interpolation site would have desynced every drawn monster from the tick it was walking
to, **silently**.

⚠ **The clamp is not cosmetic.** The consumers are `while accrued >= span`; a span at or below
zero never terminates. A stat drains to a floor of 1 — fifteen points under the baseline, i.e.
0.25× unclamped — so the floor is what stands between a poison potion and a hung frame.
`derivetest` asserts it as an **equality that can only hold because of the clamp**: −10 sits
exactly on the boundary and −20 is driven well past it, and the two must produce the *same*
walk (41 ticks each; unclamped, −20 would roughly double it).

#### What the numbers came out at — the material for the `make play` read

Level 1, no equipment. Races are unclassed; classes are shown on a human.

| race | HP | save | shoot | Speed | | class | HP | save | shoot | Speed |
|---|--:|--:|--:|--:|---|---|--:|--:|--:|--:|
| Human | 30 | 11 | 0 | 16 | | Warrior | 44 | 13 | 3 | 17 |
| Half-Elf | 29 | 14 | 3 | 16 | | Mage | 29 | 17 | 1 | 15 |
| Elf | 26 | 18 | 8 | 17 | | Priest | 33 | 17 | 2 | 15 |
| High-Elf | 30 | 20 | 10 | 17 | | Rogue | 39 | 15 | 5 | 17 |
| Dwarf | 35 | 18 | 1 | 15 | | Ranger | 36 | 16 | 9 | 18 |
| Gnome | 29 | 14 | 4 | 17 | | Paladin | 40 | 17 | 1 | 15 |
| Halfling | 27 | 16 | 6 | 19 | | Druid | 33 | 17 | 5 | 16 |
| Half-Orc | 32 | 14 | 0 | 16 | | Necromancer | 29 | 16 | 2 | 14 |
| Half-Troll | 39 | 14 | 0 | 14 | | | | | | |
| Highborn | 32 | 17 | 2 | 15 | | | | | | |

The shapes read the way `M3` authored them — the ranger and the high-elf top the bow, the
half-troll and the warrior top HP, the halfling is the fastest thing on the roster and the
half-troll the slowest. **The judgement that is still the user's is whether the SPREAD feels
right in motion** — Speed especially, since a halfling walking at 1.15× against a half-troll's
0.90× is a 28 % difference in how often the world gets a turn, and no gate can say whether that
reads as *nimble* or as *twitchy*.

#### ⚠ And `make probe` was rotted THREE LAYERS DEEP, each one hiding the next

Verifying the render side turned up `make probe` failing. Peeling it took three passes, and the
order matters — **each rot masked the one behind it**, which is how a gate ends up this far gone
without a single complaint:

| # | what was wrong | how it hid |
|---|---|---|
| **1** | three undischarged `float?` divides in `src/gpushot.loft` (`SCALE / hw`, `CX / hw`, `(gq+0.5) / lwf`) — a tightened loft rule turned them into compile errors | aborted the target at step one, so nothing after it ever ran |
| **2** | the target rendered **`src/*probe.loft`**, a glob that swallows `src/reloadprobe.loft` — plan #6 `K3`'s **windowed** live-reload tool, which waits for Esc and under Xvfb **never exits** | it HUNG rather than failed, and **a hang reads as progress** |
| **3** | `probes/world_r4` (1/4) and `world_r5` (0/3) fail against goldens **measured 2026-06-12** | unreachable behind 1 and 2 |

**Fixed here (1 and 2):** the three `?? 0.0`s, and the scene list is now **named, not globbed**
(`PROBE_SCENES`) with a `timeout` so a hang fails loudly. A scene belongs in the gate only if it
is headless and produces a PNG some `.probe` asserts — `reloadprobe` is neither.

⚠ **NOT fixed, and deliberately not (3).** The two world specs fail **identically with pre-`M4`
code** — verified by checking `src/sim.loft`/`src/view.loft` out at the `M3` commit and
re-rendering, not by argument. `worldprobe.loft` reads no statistic and runs no tick, so `M4`
could not have moved it; the world it renders has changed since the goldens were pinned (the
tree's measurement seed moved 777 → 1337, and #17 cut gates into the town wall). **Re-pinning
them to whatever renders today would destroy the evidence** — that is adopting a frame nobody
has judged, and `SCALE.md`'s whole point is that a wrong world should be *provable* wrong. It is
plan #7's call. `gpu_r3` (3/3) and `post_r6` (5/5) pass.

⚠ **A method note, because it nearly went wrong.** The first attempt to establish "pre-existing"
used `git stash push -- <paths>` on files that were *already committed* — so it stashed nothing,
and `git stash pop` then popped **an unrelated pre-existing stash** (`WIP on main: e8c2cb4`),
conflicting `loft.lock`. Restored, and that stash is untouched and still listed. The lesson is
the one this repo already writes down: **another agent's work is routinely sitting in the tree**,
so reach for `git checkout <commit> -- <paths>` to compare against history, never `stash`.

**The mechanism behind all three is the same one this plan keeps finding: a check nobody runs is
not a check.** `make probe` is outside `make test` (it needs Xvfb and takes ~10 min), so it rots
for as long as nobody types it — exactly like the five unwired tests CLAUDE.md records, and
exactly like the sidebar labels `M3` found. ⚠ **Nothing yet stops it rotting again** — open
question 3.

## What this plan does NOT change

- **The clean-room rule.** Race and power *names* are shared-world IP and already in use
  (`CATALOG.md`'s closing section); this changes axes, not naming policy.
- **Saves.** Measured: no stat vector persists. Nothing to migrate.
- **The advancement economy** — unless `M1` says otherwise. Separate decision, separate cost.
- **moros.** Nothing is requested of that project (`MOROS.md`); this executes a decision
  crawler made in June.
- **The active roster.** `status:future` by the user's own scheduling, so `#11`/`#12`/`#13`
  keep their slots.

## Open questions

1. ~~`M1`'s scope — axes only, or the economy too?~~ ✅ **Settled 2026-08-09 — the axes only.**
2. Do the eight axes want a **stat bundle** rather than engine constants? Every other
   content enumeration moved bundle-side (`BUNDLE.md`); a hard-coded eight would be the
   same shape of decision `plan #13` is trying to remove from ground identity.
   ⚠ **`M3` sharpened this rather than answering it.** The axis *count* is already a length
   everywhere it matters (I-AXIS), so a bundle would not be buying that. What is still
   hard-coded is the **vocabulary** — `stat_index`, `stat_name` and `stat_abbrevs` each spell
   the eight keys — and `M3` added a fourth site rather than removing one. Three sites is the
   number to weigh a stat bundle against, and the honest note is that the same eight keys now
   also appear as 16 STRUCT FIELD NAMES, which no bundle can make dynamic. Decide in `M4` or
   defer it to #13, whose problem this is a smaller copy of.
3. **What keeps `make probe` honest?** ⚠ **Sharpened by `M4` into something worse than the
   original question.** `M3` shipped a wrong-label defect no gate row could see, and the
   suggestion was a sidebar probe — then `M4` found **`make probe` itself red at HEAD**, on
   three undischarged `float?` divides, for however long it had been since anyone typed it.
   Fixing the rot is done; nothing stops it recurring, because the render gate is outside
   `make test` (it needs Xvfb). So the real question is **scheduling, not coverage**: does
   `make probe` join `make test`, gain a CI row, or get accepted as by-hand? Adding a sidebar
   probe to a gate nobody runs would buy nothing. **A call for whoever owns the render gate
   (plan #7).**
4. **Charisma and Handiness drive nothing, and `M4` is the last step that could have keyed
   them.** Both need a SYSTEM (a party / a priced transaction; the durability layer), and both
   are tracked elsewhere — `CATALOG.md` `OW2` and `CRAFTING.md` q4. ⚠ The risk to name is that
   *"authored but unread"* is a stable-looking state that can last as long as the six-vs-eight
   gap did (six weeks, and nothing said so). The character page saying *(later)* out loud is
   the only thing in the tree that will keep saying it.

## See also

- `CATALOG.md` §0 (the decision) and `OW1` (the fork this closes) · §12a, §6.3
- `RESOLUTION.md` §5a — the progression the eight were adopted for
- `MOROS.md` — why this is crawler's call and needs nothing from moros
