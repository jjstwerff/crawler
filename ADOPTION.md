# ADOPTION.md — consuming the `hex_*` family instead of copying it

The **pull** side of the seam `EXTRACTION.md` describes from the push side. Extraction asks
*what belongs in the library layer*; adoption asks *what is already there and is still sitting
here as a copy*. Same seam, opposite direction, and the two must agree — a routine that is in
the library and also here is a **fork nobody agreed to**.

Written 2026-08-09, against loft **2026.8.0**, `loft-libs-world` @ `178faf5`.

---

## The governing rule — no project owns a library

> **No first-class project owns a library.** Not loft, not moros, not crawler, not lavition. A
> library must be useful to *everybody*, and **any project may add what it needs** — the only
> constraint is that it must not break the others, which is what the **library contract**
> (`api_compatible_with` / `data_compatible_with`) exists to enforce.
>
> — user ruling, 2026-08-09

⚠ **This is the authority over everything below, and it corrects the obvious reading of the
measurement in the next section.** A 100 % API match between a crawler module and a package
does **not** mean "that code is ours and has come home". It means **there is one construction
and two copies of it**, and one of them is in the place where every project can reach it. The
argument for adopting is not provenance — it is that a duplicate of a shared asset is a fork.

Three consequences that this document would otherwise get wrong:

1. **Provenance is not an argument, in either direction.** "We wrote it" does not entitle
   crawler to keep a copy, and "hexbody wrote it" is not a reason to refuse a package. The
   only questions are *does the library have this construction* and *what does switching cost*.
2. **"Not adopting" is not the same as "keeping ours forever."** Where a package solves a
   problem differently than crawler does, the resolution is eventually **convergence in the
   library**, not two permanent implementations — see *The line*.
3. **Crawler may add to these packages.** If crawler needs something the family lacks, the
   move is to **add it to the package under the contract**, not to grow a private copy. A
   local module that exists because "the library didn't have it" is a fork with a good excuse.

---

## The measurement that decides everything

The question *"how much of the family can we reuse?"* is not a matter of taste. There is a
discriminator, it is cheap, and it separates the packages into two groups with nothing in
between: **the fraction of a crawler module's function names that the package also declares.**

| crawler module | lines | best-matching package | shared fn names | reading |
|---|---:|---|---:|---|
| `hexedge` | 660 | `hex_edge` | **39 / 39 = 100 %** | it *is* the package |
| `hexway` | 377 | `hex_way` | **21 / 21 = 100 %** | it *is* the package |
| `hexroof` | 521 | `hex_roof` | **20 / 20 = 100 %** | it *is* the package |
| `hexwheel` | — | `hex_body` | 1 (`wheel_angle`) | different construction |
| `wallgeo` | — | `hex_shape` | 0 | different layer |
| `hexseat` | — | `hex_place` (`hexseat`) | 0 | same *name*, different code |
| `hexmatch`, `hexskel`, `hexlink`, `hexplace`, `hexprim`, `hexcanopy`, `hexcache`, `hexderive`, `hexhinge`, `hexpart` | — | — | 0 | crawler's own |

**There is no middle.** Three modules score 100 %; everything else scores 0 or 1. That gap is
not a coincidence — it is the record of what actually happened: those three constructions were
lifted verbatim into the library during the 2026-07-24 lib-split, and crawler kept running its
copies. The rest of the family reached the library by a different route (the `hexbody`
workshop) and solves adjacent problems a different way.

⚠ **Read that as topology, not as title.** Per the governing rule, none of it is crawler's and
none of it is hexbody's; the 100 % rows are simply the ones where **switching costs nothing
because the code is the same**, and the 0 % rows are the ones where switching costs a rewrite.
That is a cost measurement, not an ownership claim.

So "reuse as much as possible" has a precise answer *for one step*, and it is smaller and safer
than the ambition suggests: **1558 lines, three modules, one commit.** The 0 % rows are not
refused — they are **deferred on cost**, and the way they eventually close is convergence in
the library, not two permanent implementations. See *The line*.

---

## The invariant

> **I-SAME — a module is adopted only when the package IS that module.** The proof obligation
> is then a **textual identity check**, not a behavioural one: nothing can regress, because
> nothing changed. Where the package is *different* code, adoption is a rewrite and this
> invariant does not license it.

Everything below is this one sentence applied. It is what makes the step provable in an
afternoon rather than argued about for a week, and it is what stops the step from growing.

Its companion, which does the work of saying *not in this step*:

> **I-LINE — the discriminator above sizes the step, it does not confer membership.** 100 %
> shared API ⇒ the same construction exists twice ⇒ adopt now, provably free. ~0 % ⇒ a
> different construction of a related idea ⇒ **a rewrite, priced separately** — deferred on
> cost, not rejected on principle, and never on provenance.

---

## The probes, and what they falsified

Run before any code, per `DESIGN-PROTOCOL.md`. **The clean form of I-SAME was false and had to
be weakened** — which is the point of running them.

| # | Claim | Probe | Result |
|---|---|---|---|
| 1 | The three are byte-identical modulo header + module rename | normalise both sides, `diff` | ⚠ **FALSIFIED** — 4 / 20 / 6 lines differ |
| 1b | …but every difference is semantics-neutral | read all 30 lines | **HOLDS** — see below |
| 2 | Deleting the local copies removes the name collisions | declared-name intersection, post-deletion | **HOLDS** — 0 type, 0 fn collisions |
| 3 | The rewrite surface is small | count `use` lines + qualified sites | **HOLDS** — 57 `use` lines, **0** qualified call sites |
| 4 | The three can be adopted independently | read the packages' own `use` lines | ⚠ **FALSIFIED** — they are a chain |
| 5 | The gate proves behaviour is preserved | run `make test` | ⚠ **FALSIFIED** — the gate is **red** |

### Probe 1b — the 30 lines, in full

Nothing here is hidden behind "cosmetic":

| where | difference | count |
|---|---|---|
| all three | licence header + the module's own name in its top comment | 4 |
| `hex_way` | local `L` → `seg_l`, `L2` → `len2` | 20 |
| `hex_roof` | `for pass in 0..4` → `for _ in 0..4` (the variable is unused) | 4 |

⚠ **The library copies are not merely equal — they are strictly ahead.** `L`, `L2` and the
unused loop variable are exactly the 2026.8.0 naming defects. loft 2026.8.0 now reads a
`CamelCase` local as a *type*, so `Na = 4` no longer declares a variable; that is what is
breaking `canopyopactest` today. **The upstream copies already have the fix; ours do not.**
Adoption is not a lateral move — it imports a repair.

### Probe 4 — the chain, and why the step is atomic

```
hex_field  ←  hex_edge  ←  hex_way  ←  hex_roof
```

Each package `use`s the one before it, and crawler's local copies mirror that chain exactly.
So a partial adoption is not a smaller step, it is a **broken** one:

- adopt `hex_edge` alone → local `hexway` does `use hexedge`, which no longer exists;
- adopt `hex_roof` alone → it pulls `hex_way` in transitively, and `hex_way`'s `Track`,
  `seg_len`, `pv`, … meet local `hexway`'s. Under 2026.8.0 that is now a **hard error at the
  use site** ("declared by more than one package"), not the coin-flip it used to be.

**P1 is one commit or it is nothing.**

### Probe 5 — there is no baseline, and that is the ordering constraint

A behaviour-preserving refactor is proved by *the gate saying the same thing before and after*.
Today `make test` is red: 66 of 86 pass, `canopy-opacity` fails with 25 errors, and **17 tests
plus `kerneltest` never run at all**. With no green baseline, an adoption failure and the
pre-existing failure are indistinguishable. Hence P0.

---

## Step 2 — counting the re-assertion sites

The protocol's brittleness measure is `N × silence`: how many independent places must restate
the invariant, and is forgetting one *silent*?

| site class | N | forgetting one is… | brittleness |
|---|---:|---|---|
| `use hexedge;` → `use hex_edge;` | 57 | **loud** — unknown module, compile error | **0** |
| qualified call sites | 0 | — | 0 |
| **which `hex_field` the build resolves** | **2** | ⚠ **SILENT** | **the real risk** |

**The whole design's brittleness lives in one row**, and it is not the row anyone would have
guessed. Crawler resolves libraries down **two paths that can disagree without a word**:

```make
# Makefile:87
LIB_DEPS := --lib ../loft-libs-core-main/ --lib ../loft-libs-world/ --lib ../loft/lib/
```

- `make test` / `make play` / `make check` compile the **working tree** of `loft-libs-world`;
- `loft.lock` pins the **registry tarballs**, which `run_tests.sh`'s loft-doctor smoke (no
  `--lib`) and any registry-only consumer use instead.

Those two are **already different**: the working tree gained `stencil_unstamp` / `_layers` /
`_all` on 2026-08-03; the registry is still `hex_field` 0.1.0 and has none of it. And the
manifest does not describe either path — `hex_field` is `use`d in **48 files and is absent
from `loft.toml`**; `random` is declared `>=0.2` and locked at `0.1.0`.

⚠ Adoption **multiplies this row by four** (`hex_field`, `hex_edge`, `hex_way`, `hex_roof`).
That is why P3 exists and why it is not optional bookkeeping.

---

## The failure paths

Written down first, because this is where the invariant became nameable.

| # | How it breaks | Caught by |
|---|---|---|
| F1 | Partial adoption → missing module, or duplicate bare names | P1 is atomic (probe 4) |
| F2 | Adoption blamed for a failure that predates it | P0 green baseline (probe 5) |
| F3 | Build and ship resolve **different** `hex_field` | P3 — one resolution path |
| F4 | Upstream edits land in our build with no local change | P4 — pinned + a drift check |
| F5 | A local fix to `hexedge` has nowhere to go once we don't own it | P4 — the contribution rule |
| F6 | A **future** library name collides with a crawler name | P4 — the standing grep |
| F7 | `Stencil` means two things in one graph | P2 |

F6 and F7 are the ones that bite later. `crawler::Stencil` (a bundle room template:
`sk`/`shape`/`radius`/`boss`/`guard`/`pool`) and `hex_field::Stencil` (a geometry stamp:
`sn_cells`/`sn_heights`/`sn_labels`/`sn_edges`) are two unrelated things wearing one name in
one dependency graph **today**. It compiles only because a local definition shadows an
imported one. It is a trap with a fuse, not a bug.

---

## The phases

### P0 — a green baseline (blocking, ~1 file)

Rename the seven `CamelCase` locals in `src/canopyopactest.loft` (`Ns`, `Lm`, `Nm`, `La`,
`Lb`, `Na`, `Nb`) to lowercase. Re-run `make test` until green, including the 18 tests that
currently never execute. **Record the passing output — it is the baseline P1 is measured
against.**

*Note the shape of this: P0 is the same defect the library copies already fixed. We are
paying it here because we did not adopt.*

### P1 — adopt the three, atomically

1. `git rm src/hexedge.loft src/hexway.loft src/hexroof.loft` (1558 lines);
2. rewrite 57 `use` lines: `hexedge`→`hex_edge`, `hexway`→`hex_way`, `hexroof`→`hex_roof`;
3. fix the one stale comment (`jointest.loft:30`, `hexway::way_mark`);
4. declare all four in `loft.toml`: `hex_field`, `hex_edge`, `hex_way`, `hex_roof`.

**Definition of Done: `make test` produces the P0 output.** Not "passes" — *the same output*.
Under I-SAME anything else is a real difference and must be explained before the commit lands.

### P2 — name hygiene

Rename `crawler::Stencil` → `RoomStencil` in `src/worldtypes.loft` and its uses. It is bundle
vocabulary, not geometry; the geometry meaning belongs to `hex_field` and crawler should stop
competing for the word. Closes F7, and removes a shadow that a future reader will misread.

### P3 — one resolution path (the chokepoint) — **DONE**

The step that actually reduces brittleness, and the only one that does.

**THE DECISION: the registry is authoritative.** A `--lib` sibling tree *outranks* the registry
copy, so every entry on that line was a silent override waiting to fire. The rule is now one
sentence: **the only legal `--lib` is a package that is NOT published, and it must say why in
the Makefile.** Today that is exactly one — `../loft/lib/` for `engine_host`, which has no
registry entry; it goes the day `engine_host` is published. To test against an unreleased
sibling, pass `--lib` **on the command line for that run** — an override that outlives the
experiment is the defect below.

⚠ **This was not a new policy. It was an intent already written on that line and never
triggered** — *"after a registry release these move to version deps and the worktree flag
drops."* Both repos were published on 2026-07-24 and the flags stayed. An intent with no
trigger is not a plan, and the cost of the gap is the next paragraph.

#### What the two paths had already silently disagreed about — the load-bearing find

| package | `loft.lock` said | the build actually used | |
|---|---|---|---|
| `random` | **0.1.0** | **0.2.0** (working tree) | ⚠ |
| `hex_terrain` | 0.1.0 | 0.1.1 (working tree) | |
| `hex_edge`, `hex_way`, `hex_roof` | *absent* | working tree | |

⚠ **The `random` row is the one that matters: the lock described a build that could not
compile.** `src/sim.loft` uses `random::RandStream`, which is a **0.2.0** API and does not
exist in 0.1.0. So the pinned version had been wrong — not merely stale — for as long as the
`--lib` line covered for it, and nothing reported it, because *the path that worked was never
the path that was written down.* That is the exact failure this phase exists to remove, found
by measuring the two paths against each other rather than by anything going wrong.

#### The version question, kept separate on purpose

Refreshing the lock moved `random` **0.1.0 → 0.3.0**, and `random` is the seeded RNG behind
crawler's determinism invariants (`replaytest`, scene_key-identical worlds). A silent sequence
change there is not a regression the gate would call a failure — it would simply be a different
world. So the bump was **not taken on faith from a version number**: it was measured, by the
same normalised-output diff P1 used.

✅ **MEASURED, AND IT HELD.** 88 OK, exit 0, and the diff against the P1 baseline contains
**zero non-diagnostic lines** — every `println`, every number, every banner identical. So
`random` 0.3.0 yields the same sequences as the 0.2.0 the build had been quietly using, and the
worlds are unchanged. The diagnostic delta is **37 removed, 0 added**, all of one kind (`null`
stored into a non-null `integer` return) — the registry copies are *cleaner* than the
working-tree ones crawler was silently compiling against.

⚠ **Note what the evidence does and does not cover.** This says the bump is safe *for what the
gate exercises*, which includes the determinism gates. It is not a proof that no sequence
anywhere differs. Had a single number moved, the response was already decided: pin `random` at
0.2.0 and take the bump as its own measured step.

⚠ **The compatibility contract could not help here, and that is worth knowing.**
`api_compatible_with` / `data_compatible_with` were declared across the libraries on
2026-07-28, but they are **additive manifest fields that only reach the index on the next
publish** — and nothing crawler depends on has been republished since. So **not one package in
crawler's graph carries a published floor**. Until that changes, "is this bump a drop-in?" has
no answer in the registry and must be answered by building.

#### A defect found on the way — the lock does not describe the declared set

`loft update` reports `hex_edge: already on the highest satisfying version` and writes **no
lock entry**. The entry appears only once something *compiles* against the package: `hex_edge`
landed when `make check` built `story.loft`, and `hex_way` / `hex_roof` only after a test that
uses them was checked. So a freshly-declared dependency is absent from `loft.lock` until an
unrelated build happens to exercise it — the lockfile lags the manifest, silently. Filed; see
`LOFT-HANDOFF.md`.

#### Also fixed here

- `graphics` floor `>=0.2` → `>=0.5`; CLAUDE.md has required 0.5.0 (the len/size flip) all
  along, and only the lock was keeping it honest.
- `.loft/api/*.api` stubs regenerated for all ten packages. `.gitignore` already exempts that
  directory from the `.loft/` ignore (loft#362) — they are meant to be committed.

### P4 — the standing rules

Four sentences that make the state stay true:

1. **No project owns a library.** Crawler is one consumer among several; so is moros, so is
   hexbody, so is loft itself. A library serves all of them or it is in the wrong place.
2. **A module that exists in the library is consumed, never copied.** A copy is a fork,
   regardless of who wrote the original.
3. **A change to library code goes to the library** — including one crawler needs and nobody
   else asked for. **Adding is allowed and expected**; what is forbidden is *breaking*, which
   the contract (`api_compatible_with` / `data_compatible_with`, declared 2026-07-28) makes
   checkable rather than a matter of goodwill. No local patch, no private divergence.
4. **Before adding a public name, grep the siblings** — a name added in `loft-libs-*` can turn
   a consumer red with no local edit (moros' `CLAUDE.md` states this from the other side).

Add to `CLAUDE.md` alongside the existing architecture invariant.

⚠ **Rule 3 has a corollary this repo has been quietly violating.** "The library doesn't have
it" has never been a reason to grow a private module — it is a reason to *extend the library*.
Every crawler-local `hex*` module should be able to answer *why is this not in the family?*
with something other than "nobody moved it yet".

---

## The line — a price, not a border

The tempting next sentence is *"and while we're at it, adopt `hex_shape`, `hex_draw`,
`hex_place`, `hex_fit`, `hex_recover` and `hex_body` too."* The protocol calls this the
elegant absorption — the failure that presents as success — so it gets attacked rather than
celebrated. It does not survive the discriminator:

| package | what it actually contains | crawler's overlap |
|---|---|---|
| `hex_shape` | `hexwall` / `hexbox` / `hexarc` — exact-lattice wall *geometry* (`wall_step_k`, `wall_separates`, `wall_offset_signed`) | 0 fns. `wallgeo` builds room **outlines** from corners — a different layer, not a worse one |
| `hex_place` | `hexframe` / `hexseat` / `hexcombine` — hexbody's seating (rung A8) | 0 fns, despite `hexseat` sharing the *filename* |
| `hex_draw` | `hexsurf` / `housedraw` — the hexbody building geometry | 0 fns. crawler has no caller yet |
| `hex_body` | rigs, joints, poses, collision proxies | 1 fn (`wheel_angle`, vs `hexwheel`) |
| `hex_fit`, `hex_recover`, `hex_form` | `hexfit`/`hexdraft`, `formcensus`/`formfit`, `hexform`/`formtext` | 0–1 fns |

**Adopting any of these means deleting working crawler code and writing new callers against a
different API.** That is a rewrite with a rewrite's risk, and it must be justified on its own
merits — *"is this construction the better one?"* — not carried in on I-SAME's coat-tails,
which says nothing about it. `hex_draw`/`housedraw` is the strongest candidate for a *later*
plan, because plan #11's `BUILDING.md` wants exactly that and crawler has no implementation to
lose; it is still not this design.

⚠ **But a deferred row is a debt, not a settlement.** Under the governing rule, two
implementations of one idea in one library layer is the state to leave, not the state to
defend — `hexseat` and `hex_place::hexseat` are the sharp case: same filename, same problem,
0 shared functions, and **neither is entitled to survive on the grounds of who wrote it.**
Closing such a row has three legal moves and one illegal one:

| move | when |
|---|---|
| crawler switches to the package's construction | the package's is better, or good enough |
| the package **gains** what crawler's has, under the contract | crawler's construction is better, or covers a case the package doesn't |
| the two are genuinely different problems and get different names | the shared name was the only thing they had in common |
| ⚠ *keep a private copy indefinitely because switching is inconvenient* | **never** — that is the fork this document exists to end |

Whichever move applies, it is priced and scheduled on its own, and it is a `loft-libs-world`
conversation, not a crawler-internal one.

⚠ `hex_body`'s `wheel_angle` and `hexwheel`'s are a **pre-armed F6**: the day crawler adopts
`hex_body`, that name is an error. Noted here so it is found before it fires.

---

## Universal for the class — the indexing case

> **The goal is to grow everybody through libraries: a library's design must be universal for
> the CLASS, not for one project. So the indexing of walls / items / ground must be done in a
> way every project benefits from, in its own scope.**
>
> — user ruling, 2026-08-09

This is the governing rule's constructive half. *No project owns a library* says what may not
happen; *universal for the class* says what the design must be **before** it is worth putting
there. A package shaped to one game's scope is that game's internals in a shared directory.

### The class, stated once

Every project in this family has the same problem and has been solving it privately:

> **A stored identity is meaningless on its own; it is an INDEX into a table owned by a
> SCOPE.** Only `0 = nothing` is fixed. What differs between projects is not the mechanism —
> it is which scope owns the table (a region, a level, a bundle, a world) and what the entries
> are.

That last sentence is the whole design. The **indirection** is the library's; the **palette**
is the consumer's; the **scope** is a parameter, not a constant.

### It has been solved twice already, each time by half — measured, not asserted

| | ground / walls | items / actors |
|---|---|---|
| **crawler** | ⚠ **hard-coded** — `tiles: vector<integer>`, vocabulary in a *comment* (`0 floor, 1 solid wall`, tile 5 / 8 / 9), **36 sites** comparing a stored tile to a literal | ✅ **indirected** — bundles author string keys, `catalog.loft` merges them generically, the engine never names a bundle |
| **moros** | ✅ **being built** — plan 21: a byte is an index into a **region-owned** palette, `0 = nothing` the only fixed identity (329 uses, 22 of them true identity comparisons) | plan 21 says items get "their own mapping similar to the other mappings" |

⚠ **Neither project has both halves, and the halves are the same mechanism.** crawler solved
identity for *open* enumerations (content that bundles add) and left *closed* ones (ground,
walls) as literals; moros is solving the closed ones and has the open ones queued. Two
projects, two half-answers, one class — which is precisely the situation the rule exists to
end. Neither half should be finished privately.

⚠ **And crawler's solved half has leaked.** `itemfx.loft` dispatches mechanism on content key
(`if key == "potion_cure_light" || …`, **9 sites**) and `sim.loft` maps indices to content keys
(**15 sites**) — this despite the generated `spell_defs_gen` / effect-arm dispatch existing for
exactly that job. That is BUNDLE.md's standing check drifting, and it is the same defect as a
hard-coded tile: **an identity decided in code.**

### What "in their own scope" has to mean in the API

The reason this cannot be one project's design is that the projects' scopes genuinely differ,
and a mechanism that hard-codes *which* scope owns the table fails the class:

| project | the scope that owns a palette | why it differs |
|---|---|---|
| moros | a **region** of an open world | a desert, a mountain range and an ocean each want their own 256 |
| crawler | a **bundle**, resolved per world/depth | a stranger drops a bundle in and plays against an unchanged game |
| a level-based game | a **level** | "doesn't have the region border problem" (plan 21) |

So the library takes the scope as a **handle**, never as an enum of known scopes. If the
package has to be edited to add a new kind of scope, it was not universal.

### The seam this generalises

crawler already has the right sentence, one level down — **BUNDLE.md's library/content seam**:
*a library's enumerations are of mechanisms and are closed; a consumer's are of things and are
open.* Indexing is that seam applied to identity itself: **the library owns the indirection and
the contract; the consumer owns every entry.** What must NOT travel into the package is any
particular palette — crawler's `floor`/`wall`/`pool`, moros' `grass`/`road` — for the same
reason the metre must not (`EXTRACTION.md` → *The one thing that must NOT travel*).

### The obligation this puts on crawler

Not this plan's work, and named so it is not lost:

1. **Do not build a private fix.** Crawler's 36 tile literals must not be closed by a
   crawler-only palette — that would be the third implementation of one idea, which is what
   plan 21's `R1` stopped in moros.
2. **Bring the second scope to the design.** A design validated against one project is not yet
   universal for the class. crawler's bundle scope and its already-working open-enumeration
   half are the evidence moros' design needs to be checked against — that is a contribution,
   and under the governing rule it is welcome by default.
3. **Close the leak either way.** The `itemfx` / `sim` dispatch-on-key sites are crawler's own
   defect and do not wait on any library.

## What this does *not* do

- It does not touch the push direction. `hexcanopy` (canopy-first trees), the `SCALE.md`
  contract and `wallgeo` remain crawler's and remain extraction candidates —
  `EXTRACTION.md` owns that half.
- It does not resolve the **overlap-rule refutation**. `EXTRACTION.md:1081` and `:1148` still
  claim stencil stamping is *order-free*; upstream measured that on 2026-08-03 and refuted the
  payload half (occupancy is order-free; labels and heights are last-writer-wins). Those two
  lines are wrong and should be corrected — but that is a doc fix, not an adoption.
- It does not adopt `hex_terrain` further or drop it. It is declared and used in exactly one
  file; whether that is worth a dependency is a separate, smaller question.

---

## Honest risks

| risk | severity | why it is acceptable |
|---|---|---|
| Upstream drifts and our build changes underneath us | **high** — this is F4, and it is live *today* | P3 + P4 are the answer; the risk exists **now**, adoption does not create it |
| ~~`hex_field` 0.2.0 is not ours to cut~~ — **retired, and it was never real** | — | The registry 0.1.0 source is the working tree's **minus three functions**: `stencil_unstamp`, `_layers`, `_all`. Zero removals, zero modifications, and crawler calls none of them. So going registry-authoritative is behaviour-neutral for `hex_field` and needs **no upstream publish at all**. The blocker was assumed from a version number and dissolved on one `diff` |
| The P0 rename hides a second 2026.8.0 breakage in the 18 unrun tests | medium | P0 is not done until all 86 run; that is the point of doing it first |
| 57 mechanical edits go wrong | **low** | every failure is a compile error, none is silent (`N × silence = 0`) |

---

## The prediction, written down before the build

Per the protocol, so the build can disagree with it:

- **P0** — 7 renames, 1 file. `make test` goes green with all 86 tests running.
- **P1** — 3 files deleted (1558 lines), 57 `use` lines + 1 comment + `loft.toml` changed.
  **Net diff strongly negative. No new code.** `make test` output *identical* to P0's.
- **If P1 requires a single line of new logic, the invariant was wrong** — stop, and find out
  which of the 30 differing lines was not the semantics-neutral rename it looked like.

That last line is the design's own falsification test. It is cheap, and it fires automatically.
