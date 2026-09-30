# `14` — Two implementations of one idea converge, or they get different names

**Issue:** [`jjstwerff/crawler#14`](https://github.com/jjstwerff/crawler/issues/14) ·
**Value:** `R` · **Effort:** `MH`

## Status

> ⚠ **FUTURE as of 2026-08-09 — by its own words.** This plan's Status says *"nothing here
> is urgent, and that is the risk"*. A priced debt with no schedule does not need an active
> slot; it needs to stay visible, which `libcheck`'s accepted-debt line already does on
> every gate run.

`C0` is **shipped** — `ADOPTION.md` P0–P4, the three forked modules deleted, the registry
made authoritative, and `libcheck` gating five rules. `C1`–`C3` are **designed, not
built**: the debt is measured and priced below, and none of it is paid.

⚠ **Nothing here is urgent, and that is the risk.** A priced debt with no schedule is a
debt that gets defended instead of paid — which is the exact state `ADOPTION.md` says to
leave, not to reach.

## Goal

Every crawler module that shares a library package's name or subject has been resolved
one of three legal ways, and `libcheck`'s accepted-debt table is empty.

## Why

> **No first-class project owns a library.** Any project may ADD what it needs; the only
> constraint is not breaking the others. So *"we wrote it"* never licenses a copy and
> *"they wrote it"* never licenses a refusal — judge on **switching cost**, never on
> provenance. — user ruling, 2026-08-09

`ADOPTION.md` → *The line — a price, not a border* gives the three legal moves and one
illegal one; this plan is that section with a schedule attached.

## What `C0` turned up — measured 2026-08-09

Seven pairs. The discriminator is shared public function names — 100 % meant "the same
construction twice" and was settled by P1; **every survivor scores 0 or 1**, which means
none of these is a copy and all of them are a *rewrite* if switched.

| crawler | fns | package | fns | shared |
|---|---:|---|---:|---|
| `hexplace` | 9 | `hex_place` | 17 | 0 |
| `hexseat` | 5 | `hex_place` | 17 | 0 |
| `wallgeo` | 8 | `hex_shape` | 83 | 0 |
| `hexskel` | 31 | `hex_shape` | 83 | 0 |
| `hexmatch` | 10 | `hex_fit` | 30 | 0 |
| `hexlink` | 6 | `hex_recover` | 44 | 0 |
| `hexwheel` | 3 | `hex_body` | 25 | 1 — `wheel_angle` |

⚠ **THE NAMES ARE THE URGENT HALF, NOT THE CODE.** Two of these are already errors
waiting: `hexplace`/`hex_place` collide by name (`libcheck` L5, currently the sole
accepted-debt entry) and `hexwheel`/`hex_body` share `wheel_angle`. Under loft 2026.8.0 a
bare name declared by two packages in one graph is a **hard error at the use site** — so
these fire the day crawler adopts the package, whatever the code says.

**Found while measuring:** the survivor list is **seven, not the four** stated when this
was first raised. `hexskel` (31 fns vs `hex_shape`) and `hexmatch`/`hexlink` were missed
by a scan that only looked at pairs sharing a squashed name. Subject overlap needs
reading, not grepping — which is why `C1` is a reading step and not a script.

## Steps

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`C0`** — adopt what is identical; gate the rules; measure the rest | M | `make test` (`libcheck`) | **Shipped** |
| **`C1`** — price each of the seven: switch / extend / rename | S | this file, one row each | **Designed, not built** |
| **`C2`** — take the two NAME collisions off the table | S | `make test` (L4/L5 clean) | **Designed, not built** |
| **`C3`** — execute the priced rows, one per commit | H | `make test`, per-test log diff | Blocked on `C1` |

### `C1` — price each pair, designed

For each row, answer the three legal moves from `ADOPTION.md` with a reason, not a
preference: **switch** (the package's construction is better or good enough), **extend**
(ours is better, or covers a case theirs does not — so it goes INTO the package, which
the governing rule expects), or **rename** (they are genuinely different problems and the
shared name was the only thing they had in common). ⚠ *"Keep a private copy because
switching is inconvenient"* is the illegal fourth and must not appear.

The output is a row per pair in this file, and the `libcheck` `ACCEPTED` table updated to
match — each entry carrying its reason, as that table already requires.

### `C2` — the collisions, designed

Independent of `C1`'s verdicts, because a name clash bites on adoption day regardless of
which construction wins. `hexplace` → a name that says what it does (it is not
`hex_place`'s seating); `hexwheel::wheel_angle` → renamed or contributed to `hex_body`.
This is `ADOPTION.md` P2's method applied twice more — the same shape as
`Stencil`→`RoomStencil` and `Camera`→`SceneCamera`.

### `C3` — execute, designed

One pair per commit, each proved the way P1 was: **the per-test log diff must be
identical**, since every one of these is behaviour-preserving by construction. A pair
whose switch changes output is not a switch — it is a redesign, and it stops and gets its
own row.

## What this plan does NOT change

- **The packages' contents.** Where the verdict is *extend*, the work lands in
  `loft-libs-world` under its contract — this plan schedules the decision, not the merge.
- **`hex_field`/`hex_grid`/`hex_edge`/`hex_way`/`hex_roof`.** Adopted and done (P1).
- **The standing rules.** `libcheck` L1–L6 already gate them; this pays a debt, it does
  not add a rule.
- **Anything about which project is right.** Provenance is not an input.

## Open questions

1. Is `wallgeo` vs `hex_shape` even one pair? `wallgeo` builds room OUTLINES from corners;
   `hex_shape::hexwall` is exact-lattice wall geometry. `C1` may find the honest verdict
   is *rename nothing, they are different layers* — which is a legal outcome and should be
   recorded as one rather than left implicit.
2. Does `hexskel` (31 fns) belong to `hex_shape` at all, or is it the largest extraction
   candidate crawler still holds? The push side (`EXTRACTION.md`) may own that row.

## See also

- `ADOPTION.md` → *The line — a price, not a border*; *Accepted debt*
- `EXTRACTION.md` — the push side; a verdict of *extend* is an extraction
- `tools/libcheck.py` — L3/L4/L5 and the `ACCEPTED` table this plan empties
