# assets/sprites/ref — reference drawings to draw AGAINST

A small, fixed set of public-domain reference images plus pointers to the open
corpora they came from. Two jobs:

1. **Form** — what a creature/plant actually looks like (a black-backed jackal's
   saddle, a brown rat's body-to-haunch mass), so a sprite reads as *that thing*
   (the CLAUDE.md "cold-read names it uniquely" criterion).
2. **Technique** — how fur / foliage / grass is *suggested with marks*. This matters
   here because `tools/draw.py`'s vocabulary — tapered ribbon strokes (`@root…@tip`),
   thin `Line`s, smooth-flagged (`~`) curves, tonal fills — is essentially the same
   vocabulary the old engravers and reed-pen draughtsmen used. These plates are a
   direct upgrade path for the current "spine ridge + 3 flank striations" fur recipe.

**How to use them:** open a sample beside the `.draw` source you're redrawing and
compare region by region (the draw skill's "draw from observation" loop). The single
most transferable lesson across all of them: **texture lives in the silhouette edge
and the tonal breaks, not as marks floating inside a smooth outline.** Our fur
currently lives *inside* a clean circle outline; real fur breaks the outline (a few
stray tufts past the edge) and is carried by a light→shadow value gradient with
strokes only as a finishing accent. Drawn as enumerated lines, our recent animal fur
reads as a **strange web on the back** — the line *placement* is right, the *deposition*
is wrong; the SAME lines laid by a rough brush would read as fur (failure-taxonomy #2,
not #1 — don't keep re-placing the lines, grow the brush).

> **Tool gap behind this:** `tools/draw.py` deposits paint OPAQUELY, so an interior
> hair stroke floats instead of mixing with the mass under it. The two brushes that
> would close it — a **rough brush** (the old-masters 16th-c. split-bristle drag that
> mixes with the not-yet-dry paint, leaving streaks that read as hairs *within* the
> mass) and a **modern spray-paint / airbrush tool** (translucent layering + a
> centre-strong, edge-zero cross-section + adjustable flow — for skin / water / smoke;
> the established fix for skin going flat & unicolor, which the old masters never solved
> by hand without days of colour-matching) — are recorded as missing capabilities in
> **EXTRACTION.md §3**. The whole point of both is the **illusion of detail in one
> gesture** — the masters almost never drew hairs or leaves one by one; a few clever
> strokes imply the hundreds. Until the brushes exist, *withhold* (don't fake fur with
> enumerated opaque strands — imply it, don't enumerate it).

**Licensing:** the bundled samples are public-domain (pre-1900 works / faithful
photographic reproductions) — **except** `flora/leaf_pinnate_venation_pecan.jpg`, which is
**CC BY-SA 4.0** (attributed below). Safe to study *and* to derive from: drawing your own
sprite from a photo is *reference*, not a derivative of the photo, so the share-alike term
doesn't reach your sprites or this repo (it would only bind an edited copy of the photo
itself). This does not touch the clean-room rule — that governs **names/lore**, not visual
study; these are real animals and real plants, not IP creatures.

## Authoring repeated natural marks (arrays) — not uniform, and hide the construction

Veins, leaflets, fur clumps, grass, scales, a tiled cloth motif — any *repeated* mark.
Two rules (full version: the draw skill's "Earned 2D rules"):

- **Never a uniform row.** Vary along two independent axes — a **trend** that follows the
  form (veins shorten toward the tip; spine fur longer than flank) and seeded **jitter**
  (irregular spacing / length / angle). Keep **mirror pairs equal across the axis** or the
  form reads damaged. Uniform is right *only* for man-made patterns (a cloth check).
- **Hide the construction, keep the identity.** Jitter alone leaves the period visible.
  Clump via a low-frequency field (not white noise), place aperiodically (golden angle),
  **occlude/bury** marks under bigger forms, **fray** the edges, and float a **tonal wash**
  over the field — all deterministic, so renders stay reproducible. Critique against the
  **Van Gogh** reed-pen plate in `nature/` (the answer key: repeated strokes that never
  read mechanical). Break the *incidental* regularity, keep the *diagnostic* regularity.

Both cases ship in `tools/draw.py`: the radial as **`Petals`** (a flower head), the linear
as **`Fronds`** (tapered strokes rooted along a spine — veins, barbs, fur clumps, grass, a
fringe). `Fronds` is non-uniform + construction-hiding by default (trend ramp, seeded field
clumping, jitter, frayed ends, mirror-locked pairs), with `jitter=field=fray=0` for a uniform
man-made comb. **`depth=2` makes it FRACTAL** — each frond grows its own scaled sub-array
(`sub`), i.e. real leaf venation (midrib→primaries→secondaries); see the worked example
`assets/sprites/src/leaf.draw`. Designs pinned in `tools/{petal,fronds}_blueprint.py`.

**Future direction — complex DECORATIVE patterns** (walls/curtains/cutlery; library-tier, for
later games). The opposite case to the above: decorative man-made patterns *want* crisp
uniformity (`jitter=field=fray=0`), and hide the "flat stamp" via the **surface** (folds,
perspective, lighting), not via jitter. Needs symbol-capture + affine `place` → grid/wallpaper
tiling → clip-to-region → surface-conform. Roadmap + capability stack: **EXTRACTION.md §3**.

## Bundled samples

### fur/ — animal form + fur mark-making

- **`durer_young_hare_1502.jpg`** — Albrecht Dürer, *Young Hare* (1502), Albertina.
  *The* canonical fur study. What to steal: strokes **follow the body contour** and
  turn where the form turns; fur reads in **clumps** with light ticking over a tonal
  base, never strand-by-strand; the **silhouette edge is broken** by short tufts
  (the opposite of our smooth circle outline); a bright **catchlight** in the eye.
- **`jackal_canis_mesomelas_iconographia.jpg`** — black-backed jackal (*Canis
  mesomelas*), Iconographia Zoologica (1834), Univ. of Amsterdam. The **exact species
  `jackal.draw` models** — note the dark dorsal **saddle** front-loaded over the
  shoulders (our black-backed identifier), the neck narrowing, the snout past the
  skull, the bushy black-tipped tail. Side view (form/markings reference, not the
  top-down pose).
- **`brown_rat_mus_decumanus_iconographia.jpg`** — brown rat (*Mus decumanus* =
  *Rattus norvegicus*), Iconographia Zoologica. The species behind `giant_rat.draw`
  / `white_mouse.draw` / `skarn_rat_king.draw`. What to read: the **lean body → gathered
  haunch** mass, fur direction sweeping back, the dorsal-darker → flank-lighter tonal
  gradient, the bare scaly tail thick at the root.

### limbs/ — legs / wings / claws (limb construction)

Form reference for limbs, which the fur plates only show incidentally. The project's limb
*technique* is the jointed, `@`-tapered ribbon (`cave_spider.draw` legs; humanoid arms) and
the `Fronds` leg-fringe — these plates anchor the *shapes*.

- **`arthropod_legs_scorpion_britannica1911.png`** — scorpion (1911 *Britannica*, PD). The
  best **jointed-arthropod-leg** reference: 4 leg pairs with the segment chain (coxa →
  trochanter → femur → patella → tibia → tarsus), each tapering to a point, plus the pincer
  pedipalps. The form behind `cave_spider` legs + the `centipede` leg-fringe; reuse for any
  bug/spider/crustacean limb.
- **`claws_cat_foot_anatomy.jpg`** — cat foot dissection (*Anatomy of the Cat*, IA Book
  Images, **No restrictions** ≈ PD). Curved **claws** on tapered digits + the tendon lines
  along each toe — the reference for clawed forepaws, raptor talons, any keratin claw (the
  curve + the taper to a hard point are the diagnostic cues).
- **`bat_wings_flying_fox_brehm.jpg`** — flying foxes (Brehm's *Thierleben*, PD). The **wing**
  membrane, the finger-strut skeleton spanning it, the hooked thumb-claw at the wrist, and the
  clawed hind feet — the form behind `giant_bat`'s membrane + struts.

### flora/ — flowers / herbs / ingredients (for the gathering feature)

For the herb/ingredient/pigment gathering work. Botanical plates are side / three-quarter
views — ideal for the **frontal-iconic gathered-item** sprite (a sprig lying on the floor),
and the form/colour reference for the **top-down growing node** (reason the bloom face +
leaf rosette from above; plates don't shoot top-down).

- **`chamomile_matricaria_koehler.jpg`** — chamomile (*Matricaria recutita*), Köhler's
  *Medizinal-Pflanzen*. The ideal **radial-petal** reference (and on-theme: a real
  medicinal herb). Shows the daisy head from several angles incl. near-top-down — white
  ray-petals evenly arrayed around a yellow disc. This is the case the **`Petals` op now
  ships for** (`tools/draw.py`; design pinned in `tools/petal_blueprint.py`): one line,
  `Petals (cx,cy) n=N r=R len=L w=W [bulge=B] [a0=D] <fill>`, draws a congruent,
  vertical-symmetric flower head. Also note the feathery foliage as a foliage-cluster ref.
- **`foxglove_digitalis_koehler.jpg`** — foxglove (*Digitalis purpurea*), Köhler. A
  contrasting **bell/spike** form (not radial) and the **saturated-pigment** example —
  magenta is exactly the vivid colour gathering wants; note it's anchored by dark-green
  leaves (the light-floor readability trick).
- **`usda_pomological_watercolor.jpg`** — USDA Pomological Watercolor (strawberry). A
  textbook **frontal-iconic pickup**: a single object on near-blank ground, reading as
  "lying there", anchored by its green calyx/stem. Colour/tone reference for the
  gathered-item sprite mode.
- **`leaf_pinnate_venation_pecan.jpg`** — a real pecan (*Carya illinoinensis*) leaflet,
  **pinnate venation** — the exact reference for the **`Fronds` op**. Read off it: the pale
  **midrib** (the Fronds spine); lateral veins branching off BOTH sides and angling
  **forward toward the tip** (the `ang→ang2` trend), **shorter near the apex** (the
  `len→len2` trend), gently **curved** (`bow`), at **irregular spacing** (the seeded field —
  never an even comb), and — crucially — **fractal**: secondaries branch off the primaries
  (`Fronds depth=2`). The drawn `assets/sprites/src/leaf.draw` matches it this way. Tune
  against this plate. *Licence: © JonRichfield, **CC BY-SA 4.0** (Wikimedia Commons),
  unmodified — the one non-PD sample.*

### nature/ — landscape / foliage / ground mark-making (for scene targets + overland terrain)

- **`van_gogh_trees_montmajour_1888.jpg`** — Van Gogh, reed-pen drawing, Montmajour.
  The best mark-vocabulary reference for `draw.py`. Each texture is a **distinct
  repeated mark**: grass = short tapered ticks, foliage = stipple-clusters, fields =
  directional dash rows. Exactly what a `Line`/ribbon tool can replicate. Use when
  authoring overland terrain marks (grass/scrub/trees) or a textured scene.
- **`rembrandt_landscape_tall_trees.jpg`** — Rembrandt, landscape with tall trees.
  Trees as a **scribbled canopy MASS with a drawn edge** — not leaf-by-leaf. The
  canonical "silhouette first, texture only at the boundary" lesson; same rule as the
  fur edge, applied to a tree.

## Where to find more (open corpora — all PD or CC0 unless noted)

**Animal form + fur (engraving/illustration):**
- **Biodiversity Heritage Library** — `flickr.com/photos/biodivlibrary` (~300k scans,
  no known copyright). Any mammal → plates with explicit fur direction and tonal breaks.
- **Iconographia Zoologica** (Univ. of Amsterdam, on Wikimedia Commons) — the series
  the jackal/rat samples came from; one hand-coloured plate per species.
- **Smithsonian Open Access** (CC0) and **Internet Archive Book Images** (PD) — plus
  taxidermy specimen photos, a rare source of genuine **top-down** mammal views.
- **Brehm's Tierleben** plates via **Old Book Illustrations** / Wikimedia (PD-old).

**Nature / landscape (the reed-pen + wash tradition that matches the tool):**
- **Van Gogh** reed-pen landscapes — Wikimedia Commons / Van Gogh Museum (PD): the
  mark-vocabulary catalogue (grass ticks, foliage clusters, water streaks).
- **Rembrandt** landscape drawings & etchings — Rijksmuseum **Rijksstudio** (free
  high-res): trees as a canopy mass with a drawn edge.
- **Hokusai** sketchbooks + **Hiroshige** prints (PD): waves, rain, rock, pines reduced
  to a few codified strokes — designed for woodcut reproduction, so low-detail-friendly.
- Museum open-access search ("landscape drawing", "tree study"): **The Met Open
  Access**, **National Gallery of Art**, **Art Institute of Chicago**, **Cleveland
  Museum of Art**, **Getty Open Content**, **Paris Musées** — all CC0/PD on the old works.

**Botanical (plant structure, for overland flora):**
- **BHL** botany — Curtis's Botanical Magazine, Köhler's Medizinal-Pflanzen.
- **USDA Pomological Watercolors** (PD) — plant colour/tone.

**Free instruction (technique, for reference — read, don't copy):**
- **Ruskin, *The Elements of Drawing*** (1857, Project Gutenberg) — trees, foliage
  masses, rock cleavage, water as *structures*; the mass-and-shadow rule.
- **Pennell, *Pen Drawing and Pen Draughtsmen*** (1889, Internet Archive) — a survey of
  the exact hatching/stippling techniques the engraving plates use, with worked examples.
- **Drawabox** texture lessons + **John Muir Laws** nature-journaling (modern, free):
  both land on "texture in the silhouette/shadow, clumps not strands."

## Adding to this set

Keep it **small and fixed** (a target, not a dump). Prefer PD/CC0 sources. Drop the
JPEG in `fur/` or `nature/`, add a bullet above saying **what technique or form it
teaches** and its source/licence. Fetch with a descriptive User-Agent + contact email
(Wikimedia requires it); the `.tif` plates have JPEG thumbnails via the API's
`iiurlwidth`.
