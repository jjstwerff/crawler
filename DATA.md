# DATA.md — world-state & world-data model (current → needed)

Maps crawler's **current** data structures against what the moros-flavored design
(PARTY.md · RESOLUTION.md · CATALOG.md) **needs**, on two axes:
- **World-DATA** — static / authored content (bundle-side defs).
- **World-STATE** — mutable runtime state.

Each item tagged **✅ exists** · **◑ extend** · **★ net-new**. Design-only (no code);
flags the §11b/loft#320 and determinism constraints that gate the build.

## 1. Executive summary — the shape of the change

**Current.** One `Sim` struct (`src/sim.loft`) holds the level + *the one player* (≈20
flat fields) + a `vector<Enemy>`. Static content is **keyed catalog defs**
(`MonsterDef`/`RaceDef`/`ClassDef`/`ItemDef`/`Stencil`/`Placement`) merged engine+bundle
by **key→index**, with **behaviour dispatched by routine-id** (`monster_act`/`item_use`/
`quest_check`/…). World-gen emits `GenLevel`/`Overland`. **This architecture is strong
and already library-like.**

**The design adds:** (a) a unified **Actor** + a **per-actor roster** (companions); (b)
a **capability/card** layer; (c) the **8-stat** swap; (d) the **goods economy** (drop
gold); (e) the **Slay-the-Spire combat layer** (mitigation/stacks/Broken); (f) the
**reactive-web** (spirits/factions/economy/persons as typed nodes + conditions + Tension
+ locality); (g) **missions** (QuestDef → the generic format) + **threads**; (h) the
**history-gen** + **persons/genealogy/trust**; (i) the **LOD** (faces = entries, stayers
= aggregate).

**Two findings dominate:**
1. **Most new world-DATA is *additive to the existing pools*** — new defs slot into the
   same keyed-catalog + key→index + routine-by-id pattern. Little new *architecture*,
   mostly new *pools and fields*.
2. **Two genuinely structural STATE moves:** the **per-actor migration** (§11b — already
   a planned, deferred refactor; the companion roster now *triggers* it) and the
   **reactive-web graph** (the one net-new architecture — the strategic layer). The
   **hotbar** (`qs` quick-slots) and **intent-wire** (`gameflow` S/T/A) seams already
   exist and carry the card layer + MP/replay.

## 2. World-DATA (static / authored / bundle-side)

| Def | Current | Needed | Tag |
|---|---|---|---|
| **Stat model** | 6 (STR/INT/WIS/DEX/CON/CHR) across all defs + `stat_*` arrays | **8** (Char/Dex/Endu/Hand/Might/Perc/Speed/Will) — CATALOG §0 | ◑ (ripples widely; mechanical) |
| **MonsterDef** (`monsters.loft`) | m_hp/ac/speed/dam/vision/xp/flags/habitat/tags | + **spirit-strength** (the §6.6 `S` *and* §5d Break-gate), **mitigation-ceiling + guard/window pattern**, **faction**, typed attacks (damage-type) | ◑ |
| **RaceDef** (`races.loft`, now bundle) | 6 stat-mods, skill-mods, r_flags, r_infra | race → **innate capability keys** (powers); 8-stat seeds; skill-mods recede (capabilities replace) — CATALOG §2 | ◑ |
| **ClassDef** → **BackgroundDef** (bundle) | c_hd/c_xp, 6 stat-mods, skill-mods, realm, spell-stat | reinterpret as a **starting package**: stat pair · starting **kit** (item keys) · **item-slots** · seeded **specialization keys** · **contact keys** — CATALOG §3 | ◑ |
| **ItemDef** (`items.loft`) | i_cost (**gold**), i_weight, i_dd/ds/ac/power, i_flags, mystery (known/flavour) | **`i_cost` → barter-value + bulk** (drop gold); **passive-aid props** (control / variance-narrow / +ceiling / attunement — for runes/tattoos/amulets/rings/potions, CATALOG §6.7); gear → **mitigation-ceiling + stack-ceiling**; **reagent** flag (ritual inputs) | ◑ |
| **CapabilityDef** | — (the empty `race_table`/`class_table` hint at it) | ★ power / background / specialization: key · type · **2 linked stats** · the **card** it generates · combat-role + effect (CATALOG §1 taxonomy) · **mastery** · **overwhelmed** clause (magic) · `requires` (spec ← background) | ★ |
| **CardDef** | `qs` quick-slots exist (the bind seam) | ★ a card = a capability/element **projection**: source · the **directive/effect** it emits · **Tension delta** · hotbar-bindable (PARTY §5/§5a) | ★ (mostly derived) |
| **Element defs** | — | ★ the **8 elements** (2 stats + damage-type) — CATALOG §5 | ★ |
| **SpiritDef / ElementalDef** | — | ★ spirit kinds (element · **strength tiers** · the natural-force map fire=volcano… · **attention-draw** · overwhelmed) — CATALOG §6.5 | ★ |
| **ConditionDef** | — | ★ the local-event families (**war · poverty · restless-spirits · economic-control**): state range · escalation thresholds · reaction-rules · the threshold-hostile hook (PARTY §5j) | ★ |
| **QuestDef** → **generic mission format** (BUNDLE.md, *planned*) | planned: q_key/q_kind/target/goal_placement/requirements/rewards/routine_ids | + **face** (person-anchor) · **archetype** (16) · **levers[]** · **links[]** · **stake/delta** · **partial-resolution** · **scope** · **coordination-flag** — CATALOG §7 | ◑ |
| **Archetype completion-checks** (`quest_check` routines) | RESCUE / RETRIEVE / SLAY (3) | + the other **13 archetypes** (BEFRIEND/NEGOTIATE/CONSENT/CURE/REPAIR/RITUAL/…) — CATALOG §7 open | ◑ |
| **ResolverConfig** | combat rolls via `rs1/rs2` RandStream | ★ distribution kind + params + **no-gate clamp** (RESOLUTION §7) | ★ |
| **History-gen templates** | `world_key_seed` (place gen) | ★ event / figure / migration / binding templates + the **displacement registers** (the legends-gen seed vocabulary — PARTY §5j) | ★ |
| **CampaignBundle** | bundle system ✅ | ◑ Background + **thread-web** (QuestDef graph) + tension-moment missions + NPC-signpost + branching — the §5i template, authored on the extended QuestDef + person/face defs | ◑ |
| **Bundle / catalog / routine architecture** | merge-by-key, key→index, routine-by-id, the two seams | the **same pattern absorbs all the above** — add pools (capabilities/spirits/conditions/elements), extend defs, add routine arms | ✅ (the big enabler) |

## 3. World-STATE (mutable / runtime)

| State | Current | Needed | Tag |
|---|---|---|---|
| **Actor** (unified) | split: `Player` (flat on Sim: clevel/xp/gold + stat_*/eq/inv/php…) + `Enemy` (cur_q/r, hp, dam, ac, speed, energy, awake, status, faction-less `role`) | **converge**: 8-stat layers · **learned capabilities** · **passive-aids** · hp · **faction** · location · **control-source** (AI\|local\|remote). Faces also: **wants/intents · lineage(parents/children) · trust · relationships · arc-state · displacement** | ◑/★ |
| **Per-actor roster** | single player (flat); §11b deferred | ★ `vector<Actor>` — player + companions, each a full Actor. **The companion roster triggers the §11b migration** (gated **loft#320**; seam is MP-shaped → internal, zero call-site) | ★ (gated) |
| **Combat (StS) layer** | status timers (para/poison/stun ✅), `wdam`/`pac` cache, `rs1/rs2` RNG | + per-actor **mitigation pool** (transient/decaying) · **stacks** (per-target Vulnerable/Weak/Poison/Strength + expiry) · **Broken** state · two-channel resolver (extend `rs1/rs2`) — PARTY §5a/§5d, RESOLUTION §2a | ◑/★ |
| **Card hand** | `qs` quick-slots ✅ + `A 3`/`A 5` intents ✅ | ◑ per-actor hotbar **projecting learned capabilities**; the hand state. *The bind seam already exists.* | ◑ |
| **Tension** | — | ★ **per-locality scalar** + a source/sink log (replay-determinism) — PARTY §2b/§3 | ★ |
| **Conditions** | — | ★ per-region levels (the 4 families) · dynamic (respond to activity) · threshold-hostile state — PARTY §5j | ★ |
| **Locality** | the distance clock (`accrued`/`ticks` ✅) is single-mover | ★ the **locality partition** + per-locality clock/Tension — §11a (unbuilt; gates Tension reset) | ★ (gated) |
| **Economy** | `Player.gold` ✅, `fi_gold` ✅, `inv`/`eq` slots ✅ | ◑ **goods = slots + bulk**; **contact relationships** (leveled, per-contact); **drop gold** (gold/fi_gold/grave_gold → goods); the **goods-grave** (grave_* → goods) — PARTY §5g, DESIGN §3a amendment | ◑/★ |
| **Reactive-web graph** | — | ★★ **the one net-new architecture**: typed **force-nodes** (spirit\|faction\|economy\|person) + **coupling edges** + per-node state (incl. **location**) + the **activity→reaction→consequence→propagation** loop = the §5j *generic reactive-coupling engine parameterised by actor-type*. The strategic layer | ★★ |
| **Mission / thread state** | two hardcoded flags (`q_poster`, `q_mage`), `boss_slain` | ◑/★ generalize to **QuestDef-instance** state + the **thread-web graph** (links open/resolved) + face-bindings + world-state deltas — PARTY §5h–§5j | ◑/★ |
| **History** | `world_key_seed` (deterministic place gen ✅) | ★ the generated **past** (events/figures/**migrations/lineages**) — produced *once*, then **seeds** persons/conditions/places/faction-graph; a backstory record + the derived initial node-states (a new *gen domain*, like GenLevel but at the figure/event layer) — PARTY §5j | ★ |
| **Geography** | `win_x/win_y` window ✅, dead-spawn delta `dd_idx/dd_n` ✅, persisted-levels *planned* (§10a) | ◑/★ places (settlements/dungeons/towers/zones) with **location** → **relocation under pressure** (PARTY §5j mobility); the full persisted-levels store | ◑/★ |
| **Stayer aggregate** | civilian NPCs are **individual** `Enemy` records (role + day-schedule ✅) | ★ the **stayer mass = aggregate** (settlement **population** · faction **membership**) — *not* nodes; the **gossip/economy/rumour** feeds; **promotion-to-node on significance** (PARTY §5j LOD). *Reframe the per-instance civilians toward aggregate + on-demand instances* | ★ |
| **Serialization scope** | checkpoint `{depth, position, stats, inventory, seed}` + grave + anchors; `gameflow` S/T/A wire ✅ | ◑ grows to capture **roster · trust · conditions · thread-state · web-node-state · history**; MP replica (S/T/A ✅) must stay **bit-identical** → web/Tension/conditions/AI as **seeded + quantized integer** state (`rs1/rs2` is the model) | ◑/★ |

## 4. Key architectural findings, decisions & risks

1. **The existing bundle/catalog/routine architecture absorbs most new world-DATA
   generically.** New defs (Capability/Spirit/Condition/Element, the extended QuestDef)
   are "add a pool + extend a def + add a routine-arm" — *no new architecture*. This is
   the single biggest de-risking fact.
2. **Two seams already exist for the card/MP layers.** The **hotbar** (`qs` quick-slots
   + `A 3`/`A 5` intents) carries the card UI; the **`gameflow` S/T/A intent wire** is
   the MP/replay seam — extend with **actor-id** + the **call/directive** intents.
3. **The per-actor migration (§11b) is the load-bearing STATE refactor — and the
   companion roster *forces* it now.** `Player` flat-fields + `Enemy` → a unified
   **`Actor`** in a `vector<Actor>`. Gated on **loft#320** (verify-first the container).
   The `sim_*` primitives are MP-shaped, so it's an internal refactor with ~zero
   call-site impact (§11b's own argument).
4. **The reactive-web graph is the one genuinely net-new architecture** (the strategic
   layer). Build it as the §5j *generic reactive-coupling engine parameterised by
   actor-type*; the **LOD** (faces = nodes, stayers = aggregate, promotion-on-
   significance) is what keeps it tractable. Biggest single build.
5. **Determinism is a hard constraint, and serialization scope grows a lot.**
   Checkpoint-respawn + MP-replica-replay require the web/Tension/conditions/AI to be
   **seeded + quantized integer** state (the float-dt hazard; `rs1/rs2` RandStream-on-Sim
   is the proven model). Design the save format up front for roster/trust/conditions/
   threads/web/history — don't bolt it on.
6. **History is a *gen-phase* output, not hot state.** It runs once to produce the
   initial persons/conditions/places/faction-graph, then is read — same pattern as
   `GenLevel`/`Overland`, at the figure/event/lineage layer.
7. **Keep the two "actor" notions distinct in the data.** Combat **`Actor`** (tactical —
   the Player/Enemy convergence) vs **reactive-web node** (strategic — spirit/faction/
   economy/person). They **overlap on persons** (a person is both); don't conflate the
   structs (PARTY §5j).
8. **Gold removal is mechanical but spread** — `Player.gold`, `fi_gold`, `i_cost`,
   `grave_gold` all → goods/barter/bulk.

## 5. Build-order implication (the data dependencies)

- **Foundation:** the **8-stat swap** + the **unified `Actor` struct** (gated loft#320 →
  verify the container first) + the **CapabilityDef pool** + the **resolver** (extend
  `rs1/rs2`) → unlocks the StS combat layer + the capability progression.
- **Then:** **companions/roster** (rides the per-actor struct) + the **goods economy**
  (drop gold) + **missions** (extend QuestDef + the archetype routine-arms).
- **Then (strategic layer, on the foundation):** the **reactive-web graph** + **conditions**
  + **Tension/locality** + the **history-gen** (the prerequisite for emergent threads) +
  the **LOD aggregate/promotion**.
- **Verify-first prototypes gate the load-bearing pieces** (RESOLUTION §3 resolver curve,
  PARTY §7 Tension curve, CATALOG §6.6 magic-control curve, the §5j history→thread-web,
  and the §11b container under loft#320) — cheapest medium, before loft.

*This is the data-architecture view; the mechanics live in PARTY.md / RESOLUTION.md /
CATALOG.md, the content seam in BUNDLE.md, and the deferred per-player split in DESIGN
§11a/§11b.*
