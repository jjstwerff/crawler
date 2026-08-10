# STATE.md — where things stand (2026-08-10)

Branch **`combat`**, tree clean and pushed, **full gate green** (`make test` — PASS, 99 rows in
**1m49s**, 8-wide, on installed loft md5 `0dabaa1e169e`; 2026-08-10). Written as a handoff: read
after a `/clear`.

**Read [`VISION.md`](VISION.md) first** — what this is for, why "properly" is load-bearing, and
where crawler sits in the stack.

> ## → NEXT: **plan #17** — make the settlement's SUPPLY depend on ground that can become unsafe.
>
> **The roster is `#11` 3D world · `#13` scoped identity · `#17` safe supply** (decided
> 2026-08-09 from evidence, `plans/README.md` → *The active roster*, cap of three). The work
> is in **`#17`**, and `#16` queues explicitly behind it — #16's `M3` re-authors 18 race
> blocks with a Handiness value, and what Handiness is *for* is decided in #17.
>
> ✅ **`S4` SHIPPED TOO — and `F6` is measured on the world players actually start in.**
> *I-SAY: what a worker says about its work is read from the **same term** that decides
> whether it goes*, so the line cannot drift from the world. Three of the design's four
> signals were already shipped (short batches, a skipped rotation, an unwalked route); the
> fourth is the only one readable **without a baseline** — over three days the stall differs
> by **2 potions against 1**, which says nothing to a player who has never seen the other
> number. Now a bumped worker says *"A goblin on the picking ground, north-west of here. I'll
> not go while it stands. The stills will run dry."* — creature and bearing **derived at the
> moment of asking**, zero new keys. ⚠ **The shipped world is safe at genesis and the trouble
> ARRIVES** (that is `S5`'s design), so the gate ticks before reading: on `story.loft`'s own
> `GEN_SEED` the first worker reports at **tick 19**, and is still reporting at tick 599.
>
> ✅ **AND THE PLAN NOW MEASURES THE WORLD PLAYERS START IN** (2026-08-10). It measured world
> **777** throughout while `story.loft`'s `GEN_SEED` is **1337**, so every number it published
> described a world nobody plays. `stocktest` and `incursiontest` are switched (`safetytest`
> was already 1337). The overland is a fixed contract wilderness so the **town is identical**
> — what a seed varies is monster placement, which is this plan's entire subject.
>
> | four days | at peace | under pressure |
> |---|---|---|
> | **1337** (shipped) | 3 deliveries, stock 0..1 | **0 deliveries, stock 0..0** |
> | 777 (as published) | 7 deliveries, stock 0..4 | 1 delivery, stock 0..1 |
>
> ⚠ **The A/B separates MORE sharply on the shipped seed; what falls is PEACE.** The cause is
> measured: the gatherer spends **1023 of 1600 daylight ticks frozen mid-route**, stalled at
> safety borders while ambient wildlife drifts across an unescorted 14-hex walk (777: 887 — a
> difference of degree, not kind). That is the design working, and **`S7`'s pickets are its
> designed answer**, not a number to tune. So the gate's peaceful bar is **2 against a
> measured 3** and the margin is thin on purpose. Re-verified able to go red on the new seed,
> which is the check that matters when a gate changes worlds.
>
> **`S0`–`S3` and `S5` are shipped, ARMED and CLOSED.** `hex_safe` is the safety **category**
> and `npc_may_enter` the term that makes a worker refuse unsafe ground (`safetytest`, each
> claim seen **both ways**). `S3` adds the stock — a number per producer, `raised − drawn`,
> capped so it can run out — plus the first real bundle `production` section. **`S5` adds the
> danger**: a den at the far end of the ground the town can walk sends raiders at the
> settlement's most exposed *work*, and clearing the den ends it permanently — eligibility,
> never a schedule (`incursiontest`, 7 rows).
>
> ✅ **`I-SAFE` HOLDS END TO END (2026-08-10).** On the **shipped** world, four days with the
> den alive against four with it cleared: **0 deliveries against 3**, and the store never
> holds anything at all under pressure. (First measured on world 777 as a week — 1 load and 1
> potion against 17 and 11 — before the seed was corrected, below.) `stocktest` row 7 is the
> A/B and is verified able to go red.
>
> ⚠ **`S5`'s recorded cause was wrong on both counts, and the correction is the lesson.** It
> blamed `npc_gather`'s trapping arm; attributing every bag-fill to its place shows that arm
> fired **0 times**. What actually raised output was **`npc_may_enter`'s escape hatch**: a
> worker already in danger may enter any neighbour (or a raid *traps* it), so a large unsafe
> region is freely traversable by anyone caught inside — the gatherer stopped stalling at
> safety borders and ran a 13-hex leg in **17 ticks instead of ~75**. Danger was buying it a
> faster commute. Closed by two terms: the bag fills only at the work site and only on safe
> ground, and **nobody travels to work that is unsafe** (`S2`'s never-built second half).
> → `plans/17-safe-supply/README.md`

## What moved on 2026-08-09/10

- **The starting town is now CONTESTED** (plan #17 `S5`, 2026-08-10). Worldgen sites a **den**
  at the far end of the ground the town can walk — a goblin leader (mlvl 5) **17 hexes out**
  with three sleepers — and each dawn a living den with fewer than `RAID_CAP` of its own out
  sends one raider at the settlement's most exposed work. Kill the leader and it never sends
  again. ⚠ **That makes the opening harder on top of a curve nobody owns** (below): the answer
  is to go and clear it, which is the first danger in the game with a *cause*. Levers are the
  den's distance, its monster tier and `RAID_CAP` — **DESIGN §3a pillar #8's call, flagged not
  decided**. ⚠ **And the den exists because the mechanism had NO CONSUMER**: all three of world
  777's ruins sit in windows with 0 guards and 0 civilians, so `send_incursions` was correct
  code that could never fire on a settlement anywhere in the shipped world.
- **The home window is anchored at the alpine town** — `ov_home_town(o)` picks the town with
  the greatest height reach rather than the literal `ov_towns[0]`, so the starting economy has
  both valley fields and high ground. Producers 5 → 6. ⚠ **Its headline — "the gatherer finally
  exists", picking grounds 0 → 124 — was measured WITHOUT a reachability check, and none of the
  124 could be walked to**; the gatherer only actually worked on 2026-08-10 (below). ⚠ **Two real costs:** the **sea economy is
  gone** (roles 5/6/8 and the harbour no longer spawn), and the **starting neighbourhood is
  harder** — the nearest hostile at `surfacetest`'s vantage went from a jackal (mlvl 1) 43
  hexes out to a **gnoll (mlvl 6) 8 hexes out**, and a level-1 hero standing there died on
  tick 13. That is DESIGN §3a pillar #8's (gentle curve) business and is **not addressed**.
- **Plan #1 shipped the real-Ortler alpine bands** the study derived and never applied, and
  fixed an exact defect in `ov_kind_at` — meadow was 0.3 ‰ because the snow branch ate it.
- **The toolchain is 2026.8.0** — and it is `../loft`'s *working-tree build*, 15+ commits past
  the tag, rebuilt while gates run. `make test` stamps version + **md5** in its header, because
  `loft --version` is not provenance. Two logs with different md5 are not comparable.
- **The gate is quiet and green — 98 test files, 99 rows** (`playtest` runs 3×), after the five
  unwired tests were wired in on 2026-08-10 and a duplicate `canopytest` row removed. **It runs
  in ~1.5–2.5 min** (measured 2026-08-10, 8-wide: 1m29s / 1m47s / 2m29s warm, 2m43s with a cold
  native cache, 3m15s at `GATE_JOBS=1`; the pool absorbs the cold penalty — 14 compiles ≈ 140 s
  of rustc cost +56 s of wall clock), down from 10–13 min via two changes: the 14 tests (16 rows) that held most of the
  wall clock now run `--native-release` while the rest interpret (`tools/run_tests.sh` →
  `NATIVE_TESTS`), and rows run **`min(8, nproc-2)` at a time** — 8 on this box, and the two
  bounds mean different things: the **cap is measured** (flat past 8 — what is left is one long
  test, not many short ones, so a 64-core box finishes no sooner), the **`nproc-2` is courtesy**
  to everything else running here. `GATE_JOBS` overrides; a non-integer is refused, not limped
  through. ⚠ **Parallel was BLOCKED and is now open**:
  LOFT-HANDOFF's cdylib-wiring defect made a parallel suite fail a different test each run;
  re-probed 2026-08-10 on 2026.8.0 over **13 full passes** at -P4/-P8/-P16/-P24 (plus one with
  every native row compiling at once) — all green. A row that is red under load and green at
  `GATE_JOBS=1` is that defect, not the test. ⚠ **Per-row seconds are now wall time under
  contention** (`matrixtest` 1.0 s → 16.9 s at 8-wide): they rank the roster, they are not
  measurements. ⚠ **Budget by CACHE STATE too, not only by load**:
  those rows cost ~10 s of rustc each whenever their compile cache is cold, which a kernel edit
  does to the 40 tests that transitively `use sim` and a `make install` in `../loft` does to all
  of them. One `ok <secs> <name>` line per test (`·native` marks a compiled row), a closing line
  for anything over 5 s, `GATE_VERBOSE=1` for the old stream, `GATE_NO_NATIVE=1` to put every row
  back on the interpreter. ⚠ To prove a change behaviour-preserving, diff the **per-test** logs
  (`/tmp/story_<name>.log`), not stdout. The tail that sets the clock (2026-08-10, 8-wide,
  wall under contention): `stock` **48s** · `replay` 36s · `incursion` 35s · `mesh` 31s ·
  `play` 29s · `safety` 28s, and they move a lot run to run. `stocktest` became the tail when
  its row 7 grew a second arm — two 4-day surface weeks, which is what an A/B costs.
- **`../moros` has its own agent** and is **READ-ONLY** (`CLAUDE.md`) — findings become
  documents here; how one reaches the other project is the user's call.
- Also new: `CRAFTING.md`, `ADOPTION.md` (library pull side, P0–P4 shipped), `MOROS.md` (what
  moros must write for crawler: nothing), `tools/libcheck.py` (9 gated rules), the playthrough
  harness (`src/playtest.loft` + `scripts/*.play`), and the `production` bundle seam — which
  got its **first real content** on 2026-08-10 (`desert_surprise` → `"alchemy":
  ["naga_antivenin"]`), so the merge's bundle arm finally executes.

## The design position — eight statements, and they compose

Settled 2026-07-22. Most *resolved* a tension rather than adding a rule. This table is an
index; each statement's home is where it is argued.

| | the statement | where |
|---|---|---|
| **goal** | hand **small teams** the hard parts already solved; crawler is the proof, the substrate is the product | `CLAUDE.md` |
| **reusable** | over-engineer only where **others build on it** — *does this make a hard part reusable by someone else?* | `CLAUDE.md` |
| **bounded** | depth in the **derivation**, shallow at the **interface** — the Dwarf Fortress trap, entered one reasonable feature at a time | DESIGN §3a pillar 0 |
| **measured** | real dimensions by default, **gated**, so a wrong world can be *proved* wrong; stylisation is the implementer's choice | `SCALE.md` |
| **diorama** | *the diorama is the research, the brick is the finding* — author to discover, ship the recombinable part | DESIGN §3a pillar 1 |
| **eligible** | author **richly**, ship it **condition-gated, never scheduled** — the trap is scheduled content, not authored content | `SCRIPTING.md` |
| **souls** | most players will miss most of it, **and that is the mechanism working** — replayability is the by-product | `SCRIPTING.md` |
| **scope** | BG3's **capability** is reachable; its **uniqueness volume** is neither reachable nor needed | DESIGN §3b |

The through-line: **variety is produced, not stored**, so the content bill scales with
mechanisms instead of assets. What does not scale — and does not need to — is **direction**.

**The whole argument is [`VISION.md`](VISION.md)** (written for a person, not a build). It also
records: crawler is the **furthest ahead, not the most demanding** — `crew_punk` will overtake
it on axes crawler never touches; the stack's two **unbuilt** layers (the modding abstraction,
the behaviour layer); and that the behaviour layer **splits** — movement over the field is a
`hex_*` concern, deciding what to do is genre-shaped `roguelike-kit`.

## What got built

**The tracker is the truth, not a hand-kept table** (`CLAUDE.md`):
`gh issue list -R jjstwerff/crawler --label plan --state all`.

Briefly: **#9 canopy trees** and **#10 props** finished · **#11 3D world** active (P0–P4 built
and SEEN; P5's routines built, but the fit and the two-storey fixture are `hexbody`'s, above) ·
**#13 scoped identity** active · **#17 safe supply** active and where the work is (`S0`–`S3`
shipped and armed). **#5 geometry is `status:future`**, not active — this file said otherwise until
2026-08-10. Plus the render path (`scenemesh`/`figure`/`tools/glbview.py`), the scale contract
(`SCALE.md`, gated), and **`hex_field` 0.1.0 extracted** to `loft-libs-world` with its `EdgeSet`
merged — which took crawler's own edge storage out entirely (−192 lines, `edgetest`/`sweeptest`
unchanged).

⚠ **Plan #1 is `status:future` but was worked on 2026-08-10** (the alpine bands, the meadow
defect). That is legitimate — #17's measurement handed a worldgen defect to the plan that owns
the area — but if it continues, the label is wrong and should move.

## Decisions taken (don't re-litigate these)

1. **Scale** — one hex step = **1.5 m** (architecture); terrain is the *same* hex at 15 m
   (`OV_STEP`). The contract is code and gated. Library thresholds are **dimensionless**; only
   the metre is the consumer's. → `SCALE.md`
2. **Library/content seam** — *a library's enumerations are of MECHANISMS and are closed; a
   bundle's enumerations are of THINGS and are open.* → `BUNDLE.md`
3. **Props are objects, not field features** — own level, derived placement, state stored for
   decisions and derived for consequences. → `PROPS.md`
4. **Stencils are small fields, not bitmaps**, and rotate **exactly**. → `EXTRACTION.md`
5. **3D replaces the 2D view** (plan #11 P9); actors are camera-facing **boards** carrying the
   existing top-down PNGs for now — deliberately wrong — on the way to **glTF humanoid (VRM)**
   meshes. The presentation **seam** is what makes that swap free.
6. **A wall's THICKNESS decides its layer.** Below one hex step it is a property of the TYPE,
   rendered not rasterised — an **edge**; at or above it, a **band of cells**. Same threshold
   `SCALE.md` set for the domestic staircase. Drawn as cells a 7.5 × 6.0 m cottage loses **59 %
   of its floor** (27 → 11) and renders as two faces 1.5 m apart. So one routine serves house
   walls, fences, road sides and curtain walls — road sides are just the boundary of the road's
   own region. → `plans/11-3d-world/BUILDING.md` §1
7. **Passability is a property of the TRAJECTORY, never of a position.** We never ask *"is the
   character inside an object"* — we ask *"did its path cross a boundary it may not cross"*. So
   "inside a wall" is not a state to detect and push out of; it is a state that **cannot be
   reached**. The answer must not depend on `dt`. Measured on the old point-sample model: at a
   fall-sized step it missed **54 %** of the walls in the way. **Thin geometry is where physics
   engines die** — a thin barrier tunnels, and its push-out resolves to the *wrong side*. On the
   exact-integer lattice a wall is a 1-D boundary, so that family is **unrepresentable rather
   than handled**. We build no clamping or OOB-recovery machinery, because that machinery *is*
   the composing-corrections bug. → plan #11 **I-CROSS**
   - *Outstanding:* **the fence is still a filled cell** (`tiles[i] = 5`) — a 1.5 m thick
     barrier, the thin thing thickened until a point-sample model could see it. P2 put the
     kernel on an `EdgeSet`, so the machinery is in place; the fence moves onto it in P5
     (`BUILDING.md` order step **E**).
8. **`overland` owns settlement placement. We integrate with it; we never rewrite it.**
9. **The village is the subject**, not the castle (landscape composition).

## Open, and whose call it is

- ✅ **The town holds its own centre** (user's call, 2026-08-10). The site veto was the first
  thing that ever *read* `hex_safe` about a workplace, and it surfaced two numbers that were
  true before it and inert: the **mine** unsafe **400/400** ticks a day (an ogre camped on it,
  40 hexes from any guard) and the **market square** **143/400** (a jackal within `THREAT_R`,
  while every guard walked a ring at radius 15 and only *transited* the seat it was posted to
  hold). The mine is the plan's designed lever working. The market was answered by giving the
  **guard master** the centre and the market seat as his beat — 2 hexes apart, so both stay
  inside `GUARD_R` from every point of the walk: **215/400 → 0/400**, and civilian-ticks with a
  workable site 4710 → **6000 of 6800** (the rest is the mine). ⚠ **The ring lost nothing** —
  legs are `gd2 * 120°` and its opposite over `gd2 in 0..ngd`, so guard 3 already walked guard
  0's leg; a **duplicate** is what it spent. → `plans/17-safe-supply/`
- **The starting neighbourhood is now hostile at level 1** — a gnoll (mlvl 6) 8 hexes from the
  vantage, a level-1 hero dead on tick 13. The alpine anchor bought the gatherer and cost the
  onboarding curve. **DESIGN §3a pillar #8's business, and nobody owns it yet.** The user's call
  whether the answer is placement, the curve, or a starting-window guarantee.
- **The sea economy no longer spawns** in the starting town (roles 5 boat / 6 ship / 8 merchant
  ship, and the harbour with them), so *"goods from BEYOND the map"* (`OVERLAND.md` §584) is not
  reachable from the start. A fisher remains on the river. Accepted as a cost, not yet answered.
- ✅ **The gatherer works — after three defects, each hidden by the last** (2026-08-10). It had
  never gathered anything in any world: its schedule sent it between two *far* points so it
  never came home; civilians stepped **greedily** so it froze at the first concave obstacle;
  and its picking ground was sited nearest-first **with no reachability check** — on world 777
  there was no path at all, and of 9801 hexes the town can walk to just **498**, all grass and
  road. All three showed the same symptom, *stock stays 0*, which reads exactly like a town at
  peace. Fixed: the bag steers the trip, **civilians got the flow field** monsters have always
  had (one field per destination + movement class, built once and kept), and siting now flood
  fills first and ranks terrain (alpine shelves → woodland → grass). → `plans/17-safe-supply/`
- ✅ **The five unwired tests are wired** (2026-08-10) — `figtest`, `gentest`, `gridtest`,
  `montest`, `walltest` were on disk and in no row of `tools/run_tests.sh`. All five pass and
  each gates its `OK` marker on a real assertion, so they can go red. `canopytest` was also
  listed **twice** with the same file, marker *and log path* — it ran twice and overwrote its
  own log — so the duplicate went and the labels merged. **93 rows → 97.** The standing check is
  in `CLAUDE.md`; run it when adding a test, because nothing else complains.
- **The wall fit** — in `hexbody`, not here (see NEXT). Everything downstream renders the zigzag.
- **Does a flip preserve the LAYOUT or the READING?** `HOUSE.md` §7 claims the massing mirrors
  *and* the facade *and* interior readings are unchanged. Those cannot all hold once the massing
  is chiral, which §7 itself requires: a `(side, t)` feature lands at `mirror(original (s, 1−t))`,
  so relative to a chiral element (a terrace) the feature moves. Also suspected: §9's gate
  expects 12 distinct footprints collapsing to 6 without the terrace, but a *centred* terrace is
  still mirror-symmetric about the other axis. **Not yet measured in-engine** — the rectangle
  fixture cannot see it. Decide before building the two-storey fixture.
- **Library extraction was on the critical path and has largely LANDED** — `hex_grid`,
  `hex_field`, `hex_edge`, `hex_way`, `hex_roof`, `hex_terrain` are consumed from the registry
  and the crawler forks are deleted (`tools/libcheck.py` gates it: *no forked module*). What
  remains is priced debt, not a blocker: `hexplace` shares zero function names with `hex_place`,
  so switching is a rewrite. Contract: `EXTRACTION.md` → *The editor as the second consumer*.
- **Split `EdgeSet` out of `hex_field.loft`** into its own file — the merge is done, but one
  1350-line module with two writers is what cost ~40 minutes. ⚠ **This is now a `loft-libs-world`
  change, not a crawler one** — `hex_field` is a published package pinned in `loft.lock`, so it
  is a PR + a release there, not an in-tree edit. Any project may contribute; nobody owns it.
- **The eligibility/trigger system is designed but unbuilt** (`SCRIPTING.md`). Today the only
  trigger in the game is one hardcoded `infest_trigger == "boss_slain"` check. **Its gate is
  unlike the others:** it already has a known second consumer with *harder* requirements
  (crew_punk has no director), so design it against that and crawler gets the good version free.
- **`LOFT-HANDOFF.md` H1/H2, G5, N1/N2 and now N3 are unfiled upstream.** N1 (`%` as an
  if-branch tail breaks `--native` codegen) and N2 (`save_png` returns false under `--native`)
  are from 2026-07-23; both have standalone repros and N1 has a verified workaround already
  applied. **N3** (2026-08-10) — returning a struct read out of a `vector<T>` leaks one store
  record **per call**, measured 22 calls → 21 records, with a negative control that isolates it
  to the return rather than the table build. Unbounded in a long-running program; crawler hit
  it on a per-dawn path.
- **Plan #10 P9 leftovers** — the cart is a placement fix; the doors may dissolve under an
  eye-height camera. **`mesh_trunk` not migrated** to `prim_drum`. **Plan #5 `vm_surf`** —
  render-side attribution, the one genuine gap in DESIGN §7.2b.

## Lessons worth carrying

**1. The exact-integer lattice keeps paying off where it was never aimed.** Chosen for boundary
tracing, it then made the area round-trip exact, removed a spurious lean in the canopy
partition, made the relaxation's **termination decidable**, and made stencil rotation exact.
Five unrelated problems, one decision.

**2. Rendering finds what numeric gates pass.** Ten faults survived 36 green gates. Plan #11 P0
extended it: **a first-person camera found a world too small for its own player** (1.51 m eaves,
a 1.45 m door, a 1.75 m figure) which every raised camera had missed.

**3. The failure mode is never a check that fails — it is one that PASSES FOR THE WRONG
REASON.** The single most productive rule in this repo. Fifteen instances, and they arrive by
genuinely different routes:

- geometry too *thick* to show the bug (a solid wall hides tunnelling; only a thin one shows it)
- a perturbation *below the quantisation it was read through* (0.02 rad against a hex
  circumradius of 1.0 rounds back — 0/172 fired)
- a plain *tautology* (`project(d,0,h)` vs `project(d,0,0.0+h)`, "worst 0px")
- a *discriminator that cannot vary* (seeds 777 and 4242 give an identical surface — the
  overland is a fixed contract wilderness, so the window is the discriminator, not the seed)
- a control that **went blind when the world changed under it** — `mergetest` proved two index
  maps were the same permutation, then the merge deleted its subject, leaving it comparing
  `edgeset_new` to `edgeset_new`. *A test whose subject has been deleted does not become a
  regression test.*
- a *symmetry that makes the check trivial* — a mirror-symmetric massing makes a flip the
  IDENTITY, so "we validated all 12 orientations" on a rectangle really validates 6
- a **model of the code standing in for the code** — a Python blueprint measured the wall-run
  overhead as 39 % where the engine measures 15.5 %, because its side-classification credited
  corner edges to the wrong side. The wrong number reached a design doc. *If the primitives
  exist, measure in the engine; a model can disagree with the original silently.*
- a **subject that walked away from the assertion** (2026-08-10) — `meshtest` asserted a sand
  hex's colour; the home window moved to the alpine town, which has no sand, so it found none
  and reported `sand-exact=false` **without failing**. It did not go red, it went *vacuous*. The
  same move broke three other tests loudly, and those were the lucky ones: ⚠ **the world's
  geography was written into four tests as literals** (`sim_teleport(75, 75)`, a wizard tower at
  `(-3,-2)`, a nest at `(-1,-4)`, a gate at `(0,-2)`). Each now *asks the world* —
  `sim_window_of`, `sim_wizard_tower`, `sim_ruin_count`/`sim_ruin_pos`, `sim_desert_gate_world`.
  *A literal coordinate in a test is an assertion about a world that is free to move.*
- a **loop that never iterates** (2026-08-10) — `producttest` asserted the `production`
  merge's bundle arm inside `for i in 0..bundle_production_len(p)`, and no bundle declared a
  `production` section, so the bound was 0 for all seven producers and the assertion never ran.
  The seam compiled, the gate was green, and the bundle half had never executed. *A seam with
  no consumer is a seam with no test* — ship the content that exercises it in the same change.
- a **worker who never arrives** (2026-08-10) — the gatherer's supply chain was gated on an
  arrival that the schedule made impossible and the terrain made unreachable. Nothing failed:
  stock simply stayed 0 forever, which reads exactly like "the town is at peace". ⚠ *An input
  that is always zero and an input that is correctly zero are indistinguishable at the
  output* — which is why `S3` measures the supply rather than trusting the coupling.
- a **mechanism with no consumer** (2026-08-10) — `send_incursions` was correct, gated, and
  could not fire on a settlement in any window of the shipped world: all three ruins sit
  where there are 0 guards and 0 civilians. Its own gate passed by generating the window the
  source was in. *A gate that constructs the situation proves the mechanism, not the game* —
  worldgen now ships a den where the settlement is, and the gate runs in that window.
- a **bar written for a healthy town, left in front of a starved one** (2026-08-10) —
  `stocktest` row 7 ran a single arm and asked only "did a delivery arrive". The moment the
  coupling closed it went on passing at **one delivery and one potion in a week**. It is an
  A/B now: peace must look like a working economy, pressure must not, and the two are
  separated by a margin. *A threshold outlives the world it was chosen in.*
- an **objective at the point of its own cancellation** (2026-08-10) — raiders marched at the
  market square, which is exactly where `hex_safe`'s guard term holds ground safe. Seven days
  of raiding left the picking ground unsafe for **0 ticks** and the week's deliveries at 4,
  identical to no raiding at all. *Arriving is not pressing*; aim at what a settlement depends
  on, not at its centre.
- a **cap that was never the binding constraint** (2026-08-10) — `RAID_CAP` is 2 and exactly
  one raider ever appeared, because "farthest reachable hex" is the deepest point of a pocket
  and so has the fewest ways out. The geometry capped it at 1 and said nothing. *When a
  measured number sits below its limit, check what else could be setting it.*
- a **guard that outlived its reason** (2026-08-10) — `incursiontest` asserted a marching
  raider was `!awake`, correctly, while waking meant switching to the chase. The fix that made
  a raid keep formation removed the confound, and the assertion then failed on healthy
  behaviour. *An assertion encodes a mechanism; change the mechanism and re-derive it.*
- a **gate measuring a world nobody plays** (2026-08-10) — plan #17 measured world **777**
  from `S0` to `S5` while `story.loft` ships **1337**. Every number it published was true and
  about the wrong town: the overland is fixed so the *town* is identical, but a seed varies
  **monster placement**, which was the plan's whole subject. Switching it moved the peaceful
  supply from 7 deliveries to 3. ⚠ *A seed in a test is a claim about which world the result
  describes* — and when a gate changes worlds, the check that matters is that it can still
  **go red** there, not that it still passes. The whole tree is on 1337 now; the only other
  seeds left are **deliberate second worlds** (`4242` in `stocktest`/`placetest`, `7777` in
  `savetest`), where being a *different* world is the point.
- a **predicate borrowed across the actor it was written for** (2026-08-10) — `surfacetest`
  picked the hero's vantage with **`hex_safe`**, which is plan #17's *civilian* predicate: no
  hostile within `THREAT_R`, or a guard within `GUARD_R`. A civilian is invulnerable and
  nothing hunts it, so 6 hexes is plenty; the hero is neither — **hostiles wake and walk at
  him** — so 6 hexes is about nine ticks, and he died on tick 9. `S1` recorded the *mirror*
  of this (every danger signal answered "is it dangerous to the player" when a civilian
  needed asking). ⚠ *A safety predicate is written for one kind of actor and does not
  generalise in either direction* — and `hex_safe` is now `pub`, so it reads like a general
  test and is not one.
- a **measurement that counted the mechanism PLUS the world** (2026-08-10) — `questtest`
  asserted the brood thickens toward the surface as `inf1 > inf2` over `count_glyph(level,
  "J")`, which counts every snake including the ones ordinary generation places. On 777 that
  read `4 + 4 = 8` against `11 + 0 = 11` and passed; on the shipped seed depth 2 holds 7
  natural snakes, both totals are 11, and a healthy mechanism reads as broken. Subtracting
  each depth's boss-not-slain population cancels the wildlife and leaves **exactly** the
  bundle's declared 11 and 4 — so the row became an identity read from `world_placement()`.
  ⚠ *If a count includes anything you are not asking about, the world is a term in your
  result — subtract a same-world control and the threshold usually becomes an identity.*
- a **signal with no baseline to read it against** (2026-08-10) — three of `S4`'s four
  visibility signals shipped before `S4` did, and none of them closed `F6`. A stall holding
  **2 potions instead of 1** is a real difference and an unreadable one: a player who has
  never seen the other number cannot see it, and an idle worker is indistinguishable from a
  worker who is simply idle. ⚠ *An observable difference is not an observable signal — ask
  what the player is comparing it to.* The fourth signal (a person saying so) needs no
  comparison, which is the whole reason it works.
- a **blocker with no cause, no exit and no representation** (2026-08-10) — `occupied_hex` did
  not test `alive`, and a slain actor keeps its coordinates forever, so **every kill left a
  permanent roadblock**. A monster moves on and a wall is in the flow field the movers descend;
  a corpse does neither, and `npc_step` only takes a strictly-improving neighbour — so one
  corpse in a one-hex gap freezes a worker for good, and the symptom is *a civilian standing
  still*, the same symptom as five other defects in this plan. ⚠ *A slow leak has no incident
  to investigate; the map simply holds less ground after every fight.*
- an **escape hatch that swallowed its own rule** (2026-08-10) — `npc_may_enter` must let a
  worker already standing in danger move, or a raid *traps* the people the rule exists to keep
  out. Correct, and never followed through: a large connected unsafe region is therefore
  freely traversable by anyone caught inside it. A gatherer swallowed by a raid stopped
  stalling at safety borders and ran a 13-hex leg in **17 ticks instead of ~75** — *danger
  bought it a faster commute*, and output went **up**. ⚠ *An exemption is a rule about its
  own scope; measure how much of the domain it takes.*
- a **cause named from the code instead of from an instrument** (2026-08-10) — `S5` recorded
  that trapping "fills the bag anywhere" as the reason danger did not cut output. It reads
  correctly in the source. Attribute each bag-fill to its **place** and that arm fired **0
  times** in either arm of the week: it was not a supply path at all. The measurement existed
  (a stock number moved), the *attribution* did not. ⚠ *A diagnostic that reports the symptom
  but not its cause invites a plausible cause to be written down instead.*
- a **test the gate never runs** (2026-08-10, now fixed) — five test files sat in `src/` and
  appeared in no row of `tools/run_tests.sh`, plus one listed twice. They compiled, so nothing
  complained; they simply never executed. *Being written is not being wired* — and note the
  roster is the only place that knows, so the check has to compare `src/` against it.

**All of them printed a healthy-looking number** — or, in several, no number at all. The rule that would have caught every one:
*state what would have to break for this control to go red, and check that is reachable.* Hence
a **negative control in every phase** — and note that a negative control which stays green is a
result, not a formality (P1's did exactly that, revealing two ungated arms of a rule).

**4. Read the code before writing the claim.** Twice in one session a confident structural claim
was contradicted by the source — *"build new, extract settled"* (unbuildable: a stencil **is** a
field) and *"the two halves have never met"* (they meet at `sim.loft:3005`). Both were caught
**after** being written into a plan. Describing architecture from docs and naming produces
claims plausible enough to survive review.

**5. Two agents in one working tree has no undo.** `git add` stages into the *shared* index, so
one commit carried an unrelated file under the wrong message; and `hex_field.loft` had two
writers for ~40 minutes, leaving it transiently uncompilable **for both consumers**. The rules
come in pairs — *stage and commit in one command*, and *`git diff` before committing in a shared
tree*. Detection is `stat -c %Y` twice. **The structural fix is a smaller file, not private
copies** — the reason to keep sharing is on the record: `edgeset_equal` compares the halo
because of a negative control the *other* agent found. → `EXTRACTION.md`, `LOFT-HANDOFF` **G5**.

## How to run things

```sh
make test                     # the headless suite (98 files / 99 rows, ~1.5-2.5 min) — ONCE before committing
GATE_NO_NATIVE=1 make test    # …with every row interpreted (is a red row OURS or the backend's?)
GATE_JOBS=1 make test         # …serially (is a red row REAL, or the cdylib concurrency defect?)
loft --interpret --path ../loft/ --lib ../loft/lib/ src/<x>test.loft   # + the bundles/ --libs
loft --native-release …       # same, for a test that costs >10s interpreted (~10s to compile once)
python3 tools/glbview.py build/x.glb out.png --eye 30,-46,12 --target=-4,0,6 \
     --shadow 640 --stats          # --stats = coverage per MATERIAL, never by pixel colour
```

**Iterate on ONE test** (~0.5 s), not the whole gate (~4 min). Read `/tmp/story_<name>.log`
rather than re-running `make test` to check a result.

**`--native` pays only where a test is BIG — and that is a per-test call, not a flag.** Measured
2026-07-23 on the `hexbody` gate: warm, native was **0.34 s vs 0.47 s interpreted — ~1.4×**,
because those tests are too small for codegen to matter and startup dominates. That reading
still holds *for tests that size*, and it does not carry to crawler's heavy ones: measured
2026-08-10 across all 97 both ways, `questtest` goes **76.2 s → 3.5 s (21.7×)**, `travel`
**50.5 → 3.7**, `surface` **47.1 → 3.5**, with **zero output divergence on any of the 97**.
The whole-roster totals are what decide it: **593 s interpreted · 88 s native-warm (6.7×) ·
1058 s native-cold (1.8× SLOWER)** — cold costs ~10 s of rustc per test, so a blanket flip
loses on the ~85 tests that run in 1-3 s. Hence the hybrid now in `tools/run_tests.sh`
(`NATIVE_TESTS`, the ≥10 s rule). ⚠ Still true of the *rendering* path: `save_png` returns
**false** under `--native` (LOFT-HANDOFF **N2**), so a `Canvas` render writes no PNG — no gate
test calls it, but a diagnostic script that does must stay `--interpret`; and `%` as an
if-branch tail expression breaks native codegen outright (**N1**).

⚠ **`loft-libs-world` is NOT consumed from a sibling checkout any more** (changed 2026-08-09,
ADOPTION.md **P3**). `hex_grid`, `hex_field`, `hex_edge`, `hex_way`, `hex_roof` and
`hex_terrain` all resolve from the **registry**, pinned in `loft.lock`; the crawler forks
(`hexform`/`hexedge`/`hexway`/`hexroof`) are **deleted**. The only `--lib` in the Makefile is
`../loft/lib/`, because `engine_host` is not published — and it says so there. **A `--lib`
sibling tree outranks the registry, so every extra one is a silent override**: that is exactly
how the lock came to describe a build that could not compile. Test against an unreleased
sibling on the **command line for that run**, never in the Makefile.

**`xvfb-run` IS installed** — the native `gl_screenshot` path and `make probe` work. For plain
2D diagnostics the `graphics` `Canvas` (`fill_triangle`/`save_png`) needs no GL or Xvfb at all;
`../hexbody/src/houseshot.loft` is the worked example. `glbview.py` needs neither either.
