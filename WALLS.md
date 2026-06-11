# WALLS.md — the triangle-subdivision wall model

How we build **straight walls with sharp corners** for *constructed* structures —
buildings, houses (with interior walls), castles, curtain walls (the authored / stencil
world; §9's 24-direction walls). **Distinct from the solid-rock dungeon**, where a wall
is whole filled hexes. This model is for structures that **stand in open space**.

## Scope — constructed structures, 2D now and 3D later

Its natural home is **3D**: full houses with **interior walls**, dividing rooms, across
storeys (cf. STENCILS layers). But the same model works in **2D now** for any
**non-dungeon constructed structure** — a building or castle standing in the landscape.
Interior walls are just more wall-bands inside the footprint. **The carved dungeon stays
solid-hex; this is everything that's *built*.**

## Key idea — a wall is a band between two faces, not a solid half-plane

A built wall **encloses a room** and has **space on both sides** — room inside, world
outside, a building standing in a landscape. So a wall is a **band with an inner and an
outer face**, never a filled half-plane (a solid fill can't have floor on *both* sides).
Its **thickness is free**: one triangle (thinnest) up to ~1–2 hexes. The triangle
subdivision is what lets both faces be **straight in many directions**.

## The model — subdivide, then keep the band between the faces

1. **Subdivide** each hex into a global triangular lattice fine enough that **each hex
   edge = 3 sub-segments** — shared across hexes, so a wall spanning hexes is continuous.
2. Take the wall's two **face lines** — inner and outer, parallel, offset by the wall
   **thickness**, each snapped to the 12/24-direction set. (Thinnest wall = the faces
   coincide → a single line.)
3. Classify each triangle **by its three vertices** (not its centroid — that's the bug
   that drops half the triangles where a wall falls between lattice rows): a triangle is
   **room** only if **all three** vertices are inside the inner face; **exterior** only if
   **all three** are outside the outer face.
4. **Eliminate those full-inside and full-outside triangles** — both become traversable
   floor.
5. **Every remaining triangle — any the band passes through — IS the wall.** One triangle
   thin or two hexes thick, it's the collision/volume truth. A closed polygon in → a
   walled room.

This band is **exact** and complete (no gaps), and it's the **collision data**. Walls in
the 3 lattice directions also come out **visually straight** straight away. Walls in other
directions get a clean band too, but their *faces* sawtooth — those need the next pass.

## Center-of-lines pass — straighten the non-aligned walls

The band is collision-correct, but a wall not in a lattice direction has **sawtooth
faces**. The center-of-lines pass straightens the *render* (the collision band is
untouched): per wall segment, take the band's **centerline** (the segment's own
direction) and offset by ±half-thickness for the two visible faces; **corners are the
miter intersection of adjacent segments' face lines**. A door is a span left open on one
segment; its jambs come out *nearly* straight (the band's regular sawtooth still shows at
the opening) — good enough for now, perfectible later with a **pattern-matching pass** on
the regular sawtooth. This is far simpler than collapsing a hex zig-zag because the band's
sawtooth is *regular* (the user's "center of lines, far simpler model").

## Why this model (vs the alternatives)

- **Thin or thick, space on both sides** — the only model that lets a building stand in a
  field (room inside, world outside, a wall of any thickness between). Solid fill can't.
- **Interior walls fall out** — a house's dividing walls are just more bands inside the
  footprint; nothing special needed. This is why it's the right base for 3D houses.
- **Straight + sharp + 24-direction for free** — the sub-edge orientations *are* §9's
  direction set; roads, rivers, curtain walls are all the same operation.
- **Simpler than the midpoint-collapse model** — collapsing every other wall to edge
  midpoints (zig-zag vs already-aligned runs treated differently) *works*, but is far
  harder to reason about and has more edge cases. This is a flat per-triangle test.
- **Sound but untested our way** — a design, not shipped moros code (moros has only the
  wall *data* `h_wall_n/ne/se` + 3D corner-to-corner mesh emitters). Validate by
  rendering the rectangle / room / room+door and confirming straight + sharp.

## Two wall paradigms coexist

- **Solid-rock dungeon** (`is_wall` per hex, carved): walls are whole filled hexes; the
  render is their boundary outline. Keep the current (rounded `wallgeo`) render for now.
- **Constructed structures** (this model): wall-bands (one triangle → two hexes) in 24
  directions, room inside + world outside, interior walls inside, **a door = a gap in the
  band**.

Caves are carved, castles are built — the renderer carries both.

## Collision / binary wall data

- The **wall band is the barrier** (non-traversable); floor on **both** sides is
  traversable. A **door** = remove a span of the band's triangles.
- Record the band in the binary wall data as non-traversable so collision matches the
  render exactly — there's no solid interior to reason about.

## Validated (2D prototype)

Rendered + corner-tested in 2D (Python reference, `tools/wallproto`): lattice-aligned
rhombus (auto-straight), axis rectangle (90° sides straightened by the center-of-lines
pass), thin → ~1-hex → thick walls, and a door (real collision gap in the band + clean
jambs in the straightened render). **Corner tests pass:** rect corners exactly 90°,
rhombus 60°/120°, miter offsets correct, the band covers every corner. The vertex-based
straddle rule (step 3) was the fix for the earlier "top wall misses half its triangles".

## Open (pin at the loft port)

- representation is free again — the loft bugs that forced flat per-triangle flag
  arrays (nested-vector and store-desync panics) are fixed; pick whatever reads best.
- How the wall lines / building polygon (+ interior walls, doors) are specified — the
  12/24-direction snap, from a stencil.
- Exact subdivision layout + count vs the hex grid (the 3-per-edge triangulation;
  pointy-top, to match crawler's hexgeo).
- The two render faces carried to 3D (the band's volume).
