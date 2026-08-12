# CLAUDE.md — crawler quick reference

Clean-room, ZAngband-style **hex roguelike** written in **loft** (package `story`,
repo `crawler`). **The game is moving into first-person 3D** (decided 2026-07-22, plan
**#11**): the hex FIELD built by plans #5/#9/#10 becomes the world the player stands in,
actors are camera-facing boards on the way to animated meshes, and **3D replaces the 2D
view** once it reaches parity. The renderer-agnostic kernel is what makes that a view-side
change — keep it. *(Superseded: "2D is first-class, 3D is additive". The 2D renderer still
runs and is retired in plan #11 P9; DESIGN §7a's plane-first reasoning is being reworked
with it.)*

> **THIS FILE IS RULES AND POINTERS.** It is loaded into every session, so it carries only
> what you must know *before* you know to look it up. A rule's evidence lives in the doc or
> the script that owns it, named on the rule — read that one when the rule is what you are
> about to break.
>
> ⚠ **A number a command will print is not written here.** Every one that was had rotted
> silently: on 2026-08-11 this file said 105 test files / 108 rows / 14 native rows against
> **107 / 109 / 19** on disk, and `run_tests.sh` announced a fifth figure of its own. ⚠ **The
> audit that caught them miscounted too** — 110 rows, because a `grep -c '^collect_one'` also
> matches that function's *definition*. Ask the gate; it counts.

## Where to look it up — open ONE, and only when the task needs it

| Doc | Open it when |
|---|---|
| **STATE.md** | starting work — ⚠ **the top block ONLY**. Everything under it is RECORD, reached by grep for one question, never top to bottom |
| **plans/11-3d-world/** | the live plan: the 3D move and its seven invariants |
| **plans/README.md** | opening, closing or deferring a plan — conventions, the lightest-workflow table, value categories |
| **DESIGN.md** | the game design; **§3a** = the pillars, **§18a** = the backlog |
| **VISION.md** | what the whole stack is for (read once, first) |
| **README.md** | the game as a player or newcomer meets it |
| **ROADMAP.md** | the path to a working game |
| **LOFT-NOTES.md** | the loft survival guide in full, bug filing, and where the toolchain and libraries live on this box |
| **LOFT-HANDOFF.md** | a loft defect — findings ready to file, each with its repro (`H<N>`) |
| **FILING.md** | how and why to file a loft ticket |
| **LIBRARIES.md** | ⚠ **any signature in any dependency**. Generated (`make apidoc`, verified by `make apidoc-check`) — open a package for its *reasoning*, never to find out what a function takes |
| **EXTRACTION.md** | pushing a crawler routine down to the library layer — tiers, per-package Definition of Done |
| **ADOPTION.md** | consuming the family instead of copying it; the frozen-renderer ruling; *Universal for the class* |
| **MOROS.md** | what crawler depends on moros FOR (and why no library is listed there) |
| **UPSTREAM-PLANS.md** | you meet an `@PLN<N>` — always an upstream *loft* plan; crawler's own are `plan #<N>` |
| **BUNDLE.md** | you touch the engine↔bundle seam — including its *standing check* |
| **BUNDLE-MIGRATION.md** | moving classes, races or content into bundles |
| **SCRIPTING.md** | bundle scripting and the mod-platform path |
| **CATALOG.md** | the content tables; **§0 = the eight statistics and what each one drives** |
| **STENCILS.md** | layered, composable stencils → castles |
| **CRAFTING.md** | the living settlement — safety, workers, stock, incursions, standing (plan #17, shipped) |
| **OVERLAND.md** | the wilderness contract (§12-13), zonation, rivers |
| **SCALE.md** | ⚠ **you state a new length** — the two readings (`OV_STEP`) and the vertical |
| **TREES.md** | canopy-first trees |
| **PROPS.md** | props with hinges, wheels and linkages |
| **FORMS.md** | the kit of exact, interlocking hex parts |
| **WALLS.md** | the triangle-subdivision wall model |
| **RENDER.md** | the 2D GPU renderer (retiring in plan #11 P9) |
| **SPRITES.md** | authoring a 2D sprite — the `draw` skill, done-criterion, perspective, palette, QA |
| **DATA.md** | the world-state / world-data model |
| **DESIGN-PROTOCOL.md** | the blueprint-vs-engine case log — how a model disagrees with the original *silently* |
| **RESOLUTION.md** · **PARTY.md** | design, not built: pluggable resolution and non-trivializing progression · co-op party, Tension, cards-as-UI |
| **SLICE.md** | *historical* — the shipped June vertical slice. Nothing points at it |

Plan state is a **label on the issue**, not a directory, so the overview is the tracker:
`gh issue list -R jjstwerff/crawler --label plan --state all`.

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

- **Yes** → build it properly: exact, gated, extracted. The cost is paid once here so it is
  never paid again downstream.
- **No** → it is crawler-only polish. It waits, **and it says so out loud.**

The exact-integer lattice, canopy-first trees, the scale contract and the far-field
displacement are hard **and** reusable — build them exactly. Sprite art, per-scene colour and
one game's feel are crawler-only — which is why the 3D actors deliberately ship with the WRONG
(top-down) PNGs on boards: the seam is the reusable part, the art is not.

Two companions, and the three compose: **depth must be reusable** (this test), **depth must not
become interface** (bounded simulation, below), and **depth must be measured** (`SCALE.md` —
real dimensions by default, gated, so a wrong world can be *proved* wrong rather than argued
about).

**Multi-phase work lives in `plans/<N>-<slug>/`**, `<N>` = its `jjstwerff/crawler` issue number,
**claimed BEFORE the directory** — never numbered by scanning the tree.

## Run / build / test

```sh
make play     # native window (W/S glide, A/D turn, walk onto stairs, . wait, g grab, N next world, Esc quit)
make test     # headless deterministic gate — RUN IT BEFORE COMMITTING. Quiet on pass (one
              #   `ok <secs> <name>` per row + the compiler's version AND md5 — `--version` is
              #   NOT provenance); a FAILURE prints its own evidence. It reports its own row
              #   count, width and slow tail, so no doc has to.
make check    # quiet compile-only gate (parse + bytecode), no display
make shot     # one Xvfb frame -> story.png   (a window-grab: positionally unreliable)
make probe    # pixel-probe gate: Xvfb renders + tools/probe.py asserts probes/*.probe (~10 min)
make bundles  # re-scan bundles/*/bundle.json -> the generated registries (loft scanner)
make apidoc   # regenerate LIBRARIES.md from the resolved packages (apidoc-check verifies it)
make doccheck # doc seam (~1 s, in `make test`): links resolve, backticked crawler paths
              #   exist, every root doc is in the routing table, every nested doc is
              #   pointed at. Say `was `path`` (or a deletion word) to name a file as GONE
make ovshot   # re-draw README's two world maps from overland.loft (NATIVE, ~35 s; >10 min
              #   interpreted). Re-running must leave doc/*.png byte-identical unless the world
              #   derivation genuinely moved — the target says which, and it is a real check.
make game     # single-file story.html (WebGL)
```

Direct: `loft --interpret --path ../loft/ --lib ../loft/lib/ src/<f>.loft`
(needs the loft toolchain at `../loft`; `make play LOFT_REPO=…` to override).

- **Iterate on ONE test, not the whole gate** — a single `src/<x>test.loft` runs in ~3 s where
  the roster runs in minutes. Run the gate **once**, before committing, and to check a result
  read the existing `/tmp/story_<name>.log` rather than re-running it.
- ⚠ **To prove a change behaviour-preserving, diff the PER-TEST logs** (`/tmp/story_<name>.log`)
  — never the gate's stdout, which no longer carries the outputs and could interleave if it did.
- ⚠ **Budget ~10 s of rustc per affected native row on a cold compile cache.** A kernel edit
  invalidates every test that transitively uses it; a `make install` in `../loft` invalidates
  **all** of them (the key hashes the generated Rust *and* `libloft.rlib`'s mtime). Cold is the
  normal state here — which is why a blanket `--native-release` measured *slower* than the
  interpreter, and why the native list (`NATIVE_TESTS`, the `·native` rows) is a per-test choice.
- ⚠ **Per-row seconds are wall time under contention** — they rank the roster, they do not
  measure it. Time a test by running it alone.
- The long poles are the settlement tests (`stocktest`, `militiatest`, `incursiontest`) and
  `worldtextest`, and that is **inherent, not waste**: each generates real 101×101 surfaces,
  because plan #17's claims are about what a settlement *produces* and #11's about a whole
  world's landcover — neither can be asked of a sandbox.
- Knobs: `GATE_VERBOSE=1` (the full stream; implies serial) · `GATE_NO_NATIVE=1` (every row
  interpreted — **how you tell a native-codegen divergence from your own bug**) · `GATE_JOBS=1`
  (serial — **how you tell a scheduling flake from a real red**). Row ORDER is identical either
  way, so the log stays diffable.
- **The reasoning behind all of it is `tools/run_tests.sh`'s own comment headers** — which
  measurement chose the native list, why the width caps at 8 and must not track `nproc`, why one
  printer walks the roster in order. That script is the authority; this file does not restate it.

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
wrong number reached a design doc before anyone ran the real thing. Case log +
mechanism study: **DESIGN-PROTOCOL.md**.

## Architecture invariant (do not break)

**Kernel** modules import **no graphics** — the `hex_grid` LIB (`loft-lang/loft-libs-world`),
`sim`, `gen`, `worldmesh`, `wallgeo`, `framekey`, `gameflow`, `genbundles`,
`monsters`/`classes`/`races`/`items`. **View** is the swappable front-end — `view.loft` (2D,
retiring in plan #11 P9), `story.loft`. The view reads the kernel only through `sim_*`
accessors. **That split is what makes the 3D move a view-side change**, so keep all
`graphics::` calls in `view`/`story` and keep `sim` data-only — it is load-bearing now, not
aspirational. The 3D renderer lands as the **`hexscene`** package rather than a crawler-internal
module, because the in-world editor draws the same field (plan #11 P3; `EXTRACTION.md` → *The
editor as the second consumer*).

- Hex map, moros geometry (`L = √3`, pointy-top). Continuous player + heading;
  hex-locked enemies. **Distance-driven clock:** every `HEX_LEN` travelled = one
  `sim_tick`; turning is free; `sim_wait` forces one tick in place.
- **Bundles stay library-like.** Game content (monsters/items/stencils/placement/quests) lives
  in self-contained `bundles/<name>/` folders the engine merges generically — a stranger drops a
  bundle in, rebuilds without touching `src/`, and plays it against an unchanged game. **Every
  time you touch the engine↔bundle seam, re-evaluate that this still holds** (content
  bundle-side, mechanism engine-side, no engine-references-a-bundle-by-key): **BUNDLE.md →
  "Standing check — keep bundles library-like"**.

## Conventions

- **Clean-room IP.** Mechanics/formulas/data follow Angband faithfully, but **names are
  original** — NEVER use Tolkien (Angband, Morgoth, Sauron, balrog, Nazgûl, ent; use "halfling"
  not "hobbit") or Zelazny/Amber (Oberon, Amberites, Trumps) names.
- **BOUNDED SIMULATION — depth in the derivation, shallow at the interface** (DESIGN §3a pillar
  0, the authority over the others). Dwarf Fortress is hard to get into *not by design*; the trap
  is entered one reasonable feature at a time. A derived system buys **coherence, not
  mechanics**: derive as deep as you like, but ask of every one — *does this add something the
  player must learn?* If yes it must displace something. **The budget is 15 keys** (~11
  gameplay, 4 meta), Doom-to-Souls territory, and it stays there. "It is realistic" justifies
  the derivation, never a new verb. ⚠ **It reads 16 today** — `V`, the toggle P9 removes with
  the 2D view. Count it, never quote it: DESIGN §3a carries the one-liner and the reasoning.
- **Follow Angband logic, tune for accessibility.** Reproduce real Angband (4.2 core + ZAngband
  wilderness/realms) *systems/mechanics* faithfully — but the *curve*, *death model* (checkpoint
  respawn, not permadeath) and *class weight* are deliberately friendlier — **DESIGN §3a,
  "Angband bones, friendly tuning"**.
- **Content is authored to its FULL design; build SYSTEMS to realize it — never nerf content to
  fit a half-built engine.** A monster/item keeps its true mechanic (a floating eye = 0 melee +
  a paralysing gaze; a Scroll of Teleport teleports) even if the system that powers it isn't
  built yet — then build that system. Do NOT give the eye a stand-in bite or make a scroll
  inert. The ONLY allowed deviation is the §3a *tuning* (curve/death/class-weight), never
  removing or substituting a mechanic.
- **Every kernel feature gets a headless `src/<x>test.loft` wired into `make test`**, and kept
  warning-clean. ⚠ **WIRING IT IN IS THE STEP THAT GETS SKIPPED, and nothing complains** —
  `tools/run_tests.sh` is the roster, not `src/`; five tests sat on disk unwired for months. The
  check is one line, and it should print only `src/selftest.loft`:
  `comm -23 <(ls src/*test*.loft|sort) <(grep -oE 'src/[a-z_0-9]+test\.loft' tools/run_tests.sh|sort -u)`
- **Pixel-level render checks live in `make probe`** (Xvfb + `tools/probe.py` vs
  `probes/*.probe`) — **green 2026-08-11, all 15 checks at dmax=0**, the first time since June.
  ⚠ **It is not in `make test`** (~10 min), so run it after render-side work and treat green as
  a fact *with a date on it*. The three-layer rot plan #16 `M4` found is closed, and the last
  layer was not what it looked like: **the goldens were never stale.** `worldprobe.loft` held a
  **lost write** — `vv = s.vis` mutates a COPY (loft C86) — so its scene built **0 remembered
  cells** and two probes asserted a state it had stopped producing; with the write fixed,
  `rem_grass` passes at its original June coordinate at dmax=0. The other pins had simply been
  aimed at a town wall plan #17 re-cut, and were re-aimed at the same features with **every
  expected colour byte-identical**. ⚠ **The source fix: `make check` now compiles EVERY entry
  point and FAILS on `lost-write`** — nothing fast used to compile a render scene at all, which
  is why a compiler warning naming the exact bug went unread for two months.
- ⚠ **The tree has ~135 `fn main()`s and the gates compile SIX of them** — the game, the four
  scenes `make probe` renders, and `ovshot` (README's world map). The rest are one-off tools
  whose breakage costs one run rather than a false-green gate, so they are **swept on demand**,
  and the sweep pays for itself: over all **198** `.loft` files (2026-08-11) it found **191
  clean, 1 broken, 6 unbuildable-in-practice**.
  `for f in src/*.loft src/*/*.loft *.loft; do loft --interpret --check $LOFTFLAGS $f >/dev/null || echo $f; done`
  ⚠ **The `src/*/` term is load-bearing** — without it the glob matches 192, not 198, dropping
  `src/regions/`+`src/realworld/` — including the `ortler.loft` the finding is about.
  - The broken one was `near_mobs_test.loft`, crawler's @PLN48 validation of loft's spatial
    index: written against the upstream *plan directory's* spelling (`spacial`) where the
    feature shipped as **`spatial`**. One word, 16 cascading errors, never compiled, so the
    validation never ran. It runs now — `make near-test` — at 22× fewer candidates.
  - The six are the `ortler`-importing family (`viewer`, `hydro-test`, `rivers-test`,
    `trimesh-test`, `region`): **not broken, unusable.** `src/regions/ortler.loft` is generated
    data whose largest line is an 86 400-element vector literal, and loft parses a literal in
    **O(n²)** — ~18 min for that one line, at 99 % CPU with no output, so it presents as a hang.
    **loft#854**; a sweep's `timeout` cannot tell it from a deadlock, so do not read one as the
    other.
- **Headless rendering IS self-verifiable.** `gl_screenshot` reads the GL framebuffer reliably
  under Xvfb (`xvfb-run` is installed) — it is what `make probe` uses. The only
  positionally-unreliable capture is `make shot`'s window-grab. So render **correctness** gates
  headlessly by golden-image diff, two paths: **native GL** (`gl_screenshot` under `xvfb-run` +
  Mesa `llvmpipe`, tolerance ~max-16/mean-2) and **WebGL** (`loft --html` in headless Chrome via
  loft's `tools/html_render_check.mjs`). For plain 2D diagnostics the `graphics` **`Canvas`**
  needs no GL or Xvfb at all (`../hexbody/src/houseshot.loft` is the worked example). **The user
  still judges *aesthetics***; the agent self-checks structure and regressions. Recipe:
  `plans/7-render/`.
- **Scale: one grid, two readings** — architecture is true-scale at **1.5 m per hex step**;
  terrain is the *same* hex compressed 10× at **15 natural m per walked hex** (`OV_STEP`); and
  **rise takes the compression run takes**, so one `OV_STEP` of natural rise across one walked
  hex renders as exactly 45° and every angle in the world equals the real terrain's. The
  contract is code (`src/scale.loft`) and gated (`scaletest`). ⚠ **State a new length in metres,
  or add a row to that gate** — an unconverted threshold cannot be falsified. `SCALE.md`.
- **The view resolves sprites BY NAME, no code per sprite** — drop `<monster_key>.png` into
  `assets/sprites/` and it is in the game; a missing file falls back to the glyph.
- **Docs-first knowledge capture** (user rule, 2026-06-12): anything memory-worthy goes into the
  repo doc that owns it — agent memory holds only pointers. The repo is the shared brain.
  ⚠ **And a reference doc inside `plans/` is a doc nobody is allowed to read** (`TREES.md` was
  buried in its plan for months) — **`make doccheck` fails on it now**, with dead links and
  backticked paths that no longer exist.
- **Read narrowly.** Prefer `grep` + an offset `Read` over pulling a whole doc; skip any doc a
  newer one declares superseded. ⚠ **Editing a file through ANY shell command re-injects the
  WHOLE file** — `sed`, a heredoc, *and a `python3 -` script*, which reads as the safe
  alternative and is not: plan #11 P5 lost ~17k tokens to `sed` and ~750 lines to python on the
  same file. **Use the Edit tool for edits you make by hand**; a shell rewrite is only worth it
  for a bulk mechanical change across many sites, and then expect to pay for the file once.
- Commits: branch **`combat`** (not `main`); end messages with
  `Co-Authored-By: Claude Opus <N> (1M context) <noreply@anthropic.com>` — **naming the model
  that actually did the work**, not a version copied from this line.
- **ALWAYS COMMIT AND PUSH — it is a SAFETY MEASURE, not a publication step** (user ruling,
  2026-08-09). The remote is the backup; local-only work on a box running several agents is
  fragile. Put the **finding** in the commit message, not just the change. Still worth a word
  first: a PR, a published package, a registry entry.
  ⚠ **Stage your own paths explicitly — `git add -A` is wrong here**, because another agent's
  in-flight work is routinely sitting in the tree.
  ⚠ **And NEVER `git stash` to compare against history — use `git checkout <commit> -- <paths>`.**
  A stash of already-committed files saves nothing, so the `git stash pop` that follows pops
  **whatever stash was already there** — someone else's. It looks like it worked, and the
  "pre-existing?" answer it produces is a lie, because the code under test never changed.
  (It happened: `plans/16-eight-statistics/README.md`.)

## loft — the traps that will bite you today

**Full survival guide, bug-filing procedure and toolchain/library locations: `LOFT-NOTES.md`.**
Crawler is a CONSUMER — we never fix loft here; file it (standing grant: no per-issue
authorization needed), work around it, keep moving. `graphics` must be **>=0.5.0**; the
toolchain version is **not written here** — `make test` stamps it (version + md5 + whether it
is `../loft`'s working-tree build), because it changes under you and `--version` is not
provenance. The short list:

- **Fallible float math returns `float?`** — `sqrt`, `pow`, `ln`, `asin`, and *variable* `/`
  and `%`. Discharge at the root with `?? 0.0`. A `??` default must match the type EXACTLY —
  on a `vector<single>` write `?? 0.0f`.
- **`text as integer|float|single` is a nullable parse** — settle with `?? 0` at the cast.
- ~~`vec += [f(struct_temp)]` nulls every element but the first~~ (loft#496) and ~~a
  self-referential `??` default SIGSEGVs the compiler~~ — ✅ **BOTH FIXED, verified 2026-08-09
  on 2026.8.0.** **The hoist-into-a-local and separate-fallback workarounds are obsolete —
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

## Libraries — the reusable-library goal made concrete

**NO FIRST-CLASS PROJECT OWNS A LIBRARY** (user ruling, 2026-08-09) — not loft, not moros, not
crawler, not lavition. A library must be useful to **everybody**, and **any project may add what
it needs**; the only constraint is not breaking the others, which is what the library contract
(`api_compatible_with` / `data_compatible_with`) makes checkable. So "we wrote it" is never a
reason to keep a copy, "they wrote it" is never a reason to refuse a package, and *"the library
doesn't have it"* is a reason to **extend the library**, not to grow a private module.

**AND ITS CONSTRUCTIVE HALF — a library design must be UNIVERSAL FOR THE CLASS**, not for one
project's scope. The live case is **indexing of walls / items / ground**: a stored identity is
an **index into a table owned by a SCOPE**, `0 = nothing` the only fixed one — the library owns
the *indirection*, each project owns its *palette*, and the **scope is a parameter** (a region
in moros, a bundle in crawler, a level elsewhere), never an enum of known scopes. crawler has
solved half of this (bundles + `catalog.loft` merge) and hard-codes the other half — literal-tile
sites, plus dispatch-on-content-key sites in `itemfx`/`sim` that BUNDLE.md's standing check
forbids. ⚠ **Do not close those privately** — that is the third implementation of one idea.
**ADOPTION.md → "Universal for the class"**; the plan is **#13**.

**ONE RESOLUTION PATH — THE REGISTRY IS AUTHORITATIVE** (ADOPTION.md P3). A `--lib` sibling tree
**outranks** the registry copy, so every one is a silent override: `random` was locked at 0.1.0
while the build quietly took the working tree's 0.2.0 — and `sim.loft` uses 0.2.0's
`RandStream`, so **the lock described a build that could not compile**, unreported, for weeks.
⚠ **The only legal `--lib` in the Makefile is a package that is NOT published, and it must say
why there** — today exactly one, `../loft/lib/` for `engine_host`. Testing against an unreleased
sibling goes on the **command line for that run**. And ⚠ **`loft update` does not notice a newly
declared dependency** (it walks the lock, not the manifest, and still reports "up-to-date" —
LOFT-HANDOFF H9): after adding a dep, **compile once, then check `loft.lock` names it.**

✅ **The four known forks are gone** — `hexform`/`hexedge`/`hexway`/`hexroof` were the same
construction as the published `hex_field`/`hex_edge`/`hex_way`/`hex_roof`, are consumed from the
registry now, and the copies are deleted (2026-08-10). **A duplicate of a library module is a
fork.** The rest of the family shares 0–1 function names with crawler, so switching costs a
rewrite: those are **deferred on price, not refused on principle**. Push side: **EXTRACTION.md**.
Pull side: **ADOPTION.md**.

⚠ **OTHER PEOPLE'S TREES ARE READ-ONLY — `../moros` HAS ITS OWN AGENT RUNNING** (user
instruction, 2026-08-09). Read it freely and write down what you learn *here*; **do not edit
that tree, and do not post to its tracker either** — an edit it did not make destroys its
ability to tell its own work from yours. This mirrors moros' own rule about `../crawler`, and
the same holds for `../loft`, where the standing grant is **read plus FILE TICKETS, nothing
else**. Cross-project findings become a document in crawler; **how one reaches the other project
is the user's call**, not an action to take unasked (plan #13 `S1` is the worked example).

## Where things are

**The world is DERIVED, and `overland` owns the deriving** — where a settlement is, its size,
its field ring (`ot_fld`), its roads and its ruins, all scored from terrain. The geometry stack
(#5/#9/#10) is a **consumer** of that. We integrate with that system; we do not rewrite it —
no settlement logic in the field model, no second scorer, and the seam runs one way only.

| Module | What it owns |
|---|---|
| **`hex_field`** (LIB) | the exact-integer field core — `HexSet`, `VecMap`, `trace`/`validate`, `Labels`, `Heights`, `EdgeSet`, `Stencil`. Its gate travels with it; crawler keeps the golden-JSON diff vs the Python oracle as its consumer check |
| `overland.loft` | the contract WILDERNESS (OVERLAND.md §12-13) — vertex/side/corner/edge contracts, zonation → terrain kinds. The depth-0 surface is a 101×101 window of it. `ovmap.loft` prints it as a ZAngband character map |
| `sim.loft` | world/player/enemies, combat (+`sim_bolt`), monster AI (awareness + flow-field pathing), XP/level (`xp_need`), HP/SP pools + regen, statuses, race+class apply (`apply_creation`, cached `rc_*`), the shrine re-spec, unknown-item flavours, stairs/depth, the clock — **and the eight statistics** (table: CATALOG.md §0; gate: `derivetest`) |
| `gen.loft` | procedural dungeon (rooms+corridors), `world_key_seed` |
| `catalog.loft` | the merges: `game_monsters` / `game_items` / `race_catalog` / `class_catalog` |
| `castfx.loft` · `itemfx.loft` | the API layer above the kernel: cast + use-item verbs, dispatching to BUNDLE routines via the generated `spell_defs_gen` / effect arms |
| `ground.loft` | the continuous height sheet the camera stands on and the floor is drawn from — **one construction for both** (`horizontest`). Per-hex ground height is `Sim.theight` (world units, absolute, sea level 0) |
| `worldtex.loft` | the world texture's **CLASS raster** (I-PAINT) — one terrain kind per texel on the lattice, so a hex corner is an exact texel corner. Kernel-side, so it emits **kinds, not colours** |
| `worldmesh.loft` | the kernel-side terrain mesh (hexagon fans, stride 10, R4 tint bake in vertex colours). ⚠ It feeds **`view.loft`, the 2D renderer**, and retires *with its only consumer* in plan #11 P9 |
| `view3d.loft` | the first-person pass (`V` toggles until P9 deletes the 2D view). Floor + wall triangles at **stride 8** = pos(3)/colour(3)/uv(2) — the graphics library's own layout |
| `view.loft` | the egocentric 2D renderer; `Hud` + `build_hud` bake glyphs, HUD and sprites; overlays: char page, inv hub, crystal page. `wallgeo.loft` = wall outline |
| `gameflow.loft` | the deterministic intent seam (K2): `flow_genesis`/`flow_move`/`flow_action` + the S/T/A wire codec. Host applies AND broadcasts, a replica replays → scene_key-identical worlds (`replaytest`). `observe.loft` = the live spectator on :18099 |
| `story.loft` | the entry: the games-kernel HOST (`engine_host::run` — drift-free 60 Hz, idle backoff, observers served the intent log; `game_tick` is the frame, `N` = next world via `genbundles`). `framekey.loft` = the idle-skip scene digest, the ONE chokepoint for stale-frame bugs |
| `scale.loft` | the metres contract (`SCALE.md`), gated by `scaletest` |

**Invariants enforced at one site each — do not add a second:**

- **I-AXIS** — `NUM_STATS` is the only thing that knows the axis count; every layer follows by
  LENGTH. **I-POOL** — a *stored* pool reads only the PERMANENT stat layers (`stat_perm`, never
  `stat_eff`). ⚠ **Speed scales the clock** (`tick_span`, clamped `[0.5×, 2×]` — the clamp is
  what stops a drained stat hanging a `while` loop), read at five sites through that one owner.
- **Two the renderer turns on, and both are load-bearing where they are drawn**: the floor
  follows the **ground reading, not passability** (*rock is ground you cannot walk on, not an
  absence of ground*), so a blocked edge whose blocker is terrain rock emits **no wall quad** —
  *a cliff is not a wall*, the height already draws it at its true size.
  ⚠ **The renderer's own invariants are NOT repeated here** — the uv floor/wall discriminator,
  the per-triangle Lambert term (without which a height field is invisible, because an unlit
  floor is its landcover colour whatever its slope) and `worldtex`'s point-sampling all live in
  the **file headers of `view3d.loft` and `worldtex.loft`**, which carry the measurements too.
  The renderer surface is frozen (ADOPTION.md), so that is the least likely code you will touch
  and the worst place to keep a second copy.

**The geometry-body work lives in the `hexbody` PROJECT** (`../hexbody`, split out 2026-07-23),
not crawler: `housedraw` (buildings in the 12 orientations), gated by its own `make test`, with
`houseshot` the 12-orientation contact sheet. It is the harness where produced geometry stands
in for meshes so a system can be tested before art exists. crawler will consume it once
`stamp_house` becomes a caller; today crawler's game does not use it. Design:
`../hexbody/{VISION,ARCHITECTURE}.md`; the geometry spec is `plans/11-3d-world/BUILDING.md`.
