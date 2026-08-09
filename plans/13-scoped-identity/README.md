# `13` — A stored identity is an index into a scope-owned table

**Issue:** [`jjstwerff/crawler#13`](https://github.com/jjstwerff/crawler/issues/13) ·
**Value:** `R` · **Effort:** `MH`

## Status

Nothing is built. `S0` is **shipped** only in the sense that the measurements below were
taken and the seam was named; `S1`–`S4` are **designed, not built**.

⚠ **This plan is time-sensitive and that is unusual for crawler.** moros plan 21 has
`R1` shipped and `R2`–`R5` designed; it is finishing the half crawler has not started,
while crawler holds the half moros has queued. Whichever lands alone becomes "the
design", validated against one project — which is precisely what the governing ruling
forbids.

## Goal

The mechanism that turns a stored byte into a thing lives in the library, takes the
owning scope as a **parameter**, and is used by crawler's ground and walls — so a
project supplies a palette and nobody supplies an identity.

## Why

> *"The goal is to grow everybody through libraries: a library's design must be
> UNIVERSAL FOR THE CLASS, not for one project. So the indexing of walls / items /
> ground must be done in a way every project benefits from, in its own scope."*
> — user ruling, 2026-08-09 (recorded in `CLAUDE.md`)

## What `S0` turned up — measured 2026-08-09

**The class is solved twice, each time by half.**

| | ground / walls | items / actors |
|---|---|---|
| **crawler** | ⚠ hard-coded: `tiles: vector<integer>`, vocabulary in a COMMENT (`0 floor, 1 solid wall`, tile 5/8/9), **36** literal comparisons | ✅ indirected: bundles author keys, `catalog.loft` merges, the engine names no bundle |
| **moros** | ✅ plan 21: a byte indexes a **region-owned** palette, `0 = nothing` the only fixed identity (329 uses, 22 true identity comparisons) | queued — "items get their own mapping similar to the other mappings" |

⚠ **THE HALVES ARE THE SAME MECHANISM**, which is why neither should be finished alone.
crawler solved identity for *open* enumerations (content a bundle adds) and left the
*closed* ones as literals; moros is doing the reverse.

**Found while measuring:** crawler's solved half had **leaked** — `itemfx.loft`
dispatched on content key (9 sites) and `sim.loft` mapped indices to keys (15). Both are
closed now (the item routine-by-id seam, `BUNDLE.md`), and `libcheck` **L6** gates the
rule. That leak is the evidence for how this rots without a gate: the indirection
existed and was being bypassed.

## The design, as far as it is settled

> **I-SCOPE — a stored identity is an INDEX into a table owned by a SCOPE. `0 = nothing`
> is the only identity fixed in code. The library owns the indirection; each project owns
> every entry; the SCOPE IS A PARAMETER.**

⚠ **The scope clause is the whole test of universality**, because the projects' scopes
genuinely differ — a **region** in moros (a desert and an ocean each want their own 256),
a **bundle** in crawler (a stranger drops one in and plays), a **level** elsewhere (plan
21: *"doesn't have the region border problem"*). **If the package must be edited to admit
a new kind of scope, it was never universal.**

What must NOT travel into the package is any particular palette — crawler's
`floor`/`wall`/`pool`, moros' `grass`/`road` — for the same reason `EXTRACTION.md` says
the metre must not.

## Steps

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`S0`** — measure both halves; name the seam | XS | this file | **Shipped** |
| **`S1`** — bring crawler's scope to moros' design **before** it publishes | S | a written review on moros#21 | **Designed, not built** |
| **`S2`** — the mechanism lands in a `hex_*` package, scope-parameterised | M | the package's own gate | **Designed, not built** |
| **`S3`** — crawler's ground/walls consume it; the 36 literals go | M | `make test` + a new `identtest` | Blocked on `S2` |
| **`S4`** — a bundle supplies a palette; `libcheck` gains the L6-shaped rule for ground | S | `make test` | Blocked on `S3` |

### `S1` — the contribution, designed

Not code: a review of moros#21's design against crawler's scope, answering three
questions its author cannot answer alone. **Does the palette handle takes an opaque
scope handle, or a region id?** (crawler has no regions.) **What happens at a scope
boundary when a stored world is read under a different palette?** (crawler's bundles
compose; moros' regions tile.) **Is `0 = nothing` enough, or does a consumer need a
"not in this palette" answer distinct from "nothing here"?**

⚠ This step is the only one with an external deadline, and it is cheap. Doing `S2`–`S4`
without it risks building against a design that was never checked by a second scope.

### `S2` — the package, designed

A `hex_*` package (name TBD — `hex_ident` reads right) owning: a palette handle, `get`
(index → key/attributes), `find` (key → index), and the contract for a stored world that
outlives its palette. **Branch-selector or table form, not `vector<text>` literals**
(loft#336 — see `LOFT-NOTES.md`; the workaround was re-measured 2026-08-09 and stands).

### `S3` — crawler consumes it, designed

The 36 literals become palette lookups; `tiles: vector<integer>` keeps its storage and
loses its meaning-in-a-comment. ⚠ **This is a behaviour-preserving change and must be
proved as one** — the per-test log diff (`CLAUDE.md`), not the gate's stdout.

### `S4` — a bundle supplies ground, designed

The payoff row: a bundle ships its own terrain palette and the engine names none of it.
Gate it the way `L6` gates the item half, or it rots the same way.

## What this plan does NOT change

- **Storage.** A cell stays a byte/integer; this is about what the byte MEANS.
- **The bundle format's other sections.** `production` (BUNDLE.md) is done and separate.
- **moros' plan 21.** crawler contributes a scope and a review; it does not redesign
  someone else's plan, and `S1` is explicitly a conversation, not a patch.
- **Item identity.** Already solved here (bundles + `catalog` merge + `libcheck` L6).

## Open questions

1. Which package? A new `hex_ident`, or an arm of `hex_field` (which already owns
   `Labels`)? The second is fewer moving parts and the first is honest about the scope
   contract being a different idea from a field.
2. Does the palette persist with the world, or beside it? A stored world read under a
   changed palette is the failure mode with no obvious right answer, and `S1` should ask
   moros what plan 21 decided.

## See also

- `CLAUDE.md` → the governing ruling · `ADOPTION.md` → *Universal for the class*
- `BUNDLE.md` → the library/content seam, and `L6` as the shape of the gate
- moros `plans/21-region-mappings/` — the other half, in flight
