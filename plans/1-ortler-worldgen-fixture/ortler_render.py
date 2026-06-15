#!/usr/bin/env python3
"""ortler_render.py — the two same-scale drawings (@PLN1 S3/S4), one routine for both.

Feeds our real Ortler hex map into the existing world-drawing routine
(`tools/overland_blueprint.render_window`) and renders, at the SAME scale:
  A  ortler_actual.png — real heights, tinted by REAL OSM terrain types (ground truth)
  B  ortler_model.png  — real heights, classified by OUR model (material_contest)
plus ortler_compare.png (A | B side by side).  Only the classification differs, so the
gap between B and A is the adequacy answer (verify early, by eye).
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortler_import as oi
import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import overland_blueprint as ob

OUT = Path(__file__).resolve().parent / "out"; OUT.mkdir(exist_ok=True)
COLS, ROWS, HW, VS = oi.COLS, oi.ROWS, oi.HW, oi.VS
PX_M = 60.0

# OSM class -> colour (indexed by NAME2CODE)
OSM_PAL = np.array([
    [180, 175, 165],   # 0 none
    [ 60, 110, 165],   # 1 water
    [236, 240, 250],   # 2 glacier
    [138, 132, 126],   # 3 rock
    [172, 162, 150],   # 4 scree
    [ 56, 104,  52],   # 5 wood
    [150, 176,  96],   # 6 grass
    [201, 188, 120],   # 7 farmland
    [170, 192, 110],   # 8 orchard
    [150, 172,  96],   # 9 vineyard
    [110, 140, 130],   # 10 wetland
], dtype=float)

# fan-triangle angular boundaries on the unit hex: the 18 rays center->{corner, 1/3, 2/3}
# that separate the 18 fan triangles, in fan order. A pixel's angle from its hex center ->
# which triangle it sits in (exact, since fan boundaries ARE these radial rays).
def _fan_bang():
    cor = [(math.cos(math.radians(30 + 60 * k)), math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    pts = []
    for k in range(6):
        a, b = cor[k], cor[(k + 1) % 6]
        pts.append(a)
        pts.append((a[0] + (b[0] - a[0]) / 3, a[1] + (b[1] - a[1]) / 3))
        pts.append((a[0] + 2 * (b[0] - a[0]) / 3, a[1] + 2 * (b[1] - a[1]) / 3))
    ang = [math.degrees(math.atan2(p[1], p[0])) % 360.0 for p in pts]
    return np.array([a if a >= 30.0 else a + 360.0 for a in ang])
BANG = _fan_bang()

# --- model-B classification: per-triangle ground material, with hex-neighbor influence
# growing the rocky zones (tunable; compare B's general colour vs A on ortler_compare) ---
ROCK_LO, ROCK_HI = 2150.0, 3100.0   # rockiness ramp: treeline (0) -> snowline (1)
GROW, GROW_ITERS = 0.60, 2          # neighbour dilation: rock bleeds to neighbours -> bigger zones
T_ROCK, T_SCREE = 0.66, 0.42        # per-triangle rock / scree thresholds
TRI_NOISE = 0.18                    # per-triangle rockiness variation
H_JITTER = 250.0                    # per-triangle height jitter -> EVERY band boundary
                                    # (snowline/treeline/valley) varies per-triangle, not per-hex
WOOD_FRAC = 0.70                    # of the montane/valley band, fraction that is WOOD vs open
                                    # grass -> forest is one green among others, not all of it
VALLEY_H = 1100.0                   # below this = potential agriculture (valley floor)
AG_ERODE_ITERS = 3                  # the surroundings CREEP INTO ag (continuous erosion):
T_AG, AG_NOISE = 0.85, 0.25         # per-triangle ag threshold + variation -> ag boundary is
                                    # per-triangle (not blocky per-hex) and a realistic small size

def _h01(a, b, c):
    n = (a * 73856093 ^ b * 19349663 ^ c * 83492791) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffffffff) / 4294967296.0

def compute_model_tri(ov, h):
    """Per-triangle model material. Rockiness rises with elevation, then NEIGHBOUR INFLUENCE
    dilates it (rock grows into adjacent hexes -> larger contiguous rocky zones). Each of the
    18 triangles gets its own material via per-triangle noise. Returns codes indexed
    (c*ROWS+r)*18+loc, matching _tri_gid."""
    ROWS_, COLS_ = h.shape
    R = np.clip((h - ROCK_LO) / (ROCK_HI - ROCK_LO), 0.0, 1.0)
    for _ in range(GROW_ITERS):
        nb = np.zeros_like(R)
        for r in range(ROWS_):
            for c in range(COLS_):
                m = 0.0
                for nc, nr in ov.neighbors(c, r):
                    if 0 <= nc < COLS_ and 0 <= nr < ROWS_ and R[nr, nc] > m:
                        m = R[nr, nc]
                nb[r, c] = m
        R = np.maximum(R, GROW * nb)            # rock spreads outward from the high cores
    # agriculture EROSION as a CONTINUOUS potential: valley=1, decayed each iter by the
    # neighbour support (edges lose support as the surroundings creep in). Per-triangle noise
    # then thresholds it, so the ag boundary is per-triangle (no blocky hex right-angles).
    agp = (h < VALLEY_H).astype(float)
    for _ in range(AG_ERODE_ITERS):
        nb = np.zeros_like(agp)
        for r in range(ROWS_):
            for c in range(COLS_):
                s = 0.0; k = 0
                for nc, nr in ov.neighbors(c, r):
                    if 0 <= nc < COLS_ and 0 <= nr < ROWS_:
                        s += agp[nr, nc]; k += 1
                nb[r, c] = s / k if k else 0.0
        agp = agp * nb                          # interior stays ~1, edges decay toward 0
    # per-triangle classification with SPATIALLY-COHERENT noise: sample a smooth fbm at each
    # triangle's CENTROID (not an independent per-triangle hash), so adjacent triangles get
    # similar noise -> each type forms contiguous patches with smoothly-wandering boundaries,
    # no white-noise speckle / intermixing across the type edges.
    import trimesh as tm
    m = tm.build()
    keys = sorted(m.hex_tris.keys())                          # c-major: index = c*ROWS_+r
    tris = np.array([m.hex_tris[kk] for kk in keys], np.int32).reshape(-1, 3)
    cen = np.array(m.verts)[tris].mean(axis=1)                # (ntri,2) triangle centroids
    cx, cy = cen[:, 0], cen[:, 1]
    def chan(ch, wl):                                         # smooth fbm channel, mapped to [0,1]
        n = ob.fbm(cx, cy, wl, 3, ch)
        return (n - n.min()) / (n.max() - n.min() + 1e-9)
    nH, nR, nW, nA = chan(41, 760.0), chan(42, 760.0), chan(43, 560.0), chan(44, 620.0)
    th = np.repeat(np.array([h[r, c] for (c, r) in keys]), 18)
    tR = np.repeat(np.array([R[r, c] for (c, r) in keys]), 18)
    ta = np.repeat(np.array([agp[r, c] for (c, r) in keys]), 18)
    hht = th + (nH - 0.5) * 2.0 * H_JITTER                    # per-triangle height (coherent)
    rr = tR + (nR - 0.5) * 2.0 * TRI_NOISE
    woody = nW < WOOD_FRAC
    aok = ta + (nA - 0.5) * 2.0 * AG_NOISE > T_AG
    green = np.where(woody, 5, 6)                             # forest vs open grass
    code = np.select(
        [hht >= 3100.0, rr > T_ROCK, rr > T_SCREE, hht >= 2150.0, hht >= VALLEY_H, aok],
        [2,             3,           4,            6,             green,           7],
        default=green).astype(np.int16)
    return code

def tile_compare(tri_osm, tri_model, cols, rows, n=4):
    """Materials compare per 4x4 = 16 tiles: A-vs-B coverage of rock/scree and green in each
    region, so we catch LOCAL colour mismatches (B can match globally but be off in a zone)."""
    none = oi.NAME2CODE["none"]
    gid = np.arange(len(tri_model)); hexidx = gid // 18
    c = hexidx // rows; r = hexidx % rows
    tile = (r * n // rows) * n + (c * n // cols)
    def grid(codes, label):
        print(f"[16-tile {label} %  A|B]  (rows N->S, cols W->E):")
        for ti in range(n):
            cells = []
            for tj in range(n):
                m = tile == (ti * n + tj)
                a = tri_osm[m]; acls = a[a != none]; b = tri_model[m]
                av = round(float(np.isin(acls, codes).mean()) * 100) if len(acls) else -1
                bv = round(float(np.isin(b, codes).mean()) * 100)
                cells.append(f"{av:3d}|{bv:<3d}")
            print("   " + " ".join(cells))
    grid([3, 4], "rock/scree")
    grid([5, 6, 8, 9], "green")
    grid([7], "agric")

def occurrence_compare(tri_osm, tri_model):
    """Verify every terrain type's occurrence frequency: A (real, over classified) vs B (model)."""
    none = oi.NAME2CODE["none"]
    names = {v: k for k, v in oi.NAME2CODE.items()}
    acls = tri_osm[tri_osm != none]
    print(f"[occurrence per type]  A% (of {len(acls)} classified) | B% (of {len(tri_model)} tris):")
    for code in sorted(names):
        if code == none:
            continue
        a = float((acls == code).mean()) * 100
        b = float((tri_model == code).mean()) * 100
        note = "  <- model does not produce (lumped/absent)" if (b == 0 and a > 0.2) else ""
        print(f"   {names[code]:9s}  A={a:5.1f}  B={b:5.1f}{note}")

def spatial_agreement(tri_osm, tri_model):
    """Per-triangle SPATIAL agreement: does B's class land at the SAME triangle as A's?
    (tri_osm and tri_model share the gid indexing.) Exact-class + coarse-group match, and a
    chance-corrected kappa so we know B is located right, not just present in equal amount."""
    none = oi.NAME2CODE["none"]
    # code 0..10 -> coarse group; B only produces ice/rock/forest/open/field
    GID2GRP = np.array([-1, 0, 1, 2, 2, 3, 4, 5, 5, 5, 6])
    GNAME = ["water", "ice", "rock", "forest", "open", "field", "wet"]
    cls = tri_osm != none
    a, b = tri_osm[cls], tri_model[cls]
    ga, gb = GID2GRP[a], GID2GRP[b]
    exact = float((a == b).mean()) * 100
    coarse = float((ga == gb).mean()) * 100
    pe = sum(float((ga == g).mean()) * float((gb == g).mean()) for g in range(7))
    kappa = (coarse / 100 - pe) / (1 - pe + 1e-9)
    print(f"[spatial agreement, per-triangle over {int(cls.sum())} classified]")
    print(f"   exact-class B==A  : {exact:.0f}%")
    print(f"   coarse-group B==A : {coarse:.0f}%   (chance {pe*100:.0f}%, kappa {kappa:+.2f})")
    print(f"   per A-group recall (B lands the same coarse group):")
    for g in range(7):
        m = ga == g
        if m.any():
            print(f"     {GNAME[g]:7s} A={int(m.sum()):6d}  B-match={float((gb[m] == g).mean())*100:3.0f}%")

def check_invariants(ov):
    """Engine I2 (lakes level) + I3 (water never flows uphill) on the model's hydrology.
    Returns (uphill_flow_cells, n_lakes, worst_lake_surface_spread_m)."""
    H = ov.h
    up = 0
    for r in range(ov.ny):
        for c in range(ov.nx):
            fi = ov.flow[r, c]
            if fi >= 0:
                nc, nr = ov.neighbors(c, r)[fi]
                if 0 <= nc < ov.nx and 0 <= nr < ov.ny and H[nr, nc] > H[r, c] + 1e-6:
                    up += 1
    lake = ov.wet & (H > ob.SEA_LEVEL)        # lakes = wet land cells (pit-filled pools)
    seen = np.zeros_like(lake, bool)
    worst, nlk = 0.0, 0
    for r in range(ov.ny):
        for c in range(ov.nx):
            if lake[r, c] and not seen[r, c]:
                nlk += 1; st = [(c, r)]; seen[r, c] = True; hs = []
                while st:
                    cc, rr = st.pop(); hs.append(H[rr, cc])
                    for nc, nr in ov.neighbors(cc, rr):
                        if 0 <= nc < ov.nx and 0 <= nr < ov.ny and lake[nr, nc] and not seen[nr, nc]:
                            seen[nr, nc] = True; st.append((nc, nr))
                worst = max(worst, max(hs) - min(hs))
    return up, nlk, worst

def _lake_cell(ov):
    return ov.wet & (ov.h > ob.SEA_LEVEL)

def _cell_of(ov, x, y):
    r = int(min(max(round(y / ov.vs), 0), ov.ny - 1))
    c = int(min(max(round(x / ov.hw - 0.5 * (r & 1)), 0), ov.nx - 1))
    return c, r

def clip_rivers_at_lakes(ov, rivers):
    """Routine: flowing water must not extend INTO lakes. Truncate each course at the
    first vertex that enters a lake cell (the shore), so the river ends at the lake and
    the still body carries no current. Returns (clipped_rivers, in_lake_segments_removed)."""
    lake = _lake_cell(ov)
    out, removed = [], 0
    for (fp, width, depth, vwid, alluv, rad) in rivers:
        cut = len(fp)
        for i, (x, y) in enumerate(fp):
            c, r = _cell_of(ov, x, y)
            if lake[r, c]:
                cut = i + 1            # keep the shore entry point, drop the rest
                removed += len(fp) - cut
                break
        if cut >= 2:
            out.append((fp[:cut], width[:cut], depth[:cut], vwid[:cut], alluv[:cut], rad))
    return out, removed

def fed_rivers(ov, mask, flow):
    """Build river courses from the fed OSM directions: chain each headwater downstream,
    width by upstream accumulation. The blueprint course tuple (fp, width, depth, vwid,
    alluv, rad) — minimal depth so it draws lines without re-carving the real heights."""
    ny, nx = mask.shape
    cells = [(c, r) for r in range(ny) for c in range(nx) if mask[r, c]]
    target = {}
    for (c, r) in cells:
        fi = int(flow[r, c]); t = None
        if fi >= 0:
            nc, nr = ov.neighbors(c, r)[fi]
            if 0 <= nc < nx and 0 <= nr < ny and mask[nr, nc]:
                t = (nc, nr)
        target[(c, r)] = t
    acc = {cell: 1 for cell in cells}
    for cell in sorted(cells, key=lambda cr: -ov.h[cr[1], cr[0]]):   # high -> low
        t = target[cell]
        if t in acc: acc[t] += acc[cell]
    istarget = {t for t in target.values() if t is not None}
    heads = [cell for cell in cells if cell not in istarget]
    rivers, visited = [], set()
    for head in heads:
        fp, w, cur, n = [], [], head, 0
        while cur is not None and cur not in visited and n <= len(cells):
            visited.add(cur); c, r = cur
            fp.append(ov.center(c, r)); w.append(2.0 + acc[cur] ** 0.5)
            cur = target[cur]; n += 1
        if len(fp) >= 2:
            m = len(fp)
            rivers.append((fp, w, [2.0]*m, [120.0]*m, [10.0]*m, max(w) + 400.0))
    return rivers

def main():
    d = np.load(oi.HEX_NPZ)
    if "osm" not in d:
        print("run `osm` first (need OSM classes in the npz)"); return False
    h, osm = d["h"].astype(float), d["osm"]

    # size a render lattice to OUR grid, inject real heights, derive + classify
    ob.WORLD_W = (COLS - 1) * HW
    ob.WORLD_H = (ROWS - 1) * VS
    ov = ob.Overland(ob.TILE_M, heights=h)
    # Lakes FOLLOW THE DATA (OSM water), not pit-fill invention. Pit-fill stays (it routes
    # flow so there are no internal sinks) but it must NOT create lakes: at 1.5 km every
    # local basin flooded into a spurious lake (72). Real lakes = the OSM water cells.
    water = (osm == oi.NAME2CODE["water"])
    ov.mat[ov.mat == ob.M_LAKE] = ob.M_HILL        # demote pit-fill's invented lakes to land
    ov.mat[water] = ob.M_LAKE                       # real lakes only
    ov.wet = (ov.h <= ob.SEA_LEVEL) | water
    up, nlk, spread = check_invariants(ov)
    print(f"[I3 water-never-up] {up} cells flow uphill (want 0)")
    print(f"[I2 lakes-level]    {nlk} model lakes; worst surface spread {spread:.2f} m (want ~0)")
    print(f"[OSM water]         {int((osm == oi.NAME2CODE['water']).sum())} real water cells (ground truth)")

    # window covering all hexes (+1 cell margin for corners)
    x0, y0 = -HW, -VS
    wpx, hpx = int((COLS + 1) * HW / PX_M), int((ROWS + 1) * VS / PX_M)

    # A = OSM ground truth, PER-TRIANGLE (tri_osm centroids); B = our model's derived bands,
    # per-PIXEL on the blended real height f["h"] (no vertex-mesh fetch needed). Same palette ->
    # the only difference is the classification.
    tri_osm = np.load(oi.TRIOSM_NPZ)["tri_osm"]
    tri_model = compute_model_tri(ov, h)        # per-triangle model material (neighbour-grown rock)

    def _tri_gid(xs, ys):
        r = np.clip(np.round(ys / VS).astype(int), 0, ROWS - 1)
        c = np.clip(np.round(xs / HW - 0.5 * (r & 1)).astype(int), 0, COLS - 1)
        cx = (c + 0.5 * (r & 1)) * HW; cy = r * VS
        ang = np.degrees(np.arctan2(ys - cy, xs - cx)) % 360.0
        ang = np.where(ang >= 30.0, ang, ang + 360.0)
        loc = np.clip(np.searchsorted(BANG, ang, side="right") - 1, 0, 17)
        return (c * ROWS + r) * 18 + loc

    def osm_tint(xs, ys, matcol, f):
        return OSM_PAL[tri_osm[_tri_gid(xs, ys)]]

    def model_tint(xs, ys, matcol, f):
        return OSM_PAL[tri_model[_tri_gid(xs, ys)]]

    # general-colour comparison (the tuning target): rock/scree + green coverage, A vs B
    none = oi.NAME2CODE["none"]
    cls = tri_osm != none
    rockA = float(np.isin(tri_osm[cls], [3, 4]).mean()) * 100
    rockB = float(np.isin(tri_model, [3, 4]).mean()) * 100
    grnA = float(np.isin(tri_osm[cls], [5, 6, 8, 9]).mean()) * 100
    grnB = float(np.isin(tri_model, [5, 6, 8, 9]).mean()) * 100
    print(f"[material %]  rock/scree: A={rockA:.0f}% B={rockB:.0f}%   green: A={grnA:.0f}% B={grnB:.0f}%")
    occurrence_compare(tri_osm, tri_model)
    spatial_agreement(tri_osm, tri_model)
    tile_compare(tri_osm, tri_model, COLS, ROWS)

    # rivers: A (real) follows the fed OSM network; B (model) keeps the D8 courses
    osm_rivers = clip_rivers_at_lakes(ov, fed_rivers(ov, d["river_mask"], d["river_flow"]))[0]
    model_rivers = clip_rivers_at_lakes(ov, ob.fine_rivers(ov))[0]
    print(f"rivers: A(OSM)={len(osm_rivers)} courses, B(model)={len(model_rivers)} courses")

    print(f"=== rendering two {wpx}x{hpx} drawings (px={PX_M:.0f} m) ===")
    imgA = ob.render_window(ov, osm_rivers, x0, y0, wpx, hpx, PX_M, tint=osm_tint, real_height=True)
    imgB = ob.render_window(ov, model_rivers, x0, y0, wpx, hpx, PX_M, tint=model_tint, real_height=True)

    Image.fromarray(imgA).save(OUT / "ortler_actual.png")
    Image.fromarray(imgB).save(OUT / "ortler_model.png")

    # side-by-side with labels
    gap, lab = 14, 22
    cv = Image.new("RGB", (wpx * 2 + gap, hpx + lab), (16, 16, 20))
    cv.paste(Image.fromarray(imgA), (0, lab))
    cv.paste(Image.fromarray(imgB), (wpx + gap, lab))
    dr = ImageDraw.Draw(cv)
    dr.text((6, 6), "A  ACTUAL (real heights + OSM terrain types)", fill=(235, 235, 200))
    dr.text((wpx + gap + 6, 6), "B  OUR MODEL (material_contest classification)", fill=(235, 235, 200))
    cv.save(OUT / "ortler_compare.png")
    print(f"wrote {(OUT/'ortler_compare.png').relative_to(REPO)} (+ actual/model)")

    # orthographic relief — height + waterflow + lakes (the existing routines),
    # with river courses CLIPPED at lake shores (water must not extend into lakes)
    W3 = 1200
    imA = ob.panel_view3d(ov, osm_rivers, str(OUT / "ortho_actual.png"), wpx=W3, ck=0.6,
                          hk=1.0 / 9.0, tint=osm_tint, real_height=True,
                          caption="A  ACTUAL (OSM terrain types + OSM rivers)")
    imB = ob.panel_view3d(ov, model_rivers, str(OUT / "ortho_model.png"), wpx=W3, ck=0.6,
                          hk=1.0 / 9.0, tint=model_tint, real_height=True,
                          caption="B  OUR MODEL (derived bands + D8 rivers)")
    gap = 14
    cvo = Image.new("RGB", (imA.width + imB.width + gap, max(imA.height, imB.height)), (16, 16, 20))
    cvo.paste(imA, (0, 0)); cvo.paste(imB, (imA.width + gap, 0))
    cvo.save(OUT / "ortler_ortho_compare.png")
    print(f"wrote {(OUT/'ortler_ortho_compare.png').relative_to(REPO)}")
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
