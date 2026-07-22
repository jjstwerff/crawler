# STENCILS.md — design: layered, composable stencils → castles

> Stencils are one content type inside the larger content-bundle architecture —
> see [BUNDLE.md](BUNDLE.md) for the pool / definitions / placement / routines model
> this slots into.

## Status

**DESIGN SESSION — no implementation, and now SCHEDULED (2026-07-22).** A lean flat-grid
MVP was drafted and then **parked** (reverted from the tree) because the model below changes
the core data shape. That wait is over: the mechanism is settled in `EXTRACTION.md` →
*Stencils — and why they belong in `hexfield`* (a stencil is a small **field**, not a
bitmap; stamping is merging two fields under the existing nearest-wins arbitration; 60°
rotation is an **exact integer map**, six rotations are the identity, reflection gives 12
orientations).

**It is the first deliverable of the in-world editor track** — new code, landing
package-side in `hexfield`, and needing no renderer. The gates it must pass are listed in
that EXTRACTION section; the layer + anchor representation below is what it implements.

## The vision (north star)

Three ideas that converge:

1. **Stencils are the unit of hand-built content** — vaults, rooms, buildings,
   towers; the authored counterpart to the random rooms `gen.loft` carves.
2. **Stencils are multi-layer** — a vertical stack of hex planes, with
   **ladders/stairs connecting adjacent layers** (a tower's floors + its rampart
   roof; a building's basement / ground / upper storeys). Layers are part of the
   model *from the start*, not bolted on.
3. **Stencils compose** — towers + buildings join via **walls routed in 24
   directions** to assemble **castles** (and, later, towns).

Endgame: **a castle is an assembly of layered stencils** (towers, gatehouses,
halls) stitched together by curtain walls, with **walkable ramparts as upper
layers** and ladders/stairs threading the vertical.

## Gameplay pillar — traversal-gated content (the *point* of layers)

Worked example (the target): the player **climbs a tower** (ladder/stairs: ground →
upper → rampart layer), **traverses the curtain wall** along its walkable top,
**crosses to a second tower**, and **descends into a keep sealed at ground level** —
no door, vault granite all around — reachable *only* via the wall route.

The design value: **the route is the lock.** Content (loot, a boss, a shortcut) is
gated behind a *traversal puzzle* — vertical routing — instead of behind a key or a
switch. A "closed-off" building is simply one **sealed on the ground layer, open on
an upper/roof layer**; the rampart is the only bridge.

**It needs no new *mechanics* — only the layer axis in the world data.** The
primitives already in the game generalize:
- continuous hex movement + slide/radius collision → runs **per layer**, unchanged;
- the `>`/`<` stair is a *feature that transitions the player* → a **ladder** is the
  same kind of feature, transitioning **layer** instead of **depth**;
- "current hex" for combat/adjacency → gains a **current layer** beside it.

So "climb → cross → drop in" is **emergent** from *move-on-a-layer* +
*use-a-vertical-link* — not a bespoke system. This design adds only the layer
dimension to the data (stencils carry it); the mechanic falls out. (Today's build is
single-layer 2D — the primitives exist, the layer axis is what's new.)

## Realization — the correct model, tested in 2D *now* (no 3D needed)

The reason to design this now: **it is fully usable and testable in today's 2D
engine** — the 3D world is deferred, not a prerequisite. The existing kernel/view
invariant is what makes that true:

- **Kernel = the honest layered (stacked-Z) truth** — per-layer hex planes +
  vertical links. This is the model `moros_render` will eventually draw; we do **not**
  use a lossy single-plane hack that can't map onto real height later.
- **2D view = renders the player's *current layer*** — climbing a ladder switches the
  rendered plane (one layer at a time; over/under cues are a view nicety, not a
  blocker). 3D later is a **pure view swap** over the *unchanged* kernel.
- **The mechanic is headless-testable** — the whole traversal-gating claim is a
  deterministic assertion, no pixels needed: *ground-layer flood-fill does NOT reach
  the sealed keep; the rampart-route flood-fill DOES.* A `*test.loft` proves the
  design before anything is drawn — the project's "verify logic headless, user is the
  visual verifier" workflow exactly.

So designing now buys the **kernel data model + traversal mechanic locked and
validated in 2D**, with 3D as deferred, view-only risk. This **resolves Q1**: a
*layer* is a within-level **stacked-Z axis** (climb a tower) rendered one-at-a-time
in 2D — **distinct from *depth*** (the `>`/`<` swap to another generated level). §7's
"depth ≈ layer index" is a later 3D-drawing convenience, not a mechanical merge.

## This is already half-specced — where it lives

The pieces exist across the design; this doc unifies them.

- **§7 Height & layers** — the multi-layer height model (milestone L6); the note
  that "depth ≈ layer index later".
- **§9 Feature overlays** — **24-direction walls** (15° snap), **round towers**,
  **2-hex curtain walls = walkable rampart + battlements**, **12-direction
  building placement** (square-local `gridgeo`), the `wallgeo` outline engine, and
  the `moros_render` primitives (`emit_wall_quad` / `emit_thick_curved_wall` /
  `emit_cylinder_post` / raised surfaces) the geometry maps onto.
- **LAVITION.md** — vertical layers (**basement / ground / 2nd / roof / free**);
  `hex_walls` (**24 orientations per hex** = 6 edges × 4 sub-segments; each segment
  carries `layer` + height range); `hex_items` (12-dir placement + `layer`);
  `lavition_stencil` (capture / serialise / apply "at building scale or item
  scale"); `lavition_layer_panel`.

So: **stencil** = the authored unit · **layers** = its vertical axis · **hex_walls**
= the 24-dir connective tissue · **castle** = a composite of stencils + wall runs.

## Layered stencil — data model (PROPOSED, to resolve)

- A stencil owns a **stack of layers**, each a flat `w×h` hex grid. Stored as **one
  flat integer vector** of length `layers·w·h` (loft-safe: flat, never nested
  vectors), addressed `(L·h + y)·w + x`.
- **Layer identity** from the LAVITION set: basement / ground / upper(2nd…) /
  roof(rampart) / free. A stencil declares its base layer + count.
- **Cell codes per layer:** `0` floor · `1` wall · `9` transparent · **(new)
  ladder/stair-up, ladder/stair-down** — vertical connectors linking `(x,y,L)` ↔
  `(x,y,L±1)` *within* the stencil. Plus **anchor markers** (below).
- **Two distinct vertical axes — do not conflate:**
  - **Layer** (this) — local Z *within one generated level*: climb a tower, stand
    on a rampart. Connected by **ladders/stairs** the stencil defines.
  - **Depth** — the `>`/`<` dungeon stairs that swap a *whole generated level*.
  - §7 hints these unify later ("depth ≈ layer index"). **Open Q #1.**

## Composition — assembling castles (PROPOSED, to resolve)

- **Anchors:** a composable stencil declares attach points — `(hex within
  footprint, edge-orientation 0..23, layer, wall-type)`. Towers anchor curtain-wall
  runs on the rampart layer; a gatehouse anchors walls + carries the gate.
- **Wall runs:** between two anchors, a **2-hex-wide curtain wall** routed along hex
  edges snapped to **24 orientations** (= `hex_walls`). Walkable top = an upper
  layer; battlements = parapet. **Round towers** (`emit_cylinder_post`) at run
  junctions/corners.
- **A castle = a graph:** nodes = placed layered stencils (towers / buildings /
  gatehouse), edges = wall runs. **Realized** → baked into the level's per-layer
  hex tiles + `hex_walls` segments + `hex_items` props + height.
- **Recursion (option):** a finished castle can itself be saved as a *composite
  stencil* → stencils nest. (Matches `lavition_stencil`'s building/item scale.)
  **Open Q #8.**

## Generation — the "castle profile" (LATER)

A **castle profile** (data) + **integer hooks**: pick themed tower/building stencils
by depth, place them (12-dir), auto-route curtain walls between perimeter towers
(24-dir), drop a gatehouse, seed a guardian. Output is renderer-agnostic kernel
data (per-layer tiles + walls + props + height). Consistent with the locked
decisions: **profile data + integer-dispatched hooks**, **hardcoded loft tables**.

## Invariant preserved (§9)

Collision stays on the **hex grid, per layer** (a tower keeps its hex; walls use the
canonical hex edge-walls; the 2-hex curtain + height carry ramparts; **ladders are
the vertical links**). The 24-dir wall geometry + round towers are **render-only
overlay derived from the hex truth**. Kernel = hex collision truth (now
layer-addressed); view = pretty overlay. No `graphics::` in the kernel.

## loft-safety (see CLAUDE.md's survival guide)

- **Flat grids, including the layer axis** — never `vector<vector<…>>`.
- **Static catalogs** built at module-init (build-time append, like `items.loft`).
- **Any runtime-growing collection** (an assembly's node/edge lists) = pre-sized
  fixed array + integer count + index-write (like `enemies` / the loot arrays).
- **Hooks = integer dispatch**, not stored functions. **All randomness on gen's
  `Rng`** (determinism).

## Foundation slice (the parked MVP — reconcile FIRST)

The smallest thing that proves the pipeline: a **single-layer** flat-grid stencil
(`0/1/9`) + a stamp-into-`gen_dungeon` step + a connectivity-checked headless test.
It is a strict subset of the model above (`layers = 1`, no anchors). Build it only
**after** this design fixes the layer + anchor representation, so the struct lands
once.

## Deliberately deferred (scope — recorded, not forgotten)

For *gameplay* this layered-traversal model is **intentionally limited for now**, and
that is fine. What we are **not** building yet, by choice:
- **Contested walls / vertical combat** — adjacency stays strictly per-layer, so the
  rampart is a **safe high road**. Ranged/vertical attacks (Q12) come later.
- **Enemies using the routes** — no defenders walking the wall or pathing across
  layers yet (Q14); layer-aware AI is later.
- **Rich verticality** — no multi-storey interiors beyond what a traversal test needs.

The bet: lock and headless-test the **correct foundation** (layered data model +
traversal-gating) now; layer gameplay depth on top once it's proven.

## Open questions — session agenda

1. **Layer vs depth** — ~~orthogonal local-Z, or unified with dungeon depth (§7)?~~
   **→ resolved** (see Realization): layer = within-level stacked-Z (kernel truth,
   2D current-layer view); depth = the `>`/`<` level swap. Distinct axes; 3D is a
   deferred view swap.
2. **The "24 directions"** — `hex_walls`' 24 (6 edges × 4 sub-segments per hex) or
   24 compass bearings (k·15°)? Both land on 24; pick the canonical parameterization
   + the mapping between them. **→ crawler is validating this**: the rotating-spider
   test is the first probe; the model is **12-dir (k×30°) for stencils/items/creatures
   + 24-dir (k×15°) for walls/roads/rivers**, resolved here as one coherent set.
3. **Footprint scale** — tower = 1 hex? building = N×M hexes? Multi-hex stencils need
   a footprint *shape*, not just `w×h`. How does a `w×h` grid map onto hex addressing
   (offset vs axial)?
4. **Anchor model** — how many per tower/building, and exactly what an anchor carries.
5. **Assembly representation** — confirm: live graph (gen-time) → baked to
   tiles+walls (realize-time). Pre-sized how?
6. **Wall runs** — endpoints-only (auto-route) vs authored polyline; curtain
   thickness/height as data.
7. **Ramparts in the kernel** — how a walkable upper layer + battlements live in the
   per-layer tile model.
8. **Recursion** — is a castle itself a stencil (nesting)?
9. **Migration** — lock struct names to `lavition_stencil` / `hex_walls` /
   `hex_items` / the layer enum *now*, so adoption is a `use`-swap.
10. **Authoring** — hand-authored composites vs procedurally assembled (both?); in
    what format (hardcoded tables now).
11. **Movement across a transition** — does the player snap to a layer at a
    ladder/stair hex (discrete), or climb continuously? Does vertical travel cost
    ticks on the distance-driven clock?
12. **Adjacency & combat across layers** — *deferred (see Scope): strictly per-layer
    for now → safe high road.* Ranged/vertical attacks later.
13. **View** — how the egocentric renderer shows the *current* layer and cues what's
    above/below (the reachable rampart, the courtyard beneath). One layer at a time,
    or a composited overhead?
14. **Enemies on layers** — *deferred (see Scope).* Later: AI / flow-field per layer;
    defenders walking the wall + using ladders; cross-layer pathing to reach you.
15. **"Closed off" guaranteed** — the realizer must prove the *only* route into a
    sealed building is the intended elevated one: a **layer-aware connectivity
    check** (gentest, but per layer + across vertical links).
