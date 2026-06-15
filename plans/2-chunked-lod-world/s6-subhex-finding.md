# S6 — sub-hex cliffs/channels: blueprint finding (the κ premise is falsified)

> Detail doc for @PLN2 **S6**. Per the design-protocol, S6 started in the cheapest medium (the
> @PLN1 Ortler Python, which has real OSM + real EU-DEM per triangle) **before** any loft code.
> The blueprint *falsified* the core hypothesis cheaply. This records the result + the fork.
> Prototype: `s6_cliffs.py` (run from `plans/2-chunked-lod-world/`).

## The hypothesis (S6 as designed)

> At the 1.5 m detail tier, per-triangle **slope** resolves **cliffs** (`K_FACE`) and the fed
> **flow** resolves **channels** (`K_RIVER`) that the 1.5 km hex classification blurs — and the
> @PLN1 **spatial-κ**, re-run at the fine tier, *improves* for cliff / channel / rock-scree.

## What the data says (real Ortler, 1600 hexes × 18 inner triangles, per-triangle OSM + EU-DEM)

The triangle vertices are **real EU-DEM samples** at the 19 sub-hex points (hex centre + 6 corners
+ 12 edge-thirds, ~250–750 m spacing) — not interpolation. So this is the finest *real* signal the
@PLN1 fixture holds.

**Per-OSM-class triangle slope (deg):**

| class | n | slope p50 | slope p90 |
|---|--:|--:|--:|
| rock | 2471 | **25.2** | 38.1 |
| scree | 3062 | 22.5 | 33.7 |
| **wood** | 7220 | **25.9** | 35.9 |
| grass | 2243 | 21.1 | 31.8 |

**Per-hex local relief (real sub-hex height spread, m):** rock p50 = 649, **wood p50 = 706**.

**Forest sits on terrain just as steep and rugged as rock.** In the Alps the rock/vegetation
boundary is the **treeline (an elevation + exposure effect)** — already captured by the height
bands — *not* a geometric one. So:

- **`slope > θ → cliff` gives ZERO κ gain.** Sweeping θ: best κ **+0.464 at θ=50°** — *identical*
  to the height-band baseline (+0.464). At low θ it makes κ *worse* (calls steep forest rock).
- **Local relief / roughness doesn't discriminate either** (wood is higher-relief than rock).

Verdict: **no simple geometric sub-hex signal (slope, relief) separates cliffs from forest at the
~350 m real-data resolution.** The height-band baseline (κ=+0.464, rock/scree recall 0.731) is
effectively the achievable ceiling for *this* data. The blueprint falsified the premise — exactly
what the cheap medium is for, before writing loft code that couldn't have hit its gate.

## Why — two compounding reasons

1. **Resolution.** Real cliffs are <100 m features; the @PLN1 fixture samples at ~250–750 m. A
   cliff is averaged into the general mountainside slope. To *test* sub-100 m cliffs we'd need a
   **dense 25 m DEM + 25 m OSM raster** for a small sub-window (not hex-point samples).
2. **The loft detail tier samples synthetic fbm, not real terrain.** Even a working cliff rule in
   loft would carve cliffs out of *procedural noise* over the contract wilderness — there is **no
   real reference to compute κ against** for the loft world. The κ gate only ever made sense in the
   @PLN1 Ortler-Python world; it does not transfer to the loft detail tier as-is.

## The fork (needs a decision)

- **(A) Fetch finer real data + re-test.** Pull a dense 25 m EU-DEM + 25 m OSM raster for one
  interesting sub-window (~1.5 km² ≈ 60×60 = 3600 pts ≈ 36 OpenTopoData requests, within the
  1000/day cap). Derive cliffs (25 m slope, maybe + `natural=cliff` OSM tag) + channels (25 m flow)
  and test whether κ improves *there*. This is the faithful S6 validation. Cost: a network fetch +
  a new fine-grid pipeline.
- **(B) Rescope S6 to procedural generation (unvalidated).** Generate plausible cliffs/channels at
  the loft 1.5 m tier from the fbm height field + the fed flow (slope→`K_FACE`, flow→`K_RIVER`) as
  **terrain generation**, explicitly *not* validated against real data (the κ gate is dropped — it
  can't apply to the synthetic field). Renderer-follows-data still holds (derivation is upstream of
  the renderer). Honest, but loses the "grounded in real terrain" claim for sub-hex features.
- **(C) Defer S6.** The detail tier (S3–S5) already renders the engine's fbm sub-hex height + the
  hex-level kinds; that is coherent and shippable. Sub-hex *feature classification* waits until
  there's a real reason (a consumer that needs walk-blocking cliffs / fordable channels) and the
  data to validate it.

## The chosen approach (2026-06-15): the TALUS model (generation, neighbour-coupled)

The fork above resolved by reframing from *classification-of-real* to *geomorphological generation*
(user's steer): **a rubble/angle-of-repose model, combined with ZAngband-style neighbour blending.**

- Each cell carries **bedrock** (`ov_sample` height) + a **rubble** layer (a per-triangle weathering
  "factor"). Rubble can't hold a slope steeper than the **angle of repose** (~35°), so it **slides to
  lower neighbours** (a sandpile relaxation) until every rubble surface ≤ repose.
- Where bedrock alone exceeds repose, rubble strips away → **bare rock face (`K_FACE`)**; the shed
  rubble piles at the base → **scree talus (`K_SCREE`)**. **Cliff placement + height = the bedrock
  step to neighbours** — fully neighbour-coupled (no per-triangle-in-isolation slope).
- **Combined with ZAngband:** the coarse, neighbour-blended classification (@PLN1's model — rock
  zones grow into neighbours, coherent adjacent-triangle noise) sets *where* a cell is bedrock-rocky
  (eligible for faces) vs soil-mantled (forest/grass — vegetation holds rubble, no faces). The talus
  runs within the rocky zones.

**Gate is the INVARIANTS, not κ** (κ-vs-real is impossible here and now moot): rubble **conserved**,
relaxed rubble surface **≤ repose everywhere** (faces are the only steeper cells, only on exposed
bedrock), **watertight** across triangle/chunk seams, **deterministic**.

### Step S6.0 — 1-D mechanism PINNED (`s6_talus1d.py`)

Uniform rubble mantle over a plateau→cliff→valley bedrock profile. After relaxation: the cliff cells
strip to 0 rubble (rock face), the shed material forms a talus apron at repose below. Invariants:
rubble conserved (60.00→60.00, Δ0), max rubble-on-rubble step 0.70 ≤ SR 0.70. The geomorphology reads
correctly. **Mechanism confirmed in the cheapest medium.**

## Plan (gated)

- **S6.0** ✅ 1-D talus relaxation + invariants (`s6_talus1d.py`).
- **S6.1** ✅ 2-D talus, weathering-driven rubble (`s6_talus2d.py`). On a fine alpine patch
  (representative of the loft detail field — real Ortler bedrock is too smooth at samplable
  resolution to ever exceed repose, confirming `s6_cliffs`). 4-neighbour Gauss-Seidel sandpile;
  weathering rubble rises above the treeline. **Invariants hold:** rubble conserved (Δ 2.5e-11),
  max rubble-on-rubble step = repose exactly. **Geomorphology correct:** the escarpment relaxes to
  a clean `K_FACE` band, scree pools below as talus, and the **ZAngband treeline gate** keeps bare
  faces above the treeline (below → forest holds its rubble, `f`=forest-cliff, no bare rock).
  **Tuning note for S6.2:** face frequency ∝ (fbm local step vs repose×cell-size); high fbm
  amplitude speckles the alpine zone with spurious faces — tune amplitude, and/or require a
  *sustained* steep run (not a single rough cell), so faces land on genuine cliffs.
- **S6.2** ✅ ported to loft (`src/talus.loft`): `talus_chunk(ov,dcx,dcz)` samples bedrock + base
  kind over a **32+2·HALO** grid (HALO=4), mantles weathering rubble (`weather_rub`, rises above the
  treeline), relaxes with a **capped** (`TALUS_ITERS=120`) 4-neighbour sandpile (`talus_relax`),
  surface = bed+rubble, and classifies `K_FACE` (rubble stripped + bedrock past the **cliff** angle
  50° — separate from the 35° repose so forested slopes don't all turn to rock) / `K_SCREE` (alpine
  rubble accumulation) gated by the treeline. **Watertight is automatic** (chunk_mesh shares edges
  from the neighbour's cells + `talus_chunk` is deterministic — no seam-exact relaxation needed).
  Headless gate **`talustest` (in `make test`, TALUS OK):** rubble conserved (768→768), repose
  satisfied (max 1.0257 ≤ sr 1.0257), deterministic, faces=812 on the flank cliff, scree=303 on an
  alpine chunk. Wired into the viewer behind **`VIEWER_TALUS=1`** (generation-time, ~50 s for the
  detail window). **Tuning note (user's visual call):** the (143,83) flank averages ~62°, so at the
  50° cliff threshold it renders ~80% bare face — model-correct but erases the mixed look; the
  cliff-angle threshold is the knob.
- **S6.3** ✅ flow-carved channels (`talus.loft` `flow_accumulate` + `T_CHANNEL`). D8 steepest-descent
  flow over the talus surface, accumulation by wavefront propagation downhill; cells with upstream
  drainage > `T_CHANNEL` (45) → `K_RIVER`. The engine's major rivers are fed in via `ov_sample`'s
  base kind (now **preserved** — `talus_kind` no longer weathers water/wetland to rock); S6.3 adds
  the fine tributaries. **Gate (in `talustest`):** flow accumulation correct (a tilted plane drains
  to its outlet, maxacc = n) — flow is strictly downhill by construction (the I3 echo); channels
  appear (83 `K_RIVER` cells on the flank). Visible in the `VIEWER_TALUS=1` frame as blue channels
  threading the drainage.

## Superseded

The earlier "(A) fetch / (B) procedural / (C) defer" fork is resolved: **(B′) procedural but
*physically grounded* (the talus model)**, gated by invariants. The κ-improvement gate is dropped as
inapplicable (no real sub-hex reference; loft world is synthetic). `s6_cliffs.py` stays as the record
that *isolated* slope doesn't work — which is *why* the neighbour-coupled talus model is needed.
