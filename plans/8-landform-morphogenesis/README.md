# 8 — Landform morphogenesis: uniform hexes → real landforms, in the fixture format

**Issue:** [`jjstwerff/crawler#8`](https://github.com/jjstwerff/crawler/issues/8) ·
**Value:** `G` · **Effort:** `H`

## Status

**Future — nothing built.** This README is the draft to argue with, not a settled plan.
Every piece it composes exists and is gated; what is missing is the transform layer.

## Goal

A **system of terrain transforms** that takes a *uniform* set of hexes and models them
into hexes that read as a real landform — mountains into an alpine range, rivers into
coastlines, hills into cliffs — driven by the water-flow/height and (later) town routines
we already have.

## The architecture — the fixture format IS the contract

The load-bearing idea: **the transforms consume and produce the same hex-map format that
the OSM/DEM importer produces** (plan #1's fixture). That format is already shared by the
importer, the renderer, and the classifier:

```
Overland: h    (height, real metres)      mat  (material / terrain kind)
          flow (0..5 neighbour index, -1) acc  (flow accumulation)
```

Because input and output are the same schema, four things fall out for free:

1. **Real and synthetic are interchangeable.** `plans/1-.../data/ortler_hexes.npz` (real
   Ortler) and a generated range are the same kind of object — so the real range is a
   drop-in **reference**, not an analogy.
2. **The verification instrument already exists.** `tools/overland_blueprint.py` renders
   that format, and plan #1 already fed it real arrays. Plan #1's **two same-scale
   drawings** (real vs model) become this plan's acceptance test directly.
3. **Uniform input is expressible.** "A uniform plane of mountains" is just a starting
   array in the same schema — so a transform is a function `hexmap → hexmap`, testable in
   isolation with a trivial seed state.
4. **It is a batch transform, not a pointwise sampler.** This is the important
   consequence: because we generate a *whole window of hexes*, iterative processes
   (erosion passes, accumulation relaxation, coastal retreat) **are available** — they
   are deterministic per `(seed, window)`, the same contract plan #2's
   `gen_chunk(seed, tier, cx, cz)` already keeps. The determinism constraint is on the
   *window*, not on each cell, so this does **not** have to be a closed-form
   `ov_sample(x, y)`.

That last point is what makes the whole family tractable, and it is the thing to confirm
first (Q1).

## The gap — relief is placed, not carved

`ov_sample` builds height as a **p-norm soft-max of placed bumps**: each `OvPeak`
contributes `op_amp` over `op_rad`, each `OvRidge` an along-axis profile sagged by
`or_sadl`, combined as `vp = vp + pow(m, 5.0)` and resolved with `pow(vp, 0.2)`, plus
ridge fbm. That yields *mountains* but not a *range*: no through-going valleys, no
divides between catchments, no passes, and settlement placing against generic slope.

Real landforms are the **residue of a process**. Valleys are removed material; ridges are
what was not removed. The same is true of the other two families below.

## Transform families

Each family is the same shape — a uniform/simple input, an already-defined driver, a
structural output — which is why they belong in one plan rather than three.

### F1 — mountains → an alpine range *(the driver: flow + height)*

Accumulation incises: high-flow cells cut down, neighbours relax toward them, and what
survives between two catchments **is** the divide. Passes are saddles on those divides.
Then the existing `OvTown`/`ov_roads`/`K_FIELD` routines settle the valleys the process
created, instead of placing against undifferentiated slope. Alpine character proper
(U-shaped troughs, hanging tributaries, cirques) is a later refinement on top of the
fluvial network.

### F2 — rivers → coastlines *(the driver: the same drainage)*

A coast is where the drainage meets base level, and its shape is drainage-derived:
drowned valleys become inlets/rias, interfluves become headlands, and sediment from
high-`acc` mouths builds deltas and spits. So a coastline should be **read off the same
flow field** rather than drawn as an independent curve. `OvSide` already carries an
estuary funnel (`os_ws` taper, `os_w`), which is the seed of exactly this.

### F3 — hills → cliffs *(the driver: height + the shipped talus model)*

Steep ground strips to bedrock and sheds rubble downslope; the stripped face is `K_FACE`,
the pile is `K_SCREE`. The mechanism already **shipped** as plan #2's neighbour-coupled
talus model (`src/talus.loft`, `talustest` in `make test`). What is unresolved is *what
makes a face a face* — the bare 50° threshold over-produces (~80% face on the steepest
chunk).

> **F3 overlaps plan #1's open cliff work and must not fork it.** Plan #1 owns the
> question "is `K_FACE` the right vocabulary / does it need splitting"; this plan owns
> "what transform produces faces from hills". Settle the predicate once, in #1, and
> consume it here. Cross-link both ways before starting F3.

## Anchors

- `tools/overland_blueprint.py` — the instrument: `Overland` (`:114`), the fed-array hook
  (`:166`), `material_contest` (the `ov_sample` kind twin), `flow`/`acc` derivation
  (`:186–203`).
- `src/overland.loft` — `OvPeak`/`OvRidge` (`:118`/`:126`), `OvSide` drainage
  (`os_acc`/`os_bed`/`os_w`/`os_ws`, `:107`), `ov_flow` (`:188`), `OvTown.ot_fld`
  (`:138`), `ov_roads`, `K_FIELD` (`:38`), confluence swamps.
- `src/overlandtest.loft` — the **I1/I2/I3 gate this plan must keep green**.
- `src/talus.loft` — `flow_accumulate` (`:102`) + the shipped talus model (F3's driver).
- `OVERLAND.md` §12–13 — the wilderness contract.
- Plan **#1** — the fixture format, the real references, the two-drawings method, and
  the cliff-face predicate F3 depends on. **F2/F3 have no ground truth until #1's
  flexible region-fixture work lands a coastal region** (Wales) — see
  `plans/1-ortler-worldgen-fixture/region-fixtures.md`.
- Plan **#2** — the LOD machinery; I-LOD (a detail chunk aggregates to its overworld
  parent) must survive whatever this plan does to the coarse field.

## Blueprint gate

Exact-invariant work, so CLAUDE.md's design/debug protocol governs: **plot the concrete
end-result first**. Step 1 of every family is one specific plotted instance — for F1, a
single seed's massif before and after, with the divide and one pass marked — agreed
*before* any code. Workshop is Python in this directory, as in plans #1 and #2; the loft
port follows a pinned invariant, never precedes it.

## Phases (draft — argue with these)

| Phase | Effort | Verify | Status |
|---|---|---|---|
| **P0** — confirm the architecture: uniform-hexmap seed in the fixture schema, round-trips through the renderer | S | a uniform plane renders; real Ortler still renders | Open — **first** |
| **P1** — plot the F1 target: one seed, before/after, divide + pass marked; agree the predicates for "reads as a range" | S | user sign-off on the plot | Blocked on P0 |
| **P2** — determinism pin: which passes are deterministic per `(seed, window)`, and how windows agree at their seams | M | seam round-trip probe | Blocked on P0 |
| **P3** — F1 carve prototype in Python: incision + divide extraction + passes | M | plotted vs P1's target | Blocked on P1, P2 |
| **P4** — F1 loft port into the overland | M | `overlandtest` I1/I2/I3 green + golden diff | Blocked on P3 |
| **P5** — settlement answers the terrain (towns/roads/fields read valley floors) | M | `make test` + a plotted valley | Blocked on P4 |
| **P6** — F2 coastlines from the drainage | M | plot vs a real coast fixture | Blocked on P3 + **#1** coastal fixture |
| **P7** — F3 hills → cliffs, consuming #1's face predicate | M | `talustest` + plot | Blocked on **#1** |
| **P8** — glacial character (U-troughs, hanging tributaries, cirques) | M | plot vs the Ortler fixture | Blocked on P4 |

## Open design questions

1. **Confirm the batch-transform framing.** Is the overland free to be generated as a
   window-sized array and cached, rather than sampled pointwise per hex? `sim_travel`
   regenerates windows on revisit and plan #2 already generates per chunk, so the answer
   is probably yes — but it decides whether iterative erosion is allowed at all, so it is
   **P0/P2, not an afterthought**.
2. **Window seams.** If carving is iterative over a window, two adjacent windows must
   still agree on shared edges (plan #2's I-SEAM, one tier up). Options: derive from a
   larger halo, or make the carve a function of already-global objects (the river
   polylines). This is the hardest invariant in the plan.
3. **What is the acceptance test for "resembles the Alps"?** We are generating a *fantasy*
   range, not reproducing the Ortler, so a per-cell diff is the wrong target — and plan #1
   already ruled κ out for fine-tier work. Likely **structural predicates** (every
   catchment has one trunk; divides are connected; passes exist and are traversable;
   valley floors are flatter than walls) plus a **cold-read recognition test** on the
   plot, in the draw-skill sense.
4. **Do divides become first-class objects?** Making a divide explicit (as `OvSide` is for
   rivers) would let passes, arêtes and catchment identity hang off it — at the cost of
   another `OVERLAND.md` contract.
5. **Does settlement feed back into height?** A pass carrying a road may deserve to
   widen; fields may flatten a valley floor. That is a second inversion — probably its
   own phase, possibly its own plan.

## Risks

- **Seam agreement is the real constraint, not the aesthetics.** Iterative processes are
  what make this family work and are exactly what threatens window-local regeneration and
  the plan #2 LOD contract. Pin it in P2 before building anything on it.
- **The I1/I2/I3 gate must not be weakened to fit.** If a transform breaks a wilderness
  invariant, the transform is wrong — not the invariant.
- **Do not tune toward a screenshot.** The trap plan #1's falsified `slope → cliff`
  premise already fell into: pick the invariant, then look.
- **F3 must not fork #1's cliff work.** One predicate, decided once.

## See also

- Plan **#1** (fixture format, Ortler reference, cliff-face predicate) ·
  Plan **#2** (LOD machinery, `src/talus.loft`, I-SEAM/I-LOD).
- `OVERLAND.md` §12–13 · `DESIGN-PROTOCOL.md` (why the plot comes first).
