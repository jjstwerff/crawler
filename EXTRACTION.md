# EXTRACTION.md — pushing crawler's reusable routines to the library layer

> The FAMILY-side plan (how these routines merge with hex_world / gridmesh / dryopea's
> wall.loft / moros tooling into one coherent basis, + the capability roadmap: round
> towers, 24-direction walls, cliffs, water flow, collision, LOS, hearing):
> **loft-libs-world/CONVERGENCE.md**.

The standing goal (everything here is built toward a coherent reusable library for many
games) gets its concrete plan. Verified ground (2026-06-11): the structural blockers for
shared libraries are gone; the one live shape bug (#320 capture-append-reassign — fixed
upstream, still in the installed 0.8.5) has a clean style rule, and the Tier-1 candidates
don't even contain structs.

## Library-handling state (loft, 2026-06-14)

What the recent `../loft` work (branch `cleanup`) changes for crawler as a CONSUMER. Most
of it tightens or *removes* old caveats; act on the marked items when convenient.

- **Resolution precedence — `--lib` outranks the registry (VERIFIED).** `Parser::lib_path`
  tries `--lib`/`lib_dirs` *before* the `~/.loft/registry/` probe, so a sibling shadows a
  same-named registry copy. The ONE catch on the installed **0.8.5**: the **#322
  stale-program-cache** bug doesn't invalidate when a `--lib` dep is added/edited, so it
  keeps serving the registry binding until the cache is busted (`LOFT_NO_CACHE=1`, or a
  toolchain refresh past #322 which self-invalidates). A `path` dep in `loft.toml`
  (`graphics = { path = "…" }`) is higher-precedence still and flag-independent, if a
  committed pin is wanted. (This is the corrected story behind plan #7's L0.)
- **Native libs are largely toolchain-free now (@PLN21 / #370, MERGED).** A loft native
  artifact is a **cdylib** linking loft-ffi's C-ABI, keyed on a *loft-ffi fingerprint*, not
  rustc — so **hand-written** native (`graphics`, `random`, `gridmesh`) is rustc-INDEPENDENT
  (E0514 was only ever an **auto-compiled**-native problem; see the DoD caveat above).
  `prebuilt/<triple>/` cdylibs + `[native] runtime-libs`/`build-deps` manifest fields mean a
  fresh machine can `use graphics` with **no rustc/~90 s compile** once the registry ships
  the binaries (distribution scoped to hand-written libs; auto-native stays a loft-release-CI
  artifact). Crawler's `make game` E0514 note narrows accordingly.
- **▶ TODO (cheap win) — generate `.loft/api/*.api` stubs (#362, SHIPPED).** `loft
  install/update/pin` now writes committed, diffable API stubs (every `pub` signature) for
  each locked dep, and `loft api <name>` prints a lib's public surface. crawler's deps
  (`graphics`/`hex_grid`/`hex_terrain`/`random`) live under `~/.loft` — invisible to an agent
  in this tree. Committing `.loft/api/` would let an agent read the exact signatures instead
  of guessing. Do after a toolchain refresh exposes the command.
- **Registry is signed now (#371, MERGED).** Three-key Ed25519 trust root; once a refreshed
  toolchain embeds the keys, `loft install`/auto-install **requires** a signed `index.json`
  or hard-fails. Operational note for the next `make install`.
- **`lib_audit` @PLN20 (design ready, unimplemented).** A nightly health gate over the
  `loft-libs-*` packages crawler consumes — catches a lib silently rotting against current
  loft. Nothing to do; expect greener libs once it lands.
- **Catalog currency.** `graphics` + `random` registry copies are STALE (their repos are
  ahead); `hex_grid`/`hex_terrain` are NOT published yet (crawler rightly consumes them
  sibling-side via `--lib`). The §1/§4/§5 owner registry-release tails are what close this.

## Mechanics (what "extract" means here)

- A **library package** = a folder with `loft.toml` (`[package]` + `[library] entry =
  "src/<name>.loft"`), living in a chunk repo (`loft-libs-graphics` style: several
  packages per repo). One package = one `use`-able module name.
- **Consume locally NOW via a `--lib` dir** (VERIFIED 2026-06-10): the compile-time
  `use` resolver searches *local src → package lib dirs → `--lib` dirs → sibling
  packages* — crawler adds `--lib ../loft-libs-world/` to LOFTFLAGS exactly like the
  bundle dirs. (Sibling layout + `loft install .` also verified working.)
  **UPDATE 2026-06-14 — loft#337 is FIXED (CLOSED upstream, independently re-verified):**
  a `{ path = "../leaf" }` manifest dep now compile-time use-resolves on the
  **2026-06** loft (positive + negative-control probe: drop the edge → `use` fails,
  restore it → resolves). The installed **0.8.5 still has the bug**, so `--lib` stays
  the dev route until the toolchain refresh — after which crawler can switch its
  `--lib ../loft-libs-world/` etc. to cleaner `{ path = … }` deps in `loft.toml`.
- **Registry publication** is the five-step flow in loft2 `doc/claude/REGISTRY_SUBMIT.md`
  (see "Updating a library" below) — done when a package settles.
- **The crawler gate keeps guarding**: after each extraction the full gate (39
  tests today) runs against the lib code; the in-repo module is DELETED (never
  two copies drifting).

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

### Worked example — graphics 0.2.0, the first release driven from here (2026-06-14)

The end-to-end flow, VERIFIED, with the gotchas that bit. Needs the **refreshed loft**
(`../loft` cleanup build at `target/release/loft` — the installed 0.8.5 lacks
`package`/`publish`/the signed-registry tooling):

1. Branch off the lib's `main` (`feat/gl-2d-substrate`); make the change + version bump
   (`graphics/loft.toml` 0.1.1 → 0.2.0); lib gate green (`loft test` in `graphics/` — 67).
2. Push → PR → CI green → `gh pr merge --squash --delete-branch` (lands on `main`).
3. Tag the merged commit **`graphics-v0.2.0`** (the monorepo's per-package tag form) + push.
4. `loft package` → deterministic tarball + sha256 + size. ⚠️ its index-entry HINT derives
   the WRONG repo URL (`loft-graphics`); use **`loft publish`**'s entry instead — it derives
   the correct `loft-libs-graphics` + tag URL (a `loft package` bug worth filing).
5. `gh release create graphics-v0.2.0 graphics-0.2.0.tar.gz -R loft-lang/loft-libs-graphics`.
6. `loft publish` — verifies the live release exists + emits the correct index entry.
7. **Add the index entry, then COMMIT IT, then sign.** Clone `loft-lang/registry`; insert the
   0.2.0 block under `packages.graphics.versions` (textual insert — preserve formatting for a
   clean diff); **`git commit` that `index.json` edit FIRST.**
   > ⚠️ **The gotcha that bit us (cost a broken publish — re-verify against it).**
   > `scripts/registry-sign.sh` commits **only `index.json.sig`**, *not* your `index.json`
   > change. If the entry is still UNCOMMITTED when you sign, the push carries a *signature over
   > content that isn't in the committed index* → the index and its sig **mismatch** (a #371-aware
   > consumer gets `signature INVALID — refusing to load`) **and the version never publishes**.
   > It fails SILENTLY — the sign + push both "succeed". So: commit the entry first; after pushing,
   > always re-verify `origin/main` (below). [Worth a loft issue: registry-sign.sh should commit
   > the index edit too, or refuse when `index.json` is dirty.]
8. **Sign + verify.** `scripts/registry-sign.sh --registry-dir <clone> --no-push --yes` downloads
   the tarball, **re-checks sha256 (the integrity gate)**, and signs `index.json.sig` with
   `~/.loft/trust-root/registry-signing-key.bin` (= **K_laptop**, one of the three embedded
   trust-root keys in loft `src/registry_keys.rs` — sign with a NON-embedded key and consumers
   reject it). Ed25519 signing is **deterministic**, so re-signing identical content is a no-op.
   Verify before pushing: `loft-keygen verify --in index.json --sig index.json.sig --pub <64-hex>`
   → `signature valid`.
9. **Push (maintainer-only) + re-verify.** `git push origin HEAD:main` to `loft-lang/registry` —
   the agent's push to shared trust infra is (correctly) blocked by the safety classifier, so a
   human runs that one line. Then **re-verify `origin/main` end-to-end**: `git show
   origin/main:index.json` lists the new version, AND `loft-keygen verify` of
   `origin/main:index.json` against `origin/main:index.json.sig` says valid. (This is the check
   that catches the step-7 gotcha — we hit it, the first push published the sig without the entry.)
10. **Consumer switch:** crawler `loft.toml` `graphics = ">=0.2"`, then **`loft update graphics`**
   — NOT `loft install`. `loft install` honours an existing satisfying lock (0.2.0 satisfies
   `>=0.2`, so it won't move); `loft update <pkg>` bumps to the newest matching version, verifies
   the signature, and rewrites `loft.lock`. It also writes the loft#362 `.loft/api/<dep>.api`
   stubs — **commit them** (a `.gitignore` `!**/.loft/api/` exception keeps the rest of `.loft/`
   ignored) so the out-of-`~/.loft` API surface is visible in-tree. The #322 cache never bites
   here because a VERSION bump re-keys the cache — the win over the dev `--lib` route, and it
   **collapses the plan #7 L0 node to a version bump**. (0.2.1 consumed this way 2026-06-14,
   gate green, commit `c01faed`; the signed-install path worked with no CDN transient this time.)

Side lessons:
- **CI gap (filed):** the chunk's `library-ci.yml` matrix only tested the pure-loft packages —
  native `graphics`/`imaging` were uncovered, so 0.2.0 was validated only locally. Adding them
  (PR #7) surfaced a deeper skew: the CI clones the `jjstwerff/loft` fork's main, which is behind
  `loft-lang/loft`, so the native crates don't build there — fix the CI loft source, then they go green.
- **`loft package` URL bug:** its index-entry hint derives `loft-graphics` (wrong); `loft publish`
  derives the correct `loft-libs-graphics` URL — always take the entry from `loft publish`.

## Extraction Definition of Done (per package)

1. The package builds standalone (`loft test` in its folder, with at least a smoke test).
2. crawler consumes it (dev: the `--lib` dir; released: the registry version) and the
   duplicated `src/` module is **deleted**.
3. `make test` green (the full gate — 39 tests today) + `make check` clean against the dep.
4. Globally-unique pub names preferred (style — the native dup-symbol bug that
   required this is fixed).
5. Style rule honoured (the one live bug): no capture-append-reassign on struct
   fields (#320 — direct append or index-writes).
6. Docs: the package README states its convention/contract; crawler's CLAUDE.md "Where
   things are" updated.

**Environment caveat (not a blocker) — NARROWED 2026-06-14 by loft @PLN21 (#370).** E0514
bites **only AUTO-compiled native** (a pure-loft lib loft compiles to a cdylib that
`extern crate loft`s — rlib-linked, so SVH/rustc-locked): with the installed `libloft.rlib`
at rustc-1.95 vs active 1.96 it fails locally and falls back to the interpreter — correct,
just unoptimized. **HAND-WRITTEN native libs are rustc-INDEPENDENT** (they link loft-ffi's
`#[repr(C)]` C-ABI, not `libloft.rlib`), so `graphics`/`random`/`gridmesh` compile and load
fine across the mismatch — VERIFIED: crawler's sibling `graphics/native` builds clean.
The real fix is @PLN21's **prebuilt `prebuilt/<triple>/` cdylibs** (loft-ffi-fingerprinted,
no rustc to *use* a lib) once the registry publishes them; the `cargo +1.96.0` rebuild /
1.95 pin only matters for the auto-native tier in the meantime. See "Library-handling
state (loft, 2026-06-14)" below.

---

## Tier 1 — implementable NOW

### 1. `hexgrid` — the canonical hex geometry (+ the 12-orientation square basis)

The flagship: `hexgeo` implements the **moros convention** (pointy-top, odd-r,
`L = √3`) that moros itself only documents; extracting makes the convention *executable*
in one shared place. `gridgeo` belongs with it — its whole purpose is the 90°-square
local basis FOR objects placed on the hex world (12 × 30° orientations matching the hex
lattice), meaningless apart from it. Both are struct-free, import-free, game-free.

- [x] **HOMED in `loft-lang/loft-libs-world`** (PR #1, merged, CI green) as package
      **`hex_grid`** — the GEOMETRY axis of the `hex_*` family, beside `hex_world`
      (storage) and the pending `hex_walls`/`hex_terrain`. LESSON: a `loft-libs-game`
      repo already existed with a different charter (runtime services, lavition) —
      **check LAVITION.md § Library model (the 6-chunk topology) before homing a
      package**. Bonus: fixed hex_world's red CI on main (test temp paths doubled
      `tests/` — relative paths resolve from the test file's dir under `loft test`).
- [x] Package `hexgrid` (v0.1.0): hexgeo + gridgeo merged into one module; the colliding
      trio renamed DESCRIPTIVELY per basis (`hex_`/`cell_` `neighbor_dir`, `edge_corners`,
      `canon_edge` — the technical layer keeps technical names; a friendlier drawing
      abstraction can sit above later); `GRID_SIZE`/`GRID_LEN` now pub. (LOS stays in sim
      until the Tier-2 parameterization — it takes a Sim today.)
- [x] 10 package tests under `--deny-warnings` (round-trips, metric, neighbor ring +
      inverse, shared-edge canonicalization for BOTH bases, corner circumradius).
- [x] crawler switched: Makefile LIB_DEPS (`--lib ../loft-libs-world/`) + `use hex_grid;`
      across 23 files, six renamed call sites, `src/hexgeo.loft` + `src/gridgeo.loft`
      DELETED (the no-drift rule).
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

crawler's copy gained `Background transparent` (+ exercised `flat=` foreshortening and
`grad=` fills hard), and now the **array primitives**: `Petals` (radial flower head) and
`Fronds` (a linear array of tapered strokes rooted along a spine — veins/barbs/fur/grass —
**non-uniform + construction-hiding by default**, mirror-symmetric, with a **fractal `depth`**
that re-applies the array to each frond, i.e. real leaf venation). Both designs are pinned by
falsification-probe blueprints (`tools/{petal,fronds}_blueprint.py`, 12/12 + 10/10).
rotation/atlas still named next. The skill's `sketch/draw.py` is the library layer.

- [ ] Diff crawler's `tools/draw.py` vs the skill's `sketch/draw.py`; port the extensions
      upstream — `Background transparent`, **`Petals`, `Fronds` (+ the `_hash01`/`_lowfreq`
      deterministic noise and the blueprints)** — (the skill's own examples must still render).
- [ ] Note in the skill's docs the techniques proven here (rim-ring readability, discrete
      blotches, menace-via-posture, the join discipline; **arrays: "never a uniform row" —
      trend+jitter — and "hide the construction" — clumping/aperiodic/occlusion/fray/wash**)
      — doc, not code. (Already drafted in the skill's `references/2d.md` Earned 2D rules.)
- [ ] crawler keeps its copy only if it still carries unported experiments; else delete and
      call the skill's.

**Missing capability — the rough brush, the spray-paint tool & the grime wash (paint that INTERACTS
with the canvas; for fur/skin/water/smoke + weathered figures/machines, crawler's CURRENT sprites).** Today every `draw.py` mark deposits
OPAQUELY over whatever is under it — a `stroke` ribbon overwrites, `grad=`/`radial=` are per-shape
masks. That hard, self-contained deposition is the mechanism behind the recurring "fur lives
*inside* a clean outline" problem (`assets/sprites/ref/README.md`) and the skin uncanny-valley
ceiling (the draw skill's failure-taxonomy #5 + its "grow the tool first — colored strokes for hair
*before* you can texture a beard"). Three techniques draw.py LACKS — an old-masters brush (mixes
with the wet canvas), a *modern* spray (translucent soft falloff), and a grime wash (depth-pooled
weathering) — close it:

- [ ] **Rough brush — the 16th-c. hair / fur stroke (the HARDER of the two to mimic).** A coarse,
      stiff, SPLIT-bristle brush (the worn hog-bristle the Renaissance "rough manner" painters —
      late Titian — dragged for hair, beard, fur): its splayed bristles lay MULTIPLE broken parallel
      streaks in one pass and, pulled through the *not-yet-dry* paint beneath, pick up and smear that
      pigment — leaving the streaky value/colour lines that read as individual hairs *within* a mass.
      The stroke's **END is also ragged** — the bristle channels run out at slightly different
      lengths, so the terminus frays into separate tapering tips, and that raggedness is a big part
      of what sells the read of hair *bundles* (cf. `Fronds`' `fray=` and the README "fray the
      boundaries" rule). The best practitioners also **double-load** the brush — one side of the
      bristle bundle a slightly different colour/value than the other — so a single drag lays light
      on one side and shadow on the other: **instant form/shadow on the hair/fur in one stroke**.
      Exactly the interior texture our smooth-outline fur is missing (the README
      "texture lives in the silhouette edge + value gradient, not strokes floating inside a smooth
      outline" lesson, made a TOOL, not just a discipline). **You can't fake this from the look** — a
      faithful routine has to MODEL how the brush physically works (split channels + wet-paint pickup
      + uneven-length ragged tips); blueprint the mechanism in a cheap Python probe FIRST (the
      engineering-rigor / design-protocol way), then port. Needs a multi-channel (split-bristle)
      footprint + wet-paint pickup/drag + frayed (uneven-length) stroke ENDS + a transverse
      (across-the-width) value/colour gradient on the footprint (the double-load — instant hair
      shadow). (`Fronds` *places*
      single strokes; this makes ONE drag deposit a grown, mixed hair texture.) **Concrete evidence
      (the live diagnosis):** crawler's recent animal fur — the spine-ridge + flank striations laid
      as opaque `Fronds`/lines — reads as a *strange web on the back*; the line PLACEMENT is right,
      but enumerated opaque strokes simply can't read as fur, whereas the SAME lines laid by a rough
      brush would. So it's failure-taxonomy #2 (tool-can't-express-it), NOT #1 (drew-it-wrong) —
      stop re-placing the lines (symptom-chasing the web); the fix is the brush.
- [ ] **Spray-paint (airbrush) tool — skin / water / smoke.** A *modern* tool, NOT an old-masters
      one: the airbrush is a relatively recent invention, today the workhorse for cosplay,
      clothing/textile, and character painting — and the established answer to a problem the old
      masters never solved by hand: **skin that goes flat, unicolor and unnatural**. *Their* method
      was to mix a precise colour to match each skin region, then lay it on with a perfectly EVEN
      ("egal"/egaal) brush, region by region — matching one patch could take DAYS, and those even
      flat patches are *why* the skin reads unicolor. The airbrush sidesteps all of it: you dial the
      POWER and build the gradient up in light passes, so a natural skin transition is *easy* instead
      of days of colour-matching. Three properties draw.py can't express: (1) **translucent
      layering** — lower layers painted first, the spray TINTS rather than fully recolouring them, so
      the underlayer shows through and mixes optically (form modelled *without flattening the
      underpainting*; the "value first" build); (2) **perpendicular falloff** — intensity highest
      along the stroke's CENTRELINE, tapering to NOTHING toward its outer edges (the soft
      airbrush-cone cross-section), unlike today's `@`-taper which varies width along the stroke's
      LENGTH, never across it; and (3) **adjustable power / flow** — deposition strength is a tunable
      dial built up over light passes, NOT a fixed stamp, so the gradient is tuned by eye instead of
      pre-mixing an exact colour (this is the property that makes natural skin *easy*). In draw.py
      terms power maps to a **higher per-pass ALPHA** (stronger tint) and probably a **wider line**.
      Together: soft translucent tonal gradients that build natural skin (the uncanny-ceiling fix),
      overlapping water ripples/highlights that tint without obscuring, and soft-edged smoke/haze.
      **Achievable NOW (approximation) vs. the real mechanism — the two-pass brush.** A *spray* shape
      alone can be approximated with the CURRENT primitives: a soft circle stepped along a line, or a
      radial-falloff area filled inside a form — that gets you the cone footprint without new code. But
      a real PAINT brush (this airbrush, and the rough brush above) needs a **second pass**, because the
      footprint isn't a fixed primitive — it's an arbitrary authored shape that must be STAMPED along
      the stroke: **pass 1 — draw what the brush IS** (its footprint as a small image: shape + colours +
      per-pixel alpha channel — e.g. the airbrush's centre-bright / edge-to-zero cone, or the split-
      bristle's multi-channel streaks); **pass 2 — the line pass draws THAT shape onto the canvas**,
      stamping/dragging the pass-1 footprint along the stroke and accumulating its alpha into the
      target. So "draw a line" becomes "drag this brush-shape along a line" — the footprint is data, not
      a hardcoded mask, which is exactly what lets one op carry the rich per-stroke parameters below.
      **Skin specifically is built in SEVERAL translucent passes of DIFFERENT colours, never one** —
      e.g. a light grey, then red, then yellow, then pink (laid in lines or areas), each a thin tint
      that shows through the others; the EARLIER passes read as the deeper skin layers, the LATER
      passes as the upper ones, and that optical stack is what makes skin look alive (one flat colour
      reads dead). This is why translucent layering (property 1) is load-bearing here — the passes
      MUST show through each other. Needs per-pixel alpha accumulation + a width-wise (perpendicular)
      intensity profile + a settable flow/strength (power = per-pass alpha, likely also stroke
      width).
- [ ] **Grime wash + wipe-back (weathering — realism on figures / machines).** Not a brush — the
      realism FINISH: leave DIRT on the top surface, pooled MORE in the deeper/recessed spots. Method
      (the model-maker's / miniature-painter's shading wash): flood a thin, very watery dark tint
      (brown / dark-green / grey) over the area with a cloth, let it DRY in the lower areas (it pools
      and sets in the recesses), then WIPE it back with a slightly-wet sponge — the raised/high layers
      clean up almost totally, the deep spots stay quite dark. Net effect: depth-driven darkening that
      reads as accumulated grime AND enhances the 3D form (a cavity / ambient-occlusion shade you get
      *for free* from the dirt) — the pass that makes figures, armour, machines, props read as real
      and used rather than clean-CG. For draw.py it needs a notion of surface DEPTH/cavity (where the
      wash collects) — either the existing value (darker = deeper) or an explicit recess map — then a
      translucent dark tint scaled by depth + a wipe that clears the raised areas. Distinct from the
      airbrush (that builds the base form/skin; this *dirties the finished surface* to sell realism).
      **Why it works:** almost everything gets dirty in real use, so grime pooled in the recesses
      reads as AUTHENTIC and used while a spotless surface reads as artificial CG — and the wash
      throws ACCENTS (local dark punctuation / contrast) across the result, lifting it out of flatness.
      **This is also why CEL-SHADING reads as natural rather than artificial:** its dark lines land on
      the SAME recesses, creases and under-edges where dirt and shadow accumulate on a real figure —
      a partial match to everyday reality that *licenses* the stylization. So the rule generalises
      past a literal wash: **put the darks where dirt/shadow would collect** (the recesses) and even a
      hard-edged, stylised sprite reads right — directly crawler's case (our sprites are stylised, not
      photoreal). The grime wash and the cel-shade line are the same move at different fidelities.

**The two brushes exist to produce the ILLUSION of detail in ONE gesture, never to enumerate it.** The old
masters almost never drew individual hairs, or leaf-by-leaf detail on plants/bushes — a few clever
strokes (the ragged split-bristle drag, the soft spray) IMPLY the hundreds. That is the whole point
of these tools, and the standing rule: *imply* detail with the brush, don't draw it strand-by-strand
or leaf-by-leaf (the draw skill's "minimal ≠ symbolic" + "clarity has an optimum", made mechanical —
the brush is what makes implied detail cheap, where enumerating it is both expensive and reads worse).

**Design shape — a rich per-stroke routine, far fewer strokes.** This concentrates the complexity in
ONE op: a single drawn "line" carries many parameters — thickness, direction, multiple colours (the
double-load), brush/footprint form, fray, wetness/flow, power. That op is complex to write, but it's
the right trade — each loaded stroke does the work of dozens of thin uniform lines, so a finished
sprite needs FAR fewer marks (the master's economy: a few expressive strokes, not many timid ones).
Built once and extracted to the library, then every sprite spends fewer, richer marks — and "every
mark earns its place" becomes "make each mark earn MORE".

All three are failure-taxonomy #2 ("tool-can't-express-it → grow the tool"): record now, build when a
sprite needs them; until then *withhold* (don't fake hair with enumerated opaque strands). Ordered
BEFORE the decorative block below — these serve crawler's current mob/skin/water/smoke + weathered
figure/machine sprites; that block is for later games. (Pointer memory: `draw-tool-wet-brushes`.)

**Future capability — complex decorative patterns (library-tier, for LATER games not crawler;
a "nice addition").** The user wants the tool to eventually do **decorative surface patterns**
— wall/wallpaper damask, curtain/cloth prints, engraved/inlaid motifs on cutlery and objects.
It stacks on the array/symmetry/fractal foundation above; build order when a later game needs it:

- [ ] **Symbol capture + affine `place`** — define a motif once in local coords, then
      translate/rotate/scale/**skew** it. (Also unlocks placing a broad leaf on a branch.)
      The tool is friendly to this — every op is a point list, like `petal_polys`/`fronds`
      already transform internally; the fiddly part is transforming the PAINT specs too
      (gradient axis, radial centre, stroke width).
- [ ] **Grid/lattice array + wallpaper-group tiling** — the 2D generalization of `Fronds`'
      1D array, with per-tile offset (brick/half-drop), mirror, rotate so the repeat isn't a
      flat stamp.
- [ ] **Clip-to-region** — confine the pattern to the surface shape (drape, panel, blade);
      the architectural one (a mask stack across ops — draw.py masks only per-shape today).
- [ ] **Surface-conform / warp** — advanced: a curtain pattern follows the FOLDS, cutlery the
      curved/perspective surface (a displacement field or perspective place).

**Key inversion vs. foliage:** decorative man-made patterns WANT the uniform special case
(`jitter=field=fray=0`, crisp); the "not a flat stamp" realism comes from the SURFACE (folds,
perspective, lighting, wear), NOT from jitter on the marks. The motif's own internals can still
use the shipped `mirror` + fractal `depth`. (Roadmap also held in the auto-memory
`draw-tool-decorative-patterns`.)

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

### 5. `hex_terrain` — the overland terrain layer (NEW, landed 2026-06-11)

The OVERLAND.md blueprint ported as the hex_* family's terrain axis
(loft-libs-world PR #4, merged, CI green): overland cells + priority-flood
hydrology + neighbor-relief verticality + edge-bit/control-point/fractal rivers
with shoreline attach + additive slope-shaped carving + per-point sampling.
Pure functions; the window-independence invariant tested by rebuild-and-compare.
LESSONS (the --deny-warnings sweep): `??` binds TIGHTER than `/` — defend
divisions as `(a / b) ?? f`; struct-field index WRITES need the alias idiom
(`v = s.field; if i < len(v) { v[i] = x; }` — a guard on `len(s.field)` is not
recognized); compound guards with `||`/`??` subexpressions aren't recognized.
crawler consumes when the wilderness lands (blocks sample `terrain_sample`).

### 6. GPU 2D primitives → `graphics` (the showcase flow-back, RENDER.md R7/R8)

crawler's showcase renderer (RENDER.md, doctrine 2026-06-12) is the consumer pressure
that drives the `graphics` lib's 2D API to its modern-GPU form. Two layers, in order:

**(a) The raw substrate** — small `gl_*` additions the instanced tier needs:

- [ ] `gl_draw_instanced(vao, verts, instances)` + per-instance attributes (divisor)
      on `gl_upload_vertices`-style instance buffers.
- [ ] `gl_update_vertices(vao, data)` (buffer sub-data / orphaning) — per-frame dynamic
      buffers without the create+delete churn.
- [ ] `gl_set_uniform_vec2` / `gl_set_uniform_vec4` (only int/float/vec3/mat4 exist).
- [ ] An EBO upload entry (`gl_draw_elements` exists with no way to upload indices).
- [ ] Texture sampler control on upload (linear/nearest, mipmap generation) — RGBA-
      quality sprite minification + atlas filtering.
- [ ] Texture sub-region upload (`glTexSubImage2D`-style) — incremental auto-atlas
      packing without re-uploading the whole page.
- [ ] `gl_scissor(x, y, w, h)` — partial in-layer damage redraw (RENDER.md frame-reuse
      Tier 3).
- [x] ~~`gl_wait_events_timeout(ms)`~~ — RESOLVED by loft#343's `run_local`
      (plan #6 K1, 2026-06-12): the games kernel owns the loop and idles
      between drift-free ticks, closing the idle busy-spin without a graphics-lib
      change. Kept here as the record of the gap's route.

**(b) Painter2D v2 — a Cairo-class canvas + sprite API, GPU behind the curtain**
(the stated target, 2026-06-12: Cairo-like drawing primitives + 2D sprites with full
RGBA-quality compositing, the GPU used as efficiently as possible behind them — the
NanoVG-class architecture; full spec: RENDER.md → "The API layer"):

- [ ] The canvas surface: stateful context (`save`/`restore` transform+state stack,
      `translate`/`rotate`/`scale`, scissor), path verbs (`begin_path` ·
      `move_to`/`line_to`/`bezier_to`/`arc`/`rect`/`rounded_rect`/`circle` ·
      `close_path`) with `fill(paint)`/`stroke(paint, width)`, solid-RGBA + gradient
      paints. Strokes: join styles (miter/bevel/round) + cap styles (butt/round/
      square) — constructed 24-dir walls need sharp miters; per-point width (taper —
      rivers scale with flow); arc-length UV baked into stroke geometry (dashes, road
      texture, river flow animation). See RENDER.md → "Fit check — the 24-direction
      world".
- [ ] Batched backend: calls append to per-shader streams; **merge adjacent
      state-compatible calls, never reorder** (2D alpha compositing is order-
      dependent; the shared atlas + SDF ubershader make nearly all consecutive calls
      compatible, so adjacency-merge alone yields a handful of draws). No per-call
      CPU rasterization.
- [ ] Frame-stats introspection (draw count, batch breaks + reasons, atlas occupancy,
      tessellation-cache hit rate) — the automatic behaviors must be debuggable when
      they degrade.
- [ ] Two-tier shapes: common cases (line/circle/ring/rect/rounded-rect) are SDF fast
      paths (one quad shader, per-instance params, analytic AA — what crawler's wall
      stipple becomes); arbitrary paths flatten + tessellate CPU-side ONCE, cached by
      (path identity, scale bucket), redrawn as cached triangles.
- [ ] Sprite layer with RGBA quality: premultiplied-alpha compositing
      (`BLEND_ONE`/`ONE_MINUS_SRC_ALPHA` — constants already exist), 1px atlas padding
      against linear-filter bleed, mipmaps when minified (needs the sampler-control
      gap in (a)), rotated/scaled/tinted draw verbs.
- [ ] **Automatic atlasing — no programmer direction**: `load_image(path)` → handle;
      the painter skyline-packs images into its own ~2048² pages at load time
      (off-frame — first-draw packing only as the glyph fallback; premultiply + pad +
      extrude at insert), instance records carry the UV rect —
      one draw per page with no manual arrangement; glyphs share the pages. Heuristics,
      not API: oversized images bypass to own textures, full pages chain, dynamic
      entries evict LRU. Needs the sub-region upload gap in (a).
- [ ] Frame reuse (RENDER.md → "Frame reuse"): the idle skip (scene version unchanged →
      no render, no swap — zero gaps); per-layer caches as an API choice
      (`make_layer` / draw-into-layer / `invalidate` / `draw_layer(layer, mvp)` — the
      same verbs targeted at an owned FBO texture, never a global mode); scissored
      partial redraw inside a layer behind the `gl_scissor` gap in (a).
- [ ] Recording: the same verbs captured into a batch handle
      (`record … → draw_batch(batch, mvp)`) — static content (a level's walls) records
      once, replays per frame under the camera matrix. Display-list model: static
      performance without a second API.
- [ ] crawler adopts piecewise, proving each: R5's capsule-SDF wall shader flows back
      as the lib's stroke shader; R8's sprite batch becomes the painter's internal
      batcher; `draw_texture_rot` (today reaching into painter internals) is subsumed
      by the rotated sprite verb. The general path layer is lib-side scope (crawler
      itself needs lines/circles/rects/sprites/text) — it lands with its own tests +
      a vector-graphics demo as the second consumer.

**(b-map) Port EVERY draw.py primitive onto a BARE `vector<integer>` pixel buffer (native-
safe), uploaded via `graphics::gl_upload_canvas`.** Landed in `src/sprite_draw.loft` +
`src/sprite_drawtest.loft` (gate **[13/14] SPRITE OK**, passes BOTH interpreted and native).

> **NATIVE GOTCHA (pinned 2026-06-25, the load-bearing reason this is bare-buffer, not
> `graphics::Canvas`).** graphics' `Canvas` mutation methods (`set_pixel`/`fill_rect`/`hline`/
> `fill_circle` — all using the `d = self.data; d[i] = color` capture-then-index-write idiom)
> **work when graphics runs INTERPRETED but silently NO-OP when graphics is loaded as a native
> cdylib** (the default `--native` mode the game runs in); `save_png` additionally panics with
> "loft_save_png has no marshal bridge". Verified via `canvas()→fill_rect→get_pixel`: correct
> `--interpret`, unchanged pixel `--native` (exit 0, no error). This also silently breaks
> `view.loft`'s disc/panel texture baking under native — a separate fix needed there. Root
> cause is loft-side (the cdylib struct/vector marshalling, not graphics' code, which is
> correct interpreted) — FILE upstream with the in-crawler recipe. **Workaround = the design
> below:** a bare `vector<integer>` argument is passed by REFERENCE and mutates correctly in
> BOTH modes (verified), and `graphics::rgba/blend/color_*` are scalar-in/out so they're
> native-safe; only the one-shot `gl_upload_canvas(buf, w, h)` touches the cdylib, passing data
> IN (no mutate-back). So sprite_draw owns its buffer; graphics::Canvas is used for nothing.

The earlier plan to build on `graphics::Canvas` directly is superseded by the bare buffer for
exactly this reason. Reference (what the shipped Canvas API offered): graphics-0.2.1
`canvas(w,h,fill)` → a `{width,height,data}` RGBA
(`0xAARRGGBB`) pixel buffer with `set_pixel`/`get_pixel`, `blend`/`blend_pixel` src-over
compositing, `fill_rect`/`hline`/`vline`/`draw_rect`, `draw_line`/`draw_aa_line`,
`draw_circle`/`fill_circle`/`draw_ellipse`/`fill_ellipse`, `draw_bezier`, **`fill_triangle`**,
`draw_text`, `save_png`). **In-world drawing on textures already works through this path** and
crawler already uses it: `view.loft` builds the token disc by `canvas(64,64,0)` →
`fill_circle` → `gl_upload_canvas(c.data,64,64)` → a GPU texture (and the panel the same way);
`ovshot.loft` paints the whole world map with `set_pixel`/`fill_circle`/`fill_rect` then
`save_png`. So the surface is decided: **a `graphics::Canvas`, finished either to a runtime
texture (`gl_upload_canvas` → `draw_texture_at`) or to a PNG (`save_png`)** — same buffer,
two sinks. The job is to make that canvas do everything `tools/draw.py` does.

The whole `draw.py` program collapses to THREE rasterization ops over generated point sets —
`grad` (full-surface gradient), `fill` (closed polygon; solid/linear/radial), `stroke`
(polyline; constant or per-point width) — plus a supersample+downscale AA pass and an
optional transparent base (the op loop in `render()`). Everything else is pure-geometry
*front-end* compiling to those three. Mapping each onto the real Canvas:

- **`grad` background** → loop rows writing per-row colour with `hline` (ovshot already does
  the per-pixel version). FREE today.
- **`fill` solid** → needs `fill_polygon(pts, color)`. `fill_triangle` exists but draw.py
  polygons (smoothed outlines, petals) are CONCAVE → add a **scanline** polygon fill (active
  edges per row → `hline` spans), the load-bearing new method.
- **`fill` linear/radial** → `fill_polygon_gradient`: the SAME scanline, but per span-pixel
  compute the gradient `t` with `_make_gradient`'s exact formula and `set_pixel`/`blend_pixel`.
  This SUBSUMES draw.py's small-image-resize + mask-paste hack (no 100×100 resize).
- **`stroke` constant width** → w≈1 is `draw_aa_line` (exists); thick is the band below.
- **`stroke` variable width (`_ribbon`)** → `stroke_path(pts, widths, color)`: port `_ribbon`'s
  half-width normal-offset (left + reversed-right → one band) and hand it to `fill_polygon`.
- **`_smooth_pts` Catmull-Rom**, `circle_pts`, `petal_polys`, `fronds` (+ `_hash01`/`_lowfreq`
  + fractal recursion), `Poly`/`Line` point lists → **pure-loft geometry**, port VERBATIM
  (they only produce coordinates; Petals/Fronds are already half-ported into the skill, §3).
- **Supersample AA** → draw.py renders ×S=3 then LANCZOS-downscales. Match it by drawing onto
  an S× Canvas then a new `downscale(factor)` (box-filter over `data`) before upload/save.
- **Transparent base** → already works: `canvas(w,h,0)` (alpha-0 fill) + `blend_pixel`
  compositing IS the re-compositable RGBA sprite. Replay ops in authored order (alpha is
  order-dependent).

**The new Canvas methods this needs (the whole build list): `fill_polygon` (scanline) ✅ ·
`fill_polygon_gradient` · `stroke_path` (ribbon) · `downscale` ✅** — plus the pure-loft geometry
helpers (`smooth_pts`/`circle_pts`/`petal_polys`/`fronds`), which live crawler-side in
`src/sprite_draw.loft` first and extract to the lib once proven. Everything else already
ships. **No GPU/FBO/shader work is required for this route** — that is the Painter2D v2 (b)
upgrade for batching/SDF-AA later, not a gate.

**The verifiable invariant + concrete steps (design-protocol Step 1 = a concrete plotted
end-result, then pin each step).** Invariant: **the loft-Canvas render of a `.draw` program is
STRUCTURALLY identical to draw.py's PNG of the same program — interior pixels exact, parity
judged on MEAN (≪1).** Note (pinned by probe, Steps 1–2/7): a tight *max* gate vs draw.py's
PNG is NOT achievable, because draw.py resolves AA with **LANCZOS** while the Canvas resolves
with a **box** filter — two valid kernels that differ by ~max-14 on *identical* pixels, plus a
sub-pixel boundary difference between the even-odd scanline and PIL's polygon fill. So:
**parity vs draw.py = mean-based** (the dev probe), and the committed gate uses **deterministic
`get_pixel` assertions on the hard-edged fill** (exact, no PIL) — a frozen *loft* golden is the
route to a max gate if one is ever wanted. Build bottom-up, each step its own headless test:

1. ✅ **Surface parity** (no new code): a loft test draws solid `fill_rect`s, `save_png`, diff
   vs draw.py's PNG of the equivalent `.draw`. DONE — colour packing, y-orientation and
   coordinate→pixel mapping agree (interior pixel-exact). **Calibration found:** hard-edged
   Canvas vs draw.py's supersample+LANCZOS differ only on a 1px AA rim — **max=43 / mean=0.51**
   on 120×80. ⇒ the *max-16* gate is reachable only AFTER step 7 (downscale); earlier steps
   judge parity on **mean**.
2. ✅ **`fill_polygon`** (even-odd scanline; `src/sprite_draw.loft`) → verified on a CONCAVE
   arrow: interior pixel-exact, **0 interior holes, 0 over-fill** (characterized), parity
   **max=82 / mean=0.40** (pure AA rim). Permanent headless test `src/sprite_drawtest.loft`
   (`get_pixel` equality, no PIL) wired into `make test` as **[13/14] SPRITE OK**; the draw.py
   golden-diff harness is a dev probe (scratchpad), kept out of the gate.
3. **`smooth_pts`** (Catmull-Rom) → verify a `~`-flagged smoothed `Poly` matches.
4. **`stroke_path`** ribbon → verify a tapered `Line`/`Poly` stroke matches `_ribbon`.
5. **`fill_polygon_gradient`** → verify a `radial=`/`grad=` circle matches `_make_gradient`.
6. **`circle_pts`/`petal_polys`/`fronds`** → verify a `Petals` and a `Fronds` sprite match.
7. ✅ **`downscale`** (box-filter resolve; `src/sprite_draw.loft`) → render ×S then collapse
   S×S blocks. VERIFIED **byte-identical to PIL's BOX filter (max=1, mean=0.005)**; box-vs-
   LANCZOS on identical pixels is max-14/mean-0.19 (the irreducible kernel gap). Supersampled
   arrow parity vs the draw.py golden: **mean=0.33** (max≈47 = scanline-vs-PIL boundary + kernel,
   not error — confirmed flat across S=3→8). Deterministic block-average assertion in the gate.
8. **In-world seam**: `gl_upload_canvas(c.data,w,h)` the result and draw it with
   `draw_texture_at`; gate via `make probe` (the Xvfb pixel test). Then flip ONE monster's
   `view.loft` by-name loader from "load `<key>.png` via `gl_load_texture`" to "run
   `<key>.draw` → Canvas → `gl_upload_canvas`" — proving runtime/procedural sprite generation
   (recolour, per-instance variation) with no PNG round-trip. The by-name resolver is the
   single integration seam; the PNG path stays as fallback.

- [ ] **The two-pass wet brush (§3 airbrush/rough-brush spec) on THIS canvas.** Pass 1 —
      render the brush footprint (shape + colour + per-pixel alpha) once into a small
      `Canvas`. Pass 2 — the "line pass" walks the stroke path and stamps that footprint
      along it with `blend_pixel` (arc-length spacing so density is speed-independent). That
      is "blit a small canvas repeatedly along a path" — `blend_pixel` already gives the
      src-over accumulation, so the airbrush cone and split-bristle drag are DATA (the
      footprint canvas), not engine code; the grime wash is the same stamp modulated by a
      depth/recess channel. **The ONE genuinely new capability** is the rough brush's
      wet-paint PICKUP — it smears pigment already laid down, so the stamp must READ the
      target under the footprint (`get_pixel`), mix, and write back: a read-modify-write, not
      pure deposition. `get_pixel` already exists, so even this is expressible on the current
      Canvas — flag it as the only non-deposit-only op.

**(c) The library landing ladder** (evaluated 2026-06-12 — what "fully reusable"
adds beyond the crawler proofs: de-crawlering, a non-crawler consumer, lib-side
testability, publication):

- [ ] **L0** (S): clone `loft-libs-graphics` sibling + crawler dev `--lib` wiring
      (this box only has the registry copy).
- [ ] **L1** (M, = plan #7 P5): the `gl_*` substrate lands IN `graphics` (native
      Rust FFI — no home choice) + one GL smoke per entry; releasable as 0.2.0 alone.
- [ ] **L2** (S): painter v2 = a NEW pure-loft package (`canvas`) in the graphics
      chunk repo, layered ON `graphics` (graphics stays the lean binding; the canvas
      iterates without native rebuilds — the mesh3d layering rationale). README API
      contract first, from RENDER.md → "The API layer".
- [ ] **L3** (M per piece): port each crawler-proven piece as it's proven (stroke+SDF
      after P3, batcher+frame-stats after P7/P8, atlas after P7, recording/layers
      after P9). Each port = a **de-crawlering pass** (stride-10/visUV/FOV-dimming
      are CRAWLER policy — the lib carries a generic aux channel; the visUV trick
      becomes a consumer pattern) + lib tests + crawler consumes via `--lib` + the
      in-crawler copy DELETED + gate green. Generalize only what the demo consumer
      exercises — the generalization pass is where scope creep enters.
- [ ] **L4** (L): the generic tier (paths/fills/gradients/clip + join/cap/taper/
      arc-UV) built against the vector-graphics demo as the forcing consumer; the
      probe-harness pattern ported into the lib's test culture (it already has
      `tests/gold/`). Keep the three-layer testability: pure-data core headless,
      thin GL shell, Xvfb pixel probes.
- [ ] **L5** (S): docs migration — RENDER.md's "API layer" section MOVES to the
      package README when the canvas ships (pointer left behind, incoming links
      rewritten — the plan-close rule).
- [ ] **L6** (S per release): the five-step registry flow; crawler switches off the
      dev `--lib`. Cadence: graphics 0.2.0 after L1; canvas 0.1.0 after L3's first
      two pieces.
- [ ] **L7** (external): a second REAL consumer (moros tooling / a loft UI app / the
      draw skill's renderer) — the API stays pre-1.0 until one exists; "fully
      reusable" is a claim a consumer makes, not the author. Survival-guide rules
      apply lib-side too (#339 no thin pub wrappers, #320 idiom, no vector<text>
      literals in big fns); E0514 note in the README (interpreter fallback until the
      toolchain refresh).

### 7. The game-starter template — executable "how to build a game" docs

Decision (2026-06-12): the setup guide for OTHERS lives org-side as a runnable
template repo (**loft-lang/game-starter**), not as prose in crawler or the loft
internals. A minimal clone-and-run game — window on the kernel loop
(`run_local`), one character bundle + the scanner, one sprite, one world routine,
the test-gate + probe-harness patterns in miniature — with the guide as its
README. It is ALSO the §6 ladder's required second consumer (L4/L7): one
artifact, two jobs. Rules: the starter references only PUBLISHED packages
(never crawler source — crawler is the linked advanced example once public);
per-library contracts stay in package READMEs (the DoD), the guide links them;
each extraction rung adds its starter section, so the guide grows exactly at
the rate the platform supports outsiders. Gated on the first publications
(graphics 0.2.0 / engine_host / canvas 0.1.0).

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
- **The bundle system** (gen_bundles.loft + catalog merge + routine-by-id): the most
  valuable candidate and the most premature — SCRIPTING.md Stage 1 (the event bus) will
  reshape the routine seam. Extract after that lands and the shape survives two
  consumers.
- **The @PLN2 chunked-world substrate** (chunk/world model, heightfield surface mesh,
  camera+input, golden harness): the shared-world-substrate convergence with dryopea
  Plan 07 + moros (`gridmesh` + `hex_terrain`/`moros_map` + `moros_render`). Detailed
  targets, concrete homes, and working extraction sources (audience-demo `AutoCam`/VBO,
  dryopea `golden.loft`, crawler `chunk_mesh`) are in **`plans/2-chunked-lod-world/`** →
  "Extract to proper shared libraries". Gated: prove in crawler first, and the substrate
  itself is blocked by loft `use`-namespacing + the native struct-return bug (both noted
  there). Extract once those clear and the primitives are proven.

## Order of work

**LANDED:** §1 `hexgrid` (→ `hex_grid`), §4 `random` value-stream, §5 `hex_terrain` —
all merged in their lib repos and consumed by crawler, gate green (owner registry-
release is the only tail on each). **OPEN:** §2 text-layout (small), §3 draw.py
flow-back (small — the Petals/Fronds port), §6 GPU 2D primitives (the big block),
Tier-2 decouplings (opportunistic), Tier-3 (gated).

**The master order for the OPEN 2D/graphics work is the dependency tree in
plans/7-render/ → "Implementation tree"** — §6's rungs (L0–L7) interleave with the
P-steps on one spine there; this doc keeps the per-rung detail, the tree owns the order.
The next actionable node is **L0** (wire the `../loft-libs-graphics` dev `--lib`), with
§3 (draw.py flow-back) and P7a (atlas packer) as no-dep leaves runnable alongside it.
Tier-2 decouplings stay opportunistic. Each step independently shippable, each ends
gate-green.
