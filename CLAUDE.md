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
make game     # single-file story.html (WebGL) — currently blocked by E0514
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
- **Follow Angband logic.** Reproduce real Angband (4.2 core + ZAngband wilderness/
  realms) mechanics & numbers; only names/lore are clean-room.
- Every kernel feature gets a headless **`src/<x>test.loft`** wired into `make test`
  (currently 8/8: self, combat, wiring, ai, placement, levels, hero, compile).
  Keep it **warning-clean**.
- **The sandbox can't reliably screenshot** the GL window (`gl_screenshot` under
  Xvfb is positionally off — LOFT_ISSUES C17). Verify *logic* headlessly; the
  **user is the visual verifier**. A `src/shot.loft` aid exists but trust the user.
- Commits: branch **`combat`** (not `main`); end messages with
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`. Push only
  when asked.

## loft survival guide (the interpreter bites — full list + repros: LOFT_ISSUES.md)

Use ONLY these proven-safe shapes when touching vectors/structs:
- Filter a `vector<struct>`: `for i in 0..len(v) { m = v[i] ?? none(); if … { out += [m] } }`.
- Select an element: build the list, then **guarded direct index, no `??`**:
  `if i < len(v) { m = v[i]; … }`. (`v[i] ?? structfn()` can **SIGSEGV** — C1.)
- Prefer **append** (`v += [x]`) over `[for _ in 0..n { … }]` for vectors you index
  later (comprehension reads can return null — C5).
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
