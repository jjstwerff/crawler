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

Both are `sev:high`: one crashes the compiler, the other silently produces wrong data.

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

## Filed

*(nothing yet — move entries here with their issue numbers)*
