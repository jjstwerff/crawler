# DRAWING — walls, towers, roads, and curves, by one rule

**Plan #11 P5.** How structure is drawn onto the hex field, and how its exact geometry is
recovered on the way to the renderer.

The design in one line: **a cell stores what it is, the type names the shape, and the shape's
parameters are fitted from the cells.** Nothing stores a centre or a radius.

## The principle

Every drawn thing — a wall, a tower, a road, a road's curve — is the same operation:

> mark the cells whose centre lies within `halfwidth` of a **geometry**, and write a **type**
> into them.

One rasterise rule for all of them, and it is exact on the integer lattice:

| geometry | a cell belongs when |
|---|---|
| segment `(x0,y0)–(x1,y1)` | `dist_to_segment(centre) <= halfwidth` |
| arc `(cx,cy,r,a0,a1)` | `abs(dist_to_centre - r) <= halfwidth` and the angle lies in `[a0,a1]` |

That the same rule serves a road and a tower is the point. What differs between them is the
**type** written into the cell, and the type is the only metadata that exists.

**Why a tower stops being a hexagon.** Today `stamp_round_tower` marks `hex_distance == rad`,
which is a hexagon at every size — hex-distance bands never overlap, so the shape can be
nothing else. The arc rule above admits *part* of a band and is genuinely round as it grows.
At `rad = 2` it selects the same 12 cells (the lattice is too coarse for anything else); at
`rad = 8` it does not, and that is exactly where today's version fails.

## Where this lives: the library owns it

Drawing a circle onto hexes and recovering it from hexes is **hex-pattern interpretation** —
the same job `form_circle`, `form_octagon`, `form_hexdisk` and `trace` already do. So the
verbs, the `Surfaces` primitives and the fit all belong in **`hex_field`**, beside them. A
crawler-private copy would be written twice and diverge, and the in-world editor draws exactly
these shapes.

The seam that makes that possible is the project's existing one (`BUNDLE.md`, decision 2):

> *a library's enumerations are of MECHANISMS and are closed; a consumer's enumerations are of
> THINGS and are open.*

**Shape classes are mechanisms and closed** — there are three, and a fourth is a library
change:

```
SHAPE_LINE     a straight run
SHAPE_CIRCLE   an arc run
SHAPE_OCTAGON  eight faces, orientation frozen
```

**Wall and road types are things and open** — crawler has stone, fence, road; another game has
hedge, palisade, canal. The consumer keeps its own values and hands the library a **shape
table**: a `vector<integer>` indexed by cell type, giving that type's shape class. Data, not a
callback, so it crosses the library boundary without loft needing function values.

```
crawler's table          library sees
  1 -> SHAPE_LINE          "fit a line to runs of 1"
  4 -> SHAPE_CIRCLE        "fit a circle to runs of 4"
  6 -> SHAPE_OCTAGON       "fit an octagon to runs of 6"
```

That keeps the library ignorant of stone, roads and towers — it knows only that some cell
values mean *circle* — while crawler stays free to add a hedge without touching it.

**One line to revisit.** The EdgeSet merge put `Surfaces` crawler-side on the rule that the
library owns storage and crawler owns write policy. `Surfaces` is not policy — it is geometry
(a line's constant normal, an arc's radial one), and the fit cannot live in the library
without it. The refined split: **the library owns geometry and its interpretation; crawler
keeps `Materials` and the collision response** (`collide`, `sweep_path`, `sight_clear`).
Whether junction arbitration (`edge_block_arb`) is geometry or policy is the one genuinely
open question, since "nearest surface wins" is a geometric rule serving a physics decision.

## The type taxonomy — two axes in one value

A type names a **material/purpose** and a **shape class** together, because a rounded stone
wall must be a different value from a straight stone wall. Otherwise the fitter cannot tell
which primitive to fit, and octagonal towers in particular merge into circles.

| value | type | shape class | blocks |
|---|---|---|---|
| 1 | `WALL_STONE_STRAIGHT` | line | yes |
| 4 | `WALL_STONE_ROUND` | circle | yes |
| 6 | `WALL_STONE_OCTAGON` | octagon (orientation frozen) | yes |
| 5 | `WALL_FENCE` | line | yes |
| 12 | `ROAD_STRAIGHT` | line | no |
| 13 | `ROAD_CURVE` | circle | no |

A rectangle needs no type of its own — it is four `WALL_STONE_STRAIGHT` runs, so a house's
walls fit as lines like any other straight wall.

Values 1, 4 and 5 are what the builder writes today; `solid_kind(t) = t == 1 || t == 4 || t == 5`
already exists and keeps its meaning. What changes is that the distinction stops being
discarded.

**Blocking is a property of the type, not of the geometry.** A road and a tower are drawn by
the same call and differ in whether their boundary edges are cut.

**The octagon carries its own type deliberately.** A rasterised octagon and a rasterised
circle are similar enough on a hex lattice that a residual contest cannot separate them —
and an octagon fitted as a circle loses the eight flat faces that are the whole reason to
build one. Its orientation is frozen by `hex_field`'s `form_octagon` (one flat side on the
world x-axis; an octagon is 8-fold and the grid is 6-fold, so a free orientation would not
be representable), which is what keeps it two facts: **centre and apothem**.

## The drawing verbs

**In the library** — geometry only; the caller says which value to write, so the library never
learns what a tower or a road is:

```
draw_line   (cells, w, h, q0, r0, q1, r1, halfwidth, type)
draw_circle (cells, w, h, cx, cy, rad,     halfwidth, type)
draw_arc    (cells, w, h, cx, cy, rad, a0, a1, halfwidth, type)
draw_octagon(cells, w, h, cx, cy, rad,     halfwidth, type)
draw_opening(cells, w, h, q, r)            an opening in whatever run covers this cell
```

**In crawler** — the game's vocabulary, each one line over the above:

```
draw_wall(q0, r0, q1, r1)         -> draw_line   (…, WALL_STONE_STRAIGHT)
draw_tower(cx, cy, rad)           -> draw_circle (…, WALL_STONE_ROUND)
draw_tower_octagon(cx, cy, rad)   -> draw_octagon(…, WALL_STONE_OCTAGON)
draw_road(q0, r0, q1, r1)         -> draw_line   (…, ROAD_STRAIGHT)
draw_road_curve(cx, cy, r, a0, a1)-> draw_arc    (…, ROAD_CURVE)
```

Each takes only the facts that define the thing: two endpoints for a run, or a centre and a
size for a closed form. `rad` stays a **count of hexes** — the hexes a straight line covers
before leaving the shape — and becomes world units as `rad * HEX_LEN` inside the call.

`halfwidth` defaults to half a hex step (`HEX_LEN / 2`), which is a wall one cell thick.

## Rectangles, and why a flipped house must read the same

A rectangle is the shape that goes wrong on a hex grid, and it goes wrong for a reason worth
stating once.

**The bug.** `stamp_house` builds its rectangle in **index space**:

```
for rr in 0..hh { for qq in 0..ww { … st_set(…, x0 + qq, y0 + rr, …) } }
```

Odd-r offset shifts odd rows half a hex right *in the world*. So a rectangle in `(col, row)`
is not a rectangle in the world — it is a zigzag-edged parallelogram whose left and right
walls are ragged, and whose raggedness depends on the parity of `y0`. Mirror it and the
lopsidedness flips with it, so the mirrored house reads as a *different, visibly wrong*
building rather than the same house facing the other way. The door has the same fault: at
`qq == ww / 2` it lands at a different world position depending on parity.

**The fix is the same rule as everything else** — define the shape in world space and
rasterise it, never index-walk the grid:

```
draw_rect(cells, w, h, cx, cy, wid, dep, rot, mirror, halfwidth, type)
```

`cx, cy` anchor cell · `wid, dep` in hex steps · `rot` 0–5 (60° steps) · `mirror` boolean.
Together `rot` and `mirror` are the 12 orientations — the D6 the lattice actually has, which
is the same set `stencil_rotate` / `stencil_mirror` already implement.

The four sides are line segments in world space, numbered from the local +x side
counter-clockwise, and the walls are `draw_line` along each.

**Doors and windows are intervals on a side, not cells:**

```
draw_opening_side(cells, rect, side, t0, t1)     t in [0,1] along that side
draw_window_side (cells, rect, side, t0, t1, sill, head)
```

### `t` is measured in the OUTWARD frame — that is the whole trick

A side is stored as an ordered pair `(A, B)` chosen so the **outward normal keeps a fixed
handedness**: `n` is always 90° clockwise from `B − A`. `t` runs from `A` to `B`, which is
what an observer standing outside the wall reads left-to-right.

That single convention is what makes a flip read correctly, and it is worth being exact about
because the obvious alternative is wrong:

| | naive: mirror the coordinates | correct: mirror the frame |
|---|---|---|
| window at `t = 0.2`, door at `t = 0.5` | window → `0.8`, door → `0.5` | endpoints `A`/`B` swap, `t` unchanged |
| the observer outside sees | **door now left of window** | window still left of door |
| reads as | a mirrored photograph | the same house, facing the other way |

Under a mirror the handedness of the plane reverses, so keeping `n` 90° clockwise from `B − A`
forces `A` and `B` to **swap**. The feature keeps its `t`, lands on the mirrored wall, and the
facade still reads in the same order. A door pinned to a cell (`qq == ww / 2`) can do none of
this: `ww / 2` rounds, and rounding does not mirror.

### The invariant — two halves, and they are different on purpose

> **1. The footprint commutes with orientation.** For every one of the 12 orientations `g`:
>
>     footprint(g · spec)  ==  g · footprint(spec)
>
> **2. The facade order is invariant.** For every `g` and every side, the features read in the
> outward frame appear in the SAME sequence.

The massing mirrors, so the house fits a mirrored site. The detailing does **not**, so it
still reads as a house. Only the first half is an equivariance; asking for both from one
equation is what produced the mirrored-photograph bug.

**Gate:** for all 12 orientations, `footprint(g·spec)` equals `g·footprint(spec)` on cells
**and** on edges — compare with `edgeset_count_all` and `edgeset_equal`, not `edgeset_count`,
because the halo matters. That is not a guess: rotating a walled ring lost 8 of its 18 stored
edges because a rim edge is owned by a cell *outside* the extent, and the in-chunk count could
not tell "the wall was lost" from "the wall moved into the halo" (`hex_field` `8308180`).
Then, separately: place a window at `t = 0.2` and a door at `t = 0.5` on one side, render all
12 orientations, and read the order off each — it must be window-then-door every time.

**Two negative controls, and both have to fire:**

- Index-space rasterisation must FAIL the footprint half. Draw the house the old way at an odd
  `y0` and the equality has to break, or the test is not seeing parity at all.
- **Mirroring `t` must FAIL the order half.** Implement the naive `t → 1 − t` and the mirrored
  facade must come back door-then-window. Without this control the order check passes trivially
  on a symmetric facade — which is why the fixture is deliberately asymmetric (`0.2` and `0.5`,
  not `0.25` and `0.75`).

## The fit — class is read, parameters are detected

Once, at world build:

```
fit_runs(cells, shapes, w, h, sf, e, mats)      one library call

group    connected cells sharing a type            -> a run
fit      shapes[type] selects the primitive; only parameters are solved
           SHAPE_LINE    -> line_fit   -> surf_straight(nx, ny, c)
           SHAPE_CIRCLE  -> circle_fit -> surf_arc(cx, cy, r)
           SHAPE_OCTAGON -> centre + apothem -> EIGHT surf_straight, one per face
tag      each boundary edge of the run takes the surface nearest it
```

**The class is never inferred.** That is the one change that makes this work, and it is the
change the measurements demanded:

| measured today | why | fixed by |
|---|---|---|
| `rad 8` ring → **0 arcs, 6 straights** | the matcher must decide round-vs-straight from residuals, and a hex ring *is* a hexagon | the type says circle; only the radius is solved |
| `rad 5` ring → 3 arcs + 2 straights, junk radius | same contest, near the tolerance | as above |
| doored `rad 2` → 1 arc becomes **3** | the door is a hole, so the traced boundary fragments | runs group by type; an opening does not split one |
| octagon vs circle | too similar to separate by residual | its own type |

**Why fit at all, when the drawer knew the geometry?** Because the parameters are not stored,
and should not be: a cell's type is the durable record, and an editor painting a curved wall
by hand gets the same treatment as a generated tower. Fitting also keeps a damaged wall
honest — the fit describes the cells that are actually there.

## Openings

A door or a gate is **not** a missing cell and not a separate shape. The cell keeps its run's
type, so the run stays one surface and one fit; the opening is recorded separately and leaves
the edge passable. This is what stops a doorway from splitting a tower into three arcs, and it
is the same mechanism a gate in a town wall needs.

## What the renderer reads

Per blocked edge, from its surface:

- **arc** → centre, radius, and the edge's angular span → a curved strip of N segments, with
  exact radial normals
- **straight** → a flat quad, as today

A curved road edge and a curved wall edge take the same path. Normals come out exact instead
of snapped to one of six hex-edge directions — the reason the surface layer exists at all
(using the edge's own normal is wrong by up to 90°).

## Gates, each with the control that must fire

| | gate | negative control |
|---|---|---|
| **footprint** | `footprint(g·spec) == g·footprint(spec)` for all 12, cells **and** edges | the index-space rectangle must fail it at odd `y0` |
| **facade order** | window `t=0.2` before door `t=0.5`, read in the outward frame, at all 12 | naive `t → 1 − t` must come back door-then-window |
| rasterise | `draw_tower(rad 2)` marks the same 12 cells as today | a 10% radius change moves the marked set |
| shape | `rad 8` fits **one arc** where today it fits six straights | perturb the radius 10% → the fitted radius must follow |
| octagon | an octagonal tower fits **8 faces**, not 1 arc | draw it with the round type → it fits 1 arc, proving the type is what decides |
| openings | a doored tower fits **1** arc, not 3 | remove the opening record → it fragments again |
| passability | `fieldtest`'s differential: old ≡ new over every (hex, dir) | — |
| render | a straight wall and a tower in one frame; the straight stays straight | a renderer that curves everything fails this |

The octagon control is the important one: it is the only check that proves the *type* drives
the fit rather than the geometry happening to fit.

## What this replaces

- `stamp_round_tower`'s hex ring → `draw_tower`'s circle rasterisation
- the `towers` parameter vector recorded through `sim_new_gen_s` (P5 A1) — the cell type
  carries it, and in a place the editor also writes
- `tag_round_tower` (P5 A2) — the fit pass tags edges generically
- `match_loop`'s round-vs-straight decision, for typed content; `hexmatch` keeps the job it
  was written for, recovering surfaces from **untyped** cell-authored footprints

## Order

1. **`Surfaces` moves into `hex_field`.** Mechanical, and it unblocks everything below; the
   gate is that `edgetest` / `jointest` / `matchtest` pass unchanged, as they did for the
   EdgeSet merge.
2. **The `draw_*` verbs into the library**, on the one rasterise rule — `draw_rect` **first**,
   because a second agent is blocked on it today. Crawler's `stamp_house`,
   `stamp_round_tower` and the road painter become one-line callers. Gate: the `rad 2` cell
   set is byte-identical to today's, `rad 8` becomes round, and drawing commutes with all 12
   orientations.
3. **`fit_runs` into the library**; crawler supplies the shape table. Gate: `rad 8` fits one
   arc where today it fits six straights; an octagon fits eight faces.
4. `Sim` carries the `Surfaces`.
5. `view3d` draws arc edges as curves.

Steps 1–3 are library work with crawler as first consumer and the editor as second — which is
the sequencing `EXTRACTION.md` asks for (*build new, extract settled*), taken in the right
order for once: the routine is written where it belongs rather than migrated later.

## Open, deliberately

- **Two towers that touch** share a boundary and the same type, so connectivity alone would
  merge them into one run and one bad fit. Not solved here because nothing builds it yet; the
  likely answer is a run id rather than more geometry.
- **Junction arbitration's side of the line.** "Nearest surface wins" is a geometric rule
  serving a physics decision, so `edge_block_arb` could sit on either side of the library
  boundary. Decide it when the fit lands, with the code in hand.
- **Tagging cost.** Picking the nearest surface per boundary edge over all registered surfaces
  is O(boundary × surfaces). Worth a timing on a 101×101 world before step 3, not after.
