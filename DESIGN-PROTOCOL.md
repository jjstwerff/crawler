# DESIGN-PROTOCOL.md — reaching the correct design fast (case log → mechanism → skill)

A **living log** of design/debug episodes where the path to the *correct* design was slow,
what finally unblocked it, and the suspected mechanism. The goal is to **accumulate enough
cases to extract the actual mechanism** and fold it into a **skill** (likely updating the
engineering-rigor skill). The concise protocol lives in `CLAUDE.md` and the
`exact-invariant-verify-first` memory; **this doc is the evidence + the study.**

> How to use: when a design/debug takes much longer than its eventual fix, add a case
> below using the template. Periodically re-derive the *Mechanisms* section from the cases.

## Working hypothesis (current best)

For **exact-invariant** problems — **geometry · caching/serialization · hashing ·
store/memory-lifetime · protocols** — the correct design already exists as an *invariant*;
it is **not an open design space**. And the model (Claude) **grasps a concrete, plotted
end-result far better than any abstract spec, hint, or invariant.**

### The Blueprint phase — suss out the design via verifiable steps, *before* implementing

The failure shared by every case below is the same shape: jumping from *candidate design*
straight to *implementation*, then paying the cost in debugging. The fix is a distinct
**blueprint phase** — work the design out through a chain of **verifiable steps**, and do
**not** write the real code until each load-bearing step checks out. The blueprint phase is
the design-mode twin of the rigor skill's *"build the instrument before you act"*; its steps
are **constructive** (build *toward* the answer, e.g. a prototype that produces the plotted
end-result), which composes with — and usually precedes — the skill's *falsification probes*.

1. **Plot the concrete end-result first** — the exact target output/state for *one specific
   input*. (User plots it, or I propose a candidate end-state and we confirm/correct it.)
   This is the first verifiable step and the single strongest unblock.
2. **Name the invariant** read off that example (caching → *round-trip = identity*;
   geometry → the exact construction; store-lifetime → bindings reproduced faithfully).
3. **Decompose into verifiable steps + pin each.** Break the blueprint into its few
   load-bearing claims; give each the cheapest check that *confirms* it — a throwaway
   prototype that produces the plotted end-result, corner tests, a round-trip probe, a
   render→PNG. The concrete example is the first pinned case. **Gate: don't implement the
   real thing until the blueprint's steps verify.**
4. **Then** implement against the verified blueprint. Anchor (Angband systems / real-world
   form / moros mesh) + reuse one model across contexts by symmetry; thin tuning layer last.

**The tell that this went wrong:** *a small fix behind a large discovery cost* — there was a
cheap blueprint step you skipped.

## Case log

### Case 1 — triangle-wall straightener (crawler, see WALLS.md)
- **Domain:** geometry (exact construction).
- **Described first as:** goal + hints — "no line is straight," "eliminate every other
  wall," "**exact, not an approximation**," "**logic not angles**," "my algorithm," "read
  the moros walls implementation."
- **How the model struggled:** ~8 failed *approximations* (Douglas–Peucker ε, PCA line-fit
  + intersection, angle-bucket run/wobble, midpoint moving-average) — wavy sides / wrong
  vertex counts. It kept trying to *derive* the construction from outcome-constraints.
- **What unblocked it:** the user gave the **concrete model** — subdivide each hex into
  triangles (each edge → 3 sub-segments), then *eliminate the full triangles inside or
  outside the line; keep the band* — then refined to the **plotted end-result** (a thin
  one-triangle-wide wall). The construction was only *pinpointed* after a **Python verify
  phase** (prototype + corner tests) — *then* ported to loft. That ordering (cheap-medium
  verify pins the design; the real port comes after — **not jumping the gun**) is the method,
  not a detour.
- **Mechanism (hypothesis):** the model can't reliably reverse-engineer an exact geometric
  construction from outcome-constraints; given the construction / a plotted end-result it
  lands immediately. Approximation is the failure mode it reaches for when the construction
  is withheld.
- **Cost:** the bulk of a long session's wall thread, for a ~50-line algorithm.

### Case 2 — loft2 `data.rs` startup-cache abstraction (loft#290 → e2315c0)
- **Domain:** caching / serialization / store-lifetime.
- **Described first as:** a *symptom* — `store.rs:473` "Incomplete record", flaky,
  build-state-dependent; `main_vector<T>` stores not freed.
- **How the model struggled:** symptom-chased the store desync across manifestations
  (keys.rs OOB, "Incomplete record", cold-vs-cache builds) without converging on the cause.
- **What unblocked it:** the user **plotted the concrete end-result** — the exact target
  store/cache state after a round-trip — *even more specifically than the triangle case*.
  The invariant then read out cleanly: *the startup-cache round-trip must reproduce every
  binding identically, including the synthetic vector/tuple/fn wrappers* → fix: stamp them
  `source=0` so `rebuild_indices` recreates the global `(name,0)` binding.
- **Mechanism (hypothesis):** for caching/serialization the model defaults to chasing the
  *failure* rather than stating the *round-trip-identity invariant*; the plotted concrete
  end-state makes the invariant unavoidable.
- **Cost:** a one-line fix behind a large discovery cost.

## Case template (append new chases)

```
### Case N — <name> (<project/file/issue>)
- Domain:
- Described first as:
- How the model struggled:
- What unblocked it:
- Mechanism (hypothesis):
- Cost:
```

## Mechanisms (running synthesis — mine this for the skill)

- The model **derives poorly from outcome-constraints** on exact-invariant problems; it
  **comprehends from a concrete instance of the answer**. (Both cases.)
- Default failure modes: **approximation** (geometry) and **symptom-chasing** (caching) —
  both are "iterating toward an answer that already exists exactly."
- The unblock is consistently a **concrete plotted end-result**, and the *specificity*
  needed scales with difficulty (caching needed more than walls).
- **The unifying frame is a *missing blueprint phase*:** the cost is paid whenever the design
  jumps straight to implementation under-verified, then gets debugged. A blueprint of
  **verifiable steps** front-loads that same cost, cheaply.
- **Verify in the cheapest medium, before the real implementation — and don't jump the gun.**
  The wall construction was only *pinpointed* by a **Python verify phase** (prototype + corner
  tests), *then* ported to loft; the caching design by the plotted store state. The cheap
  prototype is where the design gets **pinned down**, not merely confirmed — so the verify
  phase is a *prerequisite*, not a check-after. **Constructive** verification (a prototype that
  *produces* the plotted end-result) is the strongest step; it precedes/composes with
  falsification probes.
- *(accumulate more before generalizing further)*

## Skill target — enhance the engineering-rigor skill's DESIGN column

The skill already carries the two-mode loop (DEBUG / DESIGN) but has **no explicit blueprint
phase**. Enhance the DESIGN column with one: between *"problem + candidate design"* and
*"build the chokepoint every site derives from"*, insert **suss out the design via verifiable
steps → a verified blueprint**, gated by *don't implement until it verifies*. Fold in:

- **Concrete end-result first** as step 1 — the strongest unblock; specificity scales with
  difficulty.
- **Constructive verifiable steps** — a throwaway prototype in the *cheapest medium* (Python
  for geometry, a round-trip test for caching) that **produces** the plotted end-result —
  alongside the skill's existing *falsification probes*. "Not jumping the gun": the cheap-medium
  verify is a **prerequisite**, and is often where the design gets *pinned*, not just confirmed.
- The gate is the design-mode form of the skill's *"build the instrument — it is your eyes."*

The skill lives in the loft repos (`loft*/.claude/skills/engineering-rigor/SKILL.md`) — it's a
**loft-side artifact, so coordinate with the user before editing it**; this doc is staged input.
