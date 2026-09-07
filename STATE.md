# STATE.md — where things stand (2026-08-11)

## THE SHORT ANSWER — read ONLY this to start work

⚠ **Everything below this block is RECORD, not state.** It is the reasoning behind how we got
here, and it is read on demand — by grep, for one question — not top to bottom. This block is
the only part that must be current, which is why it is short enough to keep current.

| | |
|---|---|
| **branch / tree** | `combat`, clean, pushed |
| **gate** | green — `make test` PASS, **109 rows in 1m43s** 8-wide (2026-08-11 evening). It went red for one afternoon on something crawler did not do: `engine_host` (the one legal `--lib`, so it tracks `../loft`'s *working tree*) gained `pub fn turn()`, which made `story.loft`'s months-old `turn` local a compile error. **Unblocked by renaming the local to `turn_dir`** — the wire format did not change. ⚠ **The renaming is not the answer to the question**: whether a library's public `fn` should claim a consumer's *variable* namespace at all is **[loft#852](https://github.com/loft-lang/loft/issues/852)** (filed 2026-08-11, `needs-design`; the follow-up #756 deferred), and the structural fix (stop tracking a sibling's working tree) is `ADOPTION.md` P3's. Detail: `LOFT-HANDOFF.md` → **H11** |
| **doc gate** | `make doccheck` **green 2026-08-12**, and in `make test`'s prelude. Links resolve, backticked crawler paths exist, every root doc is in `CLAUDE.md`'s routing table, every nested doc is pointed at. It replaces two HAND audits, one of which miscounted its own evidence. ⚠ To name a deleted file write `` was `path` ``; a bare path reads as a claim it exists. `tools/doccheck.py` header = the rules |
| **render gate** | `make probe` **green 2026-08-11, all 15 checks at dmax=0** — first time since June, and the "stale goldens" were never stale: `worldprobe.loft` had a lost write (`vv = s.vis` mutates a COPY), so its scene built 0 remembered cells. `make check` now compiles every entry point and **fails on `lost-write`**. Not in `make test` (~10 min) — run it after render-side work. Record: `plans/7-render/README.md` |
| **live plan** | **#11 — 3D world** (`plans/11-3d-world/`). Done: P0–P4, P3b, P6, and **P5 steps A+B** (2026-08-11). Closed by ruling: P6b (layer cache declined) |
| **⚠ THE RULING THAT OVERRIDES THE PLAN'S TAIL** | **crawler adopts the moros editor's rendering engine and never derives from the common base** (user, 2026-08-11). So the **renderer surface is FROZEN** — `ADOPTION.md` → *The rendering engine is the editor's*. Waiting on moros publishing the packages as part of its **lavition editor** work |
| **what is open to work on** | anything **kernel-side** (the field, settlement simulation, bundles, world derivation). Plan #11's tail (P7 props, P8 sprites, P9's 2D retirement) is renderer-side and **waits** |
| **drawing (2026-09-07)** | the **`Lock` hair/fur brush** shipped in BOTH tools — `tools/draw.py` (the oracle; probes `tools/lock_probe.py`) and the `drawing` library (`../loft-libs-graphics`, branch `drawing-lock`, 0.4.0, **byte-identical**, 42/42 on both backends). The **formal-rules register** opened with it: `formal/draw.md` (23 rules, 1 open deviation `D-draw-1` = `sprite_draw.loft`'s sprite half), `@FR-` citations in both trees, `make rules` in the gate. `LIBRARIES.md` now reads the **locked** version (it had documented graphics 0.9.0 against a 0.5.0 lock) and says where to ask *what exists*. **The performance pass** started in `drawing` (`bench/`: loft bench + pure-Rust reference + `compare.py`; all fourteen rows hash-identical across interpreter, native and Rust) — the user's standard-to-be for every library (EXTRACTION.md DoD 7, rule `Perf-Weight`). ⚠ **Its first verdict is FAIL: loft-native is 10–50× behind plain Rust on every judged routine** (best of 3, 2026-09-07) — the loft N1 class (`codegen_runtime`/`DbRef` indirection), recorded as `D-draw-2` and filed as [loft#1426](https://github.com/loft-lang/loft/issues/1426); the algorithms themselves are byte-identical |
| **whose call, not mine** | (1) P6d — its premise dissolved with P6b; re-scope or close. (2) whether P5 step B's curved wall stays running as a marked swap-site. (3) how any crawler finding reaches moros. (4) the `drawing` side: merge `drawing-lock` → `main`, publish 0.4.0, refresh the corpus oracle copy in `../loft` (`corpus/oracle/draw.py`) so the corpus can carry a `Lock` scene — and then point crawler's sprite pipeline at `drawing`'s CLI, since **draw.py is the oracle and `drawing` is production** (user, 2026-09-07; SPRITES.md). (5) `D-draw-1`'s removal — sprites through `drawing` (needs graphics ≥ 0.8, the frozen-renderer ruling) or retire `sprite_draw`'s sprite half. (6) lifting the performance pass into `../loft`'s library standard (`LIBRARY_CHECKLIST.md`) — the convention is in `drawing/bench/` and EXTRACTION.md DoD 7, and `compare.py` is package-agnostic |

**Then read:** `plans/11-3d-world/README.md`'s phase table for the plan, `ADOPTION.md`'s
engine section before touching any renderer code, and `LIBRARIES.md` (generated) for any
signature in the `hex_*` family — never the package source, which is where the reasoning is.

---

**Read [`VISION.md`](VISION.md) first** — what this is for, why "properly" is load-bearing, and
where crawler sits in the stack.

> ## ✅ **plan #11 P6a IS BUILT (2026-08-11) — THE GROUND HAS HEIGHT, and the two readings agree at exactly 0.**
>
> **I-HORIZON's gate could not be run for the life of the project because there was only ONE
> reading** — `sim`'s surface generator sampled each hex's height out of the overland and wrote
> `(_, okind)`, so the number was dropped one character before it could be stored and the world
> was a flat plane in both renderers. It is two readings now: over the window's **404-hex
> boundary ring and its full diagonal the difference is exactly 0 wu**, with a negative control
> (ask the far side about the hex next door) that disagrees on **101 of 101**. `horizontest`,
> 6 rows.
>
> **THE VERTICAL IS NOW STATED, and it belongs to the world rather than to the plan** —
> [`SCALE.md`](SCALE.md) → *The vertical*. Rise takes the compression run takes, so there is no
> second dial, and the contract is one identity: `terrain_m_to_wu(OV_STEP) == HEX_LEN` — **one
> `OV_STEP` of natural rise across one walked hex renders as exactly 45°**. Both axes take the
> same factor, so every angle in the rendered world equals the real terrain's. The rejected
> reading (heights left natural) multiplies every slope by ten: 0.40 → 4.0, i.e. walls.
>
> ⚠ **Two residues were removed BY CONSTRUCTION rather than tolerated**, and both were float
> association order, not disagreement: near-vs-far read 9.2e-14 wu apart because the generator
> computed `ax + hx - cwx` and the far side `(ax - cwx) + hx` (now **one expression**,
> `window_hex_world` — one owner for where a level's lattice sits in the wilderness), and a
> shared corner came out 1.4e-14 wu apart depending which of its three hexes asked (`a+b+c` vs
> `b+c+a`; now summed in canonical order). Sub-picometre in metres — and *a tolerance would have
> cost the gate its discriminating power*, since it could not then tell rounding from a real
> frame error.
>
> **`src/ground.loft` is the surface**: a corner is the mean of the hexes meeting there (no
> cracks), a point is barycentric inside **exactly one of the triangles the floor fan draws** —
> so the camera stands on the surface it draws by identity, gated at 28 800 points against the
> plane computed the other way (worst 7e-15 wu).
>
> ⚠ **AND THE FRAME FOUND WHAT NO NUMBER COULD, TWICE.** (1) **Without shading the height field
> is invisible** — an unlit floor is its landcover colour whatever its slope, so a 40° hillside
> rendered as the same flat green as a meadow and the phase's whole deliverable could not be
> seen. (2) **Rock is ground you cannot walk on, not an absence of ground** — the floor was
> drawn only where you may stand, so a mountain drew as a HOLE ringed by a 2.8 m fence
> duplicating a cliff the height already describes.
>
> ⚠ **The picture was explained by an INSTRUMENT, not by reading the code** (`src/skyprobe.loft`).
> The dark band across the first frame looked like the mountain; the window's **290 blocked
> hexes are 33 rock and 257 BUILT** — it is **the town's own wall ring seen from its square**.
> The same probe refuted the competing reading (a hole in the mesh: the horizon profile over all
> ground and over only-drawn ground agree to 0.1° in every bearing) and confirmed the third: the
> start **is** in a bowl, 32–44° above the eye in 8 of 12 bearings, open at 60–120° — which is
> exactly where the camera looks. ⚠ That does **not** contradict *"mean walkable slope 0.403"*:
> that statistic is about the steps you take, this one about what you see, and an alpine valley
> town is both.
>
> **Height is a RENDERING property at this phase and nothing else** — passability is still the
> edge field, so a slope neither blocks nor slows. Whether a gradient should cost the walker
> anything is a gameplay question with its own keys.
>
> ## ✅ **AND THE FAR FIELD IS DRAWN (2026-08-11) — P6 IS DONE.**
>
> The wilderness past the window reaches **48 km**, and **the skyline it draws is the world's:
> worst 0.77°** across 12 bearings against a dense independent walk of `ov_height`. The
> construction is a **polar skirt whose ring 0 IS the window's own boundary** — a circle would
> leave a void at the rhombus's edge midpoints and overlap its corners — so the **seam is exact
> (0 wu over all 400 vertices)**, there are **no T-junctions**, and angular resolution is
> constant, which is the resolution a horizon is made of. No clipmap.
>
> ⚠ **The far field's negative control (render with, render without, diff the PNGs) earned its
> place on the first run, twice.** 108 000 uploaded vertices changed **exactly zero pixels** —
> the far plane was 400 wu and the skirt reaches 4100. *Vertices that change nothing look
> precisely like vertices that were never uploaded.* And after that was fixed it STILL changed
> zero pixels, for a reason that is not a defect: from the shipped spawn the far field is
> **100% occluded** (drawn alone it fills 47% of the frame, but the *near* rim at bearing 300
> already stands at 32°, outside a 60° vertical field). From the window's high rim it
> contributes 7%.
>
> ⚠ **The horizon row found THREE faults in itself before finding none in its subject** — 44.5°
> (it compared the skirt against the world when what is drawn is near ∪ far), 39.6° (**the
> skirt's angular index is not an angle**: samples run along the window PERIMETER, and a sheared
> rhombus is very unequal in bearing), 6.4° (the reference walked in 25 wu steps and missed a
> ridge 12 wu away — *a reference must be at least as fine as what it judges*), then 0.77°.
> Every one read exactly like *"the far field is broken"*.
>
> Also: **aerial perspective replaces the fade that saturated at 42 wu** (36 m) — its own comment
> called itself a stand-in for the horizon P6 derives. Exponential extinction over a stated 25 km
> visibility.
>
> ## ✅ **P6b's CRITERION IS BUILT (2026-08-11) — and priced with the compression in it, the parallax cache BUYS ONE LAYER.**
>
> I-PARALLAX is code (`src/parallax.loft`) and gated as pure camera math, no GL
> (`parallaxtest`, 4 rows). The gate reads the **error in pixels**, not the boolean — *a
> boolean that is always true and one that is correctly true look identical at the output.*
>
> ⚠ **THE COMPRESSION IS A TERM AND `DESIGN.md`'s TABLE OMITS IT.** That table prices a 2 km
> layer at 0.6 s of walking, treating the camera's translation and the layer's distance as the
> same kind of length. They are not: terrain is compressed 10× while the player walks at
> **architecture** scale, so a layer 2 km away in natural metres stands **231 wu** from a camera
> moving 1.73 wu/s. Cache life is **0.175 s, not 1.75** — and the gate asserts the ratio is
> **exactly `TERRAIN_COMPRESS`**, so it is the compression and not something else.
>
> ⚠ **And the criterion's own answer is that the near layers are not cacheable at all.** Over a
> 150 m walk, worst case:
>
> | layer | its nearest content | budget | over 100 frames |
> |---|---|---|---|
> | 0 | 1.0 km | **0.13 m walked** | under one hex step — **not cacheable** |
> | 1 | 4.0 km | **0.52 m** | under one hex step — **not cacheable** |
> | 2 | 15.9 km | 2.09 m | 100 renders — saves nothing |
> | 3 | 63.7 km | 8.34 m | **20 renders — saves 80%** |
>
> A layer whose whole budget is under one step cannot be reused for even one frame. That is
> I-PARALLAX *answering*, not failing: such a layer must be **geometry**, which is exactly what
> P6's skirt is.
>
> ## ✅ **DECIDED (user ruling, 2026-08-11): SKIP THE LAYER MACHINERY. THE FAR FIELD STAYS GEOMETRY.**
>
> The cache buys 1 of 4 layers; the alternative — the skirt, which already ships — costs nothing
> more. So **P6b closes without building the layers**, and the criterion stays in the tree and in
> the gate because it is the *evidence for the ruling*, and because the **flight/orbit regime**
> `DESIGN.md` reserves it for is where it becomes true (at 100 m/s the same layers die every
> frame, and at walking speed they die faster than the design thought — both come out of the
> same one function).
>
> ⚠ **A consequence to notice rather than absorb: P6d's premise largely dissolves.** There is no
> sky-box to switch *to*, so there is no switch distance and no two representations to agree —
> I-AGREE's near/far half is satisfied **by construction** (the skirt's ring 0 *is* the window's
> boundary, gated at 0 wu). What is left of P6d is the aerial-perspective blend, which is a look
> rather than an invariant. **Re-scope or close — flagged, not closed unilaterally.**
>
> ⚠ **And `DESIGN.md`'s cache-lifetime table is now known-wrong in the tree** (it omits the 10×
> compression). It is contradicted in `parallax.loft`, `parallaxtest` and here, but the table
> itself still reads as authoritative where it sits — worth correcting at the source next time
> that file is open.
> ⚠ Also measured: nine of twelve bearings are fully occluded by the near rim from the shipped
> start, so a cache keyed on VISIBILITY would save more here than one keyed on distance.
> → `plans/11-3d-world/RESULTS.md` → *P6a*, *P6b-far*.

> ## ✅ **plan #11 P3b IS BUILT (2026-08-11) — landcover is a texture derived from the field, and the design named the expensive way to make one.**
>
> **The world's appearance now comes off a world texture** (`src/worldtex.loft`, sampled in
> `view3d`) instead of per-hex vertex colour — I-PAINT, which is what P6's far-field layers were
> ordered behind. It is **exact on the world players start in**: `worldtextest` diffs the shipped
> raster against an independent trace+fill oracle over **488 032 in-window texels of seed 1337
> and reports 0 mismatches**, closing the follow-up `painttest` left in writing (*"the blob is
> synthetic — re-run this against a real traced landcover region"*).
>
> ⚠ **AND THE MEASUREMENT OVERTURNED THE DESIGN'S OWN MECHANISM.** `DESIGN.md` specifies `trace`
> the region → `fill_polygons` its loops and calls it *"nearly free"*. Timed in-program, per
> level: point-sampling each texel through `px_to_hex` is **44 ms native / 1244 ms interpreted**;
> trace+fill is **589 ms / 4017 ms** — **13× and 3.2×**. Both rasters are identical, so the
> choice is cost alone. `worldtex` point-samples; **trace+fill stays as the test's independent
> oracle**, which is a better job for it than being the producer.
>
> ⚠ **`fill` is the pole, not `trace` — the opposite of the prediction**, and `trace` costs the
> **same in both modes** (203 vs 209 ms) because registry libraries run native under
> `--interpret`. Worth remembering the next time a profile looks impossible.
>
> ⚠ **Two claims NARROW, and neither is retired.** The **2:1 axis-ratio constraint** P3b
> introduced is a property of the **fill**, which must break a tie when a texel centre lands on
> a boundary; point-sampling has no tie to break, so the constraint binds anything rasterising a
> traced loop (P6's layers, the editor) and not the world texture. And **`trace` is not
> retired** — the loops are what geometry and I-AGREE's silhouettes are built from.
>
> ⚠ **LOD and tiling are P6's, and the near field never needed them.** The *"23 gigatexels"*
> arithmetic is about the 151 km overland; the **level window** is 151 m across = 812×604 =
> **0.49 Mtexel, 2 MB**, one resident texture, no clipmap.
>
> ⚠ **The one link no headless gate reaches is GL's.** A vertically flipped texture passes every
> CPU check and still puts the wrong landcover under your feet. Closed by reading the frame:
> `shot3d` prints the kind of the hex the camera stands on, and the PNG's bottom-centre band is
> that ground — surface kind 0 read **(107,132,76)** against the palette's (107,133,76); dungeon
> kind −1 read **(182,173,140)** against (184,173,140). Equal to within 8-bit rounding.
>
> **Still owed by P3b:** retiring `worldmesh.loft`'s R4 vertex-colour bake. It feeds `view.loft`,
> the **2D** renderer, which P9 deletes — so the bake retires *with its only consumer*, and
> plumbing a texture into a renderer about to be removed is work done to be thrown away. A
> decision, not an oversight. → `plans/11-3d-world/RESULTS.md` → *P3b plumbing*.
>
> **P6 is OPENED, and opening it changed the game's starting town.** The horizon needs two
> readings of the world's height and the world implements one — `sim` fetches the height and
> discards it, so the ground is flat. Switching the second on exposed that the *start* was a
> 42°-average mountainside, and that the rule choosing it (`ov_home_town`, maximising height
> reach) selected for exactly that. **Fixed: the start is now a walkable valley and the ore
> trade got STRONGER** (3 → 13 deliveries at peace). See *Open, and whose call it is* below.

> ## ✅ **plan #16 is BUILT END TO END (2026-08-11) — `M0`–`M4`. The eight statistics are the engine's, the content's, and six of them drive a number.**
>
> **`M4` keyed the derivations** (gate **104 rows**, `derivetest` is new): Might→melee damage,
> Endurance→**the HP pool**, Dexterity→stealth, Perception→**ranged accuracy** (taken from Dex),
> Speed→**the distance clock**, Will→**the saving throw** (taken from Endurance) + the SP pool.
> Two of those are SWAPS, so the gate asserts both directions — the new axis moves the number
> **and the old one no longer does**.
>
> ⚠ **Charisma and Handiness drive NOTHING, deliberately.** §0 keys them to leadership/prices
> and disarm/device/repair; crawler has no party, **no priced transaction** (gold is found and
> staked, never spent at a price), and `r_device`/`r_disarm` are authored on every race and
> **consumed nowhere** — measured. Those are systems, not derivations, so `M4` refused to invent
> one and the character page says *(later)* on exactly those two rows.
>
> ⚠ **`M4` found a live defect and a rotted gate.** A temporary Will potion plus **any**
> unrelated re-derive baked the potion into `spmax` permanently (`7 → 11 → still 11`) — fixed by
> **I-POOL**: a stored pool reads the PERMANENT stat layers only, enforced at the one site that
> stores.
>
> ⚠ **And `make probe` was rotted THREE LAYERS DEEP, each hiding the next**: (1) three
> undischarged `float?` divides in `gpushot.loft` aborted step one; (2) the target globbed
> `src/*probe.loft` and swallowed the **windowed** `reloadprobe.loft`, so it **HUNG** — and a
> hang reads as progress; (3) `world_r4`/`world_r5` fail against goldens measured 2026-06-12.
> **1 and 2 fixed** (`PROBE_SCENES` named + `timeout`). ⚠ **3 IS OPEN AND MUST NOT BE RE-PINNED
> BLIND** — verified pre-existing by re-rendering with the `M3` commit's `sim`/`view`, and the
> world moved underneath it (seed 777→1337, #17's wall gates). Adopting today's frame as golden
> destroys the evidence. **Plan #7's call.** `gpu_r3` 3/3 and `post_r6` 5/5 pass.
>
> **→ The one thing still owed is a JUDGEMENT, not a step: the `make play` read.** Whether the
> spread feels right in motion — Speed especially, a halfling at 1.15× against a half-troll's
> 0.90× — is the user's call. The level-1 numbers are tabled in the plan under `M4`.
>
> ---
>
> ### ✅ **`M3` (same day) — the CONTENT moved to the eight, and the old six left the tree.**
>
> All 18 race/class bundles were re-authored **as a set**: `RaceDef`/`ClassDef` carry eight
> named fields (`r_might…r_hand`), every caster declares `c_spell_stat: "will"`, and both of
> `M2`'s one-step shims are deleted — `stat_index("str")` now returns `-1` like any other typo.
> Full gate green, 103 rows. **The values are the bundles** (`bundles/<name>/<name>.loft`,
> `r_might…r_hand`); what each axis DRIVES is **[`CATALOG.md` §0](CATALOG.md)**. The plan is a
> closure record — read it for the cost and the findings, not for the mechanism.
>
> ⚠ **The finding: adopting the eight RE-RANKS the roster, toward the races the six left flat.**
> Dwarf went Σ -2 → +5 and gnome +2 → +7, same cause — Angband taxed them on Intelligence and
> Charisma, two axes a miner and a tinkerer never used, and **Handiness** is the axis that
> repays them. Rogue passes paladin because *both* new axes land on it. This is what "it is not
> a rename" costs and buys, arriving as a measurement.
>
> ⚠ **And it found a live rendering defect `M2` shipped**: the sidebar baked six labels reading
> `STR INT WIS DEX CON CHR` against eight values, two rows blank. `M2` asserted the
> length-driven invariant at the DRAW site and never at the BAKE site — which is the general
> lesson, since a build site can satisfy a different length and nothing compares them. One
> chokepoint (`view::stat_abbrevs`) now owns the names. **103 gate rows could not see it**, and
> still cannot; whether the sidebar earns a `make probe` row is `M4`'s call.
>
> *(Previously: plan #17 closed `status:finished` 2026-08-10, `S0`–`S7` shipped — how that
> system works is [`CRAFTING.md`](CRAFTING.md) → *All of it shipped*. It answered what
> Handiness is *for*, which is what unblocked `M3`. The roster is `#11` 3D world · `#13`
> scoped identity · `#16`; the loose thread #17 left is `FLOWD_MAX` saturated, below.)*
>
> ✅ **`S7` SHIPPED (2026-08-10): standing, and the militia it raises.** The player's push out,
> where `S5` is the world's push in — and they meet in one predicate, because `hex_safe`'s
> second term is *a guard within `GUARD_R`*, so **a militia is guards the settlement would not
> otherwise have posted.** No new safety mechanism at all, one new source of role-3 actors:
> `S1` bought this whole step without knowing it.
>
> **I-STAND: one number per settlement, earned by acts, read as a category, ONE consumer.**
> Keyed by WINDOW, which is what makes it local — a hero in one valley is a stranger in the
> next, gated by walking out and back. Earned at one deed per raider turned back and three for
> ending a source, through **`on_hostile_slain`, a single chokepoint that replaced the poster
> bounty's three copies** across melee/bolt/shot. Said by the guard master, never shown — no
> bar, no panel. The petition is a bump: **still zero new keys.**
>
> | four days, den alive in BOTH arms | ore face unsafe | ore deliveries |
> |---|---|---|
> | no militia | 775 / 1600 | 3 |
> | **militia raised** | **0 / 1600** | **6** |
>
> ⚠ **AND IT COST THREE DEFECTS, TWO OF THEM THE MILITIA'S OWN — both about a body in a
> doorway.** A picket posted ON the work made the ground perfectly safe and took the ore from
> 3 deliveries to **0**: `npc_step` refuses an occupied hex, so a permanent body in a one-hex
> pass freezes everyone behind it. *It is the corpse defect with a living body*, and the fix is
> directional — **a picket faces outward**, two hexes beyond the work, so the road behind it
> stays open. Then a picket with a patrol BEAT still cost 0 deliveries, for a different reason:
> **the flow-field cache is full — 24 of 24 — in the shipped world before a militia exists**,
> fields are first-come, and the loser falls back to greedy stepping. A picket now stands its
> post and asks the cache for nothing.
>
> ### ✅ AND THE LOOSE THREAD IT LEFT IS CLOSED (2026-08-10): the path-field cap was a silent cliff, and it was already over
>
> The question `S7` recorded as *"some civilian is walking greedily and nobody knows which"* has
> an answer: **nine of them, and it was their HOMES.** The shipped home window demands **38**
> distinct (destination, class) fields against a flat `FLOWD_MAX = 24`, so 14 were never served
> — and the losers were not random. Work is asked by day, home by night, day comes first, so
> what lost was systematically the night leg: **nine townsfolk walked home in a straight line
> every night**, freezing at the first concave obstacle, which is the exact failure the fields
> were introduced to end.
>
> **I-FIELD: every destination an actor can descend toward has a field**, and the bound is a
> property of the world rather than a constant. The derivation was already written in the old
> comment and never used: an actor's `hq`/`wq2`/`aq2` are fixed when it spawns, so **it can ask
> for at most three destinations**, and everything asked at runtime resolves to one of those or
> the town seat. `flowd_cap = 3n + 16` is provably above the demand at any actor count. Fill
> stays lazy, so memory tracks what is asked (~38 fields, ~3 MB), never the cap.
>
> ⚠ **NOTHING GATED MOVED, and that is the finding, not a relief.** `stocktest` still reads 7
> against 3, `militiatest` still 775/1600 → 0 and 3 → 6 deliveries. The nine it repaired are
> villagers, the smith, a fisher, a farmer and a merchant — **nobody in a measured supply
> chain** — which is precisely why a defect this size lived in the starting town unnoticed:
> *every gate watched the two chains that happened to win the race for a field.*
>
> Gated by `safetytest` row 5b, which counts FIELDS rather than paths — a destination with no
> field is a cache failure, one with a field and no route is a worldgen fact (this town has
> one, a ring guard's outer leg), and a row that tested the path would blame the cache for the
> world. **Verified able to go red**: pinned back to 24 it reports `24 built / 38 declared`.
>
> **The roster is `#11` 3D world · `#13` scoped identity · `#16` eight statistics** (cap of
> three; `#16` took the slot `#17` freed by finishing, 2026-08-10). ⚠ *Historical below this
> line — it reads as if #17 were still live; the state is at the top of this file.*
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

> ✅ **AND `S6` SHIPPED — GEAR DAMAGE IS AN EVENT, AND THE TOWN IS WHAT MENDS IT (2026-08-10).**
> **I-MEND**: repair is the *exact* inverse of damage (`pac`/`wdam`/`phpmax` return identical,
> because `refresh_stats` derives rather than accumulates), **and the damage belongs to the
> item, not to where it stands** — no seam launders it, not unequipping, not a staircase, not
> death. A green jelly's acid touch takes the sound piece with the most to lose; the town's
> **smith** mends one piece per bump, at **zero new keys**, and the item's own name carries
> ` (damaged)` so nothing new is shown to anybody. `mendtest` (8 rows, verified red both ways)
> + `scripts/mend.play` in the shipped town.
>
> ⚠ **THE DESIGN'S PROPOSED HOME FOR THE STATE DID NOT EXIST**, and the trap generalises:
> `IF_*` is a flag on the item **def**, and crawler has **no item instances** — a flag there
> would corrode every dagger in the world, including the one the forge makes tomorrow. It
> rides slot-parallel vectors instead, which costs a copy at each of the **nine** sites that
> move an item, and a missed copy is a *silent repair*.
>
> ## ✅✅ AND THE CAUSE WAS BIGGER THAN THE MINE: **THE TOWN WAS SEALED** — FIXED (2026-08-10)
>
> Chasing the mine found the root. The town wall is a hex-distance ring and *"roads make the
> gates"* — a ring hex stays open only where the terrain is already road. **On the shipped
> world that produced ZERO gates**, so the wall closed completely and the town's own people
> were sealed inside it: **498 of 9801 hexes reachable**, everything past ring 17 cut off.
> Every worker whose job is outside walked at a wall for the life of the world — both
> farmers, the fisher, two guards' outer legs, both miners. **13 of 21 civilians could not
> walk their own route.** The three earlier "unreachable site" bugs in this repo
> (`raid_objective`'s 45-hex field, `walk_reach`'s picking grounds, the mine) were all *this*,
> seen from the outside — which is why fixing them one at a time never converged.
>
> ✅ **SHIPPED, AND IT TOOK FOUR THINGS IN ORDER.** Six gates cut per hex direction (exact by
> construction — walk `wrad` steps out and you are *on* the ring — ±2 so a lookout tower
> cannot re-seal the gate it was stamped after); `walk_reach` on the mine; a **`WORK_MAX_D`**
> bound because **reachable is not workable** (with the window open the gatherer re-sited onto
> real alpine shelves 50 hexes out and its deliveries went 3 → 0); the furnace and miners moved
> to a **camp at the ore face**; and — the user's call, and the one that made the trade live —
> **a guard posted on the works.**
>
> | | before | after |
> |---|---|---|
> | hexes the town can walk | 498 / 9801 | **8951 / 9801** |
> | civilians who cannot walk their route | 13 of 21 | **4 of 20** (3 penned livestock, 1 guard leg) |
> | gatherer deliveries, 4 days | 3 | **6** |
>
> ⚠ **WITHOUT THE POSTED GUARD THE TRADE IS NOT HINDERED, IT IS DEAD** — no `GUARD_R` reaches
> the foot of the mountain, so the camp measured unsafe **1600 of 1600 ticks** and `npc_target`
> kept the miners home every tick of every day. *A lever the world holds at zero is not a
> lever.* One guard walking the works (legs at the face and the camp) holds one end at a time,
> which is deliberately not total cover — it leaves `S7`'s pickets something to buy.
>
> ✅ **AND `I-SAFE` NOW CLOSES ON THE CHAIN THE RAIDS ACTUALLY PRESS.** The forge lines are
> **armed** (the stated precondition — a supply — finally exists), and on the shipped world
> over four days, den cleared against den alive:
>
> | | at peace | under pressure |
> |---|---|---|
> | **ore** (the pressed chain) | 7 deliveries, store 0..5, face safe 1600/1600 | **3 deliveries, store 0..3, face unsafe 775/1600** |
> | herbs (the control) | 6 deliveries, store 0..4 | 6 deliveries, store 0..4 |
>
> ⚠ **`stocktest` row 7 now FOLLOWS THE DANGER rather than naming a trade** — it measures both
> chains and asserts the claim on whichever the raid pressed, with the other as a control.
> Pinned to the gatherer it read 6-against-6 and looked like `I-SAFE` failing; it was the row
> watching the wrong valley. `safetytest` and `incursiontest` moved the same way: both used to
> sample at a fixed 100 ticks, which was only ever enough while the most exposed work sat 14
> hexes from the square.
>
> ✅ **AND `S6`'s REPAIR COUPLING IS LIVE**: the shipped smith refuses on an empty forge store
> and mends when the ore is in — *the forge you protected is the one that fixes it*, which is
> the point at which this plan closes on the PLAYER and not only on the town.
>
> ## ✅ THE NARROWER FINDING IT STARTED FROM: THE MINE COULD NOT BE REACHED — FIXED
>
> The smith should draw the store the forge draws, so danger closes the loop on the player's
> own gear. Measuring that found something else: the ore face sits at **(7,49)**, 42 hexes
> from the miner's home at (47,53), with **no path between them at all**
> (`sim_npc_path_dist` = `FLOW_BIG`; its open neighbours are equally cut off, so it is the
> **site**, not the cave mouth). **The miners have never delivered anything, and nothing
> reported it** — they wander, and until something depended on the delivery there was nothing
> to notice.
>
> It looked like the third instance of one defect — **a site chosen by desirability and never
> checked for reachability** (`raid_objective`'s 45-hex field, `walk_reach`'s picking grounds,
> now the mine) — and it was, but all three were the **sealed town** seen from the outside,
> which is why fixing them one at a time never converged: each scan was being taught to prefer
> the inside of the pocket it was trapped in. Fixed at the source, above.

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
- ⚠ **NEW (2026-08-11) — THE STARTING WINDOW IS A MOUNTAINSIDE, AND THE RULE THAT PICKED IT
  SELECTS FOR EXACTLY THAT. The user's call.** Opening plan #11 P6 measured the world's heights
  and found the near field has **none** — `sim.loft:4896` fetches the height from `ov_sample`
  and writes `(_, okind)`, so the ground is a flat plane at z=0 in both renderers, and
  `SCALE.md` (which pins the horizontal twice) is **silent on the vertical**. At the correct
  reading (heights take the same 10× compression the horizontal already takes, which preserves
  the true slope), the home window's **passable** ground averages a slope of **1.02 — 45.6°**,
  with only 7 % of steps gentler than a ramp. **The control is the finding**: towns 0/1/2
  measure **0.077 / 0.088 / 0.386**, so the world at large is walkable country and the *start*
  is the outlier — because `ov_home_town` maximises **height reach**, which inside a 1500 m
  window simply *is* mean slope. It bought the gatherer (plan #17 needs scree/meadow, absent at
  sea level) and cost the onboarding curve; it also costs the terrain, invisibly, until P6
  makes height real. **Narrowest lever first: score `ov_home_town` on reachable high ground in a
  walkable neighbourhood rather than raw height reach** — **DONE, and it worked** (below).
  → `plans/11-3d-world/RESULTS.md` → *P6 opened*; instrument `src/horizonprobe.loft`.
- ✅ **THE STARTING WINDOW IS NOW A WALKABLE VALLEY (2026-08-11), AND THE ORE TRADE GOT
  STRONGER.** `ov_home_town` scores what its own comment always wanted: reach `ALPINE_MIN`
  (scree/meadow can exist) **and** have rock in the window (a mine can exist), then **the most
  walkable window wins**. *Height reach is a CONSTRAINT, not an OBJECTIVE* — maximising it was
  selecting for unwalkability. `ALPINE_MIN` is shared with `ov_kind_at` (one owner) and the rock
  test **asks the classifier** rather than predicting K_FACE from slope (a slope proxy reported
  50 face-like samples near town 2 where the real nearest face is 46 hexes out).
  **The start moved town 3 → town 2:** mean walkable slope **1.02 → 0.403**, cliff steps
  **6303 → 36**, gentle-ramp steps **3813 → 13451**, 20 gentle alpine hexes against 0.
  ⚠ **It took two things that were asking the wrong question, not answering it wrongly.**
  (1) The home-town rock test used `WORK_MAX_D` (330 m) — but plan #17 had already moved the
  furnace *to* the mine and posted a guard, so what must be short is the mine→furnace leg, not
  the town's view of it; the 330 m test guarded something already fixed. (2) The siting scan had
  **no candidate between "within a day's walk" and "the window edge"**, so a valley town's mine
  mouth landed on the edge — *a site pointing at rock rather than a site on it*. It now takes the
  **nearest reachable face at any distance** first (`reachm` already gated it on reachability).
  ⚠ **BOTH OF #17's MEASUREMENTS SEPARATE MORE SHARPLY NOW**: ore at peace **3 → 13 deliveries**,
  under pressure 0 → 1, the face unsafe 775/1600 → **1514/1600** without a militia and 0/1600
  with one, deliveries with a militia 6 → **7**. A distant mine is *more* exposed, which is
  exactly what makes raising a militia worth it — the lever the player holds got longer.
  ⚠ **And the old number was hiding something**: the mountain town's 3 deliveries looked like a
  working economy under strain; the valley's is 13. The old start's supply chain ran at a quarter
  speed nobody had a baseline for. Full gate green, 106 rows.
  → `plans/11-3d-world/RESULTS.md` → *P6 opened*; probes `horizonprobe` / `hometownprobe` /
  `rockprobe`.
- ✅ **THE OPENING CURVE IS RE-MEASURED ON THE NEW WINDOW (2026-08-11), AND THE CONCERN IS
  RESOLVED — but the measurement that raised it was pointed at the wrong ground.** The recorded
  worry was *"a gnoll (mlvl 6) 8 hexes from the vantage, a level-1 hero dead on tick 13"*. On
  the valley window (`src/onboardprobe.loft`, seed 1337):
  | | alpine window | valley window |
  |---|---|---|
  | nearest role-0 actor to the **vantage** | giant rat, 28 hexes | **jackal, 34 hexes** |
  | role-0 actors within 30 of the vantage | 8 | **0** |
  | hero standing still at the vantage, 400 ticks | survives | **survives** |
  The gnoll-at-8-hexes is gone; the vantage is now quieter than the pre-alpine baseline
  (jackal at 43) on the metric that matters, which is *what can reach you*.
  ⚠ **AND THE PROBE FOUND THE REAL OPENING, WHICH NOBODY HAD EVER MEASURED: the SPAWN.** The
  vantage is derived to *maximise clearance* — it is the quietest hex in the window, chosen so a
  town-watching test is not secretly a combat test. A new game does not start there. At the
  actual spawn the hero stands beside **the spawning crystal (25 hp) plus a giant rat, two
  jackals and a giant bat — 3 to 4 hp each**. That is a normal roguelike opening, not a curve
  defect: each dies in a hit.
  ⚠ **"Dead at tick 12 standing still" is an artefact of the instrument, not a finding.** The hp
  trace is `38 38 38 38 37 33 26 22 15 11 5 1 -6` — four attackers on a hero who never swings,
  because `sim_wait` is the probe's idea of a player, not a player. Reported so the number is
  not re-discovered later and mistaken for a regression.
  ⚠ **AND IT IS IDENTICAL IN THE OLD WINDOW** — verified by checking out the pre-P6
  `overland`/`sim` and re-running: same four creatures, same tick 12. **The spawn hazard is a
  property of the level GENERATOR, not of the window**: `gen_dungeon`'s seed does not depend on
  which town is home, so moving the home window moves the *terrain-derived* vantage and leaves
  the *seed-derived* spawn exactly where it was.
  ⚠ **One trap recorded: `role == 0` is not "hostile", it is "not a townsperson"**, and the
  **spawning crystal is role 0** — so any count of role-0 neighbours includes the shrine, which
  at the spawn is always adjacent by design. `surfacetest`'s vantage scan has the same
  conflation; it is harmless there (it only makes the chosen vantage more conservative) but it
  is the kind of thing that reads as a hostile in a log.
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
a 1.45 m door, a 1.75 m figure) which every raised camera had missed. P6 extended it twice more
— a mountain drawn as a **hole** (the floor followed passability, not the ground reading) and a
2.8 m fence duplicating a cliff — neither of which any number in the gate is about. ⚠ **And its
converse: the frame has to be able to SHOW the thing.** Unlit, a 40° hillside renders exactly
like a meadow, so the phase's whole deliverable was invisible and "wrong" and "fine" produced
the same picture. *Before reading a frame for a verdict, check the frame can carry one.*

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
- a **difference small enough to wave through, in the one place it must not be** (2026-08-11)
  — near-vs-far heights disagreed by 9.2e-14 wu and a shared corner by 1.4e-14, both pure float
  association order (`ax + hx - cwx` against `(ax - cwx) + hx`; `a+b+c` against `b+c+a`). In
  metres they are sub-picometre and a tolerance was the obvious answer. ⚠ *A tolerance would
  have cost the row the only thing it is for* — it could no longer separate rounding from a real
  frame error, which is exactly the class of bug it exists to catch. Both were removed **by
  construction** (one expression; one canonical summation order) and the gate reads 0.
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
