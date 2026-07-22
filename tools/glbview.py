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
                col = colour(prim.get("material"))
                wp = [xform(m, p) for p in pos]
                for k in range(0, len(idx) - 2, 3):
                    tris.append((wp[idx[k]], wp[idx[k + 1]], wp[idx[k + 2]], col))
        for c in nd.get("children", []):
            walk(c, m)

    ident = [[1 if i == j else 0 for j in range(4)] for i in range(4)]
    roots = g["scenes"][g.get("scene", 0)]["nodes"] if g.get("scenes") else range(len(g.get("nodes", [])))
    for r in roots:
        walk(r, ident)
    return tris


def render(tris, size, eye, target, up, fov, bg, sun):
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
    for a, b, c, col in tris:
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
        sh = 0.34 + 0.30 * sky + 0.52 * lam
        rgb = (int(max(0, min(255, col[0] * 255 * sh))),
               int(max(0, min(255, col[1] * 255 * sh))),
               int(max(0, min(255, col[2] * 255 * sh))))
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
                    px[x, y] = rgb
    return img, drawn


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
    a = ap.parse_args()
    W, H = (int(v) for v in a.size.split("x"))
    g, bin_ = load_glb(a.glb)
    tris = collect(g, bin_)
    img, drawn = render(tris, (W, H), a.eye, a.target, a.up, a.fov,
                        tuple(int(v) for v in a.bg.split(",")), a.sun)
    img.save(a.png)
    print(f"{a.glb}: {len(tris)} triangles, {drawn} rasterised -> {a.png} ({W}x{H})")


if __name__ == "__main__":
    main()
