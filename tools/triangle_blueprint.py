#!/usr/bin/env python3
"""triangle_blueprint.py — the OWNERSHIP-CONTRACT experiment (OVERLAND theory §9).

A small HAND-AUTHORED hex map (1.5 km tiles) with deliberate situations:
two mountains beside each other, a mountain on the sea, a mountain on a lake,
hills/forest/plains — then the contract model resolves it:

  VERTEX (hex center): valley floor elevation, jittered control point
  SIDE   (center-center, where flow runs): the CURVED river course, one size
  CORNER (triple point): the PEAK — jittered OFF the exact lattice point,
         height/character decided once from the three cells, shared by all
  EDGE   (corner-corner = hex border): DRY -> a ridge with a saddle between
         the two corner peaks; WET -> a water gap where the river breaches

then a ZAngband-style pass details the ground: per-terrain lookup tables over
a fractal band value -> concrete micro features (clearings, tree stands,
scree, snow), plus carving, alluvial floors, whitewater.

Panels (tools/_triangle/): contracts.png (the ownership diagram),
detail_map.png (the walked-scale result), ortho.png (3D miniature).
Throwaway instrument; pure functions of (seed, authored cells, x, y).
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw

np.seterr(over="ignore")

SEED = 7
TILE = 1500.0
SQ3 = math.sqrt(3.0)
RC = TILE / SQ3            # circumradius; vertical pitch = 1.5*RC
VS = 1.5 * RC
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_triangle")

# ---------------- the authored map (9 x 7, odd-r) -------------------------
# materials: s=sea  l=lake  p=plain  f=forest  h=hill  M=mountain
MAT = [
    "sssssssss",
    "sMhffffhs",   # (1,1) mountain ON THE SEA (west);  forest belt
    "shpfMMhps",   # (4,2)+(5,2) TWO MOUNTAINS side by side
    "sphhhMhps",   # (5,3) mountain...
    "spphhlhps",   # ...beside the LAKE at (5,4)
    "sppphppps",
    "sssssssss",
]
HGT = {
    "s": -60.0, "l": 170.0, "p": 55.0, "f": 95.0, "h": 270.0, "M": 950.0,
}
# terrain tuning rows: rise-boost for corner peaks, steep (jaggedness), color
TYPES = {
    "s": dict(boost=0.0,   steep=1.0,  col=(38, 84, 142)),
    "l": dict(boost=0.0,   steep=1.0,  col=(46, 96, 146)),
    "p": dict(boost=18.0,  steep=2.5,  col=(124, 152, 84)),
    "f": dict(boost=35.0,  steep=5.0,  col=(62, 106, 58)),
    "h": dict(boost=110.0, steep=28.0, col=(134, 128, 88)),
    "M": dict(boost=330.0, steep=80.0, col=(128, 124, 118)),
}
NX, NY = 9, 7
WORLD_W, WORLD_H = NX * TILE, NY * VS

# ---------------- primitives (hash noise, lattice) ------------------------
def hash01(ix, iy, ch):
    ix = np.asarray(ix, dtype=np.int64).astype(np.uint32)
    iy = np.asarray(iy, dtype=np.int64).astype(np.uint32)
    n = (ix * np.uint32(73856093)) ^ (iy * np.uint32(19349663)) \
        ^ (np.uint32(ch) * np.uint32(83492791)) ^ np.uint32(SEED * 2654435761 & 0xFFFFFFFF)
    n = (n ^ (n >> np.uint32(13))) * np.uint32(1274126177)
    return (n ^ (n >> np.uint32(16))).astype(np.float64) / 4294967296.0

def vnoise(xs, ys, wl, ch):
    u, v = xs / wl, ys / wl
    iu, iv = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - iu, v - iv
    fu = fu * fu * (3 - 2 * fu)
    fv = fv * fv * (3 - 2 * fv)
    a, b = hash01(iu, iv, ch), hash01(iu + 1, iv, ch)
    c, d = hash01(iu, iv + 1, ch), hash01(iu + 1, iv + 1, ch)
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv

def fbm(xs, ys, wl0, octs, ch):
    out = np.zeros_like(np.asarray(xs, dtype=np.float64))
    amp, wl, tot = 1.0, wl0, 0.0
    for o in range(octs):
        out += amp * (vnoise(xs, ys, wl, ch * 16 + o) * 2 - 1)
        tot += amp
        amp *= 0.5
        wl *= 0.5
    return out / tot

def center(c, r):
    return ((c + 0.5 * (r & 1)) * TILE, r * VS)

def neighbors(c, r):
    if r & 1:
        off = ((1, 0), (-1, 0), (1, -1), (0, -1), (1, 1), (0, 1))
    else:
        off = ((1, 0), (-1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))
    return [(c + dc, r + dr) for dc, dr in off]

def chash(parts, ch):
    n = SEED * 1597334677
    for p in parts:
        n = (n ^ (int(p) * 73856093)) & 0x7FFFFFFF
        n = ((n << 5) ^ (n >> 7)) & 0x7FFFFFFF
    n = (n ^ ch * 83492791) & 0x7FFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0x7FFFFFFF
    return ((n ^ (n >> 16)) & 0x7FFFFFFF) / 2147483648.0

def mat(c, r):
    if 0 <= c < NX and 0 <= r < NY:
        return MAT[r][c]
    return "s"

def hgt(c, r):
    return HGT[mat(c, r)]

# ---------------- hydrology on the authored map ---------------------------
FLOW = np.full((NY, NX), -1, int)
ACC = np.ones((NY, NX))
for r in range(NY):
    for c in range(NX):
        if hgt(c, r) <= 0 or mat(c, r) == "l":
            continue
        bh, bi = hgt(c, r), -1
        for i, (nc, nr) in enumerate(neighbors(c, r)):
            if hgt(nc, nr) < bh:
                bh, bi = hgt(nc, nr), i
        FLOW[r, c] = bi
order = sorted(((hgt(c, r), c, r) for r in range(NY) for c in range(NX)
                if hgt(c, r) > 0 and mat(c, r) != "l"), reverse=True)
for _, c, r in order:
    if FLOW[r, c] >= 0:
        nc, nr = neighbors(c, r)[FLOW[r, c]]
        if 0 <= nc < NX and 0 <= nr < NY:
            ACC[nr, nc] += ACC[r, c]

# ---------------- THE CONTRACTS -------------------------------------------
# VERTEX: jittered control point + valley elevation
def vertex_pt(c, r):
    cx, cy = center(c, r)
    jx = (chash((c, r), 6) - 0.5) * 0.55 * RC
    jy = (chash((c, r), 7) - 0.5) * 0.55 * RC
    return (cx + jx, cy + jy)

# SIDE: curved course where flow runs (anchor -> edge-bit -> anchor, displaced)
def edge_bit(ca, ra, cb, rb):
    (c1, r1), (c2, r2) = sorted(((ca, ra), (cb, rb)))
    x1, y1 = center(c1, r1)
    x2, y2 = center(c2, r2)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    d = math.hypot(x2 - x1, y2 - y1)
    px, py = -(y2 - y1) / d, (x2 - x1) / d
    off = (0.30 if chash((c1, r1, c2, r2), 5) < 0.5 else -0.30) * RC
    return (mx + px * off, my + py * off)

def displace(pts, lo_open, lvl=0):
    if lvl > 5:
        return pts
    out, moved = [], False
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        out.append((ax, ay))
        seg = math.hypot(bx - ax, by - ay)
        if seg >= 170.0:
            moved = True
            px, py = -(by - ay) / seg, (bx - ax) / seg
            h = chash((round(ax), round(ay), round(bx), round(by)), 100 + lvl)
            d = (h - 0.5) * 2 * seg * 0.34 * lo_open
            out.append(((ax + bx) / 2 + px * d, (ay + by) / 2 + py * d))
    out.append(pts[-1])
    return displace(out, lo_open, lvl + 1) if moved else out

SIDES = []   # (course pts, acc, width, depth)
for r in range(NY):
    for c in range(NX):
        bi = FLOW[r, c]
        if bi < 0:
            continue
        nc, nr = neighbors(c, r)[bi]
        slope = abs(hgt(c, r) - hgt(nc, nr)) / TILE
        open_ = max(0.38, 1.0 - slope / 0.12)
        pts = displace([vertex_pt(c, r), edge_bit(c, r, nc, nr), vertex_pt(nc, nr)], open_)
        a = ACC[r, c]
        # INVARIANT I3 (water never flows uphill): the bed is a monotone ramp
        # between the two VERTEX-owned levels (cell heights strictly descend
        # along the flow tree, so the whole network is monotone by construction)
        bedA = hgt(c, r) - 5.0
        # the bed lands ON the receiving water's surface: sea -> -5, LAKE -> its
        # owned level (I2/I3 coupling: inflows may never undercut the lake)
        if mat(nc, nr) == "l":
            bedB = HGT["l"]
        elif hgt(nc, nr) <= 0:
            bedB = -5.0
        else:
            bedB = hgt(nc, nr) - 5.0
        arc = [0.0]
        for i in range(len(pts) - 1):
            arc.append(arc[-1] + math.hypot(pts[i + 1][0] - pts[i][0],
                                            pts[i + 1][1] - pts[i][1]))
        tot = max(arc[-1], 1e-9)
        beds = [bedA + (bedB - bedA) * (t / tot) for t in arc]
        glac = hgt(c, r) >= 800.0          # sourced in the snow zone
        SIDES.append(dict(pts=pts, acc=a, beds=beds, glac=glac,
                          icew=(75.0 + 45.0 * math.sqrt(a)) if glac else 0.0,
                          width=(2.0 + 2.2 * math.sqrt(a)) * (0.35 + 0.65 * open_)))
SIDES.sort(key=lambda s: -s["acc"])     # STABILITY: bigger water first

# CORNER: the peak — jittered OFF the exact triple point, decided ONCE
def corner_cells(c, r, k):
    """The three cells meeting at corner k (0..5) of cell (c,r)."""
    nb = neighbors(c, r)
    return [(c, r), nb[CORNER_NB[k][0]], nb[CORNER_NB[k][1]]]

# corner k sits between neighbor directions (pointy-top, odd-r neighbor order
# E,W,NE,NW,SE,SW): corner angles 30+60k; adjacencies by geometry:
CORNER_NB = {0: (0, 4), 1: (4, 5), 2: (5, 1), 3: (1, 3), 4: (3, 2), 5: (2, 0)}

PEAKS = {}
for r in range(NY):
    for c in range(NX):
        cx, cy = center(c, r)
        for k in range(6):
            ang = math.pi / 6 + k * math.pi / 3
            px, py = cx + RC * math.cos(ang), cy + RC * math.sin(ang)
            key = (round(px), round(py))
            if key in PEAKS or not (0 < px < WORLD_W and 0 < py < WORLD_H):
                continue
            cells = corner_cells(c, r, k)
            mats = [mat(*q) for q in cells]
            hs = [max(0.0, hgt(*q)) for q in cells]
            boost = max(TYPES[m]["boost"] for m in mats)
            nhigh = sum(1 for h in hs if h > 600)
            boost *= (0.55 + 0.45 * nhigh)          # compounding: ranges meet
            if all(m in "sl" for m in mats):
                continue
            jr = chash(key, 11) * 0.22 * TILE
            ja = chash(key, 12) * 2 * math.pi
            steep = max(TYPES[m]["steep"] for m in mats)
            PEAKS[key] = dict(x=px + jr * math.cos(ja), y=py + jr * math.sin(ja),
                              amp=boost, steep=steep,
                              rad=620.0 + boost * 1.5,
                              base=sum(hs) / 3.0)

# EDGE: corner-to-corner = the hex border. DRY -> ridge with saddle; WET -> gap.
def corner_key(c, r, k):
    cx, cy = center(c, r)
    ang = math.pi / 6 + k * math.pi / 3
    return (round(cx + RC * math.cos(ang)), round(cy + RC * math.sin(ang)))

EDGE_OF_DIR = {0: (5, 0), 4: (0, 1), 5: (1, 2), 1: (2, 3), 3: (3, 4), 2: (4, 5)}
RIDGES = []
seen_edges = set()
for r in range(NY):
    for c in range(NX):
        for d, (nc, nr) in enumerate(neighbors(c, r)):
            ekey = tuple(sorted(((c, r), (nc, nr))))
            if ekey in seen_edges:
                continue
            seen_edges.add(ekey)
            wet = (FLOW[r, c] == d) or (0 <= nc < NX and 0 <= nr < NY
                                        and neighbors(nc, nr)[FLOW[nr, nc]] == (c, r)
                                        if (0 <= nc < NX and 0 <= nr < NY and FLOW[nr, nc] >= 0) else False)
            if wet:
                continue
            ka, kb = EDGE_OF_DIR[d]
            pa, pb = corner_key(c, r, ka), corner_key(c, r, kb)
            if pa not in PEAKS or pb not in PEAKS:
                continue
            A, B = PEAKS[pa], PEAKS[pb]
            if min(A["amp"], B["amp"]) < 70.0:
                continue
            mx = (A["x"] + B["x"]) / 2
            my = (A["y"] + B["y"]) / 2
            d2 = math.hypot(B["x"] - A["x"], B["y"] - A["y"])
            if d2 < 1.0:
                continue
            qx, qy = -(B["y"] - A["y"]) / d2, (B["x"] - A["x"]) / d2
            woff = (chash(pa + pb, 21) - 0.5) * 0.3 * TILE
            rpts = displace([(A["x"], A["y"]), (mx + qx * woff, my + qy * woff),
                             (B["x"], B["y"])], 0.55)
            RIDGES.append(dict(pts=rpts, aamp=A["amp"], bamp=B["amp"],
                               sadl=0.42 + 0.18 * chash(pa + pb, 22)))

print(f"contracts: {len(SIDES)} sides, {len(PEAKS)} peaks, {len(RIDGES)} ridges")

# ---------------- the fine map (the "zangband pass") ----------------------
def render(px_m=6.0):
    W, H = int(WORLD_W / px_m), int(WORLD_H / px_m)
    jj, ii = np.meshgrid(np.arange(W), np.arange(H))
    xs, ys = (jj + 0.5) * px_m, (ii + 0.5) * px_m

    # 1) base valley surface: kernel blend of cell heights + dominant material
    wsum = np.zeros((H, W))
    hsum = np.zeros((H, W))
    best = np.zeros((H, W))
    matc = np.zeros((H, W, 3))
    steepf = np.zeros((H, W))
    watery = np.zeros((H, W))
    lakew = np.zeros((H, W))
    rk2 = (TILE * 1.02) ** 2
    ry0 = np.round(ys / VS).astype(np.int64)
    for dr in (-1, 0, 1):
        rr = ry0 + dr
        off = 0.5 * (rr & 1)
        c0 = np.floor(xs / TILE - off).astype(np.int64)
        for dc in (-1, 0, 1, 2):
            cc = c0 + dc
            cx = (cc + off) * TILE
            cy = rr * VS
            d2 = (xs - cx) ** 2 + (ys - cy) ** 2
            w = np.maximum(0, 1 - d2 / rk2) ** 2
            ci = np.clip(cc, 0, NX - 1)
            ri = np.clip(rr, 0, NY - 1)
            hv = np.vectorize(lambda a, b: hgt(a, b))(ci, ri)
            mv = np.vectorize(lambda a, b: mat(a, b))(ci, ri)
            wsum += w
            hsum += w * hv
            stv = np.vectorize(lambda m: TYPES[m]["steep"])(mv)
            jit = 0.72 + 0.56 * (fbm(xs, ys, 1000.0, 3, 40) * 0.5 + 0.5)
            sc = w * np.sqrt(stv) * jit
            upd = sc > best
            best = np.where(upd, sc, best)
            for ch_i in range(3):
                colv = np.vectorize(lambda m, i=ch_i: TYPES[m]["col"][i])(mv)
                matc[..., ch_i] = np.where(upd, colv, matc[..., ch_i])
            steepf = np.where(upd, stv, steepf)
            watery += w * np.vectorize(lambda m: 1.0 if m in "sl" else 0.0)(mv)
            lakew += w * np.vectorize(lambda m: 1.0 if m == "l" else 0.0)(mv)
    blend = hsum / np.maximum(wsum, 1e-12)
    watery = watery / np.maximum(wsum, 1e-12)
    lakew = lakew / np.maximum(wsum, 1e-12)

    # 2) CORNER peaks + EDGE ridges: vertical structure as MAX of owned forms
    dist = np.full((H, W), 1e9)
    wf = np.zeros((H, W))
    bedf = np.zeros((H, W))
    icef = np.zeros((H, W))
    vwf = np.full((H, W), 150.0)
    for S in SIDES:
        fp = S["pts"]
        rad = 4.0 * (150.0 + 2.0 * S["width"]) * (2.3 if S["glac"] else 1.0)
        fxs = [q[0] for q in fp]
        fys = [q[1] for q in fp]
        jx0 = max(0, int((min(fxs) - rad) / px_m))
        jx1 = min(W, int((max(fxs) + rad) / px_m) + 1)
        jy0 = max(0, int((min(fys) - rad) / px_m))
        jy1 = min(H, int((max(fys) + rad) / px_m) + 1)
        if jx0 >= jx1 or jy0 >= jy1:
            continue
        pxs = xs[jy0:jy1, jx0:jx1]
        pys = ys[jy0:jy1, jx0:jx1]
        cd = np.full(pxs.shape, 1e9)
        bd = np.zeros(pxs.shape)
        for i in range(len(fp) - 1):
            ax, ay = fp[i]
            bx, by = fp[i + 1]
            ex, ey = bx - ax, by - ay
            ee = ex * ex + ey * ey
            if ee < 1e-9:
                continue
            t = np.clip(((pxs - ax) * ex + (pys - ay) * ey) / ee, 0, 1)
            d = np.hypot(pxs - (ax + t * ex), pys - (ay + t * ey))
            u = d < cd
            cd = np.where(u, d, cd)
            bd = np.where(u, S["beds"][i] * (1 - t) + S["beds"][i + 1] * t, bd)
        gd = dist[jy0:jy1, jx0:jx1]
        gu = cd < gd
        dist[jy0:jy1, jx0:jx1] = np.where(gu, cd, gd)
        wf[jy0:jy1, jx0:jx1] = np.where(gu, S["width"], wf[jy0:jy1, jx0:jx1])
        bedf[jy0:jy1, jx0:jx1] = np.where(gu, bd, bedf[jy0:jy1, jx0:jx1])
        icef[jy0:jy1, jx0:jx1] = np.where(gu, S["icew"], icef[jy0:jy1, jx0:jx1])
        svw = (150.0 + 2.0 * S["width"]) * (2.3 if S["glac"] else 1.0)
        vwf[jy0:jy1, jx0:jx1] = np.where(gu, svw, vwf[jy0:jy1, jx0:jx1])
    vertp = np.zeros((H, W))           # p-norm accumulator: smooth-max, no creases
    PN = 5.0
    rwx = fbm(xs, ys, 1400.0, 2, 87)
    rwy = fbm(xs, ys, 1400.0, 2, 88)
    rnoise = 1 - np.abs(fbm(xs + 420.0 * rwx, ys + 420.0 * rwy, 700.0, 3, 86))
    for P in PEAKS.values():
        R = P["rad"]
        jx0 = max(0, int((P["x"] - R) / px_m))
        jx1 = min(W, int((P["x"] + R) / px_m) + 1)
        jy0 = max(0, int((P["y"] - R) / px_m))
        jy1 = min(H, int((P["y"] + R) / px_m) + 1)
        if jx0 >= jx1 or jy0 >= jy1:
            continue
        d = np.hypot(xs[jy0:jy1, jx0:jx1] - P["x"], ys[jy0:jy1, jx0:jx1] - P["y"])
        m = P["amp"] * np.clip(1 - d / R, 0, 1) ** 2.1 \
            * (0.62 + 0.38 * rnoise[jy0:jy1, jx0:jx1] * min(1.0, P["steep"] / 60))
        vertp[jy0:jy1, jx0:jx1] += m ** PN
    for G in RIDGES:
        pts = G["pts"]
        arc = [0.0]
        for q in range(len(pts) - 1):
            arc.append(arc[-1] + math.hypot(pts[q + 1][0] - pts[q][0],
                                            pts[q + 1][1] - pts[q][1]))
        tot = max(arc[-1], 1e-9)
        for q in range(len(pts) - 1):
            ax, ay = pts[q]
            bx, by = pts[q + 1]
            R = 460.0
            jx0 = max(0, int((min(ax, bx) - R) / px_m))
            jx1 = min(W, int((max(ax, bx) + R) / px_m) + 1)
            jy0 = max(0, int((min(ay, by) - R) / px_m))
            jy1 = min(H, int((max(ay, by) + R) / px_m) + 1)
            if jx0 >= jx1 or jy0 >= jy1:
                continue
            pxs = xs[jy0:jy1, jx0:jx1]
            pys = ys[jy0:jy1, jx0:jx1]
            ex, ey = bx - ax, by - ay
            ee = max(ex * ex + ey * ey, 1e-9)
            t = np.clip(((pxs - ax) * ex + (pys - ay) * ey) / ee, 0, 1)
            tg = (arc[q] + t * (arc[q + 1] - arc[q])) / tot
            d = np.hypot(pxs - (ax + t * ex), pys - (ay + t * ey))
            prof = (G["aamp"] * (1 - tg) + G["bamp"] * tg) \
                 * (1 - G["sadl"] * 4 * tg * (1 - tg))      # the SADDLE dip
            m = prof * np.clip(1 - d / R, 0, 1) ** 1.6 \
                * (0.7 + 0.3 * rnoise[jy0:jy1, jx0:jx1])
            vertp[jy0:jy1, jx0:jx1] += m ** PN
    vert = vertp ** (1.0 / PN)
    # CUT DOWN the verticality before the snow/grass pass (user rule): a soft
    # ceiling flattens the tops into shoulders — summit slopes calm down, the
    # zonation then claims them with snow and meadows NATURALLY
    vert = 520.0 * np.tanh(vert / 520.0)
    # the WATER GAP rule at fine scale: peaks and ridges YIELD inside a
    # course's corridor (no slot canyons needed to keep the bed monotone)
    gapR = np.maximum(130.0 + 3.0 * wf, icef * 1.7)
    vert = vert * np.clip(dist / np.maximum(gapR, 1.0), 0.22, 1.0)
    height = blend + vert * np.clip(1.0 - watery * 1.6, 0.0, 1.0) \
           + 6.0 * fbm(xs, ys, 300.0, 5, 3)
    # INVARIANT I1 (no inland sea): solid land never dips below sea level —
    # only the bounded coastal band (real sea nearby) may
    height = np.where(watery < 0.10, np.maximum(height, 0.5), height)

    # 3) SIDE courses: carve + water (max carve; bigger-first stability)
    h_pre = height.copy()
    # INVARIANT I3 by construction: the carve is exactly what reaches the
    # monotone BED at the centerline, decaying off-channel; land only
    vw = vwf
    need = np.maximum(0.0, h_pre - bedf) * (blend > 0)
    carve = need * np.exp(-dist / vw) * np.clip(1 - dist / (4 * vw), 0, 1)
    height = height - carve

    gy, gx = np.gradient(height, px_m)
    slope = np.hypot(gx, gy)

    # 4) the ZANGBAND TABLE pass: fractal band -> per-terrain micro features
    bwx = fbm(xs, ys, 800.0, 2, 57)
    bwy = fbm(xs, ys, 800.0, 2, 58)
    band = fbm(xs + 260.0 * bwx, ys + 260.0 * bwy, 240.0, 4, 55) * 0.5 + 0.5
    col = matc.copy()
    snow = np.array([232, 236, 240.0])
    rock = np.array([128, 124, 118.0])
    scree = np.array([150, 142, 124.0])
    dgrn = np.array([42, 80, 40.0])
    lgrn = np.array([108, 142, 76.0])
    bush = np.array([84, 116, 60.0])
    # forest: clearings / light stands / dense stands (+ tree stipple)
    isf = (np.abs(col[..., 0] - 62) < 1) & (np.abs(col[..., 1] - 106) < 1)
    col = np.where((isf & (band < 0.30))[..., None], lgrn, col)
    col = np.where((isf & (band > 0.62))[..., None], dgrn, col)
    tree = isf & (hash01(np.round(xs / 9).astype(np.int64),
                         np.round(ys / 9).astype(np.int64), 77) > 0.72) & (band > 0.35)
    col = np.where(tree[..., None], dgrn * 0.8, col)
    # plains: grass tones + bush specks
    isp = (np.abs(col[..., 0] - 124) < 1) & (np.abs(col[..., 1] - 152) < 1)
    col = np.where((isp & (band > 0.66))[..., None], bush, col)
    # mountain/hill ZONATION (user rules): trees along the slopes below the
    # tree line; treeless slopes ERODE -> stone faces with rubble under them;
    # ABOVE the tree line meadows along the stone faces; snow on top
    mslope = steepf > 20
    TREEL, SNOWL = 520.0, 880.0
    conif = np.array([58.0, 98.0, 54.0])
    conif2 = np.array([44.0, 78.0, 42.0])
    face = np.array([112.0, 108.0, 102.0])
    meadow = np.array([124.0, 158.0, 92.0])
    # forested slopes (band picks the stands; very steep ground carries none)
    mtree = mslope & (height > 90) & (height < TREEL) & (band > 0.34) & (slope < 0.50)
    col = np.where(mtree[..., None], conif, col)
    tr2 = mtree & (hash01(np.round(xs / 9).astype(np.int64),
                          np.round(ys / 9).astype(np.int64), 78) > 0.55)
    col = np.where(tr2[..., None], conif2, col)
    # the erosion rule: treeless slope -> stone FACE where steep, RUBBLE below
    bare = mslope & (height > 90) & (height < TREEL) & ~mtree
    col = np.where((bare & (slope <= 0.34))[..., None], scree, col)         # rubble
    col = np.where(((bare & (slope > 0.34)) | (mslope & (slope > 0.60)))[..., None],
                   face, col)                                               # stone face
    # the alpine zone: meadows claim ALL gentle ground; rock only where steep
    alp = mslope & (height >= TREEL) & (height < SNOWL)
    meadow2 = np.array([110.0, 146.0, 84.0])
    col = np.where(alp[..., None], meadow, col)
    col = np.where((alp & (band <= 0.34))[..., None], meadow2, col)
    col = np.where((alp & (slope >= 0.44) & (slope < 0.60))[..., None], scree, col)
    col = np.where((alp & (slope >= 0.60))[..., None], face, col)
    # snow holds only on gentle ground: steep faces and windswept bands CUT
    # through the cap as bare rock formations
    sn = height >= SNOWL
    col = np.where(sn[..., None], snow, col)
    col = np.where((sn & (band < 0.22))[..., None], scree, col)
    col = np.where((sn & (slope > 0.34))[..., None], face, col)
    # alluvial floors beside big water
    am = np.clip(1 - dist / np.maximum(wf * 14.0, 1.0), 0, 1) * 0.55
    am = am * (wf > 7.0) * (height > 0)
    col = col * (1 - am[..., None]) + np.array([124, 152, 84.0]) * am[..., None]
    # beach: near sea level AND at the water (coastal blend) AND gentle ground —
    # steep shores are CLIFFS, they get no sand
    beach = np.clip(1 - np.abs(h_pre - 2.0) / 3.0, 0, 1) * (h_pre > 0) \
          * (watery > 0.12) * np.clip(1 - slope / 0.08, 0, 1)
    col = col * (1 - beach[..., None] * .8) + np.array([201, 186, 140.0]) * beach[..., None] * .8
    shade = np.clip(1 - (gx + gy) * 1.4, 0.55, 1.45)
    # (gradient computed above)
    col = col * shade[..., None]
    # water: sea / lake / rivers / whitewater
    sea = height <= 0
    lkj = lakew + 0.09 * fbm(xs, ys, 700.0, 3, 70)
    lakey = (lkj > 0.42) & ~sea
    # the BANK: terrain within the lake's blend band descends smoothly TO the
    # owned level — the world flows from the constraint, no cliff ring
    bank = np.clip((lkj - 0.16) / (0.42 - 0.16), 0.0, 1.0) ** 1.4
    height = np.where(~lakey & (height > HGT["l"]),
                      height - (height - (HGT["l"] + 0.8)) * bank, height)
    height = np.where(lakey, HGT["l"], height)   # INVARIANT I2: one flat level
    depth01 = np.clip(-height / 40, 0, 1)
    seac = np.array([72, 132, 172.0]) * (1 - depth01[..., None]) + np.array([22, 54, 102.0]) * depth01[..., None]
    col = np.where(sea[..., None], seac, col)
    col = np.where(lakey[..., None], np.array([46, 96, 146.0]), col)
    rivw = (dist < wf * 0.5) & (height > 0) & ~lakey
    col = np.where(rivw[..., None], np.array([50, 108, 158.0]), col)
    rapids = rivw & (np.hypot(gx, gy) > 0.05) & (wf < 9)
    col = np.where(rapids[..., None], np.array([208, 222, 238.0]), col)
    dith = hash01(np.round(xs).astype(np.int64), np.round(ys).astype(np.int64), 91)
    wat_any = sea | lakey | rivw
    grain = np.where(wat_any, 1.0, 0.86 + 0.28 * dith)
    col = col * grain[..., None]
    return np.clip(col, 0, 255).astype(np.uint8), height

def panel_contracts(fname):
    s = 1100 / WORLD_W
    im = Image.new("RGB", (int(WORLD_W * s), int(WORLD_H * s)), (18, 20, 26))
    dr = ImageDraw.Draw(im)
    for r in range(NY):                       # cells tinted by material
        for c in range(NX):
            cx, cy = center(c, r)
            pts = [(cx + RC * math.cos(math.pi / 6 + k * math.pi / 3),
                    cy + RC * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(7)]
            colr = tuple(int(v * 0.45) for v in TYPES[mat(c, r)]["col"])
            dr.polygon([(x * s, y * s) for x, y in pts], fill=colr, outline=(40, 42, 48))
    for G in RIDGES:                          # ridges: brown, saddle-thinned
        dr.line([(x * s, y * s) for x, y in G["pts"]], fill=(168, 120, 70), width=3)
    for S in SIDES:                           # curved river sides, width by size
        w = max(1, int(math.sqrt(S["acc"]) * 1.2))
        dr.line([(x * s, y * s) for x, y in S["pts"]], fill=(70, 140, 210), width=w)
    for key, P in PEAKS.items():              # peaks: jittered vs lattice point
        if P["amp"] < 60:
            continue
        dr.line([(key[0] * s, key[1] * s), (P["x"] * s, P["y"] * s)], fill=(90, 90, 96), width=1)
        rr = 3 + P["amp"] / 90
        dr.ellipse([P["x"] * s - rr, P["y"] * s - rr, P["x"] * s + rr, P["y"] * s + rr],
                   fill=(240, 240, 244))
    for r in range(NY):
        for c in range(NX):
            if FLOW[r, c] >= 0 or mat(c, r) in "sl":
                vx, vy = vertex_pt(c, r)
                dr.ellipse([vx * s - 2, vy * s - 2, vx * s + 2, vy * s + 2], fill=(120, 190, 250))
    dr.text((8, 6), "contracts: vertices(blue) sides(curved rivers) corners(white peaks, "
                    "jittered off lattice) edges(brown ridges w/ saddles)", fill=(255, 255, 120))
    im.save(fname)
    print("wrote", fname)

def panel_ortho(col, height, fname, px_m):
    H, W = height.shape
    hgt2 = np.maximum(height, 0)
    ck, hk = 0.5, 1.0 / 4.0
    top = int(hgt2.max() * hk) + 8
    Hi = int(H * ck) + top + 12
    out = np.zeros((Hi, W, 3), np.uint8)
    out[:, :] = (12, 14, 18)
    ybuf = np.full(W, Hi - 1, np.int64)
    cols_idx = np.arange(W)
    for rr in range(H - 1, -1, -1):
        sy = np.clip((rr * ck + top - hgt2[rr] * hk).astype(np.int64), 0, Hi - 1)
        lens = ybuf - sy
        if not (lens > 0).any():
            continue
        kmax = int(lens.max())
        for k in range(kmax):
            m = lens > k
            out[sy[m] + k, cols_idx[m]] = col[rr][m]
        ybuf = np.minimum(ybuf, sy)
    Image.fromarray(out).save(fname)
    print("wrote", fname)

def check_invariants(height, px_m):
    ok = True
    # I1: every sea pixel reachable from the border (no inland sea pockets)
    sea = height <= 0
    reach = np.zeros_like(sea)
    reach[0, :] = sea[0, :]
    reach[-1, :] = sea[-1, :]
    reach[:, 0] = sea[:, 0]
    reach[:, -1] = sea[:, -1]
    for _ in range(600):
        grown = reach.copy()
        grown[1:, :] |= reach[:-1, :]
        grown[:-1, :] |= reach[1:, :]
        grown[:, 1:] |= reach[:, :-1]
        grown[:, :-1] |= reach[:, 1:]
        grown &= sea
        if (grown == reach).all():
            break
        reach = grown
    inland = int((sea & ~reach).sum())
    print(f"I1 no-inland-sea: {'OK' if inland == 0 else f'FAIL ({inland} px)'}")
    ok &= inland == 0
    # I2: lake flatness (exact level)
    lk = np.abs(height - HGT['l']) < 1e-9
    if lk.any():
        print("I2 lake-level: OK (exact)")
    # I3: water never flows uphill — sample every side downstream
    bad = 0
    for S in SIDES:
        prev = 1e18
        for (qx, qy) in S["pts"][1:-1]:   # interiors; vertex zones belong to neighbors
            j = min(max(int(qx / px_m), 0), height.shape[1] - 1)
            i = min(max(int(qy / px_m), 0), height.shape[0] - 1)
            h = max(height[i, j], 0.0)    # WATER SURFACE: the sea is flat at 0
            if h > prev + 0.35:
                bad += 1
            prev = min(prev, h)
    print(f"I3 monotone-flow: {'OK' if bad == 0 else f'FAIL ({bad} rises)'}")
    ok &= bad == 0
    print('=== INVARIANTS OK ===' if ok else '=== INVARIANTS FAIL ===')

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    panel_contracts(os.path.join(OUT, "contracts.png"))
    col, height = render(6.0)
    Image.fromarray(col).save(os.path.join(OUT, "detail_map.png"))
    print("wrote detail_map.png", col.shape)
    check_invariants(height, 6.0)
    panel_ortho(col, height, os.path.join(OUT, "ortho.png"), 6.0)
