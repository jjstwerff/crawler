# `15` — A bundle ships behaviour, not just the flags the engine defined

**Issue:** [`jjstwerff/crawler#15`](https://github.com/jjstwerff/crawler/issues/15) ·
**Value:** `G` · **Effort:** `VH`

## Status

**Stage 0 is shipped without anyone tracking it; Stages 1–5 are designed, not built.**
`SCRIPTING.md` has carried the full design — five stages, each with a proof move and a
named gate — since before this plan existed. This plan is the tracker it never had, and
it **adopts `SCRIPTING.md`'s own stage ids verbatim** rather than inventing a second
numbering for one body of work.

⚠ **Nothing here is scheduled.** `val:G`, `status:future`: this is the ceiling, not a
blocker. It is written down so the next down payment is a *decision* instead of an
accident — see `S0`.

## Goal

A content-only bundle can add a monster that does something the engine has no flag for,
with zero edits under `src/`.

That is `SCRIPTING.md` Stage 1's proof move, and it is the sentence that decides whether
any of this worked.

## Why

`BUNDLE.md`'s standing check has a stated ceiling: **a bundle can only *set* vocabulary
the engine defined.** Every content type obeys the library/content seam, and the seam
still stops at "flags the engine shipped". `SCRIPTING.md` is the staged path past it, and
`DESIGN.md` §3a's bounded-simulation pillar is the fence around it — depth in the
derivation, shallow at the interface.

## What `S0` turned up — 2026-08-09

⚠ **THE EPIC IS ALREADY BEING SPENT, AND THAT IS THE FINDING.** The item routine-by-id
seam shipped on 2026-08-09 — `bundles/<b>/items/<item_key>.loft` exposing `pub fn apply`,
discovered by a scan and dispatched from a generated file, so a bundle ships a usable item
with no engine edit. That is drawn directly from `SCRIPTING.md`'s routine table (the
"item effect" row), and it went in as a bug fix for `itemfx`'s hand-written key chain.

It was the right change and it is gated (`libcheck` **L6**). But it was a **stage-0 down
payment on an untracked epic**, taken without reference to the stages it belongs to. That
is exactly how a large design gets consumed piecemeal and is never built: each slice is
justified locally, and the shape it was a slice of goes unrecorded.

**Found while measuring:** the spell half of the same seam (`spell_defs_gen`, effect-id →
bundle routine) has been shipped for longer still. So **two of Stage 1's mechanisms exist
already** in special-purpose form — dispatch-by-id, generated from a bundle scan, with no
engine reference to a bundle. Stage 1 is closer than `SCRIPTING.md` reads; what is missing
is the *event surface*, not the dispatch.

## Steps — `SCRIPTING.md`'s stages, adopted

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`S0`** — routine-by-id, shipped twice (spells, items) | — | `make test` (`libcheck` L6) | **Shipped, unplanned** |
| **`S1`** — event/hook bus + `EventCtx` *(the keystone)* | H | `eventtest.loft` | **Designed, not built** |
| **`S2`** — general deterministic API (~40 primitives, seeded RNG) | H | `apitest.loft` | **Designed, not built** |
| **`S3`** — flags-as-behaviours (`MF_GAZE`, `RF_FREE_ACTION` as bindings) | M | `specialtest` still green | **Designed, not built** |
| **`S4`** — extensible state (property bag; status-as-data) | H | `statetest.loft` | **Designed, not built** |
| **`S5`** — runtime-loaded sandboxed bundles (@PLN86) | VH | drop a mod folder and play | **Designed, not built** |

Each stage's checklist, proof move and gate are in **`SCRIPTING.md` → Staged epic**. This
table does not restate them — a plan never restates its anchors.

⚠ **`S1` IS THE KEYSTONE AND THE OTHERS ARE NOT INDEPENDENT.** `S3` re-expresses flags as
event bindings and cannot start before the bus exists; `S4`'s per-tick status routines are
event subscribers. `S2` is the only one that can proceed in parallel, because generalising
the `Player` verbs is useful with or without a bus.

## What this plan does NOT change

- **The bounded-simulation pillar.** `DESIGN.md` §3a is the authority: a derived system
  buys **coherence, not mechanics**, and the key budget stays where it is. Scripting
  raises the *authoring* ceiling, not the number of verbs a player learns.
- **The library/content seam.** Bundles stay library-like; `BUNDLE.md`'s standing check
  and `libcheck` L6 apply to every stage.
- **Determinism or the MP-safe clock.** `SCRIPTING.md`'s acceptance fences are
  non-negotiable and this plan inherits them — a routine gets a seeded RNG and no
  wall-clock.
- **Anything in flight.** `S0` is done; nothing else is scheduled, and no other plan
  waits on this one.

## Open questions

1. Is `S1` smaller than written, given `S0`? Two dispatch mechanisms already exist and are
   generated from bundle scans. The honest first move may be to **read them and ask what
   an event surface adds** rather than designing the bus from the document.
2. Does the item/spell dispatch converge into the bus at `S1`, or stay beside it? Two
   generated dispatchers plus a bus is three mechanisms for one idea — the shape this
   repo's own rules warn about.

## See also

- **`SCRIPTING.md`** — the design; the five stages, their checklists, proof moves and gates
- `BUNDLE.md` → *Standing check* and *A usable item's routine* (`S0`)
- `DESIGN.md` §3a — the fence · `UPSTREAM-PLANS.md` @PLN86 — what `S5` waits on
