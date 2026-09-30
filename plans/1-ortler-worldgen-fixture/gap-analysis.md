# gap-analysis.md — findings (verified vs hypothesized)

Iteration findings from the comparison render. A finding is **VERIFIED** only when it shows
on the real Ortler data; otherwise **HYPOTHESIZED**.

## Pass 1 — untuned model (2026-06-15, `out/ortler_compare.png`)

First verify-early look: real heights injected into `overland_blueprint`, B classified by the
*untuned* `material_contest`, A tinted by OSM. Failure kinds named per the draw-skill taxonomy.

| # | Finding | Kind | Status | Fix |
|---|---------|------|--------|-----|
| F1 | **B is all rock/snow.** Material thresholds (`h>640` rock, `>800` snow) are compressed-range; every real height 2000–3835 m → rock/snow. | drew-it-wrong (defaults) | **VERIFIED** | S6: real-metre thresholds (treeline ~2000, snowline ~3000) |
| F2 | **Spurious lakes — quantified: model 72 lakes vs OSM 6 water cells (~12×).** Pit-fill floods local 1.5 km basins. Lakes near-level (I2 spread 0.5 m, not exact). Water-not-into-lakes routine had to clip 1776 river segments running through them. | model behaviour | **VERIFIED** | gentler fill / lake-area floor + exact-level pass; or accept as 1.5 km blur (→ 1.5 m LOD resolves) |
| F3 | **Artifacts all over (diagonal hatch + spiky relief, apparent drop-to-0).** ROOT CAUSE: the blueprint's procedural enrichment — `fine_height_of` relief amplification (calibrated for ~100 m relief; real alpine relief = **2360 m** → render height blew up to **5649 m**, ~1800 m of spurious spikes), plus `detail` fbm and per-pixel `dither` grain. NOT literal zeros (0 px < 50 m). | tool/render artifact | **FIXED** | added `real_height=True`: render the smooth blended **real** height (`f["h"]`) directly, skip `fine_height_of`/detail/dither. Both views now clean. |
| F4 | Vertical zonation (intent P2) not yet visible — can't judge taxonomy adequacy until B is tuned (F1). | checks-not-ready | blocked on F1 | re-render after S6 |

**Taxonomy verdict: not yet** — F1 must be fixed before B's classification is meaningful. No
*tool-can't-express-it* (new-kind) finding can be trusted until then.

## Pass 2 — model tuned to data-derived bands (2026-06-15, re-render)

B re-classified by the `tuned-defaults.md` real-metre bands, same palette as A.

| # | Finding | Kind | Status | Note |
|---|---------|------|--------|------|
| F1 | **FIXED.** B now shows forest→alpine→scree/rock→glacier banding (not all-snow); broad structure matches A. | resolved | DONE | data-derived bands work |
| F5 | **B over-forests the mid band.** Model paints continuous forest 1100–2150 m; A is patchier (rock/scree/unmapped intermixed) there. | drew-it-wrong + sub-hex | **VERIFIED** | pure elevation-banding overpredicts vegetation; the missing discriminator (slope/aspect/cliff) is **sub-hex → inner-triangle** (see `mesh-pin.md`) |
| F6 | No *tool-can't-express-it* (missing-kind) finding yet — the Ortler's OSM classes all map to existing `K_*` (glacier→ICE, snow→SNOW, rock/scree→FACE/SCREE, grass→MEADOW, wood→FOREST, valley→GRASS/FIELD). | adequacy (preliminary) | **HYPOTHESIZED** | confirm with the full confusion table (S5) |

**Preliminary adequacy read:** 14 kinds look *sufficient* for the Ortler at hex scale; the
real gaps are (a) tuning the bands (done, F1) and (b) sub-hex structure — cliffs/channels —
which is the inner-triangle / 1.5 m-LOD job, not a new hex kind.

## Pass 3 — S5 per-triangle confusion (VERDICT)

Per-triangle OSM (ground truth) vs per-triangle model bands, 15989 classified of 28800.

**F6 → VERIFIED. Adequacy verdict: the 14 `K_*` kinds SUFFICE for the Ortler — no missing
kind.** Every OSM class maps to an existing engine kind: water→`K_LAKE/K_RIVER`, glacier→
`K_ICE`, rock→`K_FACE/K_SCREE`, scree→`K_SCREE`, wood→`K_FOREST`, grass→`K_MEADOW`,
farmland/orchard/vineyard→`K_FIELD`, wetland→`K_SWAMP`. No *tool-can't-express-it* gap.

**Goal 2 tuning — 62% elevation-band agreement** (glacier/rock/scree/wood/grass). Confusions:
| OSM | model mostly says | tuning hint |
|-----|-------------------|-------------|
| rock ↔ scree | scree 1030 / rock 813 (rock); scree 1493 / rock 706 (scree) | elevation can't separate; needs **slope/context → sub-hex (inner-triangle/LOD)** |
| glacier | rock 179 / glacier 301 | snowline 3100 m slightly high; glacier tongues descend lower |
| grass | wood 813 / grass 909 | treeline 2150 m slightly high on some aspects |
| water, farmland, wetland | (band model can't) | handled by engine `K_LAKE`/`K_FIELD`/`K_SWAMP` logic, not elevation bands |

**~62% is the ceiling for elevation-only at 1.5 km.** The residual is the sub-hex
discriminator (slope/aspect, cliffs, channels) the **1.5 m LOD** resolves — not a taxonomy or
a hex-band fix. Cliffs (`K_FACE`) stay deferred to the inner-triangle algorithm.

## Pass 4 — spatial-agreement metric + the switch-to-loft decision

Beyond marginal/per-tile matching, added a **per-triangle spatial-agreement** metric
(`ortler_render.spatial_agreement`): B's class vs A's class at the *same* triangle, coarse-group
+ chance-corrected κ. Result (80×80, model B with neighbour-grown rock + eroded ag +
coherent-noise per-triangle bands):

- exact-class **54%**, coarse-group **63%** (chance 33%, **κ = +0.45** — moderate, real skill).
- Per-group recall: **rock 71%, forest 77%** (elevation-driven → placed well); **open grass 30%,
  field 23%, ice 44%, water/wet 0%** (NOT elevation-driven → placed poorly: B has no signal for
  *where* grass/fields/glacier-tongues actually are).

**Decision: stop extending the python model; switch to loft.** The weak spots need town
placement + river sizes + fields-near-water — which the **loft engine already has**
(`overland.loft`: `ov_towns`/`ov_roads`, `ov_sides` with `os_acc`+`os_w` = sized rivers, the
farmers'-rule `K_FIELD` near towns, swamps at confluences). Re-implementing them in python would
duplicate the engine. The python prototype achieved its purpose: derived + validated the
real-metre defaults (ported, `make test` green), settled the taxonomy verdict, and built the
comparison machinery (material% / 16-tile / occurrence / spatial-κ). Further fidelity is
loft-side → plan #2.

## Investigation outcome

Both goals answered: (1) **14 kinds are enough**; (2) tuned real-metre defaults in
`tuned-defaults.md`, with the named confusions as the residual. Remaining work is engineering,
not investigation — port the defaults (conditional follow-on) and/or build the LOD.
