#!/usr/bin/env python3
"""trimesh.py — the triangle-vertex DATAPOINT evaluation for plan #1.

Each 1.5 km hex is a center-fan: every side is split into 3, so each side gives 3
triangles → 18 triangles / hex, over 19 vertices (center + 6 corners + 12 edge-thirds).
Heights live at these vertices, NOT at hex centers.

Design-protocol I-MESH (watertight): a corner is shared by 3 hexes, an edge-third by 2.
The shared vertex must carry ONE height or the mesh cracks. We guarantee it by computing
every vertex from its WORLD POSITION and dedup'ing on a 1 mm key — so a shared vertex is
literally the same datapoint, sampled once.

Run `python3 trimesh.py` to build the 40x40 mesh, verify I-MESH, and dump one hex.
`build(cols, rows)` returns the evaluation for the fetch/render steps to populate.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortler_import as oi          # geometry single-source (_OV, world_to_latlon)
import numpy as np

R = oi._OV.r                                  # circumradius (m) = TILE_M/sqrt(3)
ANG = [math.radians(30 + 60 * k) for k in range(6)]   # pointy-top corner angles

def hex_corners(cx, cy):
    return [(cx + R * math.cos(a), cy + R * math.sin(a)) for a in ANG]

def hex_vertices(c, r):
    """19 datapoints: index 0 = center, 1..6 = corners k, then per side k the two
    edge-thirds at 7+2k (1/3) and 8+2k (2/3)."""
    cx, cy = oi._OV.center(c, r)
    cor = hex_corners(cx, cy)
    v = [(cx, cy)]
    v += cor
    for k in range(6):
        ax, ay = cor[k]; bx, by = cor[(k + 1) % 6]
        v.append((ax + (bx - ax) / 3.0, ay + (by - ay) / 3.0))
        v.append((ax + (bx - ax) * 2.0 / 3.0, ay + (by - ay) * 2.0 / 3.0))
    return v                                   # 1 + 6 + 12 = 19

def fan_triangles():
    """18 triangles as local indices into the 19-vertex list (the side-÷3 fan)."""
    t = []
    for k in range(6):
        ck, ck1 = 1 + k, 1 + (k + 1) % 6
        ea, eb = 7 + 2 * k, 8 + 2 * k
        t += [(0, ck, ea), (0, ea, eb), (0, eb, ck1)]
    return t                                   # 18

def _key(wx, wy):
    return (round(wx, 3), round(wy, 3))        # 1 mm dedup => watertight sharing

def _tri_area(p, q, s):
    return abs((q[0]-p[0])*(s[1]-p[1]) - (s[0]-p[0])*(q[1]-p[1])) / 2.0

class TriMesh:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.verts = []          # unique (wx, wy)
        self.key2id = {}
        self.hex_tris = {}       # (c,r) -> list of 18 (id,id,id)
        self.refcount = []       # how many hexes reference each vertex
        self.height = None       # i16 metres per vertex, filled by the fetch step
        self._build()

    def _vid(self, wx, wy):
        k = _key(wx, wy)
        i = self.key2id.get(k)
        if i is None:
            i = len(self.verts); self.key2id[k] = i
            self.verts.append((wx, wy)); self.refcount.append(0)
        return i

    def _build(self):
        loc = fan_triangles()
        for r in range(self.rows):
            for c in range(self.cols):
                ids = [self._vid(wx, wy) for (wx, wy) in hex_vertices(c, r)]
                for i in set(ids):
                    self.refcount[i] += 1
                self.hex_tris[(c, r)] = [(ids[a], ids[b], ids[d]) for (a, b, d) in loc]

    def latlon(self, vid):
        return oi.world_to_latlon(*self.verts[vid])

def build(cols=oi.COLS, rows=oi.ROWS):
    return TriMesh(cols, rows)

# ----------------------------- verify (I-MESH) -----------------------------
def main():
    m = build()
    nh = m.cols * m.rows
    print(f"=== triangle-vertex datapoint evaluation ({m.cols}x{m.rows} = {nh} hexes) ===")
    print(f"[counts] unique vertices = {len(m.verts)};  triangles = {sum(len(t) for t in m.hex_tris.values())}"
          f" (want {18*nh})")

    # I-MESH watertight: an INTERIOR hex's corners are shared by 3, edge-thirds by 2.
    ids = {}                          # role -> sample vid, from interior hex (20,20)
    cx, cy = oi._OV.center(20, 20)
    hv = hex_vertices(20, 20)
    corner_refs = [m.refcount[m.key2id[_key(*hv[1 + k])]] for k in range(6)]
    edge_refs = [m.refcount[m.key2id[_key(*hv[7 + j])]] for j in range(12)]
    center_ref = m.refcount[m.key2id[_key(*hv[0])]]
    imesh = (center_ref == 1 and set(corner_refs) == {3} and set(edge_refs) == {2})
    print(f"[I-MESH @(20,20)] center ref={center_ref} (want 1); corners={corner_refs} (want all 3);"
          f" edges={set(edge_refs)} (want {{2}})  -> {'OK' if imesh else 'FAIL'}")

    # the fan exactly tiles the hex: sum of 18 triangle areas == hexagon area
    hexA = sum(_tri_area((cx, cy), hex_corners(cx, cy)[k], hex_corners(cx, cy)[(k+1) % 6])
               for k in range(6))
    fanA = 0.0
    P = hv
    for (a, b, d) in fan_triangles():
        fanA += _tri_area(P[a], P[b], P[d])
    tile = abs(fanA - hexA) < 1e-3
    print(f"[tiling @(20,20)] fan area {fanA:.3f} m^2 vs hex area {hexA:.3f} m^2"
          f"  -> {'OK' if tile else 'FAIL'}")

    # concrete one-hex dump (the plotted instance)
    print("[one hex (20,20)] 19 datapoints (role -> lat,lon):")
    roles = ["center"] + [f"corner{k}" for k in range(6)] + \
            [f"edge{j//2}{'ab'[j%2]}" for j in range(12)]
    for role, (wx, wy) in zip(roles, hv):
        la, lo = oi.world_to_latlon(wx, wy)
        print(f"   {role:8s} {la:.6f},{lo:.6f}")

    reqs = -(-len(m.verts) // 100)
    print(f"[fetch cost] {len(m.verts)} vertices -> {reqs} requests (~{reqs}s at 1/s,"
          f" < 1000/day)")
    ok = imesh and tile and sum(len(t) for t in m.hex_tris.values()) == 18 * nh
    print("=== TRIMESH I-MESH: PASS ===" if ok else "=== TRIMESH I-MESH: FAIL ===")
    return ok

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
