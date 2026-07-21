#!/usr/bin/env python3
"""dump_region_bin.py — convert the plan #1 NPZ artefacts to data/regions/<name>.bin.

This is the ONLY remaining Python in the data pipeline; per the user's standing rule
(doc/viewer-design.md §9), loft owns reading the binary AND writing the .loft data
modules. Future work replaces even this step with loft HTTP fetches.

The on-disk layout matches doc/viewer-design.md §9.1 exactly so
src/realworld/region_io.loft can read it with no surprises:

    offset       size          field            type    notes
    ---------------------------------------------------------------------------
    0            4             magic            i32     'RGN1' = 0x31_4E_47_52
    4            4             schema_version   i32     1 (bumped on layout change)
    8            4             cols             i32     hex grid columns
    12           4             rows             i32     hex grid rows
    16           4             v_cols           i32     trimesh columns (0 if none)
    20           4             v_rows           i32     trimesh rows    (0 if none)
    24           4             n_verts          i32     trimesh unique vertices
    28           4             reserved         i32     pad to 32

    32                         hex_h            i16 × cols·rows
                               hex_osm          i16 × cols·rows
                               hex_river        i16 × cols·rows
                               tri_osm          i16 × cols·rows·18
                               vert_x           f64 × n_verts
                               vert_y           f64 × n_verts
                               vert_h           i16 × n_verts
                               vert_tris        i32 × v_cols·v_rows·18·3

Run from the repo root:  python3 plans/1-ortler-worldgen-fixture/dump_region_bin.py
                         (defaults to ortler; --region NAME picks a different fixture)
"""
import argparse, struct
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NPZ_DIR = HERE / "data"
BIN_DIR = REPO / "data" / "regions"

MAGIC = 0x314E_4752      # 'RGN1' little-endian
SCHEMA_VERSION = 1


def dump_ortler() -> Path:
    """Pack the three Ortler NPZs into data/regions/ortler.bin (§9.1 layout)."""
    hex_npz = NPZ_DIR / "ortler_hexes.npz"
    tri_npz = NPZ_DIR / "ortler_triosm.npz"
    mesh_npz = NPZ_DIR / "ortler_trimesh.npz"

    hd = np.load(hex_npz)
    h = hd["h"].astype(np.int16)
    osm = hd["osm"].astype(np.int16)
    river = hd["river_mask"].astype(np.int16)
    cols, rows = int(hd["cols"]), int(hd["rows"])
    assert h.shape == (rows, cols) == osm.shape == river.shape

    td = np.load(tri_npz)
    tri_osm = td["tri_osm"].astype(np.int16)
    assert int(td["cols"]) == cols and int(td["rows"]) == rows
    assert tri_osm.shape == (cols * rows * 18,)

    md = np.load(mesh_npz)
    v_cols, v_rows = int(md["cols"]), int(md["rows"])
    vert_x = md["verts"][:, 0].astype(np.float64)
    vert_y = md["verts"][:, 1].astype(np.float64)
    vert_h = md["height"].astype(np.int16)
    n_verts = len(vert_h)
    # mtris is (NH, 18, 3) i32; the loft side reorders by (c, r) major to keep the
    # gid = (c·v_rows + r)·18 + loc convention from ortler_render.py / orttridata.
    hexcr = md["hexcr"]
    hexrank = {(int(c), int(r)): i for i, (c, r) in enumerate(hexcr)}
    ord_tris = np.empty_like(md["tris"])
    for c in range(v_cols):
        for r in range(v_rows):
            ord_tris[c * v_rows + r] = md["tris"][hexrank[(c, r)]]
    vert_tris = ord_tris.astype(np.int32).reshape(-1)

    BIN_DIR.mkdir(parents=True, exist_ok=True)
    out = BIN_DIR / "ortler.bin"

    header = struct.pack("<8i", MAGIC, SCHEMA_VERSION, cols, rows,
                         v_cols, v_rows, n_verts, 0)
    with open(out, "wb") as f:
        f.write(header)
        f.write(h.reshape(-1).tobytes())          # cols·rows i16
        f.write(osm.reshape(-1).tobytes())        # cols·rows i16
        f.write(river.reshape(-1).tobytes())      # cols·rows i16
        f.write(tri_osm.tobytes())                # cols·rows·18 i16
        f.write(vert_x.tobytes())                 # n_verts f64
        f.write(vert_y.tobytes())                 # n_verts f64
        f.write(vert_h.tobytes())                 # n_verts i16
        f.write(vert_tris.tobytes())              # v_cols·v_rows·18·3 i32

    kb = out.stat().st_size / 1024
    print(f"wrote {out.relative_to(REPO)}  ({kb:.1f} KB)  "
          f"{cols}x{rows}  v={v_cols}x{v_rows}  n_verts={n_verts}")
    return out


REGION_DUMPERS = {"ortler": dump_ortler}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--region", default="ortler",
                   help="Region name to dump (default: ortler)")
    args = p.parse_args()
    dumper = REGION_DUMPERS.get(args.region)
    if dumper is None:
        raise SystemExit(f"unknown region: {args.region}; "
                         f"known: {sorted(REGION_DUMPERS)}")
    dumper()
