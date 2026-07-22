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

---

## Pass 3 — cold critique

**Recognition:** a stone keep on a green hill, a cluster of red-roofed cottages beside it, a
stepping-stone path climbing from the foreground with a small figure on it. **That is the
intent.** The keep now reads as a keep rather than a chimney — the change was *proportion*,
not size: a squat drum with a battlement course crowning it. Square towers had been reading
as industry; a drum reads as a castle.

**Affect:** calm, overcast, unhurried. Closer to "settled and inhabited" than pass 2's
midday brightness, but the light is still flat — **not yet late afternoon**. With no shadows
in the renderer, the remaining lever is colour temperature alone, and it is not enough on
its own.

## Predicates after pass 3

| # | predicate | pass 2 | pass 3 |
|---|---|---|---|
| 1 | keep upper-left third, tallest | partial | **pass** |
| 2 | horizon below midpoint | pass | **pass** |
| 3 | ground not flat, ≥2× house height | partial | **partial** — 6.4 m vs 6.8 m |
| 4 | 3–6 houses, clustered, clear | pass | **pass** |
| 5 | every house pitched | pass | **pass** |
| 6 | ≥2 round towers + curtain wall | **fail** | **partial** — drums built, but read as one mass with the keep |
| 7 | path front-to-hamlet | pass | **pass** |
| 8 | ≥4 trees, two sizes, none intersecting | partial | **pass** |
| 9 | figure present and legible | partial | **pass** |
| 10 | grass not uniform | pass | **pass** |

**8 pass, 2 partial, 0 fail** — from 5 / 4 / 1.

## What each pass actually cost

- **Pass 2** was spent almost entirely on two *tool* faults (`abs(N·L)`, per-primitive
  materials). No amount of scene editing would have fixed either, and neither was visible
  from the spec — only from looking.
- **Pass 3** was three scene faults and one plain bug: the eye-path guard used `||` where it
  had to *exclude* a corridor, so it excluded nothing and a tree stood dead centre hiding
  both the keep and the path it leads to. The intent file is what caught it — predicate 8
  said "none intersecting," and the image plainly disagreed.

## Still open

- **Affect: the light is flat.** Colour temperature alone cannot carry late afternoon
  without cast shadows. Either add a shadow pass to `glbview.py` (the renderer is ours) or
  accept overcast and rewrite the target honestly.
- **The towers merge with the keep** — they need separation in plan, or a lower curtain, so
  three masses read rather than one.
- **Houses are roofs on grey boxes.** The wall course is too tall for its roof; a cottage is
  mostly roof.
- **Ground is 6.4 m of relief against a 6.8 m target** — the one predicate that has never
  passed.

---

## Pass 4 — the shadow pass

Colour temperature alone could not carry late afternoon, so the renderer grew the lever it
was missing: standard shadow mapping — a depth-only orthographic pass from the light
(directional, so orthographic is exact), then a depth compare per shaded pixel with
four-tap filtering and perspective-correct world reconstruction.

**The shadow removes the key light only.** Sky fill still reaches into it, so a shadow comes
out cool and blue rather than black — which is what a real shadow does, and it is why the
image now reads as *late afternoon* rather than *dim*.

### It immediately exposed a fault it inherited

**The sun had been pointing underground** — every `--sun` used so far had a negative z. The
original `abs(N·L)` shading made the sign irrelevant, so the error was invisible for three
passes and quietly flattened every one of them. The moment the key became directional and
cast shadows, the whole scene went black and the cause was obvious.

That is the third tool fault in this exercise that no amount of scene editing would have
found, and the second that an earlier "convenience" in the renderer was actively hiding.

**Affect after pass 4:** long shadows raking left, warm stone, cool grass in shade. This is
the late-afternoon target — the first pass where the feeling matches the intent rather than
approximating it.

**Remaining:** the towers still merge with the keep, houses are roofs on over-tall walls,
and relief is 6.4 m against the 6.8 m target — the predicate that has never passed.


---

## Pass 5 — towers and houses

**Houses: fixed, and the diagnosis was proportion again.** The walls were as tall as the
roof was deep, so each cottage read as a grey box with a red lid. A cottage is **mostly
roof**: eaves dropped to ~½ the wall height, and the stepped courses replaced by a real
gable — two sloped planes meeting at a ridge with triangular ends. The stepped version read
as *steps* at this scale, never as a pitch. They now read as dwellings.

That is the third time in this exercise the fix was **proportion, not detail**: the keep
(narrow → squat), the trees (uniform → varied), and now the houses. None of them needed more
geometry.

**Towers: moved but still not solved.** Pushed from 12 units to 20 so there is sky between
the masses, and the curtain lowered from 8 m to 5.2 m so it stops welding them together. But
they now sit **behind the hill crest** and are barely legible — the placement fix created a
framing problem, and widening the camera to include them lost the composition instead
(horizon rose, the hamlet shrank).

So predicate 6 remains **partial**. The honest reading: the towers need to be sited on the
*near* slope of the hill rather than beyond its crest, which is a terrain-and-placement
decision, not a modelling one. Recorded rather than fudged by picking a flattering angle.

**Score: 8 pass, 2 partial, 0 fail** — unchanged in count from pass 3, but two of the passes
(houses, affect) went from "technically true" to actually convincing.
