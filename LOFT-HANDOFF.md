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

**Status:** ✅ **FIXED upstream — verified 2026-08-09 on loft 2026.8.0** (`v2026.8.0-16-gb75887df`). NOT filed: re-running the repro below, the recorded repro prints `key=rat lvl=1` — no SIGSEGV. Kept for the record; the workaround it documents is obsolete.
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

**Status:** ✅ **FIXED upstream — verified 2026-08-09 on loft 2026.8.0** (`v2026.8.0-16-gb75887df`). NOT filed: re-running the repro below, the recorded repro prints all four entries correctly (rat/bat/wolf/orc, lvl 1/1/2/4); the nulls are gone. Kept for the record; the workaround it documents is obsolete.
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

## H4 — a struct built INLINE in an argument list, beside a store-allocated value, corrupts from the 2nd loop iteration

**Status:** ✅ **FIXED upstream — verified 2026-07-23 on loft 2026.7.2** (`@PLN118` store-UAF fixes).
Re-ran the reproducer: the INLINE section now matches the hoisted one exactly (27/23/27/23 where it
previously read 27/10/9/8). hexbody keeps the hoisting as ordinary style, not as a workaround.
**Original report below, kept for the record.**

**Status (original):** not filed · **Repo:** `loft-lang/loft`
**Labels:** `sev:high`, `wa:clean`, `area:store-lifetime`, `area:runtime`, `hit-by:hexbody`, `bug`
**Suggested title:** `interpreter: struct temp built in an argument list is corrupted from the second loop iteration when the call also takes a store-allocated value`

### Summary

`f(MkStruct(...), hexset)` inside a loop: **iteration 0 is correct, every later iteration is
wrong.** The callee reads garbage from the struct — it walks a smaller region and writes fewer
cells — and its returned count does not even agree with the resulting `HexSet`:

```
INLINE — the same struct built inside the argument list:
   rot=0  fill=27  count=27      <- correct
   rot=1  fill=10  count=11      <- returned 10, but 11 cells are set
   rot=2  fill=9   count=11
   rot=3  fill=8   count=11
```

Hoisting the constructor into a local **completely fixes it**:

```
HOISTED — the struct is a local before the call:
   rot=0  fill=27  count=27
   rot=1  fill=23  count=23
   rot=2  fill=27  count=27
   rot=3  fill=23  count=23
```

Silent: no error, no warning, exit 0. Same family as **H2** (a struct temp passed by value into a
call), but the trigger differs — H2 needs the *result appended to a vector*; here the result is a
plain `integer` and the corrupted party is the **struct argument itself**.

### Reproducer (in-repo recipe; I could NOT reduce it to a standalone file)

`hexbody` at `a515850`, `plans/m0-roundtrip/probes/inline_struct.loft`:

```sh
cd hexbody
loft --interpret --path ../loft/ --lib ../loft/lib/ --lib ../loft-libs-world/ --lib src/ \
     plans/m0-roundtrip/probes/inline_struct.loft
```

`box_fill(b: Box, cells: HexSet) -> integer` iterates the HexSet window, calls
`box_to_local(b, x, y) -> (float, float)` per cell, and `hexset_set`s the ones inside.
`box_new(...) -> Box` is the constructor. Broken: `box_fill(box_new(...), cs)`.
Correct: `bx = box_new(...); box_fill(bx, cs)`.

### What I ruled out (please do not re-derive)

Each of these was probed separately and is **NOT** sufficient to trigger it:

| tried | result |
|---|---|
| the same shape in a **single file**, no imports | correct |
| the same shape **cross-module** via `--lib` | correct |
| struct passed by value into a **nested call returning a tuple**, once per cell | correct |
| a helper `fn fresh() -> HexSet` vs inline `hexset_chunk` | no difference; both correct |
| **dense store churn** — 24 sets filled to 1681 cells, dropped, then a fresh one | fresh set is clean |
| allocation **order** of the two HexSets | changes the symptom but is not the cause |

So the minimal trigger is narrower than any of those alone, and I could not find it from the
consumer side. The hexbody recipe is deterministic and reproduces every run.

### Workaround (verified, and now a hexbody rule)

**Never construct a struct inside an argument list.** Hoist it to a local first. hexbody's
`CLAUDE.md` now carries this in "the traps that bite"; it cost about an hour of isolation and the
symptom looked exactly like a geometry bug (wrong cell counts per rotation), not like a
store-lifetime one — which is what makes it `sev:high` despite the clean workaround.

### Impact

Caught by `hexbody`'s `tests/box.loft` because two independent sections disagreed: section 1
(which hoisted) reported 27/23 cells per orientation, section 5 (which inlined) reported 27, 10,
9, 8. Had only the inlining form existed, the numbers were plausible enough to have been read as a
rasterisation result and written into a design doc as a measured constant.

## H5 — a binary op whose operands are BOTH forward-declared calls resolves as `integer`

**Status:** ✅ **FIXED upstream — verified 2026-07-23 on loft 2026.7.2.**
`v = lo() - hi()` with both helpers below `main` now compiles and prints `-1`; the three
non-triggering variants still behave. **Original report below, kept for the record.**

**Status (original):** not filed · **Repo:** `loft-lang/loft`
**Labels:** `sev:medium`, `wa:clean`, `area:type-inference`, `area:frontend`, `hit-by:hexbody`, `bug`
**Suggested title:** `two-pass inference: binary op with two forward-declared operands locks to the integer overload`

### Summary

`v = lo() - hi();` where BOTH `lo` and `hi` are defined LOWER in the file fails to compile with
a type error on `v`. The same expression compiles and runs correctly if either helper is moved
above the caller, if one operand is a literal, or if the call is used bare.

**Mechanism** (diagnosed by the reporter, not guessed): loft is two-pass. A forward call is
`Unknown` in pass 1, so operator overload resolution — unable to type EITHER operand — picks the
first candidate, `OpMinInt` / `OpMulInt`, locking the result to `integer`. Pass 2 re-resolves the
calls to `float`, and the assignment then errors. The unary case is already guarded (**loft#592**);
this is the binary case of the same gap.

### Minimal reproducer (6 lines, no imports)

```loft
fn main() {
  v = lo() - hi();          // BOTH operands forward-declared
  println("both forward: {v}   (want -1.0)");
}
fn lo() -> float { 1.0 }
fn hi() -> float { 2.0 }
```

```
error: Variable 'v' cannot change type from integer to float; use a new variable name or cast with 'as'
error: Cannot assign float to a field of type integer — use 'as integer' to cast explicitly
```

### The boundary — what does and does not trigger it

Verified, each as its own file:

| variant | result |
|---|---|
| `v = lo() - hi()` — both operands forward | **BROKEN** |
| `a = lo()` — bare forward call | OK (prints 1) |
| `b = lo() - 1.0` — one operand a literal | OK (prints 0) |
| `v = lo() - hi()` with both helpers ABOVE `main` | OK (prints -1) |

So the trigger needs *both* operands untypeable in pass 1. One known-typed operand is enough for
overload resolution to pick the float candidate.

### Expected

All four compile and produce the float result; a forward-declared function's return type is part
of its signature and is available before its body is needed.

### Workaround (verified, and now a hexbody rule)

**Define helpers above their callers.** hexbody hit this porting `wall_from_run`, which computed
`fbx - fax` from two forward-declared `tri_x` calls; moving the function below `tri_x` fixed it.
The rule is in hexbody's `CLAUDE.md` traps.

### Why `sev:medium` despite the clean workaround

The diagnostic points at the *assignment*, which is correct-looking code, and names `integer` —
a type that appears nowhere in the expression. Nothing in the message suggests "declaration
order", so the reader looks for a nonexistent integer in their own arithmetic. It cost about
twenty minutes before the pattern was recognised.

## H6 — reading a file INVALIDATES a live `list_dir()` result (2nd listing onward)

**Status:** ✅ **FIXED upstream — verified 2026-07-23 on loft 2026.7.2**, and guarded there:
loft commit `018bea06` *"test(@PLN118): guard crawler-H6 — a live list_dir survives a file read"*.
Re-ran the reproducer: both directories now report `len AFTER = 4, matched = 4`.
**Original report below, kept for the record.**

**Status (original):** not filed · **Repo:** `loft-lang/loft`
**Labels:** `sev:high`, `wa:clean`, `area:stdlib`, `area:store-lifetime`, `hit-by:hexbody`, `bug`
**Suggested title:** `list_dir result is invalidated by a subsequent file read (silently, from the second listing on)`

### Summary

Iterate a `list_dir()` result and open any file inside that loop: from the **second** directory
listed onward the vector is silently emptied mid-iteration. `len(ns)` reads its true length before
the loop and **0** after, and only a couple of entries are visited. No error, no warning, exit 0 —
the directory just looks smaller than it is.

The first listing in a program is unaffected, which is what makes it nasty: a single-directory
program is correct, and the bug appears only when a second directory is walked.

### Minimal reproducer (20 lines, no imports)

```loft
fn main() {
  for s in 1..3 {
    d = "{source_dir()}/lb{s}";
    mkdir_all(d);
    for i in 0..4 { file("{d}/f{i}.t").write("x"); }
  }
  for b in 1..3 {
    d2 = "{source_dir()}/lb{b}";
    ns = list_dir(d2);
    before = len(ns);
    seen = 0;
    for i2 in 0..len(ns) {
      nm = ns[i2] ?? "";
      if nm.ends_with(".t") { c = file("{d2}/{nm}").content(); seen = seen + 1; }
    }
    println("dir lb{b}: len BEFORE loop = {before}, len AFTER = {len(ns)}, matched = {seen}"
            + "   (want 4, 4, 4)");
  }
}
```

### Expected / Actual

```
dir lb1: len BEFORE loop = 4, len AFTER = 4, matched = 4   (want 4, 4, 4)
dir lb2: len BEFORE loop = 4, len AFTER = 0, matched = 2   (want 4, 4, 4)
                              ^^^^^^^^^^^^^            ^
```

### The boundary — what does and does not trigger it

Verified, each as its own probe:

| variant | result |
|---|---|
| iterate `list_dir`, **read a file** in the loop, 2nd directory | **BROKEN** (len -> 0 mid-loop) |
| iterate `list_dir`, read a file, **1st** directory only | OK |
| iterate `list_dir`, **append to another vector** in the loop (no file read) | OK |
| reassign `list_dir` to the same variable across loop iterations, no file read | OK |
| a plain fn returning `vector<text>`, reassigned in a loop | OK |
| **snapshot the names into a local vector, THEN read the files** | OK |

So the trigger is specifically a **file open while a `list_dir` vector is still live**, and only
after the first listing — consistent with the listing's backing store being freed or reused by the
file handle.

### Workaround (verified, and now a hexbody rule)

**Snapshot the names before touching any file:**

```loft
ns = list_dir(dir);
picks: vector<text> = [];
for i in 0..len(ns) { … picks += [ns[i] ?? ""]; }   // no file I/O in this loop
for j in 0..len(picks) { … file("{dir}/{picks[j] ?? ""}").content() … }
```

### Impact on hexbody (why `sev:high`)

The round-trip gate walks `corpus/a1` and `corpus/a2` and diffs every committed entry. It loaded
**3 of 22** entries from the second directory and reported a clean pass on the 13 it saw. A gate
that silently tests a third of its corpus and says OK is worse than one that fails: the corpus
exists precisely so that nothing is checked against freshly-generated output, and this quietly
shrank it.

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

**Status:** ✅ **FIXED upstream — verified 2026-08-09 on loft 2026.8.0** (`v2026.8.0-16-gb75887df`).
The re-verify trigger below was run: the repro now prints `direct=5  via_fn=7`, so the write
through a fn parameter lands. Still not filed, and now there is nothing to file.
*(Was: "the loft side is already working on this (2026-07-21) — do NOT file, it would duplicate.")*
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

3. **Third instance — CAUSE FOUND.** `FAIL: crystal`, a native crash inside
   `loft_shared_n_hexset_chunk` (`panic_cannot_unwind` through `shared_store_dispatch`).
   Timestamps settled it: `hex_field/src/hex_field.loft` mtime **20:00:30**, its cdylib
   `libloft_auto_hex_field.so` **19:59:57** — **the source was 33 seconds newer than the
   native artifact**, and the file was uncommitted-modified because another agent was
   editing that tree live. Crawler compiled loft-side against new source while calling an
   old cdylib. Re-run after the build settled: green.

**So the root is not a race in the toolchain but a STALE-CDYLIB WINDOW**, and `--lib` on a
shared working tree makes that window routine rather than rare: any sibling save between the
cdylib build and the consumer's run produces a native/source mismatch. The two earlier
instances fit the same shape (a cdylib compile failure, then a diagnostic-free compile
failure).

**Consumer-side rule this earns:** a native crash or a diagnostic-free compile failure in a
`--lib` sibling is a **staleness symptom until proven otherwise** — compare the source mtime
against the cdylib mtime BEFORE debugging anything. That check is two `ls` calls and it would
have saved every one of the three.

**Suspicion for the remaining half (unverified):** the toolchain does not appear to detect
that the cdylib is older than its source — the first failure names a cdylib compile, and `LOFT_NO_CACHE=1` is the known
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

## G5 — assigning to an UNDECLARED struct field reports a type error on the RECEIVER

**Observed 2026-07-22, during the EdgeSet merge.** Writing to a field that does not exist on
a struct does not say "no such field". It says the struct variable is changing type:

```
error: Variable 'e' cannot change type from EdgeSet to integer;
       use a new variable name or cast with 'as'
  1230 |   if was == 0 && mat != 0 { e.eg_live = e.eg_live + 1; }
```

`eg_live` was never declared in `EdgeSet` — a constructor edit had silently not applied. The
diagnostic names `e`, names its type, and says "integer", none of which is the problem, and
it points at the *use* site rather than at the missing declaration.

**Why it is worth recording: it produces a plausible WRONG fix.** The message reads as a
restriction on self-referential field assignment (`x.f = x.f + 1` "retyping" `x`), so the
natural response is to restructure the assignment through a local — which does not help,
because the field still does not exist. That happened here, and the error simply moved.

**The disproof is one line:** an identical self-referential assignment on a field that IS
declared compiles and runs clean —

```loft
if was == 0 && surf != 0 { e.eg_count = e.eg_count + 1; }   // eg_count IS in the struct
```

— green through all 44 `hex_field` package tests. So the form is fine; the declaration is
what was missing.

**Rule:** on "cannot change type from `<Struct>` to `<something>`", check that every field
named on that line is actually declared, BEFORE touching the assignment. Two seconds against
a restructure that cannot work.

Not filed upstream yet — the fix is a diagnostic change (name the unknown field, point at the
struct), which is `sev:low` / `wa:clean` but a real time sink.

## Filed

*(nothing yet — move entries here with their issue numbers)*

---

## N1 — `%` as an if-branch tail expression makes the NATIVE generator emit `as i8`

**Found 2026-07-23** on toolchain 2026.7.2, bringing crawler's `housetest.loft` up on
`--native`. Standalone — no crawler sources, no `--lib`.

Labels: `sev:medium` · `wa:clean` · `area:codegen` `area:native` · `hit-by:crawler`

### Summary

A function returning `integer` whose `if`-branch **tail expression** is a `%` (modulo) makes
the native generator emit the value `as i8`, and rustc rejects the function because the
declared return type is `i64`. The **interpreter is correct**; `--native` will not compile at
all, so it is a hard build break rather than a wrong result.

### Minimal reproducer

```loft
fn w1(n: integer, m: integer) -> integer { if m == 1 { n % 6 } else { n } }   // FAILS
fn w2(n: integer, m: boolean) -> integer { if m { n % 6 } else { n } }        // FAILS
fn w3(n: integer, m: boolean) -> integer { if m { return n % 6; } n }         // compiles
fn v3(n: integer, m: boolean) -> integer { if m { -n } else { n } }           // compiles
fn v4(n: integer, m: boolean) -> integer { if m { n } else { n } }            // compiles
fn main() { println("{w3(2, true)} {v3(2, true)} {v4(2, true)}"); }
```

`w1` and `w2` are the bug; `w3`/`v3`/`v4` are the discriminators.

### Expected

Compiles on both backends. `--interpret` already prints `2 -2 2` for `w3 v3 v4`, and with
`w1`/`w2` restored prints their correct values too.

### Actual (`--native`, rc=1)

```
error[E0308]: mismatched types
     --> /home/…/loft_native_NNNNNNN.rs:2378:5
      |
fn n_w1(cell: &std::cell::UnsafeCell<Stores>, mut var_n: i64, mut var_m: u8) -> i64 {
      |                                                                          --- expected `i64` because of return type
...
      |     (…ops::op_rem_int(…)…) as i8
      |     ^^^ expected `i64`, found `i8`
loft: native compilation failed (codegen bug — try --native-emit to inspect the source)
```

### What is and is not the trigger

- **`%` in the branch tail is required** — `-n` (`v3`) and a bare `n` (`v4`) compile.
- **The condition's type is irrelevant** — `w1` takes an `integer` flag and fails identically,
  so this is not about `boolean` lowering to `u8`.
- **Statement position is fine** — `w3` puts the same `%` behind an explicit `return` and
  compiles, which localises this to the if-**expression** tail lowering, not to `op_rem_int`.

### Workaround (verified)

Use an explicit `return` instead of the if-expression tail:

```loft
fn spec_rot(n: integer, m: boolean) -> integer {
  if m { return ((-n) % 6 + 6) % 6; }
  n
}
```

Applied in `../hexbody/src/housetest.loft`; `--native` then compiles and the gate prints `HOUSE OK`
identically on both backends.

---

## N2 — `graphics::save_png` returns `false` under `--native`, writing no file

**Found 2026-07-23** on toolchain 2026.7.2 with `graphics` **0.5.0**. Belongs to the graphics
chunk repo, not loft core.

Labels: `sev:medium` · `wa:partial` (run that program under `--interpret`) · `area:native`
`area:graphics` · `hit-by:crawler`

### Summary

`save_png` returns `true` and writes the PNG under `--interpret`, and returns `false` and
writes **nothing** under `--native`. Absolute and relative paths behave identically, so this is
not the program-relative path resolution of S2. No diagnostic is printed on either stream.

### Minimal reproducer

```loft
use graphics;
fn main() {
  cv = canvas(64, 64, rgb(20, 30, 40));
  fill_rect(cv, 8, 8, 40, 40, rgb(200, 120, 60));
  println("abs -> {save_png(cv, "/tmp/pngprobe_abs.png")}");
  println("rel -> {save_png(cv, "pngprobe_rel.png")}");
}
```

### Expected / Actual

| | abs | rel | file written |
|---|---|---|---|
| `--interpret` | `true` | `true` | yes |
| `--native` | **`false`** | **`false`** | **no** |

### Already-investigated — please do not re-derive

The cdylib is **not stale**: `~/.loft/build-cache/graphics-0.5.0/release/libloft_graphics_native.so`
(built 2026-07-22 23:49) exports `loft_save_png`, `n_save_png` **and**
`n_save_png__loft_bridge`, and no "native library did not load" warning is emitted.

`native/src/lib.rs:2015` already carries a comment saying the `#[loft_native]` `n_save_png`
shim was added to fix *"the stale snapshot that made the `vec_wrapper!` `save_png` return
false under `--native`"* — so this is either a regression of that fix or an incomplete one.
Note the loft declaration is `#native "loft_save_png"` (the **raw** entry point), so
`--native` does not route through the `n_save_png` shim the comment describes; that asymmetry
is the first thing to check.

Same family as loft#392 (`vector` arguments crossing the native FFI boundary), which also
fails silently with no diagnostic.

---

## N3 — returning a struct read out of a `vector<T>` leaks one store record per call

**Found 2026-08-10** on toolchain 2026.8.0 (installed binary md5 `0dabaa1e169e`, `../loft`'s
working-tree build). Reproduces on `--interpret`; not yet checked on `--native`.

Labels: `sev:low` · `wa:partial` (call it only when the result is used) · `area:stores`
`hit-by:crawler`

### Summary

A function that selects a record out of a `vector<Struct>` and **returns it by value** leaves
one store record alive per call. The program prints loft's own exit warning:

```
Warning: 1 stores not freed at program exit: kt=78 MonsterDef×21
```

The count tracks the number of CALLS, not the size of the table — 22 calls, 21 records — so it
is the returned copy that is retained, not the table.

### Minimal reproducer

Against crawler's `monsters.loft`, whose `mon_pick_tag(table, tag, salt) -> MonsterDef` scans
the vector and `return`s an element:

```loft
use catalog;
use monsters;
fn main() {
  n = 0;
  for _ in 0..22 {
    t = game_monsters();
    md = mon_pick_tag(t, TAG_RUIN_NEST, 7);   // <- returns an element of `t`
    n += len(t) + md.m_hp;
  }
  println("calls=22 sum={n}");
}
```
→ `Warning: 1 stores not freed at program exit: kt=78 MonsterDef×21`

**The negative control isolates it to the return, not the table build.** Identical loop with
the `mon_pick_tag` line removed (`for _ in 0..22 { t = game_monsters(); n += len(t); }`) exits
with **no warning at all** — so building and dropping the vector 22 times is clean.

### Why it matters to a consumer

It is unbounded in a long-running program rather than a fixed cost. crawler hit it in a
per-dawn code path (`send_incursions`): one leaked record per game day, forever. The warning
also only appears at exit, so a server or a game loop never sees it.

### Workaround (verified, and what crawler shipped)

Decide everything else FIRST and call the selector only on the branch that actually consumes
the result — in crawler's case, find the spawn hex before picking the monster, so a den with
no room to send leaks nothing. That bounds the leak to real uses; it does not remove it.
Returning an index instead of the record would remove it, at the cost of every call site.

---

## H7 — `file().content()` returns EMPTY for non-UTF-8 bytes, silently, on both backends

**Status:** ✅ **FILED as [loft#829](https://github.com/loft-lang/loft/issues/829)** (2026-08-09, still reproducing on 2026.8.0) · **Repo:** `loft-lang/loft`
**Labels:** `sev:high`, `wa:partial`, `area:stdlib`, `hit-by:hexbody`, `bug`, `both-backends`
**Suggested title:** `stdlib: file().content() silently returns "" for a file that is not valid UTF-8`

### Summary

`file(path).content()` returns an **empty text** for any file whose bytes are not valid UTF-8.
There is no error, no refusal code, and no diagnostic — the call succeeds and yields `""`, which is
indistinguishable from *"the file is empty"*.

loft can **write** such files: `f#format = LittleEndian` plus `f += (v as u8)` is the documented way
to produce binary, and `hex_field`'s `doc_write` uses exactly that to emit its `HXF1` documents. So
the language writes a file it then cannot measure or read back, and reports success either way.

This is the silent-wrong-answer class, not a missing feature: any consumer that sizes, checksums or
verifies a binary file it just wrote gets `0` and a green result.

### Minimal reproducer

Standalone — no libraries, no flags. `loft --interpret repro.loft` (and `--native`).

```loft
// file().content() returns EMPTY for non-UTF-8 bytes, silently.
fn main() {
  ok = "/tmp/loftrepro-ok.bin";
  f = file(ok);
  f#format = LittleEndian;
  f += (65 as u8); f += (0 as u8); f += (66 as u8);        // "A\0B" — valid UTF-8
  println("valid UTF-8 (3 bytes on disk): content().len() = {file(ok).content().len()}");

  bad = "/tmp/loftrepro-bad.bin";
  g = file(bad);
  g#format = LittleEndian;
  g += (65 as u8); g += (255 as u8); g += (66 as u8);      // 0xFF — never valid UTF-8
  println("invalid UTF-8 (3 bytes on disk): content().len() = {file(bad).content().len()}");
}
```

### Expected

Either a **refusal** the caller can see (a null/`?` result, or a diagnostic), or a byte-oriented
accessor that returns all 3 bytes. Anything except "success, and the answer is 0".

### Actual — identical on `--interpret` and `--native`

```
valid UTF-8 (3 bytes on disk): content().len() = 3
invalid UTF-8 (3 bytes on disk): content().len() = 0
```

Both files are **3 bytes on disk** (`ls -l` confirms). Exit code 0, no warning either way.

A NUL byte is *not* the trigger — `A\0B` reads back fine at length 3. Size is not the trigger
either: a 5000-byte ASCII file reads back at 5000. The trigger is UTF-8 validity alone.

### Workaround (partial)

Measure the file by something other than its bytes. hexbody's `tests/foxel.loft` needed to prove
that `hex_field`'s `doc_write` **appends** rather than truncates; the natural instrument (write
twice, compare lengths) reads `0` and `0`, and `0 == 0 * 2` is **vacuously true** — the gate printed
a confident, meaningless "it appended" until this was caught. It now measures the document's *cell
count* instead, which is a real instrument.

There is no workaround for actually **reading** binary content back into loft.

### Why `sev:high`

The failure is silent and inverts a test's meaning rather than breaking it. Any gate of the form
*"write bytes, read them back, compare"* passes trivially on non-UTF-8 data, because both sides are
`""`. That is the same shape as the false-green test moros documents in its own round trip.

---

## H8 — a registry-style `[dependencies]` entry that is NOT resolvable from the registry does not fall back to a library on the `--lib` path

**Status:** ✅ **FIXED upstream — verified 2026-08-09 on loft 2026.8.0** (`v2026.8.0-16-gb75887df`). NOT filed: re-running the repro below, an unpublished `pkga` declared `>=0.1` by `pkgb` now resolves from `--lib`: prints `b=43`. Kept for the record; the workaround it documents is obsolete.
**Labels:** `sev:medium`, `wa:clean`, `area:packages`, `hit-by:hexbody`, `bug`
**Suggested title:** `packages: a >= registry dep with no registry match is NOT resolved from --lib — dependent library's symbols go unresolved`
**Related:** #337 (CLOSED — *compile-time use-resolution consults `[dependencies]` **path** entries; it does not*). This is the sibling case for `>=` **registry** entries + `--lib`.

### Summary

A library `B` declares `[dependencies] A = ">=0.1"` and `use A;`. `A` is **not yet in the
registry**, but its source is present on the `--lib` search path (both `A` and `B` live under a
`--lib`'d chunk directory). When a program consumes `B` via `--lib`, loft does **not** fall back to
the `--lib` copy of `A`: `A`'s symbols are unresolved and compilation fails **inside B** with
`Unknown variable '<x>'` at the first use of an `A` function.

The library resolves fine the moment `A` **is** in the registry (published, or cached). So the gap
is specifically: *registry constraint present, registry match absent, `--lib` copy available and
ignored.*

### Confirmed cause ⇄ fix (in the real tree, not a claim)

Measured in hexbody, which produces a chunk of 10 inter-dependent `hex_*` libraries under one
`loft-libs-world` `--lib` root:

- With `hex_field` **unpublished** and `hex_edge/loft.toml` declaring `hex_field = ">=0.1"`, a
  consuming gate fails **deterministically** — `Unknown variable 'nq'` inside `hex_edge` (at its
  first `hex_at(...)` call, `hex_at` being a `hex_field` function). Across a multi-gate suite the
  *set* of failing gates shifted run to run, but any single gate failed 4/4.
- **Publishing `hex_field`** (making `>=0.1` resolvable from the registry cache) and re-adding the
  identical dep line: the same gate **passes 2/2**. Nothing else changed.

So the dependency machinery is correct once the dep is registry-resolvable; the defect is only the
**missing `--lib` fallback** while it is not.

### Reproducer (in-repo recipe; I could NOT reduce it to a standalone file)

The in-repo trigger:

```sh
# in loft-libs-world (a --lib chunk of inter-dependent libs), with hex_field UNPUBLISHED:
#   add to hex_edge/loft.toml:   [dependencies]\n hex_field = ">=0.1"
# then from hexbody:
loft --interpret --path /usr/local/share/loft/ --lib ../loft-libs-world/ --lib src/ tests/censusb.loft
#   -> error: Unknown variable 'nq'  (inside hex_edge, at (cq,cr) = hex_at(...))
# publish hex_field (or otherwise make it registry-resolvable), keep the dep line -> passes.
```

⚠ **Do not re-run these — they PASS and do not reproduce the bug** (recorded so the next person
does not repeat them): a minimal standalone `A <- B <- C` chain of trivial libraries, all with
unpublished `>=` deps consumed via `--lib`, **falls back to `--lib` correctly** — on the
interpreter, with `--path`, with two `--lib` flags, and in the mixed case (one dep published from
the registry, one unpublished on `--lib`). So the trigger needs something the synthetic chain lacks
— likely the dep being reached **transitively** through another `--lib` library inside a
multi-library chunk. The confound is not yet isolated, which is why this is a recipe and not a
minimal repro.

### Expected

When a `>=` dependency has no registry match, loft resolves it from the `--lib` search path if a
library of that name is present there (the same trees `use` already resolves against), rather than
leaving its symbols unresolved. `--lib` is the local-development path; a WIP library that depends on
another WIP library in the same chunk should build before either is published.

### Actual

The `>=` constraint is treated as registry-only. With no registry match and no fallback, the
dependent library fails to compile at the first use of the missing dependency's symbols.

### Workaround (verified, and it is what hexbody shipped)

Two, both clean:

1. **Keep the deps out of `loft.toml`; put them in the registry INDEX entry at publish time.**
   Install reads a package's deps from `version.deps` in the index, not from the tarball's
   `loft.toml` (`loft/src/install.rs::resolve_recursive`), and `loft package` omits deps for the
   author to add to the index. So the working-tree manifest can stay dep-free — `--lib` consumption
   works — while the published package still carries correct deps. This is what hexbody did.
2. **Publish bottom-up.** Publish `A` before `B` declares `A = ">=0.1"`; then `A` is always
   registry-resolvable and the fallback never has to fire.

### Why `sev:medium`

Not silent and not a crash — it fails loudly at compile time with a clear (if misleading) location
*inside* the dependency. But it makes a chunk of inter-dependent WIP libraries un-buildable via
`--lib` the moment they declare their real deps, which is exactly the local-dev loop for the first
inter-dependent library family in a chunk. The workaround is clean, so it does not block.

---

## H9 — `loft update` iterates the LOCKFILE, not the manifest: a newly declared dependency is never locked, and the report says "up-to-date"

**Status:** ✅ **FILED as [loft#830](https://github.com/loft-lang/loft/issues/830)** (2026-08-09, measured today on 2026.8.0) · **Repo:** `loft-lang/loft`
**Labels:** `sev:medium`, `wa:clean`, `area:packages`, `hit-by:crawler`, `bug`
**Suggested title:** `loft update: a dependency declared in loft.toml but absent from loft.lock is skipped silently — "all N packages up-to-date" counts the lock, not the manifest`

### Summary

Add a dependency to `[dependencies]` **and use it in the source**, then run `loft update`. The
package is **not added to `loft.lock`**, and the command reports success — counting the packages
already in the lock, not the ones declared:

```
loft update: all 1 packages up-to-date.
```

…with **two** declared and used. The lock keeps lagging the manifest until some later build
happens to compile against the package, at which point resolution writes the entry as a side
effect. `loft update <pkg>` on the missing package is no better: it answers
`already on the highest satisfying version` and still writes nothing.

The silence is what makes this bite. `loft update` is the command a consumer runs to make the
lock describe the manifest, and it affirmatively reports that it does.

### Repro (minimal, from scratch)

```sh
mkdir -p lockrepro/src && cd lockrepro
cat > loft.toml <<'EOF'
[package]
name    = "lockrepro"
version = "0.0.0"
loft    = ">=0.8"

[dependencies]
random = ">=0.2"
EOF
printf 'use random;\nfn main() { r = RandStream { s1: 1, s2: 2 }; println("{r.s1}"); }\n' > src/main.loft

loft --interpret --check src/main.loft     # lock created:  random
# now DECLARE AND USE a second package
sed -i 's|^random = ">=0.2"|random = ">=0.2"\nhex_grid = ">=0.1"|' loft.toml
sed -i '1i use hex_grid;' src/main.loft

loft update                                # -> "all 1 packages up-to-date"   <-- WRONG
grep '^name' loft.lock                     # -> random          (hex_grid absent)

loft --interpret --check src/main.loft     # "[registry] resolving hex_grid from registry"
grep '^name' loft.lock                     # -> random, hex_grid
loft update                                # -> "all 2 packages up-to-date"   (correct now)
```

### Expected

`loft update` reads `[dependencies]`, resolves every declared package, and writes a lock entry
for each — so the lockfile describes the manifest after the command that exists to make it do
so. A package it cannot resolve should be an error, not a silent omission.

### Actual

It walks the existing `loft.lock` and refreshes those entries only. A dependency the manifest
gained since the lock was written is invisible to it, and the summary line counts lock entries,
so the omission reads as success.

### Why it matters to a consumer

The lockfile stops being the authority it is meant to be. In crawler, `hex_edge`, `hex_way` and
`hex_roof` were declared in `loft.toml` and used by 55 files while absent from `loft.lock`;
`loft update` reported everything up-to-date. Each then resolved from wherever it could be
found — the local registry cache, or a `--lib` sibling tree that outranks the registry — which
is precisely the two-paths-that-disagree problem the lockfile is supposed to prevent. A fresh
clone plus `loft update` reproduces an incomplete lock.

### Workaround (verified, clean)

Build once before trusting the lock: any compile that exercises the new dependency writes its
entry, after which `loft update` behaves. Concretely — `loft --interpret --check <a file that
uses it>`, then `loft update`. Verifying the lock names every declared package is the check
that catches it.


---

## H10 — an auto-native cdylib fails to wire INTERMITTENTLY under concurrent `loft` processes, and the failure is a PANIC rather than a fallback

**Status:** ✅ **FILED as [loft#831](https://github.com/loft-lang/loft/issues/831)** (2026-08-09, measured today on 2026.8.0) · **Repo:** `loft-lang/loft`
✅ **FIXED UPSTREAM — both halves — in loft `c69f7c1a` (2026-08-10 12:22), and the fix names
this report.** Issue **CLOSED** 2026-08-10 12:22 UTC; consumer confirmation filed back as
[comment 5240891610](https://github.com/loft-lang/loft/issues/831#issuecomment-5240891610)
(the 13-pass table, what it unblocked, and the caveat that we never ran a before/after A/B).
Verified by inspection, not just by absence:
- **Defect 2, the serious one, is gone as designed.** `probe_and_mark_exports` now `dlopen`s the
  artifact and `dlsym`s each bridge before marking, marks only what resolves (**partial is a
  valid outcome**), and KEEPS the handle so a later prune or rebuild cannot invalidate the
  decision. What does not resolve **interprets** — "the fallback the auto-native model always
  promised, finally reached by the path that needed it". That is exactly the "panic where a
  fallback exists" complaint below, answered in the terms it was made in.
- **Defect 1's real mechanism was found, and it was not a race in the wiring.** `prune_artifacts`
  bounded `native-auto/` by sweeping every `.so` by AGE, and that directory is not exclusively
  its own: a `[c] shim` cdylib lives there, content-keyed and built ONCE — hence permanently the
  oldest file and the sweep's first victim. Deleting it removes the only definition of the
  package's `#c` symbols, and nothing can interpret in its place, because a `#c` binding IS the
  implementation. Upstream's words for our symptom: *"parallel runs saturate the directory
  because each type-layout context mints its own artifact, so this is the other half of why a
  suite loses a DIFFERENT test on each parallel run and passes serially."* The sweep now takes
  only the `loft_auto_<pkg>_` family it built. It had also been living in loft's own suite as a
  long-standing "known flaky" test.
- Guards landed with it (`an_unwirable_cdylib_interprets_instead_of_panicking`,
  `a_partially_exporting_cdylib_marks_only_what_resolves`,
  `a_foreign_library_in_native_auto_survives_pruning`), and `--help` now names
  **`LOFT_NO_NATIVE_LIBS`** and **`LOFT_REQUIRE_NATIVE`** — the escape hatch the *Workaround*
  section below says it searched for and could not find. That note is now stale; the flag exists.

⚠ **Our 13 green passes were not evidence of a fix — they were measured on a binary that already
had it, and we did not know.** The fix landed at 12:22 and the binary was installed at 12:33;
the first probe ran after that. Worth remembering the next time absence-of-failure looks like
information: the same 13 passes on the 06:19 binary would have meant something else entirely,
and nothing in the run said which binary we were on except the md5 in the gate header. On this
evidence crawler's gate now runs **`min(8, nproc-2)`-wide by default** — 8 on this box
(`tools/run_tests.sh`, `GATE_JOBS`); a
row that is red under load and green at `GATE_JOBS=1` is this bug returning, and belongs here.
**Labels:** `sev:high`, `wa:partial`, `area:native`, `hit-by:crawler`, `bug`
**Suggested title:** `auto-native: cdylib wiring fails intermittently when several loft processes run at once — "native function not loaded" panics instead of falling back to the interpreted body`

### Summary

Running independent `loft --interpret` programs **concurrently** makes some of them die with:

```
loft: native library …/hex_grid-0.1.0/native-auto/libloft_auto_hex_grid_….so
      needs a system library at runtime, but it is not installed
loft: auto-native fn `hex_distance` (loft_shared_n_hex_distance) is marked for cdylib
      dispatch but could not be wired (bridge symbol not found in any loaded cdylib)
      — calling it will panic
thread 'main' panicked at src/compile.rs:365:17:
native function not loaded: its library's native cdylib is missing or stale
```

Each program passes on its own. **Which** program dies moves between runs.

### Measured (crawler's 88-test gate, 24-core box)

| run | result |
|---|---|
| serial | 88/88 green |
| `xargs -P8` | 87/88 — `fieldtest` |
| `xargs -P8` (repeat) | 87/88 — `fieldtest` |
| `xargs -P4` | 86/88 — **`wheeltest`, `linktest`** |
| warm the cdylibs serially first, then `-P8` | 86/88 — **`fieldtest`, `meshtest`** |
| **8 concurrent copies of the SAME failing program** | **8/8 green** |

The last two rows are the informative ones. Pre-warming does **not** fix it, so it is not
merely a cold artifact being built under contention. And one program run eight times over is
fine — it takes a *mix* of programs to trigger, which points at concurrent access to the shared
`~/.loft/…/native-auto/` artifacts rather than at any one library.

### Two defects, and the second is the serious one

1. **The wiring is not concurrency-safe.** Same inputs, same machine, different outcome
   depending only on what else is running.
2. ⚠ **A cdylib that cannot be wired PANICS at the call site instead of falling back to the
   interpreted body.** loft has the loft-source implementation of `hex_distance` right there —
   it is running the interpreter. The message even says the call *will* panic, so the condition
   is known one step before the crash. Falling back would make defect 1 a performance
   footnote rather than a red suite. As it stands, an optimisation that fails to load takes the
   program with it.

### Why it matters to a consumer

It is the only thing between crawler's gate and a large speedup: measured when this was filed,
the suite was ~18 minutes serially and ~70 seconds at `-P8`, and the tests are genuinely
independent. We cannot take that win, because a suite that fails a *different* test each run is
worse than a slow one.

✅ **That prize has since been collected, because the fix landed.** Since 2026-08-10 the roster
runs `--native-release` on its 14 heaviest rows and **8-wide**, and the gate is **~1.5-2.5 min**
against the 18 minutes above. The consumer-impact case is therefore closed, not merely argued:
this is what the fix bought one project, and the defect held a 24-core box at one core for
weeks — worth saying plainly in the ticket, because "a suite that fails a different test each
run is worse than a slow one" is the reason a consumer eats the slow one silently instead of
reporting it.

### Workaround (partial)

~~Run the gate serially. Pre-warming does not help. There appears to be no flag to disable
auto-native dispatch (`--help` offers none, and the binary's `LOFT_*` env vars are
`LOFT_COMPAT_SAMPLE`, `LOFT_LIVE_STDLIB`, `LOFT_STORE_GUARD`, `LOFT_TIMING`) — one would be a
clean escape hatch on its own.~~

**Obsolete on both counts** (2026-08-10). The defect is fixed (see Status), so serial execution
is no longer the price; and the flag exists and is now documented — **`LOFT_NO_NATIVE_LIBS=1`**
makes every `use`d library interpret and skip its auto-native cdylib, with `LOFT_REQUIRE_NATIVE=1`
as the inverse. ⚠ The original sentence was not wrong when written but was reasoned from the
wrong instrument: it concluded "no flag" from `--help` plus a scan of `LOFT_*` strings, and the
fix commit added both names to `--help` precisely because the report had searched there. If a
capability seems absent, that is a question for the maintainers, not a fact to write down.

### Note on the environment

This box rebuilds the toolchain frequently, and the same runs showed loft invalidating and
recompiling `loft_random` / `loft_graphics_native` cdylibs mid-suite ("loft-ffi's source changed
since it was built"). That churn plausibly widens the window, but it is not required for the
failure: the `-P8` runs above reproduced it with no rebuild in progress.

