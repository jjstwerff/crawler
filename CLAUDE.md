# CLAUDE.md — crawler quick reference

Clean-room, ZAngband-style **hex roguelike** written in **loft** (package `story`,
repo `crawler`). **The game is moving into first-person 3D** (decided 2026-07-22, plan
**#11**): the hex FIELD built by plans #5/#9/#10 becomes the world the player stands in,
actors are camera-facing boards on the way to animated meshes, and **3D replaces the 2D
view** once it reaches parity. The renderer-agnostic kernel is what makes that a view-side
change — keep it. *(Superseded: "2D is first-class, 3D is additive". The 2D renderer still
runs and is retired in plan #11 P9; DESIGN §7a's plane-first reasoning is being reworked
with it.)* Full design + roadmap: **DESIGN.md** (backlog = §18a); the 3D plan +
its seven invariants: **plans/11-3d-world/**.

> **Companion docs, loaded on demand — do NOT read them unless the task needs them.**
> **`SPRITES.md`** — authoring 2D sprites (tool, done-criterion, perspective, palette, QA).
> **`LOFT-NOTES.md`** — the loft survival guide in full, bug filing, and where the toolchain
> and libraries live on this machine.
> Split out of this file 2026-07-23: they cost ~4k tokens every session and matter in few of
> them. This file keeps the pointer plus the handful of traps that bite most often.

## The singular goal, and the test that follows from it

**Everything here serves one goal: hand SMALL TEAMS the hard parts already solved.** Indies —
not 150-person studios with world builders, level designers and an art department. crawler is
the **proof and the forcing function**, not the product; the product is the substrate (loft,
the `hex_*` libraries, the editor) that lets two people build a world which currently needs a
studio.

**The over-engineering test.** This project over-engineers deliberately — a whole *language*
was built for it — and that is justified by exactly one thing: **we do the hard algorithmic
work that others build on.** So before any deep investment, ask:

> *Does this make a hard part reusable by someone else?*

- **Yes** → build it properly: exact, gated, extracted. Depth is the point, and the cost is
  paid once here so it is never paid again downstream.
- **No** → it is crawler-only polish. It waits, and it says so out loud.

The test ranks work that would otherwise look equally attractive. The exact-integer lattice,
canopy-first trees, the scale contract and the far-field displacement are hard **and** reusable
— build them exactly. Sprite art, per-scene colour and one game's feel are crawler-only — which
is why the 3D actors deliberately ship with the WRONG (top-down) PNGs on boards: the seam is
the reusable part, the art is not, and pretending otherwise would spend a month on 34 sprites
that teach nobody anything.

Two companions, and the three compose: **depth must be reusable** (this test), **depth must not
become interface** (DESIGN §3a pillar 0 — bounded simulation), and **depth must be measured**
(`SCALE.md` — real dimensions by default, gated, so a wrong world can be *proved* wrong rather
than argued about).

**Multi-phase work lives in `plans/<N>-<slug>/`**, `<N>` = its `jjstwerff/crawler` issue
number (claimed BEFORE the directory — never numbered by scanning the tree). Conventions,
the lightest-workflow table, and the value categories: **plans/README.md**; templates +
the close/defer checklist sit beside it. Lifecycle state is a **label on the issue**, not
a directory — so the overview is the tracker, not a hand-kept table:
`gh issue list -R jjstwerff/crawler --label plan --state all`. Note `@PLN<N>` always means
an **upstream loft** plan (UPSTREAM-PLANS.md); crawler's own are written `plan #<N>`.

## Run / build / test

```sh
make play     # native window (W/S glide, A/D turn, walk onto stairs, . wait, g grab, N next world, Esc quit)
make test     # headless deterministic gate — RUN THIS before committing
              #   QUIET ON PASS: one `ok  <secs>  <name>` line per test, a header
              #   naming the compiler (version + md5 — `--version` is NOT provenance),
              #   and a closing line for anything over 5 s. A FAILURE prints its own
              #   evidence, so you never go hunting for the log.
              #   GATE_VERBOSE=1 make test  -> the old full stream.
              #   14 heavy tests (16 rows) run --native-release (`·native`), the rest
              #   --interpret — 7-22x on those, ~10 s of rustc each when their cache
              #   is cold. GATE_NO_NATIVE=1 puts every row back on the interpreter:
              #   that is how you tell a native-codegen divergence from your own bug.
              #   Rows run min(8, nproc-2) at a time — 8 on this box. GATE_JOBS=1
              #   forces serial (and is how you tell a scheduling flake from a real
              #   red). Row ORDER is identical either way — the log stays diffable.
              #   ⚠ To prove a change behaviour-preserving, diff the PER-TEST logs
              #   (/tmp/story_<name>.log), not the gate's stdout — they cannot
              #   interleave, and stdout no longer carries the outputs.
make check    # quiet compile-only gate (parse + bytecode), no display
make shot     # one Xvfb frame -> story.png  (positionally unreliable, see below)
make probe    # pixel-probe gate: Xvfb renders + tools/probe.py asserts probes/*.probe
make bundles  # re-scan bundles/*/bundle.json -> the generated registries (loft scanner)
make game     # single-file story.html (WebGL) — unblocked (the E0514 rustc-mismatch is resolved)
```

Direct: `loft --interpret --path ../loft/ --lib ../loft/lib/ src/<f>.loft`
(needs the loft toolchain at `../loft`; `make play LOFT_REPO=…` to override).

**Iterate on ONE test, not the whole gate.** A single `src/<x>test.loft` runs in ~3 s; `make
test` runs all 99 (**101 rows** — `playtest` runs 4×) in **~1.5–2.5 min** (measured 2026-08-10,
8-wide: 1m29s / 1m47s / 2m29s warm, **2m43s with a cold native cache**, 3m15s at `GATE_JOBS=1`).
⚠ Box load moves that as much as cache state does — the pool absorbs the cold penalty (14
compiles ≈ 140 s of rustc cost only +56 s of wall clock). It used to be
**10–13 min**, closed by two changes: the 14 tests that held most of the wall clock now compile
via `--native-release` while the rest interpret (`tools/run_tests.sh` → `NATIVE_TESTS` carries
the measurement and the ≥10 s rule for joining), and rows now run **`min(8, nproc-2)` at a
time** (8 here — the cap is measured flat past 8, the `nproc-2` is headroom for the rest of the
box; `GATE_JOBS` overrides). ⚠ **Per-row
seconds are wall time under contention now** — at 8-wide `matrixtest` reads 1.0 s → 16.9 s — so
they rank the roster but are not measurements; time a test by running it alone. ⚠ **Budget
+10 s per affected native row when the compile cache is cold** — a kernel edit invalidates the
40 tests that transitively `use sim`, and a `make install` in `../loft` invalidates *all* of
them (the cache key hashes the generated Rust **and** `libloft.rlib`'s mtime). A blanket
`--native-release` was measured and rejected: 6.7× warm but **1.8× slower** cold, and cold is
the normal state here. Run the gate **once**, before committing — and read the existing
`/tmp/story_<name>.log` rather than re-running it to check a result.

## Design / debug protocol (exact-invariant work)

For **geometry / caching / serialization / store-lifetime / protocols** the correct design is
an **exact invariant**, not an open space. Don't approximate or symptom-chase toward it.
Step 1 is a **CONCRETE plotted end-result** (the exact target output/state for one specific
input — concrete examples land far better than abstract specs; ask the user to plot it, or
propose a candidate and confirm); **then** name the invariant (caching → *round-trip =
identity*), pin each step, and only then code. Anchor (Angband/real/moros) + reuse one model
by symmetry.

**A BLUEPRINT PHASE is for when the construction is UNKNOWN.** When the primitives already
exist in the tree, the cheapest medium is **the engine itself** — write the real code and its
gate, not a model of it. A model can disagree with the original *silently*: in plan #11 P5 a
Python blueprint reported a 39 % wall-run overhead where the engine measured 15.5 %, and the
wrong number reached a design doc before anyone ran the real thing. Case log + mechanism
study: **DESIGN-PROTOCOL.md**.

## Architecture invariant (do not break)

**Kernel** modules import **no graphics** — the `hex_grid` LIB (was hexgeo+gridgeo;
now `loft-lang/loft-libs-world`), `sim`, `gen`, `worldmesh`, `wallgeo`,
`framekey`, `gameflow`, `genbundles`, `monsters`/`classes`/`races`/`items`. **View** is the swappable front-end —
`view.loft` (2D, retiring in plan #11 P9), `story.loft`. The view reads the kernel only
through `sim_*` accessors. **That split is what makes the 3D move a view-side change**, so
keep all `graphics::` calls in `view`/`story` and keep `sim` data-only — it is now
load-bearing, not aspirational. The 3D renderer lands as the **`hexscene`** package rather
than a crawler-internal module, because the in-world editor draws the same field (plan #11
P3; `EXTRACTION.md` → *The editor as the second consumer*).

- Hex map, moros geometry (`L = √3`, pointy-top). Continuous player + heading;
  hex-locked enemies. **Distance-driven clock:** every `HEX_LEN` travelled = one
  `sim_tick`; turning is free; `sim_wait` forces one tick in place.
- **Bundles stay library-like.** Game content (monsters/items/stencils/placement/quests) lives in
  self-contained `bundles/<name>/` folders the engine merges generically — a stranger drops a bundle
  in, rebuilds without touching `src/`, and plays it against an unchanged game. **Every time you
  touch the engine↔bundle seam, re-evaluate that this still holds** (content bundle-side, mechanism
  engine-side, no engine-references-a-bundle-by-key). The standing check: **BUNDLE.md → "Standing
  check — keep bundles library-like"**.

## Conventions

- **Clean-room IP.** Mechanics/formulas/data follow Angband faithfully, but
  **names are original** — NEVER use Tolkien (Angband, Morgoth, Sauron, balrog,
  Nazgûl, ent; use "halfling" not "hobbit") or Zelazny/Amber (Oberon, Amberites,
  Trumps) names.
- **BOUNDED SIMULATION — depth in the derivation, shallow at the interface** (DESIGN §3a
  pillar 0, the authority over the others). Dwarf Fortress is hard to get into *not by
  design*; the trap is entered one reasonable feature at a time. A derived system buys
  **coherence, not mechanics**: derive as deep as you like, but ask of every one — *does this
  add something the player must learn?* If yes it must displace something. **The budget is
  measurable: 15 keys bound today** (~11 gameplay), Doom-to-Souls territory, and it stays
  there. "It is realistic" justifies the derivation, never a new verb.
- **Follow Angband logic, tune for accessibility.** Reproduce real Angband (4.2 core
  + ZAngband wilderness/realms) *systems/mechanics* faithfully — but the *curve*,
  *death model* (checkpoint respawn, not permadeath), and *class weight* are
  deliberately friendlier (see **DESIGN §3a** — "Angband bones, friendly tuning").
  Only names/lore are clean-room.
- **Content is authored to its FULL design; build SYSTEMS to realize it — never nerf
  content to fit a half-built engine.** A monster/item keeps its true mechanic (a floating
  eye = 0 melee + a paralysing gaze; a Scroll of Teleport teleports) even if the system
  that powers it isn't built yet — then build that system. Do NOT give the eye a stand-in
  bite or make a scroll inert to match the engine. The ONLY allowed deviation is the §3a
  *tuning* (numbers: curve/death/class-weight), not removing or substituting a mechanic.
- Every kernel feature gets a headless **`src/<x>test.loft`** wired into `make test`
  (currently **99 files / 101 rows** — combat/AI/placement/levels/hero/items/equip/bundles/
  defs/quests/msg/inv-hub/effects/specials/unknown-items/races/classes/crystal/overland/
  safety/production/repair/travel/idle-skip/mesh/kernel/replay/playthroughs/…). Keep it
  **warning-clean**. ⚠ **WIRING IT IN IS THE STEP THAT GETS SKIPPED, and nothing complains** —
  `tools/run_tests.sh` is the roster, not `src/`. Five tests sat on disk unwired until
  2026-08-10 (`fig`/`gen`/`grid`/`mon`/`wall`) and `canopytest` was listed twice; a test the
  gate never runs is not a gate. The check is one line:
  `comm -23 <(ls src/*test*.loft|sort) <(grep -oE 'src/[a-z_0-9]+test\.loft' tools/run_tests.sh|sort -u)`
  — it should print only `src/selftest.loft` (the kernel self-test, run before the tables).
  Pixel-level render checks
  live in **`make probe`** (Xvfb + `tools/probe.py` vs `probes/*.probe` — the render plan (#7)
  P0). The games-kernel adoption track (@PLN18 engine_host): **plans/6-games-kernel/**.
- **Headless rendering IS self-verifiable** (corrected 2026-06-15). `gl_screenshot` under
  Xvfb reads the GL **framebuffer reliably** — it's exactly what `make probe` uses (plan #7
  P0). **`xvfb-run` IS installed on this box.** The only *positionally-unreliable* capture is
  `make shot`'s window-grab (`xdotool`/`import`) — not `gl_screenshot`. So render
  **correctness can be gated headlessly** via golden-image diffs, two paths:
  (1) **native GL** — `gl_screenshot` under `xvfb-run` + Mesa `llvmpipe` (deterministic
  software GL), diffed vs a golden PNG (tolerance ~max-16/mean-2, the loft `crystal_editor_gold`
  pattern); (2) **WebGL** — the `loft --html` build in headless Chrome via loft's
  `tools/html_render_check.mjs` (CDP screenshot + canvas color-count gate). For plain 2D
  diagnostics the `graphics` **`Canvas`** (`fill_triangle`/`draw_line`/`save_png`) needs no GL
  or Xvfb at all — `../hexbody/src/houseshot.loft` is the worked example. The **user still judges
  *aesthetics***, but the agent self-checks structure/regressions. Recipe + the
  scene-`--smoke`-then-`gl_screenshot` idiom: **plans/7-render/**.
- **2D sprites → `SPRITES.md`** (the `draw` skill + `tools/draw.py`; done-criterion,
  perspective, palette, scale, QA, reference plates). The one thing to know from here: **the
  view resolves sprites BY NAME, no code per sprite** — drop `<monster_key>.png` into
  `assets/sprites/` and it is in the game; a missing file falls back to the glyph.
- **Where things stand right now — `STATE.md`.** Plans #5/#9/#10, the decisions already
  taken (scale, the library/content seam, props-as-objects, stencils), what is open and
  whose call it is, and the three lessons worth carrying. **Read it first after a `/clear`.**
- **Scale: one grid, two readings — `SCALE.md`.** Architecture is true-scale at **1.5 m
  per hex step** (1 world unit = 0.866 m); terrain is the *same* hex compressed 10× at
  **15 natural m per walked hex** (`OV_STEP`, a gameplay-evaluated user ruling). The
  contract is code (`src/scale.loft`) and gated (`src/scaletest.loft`), which converts every
  plan threshold to metres and checks it against the real object. **State new lengths in
  metres, or add a row to that gate** — an unconverted threshold cannot be falsified.
  Known consequence: a *domestic* staircase (0.28 m going) is below one hex step and is an
  **object**, not a field; plan #5's stair work describes monumental stepped work.
- **Docs-first knowledge capture (user rule, 2026-06-12): anything memory-worthy
  goes into the appropriate repo doc** (RENDER/PLAN-*/EXTRACTION/BUNDLE/this file)
  — agent memory holds only pointers. The repo is the shared brain; private notes
  must not be the sole home of project knowledge.
- **Read narrowly.** Prefer `grep` + an offset `Read` over pulling a whole doc; skip any doc a
  newer one declares superseded. Editing a file with `sed`/heredoc makes the harness re-inject
  the WHOLE file — use the Edit tool. (Plan #11 P5 lost ~17k tokens to exactly that.)
- Commits: branch **`combat`** (not `main`); end messages with
  `Co-Authored-By: Claude Opus <N> (1M context) <noreply@anthropic.com>` — **naming the model
  that actually did the work**, not a version copied from this line.
- **ALWAYS COMMIT AND PUSH — it is a SAFETY MEASURE, not a publication step** (user ruling,
  2026-08-09). The remote is the backup; local-only work on a box that runs several agents is
  fragile. ⚠ **Stage your own paths explicitly — `git add -A` is wrong here**, because another
  agent's in-flight work is routinely sitting in the tree. Put the **finding** in the commit
  message, not just the change. Still worth a word first: a PR, a published package, a
  registry entry.

## loft — the traps that will bite you today

**Full survival guide, bug-filing procedure and toolchain/library locations: `LOFT-NOTES.md`.**
Crawler is a CONSUMER — we never fix loft here; file it (standing grant: no per-issue
authorization needed), work around it, keep moving. Toolchain **2026.7.2**; `graphics` must be
**>=0.5.0**. The short list:

- **Fallible float math returns `float?`** — `sqrt`, `pow`, `ln`, `asin`, and *variable* `/`
  and `%`. Discharge at the root with `?? 0.0`. A `??` default must match the type EXACTLY —
  on a `vector<single>` write `?? 0.0f`.
- **`text as integer|float|single` is a nullable parse** — settle with `?? 0` at the cast.
- ~~`vec += [f(struct_temp)]` nulls every element but the first~~ (loft#496) and ~~a
  self-referential `??` default SIGSEGVs the compiler~~ — ✅ **BOTH FIXED, verified 2026-08-09
  on 2026.8.0** by re-running LOFT-HANDOFF's own repros (H2 prints all four records; H1 prints
  `key=rat lvl=1`). **The hoist-into-a-local and separate-fallback workarounds are obsolete —
  stop writing them.** Existing ones are harmless; no sweep needed. ⚠ Do not re-add either
  from memory: both were true for months, so they read as folklore.
- **A `fn(...) -> vector<single>` passed to a native FFI call silently ABORTS the program**
  (loft#392) — no stdout, no PNG, exit 0. Inline the buffer-building loop in the caller.
- **`!x` on a non-boolean is a NULL test, not logical-not** — compare `== 0`.
- **Never swap struct vector elements via a temp link**, and **never build `vector<text>`
  literals in large functions**.
- **Do NOT delete a `?? ""` / `?? 0` guard** the compiler calls "redundant" on the strength of
  the advice alone. ⚠ Its original reason (#496 nulling fields at RUNTIME) is **gone** — so if
  you want one removed now, *measure it*, don't cite #496.
- `make bundles` is a **silent-corruption** surface (JSON `kind()` now splits `JInteger` out of
  `JNumber`). Round-trip check: the generated `src/*_gen.loft` must be byte-identical to HEAD.

## Library extraction (the reusable-library goal made concrete)

Routines that serve other games get PUSHED to the library layer — plan + tiers + per-package
Definition of Done: **EXTRACTION.md** (hexgrid = the canonical moros-convention hex geometry,
text-layout helpers → graphics, draw.py flow-back → the skill, a seeded `random` package;
wallgeo/gen after one decoupling each; roguelike-kit + the bundle system deliberately gated).
Where the siblings, toolchain and library stores live: **`LOFT-NOTES.md`**.

**What crawler depends on moros FOR — `MOROS.md`.** The shared world (the 8 stats, races,
powers and their names, seeded from `html/data.js` — the one place the clean-room rule is
deliberately suspended), the hex convention, the scoped-identity decision crawler waits on,
and moros being the library layer's second consumer. ⚠ **No libraries in it**: a library
dependency is a **contract** (`api_compatible_with`/`loft.lock`), owned by nobody and
changeable by anybody within it — listing one there would claim a veto crawler does not
have. A dependency belongs there only if crawler would be *wrong* when it changed, and *no
contract would catch it*.

⚠ **OTHER PEOPLE'S TREES ARE READ-ONLY — `../moros` HAS ITS OWN AGENT RUNNING** (user
instruction, 2026-08-09), and it moved through four commits during one crawler session.
Read it freely and write down what you learn *here*; **do not edit that tree, and do not
post to its tracker either** — an edit it did not make destroys its ability to tell its
own work from yours. This is the mirror of moros' own rule about `../crawler` (*"raise
findings instead"*), and the same holds for `../loft`, where the standing grant is **read
plus FILE TICKETS, nothing else** (`LOFT-NOTES.md`). Cross-project findings become a
document in crawler; **how one reaches the other project is the user's call**, not an
action to take unasked — plan #13 `S1` is the worked example.

**NO FIRST-CLASS PROJECT OWNS A LIBRARY** (user ruling, 2026-08-09) — not loft, not moros, not
crawler, not lavition. A library must be useful to **everybody**, and **any project may add
what it needs**; the only constraint is not breaking the others, which is what the library
contract (`api_compatible_with` / `data_compatible_with`) makes checkable. So "we wrote it" is
never a reason to keep a copy, "they wrote it" is never a reason to refuse a package, and
*"the library doesn't have it"* is a reason to **extend the library**, not to grow a private
module.

**AND ITS CONSTRUCTIVE HALF — a library design must be UNIVERSAL FOR THE CLASS**, not for one
project's scope. The live case is **indexing of walls / items / ground**: a stored identity is
an **index into a table owned by a SCOPE**, `0 = nothing` the only fixed one — the library owns
the *indirection*, each project owns its *palette*, and the **scope is a parameter** (a region
in moros, a bundle in crawler, a level elsewhere), never an enum of known scopes. crawler has
solved half of this (bundles + `catalog.loft` merge, for open enumerations) and hard-codes the
other half (**36** literal-tile sites; plus **24** dispatch-on-content-key sites in
`itemfx`/`sim` that BUNDLE.md's standing check forbids). ⚠ **Do not close those privately** —
that is the third implementation of one idea. **ADOPTION.md → "Universal for the class"**.

**ONE RESOLUTION PATH — THE REGISTRY IS AUTHORITATIVE** (ADOPTION.md P3). A `--lib` sibling
tree **outranks** the registry copy, so every one is a silent override: `random` was locked at
0.1.0 while the build quietly took the working tree's 0.2.0 — and `sim.loft` uses 0.2.0's
`RandStream`, so **the lock described a build that could not compile**, unreported, for weeks.
⚠ **The only legal `--lib` in the Makefile is a package that is NOT published, and it must say
why there** — today exactly one, `../loft/lib/` for `engine_host`. Testing against an
unreleased sibling goes on the **command line for that run**. And ⚠ **`loft update` does not
notice a newly declared dependency** (it walks the lock, not the manifest, and still reports
"up-to-date" — LOFT-HANDOFF H9): after adding a dep, **compile once, then check `loft.lock`
names it.**

The **pull** side is **ADOPTION.md**: what is already in the family and is still here as a
copy. ✅ **The four known forks are gone** — `hexform`/`hexedge`/`hexway`/`hexroof` were the
same construction as the published `hex_field`/`hex_edge`/`hex_way`/`hex_roof`, and all four
are now **consumed from the registry** and deleted from `src/` (verified 2026-08-10; the rule
that drove it stands — **a duplicate of a library module is a fork**). The rest of the family
shares 0–1 function names with crawler, so switching costs a rewrite: those are **deferred on
price, not refused on principle**, and they close by convergence in the library.

## Where things are

- **`hex_field`** (LIB, `loft-libs-world`) — the exact-integer field core: `HexSet`,
  `VecMap`, `trace`/`validate`, `Labels`, `Heights`, `EdgeSet`, `Stencil`. **Was
  `src/hexform.loft`; extracted 2026-07-22 and the crawler copy DELETED** (46 files switched
  `use hexform` → `use hex_field`; zero qualified call sites). Its gate travels with it (`loft
  test` in the package); crawler keeps the golden-JSON diff vs the Python oracle as its
  consumer check. The in-world editor is the second consumer — `EXTRACTION.md` → *The editor
  as the second consumer*.
- **The world is DERIVED, and `overland` owns the deriving.** It decides *where* a settlement
  is, its size, its field ring (`ot_fld`), its roads and its ruins — scored from terrain. The
  geometry stack (#5/#9/#10) is a **consumer** of that: it builds what the scorer placed, at
  real measurements (`SCALE.md`). **We integrate with that system; we do not rewrite it** —
  no settlement logic in the field model, no second scorer, and the seam runs one way only
  (plan #11 P5).
- `overland.loft` — the contract WILDERNESS (OVERLAND.md §12-13): the example world's
  vertex/side/corner/edge contracts + zonation -> terrain kinds; the depth-0 surface is a
  101×101 window of it (15 natural m per walked hex); `ovmap.loft` prints it as a ZAngband
  character map.
- `sim.loft` — world/player/enemies, combat (+`sim_bolt`), monster AI (awareness +
  flow-field pathing), XP/level (race+class-scaled `xp_need`), HP/SP pools + natural
  regen, statuses (paralysis/poison/ward), race+class apply (`apply_creation`, the
  cached `rc_*` derivations), the shrine re-spec, unknown-item flavours, stairs/depth,
  the clock.
- `gen.loft` — procedural dungeon (rooms+corridors), `world_key_seed`.
- `catalog.loft` — the merges: `game_monsters`/`game_items`/`race_catalog`/`class_catalog`.
- `castfx.loft` / `itemfx.loft` — the API layer above the kernel: cast + use-item verbs,
  dispatching to BUNDLE routines via the generated `spell_defs_gen`/effect arms.
- `worldmesh.loft` — the kernel-side terrain mesh (hexagon fans, stride 10, R4
  tint bake pre-composed into vertex colors; the view only uploads/draws it).
- **The geometry-body work lives in the `hexbody` PROJECT** (`../hexbody`, a sibling split out
  2026-07-23), not crawler: `housedraw` (buildings in the 12 orientations — `draw_floor`,
  `draw_walls` thin/edge-based, `place_opening`, `draw_roof`), gated by its own `make test`
  (`housetest`), with `houseshot` the 12-orientation contact sheet. It is the harness where
  produced geometry stands in for meshes so a system can be tested before art exists — the
  vehicle/body/proxy/destruction line this whole thread designed. crawler will consume it once
  `stamp_house` becomes a caller; today crawler's game does not use it. Design + goals:
  `../hexbody/{VISION,ARCHITECTURE}.md`; the detailed geometry spec is still `plans/11-3d-world/
  BUILDING.md`.
- **`hex_roof`** (LIB) — every roof form as one distance read through a profile (ridge/hip/
  cone/dome/vaults) + the `roof_ponds` / `eave_spread` / `clear_height` gates. *Was
  `src/hexroof.loft`; consumed from the registry and the copy deleted.*
- `gameflow.loft` — the deterministic intent seam (K2): `flow_genesis`/`flow_move`/
  `flow_action` + the S/T/A wire codec; the host applies AND broadcasts, a replica
  replays — scene_key-identical worlds (replaytest). `observe.loft` = the live
  spectator (connects to a running `story` on :18099, full renderer).
- `story.loft` — the entry: the games-kernel HOST (`engine_host::run` — drift-free
  60 Hz ticks, idle backoff, observers served the intent log; `game_tick` is the
  frame; N = next world via `genbundles`). `framekey.loft` — the idle-skip scene
  digest (the ONE chokepoint for stale-frame bugs).
- `view.loft` — egocentric renderer; `Hud` + `build_hud` bake glyph/HUD textures AND the
  sprites (by-name from `assets/sprites/`: `<monster_key>.png`, `player.png`, per-category
  loot; glyph fallback); overlays: char page, inv hub, crystal page. `wallgeo.loft` —
  wall outline (rounded; DP straightener parked in `patches/`).
