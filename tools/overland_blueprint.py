#!/usr/bin/env python3
"""overland_blueprint.py — BLUEPRINT instrument for OVERLAND.md (throwaway, not game code).

Pins the overland-terrain design before any loft exists:
  * a coarse overland hex lattice (pointy-top, odd-r, the moros convention) is the
    terrain authority — one cell record {material, height, water(level+dir)} per tile;
  * fine terrain = smooth kernel blend of nearby overland cell fields + per-biome
    fractal detail noise — seamless across tile borders BY CONSTRUCTION;
  * rivers: coarse hydrology (flow dir + accumulation on the lattice) gives the truth,
    a fractal midpoint-displacement course gives the geometry — meander amplitude grows
    as the land flattens toward the sea; the landscape CARVES around the course;
  * THE invariant (window independence): every fine value is a pure function of
    (seed, overland data, world x, y) — rendering whole vs as independent apron'd
    windows is byte-identical.  `seam` executes that proof.

Usage: python3 tools/overland_blueprint.py [overland|fine|mouth|seam|strip|all]
Outputs PNGs into tools/_overland/.

Everything is deterministic: hash-based noise only, no sequential RNG anywhere.
Designed to port: pure functions over (seed, cells, x, y), no Python-only tricks.
"""

import os
import sys
import math
import heapq
import numpy as np
from PIL import Image, ImageDraw

np.seterr(over="ignore")   # uint32 hash wrap is intentional + deterministic

# ---------------------------------------------------------------- parameters
SEED = 1337
TILE_M = 1500.0         # overland hex pitch — the NATURAL scale (game compresses later)
WORLD_W = 72000.0       # world extent in meters (fixed across scales for the strip)
WORLD_H = 48000.0
SEA_LEVEL = 0.0
RIVER_ACC = 6           # DISPLAY threshold only (overlays) — geometry uses EVERY flow (7k)
MEANDER_K = 0.34        # fractal displacement strength
SEG_MIN_M = 84.0        # stop subdividing below this segment length
VALLEY_W = 138.0        # smallest valley falloff (m); per-river up to VALLEY_MAX
VALLEY_MAX = 390.0      # the biggest river carves this wide a falloff
CARVE_M = 120.0         # max valley depth (m) — ages of waterflow cut deep (7k)
RIPARIAN_W = 330.0      # moisture greening falloff (m)
APRON_M = 1680.0        # apron >= the HARD cutoffs (4*VALLEY_MAX, 3*RIPARIAN_W)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_overland")

# ===================== TERRAIN TUNING TABLE (play here) =====================
# Per terrain TWO independent numbers:
#   RISE  = general rise level: meters of ridge lift this terrain takes at a
#           reference tile-relief of 100 m (scales linearly with actual relief)
#   STEEP = internal steepness: meters of detail-noise amplitude (jaggedness);
#           also decides who WINS a boundary (steeper wins, via sqrt(STEEP))
# Globals below: how much steep NEIGHBOR tiles enhance each other.
#                 name      base RGB        RISE   STEEP
MATS = [
    ("sea",    ( 38,  84, 142),   0.0,   1.5),
    ("lake",   ( 50, 100, 150),   0.0,   2.0),
    ("sand",   (198, 182, 134),   4.0,   1.5),
    ("plain",  (124, 152,  84),  10.0,   2.5),
    ("forest", ( 62, 106,  58),  16.0,   5.0),
    ("hill",   (134, 128,  88),  80.0,  50.0),
    ("rock",   (128, 124, 118), 140.0,  98.0),
    ("snow",   (232, 236, 240), 170.0, 150.0),
]
NEIGHBOR_BASE = 0.6     # relief multiplier with zero steep neighbors
NEIGHBOR_BOOST = 0.2    # ADDED per steep neighbor (the enhance-each-other factor)
STEEP_DELTA = 60.0      # height delta (m) that counts a neighbor as steep
M_SEA, M_LAKE, M_SAND, M_PLAIN, M_FOREST, M_HILL, M_ROCK, M_SNOW = range(8)

SQ3 = math.sqrt(3.0)

# ------------------------------------------------------------ hashed noise
# Pure (seed, ix, iy, ch) -> [0,1).  uint32 wrap is deterministic & portable.
def _mix(n):
    n = (n ^ (n >> np.uint32(13))) * np.uint32(1274126177)
    return n ^ (n >> np.uint32(16))

def hash01(ix, iy, ch):
    ix = np.asarray(ix, dtype=np.int64).astype(np.uint32)
    iy = np.asarray(iy, dtype=np.int64).astype(np.uint32)
    n = (ix * np.uint32(73856093)) ^ (iy * np.uint32(19349663)) \
        ^ (np.uint32(ch) * np.uint32(83492791)) ^ np.uint32(SEED * 2654435761 & 0xFFFFFFFF)
    return _mix(n).astype(np.float64) / 4294967296.0

def value_noise(xs, ys, wl, ch):
    """Bilinear value noise, wavelength wl meters, channel ch. xs/ys in meters."""
    u = xs / wl
    v = ys / wl
    iu = np.floor(u).astype(np.int64)
    iv = np.floor(v).astype(np.int64)
    fu = u - iu
    fv = v - iv
    fu = fu * fu * (3.0 - 2.0 * fu)   # smoothstep
    fv = fv * fv * (3.0 - 2.0 * fv)
    a = hash01(iu,     iv,     ch)
    b = hash01(iu + 1, iv,     ch)
    c = hash01(iu,     iv + 1, ch)
    d = hash01(iu + 1, iv + 1, ch)
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv

def fbm(xs, ys, wl0, octaves, ch):
    """Fractal sum in [-1, 1]-ish."""
    out = np.zeros_like(np.asarray(xs, dtype=np.float64))
    amp, wl, tot = 1.0, wl0, 0.0
    for o in range(octaves):
        out = out + amp * (value_noise(xs, ys, wl, ch * 16 + o) * 2.0 - 1.0)
        tot += amp
        amp *= 0.5
        wl *= 0.5
    return out / tot

# ------------------------------------------------------- overland lattice
class Overland:
    """The coarse truth: per-cell record {material, height, water level+dir, acc}."""

    def __init__(self, tile_m):
        self.hw = tile_m                      # horizontal pitch
        self.r = tile_m / SQ3                 # circumradius (pointy-top)
        self.vs = 1.5 * self.r                # vertical pitch
        self.nx = int(WORLD_W / self.hw) + 1
        self.ny = int(WORLD_H / self.vs) + 1
        self.h = np.zeros((self.ny, self.nx))         # height (m)
        self.mat = np.zeros((self.ny, self.nx), int)
        self.moist = np.zeros((self.ny, self.nx))
        self.flow = np.full((self.ny, self.nx), -1, int)   # 0..5 neighbor index, -1 none
        self.acc = np.ones((self.ny, self.nx))
        self._gen()

    def center(self, c, r):
        return ((c + 0.5 * (r & 1)) * self.hw, r * self.vs)

    def neighbors(self, c, r):
        if r & 1:
            off = ((1, 0), (-1, 0), (1, -1), (0, -1), (1, 1), (0, 1))
        else:
            off = ((1, 0), (-1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))
        return [(c + dc, r + dr) for (dc, dr) in off]

    def _gen(self):
        # heights sampled IN WORLD METERS -> the same continent at every tile scale
        C, R = np.meshgrid(np.arange(self.nx), np.arange(self.ny))
        X = (C + 0.5 * (R & 1)) * self.hw
        Y = R * self.vs
        n = fbm(X, Y, 22500.0, 6, 7)
        ridge = 1.0 - np.abs(fbm(X, Y, 33000.0, 3, 23))   # ridged noise
        # broad continent, sea at the rim; DOMAIN-WARPED rim -> bays + peninsulas
        dx = (X - WORLD_W * 0.42) / (WORLD_W * 0.50)
        dy = (Y - WORLD_H * 0.48) / (WORLD_H * 0.58)
        rad = np.maximum(0.0, np.sqrt(dx * dx + dy * dy) + 0.30 * fbm(X, Y, 18000.0, 3, 31))
        # SEVERAL massifs (not one dome) -> basins between them CONVERGE drainage;
        # positions hash-jittered by the seed so each world has its own bones
        self.h = 380.0 * n + 170.0 - 1000.0 * rad ** 2.6
        for k, (fx, fy, sx, sy, amp) in enumerate(((0.28, 0.30, 0.10, 0.16, 980.0),
                                                   (0.40, 0.66, 0.11, 0.14, 920.0),
                                                   (0.58, 0.26, 0.09, 0.13, 860.0),
                                                   (0.52, 0.50, 0.05, 0.07, 420.0))):
            fx = fx + (float(hash01(k, 1, 51)) - 0.5) * 0.16
            fy = fy + (float(hash01(k, 2, 52)) - 0.5) * 0.16
            g = np.exp(-((X - WORLD_W * fx) / (WORLD_W * sx)) ** 2
                       - ((Y - WORLD_H * fy) / (WORLD_H * sy)) ** 2)
            self.h = self.h + amp * ridge * g
        self.moist = 0.5 + 0.5 * fbm(X, Y, 15600.0, 3, 11)
        # PRIORITY-FLOOD pit fill: every land cell drains to the sea; cells the
        # flood raised noticeably sit in depressions -> true lakes.
        filled = self.h.copy()
        seen = np.zeros((self.ny, self.nx), bool)
        pq = []
        for r in range(self.ny):
            for c in range(self.nx):
                edge = r in (0, self.ny - 1) or c in (0, self.nx - 1)
                if self.h[r, c] <= SEA_LEVEL or edge:
                    heapq.heappush(pq, (self.h[r, c], c, r))
                    seen[r, c] = True
        while pq:
            lvl, c, r = heapq.heappop(pq)
            for nc, nr in self.neighbors(c, r):
                if 0 <= nc < self.nx and 0 <= nr < self.ny and not seen[nr, nc]:
                    seen[nr, nc] = True
                    filled[nr, nc] = max(self.h[nr, nc], lvl + 0.05)
                    heapq.heappush(pq, (filled[nr, nc], nc, nr))
        is_lake = (filled > self.h + 4.0)
        self.h = filled
        # flow: steepest descent on the filled surface — no pits remain
        order = []
        for r in range(self.ny):
            for c in range(self.nx):
                if self.h[r, c] <= SEA_LEVEL:
                    continue
                best, bi = self.h[r, c], -1
                for i, (nc, nr) in enumerate(self.neighbors(c, r)):
                    if 0 <= nc < self.nx and 0 <= nr < self.ny and self.h[nr, nc] < best:
                        best, bi = self.h[nr, nc], i
                self.flow[r, c] = bi
                order.append((self.h[r, c], c, r))
        # accumulation: high cells drain first
        order.sort(reverse=True)
        for _, c, r in order:
            bi = self.flow[r, c]
            if bi >= 0:
                nc, nr = self.neighbors(c, r)[bi]
                self.acc[nr, nc] += self.acc[r, c]
        # in-tile VERTICALITY input: a cell's relief = max height delta to its
        # neighbors — but WATER-FLOW cells (rivers/lakes/sea) contribute ZERO,
        # so the dry land rises around them and the water cuts deep for free.
        self.wet = (self.h <= SEA_LEVEL) | is_lake
        self.relief = np.zeros((self.ny, self.nx))
        for r in range(self.ny):
            for c in range(self.nx):
                if self.wet[r, c]:
                    continue
                m, nsteep, nbacc = 0.0, 0, 0.0
                for nc, nr in self.neighbors(c, r):
                    if 0 <= nc < self.nx and 0 <= nr < self.ny:
                        d = abs(self.h[r, c] - self.h[nr, nc])
                        m = max(m, d)
                        if d > STEEP_DELTA:
                            nsteep += 1
                        nbacc = max(nbacc, self.acc[nr, nc])
                # MORE steep neighbors -> the effect compounds (a cell ringed by
                # steep terrain soars; one steep contact only lifts moderately)
                rel = m * (NEIGHBOR_BASE + NEIGHBOR_BOOST * nsteep)
                # GRADED water mitigation (naturalization): sizable rivers flatten
                # their own cell; BIG rivers flatten their shoulders too — corridor
                # width grows with size.  Small streams keep their relief: gorges.
                s_self = min(1.0, max(0.0, (self.acc[r, c] - 8.0) / 16.0))
                s_nb = min(1.0, max(0.0, (nbacc - 20.0) / 60.0))
                self.relief[r, c] = rel * (1.0 - max(s_self, 0.85 * s_nb))
        # materials
        for r in range(self.ny):
            for c in range(self.nx):
                h, m = self.h[r, c], self.moist[r, c]
                if h <= SEA_LEVEL:
                    self.mat[r, c] = M_SEA
                elif is_lake[r, c]:
                    self.mat[r, c] = M_LAKE
                elif h < 9.0:
                    self.mat[r, c] = M_SAND
                elif h > 640.0:
                    self.mat[r, c] = M_SNOW if h > 800.0 else M_ROCK
                elif h > 330.0:
                    self.mat[r, c] = M_HILL
                else:
                    self.mat[r, c] = M_FOREST if m > 0.55 else M_PLAIN

    # -------------------------------------- river course anchors (the user rule)
    # A river NEVER exits through the middle of a tile side: each shared edge
    # carries one canonical random BIT choosing a crossing point more-left or
    # more-right of the side.  Both tiles hash the same (sorted) cell pair ->
    # the same point -> seamless.  Inside the tile the course routes via a
    # hash-jittered interior CONTROL point (also the natural confluence spot);
    # only BELOW that does the fractal displacement work.
    def _cellhash(self, c1, r1, c2, r2, ch):
        n = (c1 * 73856093 ^ r1 * 19349663 ^ c2 * 83492791 ^ r2 * 2971215073
             ^ ch * 668265263 ^ SEED * 2654435761) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 4294967296.0

    def edge_cross(self, ca, ra, cb, rb):
        """The crossing point on the shared edge of two adjacent tiles."""
        a, b = (ca, ra), (cb, rb)
        (c1, r1), (c2, r2) = (a, b) if a <= b else (b, a)
        x1, y1 = self.center(c1, r1)
        x2, y2 = self.center(c2, r2)
        mx, my = (x1 + x2) * 0.5, (y1 + y2) * 0.5
        d = math.hypot(x2 - x1, y2 - y1)
        px, py = -(y2 - y1) / d, (x2 - x1) / d        # along the edge
        bit = self._cellhash(c1, r1, c2, r2, 5) < 0.5  # THE left/right bit
        off = (-0.30 if bit else 0.30) * self.r        # side length = r
        return (mx + px * off, my + py * off)

    def control_pt(self, c, r):
        """Interior routing point of a tile (jittered off-center, canonical)."""
        cx, cy = self.center(c, r)
        jx = (self._cellhash(c, r, c, r, 6) - 0.5) * 0.8 * self.r
        jy = (self._cellhash(c, r, c, r, 7) - 0.5) * 0.8 * self.r
        return (cx + jx, cy + jy)

    def river_paths(self):
        """Cell chains head->mouth with per-cell accumulation."""
        is_river = (self.acc >= RIVER_ACC) & (self.h > SEA_LEVEL)
        feeds = np.zeros_like(is_river)
        for r in range(self.ny):
            for c in range(self.nx):
                if is_river[r, c] and self.flow[r, c] >= 0:
                    nc, nr = self.neighbors(c, r)[self.flow[r, c]]
                    if 0 <= nc < self.nx and 0 <= nr < self.ny and is_river[nr, nc]:
                        feeds[nr, nc] = True
        paths = []
        for r in range(self.ny):
            for c in range(self.nx):
                if not is_river[r, c] or feeds[r, c]:
                    continue                       # heads only
                cells, cc, rr = [], c, r
                while True:
                    cells.append((cc, rr))
                    bi = self.flow[rr, cc]
                    if bi < 0:
                        break                      # lake mouth
                    nc, nr = self.neighbors(cc, rr)[bi]
                    if not (0 <= nc < self.nx and 0 <= nr < self.ny):
                        break
                    if self.h[nr, nc] <= SEA_LEVEL:
                        cells.append((nc, nr))     # one step into the sea
                        break
                    cc, rr = nc, nr
                if len(cells) >= 3:
                    paths.append(cells)
        return paths

    def coarse_course(self, cells):
        """Anchor polyline: control pt -> edge crossing -> control pt -> ...
        with per-vertex accumulation. Pure function of the overland data."""
        pts, accs = [], []
        for i, (c, r) in enumerate(cells):
            if i > 0:
                pc, pr = cells[i - 1]
                pts.append(self.edge_cross(pc, pr, c, r))
                accs.append(float(self.acc[pr, pc]))
            pts.append(self.control_pt(c, r))
            accs.append(float(self.acc[r, c]))
        return pts, accs

# ------------------------------------------------ coarse field blend (seamless)
def blend_fields(ov, xs, ys):
    """Smooth kernel blend of the overland cells around each point.
    Returns dicts of blended fields. Pure (cells, x, y) -> values; C1-continuous,
    so two adjacent tiles merge seamlessly by construction."""
    xs = np.asarray(xs, dtype=np.float64)
    ys = np.asarray(ys, dtype=np.float64)
    rk = ov.hw * 1.02                       # kernel radius: covers >=3 centers anywhere
    ry0 = np.round(ys / ov.vs).astype(np.int64)
    acc = {k: np.zeros_like(xs) for k in ("w", "h", "moist", "watery", "lakey", "relief")}
    wmax = np.zeros_like(xs)
    wm = np.zeros((len(MATS),) + xs.shape)  # per-MATERIAL weight (the contest input)
    for dr in (-1, 0, 1):
        r = ry0 + dr
        off = 0.5 * (r & 1)
        c0 = np.floor(xs / ov.hw - off).astype(np.int64)
        for dc in (-1, 0, 1, 2):
            c = c0 + dc
            cx = (c + off) * ov.hw
            cy = r * ov.vs
            d2 = (xs - cx) ** 2 + (ys - cy) ** 2
            w = np.maximum(0.0, 1.0 - d2 / (rk * rk)) ** 2
            ci = np.clip(c, 0, ov.nx - 1)
            ri = np.clip(r, 0, ov.ny - 1)
            mat = ov.mat[ri, ci]
            acc["w"] += w
            acc["h"] += w * ov.h[ri, ci]
            acc["moist"] += w * ov.moist[ri, ci]
            acc["watery"] += w * ((mat == M_LAKE) | (mat == M_SEA))
            acc["lakey"] += w * (mat == M_LAKE)
            acc["relief"] += w * ov.relief[ri, ci]
            for m in range(len(MATS)):
                wm[m] += w * (mat == m)
            wmax = np.maximum(wmax, w)
    iw = 1.0 / np.maximum(acc["w"], 1e-12)
    out = {k: acc[k] * iw for k in acc if k != "w"}
    out["wm"] = wm * iw[None]
    # GEOLOGY (user model): cells are CATCHMENTS — rivers run the centers, so
    # the watershed runs the rim and the CORNERS are the summits.  rim = 0 at
    # a cell center, ~1 at a triple point; smooth + seamless by construction.
    out["rim"] = np.clip((1.0 - wmax * iw) / 0.667, 0.0, 1.0)
    return out

LAND_MATS = (M_SAND, M_PLAIN, M_FOREST, M_HILL, M_ROCK, M_SNOW)

def material_contest(f, xs, ys):
    """The boundary-line contest (steeper wins). Returns (color, detail amp).
    ONE implementation — the renderer and the shoreline trim must agree."""
    scores = []
    for m in LAND_MATS:
        jit = 0.72 + 0.56 * (fbm(xs, ys, 1020.0, 3, 40 + m) * 0.5 + 0.5)
        scores.append(f["wm"][m] * math.sqrt(MATS[m][3]) * jit)
    S = np.stack(scores)
    i1 = np.argmax(S, axis=0)
    s1 = np.take_along_axis(S, i1[None], 0)[0]
    np.put_along_axis(S, i1[None], -1.0, 0)
    i2 = np.argmax(S, axis=0)
    s2 = np.take_along_axis(S, i2[None], 0)[0]
    tt = np.clip((s1 - s2) / (np.maximum(s1, 1e-9) * 0.18), 0, 1)  # thin smooth edge
    pal = np.array([MATS[m][1] for m in LAND_MATS], dtype=np.float64)
    steeps = np.array([MATS[m][3] for m in LAND_MATS], dtype=np.float64)
    rises = np.array([MATS[m][2] for m in LAND_MATS], dtype=np.float64)
    mt = 0.5 + 0.5 * tt
    matcol = pal[i1] * mt[..., None] + pal[i2] * (1 - mt)[..., None]
    steep_eff = steeps[i1] * mt + steeps[i2] * (1 - mt)
    rise_eff = rises[i1] * mt + rises[i2] * (1 - mt)
    return matcol, steep_eff, rise_eff

def detail_at(xs, ys):
    """Detail fbm with DOMAIN WARP: the sampling space is swirled by a second
    noise so the value-noise lattice never reads as a repeating pattern."""
    wx = fbm(xs, ys, 2100.0, 2, 80)
    wy = fbm(xs, ys, 2100.0, 2, 81)
    return fbm(xs + 720.0 * wx, ys + 720.0 * wy, 1260.0, 8, 3)

def ridge_at(xs, ys):
    """LOW-frequency ridged field (domain-warped, crest sharpened): roughly ONE
    combined crest per steep zone — peaks consolidate into ridgelines instead
    of speckling a slope with one peak per noise zero-crossing."""
    wxr = fbm(xs, ys, 4500.0, 2, 84)
    wyr = fbm(xs, ys, 4500.0, 2, 85)
    r = 1.0 - np.abs(fbm(xs + 900.0 * wxr, ys + 900.0 * wyr, 2850.0, 2, 86))
    return r * r * r   # sharp crests

def fine_height_of(f, steep_eff, rise_eff, detail, ridge):
    """Coarse blend + STEEP (detail jaggedness) + RISE anchored to the LATTICE
    GEOLOGY: tile centers are the valleys (the rivers run there), tile rims the
    watersheds, tile CORNERS the summits.  rim^1.5 shapes center->peak; the
    low-frequency ridge noise only VARIES the summit heights (0.35 floor so
    every high-relief corner still rises). Water tiles blend ZERO relief."""
    return f["h"] + steep_eff * detail \
        + rise_eff * (f["relief"] / 100.0) * (f["rim"] ** 1.5) * (0.35 + 0.65 * ridge)

def lake_field(f, xs, ys):
    """Lake contour field: the blended lake weight, fractally jittered so the
    shore is a ragged natural line, not a rounded hexagon union."""
    return f["lakey"] + 0.11 * fbm(xs, ys, 990.0, 4, 70)

def water_mask_at(ov, pts):
    """Is each point in sea/lake water? (pre-carve fine height + lake contour)"""
    xs = np.array([p[0] for p in pts], dtype=np.float64)
    ys = np.array([p[1] for p in pts], dtype=np.float64)
    f = blend_fields(ov, xs, ys)
    _, steep_eff, rise_eff = material_contest(f, xs, ys)
    h = fine_height_of(f, steep_eff, rise_eff, detail_at(xs, ys), ridge_at(xs, ys))
    return (h <= SEA_LEVEL) | (lake_field(f, xs, ys) >= 0.5)

def shore_cross(ov, dry, wet):
    """Bisect the exact shoreline crossing between a dry and a wet point."""
    for _ in range(9):
        mid = ((dry[0] + wet[0]) * 0.5, (dry[1] + wet[1]) * 0.5)
        if water_mask_at(ov, [mid])[0]:
            wet = mid
        else:
            dry = mid
    return ((dry[0] + wet[0]) * 0.5, (dry[1] + wet[1]) * 0.5)

def shape_factors(ov, pts):
    """Coarse height + slope at course points (vectorized) — valley SHAPE input."""
    xs = np.array([q[0] for q in pts], dtype=np.float64)
    ys = np.array([q[1] for q in pts], dtype=np.float64)
    e = 60.0
    f0 = blend_fields(ov, xs, ys)
    hx = blend_fields(ov, xs + e, ys)["h"] - blend_fields(ov, xs - e, ys)["h"]
    hy = blend_fields(ov, xs, ys + e)["h"] - blend_fields(ov, xs, ys - e)["h"]
    return f0["h"], np.sqrt(hx * hx + hy * hy) / (2 * e), f0["relief"]

def trim_to_shore(ov, fp, fv):
    """ATTACH the course to the water lines: split into land pieces whose ends
    lie exactly ON the sea/lake shoreline (in and out of lakes, into the sea)."""
    wet = water_mask_at(ov, fp)
    pieces, cur_p, cur_v = [], [], []
    for i in range(len(fp)):
        if not wet[i]:
            if not cur_p and i > 0:
                cur_p.append(shore_cross(ov, fp[i], fp[i - 1]))   # exit a water body
                cur_v.append(fv[i])
            cur_p.append(fp[i])
            cur_v.append(fv[i])
        elif cur_p:
            cur_p.append(shore_cross(ov, fp[i - 1], fp[i]))       # reach a water body
            cur_v.append(fv[i])
            if len(cur_p) >= 3:
                pieces.append((cur_p, cur_v))
            cur_p, cur_v = [], []
    if len(cur_p) >= 3:
        pieces.append((cur_p, cur_v))
    return pieces

def coarse_height(ov, x, y):
    return float(blend_fields(ov, np.array([x]), np.array([y]))["h"][0])

def coarse_slope(ov, x, y):
    e = 60.0
    hx = coarse_height(ov, x + e, y) - coarse_height(ov, x - e, y)
    hy = coarse_height(ov, x, y + e) - coarse_height(ov, x, y - e)
    return math.sqrt(hx * hx + hy * hy) / (2 * e)

# ------------------------------------------------ the fractal river course
def _dhash(ax, ay, bx, by, lvl):
    """Order-independent displacement hash of the QUANTIZED endpoints -> [0,1).
    Window-independent by construction: no traversal index anywhere."""
    a = (int(round(ax)) & 0xFFFFF, int(round(ay)) & 0xFFFFF)
    b = (int(round(bx)) & 0xFFFFF, int(round(by)) & 0xFFFFF)
    lo, hi = (a, b) if a <= b else (b, a)
    n = (lo[0] * 73856093 ^ lo[1] * 19349663 ^ hi[0] * 83492791
         ^ hi[1] * 2971215073 ^ lvl * 668265263 ^ SEED * 2654435761) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 4294967296.0

def chaikin(pts, n=2):
    """Deterministic corner-cutting: kills the hex lattice's 0/60-degree zigzag."""
    for _ in range(n):
        out = [pts[0]]
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            out.append((ax * 0.75 + bx * 0.25, ay * 0.75 + by * 0.25))
            out.append((ax * 0.25 + bx * 0.75, ay * 0.25 + by * 0.75))
        out.append(pts[-1])
        pts = out
    return pts

def meander_factor(ov, x, y):
    """Flat land winds, steep land runs straight; extra wind near sea level."""
    s = coarse_slope(ov, x, y)
    f = 0.12 + 0.88 * math.exp(-s / 0.00533)
    h = coarse_height(ov, x, y)
    if 0.0 < h < 60.0:
        f = min(1.25, f * (1.0 + 0.5 * (1.0 - h / 60.0)))
    return f

def displace(ov, pts, vals, lvl=0):
    """Recursive midpoint displacement; amplitude = seg_len * K * meander(mid)."""
    if lvl > 7:
        return pts, vals
    out_p, out_v = [], []
    moved = False
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        out_p.append((ax, ay))
        out_v.append(vals[i])
        seg = math.hypot(bx - ax, by - ay)
        if seg >= SEG_MIN_M * 2.0:
            moved = True
            mx, my = (ax + bx) * 0.5, (ay + by) * 0.5
            px, py = -(by - ay) / seg, (bx - ax) / seg
            d = (_dhash(ax, ay, bx, by, lvl) - 0.5) * 2.0 * seg * MEANDER_K \
                * meander_factor(ov, mx, my)
            out_p.append((mx + px * d, my + py * d))
            out_v.append((vals[i] + vals[i + 1]) * 0.5)
    out_p.append(pts[-1])
    out_v.append(vals[-1])
    if not moved:
        return out_p, out_v
    return displace(ov, out_p, out_v, lvl + 1)

def flow_links(ov):
    """The WHOLE flow tree as per-cell links (7k: every water flow counts):
    each land cell contributes ONE link control->edge-crossing->downstream
    control, carrying its accumulation.  No duplication; confluences meet at
    the shared control points by construction."""
    links = []
    for r in range(ov.ny):
        for c in range(ov.nx):
            if ov.h[r, c] <= SEA_LEVEL:
                continue
            bi = ov.flow[r, c]
            if bi < 0:
                continue
            nc, nr = ov.neighbors(c, r)[bi]
            if not (0 <= nc < ov.nx and 0 <= nr < ov.ny):
                continue
            a = ov.control_pt(c, r)
            e = ov.edge_cross(c, r, nc, nr)
            b = ov.control_pt(nc, nr)
            links.append(([a, e, b], float(ov.acc[r, c]), c, r))
    # STABILITY rule (user): bigger rivers are counted FIRST — a canonical
    # order, so contested pixels (tied distances, overlapping claims) always
    # resolve to the bigger water, independent of any scan order.
    links.sort(key=lambda L: (-L[1], L[3], L[2]))
    return [(anch, acc) for anch, acc, _, _ in links]

def fine_rivers(ov):
    """Every flow link as a fine course piece, its character decided by the
    TERRAIN AROUND each vertex (the naturalization rule): hilly stretches ->
    narrow deep gorge; open stretches -> wide water, broad floodplain, an
    alluvial band.  Accumulation only sets the water budget.
    Tuples: (pts, width, depth, vwid, alluv, rad)."""
    rivers = []
    for anchors, acc in flow_links(ov):
        fp, fv = displace(ov, anchors, [acc, acc, acc])
        fp = chaikin(fp, 1)
        fv = [acc] * len(fp)
        for pp, pv in trim_to_shore(ov, fp, fv):   # ends ON the shorelines
            h0, sl, rel = shape_factors(ov, pp)
            fs = np.minimum(1.0, sl / 0.0167)      # 0 = flat/open, 1 = steep
            open_ = 1.0 - fs
            relctx = np.clip(rel / 250.0, 0.0, 1.0)
            sq = math.sqrt(acc)
            base = 4.0 + 5.5 * sq
            # gorges where the surrounding land is steep/high (ages cut deep),
            # wide shallow floodplains on the open flats, and the near-sea
            # bonus: the carved mouth lets the SEA inland (the ria)
            depth = np.minimum(CARVE_M, base * (0.45 + 0.55 * fs) * (1.0 + 1.5 * relctx)
                               + base * 0.90 * np.exp(-np.maximum(h0, 0.0) / 14.0))
            # SUBTLE: brooks cut deep but NARROW (no landscape-wide veining);
            # only sizable water earns wide valleys and the alluvial floor
            vwid = np.minimum(VALLEY_MAX, (20.0 + 45.0 * sq) * (1.6 - 0.6 * fs))
            width = (1.0 + 1.7 * sq) * (0.3 + 0.7 * open_)   # terrain decides
            alluv = open_ * max(0.0, 75.0 * (sq - 1.4))      # the 7g floor band
            rad = float(4.0 * vwid.max() + alluv.max() + 60.0)
            rivers.append((pp, list(width), list(depth), list(vwid),
                           list(alluv), rad))
    return rivers

# ------------------------------------------------ chamfer distance transform
def chamfer_dt(mask):
    """Two-pass 3x4-style chamfer DT in PURE INTEGER arithmetic (costs 12/17):
    no float ulps -> bit-identical no matter the window extent. Returns px."""
    h, w = mask.shape
    big = np.int64(10 ** 12)
    d = np.where(mask, 0, big).astype(np.int64)
    ar12 = np.arange(w, dtype=np.int64) * 12

    def _hsweep(row):
        row = np.minimum.accumulate(row - ar12) + ar12
        rr = row[::-1]
        rr = np.minimum.accumulate(rr - ar12) + ar12
        return rr[::-1]

    for y in range(h):
        row = d[y]
        if y > 0:
            up = d[y - 1]
            row = np.minimum(row, up + 12)
            row = np.minimum(row, np.concatenate(([big], up[:-1])) + 17)
            row = np.minimum(row, np.concatenate((up[1:], [big])) + 17)
        d[y] = _hsweep(row)
    for y in range(h - 2, -1, -1):
        dn = d[y + 1]
        row = d[y]
        row = np.minimum(row, dn + 12)
        row = np.minimum(row, np.concatenate(([big], dn[:-1])) + 17)
        row = np.minimum(row, np.concatenate((dn[1:], [big])) + 17)
        d[y] = _hsweep(row)
    return d.astype(np.float64) / 12.0

# ------------------------------------------------ fine terrain of a window
def render_window(ov, rivers, x0, y0, wpx, hpx, px_m, borders=False, want_height=False):
    """Pure function of (overland, rivers, window) -> RGB array.
    Computes with an APRON of APRON_M and crops -> window independence holds."""
    ap = int(math.ceil(APRON_M / px_m))
    # EXACTNESS: snap the origin to the WORLD PIXEL GRID and keep all pixel
    # coordinates as (world/px_m - integer) — bit-identical across windows,
    # so rasterization (and the seam invariant) is exact, not ulp-lucky.
    kx, ky = round(x0 / px_m), round(y0 / px_m)
    x0, y0 = kx * px_m, ky * px_m
    W, H = wpx + 2 * ap, hpx + 2 * ap
    jj, ii = np.meshgrid(np.arange(W), np.arange(H))
    xs = (kx - ap + jj + 0.5) * px_m
    ys = (ky - ap + ii + 0.5) * px_m

    f = blend_fields(ov, xs, ys)
    detail = detail_at(xs, ys)
    lk = lake_field(f, xs, ys)

    # THE BOUNDARY-LINE RULE: between any two terrain types runs a crisp fractal
    # LINE, not a wide crossfade — and the STEEPER type wins the contested band
    # (bias by detail amplitude).  Heights stay continuous; only the material
    # claim is a winner-takes-it contest with fractally jittered scores.
    matcol, steep_eff, rise_eff = material_contest(f, xs, ys)
    height = fine_height_of(f, steep_eff, rise_eff, detail, ridge_at(xs, ys))

    # --- rivers: EXACT per-pixel distance to the nearest course segment.
    # No rasterization, no DT: per-pixel mins over floats that are identical in
    # every window (world coords), in fixed global segment order -> the seam
    # invariant holds STRUCTURALLY.  (The loft port rasterizes into fixed
    # world-anchored blocks instead, where exactness is automatic.)
    dist_m = np.full((H, W), 1e7)      # to the nearest course (water + riparian)
    wfield = np.zeros((H, W))
    afield = np.zeros((H, W))          # alluvial half-width at the nearest course
    carve = np.zeros((H, W))           # MAX of link carves: joints stay smooth
    ox, oy = kx - ap, ky - ap
    wx0, wy0 = ox * px_m, oy * px_m
    for fp, width, depth, vwid, alluv, rad in rivers:
        fxs = [q[0] for q in fp]
        fys = [q[1] for q in fp]
        jx0 = max(0, int((min(fxs) - rad - wx0) / px_m) - 1)
        jx1 = min(W, int((max(fxs) + rad - wx0) / px_m) + 2)
        jy0 = max(0, int((min(fys) - rad - wy0) / px_m) - 1)
        jy1 = min(H, int((max(fys) + rad - wy0) / px_m) + 2)
        if jx0 >= jx1 or jy0 >= jy1:
            continue
        pxs = xs[jy0:jy1, jx0:jx1]
        pys = ys[jy0:jy1, jx0:jx1]
        cd = np.full(pxs.shape, 1e7)   # this link's own distance field
        cdep = np.zeros(pxs.shape)
        cvw = np.full(pxs.shape, VALLEY_W)
        hit = False
        for i in range(len(fp) - 1):
            ax, ay = fp[i]
            bx, by = fp[i + 1]
            ex, ey = bx - ax, by - ay
            ee = ex * ex + ey * ey
            if ee < 1e-9:
                continue
            t = np.clip(((pxs - ax) * ex + (pys - ay) * ey) / ee, 0.0, 1.0)
            d = np.hypot(pxs - (ax + t * ex), pys - (ay + t * ey))
            upd = d < cd                     # first-in-order wins ties
            if not upd.any():
                continue
            hit = True
            cd = np.where(upd, d, cd)
            cdep = np.where(upd, depth[i] * (1.0 - t) + depth[i + 1] * t, cdep)
            cvw = np.where(upd, vwid[i] * (1.0 - t) + vwid[i + 1] * t, cvw)
            # the global nearest-course fields drive water width + riparian + 7g
            gd = dist_m[jy0:jy1, jx0:jx1]
            gupd = d < gd
            if gupd.any():
                dist_m[jy0:jy1, jx0:jx1] = np.where(gupd, d, gd)
                wv = width[i] * (1.0 - t) + width[i + 1] * t
                av = alluv[i] * (1.0 - t) + alluv[i + 1] * t
                wfield[jy0:jy1, jx0:jx1] = np.where(gupd, wv, wfield[jy0:jy1, jx0:jx1])
                afield[jy0:jy1, jx0:jx1] = np.where(gupd, av, afield[jy0:jy1, jx0:jx1])
        if hit:
            lc = cdep * np.exp(-cd / cvw) * np.clip(1.0 - cd / (4 * cvw), 0, 1)
            carve[jy0:jy1, jx0:jx1] = np.maximum(carve[jy0:jy1, jx0:jx1], lc)
    carve = np.minimum(carve, CARVE_M)

    # THE SHORELINE RULE: the coast is the fine height-zero contour, a lake shore
    # the wateriness contour — the river exists only LANDWARD of those lines.
    h_base = height.copy()                       # pre-carve land height
    height = height - carve
    # the river yields to the SEA where the carved valley floods (the ria/estuary)
    river_water = (dist_m < wfield * 0.5) & (height > SEA_LEVEL) \
                & (h_base > SEA_LEVEL) & (f["watery"] < 0.5)
    riparian = np.exp(-dist_m / RIPARIAN_W) * np.clip(1.0 - dist_m / (3 * RIPARIAN_W), 0, 1)
    riparian = riparian * np.clip((wfield - 1.2) / 5.0, 0.12, 1.0)   # size-gated

    # --- coloring
    col = matcol
    green = np.array([72.0, 122.0, 58.0])
    g = np.clip(riparian * 0.45 + np.clip(f["moist"] - 0.5, 0, 1) * 0.15, 0, 1)
    g = g * (height > SEA_LEVEL)
    col = col * (1 - g[..., None]) + green[None, None, :] * g[..., None]
    # the 7g ALLUVIAL FLOOR: inside a big river's open-valley band the flatter
    # material claims the ground — the river's own plain (color/claim only;
    # the heights already flattened via carve + graded relief suppression)
    am = np.clip(1.0 - dist_m / np.maximum(afield, 1.0), 0.0, 1.0) * 0.65
    am = am * (height > SEA_LEVEL)
    plaincol = np.array([124.0, 152.0, 84.0])
    col = col * (1 - am[..., None]) + plaincol[None, None, :] * am[..., None]
    # beach band hugs the fractal coastline; lake shores get their own sand rim
    beach = np.clip(1.0 - np.abs(h_base - 1.6) / 2.4, 0, 1) * (h_base > SEA_LEVEL)
    lshore = np.clip(1.0 - np.abs(lk - 0.43) / 0.07, 0, 1) * (h_base > SEA_LEVEL)
    beach = np.maximum(beach, lshore * 0.7)
    sand = np.array([201.0, 186.0, 140.0])
    col = col * (1 - beach[..., None] * 0.8) + sand[None, None, :] * (beach[..., None] * 0.8)
    # hillshade (light from NW)
    gy, gx = np.gradient(height, px_m)
    shade = np.clip(1.0 - (gx + gy) * 1.9, 0.55, 1.45)
    col = col * shade[..., None]
    # water: sea by fine height; lakes by blended wateriness; rivers by course
    seam = height <= SEA_LEVEL
    lake = (lk >= 0.5) & ~seam
    depth01 = np.clip(-height / 42.0, 0, 1)
    shallow = np.array([72.0, 132.0, 172.0])
    deep = np.array([22.0, 54.0, 102.0])
    seacol = shallow[None, None, :] * (1 - depth01[..., None]) + deep[None, None, :] * depth01[..., None]
    col = np.where(seam[..., None], seacol, col)
    # a lake is FILLED water: a FLAT level surface — no hillshade, no detail bumps
    col = np.where(lake[..., None], np.array([46.0, 96.0, 146.0])[None, None, :], col)
    rcol = np.array([50.0, 108.0, 158.0])
    rdepth = np.clip(carve / CARVE_M, 0.25, 1.0)
    col = np.where(river_water[..., None], rcol[None, None, :] * (1.15 - rdepth[..., None] * 0.45), col)
    # 7j: WHITEWATER — small steep streams step (falls in mountains, slides in
    # hills); big graded rivers never foam (they built their own beds)
    rapids = river_water & (np.hypot(gx, gy) > 0.022) & (wfield < 8.0)
    col = np.where(rapids[..., None], np.array([208.0, 222.0, 238.0])[None, None, :], col)

    dith = hash01(np.round(xs).astype(np.int64), np.round(ys).astype(np.int64), 91)
    col = col * (0.84 + 0.32 * dith)[..., None]
    img = np.clip(col, 0, 255).astype(np.uint8)[ap:ap + hpx, ap:ap + wpx]

    if borders:
        im = Image.fromarray(img)
        dr = ImageDraw.Draw(im, "RGBA")
        r0 = int((y0 - ov.r) / ov.vs) - 1
        r1 = int((y0 + hpx * px_m + ov.r) / ov.vs) + 2
        for r in range(max(0, r0), min(ov.ny, r1)):
            for c in range(ov.nx):
                cx, cy = ov.center(c, r)
                if cx < x0 - ov.hw or cx > x0 + wpx * px_m + ov.hw:
                    continue
                pts = []
                for k in range(7):
                    a = math.pi / 6 + k * math.pi / 3
                    pts.append(((cx + ov.r * math.cos(a) - x0) / px_m,
                                (cy + ov.r * math.sin(a) - y0) / px_m))
                dr.line(pts, fill=(255, 255, 255, 56), width=1)
        img = np.array(im)
    if want_height:
        return img, height[ap:ap + hpx, ap:ap + wpx]
    return img

def sample_terrain(ov, rivers, xs, ys):
    """Fine height + color + water at arbitrary world points (the SAME formulas
    as render_window — for profiles/transects)."""
    f = blend_fields(ov, xs, ys)
    detail = detail_at(xs, ys)
    matcol, steep_eff, rise_eff = material_contest(f, xs, ys)
    h = fine_height_of(f, steep_eff, rise_eff, detail, ridge_at(xs, ys))
    h_base = h.copy()
    dist = np.full(xs.shape, 1e7)
    wf = np.zeros(xs.shape)
    carve = np.zeros(xs.shape)
    bx0, bx1 = xs.min(), xs.max()
    by0, by1 = ys.min(), ys.max()
    for fp, width, depth, vwid, alluv, rad in rivers:
        fxs = [q[0] for q in fp]
        fys = [q[1] for q in fp]
        if max(fxs) + rad < bx0 or min(fxs) - rad > bx1:
            continue
        if max(fys) + rad < by0 or min(fys) - rad > by1:
            continue
        cd = np.full(xs.shape, 1e7)
        cdep = np.zeros(xs.shape)
        cvw = np.full(xs.shape, VALLEY_W)
        hit = False
        for i in range(len(fp) - 1):
            ax, ay = fp[i]
            bx, by = fp[i + 1]
            ex, ey = bx - ax, by - ay
            ee = ex * ex + ey * ey
            if ee < 1e-9:
                continue
            t = np.clip(((xs - ax) * ex + (ys - ay) * ey) / ee, 0.0, 1.0)
            d = np.hypot(xs - (ax + t * ex), ys - (ay + t * ey))
            upd = d < cd
            if not upd.any():
                continue
            hit = True
            cd = np.where(upd, d, cd)
            cdep = np.where(upd, depth[i] * (1 - t) + depth[i + 1] * t, cdep)
            cvw = np.where(upd, vwid[i] * (1 - t) + vwid[i + 1] * t, cvw)
            gupd = d < dist
            dist = np.where(gupd, d, dist)
            wf = np.where(gupd, width[i] * (1 - t) + width[i + 1] * t, wf)
        if hit:
            carve = np.maximum(carve, cdep * np.exp(-cd / cvw) * np.clip(1.0 - cd / (4 * cvw), 0, 1))
    h = h - np.minimum(carve, CARVE_M)
    lk = lake_field(f, xs, ys)
    river = (dist < wf * 0.5) & (h > SEA_LEVEL) & (h_base > SEA_LEVEL) & (f["watery"] < 0.5)
    water = (h <= SEA_LEVEL) | (lk >= 0.5) | river
    return h, matcol, water

def panel_profile(ov, rivers, fname):
    """Orthogonal SIDE VIEW (looking north): back-to-front strips of true fine
    heights — the verticality / valley-cut / estuary judge."""
    panels = []
    hot = np.unravel_index(np.argmax(ov.h), ov.h.shape)
    mx, my = pick_mouth(ov, rivers)
    cuts = ((ov.center(hot[1], hot[0])[0], ov.center(hot[1], hot[0])[1], "through the high massif"),
            (mx, my, "through the river mouth"))
    Wp, Hp, pz = 1500, 420, 3.2          # 3.2 m height per px
    span = 27000.0                        # 27 km wide window
    for cx, cy, label in cuts:
        x0 = min(max(0.0, cx - span / 2), WORLD_W - span)
        img = np.zeros((Hp, Wp, 3), np.uint8)
        img[:, :] = (16, 18, 24)
        xs = x0 + (np.arange(Wp) + 0.5) * (span / Wp)
        zrow = np.arange(Hp)
        for k in range(36, -1, -1):       # far -> near, strips 40 m apart
            yy = cy - 2160.0 + k * 120.0
            ys = np.full(Wp, yy)
            h, mc, wat = sample_terrain(ov, rivers, xs, ys)
            fade = 0.55 + 0.45 * (1.0 - k / 36.0)
            col = (mc * fade).astype(np.uint8)
            col[wat] = (np.array([60.0, 120.0, 170.0]) * fade).astype(np.uint8)
            hw = np.where(wat & (h <= SEA_LEVEL), 0.0, h)   # sea surface at 0
            top = np.clip(Hp - 40 - (hw / pz), 0, Hp - 1).astype(int)
            mask = zrow[:, None] >= top[None, :]
            img[mask] = np.repeat(col[None, :, :], Hp, 0)[mask]
        im = Image.fromarray(img)
        d2 = ImageDraw.Draw(im)
        sl = Hp - 40
        d2.line([(0, sl), (Wp, sl)], fill=(90, 140, 190), width=1)   # sea level
        d2.text((10, 8), "side view " + label + "  (27 km wide)", fill=(255, 255, 90))
        panels.append(im)
    sheet = Image.new("RGB", (Wp, Hp * 2 + 8), (0, 0, 0))
    for i, im in enumerate(panels):
        sheet.paste(im, (0, i * (Hp + 8)))
    sheet.save(fname)
    print("wrote " + fname)

def panel_view3d(ov, rivers, fname, wpx=1440, ck=0.55, hk=1.0 / 7.0,
                 caption="orthographic 3D miniature of the whole map "
                         "(24x16 km, height exaggerated)"):
    """Orthographic 3D relief model of the WHOLE map, viewed from the south
    (parallel projection, y-buffer painter). wpx/ck/hk size it: the default is
    the miniature; the `orthofull` mode renders the full-detail version."""
    pm = WORLD_W / float(wpx)
    Wg, Hg = wpx, int(WORLD_H / pm)
    img2d, hgt = render_window(ov, rivers, 0.0, 0.0, Wg, Hg, pm, want_height=True)
    im2 = Image.fromarray(img2d)             # bake the river overlay into the colors
    d2 = ImageDraw.Draw(im2)
    for fp, width, _, _, _, _ in rivers:
        if max(width) < 4.0:
            continue
        for i in range(len(fp) - 1):
            wpx2 = max(1, int(round(width[i] / pm * 1.6)))
            d2.line([(fp[i][0] / pm, fp[i][1] / pm),
                     (fp[i + 1][0] / pm, fp[i + 1][1] / pm)],
                    fill=(40, 96, 150), width=wpx2)
    img2d = np.array(im2)
    hgt = np.maximum(hgt, 0.0)               # water surfaces at sea level
    top_off = int(hgt.max() * hk) + 10
    Himg = int(Hg * ck) + top_off + 16
    out = np.zeros((Himg, Wg, 3), np.uint8)
    out[:, :] = (12, 14, 18)
    ybuf = np.full(Wg, Himg - 1, np.int64)
    cols = np.arange(Wg)
    for r in range(Hg - 1, -1, -1):          # NEAR -> FAR with occlusion buffer
        sy = np.clip((r * ck + top_off - hgt[r, :] * hk).astype(np.int64), 0, Himg - 1)
        lens = ybuf - sy
        if not (lens > 0).any():
            continue
        color = img2d[r, :, :]
        kmax = int(lens.max())
        for k in range(kmax):
            m = lens > k
            out[sy[m] + k, cols[m]] = color[m]
        ybuf = np.minimum(ybuf, sy)
    im = Image.fromarray(out)
    ImageDraw.Draw(im).text((10, 8), caption, fill=(255, 255, 90))
    im.save(fname)
    print("wrote " + fname)

# --------------------------------------------------------------- panels
def panel_overland(ov, fname):
    sc = 26.0 / (ov.hw / 500.0)    # px per tile, scale-aware
    s = sc / ov.hw
    W, H = int(WORLD_W * s) + 40, int(WORLD_H * s) + 40
    im = Image.new("RGB", (W, H), (12, 14, 18))
    dr = ImageDraw.Draw(im)
    hexpts = [(math.cos(math.pi / 6 + k * math.pi / 3),
               math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
    for r in range(ov.ny):
        for c in range(ov.nx):
            cx, cy = ov.center(c, r)
            px, py = cx * s + 20, cy * s + 20
            base = np.array(MATS[ov.mat[r, c]][1], float)
            li = 0.72 + 0.5 * max(0.0, min(1.0, ov.h[r, c] / 900.0))
            col = tuple(int(min(255, v * li)) for v in base)
            dr.polygon([(px + ov.r * s * a, py + ov.r * s * b) for a, b in hexpts],
                       fill=col, outline=(30, 32, 36))
    # the coarse anchor courses (control pts + edge-bit crossings) on top
    for cells in ov.river_paths():
        pts, accs = ov.coarse_course(cells)
        for i in range(len(pts) - 1):
            wpx2 = max(1, int(math.sqrt(accs[i]) * 0.55))
            dr.line([(pts[i][0] * s + 20, pts[i][1] * s + 20),
                     (pts[i + 1][0] * s + 20, pts[i + 1][1] * s + 20)],
                    fill=(60, 120, 190), width=wpx2)
    im.save(fname)
    print(f"wrote {fname}  ({ov.nx}x{ov.ny} tiles @ {ov.hw:.0f} m)")

def pick_mouth(ov, rivers):
    """The biggest river's last-land vertex — the meander showcase spot."""
    best, spot = -1.0, (WORLD_W / 2, WORLD_H / 2)
    for fp, width, _, _, _, _ in rivers:
        if width[-1] > best:
            best = width[-1]
            spot = fp[max(0, len(fp) - 1 - len(fp) // 4)]   # a bit inland of the mouth
    return spot

def main():
    os.makedirs(OUT, exist_ok=True)
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    ov = Overland(TILE_M)
    rivers = fine_rivers(ov)
    print(f"overland {ov.nx}x{ov.ny} tiles, {len(rivers)} river courses")

    if what in ("overland", "all"):
        panel_overland(ov, os.path.join(OUT, "overland_map.png"))

    if what in ("world", "all"):
        # the WHOLE map through the fine pipeline — general forms at a glance
        pm = WORLD_W / 1500.0
        img = render_window(ov, rivers, 0.0, 0.0, 1500, int(WORLD_H / pm), pm,
                            borders=False)
        im = Image.fromarray(img)
        dr = ImageDraw.Draw(im)
        for fp, width, _, _, _, _ in rivers:      # map-layer overlay: courses stay visible
            if max(width) < 4.0:
                continue
            for i in range(len(fp) - 1):
                wpx2 = max(1, int(round(width[i] / pm * 1.6)))
                dr.line([(fp[i][0] / pm, fp[i][1] / pm),
                         (fp[i + 1][0] / pm, fp[i + 1][1] / pm)],
                        fill=(40, 96, 150), width=wpx2)
        im.save(os.path.join(OUT, "world_fine.png"))
        print(f"wrote world_fine.png  full {WORLD_W/1000:.0f}x{WORLD_H/1000:.0f} km @{pm:.0f} m/px")

    if what in ("fine", "all"):
        mx, my = pick_mouth(ov, rivers)
        x0 = min(max(0.0, mx - 7800.0), WORLD_W - 10800.0)
        y0 = min(max(0.0, my - 4500.0), WORLD_H - 7800.0)
        img = render_window(ov, rivers, x0, y0, 1500, 1080, 7.2, borders=True)
        Image.fromarray(img).save(os.path.join(OUT, "fine_blend.png"))
        print(f"wrote fine_blend.png  window ({x0:.0f},{y0:.0f}) 3.6x2.6 km @2.4 m/px")

    if what in ("mouth", "all"):
        mx, my = pick_mouth(ov, rivers)
        x0 = min(max(0.0, mx - 2700.0), WORLD_W - 5400.0)
        y0 = min(max(0.0, my - 2700.0), WORLD_H - 5400.0)
        img = render_window(ov, rivers, x0, y0, 900, 900, 3.6, borders=False)
        Image.fromarray(img).save(os.path.join(OUT, "mouth_closeup.png"))
        print(f"wrote mouth_closeup.png  window ({x0:.0f},{y0:.0f}) 1.1x1.1 km @1.2 m/px")

    if what in ("seam", "all"):
        # THE invariant, executed: whole window vs four independent quadrants.
        mx, my = pick_mouth(ov, rivers)
        x0 = min(max(0.0, mx - 4200.0), WORLD_W - 6600.0)
        y0 = min(max(0.0, my - 3300.0), WORLD_H - 5400.0)
        wpx, hpx, pm = 720, 560, 7.2
        whole = render_window(ov, rivers, x0, y0, wpx, hpx, pm)
        tiles = np.zeros_like(whole)
        for qy in range(2):
            for qx in range(2):
                qw, qh = wpx // 2, hpx // 2
                qimg = render_window(ov, rivers, x0 + qx * qw * pm, y0 + qy * qh * pm,
                                     qw, qh, pm)
                tiles[qy * qh:(qy + 1) * qh, qx * qw:(qx + 1) * qw] = qimg
        same = np.array_equal(whole, tiles)
        diff = int(np.abs(whole.astype(int) - tiles.astype(int)).max())
        Image.fromarray(whole).save(os.path.join(OUT, "seam_whole.png"))
        Image.fromarray(tiles).save(os.path.join(OUT, "seam_tiled.png"))
        print(f"SEAM TEST: byte-identical={same} maxdiff={diff} "
              + ("=== SEAMLESS OK ===" if same else "=== FAIL ==="))

    if what == "seeds":
        # contact sheet: four worlds, same algorithm — pick the form direction
        global SEED
        cells = []
        for sd in (1337, 7, 99, 2026):
            SEED = sd
            o2 = Overland(TILE_M)
            r2 = fine_rivers(o2)
            pm = WORLD_W / 750.0
            img = render_window(o2, r2, 0.0, 0.0, 750, int(WORLD_H / pm), pm)
            im = Image.fromarray(img)
            d2 = ImageDraw.Draw(im)
            for fp, width, _, _, _, _ in r2:
                if max(width) < 4.0:
                    continue
                for i in range(len(fp) - 1):
                    wpx2 = max(1, int(round(width[i] / pm * 1.6)))
                    d2.line([(fp[i][0] / pm, fp[i][1] / pm),
                             (fp[i + 1][0] / pm, fp[i + 1][1] / pm)],
                            fill=(40, 96, 150), width=wpx2)
            d2.text((10, 8), f"seed {sd}", fill=(255, 255, 90))
            cells.append(im)
            print(f"  seed {sd}: {len(r2)} courses")
        hh = cells[0].size[1]
        sheet = Image.new("RGB", (750 * 2 + 8, hh * 2 + 8), (0, 0, 0))
        for i, im in enumerate(cells):
            sheet.paste(im, ((i % 2) * 758, (i // 2) * (hh + 8)))
        sheet.save(os.path.join(OUT, "world_seeds.png"))
        print("wrote world_seeds.png")

    if what in ("view3d", "all"):
        panel_view3d(ov, rivers, os.path.join(OUT, "ortho_3d.png"))

    if what in ("orthofull",):
        # the FULL orthographic render — the whole island at fine-pipeline detail
        panel_view3d(ov, rivers, os.path.join(OUT, "ortho_3d_full.png"),
                     wpx=2880, ck=0.7, hk=1.0 / 5.0,
                     caption="orthographic 3D of the whole map, full detail "
                             "(24x16 km, height exaggerated)")
        print("wrote ortho_3d_full.png")

    if what in ("profile", "all"):
        panel_profile(ov, rivers, os.path.join(OUT, "side_profile.png"))

    if what in ("strip", "all"):
        # the scale dial: same continent at 1500/500/300 m tiles
        panels = []
        for tm in (1500.0, 500.0, 300.0):
            o2 = Overland(tm)
            r2 = fine_rivers(o2)
            mx, my = pick_mouth(o2, r2)
            x0 = min(max(0.0, mx - 1300.0), WORLD_W - 2400.0)
            y0 = min(max(0.0, my - 1000.0), WORLD_H - 1900.0)
            img = render_window(o2, r2, x0, y0, 760, 600, 3.0, borders=True)
            im = Image.fromarray(img)
            ImageDraw.Draw(im).text((10, 8), f"{tm:.0f} m tiles", fill=(255, 255, 90))
            panels.append(im)
        strip = Image.new("RGB", (760 * 3 + 16, 600), (0, 0, 0))
        for i, p in enumerate(panels):
            strip.paste(p, (i * (760 + 8), 0))
        strip.save(os.path.join(OUT, "scale_strip.png"))
        print("wrote scale_strip.png (1500 / 500 / 300 m)")

if __name__ == "__main__":
    main()
