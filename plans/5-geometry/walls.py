#!/usr/bin/env python3
"""walls.py — can a block be pushed inward?  The arch principle, in plan view.

For a wall-building game where attacks PUSH: a "correctly built" wall is one whose blocks
cannot be driven inward.  That is a purely KINEMATIC question and it is decidable from
the geometry alone, before any force or material is considered.

THE TEST.  A block sits between two joint faces.  Face i has an outward normal n_i
pointing from the block toward its neighbour.  If the block translates by u it drives
into that neighbour exactly when u . n_i > 0.  So:

    the block can move along u   <=>   u . n_i <= 0  for EVERY face i
    the block is LOCKED against u   <=>   some face has u . n_i > 0

For a wall built with **radial joints** (joint planes perpendicular to the centreline),
that resolves to one signed scalar per block:

    interlock = signed turn angle across the block = curvature * block_length

  * wall curving AWAY from the attacker  -> faces converge inward, block WEDGES  -> LOCKED
  * straight wall                        -> faces parallel, block slides straight through
  * wall curving TOWARD the attacker     -> faces diverge inward, block falls in  -> WORSE

So curvature is not decoration: it is the whole mechanism.  A straight wall is pushable
by construction and only friction resists it; an arch cannot be pushed inward at all.

Scope: this is the LOCAL (block-through-wall) failure mode.  The GLOBAL mode -- the ring
spreading / hinging, classical thrust-line analysis -- is a separate question and is
flagged, not solved, here.

    python3 plans/5-geometry/walls.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import SQ3
from ways import Straight, ArcSeg, Track

HEXW = SQ3


def blocks(track, block_len):
    """Cut the centreline into blocks; joints are perpendicular to the centreline."""
    out = []
    for seg in track.segs:
        n = max(1, int(round(seg.len / block_len)))
        for i in range(n):
            s0, s1 = seg.len * i / n, seg.len * (i + 1) / n
            out.append({
                "seg": seg,
                "s0": s0, "s1": s1,
                "p0": seg.point(s0), "p1": seg.point(s1),
                "t0": seg.tangent(s0), "t1": seg.tangent(s1),
                "mid": seg.point((s0 + s1) / 2),
                "tmid": seg.tangent((s0 + s1) / 2),
                "k": seg.curvature((s0 + s1) / 2),
                "len": s1 - s0,
            })
    return out


def left_normal(t):
    return (-t[1], t[0])


def can_translate(b, u):
    """Can the block move along u without driving into either neighbour?

    Face normals point OUT of the block toward each neighbour: -t0 at the start joint,
    +t1 at the end joint."""
    n_start = (-b["t0"][0], -b["t0"][1])
    n_end = (b["t1"][0], b["t1"][1])
    d0 = u[0]*n_start[0] + u[1]*n_start[1]
    d1 = u[0]*n_end[0] + u[1]*n_end[1]
    return max(d0, d1) <= 1e-12, max(d0, d1)


def signed_curvature(seg, s):
    """+k = turning left (centre of curvature on the LEFT of travel), -k = turning right."""
    if isinstance(seg, ArcSeg):
        return (1.0 / seg.R) * (1 if seg.a1 >= seg.a0 else -1)
    return 0.0


def analyse(track, block_len, attacker_convex):
    """Per-block verdict.  `attacker_convex=True` = the attacker stands on the CONVEX
    (outer) side and pushes inward — the normal siege case."""
    rows = []
    for b in blocks(track, block_len):
        k = signed_curvature(b["seg"], (b["s0"] + b["s1"]) / 2)
        n_left = left_normal(b["tmid"])
        # +k: centre on the LEFT -> concave side is LEFT, convex side is RIGHT.
        if k > 0:
            convex_normal = (-n_left[0], -n_left[1])     # points out of the convex side
        elif k < 0:
            convex_normal = n_left
        else:
            convex_normal = n_left                       # straight: pick a side, no wedge
        # the attacker pushes INTO the wall from their side
        u = ((-convex_normal[0], -convex_normal[1]) if attacker_convex
             else (convex_normal[0], convex_normal[1]))
        free, drive = can_translate(b, u)
        turn = abs(k) * b["len"]
        rows.append({**b, "k": k, "free": free, "drive": drive, "turn": turn,
                     "signed": turn if attacker_convex else -turn})
    return rows


def report(name, track, block_len, attacker_convex):
    rows = analyse(track, block_len, attacker_convex)
    free = [r for r in rows if r["free"]]
    print(f"\n{name}")
    print(f"  blocks={len(rows)}  block_len={block_len}  "
          f"attacker on the {'CONVEX (outside)' if attacker_convex else 'CONCAVE (inside)'} side")
    turns = [math.degrees(r['signed']) for r in rows]
    print(f"  turn across a block: {min(turns):+.3f}..{max(turns):+.3f} deg")
    if free:
        worst = max(free, key=lambda r: -r["drive"])
        print(f"  ** {len(free)}/{len(rows)} blocks CAN be pushed inward "
              f"(weakest drive margin {worst['drive']:+.2e})")
    else:
        margin = min(r["drive"] for r in rows)
        print(f"  all {len(rows)} blocks LOCKED — min penetration margin {margin:+.4f}")
    return rows


def main():
    R = 9.0
    THICK = 2.0
    BLOCK = 1.2

    print("PUSH RESISTANCE — can a block be driven inward?")
    print(f"wall thickness {THICK}, block length {BLOCK} "
          f"({BLOCK/HEXW:.2f} hex widths), arc radius {R}\n")
    print("A block is LOCKED when no inward translation exists that avoids driving into")
    print("a neighbour.  Curvature is what creates that; a straight wall has none.")

    # 1. straight wall — the baseline
    st = Track([Straight((-12.0, 0.0), (12.0, 0.0))])
    report("STRAIGHT WALL — no curvature, so no wedge", st, BLOCK, attacker_convex=True)

    # 2. arc curving AWAY from the attacker (convex toward them) — the correct build
    arc = ArcSeg((0.0, 0.0), R, math.radians(200), math.radians(340))
    report("CURVED WALL — attacker on the CONVEX side (bulging toward them): CORRECT",
           Track([arc]), BLOCK, attacker_convex=True)

    # 3. same arc, attacker on the concave side — the wrong way round
    report("SAME WALL — attacker on the CONCAVE side (wall cups toward them): WRONG",
           Track([arc]), BLOCK, attacker_convex=False)

    # 4. how much curvature is enough?
    print("\nHOW MUCH CURVATURE IS ENOUGH?  The binary verdict is NOT the useful number:")
    print("  ANY non-zero curvature locks geometrically, but a 0.3-degree wedge is swamped")
    print("  by block irregularity and mortar. What matters is the INTERLOCK MARGIN.")
    print(f"\n  {'R':>7} {'turn/block':>11} {'verdict':>8} {'margin':>9} {'~len/(2R)':>10}")
    for Rt in (200.0, 60.0, 25.0, 9.0, 4.0, 2.0):
        a = ArcSeg((0.0, 0.0), Rt, math.radians(200), math.radians(340))
        rows = analyse(Track([a]), BLOCK, attacker_convex=True)
        anyfree = any(r["free"] for r in rows)
        margin = min(r["drive"] for r in rows)
        print(f"  {Rt:>7.1f} {math.degrees(BLOCK/Rt):>10.3f}° "
              f"{'PUSHABLE' if anyfree else 'locked':>8} {margin:>9.4f} {BLOCK/(2*Rt):>10.4f}")
    print("\n  -> the margin matches block_len/(2R) to 3 decimals. THE GAME RULE:")
    print("\n         interlock margin  ~=  block_length / (2 * radius)")
    print("\n     Tighter curve and LONGER blocks resist more; a straight wall scores 0.")
    print("     That is a designer-facing number, not a physics simulation.")

    # 5. the closed ring — a tower
    print("\nCLOSED RING (a round tower) — every block locked, from every direction:")
    ring = Track([ArcSeg((0.0, 0.0), R, 0.0, 2*math.pi)])
    rows = analyse(ring, BLOCK, attacker_convex=True)
    print(f"  blocks={len(rows)}  free={sum(1 for r in rows if r['free'])}  "
          f"-> a ring cannot be pushed in anywhere; it can only SPREAD.")

    print("\nWHAT THIS DOES NOT COVER (flagged, not solved)")
    print("  * GLOBAL failure: the ring spreading or forming hinges (thrust-line analysis).")
    print("    Local interlock says a block cannot pass through; it does not say the wall")
    print("    cannot open up. A closed ring resists spreading; an open arc needs buttresses.")
    print("  * FRICTION: a straight wall is not instantly pushable in practice — friction")
    print("    resists it. But it has NO geometric interlock, so it degrades to a material")
    print("    property, which is exactly what a 'correctly built' wall should not rely on.")


if __name__ == "__main__":
    main()
