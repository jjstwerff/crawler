# FILING.md — how (and why) to file loft tickets

> crawler is a **consumer** of loft (the toolchain) and its libraries (`graphics`, `hex_grid`,
> `hex_terrain`, …). **We never fix loft in this repo.** When a loft/lib bug bites crawler, we
> **file it upstream**, **work around it**, and **keep moving**. This doc is the full procedure;
> CLAUDE.md → "Filing loft bugs" is the quick reference and points here.

## Purpose — why we file at all

- **Separation of concerns.** loft is a separate project with its own repo, agents, and release
  cadence. A bug we hit in codegen / native-link / store-lifetime / the interpreter / a stdlib or
  graphics function is *their* fix, not a patch we carry. Filing keeps the fix where it belongs.
- **Don't block crawler.** A filed issue + a recorded workaround lets crawler keep shipping while
  loft fixes it on their schedule. Never stall crawler waiting on an upstream fix.
- **The upstream backlog is the shared brain.** A precise, reproducible ticket is what lets the
  loft team (or the loft agent) pick the work up cold. A vague "native is broken" is noise; a
  minimal repro + expected/actual + labels is actionable.
- **Avoid re-discovery.** Filing (and checking for existing filings) stops us from re-debugging the
  same trap twice — see the worked examples below; several are recurring loft idioms we now design
  around.

## What to file — and what NOT to

**File** a reproducible defect (or a clearly-scoped enhancement) in **loft itself or a loft
library** that crawler hits: codegen/`--native`/`--check`/wasm, the interpreter, store-lifetime,
the package/native-link system, a stdlib or `graphics`/`hex_*` function, formatter, etc.

**Do NOT file:**
- **A crawler bug.** If the defect is in our `src/` or a bundle, fix it here.
- **A duplicate.** **Always search first** (next section) — the issue may already be filed, even
  closed-with-workaround (e.g. the `cfg_if`/SVH collision is #274).
- **A design question or a "how do I".** Those are conversations, not bug tickets.
- **Something you can't characterize.** If you can't say *expected vs actual* and can't produce
  *some* repro (standalone or in-crawler recipe), keep investigating before filing.

## Where it goes

- **loft core** (toolchain, interpreter, codegen, native, store, stdlib): `loft-lang/loft`.
- **A specific library's bug** (a bug *in* `graphics`/`hex_grid`/… as opposed to loft's handling of
  it): that **library's chunk repo** instead.
- **Standing grant (CLAUDE.md, 2026-06-12):** file loft issues for rough spots **proactively** — no
  per-issue authorization needed. Use the shape below, then work around and keep moving.

## Procedure

### 1. Search for an existing issue first

```sh
gh issue list -R loft-lang/loft --state all -S "<keywords>"      # e.g. "cfg_if", "StableCrateId",
gh issue list -R loft-lang/loft --state all -S "native graphics" #      "registered native crate"
```
If it exists: if **open**, add your repro/data as a comment; if **closed with a workaround**, apply
the workaround (and only re-open / comment if it genuinely **regressed** after a clean rebuild).

### 2. Build a minimal reproducer — verify on BOTH backends

- **Shrink to a standalone `.loft`** if you can: the smallest program that triggers it.
- **Verify on both backends** — `--interpret` *and* `--check`/`--native`. Record which fail. (Many
  bugs are backend-specific; "both-backends" is a label and a strong signal.)
- **Record expected vs actual** precisely (exact error text, exit code, "no output, exit 0", …).
- **If it won't shrink standalone**, file with the **in-crawler recipe** (the exact command +
  file) — context-dependent store-lifetime bugs often only reproduce in the full program; that's a
  valid filing (precedent: #303, #336, #392).

### 3. Pick labels (exactly the required set)

| dimension | values | rule |
|---|---|---|
| severity | `sev:high` \| `sev:medium` \| `sev:low` | **exactly one** |
| workaround | `wa:clean` \| `wa:partial` \| `wa:none` | **exactly one — VERIFY the claim** before labelling |
| area | `area:native`, `area:codegen`, `area:store-lifetime`, `area:runtime`, `area:packages`, `area:stdlib`, … | **one or more** |
| source | `hit-by:crawler` | **always**, for anything crawler surfaced |
| kind/extra | `bug` \| `enhancement`; optionally `both-backends`, `user-facing` | as applicable |

`wa:clean` = a fully-equivalent loft-safe workaround exists (no behaviour loss). `wa:partial` = a
workaround exists but costs something. `wa:none` = blocked until fixed. **Don't claim a workaround
you haven't run.**

### 4. File it

```sh
gh issue create -R loft-lang/loft \
  --title "<area-tag> one-line symptom → root cause if known" \
  --label "sev:high,wa:clean,area:native,hit-by:crawler,bug" \
  --body-file /tmp/issue-body.md
```
Body shape (the bug_report form):

```markdown
### Summary
<one paragraph: what fails, where, and the root cause if known>

### Minimal reproducer
<standalone .loft, OR the in-crawler command + file>
\`\`\`
loft --check --native <flags> repro.loft     # FAILS: <exact error>
loft --interpret <flags> repro.loft           # OK (or: same failure)
\`\`\`

### Expected
<what should happen>

### Actual
<exact error text / exit code / "no output, exit 0">

### Workaround (if any)
<the loft-safe shape crawler now uses>
```

### 5. Work around + capture knowledge

- Apply a loft-safe workaround and **keep moving** — never block crawler on the fix.
- **Docs-first (CLAUDE.md rule):** if it's a recurring trap, add it to the **loft survival guide**
  in CLAUDE.md (the idioms that keep biting) and/or the relevant plan doc — agent memory holds only
  a pointer. The repo is the shared brain.

## Worked examples (real crawler-filed issues)

| # | what | label highlights | lesson |
|---|---|---|---|
| #392 | silent program abort when a fn-returned `vector<single>` is passed to native `gl_upload_vertices` | `sev:high`, `wa:clean`, `area:store-lifetime`,`area:native` | inline the buffer build; don't route `vector<single>` through a returning helper |
| #274 | `#native` crate built without loft's `RUSTFLAGS=-g` → shared-dep SVH mismatch → colliding StableCrateId at link | `sev:medium`, `wa:clean`, `area:native`,`area:packages` | rebuild native cdylibs **with loft's RUSTFLAGS** (`make rebuild-native-cdylibs`); the `cfg_if` collision in the viewer's native build is this |
| #320 | capture-append-reassign on a struct's vector field empties it | `area:store-lifetime` | use the pre-allocated array + count + index-write idiom for hot collections |
| #336 | `vector<text>` literals in large fns hang/panic the interpreter | `area:runtime` | branch-selector fns returning `text`, not text-vector literals |
| #338 | swapping vector struct elements via a temp link duplicates | `area:store-lifetime` | sort by selection into a fresh vector |
| #339 | a thin arity-reducing pub wrapper around a big-struct-returning pub fn panics codegen | `area:codegen` | don't wrap; pass the defaulted arg at call sites |

(These also live as defensive idioms in CLAUDE.md → "loft survival guide".)

## Open from the viewer-native work (2026-06-16)

- **`cfg_if` StableCrateId collision** in the viewer's `--native` build = **#274** (closed,
  `wa:clean`). Action: **not a new ticket** — apply the workaround (coherent native-cdylib rebuild
  with loft's RUSTFLAGS); only re-open if it persists after a clean rebuild.
- **P269 — consumer `--native` can't register a registry `#native` GL lib** (`gl_create_window`
  etc. → "no implementation in any registered native crate"): **filed #396** (`sev:medium`,
  `wa:partial`, `area:native`,`area:packages`, `hit-by:crawler`) with a verified standalone repro
  (`use graphics; gl_create_window`, both backends). The worked example for this procedure.
- **`make install` can silently leave a mismatched binary↔stdlib → loft panics on every run**
  (`02_files.loft` `#pure`/`#rust` syntax vs an older binary; root cause = the `Makefile:186` `cmp`
  guard + non-atomic binary/stdlib copy + no post-install smoke): **filed #398** (`sev:high`,
  `wa:partial`, `area:packages`, `hit-by:crawler`). Surfaced trying to install the loft that
  unblocks native; the toolchain must be working after `make install`, not hand-repaired.
