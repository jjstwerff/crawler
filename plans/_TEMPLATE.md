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

# `<N>` — `<Plan title>`

**Issue:** [`jjstwerff/crawler#<N>`](https://github.com/jjstwerff/crawler/issues/<N>) ·
**Value:** `<S|R|G|F|U|C|Q|N>` · **Effort:** `<XS|S|M|MH|H|VH>`

## Status (REQUIRED)

*(delete)* The **single source of truth** for what is shipped / open / deferred /
blocked. The issue carries the lifecycle label; the per-phase truth lives here, so
there is no second copy to drift. One paragraph: the state of the world today and what
this plan changes.

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

| Phase | Effort | Verify | Status |
|---|---|---|---|
| **A** — short title | S | `make test` / `<x>test.loft` | Open |
| **B** — short title | M | `make probe` / `<name>.probe` | Blocked on A |

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
