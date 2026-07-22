# UPSTREAM-PLANS.md — the loft-lang/plans crawler depends on

> crawler is a **consumer** of the loft ecosystem (the `loft` toolchain + the libraries +
> the `lavition` engine). The ecosystem roadmap is tracked in **[loft-lang/plans](https://github.com/loft-lang/plans)**
> as one GitHub issue per plan — **`@PLN<N>` = issue `#N`** (`…/plans/issues/N`). *Design* lives
> in each code repo's `plans/` (or loft's `doc/claude/plans/`) dir; the issue is the tracker + the
> one-place overview. This doc is crawler's **read-only map** of the upstream plans that touch us:
> what we depend on, what blocks us, and what our local prototypes feed back. We never edit those
> plans here — when an upstream defect bites, we file a bug ([FILING.md](FILING.md)).

**crawler is not (yet) a tracked plan there.** loft-lang/plans tracks the language, the libs, and
the `[audience]` demo games (generative-art `@PLN6`, dryopea `@PLN49`, bumper-airplanes `@PLN51`,
tic-tac-toe `@PLN39`) — crawler is a separate repo with its own `plans/`. Only `@PLN9` names
crawler in its body (asset paths). Plan migration is `@PLN27`; if crawler is ever tracked centrally
it lands as a `[audience]`/`[game]` issue there.

## The live blocker — `@PLN26` (native C-ABI linking)

**[#26 — Native C-ABI linking across all link paths (retire the rlib/SVH collision everywhere)](https://github.com/loft-lang/plans/issues/26)** · `subject:loft` · *closed state, but `status:active` — the
executable path ships; library-cdylib path is an open residual gap.*

This is the upstream plan behind **`make viewer-release` not going native**. Its invariant — *a
native consumer never pulls a `#native` package's Rust crate graph into its own rustc link; every
path binds the package cdylib by C-ABI* — is shipped for the native **executable** backend, but the
issue explicitly lists the **library-cdylib path (the viewer/graphics consumer) as still on the
rlib → the `StableCrateId`/SVH collision is NOT fixed there.** That is exactly crawler's case:

| crawler-filed bug | what it is | `@PLN26` relation |
|---|---|---|
| [loft#396](https://github.com/loft-lang/loft/issues/396) | registry `graphics` `#native` not registered for `--native` → P269 | the consumer link-path gap |
| [loft#274](https://github.com/loft-lang/loft/issues/274) | `cfg_if` SVH `StableCrateId` collision at link | the rlib-collision class `@PLN26` retires |
| [loft#398](https://github.com/loft-lang/loft/issues/398) | `make install` leaves a binary↔stdlib/cdylib desync | adjacent (native install robustness) |

When `@PLN26` closes the library-cdylib path (or `@PLN21`'s prebuilt cdylibs ship), crawler's
`make viewer-release` goes native (~22×) with no crawler change. Track: [s5-viewer-smooth.md](plans/2-chunked-lod-world/s5-viewer-smooth.md)
V0/V4/V5; [FILING.md](FILING.md).

## Direct dependencies (crawler runs on these today)

| `@PLN` | title | status | why it matters to crawler |
|---|---|---|---|
| **[#18](https://github.com/loft-lang/plans/issues/18)** | [loft] Engine host (C71/N9 execution model) | active | `story.loft` is hosted on `engine_host::run` (the games kernel). Our adoption track: [plans/6-games-kernel/](plans/6-games-kernel/). |
| **[#21](https://github.com/loft-lang/plans/issues/21)** | [libs] Prebuilt native libraries (no rustc) | finished | the cdylib-not-rlib model that makes `graphics` rustc-independent (avoids E0514); the path to a no-compile native viewer. |
| **[#11](https://github.com/loft-lang/plans/issues/11)** | [loft] `Data` as a store | active (G2/M5 done) | store-backed IR = our save/replay substrate + the cold-start cache; underpins C71/`@PLN18`. |
| **[#9](https://github.com/loft-lang/plans/issues/9)** | [lang] Program-relative paths | finished | source-relative asset loading — how the view resolves `assets/sprites/<key>.png` by name. **Names crawler.** |
| **[#7](https://github.com/loft-lang/plans/issues/7)** | [libs] `gridmesh` grid→mesh primitives | finished | the chunk-local mesh primitive lineage behind `worldmesh`/the chunked-LOD viewer. |
| **[#3](https://github.com/loft-lang/plans/issues/3)** | [libs] Library extraction | finished | the `lib/* → external repos` split crawler consumes (`hex_grid`/`graphics`/…); our side: [EXTRACTION.md](EXTRACTION.md). |

## Extraction targets — our prototypes feed these (future lib trackers)

These are thin trackers (content still in loft's local `doc/claude/lib_plans/` dirs, pending the
`@PLN27` migration). They are the **upstream generalisations of what crawler is prototyping** —
when they're built, crawler's bespoke code should collapse onto them (the reusable-library goal).

| `@PLN` | title | crawler prototype that feeds it |
|---|---|---|
| **[#71](https://github.com/loft-lang/plans/issues/71)** | [libs] Terrain heightmap | `chunk`/`chunkgen`/`chunkmesh`/`worldmesh` + the Ortler import (`plans/1-ortler-worldgen-fixture`). |
| **[#70](https://github.com/loft-lang/plans/issues/70)** | [libs] Viewer generalisation | `src/viewer.loft` (chunked-LOD + Ortler dual screen + fly camera). |
| **[#72](https://github.com/loft-lang/plans/issues/72)** | [libs] Renderer backend boundary | the kernel↔view split (DESIGN architecture invariant); the moros/3D target. |
| **[#60](https://github.com/loft-lang/plans/issues/60)** | [libs] Asset pipeline | `assets/sprites/` by-name resolution + the `draw` tool. |
| **[#64](https://github.com/loft-lang/plans/issues/64)** / **[#61](https://github.com/loft-lang/plans/issues/61)** | [libs] Game client library / Game infrastructure | the bundle system, `gameflow` intent seam, `observe` spectator. |
| **[#56](https://github.com/loft-lang/plans/issues/56)** | [libs] Rigged characters | the character-model direction (DESIGN §2; Player→character core). |
| **[#48](https://github.com/loft-lang/plans/issues/48)** | [loft] spacial index (Morton/Z-order) | chunk addressing / global-raster tiling in `chunk`. |

## Language/idiom plans behind our loft survival guide

The defensive idioms in LOFT-NOTES.md → "survival guide" trace to these (mostly finished — the
idioms remain as defence-in-depth):

| `@PLN` | title | status | crawler idiom |
|---|---|---|---|
| **[#2](https://github.com/loft-lang/plans/issues/2)** | [loft] Vector store-lifetime watermark | finished | the loft#320 family — pre-allocated array + index-write for hot collections. |
| **[#25](https://github.com/loft-lang/plans/issues/25)** | [lang] Nullable sequences (`vector<T>` in the null model) | active | unifies the `v[i] ?? fallback` / H6 sentinel rules our code follows. |
| **[#17](https://github.com/loft-lang/plans/issues/17)** | [loft] Three-state boolean | finished | why `!x` is a null-test on non-bools (compare `== 0`). |
| **[#15](https://github.com/loft-lang/plans/issues/15)** / **[#43](https://github.com/loft-lang/plans/issues/43)** | serialisable cross-branch refs / store durability | future / active | the save-format + replay direction (plan #6 save track). |

## An observation for the owner — crawler is absent from loft's Goal C check

Read from `../loft/doc/claude/GOALS.md` (2026-07-22). **Goal C — Capability via dogfood** is
measured by a consumer build matrix, and its rows are: the branch-review viewer, the tracker
indexer, the `lib/markdown` suite, and *"the games **moros / dryopea** build and run against
current loft"*. **crawler appears once in the whole document, and not in that check.**

That looks like a gap worth closing, and the argument is **not** that crawler stresses loft
hardest — it does not, and `crew_punk` will eventually stress it far harder on axes crawler
never touches (six concurrent clients, phones, audio timing). The argument is that crawler is
**furthest ahead**: it reaches surfaces other consumers have not yet, so it fails *first*. That
is the definition of an early-warning row.

The evidence is on the record: the 2026.7.2 bump turned crawler's whole gate red, and **two of
the three failures were silent data corruption, not compile errors** (LOFT-NOTES.md § survival
guide) — exactly the latent-UB failure mode Goal A's north star names. crawler has also
produced loft#320, #336, #339, #392, #496, #497 and the JSON `kind()` split.

Adding a `crawler: make test` row would cost loft nothing and give both sides earlier warning.
**Not filed — this is a goals-doc change in the owner's own repo, so it is raised here rather
than acted on.**

Note that Goal C is **deliberately paused** behind the soundness and structure floors
(*"building a game on either un-cleared floor means building on a base that can still shift
under you"*). That is coherent — but it does mean crawler is currently doing **unmeasured
dogfood**: absorbing toolchain breakage without being one of the rows that would make it
visible upstream.

## Keeping this current

This is a hand-curated snapshot (2026-06-17). loft-lang/plans is the source of truth — re-derive
with `gh issue list -R loft-lang/plans --state all`. Update this doc when an upstream status flips
that unblocks crawler (especially `@PLN26`/`@PLN21` → native viewer, `@PLN18` → kernel adoption).
Per the docs-first rule, knowledge lives here; agent memory holds only a pointer.
