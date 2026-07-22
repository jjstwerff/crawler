# BUILDING — one drawing routine for walls, houses, roads, fences and roofs

**Plan #11 P5.** The implementation design for the verbs specified in
[`DRAWING-API.md`](DRAWING-API.md), corrected where drawing one house falsified it, and
carried through to a **roof** and to the renderer.

[`DRAWING.md`](DRAWING.md) says *why*, `DRAWING-API.md` says *what must exist*. This file
says **how**. It is written from measurements, and the routines it describes now exist:
**`src/housedraw.loft`**, gated by **`src/housetest.loft`** (in `make test`, 3 s). Every
number below that carries a ✅ is measured by that gate, in the engine, on the real
lattice; every negative control there has been seen to fire.

> An earlier draft was measured by a Python blueprint instead. That was dropped, because a
> model of the drawing routines can disagree with the routines silently — and did: it
> reported the wall run as **39 %** longer where the real figure is **15.5 %**, because its
> side-classification credited corner edges to the wrong side. Measure in the engine.

> `DRAWING-API.md` is corrected in six places. It was written before anything was drawn.

The first thing built with these routines — a two-storey house with stairs, a terrace and a
roof, stencilled into 12 orientations — is designed in **[`HOUSE.md`](HOUSE.md)**. It is the
fixture that makes these routines falsifiable, so it is worth reading before building them.

---

## 1. The one thing that decides everything: thickness

A wall is not a kind of cell. It is a **line with a thickness**, and the thickness decides
which layer stores it:

| the thing | real thickness | stored as | costs floor? |
|---|---|---|---|
| cottage wall | 0.3 – 0.5 m | **an EDGE** | no |
| fence, palisade, railing | 0.05 – 0.2 m | **an EDGE** | no |
| road side / kerb / verge | ~0.15 m | **an EDGE** | no |
| interior partition | 0.1 – 0.2 m | **an EDGE** | no |
| hedge | 0.5 – 1.0 m | **an EDGE** | no |
| **castle / palace curtain wall** | **1.5 – 3 m** | **a BAND of cells** | yes, correctly |
| road surface, floor, courtyard | — (an area) | **cells + a type** | it *is* the floor |

> **THE RULE. Thickness below one hex step is a property of the TYPE — rendered, never
> rasterised. Thickness at or above one hex step is a band of cells.**

The threshold is `HEX_LEN` = **1.5 m**, and it is not a new one: `SCALE.md` already settled
that a domestic staircase at 0.28 m going is *below one hex step and is therefore an object,
not a field*. Wall thickness is the same question with the same answer. A hex is 1.5 m of
world; anything thinner than that cannot be a hex without being **thickened until the model
can see it** — which is exactly the defect `STATE.md` decision 6 already names for the
fence: *"the fence is currently a filled cell (`tiles[i] = 5`) — a 1.5 m thick barrier, the
thin thing thickened until a point-sample model could see it."*

**Measured, on the same 5 × 4 house — 7.5 m × 6.0 m of plan:**

| | floor | wall |
|---|---|---|
| **thin** (wall = boundary edges) | **27 cells = 52.6 m²** | 38 edges, 32.9 m of run |
| **thick** (wall = a band of cells) | **11 cells = 21.4 m²** | 16 cells, 1.5 m thick |

The thick wall eats **59 % of the cottage** — 31 m² of a 53 m² house — and renders as **two
faces 1.5 m apart with dead space between them**. That is a curtain wall around a cupboard.

The machinery is already in the kernel and does not need building: `Sim.walls` is
*"the edge authoring surface"* (`idx = hex*3 + edge`), `build_field` blocks those edges
directly beside the filled-cell path, and `view3d` already draws one thin quad per blocked
edge. The demo world even carries *"a 3-edge wall stub on hex (12,7)… demonstrates edge
walls alongside the full-hex walls"*. **Nothing about thin walls is new. The house simply
was not using them.**

---

## 2. One routine, two outputs

Because thickness is a property of the type, every drawn thing is the **same call**. A
geometry is rasterised once and writes up to two layers:

```
draw_<geometry>(cells, types, edges, …geometry…, area_type, edge_type)

   area_type  ->  written into every cell of the region       (road metal, floor, courtyard)
   edge_type  ->  written onto every boundary edge of it      (wall, kerb, fence, hedge)
```

Either may be absent. That single shape covers the whole table:

| call | `area_type` | `edge_type` | what you get |
|---|---|---|---|
| `draw_road` | road surface | kerb | the metal **and its sides**, one call |
| `draw_house` | floor | cottage wall | the floor **and its walls**, one call |
| `draw_field` | ploughed | hedge | a field **and its boundary** |
| `draw_courtyard` | flagstone | — | paving, no boundary |
| `draw_curtain_wall` | wall fill | — | a **band of cells**: the castle case |
| `draw_fence` | — | fence | a bare line of edges, no region |

**Road sides come free** and were never a separate problem: a road's kerb is the boundary of
the road's cell region, which is the same object as a house's wall. This is what the user's
"one routine" means concretely — not a shared helper, but a shared *output shape*.

### Two ways to get edges, and only one of them is safe

- **Boundary of a filled region** (house, tower, road, courtyard) — the edges between a cell
  of the region and one outside it. **Closed by construction**: measured on the 5 × 4 house,
  **0 corners with an odd edge count**, at any size, orientation or tie. Nothing to gate,
  nothing to break.
- **Edges a bare curve crosses** (a fence across a field, a partition inside a house). Not
  closed and not meant to be; it needs its own gate — the run must be **edge-connected end
  to end**, and a curve passing exactly through a hex corner is the tie case that can drop
  one.

`DRAWING-API` §5.1's inner walls (`iw_*`) are the second kind, and that is why they need a
different gate from the outer wall rather than the same one.

### The distance functions are what is actually shared

`DRAWING.md`'s "one rasterise rule" survives, one level down: the **distance** is shared, and
the layer that receives it is chosen by the type.

| geometry | distance |
|---|---|
| segment | point-to-segment, projection clamped to `[0,1]` |
| arc | `abs(‖p−c‖ − r)`, angle in `[a0,a1]` with wrap |
| circle | as arc, no angular test |
| octagon | min over its 8 sides, orientation frozen |
| **filled rect** | 0 inside; `hypot(max(|u|−hw,0), max(|v|−hd,0))` outside |

The filled-rect row is the addition. A closed shape's geometry is its **filled region**, so
"within halfwidth" means the region grown by halfwidth — and that is what makes fill-then-
boundary one rule rather than two.

---

## 3. Do not paint a band of cells along a line

For the **castle** case the band is the wall, so it must be rasterised — and there the naive
buffer rule bites. Walls painted as cells within `halfwidth` of the four sides of the 5 × 4
rectangle:

| tie | cells | parts | encloses |
|---|---|---|---|
| out | 14 | **2** | **0 — the wall has a hole** |
| in | 22 | 1 | 11, but **2 cells thick on two of its four sides** |

**The tie is structural, not bad luck.** With `halfwidth = HEX_LEN/2 = √3/2` — the cell
inradius, the spec's default — every cell-to-side distance along the local *u* axis is an
exact integer multiple of that same `√3/2`:

```
   row r=0: distances / halfwidth = [1.0, 3.0, 4.0]
   row r=1: distances / halfwidth = [0.0, 2.0, 2.268, 4.0]
```

So `d ≤ halfwidth` lands **exactly on the comparison boundary** for a whole column of cells,
at every ordinary size, and which side it falls is the last bit of a float.

> **For a thick wall: fill the region, then take its boundary band.** Comparisons stay
> inclusive (`≤ bound + ε`, `ε = 1e-9`) so the *fill* does not lose a cell to the same tie —
> that moves a wall by one cell at worst, never breaks it.

**This also fixes the tower** — which is a castle thing, so the band is right for it. Rim of
a rasterised disk against today's `hex_distance == rad` ring:

| rad | hex ring | spread | disk rim | spread | |
|---|---|---|---|---|---|
| 2 | 12 cells | 14.4 % | 12 | 14.4 % | **same cells** |
| 3 | 18 | 12.8 % | 18 | 12.8 % | **same cells** |
| 5 | 30 | 14.0 % | 30 | 14.0 % | **same cells** |
| 8 | 48 | 14.7 % | 54 | **10.3 %** | differ by 42 |
| 12 | 72 | 14.7 % | 78 | **7.5 %** | differ by 90 |

The hex ring's radial spread is **flat with size** — it is a hexagon at every radius, which
is `DRAWING.md`'s complaint as a number. The disk rim's spread **falls**: it is genuinely
round. They are identical to rad 5, so the migration moves no tower the game builds
(`DRAWING-API` §8.3 asks for rad 2 and gets rad 5 free). That spread is also a **better gate
than the matcher** — no fit, no tolerance, no arc recovery. *A shape is round iff its rim's
radial spread falls as it grows.*

---

## 4. The house

```
house_new(cq, cr, wid, dep, rot) -> House          wid/dep in hex steps (1.5 m each)
house_opening(h, side, t_centre, nedges, kind)     ← n EDGES, not a t-interval
house_inner(h, side_a, t_a, side_b, t_b)           ← a crossed-edge run, gated separately
house_flip(h) -> House                             toggles ho_mir; nothing else
house_draw(h, cells, types, edges, floor_type, wall_type)
house_side_point / house_side_normal               outward, unit, from the MASSING
```

`house_draw` fills the massing with `floor_type` and writes `wall_type` onto its **boundary
edges**. Occupancy is *not* set for the wall: passability is the `EdgeSet` (plan #11 P2), so
a house needs no solid cells at all and its floor stays walkable end to end.

Sizes are hex steps and the **metre value is the honest one**: 5 × 4 is 7.5 m × 6.0 m. It is
not 5 cells × 4 cells — along *u* cells are `√3` apart, but rows are `1.5` apart, so `dep`
steps span `dep · 1.1547` rows. Say metres (`SCALE.md`).

### The mirror is applied ONCE — `DRAWING-API` §5.2 applies it twice

§1 puts the mirror in the local→world frame; §5.2 then negates local x **again** in
`ends(s) = (−Bx, By, −Ax, Ay)`. The two negations cancel, leaving a bare exchange, and the
outward normal turns **inward**:

| reading | worst `n · outward` |
|---|---|
| frame mirrors, endpoints **exchange only** | **+1.000** |
| **§1 + §5.2 as literally written** | **−1.000 — broken** |

> **Corrected:** the mirror lives in the frame; a mirrored side's endpoints
> **exchange and do not negate** — `ends(s) with mirror = (Bx, By, Ax, Ay)`. §5.2's prose is
> right (*"the swap is not a detail, it is the mechanism"*) and §5.3 is untouched:
> `house_flip` is one line.

**And §8.2's gate must not read `outward` off the endpoints** — that is the thing under test,
so a broken rule supplies its own definition of outward and the check passes. Take outward
from the **massing** (centre → side midpoint):

| facade order, window `t=0.2` vs door `t=0.5` | reversed |
|---|---|
| endpoints exchange (correct) | 0 of 24 (6 rot × 4 sides) |
| endpoints unchanged (**control**) | **24 of 24** |

### The door: n edges, and a real door is one of them

`DRAWING-API` §5.4 erases along the `t`-interval. Measured on side 3 (7.50 m long):

| rule | asked 3.00 m | got |
|---|---|---|
| `erase_seg` as given | | 4.50 m — **over by 1.50 m** |
| `erase_seg` shrunk by halfwidth | | 1.50 m — **under by 1.50 m** |
| n **cells** centred at `t` (castle gate) | | exactly n × 1.50 m |
| **a feature interval on the fitted surface (house door)** | | **3.00 m, straight** |

`erase_seg` over-erases by ~`halfwidth` at *each* end and shrinking over-corrects; neither is
predictable. **A door is an interval on the SURFACE**, and the edge layer only records which
edges that interval makes passable — plan #5 §4 L1b, already shipped and gated by
`src/feattest.loft`:

> *"A door is `[s0, s1]` along an exact straight or arc, so it is straight because the
> surface is, at any width and any position. The cell/edge layer only answers which edges
> that interval opens. **The zigzag never reaches the render or the mesh.**"*

**Two corrections to earlier drafts of this file, both found by asking what a door on a
zigzag actually does:**

1. **The clear width is 0.87 m per edge, not 0.75 m.** 0.75 m is the edge's *projection onto
   the nominal wall line*; the gap you walk through is the edge's own length, 1.0 world unit
   = **0.866 m** — a proper domestic door. Plan #5's measured table gives 1 edge = 1.0 unit
   at every heading, 2 edges = 1.6–1.9 (a double door), 4 = 3.1–3.6 (a gateway). The
   **quantum varies ~19 % with heading**, which is the one real residual: pick the edge count
   per heading to hit a target width.
2. **A door must not delete the edge.** L5 is explicit — *"a feature is an annotation on a
   continuous body, never a break in it… features must be stored beside the surface, never by
   deleting cells or edges from it"*. Deleting the edge fragments the wall run, which is the
   same defect as `DRAWING.md`'s doored tower fitting **3 arcs instead of 1**. The edge keeps
   its wall type; the feature **overrides a subset of its terms** (L4: a door changes `solid`;
   a window changes `opacity`/`sound`/`permeability` and *not* `solid`).

### The wall run is longer than the wall — by one of TWO exact amounts ✅

A thin wall is not a line, it is a **strip of hex edges**, and how much longer that strip
runs depends on which way the wall faces. The lattice has line directions at 0°/60°/120°;
a rectangle has two perpendicular side families, so **only one family can align with them**
and the two behave differently:

| side | edges | run | wall | overhead | axes used |
|---|---|---|---|---|---|
| perpendicular to a lattice line — **zigzag** | 10 | 8.66 m | 7.50 m | **2/√3 = 1.1547** | 2 of 3 |
| along one — **staircase** | 9 | 7.79 m | 6.00 m | **3√3/4 = 1.2990** | 3 of 3 |

Both are exact and hold at every size. **There is no single "wall run overhead" figure** —
a claim that there is means the sides were not measured separately.

That is not a rounding note. At eye height a 7.5 m cottage wall reads as **ten faceted
panels**, and the first-person camera is the thing that finds exactly this class of defect
(`STATE.md` lesson 2). So the **fit is load-bearing for thin walls, not an optimisation**:
`DRAWING.md`'s fit pass recovers the straight surface and the renderer draws one flat quad,
as `mesh_walls_fitted` already does. Store the zigzag, draw the line.

`src/houseshot.loft` renders the 12 orientations with walls drawn as the raw stored
edges — that contact sheet (`/tmp/house12.png`) is the picture of what the fit has to fix.

---

## 5. The roof — the same distance, a profile instead of a threshold

No new machinery. The footprint verbs already compute distance to a segment; a roof reads it
through a profile instead of a threshold:

```
   footprint:   mark the cell   iff   d(geometry) ≤ halfwidth
   elevation:   set z           =     peak − pitch · d(geometry)
```

which is `src/hexroof.loft`'s own claim reached from the other side — *"every roof form
anyone names is the same function of a distance, and only the distance SOURCE changes"*. A
cone is the point distance, a gable/hip the segment distance, a barrel vault the same
distance with a circular profile.

```
house_roof(h, hz, layers, eave, pitch, hip_steps, roof_type)
house_facets(h, eave, pitch, hip_steps) -> the exact roof planes, for the mesh
```

**The ridge runs along `u`, through the anchor cell, and past the gable end.** All 6
rotations put `u` on a lattice line (the grid has line directions at 0°, 60°, 120°), so the
ridge always lies on a row of cell centres — which is exactly plan #5 §14's condition for a
planar roof to be exact. It must also extend past the ends:

| | worst interpolation error vs the analytic surface |
|---|---|
| gable, ridge extended past the wall | **1.8e-15** |
| hip, shortened one step | 2.3e-01 *(genuine — a hip end IS conical)* |
| **control: ridge stops at the wall** | **4.3e-01 — fires** |

0.43 units is 0.37 m of bulge: past the ridge's tip the distance goes radial and the gable
end **rolls over like a cone quadrant**. A gable's ridge is effectively the line; only a hip
shortens it, and then the conical ends are the feature.

**The height field extends one ring past the massing**, and that ring is load-bearing:

| | wall edges with no roof height above them |
|---|---|
| with the one-ring halo | **0** of 76 |
| **control: halo dropped** | **38 — fires** |

The halo is not padding: it is what makes the eave interpolable. Same answer the `EdgeSet`
reached for its rim edges, arrived at independently.

**What the renderer draws.** Plan #5 §14 settled it with measurements — *interpolate planar
roofs; recover only cones*. A gable and a hip are flat facets, so:

- **the roof** is `house_facets` — two planes for a gable, four for a hip, vertices at the
  rect corners (`z = eave`) and the ridge ends (`z = peak`). Exact, and 2 quads.
- **the wall top** is that facet evaluated on the **fitted wall line**, never at the zigzag
  boundary — reading it at the zigzag would make the eave wander ±0.43 m. On the long sides
  it is constant and equals `eave`; on the gable ends it rises linearly, giving a proper
  triangle instead of a staircase. `hexroof::eave_spread` already measures exactly this and
  must read 0.
- **the stored heights** are the durable record — what an editor paints. They are not the
  drawing path.

Two representations, so **gate them against each other**: the facet surface evaluated at
every stored cell centre must equal the stored height. Cheaper than choosing one, and it is
what stops them drifting.

**A roof blocks nothing.** Heights are not passability; the `EdgeSet` is untouched, so no
part of plan #11 P2 is at risk.

---

## 6. Where it lives

| | |
|---|---|
| **`hex_field`** | the distance functions, the region/boundary writers, `House`, `house_draw`, `house_roof`, `house_facets`, the stencil variants |
| **crawler** | the type *values*, the **thickness/blocking/material table**, metres, the renderer |
| **not moved** | `hexroof`, `hexway` |

The thickness table is the library/consumer seam doing its job (`BUNDLE.md` decision 2):
**the mechanisms are closed** — area, boundary-edge, cell-band — **and the things are open**.
Crawler adds a hedge by adding a row; a fourth mechanism would be a library change.

`hexroof` stays crawler-side for now: a house's roof needs one segment distance that
`draw_seg` already computes, and pulling in cones, domes, vaults and `hexway::Track` to get
it would be a migration wearing a feature's clothes. Move it when the editor wants vaults,
on the `EdgeSet` merge's pattern (gate: `rooftest`/`vaulttest`/`roofmatchtest` unchanged).

---

## 7. Gates — and the two in `DRAWING-API` §8 that are blind

Each control has been run and seen red.

| gate | control that fires |
|---|---|
| **thickness** — every type's rendered thickness matches its metre value; nothing under 1.5 m occupies a cell | draw the fence as a cell: the barrier measures **1.5 m thick** |
| **closure** — a region's boundary edge set has no odd corner | *(by construction — the gate is that it stays a region boundary)* |
| **continuity** — a bare fence/partition run is edge-connected end to end | route it through a hex corner |
| **band sealing** — a thick wall is one 6-connected loop enclosing ≥1 cell | buffer rule, ties out: **2 parts, 0 enclosed** |
| **equivariance** ✅ — `footprint(g·spec) == g·footprint(spec)`, cells **and** edges, 12 orientations; per-side edge counts identical `[9 10 9 10]` and the axis histogram a permutation | the index-space rectangle: **not mirror-closed at either parity** |
| **facade order** ✅ — window left of door, outward frame, before and after flip | endpoints not exchanged: **24 of 24 reversed** |
| **outward normal** — `n · (massing normal) > 0`, all 12 × 4 | §1+§5.2 as written: **−1.000** |
| **roundness** — the band's radial spread falls with radius | the hex ring: **flat at 14.7 %** |
| **roof exactness** — interpolation vs analytic ≤ 1e-12 for a gable | ridge stopped at the wall: **0.43** |
| **roof/wall meeting** ✅ — every wall edge has a roof height above it; the eave is level **on the long sides** (`eave_spread` over a whole GABLE boundary reads the ridge-to-eave range by design, and over the halo ring is meaningless) | halo dropped: **38 edges** |
| **facet agreement** — facets at each stored cell centre == the stored height | perturb the pitch 10 % |
| **door** ✅ — clear width == n × 0.87 m; an opening deletes no edge (38 → 38) and no cell (27 → 27) | delete the edge instead of annotating: the run fragments |

> **Two gates in `DRAWING-API` §8 cannot see the faults they sit next to.**
>
> **§8.1 equivariance passes on a wall with a hole in it.** The buffer wall with ties
> excluded is **12/12 equivariant, 2 components, 0 enclosed**. Equivariance asks whether a
> shape moves correctly, never whether it *is* a shape. Sealing is a separate gate and
> neither implies the other.
>
> **§8.2's facade check defines its own subject.** Taking outward from `B − A` — the
> ordering under test — lets the broken rule supply its own notion of outward, and the
> control cannot fire until outward comes from the massing.
>
> `STATE.md` lesson 3 again, twice, by two routes it had not been caught by: *a check that
> passes for the wrong reason.* State what would have to break for a control to go red, and
> check that it is reachable.

---

## 8. Order

| | | effort | gate |
|---|---|---|---|
| **A** | distance functions + the region/boundary writer + the thickness table | S | thickness, closure, equivariance |
| **B** | thick bands: `fill_*` + the band; `draw_tower_hex`, `draw_octagon_hex` | S | band sealing; rad ≤ 5 identical; spread falls |
| **C** | the house: frame, sides, openings by edge count, inner walls, `house_flip` | M | equivariance, facade order, outward normal, continuity |
| **D** | the roof: `house_roof` + `house_facets` | M | roof exactness, facet agreement, eave, ponding |
| **E** | crawler: `stamp_house`/`stamp_round_tower`/the road painter become one-line callers; **the fence moves onto edges**; `Sim` carries `Heights` | M | `make test` green; `rad 2` cell set unchanged |
| **F** | `view3d`: fitted wall lines, wall tops from the roof, roof facets | M | a village at eye height, and the user's eyes |

**E carries plan #11's outstanding fence work** (`STATE.md` decision 6: *"the fence moves
onto it when `hexedge`'s materials carry it (P5)"*) — it is the same change as the house, so
it should not be a separate errand.

---

## 9. Open, deliberately

- **The fitted wall line is what the renderer draws** (§4). Until the fit lands, thin walls
  render as the raw zigzag/staircase (§4). That ordering risk is real: **F depends on the fit**, not
  just on D.
- **Which roof, which thickness.** Pitch, hip-vs-gable, material and wall thickness are
  *content* — `overland`'s scorer and the bundles decide them. No tables in `hex_field`.
- **Two shapes of the same type that touch** merge under connectivity alone
  (`DRAWING-API` §10). Unchanged; nothing builds it yet.
- **`hexroof`'s migration**, when the editor wants vaults (§6).
- **Chimneys, dormers, porches, door leaves** — objects, not field features (`PROPS.md`).
  A 0.87 m doorway takes a door *leaf* as a prop, which `land.loft` already derives.
