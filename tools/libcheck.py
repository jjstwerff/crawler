#!/usr/bin/env python3
"""libcheck — gate the library-layer standing rules (ADOPTION.md P4).

The rules were written down before anything enforced them, which is how three modules
stayed forks of published packages for two weeks and `hex_field` was used by 48 files
while absent from `loft.toml`. A rule nobody can fail is a preference. This makes each
one falsifiable in about a second.

    L1  the lock names every declared dependency        (LOFT-HANDOFF H9)
    L2  no --lib tree shadows a locked package          (ADOPTION.md P3)
    L3  no crawler module duplicates a LOCKED package   (ADOPTION.md P1)
    L4  no crawler type name collides with a package    (loft 2026.8.0 bare names)
    L5  no crawler module NAMES an available package    (ADOPTION.md P1)

L3 and L5 divide one question by what evidence is available. L3 is the strong form and
needs the package's API surface, which exists only for packages already in the lock — so
it is blind to precisely the case that matters most: a module whose package we have not
adopted yet. That was the real history here (hexedge/hexway/hexroof were published and
unlocked for two weeks). L5 covers that gap with the one signal the registry catalog does
carry: the NAME. `hexedge` vs `hex_edge` is not a coincidence worth ignoring.

Reads only committed artifacts — loft.toml, loft.lock, Makefile, .loft/api/*.api and
src/ — so it needs no toolchain, no network and no build. Exit 0 clean, 1 on violation.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A module whose whole surface sits inside a package is a duplicate. Below this many
# functions the containment is coincidence rather than evidence — hexcache's 3-function
# surface can land inside a big package without being that package.
MIN_FNS_FOR_DUPLICATE = 4

# ACCEPTED DEBT — known, priced and deliberately not fixed yet. Each entry must carry a
# reason and a pointer, and each is REPORTED on every run so it cannot fade into the
# background. This exists so the gate stays honest: a check that is permanently red is a
# check people delete, but a debt that vanishes from the output is one nobody pays.
#
# ⚠ Adding a line here is a decision, not a silencing. If you cannot write the reason,
# you do not have one.
ACCEPTED = {
    ("L5", "hexplace"): (
        "hex_place exists and shares ZERO function names with src/hexplace.loft — it is "
        "hexbody's seating (hexframe/hexseat/hexcombine), not this. So the name is taken "
        "but the code is not a copy: switching is a rewrite, priced separately. "
        "ADOPTION.md -> 'The line — a price, not a border'."
    ),
}


def read(p):
    # is_file(), not exists(): `src/.loft` is a DIRECTORY that matches a *.loft glob.
    return p.read_text(errors="replace") if p.is_file() else ""


def declared_deps():
    """Package names in loft.toml's [dependencies]."""
    body = read(ROOT / "loft.toml").split("[dependencies]")
    if len(body) < 2:
        return set()
    names = set()
    for line in body[1].splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith("["):
            if line.startswith("["):
                break
            continue
        if "=" in line:
            names.add(line.split("=")[0].strip())
    return names


def locked_packages():
    return set(re.findall(r'^name\s*=\s*"([^"]+)"', read(ROOT / "loft.lock"), re.M))


def lib_paths():
    """--lib directories on the Makefile's LIB_DEPS line."""
    m = re.search(r"^LIB_DEPS\s*:?=\s*(.*)$", read(ROOT / "Makefile"), re.M)
    return re.findall(r"--lib\s+(\S+)", m.group(1)) if m else []


def packages_under(path):
    """Package names a --lib directory provides (a dir per package, each with loft.toml)."""
    d = (ROOT / path).resolve()
    found = set()
    if not d.is_dir():
        return found
    for toml in d.glob("*/loft.toml"):
        m = re.search(r'^name\s*=\s*"([^"]+)"', read(toml), re.M)
        if m:
            found.add(m.group(1))
    return found


def api_surface():
    """{package: (fns, types)} from the committed .loft/api stubs."""
    out = {}
    for stub in sorted((ROOT / ".loft" / "api").glob("*.api")):
        if stub.name == "_available.api":
            continue
        text = read(stub)
        fns = set(re.findall(r"^pub fn ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        types = set(re.findall(r"^pub (?:struct|enum|type) ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        out[stub.stem] = (fns, types)
    return out


def available_packages():
    """Every package name in the registry catalog stub, not just the locked ones."""
    text = read(ROOT / ".loft" / "api" / "_available.api")
    return set(re.findall(r"^([a-z][a-z0-9_]*) \d", text, re.M))


def squash(name):
    """`hex_edge` and `hexedge` are the same name for collision purposes."""
    return name.replace("_", "").lower()


def crawler_modules():
    """{module: (fns, types)} for every .loft under src/, tests excluded."""
    out = {}
    for f in sorted((ROOT / "src").rglob("*.loft")):
        if not f.is_file() or f.stem.endswith("test"):
            continue
        text = read(f)
        fns = set(re.findall(r"^\s*pub fn ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        types = set(re.findall(r"^\s*pub (?:struct|enum|type) ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        out[f.stem] = (fns, types)
    return out


def main():
    raw = []
    note = []
    accepted = []

    def report(rule, subject, message):
        """Route a violation to the failure list, or to the accepted-debt list."""
        key = (rule, subject)
        if key in ACCEPTED:
            accepted.append(f"    [{rule}] {subject} — {ACCEPTED[key]}")
        else:
            raw.append(message)


    fail = raw
    deps, locked, api, mods = declared_deps(), locked_packages(), api_surface(), crawler_modules()

    # L1 — the lock names every declared dependency.
    for d in sorted(deps - locked):
        report("L1", d,
            f"L1  `{d}` is declared in loft.toml but ABSENT from loft.lock.\n"
            f"    `loft update` will not notice it (it walks the lock, not the manifest —\n"
            f"    LOFT-HANDOFF H9). Compile once against it, then re-check."
        )
    for d in sorted(locked - deps):
        note.append(f"    locked but not declared: {d}")

    # L2 — no --lib tree shadows a locked package. A --lib copy OUTRANKS the registry,
    # so this is the silent-override check, not a tidiness one.
    for path in lib_paths():
        for pkg in sorted(packages_under(path) & locked):
            report("L2", pkg,
                f"L2  --lib {path} provides `{pkg}`, which loft.lock also pins.\n"
                f"    A --lib tree outranks the registry copy, so the build silently takes\n"
                f"    the tree and the lock becomes fiction (ADOPTION.md P3). Drop the --lib,\n"
                f"    or drop the package from the lock — not both paths at once."
            )

    # L3 — no crawler module duplicates a package.
    for mod, (fns, _) in sorted(mods.items()):
        if len(fns) < MIN_FNS_FOR_DUPLICATE:
            continue
        for pkg, (pfns, _) in sorted(api.items()):
            if fns <= pfns:
                report("L3", mod,
                    f"L3  src/{mod}.loft declares {len(fns)} public functions and package "
                    f"`{pkg}` declares all of them.\n"
                    f"    That is a fork of a published module. Consume the package and delete\n"
                    f"    the copy, or — if this module has grown something the package lacks —\n"
                    f"    ADD it to the package (no project owns a library)."
                )

    # L4 — no crawler type name collides with a locked package's.
    for mod, (_, types) in sorted(mods.items()):
        for pkg, (_, ptypes) in sorted(api.items()):
            for t in sorted(types & ptypes):
                report("L4", f"{mod}.{t}",
                    f"L4  `{t}` is declared by src/{mod}.loft AND by package `{pkg}`.\n"
                    f"    Under loft 2026.8.0 a bare `{t}` is an error where both are in scope,\n"
                    f"    and until then the local one silently SHADOWS the package's. Rename\n"
                    f"    the crawler type (ADOPTION.md P2 renamed Stencil -> RoomStencil)."
                )

    # L5 — no crawler module carries the name of an available registry package. This is the
    # only rule that can see an UNADOPTED package, because it needs the catalog and not the
    # API surface. It is what would have caught hexedge/hexway/hexroof on day one.
    avail = available_packages()
    by_squashed = {squash(p): p for p in avail}
    for mod in sorted(mods):
        pkg = by_squashed.get(squash(mod))
        if pkg:
            report("L5", mod,
                f"L5  src/{mod}.loft has the name of registry package `{pkg}`.\n"
                f"    Either it is that package kept as a copy — consume it — or it is a\n"
                f"    different thing wearing a taken name, which will collide the day both\n"
                f"    are in one graph. Neither resolves itself by waiting."
            )

    print(f"libcheck: {len(deps)} declared deps, {len(locked)} locked, {len(api)} api stubs, "
          f"{len(avail)} packages available, {len(mods)} crawler modules")
    if note:
        print("\n".join(note))
    if accepted:
        print(f"  accepted debt ({len(accepted)}) — priced, not hidden:")
        print("\n".join(accepted))
    if fail:
        print()
        for f in fail:
            print(f"  {f}\n")
        print(f"    FAIL: libcheck — {len(fail)} violation(s)")
        return 1
    print("  LIBCHECK OK — lock complete, no --lib shadowing, no forked module, no name clash")
    return 0


if __name__ == "__main__":
    sys.exit(main())
