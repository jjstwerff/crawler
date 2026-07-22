# SPRITES.md — authoring the game's 2D sprites

Everything about making sprites: the tool, the done-criterion, perspective, palette, scale
and QA. **Extracted from `CLAUDE.md` (2026-07-23)** so a session that is not drawing does
not pay for it — the rules are unchanged, only their home is.

Read this when you are authoring or critiquing a sprite. `CLAUDE.md` keeps the one-line
pointer and the rule that the view resolves sprites **by name**.

---

## The tool

**2D sprites → the `draw` skill** (method: loft `.claude/skills/draw`; **tool: crawler's own
`tools/draw.py`** — copied from the skill's `sketch/draw.py` and extended: `Background
transparent`, `--once` (render-and-exit; exit 1 on unparsed lines / failed checks — agent/CI
use) + unparsed-line reporting, and the `Petals`/`Fronds` ARRAY primitives (radial + linear
natural marks — non-uniform + construction-hiding by default; designs pinned in
`tools/{petal,fronds}_blueprint.py`); rotation/atlas + the old-masters rough brush (16th-c.
split-bristle hair/fur stroke that mixes with wet paint) & the modern spray-paint/airbrush
tool (translucent + adjustable-flow; skin/water/smoke — the fix for old painters' flat
unicolor skin) & a grime wash (depth-pooled weathering — dirt in the recesses, wiped off the
raised areas, for authentic figures/machines) next (paint-interacts-with-canvas; the missing
capability, EXTRACTION.md §3).

Built to be extractable as a **reusable 2D sprite library** — 3D/moros is the goal, but the
2D stack stands on its own for 2D-preferring devs. Used to author the game's **simple 2D
sprites** — the mob/item presentations (and other 2D art), upgrading the text-glyph
placeholders. **2D only — we do not rely on the 3D path.**

**Workflow:** iterate a sprite with the skill (it outputs a PNG to a tmp dir + a cheap text
report), then copy the final PNG into `assets/sprites/` — **the view resolves sprites BY
NAME, no code per sprite**: a monster loads `<monster_key>.png` (+ optional `<key>_gaze.png`
ACTION variant, shown in striking contact), the player `player.png`, floor loot per-category
(`sword.png`, `potion.png`, … see `cat_sprite_name`), gold `gold_pile.png`; a missing file
falls back to the glyph. Drop the PNG in and it's in the game.

The PNG output is reviewable, so Claude *can* self-critique the sprite (the loop closes
here); the **user still verifies how it composites in the live frame**. Also handy for
setting a visual target (wall aesthetic, palette). Not the runtime renderer; not for HUD/UI
layout.

## The done-criterion — real-world, verifiable forms, MENACING

Ground each sprite in a real-world creature/object (a spider, an ant, …) and **stop when a
*cold read* names it uniquely** as that form ("spider", not "some bug") — unique
recognizability is "finished for the game"; don't over-render past it (clarity has an
optimum).

**Monsters must read as a THREAT, never cute** (cute is valuable elsewhere — not here):
hunched/lunging posture, jagged-spiky outlines over smooth rounds, the weapon feature LARGE
(fangs/claws/stinger), mean or glowing eye-glints, gritty darker tones. It's verifiable (the
draw skill's recognition critic runs the test) and clean-room (real forms, not IP creatures).

**Monsters also need a visible *legitimate attack means*** (a biter shows fangs, a clawer
shows claws) matching its combat — no pass without it; and all monster sprites use a **locked
orientation: attack/front = up**, uniform across monsters (never varies per monster) —
authored facing **up** so the engine can **rotate** each sprite to the monster's
movement/facing at runtime (uniform up-authoring is what makes that clean).

**Mood/affect is out of scope** — run only the *recognition* critic (+ the attack +
orientation checks); per-token feeling isn't evaluated (atmosphere comes from the scene /
light / audio, not the icon).

**A STILL + an ACTION version is allowed** — especially for enemies without much other
expression (the floating eye: idle ball vs. gaze-rays firing); the action sprite shows the
attack happening, the still keeps the threat readable.

## PERSPECTIVE rules (the world is top-down)

> *These hold for the CURRENT sprite set and are superseded for 3D by plan #11 P8, which
> re-authors actors as side-on boards. Until P8, keep authoring top-down: the 3D boards
> deliberately carry the existing top-down PNGs, wrong perspective and all, because actors
> were never that plan's focus.*

Creatures + structural features are drawn top-down, with **slight foreshortening allowed** to
show the third dimension (the eye's iris as a front-displaced ellipse; the door as its lit
top edge + a foreshortened face) as long as the feature stays inside its slot (the door
within the wall gap).

**An upright HUMANOID from above shows its SCALP + protruding snout — never a camera-facing
face**; eyes at most as side-hints at the snout root. (Quadrupeds' horizontal heads
legitimately show eyes from above — the jackal model; the player shows hair only.)

**Items may be frontal-iconic** — they read as lying on the floor, the illusion holds. Stairs
are the floor-hole exception (down = a black cube's top opening, steps descending inside it;
up keeps transparent gaps — floor shows under a rising flight). **A feature that sits IN the
wall carries NO architecture of its own** (no jambs/frame — the engine's wall renders that; a
sprite's own stonework clashes).

*(3D — out of scope for now — would extend this with **scale + proportion** checks via the
metric/multi-view channel; 2D sprites need only the unique-recognition test.)*

## Readability + palette — natural-coloured monsters on a light floor

Floor is **light** — warm **yellowish aged stone** (original Roman granite/travertine, *not*
modern pure-white) — walls **dark-toned**, monsters read as **dark-toned shapes in their
creature's NATURAL colours** (a brown rat is brown, a sand adder sandy; the cave spider is
near-black only because real cave spiders are). Detail still reads primarily by *silhouette
shape* (fangs are points in the outline); keep tones dark enough to carry on the light floor.
The soft-black token disc is **dropped** for sprites (a dark shape reads on the light floor;
a disc would bury it). **Critique sprites on a light background (the floor), not dark.**

## Scale = the creature's body, not its box

Size a creature by its **core mass** relative to the existing player/enemy scale; thin
appendages (legs, antennae, tail) count *less* and may **overhang** the cell. A wide-legged
spider is sized by its body — the legs spill past the footprint, not shrink the body to fit
the box.

## QA — two tiers + test-driven redraw

1. *Recognition* (above) — Claude judges it per-sprite at authoring time from the PNG.
2. *Theme coherence* — does it fit the set's overall look — is judged **in-game during
   playtesting** (the user's call; it only shows in context). Flagged off-theme sprites get
   **adjusted/redrawn**.

Keep the editable `.draw` sources in `assets/sprites/src/` (IN the repo) — both so a redraw
is a quick edit + re-render, and as a growing **technique library**: when a similar creature
is needed later, fall back on the existing sources for their *constructions* (jointed tapered
legs, eye-glints, body-mass proportions) — not 1-on-1 copies, but the techniques are the
value.

**When reusing/redrawing parts, always check the JOINS**: a new part must align + scale to
the kept ones or it reads bolted-on — bury a part's joint corners inside the neighbouring
mass, bridge with an intermediate shape/tone (e.g. a skull circle between shoulders and
muzzle), and run connecting features (a spine ridge) ACROSS the joint to tie the parts
together.

## Reference drawings — draw AGAINST real form + real mark-making

`assets/sprites/ref/` holds a small fixed set of public-domain plates (Dürer's hare =
canonical fur; the *Canis mesomelas* / *Mus decumanus* prints = the exact species our
jackal/rat model; Van Gogh reed-pen + Rembrandt for foliage/terrain marks) plus pointers to
the open corpora (BHL, Smithsonian, Rijksstudio, Met/NGA open access, Ruskin/Pennell). Open
the matching plate beside the `.draw` source and compare region-by-region.

The recurring lesson our fur hasn't taken yet: **texture lives in the broken silhouette edge
+ the value gradient, not as strokes floating inside a smooth outline** — see
`assets/sprites/ref/README.md` for what each teaches and how to extend the set.
