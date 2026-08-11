# `16` — The eight the powers are authored against are the eight the engine answers

**Issue:** [`jjstwerff/crawler#16`](https://github.com/jjstwerff/crawler/issues/16) ·
**Value:** `F` · **Effort:** `MH`

## Status

**`status:active` from 2026-08-10** (user: *"start #16"*), taking the slot [#17](../17-safe-supply/)
freed by finishing — the roster is `#11`/`#13`/`#16`, still capped at three.

`M0`/`M1`/**`M2`** are **shipped**: the measurements, the scope ruling, and the engine now
answering the eight (full gate green, 103 rows, **zero new keys**). **→ NEXT is `M3`** — the
expensive one, and the one that must not be automated: 18 bundles re-authored as a set.
`M4` follows it.

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
| **`M3`** — re-author 18 bundles' stat blocks | **M/H** | `make test` + a user read of the roster | **→ NEXT** (unblocked) |
| **`M4`** — re-key the derived stats and the character page | M | `make test`, `make play` | Blocked on `M3` |

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

### `M4` — derived stats and the page, designed

`RESOLUTION.md` §2a re-keys: Might→damage, Endurance→mitigation/HP, Dex→crit,
Perception→the perception action, Speed→the distance clock, Will→Tension-resist. The
character page (§12a) lists eight. This is where the tuning is judged, in `make play`.

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

1. `M1`'s scope — axes only, or the economy too?
2. Do the eight axes want a **stat bundle** rather than engine constants? Every other
   content enumeration moved bundle-side (`BUNDLE.md`); a hard-coded eight would be the
   same shape of decision `plan #13` is trying to remove from ground identity.

## See also

- `CATALOG.md` §0 (the decision) and `OW1` (the fork this closes) · §12a, §6.3
- `RESOLUTION.md` §5a — the progression the eight were adopted for
- `MOROS.md` — why this is crawler's call and needs nothing from moros
