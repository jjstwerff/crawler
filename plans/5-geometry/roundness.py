#!/usr/bin/env python3
"""roundness.py — is a hexagon still the right tower shape at size?

The footprint is reused for (a) the drawn form, (b) COLLISION, and probably (c) the same
rounding model for curved roads.  That makes "which family" a systems question, not a
taste question — so measure it.

Collision metric: the EFFECTIVE RADIUS as a function of approach direction.  A shape whose
radius depends on the angle you approach from feels wrong to walk into / shoot past, and
the error is bounded below by the family, not by the raster.

    python3 plans/5-geometry/roundness.py
"""
import math, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import (SQ3, bfs, lattice, neighbors, wall_of, trace, shoelace2,
                      f_hexdisk, f_circle, f_octagon)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
C_BG, C_TEXT = (28, 30, 34), (232, 230, 226)
SERIES = [("A hex-disk", (250, 140, 90)), ("B circle", (120, 200, 250)),
          ("C octagon", (170, 230, 140))]


def world(cell):
    k, m = lattice(*cell)
    return (k * SQ3 / 2, m / 2)


def ring_radii(form):
    """Distance from centre to each WALL cell centre — the collision surface."""
    return sorted(math.hypot(*world(c)) for c in wall_of(form))


def outline_radii(form, samples=720):
    """Effective radius per approach angle: where a ray from the centre leaves the form.

    Cast against the traced outline segments — this is what a collision query sees."""
    loops = trace(form)
    outer = max(loops, key=lambda l: abs(shoelace2(l)))
    pts = [(k * SQ3 / 2, m / 2) for k, m in outer]
    segs = list(zip(pts, pts[1:] + pts[:1]))
    out = []
    for i in range(samples):
        th = 2 * math.pi * i / samples
        dx, dy = math.cos(th), math.sin(th)
        best = 0.0
        for (x1, y1), (x2, y2) in segs:
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = (ex * (-y1) - ey * (-x1)) / den      # ray param
            u = (dx * (-y1) - dy * (-x1)) / den      # segment param
            if t > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = max(best, t)
        out.append((th, best))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    dist = bfs(14)
    SIZES = [3, 4, 5, 6, 8, 10]
    fams = [("A hex-disk", lambda N: f_hexdisk(N, dist)),
            ("B circle",   lambda N: f_circle(N, dist, (N + 0.45) * SQ3)),
            ("C octagon",  lambda N: f_octagon(N, dist, (N + 0.35) * 1.5))]

    print("COLLISION — effective radius vs approach direction (ray-cast on the outline)")
    print("  anisotropy = r_max/r_min   (1.000 = a true circle)")
    print(f"\n{'family':12} {'N':>2} {'cells':>5} {'r_min':>7} {'r_max':>7} "
          f"{'aniso':>7} {'err_hexw':>9} {'iso Q':>7}")
    data = {}
    for name, fn in fams:
        for N in SIZES:
            form = fn(N)
            rr = outline_radii(form)
            rs = [r for _, r in rr]
            rmin, rmax = min(rs), max(rs)
            aniso = rmax / rmin
            # area is exact from the integer shoelace; perimeter from the outline
            loops = trace(form)
            outer = max(loops, key=lambda l: abs(shoelace2(l)))
            A = abs(shoelace2(outer)) * SQ3 / 8
            pts = [(k * SQ3 / 2, m / 2) for k, m in outer]
            P = sum(math.dist(p, q) for p, q in zip(pts, pts[1:] + pts[:1]))
            Q = 4 * math.pi * A / (P * P)
            # worst radial error against the equal-area circle, in HEX WIDTHS
            r_eq = math.sqrt(A / math.pi)
            err = max(abs(r - r_eq) for r in rs) / SQ3
            print(f"{name:12} {N:>2} {len(form):>5} {rmin:>7.3f} {rmax:>7.3f} "
                  f"{aniso:>7.3f} {err:>9.3f} {Q:>7.3f}")
            data[(name, N)] = rr
        print()

    # radius-vs-angle plot at one large size — the picture of the collision surface
    N = 8
    W = H = 720
    img = Image.new("RGB", (W, H), C_BG)
    dr = ImageDraw.Draw(img)
    cx, cy, s = W / 2, H / 2 + 10, 26
    for rad, col in ((6, (60, 62, 68)), (8, (60, 62, 68)), (10, (60, 62, 68))):
        dr.ellipse([cx - rad * s * SQ3 / SQ3, cy - rad * s, cx + rad * s, cy + rad * s],
                   outline=col)
    for (name, col) in SERIES:
        rr = data[(name, N)]
        pts = [(cx + r * math.cos(t) * s / SQ3 * SQ3 / SQ3 * SQ3,
                cy + r * math.sin(t) * s / SQ3 * SQ3 / SQ3 * SQ3) for t, r in rr]
        pts = [(cx + r * math.cos(t) * s / SQ3, cy + r * math.sin(t) * s / SQ3)
               for t, r in rr]
        dr.line(pts + [pts[0]], fill=col, width=2)
    dr.text((16, 14), f"collision surface at N={N} — radius vs approach angle", fill=C_TEXT)
    for i, (name, col) in enumerate(SERIES):
        rr = [r for _, r in data[(name, N)]]
        dr.text((16, 36 + i * 14),
                f"{name}   aniso={max(rr)/min(rr):.3f}", fill=col)
    img.save(os.path.join(OUT, "roundness.png"))
    print(f"wrote {OUT}/roundness.png")

    # ---- the ROADS question: can the family express an arbitrary arc?
    print("\nROADS — can the family express an arc that is NOT hex-centred / integer-radius?")
    print("  test: a disk of radius 4.30 centred at the midpoint BETWEEN two hexes")
    off = (0.5 * SQ3, 0.0)                     # between two horizontal neighbours
    for name, fn in fams:
        if name.startswith("A"):
            print(f"  {name:12} NO — `hex_distance <= N` is defined only from a hex "
                  f"centre, integer N.  No expression for r=4.30 off-centre.")
            continue
        cells = set()
        for cell in dist:
            x, y = world(cell)
            if math.hypot(x - off[0], y - off[1]) <= 4.30:
                cells.add(cell)
        loops = trace(cells)
        print(f"  {name:12} yes — {len(cells)} cells, {len(loops)} loop(s); the predicate "
              f"is a distance test, so centre and radius are free.")


if __name__ == "__main__":
    main()
