#!/usr/bin/env python3
"""hexforms.py — BLUEPRINT PHASE for plan #5 / FORMS.md.

A test bench for **hex placement routines** (towers, walls, stencils) whose product is a
**validated exact vector map** — the thing a 2D renderer draws and a mesh routine extrudes.

Why this shape (the three constraints, from the user):
  * routines must be library-grade — reusable across games/editors, so the contract is
    `tagged hex cells -> vector map`, with no consumer-specific knowledge inside;
  * the end result is a VECTOR map (points/loops), not painted cells;
  * the data handed to a renderer/mesh routine must be **validated** before it is consumed.

EXACTNESS — the reason this is integer, not float:
    every hex centre AND every hex corner lies on the lattice
        x = k * sqrt(3)/2 ,  y = m / 2      (k, m integers)
    for pointy-top odd-r with circumradius 1.  So the vector map is stored as integer
    (k, m) pairs: no float drift, no epsilon compares, and a golden JSON diff is EXACT.
    Consumers multiply by (sqrt(3)/2, 1/2) at the end, once.

THE ROUND-TRIP INVARIANT (what makes the output trustworthy):
    sum of the integer shoelace over all loops  ==  12 * (number of hexes)
    A single hex shoelaces to exactly 12, holes contribute negative.  Cell-count and
    traced-outline area cannot disagree — the vector map provably describes the hex set.

Throwaway prototype in the cheapest medium, per CLAUDE.md's design/debug protocol.
Nothing here is engine code; the loft port follows a PINNED invariant, never precedes it.

    python3 plans/5-geometry/hexforms.py            # report + json + png
    python3 plans/5-geometry/hexforms.py --check    # exact diff vs the golden json
"""
import json, math, os, sys
from PIL import Image, ImageDraw

SQ3 = math.sqrt(3.0)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
GOLDEN = os.path.join(HERE, "golden", "hexforms.json")

C_EXT, C_FLOOR, C_WALL = (70, 72, 78), (204, 190, 150), (38, 36, 33)
C_LINE, C_TEXT = (250, 190, 90), (232, 230, 226)

# CANONICAL corner order — do NOT invent another one.  This is hex_grid's
# hex_corner_offset / crawler's worldmesh.loft hex_lat_offset (which the watertight
# instanced floor depends on), expressed in exact lattice units:
#   hex_grid (0,1) (-.5,.5) (-.5,-.5) (0,-1) (.5,-.5) (.5,.5)   [dx in lattice, dy world]
CORNER = [(0, 2), (-1, 1), (-1, -1), (0, -2), (1, -1), (1, 1)]
# neighbour lattice-offset -> the corner pair (i, i+1) of the shared edge
EDGE_OF = {(-1, 3): 0, (-2, 0): 1, (-1, -3): 2, (1, -3): 3, (2, 0): 4, (1, 3): 5}


def lattice(c, r):
    """Hex (col,row) -> exact integer lattice centre (k, m)."""
    return (2 * c + (r & 1), 3 * r)


def neighbors(c, r):
    """Canonical pointy-top odd-r neighbours (tools/overland_blueprint.py:133)."""
    off = (((1, 0), (-1, 0), (1, -1), (0, -1), (1, 1), (0, 1)) if r & 1
           else ((1, 0), (-1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)))
    return [(c + dc, r + dr) for dc, dr in off]


def hex_dist(dist_map, cell):
    return dist_map[cell]


def bfs(maxn):
    d, frontier = {(0, 0): 0}, [(0, 0)]
    for step in range(1, maxn + 2):
        nxt = []
        for cell in frontier:
            for nb in neighbors(*cell):
                if nb not in d:
                    d[nb] = step
                    nxt.append(nb)
        frontier = nxt
    return d


# ── candidate placement routines (add one here to put it on the bench) ────────

def f_hexdisk(N, dist):
    return {c for c, d in dist.items() if d <= N}


def f_circle(N, dist, radius):
    """Euclidean disk: the hex CENTRE must lie within `radius` (in lattice x-units)."""
    out = set()
    for cell in dist:
        k, m = lattice(*cell)
        if (k * SQ3 / 2) ** 2 + (m / 2) ** 2 <= radius ** 2 + 1e-9:
            out.add(cell)
    return out


def f_octagon(N, dist, apothem):
    out = set()
    for cell in dist:
        k, m = lattice(*cell)
        x, y = abs(k * SQ3 / 2), abs(m / 2)
        if max(x, y, (x + y) / math.sqrt(2.0)) <= apothem + 1e-9:
            out.add(cell)
    return out


# ── cell-set properties ───────────────────────────────────────────────────────

def wall_of(form):
    return {c for c in form if any(nb not in form for nb in neighbors(*c))}


def floor_of(form):
    return form - wall_of(form)


def enclosed_gaps(form, universe):
    outside = {c for c in universe if c not in form}
    if not outside:
        return set()
    far = max(outside, key=lambda c: abs(lattice(*c)[0]) + abs(lattice(*c)[1]))
    seen, stack = set(), [far]
    while stack:
        cell = stack.pop()
        if cell in seen:
            continue
        seen.add(cell)
        for nb in neighbors(*cell):
            if nb in universe and nb not in form and nb not in seen:
                stack.append(nb)
    return outside - seen


def wall_one_thick(form):
    wall, floor = wall_of(form), floor_of(form)
    if not floor:
        return False
    return all(any(nb in floor for nb in neighbors(*c)) for c in wall)


# ── the tracer: hex cells -> exact vector loops ───────────────────────────────

def trace(form):
    """Boundary of a hex set as ordered closed loops of exact integer lattice points.

    Emits each boundary edge directed corner_i -> corner_i+1, which gives every loop a
    consistent orientation (outer one way, enclosed holes the other) — what a fill rule
    and a mesh triangulator both need."""
    edges = {}
    for cell in form:
        k0, m0 = lattice(*cell)
        for nb in neighbors(*cell):
            if nb in form:
                continue
            k1, m1 = lattice(*nb)
            i = EDGE_OF[(k1 - k0, m1 - m0)]
            a = (k0 + CORNER[i][0], m0 + CORNER[i][1])
            b = (k0 + CORNER[(i + 1) % 6][0], m0 + CORNER[(i + 1) % 6][1])
            edges.setdefault(a, []).append(b)

    # TERMINATION.  The walk below is only unambiguous because every boundary vertex has
    # exactly ONE outgoing edge.  That is a real property of hex grids -- each vertex
    # touches exactly 3 MUTUALLY ADJACENT cells, so a boundary cannot pinch at a vertex
    # the way it can on a square grid (verified over 412 forms incl. 400 random blobs).
    # But relying on it silently means a bad input HANGS instead of failing, so assert it.
    bad = {a: len(bs) for a, bs in edges.items() if len(bs) != 1}
    if bad:
        raise ValueError(f"boundary vertex with out-degree != 1: {list(bad.items())[:4]} "
                         "— the hex no-pinch property does not hold for this input")

    loops = []
    remaining = {a: list(bs) for a, bs in edges.items()}
    budget = sum(len(bs) for bs in edges.values()) + 1     # every edge is used once
    while any(remaining.values()):
        start = next(a for a, bs in remaining.items() if bs)
        loop, cur = [start], start
        while True:
            budget -= 1
            if budget < 0:
                raise ValueError("tracer did not terminate — edge budget exhausted")
            nxt_list = remaining.get(cur)
            if not nxt_list:
                raise ValueError(f"open boundary: no edge leaves {cur} "
                                 "(the cell set is not closed)")
            nxt = nxt_list.pop()
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        loops.append(canonical(loop))
    return loops


def canonical(loop):
    """Rotate a loop to start at its lexicographically smallest vertex.

    A traced cycle is the same shape whichever edge you seed from, so the raw start
    vertex is an artefact of iteration order -- and two correct implementations will
    disagree on it.  Canonicalising makes the emitted vector map UNIQUE, which is what
    lets the golden JSON act as a language-neutral contract (the loft port found this)."""
    if not loop:
        return loop
    i = min(range(len(loop)), key=lambda j: loop[j])
    return loop[i:] + loop[:i]


def shoelace2(loop):
    """Twice the signed area, in integer lattice units.  Exact."""
    s = 0
    for i, (k, m) in enumerate(loop):
        k2, m2 = loop[(i + 1) % len(loop)]
        s += k * m2 - k2 * m
    return s


# ── THE VALIDATOR — what must hold before a renderer/mesh may consume it ──────

def validate(loops, form):
    """Return a list of failures; empty means the vector map is safe to consume."""
    bad = []
    if not loops:
        bad.append("no loops emitted")
        return bad

    for li, loop in enumerate(loops):
        if len(loop) < 3:
            bad.append(f"loop {li}: degenerate ({len(loop)} pts)")
        if len(set(loop)) != len(loop):
            bad.append(f"loop {li}: repeated vertex (self-touching)")
        for i, p in enumerate(loop):
            q = loop[(i + 1) % len(loop)]
            if p == q:
                bad.append(f"loop {li}: zero-length segment at {i}")
            dk, dm = q[0] - p[0], q[1] - p[1]
            if (dk, dm) not in {(1, 1), (-1, -1), (1, -1), (-1, 1), (0, 2), (0, -2)}:
                bad.append(f"loop {li}: segment {p}->{q} is not a hex edge")
        if any(not (isinstance(k, int) and isinstance(m, int)) for k, m in loop):
            bad.append(f"loop {li}: non-integer vertex (lattice drift)")

    total = sum(shoelace2(l) for l in loops)
    want = 12 * len(form)
    if total != want:
        bad.append(f"AREA ROUND-TRIP: shoelace {total} != 12*cells {want}")

    outer = [l for l in loops if shoelace2(l) > 0]
    if len(outer) != 1:
        bad.append(f"expected exactly 1 outer loop, got {len(outer)}")
    return bad


# ── rendering (the eyeball pass — the JSON is the accuracy gate) ──────────────

def draw(dr, form, loops, ox, oy, s, title, sub):
    wall = wall_of(form)
    for cell in sorted(form, key=lambda t: (t[1], t[0])):
        k, m = lattice(*cell)
        cx, cy = ox + k * SQ3 / 2 * s, oy + m / 2 * s
        pts = [(ox + (k + dk) * SQ3 / 2 * s, oy + (m + dm) / 2 * s) for dk, dm in CORNER]
        dr.polygon(pts, fill=C_WALL if cell in wall else C_FLOOR)
    for loop in loops:
        pts = [(ox + k * SQ3 / 2 * s, oy + m / 2 * s) for k, m in loop]
        dr.line(pts + [pts[0]], fill=C_LINE, width=2)
    dr.text((ox - 58, oy - 74), title, fill=C_TEXT)
    dr.text((ox - 58, oy - 62), sub, fill=C_TEXT)


def main():
    check = "--check" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    MAXN = 6
    dist = bfs(MAXN + 3)

    routines = [
        ("A hex-disk (today)", lambda N: f_hexdisk(N, dist)),
        ("B circle-raster",    lambda N: f_circle(N, dist, (N + 0.45) * SQ3)),
        ("C octagon",          lambda N: f_octagon(N, dist, (N + 0.35) * 1.5)),
    ]

    print(f"{'routine':20} {'N':>2} {'cells':>5} {'wall':>5} {'floor':>5} {'gaps':>5} "
          f"{'thin':>5} {'loops':>5} {'pts':>4} {'valid':>6}")
    report, failures = {}, 0
    for name, fn in routines:
        prev = None
        for N in range(1, MAXN + 1):
            form = fn(N)
            loops = trace(form)
            errs = validate(loops, form)
            gaps = len(enclosed_gaps(form, dist))
            thin = wall_one_thick(form)
            nested = prev is None or prev <= form
            ok = not errs and gaps == 0 and thin and nested
            failures += 0 if ok else 1
            print(f"{name:20} {N:>2} {len(form):>5} {len(wall_of(form)):>5} "
                  f"{len(floor_of(form)):>5} {gaps:>5} {str(thin):>5} {len(loops):>5} "
                  f"{sum(len(l) for l in loops):>4} {'ok' if ok else 'FAIL':>6}")
            for e in errs:
                print(f"    ! {e}")
            if not nested:
                print(f"    ! not nested inside N={N-1}")
            report[f"{name.split()[0]}:{N}"] = {
                "cells": len(form), "wall": len(wall_of(form)),
                "loops": [[list(p) for p in l] for l in loops],
            }
            prev = form

    print(f"\nbench: {'ALL PASS' if failures == 0 else f'{failures} FAILURE(S)'}")

    # exactness gate: integer JSON, compared byte-for-byte
    blob = json.dumps(report, indent=1, sort_keys=True)
    if check:
        if not os.path.exists(GOLDEN):
            print(f"no golden at {GOLDEN} — run without --check first"); sys.exit(1)
        same = open(GOLDEN).read() == blob
        print(f"golden: {'MATCH (exact)' if same else 'DRIFT'}")
        sys.exit(0 if same and failures == 0 else 1)
    os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
    if not os.path.exists(GOLDEN):
        open(GOLDEN, "w").write(blob)
        print(f"wrote golden {GOLDEN}")
    open(os.path.join(OUT, "hexforms.json"), "w").write(blob)

    s, colw, rowh = 11, 300, 250
    img = Image.new("RGB", (colw * len(routines) + 40, rowh * MAXN + 40), C_EXT)
    dr = ImageDraw.Draw(img)
    for ci, (name, fn) in enumerate(routines):
        for N in range(1, MAXN + 1):
            form = fn(N)
            loops = trace(form)
            draw(dr, form, loops, 90 + ci * colw + 60, 100 + (N - 1) * rowh, s,
                 f"{name}  N={N}",
                 f"cells={len(form)} loops={len(loops)} pts={sum(len(l) for l in loops)}")
    img.save(os.path.join(OUT, "hexforms.png"))
    print(f"wrote {OUT}/hexforms.png and hexforms.json")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
