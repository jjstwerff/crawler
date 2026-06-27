# RESOLUTION.md — pluggable resolution & non-trivializing progression

The character-rules *core* beneath PARTY.md: **keep Angband's combat/skill
systems, but make the random-resolution scheme swappable** (2d6 vs 1d10 vs d20…)
for experimentation — and design progression so **a +1 (stat / skill /
specialization) is meaningful yet never trivializes enemies** (the D&D accuracy
treadmill we explicitly want to avoid). Companion to PARTY.md (whose invariant #1
says *all combat goes through the unchanged kernel* — this doc defines that
kernel's flexibility and curve). Extends DESIGN.md §3a (friendly tuning),
§10a (combat), §12a (Angband levelling). Blueprint-shaped per DESIGN-PROTOCOL.

## 1. The two requirements

- **R1 — pluggable resolution.** Angband math is the default and nothing breaks,
  but the *random distribution* a check rolls on is a config-swappable backend
  (`d20`, `2d6`, `3d6`, `d100`, dice pool…) so we can experiment with feel.
- **R2 — meaningful but bounded +1.** Each +1 should *matter* (felt progress) yet
  must **not** push success toward certainty / make earlier content trivial — and
  must not force the DM-treadmill of inflating enemy numbers to compensate.
- **R3 — no number is a gate (the Dark-Souls model).** It must **never** be
  *impossible* to succeed merely because you lack a +N. A fresh level-1 character
  can, with skill, beat the end boss. Numbers tilt odds and widen options; **skill
  is the real gate.** (Governing principle — §2a.)

## 2. The hinge: R1 and R2 are the same lever

The **resolution distribution is the primary control on what a +1 is worth.**

- **Uniform `d20`** (Angband/D&D): +1 is a flat **+5% everywhere**. Accumulated
  modifiers march success toward 100% → weak content auto-resolves → the
  treadmill. This *is* the problem the user named.
- **Bell curve (`2d6`/`3d6`, GURPS/PbtA-style):** +1 is **large where the outcome
  is contested** (near parity) and **vanishingly small at the tails**. You
  *cannot* push a contested check to certainty, and dumping +N past dominance buys
  almost nothing. The curve **structurally bounds trivialization.**

So R1's swappable distribution is the main tool for R2. Choosing a bell backend
is not just "different dice" — it is the anti-treadmill mechanism.

## 2a. Governing principle — no number is a gate (the Dark-Souls model)

**R3, and it overrides the rest where they conflict:** outcomes are never
*impossible* for want of a +N. Character numbers **tilt the odds and widen
options; they never decide the result.** The real gate is **skill** —
positioning, timing, terrain/FOV use, target priority, resource & Tension play,
knowing when to retreat. This is the explicit rejection of Angband's stat/gear
wall (where a weak character genuinely *cannot* beat the deep boss) for a
Souls-like *execution beats stats*. **A +3 makes a fight easier; it is never what
makes it possible.**

Two hard consequences:

1. **No structural 0% / 100% on any roll.** A bounded bell (`3d6`) auto-fails once
   difficulty outruns skill — **forbidden** (it *is* the wall R3 bans). The
   resolver guarantees a **floor and a ceiling**: every check keeps a puncher's
   chance and is never a certainty (an always-possible max-roll / a min-success
   clamp — e.g. open-ended dice, or a nat-max-always-hits rule). This is a hard
   constraint on the R1 backend (§4 invariant 5), and it refines §2: the bell
   shapes the *middle*, the clamp guarantees the *ends* never close.
2. **Execution can substitute for stats.** The dominant survival lever is
   **mitigating / repositioning** — not being adjacent, breaking LOS, using walls
   and chokes, interrupting, kiting on the distance clock, spending coordination/
   Tension well (PARTY.md) — so a single roll never decides a fight: you don't
   out-stat the boss, you mitigate and **chip it down**. This demands the combat
   layer carry **enough execution depth** that skill *can* overcome a stat deficit
   (positioning/terrain/timing matter, not only the roll) — a real requirement on
   §10a combat, and a deliberate departure from vanilla Angband (flagged §6).

**Combat resolution — two channels (the concrete shape of R3 in a fight).** This
is where the no-gate guarantee actually lives:

- **Damage channel (primary, always-progresses).** Every blow **connects** and
  does **≥1 damage** — there is no whiff. The StS undercurrent (PARTY.md §5a)
  **biases the *damage* roll**: mitigation shrinks it toward (never to) zero,
  Vulnerable/stacks push it up. Against a well-guarded foe you do **little but
  never *no* damage** — the Dark-Souls chip. Gear/mitigation sets how *slow*, never
  *whether*. This is the cleanest realization of R3. *(And HP bottoming out doesn't
  kill — it **Breaks the spirit**: out of action, recoverable; actual death needs an
  enemy's deliberate execute. PARTY.md §5d.)*
- **To-hit channel (repurposed — a *crit engine*, not hit/miss).** The Angband
  to-hit math (skill vs AC, the roll) is **kept**, but it no longer gates landing —
  it decides **crits / degree-of-success** layered on top of the guaranteed hit,
  and it is **two-tailed**: a strong roll → a **crit** (strips the *target's*
  mitigation, opening a window); a weak roll → a **fumble** (exposes the *acting
  actor* — self-vulnerability the party must cover, +Tension). So **AC and to-hit
  skill still matter** (they shift both tails) but can never reduce you to *no*
  progress — neither tail gates landing. This **settles the AC question** (§6): AC survives as a
  crit-engine input, not a wall. (The bell's `margin`, §9, is the natural crit
  signal.) **The two channels couple at one pinned point (two-tailed): a crit
  *strips the target's mitigation* and a fumble *exposes the acting actor*** (PARTY.md
  §5a) — the crit roll is *how you crack a guard*, the fumble *how you leave one
  open* for the party to cover. Coupled, yet the chip floor (≥1) means neither tail
  is ever *required* or unrecoverable — R3 holds.

**One philosophy now:** numbers tilt and open options (breadth, §5a); the bell
keeps tilts inside the contested band (§2); the Dark-Souls clamp + execution depth
guarantee the **skill path is always open**. Breadth, bounded math, and "no gate"
are three faces of the same rule — *progress changes how you play, not whether you
can.*

## 3. Concrete plotted end-result (pin before code)

For each candidate backend, plot **P(success) vs (skill − difficulty)** and the
**marginal value of a +1** across that range. Target shape:

| Situation (skill − difficulty) | a +1 should swing P(success) by |
|---|---|
| near parity (contested)        | ~**10–15%** — *clearly meaningful* |
| already dominating             | ~**0–2%** — *can't trivialize*     |
| hopeless underdog              | ~**0–2%** — *small, but never 0* (R3) |

A `3d6`/`2d6` bell hits the *middle* shape; flat `d20` does not (~5% everywhere,
including where it shouldn't be). But a raw bell **fails R3 at the tails** (it
hits literal 0%/100%), so the chosen backend must **clamp the ends to a non-zero
floor and a sub-100% ceiling** (§2a) — the underdog row floors at, say, ~1–2%, the
dominator ceiling caps below certainty. **Pin this curve *including the clamped
tails*, pick the backend + clamp that produce it (cheapest medium: a Python plot
of each distribution), then port.** Choose the curve by plotting the *answer*, not
by guessing.

## 4. Invariants

1. **Single resolution chokepoint.** Every contested outcome — to-hit, save,
   skill use, device activation — goes through one seam:
   `resolve(skill_total, difficulty, kind) -> {hit, margin, crit}`. The backend
   (distribution + its scaling) lives *behind* that seam; swapping it touches
   **zero call-sites**. (DESIGN-PROTOCOL exact seam; enforced at the chokepoint,
   no wider.)
2. **Determinism.** Resolution draws from a **seeded, quantized** PRNG, replicated
   bit-identically (ties PARTY.md invariant #4 / `replaytest`). No wall-clock, no
   float drift in the roll.
3. **+1 is breadth-first — DECIDED: the moros way.** Progression's primary unit is
   a **new capability** (a power / background / specialization = a new *verb or
   tactic*), **not** raw +N to existing stats. Raw stat height is **capped with
   diminishing returns**; most of what a level buys is *a new thing you can do*.
   This is settled (not an either/or with "big numbers bounded by the bell") — see
   §5a for the concrete model.
4. **Threat ≠ numbers.** A weak enemy stays relevant through its **mechanic**
   (gaze / poison / breeding / numbers), never its to-hit — so high accuracy can
   never make content trivial. (Already the CLAUDE.md content rule: a monster
   keeps its true mechanic.)
5. **No-gate clamp (R3 / §2a).** Every resolved check keeps `P(success) ∈ (floor,
   ceiling)` with `floor > 0` and `ceiling < 1` — **no roll is ever a structural
   0% or 100%.** A puncher's chance always exists; certainty never does. *Verify:*
   a `puncher` test sweeps skill−difficulty across its whole range and asserts the
   bound holds at both extremes (including absurd mismatches).

## 5. The anti-trivialization design (R2) — levers, stacked

No single trick; they reinforce:

1. **Bell-curve resolution** (R1, §2) — bounds win-rate; +1 can't reach certainty.
2. **Breadth > height** (invariant #3, **the chosen spine** — §5a) — a +1 into a
   *new* capability unlocks *doing a new thing* (a new action/tactic), which is
   felt progress **without** moving the win-rate against existing enemies. A +1
   into an *existing* stat has diminishing returns + a soft cap. This is the core
   reconciliation of "meaningful **and** non-trivializing": make most progress
   **qualitative**, not a bigger number.
3. **Contested/relative resolution** — resolve against the enemy's *scaling*
   defense, so +1 is a relative edge; the bell keeps that edge from ever becoming
   certainty, and breadth keeps progress felt as *new options*, not a moving
   target that erases the sense of getting stronger.
4. **Mechanics-as-threat** (invariant #4) — weak monsters keep dangerous
   mechanics, so they never trivialize regardless of your accuracy.
5. **Flatter HP/damage curve than Angband** (§3a licenses curve deviation —
   numbers, not mechanics). Keep HP, but flatten the balloon so a +1 damage stays
   meaningful (kills a beat sooner) **and** enemies stay lethal (no "two bags of
   HP" non-fight). *(moros goes to the extreme — no HP, attacks reduce stats
   directly; recorded as the far end of this axis, but we keep HP.)*
6. **Gear buys ceiling, not flat power (the anti-gate gear model).** Armor/weapons
   raise the **soft ceiling** of the Slay-the-Spire mitigation/stacking pools
   (PARTY.md §5a) — how much mitigation you can hold, how high you can stack damage —
   **not** a flat reduction or bonus. *Gear widens headroom; skilled play fills
   it.* So gear is never a gate (R3): poor gear + great play is capped-but-viable,
   great gear + bad play stays empty. Same anti-treadmill shape as breadth-over-
   height. *(Reinterprets Angband armor from flat AC toward a mitigation-ceiling —
   a deliberate gear-model departure, flagged §6.)*

## 5a. Progression model — "the moros way" (DECIDED)

Crawler advancement becomes a **tree/pool of learnable capabilities**, not a
class-bound stat ladder. Adapted from moros's model (RULES.md § Progression),
kept compatible with Angband *combat*:

- **The unit of growth is a capability** — a **power** (innate/racial ability), a
  **background** (a learned role that opens item slots + specializations), or a
  **specialization** (a trained skill, tied to one governing stat, requires a
  supporting background). Learning one **grants a new action/tactic** and a small
  **+1 to one of its two linked stats**.
- **Breadth is enforced, à la moros:** early picks are cheap (the "first 6 free"
  shape), then XP cost climbs; **a single stat can't be raised past a soft cap**
  (moros: "no stat raised >3 times early"); and you **can't repeat a type
  consecutively** (power → background → specialization → …) so growth stays broad.
- **Raw stat height is capped + diminishing** (invariant #3 / §5 lever 2) — the
  numbers stay in the bell's contested band (§3) where a +1 still *matters* but
  never reaches certainty. Height tops out; breadth doesn't.
- **Race is the primary *playstyle* definer — moros's biggest upside.** *Not* a
  stat tilt (Angband's +1 STR / infravision / hit-die mod, which barely changes how
  you play) but a **distinctive set of innate powers / capabilities that change how
  you *play***: flight, digging, climb, smell-tracking, night-sight, charge, hide
  (moros: a **Boar folk** digs/smells/charges; an **Owl** flies/scouts/claws). Those
  innate powers **seed your starting cards** (PARTY.md §5/§5a), so race shapes your
  tactics and coordination **from turn one** — a flyer, a tunneler, and a tracker
  play *genuinely differently*, not just with different numbers. **Deep in
  *playstyle*, shallow in *engine*:** each race is a different *selection* from the
  shared capability pool, authored **bundle-side** (BUNDLE.md) — **no bespoke
  per-race code**, which keeps §3a #4's "no deep per-class mechanics" intent while
  delivering deep per-race *feel*. This is the single richest thing crawler takes
  from moros. **Drafted in CATALOG.md** (16 races + their innate power sets + the
  capability pool, seeded from moros `data.js`).
- **Class becomes a starting package, not a ladder.** crawler's existing `ClassDef`
  (bundle-side) is reinterpreted as an opening **background + a few seeded
  capabilities**, not a fixed per-level stat track. (Authoring moves bundle-side,
  BUNDLE.md seam — content-side, mechanism engine-side.)
- **Spells & skills are capabilities — the casting *economy* is replaced.** Angband's
  SP pool, fail-rate, spell-levels, and learn-from-books are *advancement economy*,
  so they moros-ize: a spell is a **card** costing the **action** (+ Tension if it's
  a coordination/big play), **gated by stat + mastery, not a fail-roll** — no SP, no
  whiff. Spell *effects* are preserved as capabilities; the realms → the Will
  specializations. Full mapping of Angband's indirect layer (skills + utility spells)
  and the gaps that instead belong in `itemfx` (teleport, recall, identify): **CATALOG.md §6.**

**The unification with PARTY.md:** a character's **learned capability set *is*
their card deck.** Every power/background/specialization (and item) projects a
**card** into the party hand — so progression (this doc) and the coordination/
Tension card UI (PARTY.md §5) are the *same data* seen two ways: what you've
*learned* is exactly what you can *play* to coordinate. Growing the party's
breadth grows the hand. This is why "breadth over height" and the card layer
reinforce each other rather than being two separate systems.

## 6. Relationship to Angband & moros (charter check)

- **Angband (kept):** the *systems* — to-hit vs AC, saves, skill mods, blow dice —
  are reproduced faithfully (§3a). The resolution backend **defaults to Angband's
  `d20`-ish math** so the existing game is unchanged; alternate backends are an
  **experiment behind config**, not the default until validated.
- **moros (borrowed philosophy only):** the **progression shape** (broad, slow,
  capability-unlocks over raw numbers) and optionally its typed/element model. Not
  its card resolution (PARTY.md §1). The card *UI* nods to the shared world; the
  math stays Angband.
- **§3a friendly tuning** already permits deviating the *curve* (curve / death /
  class-weight — numbers), not the mechanics. A bell-curve resolver + flatter HP
  sit squarely inside that allowance; names/mechanics stay clean-room.
- **Honest charter flag — the progression model is a *structural* departure, not
  a tuning.** Replacing Angband's class-bound per-level stat ladder with a
  moros-style **capability tree** (§5a) goes beyond §3a's "numbers, not mechanics"
  license. We do it deliberately, and the line we hold is: **Angband *combat*
  systems are kept faithfully** (to-hit vs AC, saves, blow dice, HP) — it is the
  **advancement model** that goes the moros way. **Recorded** in the DESIGN §3a
  amendment (2026-06-27) + the §12a "Levelling" note, so the charter reflects the
  decision rather than being silently contradicted.
- **Second structural departure — the Dark-Souls difficulty model (§2a / R3).**
  Vanilla Angband *is* a stat/gear wall: a weak character cannot beat deep content,
  full stop. We reject that — no number is a gate, skill is. This needs (a) the
  no-gate clamp on resolution and (b) **enough execution depth in §10a combat that
  positioning/timing/terrain/coordination can overcome a stat deficit.** (b) is the
  larger ask: it pushes crawler's combat toward action-game execution (which the
  continuous-glide/heading/FOV model, §10/§12, already partly affords) and away
  from Angband's roll-dominated melee. **Recorded** in the DESIGN §3a amendment
  (2026-06-27).
- **Third structural departure — gear as a mitigation/stack *ceiling*, and to-hit
  repurposed as a crit engine (§2a two-channel model / §5 lever 6 / PARTY.md §5a).**
  Two linked shifts: (1) armor stops being a flat to-hit/damage reducer and becomes
  the soft cap on the StS mitigation/stack *tilt*; (2) **the Angband to-hit roll is
  kept but no longer gates landing — it becomes the crit/degree-of-success engine**,
  while the *damage* roll (always ≥1) carries the no-gate floor. **AC survives** as
  a crit-engine input. This is the larger combat-model departure from vanilla
  Angband (no whiffs; damage, not hit-chance, is the lever). **Recorded** in the
  DESIGN §3a amendment (2026-06-27).

## 7. Pluggable backend shape

- A **`Resolver` config**: `kind` (distribution) + params. Backends: `D20`
  (Angband default), `B2D6`, `B3D6`, `D100`, `POOL`. Each implements
  `resolve(skill_total, target, kind) -> {hit, margin, crit}`.
- **Scaling is the backend's job.** The kernel speaks in abstract *skill points*;
  each backend maps a skill delta into its own units (a +1 in `d20`-space maps to
  the backend's equivalent in `2d6`-space), so changing distribution doesn't
  require re-tuning every monster. The seam owns that conversion.
- **Verify-first:** prototype each backend in Python, plot §3's curves, choose.
  Only then port the chosen default into loft, keeping the others behind config.

## 8. Phasing & tests (each ships a headless `*test.loft`, warning-clean)

- **R0 — extract the chokepoint.** Route *all* current to-hit/save/skill/device
  checks through one `resolve()` with the existing Angband-`d20` math as the only
  backend. A **behavior-preserving refactor** — follow the loft-codegen discipline
  (prove emitted IR / outputs identical before vs after). → `resolvetest`: same
  seed → byte-identical outcomes to pre-refactor.
- **R1 — alternate backends + the no-gate clamp.** Add `B2D6`/`B3D6`/`D100` behind
  config with the §2a floor/ceiling clamp baked into the seam; the prototype's
  chosen curve becomes selectable. → distribution test: each backend's empirical
  P(success) over many seeds matches the plotted §3 target; **+ the `puncher` test
  (invariant #5): no skill−difficulty value yields 0% or 100%, at any extreme.**
- **R-exec — execution depth (§2a consequence 2).** Audit §10a combat for whether
  positioning/terrain/timing/coordination can actually overcome a stat deficit; add
  the missing execution levers so skill *can* substitute for numbers. → a **skill-
  beats-stats test**: a scripted low-stat-but-well-played run survives content that
  a stat-only policy loses (the headless "Borg"-style policy, §10a tier 3).
- **R2 — the capability tree (§5a).** Implement progression as learnable
  capabilities (power/background/specialization) with the breadth rules
  (cheap-then-climbing cost, no-repeat-type, soft cap on raw stat height), reframe
  `ClassDef` as a starting package, and flatten the HP/damage curve. The learned
  set is the card deck (PARTY.md). → a **trivialization stats test**
  (`main-stats`-style, §10a tier 2): after K levels, win-rate vs early enemies
  *rises but stays under a ceiling*, those enemies *remain able to deal damage*,
  and acquired **capabilities** outweigh raw +N in measured power.

## 9. Open points

- The exact target curve numbers (§3) and which bell backend (`2d6` vs `3d6`)
  becomes the *recommended* experiment default — settle on the Python plots.
- The diminishing-returns/soft-cap formula for raw stat height (a curve, a hard
  cap, or rising XP cost à la moros's "no stat raised >3 times early").
- The capability catalog itself (§5a): which powers/backgrounds/specializations
  exist, their linked stats, and the action/tactic each unlocks — authored
  bundle-side (BUNDLE.md). **Initial draft: CATALOG.md** (seeded from moros
  `data.js` — 37 powers by combat role, 16 races, 14 backgrounds, specializations,
  the 8 element cards). Its gating open call is the **6-vs-8 stat-set decision**
  (CATALOG.md §0) — settle that first.
- **DECIDED & PINNED:** the to-hit roll is the **two-tailed crit engine** (§2a) —
  a **crit strips the *target's* mitigation** (+ damage bonus), a **fumble exposes
  the *acting actor*** (self-vulnerability the party covers, +Tension). The pinned
  coupling of the two channels (PARTY.md §5a). To-hit skill = guard-cracking *rate*
  / fumble-avoidance; the damage roll (≥1) keeps the no-gate floor; neither tail
  gates or whiffs. Remaining detail: the `ΔM`-per-crit-margin curve, the fumble
  self-exposure magnitude, the crit/fumble-rate curve, and mitigation **regen**
  rate.
- Where the `Resolver` config lives (per-world? a bundle-selectable ruleset?) —
  keep it engine-side mechanism, content-side selection (BUNDLE.md seam).
