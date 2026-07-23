# STATE.md — where things stand (2026-07-23)

Branch **`combat`**, **the full gate green** (`make test` — run it, don't trust a count; the
table in `tools/run_tests.sh` is the roster). Written as a handoff: read after a `/clear`.

**Read [`VISION.md`](VISION.md) first** — what this is for, why "properly" is load-bearing, and
where crawler sits in the stack. Then **`plans/11-3d-world/`**: the game is moving into
first-person 3D and the hex field becomes the world the player stands in.

> ## → NEXT: **the wall FIT** — the routines exist, their output still renders as a zigzag.
>
> **The geometry-body work now lives in the `hexbody` project** (`../hexbody`, split out
> 2026-07-23 — its VISION/ARCHITECTURE carry the harness thesis, the vehicle/proxy/animation/
> destruction line, and the roadmap to a *Shadow of the Colossus*-class body). **Plan #11 P5.
> `housedraw` is built and gated** (`hexbody`'s own `make test`): `draw_floor` (massing →
> HexSet+Labels), `draw_walls` (its boundary → EdgeSet, **thin**, so no floor is lost),
> `place_opening` (doors/windows as N edges at `(side, t)`, **annotating, never deleting**),
> `draw_roof` (a ridge, via `hexroof`). 12/12 equivariant in cells **and** edges; per-side edge
> counts identical at all 12. `hexbody`'s `houseshot` renders the contact sheet →
> `/tmp/house12.png`. The wall fit below is the next piece and belongs in `hexbody`.
>
> **What that sheet shows is the next job.** A thin wall is a *strip of hex edges*, so it runs
> longer than the line it stands on by one of **two exact amounts** — `2/√3 = 15.5 %` where the
> side is perpendicular to a lattice line (2 of the 3 hex axes), `3√3/4 = 29.9 %` where it runs
> along one (all 3). At eye height that reads as ten faceted panels. **The fit is load-bearing,
> not an optimisation**: store the zigzag, draw the line. `mesh_walls_fitted` already does this
> shape of thing. → `plans/11-3d-world/BUILDING.md` §4, order step **F**.
>
> **Then the `HOUSE.md` fixture**, still unbuilt: a two-storey house — stair, first floor,
> terrace, interior walls — which is what makes the routines falsifiable beyond a rectangle.
>
> **The user HALTED the other agent** so this could be built without two people writing similar
> routines. `loft-libs-world` is yours alone for now. **Finishing this unblocks them.**

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

Briefly: **#5 geometry** active · **#9 canopy trees** and **#10 props** done · **#11 3D world**
active (P0–P4 built and SEEN; **P5 routines built**, the fit and the two-storey fixture open).
Plus the render path (`scenemesh`/`figure`/`tools/glbview.py`), the scale contract (`SCALE.md`,
gated), and **`hex_field` 0.1.0 extracted** to `loft-libs-world` with its `EdgeSet` merged —
which took crawler's own edge storage out entirely (−192 lines, `edgetest`/`sweeptest`
unchanged).

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

- **The wall fit** — see NEXT. Everything downstream of it renders the zigzag.
- **Does a flip preserve the LAYOUT or the READING?** `HOUSE.md` §7 claims the massing mirrors
  *and* the facade *and* interior readings are unchanged. Those cannot all hold once the massing
  is chiral, which §7 itself requires: a `(side, t)` feature lands at `mirror(original (s, 1−t))`,
  so relative to a chiral element (a terrace) the feature moves. Also suspected: §9's gate
  expects 12 distinct footprints collapsing to 6 without the terrace, but a *centred* terrace is
  still mirror-symmetric about the other axis. **Not yet measured in-engine** — the rectangle
  fixture cannot see it. Decide before building the two-storey fixture.
- **Library extraction is on the CRITICAL PATH**, not the tail. `hex_field` 0.1.0 has LANDED and
  the second agent is unblocked. Contract: `EXTRACTION.md` → *The editor as the second consumer*.
- **Split `EdgeSet` out of `hex_field.loft`** into its own file — the merge is done, but one
  1350-line module with two writers is what cost ~40 minutes. Nobody owns this; it is cheap.
- **The eligibility/trigger system is designed but unbuilt** (`SCRIPTING.md`). Today the only
  trigger in the game is one hardcoded `infest_trigger == "boss_slain"` check. **Its gate is
  unlike the others:** it already has a known second consumer with *harder* requirements
  (crew_punk has no director), so design it against that and crawler gets the good version free.
- **`README.md`'s Status and Layout sections are stale** and carry a marker saying so. A
  contained, unglamorous job.
- **`LOFT-HANDOFF.md` H1/H2, G5, and now N1/N2 are unfiled upstream.** N1 (`%` as an if-branch
  tail breaks `--native` codegen) and N2 (`save_png` returns false under `--native`) are new
  2026-07-23; both have standalone repros and N1 has a verified workaround already applied.
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
REASON.** The single most productive rule in this repo. Seven instances, and they arrive by
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

**All of them printed a healthy-looking number.** The rule that would have caught every one:
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
make test                     # the headless suite — run ONCE before committing
loft --interpret --path ../loft/ --lib ../loft/lib/ --lib ../loft-libs-world/ src/<x>test.loft
python3 tools/glbview.py build/x.glb out.png --eye 30,-46,12 --target=-4,0,6 \
     --shadow 640 --stats          # --stats = coverage per MATERIAL, never by pixel colour
```

**Iterate on ONE test** (~0.5 s), not the whole gate (minutes). Read `/tmp/story_<name>.log`
rather than re-running `make test` to check a result.

**`--native` is NOT the speed win it looks like here.** Measured 2026-07-23 on the `hexbody`
gate: warm, native is **0.34 s vs 0.47 s interpreted — ~1.4×**. These tests are too small for
codegen to matter; startup dominates. It also currently costs correctness: `save_png` returns
**false** under `--native` (LOFT-HANDOFF **N2**), so a `Canvas` render writes no PNG, and `%` as
an if-branch tail expression breaks native codegen outright (**N1**). Use `--interpret` unless
profiling says otherwise.

**`loft-libs-world` is consumed from its shared `dev` branch** — both projects check it out; no
PR per change until stabilisation. `--lib` reads the **working tree**, so a consumer on the
wrong branch silently compiles different code. Check the branch before debugging anything odd.

**`xvfb-run` IS installed** — the native `gl_screenshot` path and `make probe` work. For plain
2D diagnostics the `graphics` `Canvas` (`fill_triangle`/`save_png`) needs no GL or Xvfb at all;
`../hexbody/src/houseshot.loft` is the worked example. `glbview.py` needs neither either.
