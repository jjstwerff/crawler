# STATE.md — where things stand (2026-07-22)

Branch **`combat`**, **the full gate green** (`make test` — run it, don't trust a count; the
table in `tools/run_tests.sh` is the roster). Written as a handoff.

**Read [`VISION.md`](VISION.md) first** — what this is for, why "properly" is load-bearing, and
where crawler sits in the stack. Then **`plans/11-3d-world/`**: the game is moving into
first-person 3D and the hex field becomes the world the player stands in.

> ## → NEXT: **the towers + doors** (plan #11 P5's tail). The EdgeSet merge is DONE.
>
> ### 1. The `hex_field` / `hexedge` EdgeSet merge — ✅ DONE 2026-07-22
>
> Library `5b4bba1`, crawler `2a72763`. `edgetest` and `sweeptest` pass **unchanged**, which
> was the contract. Crawler is **−192 lines** and owns no edge storage at all.
>
> **The question was posed as *which layer owns `Surfaces`* and that was the wrong axis.** The
> real one is **where the WRITE POLICY lives**: the library owns the storage *and* the surface
> slot, and crawler owns the rule that decides what goes in it. `edge_set_surf` writes what it
> is told; first-writer-wins and nearest-surface arbitration stay at the call site where a
> reader can see which rule is in force. Baking either into storage would silently settle
> junctions for every consumer — a physics decision hidden in a data structure.
> `Surfaces`/`Materials`/`Features` did stay crawler-side, but as a *consequence* of that rule.
>
> `eg_index` stayed **private**: publishing `(cell, direction, slot)` would freeze the layout
> into the contract for both consumers, against a saving of one index computation per write in
> a build-time loop. Instead `edgeset_equal`/`edgeset_digest`/`edgeset_bytes` let consumers
> compare, checksum and gate the footprint without reading the vectors.
>
> **Two lessons, both about verification rather than geometry:**
> - **The precondition was gated, then deleted.** `mergetest` proved the two index maps were
>   the same permutation — halo included, origin-spanning, negative control firing at exactly
>   2 — and was removed in the same commit that made it a tautology. *A test whose subject has
>   been deleted does not become a regression test; it becomes a check that passes for the
>   wrong reason.*
> - **Two agents in one working tree is the real hazard**, and it is worse than the git-index
>   one because it has no undo: ~40 minutes of a transiently uncompilable shared library, a
>   silently-failed edit, and each agent debugging the other's errors. Detection is `stat -c
>   %Y` twice. → `EXTRACTION.md`, and **LOFT-HANDOFF G5** for the misleading diagnostic it
>   produced.
>
> ### 2. NOW: the towers + doors (plan #11 P5's tail)
>
> Towers are **hexagons** (`hex_distance == rad`), doors are **gaps** (`v = 0`). One phase
> across four layers — builder → `Sim` → `build_field` → renderer — because stopping short of
> the renderer changes nothing visible: a recorded arc still draws as six flat quads. Layer
> table + the plotted end-result: `plans/11-3d-world/RESULTS.md` → *P5 — what remains*.
> Doing this before the merge means doing the merge twice, because whichever structure `Sim`
> carries the arc in **is** the answer to step 1's question.

## The design position — eight statements, and they compose

Settled 2026-07-22. Most of these *resolved* a tension rather than adding a rule, and several
describe what the project was already doing without having named it.

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

**The whole argument, and crawler's place in it, is [`VISION.md`](VISION.md)** (written for a
person, not a build). It also records: crawler is the **furthest ahead, not the most
demanding** — `crew_punk` will overtake it on axes crawler never touches (six concurrent
clients, phones, audio timing, a trigger engine with no director); the stack's two **unbuilt**
layers (the modding abstraction, the behaviour layer); and that the behaviour layer **splits**
— movement over the field is a `hex_*` concern, deciding what to do is genre-shaped
`roguelike-kit`. `../loft/doc/claude/GOALS.md` states the same drive one layer down and stated
it first; three things it says better are adopted there, including the acceptance test
**"a thing is done when picking it up is *fun*"** — a bar `EXTRACTION.md`'s DoD does not yet
carry.

## What got built

| plan | state | gates |
|---|---|---|
| **#5 geometry** | active — points, crossings/slips, level crossings, platforms, signals, bridges/tunnels, stairs, spiral stairs, roofs, cones, arches, domes, vaults, the matcher | 20 |
| **#9 canopy trees** | **T1–T10 all done** | 10 |
| **#10 props** | **P1–P9 all done** (P9 scored 4/6, both failures understood) | 6 |
| **#11 3D world** | **ACTIVE — P0–P4 built + SEEN; P5 part done** | 6 |

Plus the render path (`src/scenemesh.loft`, `src/figure.loft`, `tools/glbview.py`), the scale
contract (`SCALE.md`, `src/scale.loft`, gated), and **`hex_field` 0.1.0 extracted** to
`loft-libs-world` with `src/hexform.loft` deleted.

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
6. **Passability is a property of the TRAJECTORY, never of a position.** We never ask *"is
   the character inside an object"* — we ask *"did its path cross a boundary it may not
   cross"*. So "inside a wall" is not a state to detect and push out of; it is a state that
   cannot be reached. And the answer **must not depend on `dt`** — dropped frames and fast
   motion (falling) must stop on the same walls. **That is not an optimisation**; it is
   whether a wall is a wall. Measured on today's point-sample model: at a fall-sized step it
   misses **54%** of the walls in the way. **The reason is thin geometry** — fences, thin
   walls, stairs are where physics engines die (the old Bethesda games), because a thin
   barrier tunnels, and its push-out is ambiguous enough to resolve to the *wrong side*. On
   the exact-integer lattice a wall is a 1-D boundary, so that whole family is
   **unrepresentable rather than handled**. → plan #11 **I-CROSS**
   The mechanism: a person is normally reduced to **one point**, and a wall **and** a step
   apply two independent corrections in the same frame — neither checking what the other
   maintains — which composes the point across a boundary nothing was watching. Here nothing
   corrects a position (so corrections cannot compose) and the plane is a **partition, not a
   mesh** (`px_to_hex` is total; beyond the map is *rock*, not void), so there is nowhere for
   "outside geometry" to be. **The bar is normal play, not impossibility** — speedrunners
   getting out is fine and should stay *earned*; we build no clamping or OOB-recovery
   machinery, since that machinery **is** the composing-corrections bug.
   - *Consequence found while writing it down:* **the fence is currently a filled cell**
     (`tiles[i] = 5`) — a 1.5 m thick barrier, the thin thing thickened until a point-sample
     model could see it. **P2 put the kernel on an `EdgeSet`, so the machinery is now in
     place**; the fence moves onto it when `hexedge`'s materials carry it (P5). Fences were
     the site of both bugs found today, which is not a coincidence.
7. **`overland` owns settlement placement. We integrate with it; we never rewrite it.**
8. **The village is the subject**, not the castle (landscape composition).

## Open, and whose call it is

- **Library extraction is on the CRITICAL PATH**, not the tail. An **in-world editor is being
  built outside crawler by a second agent**, so packages are what make two agents possible.
  **`hex_field` 0.1.0 has LANDED** — its contract gate passes standalone (`loft test`, 6 tests
  incl. a negative control), crawler consumes it, `src/hexform.loft` is deleted, and the second
  agent is unblocked. Contract: `EXTRACTION.md` → *The editor as the second consumer*.
- **The eligibility/trigger system is designed but unbuilt** (`SCRIPTING.md`). It rides lever 1,
  the event bus. Today the only trigger in the whole game is one hardcoded
  `infest_trigger == "boss_slain"` string check. **Its gate is unlike the others:** it has a
  known second consumer with *harder* requirements already (crew_punk has no director, so its
  trigger engine must be complete), so it is **not** waiting for a second consumer to appear —
  design it against the harder requirement and crawler gets the good version free.
- **`README.md`'s Status and Layout sections are stale** and carry a marker saying so. They
  predate items, equipment, save points, FOV, classes/races, quests, the overland and the games
  kernel, and name modules that are now the `hex_grid` library. A contained, unglamorous job.
- **crawler is absent from loft's Goal C dogfood check** — raised for the owner in
  `UPSTREAM-PLANS.md`, deliberately not filed (it is a goals-doc change in their own repo).
- **Plan #10 P9 leftovers** — the cart is a placement fix; the doors may simply dissolve under
  an eye-height camera (plan #11 P0).
- **`mesh_trunk` not migrated** to `prim_drum` (P1): a six-segment taper whose *surface* equals
  a one-segment taper, so migrating changes tessellation. A real change wanting its own step.
- **Plan #5 `vm_surf`** — render-side attribution; the one genuine gap in DESIGN §7.2b.
- **LOFT-HANDOFF.md H1/H2** still unfiled upstream.

## Four things worth carrying forward

**1. The exact-integer lattice keeps paying off where it was never aimed.** Chosen for boundary
tracing, it then made the area round-trip exact, removed a spurious lean in the canopy
partition, made the relaxation's **termination decidable**, and made stencil rotation exact.
Five unrelated problems, one decision.

**2. Rendering finds what numeric gates pass.** Ten faults survived 36 green gates — three of
them renderer faults, two of those *concealed by a convenience in the renderer*. Plan #11 P0
extended the lesson: **a first-person camera found a world too small for its own player**
(1.51 m eaves, a 1.45 m door, a 1.75 m figure) which every raised camera had missed.

**3. The failure mode is never a check that fails — it is one that passes for the wrong
reason. Four times in one session (2026-07-22), each a different way:** a control aimed at
geometry too *thick* to show the bug (P2b: a solid wall hides tunnelling, only a thin one
shows it) · a perturbation *below the quantisation it was read through* (P3: 0.02 rad shifts
the ground point 0.2 units against a hex circumradius of 1.0, so it rounds back — 0/172
fired) · a plain *tautology* (P4: `project(d,0,h)` vs `project(d,0,0.0+h)`, "worst 0px") ·
and a *discriminator that cannot vary* (P5: seeds 777 and 4242 give an identical surface,
because the overland is a fixed contract wilderness — the window is the discriminator, not
the seed). **All four printed a healthy-looking number.** The rule that would have caught
every one: *state what would have to break for this control to go red, and check that is
reachable.* Hence a **negative control** in every phase. Same session: the town ring's `0.866`
was the **reciprocal** of the right constant, so every village in the game was 33% wider than
tall — and a squashed ring still looks like a ring. **Plan #11 P1 paid this back immediately:
one of its two controls did not fire.** Shrinking the solidity rule to `t == 1` left the whole
suite green, though the surface world carries 232 boulders and fence posts — so the rule's
other two arms had never been gated at all. *A negative control that stays green is a result,
not a formality.*

**4. Read the code before writing the claim.** Twice in one session a confident structural claim
was contradicted by the source — *"build new, extract settled"* (unbuildable: a stencil **is** a
field, so it needs `HexSet`) and *"the two halves have never met"* (they meet at
`sim.loft:3005`). Both were caught, both **after** being written into a plan. Describing
architecture from docs and naming produces claims plausible enough to survive review.

## Docs reconciled 2026-07-22 (they had drifted badly)

`CLAUDE.md` (2D-first reversed; the singular goal + over-engineering test added) · `ROADMAP.md`
(still said "next step: G1 — nice walls"; M-Core shipped at `d1ecc56`) · `DESIGN.md` §18a
(stale-banner: the gate is the truth, not the checkboxes), §7a (layer *model* survives, its 2D
reading conventions retire), **§3a pillar 0 + pillar 1**, **new §3b scope** · `RENDER.md` +
plan **#7** (parked — substrate flow-backs and verification channels survive, the 2D tiers do
not) · `STENCILS.md` (unparked: the editor's first deliverable) · `SCALE.md` (real-measurement
rule; the ladder question) · `SCRIPTING.md` (what rides on the bus) · `EXTRACTION.md` (the
editor contract) · issues **#9/#10 → `status:finished`**, **#7 → `status:future`**.

## How to run things

```sh
make test                     # the headless suite — run before committing
loft --interpret --lib ../loft-libs-core-main/ --lib ../loft-libs-world/ \
     --lib ../loft/lib/ --lib src/ src/<x>test.loft
python3 tools/glbview.py build/x.glb out.png --eye 30,-46,12 --target=-4,0,6 \
     --shadow 640 --stats          # --stats = coverage per MATERIAL, never by pixel colour
```

**`loft-libs-world` is consumed from its shared `dev` branch** — both projects check it out; no
PR per change until stabilisation. `--lib` reads the **working tree**, so a consumer on the
wrong branch silently compiles different code. Check the branch before debugging anything odd.

`xvfb` is **not installed** — the native `gl_screenshot` path and `make probe` need
`sudo apt install xvfb`. `glbview.py` needs neither, which is why it exists.
