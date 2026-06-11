# OVERLAND.md — the overland hex grid: terrain source, seamless merge, rivers first

Status: **DESIGN + BLUEPRINT PHASE** (no loft yet — per the design/debug protocol this is
exact-invariant work: pin it in Python, then port). Companion docs: DESIGN.md (§ roadmap),
loft-libs-world/CONVERGENCE.md (the hex_* family this feeds), BUNDLE.md (the seam rules).

## 1. Goals (what this layer must deliver)

1. **Terrain comes FROM a macro overland hex grid** — a coarse lattice of big tiles is the
   single source of truth for the outdoor world. Each overland tile is authorable content:
   drawable as pixels (one px = one overland hex → a continent fits in one PNG) and
   assignable by bundles.
2. **Two adjacent overland tiles merge into a seamless whole** — no visible seam, border,
   or stitch line anywhere at the fine (walked) scale. Seamlessness is a *construction
   property*, never a post-pass.
3. **Rivers are first-class and never straight.** Water flow is computed on the overland
   graph, but the *actual course* is fractal: meanders, with curvature growing as the land
   flattens toward the sea. **The landscape forms itself around the rivers** — valleys
   carve around the course, moisture/biome follow it — not rivers painted on top of
   finished terrain.
4. **The fine world stays the existing game**: the 1.5 m hex movement lattice, the 60 m
   sim blocks, the distance-driven clock, bundles for content. The overland layer feeds
   them; it does not replace them.
5. **Multiplayer/persistence-ready by determinism**: every fine value is a pure function
   of (seed, world position) + the overland data — any client/shard computes the identical
   world from the same inputs.
6. **Engine-portable by construction** (user goal: "useful for the other engines"): the
   whole algorithm layer is pure functions over (seed, cells, x, y) in the shared moros
   convention — it targets `hex_terrain` in loft-libs-world (CONVERGENCE.md), consumed
   alike by crawler, moros and dryopea; the blueprint deliberately avoids any
   Python-only construct (hash noise, kernel blends, segment distances — all portable).

## 2. The three-level hierarchy

| Level | Size (default) | Role |
|---|---|---|
| **Overland hex** | ~500 m (PARAMETER, see §4) | terrain authority: one cell record per tile; authored or generated; bundle-able |
| **Block** | ~60 m (41 fine hexes) | simulation / persistence / MP window (unchanged) |
| **Fine hex** | ~1.5 m | the movement lattice the player walks (unchanged) |

No alignment constraint between tiles and blocks: terrain is a continuous function of
position; blocks sample it wherever they sit (with an apron margin, §6).

## 3. The cell record — one schema, two scales

The overland tile record is *the same shape as a detail tile* plus a water flow direction.
It already exists verbatim in dryopea (`OverlandMap`) and is what `hex_terrain` should
standardize:

```
material: u8     // terrain/biome type
item:     u16    // feature/POI marker
height:   u16
water:    u16    // level + 3 bits of flow direction (6 hex dirs + none/source)
```

Self-similarity pays three ways: one storage/persistence/gen machinery serves both
lattices; the overland map is itself *displayable* with the same renderer (ZAngband's
wilderness map mode for free); and the record is the convergence point with dryopea's
overland.loft and moros's overworld.json.

## 4. Scale — a parameter, not a constant of nature

The 1.5 km figure came from "a continent in one PNG"; the PNG goal survives any tile size
(512 px at 300 m is still a 150 km landmass — Skyrim is ~6 km across). Tile size is really
an **encounter-pacing dial**:

- 1500 m ≈ 1000 steps/tile: biomes are regions you *journey between*; travel mode mandatory.
- 500 m ≈ 333 steps (~1.6 min): transitions inside a casual walk; travel mode = comfort.
- 300 m ≈ 200 steps (~1 min): the world changes as you walk (the classic overland-game cheat).

**Decision (revised): the MODEL is tuned at the NATURAL scale — 1.5 km tiles** (user call:
"that is the natural scale; the in-game world will not be natural"). Horizontal in true
kilometers, vertical in true meters — the geology rules (7e–7j) tune against real-world
proportions. The GAME then compresses at consumption: the fine-hexes-per-overland-tile
ratio is a gameplay mapping (the classic overland-game cheat), deliberately un-natural,
chosen for encounter pacing — separate from and not constraining the model. The bench
runs at 1500 m tiles, 72×48 km world.

## 5. Seamless merge — triangular interpolation on the hex lattice

Continuous fields (height, moisture, per-material weights) are a **smooth kernel blend of
the overland cells around the point** (C1 falloff to a radius just past one tile pitch —
the blueprint refined the barycentric idea: same seamless property, no triangle creases).
Along a shared tile edge both tiles contribute equally — adjacent tiles merge seamlessly
*by construction*. Per-biome fractal detail noise (amplitude blended the same way) goes
on top; the crisp material LINES are §7d's contest over these blended weights.

Consequences that fall out free:
- **Ecotones**: the blend band IS the transition biome; "sea-shore" is a weight-band claim
  between a water tile and a land tile (the shore follows the fractal blend line, not the
  hex edge).
- **Spawning**: the dominant tile sets the table; in blend bands the tables interpolate.

## 6. THE invariant (pin this first)

> **Window independence**: the fine terrain value at any world position is identical no
> matter which window/block/tile computes it — `terrain(seed, overland_data, x, y)` is a
> pure function; rendering a region whole and rendering it as independent windows are
> pixel-identical.

Mechanics that make it hold:
- All noise is **hash-based** (seed, quantized coords, channel) — no sequential RNG in
  terrain evaluation.
- River geometry derives **deterministically from the overland data alone** (§7) — every
  window computes identical courses.
- Effects with a radius (valley carving, river moisture) have a **bounded influence
  radius**; a window evaluates with an apron ≥ that radius and crops. The apron bound is
  part of the design, not an implementation detail.

The blueprint *executes* this invariant: render whole vs. render as independent windows,
assert byte-identical. **Hard-won exactness mechanics** (each was a real seam leak):
- Float falloffs with infinite tails leak: every radius effect needs a HARD cutoff the
  apron covers (asymptotic ≠ bounded).
- Window-relative float arithmetic leaks: snap window origins to the world pixel grid
  and compute pixel coords as `world/px − integer` (different binades round differently).
- Raster propagation (distance transforms, PIL strokes) leaks one-pixel edge flips:
  compute river fields as **exact per-pixel point-to-segment distances** in fixed global
  segment order — mins over identical floats are structurally window-independent. (The
  loft port rasterizes into FIXED world-anchored blocks instead, where anchoring is free.)
- The same field must have ONE implementation: the shoreline trim and the renderer share
  `detail_at`/`lake_field`/`material_contest` — a private copy WILL drift.

## 7. Rivers — coarse truth, fractal course, terrain follows

### 7a. Coarse hydrology (on the overland graph)
- Flow direction per land tile = steepest-descent neighbor (the 3 direction bits).
- Flow accumulation by height order; tiles above a threshold are **rivers**; terminating
  flow = lakes; below sea level = sea. One direction per ~500 m tile — trivially cheap,
  and authorable (a painted river is just assigned direction bits).

### 7b. The fractal course (rivers never go straight) — THREE levels of diversity
A river's geometry never touches a tile center or a side midpoint; it is anchored,
jigged, then fractalized (each level window-independent by canonical hashing):
1. **The edge BIT** (user rule): a river never exits through the middle of a tile side.
   Every shared edge carries one canonical random bit (hash of the *sorted* cell pair)
   choosing a crossing point more-LEFT or more-RIGHT of the side (±0.30·side). Both
   tiles derive the same point — seamless, and the coarse network stops looking like
   parallel lattice spokes.
2. **The interior CONTROL point**: each tile routes its rivers through one hash-jittered
   off-center point — courses bend *inside* tiles, and tributaries entering the same
   tile naturally CONFLUENCE there (they share the control→exit geometry exactly).
3. **Fractal midpoint displacement** on the anchor polyline: each midpoint displaced
   perpendicular by `(hash(seed, endpointA, endpointB, level) − ½) · seg_len · K · meander(mid)`
   (quantized-endpoint hashing, no traversal index). **`meander(p)` grows as the land
   flattens**: blended-height gradient low → big amplitude, plus a near-sea-level boost —
   steep young streams run straight, the river winds hard on the plain. Subdivide to
   ~28 m; deterministic corner-cutting after; width/depth grow with accumulation.

### 7d. Shorelines: attachment, flatness, boundary lines (user rules, blueprint-pinned)
- **Shoreline determination**: the sea shore IS the fine height-zero contour; a lake
  shore is the blended lake-weight contour, **fractally jittered** so it reads as a
  ragged natural line, never a rounded hexagon union.
- **Rivers ATTACH to the line**: every course is trimmed against the actual fine
  shoreline (bisection for the exact crossing); lake-crossing rivers split into an
  inflow and an outflow piece, both ending ON the contour. No course ever draws over
  open water or stops short of it.
- **A lake is FILLED water**: a flat level surface — no hillshade, no detail bumps.
  (Port note: the exact rule is "water where fine height < the lake's fill level",
  with the lakebed stored a few meters under the sill.)
- **The boundary-line rule** (generalized from the shoreline): between almost ANY two
  terrain types runs a crisp fractal LINE, not a wide crossfade — material claim is a
  winner-takes-it contest of kernel-blended per-material weights with fractally
  jittered scores, and **the STEEPER type wins the contested band** (bias by the
  material's detail amplitude: rock pushes its foot-line out over the plain). Heights
  stay continuous; only the *claim* is crisp.
- **Pattern hygiene**: the detail noise is **domain-warped** (a second noise swirls the
  sampling space) so the value-noise lattice never reads as a recursive pattern — this
  ADDS in-tile detail rather than smoothing it away — plus a per-world-position hash
  **dither** on the final color. Both are pure functions of position (seam-safe).
- **Bounded influence, exactly**: every radius effect (valley carve, riparian band) has
  a HARD cutoff its window apron covers — the seam test only went byte-identical once
  asymptotic falloffs were truncated. Asymptotic influence = a seam leak.

### 7c. The landscape forms around the river (dramatic, by rule)
- **Additive carving**: every course digs its own valley (depth × bounded falloff from
  *its* distance field); overlapping valleys SUM — confluences naturally deepen (capped).
  Winner-takes-nearest carving creases along Voronoi edges; additive doesn't.
- **Valley shape follows slope**: steep land → narrow gorge (full depth); flat plain →
  wide shallow floodplain (depth × ~0.45, falloff ~1.6× wider). Both scale with river
  size (√accumulation).
- **The ria rule (sea comes inland)**: near sea level the carve gets a size-proportional
  depth bonus — where a big river meets the low coast, the carved valley dips below sea
  level and **the sea itself floods inland up the valley**, exactly proportional to
  river size. The river yields to the sea wherever the carved height is below sea level.
- **Riparian band**: moisture/greening rises near the course (bounded falloff; later its
  own spawn tables). Order of authority: river course first, terrain shaped to it.

### 7e. In-tile verticality from neighbor relief (user rule, blueprint-pinned)
Each overland cell carries a **relief** value = its max height delta to its neighbors;
the kernel blend spreads it like every field. Fine verticality = `VERT_K · relief_blend ·
ridge(x,y)` where `ridge` is a **LOW-frequency** domain-warped ridged field, crest-sharpened
(~one combined crest per steep zone — shaping by high-frequency noise would speckle a slope
with a peak per zero-crossing where the land should throw up ONE combined peak). Behavior:
- steep-vs-steep neighbors → their shared zone soars (both blend high relief);
- steep-vs-flat → still rises (half the relief blends in);
- flat-vs-flat → almost unchanged (relief ≈ 0);
- **water-flow cells (river/lake/sea) contribute ZERO relief** — the dry land rises
  around them while their courses stay low, so rivers cut deep automatically and the
  coastline grows cliffs where steep cells meet the sea.
The **orthogonal side view** (`profile` panel: back-to-front strips at true heights) is
the judge instrument for this rule — top-down shading hides verticality.

### 7f. The GEOLOGY of the lattice (user model — recorded, NOT yet coded)
At overland scale a hex could fit a whole hill or mountain — but that is NOT our
model. Because rivers flow through the tile CENTERS (the control points), the
lattice is a drainage skeleton: **each cell is a catchment** — its center the
valley line the water runs, its rim the watershed, and the tile POINTS (the
triple corners where three cells meet) the hills and mountain summits. In
mountain cells the center is the gorge/crevice inside the massif, not the peak.
The existing machinery already implies this (carve lowers the centers, relief
rises between the drainage lines); expressing it fully is a TUNING question —
where the rise lands within the tile — deliberately left to the tuning passes,
not new code. (If tuning alone can't reach it, the candidate knob is anchoring
the rise to a center→rim coordinate derived from the blend weights — seamless
by construction — but that is parked until the numbers say it's needed.)

### 7g. Materials follow the water: big rivers carve their own PLAINS (user model)
A large river through mountains doesn't just cut a notch — it builds a FLAT
floor. Inside a course's valley band (width size-proportional, like the carve)
the material contest flips: **there the FLATTER type wins**, overriding the
surrounding rock with plain/hill — so even the biggest ranges carry ribbons of
plains and hills inside them. The carve already flattens the *height*; this
rule makes the floor *read and play* as plain: palette, spawn tables, and the
plain's own rise/steep numbers (calm floor, soaring walls — the zero-relief
water rule already keeps those tiles' centers low). Consequences: the great
valleys are the natural passes/roads/settlement sites through massifs (the
travel layer follows them). Content side: an "alluvial floor" band is a
transition CLAIM like sea-shore — a bundle claims it by river-size condition.
Status: recorded, NOT yet coded — same discipline as 7f.

### 7h. Mountain AGE = the rise/steep ratio (user model)
The divide between the white and the normal mountains is geological age:
- **Young ranges** (the white, steep Switzerland kind): high RISE **and** high
  STEEP — they soar and they're jagged; snow caps them.
- **Old ranges** (the gray eastern-Alps kind): the RISE remains, the STEEP has
  eroded away — equally high but FLOWING, rounded, walkable higher up.
- **The limit case**: even a continuous HILL pattern with enough rise (and the
  neighbor compounding feeding it) becomes a high range that rolls instead of
  cutting — no special case; it's just a point in rise/steep space.
The MIX in between comes two ways: an explicit middle row in the type table
(an "old rock / worn massif" terrain between hill and young rock), and the
boundary contest already crossfading rise/steep where young meets old — the
transition character is free. This is the model that VALIDATES the two
independent numbers: HEIGHT comes from RISE (+ relief), CHARACTER from STEEP;
age is their ratio. Status: tuning-table content (the user owns the numbers);
no engine change needed.

### 7i. Ranges form on the DIVIDES between water systems (user model)
Mountain ranges are not placed — they stand on the watershed DIVIDES between
drainage basins, two systems back-to-back **flowing outwards of each other**,
the crest between them the range. (7f scaled up: within a cell the rim is the
watershed; across the continent the basin boundary is the range.) Machinery
mapping: accumulation is the inverse signal — high-acc cells are valley floors
(already forced low by the zero-relief water rule), acc≈1 cells are headwaters
= the tops; basin identity is derivable (follow flow to the mouth, label; a
cell whose neighbor drains to a DIFFERENT mouth sits on a divide) — that
divide-ness is where RISE should concentrate. Causality becomes water pattern
→ divides → ranges; authored heights merely seed where the basins fall.
Status: recorded, NOT yet coded (the candidate inputs — inverse acc, basin
labels — are cheap derivations over existing fields).

### 7j. Waterfalls and slides: the small river's vertical features (user model)
A SMALL river through a mountain tile cuts deep and normally forms WATERFALLS
— its profile steps instead of grading. Through hills the gentler version:
water SLIDES / rapids. Both are a bit rare in the large because of 7g: rivers
of any size build their own natural plains and grade their beds — cascades
concentrate on small, young, steep streams. Machinery mapping: cascade sites
derive from existing per-vertex course data (LOW accumulation × HIGH coarse
slope → waterfall; moderate slope → slide), placed as discrete steps in the
carved channel profile. Content/gameplay: waterfalls are landmarks, hearing-
channel sound sources, and passage features — bundle-placeable POIs exactly
where the terrain is most dramatic. Status: recorded, NOT yet coded.

### 7k. EVERY water flow counts (user model)
Even the smallest stream cuts deep through ages of waterflow. Accumulation
gates **water visibility and width**, never *whether the cut exists*: every
cell's flow path is a course; an acc-1 brook owns a deep-but-NARROW cut (the
gorge), a great river a wide one (+ its 7g plain). This is also what makes 7j
possible — gorges and waterfalls live exactly on the small steep streams the
current RIVER_ACC threshold discards. Bench/lib implication when coded: build
courses from ALL source cells; scale width and water rendering by acc; keep
carve depth substantially acc-independent (age does the cutting, size does the
widening). Status: recorded, NOT yet coded.

### 7l. The NATURALIZATION pass (user direction — the next blueprint phase)
The current generated form is very UNNATURAL; an algorithmic pass over it is
required — but that pass must be **SUBTLE**. Its charter:
- **The terrain around a river decides its local character, not its size
  alone.** Not every river is wide: the SAME course has its hilly parts
  (narrow, gorge-like, fast) and its valley parts (wide, floodplain, slow),
  alternating along its run as the surrounding relief changes. Width, valley
  breadth, carve shape, and the 7g alluvial claim all become per-segment
  functions of the LOCAL terrain context (the cells around the vertex), with
  accumulation only setting the overall budget.
- Folds in the standing recorded rules where they touch courses: 7k (every
  flow counts — small streams get courses + deep narrow cuts), 7j (cascade
  sites where small × steep), graded river mitigation of peak rows (the
  evaluation's finding: suppression width ∝ size, not binary).
- SUBTLE means: no re-randomizing, no global smoothing, no form change a
  player would notice as a "pass" — only local, terrain-justified adjustments
  of what already exists. **Status: STARTED in the bench (2026-06-11)** — landed:
  the flow-TREE link model (every cell = one course link, 7k; no duplication,
  confluences at shared control points), terrain-decided per-vertex character
  (gorge vs valley along one course: width/(depth×relief-context)/valley-breadth/
  alluvial band all from local slope+relief; accumulation = budget only), graded
  peak-row suppression (self from acc≈8, shoulders from acc≈20 — corridor ∝ size),
  the 7g alluvial floor as a color/claim band (heights untouched — no trim cycle),
  7j whitewater (river pixels foam where bed steep × stream small), MAX-of-links
  carving (smooth at link joints; replaces additive), and the STABILITY rule:
  links sort biggest-water-first so contested claims resolve canonically.
  SUBTLETY lesson: brooks cut deep but NARROW — wide falloffs, riparian green and
  alluvial bands are size-gated, else the lattice reads as a honeycomb. Seam test
  byte-identical throughout. The lib (hex_terrain) follows once the bench look is
  user-approved.

### 7m. SETTLEMENTS (user rules — IMPLEMENTED in the loft port)
- **Towns stand where the land supports them**: scored on flat fertile ground
  (plains/forest), water access (river accumulation through the cell, lake/sea
  harbor bonus), with spacing; the better the spot, the BIGGER the town (size
  1–3). A town sits at its cell's vertex point — on the river, at the
  confluence, exactly where settlements really form.
- **The farmers' rule**: fields ring the town on flat ground; the forest NEAR
  town is CUT (cleared to grass) for those fields; the farther forest stands —
  that's where the wood is gathered.
- **Roadside farms**: roads make outlying land reachable — scattered fields
  along them, sparser than the town belt.
- **Roads take the easiest walk**: Dijkstra over the cell graph (slope +
  terrain costs, water heavy, never through open water), each town connecting
  to its nearest neighbor; the path renders as a displaced course that fords
  rivers where it must.
- **Buildings are dungeon-style rooms for now** (rect walls + a door), stamped
  by the surface generator at the town center — nice versions later.

### 7n. Swamps and estuaries (user rules, implemented in the loft port)
- **SWAMP = water against FLAT TERRAIN**: flatness judged on the COARSE land
  (the floodplain), never the carved channel banks; riverside marsh beside
  sizable water, lake-shore marsh on flat banks, and CONFLUENCE pools where
  two rivers flow into one another (the flow tree's in-degree); towns/roads
  drain their ground (their claims come first). Plains were flattened (25 m)
  to give floodplains room — small worlds are stingy with flat-water ground.
- **ESTUARY**: river mouths are never straight — the daily tide pushes in and
  BROADENS the mouth into a funnel (water width flares quadratically toward
  the sea end), but NOT when the river drops steeply (openness-gated).

## 8. Fast travel (scale consequence, designed earlier — recorded here)

- **Overland travel mode**: the overland is itself a walkable level (same cell schema, same
  renderer zoomed; one step = one tile; biome encounter checks; an encounter/arrival drops
  into the fine scale at a deterministically generated block). ZAngband's wilderness map mode.
- **Mounts**: distance-per-tick multiplier (the world ages less per km — clock-correct,
  MP-clean); mounts are bundle content.
- **Roads/trails**: a material with travel multiplier + lower encounter rate; same coarse
  graph machinery as water flow.
- **Auto-hike**: hold-to-travel at fine scale, interrupted by the perception channels.
- **Honest tension**: fast travel + natural regen = free heals → **hunger** becomes the
  needed counterweight (rations exist, inert today; foraging by biome = a bundle hook).

## 9. Bundles plug in (mechanism engine-side, content bundle-side)

The engine owns: the lattice, the triangle blend, hydrology, the meander algorithm, spawn
mixing. Bundles own, composably:
1. **Biome defs** — palette, detail-noise character, monster tables, features (volcano
   caldera = the existing stencil/placement machinery).
2. **Assignment rules** — claims over seeded coarse fields ("volcanism high → volcano") or
   adjacency grammar ("foothills ring mountains").
3. **Explicit overland maps** — authored regions (the PNG/overworld.json style) pinning
   content at known places.
4. **Transition claims** — weight-band biomes (sea-shore, riparian).

The standing check applies: the engine never names a biome.

## 10. Blueprint plan (the verifiable steps, in order)

Instrument: `tools/overland_blueprint.py` (throwaway, numpy+PIL, deterministic).

1. **Concrete plotted end-result**: a small painted/generated overland map (~24×20 tiles:
   sea, shore, plains, forest, hills, mountains, one lake) rendered to `overland_map.png`
   — heights, flow arrows, accumulation-scaled rivers. *Check: hydrology reads correctly.*
2. **Fine blend window** spanning several tiles → `fine_blend.png` with faint tile borders
   overlaid. *Check: no seam visible at any border; ecotone widths feel right.*
3. **Rivers**: fractal course + carving + riparian band; a close-up at the river mouth.
   *Check: straight in the hills, winding on the plain — visibly more curves near the sea.*
4. **THE invariant executed**: render the window whole vs. as independent apron'd
   sub-windows; assert byte-identical. *Check: prints SEAMLESS OK.*
5. **Scale strip**: same world at 1500/500/300 m tiles. *Check: user picks the constant.*
6. User verdict on the PNGs → the loft port. **DONE 2026-06-11**: the algorithm
   layer is **`hex_terrain` in loft-libs-world** (PR #4, merged, CI green, 0.25 s
   gate under --deny-warnings) — cells/hydrology/relief/rivers/sampling as pure
   functions; the rise/steep tuning table is the `TerrainType` input (bundle-ready);
   the invariant is tested by rebuild-and-compare. Crawler consumption (wilderness
   blocks sampling `terrain_sample`) is the NEXT increment; the Python instrument
   stays the visual tuning bench.

## 11. Out of scope (parked, named)

Round towers + 24-direction walls (CONVERGENCE roadmap, next after this); block travel
increments wiring (`world_key_seed(wx,wy,depth)` is pre-parameterized); MP sharding
(blocks are the shards; RandStream state on Sim is syncable); hunger system build;
overland travel mode implementation (designed in §8, built after terrain exists).

## 12. THE SCALE LADDER — deriving the detailed map (theory, pinned 2026-06-11)

The gap from 1.5 km tiles to 1.5 m walked hexes is bridged by a LADDER of layers,
each a pure sampler over the one above — never a tree you descend, never data you
store. Each layer owns roughly one order of magnitude of form: overland (biome,
geology, trunk hydrology) → meso (~500–150 m: gullies, stands/clearings, ponds,
cliff lines) → micro (~60 m: individual landforms, POIs, stencils) → fine (the
walked tiles). Two channels everywhere: continuous FIELDS give the ground;
discrete FEATURES give the forms — linear features reuse the river template,
area features the lake template, point features the 7j site rule. Per-terrain
INCLUSION tables (forest contains clearings/groves/ponds…) are bundle content
over ONE generic claim mechanism. The realization unit is the block/map: sample
fields + collect bounded-influence features + rasterize; the detailed map is a
VIEW of a function — only player deltas persist. The game's compression constant
(walked hex → natural meters, C ≈ 3–5) stays outside the model entirely.

### 12a. The ZAngband graft
ZAngband's wilderness gen already has this shape: per-block seeded plasma
fractal anchored at SHARED CORNER values + per-terrain LOOKUP TABLES (fractal
band → grass/tree/bush/rock/water) + overlays. We adopt it as the micro layer,
upgraded: the anchors sample OUR field stack (the rough structure is followed
by construction), the plasma residual is the per-type micro-roughness number,
the tables are the inclusion tables (bundle rows beside rise/steep), and our
features (courses, cliffs, sites) rasterize over the result in authority order.
`world_key_seed(wx, wy, depth)` is the per-map seed, already parameterized.

### 12b. The DUAL-TRIANGLE map (user direction)
The local-map unit is the triangle of the DUAL lattice — vertices = three
mutually adjacent hex CENTERS (2 triangles per hex of area). Then:
- the SIDES are the river corridors (center→edge-bit→center = the flow links);
  a river ROUGHLY FOLLOWS a side, never straight — the side is the AXIS, the
  course the fractally displaced curve around it, meander belt ∝ size ×
  openness, excursion bounded (a geometric series → the provable corridor bound);
- the VERTICES are the valleys and confluences (hex centers, control points);
- the INTERIOR is one coherent landform rising to the hex CORNER (triple
  point) at the centroid — the summit (7f). No water inside an interior, ever.
Triangle id = (hex, index) is the natural key for gen seed, persistence deltas,
MP shards, travel. **Triangles feed the ZAngband GENERATION loop only — never
the world render**: rendering is a pure per-pixel evaluation of fields +
contracts at any zoom; a triangle is the unit that gathers its contracts and
realizes a walked map (at 1.5 km / C=4 ≈ 27k walked cells ≈ two Angband levels;
one 4-fold subdivision ≈ screen-scale — a pacing knob, contracts recurse free).
The 60 m sim blocks keep streaming within it. (3D bonus: the subdivision
triangles ARE the future moros mesh — the gridmesh seam, second customer.) Triangles subdivide 4-fold forever (hexes can't subdivide);
midpoint displacement on triangles is the ORIGINAL fractal terrain, and with
endpoint-hashed offsets every level is window-independent and edge-consistent.
Self-similar drainage: sub-gullies follow sub-triangle sides, sub-interiors
stay whole.

### 12c. THE OWNERSHIP CONTRACTS (user rules — the law of the lattice)
**No feature ever sits ON exact lattice geometry, and every feature is owned by
the lattice element all its observers share** — maps CONSUME contracts, never
regenerate them. The ladder of ownership:
- **VERTEX** (hex center): valley-floor elevation, jittered control point,
  confluence, ONE hashed flow tangent (the through-river leaves and arrives
  along it — C1 across the vertex; tributaries join at honest angles).
- **SIDE** (center–center): the river — ONE size budget along the whole side
  (= the upstream cell's accumulation; size changes ONLY at vertices where
  tributaries join — deliberate, never generation noise), the curved course,
  the width/depth profile (terrain-deliberate gorge/valley variation from the
  canonical fields), banks/carve out to a bounded radius, cascade sites (7j).
- **CORNER** (triple point): the PEAK — jittered OFF the exact point (a
  lattice-perfect peak grid is as artificial as a ruler-straight river),
  height/character decided ONCE from the three meeting cells (relief
  compounding 7e, age mix 7h, water suppression 7l), bounded influence radius.
  "Multiple triangles decide where the top is" = all evaluate the same
  corner-owned function — agreement by construction, not negotiation.
- **EDGE** (corner–corner = hex border): DRY → a RIDGE between the two corner
  peaks with a hashed saddle (the divide continuing); WET → a WATER GAP where
  the river breaches at its edge-bit point. The drainage network (dual sides)
  and the divide network (hex edges) are interlocking duals crossing only at
  the gaps — 7i read straight out of the geometry.
- **INTERIOR**: everything else, anchored by all four, generated last.
Stability throughout: bigger water first; canonical hashes from sorted ids.

### 12d. The experiment (tools/triangle_blueprint.py — first results)
A hand-authored 9×7 map (two mountains adjacent, a mountain on the sea, a
mountain on a lake, hills/forest/plains) resolved through the contracts plus a
first ZAngband table pass. Panels in tools/_triangle/: contracts.png (the
ownership diagram — jittered peaks tethered to their lattice points, saddled
ridges ringing the massifs, curved rivers), detail_map.png (6 m/px), ortho.png.
FINDINGS: adjacent mountains merge into ONE range with a visible saddle (corner
compounding works); the coastal massif cliffs into the sea; vertical structure
as MAX of owned forms (peaks + ridges) replaces free noise — form follows
ownership; lessons: never carve the seabed; lake contours need fractal jitter;
rivers at 6 m/px read correctly thin (brooks invisible from above — natural).

### 12e. The CONTRACT INVARIANTS (user-named, executable, enforced by construction)
Pinned in the experiment (`check_invariants`), to become the loft test suite:
- **I1 — no inland sea**: solid land (coastal blend weight ≈ 0) is FLOORED above
  sea level; only the bounded coastal band may dip. Check: flood-fill the sea
  from the map border — zero unreachable sea pixels.
- **I2 — lakes are level**: a lake OWNS one surface elevation (a vertex/cell
  contract value); every lake pixel sits exactly on it. Inflowing beds LAND on
  that level (never undercut it). Check: max−min over the lake = 0, exact.
- **I3 — water never flows uphill**: the bed is a monotone ramp between
  vertex-owned levels (cell heights strictly descend along the flow tree, so
  the network is monotone by construction); the carve is re-derived as exactly
  the depth that reaches the bed at the centerline. Check: sample every side's
  interior downstream on the WATER SURFACE (sea = flat 0; vertex zones belong
  to the neighbor) — no rise.
LESSON: the checkers caught a REAL bug immediately (false lakes: a wateriness-
keyed classifier stamped lake level onto sea-coast bands — the lake mask must
blend LAKE-cell weight only). Invariants are detectors, not just guarantees.
Also fixed by construction in the same pass: beach requires water adjacency +
gentle slope (no sand patches up coastal mountains; steep shores are cliffs),
peak/ridge composition via SMOOTH p-norm max (no crease seams), water surfaces
excluded from the color dither (smooth lakes/sea/rivers).

## 13. IN THE GAME (status 2026-06-11): the walkable contract wilderness

The loft port is LIVE in crawler:
- **`src/overland.loft`** (kernel): the example world authored as data; the
  contracts resolved once (32 sides w/ monotone beds + aggradation fill, 99
  corner peaks, 13 saddled ridges, 4 towns, 3 roads); pure sampling
  (`ov_sample` -> height + terrain KIND) with the zonation pass (forest belts,
  eroded faces + scree, alpine meadows, snow cut by rock, glaciers melting
  into streams, beaches, fields, roads). Uses hex_grid (lattice) + hex_terrain
  (noise) from loft-libs-world.
- **The walked scale**: `OV_STEP = 15` natural meters per fine hex — 100 steps
  cross a dual-triangle side (the user spec). The surface (depth 0) is a
  101×101 wilderness WINDOW anchored at the biggest town: kinds drive
  walkability (faces = walls, lake/sea block, rivers ford), buildings stamped
  as dungeon rooms, the crystal knot + dungeon entrance preserved on cleared
  ground (all pre-existing tests hold).
- **The view** tints each hex by kind (translucent wash over the light floor;
  water/snow/forest/fields/roads all read) and gives glyphs a round disc
  back-plane on the wilderness so letters stand out on tinted ground.
- **The gate**: `overlandtest` runs the three contract invariants (I1 no
  inland sea, I2 lakes exactly level, I3 monotone flow — the aggradation rule
  came from I3 catching a coastal-dip rise), determinism, the walked scale,
  walkability mapping, and the settlement assertions (35 tests total).
- **`src/ovmap.loft`**: the ZAngband CHARACTER MAP of the world (2 s) —
  ' ' sea, '~' river, '=' lake, ',' sand, '.' grass, '+' field, '-' road,
  'T' forest, '"' meadow, ':' scree, '^' rock face, '*' snow, '%' glacier,
  digits = towns by size.
### 13a. The settlement ARCHITECTURE (user rules, implemented)
- **Small houses** (5×4 hexes ≈ 7.5×6 m — ARCHITECTURE IS TRUE-SCALE: 1.5 m
  per walked hex, while the TERRAIN is compressed at 15 natural m per hex).
  This 1/10 terrain-vs-true split is the standard overland-game illusion
  (user ruling); the compression is ONE dial (`OV_STEP`) and is EVALUATED BY
  GAMEPLAY, not by theory — play sessions decide if 15 walks right;
  count grows with town size, doors face the village square.
- **Round towers** for size-2+ towns; the BIG town gets a **wall ring with
  LOOKOUT TOWERS in it**, gated wherever a road crosses.
- **Fortresses** (a contract object): sited ABOVE and away from the town they
  protect, but close enough for CLEAR SIGHT on the waterways/roads they watch
  (elevation + watch-distance scoring over a candidate ring); built as a
  walled keep with four round corner towers, gate facing the town.
- **Round detectability** (user rule): round structures stamp tile value 4 —
  solid like a wall, but a later pass (true circles in wallgeo / the 3D mesh)
  can DETECT rings of 4s as round shapes with center + radius. Tile 5 = the
  farmers' FENCES (straight + light) along roads where fields border them,
  with gaps; solid for now, light rendering later.
- **24 directions** (user ruling): stamped walls/roads WOBBLE on the hex
  lattice for now; the 24-direction vocabulary + straightening (the parked DP
  straightener, CONVERGENCE) make them clean later.

### 13b. The DAILY LOOP (user direction, implemented)
The town LIVES: civilians are scheduled entities (the Enemy machinery with a
ROLE — never aggressive, never punched; the player's bump slides past):
- a day lasts DAY_LEN ticks (280 day / 120 night, `sim_phase`);
- VILLAGERS sleep at home, take the village square by day;
- FARMERS cycle home -> their nearest FIELD -> the food stalls on the square,
  carrying the crops round and round;
- GUARDS patrol day AND night between lookout legs (the wall ring's towers in
  the big town) — safety on the walls and the land;
- the FISHER walks to the water's edge and fishes the day away;
- a small BOAT works the lake, a bigger SHIP the sea — water-only movement —
  and both anchor for the night at THE HARBOR: a pier of planks over the
  water (K_ROAD on water hexes = walkable dock) with a harbor hut, stamped at
  the nearest shore; mooring there is the nightly repair;
- determinism throughout: schedules derive from (ticks, role, hashed salts).
### 13c. TRADE + the ECONOMY (user direction, implemented)
- **The merchant cart** (role 7): a SLOW cart on a multi-day route along the
  road (far end <-> the home market, leg per day); it prefers road hexes when
  stepping (carts stay on roads) and avoids swamp/water; at night it PARKS at
  the nearest ROAD STOP.
- **ROAD STOPS** (a contract object): where a road's arc outruns a cart's day
  of travel (2.8 km natural), waystations sit at day-interval points; visible
  ones get their hut stamped.
- **Ships, divided**: the working sea boat is a FISHER with nets; the
  **merchant ship** (role 8) brings goods in from BEYOND the map — sailing
  between open water at the window's edge and the harbor anchorage on the
  multi-day schedule. The chain reads: ship lands goods -> the harbor -> the
  carts move them along the roads.
- **The ECONOMY v1**: each morning the makers bring the night's work to the
  stalls — TOWNS craft the simple goods (rations, torches), CITIES the
  complex armour and weapons (blades, leathers) — daily floor-item production
  at the market, capped.
- **The ALCHEMIST-FACTORY** (user rule): the main cities host one, drowned
  in requests — it only actually BREWS on some days of the week (3 of 7), and
  each brewing day yields ONE type of potion (the type rotates by week and
  day), a real BATCH (5 bottles) beside the stalls. Prices outside the city
  SKYROCKET, so the cart traders load potions FIRST (arms fill what's left).
- **The GATHERERS** (user rule): the alchemists need a constant supply of
  special ingredients — rugged travelers fetch them, met on the roads and the
  hillsides (scree/meadow picking grounds), CAMPING where dusk finds them and
  SHUNNING the deeper mountains (no snow, no ice). There are not many: one
  walks the window.
- **The cart TRADES** (user rule): at the home market it loads what the
  makers offer — weapons/armour only, only the LIGHT ones (weight-capped: no
  broadswords on a cart's springs), and only TWO slots (not much choice);
  at the route's far end it sets the goods out. Distribution made visible.
### 13d. The FULL economy (user direction, implemented)
- **Repertoires**: the forge rotates ALL its arms (weapons even days, armour
  odd — the heavy pieces stay home via the cart's weight cap); the brewery
  rotation now includes the premium brews; the SCRIPTORIUM writes scrolls on
  the quiet days and a realm book at week's end; towns craft leatherwork and
  the FLETCHER's bows/arrows beside their staples.
- **The ship's MANIFEST**: at night anchor the merchant ship LANDS the goods
  no local craft can make — wands, staves, rings, amulets — onto the pier.
- **MINERS + the SLAG-FURNACE**: miners cycle ore from the mountain face to a
  big round furnace stamped OUTSIDE the walls (dirty industry stays out);
  when the window holds no rock, the mine mouth sits at the window edge
  toward the nearest mountain cell — the workings continue beyond the map.
- **LIVESTOCK + WILDLIFE**: cows and horses in a fenced pen by the farms (the
  hides come from somewhere), grazing by day; beaver/fox/goat live wild by
  water/woods/rough ground — and the gatherer TRAPS what it passes (wildlife
  is not counted as civilians; it comes and goes).
- **THE MILLS**: bread needs grinding — a WATER-powered mill at the riverbank
  when the window has running water, a WIND-powered one on open ground when
  it doesn't (round structures, tile 4); the mill's bread reaches the city
  stalls every morning.
- LESSON (filed as loft#336): vector<text> literals HANG the interpreter in
  deep contexts and PANIC when indexed in call args — production repertoires
  are branch-selector functions instead.

### 13e. THE HISTORY: the maximal past, broken (user direction, implemented)
The world's history derives from its own settlement scoring: re-score the
sites with a LOWER bar and looser spacing — the runners-up the living world
rejected were inhabited ONCE, in the maximal past. Something went wrong; they
stand as RUINS now (size-tiered: fallen village / broken castle-town / dead
city). Each ruin keeps a SPOTTED PATH toward the nearest living town — a
displaced trace claimed only in hash-patches (the land swallowed the rest),
and faded paths feed NO road claims (no roadside farms along dead ways).
Within the window, ruins stamp as broken architecture (houses and walls
breached by per-cell hash, rubble drifted over the floors, a tumbled tower,
the dead city's wall reduced to arcs) — and GOBLINS nest in them: a band with
its LEADER (new monster def), asleep among the stones until someone pokes.
The STRAIN this places on the economy is structural: fewer living settlements
than the land once fed, dangerous ruins beside the trade ways, and the spotted
paths as the player's invitation toward history.

### 13f. WHERE THE WILD THINGS LIVE (user direction, implemented)
The bestiary audited for natural HABITATS (not just the dungeon) and the
wilderness spawns by them, distance = danger (tier 2 beyond ~40 hexes):
- FOREST: centipedes, giant spiders, rats; far woods hold dark elves + ogres.
- MEADOW: mice + white snakes; the high shelves nest HARPIES.
- SCREE/rock: kobolds, bats, cave spiders; the far rough holds basilisks +
  TROLLS.  SNOW/ICE: wyverns, stone giants, harpies — the high cold.
- SWAMP: giant frogs + grey molds; the deep mires hide ghouls.
- SAND: giant ants + snakes (the desert bundle's own serpents place through
  its rules — engine lists keep engine keys only, the bundle seam holds).
- Open GRASS: jackals + ants near, gnoll packs + ogres far.
- RUINS: goblin bands + the leader; the DEAD CITY keeps its dead (skeleton +
  zombie join the tier-3 nests).
- Dungeon-only by design: the floating eye, the wraith/lich tier, the uniques.
All wild spawns sleep until disturbed; none within 25 hexes of the town —
the daily loop stays safe, the far wilds carry the strain.

NEXT: shops with real interiors + trade, NPC dialogue, ship routes between
coastal towns, multi-window travel, nicer buildings, true round rendering
(tile 4) + light fences (tile 5), the lib-ward extraction into hex_terrain.
