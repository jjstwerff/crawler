# mesh-pin.md — triangle-vertex datapoint model + I-MESH (the height representation)

**Status: PINNED ✓ + POPULATED (2026-06-15)** — `python3 trimesh.py` (verify) and
`python3 ortler_import.py mesh` (sample) → exit 0.

## The model

Heights live at the **triangle vertices** of each 1.5 km hex, not at hex centers. Each hex
is a **center fan**: every side is split into 3, so each side yields 3 triangles →
**18 triangles over 19 vertices** (center + 6 corners + 12 edge-thirds). `trimesh.py` is the
structure; `ortler_import.py mesh` populates heights.

## I-MESH — watertight (design-protocol exact invariant)

A corner is shared by **3** hexes, an edge-third by **2**. A shared vertex must carry **one**
height or the rendered mesh cracks between hexes (the triangle-wall lineage). Guaranteed by
computing every vertex from its **world position** and dedup'ing on a **1 mm key** — a shared
vertex is literally the same datapoint, sampled once.

Verified on interior hex (20,20):
```
[counts] unique vertices = 14878;  triangles = 28800 (want 28800 = 18x1600)
[I-MESH @(20,20)] center ref=1; corners=[3,3,3,3,3,3]; edges={2}  -> OK
[tiling @(20,20)] fan area 1948557.159 m^2 == hex area 1948557.159 m^2  -> OK
```
(`tiling` = the 18 fan triangles exactly cover the hexagon: no gaps, no overlap.)

## Heights populated

```
[holes] 0
[stats] min/mean/max = 557/2166/3835 m over 14878 vertices
[summit vertex] 3835 m
```
→ `data/ortler_trimesh.npz` — `verts` (world xy f64), `height` (i16 m), `tris` (1600,18,3
vertex ids), `hexcr` (the (c,r) order). 14878 vertices = 149 requests at 1/s (165 total today,
< 1000/day).

## Why this matters downstream

- The fed-into-renderer step (S3) consumes **per-vertex** heights, so `overland_blueprint`'s
  one-height-per-cell lattice grows a vertex-height field (or the fan is rendered directly
  from this mesh). Note this when wiring S3.
- The classifier (S5) can run per-vertex or per-hex (aggregate the 19); decide at S5.

## Cliff projection is an inner-triangle algorithm (not a hex one)

The data shows slope is meaningless at hex scale — averaged over 1.5 km, even the steepest
cells reach only ~27° (`tuned-defaults.md`), so a hex-level slope test can never find a cliff.
**That is why cliff projection runs on the triangles, not the hex:** a cliff face is detected
from the height deltas **between triangle vertices** (corner↔center↔edge-third, ≤866 m apart),
where real relief survives, rather than hex-center↔hex-center. The triangle-vertex height model
is the substrate for it. At the recursive **1.5 m LOD** the inner-triangle deltas resolve actual
cliff faces (and stream channels) that 1.5 km necessarily blurs — so cliff/`K_FACE` is a
per-triangle classification, elevation-banding is the per-hex one.

## Gate

unique=14878, triangles=18×1600, refcounts {center:1, corner:3, edge:2}, fan area == hex
area, 0 holes, summit vertex 3835 m → **the height datapoint evaluation is ready.**
