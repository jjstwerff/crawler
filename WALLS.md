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
3. Classify each small triangle: **inside the inner face** (→ room floor), **outside the
   outer face** (→ exterior floor), or **between the faces** (the wall band — for the
   thin case, the triangles the single line straddles).
4. **Eliminate the full inside and full outside triangles** — both become traversable
   floor.
5. **Keep the band between the faces — that IS the wall.** One triangle thin or two hexes
   thick, it traces straight faces. A closed polygon in → a walled room. **Corners are
   intrinsic** where two walls' bands meet.

That's the entire straightener: the wall is *the triangles between two straight face
lines*. No outline walk, no vertex merging, no angle math — just per-triangle side-of-line
tests. Exact at the triangle resolution; a finer lattice → straighter.

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

## Open (pin at implementation)

- Exact subdivision layout + count (the 3-per-edge triangulation; flat-top vs pointy-top).
- Face-line offsets for the standard thicknesses (1 triangle, 1 hex, 2 hexes) + the two
  render faces.
- How the wall lines / building polygon (+ interior walls) are specified (12/24-dir snap).
- loft-safe representation — flat per-triangle flag arrays + index-writes (no nested
  vectors / no struct-field hash; cf. loft#290).
