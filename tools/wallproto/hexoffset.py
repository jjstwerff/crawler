#!/usr/bin/env python3
"""Proof-of-concept: migrate crawler's hex geometry from AXIAL to moros's
POINTY-TOP, ODD-R OFFSET, so rectangular rooms render UPRIGHT (not sheared).

moros convention (tools/build_overworld_map.py, data/overworld.json):
  pointy-top, odd-r offset — odd rows shifted half a hex right.
  x = √3·(col + ½·(row&1))      y = 1.5·row        (size R = 1)

This pins the EXACT model before porting to src/hexgeo.loft. It is its own
verification: it asserts the invariants the kernel relies on, so a wrong
neighbour delta or distance formula fails here, cheaply, not in the game.

Invariants checked:
  1. adjacency      — every hex_neighbor() result is physically distance √3 away
  2. symmetry       — a is b's neighbour  <=>  b is a's neighbour
  3. distance       — hex_distance() == BFS graph distance over hex_neighbor()
  4. round-trip     — px_to_hex(hex_to_px(h)) == h   for every cell
Then renders an offset-rect dungeon: rooms come out UPRIGHT, and the wall
straightener (snap boundary corners onto each room's 4 known edge-lines) gives
straight walls + smooth corridors — the same straightener, now on upright rooms.

    python3 hexoffset.py        # asserts + ./out/offset_*.png
"""
import math, os
from PIL import Image, ImageDraw

S3 = math.sqrt(3.0); HW = S3 / 2.0

# ── placement (odd-r offset) ─────────────────────────────────────────
def hex_to_px(col, row):
    return (S3 * (col + 0.5 * (row & 1)), 1.5 * row)

CORNER = {0:(0.0,1.0), 1:(-HW,0.5), 2:(-HW,-0.5), 3:(0.0,-1.0), 4:(HW,-0.5), 5:(HW,0.5)}
def hex_corner_px(col, row, i):
    cx, cy = hex_to_px(col, row); ox, oy = CORNER[i]; return (cx + ox, cy + oy)

# ── neighbours (dir 0..5 = E,NE,NW,W,SW,SE — same compass order as the axial
#    version, so edge_corners() and callers keep their meaning). Parity-dependent. ──
NB_EVEN = {0:(+1,0), 1:(0,-1), 2:(-1,-1), 3:(-1,0), 4:(-1,+1), 5:(0,+1)}
NB_ODD  = {0:(+1,0), 1:(+1,-1), 2:(0,-1), 3:(-1,0), 4:(0,+1), 5:(+1,+1)}
def hex_neighbor(col, row, d):
    dc, dr = (NB_ODD if (row & 1) else NB_EVEN)[d]
    return (col + dc, row + dr)

# ── offset <-> cube/axial + distance ─────────────────────────────────
def offset_to_axial(col, row):           # odd-r -> axial (q,r)
    return (col - (row - (row & 1)) // 2, row)
def axial_to_offset(q, r):               # axial -> odd-r (col,row)
    return (q + (r - (r & 1)) // 2, r)
def hex_distance(c1, r1, c2, r2):
    q1, s1 = offset_to_axial(c1, r1); q2, s2 = offset_to_axial(c2, r2)
    return (abs(q1 - q2) + abs(q1 + s1 - q2 - s2) + abs(s1 - s2)) // 2

# ── pixel -> hex (axial inverse, cube-round, then ->offset) ──────────
def _axial_round(qf, rf):
    xf, zf = qf, rf; yf = -xf - zf
    rx, ry, rz = round(xf), round(yf), round(zf)
    dx, dy, dz = abs(rx - xf), abs(ry - yf), abs(rz - zf)
    if dx > dy and dx > dz: rx = -ry - rz
    elif dy > dz:           ry = -rx - rz
    else:                   rz = -rx - ry
    return rx, rz
def px_to_hex(px, py):
    qf = (S3 / 3.0 * px - 1.0 / 3.0 * py); rf = (2.0 / 3.0 * py)
    q, r = _axial_round(qf, rf)
    return axial_to_offset(q, r)

# ════════════════════════════ INVARIANTS ════════════════════════════
def check_invariants():
    cells = [(c, r) for r in range(-6, 7) for c in range(-6, 7)]
    ok = True
    # 1. adjacency: neighbour centres are exactly √3 from the centre
    bad = 0
    for (c, r) in cells:
        cx, cy = hex_to_px(c, r)
        for d in range(6):
            nc, nr = hex_neighbor(c, r, d); nx, ny = hex_to_px(nc, nr)
            if abs(math.hypot(nx - cx, ny - cy) - S3) > 1e-9: bad += 1
    print(f"  1. adjacency (all neighbours dist √3): {'PASS' if bad==0 else f'FAIL ({bad})'}"); ok &= bad == 0
    # 2. symmetry
    nbad = 0
    for (c, r) in cells:
        for d in range(6):
            nc, nr = hex_neighbor(c, r, d)
            if (c, r) not in [hex_neighbor(nc, nr, e) for e in range(6)]: nbad += 1
    print(f"  2. neighbour symmetry: {'PASS' if nbad==0 else f'FAIL ({nbad})'}"); ok &= nbad == 0
    # 3. hex_distance == BFS graph distance
    def bfs(src):
        seen = {src: 0}; frontier = [src]
        while frontier:
            nf = []
            for (c, r) in frontier:
                for d in range(6):
                    n = hex_neighbor(c, r, d)
                    if n not in seen and -6 <= n[0] <= 6 and -6 <= n[1] <= 6:
                        seen[n] = seen[(c, r)] + 1; nf.append(n)
            frontier = nf
        return seen
    dbad = 0
    for src in [(0, 0), (1, 0), (0, 1), (-2, 3)]:
        dist = bfs(src)
        for tgt, gd in dist.items():
            if hex_distance(src[0], src[1], tgt[0], tgt[1]) != gd: dbad += 1
    print(f"  3. hex_distance == graph distance: {'PASS' if dbad==0 else f'FAIL ({dbad})'}"); ok &= dbad == 0
    # 4. round-trip px_to_hex(hex_to_px(h)) == h
    rbad = 0
    for (c, r) in cells:
        px, py = hex_to_px(c, r)
        if px_to_hex(px, py) != (c, r): rbad += 1
    print(f"  4. hex->px->hex round-trip: {'PASS' if rbad==0 else f'FAIL ({rbad})'}"); ok &= rbad == 0
    return ok

# ════════════════════════ DUNGEON + STRAIGHTENER ════════════════════
EDGE_CORNERS = {0:(4,5), 1:(3,4), 2:(2,3), 3:(1,2), 4:(0,1), 5:(5,0)}
def gen(w, h, rooms):
    tiles = [1]*(w*h); rects = []; centres = []
    for (c0, r0, rw, rh) in rooms:
        for r in range(r0, r0+rh):
            for c in range(c0, c0+rw):
                if 0 <= c < w and 0 <= r < h: tiles[r*w+c] = 0
        rects.append((c0, r0, rw, rh)); centres.append((c0+rw//2, r0+rh//2))
    for i in range(len(centres)-1):
        (ac, ar), (bc, br) = centres[i], centres[i+1]; cc, cr = ac, ar; guard = 0
        while (cc, cr) != (bc, br) and guard < 2000:
            guard += 1; tiles[cr*w+cc] = 0
            best = hex_distance(cc, cr, bc, br); nc, nr = cc, cr
            for d in range(6):
                tc, tr = hex_neighbor(cc, cr, d)
                if 1 <= tc < w-1 and 1 <= tr < h-1 and hex_distance(tc, tr, bc, br) < best:
                    best = hex_distance(tc, tr, bc, br); nc, nr = tc, tr
            if (nc, nr) == (cc, cr): break
            cc, cr = nc, nr
        tiles[br*w+bc] = 0
    return tiles, rects

def is_wall(t, w, h, c, r): return c < 0 or r < 0 or c >= w or r >= h or t[r*w+c] == 1
def boundary_edges(t, w, h):
    e = []
    for r in range(h):
        for c in range(w):
            if t[r*w+c] != 0: continue
            for d in range(6):
                nc, nr = hex_neighbor(c, r, d)
                if is_wall(t, w, h, nc, nr):
                    a, b = EDGE_CORNERS[d]; e.append((hex_corner_px(c, r, a), hex_corner_px(c, r, b)))
    return e

def room_sides(rect):                       # 4 upright-rect side-lines (same room_tip logic)
    c0, r0, rw, rh = rect
    ccx, ccy = hex_to_px(c0 + rw//2, r0 + rh//2)
    cells = [(c0, r0), (c0+rw-1, r0), (c0+rw-1, r0+rh-1), (c0, r0+rh-1)]
    tips = []
    for (c, r) in cells:
        best = None; bd = -1
        for i in range(6):
            p = hex_corner_px(c, r, i); dd = (p[0]-ccx)**2 + (p[1]-ccy)**2
            if dd > bd: bd = dd; best = p
        tips.append(best)
    return [(tips[i], tips[(i+1) % 4]) for i in range(4)]

def key(p): return (round(p[0]*1000), round(p[1]*1000))
def hybrid(edges, rects, tol=0.62, iters=3, lam=0.5):
    idx = {}; pts = []; nb = []
    def goa(p):
        k = key(p)
        if k in idx: return idx[k]
        i = len(pts); idx[k] = i; pts.append(list(p)); nb.append([]); return i
    E = [(goa(a), goa(b)) for a, b in edges]
    for a, b in E: nb[a].append(b); nb[b].append(a)
    sides = [s for rect in rects for s in room_sides(rect)]; anc = [False]*len(pts)
    for i in range(len(pts)):
        best = None; bd = tol*tol
        for (a, b) in sides:
            dx, dy = b[0]-a[0], b[1]-a[1]; l2 = dx*dx+dy*dy
            if l2 == 0: continue
            t = ((pts[i][0]-a[0])*dx + (pts[i][1]-a[1])*dy)/l2
            if -0.12 <= t <= 1.12:
                fx, fy = a[0]+t*dx, a[1]+t*dy; d2 = (pts[i][0]-fx)**2 + (pts[i][1]-fy)**2
                if d2 < bd: bd = d2; best = (fx, fy)
        if best: pts[i] = list(best); anc[i] = True
    for _ in range(iters):
        for i in range(len(pts)):
            if not anc[i] and len(nb[i]) == 2:
                p1, p2 = pts[nb[i][0]], pts[nb[i][1]]
                pts[i][0] += lam*((p1[0]+p2[0])/2 - pts[i][0]); pts[i][1] += lam*((p1[1]+p2[1])/2 - pts[i][1])
    return [(tuple(pts[a]), tuple(pts[b])) for a, b in E], sides

def render(tiles, w, h, panels, fname, title=""):
    sc = 22; pad = 20
    xs = []; ys = []
    for r in range(h):
        for c in range(w):
            x, y = hex_to_px(c, r); xs.append(x); ys.append(y)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    PW = int((maxx-minx)*sc)+2*pad; PH = int((maxy-miny)*sc)+2*pad
    n = len(panels); img = Image.new("RGB", (PW*n+30*(n-1), PH+30), (244,244,244)); dr = ImageDraw.Draw(img)
    def px(p, k): return (k*(PW+30)+pad+(p[0]-minx)*sc, PH-(pad+(p[1]-miny)*sc)+20)
    for k, (lab, edges) in enumerate(panels):
        for r in range(h):
            for c in range(w):
                if tiles[r*w+c] == 0: dr.polygon([px(hex_corner_px(c, r, i), k) for i in range(6)], fill=(204,190,150))
        for a, b in edges: dr.line([px(a, k), px(b, k)], fill=(36,32,30), width=3)
        dr.text((k*(PW+30)+pad, 4), lab, fill=(20,20,20))
    if title: dr.text((14, PH+12), title, fill=(90,40,40))
    img.save(fname)

if __name__ == "__main__":
    print("odd-r offset model — invariant checks:")
    ok = check_invariants()
    print("  ->", "ALL PASS" if ok else "FAIL")
    out = os.path.join(os.path.dirname(__file__), "out"); os.makedirs(out, exist_ok=True)
    W, H = 30, 22
    for name, rooms in {"2room": [(4,4,6,5),(18,12,7,6)], "3room": [(3,3,5,5),(16,4,7,5),(10,13,8,6)]}.items():
        tiles, rects = gen(W, H, rooms)
        raw = boundary_edges(tiles, W, H)
        hy, _ = hybrid(raw, rects)
        render(tiles, W, H, [("RAW boundary (rooms now UPRIGHT)", raw), ("STRAIGHTENED (snap to upright edges)", hy)],
               f"{out}/offset_{name}.png", title=f"{name}: odd-r OFFSET — rooms upright + straightener gives straight walls")
    print("rendered ->", out)
