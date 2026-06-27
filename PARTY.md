# PARTY.md — co-op party, coordination Tension & cards-as-UI

The co-op layer: a **goal-directed party of allies** (AI-driven now, drop-in
human-playable later) whose **coordination carries a moros-style Tension cost**,
surfaced through a **card UI** — sitting *on top of* an unchanged Angband combat
kernel. This doc is the blueprint (DESIGN-PROTOCOL: concrete end-result →
invariants → cheapest-medium verify → phasing). It extends DESIGN.md §10
(actors), §10a (flow-field AI + `MF_FRIENDS`), §11a (locality clock under MP),
§11b (the MP-shaped per-player seam), and the `gameflow.loft` intent wire.

## 0. Read-first — design index, through-lines, decisions, open items

> **What this is.** A design exploration (2026-06-27) of adopting moros's *character
> rules + world model* onto crawler's Angband engine. **Design only — no code yet.**
> The corpus: **PARTY.md** (co-op party · Tension · cards · Slay-the-Spire combat
> undercurrent · Broken-spirit death · companions · missions · campaign · emergent
> threads · the reactive-web world) · **RESOLUTION.md** (resolution + progression
> core) · **CATALOG.md** (capability/race/quest catalog + the spirit cosmology) ·
> **DESIGN.md §3a/§12a amendments** + a **BUNDLE.md** cross-ref (charter + quest seam).

**The through-lines (the unifying ideas — read these and the rest follows):**
1. **One reactive web of forces — *spirits + economy + factions*.** *One* mechanic
   (activity → reaction → consequence → propagation), several **domains**
   (spirit/ecology · economy · faction/political), nested **scales** (local · country
   · world). **A war and an environmental calamity are the same mechanic in different
   domains.** One data structure; only the **actor (node) type** differs by domain
   (§5j; CATALOG §6.5).
2. **Opacity = agency.** The forces' relationships are **never stable or fully
   understood, *by design*** — a solved system is mere optimisation; an unstable,
   read-not-metered one gives real agency. *Agency from play, not a decoded machine.*
   (Echoed by §5a qualitative tints, §6.6 uncontrollable magic, RESOLUTION §2a.)
3. **Persons behind everything.** Missions, economy, companions, contacts = **one
   graph of people**; every mission is **face-first** (person-anchored); **genealogy
   (parents/children) is the backbone** (§5h–§5j, §5e–§5g).
4. **Spirit-strength is one axis** behind *both* magical uncontrollability (stronger
   spirit ⇒ less control) *and* mortality (strong spirits Break, weak ones die)
   (CATALOG §6.5–§6.6; §5d).
5. **Front / coordination-load** is what Tension measures (§2b); **Tension = the cost
   of group-shaped action**.
6. **Combat:** two-channel — damage always **≥1** (no whiff; the no-gate floor),
   to-hit **repurposed as a crit engine** (crit strips foe mitigation / fumble exposes
   self); **Dark-Souls "no number is a gate"**; **breadth-over-height** progression
   (RESOLUTION §2a/§5a).
7. **The recurring hybrid:** *procedural baseline + authored standouts* — used for
   companions, missions, campaigns, and the history layer.

**Settled decisions (dated 2026-06-27):** adopt moros's **8 stats** (CATALOG §0);
breadth-over-height capability tree; Dark-Souls no-gate; two-channel combat with
crit-strips-mitigation / fumble-exposes-self; gear = ceilings not flat; **Broken-spirit
death** (no attrition-death; execute-to-kill; spirit-strength gates Break-vs-die);
persistent named companions (grow on the same tree; no permadeath; trust/grudge/
departure; sports-squad anchor; economic engine); **drop money — adopt moros's
barter/goods/contacts economy**; magic = the spirit world (effective/sparse/
unpredictable; passive-aid items; deniable); the reactive-web world model + opacity=
agency. Charter departures recorded in DESIGN §3a/§12a.

**Open / verify-first (the next work — all flagged in-doc):** the **history-generation
layer is the foundational prerequisite** (§5j — DF-style legends, *recent + detailed*;
build it *before* the emergent-thread generator). Verify-first prototypes (cheapest
medium, before loft) for the load-bearing generative pieces: the **resolution curve**
(RESOLUTION §3), the **Tension curve** (§7), the **magic-control / unpredictability
curve** (CATALOG §6.6), and the **history→thread-web** generator (§5j). Plus tuning:
stack vocabulary, mitigation/gear ceilings, crit/fumble magnitudes, per-archetype
completion-checks (CATALOG §7).

> *Note: detailed working notes were also kept in agent memory, which is **machine-
> local** — this §0 is the portable record. The repo docs are the source of truth.*

## 1. What we are taking from moros — and what we are NOT

moros (DESIGN §2 — *same world, generated not authored*) is a **card-based
narrative TTRPG**: 8 stats, no HP, combat **resolved by drawing/committing
cards**, a human DM, and a **Tension** meter — *every act of aid raises Tension
by 1; past 5 the scene turns hostile; you bleed it off at camp.*

We take **the Tension loop** (coordination is strictly stronger, but each act of
cooperation pushes a shared meter toward "the situation turns against the
group") and **the card as the visible language of coordination**. We do **not**
take card-based resolution. Crawler stays Angband: HP, dice, to-hit-vs-AC, the
distance clock. **Cards never resolve combat** — they *direct the party* and
*spend Tension*. The card UI is the nod to moros's shared world; the engine
underneath is the Angband kernel (the §3a charter is intact).

> The pivot that unlocked this design: in moros the card *is* the combat verb;
> in crawler the card *is the coordination/goal-direction verb*. "Spend a card on
> an ally" is simultaneously the party-command gesture, the moros *act of aid*
> that raises Tension, and the Tension display surface. One metaphor, three jobs.

**Design stance — aid is the central *active* dimension, NOT D&D static flanking.**
We explicitly reject D&D's model, where cooperating is thin and passive — one
once-per-turn positional bonus (flank for +2) on a static turn-grid. In crawler
**aiding is the heart of combat and it is active and varied:** ward, intercept a
hit, stack debuffs, focus a target, open and exploit windows, cover a fumble — each
a deliberate, timed act with a cost (Tension) and a read-out (the tint). It is
*positional* but **fluidly** so (the real-time-ish distance clock, continuous
movement, intercept-by-interposing), never a static "stand on the opposite square."
If any aid mechanic ever degrades into a flat passive +N, it has drifted toward the
model we're rejecting — keep aid an *action*, not a *bonus*.

## 2. Concrete plotted end-result (one fight, beat by beat)

The target experience for **one specific scene** — pin this before any code; it
is what every invariant and test below must reproduce.

*Setup:* Hero (human) + two AI companions (a **Skirmisher**, a **Warder**) in a
corridor. Three kobolds ahead. Tension **= 0** (resets when a scene/locality
engagement begins, §11a).

1. **Baseline (free, Tension 0).** Hero glides in, bumps a kobold → ordinary
   Angband melee. Companions hold the default goal *follow + engage nearest* and
   flow-field onto the kobolds (existing §10a pathing). Three independent
   fighters — functional, but *uncoordinated and therefore weaker*. No card
   played, Tension unmoved.
2. **First aid (+1).** Hero **plays a card onto the Skirmisher** — *Focus*. Its
   goal becomes "kill THAT kobold" and it **stacks Vulnerable** on it (+% damage
   taken — a modifier into the **normal** combat path, §5a). **Tension = 1.**
3. **Second aid (+1).** Hero plays *Cover* onto the Warder → goal "ward the hero",
   building **mitigation** that **biases the kobolds' damage rolls against the hero
   downward** — up to the **soft ceiling the hero's armor sets** (§5a: gear raises
   the *cap*, not a flat reduction; to-hit barely matters — damage is the lever).
   **Tension = 2.**
4. **The burst.** With Vulnerable up, the hero stacks **Poison** and the Skirmisher
   lands the amplified hit — combined stacks = multiplicative damage no solo actor
   reaches; the kobold bursts down. Each stack-across-actors is an act of aid →
   **Tension = 3, 4, 5.**
5. **Threshold crossed (>5) → the scene turns hostile.** The crawler analog of
   "complications stack": adjacent sleepers wake, a wandering-reinforcement check
   fires, monster to-hit gets a swing. The 3-kobold skirmish becomes a real
   fight — *the dungeon noticed the party leaning on each other.*
6. **Resolve & bleed off.** Party wins, retreats to a safe pocket, **rests/camps**
   → Tension decays toward 0 over rest ticks (the §11 / regen hook). Cooldown
   before the next push.

The loop is moros's loop exactly — *lean on coordination to win faster, pay a
shared rising danger, release it in the calm* — re-pegged from
cards-resolve-combat to cards-direct-the-party. **Falsifiable:** if leaning on
coordination does **not** measurably win faster AND does **not** measurably raise
danger, the design has failed and the modifier/threshold numbers are wrong.

**Coordination is a skill lever, not a stat gate (RESOLUTION.md §2a / R3).** A
well-played, under-levelled party should be able to punch above its numbers
through *how* it coordinates — focus order, Cover timing, riding Tension right up
to the threshold without tipping it. That is the Dark-Souls "execution beats
stats" principle expressed in the co-op layer: the party hand is one of the skill
levers that keeps the end boss beatable by a fresh group.

## 2b. Solo is a party of one — and Tension is the cost of *group-shaped action*

**Solo play uses the *same* system — no separate mode.** A lone player is a
**party of one** (the actor-symmetry invariant #3 — every actor is the same Actor;
the player just fields N≥1 of them). Without NPC mates you are **structurally
weaker**: fewer cards in play, no **intercept** (no one to step in for you), no
**group-stack burst**, and you must **self-cover** your fumbles by repositioning.
You don't switch games — you run the same engine with fewer actors and feel the
gap. This is *why you recruit a party*: more actors = more coordinated power, at
more Tension.

**Tension is almost always a *group* action — the cost of *coordination*, not a
solo thing.** It is raised by *reaching above baseline together*:

- **Aid that *reaches*** — **rush-intercept** (covering a non-adjacent mate, §5a),
  **focus**, a passed/combined card. *(Adjacent intercept and ordinary positioning
  aid are **baseline** — free; only the reach costs.)*
- **Group-stack burst** — combining stacks across actors for the amplified kill.
- **Combined limit-breakers / party special opportunities** — the big group payoffs.

Baseline play (a normal attack, chipping, careful positioning, adjacent bodyblock,
a **focused single-front** fight) is **Tension-neutral**.

**The unifying definition: Tension is the cost of *group-shaped action* — divided
coordination load.** It rises whenever effort is spread beyond one focused
engagement, in *either* of two ways:

- **Many actors coordinating** (party): reaching aid, group-stack burst, combined
  limit-breakers.
- **One actor spread across many fronts** (solo overextension): **attacking
  multiple enemies at once**, **defending against enemies front *and* back** /
  fighting **surrounded** — one body doing a party's job. *Acting like a group
  alone raises Tension just as coordinating a group does.*

So **solo is not flatly low-Tension** — it's cheap while you fight *focused*
(one front at a time, the Dark-Souls "funnel them into a corridor" play), and it
**climbs as you're forced to spread** (swarmed, flanked, covering your own rear).
That's the same meter and the same push-your-luck — getting surrounded *is* the
solo version of over-coordinating. Good positioning (keep it one-front) is how a
solo player keeps Tension down; the party's job is to *let* you stay focused.

**Coordination manages the front-count from both ends — the two faces of aid.**
Since *spread* (live fronts) is what drives the load, the player coordinates the
group around *fronts*:

- **Collapse a front — *offensive*: target an enemy as priority for a quick
  takedown.** The player **marks an enemy** (the `focus(target)` goal, §5) and the
  group **concentrates** — stacks + crit-strips + the group-stack burst (§5a) — to
  **drop it fast**, removing a front. This is the offensive coordination axis:
  *focus-fire for a quick kill.*
- **Hold a front — *defensive*: ward / intercept / cover the rear** (§5a), so a
  mate (or you) isn't left fighting an extra front alone.

Both are *coordination* → both raise Tension, but both **shrink the spread** that
would otherwise drive danger. So the tactical meta-game is **collapse fronts faster
than the coordination cost accrues** — concentrate, kill, shrink the battle, before
Tension tips the scene hostile. (Solo you *can't* concentrate a group, so a
multi-front fight is far harder to collapse — exactly why you bring a party.)

Fronts also **open from the offense side**, via **attention draw** — a property of
powers (the **moros powers system**): a high-attention play *pulls more enemies in*,
adding fronts. So managing attention (and sometimes *declining* a loud play —
§5b) is part of the front game too; attention-draw spends the same front/spread
currency as everything else.

**For a party to get *all* its opportunities, Tension must rise** — and likewise a
solo player who tries to do everything at once pays for it. That gate *is* the
push-your-luck. (Sinks: rest/camp, scene reset.)

## 3. The load-bearing invariants

These are exact, not aspirational — each gets a verification (cheapest medium
first, then a headless `*test.loft` per the §10a testing tiers).

1. **Combat-resolution invariant (the charter guard).** Cards/Tension never
   resolve combat. Every hit, damage roll, and death goes through the unchanged
   Angband kernel; a card only (a) sets an actor *goal*, (b) feeds the resolution —
   **a behind-the-scenes mitigation that biases incoming-damage rolls, and status
   influences (Vulnerable / Weak / Poison / Strength) that are *modifiers into* the
   to-hit/damage rolls** (the Slay-the-Spire *undercurrent*, §5a — not a visible
   StS surface game) — and (c) moves *Tension*. Cards are the heavy action+
   coordination layer, but they **never resolve**: the kernel still rolls; the StS
   layer only **biases those rolls**. **Delete the entire card+Tension layer and a
   fully playable (if barebones) Angband co-op game remains — bump-melee still
   works.** *Verify:* the kernel combat path has zero references to cards/Tension. (That
   kernel's own flexibility — a swappable resolution distribution and a
   non-trivializing progression curve — is **RESOLUTION.md**.)
2. **Actor-symmetry invariant (the "playable by humans eventually" guarantee).**
   Every party member — hero included — is the **same Actor**; *who controls it*
   is a swappable **intent source** (AI policy | local human | remote human)
   behind the `gameflow` seam. The kernel cannot tell an AI-driven actor from a
   human-driven one. *Verify:* an actor's tick consumes only intents (`T/A`
   wire + new directive intents); it never branches on "am I the player."
3. **Tension-conservation invariant.** Tension is a single shared scalar **per
   locality** (§11a). It changes **only** at defined *sources* — **group-shaped
   action / divided coordination load (§2b):** many actors coordinating (reaching
   aid · group-stack burst · combined limit-breaker) *or* one actor spread across
   fronts (multi-target / fighting surrounded) — and *sinks* (rest/camp; scene
   reset). Focused single-front play (normal attacks, chipping, **adjacent**
   bodyblock) is Tension-neutral. Same ordered sequence of source/sink events →
   same Tension (round-trip identity). *Verify:* `tensiontest` drives N source +
   M rest events and lands on a pinned value.
4. **Determinism invariant (the hazard — read with the float-dt note).** Allies
   are **replicated** actors; their AI decisions and the Tension scalar must be
   **bit-identical** across host and replica (the `replaytest` guarantee, §gameflow
   K1). Ally AI therefore reads only the fixed-quanta clock and quantized/integer
   state — **never wall-clock, never raw float drift** (the known crawler MP
   hazard: *quantize early*). *Verify:* extend `replaytest` to a multi-actor
   fight; host and replica Sims bit-identical after a scripted party engagement.

## 4. The actor / control model — resolves the "now vs later" fork

The question was: *build the unified peer-actor model now, or lightweight
AI-only allies now + refactor later?* **§11b already settles the project's
stance, and we adopt it unchanged:**

- **The seam is MP-shaped now and never changes.** Ally control flows through the
  **same `gameflow` intents** as the human (extend the `T`/`A` wire with an
  **actor-id** and add directive intents — §6). An AI policy is one intent
  producer; a remote human is another; they are interchangeable at the seam. This
  *is* invariant #2, and it is free to honor today because the seam already
  exists.
- **The data layout migration stays deferred (§11b).** We do **not** migrate to
  `vector<PlayerState>` yet — it is gated by loft#320 (capture-append-reassign on
  a struct's vector field) and by the unbuilt §11a locality split. Allies live as
  AI-only actors *behind* the MP-shaped seam until human drop-in is actually
  built; then the data moves **once** into the verified container (§11b trigger).

So: **MP-shaped seam from day one (cheap, already there); heavy per-player data
migration deferred (per §11b, do not jump the gun).** This is the hybrid — and it
is the established crawler philosophy, not a new bet.

## 5. New pieces (and what they reuse)

**Reused (no new mechanism):**
- Flow-field pathing + target acquisition (§10a) — allies use it; target =
  current *goal* / nearest monster instead of "the hero."
- `gameflow` intent seam (`S/T/A` wire) — extended, not replaced (§6).
- §11a locality clock — Tension is per-locality; the party shares the hero's.
- `MF_FRIENDS` (already planned, §10a) — the faction seed.
- Rest/regen + the distance clock (§11) — the Tension sink.
- The overlay system (char page, inv hub) — the card hand is one more overlay.

**New (engine-side mechanism; content stays bundle-side per BUNDLE.md):**
- **Faction** on every actor (`ally | monster | neutral`) — drives targeting and
  who-damages-whom. The one cross-cutting kernel change.
- **Goal model** — a small per-ally goal (`follow · hold(hex) · focus(target) ·
  retreat · guard(actor) · gather`) the ally AI policy reads each tick. `focus` is a
  **broadcast call** others opt into (§5b), not a hard per-ally command.
- **Ally AI policy** — monster AI (§10a) with a friendly objective function:
  pursue the goal, don't suicide, respect `hold`, fall back when downed-risk, **and
  autonomously decide whether to *join* the lead's target calls** (§5b) — the same
  call-or-decline a human teammate makes.
- **Tension system** — the per-locality scalar; sources = *group-shaped action /
  coordination load* (group: reaching-aid · group-stack · combined limit-breaker;
  solo: multi-target / surrounded — §2b), sink (rest/scene reset), and the
  **threshold escalation hook** ("scene turns hostile": wake-adjacent + reinforcement
  check + enemy to-hit swing). **Solo pays it only when spread across fronts** (§2b).
  Tunable numbers, §7.
- **Card layer (the heavy action+coordination layer)** — a *hand* projected from
  each member's **learned capabilities** (the RESOLUTION.md §5a progression set —
  powers / backgrounds / specializations + items) plus moros's shared element cards
  as flavor. *What you've learned is exactly what you can play* — progression and
  the hand are the same data (RESOLUTION.md §5a). Cards are **hotbar/key-bound and
  swappable on the fly** (a quick loadout you re-key for the situation — rides the
  existing `qs` quick-slots + the `A 5` inv-bind / `A 3` use-slot intents). A card
  carries a **Slay-the-Spire-style effect payload** (§5a) — attack, **ward**,
  **stack** a debuff, or a **coordination/aid** directive — and **playing a card
  emits a directive intent + its Tension delta**. The card *interfaces and
  modifies*; the kernel still *resolves* (invariant #1). (Verified by the C4
  test: a card play emits exactly its declared intent + effect + Tension.)
- **Slay-the-Spire effect & mitigation layer** — see **§5a** (mitigation as a
  roll-biasing tilt via **two axes — ward and intercept**; stacking debuffs as
  resolver modifiers; group stacking = the coordination burst = the Tension source).
- **Hit-redirect (intercept) mechanism** — reassign an incoming attack's target to
  an **adjacent** interposing ally (the `guard(actor)` goal drives positioning),
  **capacity-limited** (the interposer's own mitigation ceiling; can't cover a
  swarm / simultaneous hits — §5a). A new kernel combat mechanism the StS
  *intercept* axis needs; explicitly *not* an absolute-tank aura.
- **Control handoff** — controller-leave → AI policy resumes that actor;
  human-join → bind to a free/AI actor. Pure intent-source swap (invariant #2).

## 5a. The Slay-the-Spire undercurrent — mitigation & group damage-stacking

The combat *texture* draws on Slay-the-Spire — mitigation, stacking, windows — but
**not the pure StS surface game.** There is **no visible block bar / energy /
explicit-counter deckbuilder** to optimize. Instead the StS concepts **heavily
influence the rolls behind the scenes:** the player fights **roll-based Angband
combat** whose odds are *biased* by mitigation and stacks they build through card
play. The StS layer is an **undercurrent feeding the resolver** (RESOLUTION.md
invariant #1) — never a parallel numeric minigame. It rides the **damage channel,
not hit-chance:** every blow **connects** and does **≥1**, so a guarded foe is
*chipped*, not *whiffed* (RESOLUTION.md §2a two-channel model). The Angband to-hit
roll **stays, but only as a crit engine** (skill/AC → crit magnitude, never
hit/miss). Two pillars:

- **Mitigation (the defensive skill layer) — two axes.** Mitigation is the
  *transient, play-built* reduction of harm (not a tracked block bar; distinct from
  static Angband AC, a fixed to-hit input). It comes **two ways**, mechanically
  different:
  1. **Ward (direct aid).** A card applies mitigation *to an ally* — biasing
     *their* incoming-damage rolls **downward** (decays over a few ticks). The
     helper stays put and grants it. Changes **how much** the protected actor takes.
  2. **Intercept (step in / take the hit) — two tiers by distance, *not* an
     absolute tank.** A mate **redirects an incoming hit onto themselves**, taking
     the damage in the fighter's place. It comes in two tiers:
     - **Adjacent intercept = FREE** (Tension-neutral). Standing beside the one you
       cover and bodyblocking is *baseline positioning* — the reward for good
       placement — and it lets **even a less-capable member protect a fighter**:
       body-blocking needs *presence, not power*.
     - **Rush-intercept = possible, but raises Tension.** To cover a mate a few
       steps away you **rush to interpose** — an *above-baseline reach* (§2b), so
       it **costs Tension** (and the rush spends your action + repositions you).
       This is how you save the out-of-position mage: never walled, but it draws
       heat.
     Changes **who** takes it. Risk-*transfer*, not erasure: the hit lands on the
     interposer (their own mitigation/HP matters), and they are **no damage-sponge**
     — intercept is **finite**: bounded by their mitigation ceiling (gear, §5a),
     **one body can't cover a swarm or simultaneous hits**, and the interposer
     wears down. Defense stays an **active, distributed, positional, fallible** task
     — never a parked tank that negates everything (Dark-Souls no-absolute-safety +
     anti-static-flank, §1). **Good positioning keeps protection free; rescuing the
     out-of-position pays Tension** — the §2b rule made concrete.
  Both are **acts of aid → +Tension**, and both are how you **Cover** a fumble-
  exposure (the low tail above). Warding the right ally and interposing the right
  body is how a weak party survives a tougher foe — the R3 "execution beats stats"
  defense (RESOLUTION.md §2a).
- **Damage-stacking (the offensive payoff).** Cards apply **status influences** on
  a target or self — **Vulnerable** (tilts its damage-*taken* rolls up), **Weak**
  (tilts its damage-*dealt* rolls down), **Poison** (a per-tick bleed),
  **Strength/Focus** (tilts your damage up). These **feed the resolver as roll
  modifiers** — biasing the normal Angband to-hit/damage behind the scenes, not as
  explicit +%-counters the player micromanages.
- **Group stacking *is* coordination *is* Tension.** The payoff is *combining*:
  one ally tilts a target Vulnerable, another lays Poison, a third lands the
  amplified hit — the rolls swing far enough that the combined burst lands what no
  solo actor's rolls would. **Stacking influences across party members is the act
  of aid → +Tension** (invariant #3). The push-your-luck stays: *stack hard for the
  kill and watch Tension climb toward the scene turning hostile, or play
  mitigation-safe and slow.* moros's Tension and StS's stacking, the **same
  gesture** — under a roll-based skin.

- **Gear sets the *ceiling*, not a flat bonus (the anti-gate gear model).** Thick
  armor does **not** grant absolute/flat damage reduction — it raises the **soft
  ceiling** on **how far mitigation can tilt the incoming rolls in your favor**; a
  better weapon/focus raises the ceiling on how far you can stack the offensive
  tilt. *Gear widens the headroom; play fills it.* This keeps gear from being a
  stat gate (R3): great armor with bad play leaves the tilt **unbuilt**, and poor
  gear with great play is *capped but always viable* (never a wall). Same
  anti-treadmill move as breadth-over-height — gear buys *ceiling*, not raw power
  (RESOLUTION.md §5/§5a). *(Reinterprets Angband armor from flat AC toward a
  mitigation-ceiling — a deliberate gear-model departure; whether AC-as-to-hit-
  input survives alongside is open, §5a open list / RESOLUTION.md §6.)*

- **The model is symmetric — monsters run it too, which is what creates *attack
  windows*.** Monsters carry **Block, stacks, and gear-style ceilings exactly like
  players/allies** — one combat model for every faction (reinforces invariant #1
  *one kernel* and extends invariant #2's symmetry from *control* to the *combat
  model*). Because a monster carries the same behind-the-scenes mitigation, the
  offensive skill is **opening a window**: land **crits** (and mitigation-strip
  cards) that **strip its mitigation** (the pinned mechanism below), lay
  **Vulnerable/Weak** to soften it, then **time the coordinated burst into the
  exposed window** — the stretch where the rolls swing hard your way because you've
  degraded its tilt. This is the *offensive* face of "skill beats
  stats" (R3) — you don't out-stat the guard, you **break it and exploit the
  opening** (Sekiro/StS guard-break → riposte). It is **two-way**: dropping your
  *own* mitigation to burst opens *you*; a monster winding up a heavy attack drops
  *its* guard and opens *it* — read the windows both directions.
- **Monster identity lives in its guard/window pattern** (ties the CLAUDE.md
  "monster keeps its true mechanic" rule). An armored brute = a high mitigation
  ceiling you must strip before its rolls turn beatable; a frenzied thing rarely
  guards but hits hard; a caster shields, then exposes itself while casting; the
  floating eye = no mitigation at all, pure gaze. Monsters become **tactically
  distinct beyond HP** —
  threat is the *pattern*, not the number (RESOLUTION.md invariant #4).

**PINNED — the crit engine is two-tailed: crit strips the foe, fumble exposes
*you*.** The to-hit/crit channel (RESOLUTION.md §2a) and the damage channel meet
here, and the roll matters on **both** tails — never as hit/miss. The rule:

- **Damage channel** (every beat): effective damage = the damage roll **reduced by
  the target's current mitigation `M`, floored at ≥1.** You always chip — on a
  crit *and* on a fumble; the crit/fumble tails cost *windows*, not damage.
- **Crit channel — the HIGH tail (offense):** on a **crit**, **strip a chunk of the
  target's `M`** (`ΔM` scaled by crit margin) and pulse its guard-tint *down*. Crit
  rate is driven by to-hit skill vs AC — so **to-hit skill = your guard-cracking
  *rate***, never a hit-gate.
- **Fumble channel — the LOW tail (defense), symmetric to the crit:** on a
  **failed roll**, create **vulnerability on the acting actor *itself*** — its own
  incoming-damage rolls biased up (self-mitigation stripped) — a self-exposure the
  **rest of the party must mitigate**, by **ward *or* intercept** (the two axes
  above) → **+Tension**, invariant #3. The exposed actor wears the **Vulnerable tint** so teammates *see* the
  opening and cover it (the co-op-legibility rationale, below). **This is the core
  reason to want a party — someone to cover your fumbles.** Solo, you cover your
  own fumble (reposition / break LOS / spend mitigation) or eat the exposure — and
  you still hit for ≥1, so a fumble is never a whiff or a gate.
- **Coupling:** crits drive the foe's `M` down → its window opens → stacks bias the
  landing rolls → the party **bursts**. Fumbles drive *your* exposure up → your
  window opens to the enemy → the party **covers** before the enemy bursts *you*.
  `M` (both sides') **regenerates** when pressure lapses (a tuning knob) — so you
  sustain crits to crack a guard before it recovers, and clear exposure before it's
  punished: the push-your-luck, offense and defense, mirroring Tension.

Concrete plotted beat — an armored brute, `M_ceiling` 10 (illustrative numbers):

| beat | event | `M` after | effective dmg | tint |
|---|---|---|---|---|
| 0 | guarded | 8 | — | deep blue (strong) |
| 1 | hit, no crit (roll 6) | 8 | `max(1, 6−8)` = **1** | deep blue |
| 2 | hit + **CRIT** (strip 3) | 5 | 1 + crit bonus | pulse → mid blue |
| 3 | ally stacks **Vulnerable** | 5 | — | red pulse → red tint |
| 4 | **CRIT** (strip 3) | 2 | `(6−2)×Vuln` = real dmg | tint nearly gone |
| 5 | party **burst** (`M`≈0) | 0 | full rolls + stacks → **kill** | guard gone |

*Fumble beat (the low tail, same fight):* the hero's roll **fumbles** → the hero
gains **self-vulnerability** (red tint on the *hero*); the Warder spends **Cover**
to mitigate it (**+1 Tension**) before the brute's next swing lands amplified.
Uncovered, the hero just takes a harder hit — worse, never an instakill.

**Invariant (R3 preserved, both tails):** with **zero** crits you still win — chip
is always ≥1, grinding HP slowly; crits/stacks only **accelerate** by cracking the
guard. A crit is never *required* and never a gate; a **fumble never whiffs and
never instakills** — it adds a *recoverable* exposure (covered by the party, or
self-cleared solo). **Verify:** a `combat` test drives a scripted fight and asserts
(a) damage ≥1 every beat (crit, normal, *and* fumble); (b) `M` strictly decreases
on a crit; (c) a **zero-crit run still reduces HP to 0** (slowly); (d) a crit-rich
run kills in fewer beats; (e) a **fumble applies self-vulnerability that an ally's
mitigation clears** (and that a solo actor can self-clear); (f) uncovered exposure
raises incoming damage but never one-shots. *(Falsifiable: if a guarded foe is
un-killable without crits, or a fumble can be unrecoverable, the coupling has
reintroduced a gate — R3 violated.)*

**Reading the hidden state — color-shift indicators only (and they are
load-bearing for co-op).** The rolls are hidden, but the player must read the
*qualitative* tactical state — and in multiplayer this is **necessary, not
polish:** an aid action comes from *another* actor (an AI ally or another human),
so unless it produces a **visible change on the target, it is unclear an aiding
action even happened** — you couldn't tell your teammate's Vulnerable landed
before you burst, or *why* Tension just jumped. The color-shift is the **render of
a broadcast aid-intent** (§6) — the visible face of invariant #3's *act of aid*.
The **only** indicators are **special-states drawn on the actor itself as color
shifts**, the **shift intensity encoding magnitude** — *no bars, no numeric
counters, no separate StS HUD.* You glance at an enemy's tint to know "heavily
guarded" vs "vulnerable now — burst it"; an ally's to know it's warded or buffed.
Each tracked state maps to one shift (illustrative): **guard/mitigation** a cool
armored tint, **Vulnerable** a hot red shift, **Poison** deepening green, **Weak**
a desaturated pall, **Strength/Focus** a warm glow, **window-open/exposed** the
guard-tint *dropping* or a brief flash. Stronger state → stronger shift.

- **Show the *event*, not just the steady state.** Because the point is "did an
  aid action happen," the **onset** of a state needs its own cue — a brief pulse /
  flash as the tint appears — so the *moment* of aid registers, distinct from the
  persisting tint that shows the ongoing magnitude. (A teammate stacking Vulnerable
  reads as a red *pulse* settling into a red *tint*.)

- **It rides the existing renderer** — sprites already carry per-actor colour
  (`cr/cg/cb`, view.loft); the kernel stays data-only and **exposes state
  magnitudes via `sim_` accessors**, the view maps state → tint (architecture
  invariant intact: no graphics in the kernel).
- **Legibility caps the vocabulary.** Color shifts must stay distinguishable, so
  only a **small set of states** can read at once — this **bounds the stack
  vocabulary** (feeds §5a's "stack vocabulary + caps" open item) and argues for
  *few, strong, legible* states over many subtle ones. A dominant/most-recent
  state may need to win the tint when several overlap.
- **Perception reads it deeper.** The tints show to everyone, but a *perception
  action* / high-Perc actor (§5c) reads them **earlier and more precisely** (exact
  mitigation, a telegraphed blow) — so reading the field is itself a skill/build, not
  a free universal HUD.

**The execution-depth question (R3 / RESOLUTION.md §2a, R-exec) is answered here:**
crawler's execution depth is **StS-tactical** — opening windows (crit-strip
mitigation → stack → burst), mitigation timing, landing the burst before Tension
tips, hotbar-swapping for the situation — **not twitch-dodging.** The turn/roll Angband core is
*kept*; depth comes from the card layer. (So we land on the *lighter* point of the
twitch axis but *deep* on the tactical axis — the spectrum question is resolved.)

*Open:* the exact stack vocabulary + caps (bounded by color-shift legibility —
above); Block decay rate; whether stacks are per-target counters (likely); the
**state→tint palette + intensity curve + overlap-priority** (view-side: which
state wins the tint when several stack, the magnitude→saturation mapping); how
`margin` from
the bell resolver (RESOLUTION.md §9) feeds stack potency; **the gear→ceiling
mapping** (how an armor value sets the mitigation soft cap and a weapon/focus sets
the stack cap — a curve with diminishing returns, not a flat add); the `ΔM`-per-
crit and **mitigation regen** rates (the pinned coupling's tuning knobs); and
**the monster *guard/window pattern* data** — `MonsterDef` (bundle-side,
BUNDLE.md; extends DESIGN §10a "Data additions") gains a mitigation ceiling +
guard/expose rhythm + a **spirit-strength** value (the §6.6 magic-target `S` *and*
the §5d Break-vs-die gate — one field, double duty) so each monster's window
behaviour and mortality are authored content, the engine reading it generically. *(AC-survives-as-to-hit is now decided — yes, as
the crit-engine input, §2a / pinned coupling.)*

## 5b. Coordination control — *call-and-join*, not command (and not a mood)

**Who decides to spend the shared Tension?** Each actor — by choosing to *join* a
call. The control model is **target-driven and invitational**, not a posture/mood
dial and not puppeteering:

- **The coordination lever is *designating targets* — two ways.** **Explicitly:** a
  priority mark / focus call ("take this one down"), issuable from anywhere — incl. a
  backline supporter who never engages. **Implicitly, by attacking:** the front
  fighter's target *is* a call — **who you swing at becomes the focus** others can
  rally to, no separate button (lean inputs, §3a #7). Either way it's an
  *invitation*, not a command — and there is **no mood dial**; the mark (explicit or
  by-attack) is the whole interface.
- **Every other actor — AI ally *or* human teammate, identically (invariant #2) —
  autonomously chooses to *join*** the call (pile their actions onto the marked
  target → the group-stack / quick-takedown front-collapse of §2b) **or not** (keep
  doing their own thing). Coordination is therefore **emergent**, not commanded.
- **Declining is legitimate and *reasoned*, not inertia.** An actor weighs a call
  against its own situation and may rightly refuse for:
  - **internal safety** — too low, or joining would overextend/expose it (the §2a
    fumble risk, the §5a "not an absolute tank" finitude); and
  - **attention draw** — a property of the power it would use (the **moros powers
    system**): high-attention plays **pull more enemies onto the party** → *more
    fronts* → more spread/Tension (§2b). Declining over attention-draw is the AI
    managing the front-count, same currency as everything else.
  So an AI ally may decline because joining would imperil it or *draw the room* —
  exactly the call a human teammate makes ("I'm too low" / "that'll aggro
  everything"). This is what makes allies feel like agents, not yes-men.
  - **trust / grudge** — a persistent companion's **cooperation level** toward the
    leader (§5e): a **grudging** companion is *less likely to join* (hangs back,
    declines aid), a trusting one rallies readily. So how you've *led* — protected
    them, honoured their goals, split loot fairly — feeds directly into whether they
    answer your calls.
- **Tension rises only when others *rally*** — i.e. when coordination actually
  happens. **The lead never spends the shared meter on others' behalf**; the lead
  *calls*, the others *join*, and the join is what raises Tension. A call nobody
  joins **costs nothing**.
- **The caller role is decoupled from tank/DPS — you can *support by directing*.**
  Because a call is a *mark*, not a front-line act, a player can contribute mainly
  by **setting targets** (plus warding/buffing) **without being the tank or the
  damage** — a *support / shot-caller* role. Calling takes **judgment, not power**,
  so — like intercept-by-presence (§5a) — it gives a **frail or support-built
  character a real job**: *direct the party's focus*. And "lead" is not a fixed
  seat: **any actor can call** (calling is a contribution, not an authority), so the
  shot-caller is a *playstyle* a capability build (RESOLUTION.md §5a) can specialize
  into, not a throne. **Directing spans the whole spectrum:** a backline supporter
  calls by *explicit mark*, a **front fighter calls by *attacking*** (who they swing
  at — above) — so leading the party's focus is available from *any* role or
  position, back or front. (Open: multi-caller arbitration when several mark at once
  — §7.)

This **answers the AI-Tension-control question** (and replaces the earlier
posture/budget sketch): an AI ally decides to join a call exactly as a human
teammate would — weighing it against its own situation — so the model is **identical
for AI now and human drop-in later** (invariant #2), nothing to redesign. The lead's
influence is the **strength/clarity of the mark**, never authority over each ally's
actions. (`focus(target)` in the goal model, §5, is thus a *broadcast call* others
opt into, not a per-ally command; the ally AI policy's core decision is *join this
call or not*.)

## 5c. Round actions beyond attacking — leadership & perception (from moros)

A combat round's action **need not be an attack.** moros formalises this: a faster
actor spends spare time on a **secondary action — Scout / Observe / Gather — taken
alone and *not* raising Tension** (RULES.md). crawler imports the two combat-relevant
ones as first-class round actions — which the call-and-join model (§5b) makes
natural:

- **Leadership — *call / direct*.** Spend the round **marking targets**, rallying,
  or repositioning the party (§5b) instead of swinging. The call itself is
  **Tension-neutral**; Tension rises only if others *rally* (§5b). This is what lets
  a **backline shot-caller / support** play a full, active round without
  front-lining (§5b).
- **Perception — *Observe / Scout* (Perc-based; moros's secondary action).** Spend
  the round **reading the field**: surface an enemy's hidden state (its mitigation
  level, an opening — the §5a color-shift read, *sharpened*), reveal threats, or
  **scout** what's coming (a front about to open — moros's "can't be surprised next
  round"). It buys **information** — the input good calls need — and, per moros,
  **does not raise Tension.**

Why it matters: it gives **non-fighters and the lead real round-to-round agency** —
you contribute by *directing* or *reading*, not only by damage — and it makes
**perception a build** (a Perc/Lookout capability, RESOLUTION.md §5a) that earns its
place *in combat*, not just exploration. Perception is also the **skill that reads
the hidden state**: the §5a tints show to everyone, but a perception action / a
high-Perc actor reads them **earlier and deeper** (an enemy's exact mitigation, a
telegraphed blow), turning "execution beats stats" (R3) into partly an *information*
game. *(Source: moros RULES.md secondary actions; COORDINATION_ROADMAP.md — "the
cooperative register Moros rewards.")*

## 5d. The Broken-spirit state — no death by attrition; killing is a deliberate act

There is **no per-se death mechanic** (resolving the §7 "downed model" open item).
This is moros's **Broken** state (the Clan power "stabilises a fallen *Broken* ally").

- **HP attrition breaks the *spirit*, it doesn't kill.** When an actor's HP bottoms
  out its **spirit breaks → Broken** — ties the spirit cosmology (CATALOG.md §6.5):
  combat breaks *spirits*, the same substrate as magic. Broken = **out of combat
  participation** (no attacks / cards / abilities — it doesn't fight or coordinate)
  — but **not frozen.**
- **A Broken member still follows the group — slowly — and aid hastens them.** It
  **shambles along** after the party at reduced speed (the distance clock, §11; cf.
  moros's minimum-group-pace), and a mate can **lend aid to speed it up** (help it
  along / haul it — a Portage-flavoured support act). So a Broken ally is a
  **mobility burden, not dead weight to abandon**: the group either **slows to its
  pace**, **aids it to keep up**, or risks it **lagging out of the protective
  formation — where an enemy can catch and *execute* it** (below). Keeping a Broken
  mate moving *with* the party is itself part of the protect-the-body loop.
- **Recoverable, not dead.** Stabilise/revive (Clan in-fight; camp/rest out of
  fight) restores participation. Broken is the **buffer**, not the end.
- **Actual death is a *deliberate act*, never attrition.** To truly kill a Broken
  character an enemy must spend an **active action to execute** it. **Only execution
  → real death → the §3a stake** (respawn at the checkpoint + **goods**-grave, the
  hauled cargo dropped at the death spot — money is dropped, §3a economy). So death
  is **rare, intentional, telegraphed, and preventable** — never a chip-attrition
  accident (maximally §3a-friendly, R3-consistent: the ≥1 chip floor, §2a RESOLUTION,
  brings actors *to Broken* — always progress — but Broken ≠ dead).
- **The co-op loop this creates.** A Broken ally is a **body to defend**:
  intercept / cover / hold the front around them (§5a) to **deny the executioner**,
  then **revive** (Clan). The enemy's execute is a *tactical choice* — an action
  **not** spent fighting — that the party can disrupt (body-block the executioner).
  This is the **visceral heart of "why a party"**: they keep your broken spirit from
  being finished.
- **Solo.** Broken with no reviver is dire — an enemy can execute you; or, if you
  survive / disengage, a **slow self-recovery**. One more way "a party of one is
  structurally weaker" (§2b).
- **§3a reconciliation.** The §3a death model (lose-the-dive, **goods**-grave, respawn)
  now fires on **actual death (execution)**, *not* on being Broken — a Broken-then-
  revived fall costs only the scare. The stake is reserved for the party **failing to
  protect/revive**; the §3a "graves at deadly spots → group up" loop holds, keyed to
  real deaths.
- **The party *is* the primary death-stake mitigation — by design.** Because Broken
  is recoverable and death needs a *deliberate execute the party can deny* (defend
  the Broken body, revive, haul it out — above), **a functioning party strongly
  buffers individual death.** That's not softness, it's the **party's value** —
  safety in numbers, *no one left behind*. Consequences:
  - the death stake's **full bite lands on *solo* play and *party wipes*** (the
    moments protection fails) — reinforcing "a party of one is structurally weaker"
    (§2b);
  - **don't over-engineer extra death penalties** — the stake is *calibrated by
    party-presence*, not by piling on cost;
  - so in party play the **meaningful stakes shift** to: a **wipe** (catastrophic —
    the §3a goods-grave on the *whole* haul), **retreating and losing the dive's
    haul** (the goods-grave bites *without* a death), and the **Tension /
    scene-turns-hostile / overwhelmed** pressure — *not* individual falls.

**Monster symmetry — SETTLED: spirit strength gates the Broken state.** Symmetry
holds at the *model* level (one mechanic for all actors), resolved by the **same
spirit-strength axis that governs magic** (CATALOG.md §6.6) — not a special case:

- **Strong spirits Break** — the party, sapient folk, uniques, bosses, significant
  creatures: out of combat, recoverable, **execute-to-finish**, **faction-revivable.**
  The beings where the Broken *drama* matters.
- **Weak spirits die outright** — vermin / trash (rats, molds, the like): no Broken
  state, no execute step → **fast clean kills** (the mow-through-trash pace). Creature
  type is the flavour correlate; **spirit strength is the governing variable.**
- **Player & party are strong spirits by definition** → always Break, never die
  outright (§5d above).
- **Mirror payoff:** a Broken *significant enemy* can be **revived by its faction**
  (a lieutenant raises its boss; a pack-leader its pack) — so the player faces the
  **same execute-choice** (finish it to deny the revive, or press on). Escalating and
  **rare** (significant foes only), never per-trash friction.

So the **one spirit-strength axis governs both magical uncontrollability (§6.6) and
Break-vs-die** — strong spirits are *both* hard to control and hard to kill, a single
world-property. **Data:** `MonsterDef` gains a **spirit-strength** value
(bundle-authored — likely needed anyway for the spirit cosmology / magic targeting);
the Broken-gate is a threshold on it.

## 5e. Companions — a persistent, growing roster (no permadeath)

Where the party comes from. **DECIDED: persistent named companions, growing on the
same tree, no permadeath.**

**Design stance — companions feel *real*, but never take the hero spot.** The
calibration for *everything* in this section: companions are **vivid, autonomous,
persistent people** (named, growing, with wants, trust, grudges, departures, homes) —
*real* — **yet the protagonist spot stays the player's.** Concretely:
- **Narrative** — companion arcs are **supporting** threads that enrich the hero's
  journey, never supplant it; the story is the player's.
- **Spotlight / agency** — the **player leads**: the primary caller and decision-maker
  (call-and-join, §5b — the player *calls*, companions *join*); focus and key choices
  default to the hero.
- **Competence** — companions are **complementary specialists**, not strictly-better
  replacements. A companion may out-tank or out-scout the hero (they grow on the same
  tree), but the hero is the **fulcrum** — the leader, the one the player directs, the
  adaptable centre — never out-shone at *being the protagonist*.
- **Self-enforcing** — a dissatisfied companion **leaves** (§5e departure); it never
  *usurps*. Their autonomy serves the party's (hero's) endeavour, not a competing one.
- **MP framing** — the **hero spot = the player-controlled character(s)**; AI
  companions are real-but-supporting. A human takeover (invariant #2) *makes* that
  slot a hero spot; the remaining AI support. So "NPC" = AI-driven = supporting; the
  spotlight belongs to whoever a human is driving.

(This is a *design / narrative / UX* primacy, **not** a kernel special-case — the
actor model stays symmetric, invariant #2; hero-primacy lives in *who the player
drives + leadership + spotlight*, never in bespoke hero-only mechanics.) The tone:
you **care about** your companions and they feel alive, but you're living **the
hero's** story, not managing a cast that eclipses you.

- **Persistent named companions, not fungible hires.** Party members are **recruited
  from the world's folk** — of varied **races** (→ the playstyle diversity of §5a /
  CATALOG.md §2: a flying Owl scout, a digging Boar tank, a Wolf-folk pack-hunter) —
  each a **full character** with its own capability build (race innate powers +
  learned capabilities + passive aids), *yours*, named, not a generic merc. That
  identity is what makes the co-op drama land (covering *their* Broken body, reviving
  *them*). They are full `Hero`-grade actors (actor-symmetry invariant #2).
- **They grow on the same tree.** Companions **progress on the same breadth
  capability tree as the player** (RESOLUTION.md §5a — learn powers/backgrounds/
  specializations, +1 linked stat, soft-capped height; find/craft passive aids,
  CATALOG.md §6.7). So each is a **growing, invested character** — you build your
  party's playstyles over time. *(Open: do you direct a companion's capability picks
  as party leader, or do they auto-grow with light guidance?)*
- **No permadeath — companions are covered too.** A companion can be Broken (§5d) and
  even executed, but the §3a no-permadeath model **covers them**: a lost companion is
  **recoverable / returns at a checkpoint**, never permanently lost. So protecting and
  reviving a Broken companion is about **the fight** (keep them in it, avoid the §3a
  setback), *not* about losing a character you built. The stake of a dive stays **the
  dive and the hauled goods** (§3a — money dropped), never the roster.
- **Human takeover rides on this.** Because each companion is a *full built character*,
  the dynamic drop-in (invariant #2 / §5 control-handoff) puts a human into a **real
  character**, not a generic slot — persistent companions are precisely what make
  human drop-in coherent.
- **Per-actor data.** A roster of growing companions makes the per-player state
  genuinely **per-*actor*** (each carries Hero-grade stats/capabilities/aids/HP) — the
  shape §11b anticipates; its "defer the `vector<PlayerState>` migration until MP /
  locality is built" decision still holds, the container is now clearly per-actor.

- **What a companion *wants*: participation, and their unique skills *used*.** A
  companion's core desire is **to be in the action and to have what they're good at
  *employed*** — the digger to breach, the scout to scout, the tank to hold the
  front, the caller to call. They **stand *partially* for their background** (and
  race, CATALOG.md): a Watch values order/protection, a Back-alley cunning/loot, a
  Hunter the chase — the *baseline* disposition falls out of **who they are**
  ("partially" leaves room for individual personality + a later authored arc).
  So **honouring a companion = good *deployment*** — calling on their strengths
  (§5b), keeping them in the fight; **side-lining them is the betrayal** — benching
  them, leaving their unique skills unused, making them redundant. *(Roster
  consequence: you can't hoard idle companions — a benched one loses trust and
  eventually drifts home, §departure. They want to **play**.)*
- **Trust & grudges — the *strife* dimension (companions are *people*).** A
  persistent companion carries a **trust / cooperation level** toward the leader (and
  potentially other members). It **falls into a *grudge*** when leadership costs them
  — **side-lining them** (skills unused / benched — above), getting them
  **Broken/executed** (you failed to protect them, §5d), **ignoring their calls or
  goals**, **reckless overextension** (spiking Tension on a gamble they didn't want),
  an **unfair loot (goods) split** (§3a economy — no money). A grudging companion
  **cooperates less**: it is **less likely to *join* your calls (§5b)**, may decline
  aid, hang back, or act on its own — so **trust is a direct input to the
  call-and-join decision** (§5b), alongside safety and attention-draw. **Regaining
  trust takes *work*** (not instant): protect them, honour their goals, fair shares,
  camp/downtime, resolve the grievance. So **leadership carries a social
  consequence** — callous command breeds a party that won't rally; care earns one
  that does. The party can be *people at odds*, not just a stat-block.
- **Departure — the terminal low-trust outcome (recoverable, not loss).** At the
  bottom of the trust track — a deep grudge, a **failed mission / wipe**, or a
  betrayal of their core goal — a companion can **decide to leave the party and
  travel *home*** (back to where you recruited them). This is *agency* — the ultimate
  expression of the autonomous-actor model (invariant #2; a human teammate, too, can
  just quit). It's a **real but non-permanent loss** (consistent with no-permadeath):
  the companion still *exists*, at home — you can **seek them out, make amends, regain
  trust, and re-recruit** them. So bad leadership can cost you a companion's
  *participation*, never the *character*; a failed mission carries a **roster/social
  consequence**, not just the §3a dive-loss. (Ties recruitment: companions have
  **homes** in the world — where they return, and where you win them back.)

**Anchor — companion psychology = how a *sports player* views their work.** The whole
trust layer is grounded in a real, well-understood model: a companion is a
**professional athlete**, the leader is the **player-coach / squad manager**, and
job-satisfaction maps almost 1:1:
- **participation + unique skills used** ↔ **playing time + being played *in
  position*** (benching, or playing someone out of role, is the core grievance);
- **fair loot (goods) split** ↔ **fair pay & recognition**;
- **mission success / failure** ↔ **winning / losing** (morale);
- **trust in leadership** ↔ **trust in the coach** (man-managing a dressing room);
- **departure → travel home** ↔ a **transfer request / leaving the club**;
  **re-recruit** ↔ **re-signing / reconciliation**;
- **trust → willingness to join calls (§5b)** ↔ **morale → form & effort.**

This is the **tuning lens** (think *squad morale / a football-manager sim*) and the
reason the design reads as authentic — real athletes feel exactly this. It opens
further hooks: **rotation** (keep the *whole* roster playing — reinforces "can't hoard
idle companions" + the roster-vs-active-party open Q); **star vs role players**
(different deployment expectations — a star wants the spotlight / focus-calls, a role
player wants their niche valued); **light companionship/relation buffs** (cohesion +
optional bonded-pair buffs — kept low-attention, *not* a rivalry-management puzzle;
§5f); and **form/morale streaks** (recent results carry momentum on the trust track).

*(Open: **recruitment mechanism** — recruit folk via towns/quests/encounters; the
rich version is **gated on the overland/town layer** (like the §economy contacts,
L3), with a starting companion or two near-term. **Roster vs active-party size** and
swapping companions at camp/town. The trust/grudge layer is a **cooperation**
mechanic (it gates *working together*) — **not** a full romance/social sim; it
deepens the persistent-companion idea and extends §3a's relaxed "no factions/NPCs"
pillar, without reopening it as a social sim.)*

## 5f. Light companionship buffs — and why group size still governs itself

Inter-companion relations are kept **light — no micromanagement** (deliberately *not*
a dressing-room rivalry puzzle to babysit).

- **Companionship buff.** A party that adventures together develops **cohesion** — a
  passive group buff for being a settled, familiar unit. Always-on, low-attention.
- **Relation-buff (optional, emergent).** Specific pairs that bond (shared history /
  race-background affinity) grant a small **pairwise buff** — it *emerges*, you don't
  tend it.
- **The one real downside: losing a bond hurts.** When a **bonded companion leaves**
  (§5e departure), the other **loses the relation-buff and takes a morale/trust
  knock** — so a departure *ripples* (felt, not free), but it happens on its own; you
  feel the loss, you don't manage the relationship.

**No rivalry micromanagement.** We deliberately **drop** the "manage feuds /
two-strikers-one-spot dressing-room puzzle" — too much attention. Role overlap still
matters, but **through the *individual* want, not an inter-NPC rivalry**: a redundant
companion simply gets **under-deployed** → unhappy (§5e: they want participation +
their skills used) → **drifts home**.

**So group size still governs itself** — you can't recruit-everyone-and-trivialize,
because the **under-used leave** (no need for any rivalry layer). Party size is
bounded **organically — by how many you can keep meaningfully deployed — not by an
arbitrary "max party = N."** The **§3a #2 non-trivialization charter, achieved
*socially***: you can't **out-*number*** content; you field a **manageable, deployed
squad** and win by *play* — Dark-Souls "skill, not numbers" (RESOLUTION.md §2a) at
the **roster** level. *(Resolves the "roster vs active-party size" open Q toward a
**soft social governor**, not a hard cap — a practical active-party limit may still
exist for coordination / Tension / screen reasons.)*

## 5g. Companions are your economic & status engine

A specific companion — **grown and trusted** — has a **tangible impact on the
player's economy and standing**, not just combat. Companions are recruited from
world-folk with **backgrounds** (CATALOG.md §3), and a background brings its network
and assets to the party:

- **Contacts** → market **channels, access, reputation** (a Trader's caravan/guild
  factors; a Back-alley's fences; a Noble's court; a Watch/Army's garrison).
- **Kit** → transport/**capacity** (cart, mounts → hauling, the §3a economy).
- **Crafting** → **value-conversion** (Smithing/Jeweler/Cooking — loot → gear, food,
  appraised value; CATALOG.md §6.7).

So **which companions you hold shapes your economy and standing** — you don't have
every background yourself, **you recruit the folk who bring them**: a **Trader** opens
trade channels, a **Noble** lends **status/access** (doors open, factions receive
you), a **Crafter** converts loot to value, a **Back-alley** opens illicit channels.

- **Growth + trust *amplify* it.** As a companion grows (capabilities — esp. the
  economic axes **Hand/Char/Perc**) and **trust deepens** (§5e), their economic/status
  contribution **scales**: they open more of their network, **vouch** for you
  (reputation), craft more, haul more. A *trusted, grown* companion is a far bigger
  asset than a fresh, wary one — **trust gates the economy** (a grudging companion
  withholds network and craft; and an unfair loot-split → grudge → *lost economic
  benefit*, a feedback into §5e).
- **Departure has economic teeth.** Losing a trusted companion isn't just a combat
  slot — it's losing their **network, capacity, crafting, and the standing they
  lent** (§5e). A tangible blow that raises the stakes of keeping them on-side.
- **The hero's *standing* rises through companions** — you become "the company with a
  noble / a famed crafter / a trade magnate's friend." Keeps the hero central (§5e
  stance): it's **your** status, grown via **your** people.
- **Diversity incentive.** Because each background opens *different* doors, you're
  drawn to a **diverse roster** (varied backgrounds + races) — dovetailing with §5f's
  group-size governance (a few diverse, well-deployed companions, not a horde).

*(The rich **contacts/channel** layer is **gated on the overland/town layer** (L3),
like the economy notes; near-term a companion's **kit (capacity)** + basic
value-conversion already bite. The economy systems themselves: DESIGN §3a #5, §12b.)*

## 5h. Missions — person-anchored objectives (the existing quest system)

**Missions are crawler's existing bundle-authored quests** (BUNDLE.md `QuestDef` —
objective types RESCUE / RETRIEVE / SLAY…, target, requirements (lock-and-key chains),
rewards, routine-ids; death-bound quest items; a quest is both a *pooled definition*
and a *generative force* placed in the world). **Reuse it — not a new system.** The
**archetype taxonomy** (16 quest-kinds in 6 lever-families — *relational-first*) and the
**generic mission format** (the schema a quest fills, = `QuestDef` + face/levers/links/
stake/partial-resolution) are in **CATALOG.md §7**, derived from the whole moros corpus.

- **Authoring spectrum** (all bundle-side, library-like): **generic** (pooled +
  generative — templated, assigned to a place, linking other places; replayable) →
  **designed** (specific hand-authored lines — the Circle's writ, desert_surprise) →
  **campaign-specific** (authored packs — the **moros tension-moment /
  COORDINATION_ROADMAP arcs** as a campaign bundle).
- **THE rule — every mission ties to a *person* in the world** (a giver / stakeholder
  / target). This **wires missions into the social & economy web**: the person behind
  a mission is a **contact** (economy network, §5g), a **companion** (their arc, §5e),
  or world-folk (a **recruit-to-be**). **Completing a person's mission deepens that
  relationship** — a contact **levels up** (more economy/access), a companion's
  **trust grows / their arc resolves**, a rescued or aided person may become a
  **contact or a recruit**. So missions are the **engine of the social/economy
  graph**, not isolated objectives — and a **failed mission** (§5e) is what *costs*
  that relationship (companion trust, contact standing).
- **Nesting (the synthesis).** The **overland** is the canvas (player-chosen
  difficulty, §3a #9); **dives** are the spatial-challenge venue; a **mission** is the
  directed, person-anchored objective that often **contains a dive** (a *reason* to
  dive *this* place) and — for the bigger / campaign ones — climaxes in a coordinated
  **tension-moment setpiece** where the party shines. Generic missions are emergent /
  replayable; campaign missions are the authored spine (the **structure: §5i**).
  **Companion arcs (§5e) are person-anchored missions tied to a companion.**

## 5i. Campaign-bundle structure (the moros template)

A **campaign-specific mission pack** (§5h campaign tier) is authored as a **bundle**
following moros's campaign shape (inspected from `moros/doc/claude/CAMPAIGN.md` +
`COORDINATION_ROADMAP.md`). The template — and how each part rides systems already
built:

- **Background** — the standing world-situation the campaign opens on (the crisis, the
  key faces, the key places). Sets the stage; not yet play.
- **Thread-web — a thread ≈ a crawler quest/mission.** The campaign is a *table* of
  long-running **threads** (`thread · core question · connects to`), interconnected (a
  graph, not a line). **Each thread maps cleanly onto a `QuestDef`:** the *core
  question* = the quest **objective**, *connects to* = its **requirements / lock-and-
  key links**, the *resolution* = its completion (a **tension-moment** setpiece), the
  *face* = its **person-anchor**. So **crawler already has the thread-web
  representation — it *is* the existing quest lock-and-key graph** (BUNDLE.md: a quest
  is a generative force that makes places link logically). moros's campaign structure
  is the **spine + face + signpost + branching layer authored *on top* of** that graph.
- **Tension-moment missions are the SPINE — they *are* the campaign.** Progression
  happens **only** through **coordinated group setpieces** that **resolve** a thread
  and **open** new ones; everything between (travel, camp, talk, prep) is *approach*,
  not progression. **2–3 tension-moments per arc.** Test: *could it happen without the
  group?* — if one specialist carried it while others watched, it isn't one. → these
  are the **party-coordination climaxes** (the party *shines* — Tension §2b, call-and-
  join §5b, the front game); a mission *contains* a dive (§5h nesting).
- **Face-first — every moment leads with a *person*** (a **name** + a **condition
  specific to them** + a **reason the party would feel their loss**); the mechanics
  hang off the face. → this **is** the §5h "every mission ties to a person" rule
  (moros's #1 principle); the person is a contact/companion/recruit-to-be, and the
  moment **deepens that relationship** (§5e/§5g).
- **NPC signpost-map** ("who leads to what") — each NPC → where found → what they point
  toward or teach; organised by hub; + an **"if the party is lost"** fallback
  (re-surface threads via rumour). → the person-anchored mission graph (contacts /
  companions are the signposts).
- **Branching / partial / combinable resolutions, multiple climaxes.** A big thread has
  **several valid resolution paths** (partial outcomes accepted; paths combine;
  world-specifics are levers on multiple paths); the campaign has **several possible
  climaxes**, player-steered, often bittersweet. → §3a #9 player-chosen; the open feel.
- **Repeated setpiece pattern, relationally solved** (moros's *shackle towers*: six,
  each broken by its own *relational* lever — befriend / free / bring-what-it-wants /
  consent — **not a combat clear**). → the **template for a crawler campaign mission**:
  person-anchored, coordinated, **relationally-solvable** (the trust/contact web), not
  just a kill.
- **Scenario-progression = onboarding; places are layered.** The campaign introduces
  mechanic/scenario types **in sequence** (the tutorial curriculum — §3a #8 novelty
  curve); a place is **layered** (a dungeon *and* a thread-node *and* an NPC-home at
  once).

**So a crawler campaign bundle = Background + thread-web + a handful of person-anchored
tension-moment missions (relationally-solvable coordinated setpieces) + an NPC-signpost
map + branching/partial resolutions** — all on the `QuestDef` mechanism (BUNDLE.md),
riding the party-coordination, trust/contact, and person-anchored-mission systems above.
Generic + designed missions (§5h) are the everyday tier; **this is the authored spine.**

## 5j. Emergent threads from the procedural world (the generative engine)

Can threads/missions **emerge** from crawler's procedural world rather than only be
authored? Yes — crawler already has the pieces: procedural world-gen (§3a #1, §10a),
the **generative quest graph** (`QuestDef` "makes places link logically", BUNDLE.md),
procedurally-placed **persons** (the civilian role/folk system), and now the moros
*thread-shape* (§5i). A thread ≈ a `QuestDef` (§5i), so generating threads = generating
person-anchored quests from the world's own material.

**PREREQUISITE — the world-building (history) path comes *first*.** Much of what makes
moros's structure *meaningful* rests on **history — *why* things are the way they are
now**: the elemental is caged *because* the seizing mages moved the towers; pirates
exist *because* a war stranded soldiers; the desert spreads *because* chaotic spirits
migrated from the blasted lands. Threads draw their **meaning and interconnection from
that history.** So before the generator below can be *realized*, crawler needs a
**procedural history-generation layer** — generate the **past** (foundings, wars,
catastrophes, migrations, bindings) that *produces the present world-state with
built-in causes*.

**Method: Dwarf-Fortress-style legends-generation — but *shorter time-scale, more
detail*.** DF simulates *millennia* of broad-but-shallow history (an encyclopedia of
ancient kings). crawler takes the **opposite trade**: a **recent, dense,
character-driven** history — **living memory** (a generation or a few, like moros's
"the war a generation ago"), **not ages** — swapping DF's vast breadth for **depth**.
Fewer events, each **richly detailed, consequential, and traceable to a named cause**
(matching moros's face-first tone) — so the present world inherits *specific, legible*
causes, not a shallow ancient sweep. The layer produces:
- **persons** whose wants/relationships are **historical residue** (a refugee of a
  collapse, the mage who caged the spirit, a soldier-turned-pirate);
- **crises** that are **ongoing consequences** of past events (the §5j crisis-drivers,
  now *explained*);
- **places** layered with their history (a tower = where a mage hid caches before the
  seizing);
- a **genealogy — parents + children** — the **backbone** of the person-graph: at the
  short/living-memory scale "history" largely *is* **a few generations of lineage**
  (DF-style legends, recent). Family is the **most weighted link** (rescue *my child*,
  avenge *my father*, find *my lost kin* — moros's Bean arc, the scattered-kin search)
  and a **prime thread source** (succession, inheritance, continue-a-parent's-work,
  lost kin). NPCs are **born, age, and die**, so the world has **generational
  continuity** across a campaign (late faces carry inherited stakes — §5i). Companions
  and the player have parents/children too (a companion's kin feeds their arc & their
  "go home", §5e).
- the **faction/relationship graph** = the **residue of historical alignments and
  grudges** — built *on top of* the genealogy (alliances and feuds run *through*
  bloodlines).

**Without a generated history, emergent threads are shallow** ("kill rats for a
farmer"); *with* one, a thread is "resolve a **consequence of a historical event**,
anchored on a person whose **stake comes from that history**" — meaningful and
interconnected *by construction*. This builds **on top of** crawler's existing
*spatial* world-gen (the overland §3a #9 / §10a zone-danger / OVERLAND.md contracts):
it adds the **causal / historical** layer (the *why*) beneath the *where*.
**Sequencing: the history path is a prerequisite milestone — it precedes the realized
emergent-thread system.** (Hybrid, as ever: **authored campaigns supply authored
history** — the shared moros lore, DESIGN §2 — while **procedural worlds generate their
own**; the §5j generator consumes whichever.) *Verify-first:* generate a history from a
seed and check the present-state threads it yields are **caused and connected**, not
random — the deep substrate; pin it on a plot before building.

**The substrate (produced by that history) — persons with *wants* + *intents* + relationships + a crisis.**
- **Wants** — each person carries a disposition/want from their **background/race**
  (§5e: a farmer wants their land safe, a merchant trade, a scholar lore).
- **Intents, NOT a script — the day-cycle is *intent*, not outcome.** crawler's NPC
  daily routines (the role cycle) state what an actor **wants to do** (work the field,
  walk the route, go home) — **never what *will* happen.** What *actually* happens is
  resolved **live by encounters**: a routine is a *plan* the world can interrupt. (A
  deterministic schedule can't emerge threads; an **intent that gets interrupted**
  can.) This generalises the intent-seam (§6) and the companion want (§5e): *everyone
  has intents; the world resolves them non-deterministically.*
- **Relationship graph** — **genealogy (parents/children) is the backbone**, with
  rival / faction / contact links layered on; the **connects-to** substrate. Kin ties
  are the **most weighted** links (the strongest stakes and the prime thread source —
  above).
- **A regional crisis-driver** — world-gen seeds a **big question** grounded in the
  §10a zone-danger model — the campaign **spine**.
- **Local events / conditions — the *shared ground* every person is tied into
  (players AND NPCs).** A region carries present **conditions**, generated from its
  history, in (at least) four families:
  - **War** (armed conflict — the war-pressure / Brumal threads);
  - **Poverty** (scarcity, hardship — the goods-economy, refugees, §5g/§3a);
  - **Restless spirits** (the spirit cosmology disturbed — chaotic/warped spirits, the
    fungus; magic runs wilder, §6.5–§6.6);
  - **Economic control** (who holds trade/resources — factions, monopolies, the
    contact-economy, §5g).
  These are the **connective ground between everyone in a region:** they **shape each
  NPC's wants/intents and threads** (a farmer in a war-zone wants safety; under
  economic control wants fair trade; amid restless spirits wants protection) **and
  they embed the *player* too** — *affected by* them (a war-zone is disrupted/lethal;
  poverty = scarce barter; restless spirits = wilder magic; economic control gates
  access/prices), *staked* through your **companions, contacts, and economy** (§5e/§5g
  — a war threatens your contacts, etc.), and *able to influence* them (the
  resolution threads — negotiate a peace, relieve poverty, calm the spirits, break a
  monopoly, via the §7 archetypes). So **player and NPCs share the region's
  conditions** — the player is *of* the world, not a detached delver. (Enriches §10a:
  a zone's "danger" is now also its *condition*.)
  - **Conditions are *dynamic* — they respond to activity (the feedback engine).**
    Via the **reactive spirit-world** (CATALOG.md §6.5): how players, NPCs, and
    **factions** extract / trade / exploit / tend **shifts the conditions** — a strip-
    mine breeds restless spirits, exploitation deepens poverty, tending a shrine eases
    the spirit-unrest. So the tie-in is **two-way**: you're *affected by* conditions
    **and** your (and others') activity *reshapes* them. Restoring a soured condition
    is itself a **thread / mission** (relationally solved, §7; costly, never a switch).
  - **ONE reactive mechanic, several *domains*, nested *scales* — a war and an
    environmental calamity are the *same* mechanic.** The reactive/unstable/opaque
    coupling (CATALOG §6.5) is **one** mechanic expressed across **domains** —
    **spirit/ecology · economy · faction/political**. So a **war** (the faction domain
    reacting: alliances shift, grudges form, conflict escalates) and an
    **environmental calamity** (the spirit domain reacting: restless spirits, the
    fungus, the spreading desert) are **two expressions of the same mechanic** — as is
    famine/poverty (economy domain). The §5j conditions (war · poverty · restless
    spirits · economic control) are therefore *the same thing in different domains* —
    which is **why they interconnect and propagate.** It runs at **three nested
    scales** — **local** (a town's factions & spirits), **country** (a crown,
    succession, the war pressure), **world** (the overseas powers, the portal, the
    artefact-buyers' fortress) — and **couples *across* domains and scales**: a war
    drives extraction → spirit calamity; a calamity → scarcity → war; an overseas war
    → country mobilisation → a local mine run harder → local spirit-disturbance →
    refugees (moros's cascade). **Factions react to activity** (yours *and* each
    other's) exactly as spirits do — not always negatively, presence felt, never
    stable or fully understood (→ the same agency, §6.5 capstone). **Steering this web
    at country/world scale *is* moros's resolution-paths** (Political · Infiltration ·
    Military · Spiritual, BRUMAL_RESOLUTIONS) — the player's high-scale agency. *The
    whole world is **one reactive web of forces — spirits + economy + factions —
    across nested scales**, governed by the single agency-giving mechanic.*
  - **Architecture — *one* data structure for the web; the *actor* differs by
    domain.** The reactive web is **built once**: a graph of **force-nodes** +
    **coupling edges** + **state** + the **activity → reaction → consequence →
    propagation** loop — the *same structure and mechanic* for spirit/ecology,
    economy, and faction/political. What **differs is *what an actor (node) is*** per
    domain: a **spirit** (strength / element / restlessness, §6.6), a **faction**
    (power / interests / ties), an **economic entity** (resources / flows / control),
    a **person** (wants / intents / lineage). Each has domain-specific attributes and
    *acts*, but **plugs into the same web** via the same edges + reaction-rules ⇒ a
    **generic reactive-coupling engine parameterised by actor-type** (the
    data-structure form of "one mechanic, several domains"). *This "actor" is a
    **distinct notion** from the combat **`Actor`** (invariant #2, pluggable control,
    the tactical layer); the two layers **overlap on persons**: a **person** is both a
    web-node and — if a combatant — a combat `Actor`; a **faction** is web-only (it
    acts at scale through members); a **spirit** can be a web-node, a combat actor (an
    elemental you fight), **or** a condition (a calamity).*

**The generator — matching.** A thread (`QuestDef`) is generated by matching a
**(person + their want/intent)** against a **(world condition + place)**: want × a
monster-nest-in-their-zone → a SLAY thread (face = the person, site = the nest);
intent-interrupted × kin-taken-to-a-dungeon → a RESCUE thread (two persons + a place);
contact-need × a resource-in-a-place → RETRIEVE. Objective types are crawler's existing
RESCUE/RETRIEVE/SLAY; the **anchor is the person**, the **site is procedural**, the
**connects-to is the relationship graph + shared crisis.**

**Interconnection + open/close.** Threads link because their persons are linked and
many point at the **same crisis**. Resolving a thread **deltas world-state** (the
person's situation, the relationship graph, the crisis level) → which **opens/closes**
others — moros's "resolve and open," driven by **world-state deltas, not authoring.**

**Branching = systemic levers.** A thread is resolvable by whatever **systems** the
world offers — combat (clear the source), magic (a ritual, the spirit cosmology),
social (ally a faction / sway a person via trust+contacts), economy (supply goods).
Multiple, partial, combinable — **emergent from which systems the player engages**,
not authored branches. A resolution needing the **party coordinated** becomes a
**tension-moment** (the §5i spine, emergent).

**The invariant (DESIGN-PROTOCOL — pin before building):** the generator must **never
emit a thread missing any of — a FACE (person-anchor), a PLACE (procedural site), a
LEVER (a systemic resolution path), a LINK (relationship/crisis connection).** Missing
any → "a task-table, not a tension moment" (moros's own warning). Contract:
*(person-want/intent × world-condition × place × systemic-lever × relationship-link) →
QuestDef.*

**The hard part + the hybrid.** Procedural *narrative coherence* is the risk —
generated threads can read random ("kill 10 rats") rather than meaningful. Mitigations:
the **person-anchor + want** give every thread a *face with a reason* (face-first,
generated); the **relationship graph + crisis** force interconnection; **layered
places** concentrate meaning. But the *emotional weight* of an authored face (Irna at
the gate) is hard to match procedurally — so, as with companions and missions, go
**hybrid: procedural threads as the emergent baseline (the living everyday web) +
authored campaign packs (§5i) as seeded standouts** in the same `QuestDef` graph.

**Verify-first (cheapest medium):** generate a campaign from a seed (persons +
relationships + a crisis) and **read off the thread-web** against the moros template —
every thread person-anchored? threads interconnect? multiple resolution paths? does
resolving one shift others? Plot one worked seed and eyeball it vs a moros campaign
**before** building the generator. (This is a load-bearing generative system — pin it
on the plot, don't guess.)

## 6. The intent-seam extension (`gameflow`)

Today: `S <seed> <depth>` · `T <fwd> <turn>` · `A <kind> <a1> <a2>` (all implicitly
"the one player"). The co-op extension keeps the codec shape and adds:

- an **actor-id** dimension so a tick/action names *which* actor it drives (the
  host applies + broadcasts identically; replicas replay — unchanged contract);
- a **call** intent — a *strong target mark* (`target`, `priority`), a **broadcast**
  others opt into (§5b); it sets no one's action — it *invites*. (An *attack* on a
  target is an **implicit call** — the front fighter's swing already names a target,
  so it doubles as the mark; no separate intent needed, §5b.)
- a **directive** intent kind — *set goal* (`actor`, `goal`, `arg`) and *play
  card* (`actor`, `card`, `target`), the latter being *set-goal + modifier +
  Tension delta* in one wire line. **Joining a call is an actor's *own* action
  intent** (it acts on the marked target); the Tension delta lands when the join
  is a coordination act (§5b) — so Tension is emergent from who joins, exactly the
  same whether the actor is AI- or human-driven.

This is purely additive to the wire format; `wire3`-style parsing generalizes.
The directive intent is the single chokepoint where coordination, goals, and
Tension meet — keep it the only place Tension rises (invariant #3).

## 7. Open design points (pin before the phase that needs them)

- **The Tension curve (verify-first, cheapest medium).** Threshold (moros uses 5),
  the per-source increments (aid vs limit-breaker vs special opportunity — §2b),
  decay rate, and the size of the coordination modifier vs the escalation penalty.
  Prototype the loop over a *scripted* fight (throwaway Python or a tiny loft sim)
  and confirm the §2 *party* drama emerges at the chosen numbers **before** wiring
  it into `sim` — and that **solo** stays calm while *focused* and climbs when
  *spread* across fronts (§2b). This is the exact-invariant step the design protocol
  demands — pin the curve, don't guess it.
- **The group limit-breaker & special-opportunity vocabulary (§2b).** What counts
  as a (predominantly *group*) limit-breaker / party special opportunity (a
  combined burst into an opened window, a party combo) — the above-baseline *group*
  acts that raise Tension — plus the rare *solo* limit-breaker exception. Authored
  bundle-side where possible (BUNDLE.md).
- **What a "card" maps to.** Deck construction from party abilities + moros's
  element cards (Flame/Water/…); how the hand refreshes; whether cards are purely
  directives or also gate the bigger specials. Ties to moros `data.js` for flavor.
- **The "scene/locality" boundary for Tension reset** — inherits the §11a open
  question (room/layer → distance radius) and the locality-merge-on-convergence
  case. Tension is per-locality, so it forks/merges with the locality clock.
- **Downed model — RESOLVED (§5d): the Broken-spirit state.** HP attrition → Broken
  (out of action, recoverable); actual death only via an enemy's deliberate
  *execute* of a Broken character → §3a stake. (Remaining: the monster-symmetry
  question, §5d open.)
- **Aid eligibility** — moros forbids aid beyond adjacent tiles ("the tension
  mechanic cannot model a party that cannot reach each other"). Mirror that: a
  card-to-ally requires the ally within a coordination radius.
- **Attention-draw / moros powers integration (§5b).** Port the **moros powers
  system's attention-draw** as a per-power property that pulls enemies (opens
  fronts → feeds the §2b spread/Tension currency) and is one input to an actor's
  *join-or-decline* decision. Open: the attention→aggro/spawn mapping, how it reads
  on the view (a draws-attention cue), and how it ties to the capability catalog
  (RESOLUTION.md §5a) where powers are authored.

## 8. Phasing & tests (mirrors §10a / §12 phasing; each phase = one headless test)

- **C1 — Allies exist (AI-only; no cards, no Tension).** Actor `faction`; a basic
  ally that follows the hero and engages the nearest monster via existing
  flow-field; targeting/damage respect faction. *Minimum playable party.*
  → `partytest`: ally fights monsters, never the hero; follows; survives.
- **C2 — Goals.** The goal model + minimal goal-issue input; allies obey
  follow/hold/focus/retreat/guard. → `partytest` extended: issuing a goal changes
  ally behavior deterministically.
- **C3 — Tension scalar.** Sources = *above-baseline* acts (aid · limit-breaker ·
  special opportunity, §2b), sink (rest), threshold escalation hook; per-locality
  scalar. → `tensiontest`: scripted source/rest → pinned Tension (invariant #3);
  crossing the threshold fires the escalation; **a solo run stays low when focused
  but climbs when spread** (multi-target / surrounded) — the §2b group-shaped-load
  check.
- **C4 — Cards as UI.** The hand overlay; card-play emits the C2 directive + C3
  aid in one gesture, with visuals + the Tension meter. → test: card play emits
  **byte-identical intents** to the raw directive (cards are skin — invariant #1).
- **C5 — Dynamic control handoff.** Actor-id on the wire; AI policy as one intent
  producer; a second client binds to an actor; controller-leave → AI resumes.
  → extend `replaytest` to a party (invariant #4): host/replica bit-identical;
  hand off control mid-fight, determinism holds.

C1–C2 are mostly engineering on existing rails (faction + goals over §10a AI).
C3 is the novel design (the Tension curve, §7). C4 is a UI projection. C5 turns
the already-MP-shaped seam into live drop-in. Build in order; each ships a green
headless test and stays warning-clean (CLAUDE.md).
