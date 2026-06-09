#!/usr/bin/env bash
# Capture a single frame of the story game to a PNG.
#
# Mirrors loft's tests/scripts/snap_smoke.sh: launch the game, wait for its
# window to appear under the current $DISPLAY, grab it with ImageMagick's
# `import`, then correct the R/B channel swap that Xvfb + Mesa swrast applies
# (a near no-op on a real display).  Intended to be run via `make shot`,
# which wraps this in `xvfb-run`.
#
# Args: $1 = output png   $2 = loft binary   $3 = entry .loft   $4 = loft flags
#       ($4 is the --path/--lib string for repo mode, or empty for an installed loft)
set +e

OUT="${1:?output png path required}"
LOFT="${2:?loft binary required}"
SRC="${3:?entry .loft required}"
FLAGS="${4-}"

export LIBGL_ALWAYS_SOFTWARE=1

# shellcheck disable=SC2086  # FLAGS must word-split into --path/--lib (empty = installed)
"$LOFT" --interpret $FLAGS "$SRC" >/tmp/story_shot.log 2>&1 &
PID=$!

# Poll for the window to appear (max ~12s), bailing early if loft died.
WIN=""
for _ in $(seq 1 24); do
  sleep 0.5
  WIN=$(xdotool search --name "." 2>/dev/null | tail -1)
  [ -n "$WIN" ] && break
  kill -0 "$PID" 2>/dev/null || break
done

# Let it render a few frames.
sleep 1

if [ -z "$WIN" ]; then
  echo "snap: no window appeared"
  head -20 /tmp/story_shot.log
  kill "$PID" 2>/dev/null
  exit 1
fi

import -window "$WIN" "$OUT" 2>/tmp/story_import.log || {
  echo "snap: import failed"
  head -5 /tmp/story_import.log
  kill "$PID" 2>/dev/null
  exit 1
}

# Xvfb + Mesa swrast stores captured pixels with R and B swapped; swap back.
convert "$OUT" -separate -swap 0,2 -combine "$OUT" 2>/dev/null

kill "$PID" 2>/dev/null
wait "$PID" 2>/dev/null
echo "snap: wrote $OUT"
