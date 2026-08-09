# plans/ — crawler's plan structure

Crawler organizes multi-phase work the way **loft** does, so one convention spans every
repo in the org (`_PLAN_TEMPLATE`: *"every other subject builds its own plans to match
this shape in its own repo"*). This file is the **binding** — the conventions and where
crawler differs. The *method* it serves lives elsewhere and is not restated here:

- **DESIGN-PROTOCOL.md** — the blueprint phase (concrete plotted end-result → name the
  invariant → pin each step → only then code). This is crawler's equivalent of loft's
  composition-matrix discipline, and it is what a plan's phases should be *made of*.
- **CLAUDE.md** — branch/commit policy, and the bug-filing policy (crawler is a
  consumer; upstream defects go to FILING.md / LOFT-HANDOFF.md, never into a plan).

## The rule — docs vs plans

- A **reference doc** (`DESIGN.md`, `RENDER.md`, `BUNDLE.md`, `WALLS.md`, …) describes
  **how the thing works** — the durable truth, updated in place as the code changes.
- A **plan** describes **a change we intend to make** — phases, ordering, verification.
  It is temporary by nature: when a phase ships, its reference content **moves out** to
  the doc that owns it, and the plan keeps only the closure record.

If you cannot say what *changes* when the plan is done, it is a doc, not a plan.

## Pick the lightest workflow that fits

| Work shape | Path |
|---|---|
| **Bug fix** (one root cause, one commit) | Fix + a `src/<x>test.loft` case + commit. No plan, no row. |
| **Upstream (loft) defect** | LOFT-HANDOFF.md → file per FILING.md. **Never a crawler plan.** |
| **Tiny deliverable** (a sprite, a version bump) | Nothing, or one line in the relevant doc. |
| **Light TODO** *(the default)* | An `## Open work` section in the reference doc that owns the area. Same lifecycle as a plan, just one row — the row and the design share a file. |
| **Plan** | A directory here. Earns it only when the work is genuinely **multi-phase** *and* benefits from its own document space. Cap active plans at **2–3**. |

Most work is not a plan. A one-row TODO in `RENDER.md § Open work` beats a plan
directory that only points back at `RENDER.md`.

## Identity — the issue number, claimed first

A plan's identity is its **`jjstwerff/crawler` issue number**, not a local integer.

**Open the issue first, then name the directory after the number it returns.** Never
pick the number by scanning `plans/` — an unmerged branch may already hold that number,
and GitHub numbers are immutable, so a collision is expensive to unwind.

- Directory: `plans/<N>-<slug>/README.md` — **flat**. No `future/`, `finished/` or
  `deferred/` subdirectories: **lifecycle state is a label on the issue**, not a path.
- **Small plans live in the issue alone.** A directory is for work that needs a document
  space (phases, sub-files, a `probes/` dir). Issues #1 and #2 are plans with no
  directory, and that is correct.
- **No hand-maintained index here.** The overview is *derived* from the tracker:

```sh
gh issue list -R jjstwerff/crawler --label plan --state all        # every plan
gh issue list -R jjstwerff/crawler --label status:active           # what's in flight
```

`ROADMAP.md` stays the **synthesis** layer (the through-line to a playable game) and
`DESIGN.md §18a` stays the ordered backlog — neither is a plan index, and neither should
grow one.

## Labels

| Dimension | Values | Rule |
|---|---|---|
| kind | `plan` | on every plan issue (crawler's tracker also holds non-plan issues, so unlike loft's dedicated plans repo this label *does* partition) |
| status | `status:future` · `status:active` · `status:finished` · `status:declined` | **exactly one** |
| value | `val:S` `val:R` `val:G` `val:F` `val:U` `val:C` `val:Q` `val:N` | one, see below |

**A closed issue must carry `status:finished` or `status:declined` — never a live
status.** This drifts silently; when you touch a closed plan, check the label matches.

## The active roster — decided 2026-08-09

**`#11` 3D world · `#12` playthrough reach · `#13` scoped identity.** Everything else is
`status:future`; `#9`/`#10` are finished.

⚠ **"Active" means work is happening or is next — not that the plan is unfinished.** The
roster had drifted to **six** against this file's own cap of three, so it was decided from
evidence rather than intent: excluding doc edits, **no plan had been genuinely worked since
2026-07-23**. One paused thrust, and five slots held by things nobody was doing.

| | why active |
|---|---|
| **`#11`** | the declared direction (`CLAUDE.md`), 28 of the last 40 file touches, and `STATE.md`'s NEXT — paused mid-step at the wall fit |
| **`#12`** | small, `A0` shipped, and it makes the rest *verifiable* — a 3D world you cannot script-walk is one you cannot regression-test. It serves `#11` |
| **`#13`** | the only plan with an **external** deadline: moros plan 21 is finishing the other half of one mechanism now. `S1` is a cheap review that **expires** — unscheduled, it is effectively declined |

Each demotion says why in its own Status block, because a label with no reason gets
reverted by the next reader. The pattern worth naming: **`#5` was demoted although it is
neither done nor unimportant** — its live edge moved into `../hexbody` and `#11` P5 tracks
it, so holding both would double-count one body of work.

⚠ **A slot is a claim on attention, so freeing one is as much work as filling one.** Three
of the six were created on 2026-08-09 by the session that then had to cut them back.

## Value categories — what KIND of value

Same letters as loft, so the convention reads the same across repos; the examples are
crawler's. Read top-down and pick from the highest category with open work.

| Tag | Meaning | Crawler examples |
|---|---|---|
| **S** | **Silent failure / content corruption** — it "works" but the data is wrong, with no error. Highest priority: invisible, and it erodes trust fastest | the `JInteger` bundle-scanner zeroing, spawn-record corruption, a bundle that silently loses a monster |
| **R** | **Regression / gate-blocker** — `make test` or `make probe` red, or a toolchain bump that breaks the build | the 2026.7.2 upgrade arc |
| **G** | **Goal-enabling** — directly advances the playable game (DESIGN §3a pillars, ROADMAP's M-Core) | the core loop, progression, the theme-bundle game |
| **F** | **Foundation** — unblocks 2+ downstream plans | the games-kernel adoption, the geometry engine, library extraction |
| **U** | **Player experience** — feel, readability, controls, art coherence | sprite theme coherence, light/readability, input latency |
| **C** | **Clean features** — removes special cases; keeps the engine↔bundle seam honest | de-keying the engine from bundle content |
| **Q** | **Internal quality** — perf, refactor, cleanup with a clear payoff | mesh/caching perf, warning cleanups |
| **N** | **Niche / opportunistic** — small, low-priority | one-off tools, conveniences |

**Effort letters, never calendar time** — `XS / S / M / MH / H / VH`. "Two weeks" ships
in two days and "quick" takes weeks; effort buckets stay stable, projections don't.

## Files here

| File | Purpose |
|---|---|
| `_TEMPLATE.md` | the standard plan skeleton — copy to `<N>-<slug>/README.md` |
| `_INVESTIGATION_TEMPLATE.md` | for plans whose first phase is *characterize the problem*, not *design + build* |
| `_LIFECYCLE.md` | the close / defer checklist (including the link-rewrite step) |

**Length budget: 100–300 lines per plan README.** Longer means reference content is
leaking in — extract it to the doc that owns it.

## What a plan must carry (adopted from `../loft` and `../moros`, 2026-08-09)

Both siblings write plans the same way, and the three habits below are what make theirs
outlive the session that produced them. Crawler's template now requires all three.

1. **The title is a CLAIM.** *"Regions own the mapping: one byte is not one identity"*
   (moros 21), *"A hash insert that allocates once and never re-hashes"* (loft 135). A
   topic — *"region mappings"* — commits to nothing, and a plan that commits to nothing
   cannot be shown to be finished.
2. **Steps have STABLE IDS, and status is per step.** `A1`, `A1b`, `A2c`, `R1`. *"`A1`,
   `A1b` and `A2c`'s along half are shipped; `A2`–`A5` are designed, not built"* is a
   status you can check; *"in progress"* is not. ⚠ **"Designed, not built" is a
   first-class state** — it says the thinking survived even though the code has not been
   written, which is the point of a plan over a ticket. Such a step is **written out in
   full**: that is the step documentation of future work.
3. **Dated findings, one section per step — `What <step> turned up`.** loft 135 is mostly
   dated measurements; moros 21 has *"What `R1` turned up"*. ⚠ Include the ones that
   **refuted the step's own premise**, and the ones found on the way (loft 135: *"Found
   while measuring: growing a hash ABANDONS every previous bucket table"*).

⚠ **The third is the one crawler kept losing.** `plans/11-3d-world/RESULTS.md` has done
it since July — *"`P1` result — one passability predicate, measured 2026-07-22"* — and it
is the ONLY plan that does, because nothing told the next author to. Everywhere else the
numbers went into commit messages, where the next reader will not think to look.

Plus the fence: **`What this plan does NOT change`**, so a reader does not build on a
guarantee nobody made. `plans/12-playthrough-reach/` is the first plan written to the
full shape.

### And a doc that declares future work must name its plan — gated

⚠ **The plans were never the weak point.** Every `plans/<N>-*` directory has a tracker
issue; what nothing checked was the other direction — a design doc could say
`DESIGN SESSION` or carry a `## Staged epic` heading and sit outside the tracker
indefinitely. `SCRIPTING.md` did exactly that: 470 lines, no plan, no issue, and being
**spent piecemeal** (the item routine-by-id seam shipped straight out of its routine
table as a bug fix).

`tools/libcheck.py` **L9** now requires any root `*.md` carrying one of those markers to
name a plan — a local `plans/<N>-…` path, a `jjstwerff/crawler` issue link, or
`plan #<N>`. ⚠ `@PLN<N>` does **not** count: that is an upstream *loft* plan, and
accepting it is what let `SCRIPTING.md` pass on an `@PLN86` reference while having no
crawler plan at all.

**One doc, one owner.** Where a design belongs to an existing plan, LINK it both ways
rather than opening a number — `BUNDLE-MIGRATION.md` → plan #4, `STENCILS.md` and
`FORMS.md` → plan #5. The doc owns the design; the plan owns the schedule and the step
status, so progress is never recorded twice.
