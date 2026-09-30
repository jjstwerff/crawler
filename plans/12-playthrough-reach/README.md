# `12` — A scripted session can reach a fight and its spoils

**Issue:** [`jjstwerff/crawler#12`](https://github.com/jjstwerff/crawler/issues/12) ·
**Value:** `Q` · **Effort:** `S`

## Status

> ⚠ **FUTURE as of 2026-08-09 — demoted so `#17` could take the slot** (user). `A0` stays
> shipped and keeps paying: the harness and three scripts (`walk`, `descend`, `respawn`)
> run in every gate, so the *loop* is built and only its *reach* is parked.
>
> ⚠ **What that costs, stated plainly:** `A1`–`A4` are the scripts for combat, the drop,
> pickup-across-a-descent and the XP → clevel → stat-raise chain. Until they land, those
> systems have **no session-level coverage** — the 92 unit gates test them a function at a
> time, which is the exact blind spot this plan exists to close. Nothing regresses by
> waiting; it simply stays unwatched.

`A0` is **shipped** — the harness, three scripts (`walk`, `descend`, `respawn`), and the
measurements below that decided the rest of this plan. `A1`–`A4` are **designed, not
built**: each is written out here, so the next session builds rather than re-derives.

The harness itself is not blocked; what is blocked is *reach*. A script can walk,
descend and die. It cannot yet meet an enemy, so it cannot cover combat, the drop, the
pickup path, or the XP → clevel → stat-raise chain.

## Goal

A `scripts/*.play` session can fight a monster, take what it drops, and spend the level
it earned — through the shipped intent seam, with the setup arranged by pokes.

## Anchors

- `src/playtest.loft` + `scripts/*.play` — the harness and the three shipped scripts.
- `src/gameflow.loft` — `flow_move` / `flow_action`, the seam every claim runs through.
- `src/combattest.loft` — the working bump-melee idiom (`charge` is its port).
- `src/itemfx.loft` + `src/item_fx_gen.loft` — the use-item seam `A3` will cover.
- `BUNDLE.md` → *A usable item's routine*; `DESIGN.md` §3a for the death model `respawn`
  already gates.

## What `A0` turned up — measured 2026-08-09

Three scripts shipped, and two more were attempted and abandoned **on evidence**. Both
failures are recorded because each decides a step below.

| probe | result | what it decides |
|---|---|---|
| `floor` / `livefloor` at genesis, seed 1337 depth 1 | **0 and 0** | a fresh level carries NO loot — a pickup script has nothing to pick up |
| `charge 600` from spawn | `livefoes 16 → 16`, `xp 0`, `hp 70` unchanged | the charge never engages |
| `charge 60` then `charge 540`, watching the hex | `20,13 → 22,10 → 22,9` | it MOVES, then stalls: 540 frames buy one hex |

⚠ **THE CHARGE IS NOT BROKEN, IT IS BLIND.** It aims at the first *alive* enemy, which
on a generated level is usually across the map behind walls, and the glide is a straight
line with no pathing — so the player jams against a wall and presses there for the rest
of the script. `combattest` passes with the same idiom because its enemy is placed
reachable; the idiom was never the thing that made it work.

⚠ **AND THE TWO FAILURES ARE THE SAME FAILURE.** No loot at genesis is not a separate
problem: floor items come from drops, so `livefloor > 0` is *downstream of a kill*. That
is why the steps below are a chain and not a list — `A3` cannot be written before `A2`
lands, and `A2` cannot be written before `A1`.

**Found while measuring:** a fresh depth-1 level holds **16 enemies and 0 floor items**
at seed 1337. Nothing in the gate stated the loot figure, and `descend.play`'s
`expect enemies > 0` was written against the enemy half of it — the loot half had no
gate at all until this plan names one.

## Steps

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`A0`** — the harness + `walk`/`descend`/`respawn`, and the measurements above | S | `make test` (`playtest*`) | **Shipped** |
| **`A1`** — `findfoe`: stand next to the nearest live enemy | XS | `make test` | **Designed, not built** |
| **`A2`** — `fight.play`: bump-melee a kill, and the XP that follows | S | `make test` | **Designed, not built** |
| **`A3`** — `pickup.play`: the drop, the pickup, and using it across a descent | S | `make test` | Blocked on `A2` |
| **`A4`** — `levelup.play`: XP → clevel → a banked point spent with `act 4` | S | `make test` | Blocked on `A2` |

### `A1` — `findfoe`, designed

A poke, in the family of `findstair` / `findloot`: pick the live enemy with the smallest
`sim_enemy_dist`, and place the player **adjacent to it, not on it**. Adjacent because
the mechanic under test is *bump*-melee — landing on the enemy's own hex would skip the
approach that does the attacking, and `A2` would be asserting something no play produces.

⚠ Distance, not index. `A0` proved index-0 selection aims across the level; the harness
already has `sim_enemy_dist`, so the fix is selection, not pathing. **This plan does not
add pathfinding** — see the fence below.

### `A2` — `fight.play`, designed

`findfoe`, then short `charge` bursts with `expect` rows between them. The claims:

- `livefoes` drops by exactly one — a kill, not a stampede;
- `xp` strictly increases, and `hp` strictly decreases (the enemy hits back — `combattest`
  gates that today at the unit level; here it is a session);
- `alive == 1` throughout, so the script fails loudly rather than quietly respawning;
- `livefloor` **increases** — the corpse leaves something behind, which is `A3`'s premise
  and is the row that would have caught the `floor = 0` surprise earlier.

### `A3` — `pickup.play`, designed

Depends on `A2` only for the drop. Then: `findloot`, `act 2` (pick up), `expect inv ==
kit + 1`; `findstair` + `move` to descend; `expect inv` unchanged across the rebuild; and
`act 3 <slot>` to use it, asserting the effect landed (`msgs` increased, or `hp` moved
for a cure). That last row is the only gate that would cover `itemfx` → `item_fx_gen`
end-to-end *as played*.

### `A4` — `levelup.play`, designed

The kill's XP will not reach clevel 2 on its own, so this splits honestly: the kill is
real (`A2`'s rows), and the grind is a poke — `xp <n>` until `clevel` rises. Then
`expect statpts > 0`, `act 4 <stat>` to spend it, and `expect statpts` decreased with the
stat raised. The `act 4` arm of `flow_action` has no session-level gate today.

## What this plan does NOT change

- **Pathfinding.** `A1` places the player next to a foe; it does not teach the harness to
  walk there. Monsters have flow-field pathing (`sim.loft`); exposing it to scripts is a
  separate question and this plan does not answer it.
- **Combat balance.** Every claim is a relation (`xp` increased, `hp` decreased,
  `livefoes` −1). Damage numbers stay `combattest`'s business.
- **The unit gates** (89 when this was written; **98 rows** since the five unwired tests were
  wired in). This adds session coverage beside them, and replaces none.
- ~~**Parallelism.** The gate stays serial — that is blocked upstream on
  [loft#831](https://github.com/loft-lang/loft/issues/831), not here.~~ **Unblocked
  2026-08-10**: loft#831 is fixed (`c69f7c1a`) and the gate now runs **`min(8, nproc-2)`-wide**
  (8 here), so a row this plan adds costs wall clock only if it lands in the slowest few.
  ⚠ **That makes a `.play` row
  cheaper than it looks, which is a reason to design it well, not a licence to add rows** — the
  plan's claim-per-row discipline is unchanged, and each still names what it asserts.

## Open questions

1. Should `charge` fail loudly when it makes no progress for N frames? `A0` spent 540
   frames pressed against a wall and reported `PLAY OK`, because nothing claimed movement.
   A stall detector would have named the defect instead of leaving it to a hex probe.
2. Does `livefloor > 0` after a kill hold for every monster, or only ones with a drop
   table? If drops are per-monster content, `A2`'s loot row belongs on a chosen monster
   rather than "the nearest one".

## See also

- `BUNDLE.md` → *A usable item's routine* — the seam `A3` exercises.
- `DESIGN.md` §3a — the death model `respawn.play` already gates.
- `LOFT-HANDOFF.md` H10 / [loft#831](https://github.com/loft-lang/loft/issues/831) — why the
  gate *was* serial, the fix that ended it, and the consumer confirmation filed back.
