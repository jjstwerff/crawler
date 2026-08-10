# 1 — Terrain-taxonomy adequacy + default tuning (real Ortler terrain)

**Issue:** [`jjstwerff/crawler#1`](https://github.com/jjstwerff/crawler/issues/1) ·
**Value:** `F` · **Shape:** investigation

## Status

**Open — the first pass concluded; the plan is being extended.** Goals 1–3 delivered:
the 14 kinds suffice for the coarse tier, and the real-metre transition defaults are
derived (`tuned-defaults.md`). Sub-hex *structure* (the LOD that resolves detail at all)
is carried by plan **#2**.

**What is NOT settled: how to model CLIFF FACES.** This is a taxonomy-adequacy question,
so it belongs here rather than in #2 — #2 owns the LOD machinery, this plan owns whether
our terrain vocabulary can represent what that machinery exposes. See *Open work* below.

## Goal

Using the greater Ortler (Ortles) massif as a real test region, answer:

1. **Adequacy** — is crawler's current **14-kind** terrain taxonomy (`K_GRASS … K_SWAMP`,
   `src/overland.loft:26`) enough to represent real Alpine terrain *somewhat accurately*,
   or do we need **more terrain types**? Output = a verdict + concrete kinds to add/split.
2. **Defaults** — tune the per-kind default numbers (elevation bands, slope cutoffs,
   material relief, accumulation threshold) so the classification matches reality.
3. **Transition values → realistic fantasy defaults** — *derive* (not guess) the
   elevations/slopes where terrain types change inside a real range, so they seed
   realistic world-generation defaults (`tuned-defaults.md`).

**The end deliverable — two same-scale drawings.** The verification (and the adequacy
answer) is **two drawings of the Ortler at the same scale, side by side**:
- **(A) realistic, from the actual data** — real DEM heights (the triangle mesh) shaded as
  relief + **real terrain types from OSM landcover**. This is the ground truth.
- **(B) our model** — the same region rendered through crawler's world-drawing routine
  (`tools/overland_blueprint.py` fed our hex map: fine-terrain blend + the `material_contest`/
  `ov_sample` classifier).

Same projection, extent, and cell layout, so they compare directly. The **gap between B and
A** is the adequacy verdict; closing it is the default tuning. Static PNGs — reviewable by the
agent (Read) *and* gateable headlessly: `gl_screenshot` under Xvfb is reliable, so the engine
example world can be self-verified by golden diff too (plan #7 channel 2/6).

Investigation *before* engine change; an engine port is a conditional follow-on.

## This plan directory is the workshop

The Python we create lives **here**, not in `tools/`; the README refers to it, and **the
actual loft statistics (the tuned per-kind defaults) are built from here** and ported to the
engine.

```
plans/1-ortler-worldgen-fixture/
  README.md            — this design (the stable index; stays inside its length budget)
  ortler_import.py     — fetcher: EU-DEM + OSM → the hex-map source   [created]
  trimesh.py           — triangle-vertex datapoint model (18 tris / 19 verts per hex) [created]
  ortler_render.py     — driver: feed the hex map into overland_blueprint, render + compare
  ortler_stats.py      — confusion table + the loft-statistics emitter
  data/ortler_hexes.npz   — hex-center heights (S1 sanity layer)
  data/ortler_trimesh.npz — datapoint evaluation: verts, height i16, tris, hexcr, tri_osm
  data/osm_polys.npz      — cached OSM landcover polygons (re-classify at any resolution)
  out/                  — the two same-scale drawings: ortler_actual.png + ortler_model.png
  *.md                  — detail docs (see below)
```

Only existing, shared tooling stays in `tools/` — `overland_blueprint.py`, reused via import
(a minimal additive `from_arrays` hook; see S3).

**Iteration detail goes in separate `.md` files, not this README.** We assume the details
*will* churn (classification, tuned numbers, per-kind findings). The README is the design
index and holds only the *settled* one-line conclusions + links; each iteration topic gets
its own doc so the README stays scannable and inside its length budget. Anticipated:

- `geometry-pin.md` — the I-GEO round-trip evidence (S0): the worked summit-cell + parity instance.
- `mesh-pin.md` — the I-MESH watertight triangle-vertex model + the populated heights.
- `gap-analysis.md` — the S5 confusion table + missing/conflated-kind candidates, each tagged
  **VERIFIED**/**HYPOTHESIZED** (one section per candidate kind as it's investigated).
- `tuned-defaults.md` — the S6/S7 per-kind defaults (before → after) + the paste-ready
  loft-statistics artifact.

- `intent.md` — the **frozen** recognition intent (draw-skill step 1): the gestalt
  predicates the render must satisfy, written before any mark and not edited to match output.
- `region-fixtures.md` — PLANNED: the flexible N-region fixture design (a region as a data
  record) + Wales as the second reference, supplying the coast/cliff ground truth.

New cluster docs are added as new gaps surface; the README links them, never inlines them.

## The instrument — feed a real hex map into the existing renderer

`tools/overland_blueprint.py` already *is* the world-drawing routine: a coarse hex lattice
(`Overland.h` height m, `Overland.mat` material, `Overland.flow` 0..5 neighbour index,
`Overland.acc`; moros odd-r) → `blend_fields` → `flow_links`/river chains → PNG, with
`material_contest` doing kind classification (the design twin of `ov_sample`). Its lattice is
synthesised today. **The change: it "gets a hex map as a source"** — fed `h`/`mat`/`flow`/`acc`
from the real Ortler.

- **`ortler_import.py` = the fetcher** → the hex-map source over the 1.5 km grid
  (`TILE_M=1500`): `h` from EU-DEM (real metres, signed `i16`, sea 0, **negatives reserved
  for sub-sea structure**), `mat`/OSM-class, and **pre-computed water directions**. Sources,
  all verified reachable:
  - **Elevation** — OpenTopoData `eudem25m` (EU-DEM 25 m), per hex center (3835 m at summit).
  - **Landcover** — OSM via Overpass (`natural=glacier|bare_rock|scree|wood|water`,
    `landuse=farmland|orchard|vineyard|meadow`) → observed class per hex (ground truth).
  - **Real water directions** — OSM `waterway=river|stream` snapped to the grid, **oriented
    downstream by the DEM**, encoded as a `flow` neighbour index **0..5 in the blueprint's
    exact `neighbors()` odd-r order** (`overland_blueprint.py:133`) + `acc`.
- **Feeding flow is a single-site override.** `_gen()` computes `self.flow`/`self.acc` by
  steepest descent (`:184–202`); the driver **overrides that one block** with the fetched
  *actual* drainage and leaves every downstream consumer (accumulation, river chains, relief
  mitigation) untouched. `self.flow` is the one chokepoint → the feed is N=1.

## Architecture — the renderer follows the data (enrichment is upstream)

**The renderer renders the height/material data as-is** — blend + hillshade + class/water
colour, nothing invented. It does **not** synthesise relief, fractal detail, or dither at
draw time. That render-time enrichment was the F3 artifact source: tuned for ~100 m synthetic
relief, it exploded on real 2360 m alpine relief (render height hit 5649 m). So for our
pipeline the renderer always *follows the data* (the `real_height` path); the blueprint's
bundled enrichment stays only for its own synthetic-world modes.

**To add detail, refine the DATA, not the render.** More detail = more/finer vertices — the
recursive triangle **LOD** (1.5 km → 1.5 m), produced upstream — which the renderer then
follows unchanged. This is the kernel/view split (CLAUDE.md) and the LOD vision in one rule:
*enrichment generates data; rendering consumes it.* (Per-pixel render-time fbm can't live in
the coarse cell data anyway — which is the tell that it belonged in a data-refinement pass.)

## Design protocol — exact invariants (plot the answer, then build)

The load-bearing parts are **exact-invariant** (geometry, flow round-trip, classifier
equivalence): a construction to *recover*, not a space to explore. Pin each by a worked
instance in the cheapest medium before scaling up.

- **I-GEO — sampling ↔ render round-trip.** Cell `(col,row) → (lat,lon)` (fetch) is the exact
  inverse of `(col,row) → world-metres` (render), same moros odd-r, **no parity drift**. The
  convention is re-stated in ≥3 sites (`hexoffset.py`, `overland.loft`, `overland_blueprint.py`,
  `ortler_import.py`) and **silent on mismatch** ⇒ brittleness known now. *Cure (N→1):* the
  fetcher **reuses the blueprint's `center(c,r)`** as the single source; a round-trip assert
  is the loud guard. **✓ pinned (`geometry-pin.md`).**
- **I-MESH — watertight triangle mesh ✓ (`mesh-pin.md`).** Heights live at the **triangle
  vertices** of each hex (each side ÷3, center fan → 18 triangles / 19 vertices), not hex
  centers. A corner is shared by 3 hexes, an edge-third by 2; the shared vertex carries **one**
  height (compute per world position, dedup on a 1 mm key) or the mesh cracks. *Verified:*
  14878 unique verts, refcounts {center 1, corner 3, edge 2}, fan area == hex area, summit
  vertex 3835 m.
- **I-FLOW — fed directions reconcile with the heights (= engine I3).** Every fed `flow[r,c]`
  points to a neighbour whose pit-filled height ≤ this cell's. A fed real-river direction
  pointing **uphill** on our sampled heights **falsifies** the sampling or the 1.5 km
  resolution — surface it, don't smooth it. (Computed-D8 vs fed-real is a free cross-check.)
- **I-TWIN — classifier portability (the cleanest "also" claim; falsify it).** A gap in
  `material_contest` is a *real engine* gap only if that logic ≡ `ov_sample` on identical
  `(h, slope, mat)`. Probe before trusting the confusion table.

**Model-hydrology invariants** (engine I2/I3, checked by `ortler_render.check_invariants` +
`clip_rivers_at_lakes`):
- **I2 — lakes are level everywhere.** Every cell of one lake shares a surface height.
  *Status:* holds to ~0.5 m (the pit-fill anti-flat epsilon tilts each lake); the loft engine
  forces *exact* level (`OV_LAKE_LVL`) — so the model needs a flat-lake pass.
- **I3 — water never flows uphill.** Every flow step descends. *Status:* ✓ 0 uphill cells
  (by construction after pit-fill). (Distinct from **I-FLOW**, which checks the *fed* OSM
  directions.)
- **Water never extends into lakes.** A river ends at the lake shore; the still body carries
  no current. *Routine:* `clip_rivers_at_lakes` truncates courses at the first lake cell.

## Verifiable build steps (each gated — don't pass until the check is green)

**S0 — Pin I-GEO (no fetch yet). ✓ DONE** — evidence in `geometry-pin.md`.
*Build:* in `ortler_import.py`, define cell→world via the blueprint's `center(c,r)` + a
projection origin at the summit; implement cell→latlon and its inverse.
*Check:* round-trip `cell→latlon→cell` is **exact** for one **even-row** and one **odd-row**
cell (parity); the summit cell's latlon == 46.5089 N / 10.5446 E within < 1 m; the four grid
corners print to ≈ ±30 km of the summit.
*Gate:* exact round-trip + correct parity + corners bracket the Ortler. **No fetch until green.**
*Result:* parity exact (750 m / 0 / VS) · **0 mismatches / 1600 cells** · home↔summit exact ·
corners 38–40 km · bbox lat 46.287–46.742, lon 10.153–10.926. PASS.

**S1 — Elevation hex map. ✓ DONE.**
*Build:* fetch EU-DEM at each cell center (batched 100/req, ~1 req/s), store `h` as i16 m.
*Check:* no holes; summit cell `h` ∈ [3500, 3905]; valley min `h` < 1200; print min/mean/max +
an ASCII relief.
*Gate:* stats plausible for the Ortler.
*Result:* 0 holes · min/mean/max = **568 / 2165 / 3835 m** · summit cell = 3835 m · relief
shows a clear valley corridor + high core → `data/ortler_hexes.npz`. PASS.

**S2 — OSM landcover + fed water directions. ✓ DONE.**
*Build:* Overpass landcover (point-in-polygon → `osm` class) + waterways → **river-cell mask**;
direction = **steepest descent on the pit-filled DEM** (map gives the cells, DEM the downhill).
*Resolved choice:* the earlier endpoint-orientation gave 17.3% uphill (coarse heights +
edge-clipped rivers); switching to *map-cells + DEM-downhill* makes it **0 by construction**.
*Result:* 20058 polygons / 6309 waterways; classes plausible (glacier ×9 near summit, valley
farmland @1161 m); **I-FLOW = 0/1325 uphill**, 1351 river cells, 26 window-edge outlets
(downstream leaves the 60 km window) → `osm`, `river_flow`, `river_mask` saved. PASS.

**S3 — Feed into the renderer.**
*Build:* `ortler_render.py` imports `tools/overland_blueprint.py`, builds an `Overland` from
the hex-map arrays via a minimal additive `from_arrays` hook (set `h`/`mat`/`flow`/`acc`,
derive relief, **skip synthesis**), renders to `out/`.
*Check:* **deterministic** (same source → byte-identical PNG); flow **acyclic** (`acc` finite,
drains to sea/edge); render is recognizably the Ortler (user).
*Gate:* deterministic + acyclic + user recognises the Ortler.

**S4 — The two same-scale drawings (the deliverable; compared visually).**
*Build:* render two PNGs on the **same** projection / extent / cell layout →
`out/ortler_actual.png` and `out/ortler_model.png`:
- **(A) realistic** — the triangle mesh shaded as relief (numpy hillshade of vertex `h`) +
  filled with **real OSM terrain types** (the S2 ground truth).
- **(B) our model** — `overland_blueprint` fed our hex map: fine-terrain blend + the
  `material_contest`/`ov_sample` classifier (the S3 render).
*Check:* the two are pixel-aligned (same scale) so they can be **compared by eye** directly;
each region in B is read cold against the same region in A.
*Gate:* user confirms alignment, then runs the cold recognition critic on B-vs-A (the
draw-loop *look*).

**S5 — confusion table + adequacy verdict. ✓ DONE (`gap-analysis.md` Pass 3).**
*Build:* `ortler_stats.py confusion()` — per-triangle OSM (ground truth) vs per-triangle model
bands over all 28800 triangles; agreement on the elevation classes; every OSM class mapped to
an engine `K_*`.
*Result:* **VERDICT — 14 kinds suffice** (no missing kind; all OSM classes have a `K_*` home).
**62% elevation-band agreement**; residual = rock↔scree + glacier/treeline tuning + the
sub-hex discriminator (→ inner-triangle/LOD), not a taxonomy gap.

**S6 — Tune defaults; converge.**
*Build:* adjust the blueprint's `MATS` / band-slope-relief constants (real-metre treeline
~2000 m, snowline ~3000 m) per the table; re-run S3–S5.
*Check:* diagonal mass **before → after** quantified up; render reads better (user).
*Gate:* diagonal dominates; user sign-off.

**S7 — Verdict + loft statistics (built from here).**
*Build:* emit from this directory — the **adequacy verdict** (enough kinds? which to add) +
the tuned per-kind defaults as a **loft-statistics artifact** (a table + a paste-ready
`ov_sample`/`MATS` snippet) — this is what ports to the engine.
*Check:* the artifact maps cleanly to `overland.loft` constants; verdict recorded in this README.
*Gate:* verdict + loft-stats artifact committed in the plan dir.

## Iteration method — the draw-skill loop

S3 → S6 is **not one-shot**; it's the draw-skill craft loop, and convergence is judged
**across passes** (pass 1 is *supposed* to be a coarse block-in — that's a developmentally-
correct baseline, not a defect).

**Verify early, not just at the end.** The comparison render is a standing instrument: run
it on the *first* data to verify each choice (geometry, classification, river orientation)
the moment it lands — don't defer looking to a final step. The S2 I-FLOW finding is the first
such checkpoint.

- **Freeze intent first** → `intent.md` (done), never edited to match the render.
- **Two channels.** *Cheap (text, near-free):* the confusion table, the I-FLOW uphill count,
  elevation stats — all positional/structural intent measured as exact checks. *Expensive
  (a look), sparingly:* the render PNG, spent only on the **gestalt** no number gives — does
  it read as the Ortler?
- **Cold recognition critic.** Read the render **as if you'd never seen `intent.md`** —
  reconstruct what the marks *actually show*, region by region, then diff against reality.
  Critique from the image, **never** from what we meant.
- **Name the failure kind before fixing — this *is* the adequacy decision rule:**
  - **drew-it-wrong** → a wrong number; tune a default (**Goal 2**) and re-render.
  - **tool-can't-express-it** → the 14 kinds physically can't represent this terrain (no
    default makes it read true) → a real **vocabulary gap = add a terrain type (Goal 1)**.
    This is exactly the finding we are hunting; record it in `gap-analysis.md`.
  - **checks-don't-cover-the-intent** → confusion table green but the render still misreads
    → the table is missing a dimension; add it (a green board is false confidence).
- **Converge** until a cold read satisfies `intent.md`'s P1–P5, or a named floor stops us.

## Seed gap hypotheses (HYPOTHESIZED — S5 confirms/refutes)

- **Bare walkable rock vs cliff** — `K_FACE` is impassable-only; vast *walkable* high rock maps
  only to `K_SCREE` or impassable `K_FACE`.
- **Alpine tundra / krummholz band** between treeline and open meadow — lumped into
  `K_FOREST`/`K_MEADOW`.
- **Dry valley steppe / terraced orchard** — the Vinschgau is among the driest Alpine valleys;
  `K_FIELD`/`K_GRASS` may be too generic.
- **Moraine / glacial debris** apron below glacier tongues — distinct from `K_SCREE`?
- **Glacier `K_ICE` vs permanent snowfield `K_SNOW`** — likely adequate; confirm.

## A CONFIRMED defect, handed over from plan #17 — meadow is 0.3 ‰

⚠ **Not a hypothesis and not a taxonomy question — an ordering bug in `ov_kind_at`, measured
2026-08-09.** Found while [#17](../17-safe-supply/) was measuring why no alchemist gatherer
ever spawns (it needs scree-or-meadow ≥14 hexes from a town, and meadow is 15 samples in
48 600 world-wide — rarer than swamp, river *and* glacier ice).

Two rules were written independently and **the earlier one silently voids the later one**:

```
:1280   if h >= SNOWL || (steep > 20.0 && h >= SNOWL - 870.0 && slope < 0.46) {
          … return (h, K_SNOW);              // "snow crouches far down on gentle ground"
:1285   if steep > 20.0 {
          // the alpine zone: meadows claim the gentle ground
:1287     if h >= TREEL { … return (h, K_MEADOW); }
```

`TREEL = 2150`, `SNOWL = 3100` → the snow branch reaches down to **2230 m** and runs **first**,
so meadow gets `2150..2230` — **80 m of the 950 m** its own comments describe (*"treeline:
forest below, alpine meadow above"*).

Bucketed by height over 194 400 samples:

| band | samples | meadow | what is there instead |
|---|---|---|---|
| **A** `2150–2230` — all meadow may occupy | 769 | **72** | scree 165, face 531 |
| **B** `2230–3100` — treeline→snowline | **7 723** | **0** | **snow 1 749**, scree 1 656, face 3 944, ice 369 |
| **C** `3100+` — above the snow line | 2 313 | 0 | snow 2 140 — correct |

Band B is **10× band A with no meadow at all**. Its 3 944 `face` are genuinely steep
(`slope > 0.55`) and its scree is the `band < 0.10` arm — both right. **The stolen ground is
the 1 749 `snow`**: gentle land *below* the snow line that the alpine branch two lines later
exists to make meadow. Freeing it multiplies meadow ~**25×**.

**Recommended fix:** shrink the snow reach-down so it stops at or above `TREEL` — keeping
*"snow crouches far down on gentle ground"* true without erasing the zone the next branch is
written to produce. ⚠ **Left for this plan on purpose**: it changes how the whole world looks
(the user judges aesthetics) and default tuning is this plan's subject, not #17's. It also
partly answers the *"alpine tundra / krummholz band … lumped into `K_FOREST`/`K_MEADOW`"*
hypothesis above — the band is not lumped, it is **overwritten by snow**.

## Roadmap / conditional follow-on

- Verdict **"14 kinds suffice"** → land the S7 defaults into `ov_sample`
  (`src/overland.loft:1170`) with a small `overlandtest.loft` assertion.
- Verdict **"add N kinds"** → its own change (new `K_*` consts + `ov_walkable` +
  `ovmap.loft kind_ch` + `ov_sample` arms + renderer tint); open a follow-on plan, this one
  closes with the verdict.
- Optional: port the tuned Ortler in as a real `overland_from_seed` fixture + `ortlertest.loft`
  in `make test` — a standing real-terrain gate. Ties to **L3 wilderness** (ROADMAP Phase 3 /
  DESIGN §18a).
- **Recursive LOD zoom (future vision).** This 1.5 km triangle model is the **coarse tier** of
  a recursive subdivision: later, zoom into *interesting* triangles (cliffs, water, terrain
  transitions) and build down to a **1.5 m grid** (1000×) to resolve **actual water flow,
  terrain types, and cliff faces** at detail. *Design implication, true now:* the triangle-
  vertex datapoint model + **I-MESH watertightness must hold at every subdivision level**
  (a child triangle's edge vertices are shared with its siblings and its parent's neighbours),
  and the per-world-position + dedup construction is what makes that scale cleanly. The 1.5 m
  tier is where cliff faces (steep `K_FACE`) and real stream channels become resolvable that
  1.5 km necessarily blurs — note the S2 I-FLOW 17.3% is partly that very blur.
- **Interactive WebGL dual-view (future vision).** A WebGL build to *fly* the terrain —
  **WASD** to move across it, **QE** to zoom in/out — keeping the **same dual view** (A actual
  vs B model, side by side) for visual confirmation against real mountain ranges. **QE zoom
  descends the LOD** (1.5 km → … → 1.5 m): closer inspection loads finer triangles, so the
  renderer still just *follows the data* at whatever level is in view. Builds on crawler's
  existing WebGL path (`make game` / `story.html`) and the moros 3D target; the renderer-
  agnostic kernel drives it. Per-vertex/per-triangle classes (`tri_osm`) feed the A-side tint.

## Open questions

- **Extent** — 40×40 hexes ≈ 60 km for now (massif → Vinschgau, ~16 elevation requests);
  extensible to **80×80** later.
- **Overpass volume** — 60 km landcover query may need a couple of bbox tiles.

## loft hazards (CLAUDE.md) — for any eventual port

Pre-allocated array + index-write for cell vectors (loft#320); no `vector<text>` literals in
big fns (loft#336); `== 0` not `!x` for non-booleans.

## Open work — a FLEXIBLE region-fixture system (Wales as the second region)

**PLANNED — not implemented.** Design lives in **`region-fixtures.md`**.

One landform family is not enough ground truth: the Ortler has no coast and no
low-elevation cliffs, so it cannot referee plan #8's F2 (rivers → coastlines) or F3
(hills → cliffs), and "resembles a real range" risks collapsing into "resembles this one
seed". A **second real region — Wales / western Britain** — supplies exactly those, plus
a *mature* upland to contrast with a *young* alpine one.

The point is **flexibility, not a second special case**: a region becomes a **record**
(name, anchor, extent, tile size, layer set) kept as data, so a third region costs data
only and no code. The Severn window is **pinned** at **128 x 89 cells** (5.36 W..2.60 W,
50.75 N..51.95 N) — widened past the Ortler's 80x80 so Pembroke and the inner Severn
funnel are both on it, which also forces the record to allow a **non-square** grid. The loft side is already region-parameterized (`REGION=`,
`src/regions/<name>.loft`, and the Makefile's worked example is literally `wales`); the
Python importer is what is anchored to one region and needs lifting.

Gate for the refactor: the Ortler must keep producing **byte-identical** output through
the generalized path, and the I-GEO round-trip becomes a **per-region** gate.

## Open work — modelling CLIFF FACES

**The gap:** we still have no good way to model a cliff face. `K_FACE` exists in the
taxonomy, but nothing yet produces faces that read as real cliffs at a believable
density.

**What is already known — do not re-derive it:**

| Finding | Where | Verdict |
|---|---|---|
| Slope is useless as a cliff signal at 1.5 km — a hex averages a real face (tens of m) into a gentle ramp | `tuned-defaults.md` § Key finding | VERIFIED |
| "per-triangle slope → cliff, validated by κ" | plan #2 `s6_cliffs.py` | **FALSIFIED** — at ~350 m real resolution forest is as steep as rock; +0.000 κ |
| κ cannot referee sub-hex cliffs at all — the loft world is synthetic, so there is no real sub-hex ground truth to diff against | plan #2 `s6-subhex-finding.md` | VERIFIED — gate on **invariants**, not κ |
| Neighbour-coupled **talus** model: bedrock + weathering rubble, rubble slides to lower neighbours at the angle of repose; stripped steep bedrock → `K_FACE`, piled rubble → `K_SCREE` | plan #2 S6.2, `src/talus.loft`, `talustest` | SHIPPED (invariant-gated: rubble conserved / repose / deterministic / watertight) |
| The talus model's cliff-angle threshold is untuned — 50° reads **~80% face** on the steepest chunk | plan #2 S6 "Left" | OPEN — the visible symptom of this gap |

So the *mechanism* exists and is invariant-gated; what is missing is a principled answer
to **what makes a face a face** — currently a bare angle threshold, which over-produces.

**Candidate directions** (unpinned — the blueprint phase decides):

1. **Threshold → structure.** A face is plausibly not "steep cell" but a *coherent
   vertical step* — a connected run of inter-cell drops. That is a shape predicate, not a
   per-cell angle, and would naturally suppress the 80% smear.
2. **Is one `K_FACE` kind enough?** The goal-1 question, re-asked at the fine tier: does
   a believable range need to distinguish a true rock wall from a steep rubble slope from
   a broken crag? Splitting the kind is in scope for *this* plan.
3. **What is the ground truth?** κ is ruled out. The honest options are an invariant
   (a face must have a top edge, a base, and talus below it) or a **cold-read recognition
   test** on a rendered PNG, in the draw-skill sense — "does this read as a cliff?" —
   which this plan already uses for its two same-scale drawings.

**Method:** exact-invariant work → CLAUDE.md's design/debug protocol. Plot the concrete
end-result first (one specific chunk, the exact faces we want to see), name the
invariant, pin it in Python here in this workshop, and only then touch `src/talus.loft`.
Do **not** tune the 50° constant toward a nicer screenshot — that is symptom-chasing at
the threshold the falsified premise already left behind.

**Coordination with plan #2:** #2 owns the LOD machinery and `src/talus.loft`; this plan
owns the terrain *vocabulary* and the adequacy verdict. A kind split or a changed face
predicate decided here lands as an S6 change there — cross-link both ways when it does.

## See also

- `tools/overland_blueprint.py` — the world-drawing instrument; `material_contest` = the
  `ov_sample` kind twin; `center`/`neighbors` (`:130–138`) = the shared geometry.
- `src/overland.loft` — `ov_sample` zonation (`:1170`), the 14 `K_*` kinds (`:26`),
  `ov_walkable` (`:42`).
- `src/ovmap.loft` — `kind_ch` glyphs. `src/overlandtest.loft` — the I1/I2/I3 gate.
- `OVERLAND.md` §12–13 — the wilderness contract.
