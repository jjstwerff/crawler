#!/usr/bin/env python3
"""ortler_import.py — fetcher + geometry for plan #1 (real Ortler world-gen fixture).

Lives in the plan directory (the workshop); reuses the repo's existing world-drawing
routine `tools/overland_blueprint.py` as the SINGLE geometry source (design-protocol
I-GEO: collapse the moros odd-r convention to one site).

Stages (run as `python3 ortler_import.py <stage>`):
  geo   S0 — pin I-GEO: cell<->latlon round-trip + parity, NO network. (implemented)
  elev  S1 — fetch EU-DEM heights onto the hex grid.                    (TODO)
  osm   S2 — OSM landcover + pre-computed water directions.             (TODO)

S0 is the gate: nothing fetches until cell<->latlon is exact and parity is correct.
"""
import sys, math, time, json, heapq, urllib.request, urllib.parse
from pathlib import Path
import numpy as np

# --- reuse the blueprint's geometry as the single source (I-GEO) ---
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import overland_blueprint as ob          # import-safe: __main__ guarded

# ----------------------------- CONFIG -----------------------------
SUMMIT_LAT, SUMMIT_LON = 46.5089, 10.5446   # Ortler / Ortles summit
COLS, ROWS = 80, 80                          # hex grid, Ortler-centered, 1.5 km hex (~120 km)

_OV = ob.Overland(ob.TILE_M)                 # the ONE geometry instance we consult
HW, VS = _OV.hw, _OV.vs                      # horizontal pitch (1500 m), vertical pitch
HC, HR = COLS // 2, ROWS // 2                # home cell == grid center == the summit
_HX, _HY = _OV.center(HC, HR)                # home cell in blueprint world-metres

M_PER_DEG_LAT = 111320.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(SUMMIT_LAT))

def world_to_latlon(wx, wy):
    """Blueprint world-metres -> (lat,lon).  Row/y increases southward; equirectangular."""
    dx, dy = wx - _HX, wy - _HY
    return (SUMMIT_LAT - dy / M_PER_DEG_LAT, SUMMIT_LON + dx / M_PER_DEG_LON)

def cell_to_latlon(c, r):
    """Forward: hex (c,r) -> (lat,lon)."""
    return world_to_latlon(*_OV.center(c, r))

def latlon_to_cell(lat, lon):
    """Exact inverse for cell centers: world->cell using the SAME odd-r stagger."""
    wy = (SUMMIT_LAT - lat) * M_PER_DEG_LAT + _HY
    wx = (lon - SUMMIT_LON) * M_PER_DEG_LON + _HX
    r = round(wy / VS)
    c = round(wx / HW - 0.5 * (r & 1))
    return (c, r)

def _km_from_summit(c, r):
    wx, wy = _OV.center(c, r)
    return math.hypot(wx - _HX, wy - _HY) / 1000.0

# ----------------------------- S0: pin I-GEO -----------------------------
def stage_geo():
    print("=== S0 — I-GEO: cell<->latlon round-trip + parity (no network) ===")
    ok = True

    # 1) parity / pitch of the moros odd-r stagger (the silent-drift trap)
    odd_shift = _OV.center(0, 1)[0] - _OV.center(0, 0)[0]   # expect +0.5*HW
    even_align = _OV.center(0, 2)[0] - _OV.center(0, 0)[0]  # expect 0
    row_pitch = _OV.center(0, 1)[1] - _OV.center(0, 0)[1]   # expect VS
    p_ok = (abs(odd_shift - 0.5 * HW) < 1e-6 and abs(even_align) < 1e-6
            and abs(row_pitch - VS) < 1e-6)
    print(f"[parity] odd-row x-shift = {odd_shift:.3f} m (want {0.5*HW:.3f});"
          f" even-row align = {even_align:.3f} (want 0); row pitch = {row_pitch:.3f}"
          f" (want {VS:.3f})  -> {'OK' if p_ok else 'FAIL'}")
    ok &= p_ok

    # 2) round-trip exact over EVERY cell, with an even- and odd-row callout
    miss = 0
    for r in range(ROWS):
        for c in range(COLS):
            if latlon_to_cell(*cell_to_latlon(c, r)) != (c, r):
                miss += 1
    for (c, r), tag in (((10, 10), "even-row"), ((11, 11), "odd-row")):
        la, lo = cell_to_latlon(c, r)
        print(f"[round-trip {tag}] ({c},{r}) -> {la:.6f},{lo:.6f} -> "
              f"{latlon_to_cell(la, lo)}")
    rt_ok = (miss == 0)
    print(f"[round-trip] mismatches over {COLS*ROWS} cells = {miss}"
          f"  -> {'OK' if rt_ok else 'FAIL'}")
    ok &= rt_ok

    # 3) home cell <-> summit is exact
    hla, hlo = cell_to_latlon(HC, HR)
    h_ok = (abs(hla - SUMMIT_LAT) < 1e-9 and abs(hlo - SUMMIT_LON) < 1e-9
            and latlon_to_cell(SUMMIT_LAT, SUMMIT_LON) == (HC, HR))
    print(f"[home] cell ({HC},{HR}) -> {hla:.6f},{hlo:.6f}; "
          f"summit -> {latlon_to_cell(SUMMIT_LAT, SUMMIT_LON)}  "
          f"-> {'OK' if h_ok else 'FAIL'}")
    ok &= h_ok

    # 4) corners bracket the Ortler region
    print("[corners] (km from summit):")
    for c, r in ((0, 0), (COLS-1, 0), (0, ROWS-1), (COLS-1, ROWS-1)):
        la, lo = cell_to_latlon(c, r)
        print(f"   ({c:2d},{r:2d}) -> {la:.5f},{lo:.5f}   {_km_from_summit(c,r):5.1f} km")
    lats = [cell_to_latlon(c, r)[0] for r in range(ROWS) for c in range(COLS)]
    lons = [cell_to_latlon(c, r)[1] for r in range(ROWS) for c in range(COLS)]
    print(f"[bbox] lat {min(lats):.4f}..{max(lats):.4f}   lon {min(lons):.4f}..{max(lons):.4f}")

    print("=== S0 I-GEO: PASS ===" if ok else "=== S0 I-GEO: FAIL ===")
    return ok

# ----------------------------- S1: fetch EU-DEM heights -----------------------------
DATA = Path(__file__).resolve().parent / "data"
HEX_NPZ = DATA / "ortler_hexes.npz"
MESH_NPZ = DATA / "ortler_trimesh.npz"
OSM_CACHE = DATA / "osm_polys.npz"
TRIOSM_NPZ = DATA / "ortler_triosm.npz"
API = "https://api.opentopodata.org/v1/eudem25m"   # EU-DEM 25 m (Alps)
BATCH, REQ_SLEEP = 100, 1.05                         # public limits: 100/req, ~1 req/s

def _fetch_elev(latlons):
    out = []
    for i in range(0, len(latlons), BATCH):
        chunk = latlons[i:i+BATCH]
        locs = "|".join(f"{la:.6f},{lo:.6f}" for la, lo in chunk)
        url = API + "?locations=" + urllib.parse.quote(locs, safe="|,")
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.load(r)
        if d.get("status") != "OK":
            raise RuntimeError("API: " + json.dumps(d)[:200])
        out += [None if x["elevation"] is None else float(x["elevation"]) for x in d["results"]]
        sys.stderr.write(f"  {min(i+BATCH, len(latlons))}/{len(latlons)}\n")
        if i + BATCH < len(latlons):
            time.sleep(REQ_SLEEP)
    return out

def _relief_ascii(h):
    ramp = " .:-=+*#%@"
    lo, hi = float(h.min()), float(h.max())
    for r in range(ROWS):
        pad = " " if (r & 1) else ""
        line = "".join(ramp[min(len(ramp)-1, int((h[r, c]-lo)/(hi-lo+1e-9)*len(ramp)))]
                        for c in range(COLS))
        print(pad + line)

def stage_elev():
    print(f"=== S1 — fetch EU-DEM ({COLS}x{ROWS} = {COLS*ROWS} cells) ===")
    latlons = [cell_to_latlon(c, r) for r in range(ROWS) for c in range(COLS)]
    elev = _fetch_elev(latlons)
    holes = sum(1 for e in elev if e is None)
    h = np.zeros((ROWS, COLS), np.int16)
    for r in range(ROWS):
        for c in range(COLS):
            e = elev[r*COLS + c]
            h[r, c] = 0 if e is None else int(round(e))   # i16 metres, sea level 0
    DATA.mkdir(exist_ok=True)
    np.savez_compressed(HEX_NPZ, h=h, cols=COLS, rows=ROWS,
                        summit=[SUMMIT_LAT, SUMMIT_LON], hc=HC, hr=HR)
    print(f"[holes] cells with no elevation = {holes}")
    print(f"[stats] min/mean/max = {h.min()}/{h.mean():.0f}/{h.max()} m")
    print(f"[summit] cell ({HC},{HR}) = {h[HR, HC]} m  (expect ~3500-3905)")
    print(f"[relief]")
    _relief_ascii(h)
    g = (holes == 0 and 3500 <= h[HR, HC] <= 3905 and h.min() < 1200 and h.max() > 3000)
    print(f"wrote {HEX_NPZ.relative_to(REPO)}")
    print("=== S1 ELEV: PASS ===" if g else "=== S1 ELEV: FAIL (stats implausible) ===")
    return g

# ----------------------------- mesh: sample heights at triangle vertices -----------------------------
def stage_mesh():
    import trimesh as tm
    m = tm.build()
    print(f"=== mesh sample — DEM at {len(m.verts)} triangle vertices ===")
    elev = _fetch_elev([m.latlon(i) for i in range(len(m.verts))])
    holes = sum(1 for e in elev if e is None)
    h = np.array([0 if e is None else int(round(e)) for e in elev], np.int16)
    keys = sorted(m.hex_tris.keys())
    np.savez_compressed(MESH_NPZ,
                        verts=np.array(m.verts, np.float64), height=h,
                        tris=np.array([m.hex_tris[k] for k in keys], np.int32),
                        hexcr=np.array(keys, np.int32),
                        cols=COLS, rows=ROWS, summit=[SUMMIT_LAT, SUMMIT_LON])
    sid = m.key2id[tm._key(*_OV.center(HC, HR))]
    print(f"[holes] {holes}")
    print(f"[stats] min/mean/max = {h.min()}/{h.mean():.0f}/{h.max()} m over {len(h)} vertices")
    print(f"[summit vertex] {h[sid]} m (expect ~3835)")
    g = (holes == 0 and 3500 <= h[sid] <= 3905 and h.min() < 1200 and h.max() > 3000)
    print(f"wrote {MESH_NPZ.relative_to(REPO)}")
    print("=== MESH SAMPLE: PASS ===" if g else "=== MESH SAMPLE: FAIL ===")
    return g

# ----------------------------- S2: OSM landcover + fed water directions -----------------------------
OVERPASS = "https://overpass-api.de/api/interpreter"
NAME2CODE = {"none":0,"water":1,"glacier":2,"rock":3,"scree":4,"wood":5,
             "grass":6,"farmland":7,"orchard":8,"vineyard":9,"wetland":10}
CODE_CH = {0:".",1:"~",2:"*",3:"^",4:":",5:"T",6:'"',7:"+",8:"o",9:"v",10:"s"}

def _osm_class(tags):
    n, lu = tags.get("natural"), tags.get("landuse")
    if n == "glacier": return ("glacier", 90)
    if n == "water" or lu in ("reservoir", "basin"): return ("water", 80)
    if n == "wetland": return ("wetland", 70)
    if n in ("bare_rock", "rock", "cliff"): return ("rock", 60)
    if n in ("scree", "shingle"): return ("scree", 55)
    if lu == "vineyard": return ("vineyard", 52)
    if lu == "orchard": return ("orchard", 50)
    if lu == "farmland": return ("farmland", 48)
    if n == "wood" or lu == "forest": return ("wood", 40)
    if n in ("grassland", "fell", "heath") or lu == "meadow": return ("grass", 30)
    return (None, 0)

def _overpass(q):
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=data,
                                 headers={"User-Agent": "crawler-pln1/1.0 (Ortler terrain test)"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)

def _pip(plat, plon, qla, qlo):
    """ray-cast point-in-polygon, vectorized over a subset of query points (lat,lon arrays)."""
    inside = np.zeros(len(qla), bool)
    n = len(plat); j = n - 1
    for i in range(n):
        yi, xi, yj, xj = plat[i], plon[i], plat[j], plon[j]
        cond = (xi > qlo) != (xj > qlo)
        denom = xj - xi if xj != xi else 1.0
        yat = (yj - yi) * (qlo - xi) / denom + yi
        inside ^= cond & (qla < yat)
        j = i
    return inside

def _nbr_index(c, r, nc, nr):
    for i, (a, b) in enumerate(_OV.neighbors(c, r)):
        if (a, b) == (nc, nr): return i
    return -1

def _pitfill(h):
    """Priority-flood so every cell drains (no interior sinks) -> steepest descent is
    guaranteed downhill. Tiny epsilon gives flats a gradient."""
    ny, nx = h.shape
    filled = h.astype(float).copy()
    seen = np.zeros((ny, nx), bool)
    pq = []
    for r in range(ny):
        for c in range(nx):
            if r in (0, ny - 1) or c in (0, nx - 1):
                heapq.heappush(pq, (float(h[r, c]), c, r)); seen[r, c] = True
    while pq:
        lvl, c, r = heapq.heappop(pq)
        for nc, nr in _OV.neighbors(c, r):
            if 0 <= nc < nx and 0 <= nr < ny and not seen[nr, nc]:
                seen[nr, nc] = True
                filled[nr, nc] = max(float(h[nr, nc]), lvl + 1e-3)
                heapq.heappush(pq, (filled[nr, nc], nc, nr))
    return filled

def _cache_polys(polys):
    """Cache classified polygons (pr, code, plat, plon) so we can re-classify at any
    resolution (hex or triangle) without re-querying Overpass."""
    if not polys: return
    lat = np.concatenate([p[2] for p in polys]); lon = np.concatenate([p[3] for p in polys])
    lens = np.array([len(p[2]) for p in polys], np.int64); off = np.concatenate([[0], np.cumsum(lens)])
    np.savez_compressed(OSM_CACHE, lat=lat, lon=lon, off=off,
                        pr=np.array([p[0] for p in polys], np.int32),
                        code=np.array([p[1] for p in polys], np.int32))

def _load_polys():
    d = np.load(OSM_CACHE)
    lat, lon, off, pr, cd = d["lat"], d["lon"], d["off"], d["pr"], d["code"]
    return [(int(pr[i]), int(cd[i]), lat[off[i]:off[i+1]], lon[off[i]:off[i+1]])
            for i in range(len(pr))]

def _classify_pts(polys, qlat, qlon):
    """Per-point OSM class by polygon priority (point-in-polygon, bbox-prefiltered).
    Works for any query points — hex centers OR triangle centroids."""
    code = np.zeros(qlat.size, int); prio = np.zeros(qlat.size, int)
    for (pr, cd, plat, plon) in polys:
        if len(plat) < 3: continue
        sel = np.where((qlat >= plat.min()) & (qlat <= plat.max())
                       & (qlon >= plon.min()) & (qlon <= plon.max()))[0]
        if not len(sel): continue
        hit = sel[_pip(plat, plon, qlat[sel], qlon[sel])]
        better = hit[prio[hit] < pr]
        code[better] = cd; prio[better] = pr
    return code

def stage_osm():
    if not HEX_NPZ.exists():
        print("run `elev` first (need data/ortler_hexes.npz)"); return False
    h = np.load(HEX_NPZ)["h"]
    qlat = np.array([cell_to_latlon(c, r)[0] for r in range(ROWS) for c in range(COLS)])
    qlon = np.array([cell_to_latlon(c, r)[1] for r in range(ROWS) for c in range(COLS)])
    s, w = float(qlat.min())-0.01, float(qlon.min())-0.01
    n_, e = float(qlat.max())+0.01, float(qlon.max())+0.01
    bb = f"{s},{w},{n_},{e}"
    q = (f"[out:json][timeout:120];("
         f'way["natural"~"^(glacier|bare_rock|rock|cliff|scree|shingle|water|wood|grassland|fell|heath|wetland)$"]({bb});'
         f'relation["natural"~"^(glacier|water|wood|wetland)$"]({bb});'
         f'way["landuse"~"^(farmland|orchard|vineyard|meadow|forest|reservoir|basin)$"]({bb});'
         f'relation["landuse"~"^(forest|farmland|reservoir|basin|meadow)$"]({bb});'
         f'way["waterway"~"^(river|stream)$"]({bb});'
         f");out geom;")
    print(f"=== S2 — OSM landcover + water (bbox {bb}) ===")
    data = _overpass(q)
    polys, rivers = [], []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        if el["type"] == "way":
            g = el.get("geometry")
            if not g: continue
            if tags.get("waterway") in ("river", "stream"):
                rivers.append([(p["lat"], p["lon"]) for p in g]); continue
            nm, pr = _osm_class(tags)
            if nm: polys.append((pr, nm, g))
        elif el["type"] == "relation":
            nm, pr = _osm_class(tags)
            if not nm: continue
            for m in el.get("members", []):
                if m.get("type") == "way" and m.get("role") in ("outer", "") and m.get("geometry"):
                    polys.append((pr, nm, m["geometry"]))
    print(f"[osm] {len(polys)} landcover polygons, {len(rivers)} waterways")

    # convert + cache polygons (reused for per-triangle classification), then classify hexes
    polys_a = [(pr, NAME2CODE[nm], np.array([p["lat"] for p in g]), np.array([p["lon"] for p in g]))
               for (pr, nm, g) in polys]
    _cache_polys(polys_a)
    osm = _classify_pts(polys_a, qlat, qlon).reshape(ROWS, COLS).astype(np.int16)

    # MAP gives the river cells (OSM waterways densified onto the grid)...
    river_mask = np.zeros((ROWS, COLS), bool)
    for poly in rivers:
        for k in range(len(poly) - 1):
            la1, lo1 = poly[k]; la2, lo2 = poly[k + 1]
            dm = math.hypot((lo2 - lo1) * M_PER_DEG_LON, (la2 - la1) * M_PER_DEG_LAT)
            steps = max(1, int(dm / (HW * 0.5)))
            for sgn in range(steps + 1):
                f = sgn / steps
                c, r = latlon_to_cell(la1 + (la2 - la1) * f, lo1 + (lo2 - lo1) * f)
                if 0 <= c < COLS and 0 <= r < ROWS:
                    river_mask[r, c] = True
    # ...DEM gives the downhill direction: steepest descent on the pit-filled surface
    # (0 uphill by construction; cells with no lower neighbour are window-edge outlets).
    filled = _pitfill(h)
    rf = np.full((ROWS, COLS), -1, np.int8)
    for r in range(ROWS):
        for c in range(COLS):
            if not river_mask[r, c]:
                continue
            lo, bidx = filled[r, c], -1
            for i, (nc, nr) in enumerate(_OV.neighbors(c, r)):
                if 0 <= nc < COLS and 0 <= nr < ROWS and filled[nr, nc] < lo:
                    lo, bidx = filled[nr, nc], i
            rf[r, c] = bidx
    river_cells = int((rf >= 0).sum())
    edge_outlets = int(river_mask.sum()) - river_cells
    uphill = 0
    for r in range(ROWS):
        for c in range(COLS):
            if rf[r, c] < 0: continue
            nc, nr = _OV.neighbors(c, r)[rf[r, c]]
            if filled[nr, nc] > filled[r, c]: uphill += 1
    frac = uphill / river_cells if river_cells else 0.0

    # checks
    gl = [(c, r) for r in range(ROWS) for c in range(COLS)
          if osm[r, c] == NAME2CODE["glacier"] and abs(c-HC) <= 4 and abs(r-HR) <= 4]
    farm = osm == NAME2CODE["farmland"]
    farm_h = int(h[farm].mean()) if farm.any() else -1

    d = dict(np.load(HEX_NPZ)); d["osm"] = osm; d["river_flow"] = rf; d["river_mask"] = river_mask
    np.savez_compressed(HEX_NPZ, **d)

    from collections import Counter
    hist = {k: int((osm == v).sum()) for k, v in NAME2CODE.items() if (osm == v).any()}
    print(f"[classes] {hist}")
    print(f"[rivers] {int(river_mask.sum())} river cells; {river_cells} with a downhill dir, "
          f"{edge_outlets} window-edge outlets")
    print(f"[I-FLOW] uphill fed directions = {uphill}/{river_cells} ({frac*100:.1f}%)  "
          f"(map cells + DEM-downhill -> 0 by construction)")
    print(f"[glacier near summit] {len(gl)} cells within 4 of ({HC},{HR})")
    print(f"[farmland] {int(farm.sum())} cells, mean height {farm_h} m")
    print("[osm map]")
    for r in range(ROWS):
        print((" " if r & 1 else "") + "".join(CODE_CH[int(osm[r, c])] for c in range(COLS)))
    g = (frac < 0.10 and len(gl) > 0 and farm.any() and 0 < farm_h < 1600)
    print("=== S2 OSM: PASS ===" if g else "=== S2 OSM: review (gate not fully met) ===")
    return g

# ----------------------------- per-triangle OSM classification -----------------------------
def stage_triosm():
    if not OSM_CACHE.exists():
        print("run `osm` first (need the cached OSM polygons)"); return False
    import trimesh as tm
    polys = _load_polys()
    m = tm.build()                                                           # geometry only (no heights)
    keys = sorted(m.hex_tris.keys())
    tris = np.array([m.hex_tris[k] for k in keys], np.int32).reshape(-1, 3)  # (ntri,3) vertex ids
    V = np.array(m.verts)                                                    # (nverts,2) world xy
    cen = V[tris].mean(axis=1)                                               # triangle centroids
    clat = SUMMIT_LAT - (cen[:, 1] - _HY) / M_PER_DEG_LAT
    clon = SUMMIT_LON + (cen[:, 0] - _HX) / M_PER_DEG_LON
    print(f"=== per-triangle OSM: classifying {len(tris)} triangle centroids ===")
    tri_osm = _classify_pts(polys, clat, clon).astype(np.int16)
    np.savez_compressed(TRIOSM_NPZ, tri_osm=tri_osm, cols=COLS, rows=ROWS)
    none = NAME2CODE["none"]
    hist = {k: int((tri_osm == v).sum()) for k, v in NAME2CODE.items() if (tri_osm == v).any()}
    print(f"[per-triangle classes] {hist}")
    print(f"[coverage] none = {100*int((tri_osm==none).sum())/len(tri_osm):.0f}% of {len(tri_osm)} triangles")
    print(f"wrote tri_osm -> {TRIOSM_NPZ.relative_to(REPO)}")
    return True

STAGES = {"geo": stage_geo, "elev": stage_elev, "mesh": stage_mesh, "osm": stage_osm,
          "triosm": stage_triosm}
if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "geo"
    fn = STAGES.get(stage)
    if not fn:
        print(f"unknown stage {stage!r}; have: {', '.join(STAGES)}"); sys.exit(2)
    sys.exit(0 if fn() else 1)
