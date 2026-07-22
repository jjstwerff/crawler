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

### Case A — two equal trees, the degenerate check  — **BUILT, T1**

Split in two once the prototype ran: an isolated pair tests the *field*, an overlapping
pair tests the *competition*, and conflating them hides both.

Trunks are stated in **lattice coordinates** `(k, m)`, not world floats — see I-EXACT.

**A1, isolated** (`k = ±12`, `R² = 36`, crowns disjoint). Measured:
```
   counts 37 / 37 · contested 0 · lean A (0,0) · lean B (0,0)
```
The lean is the integer **0**, not a small float. That is the point of I-EXACT.

**A2, overlapping** (`k = ±8`, `R² = 64`). Measured:
```
   counts 83 / 80 · contested 3 · won outright 80 / 80
   lean A (−42, 0)   lean B (+42, 0)
```
- the tie set is **exactly the bisector column** `k = 0` (0 contested cells off it);
- outright wins are exactly equal, and `|C_A| − contested = |C_B|`;
- both trees lean **away** from the rival by exactly equal and opposite amounts.

The original draft of this case predicted "centroid equals trunk, no lean". That was wrong:
two *overlapping* equal crowns necessarily lean apart, and only the isolated pair has zero
lean. The prototype caught it before any loft was written.

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

### I-EXACT — the partition is integer arithmetic, not floating point
Every cell centre is at `(k·√3/2, m/2)` with `k, m` integers, so a trunk placed **on the
lattice** has an exactly representable squared distance:

```
   q2 = 3·Δk² + Δm²          (= 4·d², an exact integer)
```

A **paraboloid** crown `z = P·(1 − d²/R²)` depends on `d²` rather than `d`, so with
`D = 4R²` the whole comparison stays integral:

```
   z_A > z_B   ⟺   P_A·(D_A − q2_A)·D_B  >  P_B·(D_B − q2_B)·D_A
```

**This is why the crown profile is a paraboloid** — not merely because it is the usual
allometric choice, but because a cone or a dome needs `√(d²)` and drops the whole partition
back into floating point. That settles open question 2 (§8) on its own.

It is load-bearing, not tidiness. The first prototype used floats, and a crown boundary
passes *exactly* through cell centres: rounding admitted one cell while rejecting its mirror
image, giving an **isolated** tree a spurious lean of a third of a cell. In exact arithmetic
that lean is `0`.

### I-EXACT — the partition is integer arithmetic, not floating point
Every cell centre is at `(k·√3/2, m/2)` with `k, m` integers, so a trunk placed **on the
lattice** has an exactly representable squared distance:

```
   q2 = 3·Δk² + Δm²          (= 4·d², an exact integer)
```

A **paraboloid** crown `z = P·(1 − d²/R²)` depends on `d²` rather than `d`, so with
`D = 4R²` the whole comparison stays integral:

```
   z_A > z_B   ⟺   P_A·(D_A − q2_A)·D_B  >  P_B·(D_B − q2_B)·D_A
```

**This is why the crown profile is a paraboloid** — not merely because it is the usual
allometric choice, but because a cone or a dome needs `√(d²)` and drops the whole partition
back into floating point. That settles open question 2 (§8) on its own.

It is load-bearing, not tidiness. The first prototype used floats, and a crown boundary
passes *exactly* through cell centres: rounding admitted one cell while rejecting its mirror
image, giving an **isolated** tree a spurious lean of a third of a cell. In exact arithmetic
that lean is `0`.

A consequence worth knowing: exact ties need an exact algebraic coincidence, so two
*differently shaped* crowns essentially never contest a cell. Contests are a phenomenon of
**equal or commensurate** rivals — which is why A3 above has to construct one deliberately.

### I-PART — the partition is a total function, and order-free
Every canopy cell belongs to **exactly one** trunk. `Σ|C_t| = |canopy|`, no cell counted
twice, no cell unowned. Assigning the trees in any order gives the identical partition.
(The same property gated for surfaces in §P3 — and it comes free if the rule is an
`argmax`, because `max` is commutative.)

**Contested cells go to the biggest tree, and its size is derived from the hexes it already
holds** — a bigger crown overtops a smaller one and shades it out. That makes the rule
self-referential (the partition sets the sizes; the sizes settle the partition), so it runs
in two passes: assign the uncontested cells and mark the contests, size each tree from its
*uncontested* cells, then award each contest to the largest of the trees tied there.

Sizing from uncontested cells only is what keeps pass 2 order-free — a size counting
already-awarded contests would depend on the sweep order. **This is the T6 relaxation
problem in miniature**, and it is much better met here at two passes than first met at
fixed-point scale.

Only when the tied trees are *also* the same size does the stable id decide. Under exact
symmetry that is a genuine coin flip which has to land somewhere, and it is why the
symmetric pair is the degenerate case: the one scene where the physical rule has nothing to
say. Symmetric quantities must therefore be measured on the **uncontested** set — comparing
raw counts compares the tie-break as much as the competition.

**Contested cells are an output, not an internal detail.** The hex lattice is
mirror-symmetric about a cell-centre column (`k → −k` preserves `k ≡ r mod 2`), so a
symmetric pair of trees *always* produces an exact tie column — it is a property of the
scene, not a rounding artefact. Ties go to the lowest **stable id** so the partition stays
total, but that attribution is arbitrary, so **every symmetric quantity must be measured on
the uncontested set**. Comparing raw counts compares the tie rule as much as the
competition. Downstream (T9's interleaved foliage) needs the contested set anyway.

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

### I-VOLUME — a canopy is an INTERVAL, not a surface  — **BUILT, T2**
A roof is a surface: one z per cell. A canopy is **occupied space** — it has a base as well
as a top, and it is rendered by filling that space (§6). So a canopy cell carries
`(crown_base, crown_top)`, not a single height.

That needs no new structure: it is two `Heights` fields, exactly the floor/soffit pair the
arch work already used (§13). But it does mean **`roof_ponds` and the drainage invariant do
not apply** — they are statements about a surface. The canopy's equivalent invariant is
I-OPACITY below.

**The base is derived, not authored.** "Height to live crown" is a forestry quantity driven
by competition — a crowded tree self-prunes the lower branches its neighbours have shaded —
and T1's partition already measures competition:

```
   shade_t = 1 − won_t / potential_t        potential = what it would hold alone
   bole_t  = H_t · shade_t · BOLE_MAX
   top     = bole_t + (H_t − bole_t)·u      u = 1 − q2/D_t
   base    = bole_t
```

At the crown edge `u = 0`, so `top == base` and the crown closes exactly. At the trunk
`u = 1`, so `top == H_t`. Measured against increasing competition:

```
   rivals reaching it   won/potential   bole    crown depth
   0                        85/85       0.00       10.00
   1                        80/85       0.47        9.53
   2                        75/85       0.94        9.06
   4                        53/85       3.01        6.99
```

Monotone, with one parameter (a max-bole ratio), and it reproduces the forestry result:
**forest-grown trees have long clean boles, open-grown ones branch to the ground.** The
tree's full height is untouched throughout — crowding raises the base, it does not stunt.

The crown does *not* taper to zero at the last cell: an "edge" cell is one with a neighbour
outside, and a neighbour is `√3` away, so an edge cell can sit a full neighbour-distance
inside the true radius. The bound is `H·(1 − (R−√3)²/R²)` = 3.86 here, measured 2.50. **The
crown closes at the true boundary, which falls between cells.**

**The circularity is deliberate and unresolved.** The partition competes on the *potential*
profile; the realized crown is derived from the outcome. Feeding realized crowns back in is
T6, and this is the second place the same shape has appeared — the first being T1's
contested-cell rule. Gated meanwhile: no non-owner's realized crown outtops the owner
anywhere (0 cells), so the two are consistent for now.

### I-PIPE — structure is derived, not chosen  — **BUILT, T5**
Shinozaki's pipe model: the cross-sectional area of a stem is proportional to the leaf area
it supports. Canopy-first makes that directly computable:

```
   branch cross-section  ∝  number of canopy cells it supports
   trunk area            ∝  |C_t|          ->   d_t ∝ √|C_t|
```

Da Vinci's rule (`Σ child² = parent²`) is then **not an extra rule** — it is conservation
of the partition, restated. This is what makes canopy-first a *derivation* rather than a
plausible-looking generator, and it is the single most important idea in this document.

T5 sharpened it. T4 gives `load(parent) = 1 + Σ child loads`, so with area ∝ load:

```
   area(parent) = area(its own cell) + Σ child areas       exact, 0 violations
```

and da Vinci's familiar form is *that with the node's own foliage dropped*:

```
   Σ(child²)/parent² = (load − 1)/load        0.99 at load 100,  0.50 at load 2
```

Measured: thin forks (load ≤ 4) reach 0.75, thick ones (load ≥ 20) reach 0.986. **So da
Vinci's rule is asymptotically exact on thick branches and wrong in the twigs — by exactly
one cell's worth.** That is what real trees do, and the discrete form says precisely how far
off it is rather than leaving it as a modelling fudge.

Measured trunk radii: A 69 cells → 0.498, B 80 → 0.537, C 31 → 0.334, with the A/C ratio
equal to `√(69/31)` to 1e-15. A crowded tree carries less crown, so it grows a thinner
trunk — derived, not tuned (85/76/67 cells → 0.553/0.523/0.491).

### The mesh/card split, and a caveat on scale
The artist names the thinnest radius worth drawing as a solid; the geometry picks which
branches meet it — `N = (r_min/k)²`:

```
   r_min 0.12  ->  load ≥ 4   ->  18 of 69 nodes meshed
   r_min 0.20  ->  load ≥ 11  ->   5 of 69
   r_min 0.30  ->  load ≥ 25  ->   1 of 69
```

**The meshed part is always a connected subtree containing the root**, and that is a
theorem, not an enforcement: `load(parent) = 1 + Σ child loads > load(child)`, so load falls
strictly away from the root and *any* threshold on it selects such a subtree. Given a
negative control — corrupt one tip's load and the check fires.

**Caveat:** at 69 cells a crown is coarsely resolved, so a realistic `r_min` leaves only the
trunk meshed. That is consistent with the intent (trunk and major branches only), but it
means the mesh set's size is governed by crown *resolution* as much as by `r_min`. A
forest-scale crown with far more cells would mesh proportionally more. Worth knowing before
tuning `r_min` against a screenshot.

### I-REACH — a crown is connected to its own trunk, through itself  — **BUILT, T4**
Every cell in `C_t` has a path to trunk `t` using only cells of `C_t`. A crown disconnected
from its trunk is a rendering artefact with no physical meaning.

### I-NOTRESPASS — a branch may not pass through another tree's canopy  — **BUILT, T4**
The strong form of I-REACH, and the one that makes crowded forests look right. It is also
what forces branches to route *around* competitors, which is where the characteristic
asymmetry of a crowded tree comes from.

**Both hold by construction** — the search never leaves the label — so **both got a negative
control**, because a check that cannot fire proves nothing:

```
   move one node onto a rival's cell   -> trespass reports 1        ✓ fires
   let a rival slice 8 cells across a crown -> 61 cells, 42 reached  ✓ fires
```

The trespass check is what will protect the invariant once a later phase starts moving
nodes off their cells, so its control matters more than the invariant's current triviality
suggests.

Measured on Case B's scene: A 69 nodes / 69 cells (11 forks, 22 tips, 33 branches), B 80/80,
C 31/31. Load conservation — `load == 1 + Σ children` — holds at **every** node, not just
the root, which is the pipe model's input: T5 has only to take a square root of it.

### Contraction, and a caveat for T9
A per-cell path on a hex grid can step in only **six** directions, so cards hung on raw path
nodes would snap between six angles and jitter as the crown changed. Contracting each run
between forks into one segment lifts that to **9 of 36** ten-degree bins here.

That is better than six but **not by much**, because segments between forks are short. The
fix proposed here — contracting *through* forks along the dominant-load child — **was tried
at T9 and does not work** (8 bins against 8). See §13 for what did.

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

### I-LEAN — the lean is the centroid offset, and its bound is a theorem  — **BUILT, T3**
```
   lean_t = centroid(C_t) − trunk_t
```
Zero for an isolated tree — exactly zero, by I-EXACT. Non-zero and directed away from
competitors when crowded, growing monotonically with them.

**The bound needs no enforcement.** Every owned cell lies within `R` of the trunk (that is
what the crown test *is*), and a centroid of points inside a disc is inside that disc, so
`|lean| < R` always. "A trunk cannot lean outside the crown it carries" is not a clamp to
apply, it is a fact that cannot be violated. Gated at four crowding levels.

**The trunk takes out part of the lean, and the branches carry the rest.** A tree leans
toward its crown's centre of mass because that is the load it stands under, but the roots
anchor the base, so it cannot get all the way there:

```
   trunk_top = root + α·lean          residual = (1−α)·|lean|
```

At `α = 1` the tree is perfectly balanced and the branches have nothing to correct; at
`α = 0.6` a lean of 0.80 leaves 0.32 for the branches. **That residual is why T4's branch
structure comes out unequal on a crowded tree** — the asymmetry is inherited, not
generated.

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
4. ~~**Relaxation**~~ — **BUILT, T6.** Crown extent affects height affects competition, and
   the feedback is positive, so it does not obviously settle. The risk turned out to be
   answerable rather than merely survivable — see below.

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
| **T6** | relaxation to convergence | **DONE** — fixed point in 2–8 iterations; identical heights *and* label field from three very different starts |
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
2. ~~**Crown profile**: paraboloid, cone or dome?~~ **ANSWERED by T1** — the paraboloid,
   decisively: it is the only one of the three that depends on `d²` rather than `d`, so it
   alone keeps the partition in exact integer arithmetic (I-EXACT). The other two would
   reintroduce the rounding asymmetry T1 was built to remove.
3. ~~**Relaxation**: fixed iteration count or a proven fixed point?~~ **ANSWERED by T6 —
   neither was needed.** I-EXACT makes heights integers, so the state space is **finite**,
   so a deterministic map on it must reach a fixed point or enter a cycle. Both are
   detectable by remembering the states visited, so **termination is detected rather than
   assumed** and the caller is told which of `FIXED` / `CYCLE` / `BUDGET` happened. No
   convergence proof required, and no arbitrary iteration count. A direct payoff from the
   exact-arithmetic decision made in T1.
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


## 9. T6 — what relaxation actually does

The loop is: partition → measure crowns → set heights from them → partition again. The
feedback is positive (more crown → taller → more crown), which is precisely the shape that
need not settle.

**Termination is detected, not assumed.** I-EXACT keeps heights integral, so the state
space is finite and a deterministic map on it must reach a fixed point or cycle. Recording
the visited states catches either, and the caller gets `FIXED` / `CYCLE` / `BUDGET` rather
than a number and a hope. Measured: fixed points everywhere tried, never a cycle.

**The fixed point belongs to the scene, not to the starting state.** Case B from three very
different starts:

```
   start 200/200/120  ->  FIXED after 2   ->  124 / 177 / 95
   start  50/ 50/ 50  ->  FIXED after 2   ->  124 / 177 / 95
   start 400/ 20/300  ->  FIXED after 3   ->  124 / 177 / 95
```

identical heights **and** identical label fields (0 cells differing). Had that failed, the
"fixed point" would have been an artefact of where we started and the whole derivation
arbitrary.

**Competitive exclusion falls out.** Five trees packed 9 apart with `R = 8`:

```
   182 / 11 / 164 / 11 / 182       FIXED after 8
```

The flanked trees collapse to near nothing while the outer pair, each with an open side,
keep their height — and the stand stays exactly mirror-symmetric. Suppression is coded
nowhere; it is what the partition plus the pipe model do when trees are too close.

It also amplifies the T3 finding: at Case B's fixed point B is 43% taller than A, because A
is pressed by two rivals and B by one. The relaxation does not merely preserve that
asymmetry, it compounds it — which is why measuring it before relaxing (T3) and after (T6)
gives different-looking answers to the same question.


## 10. T7 — light, and the understory as a level

Two halves, both mostly reuse.

**Levels are plan #5's, unchanged.** The canopy sits at level 1 and the understory at level
0; they share cells and never arbitrate, exactly as a road crosses a railway. Gated the way
the bridge was: the canopy field is **bit-identical** whether or not an understory exists
beneath it (0 cells differing), and the two levels take distinct cache slots.

**Light needed one new routine, and only one.** `sight_clear` answers whether a ray crosses
a *barrier* — an edge carrying an opaque material. A canopy is not a barrier, it is a
**volume**: a cell is occupied between `base` and `top`, and a ray is stopped by passing
*through* that interval. So `canopy_blocks` is the volumetric counterpart, walking the same
0.2 units under a 0.866 inradius, reusing `hex_at` unchanged.

What comes out is the **sky fraction**, and that one number decides the understory:

```
   beneath a crown        0.00
   in the gap between     0.42
   out in the open        1.00
```

**Forest-gap regeneration is not scripted.** A seedling in the gap sees 42% of the sky
against 0% under a crown, so it grows away while the shaded one stays a seedling (understory
crowns 37 vs 33 cells). That is the whole mechanism by which a fallen tree lets the next
generation up, and it is nowhere written down as a rule.

Climbing gains light monotonically, and the sweep was extended past the crown top so it
actually shows the transition (`0` at z=1…16, `1` at z=21) rather than reading zero
throughout and passing on all-zeros — a vacuous gate caught and fixed.

**Negative control:** the same point with the canopy removed returns 1.00, so the shade
measured was the canopy's and nothing else's.

## 11. Two questions asked of the model: shrubs, and wind

Both probed rather than argued. Neither needs a new model; both need one reinterpretation.

### Shrubs — yes, by treating multi-stemmed growth as internal competition

A shrub differs from a tree in one structural way: it is **multi-stemmed**, with no dominant
trunk, and the skeleton (T4) is rooted at exactly one cell. The reinterpretation is to model
a shrub as **several trees at adjacent cells** — and then the shrub's own stems compete for
its crown, which is what multi-stemmed growth *is*. Measured, three stems two cells apart at
`R = 4`:

```
   crowns   12 / 11 / 10          (total 33)
   boles    1.35 / 1.35 / 1.75    the flanked stem is the most drawn up
   radii    0.208 / 0.199 / 0.190
   at r_min 0.12:  2 of 12 nodes meshed — a shrub is nearly all cards
```

Everything downstream works unchanged: each stem gets a skeleton, the pipe model sizes it,
and the mesh/card split correctly leaves a shrub almost entirely carded, which matches the
rendering intent. The flanked stem being the most drawn up is the T2 bole rule doing exactly
what it does for forest trees, one scale down.

**The limit is the resolution floor** (plan #5 §12): a shrub whose crown is a couple of
cells has nothing to partition, and belongs on the other side of that boundary as an
**object**. Shrub-as-field starts where the crown is worth several cells; below it, a mesh
or a card, as for a sapling.

### Wind — yes, at three points, and two of them already exist

1. **Drag per cell** is foliage density: `canopy_depth × leaf density`. `canopy_depth`
   exists (T2).
2. **Shelter** is `canopy_blocks` accumulating instead of stopping — the ray walk exists
   (T7), only the accumulate-vs-stop change is new.
3. **Trunk sizing gains a second constraint, and this is the interesting one.** The pipe
   model sizes a stem for *water transport*: area ∝ leaf area, so `d ∝ √load`. Wind sizes it
   for *bending*: the moment is crown area × height, resisted by the section modulus ∝ `d³`.
   A real tree is sized by whichever binds, and on an exposed site wind governs — which is
   why exposed trees are stubby and thick. So `radius = max(pipe, wind)`, and that predicts
   the right thing rather than needing a rule for it.

Measured on a five-tree shelterbelt, crown top 20:

```
   z  1.0 … 8.5   wind passes UNDERNEATH the belt
   z 11.0 … 18.5  intercepted
   z 21.0         passes over
```

The belt intercepts only between its crown base (10.54) and its top — which is correct, and
more useful than it looks. The **interior** belt trees have a bole of 10.54 against 5.27 for
the end trees: the belt's own competition draws its interior stems up, and **that destroys
its shelter at ground level**. That is the classic shelterbelt design failure — plant it
dense and you get tall clean stems and a wind tunnel underneath — and it emerges from T2's
bole rule with nothing added.

**Deeper integration, not yet designed:** wind would also enter the *partition* as a
directional penalty (windward abrasion shapes the crown) and the *lean* as a directional
term (flag trees on exposed sites). Both are additions to existing steps rather than new
machinery, but neither is specified here.


## 12. T8 — where a crown stops being a field

Plan #5 found two boundaries of the field model: a **resolution floor** (a spiral stair too
tight to lay one tread) and a **slope ceiling** (a dome too steep to carry as a height). A
canopy has its own floor, and finding it sharply matters, because below it the entire
canopy-first apparatus produces nothing a billboard would not.

**The criterion is structural, not a cell count.** A crown is worth deriving when its
skeleton has branch structure — at least one **fork** below the root. Every node at depth 1
is a direct child of the trunk, so a fork needs depth ≥ 2: the crown must reach **two cells
out**. A neighbour is `√3` away, so

```
   FIELD  when  R > 2√3 = 3.464          OBJECT below it
```

Swept across ten radii, the fork test and the analytic bound agree at **every** one — 0
disagreements. Either side of it:

```
   R = 2.65   7 cells,  0 forks, depth 1,  2 distinct loads   -> a star of twigs
   R = 3.61  19 cells,  4 forks, depth 2,  5 distinct loads, 16 branches
```

Below the floor the field does not say *less*, it says **nothing**: one depth, two distinct
loads, no fork to hang a branch on, and a pipe model with no gradient to compute. The right
emission there is a single object — one card or one small mesh, as for a sapling.

**It classifies what a crown holds, not what it was declared with.** A tree given a nominal
`R = 7`, well above the floor, but hemmed in until it holds 7 cells, is classified an
object. That is the only form of the test that stays meaningful after relaxation has
redistributed everything.

### The four derived representation changes

None of these is a tuning knob; each falls out of the lattice or the physics:

| where | rule | crossing means |
|---|---|---|
| plan #5, spiral stairs | `r_inner < √3/2π` | object, not field |
| plan #5, domes | `\|dz/dr\| > 1` | wall, not roof |
| plan #9, crowns | `R < 2√3` | object, not field |
| plan #9, branches | `load < (r_min/k)²` | card, not mesh |


## 13. T9 — cards, and a wrong diagnosis corrected

T4 measured 9 of 36 heading bins and proposed contracting *through* forks along the
dominant-load child. **That does not work.** Measured on one crown's 81 cards:

```
   fork-cut segment endpoints                    8 of 36 bins
   dominant-child axis endpoints                 8
   card, local parent-to-child step, jittered   21
   card, outward from the trunk, cell centres   32
   card, outward from the trunk, jittered       34
```

The limit was never the lattice — point-to-point vectors spanning 8 cells already cover all
36 bins — and never the contraction. **It was the basis.** A *segment* basis has only a
couple of dozen short segments to draw headings from, so whatever way you cut the path, the
headings cluster on the six directions the grid steps in. An **outward** basis has a heading
per *cell*, because every cell sits at its own angle from the trunk.

It is also the truer description: a card carries a **spray**, and a spray points outward.
The last path step is not what is drawn on it.

Sub-cell placement is kept — it adds 2 bins and gives foliage the irregularity it should
have, deterministically hashed so the same world renders the same tree — but **it is not the
fix**, and an earlier draft of this gate asserted that it was, with a "negative control"
resting on a false premise. Corrected before it shipped.

**The rest of T9 is inherited rather than built.** Cards obey I-NOTRESPASS with no
card-level rule (0 stray), because a card hangs off a branch and a branch never leaves its
own crown — so the crowded-tree asymmetry appears in the foliage for free. Every card sits
inside its cell's canopy interval (0 outside), sized by the canopy depth there
(1.40 … 18.24). Mesh and cards partition the skeleton exactly (7 + 81 = 88).


## 14. T10 — I-OPACITY, and a defect it found in T4

The canopy is **drawn** as a stack of semi-filled cards and **simulated** as a volume that
sight, light and sound cross. Those are two computations of the same physical thing, and a
disagreement is invisible from inside either layer — the canopy looks dense while being
transparent, or the reverse. It matters causally too: `sight_clear` decides understory
suppression (T7), so a miscalibrated canopy feeds a wrong answer back into the simulation.

Beer-Lambert gives the field side, `T = exp(−k·L)`; the cards give the product of their
transparencies. With one card per cell the two agree when

```
   k = −c·ln(1−a)          c = cards met per unit of canopy path
```

**`c` is measured, not chosen** — it is a property of the grid and the layout. Measured
`c = 0.655` against a geometric expectation of `1/√3 = 0.577`, and the calibration then
holds across four alphas with a worst disagreement of **0.018**. Negative control: keep half
the cards and the two transmittances diverge by **7.5×**, so the agreement was measured
rather than assumed.

### Limitation: c is not constant per ray

`c` ranges 0.46 to 0.97 — a spread of 0.78 about the mean. That is real geometry, not noise:
how many cells a ray meets depends on how it threads the lattice, and a ray grazing corners
meets more than one per nominal spacing. **So the calibration holds on average and not per
ray.** For sight, light and sound averaged over many rays that is fine; a single sight line
carries up to ~40% error in optical depth, and a consumer needing one ray exact must
integrate the volume rather than count cards.

### The defect: T4's major branches are six straight spokes

The first version of this gate cast rays *through* the trunk and measured `N = 0` against
`L = 19`. The ray was not at fault. **BFS shortest paths in a hex disc all route along the
lattice's six directions**, so the load concentrates there — and the mesh threshold, which
selects on load, therefore selects six perfectly straight radial spokes:

```
   of 14 meshed cells, 14 lie within 10° of a lattice axis
   worst deviation: 7e-15 degrees
```

That is the **most visible part of the tree** — the meshed part — and it is a grid artefact,
not a botanical structure. Real major branches do not align to six compass points.

**Cause:** BFS resolves ties by neighbour iteration order, which systematically prefers the
straight radial path. **Fix:** build a least-cost tree (Dijkstra) with a small deterministic
per-cell cost jitter, so paths meander. That is a change to **T4** and it ripples through T5
(loads move, so radii move), T9 (card/mesh membership moves) and T10 (`c` shifts).

It is **asserted in the gate** rather than merely written down, so it cannot be silently
lost — and so that fixing it will visibly break the assertion, which is the point.


## 15. The spoke fix, and the whorl budget

Two changes, and they turn out to be one.

**Least-cost growth instead of BFS.** A breadth-first tree ties constantly, and resolving
those ties by neighbour order sends every shortest path straight down a lattice direction.
Giving each cell a small deterministic cost makes the cheapest path meander, and the ties
disappear.

**A branch budget per height band.** A real tree cannot put an unlimited number of branches
at one height — they come in whorls, a few per season, and further branches form only
*later*, which means higher up as the leader extends. So each band of `WHORL_DZ` carries a
budget of `WHORL_MAX`, and once spent a new branch must attach in another band.

The second is what finishes the first: with six candidate directions and a budget of four,
some branches must be deferred to another whorl, so they **stagger instead of radiating**.

```
   busiest height band:   no limit 11 branches · limit 4 -> 5 · limit 2 -> 3
   meshed branches on-axis:  was 14 of 14 (deviation 7e-15) -> now 10 of 20, worst 30°
```

30° is the maximum possible deviation — exactly between two axes. A uniformly spread crown
would put about a third of its cells within 10° of some axis; the meshed set is now at half,
down from all.

**The budget is a preference, not a hard cap.** It is exceeded by exactly one where a crown
cell's *only* attached neighbour would have to fork. That ordering is deliberate: **I-REACH
outranks the whorl rule**, because a crown disconnected from its trunk is meaningless while
an extra branch in a band is merely untidy.

### What the render then showed

With the branches drawn rather than hidden under the crown, the spokes are visibly gone —
and the next problem is visible instead. **The skeleton is a plan-view structure.** Its
nodes are cells; the z given to each is a decoration applied afterwards, so the branches
follow the crown *surface* and the tree reads as a spider rather than a tree: no vertical
trunk, branches drooping outward like legs.

The whorl model is exactly what supplies the missing z. A branch attaches to the **trunk
axis** at its whorl height and runs outward to the canopy surface at its tip — so branch
geometry should interpolate from `(trunk_x, trunk_y, z_whorl)` to the crown surface, rather
than lying flat at the local canopy height. That is the next change, and it is the one that
turns a correct structure into a believable one.


## 16. Placing the skeleton in 3D

The skeleton is a **plan-view topology** — it says what connects to what, not where anything
sits vertically. Laying every node at its local canopy height made branches follow the crown
*surface*, and the tree read as a spider. Height is a **placement** decision, so it lives in
the geometry layer and the skeleton stays pure topology.

**Where a branch leaves the trunk** was the whole question. Deriving it from the branch's own
reach put every branch at one height — an isolated crown is round, so every first-order
branch reaches about the same distance and they all landed in a single plate. The growth
story gives the answer instead:

> a branch's **load is its age**, because it has been accumulating crown since it formed —
> so the heaviest branch is the oldest, formed when the tree was shortest, and sits **lowest**.

The whorl budget is what stopped them all forming at once to begin with, so the two rules
compose. Branch heights now spread from `0.22H` to `0.86H` by load rank, and each branch
runs from the trunk axis out to the canopy surface at its tip.

### The trunk only appears on a forest tree

Rendering the subject alone gave a giant green dome with no visible trunk — and that is the
model being **right**, not wrong. An isolated tree has `bole = 0`, so its crown reaches the
ground; open-grown trees do branch to the ground and read as bushes. Give it neighbours and
competition raises the crown base:

```
   isolated:   bole 0.00 wu  — crown to the ground
   4 rivals:   bole 7.27 wu = 6.30 m — a clean bole, and a tree
```

So the T2 forestry result is not merely gated, it is **visible**: you cannot draw a
forest-tree trunk without a forest. Total height 12.1 m against the 1.75 m figure reads
correctly.

**Still crude:** the crown is the bare analytic paraboloid — an umbrella — because the cards
that carry foliage are not rendered yet. That is T9's output and the next thing to draw.


## 17. The foliage cards, drawn

T9's cards are now rendered: one quad per card, its plane containing the **outward** heading
and the vertical, so the branch spray printed on it lies in the plane — which is exactly why
that heading could never be camera-facing. Each is crossed with a second quad, the standard
cross-card, because a single plane never reads as foliage from every angle.

The tree now reads: trunk, branches visible through gaps in the mass, foliage above, figure
at the base. Everything in it is derived — the partition sets the crown, competition sets
the bole, the pipe model sets every radius, the whorl budget sets where branches form, and
the cards hang off the branches that resulted.

### The flat crown, fixed

The first foliage render gave a **disc**: one card per cell placed near the middle of its
interval, and once competition raises the bole that interval is shallow, so the whole crown
collapsed into a plate.

**Not one card per cell.** The count follows the canopy **depth** — one per `CARD_DZ` of
interval, capped at `CARD_MAX` — and each spreads through its own slice rather than
clustering at the middle. One rule fixes the silhouette and the physics together, because
T10 calibrates on cards met per unit of canopy *path*: a deep interval must carry
proportionally more of them than a shallow one. 40 cards became 216 on the same tree, and
the crown reads as a rounded canopy with volume.

It also repaired the T10 **negative control**, which had quietly stopped proving anything.
It thinned the canopy by dropping every other *card* — but with several cards per cell,
nearly every cell still carried one, so it compared two almost identical fields (ratio
1.3×). Thinned by **cell** instead, which is what a ray actually sees, it separates them by
28×. A control that survives a change to the thing it controls is not a control.
