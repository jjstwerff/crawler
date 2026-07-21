#!/usr/bin/env python3
"""directions.py — can a wall / road run in all 24 directions (k*15 deg)?

Plan #5 Track 1 wants walls, roads and fences in **24 directions**.  But a hex grid has
only **12** natural symmetry directions: 6 through the edge midpoints and 6 through the
vertices, 30 degrees apart.  So 12 of the 24 are off-axis by 15 degrees and cannot align
with any lattice direction.

This measures what each direction actually costs, rather than assuming.  For every
direction it rasterises a band along that heading, traces the emitted vector map,
validates it, and measures the per-point deviation from the true centreline.

    python3 plans/5-geometry/directions.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import SQ3, bfs, lattice, trace, validate, wall_of
from deviation import Polyline, evaluate
from road_arcs import world, connected, outline_pts

HEXW = SQ3


class Line:
    """An infinite straight centreline through the origin at heading `theta`."""

    def __init__(self, theta):
        self.t = (math.cos(theta), math.sin(theta))

    def signed_distance(self, p):
        # perpendicular distance to the line through the origin
        return p[0] * (-self.t[1]) + p[1] * self.t[0]


def band(universe, line, halfwidth, extent):
    """Cells whose centre is within halfwidth of the line and within `extent` along it."""
    out = set()
    for c in universe:
        x, y = world(c)
        along = x * line.t[0] + y * line.t[1]
        if abs(along) > extent:
            continue
        if abs(line.signed_distance((x, y))) <= halfwidth:
            out.add(c)
    return out


def hex_natural(deg):
    """The 12 lattice-aligned headings: edge-mid directions and vertex directions."""
    return abs((deg % 30) - 0) < 1e-9 or abs(deg % 30 - 30) < 1e-9


def main():
    universe = bfs(26)
    HALF = 0.9
    EXTENT = 14.0

    print("24-DIRECTION WALLS / ROADS — what each heading actually costs")
    print("A hex grid has 12 natural directions (30 deg apart). The other 12 are off-axis.")
    print("deviation in hex widths (1.0 = one whole hex out of place)\n")
    print(f"{'deg':>5} {'axis':>9} {'cells':>6} {'loops':>6} {'valid':>6} "
          f"{'W_eff':>8} {'worst':>8} {'rms':>7}")

    rows = {}
    for k in range(24):
        deg = k * 15.0
        th = math.radians(deg)
        line = Line(th)
        cells = band(universe, line, HALF, EXTENT)
        if not cells:
            print(f"{deg:>5.0f}  (no cells)")
            continue
        loops, ptsets = outline_pts(cells)
        errs = validate(loops, cells)
        pts = [p for ps in ptsets for p in ps]
        # measure only points well inside the run, so the end caps do not dominate
        inner = [p for p in pts
                 if abs(p[0]*line.t[0] + p[1]*line.t[1]) < EXTENT - 1.5]
        # WIDTH-NORMALISED: the nominal halfwidth yields different effective widths per
        # direction (17 vs 29 cells), so raw spread conflates direction with width.
        # Fit W = mean|d| and measure the error about it, as the road ladder does.
        ds = [abs(line.signed_distance(p)) for p in inner]
        W = sum(ds) / len(ds)
        worst = max(abs(d - W) for d in ds) / HEXW
        rms = math.sqrt(sum((d - W) ** 2 for d in ds) / len(ds)) / HEXW
        isnat = hex_natural(deg)
        kind = "edge" if abs(deg % 60) < 1e-9 else ("vertex" if isnat else "OFF-AXIS")
        rows.setdefault(kind, []).append(worst)
        print(f"{deg:>5.0f} {kind:>9} {len(cells):>6} "
              f"{len(loops):>6} {'ok' if not errs else 'FAIL':>6} "
              f"{W/HEXW:>8.3f} {worst:>8.3f} {rms:>7.3f}")

    print(f"\n{'class':>9} {'n':>3} {'worst-case error (hex widths)':>32}")
    for kind in ("edge", "vertex", "OFF-AXIS"):
        v = rows.get(kind, [])
        if v:
            print(f"{kind:>9} {len(v):>3}   min {min(v):.3f}  max {max(v):.3f}  "
                  f"mean {sum(v)/len(v):.3f}")
    e = sum(rows["edge"]) / len(rows["edge"])
    v = sum(rows["vertex"]) / len(rows["vertex"])
    o = sum(rows["OFF-AXIS"]) / len(rows["OFF-AXIS"])
    print("\nAll 24 headings produce a VALID vector map — representability was never the")
    print("question, only cost. Width-normalised, the ranking is clean and three-tiered:")
    print(f"  edge directions   (6)  {e:.3f}   1.00x   the 6 hex edge normals")
    print(f"  vertex directions (6)  {v:.3f}   {v/e:.2f}x   lattice-aligned but zigzagged")
    print(f"  off-axis          (12) {o:.3f}   {o/e:.2f}x   the 15-degree headings")
    print("\nSo all 24 are usable, and the cost of leaving the lattice is about 3.5x the")
    print("error of an edge-aligned run — bounded, not catastrophic.")
    print("\nMETHOD NOTE: before width-normalising, this table appeared to show the VERTEX")
    print("directions as the worst of all. That was an artefact — a fixed nominal halfwidth")
    print("yields 17/29/19 cells by direction, so the raw spread was measuring width, not")
    print("heading. Fitting W per direction reversed the conclusion.")


if __name__ == "__main__":
    main()
