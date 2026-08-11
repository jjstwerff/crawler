#!/usr/bin/env bash
# api_index.sh — regenerate LIBRARIES.md: one line per public name in every package
# crawler declares, read from the REGISTRY copy that the build actually resolves.
#
# WHY THIS EXISTS. Measured 2026-08-11 across one session: ~500 lines of library source were
# read to recover about twenty signatures (`surf_arc`, `way_stamp`, `edge_block_arb`,
# `form_circle`, `hex_corner_px`, …). There was nowhere to look them up, so the only route was
# to open the package. The index below is ~10x cheaper to read and answers the same question.
#
# ⚠ GENERATED, NEVER HAND-KEPT. A hand-written list beside a library is the tenth copy of a
# name that has already drifted — the failure `make bundles` is built to prevent, and the one
# moros' material catalogue records ("derived from the mesher's own list"). So this reads the
# packages themselves, and `make apidoc-check` fails if the committed file is stale.
set -euo pipefail
cd "$(dirname "$0")/.."

REG="${LOFT_REGISTRY:-$HOME/.loft/registry}"
OUT="${1:-LIBRARIES.md}"

# The packages crawler declares, in loft.toml's own order — the manifest is the authority on
# what is a dependency, so a package added there appears here without touching this script.
deps=$(awk '/^\[dependencies\]/{f=1;next} /^\[/{f=0} f && /^[a-z_]+ *=/{print $1}' loft.toml)

{
  echo "# LIBRARIES.md — the public surface of every package crawler consumes"
  echo
  echo "**GENERATED — do not edit. \`make apidoc\` rewrites it; \`make apidoc-check\` fails if it is stale.**"
  echo
  echo "One line per public name, read from the registry copy the build resolves. This exists"
  echo "because looking a signature up used to mean reading the package: ~500 lines of source"
  echo "for ~20 signatures, measured over one session. Read this instead, and open the package"
  echo "only when you need the *reasoning* — which is what its comments are for."
  echo
  echo "⚠ Signatures only. **Why** a routine exists, and the traps around it, live in the"
  echo "package's own comments and in \`EXTRACTION.md\` / \`ADOPTION.md\`."
  echo

  for d in $deps; do
    dir=$(ls -d "$REG/$d"-* 2>/dev/null | sort -V | tail -1 || true)
    [ -n "$dir" ] || { echo "## \`$d\` — not in the registry (unpublished or a local path)"; echo; continue; }
    ver=$(basename "$dir" | sed "s/^$d-//")
    echo "## \`$d\` $ver"
    echo
    echo '```'
    grep -hE '^pub (fn|struct|const) ' "$dir"/src/*.loft 2>/dev/null \
      | sed -e 's/ *{.*$//' -e 's/^pub //' -e 's/ *$//' \
      | sort -u
    echo '```'
    echo
  done
} > "$OUT"

echo "wrote $OUT ($(wc -l < "$OUT") lines) for: $(echo $deps | tr '\n' ' ')"
