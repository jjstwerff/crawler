# SCALE.md — what a hex is, in metres

One hex grid, two readings of it. Until 2026-07-22 the two were stated in different
documents with no arithmetic between them, and plan #5 stated no metres at all — which made
every threshold it derived unfalsifiable. `8.4 world units` is neither right nor wrong until
you know what a world unit is.

**The contract is now code**: `src/scale.loft`, gated by `src/scaletest.loft`.

## The contract

```
   ARCHITECTURE (true scale)     one hex step  = 1.5 m
   TERRAIN      (compressed 10x) one walked hex = 15 natural m       <- OV_STEP
```

A hex step is `HEX_LEN = √3` world units (centre to centre), so

```
   1 world unit          = 1.5/√3 = 0.8660 m
   hex circumradius 1.0  = 0.866 m
   hex width √3          = 1.500 m
```

The 10× compression is the standard overland-game illusion — a town is a tile on the world
map and a full map when you enter it. It is a **user ruling evaluated by gameplay, not by
theory** (OVERLAND.md §13a), and it is **one dial**, `OV_STEP`.

## Every plan threshold, in metres

Checked by the gate against what the real object measures:

| quantity | wu | metres | real |
|---|---|---|---|
| door quantum | 1.0 | 0.87 | a single door |
| double door (2 cut edges) | 2.0 | 1.73 | a double door |
| platform edge → track centre | 1.5 | 1.30 | ~1.5 m |
| round tower radius | 8.4 | 7.27 | a keep, 6–8 m |
| driver's eye height | 2.5 | 2.17 | ~2.2 m |
| signal head | 5.0 | 4.33 | ~4 m |
| mature crown radius | 8.0 | 6.93 | an oak, ~7 m |
| **crown field floor** (plan #9 T8) | 3.46 | 3.00 | smallest tree worth deriving |

All nine land where the real thing does. **That is what makes the plans falsifiable.**

## The one that does not: stairs

Plan #5 derived a minimum stair tread of `√3` world units. In metres that is **1.50 m**,
against a real stair's going of **0.25–0.30 m** — the grid is **5.4× too coarse**.

**So a domestic staircase is an OBJECT at architecture scale**, exactly as a domestic spiral
stair and a sapling are, and for exactly the same reason: its defining dimension is below
one hex step. Plan #5's straight-stair work is correct arithmetic about *monumental* stepped
work, not about a house staircase:

| stepped work | going | resolves as a field |
|---|---|---|
| domestic staircase | 0.28 m | **no — object** |
| cathedral / temple steps | 1.5 m | yes |
| amphitheatre seating tier | 2.4 m | yes |
| stepped terrace, embankment | 6.0 m | yes |

This is **gated, not merely written down** — a limitation in prose drifts; one in a test
cannot.

## The railway numbers are illustrative

Plan #5 used `R = 26 wu` for turnouts, which is **22.5 m** — a tramway curve, not a main
line (a prototype turnout wants ≥ 150 m = 173 wu). Every railway *result* there is a ratio
(`R_max = w/tan²(θ/2)`, the 15° sweep rule, `offset = 2R(1−cos15°)`) and holds at either
size. Only the printed radii are small.

## What the compression means for trees

The same model gives the right answer at both readings without being told:

- **Architecture scale**: a crown of 8 wu is 6.9 m — comfortably above the 3.0 m crown
  floor, so a tree is a **field**, with a partition, a skeleton and cards.
- **Terrain scale**: one hex is 15 m, so the same tree spans **0.46 of a cell** — far below
  the floor, so on the overland a tree is an **object**.

That is plan #9 T8's boundary doing its job across a 10× scale change. A forest on the
overland is a terrain kind; individual trees only exist where the world is read at
architecture scale.

## The rule for new work

**State new lengths in metres and convert, or state them in world units and add a row to
the gate.** A threshold with no real-world size attached cannot be checked, and this
document exists because a dozen of them accumulated that way.
