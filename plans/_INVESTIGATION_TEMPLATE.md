# Investigation plan template

Copy to `plans/<N>-<slug>/README.md` **plus a `probes/` subdirectory** when the first
phase is *characterize the problem* rather than *design + build*.

**Use this shape when** there are multiple failure clusters to catalogue, source-reading
alone won't converge, and the fix cannot be designed without the catalogue. **Don't** use
it for a single root cause that fits one commit — that's a bug fix, not a plan.

**Primary deliverable: mechanism understanding + a fix-design decision.** Code shipped is
the *standard* template's deliverable, not this one's.

Reading order for whoever picks this up cold: **Status → Probes → Clusters → Roadmap.**

---

# `<N>` — `<Investigation title>`

**Issue:** [`jjstwerff/crawler#<N>`](https://github.com/jjstwerff/crawler/issues/<N>) ·
**Value:** `<S|R|G|F|U|C|Q|N>` · **Effort:** `<XS|S|M|MH|H|VH>`

## Status (REQUIRED)

*(delete)* Which stage, which clusters are characterized, which are fixed. Track
severity as **two separate fields** — *corruption/crash/hang* and *leak/cost* — so
"FIXED" cannot quietly close one while the other persists.

## The question (REQUIRED)

*(delete)* One sentence. What must be understood before a fix can be designed. If you
can already state the fix, this is not an investigation.

## Stage A — probes BEFORE reading source (REQUIRED)

*(delete)* Probes are the **executable spec for "understood"**: a hypothesis is
confirmed when the probe-pair diff confirms it. Write them before source-reading —
source-reading without a probe to ground it explores code paths without converging.

**Be liberal.** Missing a crucial shape is the worst outcome; redundant variants cost
nothing because curation happens at the *end* of Stage A, not during it.

**At least one probe must be extracted from a REAL consumer** (an actual crawler seed,
bundle, or frame), not only synthetic cases — real extraction surfaces classes synthetic
probes never imagine. Today's example: the monster-spawn corruption reproduced only once
a real generated world was in play.

| Probe | Shape it isolates | Cluster | Status |
|---|---|---|---|
| `probes/<name>.loft` | one-line description | 1 | pass / FAILS / flaky |

**Run every probe on every mode the result can diverge across** and record the full
matrix. For crawler that is at least `--interpret` vs `--native` (they *do* diverge —
see LOFT-NOTES.md's survival guide), plus seeded generation where relevant.

| Probe | `--interpret` | `--native` | Notes |
|---|---|---|---|
| `<name>` | ✅ / ❌ | ✅ / ❌ | |

## Clusters (REQUIRED — one section or file per failure mode)

*(delete)* Per cluster, a **verified-vs-hypothesized accountability table**. Every
mechanism statement is either VERIFIED (cite the trace, the probe, the source line) or
HYPOTHESIZED (marked as such). Without this column hypotheses drift into the prose and
get read as facts.

| Claim | VERIFIED / HYPOTHESIZED | Evidence |
|---|---|---|
| `<mechanism statement>` | VERIFIED | `probes/x.loft` + `src/sim.loft:3192` |

## Tool gaps (REQUIRED)

*(delete)* **Tools as needed, not upfront.** Don't build a debugging framework first;
add the *one* tool blocking progress, revert the nice-to-haves, and list what you added
here — tools added during the investigation are part of its output.

## Roadmap (REQUIRED)

*(delete)* Per-cluster action items with effort letters. What the next session picks up
without re-reading everything.

---

## Probe → gate migration *(delete this section)*

Probes live in `probes/` during the investigation and graduate to the standing gate
**per cluster, as each cluster's fix lands** — not all at once. The plan stays open
through phased implementation and closes when the last cluster's regression is in the
gate.

A probe is graduation-ready only when **all** hold:

- assertions pass, **and** the process exits clean (check the exit code — "it printed
  PASS" is not enough; crawler has hit silent aborts that still exit 0)
- no `stores not freed` warning
- bounded runtime — seconds, not a hang

A probe that passes its assertions but fails another gate **stays in `probes/`** with a
status note; graduate a representative sibling from the same cluster instead.

Graduated probes become `src/<x>test.loft` cases (wired into `make test`) or
`probes/*.probe` pixel assertions (`make probe`).

**Upstream defects found on the way out** go to LOFT-HANDOFF.md → FILING.md, never into
this plan's clusters — crawler is a consumer. Cross-link them from the cluster instead.
