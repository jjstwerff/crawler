# MOROS.md — what crawler depends on moros for, and what it must never depend on

crawler and `../moros` share a world, a hex convention and a library layer. This file is
the **register of the first two only**: the things crawler would be wrong about if moros
changed them, and which no version number would catch.

⚠ **NO LIBRARIES IN THIS FILE.** *"Each project is allowed to change libraries as long as
the contract of them stays valid"* (user, 2026-08-09). A library dependency is not a moros
dependency at all — it is a **contract** (`api_compatible_with` / `data_compatible_with`,
`loft.lock`), owned by nobody, changeable by anybody, and enforced by machinery rather
than goodwill. Writing `hex_grid` in here would be claiming a veto crawler does not have
and does not want. See `ADOPTION.md` → *No project owns a library*.

⚠ **AND `../moros` IS READ-ONLY** — it has its own agent (`CLAUDE.md`). Everything below
is something crawler *reads, follows or waits on*, never something crawler changes there.
A finding becomes a document **here**; delivery is the user's call.

---

## What this file IS for

A dependency belongs here when **all three** hold:

1. crawler would be **wrong**, not merely out of date, if moros changed it;
2. **no contract would catch it** — no version, no lockfile, no compile error;
3. it is a **decision or a fact**, not code. Code that both projects use is a library, and
   libraries are governed by contract, not by this register.

---

## D1 — The shared world: stats, races, powers, names

**The largest dependency, and the least visible.** crawler's character model is *seeded
from moros* (`CATALOG.md`), not derived from Angband:

| | |
|---|---|
| **the 8 statistics** | Adopted 2026-06-27, **replacing Angband's 6** (STR/INT/WIS/DEX/CON/CHR). Might, Endurance, Dexterity … each mapped to a crawler combat role (`CATALOG.md` §0). |
| **races, powers, capabilities** | 37 capabilities seeded directly from moros `html/data.js`, regrouped by their role in crawler combat. |
| **the names themselves** | *"Names are moros's own (shared world, DESIGN §2) — **not** an IP concern"*. ⚠ This is the ONE place crawler's clean-room rule is deliberately suspended, and it is suspended *because* the world is shared. |
| **the advancement economy** | Spell/casting economy *"goes the moros way"* (`CATALOG.md` §6.3) — the content stays Angband's, the economy is moros'. |

**What crawler needs:** that the shared world's stat set, race list and power names stay
the shared world's. A rename there is a rename here.

**What would break silently:** everything content-facing. There is no version on
`data.js`, no gate on either side that compares the two, and a divergence would look like
crawler content drifting rather than a shared world moving. ⚠ **This is the only entry
with no instrument at all** — see *Open* below.

## D2 — The hex convention

**Pointy-top, odd-r, `L = √3`** — `CLAUDE.md` calls it "moros geometry", `EXTRACTION.md`
calls `hex_grid` "the canonical **moros-convention** hex geometry".

**What crawler needs:** the convention, not the code. The *code* is `hex_grid` and is a
library — out of scope here by the rule above. What is in scope is that moros keeps
answering the same lattice, because crawler's world, its stored coordinates and every
golden fixture assume it.

⚠ **This one HAS an instrument, and it earned itself on its first run.** `hex_grid` ships
a cross-language parity fixture (`tests/fixtures/lattice.tsv`) asserted on *both* sides —
loft and moros' JS — precisely because two implementations of one convention drift in
silence. It immediately found that `html/hex-lattice.js` tested row parity with
`row % 2 === 1`, and JavaScript `%` keeps the dividend's sign, so the half-hex shift
stopped on every **negative** odd row: the browser map and `hex_grid` were half a hex
apart below `y = 0`.

**Doubled-lattice integers, not sampled floats** — the fixture holds `k = 2·col + (row & 1)`,
`m = 3·row`, exact in both languages, because a float fixture needs a tolerance and *a
tolerance is exactly where a half-hex error hides*.

## D3 — Scoped identity: a decision crawler is waiting on

moros plan 21 — *"regions own the mapping: one byte is not one identity"* — is building
the half of an idea crawler holds the other half of (`plans/13-scoped-identity/`, issue
#13). crawler is **not** waiting on their code; it is waiting on three decisions, because
a design validated against one project is not yet universal for the class:

1. Does the palette handle take an **opaque scope handle** or a region id? (crawler has no
   regions; its scope is a bundle.)
2. What happens when a **stored world is read under a different palette**? (crawler's
   bundles compose; moros' regions tile.)
3. Is `0 = nothing` enough, or does a consumer need *"not in this palette"* distinct from
   *"nothing here"*?

**Status:** unanswered. `plans/13-scoped-identity/` `S1` writes crawler's scope up as
`REVIEW.md` **in this repo**; how it reaches moros is the user's call.

## D4 — moros as the second consumer of the library layer

`EXTRACTION.md` → *The editor as the second consumer* makes a load-bearing claim: the
`hex_*` seam is proven because something other than crawler uses it. moros' `hex_editor`
does — it depends on `hex_field`, `hex_edge`, `hex_way`, `hex_draw`, `hex_form`,
`hex_shape`.

**What crawler needs:** not a library (those are contract-governed and may change freely)
but the **fact of a second consumer**. If moros stopped consuming the family, crawler's
extraction argument would lose its evidence and every "this is reusable" claim would rest
on one user again.

⚠ Nothing to coordinate and nothing to ask for — recorded because losing it would be
invisible, and because it is the reason `EXTRACTION.md`'s Definition of Done is worth
anything.

---

## What is deliberately NOT here

- **Every `hex_*` package, `graphics`, `mesh3d`, `glb`, `random`.** Libraries. Contract
  territory: `loft.toml` floors, `loft.lock`, and `libcheck` L1/L2. Any project may change
  them within the contract, including moros, including crawler.
- **The gate harness, the parallel runner, the plan shape.** Borrowed *methods*
  (`tools/run-gates.sh` inspired `libcheck`'s reporting and the quiet gate; moros' plan
  shape is adopted in `plans/README.md`). Borrowing an idea creates no dependency — crawler
  owns its copies outright and moros may change theirs freely.
- **Anything in the moros tree.** Read-only, and its agent's.

## Open

1. **D1 has no instrument.** D2 has a parity fixture that caught a real bug on day one; D1
   — the larger dependency — has nothing. A `data.js`-vs-`CATALOG.md` check (stat names,
   race keys, power keys) would be cheap and would make a shared-world drift *loud*.
   Not built, and not obviously crawler's to build alone.
2. **D3 has a deadline crawler cannot see.** moros 21 `R1` shipped and `R2`–`R5` are
   designed; whichever half lands first sets the design. crawler can write its review but
   cannot time it.
