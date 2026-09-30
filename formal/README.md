# formal/ — crawler's formal rules, cited from the code

A rule is written ONCE, here, and **cited by every site that enforces it** as `@FR-<Name>`
in a code comment. That is what makes *"which sites enforce this rule?"* a query
(`python3 formal/rule_tags.py sites <Name>`) and *"is this rule already implemented?"* a
lookup instead of a guess at which code shape someone chose. **The doctrine: the rules do
not change to match the code; the code changes to match the rules.** Read the register for
a domain BEFORE deliberating a fix that has a choice in it — a rule already written settles
it.

The convention is the loft tree's (`../loft/doc/claude/formal/README.md` § Rule tags, and
the `formal-rules` skill); `formal/rule_tags.py` is its checker, vendored unchanged.

## The shape

- A **rule** is defined by a line `  (Name)  prose` inside a fenced code block. Section
  headers and parenthesised mentions in prose are NOT definitions.
- A **deviation** — a measured, deliberate divergence of the code from a rule — is a
  register entry `### D-<area>-N — <name> (OPEN|CLOSED)` with *Violates / Where / Effect /
  Status / Removal*. An OPEN deviation may be cited by a site that implements the shortfall
  (those are the sites that change when it closes); a CLOSED one is history and is not
  citable. Drive the open count to zero.
- A **citation** is `@FR-<Name>`, matched boundary-exact, so `@FR-Brush-Image` is not a hit
  for `@FR-Brush`. Only a defined rule is a citation target.

## The gate

```sh
make rules      # every citation resolves; no rule defined twice (in `make test`)
python3 formal/rule_tags.py list | sites <Name> | dups
```

Bindings (`make rules` sets them): `RULES_DIR=formal`, `CITE_EXTS=.py,.loft`, and
`CITE_DIRS` = `tools`, `src`, **and the `drawing` library's `src` + `tests` in
`../loft-libs-graphics`** — the loft port of `tools/draw.py` cites this register too, because
draw.py is the oracle its bytes are held to and the rules are one contract with two
implementations. The library's own CI does not run the checker; if the register ever moves to
the library, that is one directory move and one env var here.

## The domains

| doc | covers |
|---|---|
| [draw.md](draw.md) | the `.draw` scene language and its renderers — `tools/draw.py`, the `drawing` library, `src/sprite_draw.loft` |
