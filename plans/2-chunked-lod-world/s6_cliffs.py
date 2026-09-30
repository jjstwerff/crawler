#!/usr/bin/env python3
"""plan #2 S6 blueprint (cheapest medium): does per-triangle SLOPE -> cliff improve agreement with
the real Ortler OSM vs the height-band baseline? Reuses plan #1's mesh (1600 hexes x 18 inner
triangles, per-triangle real OSM class + per-vertex height). This PINS the inner-triangle cliff
rule + threshold before porting to the loft detail tier.

Run: python3 s6_cliffs.py   (from plans/2-chunked-lod-world/)
"""
import sys, os
import numpy as np

P1 = os.path.join(os.path.dirname(__file__), "..", "1-ortler-worldgen-fixture")
sys.path.insert(0, P1)
import ortler_import as oi  # noqa: E402

ROCK, SCREE, GLAC, WOOD, GRASS, FARM, WATER = 3, 4, 2, 5, 6, 7, 1
NAMES = {v: k for k, v in oi.NAME2CODE.items()}


def tri_slope_deg(verts, height, tris_flat):
    """steepest-descent slope (deg) of each triangle's plane (verts in metres, height in m)."""
    p = verts[tris_flat]                      # (N,3,2)
    z = height[tris_flat].astype(np.float64)  # (N,3)
    v1 = p[:, 1] - p[:, 0]; v2 = p[:, 2] - p[:, 0]
    z1 = z[:, 1] - z[:, 0]; z2 = z[:, 2] - z[:, 0]
    nx = v1[:, 1] * z2 - z1 * v2[:, 1]
    ny = z1 * v2[:, 0] - v1[:, 0] * z2
    nz = v1[:, 0] * v2[:, 1] - v1[:, 1] * v2[:, 0]
    horiz = np.hypot(nx, ny)
    return np.degrees(np.arctan2(horiz, np.abs(nz)))


def kappa(a, b, classes):
    """Cohen's kappa between label arrays a,b over the given class set."""
    idx = {c: i for i, c in enumerate(classes)}
    n = len(classes)
    m = np.zeros((n, n))
    for x, y in zip(a, b):
        if x in idx and y in idx:
            m[idx[x], idx[y]] += 1
    tot = m.sum()
    if tot == 0:
        return 0.0
    po = np.trace(m) / tot
    pe = (m.sum(0) * m.sum(1)).sum() / (tot * tot)
    return (po - pe) / (1 - pe) if pe < 1 else 0.0


def main():
    m = np.load(oi.MESH_NPZ)
    verts, height = m["verts"], m["height"]
    tris_flat = m["tris"].reshape(-1, 3)          # (28800, 3)
    tri_osm = m["tri_osm"]                          # (28800,)
    tri_h = height[tris_flat].mean(axis=1)
    slope = tri_slope_deg(verts, height, tris_flat)

    # validate units: rock/scree should be markedly steeper than grass/wood
    print("=== per-OSM-class triangle slope (deg) — expect rock/scree steepest ===")
    print(f"{'class':9s} {'n':>6s} {'slope.p50':>9s} {'slope.p90':>9s} {'h.p50':>7s}")
    for c in [WATER, GLAC, ROCK, SCREE, WOOD, GRASS, FARM]:
        sub = slope[tri_osm == c]
        if len(sub):
            hh = tri_h[tri_osm == c]
            print(f"{NAMES[c]:9s} {len(sub):6d} {np.percentile(sub,50):9.1f} "
                  f"{np.percentile(sub,90):9.1f} {np.percentile(hh,50):7.0f}")

    # height-band baseline (the plan #1 confusion() model)
    base = np.select([tri_h >= 3100, tri_h >= 2800, tri_h >= 2500, tri_h >= 2150, tri_h >= 1100],
                     [GLAC, ROCK, SCREE, GRASS, WOOD], default=FARM).astype(np.int16)

    mapped = np.isin(tri_osm, [GLAC, ROCK, SCREE, WOOD, GRASS, FARM])
    classes = [GLAC, ROCK, SCREE, WOOD, GRASS, FARM]
    to = tri_osm[mapped]
    base_m = base[mapped]
    sl_m = slope[mapped]

    base_acc = (base_m == to).mean()
    base_k = kappa(to, base_m, classes)
    rock_osm = np.isin(to, [ROCK, SCREE])
    base_rock_recall = (np.isin(base_m[rock_osm], [ROCK, SCREE])).mean()
    print(f"\nbaseline (height bands): acc={base_acc:.3f} kappa={base_k:+.3f} "
          f"rock/scree-recall={base_rock_recall:.3f}")

    # S6: where slope > theta -> cliff (rock); keep the band class elsewhere. Sweep theta.
    print("\n=== S6 slope->cliff rule (slope>theta -> rock) ===")
    print(f"{'theta':>5s} {'acc':>6s} {'kappa':>7s} {'rock/scree-recall':>17s} {'rock-precision':>14s}")
    best = (-1, None)
    for theta in [25, 30, 35, 40, 45, 50, 55]:
        s6 = base_m.copy()
        steep = sl_m > theta
        s6[steep] = ROCK
        acc = (s6 == to).mean()
        k = kappa(to, s6, classes)
        rr = (np.isin(s6[rock_osm], [ROCK, SCREE])).mean()
        # precision: of triangles WE call rock-via-slope, how many are really rock/scree
        called = steep
        prec = (np.isin(to[called], [ROCK, SCREE])).mean() if called.any() else 0.0
        print(f"{theta:5d} {acc:6.3f} {k:+7.3f} {rr:17.3f} {prec:14.3f}")
        if k > best[0]:
            best = (k, theta)
    print(f"\n[PIN] best kappa {best[0]:+.3f} at theta={best[1]}deg "
          f"(baseline kappa {base_k:+.3f}; delta {best[0]-base_k:+.3f})")


if __name__ == "__main__":
    main()
