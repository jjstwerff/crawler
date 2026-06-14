# CLAUDE.md — crawler quick reference

Clean-room, ZAngband-style **hex roguelike** written in **loft** (package `story`,
repo `crawler`). **The 2D game is first-class and complete in its own right** (some
players prefer 2D) — *most of the design lives on the 2D plane* (DESIGN §7a); the *same*
renderer-agnostic kernel also drives an **optional** 3D/WebGL build added for those who
want it (3D is additive, not the destination). Full design + roadmap: **DESIGN.md**
(backlog = §18a).

## Run / build / test

```sh
make play     # native window (W/S glide, A/D turn, walk onto stairs, . wait, g grab, N next world, Esc quit)
make test     # headless deterministic gate — RUN THIS before committing
make check    # quiet compile-only gate (parse + bytecode), no display
make shot     # one Xvfb frame -> story.png  (positionally unreliable, see below)
make probe    # pixel-probe gate: Xvfb renders + tools/probe.py asserts probes/*.probe
make bundles  # re-scan bundles/*/bundle.json -> the generated registries (loft scanner)
make game     # single-file story.html (WebGL) — unblocked (the E0514 rustc-mismatch is resolved)
```

Direct: `loft --interpret --path ../loft/ --lib ../loft/lib/ src/<f>.loft`
(needs the loft toolchain at `../loft`; `make play LOFT_REPO=…` to override).

## Design / debug protocol (exact-invariant work)

For **geometry / caching / serialization / store-lifetime / protocols** the correct
design is an **exact invariant**, not an open space. Don't approximate or symptom-chase
toward it. Run a **BLUEPRINT PHASE before implementing — don't jump the gun:** suss the
design out through *verifiable steps* in the **cheapest medium** (a throwaway Python
prototype, a round-trip test) and don't write the real code until each step checks out —
the cheap prototype is often where the design gets *pinned*, not just confirmed (the
triangle wall was only pinpointable **after** a Python verify phase, *then* ported to loft).
Step 1 is a **CONCRETE plotted end-result** (the exact target output/state for one specific
input — the model grasps concrete examples far better than abstract specs; ask the user to
plot it, or propose a candidate and confirm); **then** name the invariant (caching →
*round-trip = identity*), **pin each step**, and only then code. Tell that this went wrong:
*a small fix behind a large discovery cost* (the triangle-wall saga; the loft2 `data.rs`
cache fix). Anchor (Angband/real/moros) + reuse one model by symmetry. Case log + mechanism
study (growing, → enhance the engineering-rigor skill's DESIGN column): **DESIGN-PROTOCOL.md**.

## Architecture invariant (do not break)

**Kernel** modules import **no graphics** — the `hex_grid` LIB (was hexgeo+gridgeo;
now `loft-lang/loft-libs-world`), `sim`, `gen`, `worldmesh`, `wallgeo`,
`framekey`, `gameflow`, `genbundles`, `monsters`/`classes`/`races`/`items`. **View** is the swappable 2D front-end —
`view.loft`, `story.loft`. The view reads the kernel only through `sim_*`
accessors. That split is what lets the kernel later drive `moros_render` in 3D, so
keep all `graphics::` calls in `view`/`story` and keep `sim` data-only.

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
  (currently 39 — combat/AI/placement/levels/hero/items/equip/bundles/defs/quests/
  msg/inv-hub/effects/specials/unknown-items/races/classes/crystal/overland/
  idle-skip/mesh/kernel/replay/…). Keep it **warning-clean**. Pixel-level render checks live in
  **`make probe`** (Xvfb + `tools/probe.py` vs `probes/*.probe` — PLAN-RENDER P0).
  The games-kernel adoption track (@PLN18 engine_host): **PLAN-KERNEL.md**.
- **The sandbox can't reliably screenshot** the GL window (`gl_screenshot` under
  Xvfb is positionally off — a known test-env quirk). Verify *logic* headlessly; the
  **user is the visual verifier**. A `src/shot.loft` aid exists but trust the user.
- **2D sprites → the `draw` skill** (method: loft `.claude/skills/draw`; **tool:
  crawler's own `tools/draw.py`** — copied from the skill's `sketch/draw.py` and
  extended: `Background transparent`, `--once` (render-and-exit; exit 1 on unparsed lines /
  failed checks — agent/CI use) + unparsed-line reporting, and the `Petals`/`Fronds` ARRAY
  primitives (radial + linear natural marks — non-uniform + construction-hiding by default;
  designs pinned in `tools/{petal,fronds}_blueprint.py`); rotation/atlas next. Built to be extractable
  as a **reusable 2D sprite library** — 3D/moros is the goal, but the 2D stack stands
  on its own for 2D-preferring devs): used to author the game's **simple 2D sprites** — the mob/item
  presentations (and other 2D art), upgrading the text-glyph placeholders. **2D only —
  we do not rely on the 3D path.** Workflow: iterate a sprite with the skill (it
  outputs a PNG to a tmp dir + a cheap text report), then copy the final PNG into
  `assets/sprites/` — **the view resolves sprites BY NAME, no code per sprite**:
  a monster loads `<monster_key>.png` (+ optional `<key>_gaze.png` ACTION variant, shown in
  striking contact), the player `player.png`, floor loot per-category (`sword.png`,
  `potion.png`, … see `cat_sprite_name`), gold `gold_pile.png`; a missing file falls back
  to the glyph. Drop the PNG in and it's in the game. The
  PNG output is reviewable, so Claude *can* self-critique the sprite (the loop closes
  here); the **user still verifies how it composites in the live frame**. Also handy
  for setting a visual target (wall aesthetic, palette). Not the runtime renderer; not
  for HUD/UI layout.
- **Sprite done-criterion — real-world, verifiable forms, MENACING.** Ground each sprite in
  a real-world creature/object (a spider, an ant, …) and **stop when a *cold read* names
  it uniquely** as that form ("spider", not "some bug") — unique recognizability is
  "finished for the game"; don't over-render past it (clarity has an optimum). **Monsters
  must read as a THREAT, never cute** (cute is valuable elsewhere — not here): hunched/
  lunging posture, jagged-spiky outlines over smooth rounds, the weapon feature LARGE
  (fangs/claws/stinger), mean or glowing eye-glints, gritty darker tones. It's
  verifiable (the draw skill's recognition critic runs the test) and clean-room (real
  forms, not IP creatures). **Monsters also need a visible *legitimate attack means*** (a
  biter shows fangs, a clawer shows claws) matching its combat — no pass without it;
  and all monster sprites use a **locked orientation: attack/front = up**, uniform
  across monsters (never varies per monster) — authored facing **up** so the engine can
  **rotate** each sprite to the monster's movement/facing at runtime (uniform up-authoring
  is what makes that clean). **Mood/affect is out of scope** — run
  only the *recognition* critic (+ the attack + orientation checks); per-token feeling
  isn't evaluated (atmosphere comes from the scene / light / audio, not the icon).
  **A STILL + an ACTION version is allowed** — especially for enemies without much other
  expression (the floating eye: idle ball vs. gaze-rays firing); the action sprite shows
  the attack happening, the still keeps the threat readable.
  **PERSPECTIVE rules (the world is top-down):** creatures + structural features are drawn
  top-down, with **slight foreshortening allowed** to show the third dimension (the eye's
  iris as a front-displaced ellipse; the door as its lit top edge + a foreshortened face)
  as long as the feature stays inside its slot (the door within the wall gap). **An upright
  HUMANOID from above shows its SCALP + protruding snout — never a camera-facing face**;
  eyes at most as side-hints at the snout root. (Quadrupeds' horizontal heads legitimately
  show eyes from above — the jackal model; the player shows hair only.) **Items may
  be frontal-iconic** — they read as lying on the floor, the illusion holds. Stairs are
  the floor-hole exception (down = a black cube's top opening, steps descending inside it;
  up keeps transparent gaps — floor shows under a rising flight). **A feature that sits IN
  the wall carries NO architecture of its own** (no jambs/frame — the engine's wall
  renders that; a sprite's own stonework clashes).
  *(3D — out of scope for now — would extend this with
  **scale + proportion** checks via the metric/multi-view channel; 2D sprites need
  only the unique-recognition test.)*
- **Readability + palette — natural-coloured monsters on a light floor.** Floor is **light**
  — warm **yellowish aged stone** (original Roman granite/travertine, *not* modern
  pure-white) — walls **dark-toned**, monsters read as **dark-toned shapes in their
  creature's NATURAL colours** (a brown rat is brown, a sand adder sandy; the cave spider
  is near-black only because real cave spiders are). Detail still reads primarily by
  *silhouette shape* (fangs are points in the outline); keep tones dark enough to carry
  on the light floor. The soft-black token disc is **dropped** for sprites (a dark shape
  reads on the light floor; a disc would bury it). **Critique sprites on a light
  background (the floor), not dark.**
- **Sprite scale = the creature's body, not its box.** Size a creature by its **core
  mass** relative to the existing player/enemy scale; thin appendages (legs, antennae,
  tail) count *less* and may **overhang** the cell. A wide-legged spider is sized by
  its body — the legs spill past the footprint, not shrink the body to fit the box.
- **Sprite QA — two tiers + test-driven redraw.** (1) *Recognition* (above) — Claude
  judges it per-sprite at authoring time from the PNG. (2) *Theme coherence* — does it
  fit the set's overall look — is judged **in-game during playtesting** (the user's
  call; it only shows in context). Flagged off-theme sprites get **adjusted/redrawn**.
  Keep the editable `.draw` sources in `assets/sprites/src/` (IN the repo) — both so a
  redraw is a quick edit + re-render, and as a growing **technique library**: when a
  similar creature is needed later, fall back on the existing sources for their
  *constructions* (jointed tapered legs, eye-glints, body-mass proportions) — not 1-on-1
  copies, but the techniques are the value. **When reusing/redrawing parts, always check
  the JOINS**: a new part must align + scale to the kept ones or it reads bolted-on —
  bury a part's joint corners inside the neighbouring mass, bridge with an intermediate
  shape/tone (e.g. a skull circle between shoulders and muzzle), and run connecting
  features (a spine ridge) ACROSS the joint to tie the parts together.
- **Reference drawings — draw AGAINST real form + real mark-making.** `assets/sprites/ref/`
  holds a small fixed set of public-domain plates (Dürer's hare = canonical fur; the
  *Canis mesomelas* / *Mus decumanus* prints = the exact species our jackal/rat model;
  Van Gogh reed-pen + Rembrandt for foliage/terrain marks) plus pointers to the open
  corpora (BHL, Smithsonian, Rijksstudio, Met/NGA open access, Ruskin/Pennell). Open the
  matching plate beside the `.draw` source and compare region-by-region. The recurring
  lesson our fur hasn't taken yet: **texture lives in the broken silhouette edge + the
  value gradient, not as strokes floating inside a smooth outline** — see
  `assets/sprites/ref/README.md` for what each teaches and how to extend the set.
- **Docs-first knowledge capture (user rule, 2026-06-12): anything memory-worthy
  goes into the appropriate repo doc** (RENDER/PLAN-*/EXTRACTION/BUNDLE/this file)
  — agent memory holds only pointers. The repo is the shared brain; private notes
  must not be the sole home of project knowledge.
- **Standing grant (2026-06-12): file loft issues for rough spots found on the
  debugger and the games kernel proactively** — no per-issue authorization needed;
  use the filing shape below (one sev:*, one VERIFIED wa:*, area:*, hit-by:crawler),
  then work around and keep moving.
- Commits: branch **`combat`** (not `main`); end messages with
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Push only
  when asked.

## Filing loft bugs (crawler is a CONSUMER — we never fix loft here)

When a loft bug bites: **minimal repro first** (verify on BOTH backends — `--interpret`
and `--check`/`--native`; record expected vs observed; if it won't shrink standalone,
file with the in-crawler recipe, as loft#303/#336 were). **Open a GitHub Issue** with
`gh issue create -R loft-lang/loft` (the bug_report shape: *Minimal reproducer ·
Expected · Actual*) — lib-native bugs go to that lib's chunk repo instead. **Labels:
exactly one `sev:high|medium|low`, one `wa:clean|partial|none` (VERIFY the workaround
claim), one+ `area:*`, plus `hit-by:crawler`.** Then work around it (a loft-safe shape
below) and keep moving — never block crawler on a loft fix. The historical C-id map
lived in LOFT_ISSUES.md (removed 2026-06-10; all survivors are now filed upstream).

## loft survival guide (updated 2026-06-11 — repros live in the filed issues)

The old C-series minefield is FIXED and re-verified (struct returns, text handling,
cross-module `&`, casts, store pressure, struct-literal comprehensions). What still bites:
- **STILL LIVE in the installed 0.8.5 — capture-append-reassign on a struct's vector field
  EMPTIES it** (loft#320: `w = s.v; w += [x]; s.v = w` → len 0; closed upstream, re-verify
  after the next toolchain refresh). Direct `s.v += [x]` works; the pre-allocated array +
  count + **index-write** idiom (`enemies`/floor-items) stays the default for hot collections.
- **STILL LIVE — a thin arity-reducing pub wrapper around a big-struct-returning pub fn
  panics codegen** (loft#339: "Too few parameters on n_<fn>"): don't wrap; pass the
  defaulted arg at the call sites.
- `!x` on a **non-boolean is a NULL test, not logical-not** — BY DESIGN (loft C69; an
  always-false warning covers `not null` operands). Compare `== 0`.
- **NEVER swap struct elements of a vector in place via a temp link** (`tmp = v[j];
  v[j] = v[k]; v[k] = tmp` DUPLICATES v[k] — slot assignment copies into the slot's
  storage, so the held link reads the overwrite). Sort by SELECTION into a fresh
  vector instead (the overland sides corruption; filed as loft#338).
- **NEVER build `vector<text>` literals in large functions** — they can HANG the
  interpreter; indexing one in a call argument can PANIC the allocator (loft#336).
  Use branch-selector functions returning text (`fn key(i) -> text { if ... }`).
- Manifest `{ path = ... }` deps are NOT compile-time resolved on the installed 0.8.5
  (loft#337) — consume local packages via `--lib` dirs or sibling layout (the EXTRACTION.md
  dev route). **#337 is FIXED in the 2026-06 loft (verified 2026-06-14)** — after the
  toolchain refresh, the `--lib` dev dirs can become `{ path = … }` deps in `loft.toml`. **`--lib` outranks the registry** (VERIFIED) so a sibling shadows a same-named
  registry copy — BUT 0.8.5's **#322 stale-program-cache** doesn't invalidate when a `--lib`
  dep changes, so it keeps the old binding until you bust the cache (`LOFT_NO_CACHE=1`) or
  refresh past the #322 fix. (Full picture: EXTRACTION.md → "Library-handling state".)
- Doubled braces `{{`/`}}` in string literals (C14, by design).
- Soak-period habits kept as defense-in-depth (their bugs are fixed, the idioms are still
  good): same-module `&`-mutating helpers; don't hold many large `Sim`s live / consume
  `sim_new_gen(...)` straight into small values; the kernel/view never copy `Sim` by value
  per hit (that one is also perf: the rc_*/wdam cache idiom).

## Library extraction (the reusable-library goal made concrete)

Routines that serve other games get PUSHED to the library layer — plan + tiers + per-package
Definition of Done: **EXTRACTION.md** (hexgrid = the canonical moros-convention hex geometry,
text-layout helpers → graphics, draw.py flow-back → the skill, a seeded `random` package;
wallgeo/gen after one decoupling each; roguelike-kit + the bundle system deliberately gated).

## Where moros, the toolchain & the libraries live (this machine, as of 2026-06-09)

All siblings under `/home/jurjen/workspace/`:
- **crawler** — `crawler/` (this repo, branch `combat`).
- **moros** — `moros/` (branch `main`): the 3D target + the **canonical hex convention**:
  *pointy-top, **odd-r offset*** — `x = √3·(col + ½·(row&1))`, `y = 1.5·row` (see
  `tools/build_overworld_map.py`, `data/overworld.json`, `doc/claude/SCENE_MAP.md`).
  Companion repo **`moros_init/`** (branch `master`).
- **loft toolchain source** — two checkouts: **`loft2/` (branch `main`) = daily maintenance
  & bug fixes**, **`loft/` (branch `engine`) = the big / engine projects**. So the installed
  loft tracks `loft2` (the Makefile prune fix + graphics/native fixes were loft2 bug work);
  `make loft-doctor` compares against `../loft2` for that reason.
- **library SOURCES** (where the `use`d libs are authored) — **`loft-libs-graphics/`** (the
  `graphics` lib crawler uses, + `glb`/mesh/shapes; branch `fix-255-program-relative-font`),
  `loft-libs-core/`, `loft-libs-net/`.

**Installed loft** (what `make` targets use by default after `make install`):
- binary `/usr/local/bin/loft` (0.8.5); stdlib `/usr/local/share/loft/` (`default/`, `deps/`,
  `libloft.rlib`, `wasm32-*`). Refresh = `make install` in a loft repo (sudo); check with
  `make loft-doctor`.

**User library store `~/.loft/`:**
- `registry/` — *built/published* libs **auto-loaded on `use`**: `graphics-0.1.0`,
  `glb-0.1.0`, `gridmesh`, `mesh3d`, `shapes`, `server`, `web` (+ `index.json`). crawler's
  `use graphics` (declared in `loft.toml`) resolves here by default — a sibling `--lib` can
  shadow it (the L0 dev route). The `index.json` is **Ed25519-signed** now (loft#371): once a
  refreshed toolchain embeds the trust keys, `loft install` requires a signed index.
- `build-cache/` — compiled native cdylibs per lib. `lib/` — global `loft install` packages (empty now).
- **Native libs are toolchain-free-ish now (loft @PLN21/#370):** a native artifact is a
  loft-ffi-fingerprinted **cdylib**, so **hand-written** native (`graphics`/`random`) is
  rustc-INDEPENDENT (E0514 is auto-native-only); published `prebuilt/<triple>/` cdylibs will
  drop the ~90 s first-use compile entirely. **`.loft/api/<name>.api` stubs** (loft#362): a
  refreshed toolchain's `loft install/update/pin` writes committed, agent-readable `pub`
  signatures for each dep — worth committing so the out-of-`~/.loft` APIs are visible in-tree.
  Details + action items: EXTRACTION.md → "Library-handling state (loft, 2026-06-14)".

## Where things are

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
