# LOFT-HANDOFF.md — findings for the loft side, ready to file

> crawler is a **consumer** of loft (FILING.md). This doc holds defects crawler surfaced that
> belong upstream, written in the `gh issue create` body shape so they can be filed cold — by a
> human or an agent — without re-deriving anything. **Nothing here is a crawler bug.**
>
> Move an entry to "Filed" (with its issue number) once it is opened; delete it once the fix is
> released *and* re-verified here.

## Context

Found on **2026-07-21** while bringing crawler up on toolchain **2026.7.2** (installed
2026-07-21, binary `/usr/local/bin/loft`). Every reproducer below is **standalone** — no crawler
sources, no `--lib` flags, no bundles. Run them from any directory.

H1/H2 are `sev:high` — one crashes the compiler, the other silently produces wrong data.
H3 is `sev:medium` with a clean workaround.

---

## H1 — a self-referential `??` default SIGSEGVs the compiler

**Status:** not filed · **Repo:** `loft-lang/loft`
**Labels:** `sev:high`, `wa:clean`, `area:codegen`, `hit-by:crawler`, `bug`, `both-backends`
**Suggested title:** `codegen: self-referential ?? default (x = v[i] ?? x) SIGSEGVs the compiler on both backends`

### Summary

Assigning to a variable whose `??` default **is that same variable** — `chosen = t[k] ?? chosen;`
— segfaults the compiler. It dies during **compilation**, not execution: `--interpret --check`
(compile-only, never runs `main`) crashes identically to a real run, and `--native` crashes too.
No diagnostic is printed, just a core dump. Presumably the ownership/lifetime pass follows the
self-reference while the destination slot is mid-write.

### Minimal reproducer

`v1.loft` (14 lines, no imports):

```loft
struct Def { key: text, lvl: integer }
fn pick(t: vector<Def>, i: integer) -> Def {
  chosen = Def { key: "none", lvl: 0 };
  for k in 0..len(t) {
    if k == i { chosen = t[k] ?? chosen; }   // <-- self-referential ?? default
  }
  chosen
}
fn main() {
  t: vector<Def> = [];
  t += [Def { key: "rat", lvl: 1 }];
  d = pick(t, 0);
  println("key={d.key} lvl={d.lvl}");
}
```

```
loft --interpret v1.loft            # Segmentation fault (rc=139)
loft --interpret --check v1.loft    # Segmentation fault (rc=139)  <-- compile-only
loft --native v1.loft               # Segmentation fault (rc=139)
```

### Expected

Either it compiles and prints `key=rat lvl=1`, or — if a self-referential default is not a
supported shape — a diagnostic saying so. A compiler segfault is never the right answer, and
`--check` crashing means a *syntax/type check* of untrusted source can take the process down.

### Actual

`Segmentation fault`, rc=139, no stdout and no diagnostic, on all three invocations.

### Workaround (verified)

Hoist the fallback into its own variable — the default must not name the assignment target:

```loft
fallback = Def { key: "none", lvl: 0 };
chosen = fallback;
for k in 0..len(t) {
  if k == i { chosen = t[k] ?? fallback; }   // OK -> prints key=rat lvl=1
}
```

### Note

crawler does **not** ship this shape — it surfaced while shrinking H2. Filing it because a
compiler crash on 14 lines of valid-looking source is worth a regression test regardless of who
hits it.

---

## H2 — `vec += [f(struct_temp)]` silently nulls every element but the first (interpreter only)

**Status:** not filed · **Repo:** `loft-lang/loft`
**Labels:** `sev:high`, `wa:clean`, `area:store-lifetime`, `area:runtime`, `hit-by:crawler`, `bug`
**Suggested title:** `interpreter: vec += [f(struct_temp)] in a loop nulls all but the first element (native is correct)`

### Summary

A struct temp reassigned each iteration of a loop, passed **by value** into a function whose
result is **appended directly** to a vector, leaves every appended element but the first with all
fields `null`. The by-value copy appears to be elided to a borrow of the temp's storage, which the
next iteration's reassignment frees — so the already-appended elements are left dangling.

**The interpreter is wrong; `--native` is correct.** Same source, same inputs, different results —
so this is also a backend-divergence bug. It is completely silent: no error, no warning, exit 0.

This is the wider form of the shape recorded as **loft#496** ("struct temp reassign clobbers the
first source"). Unlike #496 it needs no large function and no store pressure — 33 standalone lines
reproduce it.

### Minimal reproducer

`repro2.loft` (33 lines, no imports):

```loft
struct Def { key: text, name: text, lvl: integer, hp: integer }
struct Ent { key: text, name: text, mlvl: integer, hp: integer }

fn none() -> Def { Def { key: "none", name: "none", lvl: 0, hp: 0 } }

fn pick(t: vector<Def>, i: integer) -> Def {
  chosen = none();
  for k in 0..len(t) {
    if k == i { chosen = t[k] ?? none(); }
  }
  chosen
}

fn mk(d: Def, q: integer) -> Ent {
  Ent { key: d.key, name: d.name, mlvl: d.lvl, hp: d.hp + q }
}

fn main() {
  t: vector<Def> = [];
  t += [Def { key: "rat",  name: "giant rat", lvl: 1, hp: 3 }];
  t += [Def { key: "bat",  name: "giant bat", lvl: 1, hp: 4 }];
  t += [Def { key: "wolf", name: "grey wolf", lvl: 2, hp: 6 }];
  t += [Def { key: "orc",  name: "orc",       lvl: 4, hp: 16 }];

  ents: vector<Ent> = [];
  for i in 0..4 {
    d = pick(t, i);            // struct temp, REASSIGNED each iteration
    if d.hp > 0 { ents += [mk(d, 0)]; }
  }
  println("--- expect rat/bat/wolf/orc lvl 1/1/2/4 ---");
  for j in 0..len(ents) {
    e = ents[j] ?? Ent { key: "?", name: "?", mlvl: -1, hp: -1 };
    println("  ent[{j}] key='{e.key}' name='{e.name}' mlvl={e.mlvl} hp={e.hp}");
  }
}
```

```
loft --interpret repro2.loft   # WRONG (rc=0, silent)
loft --native   repro2.loft    # CORRECT
```

### Expected

Both backends print all four entries (this is exactly what `--native` prints):

```
  ent[0] key='rat' name='giant rat' mlvl=1 hp=3
  ent[1] key='bat' name='giant bat' mlvl=1 hp=4
  ent[2] key='wolf' name='grey wolf' mlvl=2 hp=6
  ent[3] key='orc' name='orc' mlvl=4 hp=16
```

### Actual (interpreter, rc=0, no diagnostic)

```
  ent[0] key='rat' name='giant rat' mlvl=1 hp=3
  ent[1] key='null' name='null' mlvl=null hp=null
  ent[2] key='null' name='null' mlvl=null hp=null
  ent[3] key='null' name='null' mlvl=null hp=null
```

Note the integer fields print `null` too, so the damage is the whole record, not just the text
fields.

### Workaround (verified)

**Hoist the call result into a local before appending.** Single call preserved, so RNG/side-effect
order is unchanged:

```loft
if d.hp > 0 { e2 = mk(d, 0); ents += [e2]; }   // correct on both backends
```

Variants tested, for whoever writes the regression tests:

| variant | result |
|---|---|
| `ents += [mk(d, 0)]` (append call result directly) | **BROKEN** |
| `e2 = mk(d, 0); ents += [e2]` (hoist result) | OK |
| `ents += [Ent { key: d.key, … }]` (inline literal, no call) | OK |
| `ents += [mk(pick(t, i), 0)]` (no temp at all) | OK — but calls `pick` twice |

So the trigger needs all three: a **reassigned struct temp**, passed **by value into a call**,
whose result is **appended directly**. Break any one and it is correct.

### Impact on crawler (why it is `sev:high`)

This corrupted **every monster spawn** in the dungeon: enemies came out with empty names and
garbage native depths (`mlvl=38` on a depth-1 floor, where no monster in the catalog exceeds
depth 20). The monster-selection chain was verified clean in isolation — the corruption happened
purely on append. Only one of 46 test gates (`depthtest`) noticed, because it is the only one that
asserts on a spawned monster's *data* rather than its count. A game shipped on the interpreter
would have had silently broken content.

---

## Secondary — library behaviour changes worth a note (not necessarily bugs)

These are almost certainly intentional, but each is a **silent** source-compatible break: existing
code keeps compiling and starts doing something different. Flagging in case a lint or a changelog
line is cheaper than the next consumer rediscovering them.

### S1 — JSON `kind()` split `JInteger` out of `JNumber`

Whole numbers now report `"JInteger"`; `"JNumber"` is left for floats. Any accessor written as

```loft
if f.kind() == "JNumber" { return f.as_long(); }
def
```

silently returns **`def` for every integer field** — no error, no warning. In crawler this zeroed
every dimension in a generated content registry (`w_min: 0, w_max: 0, …`) while the adjacent text
fields parsed fine, so the generated output looked structurally healthy and the values that
happened to match their defaults looked correct.

Probe:

```loft
fn main() {
  j = json_parse(file("t.json").content());   // {"a": 4, "b": "hi", "c": 1.5, "d": true}
  println("a={j.field(\"a\").kind()}");       // JInteger  (was JNumber)
  println("c={j.field(\"c\").kind()}");       // JNumber
}
```

Suggestion: mention the split in the changelog, or have `as_long()` on a `JInteger` remain
reachable through a `JNumber` test (an `is_number()` predicate covering both would be ideal).

### S2 — `graphics` 0.5.0 resolves font paths program-relative, not cwd-relative

`gl_load_font("assets/X.ttf")` returns null where it previously loaded, when the process cwd is
the repo root but the program lives in `src/` (loft-libs-graphics #255, branch
`fix-255-program-relative-font`). Absolute paths work. Consumers silently degrade — crawler fell
back to coloured squares instead of glyphs — because the failure is a null return, not an error.
Worth a line in the graphics release notes, since the fix on the consumer side is a one-liner
(`env_variable("PWD")`) but the symptom points nowhere near fonts.

### S3 — `graphics` <0.5.0 aborts on 2026.7.2

`graphics` 0.3.0 panics in `loft_gl_create_window` with winit's *"Initializing the event loop
outside of the main thread"*, a non-unwinding panic that aborts the process. 0.5.0 declares
`loft = ">=2026.7.2"` and works, so the version constraint already encodes this — but a consumer
on an older pin gets an abort with a winit backtrace rather than a version-mismatch message. If
the registry can refuse the combination at load time (as it does for too-new libraries), that
would turn an abort into a diagnostic.

---

## H3 — narrow-width vectors: `u16`/`i16` reject index assignment, and `u32` LOSES IT SILENTLY

**Status: the loft side is already working on this (2026-07-21) — do NOT file, it would
duplicate.** Kept here for the reproducer and for the re-verify trigger below.
· **Repo:** `loft-lang/loft`
**Labels:** `sev:high`, `wa:clean`, `area:codegen`, `hit-by:crawler`, `bug`
**Suggested title:** `vector<u32> element write through a struct parameter is silently discarded; vector<u16>/<i16> reject index assignment outright`

### Summary

Two related defects in index-assignment to narrow-width vector elements. The second is the
dangerous one because it is **silent**.

| element type | direct `v[i] = x` | `v[i] = x` inside a called fn, via a struct param |
|---|---|---|
| `u8` | ok | ok |
| **`u16`** | **compile error** | — |
| **`i16`** | **compile error** | — |
| **`u32`** | ok | **SILENTLY LOST — reads back 0** |
| `i32` | ok | ok |
| `integer` | ok | ok |
| `single` | ok | ok |

So `u32` writes appear to work when written and read in the same function, and vanish the
moment the write happens through a parameter — with no error, no warning, and a plausible
zero left behind.

### Minimal reproducer

```loft
struct S { a: vector<u32> }
fn poke(s: S, i: integer, v: integer) { s.a[i] = v as u32? ?? 0; }
fn main() {
  s = S { a: [] };
  for i in 0..4 { s.a += [0 as u32? ?? 0]; }
  s.a[0] = 5 as u32? ?? 0;      // direct   -> 5, correct
  poke(s, 1, 7);                // via a fn -> 0, WRONG
  println("direct={s.a[0] ?? 0}  via_fn={s.a[1] ?? 0}");
}
```

```
loft --interpret repro.loft
direct=5  via_fn=0            # expected: direct=5  via_fn=7
```

Swap `u32` for `i32`, `u8`, `integer` or `single` and it prints `via_fn=7`.

For the 16-bit half, the same program with `u16` or `i16` fails to compile:

```
error: Cannot assign to attribute on type 'OpGetShortRaw'
```

### Expected

`poke` writes through the struct parameter exactly as it does for `i32`/`integer`; and
`u16`/`i16` accept index assignment like every other width.

### Actual

`u32` silently discards the write (reads back 0). `u16`/`i16` fail to compile.

### Why it is `sev:high`

The `u32` case is silent data loss with a plausible-looking result, in exactly the shape a
grid/field layer uses: a struct holding a vector, mutated by helper functions. crawler hit
it in the collision field, where every wall silently became passable — the flood test
reported *every* heading leaking, which is the only reason it was noticed.

### Workaround (clean, in place)

Use `i32` where you wanted `u32`, and `i32`/`integer` where you wanted `u16`. crawler
stores a 32-bit surface id (`i32`) and an 8-bit material (`u8`) — 5 bytes a slot where
`u16`+`u8` would have been 3.

### Re-verify when the fix lands

Run the type matrix again (`u8 / u16 / i16 / u32 / i32 / integer / single`, each written
directly *and* through a struct parameter). If `u16` becomes index-assignable, narrow
`EdgeSet.ee_surf` from `i32` to `u16`: **17 340 B → 10 404 B** per 32×32 chunk, the last
1.7× of the P6 minimisation. `src/edgetest.loft` already asserts the footprint, so the
gain shows up as a gate change rather than a claim.

## G1 — RESOLVED, and my prediction was WRONG: depth works fine

Written up as a risk, then **measured once `xvfb` was installed, and refuted.** Kept because
the refutation is the useful part.

**Claim:** `gl_clear` is documented as clearing colour only and `gl_create_window` does not
document a depth attachment, so plan #11's 3D pass — the first in the repo ever to
`gl_enable(GL_DEPTH_TEST)` — might have no depth buffer.

**Measurement:** draw a NEAR quad (z=-0.5) FIRST, then a FAR quad (z=+0.5) over it. Without
depth the last draw wins and the centre pixel is the far colour; with depth the near one
survives. Centre pixel came back `(0, 76, 255)` — **blue, the near quad. Depth works.**

The lesson is the cheapness: one 40-line probe and one pixel settled a question I had
written two paragraphs of hedging about. **Install the instrument before writing the risk.**

## G3 — `gl_window_height()` overstates the DRAWABLE by a constant 35 px

`sev:medium` · `wa:partial` · `area:graphics` · `hit-by:crawler` — **measured, not inferred.**

`gl_create_window(1024, 576, …)` succeeds and `gl_window_height()` returns **576**, but the
GL drawable is **541**. A full-screen NDC quad (±1 in both axes) covers only rows 35..575 of
a 576-row screenshot — 541 rows — anchored at GL's bottom-left, so the shortfall appears as a
black band along the TOP of every captured frame.

**It is a constant, not a scale factor:**

| requested window height | content rows | drawn | missing |
|---|---|---|---|
| 576 | 35..575 | 541 | **35** |
| 400 | 35..399 | 365 | **35** |
| 720 | 35..719 | 685 | **35** |

**It is the drawable, not a screenshot offset.** A quad at NDC ±0.9 lands at rows 62..548. A
35-row capture offset would push content to 64..575 — hard against the bottom edge. It stops
at 548, which is exactly `35 + 0.95·541`. `gl_viewport(0,0,1024,576)` does not help: the
drawable clamps it.

**Why it matters beyond the black band:** any camera that takes its aspect ratio from
`gl_window_height()` is wrong by `576/541 = 1.065`, so **the world renders ~6.5% too tall**.
That is silent — a stretched world looks like a world — and it is exactly the class of defect
plan #11's I-STAND exists to forbid.

**Workaround (partial):** none that is clean. The 35 is environment-specific (it smells like a
decoration inset, though this was measured under `xvfb` with no window manager), so
subtracting it would hard-code one host's answer.

**Ask:** have `gl_window_width`/`gl_window_height` report the **framebuffer** size, or add
`gl_drawable_width`/`gl_drawable_height`. A camera cannot be correct without it.

## G4 — the compile gate fails INTERMITTENTLY, then passes unchanged

`sev:medium` · `wa:partial` · `area:toolchain` · `hit-by:crawler` — observed twice on
2026-07-22, both times self-healing.

`make test`'s step 14 (compile gate: parse + bytecode) failed with no source change, and
passed on an immediate re-run of the identical tree. Neither failure reproduced under
`make check`.

1. **Session start.** `loft: library 'hex_field' failed to build native (cdylib compile
   failed … error[E0463]: can't find crate for 'typenum')`. The toolchain refused to fall
   back to interpretation — correctly, it says so explicitly — and the whole gate went red.
   The next run was green with no intervention.
2. **Session end.** `FAIL: compile` with no error text captured at all in the log. `make
   check` immediately after: clean. `make test` immediately after: EXIT=0.

**Why it matters more than a retry:** a gate that is intermittently red trains the reader to
re-run instead of read, which is exactly how a real failure gets waved through. It also cost
a bad call here — a commit was made on a red gate on the assumption it was this flake, which
happened to be true and should not have been assumed.

**Suspicion (unverified):** a race or staleness in the per-library native cdylib build /
program cache — the first failure names a cdylib compile, and `LOFT_NO_CACHE=1` is the known
lever for the sibling `--lib` staleness bug (#322, not re-verified on 2026.7.2).

**Ask:** make the compile gate's failure output always include the diagnostic, and make a
cdylib build failure retryable rather than fatal to the whole run.

## G2 — "expected Camera, got Camera" on a cross-module struct return

`sev:low` · `wa:clean` · `area:types` · `hit-by:crawler`

A `pub fn` in module B returning a struct type defined in module A fails to type-check with a
diagnostic that prints the SAME name on both sides:

```
error: expected Camera, got Camera on return from block
error: expected Camera, got Camera on argument 1 of call to cam_mat4
```

`view3d.loft` does `use hexscene;` and declares `pub fn view3d_camera(...) -> Camera`, whose
body returns `camera_new(...)` — `hexscene`'s own constructor. The unqualified `Camera` in the
signature resolves to something the checker treats as distinct from `hexscene::Camera`.

**Workaround (clean, VERIFIED):** qualify the type in the signature —
`-> hexscene::Camera`. The body needs no change.

**The cost is the diagnostic, not the fix.** "expected X, got X" gives the reader nothing to
act on; printing the fully-qualified names on both sides would make it self-explanatory.

## Filed

*(nothing yet — move entries here with their issue numbers)*
