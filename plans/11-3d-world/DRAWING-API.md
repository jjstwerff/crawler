# DRAWING-API — detailed requirements

Implementation spec for the design in [`DRAWING.md`](DRAWING.md). That file says *why*; this
one says *what must exist and what must be proved*. Written to be implemented cold.

**Placement:** all of it in **`hex_field`** (`loft-libs-world`). No new dependencies — it uses
`lattice_k`/`lattice_m`, `HexSet`, `Labels`, `EdgeSet`, `Stencil`, `cell_rot`, `cell_mirror`,
all already there.

---

## 1. Conventions

| | |
|---|---|
| cell centre → world | `x = lattice_k(q,r) * 0.8660254037844386`, `y = lattice_m(q,r) * 0.5` |
| one hex step | `HEX_LEN = 1.7320508075688772` (√3) world units |
| sizes | given as **integer counts of hex steps**, converted internally (`n * HEX_LEN`) |
| rotation | `rot` 0–5, 60° steps: `θ = rot * π/3` |
| mirror | `mir` boolean. `(rot, mir)` together are the **12 orientations** — the D6 the lattice has |
| local frame | `u = (cos θ, sin θ)`, `v = (−sin θ, cos θ)`; mirror negates the local x coordinate |
| default half-width | `HEX_LEN / 2` — a wall one cell thick |

**Angles** are radians, counter-clockwise, 0 along +x.

**Every routine writes two layers together:** occupancy into a `HexSet` and the cell's **type**
into a `Labels`. A routine never writes one without the other.

---

## 2. The one rasterise rule

> A cell belongs to a shape **iff the distance from its centre to the shape's geometry is
> ≤ `halfwidth`**.

This is the only rule. Every verb below is this rule over a different geometry, and no verb may
index-walk the grid (`for qq in 0..ww` over offset coordinates) — that is the parity bug
`DRAWING.md` exists to kill.

| geometry | distance |
|---|---|
| segment `A→B` | point-to-segment distance (clamp the projection parameter to `[0,1]`) |
| arc `(c, r, a0, a1)` | `abs(‖p − c‖ − r)`, **and** the angle of `p − c` must lie in `[a0, a1]` |
| circle `(c, r)` | as arc, with no angular test |
| octagon `(c, apothem)` | min distance over its 8 side segments |

**Angular containment** must handle wrap: bring the angle into `[a0, a0 + 2π)` by adding `2π`
while below `a0`, then test `≤ a1`.

**Octagon orientation is FROZEN** — one flat side on the world x-axis, matching the existing
`form_octagon`. Vertices sit at `22.5° + k·45°` at radius `apothem / cos(22.5°)`. An octagon is
8-fold and the grid 6-fold, so a free orientation is not representable and must not be offered.

---

## 3. Primitive verbs — world space

```
draw_seg    (cells, types, x0, y0, x1, y1,        halfwidth, type)
draw_arc    (cells, types, cx, cy, r, a0, a1,     halfwidth, type)
draw_circle (cells, types, cx, cy, r,             halfwidth, type)
draw_octagon(cells, types, cx, cy, apothem,       halfwidth, type)
erase_seg   (cells, types, x0, y0, x1, y1,        halfwidth)
erase_arc   (cells, types, cx, cy, r, a0, a1,     halfwidth)
```

`erase_*` clear occupancy and reset the type to `-1` (the `Labels` empty value). They exist so
an opening can be cut from a wall already drawn.

Each iterates the `HexSet`'s own extent. Cost is O(extent) per call, which is acceptable for
building-sized shapes; a caller drawing many shapes into one large field should pass a
sub-extent.

## 4. Hex-anchored wrappers

Callers work in cells, not floats. These convert and delegate:

```
draw_wall_hex  (cells, types, q0, r0, q1, r1,     halfwidth, type)
draw_tower_hex (cells, types, cq, cr, rad,        halfwidth, type)
draw_octagon_hex(cells, types, cq, cr, rad,       halfwidth, type)
draw_road_hex  (cells, types, q0, r0, q1, r1,     halfwidth, type)
draw_road_arc_hex(cells, types, cq, cr, rad, a0, a1, halfwidth, type)
```

`rad` is **the count of hexes a straight line covers before leaving the shape**, so the world
radius is `rad * HEX_LEN` and the apothem likewise. Roads and walls differ **only** in the
`type` written — never in geometry or code path. Whether a type blocks is the consumer's
business, expressed through its shape table (§7).

---

## 5. The house

### 5.1 Structure

```
pub struct House {
  ho_cx, ho_cy   : integer      // centre cell
  ho_wid, ho_dep : integer      // extent in hex steps
  ho_rot         : integer      // 0..5
  ho_mir         : boolean
  op_side        : vector<integer>   // 0..3
  op_t0, op_t1   : vector<float>     // interval along that side, in [0,1]
  op_kind        : vector<integer>   // OPEN_DOOR | OPEN_WINDOW
  op_n           : integer
  iw_sa, iw_sb   : vector<integer>   // inner wall: from side a to side b
  iw_ta, iw_tb   : vector<float>
  iw_n           : integer
}

pub const OPEN_DOOR = 1
pub const OPEN_WINDOW = 2
```

```
house_new(cx, cy, wid, dep, rot) -> House
house_opening(h, side, t0, t1, kind)
house_inner(h, side_a, t_a, side_b, t_b)
house_flip(h) -> House
house_draw(h, cells, types, wall_type, halfwidth)
house_side_point(h, side, t) -> (x, y)
house_side_normal(h, side)    -> (nx, ny)     outward, unit
```

**Inner walls are anchored to the boundary**, from `(side_a, t_a)` to `(side_b, t_b)`. This is
deliberate and is what makes them flip correctly for free: they are expressed in the same
`(side, t)` vocabulary as openings, so whatever the flip does to a side and a parameter, it
does to both.

### 5.2 Side numbering and the frame rule — the load-bearing part

Sides are 0–3, in local units where the rectangle spans `[−1,1] × [−1,1]`:

| side | A | B | outward |
|---|---|---|---|
| 0 | `(+1, −1)` | `(+1, +1)` | `+u` |
| 1 | `(+1, +1)` | `(−1, +1)` | `+v` |
| 2 | `(−1, +1)` | `(−1, −1)` | `−u` |
| 3 | `(−1, −1)` | `(+1, −1)` | `−v` |

> **THE RULE: the outward normal is always 90° clockwise from `B − A`** — i.e. `n = (dy, −dx)`
> normalised. `t` runs `A → B`, which is what an observer standing outside reads left-to-right.

**When `ho_mir` is set, the side's endpoints are mirrored AND SWAPPED:**

```
ends(s) with mirror  =  ( −Bx, By, −Ax, Ay )      // negate local x, exchange A and B
```

The swap is not a detail, it is the mechanism. Mirroring reverses the plane's handedness, so
holding `n = (dy, −dx)` outward forces the exchange. The consequence is that **`t` is
unchanged by a flip**, and the facade still reads in the same order.

### 5.3 `house_flip`

```
house_flip(h)  =  copy of h with ho_mir = !ho_mir
```

**Nothing else changes.** No side remapping, no `t → 1 − t`, no touching inner walls. The frame
rule in §5.2 already routes every `(side, t)` to the mirrored wall while preserving reading
order. If an implementation finds itself remapping sides or parameters, the frame rule is wrong
somewhere and that is the bug to fix.

### 5.4 `house_draw` semantics

1. Draw all four sides with `draw_seg`, type `wall_type`.
2. Draw every inner wall with `draw_seg`, same type.
3. For each opening of kind `OPEN_DOOR`, `erase_seg` along the sub-segment
   `house_side_point(h, side, t0) → house_side_point(h, side, t1)`.
4. Openings of kind `OPEN_WINDOW` **do not alter cells** — a window sits above the ground
   course, so it belongs to the feature/elevation layer, not the footprint.

---

## 6. Stencil variants

Every verb has a stencil form returning a `Stencil` rather than drawing into a caller's field:

```
stencil_seg(...)      stencil_arc(...)      stencil_circle(...)
stencil_octagon(...)  stencil_house(h, wall_type, halfwidth)
```

Requirements:

- The returned `Stencil` is sized to the shape's own bounds **plus the halo a rim edge needs**.
- It carries **cells, labels and edges**. A stencil that drops its labels drops the shape class
  and the fit downstream becomes a guess again.
- `stencil_*` and the direct `draw_*` must agree: stamping the stencil into a field must
  produce exactly what drawing directly into that field produces, cells **and** edges.

---

## 7. The shape table (the library/consumer seam)

The library never learns what a tower or a road is. The consumer passes a
`shapes: vector<integer>` indexed by type value, giving that type's class:

```
SHAPE_LINE = 1     SHAPE_CIRCLE = 2     SHAPE_OCTAGON = 3
```

Shape classes are **mechanisms and closed**; wall and road type values are **things and open**
(`BUNDLE.md` decision 2). Adding a hedge is a consumer change; adding a fourth shape class is a
library change.

---

## 8. Validation — required gates, each with a control that must fire

A gate without a demonstrated failure mode does not count. Each row's control must be *run* and
seen red before the gate is trusted.

### 8.1 Footprint equivariance — every verb, all 12 orientations

> `footprint(g · spec) == g · footprint(spec)` for all 12 `g`.

Compare a shape drawn at orientation `g` against the shape drawn at identity and then moved by
the library's own `cell_rot` / `cell_mirror`. Applies to wall, tower, octagon, road, road-arc
and house.

- **Compare cells AND edges.** Use `edgeset_count_all` and `edgeset_equal`, **never**
  `edgeset_count` — the in-chunk count moves when the extent moves and cannot distinguish
  "the wall was lost" from "the wall is now owned by a halo cell". Rotating a walled ring
  already lost 8 of 18 stored edges this way (`hex_field 8308180`).
- **Control:** an index-space rectangle (`x0 + qq, y0 + rr`) must FAIL this at an odd `y0`.
  If it passes, the test is not seeing parity and proves nothing.

### 8.2 Facade order under flip — the house

> A window at `t = 0.2` and a door at `t = 0.5` on the same side: the window is on the outside
> observer's **left**, before and after `house_flip`.

Check it geometrically, not from the stored `t` — reading `t` back is a tautology. For side `s`
with outward normal `n`, the observer faces `−n`, so their left is `(n_y, −n_x)`. Assert
`(P_window − P_door) · left > 0` for the house and its flip, at all 6 rotations.

- **Control:** implement the naive `t → 1 − t` and the flipped facade must come back
  door-then-window. Without this the check passes trivially on a symmetric facade — which is
  why the fixture is asymmetric (`0.2` and `0.5`, never `0.25` and `0.75`).

### 8.3 Rasterise stability

> `draw_tower_hex(rad 2)` marks exactly the 12 cells today's `stamp_round_tower` marks.

Guards the migration: the small towers the game already builds must not move.

- **Control:** a 10% radius change must move the marked set.

### 8.4 Round is not octagon

> An octagonal tower and a round tower of the same size produce **different** cell sets, and a
> run of octagon type fits 8 faces where a run of circle type fits 1 arc.

This is the check that proves the **type** drives the fit rather than the geometry happening to
fit — the reason the octagon carries its own type at all.

- **Control:** draw the octagon with the round type; it must fit 1 arc, not 8 faces.

### 8.5 Stencil agreement

> `stamp(stencil_X(args))` equals `draw_X(args)` — cells, labels and edges — for every verb and
> all 12 orientations.

- **Control:** drop labels from the stencil and the comparison must fail.

### 8.6 Openings

> A door interval removes wall cells; a window interval removes none.
> A doored tower still fits **one** arc (openings do not split a run).

- **Control:** delete the opening record and the tower must fragment to 3 arcs — the measured
  behaviour today.

---

## 9. Acceptance

Done when:

1. Every verb in §3–§6 exists in `hex_field` with the stencil variant.
2. Every gate in §8 passes, **and each control has been observed failing**.
3. Crawler's `stamp_house`, `stamp_round_tower` and the road painter are one-line callers, and
   `make test` is green with the `rad 2` cell set unchanged.
4. `rad 8` fits one arc where it fits six straights today.

## 10. Deliberately out of scope

- **Two shapes of the same type that touch** merge into one run under connectivity alone. Needs
  a run id; nothing builds it yet.
- **Junction arbitration's side of the library boundary** — "nearest surface wins" is a
  geometric rule serving a physics decision. Decide with the code in hand.
- **Tagging cost** — nearest-surface per boundary edge over all surfaces is O(boundary ×
  surfaces). Time it on a 101×101 world before relying on it.
