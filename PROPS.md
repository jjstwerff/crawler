# PROPS.md — small detail, without a library of model files

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
