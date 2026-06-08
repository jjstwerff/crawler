# CLAUDE.md — crawler quick reference

Clean-room, ZAngband-style **hex roguelike** written in **loft** (package `story`,
repo `crawler`). 2D today; the *same* renderer-agnostic kernel is meant to drive a
3D/WebGL build later. Full design + roadmap: **DESIGN.md** (backlog = §18a).

## Run / build / test

```sh
make play     # native window (W/S glide, A/D turn, E stairs, . wait, Esc quit)
make test     # headless deterministic gate — RUN THIS before committing
make check    # quiet compile-only gate (parse + bytecode), no display
make shot     # one Xvfb frame -> story.png  (positionally unreliable, see below)
make game     # single-file story.html (WebGL) — unblocked (E0514 resolved, LOFT_ISSUES C15)
```

Direct: `loft --interpret --path ../loft/ --lib ../loft/lib/ src/<f>.loft`
(needs the loft toolchain at `../loft`; `make play LOFT_REPO=…` to override).

## Architecture invariant (do not break)

**Kernel** modules import **no graphics** — `hexgeo`, `gridgeo`, `sim`, `gen`,
`monsters`/`classes`/`races`/`items`. **View** is the swappable 2D front-end —
`view.loft`, `story.loft`. The view reads the kernel only through `sim_*`
accessors. That split is what lets the kernel later drive `moros_render` in 3D, so
keep all `graphics::` calls in `view`/`story` and keep `sim` data-only.

- Hex map, moros geometry (`L = √3`, pointy-top). Continuous player + heading;
  hex-locked enemies. **Distance-driven clock:** every `HEX_LEN` travelled = one
  `sim_tick`; turning is free; `sim_wait` forces one tick in place.

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
- Every kernel feature gets a headless **`src/<x>test.loft`** wired into `make test`
  (currently 8/8: self, combat, wiring, ai, placement, levels, hero, compile).
  Keep it **warning-clean**.
- **The sandbox can't reliably screenshot** the GL window (`gl_screenshot` under
  Xvfb is positionally off — LOFT_ISSUES C17). Verify *logic* headlessly; the
  **user is the visual verifier**. A `src/shot.loft` aid exists but trust the user.
- **2D sprites → the `draw` skill** (method: loft `.claude/skills/draw`; **tool:
  crawler's own `tools/draw.py`** — copied from the skill's `sketch/draw.py` and
  extended: `Background transparent` now, rotation/atlas next. Built to be extractable
  as a **reusable 2D sprite library** — 3D/moros is the goal, but the 2D stack stands
  on its own for 2D-preferring devs): used to author the game's **simple 2D sprites** — the mob/item
  presentations (and other 2D art), upgrading the text-glyph placeholders. **2D only —
  we do not rely on the 3D path.** Workflow: iterate a sprite with the skill (it
  outputs a PNG to a tmp dir + a cheap text report), then copy the final PNG into
  `assets/` for the game to load as a texture and composite where the glyph was. The
  PNG output is reviewable, so Claude *can* self-critique the sprite (the loop closes
  here); the **user still verifies how it composites in the live frame**. Also handy
  for setting a visual target (wall aesthetic, palette). Not the runtime renderer; not
  for HUD/UI layout.
- **Sprite done-criterion — real-world, verifiable forms.** Ground each sprite in a
  real-world creature/object (a spider, an ant, …) and **stop when a *cold read* names
  it uniquely** as that form ("spider", not "some bug") — unique recognizability is
  "finished for the game"; don't over-render past it (clarity has an optimum). It's
  verifiable (the draw skill's recognition critic runs the test) and clean-room (real
  forms, not IP creatures). **Monsters also need a visible *legitimate attack means*** (a
  biter shows fangs, a clawer shows claws) matching its combat — no pass without it;
  and all monster sprites use a **locked orientation: attack/front = up**, uniform
  across monsters (never varies per monster) — authored facing **up** so the engine can
  **rotate** each sprite to the monster's movement/facing at runtime (uniform up-authoring
  is what makes that clean). **Mood/affect is out of scope** — run
  only the *recognition* critic (+ the attack + orientation checks); per-token feeling
  isn't evaluated (atmosphere comes from the scene / light / audio, not the icon).
  *(3D — out of scope for now — would extend this with
  **scale + proportion** checks via the metric/multi-view channel; 2D sprites need
  only the unique-recognition test.)*
- **Readability + palette — dark monsters on a light floor.** Floor is **light** — warm
  **yellowish aged stone** (original Roman granite/travertine, *not* modern pure-white)
  — walls **dark-toned**, monsters/tokens are **almost-black silhouettes** (the menacing,
  high-attention look) read against the light floor. **Colour is reserved for clothed /
  armoured creatures**; plain creatures are near-black. **No internal light/dark
  patterns** on a monster (out of scope) — detail reads by *silhouette shape* (a
  spider's fangs are points in the outline, not pale marks; no pale eyes). The current
  bright glyphs become **dark**, and the soft-black token disc is **dropped** (a dark
  token reads on the light floor; a dark disc would bury it). **Critique sprites on a
  light background (the floor), not dark.**
- **Sprite scale = the creature's body, not its box.** Size a creature by its **core
  mass** relative to the existing player/enemy scale; thin appendages (legs, antennae,
  tail) count *less* and may **overhang** the cell. A wide-legged spider is sized by
  its body — the legs spill past the footprint, not shrink the body to fit the box.
- **Sprite QA — two tiers + test-driven redraw.** (1) *Recognition* (above) — Claude
  judges it per-sprite at authoring time from the PNG. (2) *Theme coherence* — does it
  fit the set's overall look — is judged **in-game during playtesting** (the user's
  call; it only shows in context). Flagged off-theme sprites get **adjusted/redrawn**.
  Keep the editable `.draw` sources in `assets/sprites/src/` so a redraw is a quick
  edit + re-render, not from scratch.
- Commits: branch **`combat`** (not `main`); end messages with
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Push only
  when asked.

## loft survival guide (the interpreter bites — full list + repros: LOFT_ISSUES.md)

Use ONLY these proven-safe shapes when touching vectors/structs:
- Filter a `vector<struct>`: `for i in 0..len(v) { m = v[i] ?? none(); if … { out += [m] } }`.
- Select an element: build the list, then **guarded direct index, no `??`**:
  `if i < len(v) { m = v[i]; … }`. (`v[i] ?? structfn()` can **SIGSEGV** — C1.)
- **Never grow a struct's vector field at runtime** (`s.v += [x]` and
  capture-append-reassign both desync — C18). For a growable collection on the
  `Sim`, pre-allocate a fixed array (`zeros(N)`) + an integer count and
  **index-write**, exactly like `enemies` / floor-items: `n = s.fi_n; v = s.fi_q;
  v[n] = q; s.fi_n = n + 1`. Index-writes on a captured field vector persist;
  integer `+=` on a field persists; append / whole-field reassign don't.
- Keep a **`&Struct`-mutating helper in the same module** as its callers
  (cross-module `&` mutation is lost — C4; e.g. `sim` has its own `SimRng`).
- `!x` on an **integer is not logical-not** — compare `== 0` (C6). No chained `as`
  casts (split them — C7). `false ?? x` is unreliable; use int flags (C10). Doubled
  braces `{{`/`}}` in strings (C14). A `println` can change results — don't trust
  print-debugging blindly (C2).

## Where things are

- `sim.loft` — world/player/enemies, combat, monster AI (awareness + flow-field
  pathing), XP/level (`sim_award_xp`), stairs/depth (`sim_descend`), the clock.
- `gen.loft` — procedural dungeon (rooms+corridors), `world_key_seed`.
- `view.loft` — egocentric renderer; `Hud` + `build_hud` bake glyph/HUD textures
  (font in `assets/`; reached as `../story/assets/…` — gl_load_font resolves vs the
  `--path` root, C8). `wallgeo.loft` — wall outline (rounded; DP straightener parked
  in `patches/`).
