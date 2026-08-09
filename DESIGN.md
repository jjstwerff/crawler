# crawler — Design Document

**Status:** In development. M0 vertical slice + data foundations built; the
2D game runs; procedural world generation underway. (Repo: `crawler`; loft
package: `story`; final in-world name TBD.)
**Last updated:** 2026-06-03

---

## 1. Summary

A **clean-room, ZAngband-style roguelike** written in the **loft** language.
The **2D game is first-class and complete in its own right** (some players prefer
2D); the *same* renderer-agnostic **simulation kernel** also drives an **optional 3D
browser build**, added for those who want it — **3D is additive, not the destination**.
This also keeps the game **reachable on lesser / low-power devices**: a phone screen
renders the 2D version cleanly, where 3D would only distract. 3D is for desktops / big
screens — plus an opt-in **viewing mode** to admire a scenic backdrop when one's worth it.

Defining twist: the player moves and turns **smoothly and continuously**,
enemies live on a **hex grid**, and the game clock is **driven by how far the
player travels**, not by wall-clock time.

---

## 2. Relationship to moros — same world, *generated* not authored

The world model here — a **hex world** with per-hex height + stacked layers,
materials, items, and walls/buildings/castles/towers/roads/rock-faces — is the
**same rich system `moros` already details**, *but `moros` builds it by hand
through an editor* (a long content/tooling tail). **`crawler` is the
anti-moros:** it shares that world model (and reuses `moros_map`/`moros_render`)
yet reaches a **working, playable foundation much faster by *generating* the
world procedurally** instead of authoring it. Same destination world; code- and
generation-driven path to a working game, with no editor dependency.

Consequence that recurs throughout: **everything is procedural** (dungeons,
buildings, towns, roads, terrain), and the engine favors a solid generated core
over hand-authored content.

**Build order + the character model (direction, 2026-06-14).** Construction goes
**world first → content → character/NPC interactions** — the structural layers
before the social/behavioural ones. The current D&D/Angband-derived character
system (stats, classes, races) is **transitional**: the long-term target is to
adopt **moros's character types** (same as the world model is shared with moros),
not to deepen the D&D model. So the player/character data structures are built to
**generalize, not to be player-specific** — **NPCs will share most of their DNA
with players** (a common character/being core; `Enemy` is the NPC precursor today).
Concretely: the `Player` struct lives kernel-side (`sim.loft`, beside `Enemy`) as a
character record, with `player.loft` a thin method facade over it — shaped so the
same core later backs NPCs and swaps to moros types without a call-site rewrite.

---

## 3. Goals & Non-Goals

**Goals**
- A **playable** roguelike — open it, drive around, fight, lose.
- A **renderer-agnostic simulation kernel**: all rules/state, zero rendering;
  2D and future 3D are interchangeable front-ends.
- **2D as a complete game; an optional 3D browser front-end** on the same kernel,
  no rewrite (3D additive, not the destination).
- **Deterministic** simulation (testing, replay, world-keyed generation).
- **Procedural** content throughout; **no IP risk** (§4).

**Non-Goals (for now)**
- Reproducing ZAngband's exact content/balance — we clone *mechanics*.
- Multiplayer — not now, but the pillars (§3a) deliberately leave the **door open**:
  no permadeath, persistent characters, a shared seed-deterministic zone-world, a flat
  curve (veterans + newcomers co-op without one trivializing the other), and the
  `loft-libs-net` substrate make it a *later addition, not a rewrite*. Mods — later, if
  ever.
- A bespoke 3D renderer — reuse `moros_render`.
- A hand-authoring editor — that's moros's path, deliberately not ours.

---

## 3b. Scope — what is reachable, and what we deliberately do not need

**The target (user, 2026-07-22): Baldur's Gate 3's *capability*, not its *volume*.** Stated
here because the two get confused, and confusing them either sets the bar absurdly high or
gives up fidelity that is actually within reach.

**BG3's budget is dominated by UNIQUENESS VOLUME** — hundreds of bespoke individuals, each
with their own scenes, dialogue and cinematics. That is where four hundred people go. Its
**capabilities** are a different thing entirely: rendering fidelity, party locomotion,
traversal, animation. Those are *systems* — built once, used everywhere, never re-authored
per scene.

| BG3 has | reachable here | why |
|---|---|---|
| graphical fidelity | **yes** | fidelity's cost is authoring assets to a photoreal standard; in a **derived** world it becomes *deriving to a higher standard* — algorithmic work, which is what this project is for |
| party locomotion / traversal | **yes** | a system, authored once |
| animated actors, mocap | **yes, increasingly** | markerless video capture is real and the cost is falling every year |
| voice | **yes, at our volume — and the volume is the point** | The **eligibility model collapses the budget**: if a line only fires when its conditions are genuinely met, **ambient chatter becomes unnecessary rather than cheap** — no barks, no flavour lines. *"That changes the discipline more than the budget: every line is worth a real performer and a real take"* (`../crew_punk/WORK.md` §9 works the whole pipeline through — read it before planning any VO). Recording is ~80% an actor **in their own chair**: remote has been standard since ~2020, a good mic in a treated space is close to a booth, and the same seat covers webcam/phone face capture for non-hero content. A stage is still wanted for full-body capture, overlapping ensemble scenes and physically exerted vocals. You drop **facilities, not direction** |

**One refinement to that pipeline, and it changes which tool is needed.** `crew_punk` assumes
generated voice hands over word timings and *"real performers replace the audio later without
changing a word"*. **They will change words** — actors rephrase, add hesitations, shift
emphasis, and the take is usually **better** for it. So timings cannot come from the script:

- **Script-based forced alignment is the wrong tool** (Montreal Forced Aligner, Gentle) — it
  assumes the transcript matches and fights every deviation.
- **Transcribe-then-align is the right one** (WhisperX-class: ASR + wav2vec2 word-level
  timestamps). It handles deviation by construction, because it aligns what was *actually
  said*. Largely off-the-shelf — this probably needs **integrating, not inventing**.
- **And the recording becomes the source of truth.** If the performance beats the line, the
  script is updated to match it — so the tool's real job is *reconcile script to performance*,
  not merely emit word spaces.

| hundreds of unique individuals, monsters, bespoke scenes | **no — and not needed** | **systemic variety substitutes for unique authored assets** |

**That substitution is the whole economic argument.** One derived tree routine instead of a
library of tree models; one eligibility system instead of an authored branch tree; one
settlement scorer instead of hand-placed villages. The variety a player experiences is
produced, not stored — so the content bill scales with *mechanisms*, not with *assets*.

**What stays human, and does not scale: DIRECTION.** What a scene means, how a line lands, why
this moment matters. No system produces that. It is affordable only because the volume a
derived world needs is small — and it is exactly where a small team's taste shows.

**The consequence for the build:** fidelity is a legitimate long-run target, so today's
deliberately-wrong sprite boards really are a waypoint. That makes the **actor presentation
seam** (plan #11 P4) load-bearing rather than tidy — it is what lets animated meshes replace
boards without a rewrite. Style is still the near-term answer (indies win on style, not
fidelity: Hades, Obra Dinn, Disco Elysium), but the ceiling is not style-shaped.

## 3a. Design direction — accessible action-roguelite ("Angband bones, friendly tuning")

crawler clones Angband's **systems** (§4, §13) but deliberately departs from its
*feel*: the numbers, death model, and class weight are tuned for an **accessible,
Zelda-flavoured action-roguelite**, not a faithful Angband difficulty clone. **These
pillars are the authority where they conflict with "reproduce Angband numbers"
(§13)** — systems faithful, tuning friendly.

**Accessible ≠ easy.** À la Dark Souls, we lift *permadeath and grind*, not the
*challenge*: the game can be genuinely hard. Difficulty lives in skill, combat,
hazards, and the lose-the-dive stakes (#5) — never in stat-gates, RNG instakills, or a
permadeath tax. The identity in one line: **Zelda's exploration + capability feel,
Souls-grade fair challenge, no permadeath.**

0. **BOUNDED SIMULATION — depth in the derivation, shallow at the interface.** *(user,
   2026-07-22, and the authority over every later pillar when they conflict.)* Dwarf Fortress
   is hard to get into **not by design**: its simulation is exposed directly, so the player
   must learn the *model* before they can play the *game*. That is the trap, and it is
   entered one reasonable feature at a time.

   The rule that prevents it: **a derived system buys COHERENCE, not mechanics.** The canopy
   may run a competition model — the player sees "a wood, thicker on the north slope". A
   village may be scored from terrain, roads and water — the player sees "a village where a
   village makes sense". Arbitrarily deep derivation is welcome, because it costs the player
   nothing to look at.

   **The measurable form: count the verbs.** The player's action vocabulary is a budget, and
   it is small — **15 keys bound today** (~11 gameplay, 4 meta), which is Doom-to-Souls
   territory and where it stays. Angband has 40+; DF is effectively unbounded through nested
   menus. So every new simulation faces one question: **does this add something the player
   must learn?**
   - **No** → it is free, however deep. Build it as deep as it wants to be.
   - **Yes** → it must *displace* something, or earn its slot against the onboarding budget
     (#8's one-mechanic-first-per-floor). "It is realistic" is not an argument; realism is a
     property of the derivation, never a licence for a verb.

   **The budget is NET, not frozen** (user, 2026-07-22): we can build more, but carefully, and
   we look for what to drop *at the same time*. Adding without pruning is how the budget is
   lost — never in one decision, always in ten reasonable ones. So a verb audit runs whenever
   verbs are added. The standing one (2026-07-22, read off `story.loft`):

   | binding | what it is | verdict |
   |---|---|---|
   | `.` and Space | both wait | **alias — keep.** An alias costs nothing to *learn* |
   | `1`–`9` + `Q` + `E` | numbered quickslots *plus* two named ones | **collapse the concept** — three ways to use an item is one too many |
   | `C` and `I` | character page *and* inventory page | **merge** — the hub already shows carried \| equipped |
   | `G` grab, gold auto | items manual, gold automatic | **an inconsistency to learn** — auto-pick-up drops the verb *and* the rule |
   | `N` next world | a host/dev action | **not a player verb** — move out of the play key space |

   ⇒ **15 keys → ~11, and three fewer concepts**, losing nothing a player would miss.

   **The rule paying off, concretely:** plan #11 P5 turns doors from gaps in a wall into real
   openings with hinges, leaves and clear widths — a large simulation deepening — and it costs
   **zero verbs**, because doors are **bump-to-open** (already specified in §18a). Deep
   derivation, unchanged interface. That is the shape every new system should have.

   Corollary — **legibility beats fidelity at the interface.** Where a correct simulation and
   a readable one disagree in what the *player* is shown, readability wins and the deviation
   is recorded (`SCALE.md` → the real-measurement rule already carries the same shape: ship
   correct, let the consumer depart deliberately).

1. **Procedural, never authored — in what SHIPS, not in what you write.** Content is
   generated; hand-designed set-pieces are moros's path (§3 Non-Goals). crawler's richness
   comes from procedural variety + systemic mechanics, not authored layouts.

   **But the way you GET a good generator is to author one specific thing and strip it.**
   From the sibling project (`../crew_punk/BLOCKS.md`, and it is the sharpest statement of
   this anywhere in the org): *"The diorama is the research. The brick is the finding."*
   Nobody designs a good brick in the abstract — you write the concrete scene, discover what
   actually lands, and only then can you say which part was load-bearing.

   **crawler has always worked this way without naming it.** `land.loft` is a diorama — a
   hand-placed village — and plan #11 P0 stripped a *rule* out of it (real measurements; the
   1.51 m eaves nobody had measured). `PROPS.md`'s cart is a diorama that produced the
   general part-list. The authored artefact was never the deliverable; it was the instrument.
   So: **author freely to discover, ship only the recombinable finding** — and never confuse
   the diorama for content.
2. **Gentle vertical progression.** Levels/depth still make you stronger, but the
   curve is *much* shallower than Angband's (a run's span ≈ a few×, not 10×+), and
   the player↔monster power ratio is **capped both ways** — nothing is unreachable
   from under-levelling, nothing earlier goes trivial. The cap makes difficulty
   **fair/skill-gated, not easy**: a tough fight stays tough, it just can't be won or
   lost on raw level alone. (Tunes down §12a's curve / §10a difficulty.)
   - **Monsters mirror the item model (#3).** Their damage output, HP, and
     **resistances/vulnerabilities** scale as **percentage + flat, never 100%** — no
     monster is fully immune or one-note. **Vulnerabilities are a learnable shortcut,
     not a gate:** hitting a monster the way it's weak (the right damage type) is the
     *efficient, skilled* play — knowledge is progression (Zelda "find the weakness") —
     but it's **never required**; with extra levels you can **ignore the weakness and
     grind it down the hard way**. Raw level is always a fallback — fair, never walled.
     All of this is **tuning, not redesign**: we keep Angband's monster *bones* (stats,
     resists/vulns, behaviours, the data) and only adjust numbers/curve — monsters never
     need a fundamental rework, so the original set ports straight in.
3. **Progression is mostly lateral, from items.** Power and identity come from the
   *kit* you find, not your level. Items are **sidegrades + capabilities +
   tradeoffs**, not a linear +N ladder — no gear treadmill to grind, and two
   characters at the same depth play differently. Equipment/effects is the linchpin
   mechanic.
   - **HP is class-uniform** (fair); durability comes from **gear**, not class. The
     uniform HP base is set by **G2**; the gear modifiers below land with equipment (**G3**).
   - **Items stay relevant** — the same philosophy as the monster-relevance cap (#2).
     Modifiers mix kinds so no item type obsoletes the rest and the pool stays varied:
     **percentage** (scales with level — always proportionally relevant), **flat**
     (matters most early, never zero), and **damage-reduction** — general or **per
     damage-type** (fire/cold/…) resistances, each a **percentage + a modest flat** cut,
     **never 100%** (no full immunity — every damage type stays a threat, the same
     relevance cap as monsters in #2). Modelled on **Angband's resist / ego-item
     system**, friendly-tuned (capped, no immunity). Combine freely for variety.
   - **Canonical axis — armour vs casting.** **Metal armour** → **+HP%** *and*
     **+spell-cost%** (tanky, dear spells — the fighter's compensation for not casting
     cheaply); **magic cloth** → **−spell-cost%** (cheap spells, little HP — the
     caster's reason to stay light); plain gear sits between. More axes/types later.
4. **Class = a soft start, not a path.** A class is a **mild stat tilt + a starting
   equipment kit** that seeds a playstyle — and the kit is swappable, so class is
   where you *begin*, not a lock-in. Shrinks classes/races to tilt + kit data (no
   deep per-class mechanics).
5. **Checkpoint respawn, not permadeath.** Procedurally-placed **save points** (auto,
   no button) are footholds; the **first is the class's starting house/bed** (part of
   the class bundle). Death respawns you at the **last save point reached** — so death
   costs the *dive, not the character*: you **keep your character** (XP, items) but
   **lose exploration progress** (revealed map + dungeon state since that point; you
   re-dive from there — deeper save points limit re-traversal). Leverages deterministic
   gen — a checkpoint stores `{depth, position, stats, inventory, seed}` and re-derives
   the level. Save points double as goals (quest nodes later). A permadeath *mode*
   could return; the default is friendly.
   - **Souls-style stake.** *(Amended 2026-06-27 — money is **dropped** (§3a
     amendment): read every "gold" below as the **hauled goods/cargo** you drop at the
     death spot; the stake is concrete *stuff* from this dive, not a coin total, and
     your contact network persists. The grave/reclaim/group-up logic is unchanged.)*
     On death a percentage of your **gold** (`GRAVE_PCT`, start 50%) is left as a
     **grave marker at the death spot**; respawn at the checkpoint, then make the
     risky trip back to
     reclaim it. In **single-player**, **die again first and it's forfeit** (one grave at
     a time — the bloodstain tension). In **multiplayer** the rule softens: graves
     **persist** (lose half, it stays even if you die again — graves accumulate, any
     player can claim them) — a later, non-rewrite variant (the grave is owner-less data
     either way). Because graves pile up where players keep dying — the hard-to-reach,
     deadly spots — those places turn **gold-rich**, an emergent reason to **form a
     group** and clear them out together (positive-sum, still no PvP). **Gold only —
     never items / XP / levels** — so it stings but is
     **never progression-blocking** (the stake you value, not one that walls you). The
     grave is **owner-less** (any character can claim it — co-op-friendly) and there is
     **no PvP**. The grave persists across the level regen and re-materialises when you
     return to that depth. *Why the stake bites:* characters have a **hauling
     (carry-weight) limit**, so loot must be **sold to a merchant** — or **bartered with
     players** (MP) — to become gold. Gold is therefore *earned, converted loot*, not
     abstract currency; losing it is losing real hauling-and-selling effort. (Carry limit
     + merchants + barter are economy systems — later; ItemDef already carries
     `i_weight` + `i_cost`.) The limit also seeds a **high-value capacity tier** —
     backpacks, a pack-horse, a cart — that raises how much you can haul (more loot →
     more gold → more at stake): valuable items worth protecting in their own right.
     **On death these don't come back with you** — your horse / cart (and the bulk loot
     they haul) **stay at the death spot**, not transported to the respawn; only your
     *person* (worn + personally-carried + half your gold) returns. So the capacity tier
     is a **bigger stake than the gold grave** — recover the vehicle *and* its cargo by
     trekking back — and it's exactly the gold-rich prize a group bands together to
     reclaim from a deadly spot. The abandoned vehicle is **never auto-destroyed** —
     monsters don't attack it while you're away, so it is never a *permanent* loss — but
     it must be **fetched**: travel back and lead it home (a group can help in MP). The
     stake is the retrieval trip, not the item. (Respawn already drops the rest; the
     personal/hauled split lands with the carry-limit + capacity items.)
6. **No factions / NPCs.** The entity set stays Angband's — monsters · items · dungeon
   · uniques. Quests / motifs (future, see BUNDLE.md) are *structure over* those
   pools, never a social sim. A "captive" (a rescued princess) is a special passive
   monster/object. ⚠ **Superseded twice — read the departures below before relying on
   this**: the co-op ally faction, and the living settlement + standing (plan #17 `S7`).
   What survives is the *"never a social sim"* clause, which both departures are held to.
7. **Lean inputs.** Attack-on-push (you strike what you face by moving into it),
   bump-to-open doors — capabilities are added without piling on buttons.
8. **Engaging onboarding — a novelty curve, not just a difficulty curve.** The biggest
   fix vs Angband: its early floors are dull because the *mechanical richness is
   back-loaded to depth* — you commute, you don't discover. Here every early floor
   **introduces something** — a mechanic, an item capability, an enemy behaviour, a
   hazard — as an interesting *first*, taught by play, never a tutorial wall, never an
   empty filler floor. The gentle curve (#2) + lateral items (#3) are what *let* early
   content be genuinely interesting instead of trivial or lethal. Delivered
   procedurally via **composed encounters** (Angband's pits / nests / themed packs /
   guardian setups / aftermath generation — procedural, not authored) + systemic
   mechanics firing early. *Implementation leans lightly-baked* — a soft rule that
   early floors each surface one new mechanic — exact pacing to tune.
9. **Player-chosen difficulty — gentle ↔ harsh zones.** The world spreads danger
   *horizontally* (§10a: `zone_danger + depth`), not as a forced level ladder. Because
   the player↔monster ratio is capped and gating is skill- not stat-based (#2), harsh
   zones are *attemptable, not walled* — so the player **sets their own progression
   curve** by where they go: cruise the gentle zones, or dive into a harsh one for
   risk/reward (better lateral gear, faster progress). Lose-the-dive death (#5) makes
   venturing a fair gamble; save points are the footholds that let you push. Zelda-open
   world, Souls-optional-hard. (Realized by L2 zone-difficulty / L3 overworld — a
   *later* milestone; near-term G1–FOV is single-dungeon.)
10. **Angband bones, friendly tuning** (the umbrella). Keep the systems (combat
   resolution, monster/item rules, FOV, AI); make the *experience* — curve, death,
   class weight, onboarding — welcoming. The build order doubles as the onboarding
   curriculum: each addition debuts a mechanic engagingly.

**Forward-compatible — multiplayer (later; §3 Non-Goals).** The same choices that give
player-chosen difficulty keep the door open for a *later* multiplayer addition: no
permadeath + home/save-point respawn (persistent characters, long sessions); a shared
**seed-deterministic, bundle-defined world** (every client generates the same world —
cheap sync); a flat curve (different-skill players co-op without trivializing); and a
renderer-agnostic, data-only kernel that can run **server-authoritative** over the
existing `loft-libs-net` (server / game_protocol). Not built now; not designed against.

### Amendment (2026-06-27) — co-op party, Tension & the combat model → PARTY.md / RESOLUTION.md

A design direction explored after this section was written, specified in full in
**PARTY.md** (goal-directed AI party, moros-style **Tension**, **cards** as the
coordination UI, a Slay-the-Spire combat *undercurrent*) and **RESOLUTION.md**
(pluggable resolution backend + the progression/difficulty model). It is mostly a
*concretisation* of the pillars above, plus a few **deliberate structural
departures** recorded here so the charter is not silently contradicted.

**Consistent with / concretises the pillars** (no conflict): the power-ratio cap
(#2 — nothing walled by under-levelling, nothing goes trivial), lateral
capabilities-not-a-+N-ladder (#3), class = soft start (#4), skill-gated not
stat-gated harsh zones (#9), and the "Accessible ≠ easy / Dark Souls" framing all
*already* point here. RESOLUTION.md's **Dark-Souls "no number is a gate"** and
**breadth-over-height** are these pillars made exact.

**Deliberate departures (beyond "Angband bones, friendly tuning" #10 — these are
*mechanism* changes, not just numbers):**
- **Co-op party + an ally faction** — relaxes pillar **#6 ("No factions / NPCs")**:
  a *friendly* faction (goal-directed party allies, AI now / human drop-in later)
  now exists. This is still **not a social sim** — allies are combat/coordination
  actors, the entity model just gains a friendly side. It also **updates the
  multiplayer note above**: the co-op axis is now *actively designed for* (specified
  in PARTY.md, built incrementally — allies first, human takeover later via the
  `gameflow` intent seam), not merely "not designed against."
- **A living settlement, and STANDING with it** — relaxes pillar **#6** a second time, and
  ⚠ **the first half of it was already relaxed without being written down here**: farmers,
  gatherers, merchant carts, workshops and a quest-running guard master are all shipped
  (`OVERLAND.md` §13b/§13c, `CRAFTING.md`), so "no NPCs" has not described this engine for
  some time. On top of them, plan #17 `S7` adds **standing** — earned *locally*, per
  settlement — which lets a player raise a **militia** that enlarges the safe area on its
  own. This is the campaign's advancement axis: the hero grows in **what they can cause**,
  and it spends **nothing** from pillar 0's interface budget (the petition is
  `sim_talk_to` — bump-to-petition, beside #7's bump-to-open). ⚠ **Still not a social sim,
  and the guard rail is exact**: standing is ONE number per settlement, read as a category,
  with exactly ONE consumer. A second consumer is a re-check, not a free extension.
- **Combat-resolution model** — extends #10's "keep combat resolution": the Angband
  to-hit math is **kept but repurposed as a two-tailed *crit engine*** (no hit/miss
  whiff; **damage always ≥1**; a crit strips the foe's mitigation / a fumble exposes
  the actor), with a **Slay-the-Spire mitigation/stacking/window undercurrent** (the
  two mitigation axes — *ward* and *intercept*; gear as a mitigation **ceiling**, not
  flat AC) and a **pluggable resolution distribution** (bell-curve option). The
  Angband rolls/HP/AC math are *kept and repurposed* (AC → crit input), not
  discarded. **And no death-by-attrition: HP bottoming out *Breaks the spirit***
  (out of action, recoverable) — **#5's death stake fires only on an enemy's
  deliberate *execute* of a Broken character**, never on chip damage (PARTY.md §5d).
- **Progression model** — the §12a Angband clevel stat-ladder is **superseded** by a
  moros-style **breadth-over-height capability tree** (powers/backgrounds/
  specializations = the card deck; raw stat height soft-capped). See RESOLUTION.md §5a.
  **And the stat set changes — DECIDED 2026-06-27: Angband's 6 stats are replaced by
  moros's 8** (Char/Dex/Endu/Hand/Might/Perc/Speed/Will), which the capability
  catalog is authored against and which map onto the combat model (CATALOG.md §0;
  §12a amendment).
  - **Race deepens beyond pillar #4's "tilt + kit."** A race is no longer (just) a
    stat tilt — it grants a **distinctive set of innate powers/capabilities that
    change *how you play*** (flight, digging, smell, night-sight…), the **single
    richest thing crawler takes from moros** (RESOLUTION.md §5a). This is *playstyle*
    depth, not engine depth: each race is a different selection from the shared
    capability pool, **authored bundle-side** — so #4's "no deep per-class/race
    *engine* mechanics" still holds (no bespoke per-race code), while the *feel* per
    race becomes deep.

- **Economy — adopt moros's; DROP money (DECIDED 2026-06-27).** Crawler abandons
  **gold/currency entirely** for moros's **barter-goods-contacts** economy. Wealth =
  **goods** (held in **item slots**, bulk-limited) **+ leveled contact relationships**
  (a contact's level rises with repeated meaningful interaction — lodging → local
  knowledge → introductions → goods/refuge) **+ craft/forage capacity** — *not* a coin
  total. Items come via **backgrounds** (kit + slots), **contacts** (barter / earn /
  introductions — relationships, never coin), **crafting** (Handiness — make/convert),
  rare **finds**, and **forage/gather/hunt**. Ripples:
  - **#5's death stake re-bases from gold to *goods*.** On death you **drop the goods
    you were hauling** (slot cargo + the vehicle's bulk cargo, §5) at the death spot —
    reclaim by trekking back; your **person + your contact network persist**
    (relationships aren't carried goods, so death never costs your network). The
    "graves pile up at deadly spots → reason to group up" loop becomes **goods-rich**
    death spots. *Strengthens* #5: the stake is concrete *stuff* from this dive, not
    abstract money — and it makes **carry-capacity the core economic constraint**
    (goods are wealth; they can't be abstracted into weightless coin).
  - **Selling → bartering.** "Sell loot to a merchant for gold" becomes **barter goods
    through leveled contacts** (or craft them up / use them). Merchants are **contacts**.
  - **§12b item `i_cost` → barter-value + bulk** (what a contact will trade for it +
    what it occupies), not a gold price.
  - Companions are the **economic engine** (PARTY.md §5g): they bring backgrounds'
    **contacts + slots + crafting**; "fair *loot* split" (not gold) is a trust lever.

**The line we hold:** Angband **combat *systems*** (the rolls, HP, AC math, monster/
item rules, FOV, AI) are kept and repurposed; the **advancement model, the no-gate
difficulty philosophy, the co-op axis, and the economy (moros barter, no money)** are
where crawler intentionally diverges. Names/lore stay clean-room (§4) throughout.

> Stencils / bundles / castles / quests / motifs (BUNDLE.md, STENCILS.md) are the
> *authored* content architecture — moros-side / future. crawler's near-term is
> procedural + these pillars.

---

## 4. Intellectual property — clean-room

Game mechanics/systems aren't copyrightable; names, art, and specific lore are.
We clone the **systems** and invent the **fiction**.

- **Banned:** any Tolkien name (Angband, Morgoth, Sauron, balrog, Nazgûl, ent,
  Shelob, the One Ring, "hobbit", …) and any Zelazny/Amber name (Oberon,
  Amberites, the Pattern, Trumps, Serpent of Chaos). Use **"halfling"** not
  "hobbit".
- **Free to reuse:** depth progression, XP/leveling, stats/HP, resistances,
  ego-items/artifacts and monster "uniques" *as concepts*, spell schools,
  bump-to-attack, inventory; generic D&D race/class scaffolding.
- Angband/ZAngband are **GPL**, so reading their source to reproduce formulas is
  legitimate (crawler is LGPL-3.0-or-later, GPL-compatible). All original
  content lives in swappable data files. (The `moros_*` libs contain zero such
  names — verified.)

---

## 5. Architecture — kernel / view split

```
            ┌─────────────────────────────────────────────┐
            │  kernel  (pure loft, NO graphics dependency) │
            │  hex world · continuous player · hex-locked  │
            │  enemies · distance clock · collision ·      │
            │  combat · FOV · items · world generation     │
            │  → exposes read-only state + step(intent)    │
            └───────────────┬─────────────────┬───────────┘
                            │                 │
             ┌──────────────▼──────┐   ┌──────▼───────────────────┐
             │  view-2d (NOW)      │   │  view-3d (LATER)         │
             │  graphics package;  │   │  moros_render;           │
             │  world rotates to   │   │  camera_follow behind    │
             │  player heading;    │   │  the player; SAME kernel │
             │  cells/glyphs, HUD  │   │  state, 3D meshes         │
             └─────────────────────┘   └──────────────────────────┘
```

**Hard rule:** the kernel never calls a draw/window/input API. It takes an
**input intent** + frame delta, advances state, and exposes **read-only state**.
Swapping renderers requires zero kernel changes. (The `hexgeo`/`sim`/`gen`/data
modules import no graphics; `view`/`story` are the swappable front-end.)

**Reused from moros:** `moros_map` (hex world store, JSON, no graphics) and
`moros_render` (hex→3D mesh→GLB→WebGL, `camera_follow`, thick walls, curved
walls, cylinder posts, raised surfaces). We do **not** depend on `moros_sim`
(it imports graphics) — the small continuous/hex collision we need is
reimplemented graphics-free in the kernel.

---

## 6. World model — hex terrain

- **Coordinates:** axial `(q, r)` for hexes; continuous `(x, y)` for the player.
- **Hex layout = moros's default:** `HEX_WIDTH = √3`, `HEX_ROW_HEIGHT = 1.5`.
  *Caveat:* the geometry is **pointy-top** (vertex up/down, flat edges
  left/right) despite moros's comments mislabeling it "flat-top" — defer to the
  function. (`hexgeo.loft` works in clean axial coords; converts to moros offset
  coords at the moros_map boundary.)
- **"Hex length" `L = √3`** (all 6 neighbors equidistant) = the unit of the
  game clock (§11). The clock accrues **path length travelled** (wiggling costs
  time).
- **Two collision-level wall kinds** (moros's model): **solid full-hex walls**
  (non-walkable cells — Angband granite) and **edge walls** (thin barriers on a
  hex edge, stored on the 3 canonical edges N/NE/SE; the other 3 belong to the
  neighbor). A move A→B is blocked if **B is solid** or the **shared edge** is
  walled — `is_blocked_move`, with axis-separated **sliding** + a **collision
  radius** (already built in `sim.loft`).

---

## 7. Height & layers (mirrors `moros_map`)

The terrain is ultimately a **stack of layers (`cy`)** with a **per-hex centre
height (`h_height`)** — exactly `moros_map`'s shape, so the kernel carries the
fields and `moros_render` draws them (`y = h_height·HEIGHT_SCALE`, slopes via
`emit_slope_face`, layers stacked). Additive terrain data, 1:1 with `moros_map`
→ free 3D hand-off. **Height deltas between adjacent hexes are slopes/cliffs**
(→ rock faces, §9). Surfaced for later: step-up limit + climb cost vs. the
clock; height-aware FOV; **layer changes** (stairs/ladders/trap doors/cliffs — §8a;
walk-onto stairs is 2D-done) and **reading adjacent layers** on the plane (§7a —
sky/ceiling/shadows + the lower layer over a cliff); the 2D view shows one layer at a
time (height as shading).

---

## 7a. Reading adjacent layers on the 2D plane — sky, ceiling, shadows & cliffs

> **Being reworked by plan #11 (2026-07-22).** This section solves "how does a *2D plane*
> convey a layer above it" — a question first-person 3D answers by *showing* the layer
> instead of encoding it. The **layer MODEL** below (what a layer is, how portals link them)
> survives and is still the target; the **2D reading conventions** (sky glyphs, ceiling
> tints, shadow hints) retire with the 2D view in plan #11 P9. Keep reading for the model,
> not for the presentation.

*Designed first (the user's call). A near-term 2D render feature; it reads the layer-above
data, so it rides §7's multi-layer model (L6) + §9's outline engine — a **no-op on today's
single-layer dungeon**, designed now to land with that work.* This is the clearest case of
the guiding principle: **the 2D game is first-class and complete in its own right (some
players prefer 2D) — most of the design lives on the 2D plane, and the *optional*
`moros_render` build just *extrudes* it** (round towers, stairs §8a, height §7 are each
designed and playable in 2D first; **3D is additive, not the destination**). Here the 2D
floor is made to *read* the layers **above** (sky / ceiling / cast shadows) and **below**
(the lower layer seen over a cliff).

**What's overhead.** For a hex `(q,r)` on layer `cy`, consult one layer up (`cy+1`) only —
not deeper levels:
- **Open to sky** — nothing solid at `(q,r,cy+1)`: daylight reaches the floor.
- **Under a ceiling** — `(q,r,cy+1)` is solid (a roof / the floor of a structure above).

**Three cues, all planar stand-ins for what 3D would render for free:**

1. **Sky-vs-ceiling tint (per hex).** Tint the floor by the overhead test: **open-sky**
   hexes catch daylight — **brighter, slightly warm** (aged stone in sun); **ceilinged**
   hexes are **dimmer / cooler** (in shade). One clear value step → you read *inside vs
   outside* at a glance. A per-hex brightness multiplier on the floor colour: the kernel
   exposes `hex_ceilinged(q,r)`, the view applies the tint. In 3D the roof casts this shade
   for real; in 2D the tint fakes it.

2. **Cast shadow of the structure above (exact projection).** Take the `cy+1` structure's
   **footprint outline** — the *same polygon §9's overlay engine already emits* for its
   walls/buildings — and **project it onto the `cy` floor**, offset by a fixed sun vector:
   `shadow_poly = footprint ⊕ (sun_dir · height_above · k)`. Floor under the footprint =
   full ceiling-shade; floor inside the *offset* polygon = the cast shadow. You see "a
   building stands overhead" from its shadow across the floor — a 2D cue for real 3D
   structure. This is an **exact-invariant projection** (a fixed affine offset of a known
   polygon): per the `design-protocol` skill, **plot the concrete end-result first** (one
   footprint + one sun vector → the exact shadowed hexes) in a tiny `tools/` prototype —
   like the wall straightener — *then* port. Don't approximate it.

3. **The lower layer over a cliff edge.** When the player stands **beside a cliff** (a
   height edge dropping to `cy-1` — §7, a §9 rock-face boundary), render the **lower
   layer** visible over the drop — its floor + features — drawn **darker and blurred**
   (atmospheric depth: less light, out of the focal plane). You *see down* into the area
   you could jump or be pushed into (pairs with the cliff portal, §8a). Only the
   immediately-lower layer (`cy-1`), only the region the cliff edge reveals from the
   player's side. In 3D you simply see down the cliff; the 2D dim+blur composite is the
   planar stand-in. (Which `cy-1` hexes the edge reveals is a geometry question — if it
   needs to be exact, pin the end-result first, `design-protocol`.)

**Scope & dependencies.**
- Applies where a layer **above** exists: the **overworld + buildings** (outside = sky;
  under a roof = ceiling + its cast shadow) and **multi-storey structures** (an upper floor
  shades the one below). Needs the multi-layer data (§7 L6) + the §9 footprints — so it's a
  no-op on the current single dungeon, designed now to land with that work.
- **Deeper enclosed levels** (no sky above) — *maybe later* (the user's "we might even do
  something there too"): a faint ambient/depth darkening, or a hint of the level overhead.
  **Out of scope now.**
- Architecture (§5): the **geometry is kernel / outline-engine** (renderer-agnostic —
  `hex_ceilinged`, the projected shadow polygons); the **tint/shadow *drawing* is
  view-side**. `moros_render` reproduces both from real geometry + a light; the 2D version
  is the planar stand-in.

---

## 8. World structure — wilderness overworld + dungeons

A **wilderness overworld** (a large surface hex map — terrain, height, towns,
dungeon entrances) you travel across continuously, plus **dungeons** (separate
descending hex maps) entered from it. The overworld *is* a `moros_map`;
`moros_render` draws both in 3D. The kernel gains a **current map** +
**transitions** (enter/descend/ascend/recall); the view treats overworld and
dungeon identically.

- **World-keyed + persistent.** Every place is generated **deterministically
  from a position-seed** (`gen.world_key_seed(wx,wy,depth)`); once visited, its
  **state is persisted** (monsters/items/changes) so re-entry restores it —
  rewarding travel. Same machinery for overworld and dungeons; persistence via
  `moros_map` JSON per visited level.
- **Zone-based difficulty + shallow dungeons.** Each region has a **zone
  difficulty** (ZAngband's "law"); dungeons are **shallow**, monsters drawn at
  **effective level = zone difficulty + sub-level** (not pure descent).
  Progression is mainly **horizontal** (travel to harder zones). Preserves
  Angband monster-selection (`monsters.loft` `m_depth` + `mon_for_depth`, fed
  the zone-derived level) and fixes ZAngband's "no incentive to travel" weakness.

---

## 8a. Layer changes & level transitions — *2D mechanics & look now, 3D meshes later*

Most of the layer-change design lives on the **2D plane** (§7a); only the portal geometry
(steps, rungs, cliff face) is genuinely 3D. Probed `../moros` (the 3D target) + `../dryopea`
(2026-06-09; `../Dryopea` is the Dryopea language, not a game). moros is the source, and
crawler's `(wseed, depth)` already *is* moros's per-layer `(seed, cy)` — so **`depth ↔ cy`**
locks with no rework.

**2D plane — now / near-term:**
- **Mechanic — walk onto a stair to change level (DONE).** Step onto a `>` to descend, a
  `<` to ascend; no button — this is *why* E/Q stay free (§12). Edge-triggered: fires only
  on *entering* a stair hex, and the arrival stair is armed so you land on it without
  bouncing back (step off and re-enter to use it again). `sim_descend` regenerates
  `(wseed, depth)` and carries the hero (HP/XP/gold/inventory/equipment).
- **Means — one transition core, several portals.** The *same* layer-change (move `cy±1`,
  regenerate/load the destination, place at the arrival point) drives all of these — one
  invariant at the chokepoint, parameterized by *direction · trigger · reversibility ·
  fall-cost*, **not** four separate mechanisms (engineering-rigor):

  | Portal | Dir | Trigger | Feel / cost |
  |---|---|---|---|
  | **Stairs** | up & down | walk onto | gradual; the graded stepped look below |
  | **Ladder** | up & down | walk onto (climb) | steep 1-hex shaft; rung pattern |
  | **Trap door** | down only | walk onto (often hidden, sprung) | sudden fall, one-way — a surprise |
  | **Cliff jump / push** | down only | move off a height edge, or **knockback** | a fall → damage; ties §7 cliffs + combat knockback (shove a foe off a ledge, or get shoved) |

  All are 2D mechanics (walk-onto / fall / knockback all resolve on the plane); only each
  portal's 3D geometry (rungs, hatch, cliff face) is deferred (below).
- **Look — a small staircase that *reads* as stairs (draw-skill task).** Replace the flat
  `>`/`<` glyph with a graded step form: a **stepped line pattern + shadows** so a cold
  read names it "stairs" (the draw done-criterion, CLAUDE.md) — graded so **up = steps
  fanning *wider* + *lighter/white*** (ascending toward light) and **down = steps narrowing
  + *darker*** (descending into dark). Direction reads from value + perspective, no glyph.
  Author via the draw skill (PNG + recognition critic), composite where the glyph was.
- **Layout — multiple stairs per level + pairing.** Real Angband scatters several `>`/`<`
  (replaces today's single `>` at the farthest floor hex + single `<` at start). Which `>`
  maps to which arrival `<` is an **exact-invariant protocol** — plot the concrete
  end-result and pin it *before* coding (`design-protocol` skill). *(optional, from
  `../dryopea`'s free-landing: player-chosen descent; its carryover echoes §3a hauling.)*

**3D extrusion — deferred to the 3D build (§18a Eventually):**
- A stair becomes a **floor material with a `StairKind`** (`LINEAR | SPIRAL | GRAND_ARC`) +
  `climbable` flag; the per-hex **`h_height`** (§7) is the step delta; `moros_render` emits
  the geometry — **spiral** around a **newel** column, **grand-arc** along an **arc_pivot**
  radius. Add `StairKind`/height as kernel **data-only** fields when the 3D path is wired;
  the 2D look above already conveys direction, so nothing blocks on it.
- **`moros_init` shape** (the aside): palette-first (`well_known_materials/walls/items` →
  map → state); crawler's monster/item DBs before `sim_new_gen` already match — no change.

**Current 2D baseline (what the above enriches):** tile kind `2 = down`, `3 = up`; one `>`
at the farthest reachable floor hex, one `<` at the player start; walk-onto transition;
per-(cy/depth) level-state persistence (§8) restores a level on re-entry.

---

## 9. Feature overlays — walls, buildings, castles, roads, rock faces

The hex terrain (§6–7) is the simulation truth. Walls/buildings/roads/rock-faces
are **one outline engine** producing **render geometry** over that terrain.

**One processor, parameterized per feature:**
- **Input** — run/polylines, either *placed* (houses, roads, walls) or
  *derived from terrain* (rock faces = layer-boundary silhouettes; organic caves
  = solid/floor silhouette).
- **Knobs** — **direction resolution** (snap to **12** = 30° or **24** = 15°)
  and **junction policy** (**sharp-miter** / **rounded-arc** / **semi-rounded** /
  **round-tower**).
- **Output** — render geometry only (segments / arcs / towers / raised surfaces)
  → 2D now, `moros_render` in 3D.

| Feature | Source | Dir | Junction / outline |
|---|---|---|---|
| Houses/buildings | placed (square local, `gridgeo`) | 12 | sharp 90° |
| Roads | placed | 24 | rounded (smooth turns) |
| Town/castle walls | placed | 24 | sharp curtains + **round towers** at corners |
| Rock faces | terrain layer boundary | 24 | road-rounded **now** → **semi-rounded later** |

- **Buildings** are laid out in a **local square grid** (`gridgeo.loft`) so
  corners are clean 90° by construction, then oriented to one of **12 directions**
  (k×30°: the hex lattice's 6 edges + 6 vertices) and placed at a hex anchor.
- **Castle curtain walls are 2 hexes wide** → a **walkable rampart top** +
  **battlements** (parapet). A castle wall is therefore a **height feature**
  (§7): solid at ground, walkable on the elevated top (reached by stairs/gate
  tower); **round towers** rise to wall-walk height and link the rampart runs.
- **Both wall experiments have homes:** the parked Douglas–Peucker **straightener
  → buildings & castle walls** (sharp); the active averaging/Laplacian `wallgeo`
  **→ roads & (for now) rock faces** (rounded). The three geometries map 1:1 onto
  `moros_render` primitives that already exist — `emit_wall_quad` (straight),
  `emit_thick_curved_wall` (arc), `emit_cylinder_post` (round tower/post),
  raised surfaces (ramparts) — so the 3D side is largely free.

**Collision stays on the hex grid; the overlay is render-only.** Towers keep
their own **hex**; walls use the **3 canonical hex edge-walls** (`h_wall_*`);
2-hex castle walls + cliffs use **height**. The continuous player collides
against **hex cells / edges / height**, never the pretty overlay segments.
**Kernel = hex collision truth; view = pretty overlay derived from it.**

---

## 10. Actors

- **Player (continuous):** float `(x,y)` + heading θ; derived *current hex* is
  used for combat/adjacency.
- **Enemies (hex-locked):** logical position is a hex centre; move **one hex per
  tick**, animate smoothly between centres (interpolation keyed to the player's
  accrued distance); attack into the **whole hex** the player occupies.

---

## 10a. Monster AI, placement & level structure

Three meshing layers, all in the kernel (no graphics), Angband-faithful and
adapted to the hex grid + distance clock. They join at **"a monster is spawned
asleep on a level whose difficulty is set by where it is."**

### Difficulty model — one number
`effective_level = zone_danger(wx,wy) + dungeon_depth`. Feeds monster selection
and loot. Difficulty is mostly **horizontal** (travel to nastier zones); descent
adds on top. Dungeons stay **shallow** (per-zone `max_depth` ≈ 3–8), so the
deepest content lives in far dungeons, not 100 floors down (§8).

### Level & world structure
- **Identity & keying:** a level is `(wx,wy,depth,kind)`, generated
  deterministically from `gen.world_key_seed(wx,wy,depth)`. Same key → same level.
- **Persistence:** first visit realizes + stores the level (map + monster roster
  + items + your carnage); revisit **restores** it (Angband regenerates on leave —
  we persist, to reward travel). Bound storage: keep recent + always-special
  (town, unique sites); evicted ordinary levels re-derive from seed.
- **Connectivity (stairs):** overworld entrance → depth 1; `>` descends, `<`
  ascends; ascending from depth 1 exits to the overworld cell. Connected stairs:
  you arrive on the matching stair. Bottom level (`max_depth`) has a guardian +
  reward and no down stair. Stairs are **tile features** (extend `0 floor / 1
  wall` with `2 down / 3 up`).
- **Level kinds / profiles** (rolled, weighted by `effective_level`): overworld
  (wilderness surface — terrain/towns/entrances), town (safe hub), dungeon
  (room+corridor → cavern → maze → lake), special rooms (pit/nest/vault). Aligns
  with the moros multi-layer/height target (§7): depth ≈ layer index later.
- **State model:** `World{ cur(wx,wy,depth), hero, persisted-levels store, global
  unique flags }`; `Level{ tiles, features, monsters, items }`; transition = save
  current → resolve key → restore-or-generate → place hero on the arrival stair.
  `sim_new_gen` generalizes to `level_load(world, wx, wy, depth)`.

### Placement (`get_mon_num` + `place_monster`)
- **Budget:** `N = LEVEL_MONSTER_MIN + rand(1..8)` per level (Angband ≈ 14+d8),
  scaled to map size — a *spread*, not one species.
- **Selection `get_mon_num(effective_level)`:** candidate pool = races with
  `m_depth ≤ effective_level`; probability ∝ `1/m_rarity`; **deepen bias** (keep
  the deepest of a few draws); small **out-of-depth** chance boosts the level for
  a nastier surprise; **uniques** gated to `depth ≥ m_depth`, once per game
  (world-state), never in random groups.
- **Where:** random passable, unoccupied floor (rooms *and* corridors); **never
  in LOS / within ~a screen of the player start**; retry-capped, `log` shortfalls.
- **Groups & escorts:** `MF_GROUP` places a cluster of the race (size scales with
  depth); unique escorts (future `MF_ESCORT`) bring a themed retinue.
- **Initial state:** spawned **asleep** (sleep depth from new `m_sleep`, else
  derived from `m_vision`) — the input to awareness below.

### Behavior (`process_monster` pipeline)
Per monster action:
```
energy += gain(speed); while energy>=100 { act; energy-=100 }   # speed/energy
wake check (if asleep): roll vs distance & player noise/stealth  # awareness
if asleep: stop
acquire target: player if perceived (LOS + m_vision) else last-seen / scent
decide: afraid? -> FLEE | caster+in range? -> CAST | adjacent? -> MELEE
        | can move? -> STEP via noise flow-field
breeder? -> maybe multiply (free neighbour, under cap)
```
- **Speed/energy:** one world tick = the player spent one hex (one player turn).
  `gain(speed)` via Angband's `extract_energy`, normalized so `m_speed=0` → +100/
  tick (parity with the player), `+10` ≈ ×2, `-5` ≈ ×0.66; leftover carries. The
  hook for player haste/slow (scale the distance clock).
- **Awareness:** spawn asleep; each tick within range, roll to wake (closer +
  louder player vs stealth ⇒ wakes). Kills "the whole level swarms at t=0."
- **Perception:** hex LOS (walk the hex line, blocked by solid) + `m_vision`.
  Loses sight → head to last-seen, then scent, then give up.
- **Pathfinding (the real fix):** a **noise flow-field** — Dijkstra cost grid from
  the player's hex over walkable cells, recomputed on player hex-change; each
  monster steps to the lowest-cost neighbour ⇒ **routes around walls**, no clump /
  stuck (greedy `best_step` can't). Scent = decaying timestamps for out-of-LOS
  tracking.
- **Modifiers/flags:** `MF_NEVER_MOVE` (attack-only), `MF_ERRATIC` (random step
  X%; split into `RAND_25/50` for fidelity), fear/flee (step *up* the gradient),
  `MF_GROUP` surround, `MF_BREEDER` multiply. Future: `PASS_WALL/KILL_WALL`,
  doors, `MOVE_BODY/KILL_BODY`, `SMART/STUPID`.
- **Casters (`MF_CASTER`):** cast-frequency roll; in range + LOS → pick from the
  realm/spell pool (bolt/ball/breath/summon/heal/blink) — the §13 ZAngband hook.
- **Melee:** Angband to-hit vs `m_ac`, blow dice/effects (expand `m_dam` → dice +
  a blow list later); big hits can trigger fear.

### Data additions
- `MonsterDef`: `m_sleep` (sleep depth). Existing `m_rarity / m_depth / m_speed /
  m_vision / m_ac / m_flags` already feed the above.
- New flags: `MF_SMART, MF_STUPID, MF_COWARD/MF_FEARLESS, MF_RAND_25/MF_RAND_50,
  MF_PASS_WALL/MF_KILL_WALL, MF_OPEN_DOOR/MF_BASH_DOOR, MF_MOVE_BODY/MF_KILL_BODY,
  MF_FRIENDS, MF_MULTIPLY (= BREEDER)`; a separate **spell-flag bitmask** for casters.
- `Enemy` (per-instance): copy `speed / vision / ac / flags` off the def + dynamic
  `energy, awake/alert, fear, seen_q/seen_r`.
- `Sim`/`World`: noise flow grid (+ optional scent grid), `player_hex` cache,
  `player_noise/stealth` scalar, persisted-levels store, global unique flags.

### Testing — three tiers (mirrors modern Angband)
Angband ships `src/tests/` (unit incl. data-file parser tests, `make test`, CI),
`main-stats` (`-m stats`: thousands of generated levels for balance
distributions), and the **Borg** (an automated player). We mirror all three:
- **Unit** (our `*test.loft` pattern): deterministic seeded assertions —
  `aitest` (sleeper stays put until approached; `NEVER_MOVE` never moves; monster
  routes around an L-wall; fast monster closes on a fleeing player; afraid flees;
  caster fires at range), `placetest` (same seed → identical roster; none in
  start LOS/radius; counts in `[N_min,N_max]`; `MF_GROUP` clusters; unique once &
  not below depth; restore reproduces hp/positions), `leveltest` (descend→ascend
  returns the persisted level; stairs reachable; `effective_level` = zone+depth;
  bottom has a guardian, no down stair).
- **Stats** (`placestats`, `main-stats`-style): run many `world_key_seed`s and
  assert the monster **distribution** matches the `effective_level` curve + OOD
  rate — the right tool for the probabilistic parts a single seed can't prove.
- **Borg** (later): a headless goal policy driving `sim_step` to descend/fight
  over long runs, surfacing emergent AI / transition bugs.

### Phasing
- **L1** stairs + real depth (deterministic per-depth gen; roster persistence
  next). **A1** budgeted weighted `get_mon_num` scatter with start-safety
  (replaces room-center). **P1** awareness + `m_vision` + `NEVER_MOVE`. *←
  foundation slice (in progress).*
- **A2 / P2** groups + OOD; noise flow-field pathing.
- **P3** speed/energy. **P4** erratic / fear / group-surround / breeder.
- **A3 / L2** unique-once + roster persistence; `effective_level = zone+depth`.
- **P5** casters + spell pool. **P6** melee depth (AC / to-hit / dice).
- **L3** overworld surface + town. **L4** profiles + pit/nest/vault. **L5**
  bottom-guardian + final boss. **L6** multi-layer height.

---

## 11. The distance-driven clock

The player's accumulated **travel distance** is the master clock. Every **`L`
(one hex-length)** travelled fires **one world tick** (enemies act, status/regen
advance). **Turning covers zero distance ⇒ zero ticks** ("turning is free");
standing still freezes the world. Enemy glide interpolation = `(accrued mod L)/L`
→ fully deterministic, no wall-clock dependence. A **wait** action advances one
tick in place. A turn engine wearing a real-time coat.

---

## 11a. The clock under multiplayer (locality-scoped) — *design; MP is built-for from the start*

The distance-driven clock (§11) is single-mover by construction: one player's travel is the
master tick. Multiplayer breaks that — many players move at once. The model: **the clock is
scoped to a *locality*, not the whole world.** Players in different localities keep independent
clocks; players sharing one share a clock.

- **Locality = "together".** Two players are *apart* when they can't affect the same moment —
  **different rooms / layers now; a distance radius later** (§7 `cy`, §12 FOV). Apart players
  run their own distance-driven local time and **never block each other — just ignore it.**
  They couple into a shared locality clock as they converge, and decouple as they separate.
- **Shared clock when together.** The world (monster AI, status/regen) must advance once per
  `L` of *locality* travel, the same for everyone present. The base rule — *a player skips a
  turn when another moves* (one mover consumes the shared tick) — is correct but feels frozen.
  Two softeners keep the real-time feel without losing world-consistency:
  1. **Queue key presses** — each player's input is buffered, so a held/intended move isn't
     lost while it isn't their turn; it fires the instant the shared turn allows (continuous-
     glide intent preserved, not dropped).
  2. **Simultaneous-move window** — when another player is **moving and visible on your screen**
     (FOV), you get a *small window* to move within the **same** world-tick, so co-located
     players move near-simultaneously rather than strictly alternating. The window is what keeps
     "we're in the same room" feeling live.
- **Invariant:** within a locality, all moves landing in one window resolve against **one**
  world-tick; across localities, clocks are independent; convergence merges two locality clocks
  (resync), separation forks them — §11's "turn engine in a real-time coat", held per-locality
  under N players.
- **Open (pin when MP is built):** the locality threshold (room/layer → distance radius); the
  window length; merging two localities' clock state on convergence; fairness when many cluster.
  Ties to the Player handle (`player.loft`, built MP-shaped) and FOV (visibility = "on screen").

---

## 11b. Per-player data layout — *deferred decision (do NOT migrate yet)*

Today all player state is ~20 flat fields on `Sim` (`php/phpmax/over, clevel/xp/gold, stat_*,
px/py/heading/accrued, inv/ninv, eq/wdam/pac, rstate, grave_*`). Multiplayer wants that
*indexed by player*. **Decision: keep accreting behind the primitives; do not move the data
into an MP structure yet.** The reasoning — recorded so it isn't re-litigated, *and* so nobody
migrates it prematurely:

- **The expensive boundary is already locked.** Every call-site goes through the Player methods
  + `sim_*` primitives (`p.drain_stat(s,…)`), which are MP-shaped now and never change. The
  data layout sits *behind* that seam, so moving it later is a pure internal refactor with
  **zero call-site impact** — there is no "rewrite everything later" penalty for waiting. (This
  relies on the architecture invariant: the view reads player state *only* via `sim_` accessors,
  never raw `s.php`.)
- **The right container is gated by a live loft bug.** `vector<PlayerState>` (a struct in
  a vector, with *nested* vector fields for stats/inv/eq) is where loft still bites —
  growing a struct's vector field via capture-append-reassign empties it (loft#320, fixed
  upstream, not yet in the installed toolchain). That makes the container a **verify-first
  prototype** question (DESIGN-PROTOCOL / exact-invariant), not a migrate-on-a-guess.
- **`PlayerState`'s shape needs §11a.** Extracting it forces the per-player vs per-*locality* vs
  per-world split (position is per-player; the map is world; the clock is per-locality) — and the
  locality model (§11a) is itself unbuilt. Migrating now bakes in an unvalidated split.
- **Move once.** flat → `PlayerState` struct → `vector<PlayerState>` is two migrations; grouping
  the fields now doesn't de-risk the hard part (the vector under loft).

**Cost of waiting:** each player field added (e.g. the three-layer stats) is one more line the
eventual mechanical move touches — contained, all behind the primitives.

**Trigger + how (when MP / §11a is built):** (1) verify-first which container loft tolerates;
(2) pin the per-player / per-locality / per-world split; (3) move the data *once* into the
proven shape, primitives unchanged. The middle option — extract a single-instance `PlayerState`
now (no vector) — was considered and **declined**: it costs a refactor today, still bakes the
split early, and doesn't de-risk the vector.

---

## 12. Controls, camera, FOV

**Controls** (analog/held; release stops immediately, no inertia):
`W`/`S` glide forward/back (cost time), `A`/`D` turn (free), `.`/`Space` wait,
`g` grab, bump-forward-into-enemy = melee, and **walk onto a `>`/`<` to change
level** (no button — §8a). `E` and `Q` are **reserved** for character actions
(fire arrow / cast spell), which is why stairs are walk-onto, not a key. Heading is
a continuous float (the "30°" is turn *feel*, not quantization).

**Camera — egocentric, forward-biased:** the world rotates around the player so
heading is always "up"; player anchored **~70% down** the screen (rear-visibility
margin). 3D later = `moros_render::camera_follow`.

**FOV:** wide forward arc + short all-around radius — directional, tense
exploration; distant flankers unseen, point-blank rear always seen.

---

## 12a. HUD sidebar, character stats & levelling

A persistent **left sidebar** (Angband's character column) plus a **bottom status
line**, drawn screen-space over the egocentric view (like the HP bar — fixed, does
not rotate). Backed by a runtime **`Hero`** model (kernel data, graphics-free; the
sidebar is its view). Uses the existing `classes/races/items` tables (6 stats:
STR/INT/WIS/DEX/CON/CHR; class `c_hd`/`c_xp`/`c_spell_stat`/`c_realm`; race
`r_hd`/`r_xp`/`r_infra`; per-skill `*_melee/bow/device/disarm/stealth/save`) and
monster `m_xp`.

### `Hero` model (M2)
- **Identity:** name, race idx, class idx, **title** (by class + level).
- **Progression:** `clevel` (1–50), `xp`, `gold`.
- **Stats:** the 6, stored Angband-style (3–18 then 18/01..18/220 percentile),
  **cur + max** (max = drain ceiling). `effective = base(rolled) + race_mod +
  class_mod` (+ equip/effects).
- **Derived (recomputed from stats+level+equip):** `maxhp/hp`, `maxsp/sp`
  (casters), `ac`, `speed`, the six **skills**, infravision, carry weight.
- **Conditions/timers:** food/hunger clock, poisoned/afraid/confused/blind/
  stunned/hasted/…; inventory + equipment slots (`items.loft` `SLOT_*`).
- The kernel's current `Sim.php/phpmax` are **subsumed** into `Hero.hp/maxhp`.

### Levelling (Angband formulas)
> **Amendment (2026-06-27):** this Angband clevel stat-ladder is **superseded** as
> the *primary* progression model by RESOLUTION.md §5a's **breadth-over-height
> capability tree** (powers/backgrounds/specializations; raw stat height
> soft-capped) — see §3a's amendment. The XP/threshold/derived-stat machinery below
> is **kept** (capabilities and the soft-capped stats still need XP, thresholds,
> and recompute-on-change), but "level-up = +clevel and a hit-die HP roll" is no
> longer the spine — most growth is a *new capability*, not a bigger number. Read
> this section as the baseline mechanics RESOLUTION.md §5a reshapes, not the final
> progression design.
>
> **Stat set (DECIDED 2026-06-27):** the **6 Angband stats below
> (STR/INT/WIS/DEX/CON/CHR) are replaced by moros's 8** — Charisma, Dexterity,
> Endurance, Handiness, Might, Perception, Speed, Willpower — which the capability
> catalog is authored against and which map onto the combat model (Might→damage,
> Endurance→mitigation/HP, Dexterity→crit, Perception→the perception action, Speed→
> the clock, Will→Tension-resistance, Charisma→leadership, Handiness→craft/device).
> See CATALOG.md §0. So the `Hero`/`races`/`classes` stat fields below grow 6→8 and
> re-key; the sidebar lists 8. Treat every "the 6 stats" reference below as "the 8."

- **XP needed:** `player_exp[clevel]` base table × **total exp factor**
  `(r_xp × c_xp)/100` ⇒ next-level threshold (warrior cheap, mage dear).
- **XP per kill:** `gained = m_xp × monster_level ÷ clevel` (scaled down as you
  out-level prey; `monster_level` from `m_depth`).
- **On level-up:** `clevel++`; add a **hit-die roll** (`c_hd + r_hd` base) + CON
  per-level bonus → `maxhp`; recompute `maxsp` + learnable spells (casters);
  refresh **title**. HP rolls come from a deterministic per-character table so a
  given seed levels identically (testable).
- **SP/casters:** from the **spell stat** (`c_spell_stat`: INT=arcane,
  WIS=divine) + `clevel`; spell fail-rate from stat + level vs spell level.
- **AC:** equipment + DEX + class; **speed:** equipment/effects; **skills**:
  `race + class + level + stat` (the to-hit / device / disarm / stealth / save
  numbers).

### Sidebar layout (left column, ~13 chars wide)
```
Name
Race  Class           <- e.g. "Halfling Mage"
Title               <- class+level title
LEVEL   n
EXP     n  (next: m)
GOLD    n
                    <- blank
STR  18/50
INT  15
WIS  10
DEX  16
CON  14
CHR  11             <- drained stat shown dim/yellow (cur<max)
                    <- blank
AC      n
HP   cur/max        <- plus the coloured bar, ratio-tinted
SP   cur/max        <- casters only
SPEED   +n
                    <- blank
L1  (50')           <- depth / location
```
- **Bottom status line** (Angband's): hunger (Hungry/Weak/Faint), then condition
  flags (Afraid, Poison, Conf, Blind, Stun, Fast/Slow…), and — when targeting —
  the **target monster's name + health bar**.
- **Render:** reuse `build_hud`'s font; bake static labels once; changing values
  (HP/SP/XP/gold/stats) via digit composition (`draw_number`) or re-bake-on-change
  (cache keyed by value) — all through the text bridge, square/text fallback-safe.
- **Layout:** sidebar claims the left ~130 px; the egocentric view re-centres into
  the remaining width (shift `CX`), so the player stays centred in the *play area*,
  not the window. Sidebar + status line never rotate.

### Phasing
- **H1** minimal `Hero` (promote `php`→`hero.hp`; clevel/xp/gold + the 6 stats
  from a fixed starting race/class) + **XP-on-kill** + **level-up HP growth**.
- **H2** render the sidebar (name/race/class/level/xp/gold/stats/AC/HP/depth).
- **H3** SP + casters, conditions + status line, hunger clock.
- **H4** character-creation screen (pick race/class, roll/point-buy stats).
- **H5** monster health bar / look-targeting on the status line.

### Testing
`herotest.loft`: same seed → identical level-up HP curve; XP-to-next matches
`player_exp × factor`; kill XP = `m_xp × mlvl ÷ clevel`; effective stat =
base+race+class; drained stat (cur<max) flagged; derived AC/SP/skills recompute
correctly. (Sidebar render verified via the `shot.loft` frame, like the HUD.)

---

## 12b. Items — generation, drops, pickup & inventory

Built on `items.loft` (cats `IT_*`, slots `SLOT_*`, dice `i_dd/i_ds`, `i_ac`,
`i_depth/i_rarity/i_weight/i_cost`, `i_power`, `IF_STACKABLE`, glyph+colour). Same
world-keyed determinism + persistence as monsters: **floor items live in the
`Level`**, carried/worn items live on the **`Hero`**.

### Item instances
A floor/inventory item is an **`ItemInst`** (not the static def): `{ def idx, qty,
to_hit, to_dam, to_ac, ego idx, art idx, flags(known/ID'd), charges, timeout }`.
Static stats from `ItemDef`; per-instance magic from `apply_magic`.

### Generation & drops (Angband `get_obj_num` + `apply_magic`)
- **Floor objects at level-gen:** a small budget placed in rooms (vaults richer),
  each via `get_obj_num(effective_level)` — pool = items with `i_depth ≤ level`,
  prob ∝ `1/i_rarity`. Same `effective_level = zone + depth` as monsters.
- **Monster drops:** on death, roll **gold** (level-scaled pile) and/or **items**.
  Add Angband drop flags to `MonsterDef`: `DROP_60/DROP_90`, `DROP_1D2/2D2`,
  `ONLY_GOLD/ONLY_ITEM`, `DROP_GOOD/DROP_GREAT`; items rolled via
  `get_obj_num(monster_level [+good/great boost])`.
- **Quality tiers / `apply_magic(item, level)`:** normal → **good** (plusses) →
  **great/ego** (ego pool) → **artifact** (rare, once each), enchant rolls scaling
  on `level`. Deferred past the basic drop.

### Pickup / drop
- On a hex with item(s): **gold auto-collects**; items grabbed with **`g`** (or an
  auto-pickup option). Stacks (`IF_STACKABLE`: potions/scrolls/ammo) merge by
  def+ego. Inventory ≈ Angband's ~23 slots; **weight** over the STR-derived carry
  limit **slows** you (speed penalty — ties into the AI speed model).
- **`d`** drops onto the current hex → `Level.floor_items` (persisted). Items render
  on the map as their **glyph in colour** (reuse the text-bridge glyph system: `$`
  gold, `!` potion, `?` scroll, `/` wand, `-` ring/amulet, …).

### Inventory & equipment model
- **`Hero.inventory`:** `vector<ItemInst>`, letter-indexed (a–w), category-sorted.
- **`Hero.equip`:** one slot each `SLOT_*` (weapon, bow, body, shield, head, hands,
  feet, cloak, light, **ring×2**, amulet). Wield/wear **`w`**, take off **`t`**;
  equipped items feed the Hero's **derived** AC / to-hit+dam / stat mods / resists /
  speed (the §12a recompute).
- **Identification:** unidentified items show by **flavour** ("a blue potion"); ID
  by use / scroll / sensing; ego/artifact properties hidden until known. (Later.)
- **Use/consume:** quaff (potion), read (scroll), aim (wand), use (staff), zap
  (rod), eat (food), fire (ammo via bow) — effects from the def (`i_power` + flags).

### Inventory screen (UI)
- A **modal overlay** — the distance clock **freezes** while open (consistent with
  "standing still freezes the world"). Toggle **`i`** inventory / **`e`** equipment.
- **Inventory view:** category-grouped rows — `letter) name (qty)   weight` (name in
  known/flavoured form; ego/artifact shown once ID'd).
- **Equipment view:** the slot list with each worn item (or "(nothing)").
- **Select a letter** → action menu: **wield/wear · take off · use/quaff/read · drop
  · inspect**; **inspect** opens a detail panel (description, dice/AC, known plusses
  & properties, weight, value).
- **Render:** text-bridge rows (reuse `build_hud` font) over a dimmed backdrop;
  fallback-safe like the sidebar.

### Data additions
- `ItemInst` struct; `Hero.inventory` + `Hero.equip`; `Level.floor_items`
  (`{hex, ItemInst}` list, persisted).
- `MonsterDef` drop fields/flags; a new `objects.loft` with `get_obj_num(level)` +
  `apply_magic(item, level)` (mirrors `monsters.loft` + the placement pass).

### Phasing
- **I1** floor gold + simple monster-death item drop (chance/quality from `m_depth`)
  + **pickup `g`** (auto-gold) + items as map glyphs.
- **I2** inventory `i` / equipment `e` screens + wield/wear/takeoff + AC/stat
  recompute + **drop `d`**.
- **I3** level-gen objects (`get_obj_num`) + quality tiers / `apply_magic` (ego).
- **I4** identification + flavours + use/consume effects.
- **I5** artifacts; monster drop flags; weight → encumbrance.

### Testing
`itemtest.loft`: same seed → identical floor/drops; pickup adds to inventory &
clears the floor hex; stack merge; wield updates AC/to-hit; takeoff reverts; drop
adds to (persisted) `Level.floor_items`; `get_obj_num` honours depth/rarity; over-
weight applies the speed penalty.

---

## 13. Source of truth for logic — hybrid

- **Modern Angband (4.2.x)** for the **core engine + monster/object rules/data**
  (`monster.txt`/`object.txt` flags, resistances, ego/affixes; combat to-hit/
  damage, stats, HP, XP/leveling, FOV, monster AI) — cleanest to reproduce
  faithfully.
- **ZAngband** for **world structure & flavor:** wilderness overworld (§8),
  **realm-based magic + the full spell pool** (~7 realms × 4 books × 8 spells;
  classes pick 1–2 realms), mutations later.
- **Spells ↔ monster/object rules are compatible:** every spell resolves as an
  effect/projection the target resists + saves against; ZAngband supplies the
  spell catalog, modern Angband the execution machinery. A small effect-type map
  + a few ZAngband-unique effects (Chaos/Trump/Death) bridge them.
- **Skills** = derived Angband values (not a skill tree).
- The placeholder values in the data tables (§14) will be **re-derived from the
  real source** as each system lands. Reproduce logic faithfully; only names are
  clean-room.
- **Tuning departs by design (§3a):** the *curve*, *death model* (checkpoint respawn,
  not permadeath), and *class weight* are deliberately friendlier than Angband —
  systems reproduced faithfully, numbers tuned for accessibility.

---

## 14. Content — data tables + procedural generation

Static catalogs are **loft data modules** (struct + table builder + helpers);
the runtime character is a struct; saves are JSON (loft struct round-trip).

- **`monsters.loft`** — 32 monsters (depth 1–25) + 4 original uniques (final boss
  *Maug*); stat/AI-flag fields. *(placeholder → align to `monster.txt`.)*
- **`classes.loft`** (8), **`races.loft`** (10, halfling-not-hobbit + original
  "highborn"), **`items.loft`** (54 base kinds across all categories).
- **`gen.loft`** — procedural dungeon generator (rooms + corridors, connectivity
  verified, deterministic LCG, `world_key_seed`). Grows: room types, vaults,
  buildings, towns, wilderness.
- **`gridgeo.loft`** — square basis for 90° building/wall layouts (§9).
- **To build:** `spells.loft` (ZAngband realm pool), a `Hero` struct + character
  creation, the feature-overlay processor (§9), combat/FOV/HUD.

---

## 15. Package layout (actual)

```
crawler/  (loft package "story")
├── loft.toml · loft.lock · Makefile · README.md · DESIGN.md
├── patches/            # parked diffs (wallgeo Douglas–Peucker) + README w/ hashes
├── tools/snap.sh       # Xvfb screenshot helper (make shot)
└── src/                # flat; kernel modules import NO graphics
    ├── hexgeo.loft     # hex geometry (axial)            — kernel
    ├── gridgeo.loft    # square geometry for 90° walls   — kernel
    ├── sim.loft        # world + player + enemies + clock + collision — kernel
    ├── gen.loft        # procedural dungeon generator     — kernel
    ├── monsters/classes/races/items.loft  # data tables   — kernel
    ├── wallgeo.loft    # wall outline (rounded active; DP parked) — derived geo
    ├── view.loft       # 2D egocentric renderer           — view
    ├── story.loft      # entry: window + loop + input      — view
    └── *test.loft      # selftest/montest/deftest/gentest/gridtest (headless)
```

`use <name>;` imports a dependency or sibling module. **No `kernel/` tree
imports graphics** — the invariant that keeps 2D/3D interchangeable.

---

## 16. Build & run

loft toolchain at `loft/target/release/loft`; deps resolved via
`--lib …/loft/lib/`. Use the loft-style **Makefile** (LOFT_REPO defaults to
`../loft`):

```sh
make play     # run in a window          make test   # headless self-tests + compile gate
make game     # single-HTML browser build make check  # quiet parse+bytecode gate
make shot     # Xvfb screenshot           make help   # all targets
```

(`--path` must end in `/`. Sandbox here can't grab the GL window — the user is
the visual verifier; headless logic is fully testable.)

---

## 17. Current state — what's built

- **M0 vertical slice** runs: generated hex map, continuous WASD with the
  rotating egocentric view, one hex-locked enemy ticking on travel distance,
  **collision with sliding + radius**, quit on Esc.
- **Data foundations:** monsters / classes / races / items tables (clean-room,
  tested, warning-clean).
- **Combat:** bump-melee, player/enemy HP, enemy-attacks-when-adjacent, death +
  game-over (`combattest`).
- **Procedural dungeon WIRED** (`sim_new_gen`): rooms + corridors populated with
  monsters from the DB by depth; monsters render as **glyph letters in colour**
  (`@` = player) on soft-black discs, with an HP readout + "YOU DIED" via the text
  bridge (font bundled in `assets/`). `gen.loft` itself is connectivity-verified +
  world-keyed.
- **Design specced** for **monster AI, placement & level structure** (§10a), the
  **HUD sidebar / stats / levelling** (§12a) and **items — drops / pickup /
  inventory** (§12b). Building the **foundation slice**: L1 stairs + real depth,
  A1 weighted placement, P1 awareness/vision/NEVER_MOVE.
- **Walls:** active `wallgeo.loft` = averaged/rounded silhouette (runs; the game
  is playable). The Douglas–Peucker straightener is **parked** at
  `patches/wallgeo-douglas-peucker.diff` (compiles, runtime-broken in the current
  loft interpreter — a nested-vector store panic — pending loft master fixes;
  base `60d523c`, source `8fcedc3`, replay in `patches/README.md`).
- **Headless tests** all green (`make test` = self-test + combat + wiring +
  compile; plus gentest, gridtest, deftest, montest).

---

## 18. Milestones

- **M0 — vertical slice** ✅ (built; visual confirm pending from user).
- **M1 — combat loop:** bump-melee, HP/death, wait, HUD, facing-cone FOV,
  game-over. Wire `gen` into the live game; spawn from `monsters` by zone level.
- **M2 — progression & world:** `Hero` struct + character creation (race/class/
  stats), inventory/equip from `items`; stairs + world-keyed multi-level
  descent; the feature-overlay processor (houses → roads → castles).
- **M3 — systems:** ZAngband realm magic (`spells.loft`), resistances,
  ego-items/artifacts, detection kit, monster speed; rock faces (semi-rounded).
- **M4 — 3D browser:** swap in `moros_render::camera_follow` (+ thick walls /
  towers / raised ramparts) over the unchanged kernel; ship single-HTML WebGL.

(Two threads wait on the loft master merge: the `wallgeo` runtime fix, then
intersection-based building corners.)

---

## 18a. TODO — ordered backlog

The canonical execution order (interleaves the per-section phases P*/A*/L*/H*/I*
by dependency + playability). Tiers are rough priority bands, ordered top→bottom.

### Done
- [x] **M0** vertical slice — continuous movement, rotating egocentric view, hex
  collision with slide + radius.
- [x] **Combat** — bump-melee, player/enemy HP, death + game-over.
- [x] **Dungeon wired** — `sim_new_gen` builds gen + spawns DB monsters; glyph
  rendering (`@`/letters in colour on backdrop discs), HP bar + numeric HP,
  "YOU DIED".
- [x] **P1** awareness — monsters spawn asleep, wake on `m_vision` + LOS,
  `NEVER_MOVE` holds.
- [x] **A1** placement — budgeted scatter, `get_mon_num` (rarity/depth/deepen/OOD,
  uniques excluded), `MF_GROUP` clusters, start-safe.
- [x] **L1** stairs + real depth — `>`/`<` features, deterministic per-depth
  descent (HP carry, arrival stair), `E` to use stairs, DEPTH readout.
- [x] **P2** flow-field pathing — BFS distance field from the player (respects
  solid hexes + edge walls), recomputed per tick; monsters descend the gradient
  and **route around walls** (no more greedy `best_step` wall-stick/clump).
- [x] **H1** hero progression — **XP on kill** (scaled by monster level),
  level-up grows max HP + heals the gain; `CL` + XP bar in the HUD. (Hero stored
  as flat `Sim` fields — `clevel/xp/gold/hcon`; full 6-stat block lands with H2.)

- [x] **Wait** — `.`/Space advances one world tick in place (enemies act; you
  don't move).
- [x] **I1** loot — monsters drop **gold** (auto-collected on walk-over) + a
  chance of an **item** (rarity-weighted by depth); items render as category
  glyphs (`$ ! ? | [ …`) and are grabbed with `g`; gold + inventory carry across
  levels; HUD gold readout. (Floor/inv use fixed arrays + counts — runtime append
  to a struct field is unreliable in loft — loft#320; the index-write idiom stays.)

### Now — **the 3D world view (plan #11)**

> **STALE BELOW — read this first (2026-07-22).** The G1–G4 + FOV list that follows
> **shipped** (`d1ecc56` = "FOV … M-Core complete"), as did much of *Next* and *Later*:
> sprites, the inventory hub, quests, ranged, quickslots, classes/races, the shrine, the
> overland, caves, travel and persistence all have gates in `tools/run_tests.sh`. The
> checkboxes were never re-ticked; **the gate is the truth, not this list.**
>
> The actual next work is **plan #11 — the hex field becomes the world you stand in**,
> first-person 3D, with 3D replacing the 2D view. See `plans/11-3d-world/` and
> `ROADMAP.md`. Items below that 3D *changes* rather than inherits: the wall aesthetic
> (G1), the top-down sprite perspective, and the dark-token palette — all re-decided
> in plan #11 P3/P3b/P8.

*Historic ordering, kept for the record — walls first, then the fastest path to a working
game with real (mostly lateral) progression:*
- [ ] **G1 walls** — nicer wall rendering: land the parked Douglas–Peucker
  straightener (crisp straight runs + sharp corners) — the loft bugs it was parked on
  (nested-vector type-id panic, keys.rs store desync) are fixed and probe-verified on
  the installed toolchain, so the diff in `patches/` should replay directly —
  then place corners at adjoining-line intersections. *Rounded
  vs sharp is your visual call.* (Graphics-only; `wallgeo`/`view`.) First set the
  **wall aesthetic target** with the `draw` skill — compose + cold-critique a
  reference egocentric view so "nice" is concrete (a checkable look) before coding.
- [ ] **Floor + wall tone** *(core look; do with G1)* — floor = warm **yellowish aged
  stone** (original Roman granite/travertine, *not* modern pure-white); walls
  **dark-toned**. `view` colours; forward-compatible with either bright-letters-on-disc
  (now) or the later dark-token palette.

*The cave-spider PoC proved the pipeline + locked the sprite rules (SPRITES.md). We
**integrate that first spider now** (it has a role — a dark silhouette **rotated to its
movement direction**), but **do not mass-produce** the 100+ catalog: letters stay for
everything else. **Next** sprite, *after the first bundle builds*: the **main character
as a fighter** with sword-swing stances on push/attack.*
*Rotation fits the **12/24-direction model** — 12 (k×30°) for stencils/items/creatures
(the spider), 24 (k×15°) for walls/roads/rivers — and crawler is the **testbed
validating that coherent set** (§9; STENCILS.md Q2). The graphics `draw_texture_rot`
primitive takes a general angle; callers snap to 12 or 24. The primitive is
**rotate + (optional) scale + translate** — the moros placement transforms (orientation
+ scale); a creature/item can be placed rotated *and* scaled. (This is the moros
item rotation/scale feature, native in 3D, proven first in 2D here.)*
- [ ] **Dark-token palette + drop the disc** *(bonus; with sprites)* — almost-black
  monster silhouettes read on the light floor; drop the soft-black token disc. Colour
  reserved for clothed/armoured creatures.
- [ ] **Mob/item sprites** *(parallel art track — doesn't block the progression
  work)* — author **clean flat-icon** 2D sprites with the `draw` skill (`sketch/draw.py`)
  → PNG in `assets/sprites/` → `graphics::gl_load_texture` (confirmed, graphics.loft:864)
  → composite where the glyph was (`etex[]`/`catex[]` in `view`). **Ground each in a
  real-world, verifiable form** (spider, ant, …); a sprite is **done when a cold read
  names it uniquely** as that form (unique recognizability = finished; don't
  over-render). Start with one mob + one item to lock style + the load path, then
  expand across `monsters`/`items`. 2D only. All sprites are **single static** images;
  the only animated one (later) is the **main character**, which gets a few **stance**
  frames (idle / reach-thrust / side-slash) driven by the attack-on-push swing.
  Refinement is **test-driven**: keep `.draw` sources in `assets/sprites/src/`;
  playtest flags off-theme sprites → adjust/redraw (recognition is the per-sprite bar,
  theme coherence is judged in-game). Monster sprites must show a **legit attack means**
  (spider → fangs) and use a **locked orientation — attack = up, uniform across
  monsters**. Scale a creature by its **body/core, not the sprite bbox** — thin
  appendages (legs, antennae) count less and overhang the cell.
- [ ] **G2 gentle curve** — flatten the level curve + cap the player↔monster power
  ratio both ways (§3a #2): retune `hero_maxhp`/`xp_for_level`/damage; `curvetest`.
- [ ] **G3 equipment + starting loadout** — wield/effects so **items are the
  progression** (§3a #3/#4): a few equip slots + stat recompute; a starting loadout
  (seeds the future class-bundle, BUNDLE.md); first lateral-item tuning of
  `items.loft` (sidegrades + capability flags, not +N). Subsumes I2's equip half.
- [ ] **G4 save points + respawn** — checkpoints (auto, no button) replace permadeath
  (§3a #5); first = the class's **home/bed**. Death → last save point: **keep
  character (XP/items), lose exploration** (map + dive re-derive from the seed);
  `savetest`.
- [ ] **FOV** — facing-cone field of view / fog of war (exploration; built on
  `hex_los`).

→ G1–FOV = a working, progression-bearing game. Onboarding (§3a #8) then rides these
as per-level "firsts"; the per-class **starting quest** (BUNDLE.md, classes-are-
bundles) is its authored/future form.

*Later (efficiency): pack mobs/items into a **sprite-sheet atlas** (one texture) —
the engine already has `create_sprite_sheet`/`draw_sprite_at`; add atlas-composition to
`tools/draw.py` then. (Rotated atlas-sprites = combine the rotated-MVP with sub-texture
UVs.) Now: one PNG per sprite via `gl_load_texture`.*

### Next — depth, texture & UI
- [ ] **Doors** — bump-to-open (closed/locked/jammed); block LOS + move; `gen`
  placement. (Lean input; pairs with FOV.)
- [ ] **Combat juice** — knockback on hit + **fear/flee** (P4 subset) via the flow
  field; no new buttons. (Combat polish — no hurry.)
- [ ] **H2** character **sidebar** (name/race/class/level/xp/gold/stats/AC/HP/depth) +
  status line.
- [ ] **I2 (UI half)** inventory `i` / equipment `e` screens; drop `d` (equip
  *mechanic* ships in G3).
- [ ] **P3** monster **speed/energy** (fast monsters run you down).
- [ ] **P4 (rest)** movement modifiers — erratic, group-surround, breeder multiply.
- [ ] **Persistence** — unique-once + **roster persistence on revisit** (distinct from
  G4's respawn; cross-session disk save/load rides the loft own-format serializer).
- [ ] **Combat depth** — AC / to-hit / blow dice (expand `m_dam`).

### Later — systems & world
- [ ] **P5** casters + ZAngband **realm spell pool** (bolt/ball/breath/summon/
  heal/blink).
- [ ] **I3/I4** level-gen objects (`get_obj_num`) + quality tiers / `apply_magic`
  (ego); identification + flavours + use/consume effects.
- [ ] **H3** player SP/casting, conditions + status line, hunger clock.
- [ ] **L2** zone difficulty (`effective_level = zone + depth`).
- [ ] **L3** wilderness **overworld** surface + town (enter/exit dungeons).
- [ ] **L4** level profiles (cavern/maze) + special rooms (pit/nest/vault).
- [ ] **L5** bottom-level guardians + final boss.
- [ ] **P7 / A2 / H4 / H5 / I5** — smart/pack/doors/wall-pass; unique escorts;
  character creation; monster health-bar/look; artifacts + encumbrance.

### Eventually
- [ ] **L6** multi-layer height model (§7); the feature-overlay processor
  (houses → roads → castles), incl. the parked Douglas–Peucker straightener.
- [ ] **Layer system** (**§7a + §8a**) — rides L6: multi-portal layer changes (ladder /
  trap door / cliff jump-push — one transition core), reading adjacent layers on the plane
  (sky/ceiling tint, cast shadow of the layer above, the lower layer over a cliff edge —
  darker/blurred), multiple stairs + pairing (pin the end-result first). The **3D meshes**
  (stair `StairKind`/newel, cliff face, hatch) ride M4. *(walk-onto stairs: shipped, 2D;
  the stepped+shadowed stair sprite — §8a "Look" — is a near-term draw task.)*
- [ ] **M4** 3D browser — `moros_render::camera_follow` over the unchanged kernel;
  single-HTML WebGL. *(The old E0514 rustc-mismatch blocker is resolved.)*
- [ ] **Testing tiers** — `placestats` (main-stats-style distribution harness),
  Borg-style headless auto-player.
- [ ] Pick a final **game title + world name** (replace the placeholders).

---

## 19. Open questions

- Backward glide (`S`) speed; on-screen scale; exact FOV shape.
- Monster turn order within a tick (simultaneous vs. sequenced).
- "Current hex" tie-break on hex boundaries; save/determinism seed boundary.
- Naming: pick an original game title + world name (replaces "Angband/Amber"
  slots); `story`/`crawler` are placeholders.
