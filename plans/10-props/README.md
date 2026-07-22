# 10 — Props: small detail as generators, on a level, with moving parts

**Issue:** [`jjstwerff/crawler#10`](https://github.com/jjstwerff/crawler/issues/10) ·
**Value:** `C` · **Effort:** `M` · **Depends on:** #5 (geometry), #9 (`way_param`, card placement)

## Status

**Active — P1–P4 done.** The design is settled in **[PROPS.md](../../PROPS.md)** (parts
1–4). This file is the implementation order.

## The shape of the work

Nine phases. Each is small, independently gated, and leaves the tree green — **no phase
requires the next one to be useful.** P1 is a pure refactor with a bit-identity guard; the
riskiest (P3, P8) come after the cheap structural ones so a mistake there is cheap to unwind.

Every gate below is an **exact invariant**, not a tolerance, wherever one exists. Where the
honest answer is a tolerance, it is stated as one.

---

## P1 — axis-agnostic primitives  — **DONE**, `src/primtest.loft`

`src/hexprim.loft`: `basis_u`/`basis_v` and `prim_drum`, taking an **axis** instead of a
z-range. A wheel is `prim_drum(base, axis=(0,1,0), r, r, 0.07, 16)`; a tower is the same
call with `axis=(0,0,1)`. The four tower/keep/battlement call sites are **migrated** and the
local hardcoded-z copy is gone.

**Bit-identity was the point, and it held.** `basis_u` computes `u = r × a`, not `a × r` —
the order chosen so the vertical case yields exactly `u=(1,0,0), v=(0,1,0)`, the
parameterisation the old drums used. `a × r` gives the same drum rotated 90° about its axis,
and *every geometric check would pass while every vertex had moved*.

```
   vertex-for-vertex against the reference implementation:  delta² = 0, three cases
   whole-scene render, identical camera, before vs after:   PIXEL-IDENTICAL
```

The reference implementation is kept **inside the gate**, because a claim that new code
reproduces old code needs the old code present to be checked against, not remembered.

**Also gated:** the frame is orthonormal and right-handed across 64 axes including both
poles (worst |dot| 5.6e-17, handedness 2.8e-32); a rotation changes no radius, length or
triangle count; a zero-length axis is refused rather than producing NaNs.

**Deliberately not migrated:** `mesh_trunk` is a six-segment linear taper whose *surface* is
identical to a one-segment taper, so moving it to `prim_drum` would change the tessellation.
That is a real change, not a free one, and it belongs in its own step where the difference is
visible rather than smuggled in under a bit-identity banner it would not satisfy.

## P2 — the part-list  — **DONE**, `src/proptest.loft`

A prop becomes a two-level tree: an anchor transform plus parts, each with its own local
transform. `mesh3d`'s `Node` + `Mat4` already provides it; this phase is the discipline of
using it.

**Concrete end-result:** the cart of PROPS §Class 3 — body, two wheels, axle, two shafts —
five parts, two primitives, one seed.

**Gate** `src/proptest.loft`:
- the cart exports as one node with five children, and the GLB round-trips through
  `tools/glbview.py`'s reader;
- the assembly's bounding box equals the union of its parts' boxes under the anchor
  transform (an exact check on the transform composition);
- the same seed gives byte-identical geometry; two seeds differ;
- **negative control:** a part with an identity transform must land at the anchor, so a
  mis-composed matrix is visible rather than plausible.

## P3 — seats  — **DONE**, `src/seattest.loft`

Generators take the surface they meet (a plane, or a height function) and **parameterise**
rather than intersect. This is the phase with real design content (PROPS §Class 2).

**Concrete end-result:** a chimney on a 30° roof, its base cut on the roof plane; a fence of
six panels on a slope, posts plumb and rails following; a drainpipe whose length is derived
from eave and ground.

**Gate** `src/seattest.loft`:
- every vertex of the chimney's base lies **on** the roof plane (residual < 1e-9) — not
  above it (floating) and not below it (buried);
- fence posts are vertical to 1e-9 while every post base sits on the terrain;
- the drainpipe's bottom touches the ground and its top the eave, at three different
  ground slopes;
- **negative control:** hand a generator a seat it does not touch and the residual check
  must fire.

## P4 — the prop level  — **DONE**, `src/proplevtest.loft`

Props recorded on their own level. `FieldCache` is already keyed `(chunk, level, version)`.

**Gate** `src/proplevtest.loft` — this is **the bridge gate, reused**:
- the architecture field is **bit-identical** with and without props present;
- a prop's material change does not invalidate the architecture level (the barrier result);
- `L_FIXED` and `L_MOVABLE` occupy distinct cache slots and an underived level misses;
- several props on one cell via the bucketed list, with the chain walked in a
  deterministic order.

## P5 — derived placement

The prop level becomes a **pure function of the architecture level plus a seed**: every wall
opening gets a door, every ridge a chimney, every field boundary a fence.

**Gate** `src/propgentest.loft`:
- same architecture + same seed ⇒ identical prop set (order-free, like every other
  derivation here);
- **every** `Feature` opening receives exactly one door — none missed, none doubled;
- no prop is placed inside a wall or off its seat;
- **negative control:** remove one opening and exactly one door disappears.

## P6 — state, Class A (hinges)

Door, casement, awning, shutters: one angle per prop.

**Gate** `src/hingetest.loft`:
- the drawn leaf angle equals the stored angle;
- **the material follows the state** — open ⇒ `mat_solid` false ⇒ `sight_clear`/movement
  agree with what is drawn. One number, both consumers;
- toggling costs **zero edge writes** and the L2 cache still hits (the level-crossing gate,
  reused verbatim);
- shutters are mirrored: equal and opposite angles from one state.

## P7 — state, Class B (wheels)

`phase = way_param / (2πr)`.

**Gate** `src/wheeltest.loft`:
- **rolling without slip is the exact invariant:** over a traverse, the wheel's contact
  point has zero velocity relative to the ground — checked as
  `Δphase · 2πr == Δdistance` to float tolerance at 40 sample points;
- phase is a **pure function of position**: drive forward then back and the phase returns to
  its original value exactly;
- slip is opt-in — with `slip = 0.1` the identity breaks by exactly 10%;
- **negative control:** a timer-driven phase must fail the no-slip check, so the gate is
  known to be able to fail.

## P8 — state, Class C (linkages)

The slider-crank. **The exact invariant is that the con-rod does not stretch** — if the
linkage is solved wrongly, its length varies, and nothing else about the motion will tell
you.

**Gate** `src/linktest.loft`:
- **|con-rod| is constant to 1e-12 over a full revolution**, sampled at 360 crank angles;
- the crosshead stays on its slide line (perpendicular offset < 1e-12);
- crank phase is locked to wheel phase — the gear cannot drift from the wheels because it
  is derived from them;
- both dead centres are reached and passed without a sign flip or a NaN;
- **negative control:** perturb the con-rod length by 1% and the constancy check fires.

## P9 — render, and a draw-skill pass

Props drawn in the landscape scene, then the `draw` skill's loop: freeze intent, block in,
measure on the cheap channel, look, critique cold, iterate.

**Gate:** `make test` green, plus a recorded cold critique with predicates scored — the
honest kind, as in `build/INTENT-landscape.md`.

**Carry forward from that exercise:** measure by **material id at render time**, never by
classifying output pixels. A cheap channel that guesses is not a cheap channel.

---

## Order, and why

```
   P1 primitives ──▶ P2 part-list ──▶ P3 seats
                          │
                          ▼
                     P4 level ──▶ P5 derived placement
                          │
                          ▼
                  P6 hinges · P7 wheels ──▶ P8 linkages ──▶ P9 render
```

- **P1 before everything** — it is a refactor with a bit-identity guard, so it is the one
  phase that cannot cost anything.
- **P4 before P5** — placement writes to the level, so the level must exist and be proven
  isolated first.
- **P7 before P8** — the crank angle *is* the wheel phase; solving a linkage against an
  unproven phase would hide which of the two was wrong.
- **P9 last**, because the draw loop's value is judging a thing that is already correct.

## Open questions, carried from PROPS.md

1. **Which edges an open door marks** on the prop level (PROPS §Part 4).
2. **State separated from placement?** A door on `L_FIXED` has not moved, only turned —
   which suggests state is its own small table rather than a field of the placement record.
3. **Prop kind: integer or bundle key?** `BUNDLE.md`'s standing check — content bundle-side,
   mechanism engine-side. A kind is content; a generator is mechanism. Settle before P5
   turns the catalogue into a hard-coded list.
