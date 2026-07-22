#!/usr/bin/env python3
"""glbview.py — render a .glb to a .png, for VERIFICATION.

Plans #5 and #9 verified every threshold numerically against metres (SCALE.md). This closes
the other half: whether the shapes those numbers describe are *believable*. A door, a tread,
a platform edge or a crown height is right or wrong against a person, and arithmetic does
not settle that.

Deliberately self-contained — a z-buffer rasteriser with flat shading, PIL only. No browser,
no xvfb, no GPU, and therefore deterministic: the same scene always yields the same pixels,
so a render can be diffed like any other gate.

    python3 tools/glbview.py build/scene.glb out.png --eye 12,-14,7 --target 0,0,2 --fov 42
"""
import argparse, json, math, struct, sys
from PIL import Image

FLOAT, USHORT, UINT, UBYTE = 5126, 5123, 5125, 5121
NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
CSIZE = {FLOAT: 4, USHORT: 2, UINT: 4, UBYTE: 1}
CFMT = {FLOAT: "f", USHORT: "H", UINT: "I", UBYTE: "B"}


def load_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, _ver, _len = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        raise SystemExit(f"{path}: not a GLB")
    off, js, bin_ = 12, None, b""
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bin_ = chunk
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return js, bin_


def read_accessor(g, bin_, idx):
    """Accessor -> list of tuples (or scalars), honouring byteStride."""
    acc = g["accessors"][idx]
    n, ctype, atype = acc["count"], acc["componentType"], acc["type"]
    ncomp, csz = NCOMP[atype], CSIZE[acc["componentType"]]
    bv = g["bufferViews"][acc["bufferView"]]
    base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or ncomp * csz
    fmt = "<" + CFMT[ctype] * ncomp
    out = []
    for i in range(n):
        v = struct.unpack_from(fmt, bin_, base + i * stride)
        out.append(v[0] if ncomp == 1 else v)
    return out


def node_matrix(nd):
    if "matrix" in nd:                       # glTF matrices are COLUMN-major
        m = nd["matrix"]
        return [[m[0], m[4], m[8], m[12]],
                [m[1], m[5], m[9], m[13]],
                [m[2], m[6], m[10], m[14]],
                [m[3], m[7], m[11], m[15]]]
    t = nd.get("translation", [0, 0, 0])
    r = nd.get("rotation", [0, 0, 0, 1])
    s = nd.get("scale", [1, 1, 1])
    x, y, z, w = r
    rot = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
           [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
           [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[rot[i][j] * s[j] for j in range(3)] + [t[i]] for i in range(3)] + [[0, 0, 0, 1]]


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def xform(m, p):
    return (m[0][0] * p[0] + m[0][1] * p[1] + m[0][2] * p[2] + m[0][3],
            m[1][0] * p[0] + m[1][1] * p[1] + m[1][2] * p[2] + m[1][3],
            m[2][0] * p[0] + m[2][1] * p[1] + m[2][2] * p[2] + m[2][3])


def collect(g, bin_):
    """Flatten the node tree into world-space triangles with a base colour."""
    tris = []
    mats = g.get("materials", [])

    def colour(mi):
        if mi is None or mi >= len(mats):
            return (0.75, 0.75, 0.75)
        pbr = mats[mi].get("pbrMetallicRoughness", {})
        c = pbr.get("baseColorFactor", [0.75, 0.75, 0.75, 1])
        return (c[0], c[1], c[2])

    def walk(ni, parent):
        nd = g["nodes"][ni]
        m = mat_mul(parent, node_matrix(nd))
        if "mesh" in nd:
            for prim in g["meshes"][nd["mesh"]].get("primitives", []):
                pos = read_accessor(g, bin_, prim["attributes"]["POSITION"])
                idx = (read_accessor(g, bin_, prim["indices"]) if "indices" in prim
                       else list(range(len(pos))))
                mi = prim.get("material")
                col = colour(mi)
                wp = [xform(m, p) for p in pos]
                for k in range(0, len(idx) - 2, 3):
                    tris.append((wp[idx[k]], wp[idx[k + 1]], wp[idx[k + 2]], col, mi))
        for c in nd.get("children", []):
            walk(c, m)

    ident = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    roots = g["scenes"][g.get("scene", 0)]["nodes"] if g.get("scenes") else range(len(g.get("nodes", [])))
    for r in roots:
        walk(r, ident)
    return tris


def render(tris, size, eye, target, up, fov, bg, sun, sm=None, bias=0.05):
    W, H = size
    fwd = [target[i] - eye[i] for i in range(3)]
    fl = math.dist(eye, target) or 1.0
    fwd = [c / fl for c in fwd]
    right = [fwd[1] * up[2] - fwd[2] * up[1], fwd[2] * up[0] - fwd[0] * up[2],
             fwd[0] * up[1] - fwd[1] * up[0]]
    rl = math.hypot(*right) or 1.0
    right = [c / rl for c in right]
    cup = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2],
           right[0] * fwd[1] - right[1] * fwd[0]]
    f = 1.0 / math.tan(math.radians(fov) / 2)
    aspect = W / H
    img = Image.new("RGB", (W, H), bg)
    px = img.load()
    zbuf = [[1e30] * W for _ in range(H)]
    sl = math.hypot(*sun) or 1.0
    sun = [c / sl for c in sun]

    def project(p):
        d = [p[i] - eye[i] for i in range(3)]
        cx = sum(d[i] * right[i] for i in range(3))
        cy = sum(d[i] * cup[i] for i in range(3))
        cz = sum(d[i] * fwd[i] for i in range(3))
        if cz <= 0.01:
            return None
        return ((cx * f / aspect / cz + 1) * 0.5 * W, (1 - cy * f / cz) * 0.5 * H, cz)

    drawn = 0
    for a, b, c, col, _mi in tris:
        pa, pb, pc = project(a), project(b), project(c)
        if not (pa and pb and pc):
            continue
        n = [(b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]),
             (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
             (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])]
        nl = math.hypot(*n) or 1.0
        n = [v / nl for v in n]
        # A hemisphere term, not abs(N.L).  Using the absolute value crushed every
        # VERTICAL face to the ambient floor, which collapsed the whole material palette
        # into one dark brown — walls, roofs and trunks became indistinguishable. Sky
        # light from above plus a warm key gives vertical surfaces their own value again,
        # which is what lets colour carry meaning at all.
        lam = max(0.0, sum(n[i] * sun[i] for i in range(3)))
        sky = 0.5 + 0.5 * n[2]                 # up-facing catches more sky
        # Warm low key + cool sky fill. Colour temperature is the mood lever (skill:
        # "dusk = a warm low key light + cool ambient"), and in 3D you SET it rather than
        # paint it — the renderer then does the warm/cool across every surface for free.
        amb = 0.34
        kr = amb + 0.26 * sky * 0.82 + 0.56 * lam * 1.16
        kg = amb + 0.26 * sky * 0.90 + 0.56 * lam * 1.00
        kb = amb + 0.26 * sky * 1.15 + 0.56 * lam * 0.74
        rgb = (int(max(0, min(255, col[0] * 255 * kr))),
               int(max(0, min(255, col[1] * 255 * kg))),
               int(max(0, min(255, col[2] * 255 * kb))))
        x0 = max(0, int(min(pa[0], pb[0], pc[0])));  x1 = min(W - 1, int(max(pa[0], pb[0], pc[0])) + 1)
        y0 = max(0, int(min(pa[1], pb[1], pc[1])));  y1 = min(H - 1, int(max(pa[1], pb[1], pc[1])) + 1)
        if x1 < x0 or y1 < y0:
            continue
        d = ((pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1]))
        if abs(d) < 1e-12:
            continue
        drawn += 1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                sx, sy = x + 0.5, y + 0.5
                w0 = ((pb[1] - pc[1]) * (sx - pc[0]) + (pc[0] - pb[0]) * (sy - pc[1])) / d
                w1 = ((pc[1] - pa[1]) * (sx - pc[0]) + (pa[0] - pc[0]) * (sy - pc[1])) / d
                w2 = 1 - w0 - w1
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                z = w0 * pa[2] + w1 * pb[2] + w2 * pc[2]
                if z < zbuf[y][x]:
                    zbuf[y][x] = z
                    if sm is None:
                        px[x, y] = rgb
                    else:
                        # perspective-correct world position, so the shadow lookup lands
                        # where the surface actually is rather than where affine screen
                        # interpolation would put it
                        ia, ib, ic = w0 / pa[2], w1 / pb[2], w2 / pc[2]
                        den = ia + ib + ic
                        wp = [(ia * a[k] + ib * b[k] + ic * c[k]) / den for k in range(3)]
                        vis = shadow_factor(sm, wp, bias)
                        # the shadow removes the KEY only; sky fill still reaches into it,
                        # which is why a real shadow is coloured rather than black
                        s2 = amb + 0.26 * sky
                        kr2 = s2 * 0.82 + 0.56 * lam * 1.16 * vis
                        kg2 = s2 * 0.90 + 0.56 * lam * 1.00 * vis
                        kb2 = s2 * 1.15 + 0.56 * lam * 0.74 * vis
                        px[x, y] = (int(max(0, min(255, col[0] * 255 * kr2))),
                                    int(max(0, min(255, col[1] * 255 * kg2))),
                                    int(max(0, min(255, col[2] * 255 * kb2))))
    return img, drawn



# ── SHADOW PASS ──────────────────────────────────────────────────────────────
#
# Colour temperature alone could not carry "late afternoon" — the landscape stayed flat and
# overcast through three passes, and the intent file named cast shadows as the missing lever
# rather than a nice-to-have. A shadow proves the sun and the object share a world, which is
# the "coherent world" the skill says realness actually lives in.
#
# Standard shadow mapping, sized to the scene: a depth-only orthographic pass from the
# light (directional, so orthographic is exact), then a depth compare per shaded pixel.

def _norm(v):
    l = math.hypot(*v) or 1.0
    return [c / l for c in v]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def build_shadow_map(tris, sun, res=768):
    """Depth from the light's point of view. `sun` points TOWARD the light."""
    f = _norm([-c for c in sun])                     # the way light travels
    up = [0, 0, 1] if abs(f[2]) < 0.9 else [0, 1, 0]
    r = _norm(_cross(f, up))
    u = _cross(r, f)
    pts = [p for t in tris for p in t[:3]]
    if not pts:
        return None
    xs = [sum(p[i] * r[i] for i in range(3)) for p in pts]
    ys = [sum(p[i] * u[i] for i in range(3)) for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    pad = max(x1 - x0, y1 - y0) * 0.02 + 1e-6
    x0 -= pad; x1 += pad; y0 -= pad; y1 += pad
    sx = (res - 1) / (x1 - x0)
    sy = (res - 1) / (y1 - y0)
    depth = [[1e30] * res for _ in range(res)]
    for a, b, c, _col, _m in tris:
        P = []
        for p in (a, b, c):
            P.append((( sum(p[i] * r[i] for i in range(3)) - x0) * sx,
                      ( sum(p[i] * u[i] for i in range(3)) - y0) * sy,
                        sum(p[i] * f[i] for i in range(3))))
        d = (P[1][1] - P[2][1]) * (P[0][0] - P[2][0]) + (P[2][0] - P[1][0]) * (P[0][1] - P[2][1])
        if abs(d) < 1e-12:
            continue
        mnx = max(0, int(min(P[0][0], P[1][0], P[2][0])))
        mxx = min(res - 1, int(max(P[0][0], P[1][0], P[2][0])) + 1)
        mny = max(0, int(min(P[0][1], P[1][1], P[2][1])))
        mxy = min(res - 1, int(max(P[0][1], P[1][1], P[2][1])) + 1)
        for yy in range(mny, mxy + 1):
            row = depth[yy]
            for xx in range(mnx, mxx + 1):
                px, py = xx + 0.5, yy + 0.5
                w0 = ((P[1][1] - P[2][1]) * (px - P[2][0]) + (P[2][0] - P[1][0]) * (py - P[2][1])) / d
                w1 = ((P[2][1] - P[0][1]) * (px - P[2][0]) + (P[0][0] - P[2][0]) * (py - P[2][1])) / d
                w2 = 1 - w0 - w1
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                z = w0 * P[0][2] + w1 * P[1][2] + w2 * P[2][2]
                if z < row[xx]:
                    row[xx] = z
    return (r, u, f, x0, y0, sx, sy, res, depth)


def shadow_factor(sm, p, bias):
    """0 = fully shadowed, 1 = lit.  Four taps, so the edge is not a staircase."""
    if sm is None:
        return 1.0
    r, u, f, x0, y0, sx, sy, res, depth = sm
    lx = (sum(p[i] * r[i] for i in range(3)) - x0) * sx
    ly = (sum(p[i] * u[i] for i in range(3)) - y0) * sy
    lz = sum(p[i] * f[i] for i in range(3))
    lit = 0
    for dx, dy in ((0.0, 0.0), (0.9, 0.0), (0.0, 0.9), (0.9, 0.9)):
        xi, yi = int(lx + dx), int(ly + dy)
        if xi < 0 or yi < 0 or xi >= res or yi >= res:
            lit += 1
            continue
        if lz <= depth[yi][xi] + bias:
            lit += 1
    return lit / 4.0


def material_coverage(tris, size, eye, target, up, fov, sun):
    """Pixels per MATERIAL, measured at render time.

    The landscape exercise measured composition by classifying output pixels into "stone"
    and "roof" by colour, and the classifier mis-binned shaded maroon as ground — so a
    predicate passed on a number nobody should have trusted. The renderer knows exactly
    which triangle carries which material, because it read them from the GLB. Counting
    those is a fact; inferring them from pixels is a guess wearing a fact's clothes.
    """
    W, H = size
    fwd = [target[i] - eye[i] for i in range(3)]
    fl = math.dist(eye, target) or 1.0
    fwd = [c / fl for c in fwd]
    right = [fwd[1] * up[2] - fwd[2] * up[1], fwd[2] * up[0] - fwd[0] * up[2],
             fwd[0] * up[1] - fwd[1] * up[0]]
    rl = math.hypot(*right) or 1.0
    right = [c / rl for c in right]
    cup = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2],
           right[0] * fwd[1] - right[1] * fwd[0]]
    f = 1.0 / math.tan(math.radians(fov) / 2)
    aspect = W / H
    zbuf = [[1e30] * W for _ in range(H)]
    mbuf = [[None] * W for _ in range(H)]

    def project(p):
        d = [p[i] - eye[i] for i in range(3)]
        cx = sum(d[i] * right[i] for i in range(3))
        cy = sum(d[i] * cup[i] for i in range(3))
        cz = sum(d[i] * fwd[i] for i in range(3))
        if cz <= 0.01:
            return None
        return ((cx * f / aspect / cz + 1) * 0.5 * W, (1 - cy * f / cz) * 0.5 * H, cz)

    for a, b, c, _col, mi in tris:
        pa, pb, pc = project(a), project(b), project(c)
        if not (pa and pb and pc):
            continue
        x0 = max(0, int(min(pa[0], pb[0], pc[0])));  x1 = min(W - 1, int(max(pa[0], pb[0], pc[0])) + 1)
        y0 = max(0, int(min(pa[1], pb[1], pc[1])));  y1 = min(H - 1, int(max(pa[1], pb[1], pc[1])) + 1)
        d = ((pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1]))
        if abs(d) < 1e-12 or x1 < x0 or y1 < y0:
            continue
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                sx, sy = x + 0.5, y + 0.5
                w0 = ((pb[1] - pc[1]) * (sx - pc[0]) + (pc[0] - pb[0]) * (sy - pc[1])) / d
                w1 = ((pc[1] - pa[1]) * (sx - pc[0]) + (pa[0] - pc[0]) * (sy - pc[1])) / d
                w2 = 1 - w0 - w1
                if w0 < 0 or w1 < 0 or w2 < 0:
                    continue
                z = w0 * pa[2] + w1 * pb[2] + w2 * pc[2]
                if z < zbuf[y][x]:
                    zbuf[y][x] = z
                    mbuf[y][x] = mi
    counts = {}
    for row in mbuf:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    return counts, W * H


def triple(s):
    return tuple(float(v) for v in s.split(","))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb"); ap.add_argument("png")
    ap.add_argument("--eye", type=triple, default=(14, -16, 9))
    ap.add_argument("--target", type=triple, default=(0, 0, 2))
    ap.add_argument("--up", type=triple, default=(0, 0, 1))
    ap.add_argument("--fov", type=float, default=40.0)
    ap.add_argument("--size", default="900x620")
    ap.add_argument("--bg", default="30,34,40")
    ap.add_argument("--sun", type=triple, default=(0.4, 0.6, -0.7))
    ap.add_argument("--shadow", type=int, default=0, help="shadow-map resolution, 0 = off")
    ap.add_argument("--bias", type=float, default=0.06)
    ap.add_argument("--stats", action="store_true",
                    help="report pixel coverage per MATERIAL, measured not guessed")
    a = ap.parse_args()
    W, H = (int(v) for v in a.size.split("x"))
    g, bin_ = load_glb(a.glb)
    tris = collect(g, bin_)
    sm = build_shadow_map(tris, a.sun, a.shadow) if a.shadow else None
    img, drawn = render(tris, (W, H), a.eye, a.target, a.up, a.fov,
                        tuple(int(v) for v in a.bg.split(",")), a.sun, sm, a.bias)
    img.save(a.png)
    print(f"{a.glb}: {len(tris)} triangles, {drawn} rasterised -> {a.png} ({W}x{H})")
    if a.stats:
        counts, total = material_coverage(tris, (W, H), a.eye, a.target, a.up, a.fov, a.sun)
        mats = g.get("materials", [])
        rows = sorted(counts.items(), key=lambda kv: -kv[1])
        print("  material coverage (measured at render time, not classified from pixels):")
        for mi, n in rows:
            nm = "sky" if mi is None else mats[mi].get("name", f"mat{mi}") if mi < len(mats) else f"mat{mi}"
            print(f"    {nm:<22} {100.0 * n / total:6.2f}%")


if __name__ == "__main__":
    main()
