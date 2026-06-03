# Copyright (c) 2026 Jurjen Stellingwerff
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# ==== What can this Makefile do for you? ===============================
#
# If you just want to play:
#
#   make play     Run the game in a native window (Esc to quit).
#                 Controls: W/S glide forward/back, A/D turn (the world
#                 rotates around you), . or Space to wait a turn.
#
#   make game     Build the game into ONE self-contained HTML file
#                 (story.html) you can open in a browser or host anywhere.
#
#   make serve    Build story.html and serve it on
#                 http://localhost:8000/story.html
#
# If you are working on the game:
#
#   make test     Run the headless, deterministic kernel self-test
#                 (turning is free, forward movement ticks the world, the
#                 enemy chases) AND the native compile gate.
#
#   make check    Compile-only gate (parse + bytecode) — reports errors
#                 without running.  Fast; needs no native toolchain.
#
#   make check-native
#                 Validate the NATIVE / wasm codegen path (run before
#                 `make game`).  Needs the loft toolchain's rlibs to match
#                 your system rustc — rebuild loft if it reports E0514.
#
#   make shot     Render one frame under Xvfb and save story.png.
#
#   make fmt      Format src/*.loft in place.
#   make clean    Remove generated artifacts (story.html, story.png, caches).
#   make help     Print this overview again.
#
# Configuration (override on the command line, e.g. make play LOFT_REPO=...):
#
#   LOFT_REPO=<dir>   Location of the loft toolchain + its lib/ directory.
#                     Defaults to ../loft relative to this Makefile.
#
# This project is the renderer-agnostic `story` kernel (src/sim.loft,
# src/hexgeo.loft) plus a swappable 2D front-end (src/view.loft,
# src/story.loft).  See DESIGN.md for the full design.  Every target below
# is a real rule — scroll to its name to see exactly what it does.
# =======================================================================

# Location of the loft language toolchain.  The story package is run by the
# loft binary with --path (for the standard library) and --lib (to resolve
# the `graphics` package); it has no toolchain of its own.
LOFT_REPO ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../loft)
LOFT      := $(LOFT_REPO)/target/release/loft
LOFTFLAGS := --path $(LOFT_REPO)/ --lib $(LOFT_REPO)/lib/

SRC   := src/story.loft       # game entry (window + loop)
KTEST := src/selftest.loft    # headless kernel self-test
HTML  := story.html
SHOT  := story.png

.PHONY: help play game serve test check check-native shot fmt clean all

# Default target: print the overview above.
help:
	@sed -n '/^# ==== What can this Makefile do for you/,/^# ====/p' Makefile \
	  | sed 's/^# \{0,1\}//'

# Convenience: format + compile gate.
all: fmt check

# ── Run ────────────────────────────────────────────────────────────────

play:
	@echo "  [1/2] checking loft toolchain ..."
	@test -x "$(LOFT)" || { \
	    echo "    FAIL: loft binary not found at $(LOFT)"; \
	    echo "    build it:  ( cd $(LOFT_REPO) && cargo build --release --bin loft )"; \
	    echo "    or point at it: make play LOFT_REPO=/path/to/loft"; \
	    exit 1; }
	@echo "  [2/2] launching story (Esc to quit) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) $(SRC)

# ── Browser build ────────────────────────────────────────────────────────

game:
	@echo "  [1/3] checking loft toolchain ..."
	@test -x "$(LOFT)" || { echo "    FAIL: loft binary not found at $(LOFT)"; exit 1; }
	@echo "  [2/3] compiling story -> $(HTML) ..."
	@$(LOFT) --html $(HTML) $(LOFTFLAGS) $(SRC) >/tmp/story_html.log 2>&1 || { \
	    echo "    FAIL: --html build — see /tmp/story_html.log"; \
	    tail -30 /tmp/story_html.log; exit 1; }
	@echo "  [3/3] sanity-checking output ..."
	@test -s $(HTML) || { echo "    FAIL: $(HTML) is empty or missing"; exit 1; }
	@grep -qi loft $(HTML) || { echo "    FAIL: $(HTML) has no loft runtime"; exit 1; }
	@echo "  built: file://$(abspath $(HTML))"

serve: game
	@echo "  serving on http://localhost:8000/$(HTML)  (Ctrl-C to stop)"
	@python3 -m http.server 8000

# ── Tests / gates ────────────────────────────────────────────────────────

check:
	@echo "  compiling (parse + bytecode gate) ..."
	@$(LOFT) --interpret --check $(LOFTFLAGS) $(SRC) || { echo "    FAIL: compile"; exit 1; }

# Native / wasm codegen gate.  Compiles the generated Rust with rustc, so it
# needs the loft toolchain's prebuilt rlibs to match the system rustc.
check-native:
	@echo "  compiling (native Rust codegen gate) ..."
	@$(LOFT) --check $(LOFTFLAGS) $(SRC) || { \
	    echo "    FAIL: native compile."; \
	    echo "    If E0514 (rustc version mismatch): rebuild loft —"; \
	    echo "      ( cd $(LOFT_REPO) && cargo build --release )"; \
	    exit 1; }

test:
	@echo "  [1/8] kernel self-test (headless, deterministic) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) $(KTEST) | tee /tmp/story_selftest.log
	@grep -q "ALL CHECKS PASS" /tmp/story_selftest.log || { \
	    echo "    FAIL: kernel self-test did not pass"; exit 1; }
	@echo "  [2/8] combat loop (player melee + enemy attacks) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/combattest.loft | tee /tmp/story_combat.log
	@grep -q "COMBAT OK" /tmp/story_combat.log || { echo "    FAIL: combat loop"; exit 1; }
	@echo "  [3/8] dungeon wiring (procedural gen + DB monsters) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/wiretest.loft | tee /tmp/story_wire.log
	@grep -q "WIRING OK" /tmp/story_wire.log || { echo "    FAIL: dungeon wiring"; exit 1; }
	@echo "  [4/8] monster AI (awareness + never-move) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/aitest.loft | tee /tmp/story_ai.log
	@grep -q "AI OK" /tmp/story_ai.log || { echo "    FAIL: monster AI"; exit 1; }
	@echo "  [5/8] placement (budget + weighted + start-safe) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/placetest.loft | tee /tmp/story_place.log
	@grep -q "PLACEMENT OK" /tmp/story_place.log || { echo "    FAIL: placement"; exit 1; }
	@echo "  [6/8] levels (stairs + descent) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/leveltest.loft | tee /tmp/story_level.log
	@grep -q "LEVEL OK" /tmp/story_level.log || { echo "    FAIL: levels"; exit 1; }
	@echo "  [7/8] hero (XP + level-up) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/herotest.loft | tee /tmp/story_hero.log
	@grep -q "HERO OK" /tmp/story_hero.log || { echo "    FAIL: hero"; exit 1; }
	@echo "  [8/8] compile gate (parse + bytecode) ..."
	@$(LOFT) --interpret --check $(LOFTFLAGS) $(SRC) >/dev/null 2>&1 || { echo "    FAIL: compile"; exit 1; }
	@echo "  PASS"

# ── Screenshot (Xvfb, mirrors loft's snap_smoke) ──────────────────────────

shot:
	@for t in xvfb-run xdotool import convert; do \
	    command -v $$t >/dev/null 2>&1 || { \
	        echo "  shot: missing '$$t' — install: apt install xvfb xdotool imagemagick"; \
	        exit 1; }; \
	done
	@test -x "$(LOFT)" || { echo "  shot: loft binary not found at $(LOFT)"; exit 1; }
	@echo "  capturing one frame under Xvfb -> $(SHOT) ..."
	@xvfb-run -a -s "-screen 0 800x600x24" \
	    tools/snap.sh "$(SHOT)" "$(LOFT)" "$(SRC)" "$(LOFT_REPO)" || { \
	    echo "  shot: FAILED"; exit 1; }
	@echo "  wrote $(abspath $(SHOT))"

# ── Housekeeping ──────────────────────────────────────────────────────────

fmt:
	@for f in src/*.loft; do $(LOFT) --format $$f; done
	@echo "  formatted src/*.loft"

clean:
	@rm -rf src/.loft .loft $(HTML) $(SHOT) /tmp/story_*.log
	@echo "  cleaned: $(HTML) $(SHOT) caches"
