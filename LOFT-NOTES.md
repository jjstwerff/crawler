# LOFT-NOTES.md — the loft toolchain: traps, filing, and where everything lives

Crawler is a **CONSUMER** of loft — we never fix loft here. This file holds the full picture:
the survival guide, the bug-filing procedure, and where the toolchain and libraries sit on
this machine.

**Extracted from `CLAUDE.md` (2026-07-23)** so a session that isn't fighting the toolchain
does not pay ~2.5k tokens for it. `CLAUDE.md` keeps the short list of traps that bite most
often; everything else is here.

---

## Filing loft bugs

**Full procedure + purpose (when/what/where/how, label taxonomy, worked examples):
FILING.md.** Quick version below. **The upstream ROADMAP crawler depends on** (which
`loft-lang/plans` `@PLN<N>` issues block us, feed our prototypes, or explain our idioms —
incl. `@PLN26` = the `make viewer-release` native blocker behind loft#274/#396):
**UPSTREAM-PLANS.md**.

**Findings written up but NOT yet filed live in `LOFT-HANDOFF.md`** — each already in the
issue-body shape (standalone repro + backend matrix + verified workaround + labels), so it
can be filed cold. Check it before re-debugging an upstream trap, and move an entry to its
"Filed" section once opened.

When a loft bug bites: **minimal repro first** (verify on BOTH backends — `--interpret` and
`--check`/`--native`; record expected vs observed; if it won't shrink standalone, file with
the in-crawler recipe, as loft#303/#336 were). **Open a GitHub Issue** with `gh issue create
-R loft-lang/loft` (the bug_report shape: *Minimal reproducer · Expected · Actual*) —
lib-native bugs go to that lib's chunk repo instead. **Labels: exactly one
`sev:high|medium|low`, one `wa:clean|partial|none` (VERIFY the workaround claim), one+
`area:*`, plus `hit-by:crawler`.** Then work around it and keep moving — never block crawler
on a loft fix. The historical C-id map lived in LOFT_ISSUES.md (removed 2026-06-10; all
survivors are now filed upstream).

**Standing grant (2026-06-12): file loft issues for rough spots found on the debugger and the
games kernel proactively** — no per-issue authorization needed; use the filing shape above,
then work around and keep moving.

---

## Survival guide (updated 2026-07-21 — repros live in the filed issues + LOFT-HANDOFF.md)

**Toolchain 2026.7.2 (installed 2026-07-21) = the @PLN110 len/size flip point release** (it
also carries @PLN102 compat-contract work + a wide store-lifetime sweep). The whole gate went
RED on the upgrade and is green again; **two of the three failures were SILENT data
corruption, not compile errors** — that is the lesson to carry.

### INTENDED changes in 2026.7.2

- **fallible float math returns `float?`** — `sqrt`, `pow`, `ln`, `log2`, `log10`, `asin`,
  `acos`, and *variable* `/` and `%` yield a nullable instead of NaN, and it PROPAGATES. A
  **literal** operand known to be in range stays plain `float` (`x / 2.0`, `pow(x, 2.0)`,
  `sqrt(2.0)`) — but `pow(x, 2.1)` is fallible (a negative base with a non-integral exponent
  has no real answer). Upstream calls this a *warning*, but it lands as a hard **error**
  whenever the result is reassigned into an existing `float` variable ("cannot change type
  from float to float?"). Discharge at the ROOT with `?? 0.0` — for `sqrt` of a sum of
  squares that is a provable no-op, never a behaviour change. (Bit
  `overland`/`sim`/`wallgeo`/`meshtest` at 24 sites.)
- **`text as integer|float|single` returns a nullable** — an honest fallible parse (`"oops"
  as integer` is `null`, not a silent `0`). Settle with `?? 0` at the cast.
- **`len(text)` = CHARACTERS, `size(text)` = BYTES** (swapped from earlier 2026.7.x). A
  default-on lint flags `for i in 0..len(s) { s[i] }`. **Verified NOT to affect crawler** (0
  lint hits) — but note `make test` never compiles the view, so re-check
  `view.loft`/`story.loft` by hand if text indexing appears there.
- **a `??` default must match the value's type EXACTLY** — `buf[i] ?? 0.0` on a
  `vector<single>` is now an error. **Write the single literal directly: `?? 0.0f`** (cleaner
  than the older `zz = 0.0 as single` idiom still in worldmesh/gpushot).
- **RELAXED: `return null` from a `-> integer` fn is a WARNING again**, not an error (the
  compat contract). `random`'s `get() -> integer` still returns null and compiles;
  loft-libs-core#14 is no longer a blocker, so the sibling needs no local patch.

### Live traps

- **FIXED — loft#497** (interpreter SIGSEGV consuming a generated Sim): `walltest.loft` runs
  clean, **verified 2026-07-21**. `make play` and `make probe` are NO LONGER blocked by it.
  (`make probe` now needs only `xvfb-run`, which **is installed** on this box.)
- **STILL LIVE — loft#496, in a WIDER form: `vec += [f(struct_temp)]` silently nulls every
  element but the first.** A struct temp reassigned in a loop and passed BY VALUE into a fn
  whose result is appended → the copy is elided to a borrow and freed under the vector.
  **INTERPRETER ONLY — `--native` is correct**, so it is a backend divergence. It corrupted
  every monster spawn (empty names, garbage `mlvl`) and only `depthtest` caught it.
  **Workaround (clean, VERIFIED): hoist the call result into a local first** — `ne =
  mk_enemy(md, q, r); enemies += [ne];`. Hoisting keeps the single call, so RNG order is
  preserved; inlining the call twice does NOT. (Repro + variant matrix: **LOFT-HANDOFF.md →
  H2**.)
- **NEW — a self-referential `??` default SIGSEGVs the COMPILER**: `x = v[i] ?? x;` kills
  `--check` on BOTH backends in 14 lines. Workaround (clean): use a separate fallback
  variable (`x = v[i] ?? fallback;`). (Repro: **LOFT-HANDOFF.md → H1**.)
- **NEW (library, silent) — JSON `kind()` split `JInteger` out of `JNumber`.** Whole numbers
  now report `"JInteger"`; a `kind() == "JNumber"` test falls through to its DEFAULT for every
  integer. This zeroed every dimension in the generated room registry while text fields still
  parsed, so the output looked healthy — `make bundles` is a silent-corruption surface. Test
  BOTH spellings. **Round-trip check: after `make bundles`, the generated `src/*_gen.loft`
  must be byte-identical to HEAD** — the cheapest proof the scanner is intact. (Write-up:
  **LOFT-HANDOFF.md → S1**.)
- **graphics `>=0.5.0` is required** on 2026.7.2 (0.5.0 declares `loft = ">=2026.7.2"`).
  Older 0.3.0 panics in winit ("event loop outside of the main thread") and `make play`
  aborts. 0.5.0 also resolves a relative **font path against the PROGRAM, not the cwd**
  (loft-libs-graphics #255) — build the absolute path from `env_variable("PWD")`, the idiom
  `story.loft` already uses, or the view silently falls back to coloured squares. (Write-up:
  **LOFT-HANDOFF.md → S2/S3**.)
- **Do NOT delete a `?? ""` / `?? 0` guard just because the compiler calls it "Redundant null
  coalescing."** The checker reasons about TYPES; the #496 use-after-free above still makes
  those fields null at RUNTIME. Those guards are load-bearing.

### The older minefield — what still bites

The old C-series is FIXED and re-verified (struct returns, text handling, cross-module `&`,
casts, store pressure, struct-literal comprehensions). What remains:

- **capture-append-reassign on a struct's vector field EMPTIES it** (loft#320: `w = s.v; w +=
  [x]; s.v = w` → len 0; closed upstream). **NOT yet re-verified on 2026.7.2** — treat as live
  until someone runs the shrink. Direct `s.v += [x]` works; the pre-allocated array + count +
  **index-write** idiom (`enemies`/floor-items) stays the default for hot collections.
- **STILL LIVE — a thin arity-reducing pub wrapper around a big-struct-returning pub fn panics
  codegen** (loft#339: "Too few parameters on n_<fn>"): don't wrap; pass the defaulted arg at
  the call sites.
- **STILL LIVE — a `fn(...) -> vector<single>` whose result is passed to a native FFI call**
  (e.g. `graphics::gl_upload_vertices`) **SILENTLY ABORTS the program** (no stdout — even
  earlier `println`s are swallowed — no PNG, exit 0; only a "stores not freed" warning) once
  the real data pipeline is in context (loft#392, `sev:high`; standalone shrinks all pass →
  context-dependent store-lifetime). **Workaround (clean): INLINE the buffer-building loop in
  the caller**, don't route it through a helper that returns `vector<single>`. The silent
  no-diagnostic failure is the trap — if a GL program produces no output and no PNG, suspect
  this.
- `!x` on a **non-boolean is a NULL test, not logical-not** — BY DESIGN (loft C69; an
  always-false warning covers `not null` operands). Compare `== 0`.
- **NEVER swap struct elements of a vector in place via a temp link** (`tmp = v[j]; v[j] =
  v[k]; v[k] = tmp` DUPLICATES v[k] — slot assignment copies into the slot's storage, so the
  held link reads the overwrite). Sort by SELECTION into a fresh vector instead (the overland
  sides corruption; filed as loft#338).
- **NEVER build `vector<text>` literals in large functions** — they can HANG the interpreter;
  indexing one in a call argument can PANIC the allocator (loft#336). Use branch-selector
  functions returning text (`fn key(i) -> text { if ... }`).
  ⚠ **Re-measured 2026-08-09 on 2026.8.0 and NOT cleared.** A synthetic probe (a big
  `vector<text>` literal, indexed in a call argument, in a loop) passes — but the recorded
  trigger is a *large function / deep context*, which the probe does not reproduce, so a
  green probe is not evidence the defect is gone. The workaround therefore **stays**: the
  town-production repertoires in `items.loft` are branch selectors and say so at the top.
  Do not "simplify" them to vectors on the strength of the small probe; if you need this
  lifted, reproduce it in a real deep caller first.
- Manifest `{ path = ... }` deps: **#337 is FIXED** (verified 2026-06-14), so the `--lib` dev
  dirs can now become `{ path = … }` deps in `loft.toml`. **`--lib` outranks the registry**
  (VERIFIED) so a sibling shadows a same-named registry copy. The **#322 stale-program-cache**
  (a `--lib` dep change not invalidating the cache; bust it with `LOFT_NO_CACHE=1`) was an
  0.8.5 bug — **not re-verified on 2026.7.2**. (Full picture: EXTRACTION.md →
  "Library-handling state".)
- **`loft update <pkg>` refreshes the lock AND writes `.loft/api/*.api` stubs** — committed,
  agent-readable `pub` signatures for each dep (loft#362). Commit them: they make the
  out-of-`~/.loft` library APIs visible in-tree.
- Doubled braces `{{`/`}}` in string literals (C14, by design).
- Soak-period habits kept as defense-in-depth (their bugs are fixed, the idioms are still
  good): same-module `&`-mutating helpers; don't hold many large `Sim`s live / consume
  `sim_new_gen(...)` straight into small values; the kernel/view never copy `Sim` by value per
  hit (that one is also perf: the rc_*/wdam cache idiom).

---

## Where moros, the toolchain & the libraries live (this machine, as of 2026-07-21)

All siblings under `/home/jurjens/workspace/`:

- **crawler** — `crawler/` (this repo, branch `combat`).
- **moros** — `moros/` (branch `main`): the 3D target + the **canonical hex convention**:
  *pointy-top, **odd-r offset*** — `x = √3·(col + ½·(row&1))`, `y = 1.5·row` (see
  `tools/build_overworld_map.py`, `data/overworld.json`, `doc/claude/SCENE_MAP.md`).
  Companion repo **`moros_init/`** (branch `master`).
- **loft toolchain source** — two checkouts: **`loft2/` (branch `main`) = daily maintenance &
  bug fixes**, **`loft/` (branch `engine`) = the big / engine projects**. So the installed
  loft tracks `loft2` (the Makefile prune fix + graphics/native fixes were loft2 bug work);
  `make loft-doctor` compares against `../loft2` for that reason.
- **`loft-libs-world/`** — the `hex_*` family (`hex_grid`, `hex_world`, `hex_terrain`,
  **`hex_field`**). **Branch `dev` is the shared working line** (user, 2026-07-22): while the
  stack moves and two projects consume it, work lands there and both projects check that
  branch out — no PR per change until stabilisation, then PR to `main` + register. **`--lib`
  reads the WORKING TREE, so a consumer on the wrong branch silently compiles different
  code** — check the branch before debugging anything strange.
- **library SOURCES** (where the `use`d libs are authored) — **`loft-libs-graphics/`** (the
  `graphics` lib crawler uses, + `glb`/mesh/shapes; branch
  `fix-255-program-relative-font`), `loft-libs-core/`, `loft-libs-net/`.

**Installed loft** (what `make` targets use by default after `make install`):

- binary `/usr/local/bin/loft` (**2026.7.2**, installed 2026-07-21); stdlib
  `/usr/local/share/loft/` (`default/`, `deps/`, `libloft.rlib`, `wasm32-*`). Refresh = `make
  install` in a loft repo (sudo); check with `make loft-doctor`.
- **`graphics` must be `>=0.5.0`** on this toolchain (see above) — the lock pins it and `loft
  update graphics` moves it.

**User library store `~/.loft/`:**

- `registry/` — *built/published* libs **auto-loaded on `use`**: `graphics-0.1.0`,
  `glb-0.1.0`, `gridmesh`, `mesh3d`, `shapes`, `server`, `web` (+ `index.json`). crawler's
  `use graphics` (declared in `loft.toml`) resolves here by default — a sibling `--lib` can
  shadow it (the L0 dev route). The `index.json` is **Ed25519-signed** now (loft#371): once a
  refreshed toolchain embeds the trust keys, `loft install` requires a signed index.
- `build-cache/` — compiled native cdylibs per lib. `lib/` — global `loft install` packages
  (empty now).
- **Native libs are toolchain-free-ish now (loft @PLN21/#370):** a native artifact is a
  loft-ffi-fingerprinted **cdylib**, so **hand-written** native (`graphics`/`random`) is
  rustc-INDEPENDENT (E0514 is auto-native-only); published `prebuilt/<triple>/` cdylibs will
  drop the ~90 s first-use compile entirely. **`.loft/api/<name>.api` stubs** (loft#362): a
  refreshed toolchain's `loft install/update/pin` writes committed, agent-readable `pub`
  signatures for each dep — worth committing so the out-of-`~/.loft` APIs are visible in-tree.
  Details + action items: EXTRACTION.md → "Library-handling state (loft, 2026-06-14)".
