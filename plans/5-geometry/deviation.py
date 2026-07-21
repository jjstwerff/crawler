#!/usr/bin/env python3
"""deviation.py — per-point distance from an emitted vector outline to the IDEAL form.

The question this answers: we asked for a circle of radius r; the rasteriser gave us a
loop of exact lattice points.  **How far is each emitted point from the shape we wanted?**

Written curve-ready on purpose.  A `Target` is anything that can answer
`signed_distance(p)` — negative inside, positive outside — so the same routine measures:

    Circle    towers, round bastions            (today)
    Arc       a road bend of given radius        (next)
    Polyline  any authored curve / spline flat   (later)

Distances are reported in **hex widths** (1 hex width = sqrt(3) world units) so the number
means something physical: 0.5 = half a hex out of place.

    python3 plans/5-geometry/deviation.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import SQ3, bfs, lattice, trace, shoelace2, wall_of, f_hexdisk, f_circle, f_octagon

HEXW = SQ3          # one hex width in world units


# ── targets ───────────────────────────────────────────────────────────────────

class Circle:
    def __init__(self, cx, cy, r):
        self.cx, self.cy, self.r = cx, cy, r

    def signed_distance(self, p):
        return math.hypot(p[0] - self.cx, p[1] - self.cy) - self.r

    def project(self, p):
        d = math.hypot(p[0] - self.cx, p[1] - self.cy) or 1e-12
        return (self.cx + (p[0] - self.cx) * self.r / d,
                self.cy + (p[1] - self.cy) * self.r / d)

    def __repr__(self):
        return f"Circle(r={self.r:.4f})"


class Arc(Circle):
    """A circular arc between two angles — a road bend.  Outside the sweep, distance is
    measured to the nearer endpoint, so the metric stays well-defined at the ends."""

    def __init__(self, cx, cy, r, a0, a1):
        super().__init__(cx, cy, r)
        self.a0, self.a1 = a0, a1

    def spans(self, p):
        """Does the arc's angular sweep cover this point?  Handles wraparound."""
        th = math.atan2(p[1] - self.cy, p[0] - self.cx) % (2 * math.pi)
        a0, a1 = self.a0 % (2 * math.pi), self.a1 % (2 * math.pi)
        return (a0 <= th <= a1) if a0 <= a1 else (th >= a0 or th <= a1)

    def signed_distance(self, p):
        if self.spans(p):
            return super().signed_distance(p)
        ends = [(self.cx + self.r * math.cos(a), self.cy + self.r * math.sin(a))
                for a in (self.a0, self.a1)]
        return min(math.dist(p, e) for e in ends)


class Polyline:
    """Any authored curve, flattened.  Unsigned distance to the nearest segment."""

    def __init__(self, pts, closed=False):
        self.segs = list(zip(pts, pts[1:] + ([pts[0]] if closed else [])))

    def signed_distance(self, p):
        best = float("inf")
        for a, b in self.segs:
            vx, vy = b[0] - a[0], b[1] - a[1]
            L2 = vx * vx + vy * vy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0]-a[0])*vx + (p[1]-a[1])*vy)/L2))
            best = min(best, math.dist(p, (a[0] + t*vx, a[1] + t*vy)))
        return best


# ── the measurement ───────────────────────────────────────────────────────────

def evaluate(points, target, unit=HEXW):
    """Per-point deviation from `target`.  Returns (rows, summary).

    rows: (index, point, signed_deviation_in_units)  — every emitted point, in order.
    """
    rows = [(i, p, target.signed_distance(p) / unit) for i, p in enumerate(points)]
    devs = [d for _, _, d in rows]
    n = len(devs)
    summary = {
        "n": n,
        "max_out": max(devs),
        "max_in": min(devs),
        "band": max(devs) - min(devs),
        "mean": sum(devs) / n,
        "rms": math.sqrt(sum(d * d for d in devs) / n),
        "max_abs": max(abs(d) for d in devs),
    }
    return rows, summary


def best_fit_circle(points):
    """Least-squares circle (Kasa) — 'how circular is it, ignoring the radius we asked for'."""
    n = len(points)
    sx = sum(p[0] for p in points); sy = sum(p[1] for p in points)
    sxx = sum(p[0]**2 for p in points); syy = sum(p[1]**2 for p in points)
    sxy = sum(p[0]*p[1] for p in points)
    sxz = sum(p[0]*(p[0]**2+p[1]**2) for p in points)
    syz = sum(p[1]*(p[0]**2+p[1]**2) for p in points)
    sz  = sum(p[0]**2+p[1]**2 for p in points)
    A = [[sxx, sxy, sx], [sxy, syy, sy], [sx, sy, n]]
    b = [sxz/2, syz/2, sz/2]
    # 3x3 solve
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
    cx, cy = rep(0, b)/det, rep(1, b)/det
    c2 = rep(2, b)/det          # this solves for c/2, so r^2 = 2*c2 + cx^2 + cy^2
    r = math.sqrt(max(0.0, 2.0 * c2 + cx*cx + cy*cy))
    # Kasa minimises ALGEBRAIC distance, not the geometric rms we report.  For a fixed
    # centre the geometric optimum is simply the mean radius, so refine r to it.
    r = sum(math.hypot(px - cx, py - cy) for px, py in points) / len(points)
    return Circle(cx, cy, r)


def outer_points(form):
    loops = trace(form)
    outer = max(loops, key=lambda l: abs(shoelace2(l)))
    return [(k * SQ3 / 2, m / 2) for k, m in outer]


def main():
    dist = bfs(16)
    print("PER-POINT deviation of the emitted outline from the ideal circle")
    print("units = hex widths (1.0 = one whole hex out of place)\n")
    print(f"{'family':12} {'N':>2} {'pts':>4} {'target r':>9} {'max_out':>8} {'max_in':>8} "
          f"{'band':>7} {'rms':>7} | {'bestfit r':>9} {'rms(fit)':>8}")

    fams = [("A hex-disk", lambda N: f_hexdisk(N, dist), lambda N: N * SQ3),
            ("B circle",   lambda N: f_circle(N, dist, 1.069 * N * SQ3),
                           lambda N: 1.069 * N * SQ3),
            ("C octagon",  lambda N: f_octagon(N, dist, (N + 0.35) * 1.5),
                           lambda N: (N + 0.35) * 1.5)]

    bad = 0
    for name, fn, rfn in fams:
        for N in (3, 5, 8, 10):
            form = fn(N)
            pts = outer_points(form)
            tgt = Circle(0.0, 0.0, rfn(N))
            _, s = evaluate(pts, tgt)
            fit = best_fit_circle(pts)
            _, sf = evaluate(pts, fit)
            # SANITY GUARD (not a theorem): Kasa minimises ALGEBRAIC distance, so it is
            # not guaranteed to beat the nominal circle on geometric rms — but after the
            # mean-radius refinement it should, by a clear margin.  A violation means the
            # fit is broken; this is what caught a dropped factor of 2 in the solve, which
            # no rendered image would have shown.
            flag = ""
            if sf["rms"] > s["rms"] + 1e-6:
                flag = "  <-- FIT WORSE THAN NOMINAL (impossible)"
                bad += 1
            print(f"{name:12} {N:>2} {len(pts):>4} {rfn(N):>9.3f} {s['max_out']:>8.3f} "
                  f"{s['max_in']:>8.3f} {s['band']:>7.3f} {s['rms']:>7.3f} | "
                  f"{fit.r:>9.3f} {sf['rms']:>8.3f}{flag}")
        print()
    print(f"least-squares invariant: {'OK' if bad == 0 else f'{bad} VIOLATION(S)'}\n")

    # worst offenders on one form — per-point output is the point of the routine
    N = 8
    form = f_hexdisk(N, dist)
    pts = outer_points(form)
    rows, s = evaluate(pts, Circle(0, 0, N * SQ3))
    worst = sorted(rows, key=lambda t: -abs(t[2]))[:5]
    print(f"A hex-disk N={N}: 5 worst points vs the circle it claims to be")
    for i, p, d in worst:
        print(f"  pt[{i:>3}] ({p[0]:>7.3f},{p[1]:>7.3f})  dev={d:+.3f} hex widths")

    print("curve-ready check — the SAME routine against an Arc (a road bend).")
    a0, a1 = math.radians(-30), math.radians(90)
    arc = Arc(0, 0, 6.0, a0, a1)
    allpts = outer_points(f_circle(4, dist, 6.0))
    # only points the arc actually spans; outside the sweep the metric measures to the
    # endpoints, which is correct behaviour but not what we are asking here.
    span = [p for p in allpts if arc.spans(p)]
    _, sa = evaluate(span, arc)
    print(f"  Arc(r=6, -30°..90°) vs the rasterised r=6 outline, {len(span)} points in span:")
    print(f"    max_out={sa['max_out']:+.3f}  max_in={sa['max_in']:+.3f}  "
          f"rms={sa['rms']:.3f} hex widths")
    print("  -> same metric, same units, no code change: roads reuse this directly.")


if __name__ == "__main__":
    main()
