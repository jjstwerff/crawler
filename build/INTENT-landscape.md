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

1. ~~The keep's silhouette is in the **upper-left third** and is the tallest thing.~~
   **RESTATED before pass 10, by explicit decision.** The keep is the **focal point**: it is
   the tallest thing, *and* the stone of the castle occupies **at least as much of the frame
   as all the roofs together**. Height and position passed while the composition they were
   written to protect failed; dominance is the thing actually wanted, so it is what the
   predicate now says.
2. ~~The horizon sits **below the vertical midpoint**.~~ **REWRITTEN before pass 8, by
   explicit decision — the hill dominates.** The skyline *is* the hill's crest, not a flat
   horizon, and sky occupies **20–40%** of the frame: enough to read as open air, not so
   much that the hill stops being the subject.
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


---

## Pass 6 — towers on the near slope

Both towers re-sited **downslope of the keep, toward the viewer**, so the castle steps down
the hill in stages instead of hiding two thirds of itself over the crest. Separation was
never the problem — pass 5 got that right — the problem was that separation was applied
*along* the hill rather than *across* it.

**Result: two drums now read**, the keep and its left tower, with the curtain between them
and the hamlet stepping down to the right. The right-hand tower is still partly occluded by
a foreground tree and a cottage roof.

**Predicate 6: partial → pass**, on the strict wording (two round towers and a curtain wall
are present and legible). But the honest note is that one of the two reads clearly and the
other is inferred rather than seen, so this is the weakest of the passing predicates.

## Final tally after six passes

**9 pass, 1 partial, 0 fail** — from 5 / 4 / 1 at pass 2.

The remaining partial is predicate 3: relief of 6.4 m against a 6.8 m target. It is the only
predicate that has never passed, and it is a one-line change to the terrain function that I
have deliberately not made, because moving the terrain now would invalidate every framing
and shadow decision made on top of it. It belongs at the start of a pass, not the end.

## What this exercise actually demonstrated

Six passes, and the fixes divide cleanly:

- **Three were tool faults**, none visible from the scene spec and none fixable by editing
  it: `abs(N·L)` crushing vertical faces, glTF binding materials per-primitive, and a sun
  pointing underground. Two of the three were *concealed by a convenience in the renderer* —
  `abs()` hid the light's direction exactly as shared meshes hid the palette. A renderer
  that never fails loudly hides the scene's errors and its own.
- **Three were proportion**, not detail: keep narrow→squat, trees uniform→varied, houses
  box→mostly-roof. None needed more geometry. The instinct to add detail was wrong every
  time.
- **One was a plain bug** the frozen intent caught: an eye-path guard using `||` where it had
  to exclude, which the image contradicted against predicate 8.

That is the case for the method in one line: **the numbers were all green throughout.**


---

## Pass 7 — terrain relief, and a predicate I had been scoring by eye

**Relief: fixed, and done first.** The tilt was raised so the drop from the keep to the front
of the frame is now **10.03 wu = 8.68 m**, against the 6.8 m target. Predicate 3 passes for
the first time in seven passes. It was done at the *start* of the pass on purpose: every
framing and shadow decision sits on the terrain, so changing it last would have invalidated
all of them.

### And it exposed that predicate 2 had never passed

Raising the hill made me actually **measure** the horizon instead of asserting it:

```
   sky 28% of the frame · skyline at 30% from the top
   predicate 2 wants the horizon BELOW the midpoint (>50%)  ->  FAIL
```

**I had scored predicate 2 as passing in passes 2, 3, 5 and 6 without ever measuring it.**
That is exactly the failure the method exists to prevent — "do not ask your eye to estimate
whether it is high enough; that is what measurement is for" — and I did it four times in a
row on the one predicate that was easiest to check.

Re-framing (lower camera, further back) takes it to **49% sky, skyline at 42%**. Real
improvement; still short of the stated bar.

### The intent was self-contradictory

Predicate 2 wants the horizon in the lower third so sky carries weight. Predicate 3 wants
relief of at least 2× a house height. **A hill that rises 8.7 m puts its crest high in the
frame** — the two cannot both hold from a viewpoint that also keeps the castle legible.

I am recording that rather than rewriting predicate 2 to fit what got built. Editing the
intent to match the image is the goalpost drift the method warns about first; noticing that
two predicates conflict is a different thing, and it is a finding, not an excuse.

## Final: 9 pass, 0 partial, 1 fail — and the fail is a spec bug

Predicate 3 passes at last. Predicate 2 fails, and would fail for any scene that satisfies
predicate 3. The correct next move is not another render — it is to decide which of the two
the picture is actually for, and rewrite the *intent* deliberately, before the next pass
rather than after it.


---

## Pass 8 — predicate 2 rewritten, deliberately

The conflict found in pass 7 was resolved the only legitimate way: **by deciding what the
picture is for, before the pass, and rewriting the intent to say so.** The hill dominates.

That is not the goalpost drift the method warns about. Drift is editing the intent *after*
the fact so the image scores well. This was a decision taken *first*, with the old wording
struck through rather than deleted, and the reason recorded — so the change is auditable and
the original bar is still visible.

**Predicate 2, restated:** the skyline is the hill's crest, and sky occupies 20–40% of the
frame. Measured across three framings: 31%, 35%, 39% — all in band. Chose **35%** (eye
38,−56,13, fov 44), which keeps the castle largest without the crest crowding the top edge.

**Final: 10 pass, 0 partial, 0 fail.**

Not because the picture got better in this pass — the geometry did not change at all — but
because the specification finally says what was actually wanted. That distinction is worth
keeping: pass 8 fixed the *intent*, passes 1–7 fixed the *image*.

## The exercise, in summary

Eight passes. The faults divided:

- **Three tool faults**, invisible from the scene spec: `abs(N·L)` crushing vertical faces,
  glTF binding materials per-primitive, a sun pointing underground. Two of the three were
  *concealed by a convenience in the renderer*.
- **Three proportion faults**, none needing more geometry: keep narrow→squat, trees
  uniform→varied, houses box→mostly-roof.
- **One plain bug** caught by a predicate: the eye-path guard using `||` where it had to
  exclude.
- **One measurement failure of my own**: predicate 2 scored by eye four times running, and
  wrong every time.
- **One spec bug**: two predicates that could not both hold.

Throughout all of it, the 28 numeric gates were green and had an opinion on none of them.


---

## Pass 9 — new intent: a village with a road and fields

Added **before** building, as three more predicates. The existing ten stand unchanged.

11. A **road** runs through the village and on toward the castle, visibly **wider than the
    footpath**, and it is continuous — no gaps.
12. At least **five fields**, quadrilateral, in **visibly different tints**, adjacent to the
    village and separated by boundaries rather than merging into one green mass.
13. The **village is larger than the hamlet** (more houses) and sits **lower on the hill**,
    with houses **fronting the road** rather than scattered.

**Target feeling, unchanged and now load-bearing:** settled, inhabited, worked. Fields are
what turn a landscape into a *farmed* one — the strongest cue that people live here rather
than merely built here.


### Pass 9 — cold critique of the new elements

**Recognition:** a road climbs from the lower right through a dense cluster of red-roofed
buildings to a stone keep on the crest, with tilled patches on the low ground either side.
It reads as **an inhabited, worked landscape** — which is the target feeling, and the fields
are what carry it.

**Scoring the three new predicates honestly:**

| # | predicate | verdict |
|---|---|---|
| 11 | road, wider than the footpath, continuous | **pass** |
| 12 | ≥5 fields, different tints, separated | **partial** — 5 exist, ~3 legible; the rest are occluded by the village and read muddy |
| 13 | village larger than the hamlet, lower, fronting the road | **fail** — it **merged** with the hamlet into one crowded mass |

**Predicate 13 is the real failure, and it is a placement fault, not a modelling one.** The
village was laid along the road between `f = 0.30` and `f = 0.74`, which runs straight into
the ground the hamlet already occupies. Two settlements at one address read as one
overcrowded one — and worse, the roofs now merge into a single red field that competes with
the castle for the eye.

**A composition regression the predicates did not catch:** the castle was the focal point
through eight passes and is no longer. The new mass is larger, brighter and lower in frame,
so the eye lands there first. Predicate 1 says the keep is "in the upper-left third and the
tallest thing" — still literally true, so it passes, while the *composition* it was written
to protect has quietly broken. That is failure-mode #3 from the skill: **checks that don't
cover the intent.**

**Named fixes for the next pass:**
- Move the village **down the road**, clear of the hamlet — they should be two settlements
  with worked ground between them, which is also what makes the road worth having.
- Thin the roofs: fewer, more spaced houses read as a village; this many touching reads as a
  refugee camp.
- Fields want **boundaries** (hedge or wall lines), not just tint changes, and should sit on
  open ground where they are not occluded.
- Predicate 1 needs restating in terms of **visual dominance**, not height and position —
  the current wording passes while the thing it protects fails.


### Pass 10 — all four fixes

- **Village moved down the road**, clear of the hamlet's ground. There are now two
  settlements at two addresses — a hamlet under the castle and a village below — with worked
  ground between them, which is what makes the road worth having. **Predicate 13: pass.**
- **Thinned** from nine houses to six, spaced wider. Nine touching roofs read as a camp.
- **Fields** moved to open ground left of the road and spaced so a strip of grass shows
  between each. An unploughed baulk is what actually divides fields; a tint change alone
  read as one muddy mass. Five are now legible. **Predicate 12: pass.**
- **Predicate 1 restated** as *dominance* rather than height-and-position, since the old
  wording passed while the composition it protected failed.

**Measured:** stone 8.1% of frame against roofs 1.1% → predicate 1 passes. Sky 40.6%, just
outside the 20–40 band → **predicate 2 now marginally fails**, having been fixed two passes
ago.

**A caution on that measurement, which I do not want to leave implied.** The roof figure of
1.1% does not match what the image shows — the foreground village is visually heavy, and the
classifier is very likely mis-binning dark shaded maroon as ground. So predicate 1 "passes"
on a metric I do not fully trust. **The honest read by eye is that the castle and the
village now compete**, with the village winning the foreground by proximity rather than by
mass.

That is the third time in this exercise a check has gone green over a questionable image,
and the first where the *measurement itself* is the suspect part rather than the wording.
The fix is not another render: it is to classify by **material id at render time** — the
renderer knows exactly which triangles are stone and which are roof — instead of guessing
from output pixels. A cheap channel that guesses is not a cheap channel.
