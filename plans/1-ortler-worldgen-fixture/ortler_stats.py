#!/usr/bin/env python3
"""ortler_stats.py — derive the real terrain-transition VALUES (@PLN1 goal 3).

From the per-cell (OSM class, elevation, slope) data, find where terrain types actually
change inside the range — treeline, alpine/scree onset, snow/glacier line, cliff slope —
so they become realistic fantasy-world generation defaults (the data-driven S6/S7).
No network: reads data/ortler_hexes.npz.
"""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortler_import as oi
import numpy as np
from collections import Counter

CODE2NAME = {v: k for k, v in oi.NAME2CODE.items()}

def slope_grid(h):
    s = np.zeros_like(h, float)
    for r in range(oi.ROWS):
        for c in range(oi.COLS):
            g = 0.0
            for nc, nr in oi._OV.neighbors(c, r):
                if 0 <= nc < oi.COLS and 0 <= nr < oi.ROWS:
                    g = max(g, math.degrees(math.atan2(abs(h[r, c] - h[nr, nc]), oi.HW)))
            s[r, c] = g
    return s

def pct(a, p):
    return int(np.percentile(a, p)) if len(a) else -1

def confusion():
    """S5: per-triangle confusion (OSM ground truth vs our model's derived bands) + the
    adequacy verdict (every OSM class -> an engine K_* kind?)."""
    mesh = np.load(oi.MESH_NPZ)
    if "tri_osm" not in mesh.files:
        print("run `triosm` first (need per-triangle OSM)"); return False
    names = {v: k for k, v in oi.NAME2CODE.items()}
    NONE = oi.NAME2CODE["none"]
    tri_osm = mesh["tri_osm"]
    tri_h = mesh["height"][mesh["tris"].reshape(-1, 3)].mean(axis=1)
    tri_model = np.select([tri_h >= 3100, tri_h >= 2800, tri_h >= 2500, tri_h >= 2150, tri_h >= 1100],
                          [2, 3, 4, 6, 5], default=7).astype(np.int16)
    mapped = tri_osm != NONE
    to, tm = tri_osm[mapped], tri_model[mapped]
    cols = [2, 3, 4, 5, 6, 7]   # model outputs: glacier rock scree wood grass farmland(valley)
    print(f"\n=== S5 — per-triangle confusion ({int(mapped.sum())} classified of {len(tri_osm)}) ===")
    print(f"{'OSM/model':>10s} | " + " ".join(f"{names[c][:5]:>5s}" for c in cols) + "  |    n")
    for oc in sorted(set(int(x) for x in to)):
        sub = tm[to == oc]
        row = " ".join(f"{int((sub == c).sum()):5d}" for c in cols)
        print(f"{names[oc][:10]:>10s} | {row}  | {len(sub):5d}")
    elev = [2, 3, 4, 5, 6]      # glacier rock scree wood grass = the height-banded classes
    em = np.isin(to, elev)
    agree = int((to[em] == tm[em]).sum())
    print(f"[elevation-class agreement] {agree}/{int(em.sum())} "
          f"({100*agree/max(1,int(em.sum())):.0f}%) on glacier/rock/scree/wood/grass")
    KMAP = {"water": "K_LAKE/K_RIVER", "glacier": "K_ICE", "rock": "K_FACE/K_SCREE",
            "scree": "K_SCREE", "wood": "K_FOREST", "grass": "K_MEADOW", "farmland": "K_FIELD",
            "orchard": "K_FIELD", "vineyard": "K_FIELD", "wetland": "K_SWAMP"}
    print("[adequacy] OSM class -> engine kind:")
    missing = []
    for oc in sorted(set(int(x) for x in to)):
        k = KMAP.get(names[oc], "??? MISSING")
        if k.startswith("???"): missing.append(names[oc])
        print(f"   {names[oc]:9s} -> {k:14s} ({int((to == oc).sum())} tris)")
    print(f"[VERDICT] missing kinds: {missing if missing else 'NONE — the 14 K_* cover the Ortler'}")
    return True

def main():
    d = np.load(oi.HEX_NPZ)
    if "osm" not in d:
        print("run `osm` first"); return False
    h, osm = d["h"].astype(float), d["osm"]
    slope = slope_grid(h)
    hf, of, sf = h.ravel(), osm.ravel(), slope.ravel()

    print("=== per-class elevation + slope (Ortler, real OSM) ===")
    print(f"{'class':9s} {'cells':>5s} {'h.p10':>6s} {'h.p50':>6s} {'h.p90':>6s} {'slope.p50':>9s}")
    for code in sorted(CODE2NAME):
        m = of == code
        if not m.any(): continue
        print(f"{CODE2NAME[code]:9s} {int(m.sum()):5d} {pct(hf[m],10):6d} {pct(hf[m],50):6d}"
              f" {pct(hf[m],90):6d} {pct(sf[m],50):8d}°")

    # dominant class per 100 m band (excluding 'none'/unmapped), + coverage
    print("\n=== dominant terrain by elevation band (none excluded) ===")
    lo, hi = int(hf.min()//100*100), int(hf.max()//100*100)+100
    none = oi.NAME2CODE["none"]
    rows = []
    for b in range(lo, hi, 100):
        sel = (hf >= b) & (hf < b+100)
        if not sel.any(): continue
        codes = of[sel]
        mapped = codes[codes != none]
        nonef = 1 - len(mapped)/len(codes)
        dom = Counter(mapped.tolist()).most_common(1)
        domn = CODE2NAME[dom[0][0]] if dom else "—"
        rows.append((b, domn, len(codes), nonef))
        bar = domn
        print(f"  {b:4d}-{b+99:4d} m  n={len(codes):3d}  none={nonef*100:3.0f}%  -> {bar}")

    # transitions: first band where the dominant becomes each higher class
    def first_band(name):
        for (b, domn, n, nf) in rows:
            if domn == name: return b
        return None
    print("\n=== DERIVED transition values (realistic fantasy defaults) ===")
    tl = first_band("grass") or first_band("scree")
    forest_top = None
    for (b, domn, n, nf) in rows:
        if domn == "wood": forest_top = b+100
    scree = first_band("scree") or first_band("rock")
    snow = first_band("glacier")
    woodm = hf[(of == oi.NAME2CODE["wood"])]
    rockm = sf[(of == oi.NAME2CODE["rock"]) | (of == oi.NAME2CODE["scree"])]
    print(f"  treeline (forest top / first alpine band) : ~{forest_top or tl} m"
          f"  [wood p90 = {pct(woodm,90)} m]")
    print(f"  scree/rock onset (first band)             : ~{scree} m")
    print(f"  snow/glacier line (first glacier band)    : ~{snow} m")
    print(f"  cliff slope (rock/scree slope p50/p90)    : {pct(rockm,50)}°/{pct(rockm,90)}°")
    confusion()
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
