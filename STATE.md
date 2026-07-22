# STATE.md — where things stand (2026-07-22)

Branch **`combat`**, everything pushed, **36 gates green** (`make test`). Written as a
handoff: what exists, what was decided, what is open.

## What got built

| plan | state | gates |
|---|---|---|
| **#5 geometry** | active — railway points, crossings/slips, level crossings, platforms, signals, bridges/tunnels, stairs, spiral stairs, roofs, cones, arches, domes, vaults, the roof matcher | 20 |
| **#9 canopy trees** | **T1–T10 all done** | 10 |
| **#10 props** | **P1–P9 all done** (P9 scored 4/6, both failures understood) | 6 |

Plus: the **render path** (`src/scenemesh.loft`, `src/figure.loft`, `tools/glbview.py`) and
the **scale contract** (`SCALE.md`, `src/scale.loft`, gated).

## Decisions taken (don't re-litigate these)

1. **Scale** — one hex step = **1.5 m** (architecture); terrain is the *same* hex compressed
   10× at 15 natural m (`OV_STEP`). The contract is code and gated. Library thresholds are
   **dimensionless**; only the metre is the consumer's. → `SCALE.md`
2. **Library/content seam** — *a library's enumerations are of MECHANISMS and are closed; a
   bundle's enumerations are of THINGS and are open.* Settled once for prop kinds, species
   parameters and stencils. → `BUNDLE.md § The library/content seam`
3. **Props are objects, not field features** — almost all are below one hex step, so the
   resolution-floor rule applies. They live on their own **level**, placement is **derived**,
   state is **stored for decisions, derived for consequences**. → `PROPS.md` (4 parts)
4. **Stencils are small fields, not bitmaps**, and rotate **exactly** (60° is an integer map
   on the lattice; six rotations are the identity). → `EXTRACTION.md`
5. **The village is the subject**, not the castle (landscape composition).

## The direction, decided 2026-07-22 — plan #11

The stack built by #5/#9/#10 was **not consumed by the game**: `story`/`view`/`sim` import
`wallgeo` + `worldmesh` and none of `hexform`/`hexedge`/`hexway`/`hexcanopy`/`hexprim` —
those had only offline GLB scenes as consumers. The decision closes that gap and changes
the renderer at the same time, because they are one job: **the game moves into
first-person 3D and the field becomes the world the player stands in.**
→ **`plans/11-3d-world/`**

Taken with it: 3D **replaces** the 2D view (reversing CLAUDE.md's "2D is first-class, 3D is
additive" — the docs are reconciled in P9); actors are **camera-facing boards** carrying the
existing top-down PNGs for now, deliberately wrong-looking, and boards are a **waypoint**
toward animated meshes; **backgrounds and the air box render from the hex world**, never a
backdrop. Priority is a functional game, so the playable milestone is P4.

## Open, and whose call it is

- **Plan #10 P9 leftovers** — the cart is a placement fix; the doors need a **second shot**,
  because a raised camera cannot show a door (roofs occlude their own walls). Not a props
  bug. *(A first-person eye-height camera may simply dissolve this one — plan #11 P0.)*
- **Library extraction — now on the CRITICAL PATH**, not the tail. An **in-world editor is
  being built outside crawler by a second agent**, so without packages it would have to copy
  crawler's source — which the DoD forbids. Sequencing is **build new, extract settled**: new
  routines (the **stencil mechanism**, the **document format** — neither exists) land
  package-side now and cannot collide; crawler's settled modules migrate after plan #11 **P2**.
  Contract: `EXTRACTION.md` → *The editor as the second consumer*.
- **Validation is largely DONE; packaging is what's left.** Audited: across every
  `*test.loft` touching the stack, **zero** import `sim`/`bundles`/content — the one
  non-stack import is `sighttest`'s `hex_grid`, already an upstream package. So the gates are
  library-shaped already; what's missing is `loft.toml`, entry modules, standalone runners
  and per-package READMEs. **The `hexfield` skeleton is the one thing blocking the second
  agent from starting**, and it is hours, not days.

## Docs reconciled 2026-07-22 (they had drifted badly)

`CLAUDE.md` (2D-first reversed) · `ROADMAP.md` (still said "next step: G1 — nice walls";
M-Core shipped at `d1ecc56`) · `DESIGN.md` §18a (stale-banner: the gate in
`tools/run_tests.sh` is the truth, not the checkboxes) and §7a (layer *model* survives, its
2D reading conventions retire) · `RENDER.md` + plan **#7** (parked — substrate flow-backs
and the verification channels survive, the 2D tiers do not) · `STENCILS.md` (unparked: it is
the editor's first deliverable) · `SCALE.md` (open work: two readings want to become a
ladder) · issues **#9/#10 → `status:finished`**, **#7 → `status:future`**.
- **`mesh_trunk` not migrated** to `prim_drum` (P1): it is a six-segment taper whose surface
  equals a one-segment taper, so migrating changes tessellation. A real change, wanting its
  own visible step.
- **Plan #5 `vm_surf`** — render-side attribution; the one genuine gap in DESIGN.md §7.2b.
  Physics is complete without it.
- **LOFT-HANDOFF.md H1/H2** still unfiled upstream.

## Three things worth carrying forward

**1. The exact-integer lattice keeps paying off where it was never aimed.** Chosen for
boundary tracing, it then made the area round-trip exact, removed a spurious lean in the
canopy partition, made the relaxation's **termination decidable** (integer state ⇒ finite
space ⇒ fixed point or cycle, both detectable), and made stencil rotation exact. Five
unrelated problems, one decision.

**2. Rendering found ten faults that 36 numeric gates all passed.** Wall fins, the crown
staircase, an arc-sweep bug, six spoke branches, the spider skeleton, the flat crown, plus
three renderer faults — `abs(N·L)` crushing vertical faces, glTF binding materials
per-primitive, and **a sun pointing underground**. Two of those three were *concealed by a
convenience in the renderer*. A renderer that never fails loudly hides the scene's errors and
its own.

**3. The failure mode is never a check that fails — it is one that passes for the wrong
reason.** Four gates this session had a first formulation that measured something *adjacent*
to the intent (the horizon scored by eye; box diagonals read as a lean; a leaf corner instead
of its centreline; shutter symmetry in the wrong axis). Three green checks stood over
questionable images. **Every phase now carries a negative control**, and that is why.

## How to run things

```sh
make test                     # the 36-gate headless suite — run before committing
loft --interpret --lib ../loft-libs-core-main/ --lib ../loft-libs-world/ \
     --lib ../loft/lib/ --lib src/ src/<x>test.loft
python3 tools/glbview.py build/x.glb out.png --eye 30,-46,12 --target=-4,0,6 \
     --shadow 640 --stats          # --stats = coverage per MATERIAL, never by pixel colour
```

`xvfb` is **not installed** — the native `gl_screenshot` path and `make probe` need
`sudo apt install xvfb`. `glbview.py` needs neither, which is why it exists.
