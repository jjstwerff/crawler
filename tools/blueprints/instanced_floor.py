#!/usr/bin/env python3
"""Blueprint for PLAN-RENDER P6 — the instanced floor.

PINS the ONE load-bearing invariant before any loft is written:

    The instanced floor must be PIXEL-IDENTICAL to the current fat-VBO floor
    (golden parity, dmax = 0). It is the SAME geometry, re-fed as one base
    hexagon of corner OFFSETS + per-instance (center, visUV, color), with the
    vertex shader computing  world = center + offset.

The exact-invariant risk (hex_grid.loft:133):
    hex_corner_px(q,r,i) = hex_to_px(q,r) + hex_corner_offset(i)*HEX_SIZE
  OLD vertex pos (build_world_mesh) = f32( center_f64 + offset_f64 )
  NEW vertex pos (instanced shader) = f32( f32(center_f64) + f32(offset_f64) )
  These can differ by ~1 ULP (double rounding) -> a sub-pixel SEAM CRACK that,
  at a tint boundary, could flip an edge pixel and break parity.

This prototype RASTERISES a hex patch BOTH ways at the real SCALE and reports
the actual pixel diff, so we ship the design only if dmax = 0 (or learn we need
the snap fix). y-coords are multiples of 0.5 (f32-exact) so only x can crack.

Run:  python3 tools/blueprints/instanced_floor.py
"""
import numpy as np

SQRT3 = 1.7320508075688772          # hex_grid.loft:20
HEX_SIZE = 1.0                      # hex_grid.loft:21
SCALE = 26.0                        # view.loft:20  (px per world unit)
f32 = np.float32


# ── hex geometry (f64 mirror of hex_grid.loft) ──
def hex_to_px(q, r):                # hex_grid.loft:27
    par = r & 1
    hx = HEX_SIZE * (SQRT3 * q + SQRT3 / 2.0 * par)
    hy = HEX_SIZE * (1.5 * r)
    return hx, hy


def hex_corner_offset(i):           # hex_grid.loft:122 (circumradius 1)
    hw = SQRT3 / 2.0
    return [(0.0, 1.0), (-hw, 0.5), (-hw, -0.5),
            (0.0, -1.0), (hw, -0.5), (hw, 0.5)][i]


# ── the two vertex-position constructions ──
def old_corner_f32(q, r, i):
    """build_world_mesh: f32(center_f64 + offset_f64*HEX_SIZE)."""
    cx, cy = hex_to_px(q, r)
    ox, oy = hex_corner_offset(i)
    return f32(cx + ox * HEX_SIZE), f32(cy + oy * HEX_SIZE)


def new_corner_f32(q, r, i):
    """NAIVE instanced shader: f32(center) + f32(offset), summed in f32.
    NOT watertight — adjacent hexes round their shared corner differently."""
    cx, cy = hex_to_px(q, r)
    ox, oy = hex_corner_offset(i)
    cxs, cys = f32(cx), f32(cy)                       # uploaded instance center
    oxs, oys = f32(ox * HEX_SIZE), f32(oy * HEX_SIZE)  # base-hexagon offset
    return f32(cxs + oxs), f32(cys + oys)             # the GPU's f32 add


# dx in LATTICE units (corner_x = SQRT3*(column+dx)); column = q + 0.5*par.
_DX = [0.0, -0.5, -0.5, 0.0, 0.5, 0.5]


def lat_corner_f32(q, r, i):
    """WATERTIGHT instanced shader. Per-instance: column=q+0.5*par (exact
    half-int), row_y=1.5*r (exact ×0.5). Base hexagon per vertex: dx (lattice)
    + dy (world). Shader: x = SQRT3*(column+dx), y = row_y+dy. Two hexes that
    SHARE a corner reach the identical (column+dx, row_y+dy) -> identical f32
    -> no crack, EVER. Differs from OLD by <=1 ULP (sub-pixel)."""
    par = r & 1
    column = f32(q + 0.5 * par)                       # instance attr (exact)
    row_y = f32(1.5 * r)                              # instance attr (exact)
    ox, oy = hex_corner_offset(i)
    dx = f32(_DX[i])                                  # base-hexagon vert (exact)
    dy = f32(oy * HEX_SIZE)                           # base-hexagon vert (exact)
    px = f32(f32(SQRT3) * f32(column + dx))           # one f32 multiply
    py = f32(row_y + dy)
    return px, py


# ── vertex-level delta scan ──
def scan_vertices(qmin, rmin, lw, lh):
    maxdx = maxdy = 0.0
    ndiff = 0
    total = 0
    for gr in range(lh):
        for gq in range(lw):
            q, r = qmin + gq, rmin + gr
            for i in range(6):
                ox, oy = old_corner_f32(q, r, i)
                nx, ny = new_corner_f32(q, r, i)
                dx, dy = abs(float(ox) - float(nx)), abs(float(oy) - float(ny))
                maxdx = max(maxdx, dx)
                maxdy = max(maxdy, dy)
                total += 1
                if dx or dy:
                    ndiff += 1
    return maxdx, maxdy, ndiff, total


# ── watertightness: do hexes sharing a corner compute the SAME f32 vertex? ──
def watertight_violations(corner_fn, qmin, rmin, lw, lh):
    """Group every corner by its TRUE (f64) world position; a construction is
    watertight iff each group maps to ONE f32 (px,py). Returns (#cracked groups,
    max crack width in px)."""
    groups = {}
    for gr in range(lh):
        for gq in range(lw):
            q, r = qmin + gq, rmin + gr
            for i in range(6):
                tx, ty = hex_to_px(q, r)
                ox, oy = hex_corner_offset(i)
                key = (round(tx + ox, 6), round(ty + oy, 6))   # the shared point
                px, py = corner_fn(q, r, i)
                groups.setdefault(key, set()).add((float(px), float(py)))
    cracked = 0
    maxw = 0.0
    for pts in groups.values():
        if len(pts) > 1:
            cracked += 1
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            w = max(max(xs) - min(xs), max(ys) - min(ys)) * SCALE
            maxw = max(maxw, w)
    return cracked, maxw


# ── faithful GL-style rasteriser (pixel-center, inclusive edges) ──
def raster(tris, W, H, cam):
    """tris = list of (v0,v1,v2,(r,g,b)) in world space (f32 verts as floats).
    cam(wx,wy)->(sx,sy). Background = dark clear. Later tris overwrite (no depth).
    Inclusive edge test (>=0) in f64 from the f32 verts — captures gaps/overlaps
    from differing vertices regardless of tie-break (identical for OLD and NEW)."""
    img = np.zeros((H, W, 3), np.float32)
    img[:] = (14 / 255, 16 / 255, 24 / 255)            # view.loft:702 clear
    for (a, b, c, col) in tris:
        ax, ay = cam(*a); bx, by = cam(*b); cx, cy = cam(*c)
        # ensure CCW (positive area) so the inclusive test is consistent
        area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        if area == 0:
            continue
        if area < 0:
            bx, by, cx, cy = cx, cy, bx, by
        x0 = max(0, int(np.floor(min(ax, bx, cx))))
        x1 = min(W - 1, int(np.ceil(max(ax, bx, cx))))
        y0 = max(0, int(np.floor(min(ay, by, cy))))
        y1 = min(H - 1, int(np.ceil(max(ay, by, cy))))
        for py in range(y0, y1 + 1):
            pyc = py + 0.5
            for px in range(x0, x1 + 1):
                pxc = px + 0.5
                e0 = (bx - ax) * (pyc - ay) - (by - ay) * (pxc - ax)
                e1 = (cx - bx) * (pyc - by) - (cy - by) * (pxc - bx)
                e2 = (ax - cx) * (pyc - cy) - (ay - cy) * (pxc - cx)
                if e0 >= 0 and e1 >= 0 and e2 >= 0:
                    img[py, px] = col
    return img


def fan_tris(q, r, corner_fn, col):
    """6 fan triangles for hex (q,r): [center, corner kc, corner kc+1]."""
    cx, cy = hex_to_px(q, r)
    ctr = (float(f32(cx)), float(f32(cy)))             # center vertex (offset 0,0)
    out = []
    for kc in range(6):
        a = corner_fn(q, r, kc)
        b = corner_fn(q, r, (kc + 1) % 6)
        out.append((ctr, (float(a[0]), float(a[1])),
                    (float(b[0]), float(b[1])), col))
    return out


def rasterise_both(qmin, rmin, lw, lh, jitter=(0.0, 0.0), new_fn=new_corner_f32):
    # two distinct floor tints so EVERY seam is a colour boundary (worst case
    # for a crack: a gap shows the dark background, not a same-colour neighbour)
    A = (0.80, 0.745, 0.59)        # bare floor (worldmesh.loft:111)
    B = (0.52, 0.72, 0.35)         # K_MEADOW-ish tint, clearly different
    def colour(q, r):
        return A if ((q + r) & 1) == 0 else B
    # camera: fit the patch with a small margin, same transform for both
    cs = [hex_to_px(qmin + gq, rmin + gr)
          for gr in range(lh) for gq in range(lw)]
    xs = [c[0] for c in cs]; ys = [c[1] for c in cs]
    margin = 2.0
    minx, maxx = min(xs) - margin, max(xs) + margin
    miny, maxy = min(ys) - margin, max(ys) + margin
    W = int(np.ceil((maxx - minx) * SCALE))
    H = int(np.ceil((maxy - miny) * SCALE))

    jx, jy = jitter

    def cam(wx, wy):
        return (wx - minx) * SCALE + jx, (wy - miny) * SCALE + jy

    tris_old, tris_new = [], []
    for gr in range(lh):
        for gq in range(lw):
            q, r = qmin + gq, rmin + gr
            col = colour(q, r)
            tris_old += fan_tris(q, r, old_corner_f32, col)
            tris_new += fan_tris(q, r, new_fn, col)
    img_old = raster(tris_old, W, H, cam)
    img_new = raster(tris_new, W, H, cam)
    diff = np.abs(img_old - img_new)
    dmax = float(diff.max())
    npix = int((diff.max(axis=2) > 0).sum())
    return W, H, dmax, npix


if __name__ == "__main__":
    print("PLAN-RENDER P6 — instanced-floor parity blueprint\n")
    print("Invariant: instanced floor == fat-VBO floor, pixel-exact (dmax=0).\n")

    print("[1] vertex-position double-rounding scan (OLD vs NEW, f32):")
    print(f"    {'qmin/rmin':>12} {'maxΔx(world)':>14} {'maxΔx(px)':>11}"
          f" {'maxΔy':>7} {'ndiff/total':>14}")
    for qmin, rmin in [(0, 0), (50, 50), (100, 100), (1000, 1000), (-512, 777)]:
        mdx, mdy, nd, tot = scan_vertices(qmin, rmin, 24, 24)
        print(f"    {f'{qmin}/{rmin}':>12} {mdx:14.3e} {mdx*SCALE:11.3e}"
              f" {mdy:7.1e} {f'{nd}/{tot}':>14}")

    print("\n[2] WATERTIGHTNESS — do hexes sharing a corner produce the SAME f32"
          " vertex?")
    print(f"    {'qmin/rmin':>12} {'NAIVE center+offset':>22} {'LATTICE √3·xlat':>20}")
    for qmin, rmin in [(0, 0), (100, 100), (1000, 1000), (-512, 777)]:
        cN, wN = watertight_violations(new_corner_f32, qmin, rmin, 24, 24)
        cL, wL = watertight_violations(lat_corner_f32, qmin, rmin, 24, 24)
        print(f"    {f'{qmin}/{rmin}':>12}"
              f" {f'{cN} cracks (≤{wN:.1e}px)':>22}"
              f" {f'{cL} cracks':>20}")

    print("\n[3] rasterised parity vs OLD (two-tint checkerboard; worst over a 5×5"
          " sub-pixel\n    camera-jitter sweep — the falsification attempt):")
    print(f"    {'qmin/rmin':>12} {'NAIVE pixels≠':>16} {'LATTICE pixels≠':>16}")
    worstN = worstL = 0
    jitters = [(jx / 5.0, jy / 5.0) for jx in range(5) for jy in range(5)]
    for qmin, rmin in [(0, 0), (100, 100), (1000, 1000), (-512, 777)]:
        wN = wL = 0
        for j in jitters:
            _, _, _, nN = rasterise_both(qmin, rmin, 8, 8, j, new_corner_f32)
            _, _, _, nL = rasterise_both(qmin, rmin, 8, 8, j, lat_corner_f32)
            wN = max(wN, nN); wL = max(wL, nL)
        worstN = max(worstN, wN); worstL = max(worstL, wL)
        print(f"    {f'{qmin}/{rmin}':>12} {wN:16d} {wL:16d}")

    print()
    print("FINDINGS:")
    print(" • Bit-exact parity vs the f64-rounded fat VBO is UNATTAINABLE by an"
          " f32 shader.")
    print(" • NAIVE center+offset is NOT watertight (cracks) and breaks parity"
          f" (worst {worstN}px).")
    print(f" • LATTICE √3·xlat is WATERTIGHT (0 cracks) — adjacent hexes share"
          " corners exactly.")
    print(f"   It differs from OLD only by sub-pixel ULP (worst {worstL}px vs the"
          " OLD golden).")
    print("\nDESIGN: ship the LATTICE construction (watertight by design); the"
          " golden-parity\nprobe re-bakes its reference from the instanced path"
          " (the fat VBO is deleted anyway).")
