# DESIGN-PROTOCOL.md — when to pivot to a mechanic that aids (case log → mechanism → skill)

A **living log** of design/debug episodes where the path to the *correct* design was slow,
what finally unblocked it, and the suspected mechanism. The goal is to **accumulate enough
cases to extract the actual mechanism** and fold it into a **skill** (likely updating the
engineering-rigor skill). The concise protocol lives in `CLAUDE.md` and the
`exact-invariant-verify-first` memory; **this doc is the evidence + the study.**

> How to use: when a design/debug takes much longer than its eventual fix, add a case
> below using the template. Periodically re-derive the *Mechanisms* section from the cases.

## What this is — *when to pivot to a mechanic that aids*, not *how*

The transferable skill is **not how we design or debug** — the *how* mostly follows the problem
at hand (geometry wants a geometric prototype, caching a round-trip test, a control-flow bug a
usage sentinel; those are interchangeable). It is **recognizing the moment to pivot from pushing
directly at the problem to building a *mechanic that aids us*** — a cheap secondary artifact that
gives sight or leverage the direct push can't: a throwaway prototype, a verify harness, a plotted
concrete end-result, an instrument / boundary matrix, a usage sentinel. The hard, transferable
part is the **pivot recognition** (the *triggers* below); the mechanic's construction is
problem-specific and the model handles it once it knows to pivot. **Jumping the gun = missing the
pivot.** Everything below — the blueprint phase, the cases — is in service of sharpening *when* to
pivot and *which class* of mechanic to reach for, never a fixed procedure.

## Working hypothesis (current best)

For **exact-invariant** problems — **geometry · caching/serialization · hashing ·
store/memory-lifetime · protocols** — the correct design already exists as an *invariant*;
it is **not an open design space**. And the model (Claude) **grasps a concrete, plotted
end-result far better than any abstract spec, hint, or invariant.**

### Triggers — decide you're in a blueprint problem *before* you start (else you'll skip it)

The phase only pays off entered **up front**, so the triggers must be cheap to check before
any code. Run a blueprint when **any** fire:

- **Domain.** The problem lives in an exact-invariant domain — **geometry / spatial
  construction, caching / serialization, hashing, store / memory-lifetime, protocol or
  encoding round-trips, numeric or byte-format exactness.** A single right answer exists →
  blueprint by default.
- **Phrasing (the user is telling you it's exact).** "*exact, not an approximation*," "*logic
  not angles / not X*," "*my algorithm*," "*read the \<source\> implementation*," "*it already
  exists / there's a known way*," or repeated "*no — like this*" corrections. The design is to
  be **recovered**, not invented.
- **Self / drift (you've already left the path).** You catch yourself **approximating**,
  **asking for more hints**, **re-explaining abstractly**, **symptom-chasing across
  manifestations**, or on **attempt ≥ 2** with the same class of miss — or you think *"I can't
  name the invariant / see the root yet."* Any one → **stop coding, start the blueprint.**
- **Stakes.** A **load-bearing** target (core representation, runtime, hot path, on-disk data)
  where *wrong-but-plausible* is expensive to unwind — or the change surface is **tiny but the
  cost-of-wrong is large** (the *small-fix / large-discovery* shape used as an **entry** signal,
  not just a postmortem).

**Anti-trigger (keep it light).** If none fire it's an **open design space** (taste /
tradeoffs, no exact invariant) — a full blueprint is overkill; iterate normally. The triggers
are what stop the blueprint phase from consuming the judgment it serves.

### The Blueprint phase — suss out the design via verifiable steps, *before* implementing

The failure shared by every case below is the same shape: jumping from *candidate design*
straight to *implementation*, then paying the cost in debugging. The fix is a distinct
**blueprint phase** — work the design out through a chain of **verifiable steps**, and do
**not** write the real code until each load-bearing step checks out. The blueprint phase is
the design-mode twin of the rigor skill's *"build the instrument before you act"*; its steps
are **constructive** (build *toward* the answer, e.g. a prototype that produces the plotted
end-result), which composes with — and usually precedes — the skill's *falsification probes*.
(This is the **design-mode pivot**; the four steps are its *typical shape*, not a fixed recipe —
the medium follows the problem. The skill is the pivot, not the steps.)

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

### Aiding mechanics — *what* we pivot to (the how follows the problem)

The pivot is the skill; the mechanic is whatever the problem affords. The recurring map:

| Problem shape | Mechanic we pivot to |
|---|---|
| Exact construction / geometry | a throwaway **prototype in a cheap medium** (Python + corner tests) that *produces* the plotted end-result |
| Caching / serialization / store-lifetime | a **round-trip test** + the **plotted target state** (round-trip = identity) |
| Renderer / *"I can't verify this"* | a **capture** (render → PNG) — challenge the can't-verify claim; it's usually false |
| A fault invisible in any one repro | an **instrument / boundary matrix** (vary one axis per probe) |
| *"Which code actually runs?"* | a **usage sentinel** (route uses through one loud chokepoint) |

The first two are *design-mode* pivots (this doc's cases); the last two are *debug-mode* and
already live in the engineering-rigor skill — same move, one level apart.

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

- **The skill is the *pivot*, not the procedure.** The hard, transferable part is *recognizing
  when* to stop pushing at the problem directly and build a **mechanic that aids** (prototype /
  verify harness / plotted end-result / instrument / sentinel); the mechanic's *how* follows the
  problem. Both failure modes below are the **same root — a missed pivot:** grinding on the
  problem when a cheap aiding mechanic was right there.
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

## Alignment with the engineering-rigor skill — *the missing generative half*

Checked against the skill + its DESIGN depth (`engineering-rigor/SKILL.md`;
`doc/claude/DESIGN_PROTOCOL.md` — "Design Protocol 1: A Design Is a Testable Hypothesis";
`DESIGN_VERIFICATION.md` C1). **Verdict: same skill, same core — this is the missing
*generative* half of the DESIGN column, not a competing frame.**

**Shared DNA (already there):** *build the instrument before you act — a sight discipline, not a
willpower one* **is** our "pivot to a mechanic that aids"; our **tell** (*small fix / large
discovery cost*) = their tell (*longer than expected for what it does*); our anti-trigger = their
*"keep it light — fires only when the tell trips on something load-bearing"*; our "pin a test /
verify before implementing" = their *"validate against the written prediction."* Their line
*"I can't name the invariant" = "it isn't a design yet — a pile of cases"* is **exactly our entry
condition.**

**Genuinely additive (verified absent in all three docs):**

1. **A second design failure mode — and the move out of it.** The existing DESIGN material is built
   around **over-reach** (the *clever* failure: elegant/false over-unification) and its mirror
   **under-reach** (the spray); its cure is **falsification** (probe each claim, attack the
   cleanest). But falsification *presupposes a candidate invariant to break*. Our cases are the
   other failure — **you can't form the right candidate at all**: you **approximate** (geometry) or
   **symptom-chase** (caching). The framework *names* this state ("a pile of cases") but only as a
   **stop sign**; it gives no generative move. We add it.
2. **A *constructive* instrument (vs the all-falsifying set).** Every existing instrument is
   diagnostic — matrix, falsification probes, usage sentinel, site-count. Ours is **constructive**:
   *plot a concrete instance of the **answer** + build the cheapest prototype that **produces** it,
   then read the invariant off it.* The generative counterpart that turns a pile of cases into a
   nameable invariant.
3. **"Build it" moves to the *front*.** Protocol 1 makes "build it" **step 5 — the last probe**
   (validation *after* naming + probing). For exact-construction problems the cheap build is
   **generative and goes first** — it's *how* the invariant gets named ("only pinpointable after
   the Python verify phase, *then* ported"). Same artifact, repositioned final → front for this class.
4. **The exact-invariant *domain* trigger.** The framework triggers on *load-bearing + the tell*; it
   has no notion that some **domains** (geometry / caching / serialization / hashing / store-lifetime
   / protocols) carry a **pre-existing exact invariant to *recover*** — so "iterate toward it" is the
   wrong mode *before any tell fires*. (Their verification question #6 "matched to the domain" is
   abstraction *width*, not this.)

**Apparent tension, resolved (extension, not clash):** the skill says *truth is in the class,
invisible in the instance* — beware acting on one instance. We say *get one concrete instance
first.* Split **which** instance: an instance of the **problem/symptom** is the trap (it hides the
class); an instance of the **answer/end-result** is the instrument (you read the invariant — hence
the class — *off* it). That distinction **extends** the skill's class/instance axis.

**Where it landed:** ✅ added to `doc/claude/DESIGN_PROTOCOL.md` (Protocol 1) — a new section
**"The other half — when you cannot form the invariant at all"** (the second failure mode + the
constructive instrument + the instance-of-problem vs instance-of-answer distinction + build-to-front),
the **exact-invariant domain trigger** in the protocol preamble, and a generative pointer in step 1.
*(loft branch `engine`, uncommitted — left for review; it's a loft-side artifact.)* **Optional
follow-ons, not yet done:** one DESIGN-column row in `SKILL.md` (*constructive instrument* beside the
falsifying probe) and a 7th C1 verification question in `DESIGN_VERIFICATION.md` (*is this an
exact-invariant domain whose answer I should recover, not approximate?*).
