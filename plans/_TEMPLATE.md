# Plan template

Copy this file to `plans/<N>-<slug>/README.md`, where **`<N>` is the
`jjstwerff/crawler` issue number** — claimed *before* the directory exists, never
derived from the local tree. Delete the guidance blocks (marked *(delete)*) as you fill
it in. Conventions + the lightest-workflow table: [`README.md`](README.md). Closing or
deferring: [`_LIFECYCLE.md`](_LIFECYCLE.md).

**Before you copy — is this actually a plan?** If it fits in one row of a reference
doc's `## Open work` table with one sentence of design, it isn't. Add the row instead.
If the first phase is *characterize the problem* rather than *design + build*, use
[`_INVESTIGATION_TEMPLATE.md`](_INVESTIGATION_TEMPLATE.md).

---

# `<N>` — `<a claim, not a topic>`

*(delete)* ⚠ **THE TITLE IS A CLAIM.** *"Regions own the mapping: one byte is not one
identity"* (moros 21) and *"A hash insert that allocates once and never re-hashes"*
(loft 135) each say what is true when the plan lands. *"Region mappings"* and *"hash
performance"* name a topic and commit to nothing — and a title that commits to nothing
cannot be shown to be finished.

**Issue:** [`jjstwerff/crawler#<N>`](https://github.com/jjstwerff/crawler/issues/<N>) ·
**Value:** `<S|R|G|F|U|C|Q|N>` · **Effort:** `<XS|S|M|MH|H|VH>`

## Status (REQUIRED)

*(delete)* The **single source of truth** for what is shipped / open / deferred /
blocked. The issue carries the lifecycle label; the per-phase truth lives here, so
there is no second copy to drift.

⚠ **PER STEP, AND NAME THE STEPS.** *"`A1`, `A1b` and `A2c`'s along half are shipped;
`A2`–`A5` are designed, not built"* (moros 20) is a status. *"In progress"* is not — it
cannot be checked, and it hides which half a reader may rely on. **"Designed, not
built" is a first-class state**: it says the thinking survived even though the code has
not been written, which is the whole reason to write a plan down rather than a ticket.

## Goal (REQUIRED)

*(delete)* One sentence — what ships when this plan is complete. No strategy or
advertising language.

## Anchors (REQUIRED)

*(delete)* The reference docs this plan implements or extends, and the source files it
touches. A plan never restates its anchors' content — it links.

## Blueprint gate (REQUIRED for exact-invariant work)

*(delete)* Geometry, caching, serialization, store-lifetime, protocols and round-trips
are **exact invariants, not open spaces** — CLAUDE.md's design/debug protocol applies
and the cheap-medium prototype comes BEFORE the loft code. State per phase: the
**concrete plotted end-result** (the exact target output for one specific input), the
**invariant** it pins (caching → *round-trip = identity*), and the medium (a Python
prototype under `tools/blueprints/`, a headless dump + plot, a round-trip test).

Say so in one line if a phase has no exact-invariant surface. Silence reads as "gate
done", not "gate N/A".

## Phases (REQUIRED if multi-phase)

*(delete)* One row per phase. **Verify** is how you see it works — name the gate:
`make test` (a `src/<x>test.loft` case), `make probe` (a `probes/*.probe`), a blueprint
plot, or a user visual check in `make play`.

| Step | Effort | Verify | Status |
|---|---|---|---|
| **`A1`** — short title | S | `make test` / `<x>test.loft` | Shipped |
| **`A2`** — short title | M | `make probe` / `<name>.probe` | **Designed, not built** |
| **`A3`** — short title | S | `make test` | Blocked on `A2` |

*(delete)* ⚠ **THE IDS ARE STABLE AND SUB-DIVIDE.** `A1`, `A1b`, `A2c` — a step that
splits keeps its parent's letter, so a commit message, a status line and a findings
section can all name the same thing a month apart. A row numbered by position renumbers
itself the first time a step is inserted, and every reference to it silently rots.

⚠ **A STEP THAT IS ONLY DESIGNED IS STILL WRITTEN OUT IN FULL**, here and in its
findings section. That is the "step documentation of future work": the design outlives
the session that produced it, and the person who builds `A3` next month is not
re-deriving it from the title.

## What `<step>` turned up (REQUIRED once a step has run — one section per step, DATED)

*(delete)* ⚠ **THIS IS WHERE A PLAN EARNS ITS KEEP, and it is the section crawler kept
losing.** loft 135 is mostly dated measurement sections (*"The Q1 measurement
(2026-08-09) — it is ONE access, and it is a byte problem"*); moros 21 has *"What `R1`
turned up"*. Plan #11's `RESULTS.md` does it here already — *"`P1` result — one
passability predicate, measured 2026-07-22"* — and it is the only crawler plan that
does, because nothing told the next author to.

Findings that live only in a commit message are findings the next reader will not
search for. Write the number, the date, and what it means — including the ones that
**refuted** the step's own premise, which are the most valuable rows in the file.

⚠ **AND RECORD WHAT YOU FOUND ON THE WAY.** loft 135 carries *"Found while measuring:
growing a hash ABANDONS every previous bucket table"* — a defect discovered by a probe
aimed at something else entirely. That is not a digression; unrecorded, it is
rediscovered from scratch months later.

## What this plan does NOT change (REQUIRED)

*(delete)* The explicit fence. moros 21 and loft 135 both carry one, because the
alternative is a reader assuming the plan covers a neighbouring problem and building on
a guarantee nobody made. Name the adjacent things that stay as they are, and where the
real answer for each lives.

## Order + risks (OPTIONAL)

*(delete)* The dependency order when this plan unpauses, and the known traps — loft
idioms to avoid (LOFT-NOTES.md's survival guide), seam rules that must not break, anything
gated on an upstream fix (link the issue; never block crawler on it).

## Open design questions (OPTIONAL)

*(delete)* Numbered. Each resolution either becomes a decision recorded in the anchor
doc or is absorbed into this plan's design.

## See also (REQUIRED)

*(delete)* Reference docs this implements · sibling plans that block or cooperate ·
the tracker issue · any upstream item it waits on.

---

## Authoring notes *(delete this whole section)*

- **Length budget 100–300 lines.** Longer means reference content is leaking in —
  move it to the doc that owns it.
- **`README.md` is required**; add sub-files only for distinct concerns
  (`DESIGN.md`, `IMPL.md`, `probes/`), one concern each.
- **Never calendar time** — effort letters only. "Two weeks" ships in two days.
- **The seam law is re-checked every phase** if the plan touches the engine↔bundle
  boundary (BUNDLE.md → *Standing check*).
- **Upstream (loft) defects never become crawler plans** — LOFT-HANDOFF.md + FILING.md.
- **On opening:** claim the issue → label it `plan` + `status:*` + `val:*` → create the
  directory named for the issue number → fill Status + Goal first.
- **Do NOT add a CLAUDE.md doc-index entry by default** — plans are discoverable from
  the tracker. Add one only if the plan introduces a genuinely new top-level concept.
