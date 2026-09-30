#!/usr/bin/env python3
"""doccheck — gate the doc set's structural rules.

Two doc passes (2026-08-11) fixed the same class of rot twice by hand, and one of those
HAND AUDITS WAS ITSELF WRONG: it reported 110 test rows because `grep -c '^collect_one'`
also matched the function's definition. A doc invariant checked by a careful person is
checked once, on the day someone cares; a doc invariant checked by a command is checked
every run. These are the ones a command can settle.

    D1  every relative markdown link resolves                (a pointer that 404s)
    D2  every backticked crawler path exists                 (a file named after deletion)
    D3  every root doc is reachable from CLAUDE.md's table   (28b1648's hand-checked claim)
    D4  every non-README doc under plans/ · doc/ · build/
        is pointed at by something                           (CLAUDE.md: buried docs)

D3 and D4 are the two halves of one rule — *a doc nothing points at is a doc that gets
re-derived* (CLAUDE.md). D3 covers the root set, where the routing table is the single
entry point and its completeness was verified once, by hand, and rots the moment a doc is
added. D4 covers the rest, where there is no table and TREES.md sat unreachable inside a
plan for months while the tree grew a second answer to the same question.

D2 is deliberately scoped to crawler-shaped prefixes. `src/parser/objects.rs` in a doc
about loft is loft's file, and this gate has no business resolving another repo's tree —
those are ACCEPTED below, each naming the repo that owns it.

Reads only committed markdown and the working tree — no toolchain, no network, no build.
Exit 0 clean, 1 on violation.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Backticked paths starting with one of these are claims about THIS repo.
CRAWLER_PREFIX = ("src/", "tools/", "probes/", "bundles/", "assets/", "patches/")

# Docs outside plans/ that D4 also requires an inbound pointer for.
D4_DIRS = ("plans", "doc", "build")

# ACCEPTED DEBT — known, priced and deliberately not fixed. Each entry carries a reason,
# and each is REPORTED on every run so it cannot fade into the background (the convention
# is libcheck.py's). ⚠ Adding a line here is a decision, not a silencing: if you cannot
# write the reason, you do not have one.
ACCEPTED = {
    # ── D2: paths that belong to another repo, named from a doc that is about that repo.
    ("D2", "src/parser/objects.rs"): "loft's tree — a note about loft's parser.",
    ("D2", "src/registry_keys.rs"): "loft's tree — the registry signing key.",
    ("D2", "tools/html_render_check.mjs"): "loft's tree — loft ships the WebGL harness.",
    ("D2", "src/tests/"): "loft's tree — where loft's own test files live.",
    ("D2", "src/editor_client.loft"): "moros/lavition's editor, not crawler's src/.",
    ("D2", "src/editor_server.loft"): "moros/lavition's editor, not crawler's src/.",
    ("D2", "tools/build_overworld_map.py"): "moros' tool, cited by LOFT-NOTES as moros'.",
    # ── D2: a plan's RECORD naming a probe that did its job and was deleted. A record
    # must be allowed to describe what happened; forcing the file back would be a lie.
    ("D2", "src/towerprobe.loft"): "plan #11 P5's one-shot probe, deleted after it ran.",
    ("D2", "src/atlastest.loft"): "plan #7's record of a test that was folded into probe.",
    ("D2", "src/chunkview.loft"): "plan #2's record; the chunked viewer was never built.",
    ("D2", "tools/layerproto.py"): "plan #5's record of a prototype, not kept.",
    ("D2", "tools/plot_geo.py"): "plan #5's record of a prototype, not kept.",
    ("D2", "src/geodump.loft"): "plan #5's record of a prototype, not kept.",
    ("D2", "tools/wallproto/out/"): "plan #5's prototype output dir, not kept.",
    ("D2", "tools/wallproto/out/target_layers.png"): "plan #5's prototype output, not kept.",
    ("D2", "probes/world_r4"): "the spec is probes/world_r4.probe; cited without suffix.",
    ("D2", "probes/x.loft"): "the investigation TEMPLATE's placeholder, not a real path.",
    ("D2", "bundles/lizardfolk/"): "BUNDLE-MIGRATION's worked EXAMPLE of adding a bundle.",
    ("D2", "bundles/undead/"): "plan #4's worked example of a theme bundle.",
    # ── D2: doc/viewer-design.md §7 PROPOSES these — they are the deliverable, not a claim
    # that they exist. A doc must be able to name what it wants built.
    ("D2", "src/orttrimesh.loft"): "proposed by doc/viewer-design.md §7, not built.",
    ("D2", "assets/sprites/river_line.png"): "proposed by doc/viewer-design.md §7, not built.",
    ("D2", "tools/blueprints/river_line.py"): "proposed by doc/viewer-design.md §7, not built.",
    ("D2", "src/regions/wales.loft"): "doc/viewer-design.md's worked example of a second region.",
    # ── D4: docs that are reached by convention rather than by a pointer.
    ("D4", "plans/_TEMPLATE.md"): "a template — plans/README.md describes it by role.",
    ("D4", "plans/_INVESTIGATION_TEMPLATE.md"): "a template, as above.",
    ("D4", "plans/_LIFECYCLE.md"): "plans/README.md's companion, reached by role.",
}


def main() -> int:
    fail: list[str] = []
    accepted_hit: list[str] = []

    def report(rule: str, key: str, msg: str) -> None:
        why = ACCEPTED.get((rule, key))
        if why:
            accepted_hit.append(f"    {rule}  {key} — {why}")
        else:
            fail.append(msg)

    docs = sorted(p for p in ROOT.rglob("*.md")
                  if ".git" not in p.parts and "node_modules" not in p.parts)
    text = {p: p.read_text(encoding="utf-8", errors="replace") for p in docs}

    # ── D1 — every relative markdown link resolves.
    link = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
    for p in docs:
        for label, target in link.findall(text[p]):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#")[0]
            if not path or (p.parent / path).exists():
                continue
            rel = p.relative_to(ROOT)
            report("D1", str(rel), (
                f"D1  {rel} links to `{target}` ([{label[:40]}]) and it does not exist.\n"
                f"    A dead link costs a search to discover and teaches nothing when found."
            ))

    # ── D2 — every backticked crawler-shaped path exists.
    #
    # ⚠ A DOC IS ALLOWED TO NAME A FILE IT SAYS IS GONE. "was `src/hexedge.loft`" is not a
    # claim that the file exists — it is the history that makes the CURRENT name findable by
    # its old one, which is the single most useful thing a doc can say after an adoption. The
    # first cut of this rule forced that history into ACCEPTED, where four fork entries would
    # sit repeating themselves forever; the honest fix is for the gate to read the idiom. So
    # `was <path>` (immediately before) or a deletion word (just after) marks it as record.
    # Both markers are narrow on purpose: a bare "was" anywhere nearby would let real rot
    # through, which is the failure this whole rule exists to catch.
    #
    # ⚠ EVERY SITE IS REPORTED, NOT THE FIRST. Deduplicating by path hides the other docs
    # naming the same dead file, so each fix reveals one more and the gate converges a
    # round-trip at a time. It cost three of them here before this was changed.
    tick = re.compile(r"`([A-Za-z0-9_./-]+)`")
    GONE = re.compile(r"\b(DELETED|deleted|removed|renamed|superseded)\b")
    bad: dict[str, list[str]] = {}
    for p in docs:
        for m in tick.finditer(text[p]):
            path = m.group(1)
            if not path.startswith(CRAWLER_PREFIX):
                continue
            if (ROOT / path).exists():
                continue
            # ⚠ Whitespace-normalised, because prose WRAPS: "was" landing at the end of a
            # line put a newline between the marker and the path and the rule missed it.
            # A gate that depends on where a line happens to break is a gate that fires on
            # reflow.
            before = re.sub(r"\s+", " ", text[p][max(0, m.start() - 8):m.start()])
            after = text[p][m.end():m.end() + 80]
            if before.endswith("was ") or GONE.search(after):
                continue
            bad.setdefault(path, [])
            rel = str(p.relative_to(ROOT))
            if rel not in bad[path]:
                bad[path].append(rel)

    for path, sites in sorted(bad.items()):
        report("D2", path, (
            f"D2  `{path}` is named by {', '.join(sites)} and is not in the tree.\n"
            f"    Either the file moved (fix the pointer) or it was deleted and the doc\n"
            f"    still describes it as present. If a doc means the file is GONE, say so —\n"
            f"    `was {path}` or a deletion word just after reads as record, not a claim.\n"
            f"    If it is another repo's file or a proposal, add it to ACCEPTED with the reason."
        ))

    # ── D3 — every root doc is reachable from CLAUDE.md's routing table.
    claude = text[ROOT / "CLAUDE.md"]
    for p in sorted(ROOT.glob("*.md")):
        if p.name in ("CLAUDE.md", "LIBRARIES.md"):
            continue  # the table itself; LIBRARIES.md is generated and cited by rule
        if re.search(r"(?<![/\w-])" + re.escape(p.name), claude):
            continue
        report("D3", p.name, (
            f"D3  {p.name} is not named in CLAUDE.md's routing table.\n"
            f"    The table is the one entry point to the root doc set — a doc missing from\n"
            f"    it is one a session finds by searching, or does not find and re-derives.\n"
            f"    Add a row saying WHEN to open it."
        ))

    # ── D4 — every non-README doc under plans/ · doc/ · build/ has an inbound pointer.
    #
    # ⚠ A POINTER IS USUALLY PATH-QUALIFIED, AND THAT IS THE BETTER KIND. The first cut of
    # this rule excluded a leading `/` to stop a name matching inside a longer path, which
    # threw away exactly the good references: plans/10-props/README.md cites
    # `build/INTENT-props.md`, and the rule called that doc an orphan. But a BARE basename
    # cannot be trusted either — DESIGN.md names three different files here. So a doc counts
    # as pointed-at by its relative PATH, or by its bare name only when that name is unique.
    basename_count: dict[str, int] = {}
    for p in docs:
        basename_count[p.name] = basename_count.get(p.name, 0) + 1

    for p in docs:
        rel = p.relative_to(ROOT)
        if not rel.parts or rel.parts[0] not in D4_DIRS or p.name == "README.md":
            continue
        pats = [re.escape(str(rel))]
        if basename_count[p.name] == 1:
            pats.append(r"(?<![/\w-])" + re.escape(p.name))
        found = any(re.search(pat, text[o]) for pat in pats for o in docs if o != p)
        if found:
            continue
        report("D4", str(rel), (
            f"D4  {rel} ({len(text[p].splitlines())} lines) is pointed at by no doc.\n"
            f"    A doc nothing points at is a doc that gets re-derived — TREES.md sat\n"
            f"    inside a plan for months while the tree grew a second answer. Point at it\n"
            f"    from the doc that owns the question, or mark it superseded."
        ))

    n_root = len(list(ROOT.glob("*.md")))
    print(f"doccheck: {len(docs)} docs ({n_root} at root), "
          f"{len(ACCEPTED)} accepted")
    if accepted_hit:
        print(f"  accepted debt ({len(accepted_hit)}) — priced, not hidden:")
        print("\n".join(sorted(accepted_hit)))
    if fail:
        print()
        for f in fail:
            print(f"  {f}\n")
        print(f"    FAIL: doccheck — {len(fail)} violation(s)")
        return 1
    print("  DOCCHECK OK — links resolve, paths exist, every doc is reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
