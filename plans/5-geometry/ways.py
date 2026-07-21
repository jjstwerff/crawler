#!/usr/bin/env python3
"""ways.py — the 3-LINE construction: a centreline plus equidistant offsets.

Covers every WAY type — railway, modern road, dirt track — because they are the same
construction with a different profile.  Do NOT derive a way from a rasterised band.
Author ONE exact centreline; everything else is an OFFSET of it:

        bed_left          <- centre - bed_half
        rail_left         <- centre - gauge/2
    ==> CENTRELINE            the authored truth
        rail_right        <- centre + gauge/2
        bed_right         <- centre + bed_half

Why this matters: rasterising a band bottoms out at the hex quantisation scale
(~0.577 hex widths, measured in road_arcs.py) because the two edges quantise
independently.  An offset construction has **no quantisation at all** — the rails are
exactly `gauge/2` from the centreline everywhere, by construction, so they are smooth and
provably equidistant.  The hex cells stay useful for collision/occupancy; they stop being
the source of the geometry.

Two invariants this pins:

  I-EQUI  every point of an offset line is EXACTLY d from the centreline.  For straights
          and circular arcs the offset is again a straight / a concentric arc, so this is
          exact, not approximate — verified below to float precision.

  I-CURV  an offset degenerates when |d| >= R (the inner rail/bed inverts through the
          centre).  That is the geometric root of a railway's MINIMUM CURVE RADIUS.

And the one it exposes: **G2**.  A straight meeting a circular arc is G1 (no kink) but the
curvature jumps 0 -> 1/R, which on a railway is the lurch a transition curve (clothoid /
Euler spiral) exists to remove.  FORMS.md's seam law covers G0+G1; track needs G2.

    python3 plans/5-geometry/railway.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import SQ3

HEXW = SQ3
EPS = 1e-9


# ── centreline segments ───────────────────────────────────────────────────────

class Straight:
    def __init__(self, p0, p1):
        self.p0, self.p1 = p0, p1
        self.len = math.dist(p0, p1)
        self.t = ((p1[0] - p0[0]) / self.len, (p1[1] - p0[1]) / self.len)

    def point(self, s):
        return (self.p0[0] + self.t[0] * s, self.p0[1] + self.t[1] * s)

    def tangent(self, s):
        return self.t

    def curvature(self, s):
        return 0.0

    def offset(self, d):
        n = (-self.t[1], self.t[0])                      # left normal
        return Straight((self.p0[0] + n[0]*d, self.p0[1] + n[1]*d),
                        (self.p1[0] + n[0]*d, self.p1[1] + n[1]*d))

    def distance(self, p):
        vx, vy = self.p1[0]-self.p0[0], self.p1[1]-self.p0[1]
        L2 = vx*vx + vy*vy
        t = max(0.0, min(1.0, ((p[0]-self.p0[0])*vx + (p[1]-self.p0[1])*vy)/L2))
        return math.dist(p, (self.p0[0]+t*vx, self.p0[1]+t*vy))


class ArcSeg:
    """Circular arc.  `turn` = +1 left-hand (centre on the left), -1 right-hand."""

    def __init__(self, centre, R, a0, a1, turn=+1):
        self.c, self.R, self.a0, self.a1, self.turn = centre, R, a0, a1, turn
        self.len = abs(a1 - a0) * R

    def point(self, s):
        a = self.a0 + (s / self.R) * (1 if self.a1 >= self.a0 else -1)
        return (self.c[0] + self.R*math.cos(a), self.c[1] + self.R*math.sin(a))

    def tangent(self, s):
        a = self.a0 + (s / self.R) * (1 if self.a1 >= self.a0 else -1)
        sgn = 1 if self.a1 >= self.a0 else -1
        return (-math.sin(a)*sgn, math.cos(a)*sgn)

    def curvature(self, s):
        return 1.0 / self.R

    def offset(self, d):
        # left normal points AWAY from the centre when sweeping counter-clockwise
        sgn = 1 if self.a1 >= self.a0 else -1
        R2 = self.R + d * sgn
        return ArcSeg(self.c, R2, self.a0, self.a1, self.turn)

    def distance(self, p):
        a = math.atan2(p[1]-self.c[1], p[0]-self.c[0])
        lo, hi = min(self.a0, self.a1), max(self.a0, self.a1)
        aa = a
        while aa < lo:
            aa += 2*math.pi
        if lo <= aa <= hi:
            return abs(math.hypot(p[0]-self.c[0], p[1]-self.c[1]) - self.R)
        ends = [self.point(0.0), self.point(self.len)]
        return min(math.dist(p, e) for e in ends)


class Track:
    def __init__(self, segs):
        self.segs = segs

    def offset(self, d):
        return Track([s.offset(d) for s in self.segs])

    def sample(self, per_seg=400):
        out = []
        for s in self.segs:
            for i in range(per_seg + 1):
                out.append(s.point(s.len * i / per_seg))
        return out

    def distance(self, p):
        return min(s.distance(p) for s in self.segs)


# ── the 3-line (really 5-line) construction ──────────────────────────────────

# A WAY PROFILE is just a list of (offset, kind).  The insight that unifies the family:
# the INNER OFFSET PAIR is rails on a railway, wheel ruts on a dirt track, and lane
# markings on a modern road -- the gauge is a cart axle, a rail gauge, or a lane width.
def profile_railway(gauge=1.0, bed=3.0):
    return [(-bed/2, "bed_edge"), (-gauge/2, "rail"), (0.0, "centre"),
            (+gauge/2, "rail"), (+bed/2, "bed_edge")]


def profile_dirt_track(axle=1.2, width=2.6):
    # two ruts worn by wheels, a grass strip between them, and the worn-out edges
    return [(-width/2, "edge"), (-axle/2, "rut"), (0.0, "centre_grass"),
            (+axle/2, "rut"), (+width/2, "edge")]


def profile_modern_road(lane=1.6, width=3.6):
    return [(-width/2, "edge"), (-lane/2, "lane_line"), (0.0, "centre_marking"),
            (+lane/2, "lane_line"), (+width/2, "edge")]


PROFILES = {"railway": profile_railway, "dirt_track": profile_dirt_track,
            "modern_road": profile_modern_road}


def build_way(centre_track, profile):
    """One construction for every way type: offset the centreline per the profile."""
    return [(d, kind, centre_track.offset(d)) for d, kind in profile]


def build(centre_track, gauge, bed_width):
    """Back-compat shim for the railway demo below."""
    out = {}
    for d, kind, line in build_way(centre_track, profile_railway(gauge, bed_width)):
        key = {"bed_edge": "bed", "rail": "rail", "centre": "centre"}[kind]
        if kind == "centre":
            out["centre"] = line
        else:
            out[f"{key}_{'left' if d < 0 else 'right'}"] = line
    return out


def check_equidistant(centre_track, line, d, per_seg=400):
    """I-EQUI: every sampled point of `line` must be EXACTLY |d| from the centreline."""
    worst = 0.0
    for p in line.sample(per_seg):
        worst = max(worst, abs(centre_track.distance(p) - abs(d)))
    return worst


def main():
    # a track: straight -> left-hand arc -> straight, joined tangentially
    R = 9.0
    arc = ArcSeg((0.0, 0.0), R, math.radians(-90), math.radians(-20), turn=+1)
    p_in, p_out = arc.point(0.0), arc.point(arc.len)
    t_in, t_out = arc.tangent(0.0), arc.tangent(arc.len)
    s_in = Straight((p_in[0] - t_in[0]*12, p_in[1] - t_in[1]*12), p_in)
    s_out = Straight(p_out, (p_out[0] + t_out[0]*12, p_out[1] + t_out[1]*12))
    track = Track([s_in, arc, s_out])

    GAUGE, BED = 1.0, 3.0          # world units
    lines = build(track, GAUGE, BED)

    print("3-LINE CONSTRUCTION — centreline + equidistant offsets")
    print(f"  gauge={GAUGE}  bed={BED}  arc R={R}  "
          f"(in hex widths: gauge={GAUGE/HEXW:.3f} bed={BED/HEXW:.3f} R={R/HEXW:.3f})\n")

    print("I-EQUI — worst deviation of each offset line from its nominal distance:")
    ok = True
    for name, d in (("bed_left", -BED/2), ("rail_left", -GAUGE/2),
                    ("rail_right", GAUGE/2), ("bed_right", BED/2)):
        w = check_equidistant(track, lines[name], d)
        flag = "EXACT" if w < 1e-9 else f"{w:.3e}"
        if w >= 1e-9:
            ok = False
        print(f"  {name:11} d={d:+5.2f}   worst |dist-{abs(d):.2f}| = {flag}")
    print(f"  -> I-EQUI {'HOLDS to float precision' if ok else 'VIOLATED'}: "
          f"rails are equidistant BY CONSTRUCTION, not by fitting.\n")

    print("I-CURV — the offset degenerates when |d| >= R (minimum curve radius):")
    print(f"  bed={BED} (half={BED/2}); tighten the centreline radius until it breaks:")
    print(f"  {'R':>6} {'inner R':>8}  status")
    for Rt in (5.0, 3.0, 2.0, 1.5, 1.0):
        inner = Rt - BED/2
        if inner > 1e-12:
            st = "ok" if inner >= 0.5 else "ok but very tight"
        elif abs(inner) <= 1e-12:
            st = "DEGENERATE — inner bed collapses to a point"
        else:
            st = "INVERTED — inner bed folds through the centre"
        print(f"  {Rt:>6.1f} {inner:>8.2f}  {st}")
    min_R = BED/2
    print(f"  -> minimum centreline radius for bed={BED}: R > {min_R:.2f} world units "
          f"({min_R/HEXW:.3f} hex widths)\n")

    print("G2 — curvature continuity at the joins (what a transition curve fixes):")
    for i in range(len(track.segs) - 1):
        a, b = track.segs[i], track.segs[i+1]
        ta, tb = a.tangent(a.len), b.tangent(0.0)
        kink = math.degrees(math.acos(max(-1, min(1, ta[0]*tb[0] + ta[1]*tb[1]))))
        ka, kb = a.curvature(a.len), b.curvature(0.0)
        print(f"  join {i}->{i+1}:  G1 kink = {kink:8.5f} deg   "
              f"curvature {ka:.4f} -> {kb:.4f}   G2 {'OK' if abs(ka-kb) < 1e-9 else 'JUMP'}")
    print("  -> tangent-continuous (G1) but curvature JUMPS at straight<->arc.")
    print("     On a railway that is the lurch a clothoid / Euler-spiral transition removes.")
    print("     FORMS.md's seam law covers G0+G1; TRACK additionally needs G2.\n")

    print("EVERY WAY TYPE, ONE CONSTRUCTION — I-EQUI checked per line")
    for name, mk in PROFILES.items():
        worst_all = 0.0
        for d, kind, line in build_way(track, mk()):
            if d == 0.0:
                continue
            worst_all = max(worst_all, check_equidistant(track, line, d, per_seg=200))
        prof = ", ".join(f"{k}@{d:+.2f}" for d, k in mk())
        print(f"  {name:12} worst |dist-d| = {'EXACT' if worst_all < 1e-9 else f'{worst_all:.2e}'}")
        print(f"  {'':12} {prof}")
    print()

    print("WHY THIS BEATS A RASTERISED BAND")
    print(f"  rasterised road band  : worst-case ~0.45-0.66 hex widths (road_arcs.py),")
    print(f"                          floored by the {1/SQ3:.3f} hex-width corner offset.")
    print(f"  3-line offset         : EXACT — the error is not small, it is ZERO.")
    print("  The hex cells still give collision/occupancy; they stop being the geometry.")


if __name__ == "__main__":
    main()


# ── clothoid transition: where the EXACT-offset property stops holding ────────

class Clothoid:
    """Euler spiral: curvature grows linearly with arc length, k(s) = s/(R*L).

    This is what G2 requires between a straight and an arc.  Its parallel curve is NOT
    another clothoid, so — unlike straights and arcs — it cannot be offset exactly in the
    same primitive.  It must be flattened, and equidistance then holds only to the
    flattening tolerance.  That is the honest limit of the 3-line construction."""

    def __init__(self, R, L, n=4000):
        self.R, self.L, self.n = R, L, n
        self.pts, self.tan = [], []
        x = y = th = 0.0
        ds = L / n
        for i in range(n + 1):
            s = i * ds
            self.pts.append((x, y))
            self.tan.append((math.cos(th), math.sin(th)))
            k = s / (R * L)                       # linear curvature ramp
            th += k * ds
            x += math.cos(th) * ds
            y += math.sin(th) * ds
        self.len = L

    def sample(self, m):
        step = max(1, self.n // m)
        return [(self.pts[i], self.tan[i]) for i in range(0, self.n + 1, step)]

    def offset_pts(self, d, m):
        out = []
        for (px, py), (tx, ty) in self.sample(m):
            out.append((px - ty * d, py + tx * d))    # left normal
        return out

    def distance(self, p):
        return min(math.dist(p, q) for q in self.pts)


def clothoid_report():
    """Honest test: the error lives BETWEEN samples, on the flattened chords.

    Measuring an offset point's distance back to the sample that generated it is
    circular -- it is d by construction.  A parallel curve is equidistant BY DEFINITION
    for any smooth centreline; what actually costs accuracy is FLATTENING the offset to
    a polyline, whose chords cut inside the true curve."""
    R, L = 9.0, 6.0
    cl = Clothoid(R, L)
    GAUGE = 1.0
    d = GAUGE / 2
    print("\nCLOTHOID TRANSITION — the real cost is FLATTENING, not the offset")
    print(f"  straight -> arc R={R}, transition L={L}, rail offset d={d} (gauge {GAUGE})")
    print(f"  error sampled ALONG the chords, not at the vertices\n")
    print(f"  {'segments':>9} {'chord len':>10} {'worst err':>11} {'% of gauge':>11} {'ratio':>7}")
    prev = None
    for m in (8, 16, 32, 64, 128, 256):
        verts = cl.offset_pts(d, m)
        worst = 0.0
        for i in range(len(verts) - 1):
            a, b = verts[i], verts[i + 1]
            for j in range(1, 16):                      # points along the chord
                t = j / 16.0
                q = (a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t)
                worst = max(worst, abs(cl.distance(q) - d))
        chord = L / max(1, len(verts) - 1)
        ratio = (prev / worst) if prev else float("nan")
        print(f"  {len(verts)-1:>9} {chord:>10.4f} {worst:>11.3e} "
              f"{100*worst/GAUGE:>10.4f}% {ratio:>7.2f}")
        prev = worst
    print("\n  -> error falls ~4x per doubling (quadratic in chord length), as chord")
    print("     sagitta theory predicts: err ~ c^2 / (8*R).")
    print("  -> so 'exact' is not the right word, but NEAR-exact is cheap: the rails can")
    print("     be held to any tolerance you name by flattening finer.")


if __name__ != "__main__":
    pass
