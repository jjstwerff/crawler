# VISION.md — what this is for

> Written for a person, not for a build. If you have arrived here cold — to use this, to
> contribute to it, or to decide whether either is worth your time — start here. The
> operational docs (`CLAUDE.md`, `DESIGN.md`, `STATE.md`, `plans/`) tell you *how the work is
> done*; this one says *why the work exists*.

## The problem

**A rich game world currently costs a studio.**

Not because the techniques are secret — they are published, taught, and largely commodity. It
is because the dominant way to build a world is to **assemble it from unique assets**:
hundreds of hand-modelled buildings, hand-placed trees, hand-written NPCs, hand-authored quest
branches. Every one of those is somebody's week. Baldur's Gate 3 is magnificent and it took
roughly four hundred people six years, and the great majority of that was *volume* — not
capability.

So an entire category of game is closed to small teams. Not for lack of skill or ideas: for
lack of headcount. Two people cannot hand-place a continent.

## The thesis

**Variety can be produced instead of stored.**

If the world is *derived from a model* rather than assembled from assets, the content bill
scales with **mechanisms** instead of with **headcount**. One tree routine replaces a library
of tree models. One settlement scorer replaces a thousand hand-placed villages. One
eligibility system replaces an authored branch tree.

That is not a new idea — Dwarf Fortress has been proving it for two decades. What is missing is
that almost none of it is *reusable*. Every project that wants a derived world builds the hard
parts again from scratch, badly, and usually gives up somewhere around the geometry.

**So: do the hard algorithmic work once, properly, and hand it over.**

## Why "properly" is the load-bearing word

Derivation is unforgiving in a way that asset-assembly is not. If you place a building by hand
and it is slightly wrong, you nudge it. If a *generator* is slightly wrong, it is wrong ten
thousand times, in ways nobody can see and nobody can nudge.

Which means the standard of proof has to be higher than games usually demand:

- **Exact, not approximate.** The hex lattice here uses integer coordinates, so rotations are
  exact, areas round-trip exactly, and a traced outline provably describes the cells it came
  from. Not "within epsilon" — exactly. Approximation accumulates; exactness composes.
- **Measured, not eyeballed.** Real dimensions are the default and they are *gated by tests*,
  so a wrong world can be **proved** wrong instead of argued about. This is not fussiness: the
  first time a camera was placed at human eye height in this project, it found cottages with
  1.51 m eaves and 1.45 m doors — a world its own 1.75 m player could not stand up in. Every
  previous check had passed, because every previous camera had been above the rooftops.
- **Falsifiable, with negative controls.** A check that cannot fail is not a check. Every phase
  here has to demonstrate that corrupting its input turns the gate red — because the failure
  mode is never a test that fails, it is one that passes for the wrong reason.

That discipline is the actual product. Anyone can write a generator; the question is whether
you can *trust* it enough to build on.

## This is one layer of a stack that already says this

**`../loft/doc/claude/GOALS.md` states the same drive one layer down, and stated it first:**

> *"loft is not the goal. loft is the **foundation**: the lowest layer of plumbing. The real
> goal is the **libraries and tools built on top of it** — lavition (the engine), the hex-world
> library, the editor, the games."*
>
> *"**Do the hard plumbing yourself, deeply, so someone else can just pick it up and have
> fun.**"*

So crawler is not applying a philosophy to a substrate that lacks one — it is **the layer above
a foundation built on the same premise**, and loft's goals name the games as the real end.
Three things it says better, adopted here rather than restated:

1. **Built from the MAKER's side of the screen, not the programmer's.** *"Today's engines are
   built by programmers, from a programmer's point of view… the maker has to learn that
   worldview before building anything."* That sharpens "small teams": the audience is not merely
   *fewer people*, it is people who should not have to think like programmers to build a world.
   It is why the **editor** matters more than its line count suggests, and why content is a
   folder rather than a codebase.
2. **The acceptance test is FUN, not feature-complete.** *"A library can ship every feature and
   still be a fight to use. That library is not done."* This is a higher bar than anything in
   `EXTRACTION.md`'s Definition of Done, whose six clauses are all correctness and testing —
   **a package can satisfy every one of them and still be miserable to pick up.** Treat that as
   the missing DoD clause.
3. **Adoption is a result, not a steering input.** *"We build the idea because it is worth
   building… real value reaches the people who share the idea in its own time."* Worth holding
   onto, because "how would you know it worked" drifts very easily into "get users".

And underneath all of it, loft's quieter aim — *"software that does not fail for software
reasons"* — with **mental load** as the mechanism: every unit of attention the tools demand for
correctness is a unit stolen from the game. That is the same argument this document makes about
*content* volume, made about *cognitive* volume.

## What is being built

Not a general game engine. A specific stack, each layer usable without the ones above it:

| | what | why it exists |
|---|---|---|
| **loft** | a programming language | yes, really. Deterministic, testable, and shaped for this |
| **`hex_*` libraries** | the world model — field, ways, forms, growth, props, scene | the hard algorithmic parts, extracted so others build on them rather than rebuild them |
| **an editor** | in-world, outside the game | tooling is what small teams lack most, and it is the second consumer that proves the libraries are general |
| **bundles** | content as drop-in folders | because a small team should not have to write all the content — and others adding to your game is the only way volume ever arrives |
| **crawler** | a hex roguelike | **the proof and the forcing function, not the product.** A library nobody has shipped a game with is a hypothesis |

## The principles

Eight, and they compose. Each one exists because ignoring it has a known failure mode.

1. **The goal is small teams.** Everything is judged by whether it hands them a hard part
   already solved.
2. **Over-engineer only where others build on it.** The test is one question: *does this make a
   hard part reusable by someone else?* Yes — build it exactly and gate it, because the cost is
   paid once here and never again downstream. No — it is polish for one game, and it waits.
3. **Depth in the derivation, shallow at the interface.** Simulate as deeply as you like; the
   player must never have to learn the model to play the game. Dwarf Fortress is hard to enter
   *not by design* — that trap is entered one reasonable feature at a time.
4. **Measure it, or it is decoration.** Real dimensions by default. A game may stylise
   deliberately; the default it departs from is correct.
5. **The diorama is the research; the brick is the finding.** Author one specific thing to
   discover what is load-bearing, then ship the reusable part. Nobody designs a good generator
   in the abstract.
6. **Author richly — but never schedule it.** Content carries *conditions*, not a place in a
   sequence. This is the move that lets rich authored content and deep simulation coexist,
   which the industry treats as a trade-off only because it always tried to have both **on a
   schedule**.
7. **Most players will miss most of it, and that is the mechanism working.** Content that only
   fires when the world makes it true is content many players never see. Replayability is the
   by-product; discovery becomes something players tell each other about.
8. **Match capability, not volume.** Graphical fidelity, locomotion, animation and voice are
   *systems* — built once, and getting cheaper every year. Hundreds of bespoke individuals are
   not, and are not needed.

## What this is not

- **Not a photorealism project.** Fidelity is a legitimate long-run target, but style is how
  small teams have always won, and chasing fidelity is how budgets die.
- **Not a general-purpose engine.** It is opinionated about hex worlds, determinism and
  derivation. That narrowness is why the parts can be exact.
- **Not a content factory.** If it needs AAA content volume to be good, it has failed.
- **Not a game only its authors can understand.** See principle 3.

## How you would know it worked

Concrete, falsifiable, and none of them yet true:

- A stranger drops a bundle into the folder, rebuilds without touching the source, and their
  content plays against an unchanged game.
- Someone who did not write these libraries ships a game on them that we did not imagine.
- Two people produce a world with the reactivity people praise big-studio games for — and the
  reason it works is that nothing in it was scheduled.
- A player finds something and tells somebody else about it, because it was possible to miss.

## Where to go next

- **[DESIGN.md](DESIGN.md)** — the design: pillars (§3a), scope (§3b), and the ordered backlog.
- **[STATE.md](STATE.md)** — where the work actually stands today. Read after a break.
- **[EXTRACTION.md](EXTRACTION.md)** — how the reusable parts get out, and what "reusable"
  has to mean before a package may claim it.
- **[SCALE.md](SCALE.md)** — the measurement contract, and why it is code rather than a
  convention.
- **[SCRIPTING.md](SCRIPTING.md)** — eligibility instead of scripts: how content arrives
  without being scheduled.
- **[BUNDLE.md](BUNDLE.md)** — the content seam, so a stranger's folder is a first-class
  citizen.
