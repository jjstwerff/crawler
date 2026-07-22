# PROPS.md — small detail, without a library of model files

> **Implementation plan:** [`plans/10-props/`](plans/10-props/) — nine gated phases
> ([crawler#10](https://github.com/jjstwerff/crawler/issues/10)). This file is the design;
> that one is the order it gets built in.

Doors, windows with inset glass, drainpipes, chimneys, fences, carts, wagons, troughs,
streetlamps. **Not a folder of `.glb` files.** They are drawn the way houses are drawn — by
a function that emits geometry from parameters — and placed the way items are placed, on a
hex.

## Why they are objects, not field features

Measured against the scale contract (`SCALE.md`, one hex step = 1.5 m):

| prop | real | hex steps | |
|---|---|---|---|
| drainpipe, fence post | 0.10 m | 0.07 | object |
| streetlamp | 0.25 m | 0.17 | object |
| chimney, inset pane | 0.50 m | 0.33 | object |
| window | 0.60 m | 0.40 | object |
| single door | 0.90 m | 0.60 | object |
| handcart | 1.20 m | 0.80 | object |
| double door, fence panel | 1.8–2.0 m | 1.2–1.3 | field |
| trough, wagon | 1.6–3.5 m | 1.1–2.3 | field |

**Almost everything on the list is below one hex step**, so the rule this project already
established — for saplings (plan #9 T8), domestic spiral stairs and ordinary staircases
(plan #5 §12, SCALE.md) — applies unchanged: *below the resolution floor a thing is an
OBJECT, not a field.* Props are that rule's largest population.

That is not a limitation being worked around. It is the same boundary arriving for the
fourth time, and it is what makes props cheap: an object needs a position and parameters,
not cells.

## What a prop is

```
   prop = (kind, anchor, sub-cell offset, yaw, scale, seed)
```

- **kind** — an integer selecting a generator function. No file, no lookup table of assets.
- **anchor** — where it attaches (below).
- **sub-cell offset** — a deterministic hash of the cell, exactly as T9 places foliage
  cards. It is what stops a row of props reading as a grid, and it costs nothing to store.
- **yaw, scale, seed** — the variation that stops every instance being the same instance.
  The generator reads the seed; two lamps differ without two models existing.

Storage per prop is a handful of numbers on a hex — the same weight as an item.

## Anchors: most props hang off geometry that already exists

| anchor | attaches to | already exists as |
|---|---|---|
| `GROUND` | a hex, at terrain height | the height field |
| `WALL_FACE` | a point along a recovered wall surface | plan #5 `Surfaces` + the matcher |
| `WALL_OPENING` | a door or window **interval** on a surface | plan #5 P5 `Features` |
| `ROOF` | a point on a roof plane | plan #5 §13 roof profiles |

**Doors and windows are not new data.** Plan #5 P5 already models them as *surface
intervals* with `z0`/`z1` — a door is a stretch of wall whose material is passable, a window
a stretch that is transparent but not passable, both gated in `feattest`. The prop system
does not invent them; it **draws** what the field already holds. The physics and the picture
therefore cannot disagree, which is the same guarantee I-OPACITY gives foliage.

That is the whole economy of this design: a door already exists as *one interval on one
surface*. Rendering it costs a generator, not an asset.

## Inset glass, specifically

A window is two pieces: the **opening** (a surface interval, already there) and the **pane**,
recessed into it. The recess is the point — flush glass reads as a painted rectangle, and
`SCALE.md` puts a pane at 0.5 m, well under a hex, so it can only ever be an object.

The generator emits: reveal (the inset depth), frame, pane. The pane's material is the
*same* `opacity` the field already stores for that feature, so a shuttered window is dark in
the render because it is dark to `sight_clear` — one number, both consumers.

## Generators, not models

Each kind is a small function of the same shape as `add_house` or `mesh_gable`:

```
   mesh_door(w, h, seed)        mesh_window(w, h, inset, seed)
   mesh_chimney(h, flue, seed)  mesh_fence(len, posts, seed)
   mesh_trough(len, seed)       mesh_lamp(h, seed)
   mesh_cart(seed)              mesh_wagon(seed)
```

They compose from the primitives already in use — boxes, drums (`mesh_drum`), gables
(`mesh_gable`), tapered columns (`mesh_trunk`). **A cart is a box, two drums and a shaft.**
Nothing here needs a modelling tool.

## Cost, and why this scales

- **Authoring:** one function per kind, not one file per instance. Ten kinds cover the list.
- **Storage:** a few numbers per placed prop, on the hex it belongs to.
- **Variation:** from the seed, so a village of thirty houses has thirty different doors
  without thirty door models.
- **LOD:** a generator can emit fewer triangles at distance — an asset file cannot, without
  shipping a second asset.

## Open questions

1. **Who places them?** Hand-placed on hexes, or derived — every wall opening gets a door,
   every roof ridge a chimney, every field boundary a fence? Derived placement is consistent
   with everything else here, and would mean a village furnishes itself.
2. **Do props affect the field?** A cart blocks movement; a fence blocks movement but not
   sight; a trough holds water. That is `Materials` again — so a prop may need to *write* an
   edge material, not only draw geometry. If so, the physics/picture guarantee extends to
   props and the answer to (1) is almost certainly "derived".
3. **Kind as an integer, or a bundle key?** `BUNDLE.md`'s standing check says content lives
   bundle-side and mechanism engine-side. A prop kind is content; the generator is
   mechanism. Getting that seam right is what stops this becoming a hard-coded catalogue.

---

# Part 2 — the awkward cases, and why a wheel is the general one

A wheel is a drum on its side, and today that cannot be expressed. Chasing it turns up
**three** classes of hard case, not one, and the wheel is the cheapest of the three to fix.

## The diagnosis

Every primitive in the codebase **bakes the vertical axis in**: `mesh_drum`, `mesh_trunk`,
`mesh_crown` and `mesh_gable` all sweep `cos/sin` in *x,y* and run their length along *z*.
And the convenience transform, `mat4_trs(tx,ty,tz, ry, sx,sy,sz)`, offers **only a rotation
about Y** — so a sideways drum cannot be expressed at the primitive level *or* at the
transform level.

That is not an accident. It is the plan-view assumption of the whole stack showing through:
a footprint on hexes, extruded upward. It is exactly right for walls, towers, roofs and
trees — everything built so far — and it stops dead at the first object whose principal axis
is not vertical.

## Class 1 — a non-vertical axis (wheels, axles, gutters, ladders)

**Fix: primitives take an AXIS, not a z-range.**

```
   mesh_drum(centre, axis, r0, r1, length, sides)
```

with the ring swept in the plane perpendicular to `axis`. The vertical case is `axis =
(0,0,1)` and nothing about towers changes. A wheel is `axis = (0,1,0)`. An axle is the same
primitive, thinner and longer. A gutter is a half-drum with a horizontal axis. A ladder rail
is a thin box along a tilted axis.

**One generalisation retires the whole class** — and the user's phrasing is the proof: if a
wheel is "a tower mounted sideways," then the tower primitive was over-specified, not the
wheel under-served.

Needed alongside it: `basis_from_axis(axis, roll)` — a stable orthonormal frame from one
vector, picking a reference that is not parallel to it. Without that, every caller
re-derives the same perpendiculars and they disagree at the poles.

## Class 2 — a prop meeting a surface at an angle

Harder, and not solved by axes. A **chimney through a pitched roof** must have its base cut
on the roof plane. A **fence on a slope** needs each panel to follow the ground while its
posts stay vertical. A **drainpipe** runs from the eave to the ground, so its *length* is a
consequence of where it is placed.

**Fix: give the generator a SEAT — the plane (or the height function) it meets — and let it
parameterise, not intersect.**

```
   mesh_chimney(seat_plane, h, flue, seed)      // base cut on the plane
   mesh_fence(a, b, ground_fn, posts, seed)     // posts plumb, rails follow
   mesh_drainpipe(top, ground_fn, seed)         // length derived, not given
```

This is the difference between *fitting* and *booleaning*. A boolean needs a CSG kernel and
produces geometry nobody specified; a seat is four numbers the generator already wants. And
the seats all exist already: roof planes come from the profile×distance table (plan #5 §13),
the ground from `terrain`/`Heights`, wall planes from the recovered surfaces (P2).

**This class is where the real work is.** Class 1 is a signature change; class 2 is a
parameter every generator must be written to respect.

## Class 3 — a prop that is an assembly

A cart is not a primitive with an awkward axis. It is **a body, two wheels, an axle and a
shaft**, each with its own frame relative to the cart's. Trying to make it one generator is
what makes the wheel look like a special case in the first place.

**Fix: a prop is a small tree of PARTS.**

```
   prop  = anchor transform + [ part, part, ... ]
   part  = (primitive, local transform, params)
```

Two levels, no more. `mesh3d` already provides exactly this — `Node` carries a `Mat4`, and
`mat4_mul` composes — so the assembly is a scene-graph node with children, which glTF then
exports natively. **Nothing new is needed except the discipline of using it.**

Worked through, the cart:

```
   cart
   ├─ body      box            local (0, 0, 0.55)                 1.2 × 0.7 × 0.4
   ├─ wheel L   drum axis Y    local (0, −0.42, 0.32)  r 0.32, len 0.07
   ├─ wheel R   drum axis Y    local (0, +0.42, 0.32)  r 0.32, len 0.07
   ├─ axle      drum axis Y    local (0, 0, 0.32)      r 0.04, len 0.90
   └─ shafts    2 × box        local (0.75, ±0.25, 0.5)
```

Five parts, two primitives, one seed. A wagon is the same list with four wheels and a longer
body. **The wheel stops being special the moment the cart stops being one object.**

## What this changes in the code

| change | size | why |
|---|---|---|
| `mesh_drum` takes an axis + a basis helper | small | retires class 1 entirely |
| every generator takes a seat parameter | medium | class 2, and it must be designed in, not retrofitted |
| props become part-lists, exported as child nodes | small | class 3; `mesh3d` already supports it |
| `mat4_trs` is Y-rotation-only | — | assemblies need `mat4_mul` of a real basis instead |

## The rule this yields

**A prop is a part-list in a local frame, seated on the surface it meets.** Every awkward
case seen so far is one of: the wrong axis (fix the primitive), the wrong seat (pass the
plane), or the wrong granularity (split into parts). None of them wants a model file, and
none of them wants a CSG kernel.

## Still open

- **Rotating parts.** A wheel that turns, a weathervane, a mill sail — the part frame would
  need to be time-varying. That is animation, deliberately out of scope here, but the
  part-list is the right place for it to arrive later.
- **Seats on curved surfaces.** A chimney on a *conical* tower roof meets a curve, not a
  plane. The recovered-form machinery (plan #5 §14) can hand back the cone, so the seat
  generalises from a plane to a surface — but no generator is written for that yet.

---

# Part 3 — props live on their own LEVEL

The mechanism already exists and is gated: **a level is the topological sheet a thing sits
on** (plan #5 §10). Two ways at different levels occupy the same cells and **never
arbitrate** — that is how a road crosses a railway, and how a canopy sits over an understory
(plan #9 T7). The `FieldCache` key is already `(chunk, level, version)`.

**Props go on a level of their own.** That is the right home, and it settles more than
storage.

## What the level buys, concretely

### 1. No arbitration with the built field
A cart standing in a gateway does not fight the gate's surface for that cell. A fence
crossing a field boundary does not merge with it. A lamp against a wall does not become part
of the wall. **Same cells, different sheets, no contest** — the exact guarantee the bridge
gate proved, now reused a third time.

Without it, every prop placement would be an arbitration problem, and `cut_arb`'s
nearest-wins rule would start deciding whether a wall or a barrel owns an edge. That is a
question nobody should have to answer.

### 2. Invalidation follows change frequency
This is the part that makes it more than tidy filing. The cache is keyed by level, so
**moving a cart invalidates the cart's level and nothing else** — the wall geometry, the roof
surfaces and the recovered forms are untouched.

Which suggests splitting props by *how often they change*, not by what they are:

| level | holds | changes |
|---|---|---|
| `L_FIXED` | doors, windows, chimneys, drainpipes, fences, lamps | when a building changes |
| `L_MOVABLE` | carts, wagons, barrels, troughs | constantly |

A wagon rolling through a village then rebuilds one small field and leaves the village
alone. **Invalidation granularity is a design choice, and the level key is where it is
expressed.**

### 3. It answers "do props affect the field?" — yes, on their own level
Open question 2 above. A prop writes materials to **its** level's `EdgeSet`, and a consumer
merges the levels it cares about:

- **movement** merges architecture + fixed + movable — a cart does block you;
- **sight** merges architecture + fixed, and reads the prop's own `opacity` — a fence blocks
  movement but not sight, which is exactly the palisade/chain-link distinction `sighttest`
  already gates;
- **structure** reads architecture alone — a barrel is not load-bearing.

So the physics/picture guarantee extends to props unchanged, and it does so **without** a
prop ever being able to corrupt the building it leans against.

### 4. Several props on one hex
A level is a *sheet*, not a slot, so it does not limit one prop per cell. Within the prop
level the records are a **bucketed list** — cell → first prop, then a next-pointer chain —
and the sub-cell offsets (Part 1) keep them visually distinct. A lamp and a trough on one
hex is one cell, one level, two records.

## Placement, now answered

Open question 1 was hand-placed versus derived. With levels in hand, **derived** is clearly
right: the prop level is a *derived* field, exactly like the L2 edge field — a pure function
of the architecture level plus a seed. So:

```
   architecture level  ──derive──▶  L_FIXED   (every opening gets a door, every
                                               ridge a chimney, every boundary a fence)
```

That means **a village furnishes itself**, it is reproducible from a seed, and it costs no
authored data at all. `L_MOVABLE` stays authored, because where a cart *is* is a fact about
the world rather than a consequence of the buildings.

And because the derivation is a pure function of a level that has its own version, the
furnishings rebuild exactly when the buildings change and never otherwise.

## The revised rule

> **A prop is a part-list in a local frame, seated on the surface it meets, recorded on a
> level chosen by how often it changes.**

Parts 1 and 2 said what a prop *is*. This says where it *lives*, and in doing so retires
both open questions: placement is derived, and props affect the field on their own sheet.

---

# Part 4 — things that move

Doors and windows opening, shutters, wheels turning, piston gear. Five cases, **three
classes**, and one shape underneath all of them:

> a part's local transform stops being a constant and becomes **`f(state)`**, where the
> state is **one number per prop** — not per part.

Part 2 said `part = (primitive, local transform, params)`. This is the only change that
sentence needs.

## Class A — one hinge, one angle
Door, casement window, awning window, shutters. A part frame parameterised by a single
angle about a hinge axis. Shutters are the same thing twice with opposite sign. A casement
hinges about a vertical axis, an awning about a horizontal one — **already covered**, because
Part 1's primitives take an axis.

## Class B — continuous rotation driven by travel
A wheel. The phase must come from **distance covered**, never from a clock:

```
   phase = way_param(track, position) / (2π · r)
```

`way_param` is the milepost from plan #9 T3 — built for stair treads, and it is exactly the
quantity a wheel needs. **Accurate driving is then not something to get right; it is
something that cannot be got wrong**, because the phase is *computed from* the distance
rather than stored beside it and kept in step. A wheel driven by a timer desynchronises the
moment anything changes speed; one driven by the milepost cannot.

Wheel *slip* then becomes an opt-in term — `phase = (1 + slip) · d / 2πr` — a deliberate
effect rather than a bug you are always fighting.

## Class C — a linkage
Steam gear is the hard one and it is still closed form. Crank radius `r`, con-rod `L`, crank
angle `θ`:

```
   crank pin   = (r·cosθ, r·sinθ)
   crosshead x = r·cosθ + √(L² − r²·sin²θ)          the slider-crank identity
   con-rod     = the part between them; its angle falls out
```

Every part frame follows from `θ`, and `θ` is the wheel phase from Class B. So **the whole
valve gear is a pure function of distance travelled** — no keyframes, no animation data, and
the rods cannot drift out of phase with the wheels because they are derived from them.

## The two results that matter

### The door mechanism already exists, and is already gated
A door is a `Feature` — a surface interval whose material is passable or not (plan #5 P5).
Opening it is `material_set_solid`, which was written for **level-crossing barriers** (§8)
and gated there as costing **zero edge writes and not invalidating the L2 cache**:

```
   barrier down -> up:  surf sum 340 == 340,  mat sum 192 == 192,  cache still HIT
```

So a town's doors may open and shut freely without touching the field. That gate was
written for a railway and it is, unchanged, the door-opening mechanism.

And it keeps the physics/picture guarantee through the motion: a door that *looks* open
*is* open, because one number drives both.

### Animated state must never be geometry
The mesh is static; the **node transform** moves. glTF nodes carry a `Mat4`, so swinging a
door leaf costs a matrix, not a rebuild. If opening a door rebuilt its mesh, a village would
thrash the cache every time someone went indoors.

Which fixes how finely to split a part-list — the open question Part 2 left:

> **Part granularity follows degrees of freedom.** Split where something moves independently;
> merge where it does not.

A door leaf, a shutter, a wheel, a con-rod each earn their own part. A window's frame and
reveal do not — they never move relative to the wall.

## The principle underneath

**Store decisions; derive consequences.**

| state | kind | why |
|---|---|---|
| door angle, shutter | **stored** | someone opened it — it is a fact about the world |
| wheel phase | **derived** from the milepost | a consequence of motion |
| piston phase | **derived** from wheel phase | a consequence of a consequence |

Derived state costs nothing to store and **cannot** desync. Stored state is one float on the
prop record. Neither is animation data.

## Still open

- **A door standing open occupies space.** Its material contribution is a function of state
  too, so the swept position wants edges on the prop level. By the barrier result a material
  change on already-marked edges is free, but *which* edges an open door marks is not yet
  worked out.
- **Where does state live?** `L_MOVABLE` holds the props; a door is on `L_FIXED` but its
  angle changes constantly. Either doors move to a third level, or state is separated from
  placement — the second is probably right, since the door has not moved, only turned.
