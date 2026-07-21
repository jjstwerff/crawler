# FORMS.md — a kit of exact, interlocking hex parts (no seams by construction)

> Companion to **WALLS.md** (the triangle-band *exact* wall construction, validated in
> `tools/wallproto`), **STENCILS.md** (layered castle stencils + anchors), **plans/5-geometry/**
> (the 24-dir outline engine + multi-layer towers/walls, and the plot-to-PNG verify channel),
> **DESIGN §9** (the junction-policy table; `emit_cylinder_post`, `grand-arc`/`arc_pivot`).
> This doc owns the question those depend on: **what are the exact parts, what are their
> seams, and how do parts stitch together — and get recovered — without mismatch?**

## Status

**DESIGN SESSION — requirements only. No implementation, no geometry pinned yet.**
This is the "write the doc before the code" step (design-protocol skill): enumerate the
parts, the seams, and the failure paths so the load-bearing invariant becomes *nameable*
— THEN run the blueprint/plot phase (cheapest medium: a throwaway Python plot) before any
loft. Exact-invariant geometry: **do not approximate or symptom-chase toward it**
(CLAUDE.md "Design / debug protocol").

**Why this doc exists (origin).** The current world routines draw some round structures with
`trig + round-to-hex` — `round(rad * cos θ)`, `round(rad * sin θ * 0.866)` (sim.loft:3014,
3243, 3309; hex corners at overland.loft:304). **That is not a failure — it draws fine.** The
worry is *downstream*: a trig-and-rounded circle leaves **no exact, enumerable form**, so when
the **tower matcher** runs afterward it has nothing exact to match against — it would be
reverse-engineering an approximation. This doc's answer: an **exact predefined cell-form** is
the source of truth (matchable), and trig may still *render* it smoothly downstream. (The
camera/heading `cos(s.heading)` trig is unrelated continuous-player math — it stays.)

---

## The general problem (the reframing — read this first)

> *"I want exact matching instead of general rounding, so we can stitch together
> known-good parts and not get seam problems between them."*
> *"A set of predefined stencils (houses, towers, roads, walls) stitched into bigger
> structures, with no visible gap or angle between them."* — the user.

The goal is **composition from a kit of known-good parts that interlock at EXACT seams.**

**Acceptance criterion (the user's own test):** a composite of stitched parts reads as
**one continuous structure**, never a chain of joints — **no visible gap** (position) *and*
**no visible angle / kink** (direction) at any seam, except where an angle is *intended* (a
building corner, a deliberate sharp-miter). The predefined parts ARE the **stencils** of
STENCILS.md (the composable unit of hand-built content): STENCILS owns the layered
multi-plane composition model; **FORMS owns the seam-exactness property — no gap, no angle —
and the matcher.**
The thing to avoid is **general rounding** — each part computing its own boundary by
approximation, so two parts that were rounded *independently* don't line up where they
meet (gaps, overlaps, kinks at the join). That mismatch is the "seam problem."

The load-bearing property is therefore **seam exactness by shared construction**:

- A **seam** (the interface where two parts meet) is a **connector profile defined ONCE**.
- **Every part that exposes that seam is authored to that exact profile** — not rounded
  on its own.
- Two parts connect **iff their connectors are compatible**, and the join is **exact by
  construction** — the seam hexes/edges are *shared*, never re-rounded on each side.

This is the model-railway / modular-kit / Wang-tile principle: a *finite catalog* of
parts and *typed exact connectors*, so any compatible pieces snap together with a perfect
seam — because the seam was never independently approximated in the first place.

### Two geometry regimes — keep them separate
- **Exact-kit (constructed):** towers, curtain walls, roads, train tracks — built from
  predefined parts with exact seams. **This doc.** Extends WALLS.md's exact triangle-band
  wall construction up to the *composition* layer.
- **Approximate-rounded (organic):** terrain/rock-face boundaries, free silhouettes —
  `wallgeo.loft`'s averaged/rounded outline (DESIGN §9). Fine for nature; **wrong for the
  kit**, because independent rounding is exactly the seam problem. Don't mix the regimes.

---

## Why exact, not rounded (the protocol framing)

This is the design-protocol's **exact-invariant** case: the correct seam is a *single
construction to recover*, not a region to approximate toward. Approximation never
converges to an exact seam — that is the triangle-wall saga (CLAUDE.md: "a small fix
behind a large discovery cost").

**Re-assertion sites (protocol step 2 — count them now, before code).** If each part
rounds its own boundary, then `N` parts × independent rounding = up to `N` silent seam
mismatches — each a *wrong result*, not a compile error. The cure is a **chokepoint**:
define each seam type **once** (the connector catalog) and have every part conform to it.
Drive the re-assertion count toward **1 per seam type**. The single catalog is the one
source of truth; the stamper (place a part) and the matcher (recover a part) are its two
consumers, and they must read the *same* table or detection fails silently.

---

## The invariant (CANDIDATE — to test by plotting, do not assume)

> **Seam exactness + round-trip identity.** Stamp any set of catalog parts — each a **body
> + connectors + features** — joined at compatible connectors. Then: (a) every seam is
> **invisible** — the parts share the seam exactly (zero gap, zero overlap = **G0**) *and*
> their directions match across it (zero kink/angle = **G1**), unless the angle is an
> *intended* junction (a building corner, a sharp-miter); (b)
> `detect(stamp(parts)) == parts` — the matcher recovers each part's body, connectors, and
> features exactly, and classifies every other hex (curtain wall, interior house, floor) as
> *not that part*; and (c) **features and connectors never fragment the body** — a wall with
> three doors and a loophole still matches as **one** wall (a feature is an annotation on a
> continuous body, never a break in it).

Two testable halves: **forward** (compose → seams exact) and **inverse** (recover →
identity). Both are pinned with a throwaway plot/round-trip before any loft.

**Mechanism — see *The pipeline* below.** All seam continuity (position **G0**, tangent
**G1**, *and* texture/UV) is delivered by ONE separation: stencils write **cell data only**;
a single global mesh routine derives geometry **and** texture. No part owns a local geometry
or UV frame, so nothing can misalign at a seam. Texture continuity is the **third** seam
continuity, alongside G0 and G1.

---

## The pipeline — stencils are DATA; one mesh routine owns geometry AND texture

The seam invariant is delivered by a **separation of concerns**, not by careful authoring:

1. **Stencils write CELL DATA only** — per hex, per layer:
   `floor/wall · height · layer · feature code+orientation · connector`. **No geometry. No
   texture coordinates.** A stencil is discrete content — STENCILS.md's flat per-layer cell
   grid (`0 floor · 1 wall · 9 transparent` + markers), nothing more.
2. **One global mesh routine** sees *only* the merged hexes/layers and derives **the mesh
   geometry** from them — the worldmesh discipline (`worldmesh.loft`: the kernel bakes, the
   view only uploads/draws).
3. **Texture coordinates are computed ON that mesh, by the mesh routine** — as a function of
   **global mesh / world position**, never authored per-stencil.

**Why this is the whole mechanism.** Because no part owns a local geometry or UV frame, there
is **nothing to misalign at a seam.** Two stitched stencils are just adjacent cells in one
grid — meshed by one pass, textured by one global parameterization. All **three** seam
continuities fall out *by construction*:
- **Position (G0)** — adjacent cells fuse into one mesh; no gap.
- **Tangent (G1)** — the mesh routine resolves the junction (DESIGN §9) from the connectors;
  no kink.
- **Texture (UV)** — global-position UVs flow across the seam; **no visible texture seam.**

**The failure this prevents (the user's point).** If a stencil wrote its **own** texture
coordinates they'd be in its **local** frame, and at every stencil boundary the texture would
jump — *"almost always visible."* `N` stencils × local UV frames = up to `N` silent, visible
texture seams. The chokepoint — one global UV computation — drives that to **0**. (Same `N→1`
move as the connector catalog; protocol step 2, applied to UVs.)

**Where the matcher fits.** The mesh routine still needs the *semantic* parts to emit smooth,
non-blocky geometry (a round tower → a cylinder; a track → an arc) and to choose a junction
policy. So the **matcher reads the cell data**, recognizes parts/connectors/features, and
tells the mesh routine "cylinder here, arc there, sharp-miter at this junction." **UVs stay
global throughout** — the matcher chooses *geometry*, never *texture placement*.

### The existing toolkit — `gridmesh` (plug into it, don't rebuild it)
The "one global mesh routine" already has a home: **`gridmesh`** (registry `gridmesh-0.1.1`;
source `loft-libs-graphics/gridmesh`) — by its own header *"a TOOLKIT of primitives, not a
framework … each consumer supplies its own per-cell rule"* — for chunk-local, bounded-extent
grid→mesh generation, shared by `audience_crystal` and `lib/moros_render`. It supplies the
continuous-world pipeline: a coord→cell **spatial index** + neighbour queries, **cell-keyed**
mesh accumulation (`SegMesh`), a **`ChunkField`** partition, and **dirty-region / per-chunk
rebuild**. crawler is already on this path — `worldmesh.loft` bakes one continuous hex surface
from cell data (UVs-in-normal + tint baked, no per-stencil authoring — *the principle, already
honoured*), and `chunkmesh.loft` is slated to adopt gridmesh's dirty/group batching (S5).

- **The continuous-world guarantee = gridmesh's HALO.** Each chunk meshes using its neighbours'
  cells gathered through a **halo radius**, and an edit near a border marks the adjacent chunk
  dirty — so a chunk *boundary* is meshed with full neighbour context and shows **no seam.** The
  *same* no-seam principle as stitched stencils, now across **chunk** boundaries too.
- **Global UVs compose with it:** the per-cell rule computes UVs from **world position**, and
  because the halo gives each chunk its cross-border neighbours, those UVs stay continuous across
  both **stencil** seams *and* **chunk** seams. So FORMS supplies **per-cell rules** to gridmesh;
  it does **not** author a new mesh routine.

---

## Focus now: TOWERS (the first concrete instance)

A tower is centered on **one hex**, sized **radius 1..7**, where "radius N" = N hexes from
the center outward before the next hex falls *outside* the form; nested R1 ⊂ R2 ⊂ … ⊂ R7.
Two families: **round** and **octagonal** (octagonal keeps are common in England).

### Open decision #1 — what does "round" mean on a hex grid? (plot, don't argue)
- **(A) Hex-distance disk** — `hex_distance ≤ N`. What `stamp_round_tower` (sim.loft:2913)
  does **today** (ring = `d == N`, tagged **tile code 4** "round wall"). Its silhouette is a
  regular **HEXAGON** (6 flat sides), *not* a circle. Counts: total `1+3N(N+1)`, ring `6N`.
- **(B) Euclidean disk** — hexes whose **center** lies within radius `r` of the tower
  center. Silhouette approximates a **CIRCLE**. The threshold `r(N)` (in units of the √3 hex
  spacing) decides which corner hexes are in — an exact-invariant choice only a plot pins
  (which `r(N)` gives clean one-hex-thick rings, strictly nested, no gaps/pinholes).

> The existing code wants B's *look* ("detectable later as a circle") but ships A's
> *shape*. **Resolving this contradiction is step one.** Plausible answer: A for small N (a
> hexagon reads fine), B once N is large enough for a circle to read — but that is a
> hypothesis to plot, not a decision yet.

### Open decision #2 — octagonal towers
A regular **octagon** footprint, same size series. The hard part: an octagon is 8-fold
symmetric, the hex grid is 6-fold — they don't align, so the rasterized octagon has a
**fixed canonical orientation** (one flat side on a chosen hex axis), is **not**
rotation-free, and must be **frozen into the catalog as an authored hex-set**, not produced
by a clean formula.
- **Small-size degeneracy (failure path):** at small radius, hexagon ≈ octagon ≈ circle
  rasterize to the **same** hex-set → the matcher can't tell the families apart. Decide a
  minimum size `K` below which octagonal isn't offered (or "small tower" is one family).
  Plot to find `K`.

### Today's reality (anchor — don't contradict it silently)
- `stamp_round_tower` (sim.loft:2913): hex-distance ring, interior cleared to floor, ONE
  door punched, ring tagged **tile code 4**. ~15 call sites (wizard/fort/lighthouse/
  furnace/mill/ruins). Round-as-hexagon is half-built; octagonal is greenfield.
- `Stencil.shape` (worldtypes.loft:9) = `"round"` parametric (radius in hexes); the
  placer fills by `hex_distance ≤ rad`. No octagon, no explicit-cell form yet.

---

## Anatomy of a part — body + connectors + features

Every kit part is three kinds of **exact, predefined** element. Naming them is what makes
the matcher robust:

- **Body** — the wall run / tower ring / road ribbon / track arc. The thing the matcher
  recognizes the part *by*, and the thing whose seams must be exact.
- **Connectors** — typed seams at the part's **ends/anchors**, where *other* parts attach
  (the exterior interface).
- **Features** — typed openings carried **within** the body (doors, windows, window-seats,
  loopholes). Interior to the part.

> **The matching invariant, sharpened:** the matcher recovers the **body**; connectors and
> features sit at exact positions on it and **never fragment or truncate it.** A feature is
> an *annotation on a continuous body, never a break in it.* This is the entire fix for
> "doors in 1-hex walls are imprecise" (see Features below).

### Connectors (the exterior seam)
A **connector** is a typed seam profile, defined once and reused:
- **Position** — the seam hexes (offset from the part's origin) → **G0**: no gap.
- **Tangent / orientation** — the heading at the seam, **quantized** to a fixed set (the 24
  hex-edge directions; finer for tracks) → **G1**: no kink. Every part is authored so its
  connector tangents land on the quantized set, so two matched connectors meet with **no
  visible angle by construction** — the model-railway property.
- **Type/width** — e.g. a 2-hex-wide curtain seam vs a thin-band seam.

> Where an angle IS wanted (a building corner, a sharp-miter wall junction), it is an
> **explicit junction policy** on the connector (DESIGN §9), *chosen*, not an accident of
> stitching. "No visible angle" governs seams meant to read as continuous; intended corners
> stay sharp on purpose.

**Tower seams (anchors).** A tower exposes anchor connectors on its ring — `(ring hex,
edge-orientation 0..23, wall-type)` (STENCILS.md). A curtain wall's **end connector**
attaches iff it matches an anchor's type+orientation; the seam is exact because the anchor
hex is *owned once* and the wall's first band aligns to it (no double-rounding). Interior
parts (a wooden/stone house) sit at exact interior cells of the cleared keep.

**Junction at the seam.** Where parts meet, the render side applies DESIGN §9's junction
policy (`round-tower` / `sharp-miter` / `rounded-arc` / `semi-rounded`). Exact connectors
are what make that junction well-defined instead of a guess.

### Features (openings carried within the body)
A **feature** is a typed opening placed at an exact position+orientation *on* the body —
and **the body continues underneath it.** This is the crux the user named: a *thin* wall
carries doors and windows that must not disrupt the matching of the wall itself; a *thick*
wall carries a window with **two bench seats in its thickness**; towers and walls carry
**loopholes** to spy or shoot through. Every one is a feature on a continuous body, not a
break in it.

**The imprecision this fixes (anchor).** Today a door is punched by clearing a **whole hex**
to floor — `stamp_house` (sim.loft:2903-2906) and `stamp_round_tower` (2924) set `v = 0`.
From tiles alone that gap is indistinguishable from the wall *ending*, so the body looks
fragmented — *that* is "doors in 1-hex-thick walls are imprecise." **Fix:** model a door as
WALLS.md already does for its band — *"a door = a span left open on one face" / "remove a
span of the band's triangles"* (WALLS.md:51,85) — a **feature span on a still-continuous
body**, sub-hex-precise, not a full-hex hole. FORMS.md extends that from doors to the whole
feature set and adds the *matcher* requirement (the body stays one run across every feature).

**Feature catalog (predefined, like connectors):**
| Feature | Passage | Line-of-sight | Notes |
|---|---|---|---|
| **Door** | passable (open) | blocked when closed | bump-to-open (DESIGN backlog); the canonical opening |
| **Window** | blocked | see-through | light + sight, no passage |
| **Window-seat (embrasure)** | blocked | see-through | needs a **thick** wall: the 2 bench seats sit in the wall's *interior thickness* beside the opening |
| **Loophole / arrow-slit / spy-hole** | blocked | narrow see-through | shoot/spy **out**; asymmetric — hard to hit *in* (the defender's edge). A real mechanic to build, not nerf (CLAUDE.md: author to full design, build the system) |

**Why this needs the cross-section (band) model.** A full-hex on/off tile can't place a
sub-hex door position, a narrow loophole, or a window *with seats beside it inside the
thickness*. The WALLS.md model — *"a wall is a band between two faces"* with a **free
thickness** (one triangle → 1 hex → ~2 hex, WALLS.md:16,21) — gives both: an exact sub-hex
position for the opening, and the *interior thickness* the window-seats live in. **Wall
thickness is a part parameter** and **feature availability depends on it** (thin band:
door/window/loophole; thick wall: + window-seats; 2-hex curtain: + walkable embrasure /
battlement, DESIGN §9).

---

## The matcher (the inverse direction)

> **Match the cell-form, not the render.** The matcher reads the **exact discrete cell-form**
> (the catalog ring of hexes), **never** the smooth sin/cos geometry the mesh routine draws.
> Trig rendering is downstream and decoupled — so *"we draw round towers with sin/cos"* never
> threatens matching. This is the origin worry, resolved by the pipeline: the cell-form is the
> source of truth; the drawing is derived from it, not the other way round.

Given a composed map (generated or authored), recover the parts so the renderer/outline
engine can treat each correctly — extrude a tower as a cylinder/prism (`emit_cylinder_post`),
a curtain as a wall, a house as a house — and resolve each seam with the right junction.

**Output per tower:** center, family (round/octagonal), size (radius), and its seam list.
Plus: classify every *other* wall hex as curtain/house, **not** tower.

### Failure paths to design against (enumerate now — the invariant lives here)
1. **Door gap vs. partial tower.** A matched ring must tolerate the door (and curtain-
   attachment points). How many missing ring hexes still counts as that tower? Too tolerant
   → false matches; too strict → the door breaks detection.
2. **Curtain attaches AT a ring hex.** The ring hex is still wall → the template still
   matches; but the curtain's first band must be assigned to the curtain, not double-counted
   as tower. Need a clean tower/curtain boundary rule (the connector defines it).
3. **Interior house mimics a tiny tower.** A small round/octagon template could spuriously
   match a house corner *inside* the keep. Disambiguate: a real tower has *cleared floor*
   inside its ring; a house corner does not.
4. **Nested / concentric.** A small template matching inside a big tower's floored interior
   — forbidden by "interior is floor", but verify against the catalog.
5. **Family degeneracy at small size** (decision #2) — round ≡ octagon ≡ hexagon footprints.
6. **Tag vs. geometry — OPEN.** Tile code 4 already marks round-ring hexes. Does the matcher
   **trust the tag** (cheap; only works for engine-stamped maps), **recover from pure wall
   geometry** (works for any/imported/hand-authored map), or **both** (tag = fast path,
   geometry = fallback + validation)? This choice shapes the whole matcher.
7. **A feature fragments the body (the central wall case).** A door/window realized as a
   full-hex gap splits one wall into two runs — the live imprecision. The matcher must read
   the opening as a *feature on one run*, not two runs ending. Requires either a feature
   annotation per hex, or the continuous-band representation that never breaks.
8. **A loophole / window mistaken for the wall's end or a missing-wall gap.** A narrow opening
   must not read as "wall stops here."
9. **Connector vs. feature at a wall–tower seam.** Is an opening the tower's *door* (a feature
   on the tower) or the wall's *end* (a connector)? The catalog must disambiguate the two.

---

## Related part families (same META — predefined parts + exact connectors — distinct geometry)

> ⚠️ Shared *principle*, **not** shared *geometry*. A tower is a closed 2-D footprint with
> ring anchors; a road/track is a 1-D path rasterized to a ribbon with end connectors (and,
> for tracks, a *continuity* constraint). Forcing one mechanism over all four is the
> design-protocol's "elegant absorption" failure. **The catalog + connector + round-trip
> META is shared; each family keeps its own part geometry and its own connector content.**

- **Curtain walls.** Linear 2-hex-wide bands; end connectors at 24 orientations. The part
  geometry is WALLS.md's exact triangle-band construction (already validated). FORMS.md is
  the composition layer on top of it.
- **Roads.** Ribbon segments; smooth turns tolerated (24-dir rounded, DESIGN §9 / PLAN-
  GEOMETRY track 1). End connectors = width + orientation. Mostly owned by the outline
  engine; listed here for catalog coherence.
- **Train tracks — the sharpest example of the principle (and the hardest).** A *literal*
  kit of parts: **straight / curve (fixed radii) / switch** pieces sharing **one exact
  rail-end connector** = position + **tangent direction** + a **minimum turn radius**.
  - **No sharp turns.** Heading changes only *gradually*: arcs (not corners), every piece's
    radius ≥ the min. Curvature is **quantized to the kit's radii — not freely rounded.**
    *That quantization IS "exact instead of general rounding."* Closer to DESIGN §9's
    `grand-arc`/`arc_pivot` than to the 24-dir snap.
  - **Switches (turnouts).** Multiple tracks merge/split at a switch: a through-track plus a
    diverging track sharing a frog point, both honoring min-radius. A switch is a *junction
    of valid track arcs* — a graph of continuity-constrained curves, genuinely harder than a
    closed tower footprint.
  - **Connectors carry tangent everywhere (G1, no kink); tracks ADD curvature continuity +
    a min-radius** (towers/walls stop at tangent). So the connector *type system* must be
    rich enough for the curvature case — design it with tracks in mind even while only towers
    ship first.
  - **Verdict:** defer to its own blueprint phase. Pin towers first; do **not** let the tower
    design quietly assume it generalizes to tracks.

---

## Open questions for the user (entry to the blueprint phase)
1. **"Round" = hexagon-disk (A) or circle-raster (B)** — or A-small / B-large? (I'll plot both.)
2. **Octagon** — confirm regular-octagon footprint; choose the canonical orientation; OK to
   freeze each size as an authored hex-set?
3. **Min size `K`** for offering octagonal (below which it's indistinguishable from round).
4. **Matcher purpose** — render/outline engine (extrude cylinder/prism + junctions) vs.
   gameplay/world understanding vs. both? (Shapes how strict the round-trip must be.)
5. **Tag vs. geometry** detection (failure path #6).
6. **Door & curtain tolerance** — how many non-wall ring hexes still match (failure path #1).
7. **Feature representation** — per-hex annotation `(wall tile + feature code + orientation)`
   vs. a sub-hex band-feature (a span of the band's triangles). Tied to whether walls are
   full-hex tiles or bands — and this is the "door imprecision" fix (failure path #7).
8. **Feature × thickness matrix** — which features each wall thickness supports (seats need a
   thick wall; loopholes/doors/windows work at any thickness).
9. **Loophole / window semantics** — do they pass line-of-sight and/or projectiles, and is it
   asymmetric (shoot out but hard to hit in — the defender's edge)? A system to build.
10. **UV parameterization** — world-space projection (e.g. triplanar) vs. a continuous mesh
    unwrap: which keeps texture seam-free across BOTH flat walls and curved towers/tracks?
11. **Curved↔flat UV match at a junction** — a cylinder tower meeting a flat curtain: how do
    their world-position UVs stay continuous at the connector?
12. **gridmesh layout fit** — confirm gridmesh's coordinate-layout adapter covers crawler's
    pointy-top odd-r (its header cites moros's axial flat-top + a `layout` param); the per-cell
    rule must honour the `hex_grid` convention.

---

## Next step (NOT in this doc — the blueprint/plot phase)

Per CLAUDE.md + the design-protocol skill: a throwaway **Python** script plots each
candidate form (round A & B, octagon) for radius 1..7 as a hex-map PNG (floor-light/
wall-dark, per the readability rules), **plus** a round-trip check on a synthetic keep
(tower + curtains at anchors + an interior house) that asserts (a) seams are exact and (b)
`detect(stamp(...))` recovers the parts. Claude reads the PNGs, the user picks the
silhouettes, the invariant gets pinned — **then** the loft port. Visual-confirmation
channel: plan #5's "plot the kernel's own output to PNG" pattern.

> **Next session (user intent, 2026-06-28):** try **various stencils in various
> configurations** — exercise the kit by stitching real parts together and watching the
> seams. Needs more time/attention than a single sitting; this doc is the starting point to
> resume from.
