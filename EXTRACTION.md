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
- **Consume locally NOW via a `--lib` dir** (VERIFIED 2026-06-10): the compile-time
  `use` resolver searches *local src → package lib dirs → `--lib` dirs → sibling
  packages* — crawler adds `--lib ../loft-libs-game/` to LOFTFLAGS exactly like the
  bundle dirs. (A `{ path = ... }` manifest dep is honoured by `loft test --deps` but
  NOT by compile-time use-resolution — PACKAGES.md overpromises there; tracked as a
  doc/impl divergence. Sibling layout + `loft install .` also verified working.)
- **Registry publication** is the five-step flow in loft2 `doc/claude/REGISTRY_SUBMIT.md`
  (see "Updating a library" below) — done when a package settles.
- **The crawler gate keeps guarding**: after each extraction the same 33 tests run
  against the lib code; the in-repo module is DELETED (never two copies drifting).

## Updating a library repo (the change loop, per contribution)

Library work happens IN the lib repo under its own gate — crawler stays a consumer.
The loop, end to end:

1. **Sync**: `git fetch origin && git checkout main && git pull --ff-only` in the lib
   repo (never branch from a stale main).
2. **Branch per change**: `git checkout -b feat/<short-name>` (or `fix/...`); one
   reviewable concern per branch.
3. **Change + the repo's OWN gate locally**: the package's `loft test` (+ the repo's
   `make test`/CI script if present) green BEFORE pushing — same discipline as
   crawler's gate-before-commit.
4. **PR with the trace**: `git push -u origin <branch>` then `gh pr create` — the PR
   body links the DRIVING context (the crawler EXTRACTION step, the loft issue, or the
   plan doc) so the change is traceable to its reason; reference issues with `#NNN` so
   the trail is bidirectional.
5. **CI + review**: `gh pr checks --watch` until green; address review; never merge red.
6. **Merge**: `gh pr merge --squash --delete-branch` (one commit per concern on main,
   the PR body preserved as the trace).
7. **Register the change** (when releasing — not every merge needs a release):
   1. bump `[package] version` in `loft.toml` (+ changelog note);
   2. `git tag v<version> && git push --tags` (the tag MUST match the manifest);
   3. `loft package` → deterministic tarball + sha256 + a ready index entry;
   4. `gh release create v<version> <tarball>` (never edit assets afterwards — fix =
      yank + next patch version);
   5. PR the index entry against `loft-lang/registry` (`index.json`; the registry's CI
      re-checks the reproducible build; the maintainer signs the index).
8. **Consumers switch**: crawler moves that package from the dev `--lib` dir to the
   registry version and re-runs its gate.

## Extraction Definition of Done (per package)

1. The package builds standalone (`loft test` in its folder, with at least a smoke test).
2. crawler consumes it (dev: the `--lib` dir; released: the registry version) and the
   duplicated `src/` module is **deleted**.
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

- [x] Chunk repo created: **`../loft-libs-game/`** (LICENSE + README per the loft-libs
      conventions; local git — the GitHub remote is the owner's step).
- [x] Package `hexgrid` (v0.1.0): hexgeo + gridgeo merged into one module; the colliding
      trio renamed DESCRIPTIVELY per basis (`hex_`/`cell_` `neighbor_dir`, `edge_corners`,
      `canon_edge` — the technical layer keeps technical names; a friendlier drawing
      abstraction can sit above later); `GRID_SIZE`/`GRID_LEN` now pub. (LOS stays in sim
      until the Tier-2 parameterization — it takes a Sim today.)
- [x] 10 package tests under `--deny-warnings` (round-trips, metric, neighbor ring +
      inverse, shared-edge canonicalization for BOTH bases, corner circumradius).
- [x] crawler switched: Makefile LIB_DEPS + `use hexgrid;` across 23 files, six renamed
      call sites, `src/hexgeo.loft` + `src/gridgeo.loft` DELETED (the no-drift rule).
- [x] Gate 33/33; the package header documents the moros convention.
- [ ] (Owner) release per the "Updating a library" flow; crawler switches off the dev `--lib`.
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

### 4. `random` — a VALUE-stream API for the EXISTING loft-libs-core package

EVALUATED 2026-06-10: `loft-libs-core/random` already exists (v0.1.1, unpublished) —
native **Pcg64** (better math than crawler's weak ANSI-C LCGs), seeded + reproducible,
11/11 tests, builds + runs locally (its own native crate compiles with the active rustc;
E0514 only bites programs linking the prebuilt rlib), and `rand_indices(n)` is exactly
the flavour-shuffle primitive. So: EXTEND, don't create.

**The gap:** the API is one **hidden thread-local global stream** (`rand_seed` reseeds
*the* generator). Deterministic games need **multiple independent streams with visible,
persistable state** — crawler runs three (per-level world-gen; the Sim's combat `rstate`,
carried across descend for save/replay/MP; the per-game flavour shuffle). One global
stream means any new call site reorders every stream after it, and state hidden in a
thread-local can't be saved with the Sim.

- [x] **LANDED — loft-libs-core PR #9, merged 2026-06-10, CI green, 23/23 under
      --deny-warnings, version 0.2.0.** The METHODS way: `pub struct RandStream { ... }`,
      `seed_stream(seed) -> RandStream`, `get(self: RandStream, lo, hi) -> integer`,
      `indices(self: RandStream, n) -> vector<integer>`. The by-value receiver mutates
      the stream (a struct param is a store link — no `&` needed; `&` only relinks a
      stack variable). Pure-loft state + math (overflow-trapped 64-bit ints: keep
      products < 2^63 — MINSTD-style works; the owner may prefer a stronger pure-loft
      step or a native one). Probe: advance/reproducibility/isolation/permutation all
      green; found loft#322 (stale program-cache on lib edits) along the way.
- [x] Cross-module exercise: the package's own test module drives the streams (12
      tests incl. the isolation property: interleaved draws == the plain sequence;
      global calls never move a stream).
- [x] **crawler ADOPTED (2026-06-10, gate 33/33)** — all three streams: the flavour
      shuffle (`st.indices(FLAVOUR_POOL)` — hand-rolled LCG + Fisher–Yates deleted),
      the placement stream (`SimRng` struct deleted — the C4-era same-module shim),
      and the Sim's combat rolls (`rstate` → the stream's `rs1`/`rs2` state words
      riding the Sim: rolls now save/replay/descend through the lib). Consumed via
      the Makefile's LIB_DEPS `--lib ../loft-libs-core-main/` (a read-only git
      worktree of the repo's origin/main, so the consuming state is independent of
      the working repo's checked-out branch). `sim_seed_rolls` is pub — tests pin
      their streams (itemtest pins a both-drop-kinds seed).
- [ ] (Owner) first registry release rides the value-API landing.

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
