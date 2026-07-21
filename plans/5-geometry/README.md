# 5 — Geometry: the 24-direction outline engine + multi-layer towers & walls

**Issue:** [`jjstwerff/crawler#5`](https://github.com/jjstwerff/crawler/issues/5) ·
**Value:** `F` · **Effort:** `VH`

## Status

**Future — neither track has landed.** Both are design-complete enough to start, and
`wallgeo.loft`'s corner-graph smoother is today's stand-in. This plan **blocks the
theme-bundles plan (#4) Phase G**: themed structures need doors, jambs and round forms
before their shapes can move bundle-side.

## Blueprint gate

Exact-invariant work throughout, so CLAUDE.md's design/debug protocol governs every
step: a **concrete plotted end-result** first, then the named invariant, then the loft
port — never the other way round. `tools/wallproto` is the proven medium and the
triangle-wall saga is the cautionary precedent (a small fix behind a large discovery
cost, only pinpointable *after* the Python verify phase).

---

Two big features, planned per the design/debug protocol (exact-invariant work →
BLUEPRINT PHASE in the cheapest medium, a CONCRETE plotted end-result per step,
invariants pinned before the loft port). Anchors that already exist: **WALLS.md**
(the triangle-band wall model, validated in `tools/wallproto`), **DESIGN §9**
(the one-processor outline table: dir-resolution × junction-policy), **STENCILS.md**
(kernel = layered truth, the 2D view renders the current layer, the flood-fill
gating test), `wallgeo.loft` (today's corner-graph smoother).

## The visual-confirmation channel (how Claude verifies, every step)

GL screenshots are unreliable in the sandbox (CLAUDE.md), so geometry is confirmed
by **plotting the kernel's own output to PNG** — the same segments/arcs/layer grids
the view draws, so what Claude confirms is what the renderer consumes:

1. **Blueprint steps (Python)** — the prototype plots PNGs directly
   (`tools/wallproto/out/` pattern, PIL). Claude Reads the PNG and critiques it
   against the pinned target.
2. **Loft steps (the port)** — a headless dump tool `src/geodump.loft` prints the
   outline set / layer planes for a seed as plain text; `tools/plot_geo.py` renders
   that dump to PNG (floor-light/wall-dark palette, per CLAUDE.md readability
   rules). Claude Reads it and compares against the SAME pinned target the
   blueprint used — port fidelity is *visible*, not just asserted.
3. Golden-fixture tests pin coordinates numerically (`*test.loft`, ε-compare);
   the PNG is the semantic check on top (shape, junctions, no gaps/overlaps).
4. **The user stays the live-frame verifier** — composition in the running game
   (`make play`) is the final acceptance; Claude's PNG pass happens first and
   catches geometry errors before a human ever looks.

---

## Track 1 — full 24-angle support + round structures

Goal: walls/roads/fences in **24 directions (k·15°)**; **round structures**
(towers tile 4) rendered as TRUE circles; **attachment** — a circle meets a
straight band tangentially (no gap, no stub); **roads get correct outlines**
(parallel offset faces, rounded junctions); **fences** (tile 5) get the same
angle vocabulary as thin bands.

### Step 1.0 — BLUEPRINT (Python, extends `tools/wallproto`)
Concrete plotted end-results (candidates below are seeded in
`tools/wallproto/out/target_*.png` — **user confirms or amends before any port**):
- **T1 `target_curtain.png`** — a curtain-wall polyline with 15°-snapped legs and
  a **round corner tower at each bend**: the band's faces terminate ON the circle
  at the tangent points (the wall "plugs into" the tower).
- **T2 `target_road.png`** — a road centerline in 24 directions with **parallel
  offset outlines** (±w/2) and **rounded junctions** (arc fillets), plus a fork.
- **T3 `target_fence.png`** — a fence polyline at odd 15° angles attached to a
  building corner (thin band; posts as dots at the snap vertices).
- **T4 `target_door.png`** — a building wall with a DOOR: the gap in the band is
  capped by clean perpendicular JAMBS (engine-rendered — sprites carry no
  architecture, per CLAUDE.md), a door leaf fits the gap exactly (rotated to the
  wall direction), and the SAME gap WITHOUT a leaf still reads as a deliberate
  entrance (capped jambs + threshold), never a ragged hole.

Invariants to pin (each gets an assert in the prototype before the port):
- **SNAP**: every emitted face direction = k·15° exactly.
- **OFFSET**: each face point lies exactly ±w/2 from the centerline (roads, bands).
- **TANGENCY**: circle↔band attach — the face endpoint lies on the circle AND the
  face direction ⟂ the radius at that point (|dot| < ε); no face penetrates the
  circle interior.
- **CLOSURE**: every structure outline is a closed loop (or terminates on another
  structure — attachment is the only legal open end).
- **COLLISION=RENDER**: the triangle band (WALLS.md model) and the rendered faces
  classify the same area (sampled agreement on a fine grid).
- **JAMB**: every band gap (door/entrance) is capped: a segment ⟂ the band's
  centerline joins inner face to outer face at BOTH gap ends; the gap width is
  exact (the leaf must fit); cap directions are in the 24-snap set too.

### Step 1.1 — kernel data model: outline SPECS beside the tiles
Today `stamp_round_tower`/walls/roads write only tiles; the circle is forgotten.
Add a spec record on the Sim (flat arrays + count — the loft#320 idiom):
`feat_kind` (wall/road/fence/tower), `feat_x/y/x2/y2/radius/width`, dir-res +
junction policy per kind (the DESIGN §9 table). gen/sim stamping RECORDS the spec
it stamps (tower → center+radius; town wall → polyline legs; road → centerline;
fence → polyline). Tiles stay the hex-collision truth; specs are the outline
engine's input. Test: every tile-4 ring has a recorded circle; every road tile is
within w/2 of a recorded centerline (`outlinetest.loft`, part 1).

### Step 1.2 — the outline engine (kernel, no graphics): `outline.loft`
Port the blueprint: specs → **segments + arcs**. Band faces from centerlines
(±w/2), **miter** at sharp junctions, **arc fillets** at rounded ones,
**tangent-attach** for circles, full circles for free-standing towers.
**Doors/entrances**: a gap in the band emits its two JAMB cap segments
(inner→outer face, ⟂ centerline) so an opening reads cleanly with or without a
leaf. Output: `OutSeg` (like `WallSeg`) + `OutArc {cx, cy, r, a0, a1}`.
Test: golden fixtures exported by the Python blueprint (same input spec → same
coordinates, ε = 1e-3) + the five invariants re-asserted in loft
(`outlinetest.loft`, part 2). The dungeon's carved-rock outline stays on today's
`wallgeo` path — two paradigms coexist (WALLS.md).

### Step 1.3 — geodump + plot = Claude's eye
`src/geodump.loft` (headless): build a seed's surface, print specs + outline
segments/arcs as text. `tools/plot_geo.py`: dump → PNG. Claude renders the three
target scenes IN-ENGINE (the fortress with its 4 corner towers, the town wall,
a road run, the farmers' fences) and confirms against T1–T3. This artifact is
permanent — every later geometry change re-runs it.

### Step 1.4 — view wiring (the only graphics step)
The view consumes `OutSeg` exactly like `WallSeg` today; **arcs** get a chord-fan
draw (N chords per arc, N by radius — a new small helper beside the segment
draw). Tile-4 hexes STOP emitting hex-boundary wobble (skipped in `wallgeo`) —
the circle replaces them. Roads draw their outline strokes over the tint;
fences draw as thin 24-snapped lines with posts. Doors: the leaf is a sprite
sized/rotated to the gap (the engine's jambs frame it — the sprite carries no
stonework); a doorless entrance renders as the capped opening alone. Verify: `make check`, gate
green, geodump-PNG unchanged (the view consumes, never reshapes), THEN the user
plays a fortress/town/road seed and judges the live frame.

### Step 1.5 — consistency hardening
One test asserting spec↔tile agreement on every generated surface seed of the
gate (no circle without its tile-4 ring, no band face crossing open floor)…
and the fences' gate-gaps + the towers' doors stay open in the outline
(door = a gap in the band, per WALLS.md).

---

## Track 2 — multi-layered towers & walls

Goal: the castle pillar from STENCILS.md — **a tower you climb** (ground →
upper → rampart), **a curtain wall with a walkable top**, content gated by
traversal (sealed at ground, open from above). Kernel carries TRUE stacked
layers (the model `moros_render` will draw); the 2D view renders the player's
current layer.

### Step 2.0 — BLUEPRINT (Python, new `tools/layerproto.py`)
Concrete plotted end-result (candidate seeded as
`tools/wallproto/out/target_layers.png` — user confirms/amends):
- one castle drawn as **two panes**: layer 0 (ground: gate, tower footprints
  solid, keep sealed) and layer 1 (rampart: walkable wall-top floor, tower
  upper floors, parapet edges, the ladder/stair cells marked) + the intended
  traversal path drawn through both panes.
Invariants to pin:
- **GATING**: ground-layer flood-fill does NOT reach the keep interior; the
  rampart-route flood-fill DOES (THE test, straight from STENCILS.md).
- **LINKS**: layer transitions exist ONLY at stair/ladder features; flood-fills
  per layer otherwise independent.
- **ROUND-TRIP**: save/checkpoint of a layered Sim = identity (serialization is
  exact-invariant work — pin it BEFORE the port).
- **L1-DEFAULT**: a single-layer world is bit-identical to today (the entire
  existing gate is the regression net).

### Step 2.1 — the kernel layer axis
Tiles become the STENCILS-pinned flat layout `(L·h + y)·w + x` with `L = 1`
default (today's worlds unchanged); player gains `lay`; `is_wall`/movement/
FOV/collision take the active layer; **ladder/stair-up/down tile codes**
transition `lay` (same feature pattern as `>`/`<`, transitioning layer not
depth). Enemies gain `lay`; adjacency/combat require same layer.
Test: `layertest.loft` — the GATING flood-fill assertion + L1-DEFAULT (a depth-1
dungeon byte-compares against the pre-layer snapshot) + the save ROUND-TRIP.

### Step 2.2 — gen/stamp grows UP
`stamp_round_tower` gains height: ring solid at layer 0, floor + parapet ring at
layer 1, an interior ladder cell; the curtain wall becomes the DESIGN §9 2-hex
band — wall at ground, floor on top, parapet edges; the gate tower carries the
stairs. The fortress + the big town wall upgrade to it. Test: gen-level
assertions (every rampart cell reachable from a gate stair; parapet never
walkable from outside).

### Step 2.3 — actors on layers
Guards' patrol legs (`wq2/aq2`) gain the rampart: wall-top patrol routes are
REAL paths on layer 1 (today they walk beside the wall). Monsters cannot cross
layers without a link; ranged/gaze respects layer (a rampart archer sees down —
gameplay call recorded in the step, default: same-layer only first).
Test: a guard completes a rampart circuit headlessly; a ground monster cannot
reach a rampart NPC without taking the stairs.

### Step 2.4 — the view renders the current layer
View draws the player's layer plane; cells OPEN above ground show the dimmed
ground floor under them (a nicety, not a blocker — STENCILS.md); HUD gains a
layer indicator; ladder/stair sprites (the `draw` skill, per the sprite rules).
geodump gains a `--layer` pane so Claude confirms each plane + the gating path
as PNGs (the 2.0 target re-rendered from the REAL kernel).

### Step 2.5 — outline integration (the tracks meet)
Parapets + tower rims outline through the Track-1 engine (arcs for tower tops,
24-dir parapet edges). The castle scene re-plots as the FINAL target: both
panes, true circles, straight curtains — Claude's last PNG pass, then the
user's live-frame acceptance walk (climb, cross, drop in).

---

## Order & dependencies

- 1.0 → 1.1 → 1.2 → 1.3 → 1.4 → 1.5 (strict).
- 2.0 → 2.1 → 2.2 → 2.3 → 2.4 (strict); 2.5 needs Track 1 done.
- The tracks are independent until 2.5 — interleave at will; suggested: 1.0–1.3
  first (the engine, fully confirmable headlessly), then 2.0–2.1 (the kernel
  axis, biggest regression risk, wants the calmest tree), then alternate.

## Standing risks / loft notes

- All new hot collections: pre-allocated array + count + index-write (loft#320).
- No thin arity-reducing pub wrappers around `Sim`-returning fns (loft#339).
- Text tables as branch-selector fns (loft#336).
- The layered tile array changes `Sim`'s biggest field — watch store pressure
  habits (one Sim live at a time) and keep the save round-trip test FIRST.
- Kernel stays graphics-free: `outline.loft`/layer code import no `graphics::`;
  arcs reach the view as data (the architecture invariant).
