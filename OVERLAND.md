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
