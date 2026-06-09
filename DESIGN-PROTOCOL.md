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
end-result far better than any abstract spec, hint, or invariant.** So the fast path:

1. **Plot the concrete end-result first** — the exact target output/state for *one specific
   input*. (User plots it, or I propose a candidate end-state and we confirm/correct it.)
2. **Name the invariant** read off that example (caching → *round-trip = identity*;
   geometry → the exact construction; store-lifetime → bindings reproduced faithfully).
3. **Pin a test** — the concrete example is the first case.
4. **Then** implement. Anchor (Angband systems / real-world form / moros mesh) + reuse one
   model across contexts by symmetry; thin tuning layer last.

**The tell that this went wrong:** *a small fix behind a large discovery cost.*

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
  one-triangle-wide wall). A Python prototype + corner tests then verified it in **one pass**.
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
- *(accumulate more before generalizing further)*

## Skill target

Once the mechanism is confirmed across more cases, fold into a skill: **detect an
exact-invariant domain → demand / plot a concrete end-result → name the invariant → pin a
test → build.** Likely an update to / companion of the engineering-rigor skill.
