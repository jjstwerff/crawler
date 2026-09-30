# DRAWING-API — SUPERSEDED. Do not implement from this file.

**Plan #11 P5.** This was the spec written *before anything was drawn*. Drawing one house
falsified it in six places, and the routines now exist, so **the code is the spec**:

| for | read |
|---|---|
| **how it works, and why** | [`BUILDING.md`](BUILDING.md) |
| **the routines** | `../hexbody/src/housedraw.loft` |
| **what is proved, with controls** | `../hexbody/src/housetest.loft` — in `make test`, 3 s |
| **what it looks like at all 12 orientations** | `../hexbody/src/houseshot.loft` → `/tmp/house12.png` |

This file is kept **only** so `BUILDING.md`'s citations to its section numbers resolve.
It is ~60 lines instead of ~320 because reading the rest costs a session ~3k tokens of
spec that is wrong in six places. The substance is below, compressed.

---

## What it got right, and is still the design

- **§1 Conventions.** `x = lattice_k(q,r)·0.866`, `y = lattice_m(q,r)·0.5`; `HEX_LEN = √3`;
  sizes are integer hex steps; `rot` 0–5 at 60°; `(rot, mir)` = **the 12 orientations**,
  the D6 the lattice has. Local frame `u = (cos θ, sin θ)`, `v = (−sin θ, cos θ)`.
  **The mirror negates local u — and does so ONCE, in the frame** (see the corrections).
- **§2 One rasterise rule.** A cell belongs to a shape iff the distance from its centre to
  the shape's geometry is ≤ `halfwidth`. No verb may index-walk the grid — that is the
  parity bug `DRAWING.md` exists to kill. Octagon orientation is **frozen**.
- **§5.1 Anchoring.** Openings and inner walls are `(side, t)`, never cell coordinates.
  This is what makes them flip correctly *for free*, and it is why `plan_flip` is one line.
- **§5.3 `house_flip` toggles the mirror and nothing else** — no side remapping, no
  `t → 1−t`. If an implementation starts remapping, the frame rule is wrong somewhere.
- **§7 The shape table** is the library/consumer seam: shape *classes* are mechanisms and
  closed; wall/road *type values* are things and open (`BUNDLE.md` decision 2).
- **§8 Every gate needs a control that has been SEEN to fire.** Carried into
  `../hexbody/src/housetest.loft` unchanged, and it is the reason the wrong figures below were caught.
- **§10 Out of scope**, still: two touching shapes of one type merge under connectivity
  alone (needs a run id); junction arbitration; tagging cost on a 101×101 world.

## The six corrections — the reason this file is superseded

1. **§1 + §5.2 apply the mirror TWICE.** §1 negates local x in the frame; §5.2 negates it
   again in `ends(s) = (−Bx, By, −Ax, Ay)`. The two cancel, leaving a bare swap, and the
   outward normal comes out **inward at all 12 orientations**. Correct: the mirror lives in
   the frame, and a mirrored side's endpoints **exchange only**.
2. **It draws every wall as CELLS, so every wall is 1.5 m thick** — a castle curtain wall.
   A house wall, fence, kerb and partition are all thinner than one hex and belong on
   **EDGES**. Drawn as cells a 7.5 × 6.0 m cottage loses **59 % of its floor**.
3. **§5.4's `erase_seg` over-erases by ~`halfwidth` at each end** (a 3.00 m interval opens
   4.50 m) and shrinking over-corrects. A door is **n edges**, and one hex edge is
   **0.87 m** — a real domestic door. It is *not* 0.75 m; that is the edge's projection on
   the nominal wall line, not the gap you walk through.
4. **A door must not delete its edge.** Deleting fragments the wall run — the same defect
   as a doored tower fitting 3 arcs instead of 1. The edge keeps its material; the opening
   is an annotation beside it.
5. **§8.1 equivariance passes on a wall with a hole in it.** Equivariance asks whether a
   shape *moves* correctly, never whether it *is* a shape. Sealing is a separate gate.
6. **§8.2's facade check defines its own subject.** Taking `outward` from `B − A` — the
   ordering under test — lets a broken rule supply its own notion of outward, so the
   control cannot fire. Take outward from the **massing**.

A seventh, found only once the routines ran in the engine: **there is no single wall-run
overhead.** A side perpendicular to a lattice line zigzags at exactly **2/√3 = 15.5 %**
using 2 of the 3 hex axes; a side along one staircases at **3√3/4 = 29.9 %** using all 3.
`BUILDING.md` §4 has the table. Earlier drafts said "39 %", measured by a Python model of
the routines rather than the routines — which is why that model was deleted.
