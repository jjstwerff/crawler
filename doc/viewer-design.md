# viewer-design.md — how the Ortler 3D viewer renders today, and where it falls short of the rest of the stack

This doc is a careful read of the code as it stands (2026-06-17). It maps every layer the
Ortler 3D viewer touches, so any further work doesn't accidentally drop a feature the
non-viewer paths already have. The user's standing constraint:

> **The viewer must not be less featured than the other implementations.**

That is the gate. Where the viewer is currently behind the other implementations, this doc
records *what* it's behind and *why* — without proposing a fix yet. The fix lives at the
end (§7), labelled clearly.

> **Owner:** plan **#2** (`plans/2-chunked-lod-world/`, OPEN) — this is its feature-parity
> ledger. **Read date 2026-06-17**; the code has moved since, so check a claim before acting
> on it.
>
> ⚠ **YOU CANNOT CURRENTLY RUN THE THING THIS DOC DESCRIBES, AND IT LOOKS LIKE A HANG.**
> `viewer` is one of the six entry points that import `src/regions/ortler.loft` — generated
> data whose largest line is an 86 400-element vector literal, which loft parses in **O(n²)**
> (~18 min at 99 % CPU with no output). Not broken, *unusable*: **loft#854**. So a `timeout`
> here is not evidence of a defect in the viewer. `CLAUDE.md` → the on-demand sweep.
>
> ⚠ §7 **proposes** files — `src/orttrimesh.loft`, `assets/sprites/river_line.png`,
> `tools/blueprints/river_line.py`, `src/regions/wales.loft`. None exist; they are the
> deliverable, not the record. `tools/doccheck.py` accepts them by name for that reason.

---

## 1. Geometry pillars in the repo

There are **four** distinct hex-mesh patterns in this codebase, not one. Each layer of the
system uses a different pattern, and they don't compose by themselves. Reading them in
order of refinement:

### 1.1 6-fan per hex (`src/worldmesh.loft`)
- Lives in: the **2D play view** (`view.loft` ← `worldmesh.loft`).
- 1 vertex at the hex centre + 6 vertices at the hex corners → 6 triangles, **1 per side**
  (`center, corner_k, corner_{k+1}`).
- Each side of the hex is the outer edge of exactly one fan triangle.
- `build_world_mesh` (legacy fat path) and `build_world_instances` + `build_hex_offsets`
  (the R7 instanced path, P6) both emit this. The instanced path uses an EXACT lattice
  construction (`x = √3·(column + dx), y = row_y + dy`, dx ∈ {0,±0.5}, dy ∈ {0,±0.5,±1})
  so corners are bit-identical across hexes → watertight.

### 1.2 33×33 heightfield per chunk (`src/chunkmesh.loft`, two functions)
- Lives in: the **3D viewer** (`viewer.loft` ← `chunkmesh.loft`).
- `chunk_mesh(ch, e, s, se)` — DETAIL tier: 33×33 vertex grid (32×32 cells × 2 triangles
  each = 2048 triangles per chunk). Each detail cell is ~1.5 m square. The hex shape is
  not preserved — cells form a square raster.
- `chunk_mesh_ov(ch, e, s, se)` — OVERWORLD tier: SAME 33×33 grid + 32×32 quad
  topology, but each grid vertex sits at `overworld_center(gx, gz)` (a 1.5 km moros odd-r
  hex centre). Heights of corner/sub-hex points are NOT computed — only the hex centre.
- Watertight by I-SEAM: a chunk reads its right/bottom edge from the E/S/SE neighbours,
  so adjacent chunk meshes share boundary vertices exactly.
- **For the Ortler 80×80 view this is the only path used** (`bake_ortler` →
  `chunk_mesh_ov`): every hex becomes a single vertex in the heightfield grid; the hex
  shape and any sub-hex detail are lost at the mesh level.

### 1.3 Detail-tier subdivision with talus (`src/talus.loft`)
- Lives in: the 3D viewer's *opt-in* `VIEWER_TALUS=1` / `VIEWER_DETAIL=1` mode.
- Subdivides one OVERWORLD hex (1.5 km) into **~32 × 32 detail chunks** of 32×32 cells
  each → on the order of one million ~1.5 m cells per hex.
- Adds: weathering rubble + angle-of-repose relaxation (`talus_relax`) → K_FACE bare
  cliffs + K_SCREE talus. D8 flow accumulation (`flow_accumulate`) → K_RIVER channels
  where flow > T_CHANNEL (45 cells). Watertight across chunks via the TALUS_HALO.
- Output is **still a 33×33 heightfield grid per chunk** (it goes through `chunk_mesh`),
  so the river is K_RIVER on the cell, not a ribbon.

### 1.4 18 triangles per hex — 3 per side (`plans/1-ortler-worldgen-fixture/trimesh.py`)
- Lives in: the **@PLN1 Python prototype** (Ortler ground-truth investigation).
- 19 vertices per hex: 1 centre + 6 corners + **12 edge-thirds** (at 1/3 and 2/3 of each
  side). 18 triangles per hex — per side `k`:

      T0 = (centre, corner_k,      edge_(k, 1/3))   ← flank L of side k
      T1 = (centre, edge_(k, 1/3), edge_(k, 2/3))   ← middle of side k
      T2 = (centre, edge_(k, 2/3), corner_(k+1))    ← flank R of side k

- Watertight by **I-MESH**: an interior corner is shared by 3 hexes (refcount 3); an
  edge-third by 2 (refcount 2); the centre by 1. `trimesh.py` proves this in its `main`
  with `set(corner_refs) == {3}` and `set(edge_refs) == {2}`.
- Used by `ortler_render.py` for per-pixel triangle classification, not as actual
  emitted GL geometry. The triangle id of a world-space pixel is recovered analytically
  from the angle to the hex centre (`_tri_gid` + `BANG`), so the prototype renders the
  per-triangle classes pixel-by-pixel onto an orthographic image — never as a 3D mesh.
- **This pattern has no loft port today.**

These four patterns are NOT a chain of refinements wired together. They are four parallel
ways the codebase looks at a hex.

---

## 2. The Ortler data layers

Three NPZ fixtures sit under `plans/1-ortler-worldgen-fixture/data/`. Only a slim subset
makes it into the loft world; the rest is Python-only.

### 2.1 `ortler_hexes.npz` — per-cell facts (80×80)
- `h` (i16, m) — EU-DEM height per hex centre.
- `osm` (i16, 0..10) — OSM landcover class per hex centre. Codes: 0 none, 1 water,
  2 glacier, 3 rock, 4 scree, 5 wood, 6 grass, 7 farmland, 8 orchard, 9 vineyard,
  10 wetland.
- `river_mask` (bool) — set if the hex centre lay on any OSM `waterway=river|stream`.
- **`river_flow` (i8 0..5, −1 elsewhere)** — for each river-mask cell, the **downhill
  neighbour direction** computed on the **pit-filled** height (`_pitfill`), or −1 if the
  cell has no lower in-window neighbour (i.e. it's a window-edge outlet). After
  pit-fill, water-flows-uphill = 0 by construction — the importer asserts it.
- `summit, hc, hr` — the home cell (Ortler summit).

### 2.2 `ortler_trimesh.npz` — per-vertex EU-DEM (40×40 only)
- 14878 unique vertices for 1600 hexes (19/hex deduped at corners and edge-thirds).
- `height` (i16) — REAL EU-DEM samples at each of those 19 sub-hex points (not
  interpolated; the importer does ~150 OpenTopoData requests per batch to fetch them).
- `tris` shape (1600, 18, 3) — vertex-id triplets for each of the 18 fan triangles.

  ⚠️ This is **40×40**, not 80×80. There is no equivalent per-vertex height grid for
  the 80×80 set the viewer actually uses.

### 2.3 `ortler_triosm.npz` — per-triangle OSM (80×80)
- `tri_osm` of length **115200 = 6400 × 18** — the OSM class of each of the 18 triangles
  per hex, point-sampled at the triangle's centroid via OSM polygons. Bit-identical to
  the per-pixel painting in `ortler_render.py`.
- **Exists on disk; NOT exported to loft.**

### 2.4 What loft sees today (`src/ortlerdata.loft`)
The exporter (`plans/1-ortler-worldgen-fixture/export_ortler_loft.py`) only emits three
arrays — `ort_h`, `ort_osm`, `ort_river` — and the dimensions / home cell. **Per-cell
flow direction, per-cell accumulation, per-triangle OSM, and the EU-DEM per-vertex
heights are all kept on disk in Python land.** That's the data wall the viewer is on the
wrong side of.

`src/ortlergen.loft` then turns the per-cell (height, OSM, river_mask) into a per-cell
K_* kind (`ort_osm_kind` for the ground-truth pane, `ort_model_kind` for the
elevation-band pane) — and a `DetailChunk` of CHUNK² cells.

---

## 3. Rivers in the rest of the stack (what the viewer is competing against)

This is the part the user flagged: rivers are not "a hex-to-hex straight line in one of
6 directions" — there is a richer model already implemented elsewhere in this repo, and
the viewer doesn't expose any of it.

### 3.1 The procedural river model (`src/overland.loft`)
Used by `make play`'s procedural worlds — fully ported to loft.

- **Hash-jittered interior control point per hex.** `ov_vertex(c, r)` displaces the hex
  centre by `(jx, jy)` where `jx, jy = (hash(c, r, …) − 0.5) · 0.55 · OV_RC`. So a river
  inside a hex does NOT route through the centre — it routes through a per-hex jittered
  interior point.
- **Canonical edge-crossing point per shared side.** `ov_edge_bit(ca, ra, cb, rb)`
  sorts the cell pair (so both hexes hash the SAME pair), then offsets the side midpoint
  along the side by `±0.30 · OV_RC` — the sign chosen by a hash bit. So the crossing is
  at ~0.20 or ~0.80 of the side length, **never** at the midpoint, **never** at a corner.
  Because both hexes hash the sorted pair, they agree on the same crossing point →
  rivers meet seamlessly at hex boundaries.
- **Fractal midpoint displacement.** `ov_displace(...)` recursively splits each segment
  and pushes the midpoint sideways by `±seg_len · 0.34 · open_ · hash(rounded endpoints)`,
  using endpoint hashes so two windows over the same world produce identical curves.
- **Per-point width with an estuary funnel.** `OvSide.os_ws` is a per-point width;
  estuaries widen toward the sea (`wnom · (1 + 3 · max(0, open_ − 0.45))`).
- **Monotone bed (I3).** `OvSide.os_bed` is a strictly non-increasing ramp from the
  start hex's bed level to the end hex's bed level; lakes land on `OV_LAKE_LVL`, sea on
  `−15`.
- **Confluence pools.** When 2+ rivers flow into a flat cell with combined accumulation
  ≥ 2.5, an `OvSwamp` is added (radius `min(420, 110 · √intot)`).

Number of "directions" a river segment can take inside one hex: the segment goes from
the interior CONTROL point to the edge-crossing on the chosen outgoing side. There are
6 sides × 2 crossing-bit values = **12 possible exit points per hex**, plus the
fractal-displaced course between them, plus the (different) interior control point.
"More than 6 directions" — that's the model.

### 3.2 Rivers must end at lake shores (`ortler_render.py` → `clip_rivers_at_lakes`)
- Each river course is walked vertex by vertex; the **first vertex that lands in a lake
  cell becomes the last vertex** of the course; everything beyond is dropped.
- This is the standing rule: *flowing water must not extend into lakes*. The lake
  surface itself carries no current.
- The loft port of this rule lives implicitly in `overland.loft`'s side-builder:
  inflows-to-the-lake LAND on its surface (`bedB = OV_LAKE_LVL` when `mB == 1`), and the
  side ends at that landing.

### 3.3 The I-FLOW invariant (validation)
- `ortler_import.py` after pit-fill computes `[I-FLOW] uphill fed directions = N/total
  (0 by construction)`. Every river cell's downhill direction points to a strictly lower
  pit-filled neighbour. That's what "water always flows downwards" actually means in the
  Python pipeline.
- In the loft viewer this check **does not run today**, because `river_flow` is not in
  `ortlerdata.loft`. The viewer would have to either compute pit-fill at startup or
  import the precomputed `river_flow` from the npz via the exporter.

---

## 4. The 3D viewer's actual pipeline (the path that runs by default)

`make viewer` (or `make play` with VIEWER_*) lands in `src/viewer.loft::main`. The
*default* branch (no env flags) is the Ortler dual screen — that's the one the user is
asking about.

    main()
      └─ env_variable("VIEWER_OVSHOT") != "1"
         && env_variable("VIEWER_DETAIL") != "1"
         && env_variable("VIEWER_OVERWORLD") != "1"  →  the Ortler default
            ↓
            hd = ort_h()         // 6400 i16 heights
            od = ort_osm()       // 6400 i16 OSM codes
            rd = ort_river()     // 6400 0/1 river mask
            ↓ for each Ortler 32×32 chunk (0..2 × 0..2 covers the 80×80 + margin):
              ca = ortler_chunk(hd, od, rd, cx,   cz,   real)
              ce = ortler_chunk(hd, od, rd, cx+1, cz,   real)   // east neighbour for shared edge
              cs = ortler_chunk(hd, od, rd, cx,   cz+1, real)
              cse= ortler_chunk(hd, od, rd, cx+1, cz+1, real)
              mraw = chunk_mesh_ov(ca, ce, cs, cse)   // 33×33 verts, stride 6 (x,h,z,r,g,b)
              vbuf <- cast each float → single inline (loft#392 workaround)
              vao  = gl_upload_vertices(vbuf, 6)
              gl_upload_indices(vao, idx)             // shared 32×32×2-tri EBO
            ↓
            free-look fly camera; render dual panes (left A=OSM, right B=model bands)
            using one shared shader (VERT/FRAG above) — vertex colour = kind_rgb at the
            hex centre, no texturing, no separate river pass

So the actual emitted 3D geometry is: **a 33×33 heightfield over the 80×80 Ortler grid,
2 triangles per cell quad**, with vertex colour from `kind_rgb(chunk_kind(...))`. River
cells are drawn as a flat-blue cell-square because `kind_rgb(K_RIVER)` returns
`(0.25, 0.45, 0.65)`. There is no per-side river ribbon and no per-triangle OSM
information consumed by the viewer.

Two important consequences of using `chunk_mesh_ov`:

1. **Each Ortler hex contributes exactly one vertex** to the rendered grid (at its hex
   centre). Sub-hex detail cannot be represented. Per-triangle OSM cannot be applied.
2. **The hex-side geometry is absent.** What looks like a side between two adjacent
   river cells is actually the diagonal of a heightfield-grid quad. There is no
   geometric location to attach a river ribbon "along the side".

---

## 5. Where the viewer is **less featured** than the rest of the stack

| Feature | Procedural play (worldmesh + overland.loft) | Python prototype (ortler_render.py + trimesh.py) | **Ortler 3D viewer (today)** |
|---|---|---|---|
| Hex shape preserved in the rendered mesh | yes (6-fan) | yes (18-tri fan) | **no** (heightfield) |
| Per-triangle land class within a hex | n/a (one kind per hex) | yes (`tri_osm`, 18/hex) | **no** (one colour per hex centre vertex) |
| River courses meander (fractal) | yes (`ov_displace`) | yes (`displace + chaikin`) | **no** (rivers are just blue cells) |
| Per-hex hash-jittered interior control point | yes (`ov_vertex`) | yes (`control_pt`) | **no** |
| Canonical edge-crossing point (~0.20 / ~0.80 of side) | yes (`ov_edge_bit`) | yes (`edge_cross`) | **no** |
| Per-segment water width from √accumulation | yes (`OvSide.os_ws`) | yes (`fed_rivers`/`fine_rivers`) | **no** |
| Estuary funnel near sea | yes | yes | **no** |
| Confluence swamp pools | yes (`OvSwamp`) | n/a | **no** |
| Rivers end at lake shores (no current in the still body) | implicit (bed lands on `OV_LAKE_LVL`) | explicit (`clip_rivers_at_lakes`) | **n/a — no rivers** |
| Flow-direction validation (I3 / I-FLOW) | runs in `overlandtest` | runs in `ortler_import.py` after pit-fill | **does not run** |
| Per-cell flow direction usable | yes (`Overland.ov_flow`) | yes (`river_flow` in npz) | **not exported to loft** |
| Per-cell accumulation usable | yes (`Overland.ov_acc`) | yes (recomputed) | **not exported to loft** |

So the gap is broad: the viewer renders only `h`, `osm`, and `river` (as a blue floor)
out of a much richer set of data and behaviours that exists elsewhere in the repo. The
user's standing constraint says this gap should be closed — the viewer should be at
least as featured as `worldmesh + overland.loft` on the procedural side and the Python
prototype on the real-data side.

---

## 6. Why the gap is there

Not because anyone designed it that way — because each piece landed for a different
reason:

- `worldmesh.loft` (6-fan) was authored for the **top-down 2D play view**. It does not
  carry height (`z = 0`), so it's not 3D-renderable as-is.
- `chunk_mesh_ov` was added for **@PLN2 S5d** (the overworld-tier 3D LOD), with the
  explicit assumption "one vertex per overworld hex is enough at coarse LOD." For an
  example 9×7 procedural world that's fine. For 80×80 real Ortler with OSM per
  triangle, it under-uses the data.
- `trimesh.py` (18-tri) was an **@PLN1 evaluation harness**, not a rendering target — it
  computed κ scores against per-triangle OSM, never a GL mesh.
- `overland.loft`'s `OvSide` / `ov_edge_bit` / `ov_displace` was authored for the
  **procedural overland** (the contract example world). The Ortler real-data pipeline
  doesn't pass through `overland_new()` — it bypasses it (`ortler_chunk` builds a
  `DetailChunk` directly from `ort_h`/`ort_osm`/`ort_river`), so the river polylines
  never get built for the Ortler case.

The exporter is the first chokepoint that drops information; the viewer is the second.

---

## 7. The upgrade direction (proposal, not yet implemented)

The smallest change that closes the gap without losing anything currently in the viewer:

### 7.1 Extend the Ortler exporter
`plans/1-ortler-worldgen-fixture/export_ortler_loft.py` is the single source for what
loft sees about the real Ortler. Add:

- `ort_river_flow()` — `vector<integer>` of length 6400, value = the precomputed
  downhill neighbour direction (0..5) at each river-mask cell, −1 elsewhere. Already
  exists in `ortler_hexes.npz` as `river_flow` (i8) — just re-emit it.
- `ort_acc()` — `vector<float>` of length 6400, flow accumulation per cell. Computed
  the same way as the Python `fed_rivers` does (high-to-low cell sweep over `flow`).
  Used both for river width (∝ √acc) and for the I-FLOW validation.
- `ort_triosm()` — `vector<integer>` of length 115200 = 6400×18 (10 KB ints; row-major
  c-major-by-hex-then-tri-local to match the existing `_tri_gid` convention so the per-
  triangle classes line up bit-for-bit with `ortler_render.py`). Already exists in
  `ortler_triosm.npz`.

Pit-fill is already done in Python; the exported `river_flow` is by construction
downhill on the pit-filled surface, so I-FLOW = 0 / total without any extra work in
loft.

### 7.2 Add a 18-tri-per-hex mesh builder in loft
A NEW module `src/orttrimesh.loft` (or an addition to `chunkmesh.loft`) mirroring
`trimesh.py`:

- `hex_19_verts(c, r) -> (xs, zs)` — the 19 (x, z) coordinates of one hex's mesh
  vertices (centre, 6 corners, 12 edge-thirds), using the existing `hex_grid::SQRT3`
  lattice so corners are bit-identical with `worldmesh.loft`'s 6-fan. **I-MESH watertight
  by construction** — corner shared by 3 hexes, edge-third by 2.
- `hex_19_heights(hd, c, r) -> hs` — heights at each of the 19 vertices, computed by
  averaging the relevant hex-centre heights (corner = avg of the 3 incident centres;
  edge-third = ⅔·this + ⅓·that). For 80×80 the per-vertex EU-DEM samples are absent;
  averaging the centres is the watertight stand-in (a refresh path could pull the 40×40
  EU-DEM if/when its grid resolution is increased).
- `chunk_mesh_tri(hd, od_tri, cx, cz) -> vector<float>` — 18 triangles × 3 vertices ×
  6 floats (x, h, z, r, g, b) per hex in this chunk. Per-triangle colour from
  `kind_rgb(ort_osm_kind_for_triangle(...))`, using `ort_triosm()` indexed by global
  triangle id `(c·ROT + r)·18 + loc`. Same final stride-6 shader interface as
  `chunk_mesh_ov`, so the viewer's draw loop doesn't change.

### 7.3 River ribbon as a separate textured pass
Mirroring `build_wall_mesh` (which is already a textured-quad-per-segment pattern in
`worldmesh.loft`):

- For each river cell `(c, r)` with `ort_river_flow != −1`, get the downstream cell
  `(nc, nr)` via `hex_neighbor(c, r, ort_river_flow[i])`. Validate:
  `ort_h[downstream] < ort_h[upstream]` for **every** cell. Count violations to stdout
  at startup. Per the I-FLOW invariant after pit-fill, this should print `0/N`.
- Build a polyline `control(c,r) → edge_cross(c,r,nc,nr) → control(nc,nr)` per segment,
  using the same `ov_vertex` / `ov_edge_bit` rules already in `overland.loft` (just at
  the Ortler 1500 m hex pitch). Run `ov_displace` over it. (Lake-end trim: if the
  downstream cell is K_LAKE / K_SEA, end the segment at the edge-cross — exactly what
  `clip_rivers_at_lakes` does.)
- Emit a textured quad strip per segment, stride 8 (x, h, z, r, g, b, u, v), elevated
  by a small ε above terrain to avoid z-fighting. Width per point: `w_base +
  w_scale · √acc[cell]`. UV.x runs 0..1 along the segment length; UV.y runs across the
  ribbon.
- New shader: textured + alpha-blended (`graphics::gl_blend_func(BLEND_SRC_ALPHA,
  BLEND_ONE_MINUS_SRC_ALPHA)`). Sample `assets/sprites/river_line.png` — a tileable
  strip with tapered alpha so the ribbon edges fade into the terrain (the same look the
  Python `render_window` produces from `width`).
- The `river_line.png` is the "separate river texture you can place on a triangle"
  — its UV.y range chosen at sample time controls width visually, so the texture itself
  doesn't need to be regenerated per river size.

### 7.4 The validation, on the viewer
At startup, after `ort_river_flow()` lands:

    println("river flow: N cells; M with downhill exit; K uphill (want 0)");

If K > 0 the cells are listed (q, r, self_h, target_h). This is the I-FLOW check, run
inline (no separate test file).

### 7.5 What this preserves from today
- The free-look camera, the dual-pane A/B, the `VIEWER_*` modes (OVSHOT / DETAIL /
  OVERWORLD / TALUS / ORTSHOT / FLYKEYS), the existing shaders, the headless screenshot
  path, all stay as-is.
- The right-pane B (model bands) still uses `ort_model_kind(h)` per centre — there is no
  per-triangle data for the model bands; that pane stays a one-vertex-per-hex view
  *intentionally* (it shows what the elevation-band model produces, which is
  hex-resolved by definition).
- The talus / detail / overworld views can keep `chunk_mesh` / `chunk_mesh_ov`; the new
  18-tri path is only the Ortler default.

### 7.6 What this does NOT do
- It does not refetch the 40×40 trimesh per-vertex EU-DEM at 80×80 resolution. Heights
  at sub-hex vertices stay as the watertight neighbour-average. (A separate task would
  pull EU-DEM at the full set of 80×80 vertex points; ~4× the OpenTopoData calls of the
  current 40×40 fetch.)
- It does not change the procedural-world path. `worldmesh.loft`'s 6-fan stays; the new
  18-tri builder is additive.

---

## 8. Stretch — taking the procedural world further too

If parity with `overland.loft`'s river system is the bar, the 2D play view's
`build_world_mesh` could also gain the 18-tri-per-hex subdivision (today it's
6-fan per hex, so per-triangle inside-hex OSM has nowhere to live). That's a separate
piece of work — the immediate gap is the Ortler 3D viewer, where the data already exists
on disk and is being silently dropped at the loft boundary.

---

## 9. Architecture: loft owns the data, multi-region from day one

Per the user (2026-06-17): the derivations AND the writing of loft data files live in
loft, not Python. The pipeline supports **many regions** (Ortler is one; sea-cliff
coasts of Wales is another; more will follow) and is built so future loft analyses
read the *same* base data the renderer does.

### 9.0 Pipeline shape

    raw download (HTTP, today via Python)            ─── Python step ───
            ↓                                                  ↑
    data/regions/<name>.bin  ←── one-time conversion ──────────┘  (no .loft writing)
            ↓
    [LOFT]  src/realworld/region_io.loft   reads .bin → in-memory Region
    [LOFT]  src/realworld/build_region.loft writes src/regions/<name>.loft
            ↓
    src/regions/<name>.loft   committed literal-array module
            ↓
    `use regions::<name>;`    every consumer (viewer, mesh builders, analyses)
            ↓                 — loft's program cache mmaps the compiled bytecode +
                              constants on every launch (zero-cost re-loads).

**Python writes no `.loft` file.** Its single remaining responsibility is to convert
the NPZ artefacts of the current download tooling (`plans/1-ortler-worldgen-fixture/
ortler_import.py`) into a flat little-endian binary at
`data/regions/<name>.bin`. The eventual full-loft path replaces that step with loft
HTTP fetches (`use web; http_get(opentopodata_url)` + `json_parse`), at which point the
Python disappears entirely; the on-disk `.bin` format stays as the cache hand-off.

### 9.1 The per-region binary format (`data/regions/<name>.bin`)

A single little-endian file per region. The same format works for Ortler, Wales-coast,
and every future region; only the array lengths change.

    offset       size          field            type    notes
    ---------------------------------------------------------------------------
    0            4             magic            i32     'RGN1' = 0x31_4E_47_52
    4            4             schema_version   i32     1 (bumped on layout change)
    8            4             cols             i32     hex grid columns
    12           4             rows             i32     hex grid rows
    16           4             v_cols           i32     trimesh columns (0 if none)
    20           4             v_rows           i32     trimesh rows    (0 if none)
    24           4             n_verts          i32     trimesh unique vertices
    28           4             reserved         i32     pad to 32 — future flags

    32                         hex_h            i16 × cols·rows
                               hex_osm          i16 × cols·rows
                               hex_river        i16 × cols·rows
                               tri_osm          i16 × cols·rows·18
                               vert_x           f64 × n_verts
                               vert_y           f64 × n_verts
                               vert_h           i16 × n_verts
                               vert_tris        i32 × v_cols·v_rows·18·3

Layout invariants:

- Arrays are *dense and consecutive* — no padding between sections beyond the i32
  alignment after the header. Loft's `f#read(N)` returns N bytes interpreted per the
  set `f#format` (LittleEndian).
- Section sizes are fully derivable from the header. The schema version lets a future
  field be added by bumping it and gating new sections on `schema_version >= 2`.
- For regions with no trimesh (e.g. a quick coastline-only dataset), `n_verts = 0` and
  the four `vert_*` sections are empty (length 0).

### 9.2 The loft side (NEW modules under `src/realworld/`)

Three small modules and a builder, all in loft:

    src/realworld/
      region.loft        — generic in-memory Region struct + accessors
      region_io.loft     — read .bin, write .loft (numeric literals)
      build_region.loft  — main(): read data/regions/<name>.bin,
                                   write src/regions/<name>.loft

| module | exports |
|---|---|
| `region.loft` | `pub struct Region { name, cols, rows, v_cols, v_rows, hex_h, hex_osm, hex_river, tri_osm, vert_x, vert_y, vert_h, vert_tris }`. Accessors `region_height(r, q, r) -> integer`, `region_osm(r, q, r)`, `region_river(r, q, r)`, `region_triosm(r, c, r, loc)`, `region_vert_h(r, vid)`, `region_vert_xy(r, vid) -> (float, float)`. |
| `region_io.loft` | `pub fn region_read_bin(path: text) -> Region` (opens `f#format = LittleEndian`, reads header + arrays). `pub fn region_write_loft(r: Region, out_path: text)` writes a `src/regions/<name>.loft` containing `pub fn rgn_<name>_h() -> vector<integer> { [...] }`, etc. — plain numeric-literal accessors so consumers can either `use regions::<name>` directly or load via the generic `Region` reader. |
| `build_region.loft` | `fn main()`: reads `LOFT_REGION` env var (defaults to "ortler"), runs `region_read_bin("data/regions/{name}.bin")` then `region_write_loft(rgn, "src/regions/{name}.loft")`. |

The committed `src/regions/<name>.loft` files are what every consumer `use`s. Loft's
program cache mmaps the compiled bytecode + constants on every launch, so the
literal arrays are zero-cost lazy reads. The "if missing, create it" step is
`make region REGION=<name>`; the file is regenerated only when the source `.bin`
changes.

### 9.3 Why this fits the user's three constraints

| constraint | how this design hits it |
|---|---|
| "remove the Python that writes this data" | Python no longer touches `.loft` files. Its only remaining job is NPZ → `.bin` (the existing downloaded artifacts). Once loft HTTP fetch lands, that step also disappears. |
| "many future analyses on the base data" | Every analysis program just `use regions::ortler` (or `wales`, etc.). The base data is one stable schema; new analyses add new modules, never new exporters. |
| "other maps than Ortler — Wales sea cliffs etc." | Drop `data/regions/wales.bin` (from the download tooling), run `make region REGION=wales`, commit `src/regions/wales.loft`. The Region struct is map-agnostic; mesh builders / hydrology / renderer take a `const Region` and just work. |

### 9.4 The analysis modules (region-agnostic)

| module | responsibility | key APIs |
|---|---|---|
| `src/realworld/hydro.loft` | hydrology derivations | `pitfill(r: Region)` (priority-flood with flats-epsilon), `flow_dir(filled)` (steepest descent per cell), `flow_acc(filled, flow)` (high-to-low sweep), `validate_flow(r, flow)` (the I-FLOW assertion: every river cell's flow target is strictly lower) |
| `src/realworld/trimesh.loft` | 18-tri-per-hex mesh builder, watertight | `tri_vertex_xy(r: Region, c, r, k)` for k ∈ 0..18 (0=centre, 1..6=corners, 7..18=edge-thirds), `tri_vertex_h(r, c, r, k)` (corner = avg of the 3 incident centres, edge-third = ⅔/⅓ blend — watertight by I-MESH), `chunk_mesh_tri(r, cc, cr)` → stride-6 VBO of 18 triangles per hex |
| `src/realworld/rivers.loft` | river polyline + ribbon mesh (§3.1/§3.2 rules) | `river_polylines(r, flow, acc)` returns one segment per cell-to-cell hop, built control→edge_cross→control with `ov_displace` displacement, **trimmed at lake/sea cells**. `river_mesh(polylines)` → stride-8 VBO for the textured pass. |

Every analysis takes `const Region` as its first arg — same module works for Ortler,
Wales-coast, and anything that follows.

### 9.5 Validation report (printed at viewer startup)

    region: ortler  (80×80 hexes, 14878 trimesh verts)
    river flow: 65 cells; 65 with strict-downhill exit; 0 uphill (I-FLOW PASS)

If the count is non-zero, each violating cell prints `(q, r, h_self, h_target, dir)`.
This runs once, before the render loop opens.

---

## 10. Analyses, near-term and stretch

Every analysis is a loft module that consumes a `const Region`. Adding one is purely
additive — no Python step, no schema change. Examples in flight or planned:

| analysis | what it does | status |
|---|---|---|
| hydrology (§9.4) | pit-fill + flow-direction + accumulation; the I-FLOW gate | next |
| 18-tri mesh + per-tri OSM | render rocks/forest/water boundaries inside each hex | next |
| river polylines + ribbon mesh | the §3 rules in loft, multi-region | next |
| **match the actual rock formations** | cliff geometry from the real EU-DEM relief + OSM rock polygons | stretch (§10.1) |
| coastline geometry from `natural=cliff` | sea-cliffs of Wales: a thin OSM way → faceted ribbon | future (Wales region) |
| forest-canopy / treeline analytics | per-region tree-stand statistics | future |
| watershed catchment maps | per-river accumulation basins from `flow_acc` | future |

### 10.1 The "actual rock formations" analysis

The user's stretch goal: rock cells shouldn't render as a flat per-hex colour or a flat
heightfield cell — they should reflect the **actual cliff and rock-zone shapes** from
the OSM data, with the real EU-DEM relief carrying the cliff steps.

### 10.2 Two ingredients needed

1. **Per-triangle OSM at fine enough resolution** to resolve cliff edges. The 80×80
   grid gives ~250–750 m per sub-hex triangle; real cliffs are typically < 100 m wide,
   so the present per-triangle pass is the limit of the data, not the limit of the
   renderer. To resolve below that, loft would need the raw OSM polygons (a re-fetch
   of the Overpass query, stored in `osm_polys.npz` and emitted to loft), and a
   `point_in_poly` test loft-side, so the mesh can refine per-pixel at the cliff
   boundary without re-asking Overpass.
2. **Real EU-DEM at every mesh vertex.** At 80×80 we currently have heights only at
   hex centres — `ort_h`. Corner / edge-third heights are watertight averages, but they
   *don't carry real cliff steps*. The 40×40 `ortler_trimesh.npz` already has real
   per-vertex EU-DEM and the topology — using it as the viewer's source for the
   "match the rock" mode is the cheapest first step. A future fetch can pull EU-DEM at
   the 80×80 sub-hex vertex set (~60k points; well over the 1000/day OpenTopoData
   free-tier cap, so this needs batching across days or a paid endpoint).

### 10.3 Render path

With (1) + (2) in place, the cliff render is the talus model **applied to real data**,
not procedural: walk the per-vertex EU-DEM, and where the bedrock step between two
adjacent mesh vertices exceeds the cliff angle, emit a vertical *face quad* down the
step (analogous to `K_FACE` in `talus.loft`). Where the step is shallower than the
repose angle but the OSM polygon labels the area `bare_rock` / `scree`, mark the
triangle accordingly. The mesh then *shows* the cliff as geometry, not as colour.

### 10.4 What this doc does NOT commit to yet

The §10 path involves either a multi-day data refetch or a paid EU-DEM source. The
present implementation gate is **§7 + §9** (loft consumes the raw point-sampled data we
already have on disk, derives everything else, renders 18 tri / hex with per-triangle
OSM + river ribbons). §10 is recorded as the destination, not the next step.

---

## 11. Implementation order (dependency tree, each step independently verifiable)

1. **Python NPZ → `.bin`** — `plans/1-ortler-worldgen-fixture/dump_region_bin.py`
   converts the existing NPZ artefacts to `data/regions/ortler.bin` with the §9.1
   layout. Python writes **no `.loft` file any more.**
2. **`src/realworld/region.loft` + `region_io.loft` + `build_region.loft`** — the
   loft side: read the `.bin`, write `src/regions/<name>.loft`. `make region
   REGION=ortler` runs it; `src/regions/ortler.loft` is the committed output.
3. **`src/realworld/hydro.loft`** — pit-fill / flow / accumulation / validation.
   Takes `const Region`. Verifiable stand-alone (run from the viewer at startup, print
   the I-FLOW counts).
4. **`src/realworld/trimesh.loft`** — the 18-tri-per-hex mesh builder. Takes `const
   Region`. Verifiable: triangles emitted == `cols·rows·18`; a sample corner refcount
   == 3 in an interior hex.
5. **viewer wiring** — replace `chunk_mesh_ov` in the Ortler default branch with
   `chunk_mesh_tri`. Stride stays 6 so VERT/FRAG don't change. Pane A's colour comes
   from `region_triosm(...)`, pane B from `ort_model_kind` per centre (broadcast
   across the 18 triangles of each hex, so B continues to look like the present
   model-bands view). The viewer takes the region as an env var (`VIEWER_REGION`)
   defaulting to ortler.
6. **`assets/sprites/river_line.png`** — a small tileable strip (a Python blueprint in
   `tools/blueprints/river_line.py` that generates the PNG and writes a tiny
   PASS/FAIL report on alpha taper / tileability, mirroring the existing blueprints).
7. **`src/realworld/rivers.loft`** — river polyline builder (control + edge_cross +
   ov_displace + lake-shore trim) and the textured ribbon mesh (stride-8 VBO + UVs).
8. **river overlay pass in viewer** — second shader (textured + alpha), drawn AFTER
   terrain with depth-test on / depth-write off, blend on. The river_line texture
   sampled by UV.y range (width control on the fly).
9. **Wales-coast region (validates the multi-region claim)** — drop
   `data/regions/wales.bin`, run `make region REGION=wales`, run `make viewer
   VIEWER_REGION=wales`. No source changes in viewer/hydro/trimesh/rivers.
10. (deferred — §10.1) — real per-vertex EU-DEM at the 80×80 sub-hex set and the rock-
    formation cliff geometry.
11. (deferred) — replace the Python NPZ-to-bin step with loft HTTP fetch
    (`use web; json_parse`), so the entire pipeline is loft.

Each step is one self-contained PR; after each one, the viewer is at least as featured
as it was before, never less.
