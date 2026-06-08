# loft — known issues found while building `crawler`

Issues hit while writing the **crawler** roguelike (`../story`, pure-loft kernel:
hex sim, procedural generation, monster AI/placement) against the loft
**interpreter** (`loft --interpret`). Logged so they can be triaged/fixed
efficiently. Each entry has a minimal repro, expected vs. actual, the workaround
in use, and severity.

- Observed against loft branch `debugging` @ `5745a2c2` (and earlier on `main`).
- Run mode: `loft --interpret --path <repo>/ --lib <repo>/lib/ file.loft`.
- Most are **interpreter** bugs; a couple are parser/codegen or doc gaps.
- Several cause **silent wrong results** (not just crashes) — those are the
  expensive ones and are marked HIGH.

Severity: **HIGH** = silent wrong behaviour or crash on ordinary code ·
**MED** = wrong/footgun but localized · **LOW** = parse error or doc gap.

> This file lives in the **crawler** repo (the loft program that found the bugs)
> so each fix can be verified against real game code. As loft changes land, flip
> the **Status** below and note the fixing commit; the repro for each issue is
> the linked section.
>
> **Upstreamed 2026-06-03** to `jjstwerff/loft` (tagged `hit-by:crawler`): the
> cleanly-minimal new bugs filed as issues; the HIGH "silent / emergent" ones
> (C1–C5, C18) couldn't be isolated to a minimal repro and overlap the existing
> store-lifetime issue **#248**, so they're attached there as a comment rather
> than as un-repro-able dups.
>
> **Re-verified 2026-06-03** (current loft): **C9 fixed**, **C11 no longer
> reproduces**, **C12 fixed**, and **C15 (E0514) resolved** — the native `--check`
> gate runs again, so the WebGL build is unblocked. The still-live **C10**
> (boolean `??`) and **C13** (`&ref`→local codegen panic) were filed (#256/#257).
> C14/C16/C17 are by-design/environment and not refiled.

## How to file a loft issue (crawler is a CONSUMER — we never fix loft)

loft has its own fix workflow. From **crawler** we are a downstream consumer: when we
hit a loft bug we **file it and work around it** — we do **not** fix loft here. The
procedure (loft's `ISSUE_TRACKING.md` / `CLAUDE.md § Bug-filing`, applied from a
consumer):

1. **Minimal repro first** (engineering-rigor: boundary matrix → shrink to the
   smallest example; the bug often *is* the coexistence of N constructs — stop
   shrinking there). Verify on **both backends** — `loft --interpret` **and**
   `loft --check`/`--native` — and record **expected vs observed for each**. Save the
   repro (`/tmp/p_followups/<name>.loft` or a regression). **Don't file a
   half-localized cause:** no minimal repro → keep shrinking, or attach it as a
   *comment* on the closest existing issue (as C1–C5/C18 → loft#248), not a new dup.

2. **Open a GitHub Issue — NOT a `PROBLEMS.md` row** (PROBLEMS.md is loft's
   closed/historical archive). `gh issue create -R <repo>` with the **`bug_report`**
   template (fields: *Minimal reproducer · Expected · Actual*). File in the repo
   **where the source fix lands**: a loft language/interpreter/codegen/store/stdlib
   bug → **`loft-lang/loft`** (we've used `jjstwerff/loft`); a published-lib native bug
   → that library's chunk repo (`loft-lang/loft-libs-<chunk>`). **Never record the
   origin commit** — scope (what triggers it) + present-code root cause are what fix it.

3. **Labels — exactly one `sev:`, one `wa:`, one+ `area:`, plus `hit-by:crawler`:**
   - `sev:high` (crash / corruption / soundness) · `sev:medium` (wrong result / hang) ·
     `sev:low` (cosmetic / false warning).
   - `wa:clean` / `wa:partial` / `wa:none` — **verify the workaround claim** (a wrong
     one is worse than `wa:none`; `wa:none` = blocked = top triage axis, often above sev).
   - `area:store-lifetime` (heap / store / hash desync) · `area:codegen` · `area:parser`
     · `area:runtime` · `area:native` · `area:wasm` · `area:stdlib` · `area:packages`
     · `area:closures`.

4. **Record it here** — add/keep the C-series row with the repro + the filed
   `loft#NNN`, and flip **Status** when it lands. This file is crawler's map from our
   C-ids to the filed issues.

5. **Then work around it** (a loft-safe shape — see CLAUDE.md survival guide) and keep
   moving. Never block crawler on a loft fix.

*(Status of the open wallgeo DP-straightener panic: clean workaround exists — the
active version + the line-intersection approach — so it's `wa:clean`, not blocking;
**not yet filed** because there's no minimal repro yet, P1/P2 synthetic probes pass.
Keep shrinking before filing.)*

### Status tracker

| ID  | Title | Sev | Status |
|-----|-------|-----|--------|
| C1  | `vector<struct>[i] ?? structfn()` SIGSEGV | HIGH | → loft#248 (comment; emergent, no min repro) |
| C2  | `println` changes results (Heisenbug) | HIGH | → loft#248 (comment) |
| C3  | struct copy drops a `text` field | HIGH | → loft#248 (comment) |
| C4  | cross-module `&Struct` mutation lost | HIGH | → loft#248 (comment) |
| C5  | comprehension-built vector reads null | MED | store-lifetime family (not filed) |
| C6  | `!` on an integer is not logical-not | MED | **filed loft#253** |
| C7  | chained `as` casts don't parse | LOW | **filed loft#254** |
| C8  | `gl_load_font` relative-path base | LOW | **filed loft#255** |
| C9  | native: `return let mut …` invalid Rust | HIGH | **FIXED** (re-verified — compiles native) |
| C10 | boolean `?? fallback` unreliable | MED | **filed loft#256** (re-verified) |
| C11 | struct-field vector index returns null | MED | not reproduced (re-verified — fixed / was emergent) |
| C12 | `&vector<T>` param doesn't parse | LOW | **FIXED** (re-verified — parses + mutates) |
| C13 | copy `&ref` to local panics codegen | HIGH | **filed loft#257** (re-verified — both backends) |
| C14 | literal `{`/`}` in strings must double | LOW | by-design (language) — not a bug |
| C15 | `E0514` prebuilt-rlib rustc mismatch | env | **RESOLVED** (native `--check` runs; web build unblocked) |
| C16 | GL 2D depth-test / no default blend func | doc | by-design — not filed |
| C17 | `gl_screenshot` unreliable under Xvfb | n/a | test-env — not filed |
| C18 | runtime append to a struct-field vector unreliable | HIGH | → loft#248 (comment; emergent) |
| C19 | `hash<K[k]>` lookup keys.rs index-OOB under store pressure (wallgeo DP build) | HIGH | **filed loft#290** (`wa:clean` — line-intersection walls) |

Existing upstream issues that overlap our family (for reference): **#248**
(constructor-return → CONST_STORE → read-only write), **#250** (nested-vector
3-deep store OOB), **#246** (`vv[0] += [9]` nested-element compound-assign).

---

## C1 — `vector<struct>[i] ?? structfn()` SIGSEGVs the interpreter  · HIGH

Indexing a vector **of structs** with a `??` fallback that calls a
struct-returning function, inside a loop, crashes:

```loft
fn pick(table: vector<MonsterDef>) -> MonsterDef {
  chosen = mon_none();
  for wi in 0..len(table) {
    m = table[wi] ?? mon_none();       // <-- SIGSEGV (op=165) after some iterations
    if m.m_hp > 0 { chosen = m; }
  }
  chosen
}
```

```
=== loft crash (loft) SIGSEGV caught ===
  last op:  (opcode dispatch) (op=165)
  at:       .../monsters.loft:148:10      (the `table[wi] ?? mon_none()` line)
```

- **Expected:** read element, or fall back to `mon_none()` if null.
- **Actual:** hard SIGSEGV mid-loop. Crashes from *any* module, including the
  one that defines the struct.
- **Confusing wrinkle:** a *nearly* identical function (`mon_for_depth`, same
  `m = table[mi] ?? mon_none()` line but a different/smaller loop body that does
  `out += [m]`) does **not** crash — so it's sensitive to surrounding ops / how
  the result is used, which smells like stack/slot corruption rather than a clean
  null-deref.
- **Workaround:** never use `v[i] ?? structfn()` on a struct vector. Either
  build the filtered list with the `mon_for_depth` shape (`out += [m]`), or read
  with a **guarded direct index, no `??`**: `if i < len(v) { m = v[i]; ... }`.

## C2 — `println` changes computed results (Heisenbug)  · HIGH

Adding/removing a `println` flips a function between correct and wrong output,
with **no change to RNG draw order** (println consumes no RNG):

```loft
res = mon_none();
if len(pool) > 0 {
  bi = weighted_idx(pool, rng);
  best = pool[bi] ?? mon_none();        // index-into-built-vector + struct ??
  // ...deepen loop re-indexes pool[ti] ?? mon_none() ...
  res = best;
}
```

- With an unconditional `println("...{len(pool)}...")` at the top of the
  function, `pool` was 16 and a valid monster was returned on **every** call.
- With that `println` removed, the **3rd and later** calls returned
  `mon_none()` (m_hp 0) — even though `len(pool)` was still 16.
- **Impact:** debugging by print is unreliable here; the print *hides* the bug.
- Likely same root cause as **C1** (the `pool[bi] ?? mon_none()` struct-index +
  fallback form). Rewriting selection to avoid that form (see C1 workaround) made
  it deterministic and correct.

## C3 — struct copy intermittently drops a `text` field  · HIGH

Passing a struct through a chain of copies
(`table[i] → local → out += [m] → pool[j] → local → return → assign`) read the
**`text`** field back as `""` for ~1 element in N, while **integer** fields in the
same struct were intact.

- Concretely: a `MonsterDef` selected through `mon_pool → mon_one → mon_choose`
  arrived at the call site with `m_hp/m_dam/m_cr` correct but `m_glyph == ""`.
- Shorter copy chains (one `mon_for_depth` + one guarded index) did **not** lose
  the field.
- **Expected:** struct copies are total (all fields, incl. `text`).
- **Workaround:** re-validate/default the text field after the chain
  (`g = md.m_glyph; if len(g)==0 { g = "?" }`).

## C4 — cross-module `&Struct` mutation is lost  · HIGH

A `pub fn` taking `&Struct` and mutating a field works **within its own module**
but the mutation **does not propagate** when called from another module.

```loft
// gen.loft
pub struct Rng { rs: integer not null }
pub fn rng_seed(s: integer) -> Rng { Rng { rs: (s & MASK) | 1 } }
pub fn rng_range(r: &Rng, lo: integer, hi: integer) -> integer {
  r.rs = (r.rs * 1103515245 + 12345) & MASK;   // mutate
  lo + (r.rs % (hi - lo + 1) ?? 0)
}
```

```loft
// sim.loft  (different module)
rng = rng_seed(123);
a = rng_range(rng, 0, 99);
b = rng_range(rng, 0, 99);   // a == b — rng never advanced!
```

- **Within gen.loft**, the same `rng_range` advances correctly (dungeon layout
  varies). **From sim.loft**, `rng.rs` is never updated → constant output.
- **Symptom in the wild:** a placement loop "placed" only one distinct monster
  (the RNG was stuck), everything else deduped away.
- **Workaround:** keep the mutating `&Struct` helper **and its callers in the
  same module** (I duplicated a tiny LCG into `sim.loft`).

## C5 — comprehension-built vector reads back null  · MED

A vector built with a `[for _ in 0..n { 0 }]` comprehension (runtime `n`) read
back **null** at valid indices:

```loft
used: vector<integer> = [for _ in 0..ncand { 0 }];
// ...
x = used[k];        // null, not 0  → (used[k] ?? 1) == 1, not 0
```

- **Expected:** every slot is `0`.
- **Actual:** indexed reads returned null (so `?? 1` fallbacks fired), breaking a
  "visited" marker. **Append-built** vectors (`v += [x]`) read fine.
- Likely the same family as the long-standing "struct-field vector read returns
  null" gotcha.
- **Workaround:** avoid comprehension-built marker vectors; here I dropped the
  marker and deduped a different way.

## C6 — `!` on an integer is not logical-not  · MED

```loft
font = gl_load_font("missing.ttf");   // returns 0
if !font { println("not loaded"); }   // branch NOT taken when font == 0
```

- **Expected:** `!0` truthy (or a type error if `!` requires bool).
- **Actual:** the branch silently didn't run — a "font failed to load" path never
  executed, masking the real failure.
- **Workaround:** compare explicitly (`font == 0` / `font != 0`); reserve `!` for
  actual booleans.

## C7 — chained `as` casts don't parse  · LOW

```loft
x = (v + 0.5) as integer as float;   // Syntax error: unexpected ')'
```

- **Workaround:** split — `i = (v + 0.5) as integer; x = i as float;`.

## C8 — `gl_load_font` relative-path base is surprising  · LOW (doc)

`gl_load_font(path)` resolves a **relative** path against the `--path` root
(LOFT_REPO), **not** the process cwd or the `.loft` source directory. Sibling
project assets had to be reached as `"../story/assets/Foo.ttf"`. A couple of
relative forms also gave inconsistent hits across runs. Worth documenting (and
ideally: also search cwd + source dir, or expose a resolved base).

---

## C18 — runtime append to a struct-field vector is unreliable  · HIGH

Growing a `vector<…>` **field of a struct** at runtime (through `&Struct`)
silently fails or desyncs — some appends land, sibling ones don't.

```loft
fn add(s: &Sim, q: integer) {
  s.fi_q    += [q];   // sometimes persists...
  s.fi_live += [1];   // ...sometimes doesn't — the parallel arrays desync
}
// also broken: aq = s.fi_q; aq += [q]; s.fi_q = aq;  (the reassign doesn't stick)
```

- **Observed:** after a monster died, `s.fi_q` had grown to length 2 but
  `s.fi_live` read back empty, so floor-item reads returned null and the loot was
  dead/invisible. Inconsistent between sibling fields in the *same* function.
- Build-time append to a **local** vector is fine; it's the **struct-field**
  append (and whole-field *reassignment*) through `&` that's broken.
- **Workaround (what crawler uses):** pre-allocate fixed-size arrays + an integer
  count and **index-write**, exactly like the working `enemies` vector —
  `n = s.fi_n; v = s.fi_q; v[n] = q; s.fi_n = n + 1;`. Index-writes on a captured
  field vector persist; integer-field `+=` persists; only append/whole-field
  reassign don't. Probably the same root as **C4** (the vector field-store path).

---

## Previously observed (earlier crawler sessions / prior notes)

These were hit before and worked around; included so the list is complete.

- **C9 (HIGH, native codegen):** invalid Rust `return let mut …` is emitted when a
  variable **assignment is the first statement of a block-expression used as a
  function's return value**, e.g. `if c { x = v[i]; (x.a, x.b) } else { … }`. The
  interpreter tolerates it; `--check` / native build fail. Workaround: early-return
  guard, assign as a normal statement, then a tail expression.
- **C10 (MED):** **boolean `?? fallback` is unreliable** — `false` is read as the
  null sentinel, so `false ?? true == true`. A `vector<boolean>` flood-fill with
  `!(visited[i] ?? true)` never expanded. Use integer flags (`0/1`,
  `(v[i] ?? 1) == 0`) or test booleans without `??`.
- **C11 (MED):** **reading a struct-field vector by index directly returns null at
  runtime** — `lvl.g_rq[0]` gave null; capture to a local first
  (`rqs = lvl.g_rq; rqs[0]`). (Same family as C3/C5.)
- **C12 (LOW, parse):** `&vector<T>` as a parameter type does not parse — wrap the
  vector in a struct and pass `&Struct`.
- **C13 (LOW, codegen):** copying a `&ref` parameter into a local then using it
  panicked codegen (`snap = s`); pass the `&ref` directly.
- **C14 (LOW, parse):** a literal `{` or `}` inside a `"…"` string must be doubled
  (`{{` / `}}`); a lone brace → "String not correctly terminated". (So a glyph
  `"}"` is written `"}}"`.)
- **C15 (env):** `E0514` — loft's prebuilt rlibs (rustc 1.95) vs a newer system
  rustc (1.96) breaks the native `--check` gate and the wasm/`--html` build.
  Rebuild loft against the system toolchain. (Blocks shipping crawler to the web.)
- **C16 (graphics):** the window enables `GL_DEPTH_TEST` and `build_mvp_2d` leaves
  z constant, so all 2D quads share depth → first-drawn wins (trails / black
  screen). Must `gl_disable(GL_DEPTH_TEST)`. Also no default `glBlendFunc` →
  alpha (text glyphs, tints) needs
  `gl_blend_func(BLEND_SRC_ALPHA, BLEND_ONE_MINUS_SRC_ALPHA)`.
- **C17 (tooling):** `gl_screenshot` under Xvfb + Mesa swrast is positionally
  unreliable (content lands at a fixed offset; flat-shaded rects capture
  inconsistently) — fine for "did it render / does the font load", not for
  pixel-exact checks.

---

## Patterns the interpreter *does* handle reliably (use these)

To keep large loft programs working, the crawler kernel sticks to these forms:

- Filter/transform a `vector<struct>`: `for i in 0..len(v) { m = v[i] ?? none(); if … { out += [m]; } }` (the `mon_for_depth` shape).
- Select an element: build the list first, then **guarded direct index, no `??`**:
  `if i < len(v) { m = v[i]; … }` (the `mon_pick` shape).
- Keep `&Struct`-mutating helpers in the **same module** as their callers (C4).
- Prefer `v += [x]` (append) over `[for _ in 0..n { … }]` comprehensions for
  vectors you'll index later (C5).
- Integer flags, not boolean `??` (C10). Explicit `== 0` for int "truthiness" (C6).

The biggest wins for loft would be **C1/C2/C3** (the struct-vector index +
`??`/copy family) and **C4** (cross-module `&` mutation) — together they made an
otherwise-correct selection routine silently return the wrong thing or crash, and
were only resolvable by rewriting around the interpreter.
