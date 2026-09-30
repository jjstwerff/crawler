#!/usr/bin/env python3
"""matcher.py — P2 blueprint: recover SURFACES from a traced cell boundary.

Cell-authored content (a stamped stencil, a hand-drawn footprint) has no surfaces, so it
has no normals — which makes this load-bearing for physics, not kit polish.  The job:

    traced boundary loop (exact integer lattice points)  ->  straights + arcs

The difficulty is that the boundary ZIGZAGS: no two consecutive edges are collinear
(measured), so every run wanders around the true line by roughly the hex corner offset.
So the matcher must absorb a known amount of quantisation noise while still refusing to
swallow a real corner.  Pinning that tolerance is what this prototype is for.

    python3 plans/5-geometry/matcher.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import (SQ3, bfs, lattice, trace, f_hexdisk, f_circle, f_octagon)
from directions import Line, band

HEXW = SQ3


def pts_of(loop):
    return [(k * SQ3 / 2, m / 2) for k, m in loop]


# ── primitive fits ────────────────────────────────────────────────────────────

def fit_line(pts):
    """Total-least-squares line through pts -> (nx, ny, c, max residual)."""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts)
    syy = sum((p[1] - cy) ** 2 for p in pts)
    sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts)
    # principal direction = eigenvector of the larger eigenvalue
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    dx, dy = math.cos(th), math.sin(th)
    nx, ny = -dy, dx                      # unit normal
    c = nx * cx + ny * cy
    res = max(abs(nx * p[0] + ny * p[1] - c) for p in pts)
    return nx, ny, c, res


def fit_circle(pts):
    """Kasa circle + mean-radius refinement -> (cx, cy, r, max residual)."""
    n = len(pts)
    if n < 4:
        return None
    sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0] ** 2 for p in pts); syy = sum(p[1] ** 2 for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    sxz = sum(p[0] * (p[0] ** 2 + p[1] ** 2) for p in pts)
    syz = sum(p[1] * (p[0] ** 2 + p[1] ** 2) for p in pts)
    sz = sum(p[0] ** 2 + p[1] ** 2 for p in pts)
    A = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]]
    b = [sxz / 2, syz / 2, sz / 2]
    det = (A[0][0]*(A[1][1]*A[2][2]-A[1][2]*A[2][1])
         - A[0][1]*(A[1][0]*A[2][2]-A[1][2]*A[2][0])
         + A[0][2]*(A[1][0]*A[2][1]-A[1][1]*A[2][0]))
    if abs(det) < 1e-12:
        return None
    def rep(col, v):
        M = [row[:] for row in A]
        for i in range(3):
            M[i][col] = v[i]
        return (M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1])
              - M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0])
              + M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]))
    cx, cy = rep(0, b) / det, rep(1, b) / det
    r = sum(math.hypot(p[0]-cx, p[1]-cy) for p in pts) / n   # geometric optimum
    res = max(abs(math.hypot(p[0]-cx, p[1]-cy) - r) for p in pts)
    return cx, cy, r, res


# ── greedy segmentation ───────────────────────────────────────────────────────

def segment(pts, tol, min_run=6):
    """Walk the loop, extending a primitive while it still fits within `tol`."""
    n = len(pts)
    out, i = [], 0
    while i < n:
        best = None
        j = i + min_run
        while j <= i + n:
            win = [pts[(i + t) % n] for t in range(j - i)]
            lin = fit_line(win)
            cir = fit_circle(win) if len(win) >= 8 else None
            okl = lin[3] <= tol
            okc = cir is not None and cir[3] <= tol
            if not okl and not okc:
                break
            # prefer the simpler primitive when both fit
            if okl:
                best = ("line", i, j, lin)
            elif okc:
                best = ("arc", i, j, cir)
            j += 1
        if best is None:
            win = [pts[(i + t) % n] for t in range(min(min_run, n))]
            best = ("line", i, i + len(win), fit_line(win))
        out.append(best)
        i = best[2]
        if len(out) > n:
            break
    return out


def main():
    dist = bfs(16)
    print("P2 — recovering surfaces from a traced boundary\n")

    # what does the quantisation noise actually measure, on a KNOWN straight wall?
    print("1. How much noise must the tolerance absorb?")
    print("   (measured as the FIT RESIDUAL of one long side — not distance from the")
    print("    centreline, which would just be the wall's half-width)")
    for deg in (0.0, 15.0, 30.0, 45.0):
        line = Line(math.radians(deg))
        cells = band(set(dist), line, 1.05, 8.0)
        pts = pts_of(max(trace(cells), key=len))
        # take one long side: points on the + side, away from the end caps
        side = [p for p in pts
                if line.signed_distance(p) > 0 and abs(p[0]*line.t[0]+p[1]*line.t[1]) < 6.0]
        if len(side) < 4:
            continue
        nx, ny, c, res = fit_line(side)
        print(f"   wall {deg:>5.1f}°: {len(side):>3} pts on one side, fit residual"
              f" = {res:.3f} world units ({res/HEXW:.3f} hex widths)")
    print(f"   -> the hex circumradius is 1.000 world unit; that IS the quantisation scale")

    print("\n2. Does a circle fit recover the tower catalog radius?")
    print(f"   {'form':>18} {'cells':>6} {'fitted r':>9} {'residual':>9} {'catalog r':>10}")
    for label, form, want in (
            ("hexdisk N=3", f_hexdisk(3, dist), 3.189 * HEXW),
            ("circle r=5.0", f_circle(0, dist, 5.0), None),
            ("circle r=8.4", f_circle(0, dist, 8.4), None),
            ("octagon a=5.0", f_octagon(0, dist, 5.0), None)):
        loops = trace(form)
        pts = pts_of(max(loops, key=len))
        cir = fit_circle(pts)
        w = f"{want:.3f}" if want else "-"
        print(f"   {label:>18} {len(form):>6} {cir[2]:>9.3f} {cir[3]:>9.3f} {w:>10}")

    print("\n3. Greedy segmentation at a few tolerances (a straight wall should be FEW runs)")
    line = Line(math.radians(15.0))
    cells = band(set(dist), line, 1.05, 8.0)
    pts = pts_of(max(trace(cells), key=len))
    for tol in (0.30, 0.50, 0.60, 0.75, 1.00):
        segs = segment(pts, tol)
        kinds = "".join("L" if s[0] == "line" else "A" for s in segs)
        print(f"   tol {tol:.2f} ({tol/HEXW:.2f} hexw): {len(segs):>3} runs  {kinds[:40]}")

    print("\n4. Same tolerances on a ROUND TOWER (should collapse to ~1 arc)")
    form = f_circle(0, dist, 8.4)
    pts = pts_of(max(trace(form), key=len))
    for tol in (0.30, 0.50, 0.60, 0.75, 1.00):
        segs = segment(pts, tol)
        kinds = "".join("L" if s[0] == "line" else "A" for s in segs)
        print(f"   tol {tol:.2f}: {len(segs):>3} runs  {kinds[:40]}")


if __name__ == "__main__":
    main()
