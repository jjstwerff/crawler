# HOUSE — a two-storey house, and the 12 orientations that prove it

**Plan #11 P5.** The design for the first thing built with the routines in
[`BUILDING.md`](BUILDING.md): a real house — exterior wall, door, windows, interior walls
with interior doors, a second storey reached by stairs, a terrace with its own door, and a
roof — then stencilled into all 12 orientations and rendered.

It is deliberately not a demo. It is the **fixture that makes the drawing routines
falsifiable**: every feature in the list above exists because a simpler house cannot tell a
correct implementation from a broken one. §7 is the sharpest case — a plain rectangular
house **cannot** distinguish 12 orientations from 6.

**Depends on** `BUILDING.md` steps A–D (the routines do not exist yet). This file specifies
what they must be able to express, so it is worth reading *before* building them.

---

## 1. The target, in metres

`SCALE.md`: one hex step = **1.5 m**, one world unit = 0.866 m. State metres or it cannot be
falsified.

```
   plan          5 x 4 hex steps          7.5 m x 6.0 m    (+ a 2 x 2 terrace)
   ground floor  0.00 -> 2.40 m ceiling   eye height 1.60 m, 0.80 m of head clearance
   structure     0.20 m
   first floor   2.60 -> 5.00 m ceiling
   eave          5.20 m
   ridge         8.20 m                   45 deg pitch over a 6.0 m span
   door          0.87 m clear   (ONE edge; 2 edges = 1.6-1.9 m, a double door)
   window        1.00 m wide, sill 0.90 m, head 2.00 m
   stair         2.60 m rise over 3.00 m run = 2 cells, 41 deg — a cottage stair
   parapet       1.00 m, on the terrace boundary
```

Every number above is a metre value with a real referent. The 41° stair is steep and real;
a 30° stair would need 3 cells and is the alternative if it reads badly.

---

## 2. The one new structure: a storey

The field is 2-D plus heights, so a second floor is **not** a new dimension — it is a second
field. This is plan #5's own answer, already used for spiral stairs: *"a spiral is a stack of
levels, one per revolution"*.

```
Storey = { cells      HexSet      the FLOOR area — where you can stand
           floor      Heights     top of this storey's floor
           soffit     Heights     underside of what is above (ceiling, or roof)
           types      Labels      floor material
           edges      EdgeSet     walls, as boundary edges (BUILDING.md §1)
           layers     Layers      roof material, feature ids }

Building = vector<Storey> + the anchor cell
```

**Floor *and* soffit, not one z.** `hexroof::clear_height(floor, soffit)` already assumes
this pair, and plan #5 states the reason: a roof and an arch are the same surface seen from
opposite sides, so a cell wants the surface below it and the surface above it. It is also
the only way to express the thing a second storey actually adds — *walkable here, and
something over it*.

> **The invariant a storey exists to carry:**
> `clear_height(floor_k, soffit_k) ≥ 2.0 m` at **every cell of `cells`**, on every storey,
> including on the stair and under the first floor. A storey with a cell you cannot stand in
> is a modelling error, not a tight squeeze.

Storeys stack by construction: `floor_{k+1} = soffit_k + structure`. Nothing infers it.

---

## 3. The build, as a sequence of calls

Each line is one `BUILDING.md` §2 call — a geometry, an `area_type`, an `edge_type`.

```
  GROUND STOREY
   1  draw_house    rect 5x4          floor=BOARD      edge=WALL_COTTAGE
   2  house_opening side 3, t .50, 1 edge, DOOR                    the front door
   3  house_opening side 3, t .20, WINDOW    (writes no cell — §4)
   4  house_opening side 1, t .30 / .70, WINDOW
   5  house_inner   (side 3, .62) -> (side 1, .62)   edge=WALL_PARTITION
   6  house_inner   (side 2, .45) -> inner wall 5     edge=WALL_PARTITION
   7  inner_opening on wall 5, 1 edge                             interior door
   8  inner_opening on wall 6, 1 edge                             interior door
   9  draw_stair    (side 2, .25) -> (side 2, .75), rise 2.60 m    2 cells

  FIRST STOREY
  10  draw_house    rect 5x4          floor=BOARD      edge=WALL_COTTAGE
  11  subtract      the stairwell — cells with no floor over the flight's head
  12  draw_terrace  rect 2x2 on side 0   floor=DECK    edge=PARAPET
  13  house_opening side 0, t .50, 1 edge, DOOR                    onto the terrace
  14  house_opening side 3, t .25 / .75, WINDOW
  15  house_inner   (side 3, .50) -> (side 1, .50)   edge=WALL_PARTITION
  16  inner_opening on wall 15, 1 edge

  OVER IT ALL
  17  house_roof    over storey 1 MINUS the terrace, eave 5.20 m, 45 deg, gable
  18  flat_roof     over the terrace = the ground storey's soffit, falls 1:60 to drain
```

Two things to notice, because they are design decisions and not bookkeeping:

- **The roof is drawn over a REGION, not over "the house"** (17 and 18 are two calls). That
  falls straight out of `BUILDING.md` §2 — a roof is an area with a profile — and it is what
  lets a terrace and a pitched roof coexist without a special case.
- **The terrace floor IS the ground storey's soffit.** It is not a second surface at the same
  height; it is the same surface, read from above. Storing it twice is how the two drift.

---

## 4. Doors and windows are not the same kind of thing

**Neither deletes anything.** Plan #5 §4 L5: *"a feature is an annotation on a continuous
body, never a break in it — features must be stored beside the surface, never by deleting
cells or edges from it."* Both are intervals on the wall's fitted surface; what differs is
**which of the wall's terms each overrides** (L4):

| | interval | overrides | leaves alone |
|---|---|---|---|
| **door** | `[s0, s1]` along the surface | `solid` — you walk through it | opacity, the wall run |
| **window** | `[s0, s1]` **and** `sill..head` | `opacity`, `sound`, `permeability` | `solid` — you cannot walk through it |

The edge layer only records *which edges the door interval makes passable*. The wall keeps
its type on every edge, so a wall with three doors still fits as **one** wall — the defect
`DRAWING.md` names as a doored tower fitting 3 arcs instead of 1.

`DRAWING-API` §5.4 already says a window alters no cells. Plan #5 §4 says why in more
detail and names the limitation this design inherits: **`Materials.height` is a scalar, and
a window needs an interval** (L3). So a window is a record on the wall surface —
`(side, t0, t1, sill, head)` — resolved at render, and it is the one feature here that the
field genuinely cannot carry.

That is a real dependency, not a detail: **windows will not appear until the feature
interval reaches the renderer.** Say so now rather than discover it in a frame.

A door's clear width is **one edge = 0.87 m** — the gap you walk through is the edge's own
length, not its projection on the wall line. Plan #5 measured the whole table: 2 edges =
1.6-1.9 m (a double door), 4 = 3.1-3.6 m (a gateway), with the quantum varying **~19 % with
heading**. Pick the edge count per heading to hit a target width.

---

## 5. Stairs — and the rule that says they cannot exist

`SCALE.md` reclassified stairs, and it applies here head-on:

> the grid is **5.4× too coarse for a domestic staircase**, which therefore sits on the
> object side … §P12's stair arithmetic is right; its subject is **monumental** stepped work.

A tread is 0.25 m; a hex is 1.5 m. So **the treads cannot be field features** — six of them
fit in one cell. But the *flight* is 3.0 m long and 2.6 m tall, which is two cells and
1.7 storeys: firmly field-sized.

> **The resolution: the FLIGHT is a field feature, the TREADS are an object.** The field
> carries the cells the flight occupies, the floor height ramping across them, and the
> **level link** between storey 0 and storey 1. The treads, handrail and newel are a prop
> fitted to that ramp — `PROPS.md`'s rule, and the same boundary a domestic spiral stair
> and a sapling already sit on.

This is why the storey model carries *soffit* as well as floor: the stair's own headroom is
`clear_height` along the flight, and plan #5 states the constraint in its general form —
`N·rise ≥ headroom + soffit`. The stairwell (step 11) exists to satisfy it, and its size is
**derived from that inequality, not chosen**.

**Handedness matters and is not decoration.** A flight anchored `(side, t) → (side, t)` keeps
its reading under a flip (§7), so a mirrored house does not get a mirrored stair. If it did,
the handrail would change hands — which is exactly the "mirrored photograph" defect one
storey up.

---

## 6. The terrace

A terrace is three things at once, and each is an existing mechanism:

1. **floor** — storey-1 cells with `DECK`;
2. **not roofed** — excluded from step 17's region, so the pitched roof stops at its edge;
3. **a boundary** — `PARAPET` on its boundary edges: a thin type, 1.0 m, blocking.

It is also the ground storey's roof, so it must **drain**: a flat roof is drawn with a
1:60 fall and gated by `hexroof::roof_ponds == 0`. A dead-level deck ponds, and ponding is
the roof correctness invariant plan #5 already built the check for.

**And it is the reason this fixture has a terrace at all** — see §7.

---

## 7. The 12 orientations, and what "left–right does not switch" means

A stencil carries the whole building (cells, heights, labels, edges, layers — `Stencil`
already has all five slots). The 12 orientations are 6 rotations × {identity, mirror}, which
is the D6 the lattice has.

Under the mirror, three different things happen, and keeping them apart is the whole design:

| | under a flip | why |
|---|---|---|
| **the massing** | **mirrors** — the terrace moves to the other side | so the house fits a mirrored site |
| **the facade reading** | **unchanged** — a window left of the door stays left | features are `(side, t)`, and `t` is preserved (`BUILDING.md` §4) |
| **the interior reading** | **unchanged** — rooms, doors and the stair keep their order | interior walls are `(side,t) → (side,t)`, the same vocabulary |

That is the user's requirement stated exactly: **the left–right arrangement does not switch
on a flip; only the massing's chirality does.** A flipped house is the same house facing the
other way, not a mirrored photograph of it.

### The trap, and why the terrace is load-bearing

> **A mirror-symmetric massing makes the flip observationally the IDENTITY.** For a plain
> rectangle with `(side, t)`-anchored features and interior, the flipped house is the same
> house — same cells, same edges, same reading. So *"we validated all 12 orientations"* on a
> rectangular house is a check that passes for the wrong reason: there are only **6**.

This is `STATE.md` lesson 3 arriving in a new place, and it is the single most likely way
this validation goes green while proving nothing. Two consequences, both required:

- **The fixture must be asymmetric.** The terrace is what supplies it — a 2 × 2 bite out of
  one side that has no mirror partner. With it, the 12 orientations are genuinely 12.
- **There must be a control that collapses.** Build the same house *without* the terrace and
  assert the 12 orientations reduce to **exactly 6 distinct** cell/edge sets. If that control
  does not fire, the asymmetry is not reaching the comparison and the 12-way check is blind.

The same reasoning rules out symmetric feature placement: `t = 0.20` and `0.50`, never
`0.25` and `0.75`, for the reason `DRAWING-API` §8.2 already gives.

---

## 8. Validating the render — three channels, and what each cannot see

**`xvfb` is not installed on this box**, so `make probe` and the native `gl_screenshot` path
are unavailable (`STATE.md`). `tools/glbview.py` needs neither, which is why it is the
primary channel here.

| channel | what it proves | what it cannot see |
|---|---|---|
| **headless numeric** (`../hexbody/src/housetest.loft`) | equivariance, headroom, drainage, storey stacking, the 12-way identity | anything about appearance |
| **GLB → `tools/glbview.py`** | the geometry a renderer would receive: massing, roof, wall runs, openings | shader, lighting, the live camera |
| **`make play`, `V`** | it in the game, at eye height | nothing automatable — the user's eyes |

**A roofed house renders as a roof.** Everything in §3 steps 1–16 is invisible from outside
once step 17 lands, so the render validation needs **three passes per orientation**, not one:

1. **roof on**, from outside — massing, eave, ridge, terrace, door and window openings;
2. **roof off** — the first storey's plan, its walls, the terrace parapet, the stairwell;
3. **a vertical section** through the stair — the two floors, the flight, headroom.

The 12-orientation deliverable is a **contact sheet**: 12 thumbnails from a fixed camera
azimuth, so a rotation that lands wrong is visible as a break in an otherwise regular
sequence. A single hero image cannot show a 1-in-12 defect.

> **The eye-height check is not optional.** Plan #11 P0 found a world too small for its own
> player — 1.51 m eaves, a 1.45 m door — that *every raised camera had missed*. A two-storey
> house with a stair is exactly the shape that defect hides in. Section 3 above is where it
> shows.

---

## 9. Gates, each with the control that must fire

| gate | control |
|---|---|
| **equivariance** — cells **and** edges, all 12, `edgeset_equal` / `edgeset_count_all` | the index-space rectangle fails at odd `y0` |
| **12 really is 12** — the 12 orientations give 12 distinct footprints | **drop the terrace: it must collapse to exactly 6** |
| **facade order** — window left of door on every side, all 12 | omit the endpoint exchange: 24 of 24 reverse |
| **interior order** — room sequence and stair handedness identical across all 12 | anchor an interior wall in cells instead of `(side,t)`: it must mirror |
| **headroom** — `clear_height ≥ 2.0 m` at every walkable cell of every storey | shrink the stairwell by one cell |
| **storey stacking** — `floor_{k+1} − soffit_k == structure`, exactly | perturb one storey by 0.1 m |
| **drainage** — `roof_ponds == 0` on pitched roof and terrace both | level the terrace |
| **eave** — `eave_spread == 0` on the long sides | read the wall top at the zigzag instead of the fitted line |
| **door** — the interval opens exactly the intended edges; a window opens none | make a window override `solid`: the house must leak |
| **features do not fragment** — a wall with 3 doors and a window fits as ONE wall | delete the edge instead of annotating it: it must fit as 3 |
| **render** — the 12-sheet is regular; roof-off shows the plan; the section shows two floors | corrupt one orientation by one hex |

---

## 10. Order

| | | depends on |
|---|---|---|
| **H1** | the `Storey` / `Building` structures + the stacking and headroom gates | `BUILDING.md` A |
| **H2** | ground storey: walls, door, windows, interior walls + doors | `BUILDING.md` A–C |
| **H3** | the stair: flight cells, ramp, level link, stairwell derived from headroom | H1, H2 |
| **H4** | first storey + terrace + parapet | H2, H3 |
| **H5** | roofs: pitched over the house, flat over the terrace | `BUILDING.md` D |
| **H6** | the stencil: 12 orientations + the collapse control | H4 |
| **H7** | render: GLB, the three passes, the 12-sheet | H5, H6, and the **fit** (`BUILDING.md` §4) |

**H7 depends on the wall fit**, not just on H5: without it every wall renders as the raw
zigzag/staircase (15.5 % / 29.9 % longer — `BUILDING.md` §4) and the contact sheet is
judging the wrong thing. `../hexbody/src/houseshot.loft` already produces that sheet from the real
stored edges, so the defect is visible now rather than hypothetical.

---

## 11. Open, and worth deciding before H1

- **Where storeys live.** `Storey` is generic and belongs in `hex_field` beside `Stencil`;
  the metre values and material types are crawler's. Same seam as everything else, but it is
  the first *structure* the library gains for this plan and worth confirming.
- **Does a stencil carry a whole `Building`, or one `Storey` each?** One per storey is
  simpler and rotates with machinery that already exists; a building-level stencil needs
  `stencil_rotate` to understand a vector of storeys. **Recommendation: one stencil per
  storey, rotated in lockstep**, with a gate that the storeys stay aligned after rotation —
  which is a check worth having anyway.
- **Window intervals to the renderer** (§4) — the one piece of this house the field cannot
  carry, and it is upstream of "windows are validated".
- **41° or 30° stairs** — 2 cells or 3. A metre question, decided by looking at §8's section
  pass.
