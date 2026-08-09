# `16` — The eight the powers are authored against are the eight the engine answers

**Issue:** [`jjstwerff/crawler#16`](https://github.com/jjstwerff/crawler/issues/16) ·
**Value:** `F` · **Effort:** `MH`

## Status

**Decided, not scheduled.** The fork in `CATALOG.md` `OW1` is resolved — *"we will adopt
moros"* (user, 2026-08-09) — and *"but not today"*. `status:future`, so it holds no active
slot (the roster is `#11`/`#12`/`#13`, capped at three).

`M0` is **shipped**: the measurements below, which retired the largest risk and found the
one that actually costs. `M1`–`M4` are **designed, not built**.

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
| **`M2`** — the engine answers eight | S | `make test` green, per-test log diff | **Designed, not built** |
| **`M3`** — re-author 18 bundles' stat blocks | **M/H** | `make test` + a user read of the roster | Blocked on `M2` |
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
`RaceDef`/`ClassDef` gain their two fields. ⚠ **Behaviour-preserving is NOT the gate here** —
adding axes changes derived values by construction, so `M2`'s gate is *green*, not
*identical*, and `M4` is where the numbers are judged.

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
