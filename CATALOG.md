# CATALOG.md — initial capability / race catalog (seeded from moros)

A **first draft** of crawler's capability catalog (RESOLUTION.md §5a, PARTY.md §5/§5a),
**seeded directly from moros `html/data.js`** — the shared world's races, powers,
backgrounds, and specializations. Translation is **combat-first** (crawler is
combat-centric); each power's moros *Combat* use is mapped onto the crawler model
(two-channel resolution, mitigation/stacks/windows, Tension/coordination,
perception). moros's other-scenario uses (Travel/Camp/Forage/Negotiation) map to
crawler's overland/rest/loot/parley and are noted but not the focus.

Content is **bundle-authored** (BUNDLE.md): this catalog is the *design* draft, to
land as `bundles/<race>/`, `bundles/<class>/`, and a capability pool the engine
merges generically. Names are moros's own (shared world, DESIGN §2) — *not* an IP
concern (clean-room targets Tolkien/Zelazny/Angband proper nouns only; animal-folk
+ power names are original/shared). See "Clean-room" at the end.

---

## 0. KEY DECISION — adopt moros's 8 stats (DECIDED 2026-06-27, ✅ ENGINE BUILT 2026-08-10)

> ✅ **The engine answers the eight** (plan #16 `M2`): `NUM_STATS = 8`, `sim::stat_index` and
> `gameflow::stat_name` speak Might·Endurance·Dexterity·Perception·Speed·Will·Charisma·Handiness
> in this table's order, and the character page lists and spends all eight. **It cost zero new
> keys** — the front-end already read 1–9 and merely gated at six.
>
> ✅ **And the CONTENT is on the eight too** (plan #16 `M3`, 2026-08-11): all 18 race/class
> bundles were re-authored as a set, so every race and class states a real value on all eight
> — the roster tables are in the plan. The old six-stat vocabulary is **gone from the tree**:
> no `r_str`/`c_int`, no `stat_index` alias arm, no `RF_SUST_STR`. What is still missing is the
> **consumer**: Perception, Speed, Charisma and Handiness are authored but not yet read by a
> derived stat, which `M4` re-keys — the character page says *(later)* on exactly those rows.
>
> ⚠ **`r_int` had nowhere to land**, which is the finding worth carrying: under the eight there
> is exactly ONE casting axis, so arcane and divine both key off **Will** — *which races cast
> well* stopped being a data migration and became a judgement about the roster. `M3` made it,
> and it re-ranked the roster: **the races the six left flat (dwarf, gnome) are precisely the
> ones the new axes repay**, because Angband taxed them on Intelligence and Charisma, two axes
> their playstyle never used. That is what "adopting the eight is not a rename" costs and buys.
>
> *(Historical, measured 2026-08-09: decided 2026-06-27 and never executed — six weeks in which
> three documents specified a game against eight axes while the code offered six, and nothing
> said so.)*
>
> ⚠ **This is crawler's own open decision, not a dependency on anybody.** moros has nothing
> to write for it (`MOROS.md`): the stat set was *seeded* here in June and the mapping
> below is crawler's document about crawler's game. Executing it, or reversing it, is a
> crawler call — and it was made on 2026-08-09: **adopt the eight**, tracked as
> [plan #16](plans/16-eight-statistics/), `status:active`, `M0`–`M3` shipped.
> The axes and the values below are now the **state**; §12a's derived stats and
> `RESOLUTION.md` §5a are still the **target** until `M4` re-keys them.

**Decided: crawler adopts moros's 8 statistics**, replacing Angband's 6 (§12a's
STR/INT/WIS/DEX/CON/CHR). The powers are authored against the 8, and they map onto
our combat model far better than the D&D six (the whole progression is already
moros-shaped, RESOLUTION.md §5a). The 8 and their crawler role:

| moros stat | crawler combat role |
|---|---|
| **Might** | the **damage channel** (RESOLUTION.md §2a) — melee force |
| **Endurance** | **mitigation / HP** ceiling — soak |
| **Dexterity** | **crit** / precision / evasion (the to-hit/crit channel) |
| **Perception** | **the perception action** (§5c) — reading the field, ranged accuracy |
| **Speed** | the **distance clock** (§11) / initiative / reposition |
| **Will** | **focus / Tension-resistance** / caster realms |
| **Charisma** | **leadership / calling** (§5b) / social |
| **Handiness** | crafting / disarm / improvise / device |

**Ripple — the action items this triggers** (it touches §12a's `Hero` and the
existing 6-stat `races`/`classes` tables): (1) `Hero`/`Sim` stat arrays grow 6→8
with the new names; (2) the `races`/`classes` bundle data re-expresses stat mods on
the 8 (they're empty/bundle-side already, §catalog — low cost); (3) the sidebar
(§12a) lists 8; (4) derived stats re-key (Might→damage, Endu→mitigation/HP,
Dex→crit, Perc→perception, Speed→clock, Will→Tension-resist). Recorded in DESIGN
§12a's amendment.

---

## 1. Capabilities (powers) by combat role

37 capabilities from moros, grouped by their **role in crawler combat**. Each is a
**card** in the hand (PARTY.md §5); learning one (or having it innate from a race)
adds the card + a +1 to one linked stat (RESOLUTION.md §5a). Format: **Name**
(stat·stat) — crawler combat effect.

### Attack / striking
- **Claw** (Might·Dex) — strike that **ignores the target's mitigation when it's
  unaware/exposed** → *the capability form of the crit-strip / window-exploit*
  (PARTY.md §5a). The signature offensive opener.
- **Jaws** (Might·Endu) — bite (damage) **+ grab** (target loses mobility) → attack+control.
- **Charge** (Speed·Might) — blunt rush that **knocks slower targets prone** (lose
  next action) → opener/control.

### Mitigation (the *ward* / damage-bias axis, PARTY.md §5a)
- **Fur** (Endu·Dex) — reduces incoming **blunt/fire/cold** → elemental mitigation.
- **Hide** (Endu·Will) — reduces incoming **cutting/impaling** → armor mitigation.
- **Balance** (Dex·Will) — attackers need a **higher roll to hit you** → evasion-mitigation.
- **Control** (Endu·Perc) — **+1 one stat / −1 another**, reallocable → flex buff/defense.

### Debuff / stack (the offensive *stacking* axis, PARTY.md §5a)
- **Magic** (Will·Hand) — ranged **elemental** hit; element sets damage type **+ a
  −1 stack** on a matching target stat (the element table) → caster stack.
- **Shamanic** (Will·Endu) — bind a spirit for a **sustained −1 Will** on a target
  (a Weak-like stack you maintain) → debuff.
- **Sly** (Char·Hand) — a feint that **sets up an ally (+1 vs that target)** → a
  coordination-setup stack (raises Tension when the ally joins).
- **Blood** (Will·Might) — **drain** an enemy (−1) **or restore** an ally's lost stat → drain/heal.

### Window / crit (the to-hit/crit channel, RESOLUTION.md §2a)
- **Claw** (above) is the prime window tool (mitigation-strip on the exposed).
- **Night** (Perc·Dex) — first strike **from darkness** gains an edge → an opener that
  manufactures a window.

### Front-control: taunt / redirect (defensive coordination + attention, PARTY.md §5b/§2b)
- **Scolding** (Might·Will) — **taunt: redirect enemy focus onto you** (they can't
  switch without cost) → *pull a front off a mate* (the deliberate attention-draw;
  the defensive counterpart to focus-fire).

### Buff / aid (coordination → Tension, §5b)
- **Musical** (Char·Dex) — **one ally +1 to their next action** → a focus/buff call.
- **Religion** (Char·Will) — **bless the party** (reduce incoming radiant/draining) → party ward.
- **Camp** (Char·Endu) — set up rest; **allies +1 to the first combat action** → setup/rest (Tension sink).
- **Relaxed** (Endu·Char) — radiate calm; **eases Tension** → a Tension-sink support aura.

### Revive / stabilize (the downed-cover aid, PARTY.md §5d Broken-spirit model)
- **Clan** (Char·Will) — when an ally falls, **move to them as a free action and
  stabilise** → the canonical downed-cover/revive.

### Perception (the *perception action*, PARTY.md §5c — read the field, Tension-neutral)
- **Lookout** (Perc·Endu) — spot threats / **can't be surprised** → the canonical Observe.
- **Smell** (Perc·Endu) — track by scent; detect approach a round early.
- **Hearing** (Perc·Char) — detect approach; group not surprised.
- **Travels** (Speed·Perc) — **scout**: identify hazards / the next front before it opens.
- **Hunter** (Perc·Hand) — track creatures; edge in natural terrain.
- **Labyrinth** (Perc·Will) — navigate / anti-pursuit.

### Mobility / reposition (positioning = execution depth, R3 / front-management)
- **Flight** (Speed·Dex) — **fly: reposition anywhere**, edge vs grounded → air control.
- **Nimble** (Speed·Dex) — **dash to cover** free, once/round.
- **Scurry** (Dex·Perc) — **reposition after committing**, before resolve → reactive dodge.
- **Climber** (Dex·Might) — take **elevation** (attack edge from height).
- **Adaptation** (Will·Char) — slip to cover / re-enter stealth → disengage.
- **Digging** (Endu·Might) — **tunnel through walls/terrain** (bypass a tile) → crawler-native breach.
- **Swimmer** (Dex·Endu) — water mobility / element edge in the wet.

### Summon (a temporary party actor — ties the party system)
- **Druid** (Will·Might) — **call a natural creature to fight alongside** → a
  short-lived ally actor (uses the same actor model, PARTY.md invariant #2).

### Utility (mostly non-combat; map to overland/economy)
- **Ingenuity** (Hand·Will) — improvise a weapon/tool mid-scene.
- **Portage** (Endu·Hand) — carry capacity (ties the §3a carry-weight + the
  goods-stake economy — **no money**, DESIGN §3a amendment).
- **Scrounger** (Hand·Perc) — find supplies/loot.
- **Sleeper** (Will·Endu) — recover anywhere (rest/regen → Tension sink).
- **Politics** (Char·Perc) — faction/parley (overland-side). ⚠ **Now has a mechanism**:
  **standing** with a settlement, and the militia it lets a player raise (plan #17 `S7`).
  It moves the *rate* or the *threshold* — **never a requirement**, or a utility power
  becomes a gate on the campaign's advancement axis.

---

## 2. Races (16) — each a *playstyle* via its innate power set (§5a, §3a amendment)

Each race grants ~7 **innate powers** → its **starting cards** → a distinct
playstyle from turn one. (moros power keys lower-cased as in `data.js`.)

| Race | Innate powers | Crawler playstyle archetype |
|---|---|---|
| **Boar folk** | digging, hide, camp, smell, sleeper, charge, scolding | **Frontline tank-bruiser** — hide-mitigation, charge, taunt, breach, recover |
| **Badgers** | digging, ingenuity, portage, claw, camp, fur, scrounger | **Sapper-tank** — tunnel/breach, fur-mitigation, claw-window, improvise |
| **Owls** | claw, clan, hunter, lookout, charge, flight, scolding | **Commanding aerial striker** — claw-window + charge + taunt + flight + perception; a leader |
| **Wolf folk** | jaws, travels, control, hide, clan, smell, hearing | **Pack hunter** — grab-control, mitigation, revive, heavy perception; coordinated |
| **Bull folk** | portage, swimmer, charge, labyrinth, relaxed, hide, travels | **Enduring wanderer-tank** — charge, hide, calm (Tension-ease), scout, haul |
| **Bats** | flight, scrounger, blood, claw, night, scolding, hearing | **Nocturnal flyer-skirmisher** — air + dark windows, drain, taunt |
| **Cats** | hunter, nimble, relaxed, climber, blood, claw, night | **Agile ambusher** — reposition, claw/night windows, drain |
| **Beavers** | ingenuity, hunter, jaws, swimmer, camp, fur, nimble | **Amphibious builder** — water, grab-control, fur, improvise |
| **Crows** | lookout, ingenuity, adaptation, balance, scolding, flight, night | **Clever scout-controller** — perception, evasion, taunt, flight |
| **Finches** | musical, clan, balance, hearing, politics, flight, scolding | **Social support-caller** — buffs (musical), revive (clan), perception, taunt |
| **Foxes** | adaptation, climber, musical, labyrinth, sly, nimble, travels | **Trickster-skirmisher** — mobility, feint-setup, buff, scout |
| **Humans** | adaptation, ingenuity, balance, portage, politics, sly, lookout | **Versatile generalist** — a little of everything; setup + perception |
| **Otters** | hunter, swimmer, fur, nimble, scurry, sly, lookout | **Nimble aquatic scout** — reposition, perception, water, feint |
| **Raccoons** | scurry, camp, relaxed, sly, scrounger, clan, control | **Resourceful support-trickster** — dodge, feint, revive, flex-buff, Tension-ease |
| **Rat folk** | clan, scurry, climber, sleeper, smell, scrounger, control | **Urban-survivor clan** — revive, mobility, perception, flex, recovery |
| **Rabbits** | camp, labyrinth, scrounger, hearing, sleeper, fur, digging | **Evasive survivor-burrower** — perception, fur, recovery, dig |

*(Choosing a race is foundational in moros — it seeds the innate hand; crawler keeps
it as the playstyle root, the rest learned via backgrounds/specializations.)*

---

## 3. Backgrounds (14) — the "class = soft start" starting packages (§3a #4)

A background is an opening **package**: a stat pair, a starting **kit**, and a few
**seeded specializations** (RESOLUTION.md §5a — `ClassDef` reinterpreted). Format:
**Name** (stat·stat) — kit → seeded specializations.

| Background | Stats | Kit | Seeded specializations |
|---|---|---|---|
| **Noble** | Char·Might | horse, armor, sword | Parry, Swords |
| **Army** | Might·Endu | spear, shield, leather | Shield, Brawl, Spear |
| **Watch** | Perc·Might | glaive, breastplate, crossbow | Blocking, Pole weapon, Crossbow |
| **Hunter** | Might·Dex | bow, falcon, dog | Climbing, Axes, Bows, Scouting, Tracking, Druid |
| **Miner** | Endu·Might | pickaxe, leather | Axes, Brawl |
| **Farmer** | Endu·Hand | flail, donkey, sling, dog | Sling, Druid |
| **Crafter** | Hand·Will | tools, pack | Woodworking, Smithing, Machinist, Axes, Religion |
| **Scholar** | Will·Perc | staff, pack | Healer, Jeweler, Navigation, Magic |
| **Monastery** | Endu·Will | staff | Blocking, Blunt, Religion, Monk |
| **Ascetic** | Will·Char | staff | Druid, Shamanic, Religion, Magic |
| **Trader** | Char·Hand | cart, donkey | Jeweler, Navigation |
| **Fisher** | Endu·Perc | net | Woodworking, Brawl, Religion |
| **Back alley** | Hand·Dex | dagger, darts | Climbing, Sneak, Darts, Scouting |
| **Circus troupe** | Speed·Dex | whip | Climbing, Juggle |

*(moros backgrounds also carry NPC contacts per settlement — overland/social, parked
until the overland/town layer; the combat-relevant part is stats+kit+specs.)*

---

## 4. Specializations — trainable skills, by governing stat

Each is tied to **one** governing stat and requires a **supporting background**
(RESOLUTION.md §5a). Weapon specs map to crawler weapon skills; the rest as noted.

- **Dexterity:** Shield, Parry, Blocking *(→ mitigation/block)* · Sneak *(stealth)* ·
  Juggle · Climbing
- **Handiness:** Woodworking, Cloth, Leather, Smithing, Machinist, Jeweler, Cooking
  *(crafting/economy)* · Healer *(stabilize/heal)*
- **Might:** Axes, Blunt, Brawl, Pole weapon, Spear, Swords *(melee weapon skills →
  the damage channel)*
- **Perception:** Bows, Crossbow, Sling, Darts *(ranged)* · Scouting, Tracking,
  Navigation *(→ the perception action, §5c)*
- **Willpower:** Religion, Shamanic, Magic, Druid, Monk *(caster realms / the §13
  spell hook)*

---

## 5. The 8 element cards — the shared baseline deck

Everyone holds these regardless of race/build (PARTY.md §5 "moros's shared element
cards"); each carries a **damage type / element** that drives the stack/resist
interplay (RESOLUTION.md §2b damage channel; the StS stacks key off element):

| Card | Stats | Element |
|---|---|---|
| Flame | Might·Dex | fire |
| Water | Dex·Speed | water/cold |
| Wind | Char·Speed | air/electric |
| Plants | Hand·Char | wood/grab |
| Iron | Might·Will | iron/impaling |
| Earth | Endu·Hand | stone/blunt |
| Light | Perc·Will | light/radiant |
| Dark | Perc·Endu | dark/draining |

---

## 6. Angband's indirect layer → capabilities (skills & spells)

How Angband's **non-direct-damage** content — the utility *skills* and the utility
*spell* catalogue — lands in the moros-rules framework. Two findings up front:
**spell *effects* survive as capabilities; the casting *economy* is replaced**, and
the mapping is **compression, not loss**.

### 6.1 Indirect skills

| Angband skill | crawler home | note |
|---|---|---|
| Device (wands/rods) | **Handiness** (Machinist/Jeweler spec) | a stat, not a separate number |
| Disarm (traps/locks) | **Handiness** + Ingenuity / Back-alley | clean |
| Stealth | **Adaptation · Night · Scurry · Nimble** + Sneak | *richer* — active verbs, not a passive number |
| Saving throw | **Will** stat contest + Hide/Balance | "save vs effect" becomes a Will resolution |
| Searching / perception | **the perception action** (§5c) + Lookout/Smell/Hearing | *richer* — a first-class round action |

The indirect skills map cleanly, several get **richer**: Angband's passive
stealth/perception *numbers* become active *verbs* — the point of the capability model.

### 6.2 Utility spells

| Angband spell class | crawler home | verdict |
|---|---|---|
| Detection (monsters/traps/doors/caches, magic-map, clairvoyance) | **perception action** + Lookout/Smell/Travels | clean — many detects **compress** into one verb at mastery |
| Buffs (bless, heroism, shield, resistance, protection) | **Religion** (ward) · **Musical/Camp** (ally buff) · **Control** · temporary **mitigation** (§5a ward axis) | clean |
| Haste / Slow | **Speed** → the distance clock (§11) | clean — haste *is* the clock hook |
| Debuffs/control (sleep, confuse, scare, hold, blind, slow) | **Shamanic** (−Will) · **Magic** (element + stat −1) · **Scolding** (taunt) · **Charge** (knockdown) · **Jaws** (grab) → the **stacks** (§5a) + statuses | clean — "−1 to a stat / status" *is* our stack model |
| Summoning | **Druid** (summon a fighting ally) | clean — reuses the party-actor model (PARTY.md inv. #2) |
| Realms (arcane/divine/nature) | the **Will specializations** (Magic/Religion/Shamanic/Druid/Monk) | clean — realms → caster-specs |
| Elemental attack (bolt/ball/breath) | **Magic** power: element → damage type **+ stat-debuff stack** | clean — the whole element list compressed into one card |

### 6.3 Casting economy — replaced (advancement goes the moros way, §3a amendment)

Angband's **SP pool, fail-rate, spell-levels, learn-from-books-by-realm** are an
*advancement/economy* system, so under moros rules they're **replaced**: a spell is
a **card** whose cost is the **action** (+ **Tension** if it's a coordination / big
play, §5b), **gated by stat + mastery instead of a fail-roll** — **no SP, no
fail-chance**. The spell *content* is preserved as capabilities (CLAUDE.md "build
the system, don't nerf the content"); the *economy* moros-izes. And the mapping is
**compression, not loss** — Angband's many incremental detect/buff variants collapse
into fewer, deeper capabilities-with-mastery (lossless on *function*, "lossy" only on
*list length* — exactly what breadth-over-height wants).

### 6.4 The gaps — Angband content with **no** moros analog (→ item/utility layer)

These don't fit the capability tree and correctly belong in the **item/utility
layer (`itemfx`) + the depth/overland system**, not the power set — so they're
*additive*, not conflicts:

- **Teleportation** — **NOT** Angband's cheap blink; in a low-magic world it's a
  costly coordinated **ritual**. Designed in **§6.5**.
- **Structural / navigation magic** (recall, deep descent, create stairs, detect
  whole level; stone-to-mud is already **Digging**). Roguelike *structure* → `itemfx`
  + the depth/overland layer, not capabilities.
- **HP-healing magnitude.** moros heals *stat points* (it has no HP); crawler **keeps
  HP**, so Blood/Clan/Religion exist as capabilities but heal **HP** here. Minor
  adaptation, stated so it isn't missed.
- **Identify / enchant / curse / recharge.** Tie to crawler's **item system**
  (the unknown-flavour mechanic in `sim`, ego-items) + Handiness specs
  (Smithing/Jeweler) — not standalone spells.

### 6.5 Low-magic world — magic is *effective, sparse, and slightly unpredictable* (DECIDED)

moros is a **low-magic world**, and that sets the shape of **every** magical
ability — the Will specializations (Magic/Shamanic/Druid/Religion/Monk) **and** all
item magic, not just teleport: **effective, sparse, and slightly unpredictable.**

- **Effective** — when magic fires it has *real* impact (a genuine elemental burst,
  a true heal, a ritual escape), **never weak filler**. No trivial chip-spells.
- **Sparse** — it is *rare and infrequent*: **gated by cost** (Tension, rare
  reagents, preparation / channel time, limited charges), **never a refilling SP
  pool spent every turn** (§6.3). Magic is a **special occasion / a decision**, not
  a rotation.
- **Slightly unpredictable** — magic is **never a precise instrument**: its outcome
  carries **wider variance** than martial play (which is *dependable* — the ≥1
  chip floor, §2a), plus a small ever-present chance of a **wild result**
  (scatter / surge / wrong-magnitude). Leaning on it risks moros's **`overwhelmed`**
  state — the power *acting on its own* ("elements answer your mood, not your
  intent"; spirits crowd the shaman) — which is *also* what enforces "sparse." The
  contrast is the point: **you rely on your blade; you *gamble* on magic.**
  *(R3-safe: the variance rides the magic *upside* layer — the punctuation — and
  never removes the martial floor; magic is never a gate, just a wild spike.)*

**Why magic is this way — the spirit world (the cosmology under all of it).** All
magic is **interaction with the spirit world** — there is no deterministic "arcane
physics." You **petition / bind / bargain with spirits; you never *command* them**,
so **human control is always partial.** This is the *source* of the unpredictability
above, and it carries a **scaling law:**

> **Stronger spirit ⇒ bigger effect ⇒ *less* control.**

A minor spirit (a small effect) is fairly biddable — low variance. A great spirit (a
mighty effect) is barely held — high variance, high `overwhelmed` risk, its own
agenda. So **the most powerful magic is inherently the wildest**, and the player
chooses on a **power-vs-control axis**: a modest *reliable* effect (weak spirit) or a
mighty *gamble* (strong spirit). **Will is the control-contest stat** (Will vs the
spirit's strength) — higher Will holds a *given* spirit better, but **there is always
a spirit stronger than any Will**, so control is *never* total. moros's `overwhelmed`
is exactly **losing that contest** — the spirit overtaking the caster. This also
**unifies the realms** (§6.2): Magic = elemental spirits, Shamanic = spirits openly,
Druid = nature spirits, Religion = higher/divine spirits — all one spirit cosmology,
differing only in *which* spirits and *how* they're approached. And it re-explains
**teleport** (§6.5 below): the *strongest* spirit, *least* controlled — hence the
ritual, the channel, and the **group effort to bind and direct it**, more hands
holding a power no one could hold alone.

**The spirit world is the substrate of the *natural* world too — not just magic.**
Elemental spirits **ARE the natural forces**: a **volcano** is a great **fire**
spirit, a **storm** a great **air** spirit, the **tides** a **water** spirit (and so
on across the element set, CATALOG §5 — quakes/mountains = stone, growth = wood, …).
The world is **animate**: natural phenomena — and natural *disasters* — are **spirit
acts**, chaos-touched **or not**. This **grounds the scaling law cosmically**: the
*strongest* spirits literally **are cataclysms** — you can't *command* a volcano —
which is *why* great effects are least controlled (§6.6). It also broadens the
**"restless spirits" local condition** (§5j): a region's natural hazards (an eruption,
a raging storm, a flood) are *its elemental spirits, restless* — not only chaos
spirits. And it is exactly moros's **bound elementals** (the caged **air** elemental
that lifts cities / *is* the storms; the volcano tower's **fire** elemental): the
shackle towers cage **forces of nature** — freeing one **unleashes a natural force**.
So a mage petitioning a fire spirit is relating to *the same kind of being that is a
volcano* — magic and weather and geology are **one animate spirit-world**.

**And the animate world is *reactive* — it responds to human & economic activity;
not always hostile, and its presence is *felt*** (inspected from moros LORE.md /
CAMPAIGN.md / SURVIVAL.md — the *economic-ecological-spiritual loop*). Principles:
- **Activity → reaction.** **Extraction / exploitation** — a mine that strips a
  hillside, deforestation (the felled ironwood), over-fishing, **forced spirit-binding
  or commodifying bound spirits**, reckless magic — **disturbs** the spirit-world
  (resistance, wilder magic, **restless/warped spirits**, the fungus, the spreading
  desert). **Sustainable / respectful practice** — seeded stocks, tending, **offerings,
  shrines**, working *with* the land — is **accepted / cooperated with**.
- **Not always negative — good practice *earns* the spirit-world.** Shrines, priests,
  shamans, druids **tending** a place are the **protection infrastructure** (a held
  place keeps chaos spirits off; *abandon* the tending and the door opens). Aligning
  with a great spirit's **drive** (help *its* people — moros's Felicia + refugees)
  **extends its protection** to you.
- **Presence is *felt* before consequence lands** — never a labelled "spirit attack",
  but **omens / atmosphere**: fungus & spores, an air that shimmers, plants growing
  wrong, structures unmade overnight (the shifting lands), warped local spirits, a
  weather turn, "a sense of being *watched*." Humans read the response as a **material
  crisis** (refugees, scarcity), not as a spirit.
- **The economic coupling — the economy is *not neutral*.** Economic activity is
  load-bearing on the spirit-world: how you (and NPCs / **factions**) extract, trade,
  exploit, or commodify **shifts the §5j local conditions** (restless spirits ·
  poverty · even war). So crawler's **goods-economy (§5g, no money) is coupled to the
  spirit-world**, and the §5j conditions are **dynamic — they respond to activity**
  (the feedback engine; the player and NPCs both *shift* conditions, not only suffer
  them).
- **Balance + *costly* restoration.** Extraction → imbalance → consequence →
  **restoration is possible but never cheap** (active work + real cost + drive-
  alignment) — i.e. **a §5j thread / §7 relationally-solved mission**, not a switch.
- **Moral axis — persons, not resources.** Treat spirits as **persons** (negotiate,
  respect, tend) → cooperation; as **resources** (bind, commodify, strip) →
  resentment & hostility. This is *why* relational resolution (§7) beats force — and
  it carries moros's "compassion under pressure" register.
- **Tone — keep it partly inscrutable.** The world's will is *real but neither
  consistent nor explained* ("the world… seems, in places, to be **watching**").
  **Don't over-mechanise it into a tame dial** — not a character you negotiate with,
  but never indifferent.

**Why the instability is a *feature* — it is the source of player agency.** The exact
relationships between these forces — **activity ↔ spirits ↔ conditions ↔ economy ↔
factions** — are **never stable and never fully understood**, *by design*. A *solved,
stable, legible* system leaves the player only **optimisation** (execute the known
path); an **unstable, partly-opaque, responsive** one gives **real agency** — your
choices genuinely *shift* things, outcomes are *open*, and **experimentation and
inference are rewarded.** Discipline: **keep the couplings *felt and inferred*, never a
solved dashboard** (no "spirit-meter at 73% → do X"); the **opacity is load-bearing** —
surfacing or stabilising the relationships would *kill the agency*. (Same spirit as
§5a's *qualitative* color-read (not a meter), §6.6's never-fully-controllable magic,
and the Dark-Souls "skill, not solved-stats" of RESOLUTION.md §2a — **agency from play,
not from a decoded machine.**)

> **It is *one* mechanic across several domains.** Spirit/ecology, economy, and
> faction/political all run the *same* reactive coupling — so **a war (faction domain)
> and an environmental calamity (spirit domain) are two expressions of the same
> mechanic**, coupled across domains and across **local/country/world** scales. The
> world is **one reactive web of forces.** Full treatment: **PARTY.md §5j.**
>
> **And no actor is static — relocation is itself a reaction.** Pushed hard/long
> enough, any node **moves slowly**: spirits **migrate** (chaos spirits → the
> spreading desert; an elemental leaving for the mountains; the *moved* towers),
> economies and settlements **shift**, **cities relocate** (Laurent's flying city).
> The map is **dynamic** over a campaign — a threat *and* a player lever (§5j).

Consequence for play: the **everyday layer is martial / capability** (chip,
windows, mitigation, coordination, perception); **magic is the *punctuation*** — the
rare, high-impact spike. Even a *caster* build plays mostly non-magically,
punctuated by a few effective magical acts — the opposite of Angband's
spell-rotation mage. (This is the *world-feel* reason behind §6.3's no-SP economy:
not merely "no mana bookkeeping" but **deliberately scarce, impactful** magic.)

**Teleportation — the highest-effect exemplar (a coordinated ritual).** Not a panic
button; a setpiece:

- **Preparation, not instant.** It **channels** over several ticks (or needs a
  prepared anchor / a rare reagent) — the party must *hold and defend* the
  channelers. The channel is itself an **exposure window** (§5a) enemies can
  disrupt, so it's a defensive setpiece (ward/intercept/cover the casters).
- **Heavy cost.** A large **Tension** spike (a major coordination act — a combined
  limit-breaker, §2b) **+ a rare reagent** (economic sink; precious in a low-magic
  world — losing a hoarded one on death stings, §3a).
- **Group effort scales it.** Multiple actors **channel together** (the §2b
  combined act): the more who join, the faster / cheaper / farther. **Solo it is
  barely possible** (slow and dear) — reinforcing "a party of one is structurally
  weaker" (§2b).
- **Effects worth it.** A **group escape** (blink the ritual out of a deadly spot —
  exactly the goods-rich grave spots §3a wants groups to brave) or a **recall** to a
  checkpoint/town (a deliberate, costly dive-bail vs the free death-respawn).
- **Item form:** rare, precious **reagents / scrolls** that *enable or shorten* the
  ritual — not a spammable escape; an economic sink, authored `itemfx`-side.

This turns Angband's panic-button into a **tension-moment setpiece** (moros's
cooperative register, COORDINATION_ROADMAP) and folds into the push-your-luck:
reach for the escape and you spike Tension while exposed.

### 6.6 The unpredictability mechanic — variance scales with spirit strength

The concrete realization of §6.5's "stronger spirit ⇒ less control." It **reuses the
resolver** (RESOLUTION.md §2a/§3): magic control is **the crit-engine pattern applied
to Will vs spirit strength** — the bell's *margin* selects an outcome **tier** instead
of hit/crit. No new resolution system.

**The control roll.** Invoking a spirit of strength `S` with caster Will `W`:
`c = bell() + (W − S)` (the §3 bell, clamped per §2a). Higher `c` = better control.
`c` lands the act in one of four **tiers** — and the crucial framing is **potency is
roughly preserved across tiers (the magic stays *effective*); what degrades is
*control / direction* (the *unpredictable*):**

| Tier | control `c` | what happens |
|---|---|---|
| **Clean** | high | full potency, on target — as intended |
| **Surge** | mid-high | full+ potency, **magnitude swings** (over/undershoot), roughly on target |
| **Wild** | low | full potency but **mis-directed / scatters** — wrong or extra targets (**incl. allies**), area spill |
| **Overwhelmed** | lowest | the **spirit's agenda** (moros `overwhelmed`) — backlash on caster/allies + a lingering condition; potency turned partly *against* you |

**Spirit strength `S` enters TWICE — this is what makes the biggest magic the
wildest:**
1. **Mean-shift:** bigger `S` lowers the margin `(W − S)` → the tier distribution
   skews toward Wild/Overwhelmed.
2. **Spread-widen:** the outcome **band itself widens with `S`** — a great spirit's
   magnitude swing and Wild-scatter radius are far larger than a minor spirit's, even
   at the same `c`.

**Concrete plotted instance** (caster Will = 6; numbers illustrative, to tune):

| Spirit (effect) | `S` | margin | Clean / Surge / Wild / Overwhelmed | magnitude band |
|---|---|---|---|---|
| Ember — small flame | 3 | +3 | ~70 / 22 / 6 / 2 | narrow (4–6) |
| Blaze — big burst | 6 | 0 | ~40 / 32 / 20 / 8 | medium (3–12) |
| Conflagration — ritual | 10 | −4 | ~12 / 28 / 38 / 22 | wide (0–24, scatters) |

Ember is a *reliable tool*; Conflagration is a *gamble* — huge but as likely to
scatter onto your own line or overwhelm you. That's the **power-vs-control choice**
(§6.5) made numeric.

**Invariants:**
1. **Margin governs the distribution; `S` enters twice** (mean-shift + spread-widen).
   The most powerful magic is the wildest *by construction*, not by a flavour rule.
2. **No structural certainty, either tail (R3 / §2a clamp).** Even maximal control
   keeps a sliver of Surge (**always slightly unpredictable**); even a hopeless
   margin keeps a sliver of a Clean fluke (**no gate**). Clamp both ends.
3. **Potency preserved, control degraded.** Tiers move *aim/direction*, not *power* —
   so magic stays "effective" while being "unpredictable," and Wild magic is
   **dangerous to your own party** (scatter onto allies / opens fronts, §2b) — a real
   cost that feeds Tension and the front game.
4. **Overwhelmed scales with `S`** (bigger spirit, bigger backlash) and is R3-safe —
   an *upside-layer* cost that never removes the martial ≥1 floor.
5. **Group effort raises *effective* Will** (pooled control across channelers) — the
   *only* way to make a great spirit reliable. This is the mechanical reason big
   magic is a **coordinated ritual** (§6.5 teleport): one caster's Will can't hold a
   strong spirit; more hands shift its distribution back toward Clean.

**Verify (cheapest medium — Python, before loft):** plot tier-distribution and
magnitude band vs `S` across a few `W`; assert (a) reliability falls and spread rises
**monotonically** with `S`; (b) both tails are clamped (no 0%/100%); (c) **pooling
Will** (group) recovers control on high-`S`. Pin the thresholds + spread-slope on the
plot; don't guess them in loft.

### 6.7 Magic items are *passive aids* — and casters seek & craft them

**No magic item is active-effect.** There is **no point-and-fire wand**: the magic
always runs through the **caster's own spirit-contest** (§6.6); items only
**passively aid** that contest — they *strengthen your hand*, they never cast for
you. This is the deliberate break from Angband's active wands/staves/rods (re-cast
below).

**The aids a caster is *always on the lookout* for** (found *or* crafted) —
**potions, runes, tattoos, patterns, jewelry, amulets, rings.** Each is a *passive*
enhancer of the spirit-contest, always-on while worn / inscribed / imbibed. This is a
**constant loot + economy motivation**: a caster hunts these everywhere (and the
party's finds matter to them). Mechanically each modifies the §6.6 control roll
(by quality + materials), one or more of:
- **+control** — raises *effective* Will (hold a given spirit better);
- **variance-narrowing** — tightens the outcome band (more Clean/Surge, less
  Wild/Overwhelmed) — a steadier vessel;
- **+ceiling** — bind a **stronger `S`** than raw Will alone could reach;
- **attunement/ward** — bias toward a kind of spirit/element, or blunt the
  `overwhelmed` backlash.
- *(Reagents — the consumable inputs that **enable / shorten the rituals**, §6.5 —
  are spent, not worn; still a passive input, not an active cast.)*

**Casters gravitate to crafting** because that's how you *make* these aids — **Will
contests the spirit, Handiness crafts the vessel.** Already in the source data:
moros's **Magic** = `Will·Hand`, **Ingenuity** = `Hand·Will` — the caster axis is
**Will + Handiness**, not Will alone. Craft → aid mapping: **Jeweler** → jewelry /
amulets / rings (set gems *store* spirits); an inscriber (**Leather/Cloth/Smithing**)
→ runes / tattoos / woven patterns; a brewer (**Cooking/Healer**) → potions. So the
**caster build spans Will + Handiness + the materials economy**: gather → craft (or
loot) aids → control stronger spirits.

**Non-treadmill** (§3a #3 / economy notes): an aid *enables control / a capability*,
**not** a numerical +N gear ladder.

**Re-cast of Angband's active magic items:** wands/staves/rods (active casters) and
read-to-cast scrolls do **not** carry over as active devices — the *effect* is the
caster's capability, and the *item* becomes a **passive aid** (rune/amulet that
strengthens control) or a **reagent** (a ritual input, §6.5). The "Scroll of
Teleport" is thus a reagent/inscription that aids the teleport *ritual*, not a
standalone cast.

*(Open: material→spirit flavour — iron *binds*, gems *store*, wood *channels*,
leather *wards* — tying craft/aid type to element/spirit kind; aid effect
magnitudes; whether an aid is permanent (tattoo/rune), worn (jewelry), or consumed
(potion/reagent).)*

### 6.8 Consequence — magic is *deniable* (the barometer of low magic)

Because the aids are **passive** and work **only through a caster's spirit-contest**
(§6.6/§6.7), in a non-caster's hands they **do nothing** — a rune-amulet is just
jewelry, a tattoo just ink. So disbelief is **tenable**: a person *can* not believe
in magic without being obviously wrong, never having *seen* an object do anything.

**Calibration — skeptics are *uncommon*, not a faction.** The point is **not** that
many people deny magic; it's that **the mere possibility of denial is the *barometer*
of how low-magic this world is.** In a high-magic world (fireballs everywhere)
disbelief would be absurd; here magic is subtle enough that an (uncommon) skeptic is
*plausible*. That tenability is the gauge — a measure of the setting, not a movement.
Meanwhile the same objects remain **vital to the spirit-workers** (mage / druid /
shaman / cleric) who draw aid through them.

**Design hooks** (light — this is world-*feel*, not a system):
- **Aids read as mundane to non-casters** — an amulet has *jewelry* value to a
  merchant, *control* value to a mage; appraising a magic aid is **caster knowledge**
  (ties the `sim` unknown-flavour / identify system + the economy: a non-believer
  fences a rune as a trinket, a caster prizes it).
- A wild / `overwhelmed` outcome a skeptic *does* witness reads as chance or nature,
  not proof — magic stays deniable even when it misfires.

---

## 7. Quest archetypes & the generic mission format (from moros)

Derived from inspecting the **whole moros campaign corpus** (~150 sub-quests across
CAMPAIGN.md / COORDINATION_ROADMAP.md / BRUMAL_RESOLUTIONS.md / SITUATIONS.md /
SCENARIOS.md). The point: a clean **archetype taxonomy** + a **generic mission format**
that crawler's `QuestDef` (BUNDLE.md) extends toward — the schema the §5h/§5i authoring
and the §5j *generator* both emit.

### 7.1 The headline finding — moros is *relational-first*

By a wide margin the corpus resolves through **relationship**, not force: *befriend /
negotiate / consent / broker* dominate; **combat is usually optional/avoidable**. The
signature pattern is the **shackle towers** — broken by a *relational lever* (befriend
the fire elemental, free the light elemental, bring the owner-spirit what it wants,
the hill-tower's **consent**), **not** "destroy the cage." So the format makes
**relational resolution a *first-class lever*** (powered by the trust/contact web §5e/§5g
and the spirit-contest §6.6 — befriending an elemental *is* a spirit relationship),
never combat-by-default.

### 7.2 Archetype taxonomy — 16 archetypes in 6 lever-families

The **lever-family** = which crawler system resolves it (and feeds §5j's "branching =
systemic levers"):

- **A. Force** (combat) — **SLAY/CLEAR** (a nest, a threat) · **DEFEND/HOLD** (a
  position, a person, non-combatants).
- **B. Traverse** (movement) — **REACH/EXPLORE** (a place, a tower interior) ·
  **TRAVEL** (cross terrain) · **ESCORT/DELIVER** (move a person/thing/message safely)
  · **RESCUE/EXTRACT** (get a captive/endangered person out).
- **C. Discover** (perception, §5c) — **INVESTIGATE** (read a situation, find evidence,
  spot the tell, source an outbreak) · **RETRIEVE** (find + take an item/resource).
- **D. Relational** (social / trust / spirit — *the moros signature*) —
  **BEFRIEND/EARN-TRUST** (win a being over — the shackle-breaker) ·
  **NEGOTIATE/PERSUADE** (talk down, convince, broker a deal) · **CONSENT** (earn a
  being's *honest agreement* — Gerhald's three questions; a gate, not a transaction) ·
  **BROKER/MEDIATE** (carry between two parties — cerberus↔shrine, sphinx↔chimera) ·
  **WITNESS/MORAL-CHOICE** (witness + decide — release the cerberus, the parting).
- **E. Restore** (support / magic) — **CURE** (diagnose + heal) · **REPAIR/RESTORE**
  (fix a mechanism/working — the furnace, the mosaic) · **RITUAL** (a spirit/religious
  working — condensation, the spirit-corridor, un-warping; §6.5 — costly, prepared).
- **F. Provision** (economy / management) — **TRADE/MARKET** (acquire via contacts —
  the Linar triangular deal; §5g/no-money) · **STEWARD/LOGISTICS** (organise a crisis —
  refugee triage, quarantine, watch rotation).

*(Most moros scenes blend 2–3 — e.g. the buried-tower furnace = REPAIR + BEFRIEND +
RITUAL. So a quest carries **one primary archetype + a lever-set**, not a single tag.)*

### 7.3 The generic mission format (a superset of `QuestDef`)

Every quest — generic, designed, or generator-emitted — fills this schema. The first
four are the **§5j invariant** (no thread without FACE + PLACE + LEVER + LINK):

| Field | What | Source |
|---|---|---|
| **face** | the person/being anchor — *name + condition + reason-to-care* | §5h rule / moros face-first |
| **archetype** | one of the 16 (§7.2) — the primary objective verb | this taxonomy |
| **target** | what the archetype acts on (monster/nest · item · place · person · being) | `QuestDef` target |
| **place** | the site (procedural or authored) | `QuestDef` place |
| **levers[]** | which systems *can* resolve it (force/traverse/discover/relational/restore/provision); **≥1; multiple = branching** | §5j branching |
| **links[]** | relationship / thread / crisis connections (the thread-web) | `QuestDef` requirements (lock-and-key), generalised |
| **stake / delta** | what resolving *changes* — world-state, the relationship impact (contact level, companion trust, recruit), what it **opens/closes** | §5i resolve-and-open; §5e/§5g |
| **resolution** | success / failure / **partial** conditions (partial outcomes allowed; paths combine) | §5i branching |
| **scope** | sub-quest · mission · thread · campaign-spine | §5h–§5j granularity |
| **coordination** | solo-able **vs party-required** → the **tension-moment** flag | §5i spine |

So the **generic format = crawler's `QuestDef`** (objective/target/requirements/rewards/
routine-ids) **+ {`face`, the 16-archetype set, `levers[]`, `links[]` (= generalised
requirements), `stake`/delta, partial-`resolution`, `coordination` flag}**. Generic and
authored missions hand-fill it (§5h/§5i); the §5j generator emits it from
*(person-want/intent × world-condition × place × lever × link)*. Authored bundle-side
(BUNDLE.md), engine reads it generically.

*(Open: the routine/check per archetype — `quest_check` already does RESCUE/RETRIEVE/SLAY;
the relational/restore/provision archetypes need their own completion-checks, tied to the
trust/contact (§5e/§5g), spirit (§6.6), cure/repair, and barter systems.)*

---

## 8. Clean-room & open items

- **Clean-room / shared world (DESIGN §2, §4).** moros race + power names are the
  *shared world's own* IP, reused intentionally — **not** the clean-room concern,
  which targets Tolkien/Zelazny/Angband proper nouns only. No renaming needed.
- **Open — the stat-set decision (§0)** is the gating call; everything else assumes
  it.
- **Open — per-capability *numbers*.** This draft pins each capability's *role and
  effect shape*, not its magnitudes (ΔM strip, stack potency, mitigation amounts,
  buff sizes) — those are the RESOLUTION.md §9 / PARTY.md §7 tuning curves, to pin
  on a prototype, **not guess here**.
- **Open — mastery levels.** moros powers scale by mastery (e.g. Flight: glide →
  full flight). Maps to the breadth model's "+1 to an existing capability" (height,
  soft-capped) vs learning a new one — confirm how mastery reads in crawler.
- **Open — non-combat uses.** Each power's Travel/Camp/Forage/Negotiation uses map to
  crawler's overland/rest/loot/parley; carry them over when those layers land.
- **Bundle mapping.** Races → `bundles/<race>/`; backgrounds → `bundles/<class>/`
  (the soft-start package); the capability pool + element cards → a shared content
  bundle the engine merges generically (BUNDLE.md "library-like" check).

---

## Open work

*(The lightest workflow that fits — `plans/README.md`: the row and the design share a
file. Escalate to a plan only where noted.)*

### `OW1` — the 8 stats ✅ **RESOLVED 2026-08-09 → [plan #16](plans/16-eight-statistics/)**

> **Decided: adopt the eight** (user, *"we will adopt moros"*), **not scheduled** (*"but
> not today"*). The fork below is closed; the work and its measured cost now live in
> plan #16, `status:future`. ⚠ Two findings from that measurement change the shape of it:
> **it is not a save break** (no stat vector persists), and **it is not a rename**
> (Perception and Speed are new axes, so the 18 bundles need re-authoring, not mapping).
> Left here for the reasoning; the schedule and step status are the plan's.

§0 adopted moros' eight on 2026-06-27; measured 2026-08-09, the engine answers Angband's
**six** (`gameflow::stat_name`, `sim::stat_index`) and the eight appear in no code path.
Six weeks, and nothing said so.

**The fork is crawler's alone** (`MOROS.md`: moros has nothing to write for this — the
stat set was seeded here in June and this document is crawler's own):

| | cost, measured 2026-08-09 |
|---|---|
| **execute the eight** | 7 engine files · 16 `stat_index`/`stat_name` sites · ⚠ **18 bundles carrying stat blocks**, each needing its values **re-authored** against 8 axes — content work, not a rename. Plus re-keying the derived stats (`RESOLUTION.md` §2a) and the character page |
| **reverse to six** | edit §0, §12a and the power table here so they stop describing a system the engine does not have. Cheap, and it makes the docs true today |

⚠ **The cost is asymmetric and the docs are wrong either way until it is settled** — §12a,
the 37 powers below and `RESOLUTION.md` §5a are all authored against eight axes while the
engine offers six, so a reader implementing from them builds against a system that is not
there.

⚠ **If the answer is "execute", this earns a plan** (multi-phase, and 18 bundles of
content re-authoring). If it is "reverse", it is a doc edit and stays a row here.
Note `plans/README.md` caps active plans at **2–3** and there are currently **6**.

### `OW2` — the economy is adopted, and it grows a crafting half ⚠ **decided, undesigned**

**Decided 2026-08-09** (user: *"…and the economy, we will expand it though with far more
crafting"*). Two halves, and only the first is written down anywhere.

**Adopted, already designed — §6.3.** Angband's SP pool / fail-rate / spell-levels /
learn-by-realm are an *advancement economy*, and under moros rules they are **replaced**: a
spell is a **card** whose cost is the **action** (+ **Tension** for a coordination play),
**gated by stat and mastery rather than a fail-roll** — no SP, no fail-chance. The spell
*content* survives intact (CLAUDE.md: *build the system, don't nerf the content*); only the
economy moros-izes.

**The expansion — undesigned.** *"Far more crafting"* than moros has. crawler holds **no
player crafting system today**: `Handiness` is listed as *"crafting / disarm / improvise /
device"* in §1 and nothing implements it.

⚠ **IT WOULD NOT START FROM ZERO, and the substrate is newer than this row.** `BUNDLE.md`'s
**`production` section** (added 2026-08-09) already models *making things*: seven producer
kinds — forge weapon/armour, alchemy, scriptorium scroll/book, town craft, import — each an
engine-owned **mechanism** rotating a **bundle-owned repertoire** (`I-PROD`). That is the
town half of a crafting economy, gated and shipped. Player crafting is plausibly the same
seam pointed at the player: a recipe is content, the making is mechanism.

⚠ **NOT A PLAN YET, deliberately.** `plans/README.md`: a plan *"earns it only when the work
is genuinely multi-phase **and** benefits from its own document space"*. The economy half is
designed and small; the crafting half is a **direction, not a design** — a directory today
would hold a title and an open question. **Promote it the moment the crafting design is
written**, and it will earn `status:future` at least.

**What has to be answered before it is a plan:**

1. What is crafted, and from what? crawler has items and **no materials**.
2. Where does it happen — at a `production` workshop (reusing the seam above), anywhere, or
   at a station the player carries?
3. What does it cost? The adopted economy prices spells in **actions and Tension**, not
   resources. Crafting that costs gold-and-time is a *second* economy beside it, and §3a's
   bounded-simulation pillar asks whether that adds something the player must learn.
4. Does `Handiness` gate it, and is that enough for an axis to earn its place among eight?
   ⚠ **The coupling to [plan #16](plans/16-eight-statistics/) `M3` is now resolved, and in the
   direction that frees this question**: the roster shipped 2026-08-11 and **no value in it is
   a bet on crafting** — the dwarf's +3 and the gnome's +4 are backed by the `r_device` /
   `r_disarm` already authored, and by repairs-and-improvising (`CRAFTING.md`). So crafting can
   be designed, deferred or declined without re-opening 18 bundles.
