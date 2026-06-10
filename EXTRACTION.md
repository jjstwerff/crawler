# EXTRACTION.md — pushing crawler's reusable routines to the library layer

The standing goal (everything here is built toward a coherent reusable library for many
games) gets its concrete plan. Verified ground (2026-06-10): the cross-module `&Struct`
bug (C4) is **fixed** — the one structural blocker for shared libraries is gone; the two
live loft bugs (#319 struct-literal comprehensions, #320 capture-append-reassign) are
*shape* bugs with clean style rules, and the Tier-1 candidates don't even contain structs.

## Mechanics (what "extract" means here)

- A **library package** = a folder with `loft.toml` (`[package]` + `[library] entry =
  "src/<name>.loft"`), living in a chunk repo (`loft-libs-graphics` style: several
  packages per repo). One package = one `use`-able module name.
- **Consume locally NOW via a path dep** — crawler's `loft.toml`:
  `hexgrid = { path = "../loft-libs-game/hexgrid" }`. No registry needed to develop.
- **Registry publication** (tarball + sha256 + signed `index.json` + GitHub release) is
  the OWNER'S publish flow, done when a package settles — the plan marks it as a
  separate final step per package.
- **The crawler gate keeps guarding**: after each extraction the same 33 tests run
  against the lib code; the in-repo module is DELETED (never two copies drifting).

## Extraction Definition of Done (per package)

1. The package builds standalone (`loft test` in its folder, with at least a smoke test).
2. crawler depends on it via `loft.toml` and the duplicated `src/` module is **deleted**.
3. `make test` green (33/33) + `make check` clean against the dep.
4. The API follows the **globally-unique pub-name** discipline (the C23 lesson — the
   native tier flattens module fns to global symbols).
5. Style rules honoured (the two live bugs): no struct-literal comprehensions (#319 —
   explicit loop+append); no capture-append-reassign on struct fields (#320 — direct
   append or index-writes).
6. Docs: the package README states its convention/contract; crawler's CLAUDE.md "Where
   things are" updated.

**Environment caveat (not a blocker):** the local installed `libloft.rlib` is rustc-1.95
vs active 1.96, so a `use`d package's auto-native cdylib fails locally (E0514) and falls
back to the interpreter — correct, just not the optimized tier. Fix when convenient:
install a loft built with the active rustc (the `cargo +1.96.0` recipe) or pin the
default toolchain to 1.95.

---

## Tier 1 — implementable NOW

### 1. `hexgrid` — the canonical hex geometry (+ the 12-orientation square basis)

The flagship: `hexgeo` implements the **moros convention** (pointy-top, odd-r,
`L = √3`) that moros itself only documents; extracting makes the convention *executable*
in one shared place. `gridgeo` belongs with it — its whole purpose is the 90°-square
local basis FOR objects placed on the hex world (12 × 30° orientations matching the hex
lattice), meaningless apart from it. Both are struct-free, import-free, game-free.

- [ ] Create the chunk repo home — **decision: a new `loft-libs-game/`** (game-domain
      packages: `hexgrid` now; `roguelike-kit` later) — or fold into an existing chunk
      if preferred. (`git init` + the loft-libs repo conventions; GitHub repo = owner.)
- [ ] Package `hexgrid`: `loft.toml` + `src/hexgrid.loft` = hexgeo merged with gridgeo
      (one `use hexgrid`; sectioned: hex lattice / conversions / LOS / the square basis).
      All pub names already distinct.
- [ ] A standalone smoke test in the package (round-trip `hex_to_px`/`px_to_hex`,
      `hex_distance`, neighbor ring, `cell_to_px` rotation) — `loft test` green.
- [ ] crawler: `loft.toml` dep (path form), `use hexgeo;`/`use gridgeo;` →
      `use hexgrid;` everywhere, DELETE `src/hexgeo.loft` + `src/gridgeo.loft`.
- [ ] Gate 33/33; README documents the moros convention (+ link to
      `moros/doc/claude/SCENE_MAP.md`).
- [ ] (Owner) publish to the registry; switch the path dep to a version dep.
- [ ] (Later, separate) moros adopts `hexgrid` for its tooling where loft runs.

### 2. Text layout helpers → `loft-libs-graphics`

`fit_text` (pixel-accurate ellipsis truncation) + `wrap_text` (greedy pixel word-wrap)
are pure functions over `gl_measure_text` — every text-bearing loft app rewrites them.

- [ ] Add a `text layout` section to the graphics package's API (the lib repo's working
      tree, branch `fix-255-program-relative-font` — lands via that repo's own gate):
      `pub fn fit_text(font, str, max_w, size)` + `pub fn wrap_text(...) -> vector<text>`.
- [ ] crawler: drop its local copies, call the lib's (the view already `use graphics`).
- [ ] Gate green. (Publish rides the graphics package's next release.)

### 3. `tools/draw.py` flow-back → the draw skill (loft repo)

crawler's copy gained `Background transparent` (+ this week exercised `flat=`
foreshortening and `grad=` fills hard; rotation/atlas named next). The skill's
`sketch/draw.py` is the library layer for sprite authoring.

- [ ] Diff crawler's `tools/draw.py` vs the skill's `sketch/draw.py`; port the
      extensions upstream (the skill's own examples must still render).
- [ ] Note in the skill's docs: the sprite-authoring techniques proven here
      (rim-ring readability, discrete blotches over traced patterns on smoothed
      paths, menace-via-posture, the join discipline) — doc, not code.
- [ ] crawler keeps its copy only if it still carries unported experiments;
      otherwise delete and call the skill's.

### 4. `random` — seeded RNG + shuffle → `loft-libs-core` (NEWLY UNBLOCKED)

C4 (cross-module `&` mutation) verified fixed — a shared `Rng` struct mutated through
`&Rng` from any module now works. crawler has three private LCG copies (sim's `SimRng`,
gen's, the flavour shuffle) begging to be one package.

- [ ] Package `random` in `loft-libs-core`: `rng_seed(seed) -> Rng`,
      `rng_int(&Rng, lo, hi)`, `rng_float(&Rng)`, `rng_shuffle(&Rng, v)` (Fisher–Yates),
      deterministic by contract (games replay; no ambient entropy).
- [ ] A soak guard: keep crawler's in-module RNGs until the package passes a
      cross-module hammer test (N modules bumping one `&Rng`, interpret + native),
      then swap sim/gen/flavours over one at a time, gate green after each.

---

## Tier 2 — one decoupling each, then they join `hexgrid`

- [ ] **`wallgeo`** (hex-region → smoothed wall outlines): replace its `use sim` with
      parameters (tiles vector + dims + a solid-predicate); then move into
      `loft-libs-game` beside hexgrid.
- [ ] **`gen`** (rooms + corridors): replace `use rooms_gen` (the bundle registry!) with
      a room-config parameter (the caller passes RoomDefs); then extract as the seeded
      hex dungeon generator.

## Tier 3 — gated (do NOT extract yet)

- **`roguelike-kit`** (energy/speed scheduler, status-until-tick timers, flow-field
  pathing, message ring): genuinely reusable, but lives inside `Sim` — extraction is
  earned by a SECOND roguelike existing (rule of three), not before.
- **The bundle system** (gen_bundles.py + catalog merge + routine-by-id): the most
  valuable candidate and the most premature — SCRIPTING.md Stage 1 (the event bus) will
  reshape the routine seam. Extract after that lands and the shape survives two
  consumers.

## Order of work

1 (`hexgrid`) → 2 (text layout) → 3 (draw.py flow-back) → 4 (`random`, behind its soak
guard) → Tier 2 decouplings opportunistically. Each step independently shippable,
each ends gate-green.
