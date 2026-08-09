# MOROS.md — what moros must write for crawler: nothing

moros is a **tabletop** game in a shared world. crawler is a **computer RPG** in the same
world. Two different games, one setting — which means crawler holds its own documentation
for its own game, and the register of "things moros owes us" is **empty on purpose**.

This file exists to say that clearly, because the opposite assumption is easy to drift
into and expensive: a project that believes it is waiting on a sibling stops writing its
own docs.

## Measured 2026-08-09 — the coupling is zero

| probe | result |
|---|---|
| anything in `src/`, `tools/`, `Makefile`, `bundles/` reading moros | **nothing** — no path into that tree at build or run time |
| the races | **crawler's own bundles** — `dwarf`, `elf`, `gnome`, `half_elf`, `halfling`, `half_orc`, `half_troll`, `highborn`, `high_elf`, `human` |
| the stats | **crawler's own code** (`gameflow::stat_name`, `sim::stat_index`) |

crawler cannot be broken by a moros edit, because nothing here reads anything there.

## So what was the "shared world" dependency?

**A seeding event, already finished** — not a live dependency. `CATALOG.md` was *seeded
from* moros' `html/data.js` in June 2026: the races, the powers, and a decision to adopt
its stat set. Seeding is a one-time act of copying and mapping; what came out of it is
**crawler's document about crawler's game**, and it is already written.

⚠ **AND THE PART THAT WAS NEVER EXECUTED PROVES THE POINT.** `CATALOG.md` §0 says *"KEY
DECISION — adopt moros's 8 statistics (DECIDED 2026-06-27), replacing Angband's 6"*. The
engine runs **STR/INT/WIS/DEX/CON/CHR** — Angband's six. The eight (Might, Endurance, …)
appear in no code path.

That is not a moros problem and there is nothing for them to write. It is **crawler's own
open decision**, sitting unexecuted in a crawler doc for six weeks, and the honest place
for it is crawler's tracker — see `CATALOG.md` §0, now marked.

## What is genuinely shared, and how each part is governed

| | what it is | who governs it |
|---|---|---|
| **the setting** — race and power NAMES | shared-world IP both games draw on (`DESIGN` §2). The one place crawler's clean-room rule is deliberately suspended | nobody "writes it for" anybody. crawler transcribes what it uses and holds the transcription |
| **the hex convention** — pointy-top, odd-r, `L = √3` | a lattice both implementations answer | **the library** (`hex_grid`) and its cross-language parity fixture. Contract territory |
| **the `hex_*` family** | code | **the contract** — `api_compatible_with`, `loft.lock`. Any project may change a library while the contract holds (`ADOPTION.md`) |
| **scoped identity** (moros plan 21 ↔ crawler `plans/13-scoped-identity/`) | a library DESIGN question | the contract, once it lands. Until then crawler writes down what its scope needs (`S1` → `REVIEW.md`) and proposes; it does not wait |

⚠ **Every row is either crawler's own or contract-governed. No row is an obligation on
moros.** That is the whole content of this file.

## The one thing worth keeping an eye on, and it is not a dependency

crawler and moros are **the library layer's two consumers**, and `EXTRACTION.md`'s
reusability argument rests on there being two. If moros stopped consuming the `hex_*`
family, crawler's "this is reusable" claim would rest on a single user again.

Nothing to request and nothing to coordinate — recorded because losing it would be
invisible, and because it is why `EXTRACTION.md`'s Definition of Done means anything.

## The rule this file encodes

> **crawler holds the docs for the computer game.** A design that is crawler's to make is
> crawler's to write down, here, whatever its provenance. Reading a sibling's work creates
> no dependency — and neither does having been seeded by it.

Corollaries, each of which was a live mistake before it was written down:

1. **Do not record a finished transcription as an ongoing dependency.** `CATALOG.md` is
   crawler's document now; its provenance is a footnote, not a subscription.
2. **Do not list a library here.** That is a contract, owned by nobody
   (`ADOPTION.md` → *No project owns a library*).
3. **Do not wait.** Where a decision spans both projects, write crawler's half down and
   propose it. `plans/13-scoped-identity/` `S1` is the worked example — a `REVIEW.md` in
   this repo, delivered at the user's discretion.
4. **`../moros` is read-only** — it has its own agent (`CLAUDE.md`). Findings become a
   document here.
