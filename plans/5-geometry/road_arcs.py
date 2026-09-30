#!/usr/bin/env python3
"""road_arcs.py — the collision-match ladder for ROAD ARCS.

Same objective as the tower catalog: not "reproduce width w", but **best match on
collisions**.  A road is a BAND around a curve, so the fitted quantity is the effective
HALF-WIDTH, and the ideal boundary is the level set at that distance from the centreline.

    * rasterise: cells whose centre lies within a threshold of the arc;
    * trace the emitted outline (exact integer lattice points);
    * for each outline point take d(p) = |distance to the arc centreline|;
    * fit W = mean d(p), which minimises sum (d-W)^2  -> the effective half-width;
    * rank by WORST-CASE error max|d(p) - W| — collision is felt at its worst point.

Cap points are excluded from the width fit (they measure the round end cap, not the
band's width).  Deliberately uses arbitrary, NON-lattice centres and NON-integer radii:
that is the property a hex-distance model cannot express at all, and the reason roads and
towers can share one rounding model.

    python3 plans/5-geometry/road_arcs.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import SQ3, bfs, lattice, neighbors, trace, shoelace2, validate
from deviation import Arc

HEXW = SQ3


def world(cell):
    k, m = lattice(*cell)
    return (k * SQ3 / 2, m / 2)


def band_cells(universe, arc, halfwidth):
    return {c for c in universe if abs(arc.signed_distance(world(c))) <= halfwidth}


def connected(cells):
    if not cells:
        return False
    seen, stack = set(), [next(iter(cells))]
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        for nb in neighbors(*c):
            if nb in cells and nb not in seen:
                stack.append(nb)
    return len(seen) == len(cells)


def outline_pts(cells):
    loops = trace(cells)
    return loops, [[(k * SQ3 / 2, m / 2) for k, m in l] for l in loops]


def fit_band(cells, arc):
    """Effective half-width + worst-case / rms error, measured on the emitted outline."""
    loops, ptsets = outline_pts(cells)
    pts = [p for ps in ptsets for p in ps if arc.spans(p)]     # exclude the end caps
    if len(pts) < 8:
        return None
    ds = [abs(arc.signed_distance(p)) for p in pts]
    W = sum(ds) / len(ds)
    worst = max(abs(d - W) for d in ds) / HEXW
    rms = math.sqrt(sum((d - W) ** 2 for d in ds) / len(ds)) / HEXW
    return W, worst, rms, len(cells), len(loops), len(pts)


def ladder(universe, arc, lo=0.55, hi=4.2, step=0.01):
    """Distinct valid band footprints for this arc, ranked candidates."""
    seen, out = set(), []
    t = lo
    while t <= hi:
        cells = band_cells(universe, arc, t)
        key = frozenset(cells)
        if cells and key not in seen and connected(cells):
            loops, _ = outline_pts(cells)
            if not validate(loops, cells):
                r = fit_band(cells, arc)
                if r:
                    out.append((t,) + r)
                    seen.add(key)
        t += step
    return out


def main():
    universe = bfs(22)

    print("ROAD-ARC LADDER — width is an OUTPUT of the collision fit, not an input.")
    print("W and errors in hex widths (1.0 = one whole hex out of place).\n")

    # deliberately awkward: centre off-lattice, radius non-integer
    CENTRE = (0.37, 0.81)
    print(f"centre = {CENTRE} (NOT a hex centre), radii non-integer — "
          f"a hex-distance model cannot express any of these.\n")

    print(f"{'R':>6} {'rung':>4} {'thresh':>7} {'W_eff':>7} {'worst':>7} {'rms':>6} "
          f"{'cells':>6} {'loops':>5}")
    best_by_R = {}
    for R in (4.3, 7.1, 11.6):
        arc = Arc(CENTRE[0], CENTRE[1], R, math.radians(-25), math.radians(115))
        rows = ladder(universe, arc)
        # show a representative ladder: the best rung per rough width band
        buckets = {}
        for t, W, worst, rms, nc, nl, npts in rows:
            b = round(W / HEXW * 2) / 2                     # half-hex-width buckets
            if b not in buckets or worst < buckets[b][2]:
                buckets[b] = (t, W, worst, rms, nc, nl, npts)
        for i, b in enumerate(sorted(buckets), 1):
            t, W, worst, rms, nc, nl, npts = buckets[b]
            print(f"{R:>6.1f} {i:>4} {t:>7.2f} {W/HEXW:>7.3f} {worst:>7.3f} {rms:>6.3f} "
                  f"{nc:>6} {nl:>5}")
        best_by_R[R] = min(rows, key=lambda r: r[2]) if rows else None
        print()

    TARGET_W = 1.0          # hold the width FIXED so only the bend radius varies
    print(f"TIGHT-BEND STRESS — width held at W_eff ~= {TARGET_W} hex widths; only R varies.")
    print(f"{'R (hexw)':>9} {'W_eff':>7} {'worst':>7} {'rms':>6} {'cells':>6}")
    for R in (2.0, 3.0, 4.5, 6.0, 9.0, 13.0):
        arc = Arc(CENTRE[0], CENTRE[1], R * HEXW, math.radians(0), math.radians(120))
        rows = ladder(universe, arc, lo=0.8, hi=2.6)
        if not rows:
            print(f"{R:>9.1f}   no valid footprint")
            continue
        t, W, worst, rms, nc, nl, npts = min(rows, key=lambda r: abs(r[1]/HEXW - TARGET_W))
        print(f"{R:>9.1f} {W/HEXW:>7.3f} {worst:>7.3f} {rms:>6.3f} {nc:>6}")

    print("\nARBITRARY-CENTRE SWEEP — the expressiveness claim, quantified.")
    print("Same arc, centre nudged off-lattice in small steps; error must stay bounded.")
    print(f"{'offset':>8} {'W_eff':>7} {'worst':>7} {'rms':>6}")
    for off in (0.0, 0.13, 0.27, 0.41, 0.55, 0.69, 0.83):
        arc = Arc(off * SQ3, off * 0.7, 6.5, math.radians(10), math.radians(140))
        rows = ladder(universe, arc, lo=0.8, hi=2.6)
        if not rows:
            print(f"{off:>8.2f}   none"); continue
        t, W, worst, rms, nc, nl, npts = min(rows, key=lambda r: abs(r[1]/HEXW - TARGET_W))
        print(f"{off:>8.2f} {W/HEXW:>7.3f} {worst:>7.3f} {rms:>6.3f}")
    print(f"\n(width held at ~{TARGET_W} hex widths in both sweeps above, so the only "
          f"variable is the one named.)")

    circum = 1.0 / SQ3
    print(f"\nQUANTISATION SCALE: a hex corner sits {circum:.3f} hex widths from its centre.")
    print(f"  A cell is taken when its CENTRE is within t of the curve, so an outline VERTEX")
    print(f"  lies in [t-{circum:.3f}, t+{circum:.3f}] -> the spread reaches {2*circum:.3f} and,")
    print(f"  since W is the mean, max|d-W| is bounded by {2*circum:.3f} -- NOT by {circum:.3f}.")
    print(f"  So {circum:.3f} is the CHARACTERISTIC scale, not a hard bound (0.658 was observed).")
    print(f"  Bands sit AT that scale because their two edges quantise independently; the tower")
    print(f"  catalog reaches 0.23-0.39 because a CLOSED circle fit re-centres and cancels error.")


if __name__ == "__main__":
    main()
