# 9 — Canopy-first trees: the canopy partitions, the tree is derived

**Issue:** [`jjstwerff/crawler#9`](https://github.com/jjstwerff/crawler/issues/9) ·
**Value:** `G` · **Effort:** `H` · **Depends on:** plan #5 (geometry library)

## Status

**Active — T1–T3 done**, gated in `make test`. The design is settled enough to build against:
**[TREES.md](TREES.md)** is the document; this README is the phase tracker.

## Goal

A forest where each tree's shape is the *consequence* of its neighbours. Every hex at the
top of the canopy belongs to a trunk; that assignment determines how the trunk grows, where
its main branches go, and how far it leans. **A normal mesh tree is one that never had
neighbours to fight for sunlight with.**

## Why this is a sibling of plan #5, not a phase of it

It shares the substrate **completely** — same hexes, chunks, levels, cache, `Heights`,
materials (TREES.md §2) — and differs completely in two ways:

- **Derivation direction.** Plan #5 authors a *form* and derives a *field*. This authors
  the *field* and derives the *form*.
- **Rendering model.** Houses are surfaces all the way down. A canopy is filled with
  semi-filled cards carrying pre-drawn branches and leaves; only trunk and major branches
  are meshes.

So plan #5 stays the geometry library, and this is its first consumer that is not
architecture.

## Phases

| phase | deliverable | state |
|---|---|---|
| **T1** | `Labels` + the argmax partition | **DONE** — `src/canopytest.loft` |
| **T2** | crown profiles + canopy height (base *and* top) | **DONE** — `src/canopyvoltest.loft` |
| **T3** | lean + trunk placement | **DONE** — `src/canopyleantest.loft` |
| **T4** | `Skeleton` + constrained shortest-path derivation | |
| **T5** | pipe-model radii + the mesh/card split | |
| **T6** | relaxation to convergence | |
| **T7** | levels: canopy over understory | |
| **T8** | object/field split below the resolution floor | |
| **T9** | branch-aligned cards | |
| **T10** | opacity calibration (I-OPACITY) | |

**T4, T6 and T10 are the real work.** T1–T3 are mostly reuse.

## The one idea to keep hold of

Shinozaki's **pipe model** — stem cross-section is proportional to the leaf area it
supports. Canopy-first makes that computable, so `d_trunk ∝ √cells`, and da Vinci's rule
falls out as conservation of the partition rather than being imposed. It is what makes this
a *derivation* instead of a plausible-looking generator, and it is also what fixes the
mesh/card threshold without an artistic choice.

## Open questions

Carried in [TREES.md §8](TREES.md). Case B has now been **run and printed** (TREES.md §3)
— it contradicted the design's predicted crown ordering, and the measured numbers are
awaiting confirmation. The one that blocks work beyond T5 is whether relaxation needs a
proven fixed point or a fixed iteration count.
