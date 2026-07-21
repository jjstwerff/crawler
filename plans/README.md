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
