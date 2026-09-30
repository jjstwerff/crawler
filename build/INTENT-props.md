# Intent — props legible in the landscape (plan #10 P9)

Frozen **before** the fixes, not adjusted to match what comes out.

## What this pass is for

Plan #10 built doors, chimneys, fences and carts and proved them correct across eight gates.
The question here is different and cannot be gated: **are they legible?** A prop that is
present, correct, and invisible has failed at the only job it has.

## Predicates

Measured ones use `glbview --stats`, which counts **material coverage at render time** —
never a classifier over output pixels.

1. **Every house shows a chimney**, and a chimney reads as a chimney rather than a post: its
   own material, distinct from the roof it stands on, and no more than about a third of the
   roof's height.
2. **At least one door is legible** — a distinct leaf in a wall, not a dark smudge.
3. **The fence reads as a fence** — posts *and* rails distinguishable, following the slope.
4. **The cart is visible** and reads as a wheeled vehicle.
5. **Props are present but do not dominate:** total prop coverage (door + chimney + fence +
   cart materials) between **0.5% and 6%** of the frame.
6. ~~**The castle is still the focal point:** stone ≥ roof coverage.~~
   **REWRITTEN before the finishing pass, by explicit decision — the village is the
   subject.** The village dominates (**roofs > stone**), *and* the castle stays present
   rather than vanishing behind it: **stone ≥ 5%** of the frame. A subject that erases its
   setting is as wrong as one that hides in it.

## Known floor

Flat shading, no textures, single-colour materials. "Legible" therefore means legible by
**silhouette, size and material contrast** — the only three channels available.

## What would make this fail

- Chimneys merging into the roofs they stand on → material contrast failure, not size.
- Props visible only because the camera is close → framing cheat; predicate 6 catches it.

---

## Scored — 3 pass, 3 fail

Measured by material id at render time, not by classifying pixels.

| # | predicate | verdict |
|---|---|---|
| 1 | every house shows a chimney, distinct from its roof | **pass** — own pale-stone material against dark roofs; they read as chimneys, where sharing `m_roof` had made them read as posts |
| 2 | at least one door legible | **fail** — 0.01% coverage; the doors are on front walls that face away or sit behind roofs |
| 3 | fence reads as a fence | **pass** — posts and rails distinguishable, following the slope |
| 4 | cart visible | **fail** — not in frame at its new position |
| 5 | prop coverage 0.5–6% | **pass, marginally** — ≈0.53% (chimney 0.41, fence/cart 0.11, door 0.01) |
| 6 | castle still the focal point, stone ≥ roofs | **fail** — stone 9.83% (wall 8.15 + keep 1.68) against roofs **17.59%** |

**The chimney fix worked and confirms the diagnosis was right:** the fault was *material
contrast*, not size. Halving them alone would not have separated them from the roofs.

**Predicate 6's failure is not new and not a bug.** It is exactly the regression recorded in
the landscape work's pass 9 — once a village exists, its roofs out-mass the castle, and no
amount of prop work changes that. It is a **composition decision**: either the castle is the
subject and the village must shrink or move down-slope, or the village is the subject and
predicate 6 is the wrong predicate. That is the same shape as the hill-versus-sky question,
and it should be **decided deliberately before a pass**, not resolved by nudging a camera
until a number turns green.

**Predicates 2 and 4 are straightforwardly unfinished** — doors need to be placed on walls
the camera can see, and the cart needs to be on the visible stretch of road. Neither is a
mechanism fault; both are placement.

## Status

**P9 is NOT finished.** Three of six predicates fail, and one of the three is a decision
that is not mine to make. Recording that rather than iterating on the camera until the
score improves, because a render tuned to satisfy its own predicates is exactly the
goalpost drift the method exists to prevent.

---

## Finishing pass — 4 pass, 2 fail

Predicate 6 rewritten first, by decision: **the village is the subject.**

| # | predicate | verdict |
|---|---|---|
| 1 | chimneys distinct from their roofs | **pass** — 0.56%, pale stone against dark roofs |
| 2 | a door legible | **fail** — 0.00% |
| 3 | fence reads | **pass** — 0.16% |
| 4 | cart visible | **fail** |
| 5 | prop coverage 0.5–6% | **pass** — 0.72% |
| 6 | **village dominates, castle still present** | **pass** — roofs 17.44% > stone 11.33%, and stone is well over the 5% floor |

Up from 3/6. Predicate 6 passes on its rewritten terms, and the castle has *not* vanished
behind the village — the second clause was worth writing, because "the village dominates"
alone would have been satisfied by a frame with no castle in it.

### Why the doors fail, which is a finding rather than a to-do

Trimming the eaves from 1.20× to 1.06× and shrinking the leaf to fit its wall (it had been
2.1 m tall in a 1.5 m wall, i.e. buried in the roof) both helped the geometry and changed
the coverage not at all.

**A raised camera cannot show a door.** Looking down at a village, every roof occludes its
own walls; that is what roofs are for. The overview shot and the door shot are **different
shots**, and no single frame satisfies both predicate 2 and predicate 6.

An eye-level attempt confirmed the diagnosis by failing differently: at 2.6 m the camera
landed *inside* a roof (roof coverage 53.6%). A street-level view of this village needs the
camera placed against the road with a clear sightline — a framing problem, and a third shot.

### Status

**P9 closes at 4/6** with both failures understood: the cart is a placement fix, and the
doors need a *second view* rather than a change to the props. Both are recorded rather than
absorbed by re-tuning the predicates, which — having just rewritten one deliberately — is
the distinction worth keeping sharp.
