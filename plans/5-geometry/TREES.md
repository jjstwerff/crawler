# Canopy-first trees — design

**Status: DESIGN ONLY. Nothing built.** Step 1 of the design protocol is a concrete
plotted end-result, agreed before any code. §2 proposes one; it needs confirming or
correcting before implementation starts.

---

## 1. Why nothing in this plan can do this

Every mechanism built so far runs the same direction:

```
   author a FORM  ->  derive the FIELD
   (cone, ridge, way, arch)      (cells, edges, heights)
```

A canopy-first tree runs backwards:

```
   the FIELD is primary  ->  derive the FORM
   (which hex belongs to which trunk)   (trunk position, lean, branches)
```

The closest precedent is the roof matcher (§14): read a height field back and recover the
shape. But that recovers a **known primitive** — a cone, a plane, a sphere — by fitting
four or five parameters. A tree skeleton is not a primitive. It is a *graph*, with a
variable number of nodes, and no amount of least-squares will produce one.

Three further things are genuinely new:

1. **Cells are contested.** Every footprint so far was stamped by one owner, and where two
   met we arbitrated by nearest-surface. A canopy is a *partition under competition* — the
   assignment is the interesting output, not a tie-break.
2. **The form is not centred on its field.** A crowded tree leans; its trunk sits away from
   its crown's centroid, and its branches are unequal. Nothing so far has had a form whose
   anchor is deliberately off-centre from the cells it owns.
3. **Structure must be *load-bearing*, not decorative.** A branch exists because it carries
   crown. That is a conservation law across a graph, and we have never had one.

This is the "different order" — correctly identified. The shapes are simple; the
*derivation direction* is not.

## 2. The concrete end-result (PROPOSED — confirm or correct)

Two cases. The first pins the machinery; the second is the one that matters.

### Case A — two equal trees, the degenerate check

Trunks at `(0,0)` and `(12,0)` in world units, identical vigour. Crowns are radially
symmetric, so:

```
        A                             B
        *  ·  ·  ·  · | ·  ·  ·  ·  *          | = the partition boundary
        ·  ·  ·  ·  · | ·  ·  ·  ·  ·
        ·  ·  ·  ·  · | ·  ·  ·  ·  ·
```

Exact expected output:
- the boundary is the **perpendicular bisector** `x = 6`, to within one cell;
- `|C_A| = |C_B|` exactly (equal crown cell counts);
- each crown's centroid **equals its own trunk** (no lean), to within a quantum;
- trunk diameters equal;
- every crown cell reaches its trunk through cells of its own tree.

If any of those is off, the competition step is wrong, and it is wrong in a way that will
be invisible once the scene is asymmetric.

### Case B — one suppressed neighbour, the real case

```
   A at (0,0)    vigour 6.0     open on three sides
   B at (9,0)    vigour 6.0     equal rival to the east
   C at (0,10)   vigour 3.0     weaker, north of A
```

Exact expected output:
- `|C_A| > |C_B| > |C_C|` — A is open on three sides, C is overtopped;
- C's crown centroid is displaced **+y, away from A** — C leans away from its competitor;
- A's centroid is displaced slightly **−x and −y**, away from both;
- trunk diameters satisfy `d ∝ √(cells)` (pipe model, §3);
- no branch path of C passes through a cell owned by A.

**Open**: the exact numbers depend on the crown profile and the weighting, which §3 fixes
but does not yet calibrate. Do you want to plot the expected partition for Case B yourself,
or should the first implementation print it for you to correct?

## 3. The invariants

These are the exact statements; everything else is tuning.

### I-PART — the partition is a total function, and order-free
Every canopy cell belongs to **exactly one** trunk. `Σ|C_t| = |canopy|`, no cell counted
twice, no cell unowned. Assigning the trees in any order gives the identical partition.
(The same property gated for surfaces in §P3 — and it comes free if the rule is an
`argmax`, because `max` is commutative.)

### I-CROWN — the canopy surface is a max of crown profiles
```
   height(cell) = max over trees of  crown_t(cell)
   owner(cell)  = argmax over trees of  crown_t(cell)
```
This is **exactly the groin-vault operator** (§15) with N inputs instead of 2. The canopy
is a max-combination of profiles; the partition is its argmax. So the surface inherits
every property already gated — determinism, order-independence, and drainage.

`crown_t` is one of the profiles already built: a dome, a cone, or a paraboloid, centred on
the trunk, scaled by vigour. **No new geometry.**

### I-PIPE — structure is derived, not chosen
Shinozaki's pipe model: the cross-sectional area of a stem is proportional to the leaf area
it supports. Canopy-first makes that directly computable:

```
   branch cross-section  ∝  number of canopy cells it supports
   trunk area            ∝  |C_t|          ->   d_t ∝ √|C_t|
```

Da Vinci's rule (`Σ child² = parent²`) is then **not an extra rule** — it is conservation
of the partition, restated. This is what makes canopy-first a *derivation* rather than a
plausible-looking generator, and it is the single most important idea in this document.

### I-REACH — a crown is connected to its own trunk, through itself
Every cell in `C_t` has a path to trunk `t` using only cells of `C_t`. A crown disconnected
from its trunk is a rendering artefact with no physical meaning.

### I-NOTRESPASS — a branch may not pass through another tree's canopy
The strong form of I-REACH, and the one that makes crowded forests look right. It is also
what forces branches to route *around* competitors, which is where the characteristic
asymmetry of a crowded tree comes from.

### I-LEAN — the lean is the centroid offset, and it is bounded
```
   lean_t = centroid(C_t) − trunk_t
```
Zero for an isolated tree (Case A). Non-zero and directed away from competitors when
crowded. Bounded by crown radius — a trunk cannot lean outside the crown it carries.

## 4. What is reused, and what is new

Most of it is reuse. That is the point of having built the rest first.

| need | already exists |
|---|---|
| per-cell canopy height | `Heights` (§11) |
| crown profiles | `dome` / `roof_cone` / the profile×distance table (§15) |
| max-combination + argmax | the groin-vault operator (§15) |
| multi-source competition | the boundary BFS in `roof_hip` (§13), with trunks as sources |
| light / occlusion | `sight_clear` (§9) — cast to the sky through canopy opacity |
| canopy vs understory | **levels** (§10) — canopy at level 1, understory at level 0 |
| region caching | `FieldCache`, already keyed by level (§10) |
| "too small to be a field" | the resolution floor (§12) — a sapling is an OBJECT |

**Genuinely new, and the whole cost of this work:**

1. **`Labels`** — a per-cell integer field (owner id), the sibling of `Heights`. Trivial.
2. **`Skeleton`** — nodes, parent links, radius, the first *graph* in the system.
3. **The skeleton derivation** — a shortest-path tree from trunk to every crown cell,
   constrained to the tree's own cells (I-NOTRESPASS), then contracted so that a run of
   collinear nodes becomes one branch segment. Contraction is the same idea as the 2D
   matcher (§P2): recover runs, do not emit per-cell geometry.
4. **Relaxation** — crown extent affects height affects competition. This is iterative and
   needs a convergence criterion. **The main open risk in this design.**

## 5. Phases

| phase | deliverable | gate |
|---|---|---|
| **T1** | `Labels` + the argmax partition | Case A exactly: bisector boundary, equal counts, zero lean, order-free over 24 tree orderings |
| **T2** | crown profiles + canopy height | canopy = max of profiles; pond-free; drainage as for roofs |
| **T3** | lean + trunk placement | Case B: signs and ordering of the lean vectors; lean bounded by crown radius |
| **T4** | `Skeleton` + shortest-path derivation | I-REACH on every cell; I-NOTRESPASS with a negative control (a deliberately trespassing route must be caught) |
| **T5** | pipe-model radii | `d ∝ √cells` at the trunk; `Σ child² = parent²` at every node to float tolerance |
| **T6** | relaxation to convergence | fixed point reached; identical from two different starting states |
| **T7** | levels: canopy over understory | an understory tree is a distinct level; `sight_clear` to the sky decides suppression |
| **T8** | object/field split | a crown below the resolution floor is emitted as an object, not a field |

T1–T2 are cheap and reuse almost everything. T4 and T6 are the real work.

## 6. Open questions

1. **The concrete end-result for Case B** — plot it, or have the first run print it for
   correction? (§2)
2. **Crown profile**: paraboloid, cone or dome? A paraboloid is the usual allometric
   choice; the other two are already built. Does the difference matter to you visually, or
   should we take whichever gates most cleanly?
3. **Relaxation**: is a fixed number of iterations acceptable (cheap, deterministic), or
   must it run to a proven fixed point (correct, and a convergence proof we do not yet
   have)?
4. **Species**: is one parameter set enough for now, or do you want species from the start
   (they change crown profile, shade tolerance and branching angle — and shade tolerance is
   what makes mixed forests interesting)?
5. **Scope**: is this plan #5's, or its own plan? It is a different order of thing, as you
   say — it may deserve its own issue and directory.
