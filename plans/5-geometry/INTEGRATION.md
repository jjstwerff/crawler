# Integration plan — geometry into loft, with the junction matrix

> How the design in `DESIGN.md` becomes working, gated loft. Phases are ordered by what
> unblocks what; every phase names its gate. Nothing here is built unless it says so.
>
> The hard part is not any single shape — it is **where two shapes meet**. That is where
> seams, collision arbitration and the matcher all fail at once, so the junction matrix
> (§3) is the real deliverable and the phases exist to make it testable.

## 1. Where we are

| built + gated | not built |
|---|---|
| `hexform.loft` — chunked `HexSet`, tracer, validator, exact integer `VecMap` | the §7.3 minimisation (canonical-dir index, `u16`/`u8`) |
| `hexedge.loft` — `EdgeSet`, `Surfaces` (straight/arc), `Materials`, `collide()` | the matcher (cells → surfaces) |
| `formtest.loft` — 18 forms / 900 points vs the Python golden; chunk-locality | junctions of any kind |
| `edgetest.loft` — 24/24 blocking, exact normals, materials, footprint | region cache, `vm_surf`, features |

## 2. Phases

### P1 — surfaces from curves *(unblocks everything)*
Port `ways.py` to loft: `Straight` / `ArcSeg` / `Track`, `build_way(profile)`, and the
offset construction. Emit surfaces into `Surfaces` and rasterise the footprint into a
`HexSet` + `EdgeSet` in one pass, so the surface id is attached at derivation time.

**Gate** `src/waytest.loft`: I-EQUI exact for straights/arcs · flattening error
`≤ c²/(8R)` · I-CURV rejects `|d| ≥ R` · a way's cells and its surfaces agree (every
blocked edge has a surface id).

### P2 — the matcher: cells → surfaces *(load-bearing, not polish)*
Cell-authored content has no surfaces today, so it has no normals. Fit straight runs and
arcs to a traced boundary; emit surfaces + the per-edge ids.

**Gate** `src/matchtest.loft`: `detect(stamp(parts)) == parts` on the tower catalog ·
recovered radius within one rung of the catalog value · **a wall with three doors still
matches as ONE wall** (FORMS.md's stated invariant) · every boundary edge gets a surface.

### P3 — junctions as first-class objects
Today two surfaces meeting at one edge is **first-writer-wins** — arbitrary and
order-dependent. Replace with a stated rule.

> **Arbitration: the surface whose geometry is NEAREST the edge's contact point wins;
> ties break to the lower surface id.** Deterministic, order-independent, and it matches
> what a ball should bounce off.

A `Junction` records the participating surfaces, the intended continuity (G1 smooth vs a
deliberate corner), and the arbitration outcome.

**Gate** `src/jointest.loft`: arbitration is order-independent (build A-then-B and
B-then-A, require identical `EdgeSet`) · no edge left with surface 0 · G0 exact at every
seam · G1 where intended, a corner where intended.

### P4 — the junction matrix *(the real deliverable — §3)*

### P5 — features: doors and windows *(§4)*

### P6 — minimisation + region cache
Apply §7.3 (canonical-dir index, `u16`/`u8`) and add the `(chunk, world_version)` cache.

**Gate**: footprint assertion drops from 440 592 B to ≤ 9 216 B per 32×32 chunk (the test
already measures it) · a cached region equals a freshly derived one, bit for bit.

## 3. The junction matrix

Every cell is a test. `G0` = no gap, `G1` = no kink, `∠` = a deliberate corner.

| | straight wall | curved wall | round tower | octagonal tower | road / rail |
|---|---|---|---|---|---|
| **straight wall** | collinear join · **T-junction** (inner wall) · **∠ corner** | tangent meet `G1` | **tangential** `G0+G1` | onto a **flat face** `G1`; onto a **corner** `∠` | wall crosses road: gate/arch |
| **curved wall** | — | arc↔arc, equal or opposed curvature | concentric or tangential | rarely tangential — expect `∠` | — |
| **round tower** | — | — | two towers touching / overlapping | mixed-family adjacency | — |
| **octagonal tower** | — | — | — | face-to-face vs corner-to-corner | — |
| **road / rail** | — | — | — | — | **crossing** · **merge** `G1` · **railway points** · roundabout |

### What every junction must satisfy

1. **G0** — the surfaces share the seam exactly (integer lattice, so this is exact).
2. **G1 or an intended corner** — never an accidental kink. Ways additionally need **G2**.
3. **Topology** — the traced outline still validates: closed loops, correct winding, and
   `Σ shoelace == 12 × cells` still holds *across* the junction.
4. **Collision arbitration** — deterministic and order-independent (P3).
5. **No leak** — the flood test still fails to cross a joined wall run.
6. **Matcher survival** — the parts are still individually recoverable after joining.

### The cases most likely to break, and why

- **Inner wall T-junction** — the inner wall *ends* at the outer wall. Its last edge is
  shared, so arbitration decides which surface a ball bounces off in the corner. Also the
  first case where a cell has walls on more than one of its 3 canonical directions.
- **Wall onto an octagonal corner** — 8-fold against 6-fold: the tangent cannot be
  continuous, so this must be an explicit `∠`, and the octagon's canonical orientation
  decides which walls can meet it cleanly at all. Expect a *rule*, not a fix.
- **Two towers overlapping** — the union's boundary is not either tower's boundary; the
  matcher must still recover two towers, or explicitly report a merged form.
- **Railway points** — one centreline becomes two with `G2` through the divergence. This
  is the hardest way-junction and should come last.
- **Road crossing a wall** — the collision layers disagree by design (the road is
  passable, the wall is not). Whichever wins must be *stated*, not emergent.

## 4. Doors and windows — the limitations are real

The user's suspicion is correct, and the first limitation is hard.

### L1 — the 1.0 unit is a QUANTUM, not a cap *(corrected)*

An earlier draft of this section claimed a straight opening could never exceed 1.0 unit.
**That was wrong**, and it mattered — it would have ruled out double doors.

What is true: on a traced cell boundary the longest **collinear** run of edges is 1, in
every one of the 24 headings, because the outline turns at every vertex. But that only
constrains an opening *cut from the cell outline*. In the edge model a wall is a **cut**,
and each cut edge is a unit segment running **along** the wall — so an opening is simply a
run of consecutive cut edges, and widening on both sides is exactly the mechanism.

Measured, opening `k` adjacent cut edges (all passable, wall still sealed elsewhere):

| edges opened | 0° | 30° | 45° | |
|---|---|---|---|---|
| 1 | 1.0 | 1.0 | 1.0 | single door |
| **2** | **1.9** | **1.8** | **1.6** | **double door — works** |
| 3 | 2.7 | 2.5 | 2.4 | triple |
| 4 | 3.6 | 3.2 | 3.1 | gateway / arch |

And the *visual* opening is straight regardless, because the door is an interval on the
**surface** (§L1b), not a hole cut in the cell outline. The zigzag never reaches the
render or the mesh.

### L1b — features are intervals on the SURFACE

A door is `[s0, s1]` along an exact straight or arc, so it is straight because the surface
is, at any width and any position. The cell/edge layer only answers *which edges that
interval opens*. Standing rule again: never derive a smooth thing from cells.

### L2 — the residual limits are the quantum and its anisotropy

Two real constraints remain, both bounded:

- **Collision quantises to whole cut edges.** A door of 1.5 edges cannot be expressed —
  an edge is passable or not. Fix if it ever matters: an **aperture fraction** per edge
  (how much of it is open), which is a genuine extension rather than a tweak.
- **The quantum varies ~19% with heading** — one edge projects to 1.0 along the wall at
  0°, but ~0.8 at 45°, because the cut zigzags. So "a double door" is 1.6–1.9 units
  depending on which way the wall runs. Same anisotropy family as everything else here,
  and the same fix if it matters: pick the edge count per heading to hit a target width,
  exactly as §7.3's phase knob does for wall width.

### L3 — `Materials.height` is a SCALAR; a window needs an interval

A window is `sill..head`, and the current model can only say "wall of height h". A window
therefore cannot be expressed at all today. Features need their own `(z0, z1)`.

### L4 — a door and a window modulate DIFFERENT terms

A door changes `solid` (and nothing else when shut vs open). A window changes `opacity`,
`sound_db`, `permeability` — and **not** `solid`, since you cannot walk through it. So a
feature must **override a subset** of the material's terms, not replace the material.

### L5 — features must not fragment the body

FORMS.md's invariant: a wall with three doors and a loophole still matches as **one**
wall. A feature is an annotation on a continuous body, never a break in it — so features
must be stored *beside* the surface, never by deleting cells or edges from it. (Today
`stamp_house` punches a door by clearing a whole hex — exactly the thing this forbids.)

### L6 — a feature at a junction

A doorway in a corner belongs to two surfaces. Arbitration (P3) decides, and the feature
interval must be expressed on the winning surface.

**Gate** `src/feattest.loft`: a door interval yields exactly the intended passable edges ·
**a double door (2 adjacent cut edges) is passable and the wall still seals elsewhere** ·
a window blocks movement but not sight · a wall with three features still matches as one
wall · features survive the surface round-trip · door width per heading is within the
stated ~19% band, or the edge count is chosen to hit a target width.

## 5. Order, and why

```
P1 surfaces from curves
      └─► P2 matcher (cells → surfaces)
                └─► P3 junction arbitration
                          └─► P4 junction matrix   ← the deliverable
                          └─► P5 features (needs surfaces + arbitration)
P6 minimisation + cache — independent, any time
```

P2 before P3 because a junction between two cell-authored parts has no surfaces to
arbitrate until the matcher exists. P5 after P3 because a feature at a junction needs the
arbitration rule. P6 is orthogonal and can be done whenever the footprint starts to hurt.

**Do not start P4 before P3 is green** — an unstated arbitration rule makes every junction
test order-dependent, and the matrix would encode the bug rather than catch it.
