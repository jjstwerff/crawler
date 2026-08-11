# Plan lifecycle — closing or deferring

The checklist for taking a plan out of flight. Conventions: [`README.md`](README.md).

**The step everyone skips is #5 (rewrite incoming links).** Reference content that grew
inside a plan gets linked from other docs; those links rot the moment the content moves.

## Pick the outcome first

| Situation | Outcome |
|---|---|
| All phases shipped | **Close** — `status:finished`, close the issue |
| Some phases paused with a **concrete trigger** (an upstream fix, a prerequisite plan) | **Defer** — `status:future`, issue stays **open**, deferred phases keep their full design content |
| Paused with **no** concrete trigger | Not a deferral — record the decision and close as `status:declined`. A plan parked on vibes rots. |

A plan can be **partly** closed: shipped phases become closure records while the rest
stays live. That is the normal state of a long plan, not an exception.

## Per shipped phase

**1 — Tag each section** REFERENCE (durable truth about how it works) ·
CLOSURE-RECORD (what shipped, when, what it cost) · HISTORICAL (superseded).

**2 — Move REFERENCE content out to the doc that owns it.** Two shapes:
- *create-and-move* — the phase grew a whole subsystem → it earns its own reference doc.
- *trim-only* — the content already has a home → delete the duplicate from the plan.

The test: **a reader who never opens `plans/` must still find how the thing works.**
If the only description of a shipped mechanism lives in a plan, the move is not done.

⚠ **Look for whole DOCUMENTS, not just paragraphs** — the case that actually happened. Plan
`#9` grew `TREES.md`, a full reference for a shipped subsystem, and it sat inside
`plans/9-canopy-trees/` for months while the issue carried `status:finished`. *A plan that
earns its own reference doc has done half of create-and-move; the half everyone forgets is
the move.* One command:

```sh
find plans/<N>-<slug> -name '*.md' ! -name 'README.md'   # each hit: move it, or say why not
```

And two tells that a moved doc was never really re-read: a stale header (`TREES.md` still
opened *"DESIGN ONLY. Nothing built."* after ten gated phases), and no pointer from the entry
docs — if `CLAUDE.md` has never heard of it, neither has the reader.

**3 — Trim the plan's section** to a lead status line + where the reference now lives:

```markdown
| **A** — the trait seam | S | `make test` (seam gate) | ✅ SHIPPED 2026-06-11 → BUNDLE.md § Trait seam |
```

## Common to close + defer

**4 — Set the lifecycle state on the ISSUE, not the path.** Directories never move;
there are no `finished/` subdirectories.

```sh
# Closing:
gh issue edit <N> -R jjstwerff/crawler --remove-label status:active --add-label status:finished
gh issue close <N> -R jjstwerff/crawler

# Deferring (issue stays OPEN — record the trigger in the body and the plan Status):
gh issue edit <N> -R jjstwerff/crawler --remove-label status:active --add-label status:future
```

**A closed issue must carry `status:finished` or `status:declined` — never a live
status.** Closing the issue by hand does not swap the label, so this drifts silently.
When you touch a closed plan, verify the label matches the state.

⚠ **AND THE MIRROR, which is the one that bites: a `status:finished` label on an OPEN issue.**
`#9`/`#10` sat that way and nobody noticed, because *nothing forces the two to agree*. It is
not cosmetic — the label says the checklist ran, and in `#9`'s case it had not: acting on it
found a whole reference doc still buried in the plan. **A label is not a closure.** Both
directions in one query:

```sh
gh issue list -R jjstwerff/crawler --label plan --state all \
  --json number,state,labels --jq '.[] | select(
    (.state=="OPEN"   and ([.labels[].name] | index("status:finished"))) or
    (.state=="CLOSED" and (([.labels[].name] | index("status:finished")) | not)
                      and (([.labels[].name] | index("status:declined")) | not))
  ) | "DRIFT: #\(.number) \(.state)"'
```

**5 — Grep and rewrite incoming links. THE most-skipped step.**

```sh
grep -rn "plans/<N>-<slug>" --include='*.md' --include='*.loft' --include='Makefile' .
grep -rn "PLAN-<OLD>\.md" --include='*.md' --include='*.loft' --include='Makefile' .
```

Rewrite each hit to the content's new home — not to the plan. A link that lands on a
closure record when the reader wanted the mechanism is a dead end with extra steps.

**6 — Reclassify the synthesis layer.** `ROADMAP.md` tracks the through-line to a
playable game and `DESIGN.md §18a` the ordered backlog: shipped work leaves those lists,
deferred work stays if still tracked. Neither is a plan index — don't grow one.

## After a defer

The plan stays in `plans/` with its design intact and `status:future` on the issue. When
the trigger fires, swap back to `status:active` and continue — no re-opening ceremony,
no directory move. If the trigger turns out to be permanent, close as `status:declined`
and move any still-true reference content out first (step 2 still applies).

## Pitfalls

1. **Closing without moving reference content out.** The commonest failure; it buries
   live truth in a document readers are told to ignore.
2. **Rewriting links to the plan instead of to the new home.** Step 5 is about the
   content's destination, not the plan's path.
3. **A closed issue left on a live status label.** Silent drift — check it.
4. **Deferring without a concrete trigger.** That is a decline; say so.
5. **Conflating "the gate is green" with "the phase shipped."** A phase ships when its
   verification is *in the standing gate* (`make test` / `make probe`), not when it
   passed once locally.
