# Intent — castle and hamlet in a landscape

Frozen **before** any geometry. Not to be edited to match what gets built (goalpost drift).

## Target feeling

**Settled, inhabited, late afternoon.** Somewhere people have lived a long time — not
dramatic, not threatening. The castle is old and the hamlet beneath it is ordinary. A viewer
should think "someone walks that path every day," not "a fortress guards a frontier."

## Composition (Stage 0 — decided before objects exist)

- **Focal point: the castle keep, on the upper-left third.** Not centred — centred is static.
- **Horizon low**, about the lower third, so sky carries weight and the hill reads as rising.
- **Eye path:** figure at the front edge → path → hamlet roofs → up the hill → keep.
- **Scale contrast is the main device:** one 1.75 m figure, houses ~4× that, keep ~10×.
  The figure is what makes the rest legible.
- **Negative space:** open grass in the lower right, so the built mass is not everywhere.

## Checkable predicates (gestalt level)

Positional ones are in thirds, not pixels — pitched where the eye can actually judge.

1. The keep's silhouette is in the **upper-left third** and is the tallest thing.
2. The horizon sits **below the vertical midpoint**.
3. **Ground is not flat** — a hill rises left-to-right toward the castle; the height
   difference across the frame is at least 2× a house's height.
4. There are **3–6 houses**, clustered, none touching the castle wall.
5. Every house has a **pitched roof** (a gable), not a flat top.
6. The castle has **at least two round towers** and a curtain wall connecting them.
7. A **path** connects the front of the frame to the hamlet.
8. **Trees**: at least 4, of two visibly different sizes, none intersecting a building.
9. The **figure** is present, at the front, and reads as roughly ⅓ of a house's height.
10. Ground colour is **not uniform** — grass varies, so it does not read as a painted plane.

## Known floor (named up front)

Flat single-colour shading, no textures, no alpha, no shadows in the renderer. So:
**"believable" here means believable MASSING, SCALE and ARRANGEMENT** — not surface realism.
Texture is faked only by colour variation across many small meshes. Photoreal is out of
reach and not attempted; the target is confident stylisation (skill §5: pick a side).

## What would make this fail

- Reads as "toy blocks on a green plane" → massing/regularity failure, not detail failure.
- Everything the same size → scale contrast lost, figure not doing its job.
- Castle and houses looking like the same object at two sizes → no vocabulary difference.

---

## Pass 2 — cold critique (read from the image, not the intent)

**Recognition:** a stone tower with a red cap on a grassy hill, red-roofed structures
half-hidden behind identical mushroom trees, a pale stepping-stone path climbing to it.
The tower reads more as a **chimney or a mill** than a keep — too narrow, too square, too
tall for its base. The houses read as roofs without visible walls.

**Affect:** pleasant, low-stakes, midday. Not the "settled, inhabited, late afternoon"
target — the sun is too high and the grass too bright.

## Predicates — honest scoring after pass 2

| # | predicate | verdict |
|---|---|---|
| 1 | keep in the upper-left third, tallest | **partial** — upper third, but centre-left |
| 2 | horizon below the midpoint | **pass** |
| 3 | ground not flat, ≥2× house height | **partial** — 6.4 m against a 6.8 m target |
| 4 | 3–6 houses, clustered, clear of the wall | **pass** (5) |
| 5 | every house pitched, not flat | **pass** — stepped gable |
| 6 | ≥2 round towers + curtain wall | **fail** — towers are boxes, not round |
| 7 | path front-to-hamlet | **pass** |
| 8 | ≥4 trees, two sizes, none intersecting | **partial** — sizes vary, but all identical shape |
| 9 | figure present, ~⅓ a house height | **partial** — present but very small in frame |
| 10 | grass not uniform | **pass** |

## Two tool-level faults found and fixed this pass

1. **`abs(N·L)` shading crushed every vertical face** to the ambient floor, so walls, roofs
   and trunks all rendered the same brown and the palette carried no information. Replaced
   with a hemisphere term plus a warm key.
2. **glTF binds a material to a mesh PRIMITIVE, not a node.** Every node sharing one
   `cube()` mesh therefore took a single material — whichever was written last. That, not
   the lighting, was why the first render was uniformly brown. One cube mesh per material.

Both are taxonomy #2 (tool-can't-express-it) and neither was visible from the spec.

## NOT CONVERGED — named next passes

- **The keep is a chimney.** Wider base, battlement course, fewer storeys — a keep is
  squat, a chimney is slender. This is the biggest recognition gap.
- **Round towers are boxes** (predicate 6 outright fails). `mesh_walls_fitted` already
  produces smooth arcs from a traced disc; the towers should be built that way rather than
  as scaled cubes.
- **Trees are the generic regular icon** — nine identical lollipops. Skill §"Minimal ≠
  symbolic": regularity reads as *abstraction*. Vary crown radius, height, lean and tint per
  tree, and use plan #9's real crowns rather than one primitive.
- **Affect: it is midday.** Lower the sun, warm the key, cool the ambient, lengthen nothing
  (no shadows in the renderer — a named floor).
- **Clutter:** trees stand in front of the hamlet and hide it. Move them off the eye-path.
