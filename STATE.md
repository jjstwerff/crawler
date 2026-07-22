# STATE.md — where things stand (2026-07-22)

Branch **`combat`**, **the full gate green** (`make test` — run it, don't trust a count; the
table in `tools/run_tests.sh` is the roster). Written as a handoff.

**Read `plans/11-3d-world/` next.** The game is moving into first-person 3D and the hex field
becomes the world the player stands in.

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

## What got built

| plan | state | gates |
|---|---|---|
| **#5 geometry** | active — points, crossings/slips, level crossings, platforms, signals, bridges/tunnels, stairs, spiral stairs, roofs, cones, arches, domes, vaults, the matcher | 20 |
| **#9 canopy trees** | **T1–T10 all done** | 10 |
| **#10 props** | **P1–P9 all done** (P9 scored 4/6, both failures understood) | 6 |
| **#11 3D world** | **ACTIVE — P0 done**, P1 next | — |

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
6. **`overland` owns settlement placement. We integrate with it; we never rewrite it.**
7. **The village is the subject**, not the castle (landscape composition).

## Open, and whose call it is

- **Library extraction is on the CRITICAL PATH**, not the tail. An **in-world editor is being
  built outside crawler by a second agent**, so packages are what make two agents possible.
  **`hex_field` 0.1.0 has LANDED** — its contract gate passes standalone (`loft test`, 6 tests
  incl. a negative control), crawler consumes it, `src/hexform.loft` is deleted, and the second
  agent is unblocked. Contract: `EXTRACTION.md` → *The editor as the second consumer*.
- **The eligibility/trigger system is designed but unbuilt** (`SCRIPTING.md`). It rides lever 1,
  the event bus. Today the only trigger in the whole game is one hardcoded
  `infest_trigger == "boss_slain"` string check.
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
reason.** Hence a **negative control** in every phase. Same session: the town ring's `0.866`
was the **reciprocal** of the right constant, so every village in the game was 33% wider than
tall — and a squashed ring still looks like a ring.

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
