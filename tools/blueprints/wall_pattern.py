#!/usr/bin/env python3
"""Blueprint — BRICK/STONE wall-surface pattern on the R5 capsule stroke (extends
wall_sdf.py / RENDER.md R5). Plots EXACTLY what a patterned wall fragment would compute:
the capsule coverage `cov` is UNCHANGED (so join continuity is inherited); the pattern only
RECOLORS the covered pixels, in wall-local (u,v) coords carried by the quad's loc1 = (u,v,len).

THE PREDICTION (written before probing):
  Invariant — a wall face is a jittered-boundary lattice in (u,v): u along the wall split into
  brick cells of length L (mortar = SDF gaps at the cell boundaries, analytic-AA'd by the same
  1px ramp as the stroke), v split into NC courses; alternate courses offset by `bond`*L
  (RUNNING BOND). brick = zero boundary jitter (crisp, periodic) → the man-made uniform case;
  stone = large seeded boundary jitter in u and v + per-row offset → irregular ashlar — SAME
  lattice, jitter is the only difference (the decorative-pattern "uniform vs hide" axis). All
  jitter is a reproducible integer hash (never random()). The pattern multiplies INTO `cov`, so
  it never paints outside the stroke and the join stays continuous (cov composition unchanged);
  mortar lines just seam at a corner (a quoin), opening NO floor gap. Brick uniform
  (ujit=vjit=0) is reachable and exactly periodic.
  Re-assertion sites: ONE pattern() function per fragment (N=1).

Run:  python3 tools/blueprints/wall_pattern.py   # PASS/FAIL report + /tmp/bp_wall_pattern_*.png
The report's numbers seed a future world_r*.probe (same role as wall_sdf.py for R5).
"""
import math
from PIL import Image

# ── shared with wall_sdf.py (the R5 stroke this sits on) ──────────────────────
SCALE = 26.0                  # px per world unit (the view's SCALE) — probe scale
HALFW = 0.09                  # stroke half-width, world units (~4.7px full width)
FLOOR = (165, 175, 114)       # the R4-baked floor (greenish)


def seg_dist_t(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
    dx, dy = px - (ax + vx * t), py - (ay + vy * t)
    return math.hypot(dx, dy)


def wall_local(px, py, ax, ay, bx, by):
    """Pixel → (u along the seg, v signed-across, len). u/v in world units."""
    vx, vy = bx - ax, by - ay
    ln = math.hypot(vx, vy) or 1e-9
    dx, dy = vx / ln, vy / ln           # along
    nx, ny = -dy, dx                    # across (left normal)
    u = (px - ax) * dx + (py - ay) * dy
    v = (px - ax) * nx + (py - ay) * ny
    return u, v, ln


# ── deterministic hash (NO random()) ─────────────────────────────────────────
def h01(*ints):
    x = 2166136261
    for val in ints:
        x = ((x ^ (val & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return x / 0xFFFFFFFF                 # [0,1)


def hsym(*ints):
    return h01(*ints) * 2.0 - 1.0        # [-1,1)


# ── pattern params ────────────────────────────────────────────────────────────
BRICK = dict(stone=False, L=0.22, mortar=0.035, nc=2, ujit=0.0, vjit=0.0,
             bond=0.5, tone=0.10, face=(150, 80, 60), mortar_c=(92, 74, 66))
STONE = dict(stone=True,  L=0.26, mortar=0.040, nc=3, ujit=0.34, vjit=0.28,
             bond=0.5, tone=0.22, face=(146, 142, 130), mortar_c=(98, 95, 88))


def _ubnd(k, r, P, seed):
    """World-u position of the displaced cell-boundary k in course r (in u-space)."""
    off = (h01(seed, r, 13) * P['L']) if P['stone'] else (r % 2) * P['bond'] * P['L']
    return k * P['L'] + P['ujit'] * P['L'] * hsym(seed, k, r, 3) - off


def _vbnds(P, seed):
    """Fractional v positions (0..1 across the thickness) of the NC-1 course boundaries."""
    return [rr / P['nc'] + P['vjit'] * hsym(seed, rr, 7) * (0.5 / P['nc'])
            for rr in range(1, P['nc'])]


def pattern_rgb(u, v, P, seed, aaw):
    """The wall-face color at wall-local (u,v) — brick/stone lattice with AA'd mortar.
    Returns an (r,g,b) tuple. Pure recolor; coverage/clip is the caller's `cov`."""
    vspan = 2 * HALFW
    fv = (v + HALFW) / vspan                      # 0..1 across the thickness
    vb = _vbnds(P, seed)
    r = sum(1 for fb in vb if fv >= fb)           # course index
    d_v = min((abs(fv - fb) for fb in vb), default=1e9) * vspan   # → world units

    off = (h01(seed, r, 13) * P['L']) if P['stone'] else (r % 2) * P['bond'] * P['L']
    us = u + off
    k0 = round(us / P['L'])
    cellk = k0
    for k in (k0 - 1, k0, k0 + 1):                 # the cell whose [bk,bk+1) holds us
        bk = k * P['L'] + P['ujit'] * P['L'] * hsym(seed, k, r, 3)
        bn = (k + 1) * P['L'] + P['ujit'] * P['L'] * hsym(seed, k + 1, r, 3)
        if bk <= us < bn:
            cellk = k
            break
    d_u = min(abs(us - (k * P['L'] + P['ujit'] * P['L'] * hsym(seed, k, r, 3)))
              for k in (k0 - 1, k0, k0 + 1, k0 + 2))

    dm = min(d_u, d_v)                             # distance to nearest mortar line
    t_m = max(0.0, min(1.0, (P['mortar'] * 0.5 - dm) / aaw + 0.5))   # AA'd mortar amount
    tj = 1.0 + P['tone'] * hsym(seed, cellk, r, 5)                   # per-cell tone
    face = tuple(c * tj for c in P['face'])
    groove = 0.55 + 0.45 * max(0.0, min(1.0, dm / (P['mortar'] * 0.5)))  # V-groove shadow
    mort = tuple(c * groove for c in P['mortar_c'])
    return tuple(face[i] * (1 - t_m) + mort[i] * t_m for i in range(3))


# ── render (gestalt): capsule cov UNCHANGED, pattern recolors the covered pixels ──
def render(segs, P, seed, scale, path):
    aaw = 1.0 / scale
    minx = min(min(a[0], b[0]) for a, b in segs) - 0.6
    maxx = max(max(a[0], b[0]) for a, b in segs) + 0.6
    miny = min(min(a[1], b[1]) for a, b in segs) - 0.6
    maxy = max(max(a[1], b[1]) for a, b in segs) + 0.6
    W, H = int((maxx - minx) * scale), int((maxy - miny) * scale)
    img = Image.new("RGB", (W, H), FLOOR)
    px = img.load()
    for (ax, ay), (bx, by) in segs:
        for y in range(H):
            wy = miny + (y + 0.5) / scale
            for x in range(W):
                wx = minx + (x + 0.5) / scale
                d = seg_dist_t(wx, wy, ax, ay, bx, by)
                c = max(0.0, min(1.0, (HALFW - d) / aaw + 0.5))    # the R5 coverage
                if c > 0:
                    u, v, ln = wall_local(wx, wy, ax, ay, bx, by)
                    pr = pattern_rgb(u, v, P, seed, aaw)
                    cur = px[x, y]
                    px[x, y] = tuple(round(pr[i] * c + cur[i] * (1 - c)) for i in range(3))
    img.save(path)
    return img, (minx, miny), scale


# ── probes (try to FALSIFY each load-bearing claim) ───────────────────────────
def run():
    res = []
    chk = lambda name, ok, det="": res.append((name, ok, det))
    aaw = 1.0 / SCALE
    seed = 5

    # P-brick-periodic + uniform reachable: ujit=0 → boundaries exactly k*L - off, spacing L.
    b0 = [_ubnd(k, 0, BRICK, seed) for k in range(6)]
    sp = [b0[i + 1] - b0[i] for i in range(5)]
    chk("P-brick boundaries exactly periodic (uniform reachable)",
        all(abs(s - BRICK['L']) < 1e-12 for s in sp), f"spacings={[round(s,4) for s in sp]}")

    # P-running-bond: course 1 offset from course 0 by exactly L/2 (bond=0.5).
    b1 = [_ubnd(k, 1, BRICK, seed) for k in range(6)]
    offset = (b0[0] - b1[0]) % BRICK['L']
    chk("P-running-bond course offset = L/2",
        abs(min(offset, BRICK['L'] - offset) - BRICK['L'] / 2) < 1e-12,
        f"offset={offset:.4f} want {BRICK['L']/2:.4f}")

    # P-mortar width constant: the AA'd mortar (t_m>0.5) spans exactly `mortar` across a boundary.
    boundary_u = b0[2] + (0 if not BRICK['stone'] else 0)   # a course-0 u-boundary in u-space
    # sample dm via u offset around the boundary at mid-course (v at course-0 centre)
    vc = -HALFW + (0.5 / BRICK['nc']) * (2 * HALFW)
    span = 0
    NS = 400
    for i in range(NS):
        du = (i / NS - 0.5) * 3 * BRICK['mortar']         # ±1.5*mortar around it
        u = boundary_u + du
        # t_m at this point (course 0): reuse pattern's mortar calc via distance to nearest u-bnd
        k0 = round((u) / BRICK['L'])
        d_u = min(abs(u - _ubnd(k, 0, BRICK, seed)) for k in (k0 - 1, k0, k0 + 1, k0 + 2))
        t_m = max(0.0, min(1.0, (BRICK['mortar'] * 0.5 - d_u) / aaw + 0.5))
        if t_m > 0.5:
            span += (3 * BRICK['mortar']) / NS
    chk("P-mortar full-width = mortar param", abs(span - BRICK['mortar']) < 2 * aaw,
        f"width={span:.4f} want {BRICK['mortar']:.4f} (±{2*aaw:.4f})")

    # P-stone boundaries monotonic (jitter < L/2 ⇒ no crossing / no inverted cells)
    sb = [_ubnd(k, 1, STONE, seed) for k in range(40)]
    mono = all(sb[i + 1] > sb[i] for i in range(len(sb) - 1))
    widths = [sb[i + 1] - sb[i] for i in range(len(sb) - 1)]
    chk("P-stone cells monotonic + bounded", mono and min(widths) > 0.2 * STONE['L'],
        f"min cell={min(widths):.4f} max={max(widths):.4f} L={STONE['L']}")

    # P-determinism: pattern is reproducible, and tone varies cell-to-cell (not flat).
    a = pattern_rgb(0.05, 0.0, BRICK, seed, aaw)
    a2 = pattern_rgb(0.05, 0.0, BRICK, seed, aaw)
    faces = [pattern_rgb(k * BRICK['L'] + BRICK['L'] * 0.5, vc, BRICK, seed, aaw) for k in range(6)]
    varied = len(set(tuple(round(c) for c in f) for f in faces)) >= 3
    chk("P-determinism reproducible + per-cell tone varies", a == a2 and varied,
        f"repro={a==a2} distinct_faces={len(set(tuple(round(c) for c in f) for f in faces))}/6")

    # P-clip + P-join: render the brick join, check (a) pixels outside the stroke are pure
    # floor (pattern never leaks), (b) the union interior near the corner is NEVER floor
    # (cov composition keeps it covered — join continuity inherited from R5).
    A, B = (1.6, 4.0), (6.4, 4.0)
    C = (B[0] + 4 * 0.5, B[1] - 4 * 0.8660254)             # 120° join at B
    img, (minx, miny), scl = render([(A, B), (B, C)], BRICK, seed, SCALE, "/tmp/bp_wall_pattern_join.png")
    pxj = img.load(); Wj, Hj = img.size
    # (a) clip: a point 0.4 world-units off the seg is floor
    ox, oy = int((3.0 - minx) * scl), int((4.0 + 0.45 - miny) * scl)
    chk("P-clip pattern stays inside the stroke", pxj[ox, oy] == FLOOR,
        f"off-stroke px={pxj[ox,oy]} want {FLOOR}")
    # (b) join continuity: interior within (halfw-2px) of EITHER seg near B is never floor
    leaks = 0
    for yy in range(int((B[1] - 0.45 - miny) * scl), int((B[1] + 0.2 - miny) * scl)):
        for xx in range(int((B[0] - 0.45 - minx) * scl), int((B[0] + 0.45 - minx) * scl)):
            if 0 <= xx < Wj and 0 <= yy < Hj:
                wx, wy = minx + (xx + 0.5) / scl, miny + (yy + 0.5) / scl
                d = min(seg_dist_t(wx, wy, *A, *B), seg_dist_t(wx, wy, *B, *C))
                if d < HALFW - 2 / scl and pxj[xx, yy] == FLOOR:
                    leaks += 1
    chk("P-join continuity (no floor gap in union interior)", leaks == 0, f"floor-leak px={leaks}")

    return res


if __name__ == "__main__":
    print("=== WALL PATTERN BLUEPRINT — falsification probes ===")
    res = run()
    for name, ok, det in res:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:46} {det}")
    print(f"  {sum(1 for _, ok, _ in res if ok)}/{len(res)} pass")

    # gestalt (magnified 4× for inspection — the pattern at the shipped SCALE=26 is ~5px/brick)
    GS = 96.0
    seg = [((1.0, 3.0), (9.0, 3.0))]
    render(seg, BRICK, 5, GS, "/tmp/bp_wall_pattern_brick.png")
    render(seg, STONE, 9, GS, "/tmp/bp_wall_pattern_stone.png")
    print("  renders → /tmp/bp_wall_pattern_{brick,stone,join}.png")
