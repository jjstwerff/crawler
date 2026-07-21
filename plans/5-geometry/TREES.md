# Canopy-first trees — design

**Status: DESIGN ONLY. Nothing built.** Step 1 of the design protocol is a concrete
plotted end-result, agreed before any code. §3 proposes one; it needs confirming or
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
*derivation direction* is not. What does **not** change is the substrate: §2.

## 2. One grid — trees live where houses live

The canopy is **not a separate world**. It uses the same hexes, the same chunks, the same
level key and the same cache as everything else in this plan. That is the whole reason a
forest can meet a village at all, and it belongs before the tree-specific machinery because
it constrains all of it.

Concretely, what sharing the grid buys:

- **A canopy over a building is the bridge case (§10).** Crowns and rooftops occupy the same
  cells at different **levels**, so they never arbitrate — the mechanism that lets a road
  cross a railway lets a branch overhang a roof. Nothing new required.
- **Buildings compete for the canopy.** A wall or roof holding a cell is just another
  claimant in the argmax of I-CROWN, so a tree beside a house grows away from it and an
  avenue closes over a street — with no special case for architecture anywhere.
- **One `sight_clear` crosses both.** A ray leaving a window accumulates wall opacity and
  then leaf opacity. Sight, sound and light already read materials, and a leaf is a
  material (§9).
- **One cache.** Canopy regions are `FieldCache` entries keyed `(chunk, level, version)`
  like everything else, so a forest pays the same residency policy as a town, and felling a
  tree invalidates by the same rule as moving a wall (§8, §10).
- **One height stack.** Terrain, stair treads, roof heights and canopy base/top are all
  `Heights` at their level — a tree on a terraced hillside needs no reconciliation code.

So the tree-specific parts are **additions to this field, not a parallel system**: a
`Labels` field beside `Heights`, and a `Skeleton` hanging off it. If any part of the design
below appears to want its own grid, that is a sign it is wrong.

## 3. The concrete end-result (PROPOSED — confirm or correct)

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
- trunk diameters satisfy `d ∝ √(cells)` (pipe model, §4);
- no branch path of C passes through a cell owned by A.

**Open**: the exact numbers depend on the crown profile and the weighting, which §3 fixes
but does not yet calibrate. Do you want to plot the expected partition for Case B yourself,
or should the first implementation print it for you to correct?

## 4. The invariants

These are the exact statements; everything else is tuning.

### I-PART — the partition is a total function, and order-free
Every canopy cell belongs to **exactly one** trunk. `Σ|C_t| = |canopy|`, no cell counted
twice, no cell unowned. Assigning the trees in any order gives the identical partition.
(The same property gated for surfaces in §P3 — and it comes free if the rule is an
`argmax`, because `max` is commutative.)

### I-CROWN — the canopy is a max of crown profiles
```
   top(cell)    = max over trees of  crown_t(cell)
   owner(cell)  = argmax over trees of  crown_t(cell)
```
This is **exactly the groin-vault operator** (§15) with N inputs instead of 2. The canopy
is a max-combination of profiles; the partition is its argmax. So it inherits every
property already gated — determinism, order-independence, and drainage.

`crown_t` is one of the profiles already built: a dome, a cone, or a paraboloid, centred on
the trunk, scaled by vigour. **No new geometry.**

### I-VOLUME — a canopy is an INTERVAL, not a surface
A roof is a surface: one z per cell. A canopy is **occupied space** — it has a base as well
as a top, and it is rendered by filling that space (§6). So a canopy cell carries
`(crown_base, crown_top)`, not a single height.

That needs no new structure: it is two `Heights` fields, exactly the floor/soffit pair the
arch work already used (§13). But it does mean **`roof_ponds` and the drainage invariant do
not apply** — they are statements about a surface. The canopy's equivalent invariant is
I-OPACITY below.

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

### I-OPACITY — what you see is what the field reports
The canopy is drawn as semi-filled cards (§6) and *also* queried by `sight_clear`, which
reads a material opacity. Those two must agree:

```
   rendered card coverage along a ray  ==  the opacity the L2 field reports for that ray
```

Verifiable by ray-marching the cards and comparing against `sight_clear` on the same
segment. Without it a canopy looks solid but does not block sight, or blocks sight while
looking sparse — and the bug is invisible in either layer alone, which is exactly the class
of failure this plan has been catching all along (§10's bridge, §14's silent eave).

This replaces drainage as the canopy's correctness invariant.

### I-LEAN — the lean is the centroid offset, and it is bounded
```
   lean_t = centroid(C_t) − trunk_t
```
Zero for an isolated tree (Case A). Non-zero and directed away from competitors when
crowded. Bounded by crown radius — a trunk cannot lean outside the crown it carries.

## 5. What is reused, and what is new

Most of it is reuse — §2 is why. That is the point of having built the rest first.

| need | already exists |
|---|---|
| the grid, chunks, levels, cache | unchanged; a canopy is a level over the same hexes (§2) |
|---|---|
| canopy top AND base | two `Heights` fields — the floor/soffit pair from arches (§13) |
| crown profiles | `dome` / `roof_cone` / the profile×distance table (§15) |
| max-combination + argmax | the groin-vault operator (§15) |
| multi-source competition | the boundary BFS in `roof_hip` (§13), with trunks as sources |
| light / occlusion | `sight_clear` (§9) — cast to the sky through canopy opacity |
| canopy vs understory | **levels** (§10) — canopy at level 1, understory at level 0 |
| region caching | `FieldCache`, already keyed by level (§10) |
| "too small to be a field" | the resolution floor (§12) — a sapling is an OBJECT |
| card art (branch sprays) | `tools/draw.py` + the `draw` skill, transparent ground |

**Genuinely new, and the whole cost of this work:**

1. **`Labels`** — a per-cell integer field (owner id), the sibling of `Heights`. Trivial.
2. **`Skeleton`** — nodes, parent links, radius, the first *graph* in the system.
3. **The skeleton derivation** — a shortest-path tree from trunk to every crown cell,
   constrained to the tree's own cells (I-NOTRESPASS), then contracted so that a run of
   collinear nodes becomes one branch segment. Contraction is the same idea as the 2D
   matcher (§P2): recover runs, do not emit per-cell geometry.
4. **Relaxation** — crown extent affects height affects competition. This is iterative and
   needs a convergence criterion. **The main open risk in this design.**

## 6. How it is drawn — and why that changes the design

Trees are **not** rendered like houses. A house is surfaces all the way down: recover the
form, emit geometry. A tree is two representations at once:

```
   trunk + major branches   ->  MESH        (few, thick, load-bearing)
   everything above them    ->  semi-filled CARDS with pre-drawn branches and leaves
```

This is not a rendering detail bolted on at the end. It reaches back into the design in
three ways.

### The mesh/card threshold is derived, not chosen

The temptation is to pick "mesh the first three orders of branching" by eye. I-PIPE makes
it computable instead: a branch's diameter is `∝ √(cells supported)`, so

```
   mesh while   cells_supported ≥ N      card below it
```

and `N` follows from the pixel size a branch would occupy — mesh it while it is thick
enough to read as a solid, card it once it is not. **The artist picks a visual threshold;
the geometry picks which branches meet it.**

That makes this the third derived representation change in the plan, and they are worth
seeing together — none of them is a tuning knob:

| threshold | where | rule |
|---|---|---|
| resolution floor | spiral stairs (§12) | `r_inner < √3/2π` → an object, not a field |
| slope ceiling | domes (§15) | `|dz/dr| > 1` → a wall, not a roof |
| **pipe threshold** | trees (here) | `cells_supported < N` → a card, not a mesh |

### Cards are branch-aligned, not camera-facing

A card carries a *pre-drawn branch* with its leaves, so it cannot spin to face the camera —
the branch on it would swing with it. Each card is anchored to a terminal skeleton node and
**oriented by that node's branch direction**, which T4 already produces. Camera-facing is
only admissible for the most distant LOD, where the card no longer depicts a branch but a
blob of foliage.

This is a real constraint on T4: the skeleton must yield usable *directions* at its
terminals, not merely connectivity. A shortest-path tree that zig-zags cell-to-cell would
give jittering cards, so terminal runs must be contracted and smoothed — the same
recover-runs-don't-emit-per-cell discipline as the 2D matcher (§P2).

### Card fill is calibrated against the opacity the physics already uses

How many cards, and how transparent? Not by eye: I-OPACITY fixes it. Fill the crown volume
until ray-marched coverage matches the opacity `sight_clear` reports for the same ray.
Then a canopy that *looks* dense *is* dense to sight, sound and light — which matters
because `sight_clear` is what decides suppression of understory trees (T7), so a
miscalibrated canopy would feed a wrong answer back into the simulation.

### The cards inherit the partition for free

A card hangs off a branch; a branch may not trespass into a rival's canopy (I-NOTRESPASS);
therefore no tree's foliage strays into its neighbour's crown. **The crowded-tree asymmetry
appears in the foliage automatically**, without any card-level rule — which is the whole
argument for deriving structure before drawing it.

### Where the card art comes from

The cards are 2D sprites: a branch spray with leaves, on transparent ground. That is
exactly what `tools/draw.py` and the `draw` skill already produce (`Background
transparent`, the `Fronds` primitive for linear natural marks). So the canopy texture set is
authored through the existing sprite pipeline, not a new one — and the sprite QA rules
(cold-read recognisability, `.draw` sources kept in-repo as a technique library) apply
unchanged. Worth confirming: a handful of species-typical sprays, or a generic set tinted
per species?

## 7. Phases

| phase | deliverable | gate |
|---|---|---|
| **T1** | `Labels` + the argmax partition | Case A exactly: bisector boundary, equal counts, zero lean, order-free over 24 tree orderings |
| **T2** | crown profiles + canopy height | canopy = max of profiles; pond-free; drainage as for roofs |
| **T3** | lean + trunk placement | Case B: signs and ordering of the lean vectors; lean bounded by crown radius |
| **T4** | `Skeleton` + shortest-path derivation | I-REACH on every cell; I-NOTRESPASS with a negative control (a deliberately trespassing route must be caught) |
| **T5** | pipe-model radii + the mesh/card split | `d ∝ √cells` at the trunk; `Σ child² = parent²` at every node to float tolerance; the split falls out of `cells_supported ≥ N` |
| **T6** | relaxation to convergence | fixed point reached; identical from two different starting states |
| **T7** | levels: canopy over understory | an understory tree is a distinct level; `sight_clear` to the sky decides suppression |
| **T8** | object/field split | a crown below the resolution floor is emitted as an object, not a field |
| **T9** | branch-aligned cards | terminal directions are smooth (no per-cell jitter); no card leaves its own crown, by I-NOTRESPASS |
| **T10** | opacity calibration | I-OPACITY: ray-marched card coverage matches `sight_clear` on the same segment, with a negative control (a deliberately sparse canopy must fail it) |

T1–T2 are cheap and reuse almost everything. **T4, T6 and T10 are the real work** — the
skeleton derivation, the relaxation loop, and making the drawn density agree with the
simulated one. T9 depends on T4 producing smooth terminal directions, which is a
requirement on T4 that only the rendering model reveals — worth knowing before T4 is
written rather than after.

## 8. Open questions

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
5. **Card art**: a handful of species-typical branch sprays, or one generic set tinted per
   species? (§6)
6. **Mesh threshold `N`**: pick it from a target on-screen branch thickness, or fix it as a
   crown-cell count and let apparent thickness follow? The first is more directly about how
   it looks; the second is resolution-independent.
7. **Scope**: is this plan #5's, or its own plan? The answer is now clearer than when this
   doc was started. It shares the **substrate completely** (§2 — same hexes, chunks, levels,
   cache, heights, materials), and differs completely in **derivation direction** (§1) and
   **rendering model** (§6). That is the shape of a *sibling plan consuming #5's library*,
   not a fork of it and not a phase inside it: #5 stays the geometry library, trees become
   its first consumer that is not architecture. Recommend a separate issue + directory,
   with #5 listed as a dependency — but it is your call.
