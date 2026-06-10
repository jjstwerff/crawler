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
#   (default)         Run the system-installed `loft` (on PATH): it self-locates
#                     its stdlib (/usr/local/share/loft) and auto-loads registry
#                     libraries (e.g. `graphics`, declared in loft.toml) on `use` —
#                     so NO sibling loft repo is needed. Keep it current with
#                     `make install` in the loft repo; verify with `make loft-doctor`.
#   LOFT_REPO=<dir>   Instead run that repo's freshly-built binary with its explicit
#                     --path/--lib — for testing an in-progress loft (e.g. ../loft2).
#
# This project is the renderer-agnostic `story` kernel (src/sim.loft,
# src/hexgeo.loft) plus a swappable 2D front-end (src/view.loft,
# src/story.loft).  See DESIGN.md for the full design.  Every target below
# is a real rule — scroll to its name to see exactly what it does.
# =======================================================================

# Toolchain selection (see Configuration above). Default = the system-installed
# `loft` with NO --path/--lib (it self-locates its stdlib and auto-loads `use`d
# registry libs). LOFT_REPO=<dir> switches to that repo's binary + explicit flags.
ifeq ($(strip $(LOFT_REPO)),)
  LOFT      := loft
  LOFTFLAGS :=
else
  LOFT      := $(LOFT_REPO)/target/release/loft
  LOFTFLAGS := --path $(LOFT_REPO)/ --lib $(LOFT_REPO)/lib/
endif

# Character bundles live in bundles/<name>/; add each as a lib dir so the generated
# src/bundles.loft can `use` them. Auto-discovered — drop a bundle dir and it's included.
# (BUNDLE_LIBS is separate so loft-doctor's installed-binary smoke can use it too.)
BUNDLE_LIBS := $(addprefix --lib ,$(wildcard bundles/*/) $(wildcard bundles/*/items/))
LOFTFLAGS := $(LOFTFLAGS) $(BUNDLE_LIBS)

# Which loft repo `make loft-doctor` compares the installed binary against.
REF_REPO ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../loft2)

SRC   := src/story.loft       # game entry (window + loop)
KTEST := src/selftest.loft    # headless kernel self-test
HTML  := story.html
SHOT  := story.png

.PHONY: help play game serve test check check-native shot fmt clean all loft-doctor

# Default target: print the overview above.
help:
	@sed -n '/^# ==== What can this Makefile do for you/,/^# ====/p' Makefile \
	  | sed 's/^# \{0,1\}//'

# Convenience: format + compile gate.
all: fmt check

# ── Run ────────────────────────────────────────────────────────────────

play:
	@echo "  [1/2] checking loft toolchain ..."
	@command -v $(LOFT) >/dev/null 2>&1 || { \
	    echo "    FAIL: loft not found ($(LOFT))."; \
	    echo "    Install it:  ( cd ../loft && make install )   then: make loft-doctor"; \
	    echo "    Or use a repo build:  make play LOFT_REPO=../loft2"; \
	    exit 1; }
	@echo "  [2/2] launching story (Esc to quit) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) $(SRC)

# ── Browser build ────────────────────────────────────────────────────────

game:
	@echo "  [1/3] checking loft toolchain ..."
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "    FAIL: loft not found ($(LOFT)) — see 'make loft-doctor', or LOFT_REPO=../loft2"; exit 1; }
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
	    echo "    If E0514 (rustc version mismatch): reinstall/rebuild loft —"; \
	    echo "      ( cd ../loft && make install )   or   make check-native LOFT_REPO=../loft2"; \
	    exit 1; }

# Is the installed `loft` current + working?  Compares the installed binary against a
# loft repo build (REF_REPO, default ../loft2 — the same `cmp` the installer uses) and
# runs a headless smoke.  STALE/FAIL → refresh: `make install` in that repo (needs sudo).
loft-doctor:
	@echo "  installed : $$(command -v loft 2>/dev/null || echo MISSING)  ($$(loft --version 2>/dev/null))"
	@if [ -x "$(REF_REPO)/target/release/loft" ]; then \
	    if cmp -s /usr/local/bin/loft "$(REF_REPO)/target/release/loft" 2>/dev/null; then \
	        echo "  binary    : UP-TO-DATE (byte-identical to $(REF_REPO) build)"; \
	    else \
	        echo "  binary    : STALE — differs from $(REF_REPO)/target/release/loft"; \
	        echo "              refresh:  ( cd $(REF_REPO) && make install )   # needs sudo"; \
	    fi; \
	else \
	    echo "  binary    : (nothing to compare at $(REF_REPO); build: cd $(REF_REPO) && cargo build --release)"; \
	fi
	@if [ -d "$(REF_REPO)/default" ] && [ -d /usr/local/share/loft/default ]; then \
	    extra=$$(diff -rq /usr/local/share/loft/default "$(REF_REPO)/default" 2>/dev/null | sed -n 's|^Only in /usr/local/share/loft/default: |/usr/local/share/loft/default/|p'); \
	    if [ -n "$$extra" ]; then \
	        echo "  stdlib    : STALE LEFTOVERS — install's \`cp -r\` doesn't delete files removed/renamed upstream:"; \
	        echo "$$extra" | sed 's/^/              /'; \
	        echo "              fix:  sudo rm -f $$(echo $$extra | tr '\n' ' ')"; \
	    else echo "  stdlib    : clean (no leftover files vs $(REF_REPO)/default)"; fi; \
	fi
	@printf "  smoke     : "; loft --interpret --check $(BUNDLE_LIBS) $(KTEST) </dev/null >/dev/null 2>&1 \
	    && echo "OK — installed loft runs the kernel headlessly (no --path/--lib; bundle libs only)" \
	    || echo "FAIL — installed loft errors (usually a stale stdlib; run the refresh above)"

test:
	@echo "  [1/13] kernel self-test (headless, deterministic) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) $(KTEST) | tee /tmp/story_selftest.log
	@grep -q "ALL CHECKS PASS" /tmp/story_selftest.log || { \
	    echo "    FAIL: kernel self-test did not pass"; exit 1; }
	@echo "  [2/13] combat loop (player melee + enemy attacks) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/combattest.loft | tee /tmp/story_combat.log
	@grep -q "COMBAT OK" /tmp/story_combat.log || { echo "    FAIL: combat loop"; exit 1; }
	@echo "  [3/13] dungeon wiring (procedural gen + DB monsters) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/wiretest.loft | tee /tmp/story_wire.log
	@grep -q "WIRING OK" /tmp/story_wire.log || { echo "    FAIL: dungeon wiring"; exit 1; }
	@echo "  [4/13] monster AI (awareness + never-move) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/aitest.loft | tee /tmp/story_ai.log
	@grep -q "AI OK" /tmp/story_ai.log || { echo "    FAIL: monster AI"; exit 1; }
	@echo "  [5/13] placement (budget + weighted + start-safe) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/placetest.loft | tee /tmp/story_place.log
	@grep -q "PLACEMENT OK" /tmp/story_place.log || { echo "    FAIL: placement"; exit 1; }
	@echo "  [6/13] levels (stairs + descent) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/leveltest.loft | tee /tmp/story_level.log
	@grep -q "LEVEL OK" /tmp/story_level.log || { echo "    FAIL: levels"; exit 1; }
	@echo "  [7/13] hero (XP + level-up) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/herotest.loft | tee /tmp/story_hero.log
	@grep -q "HERO OK" /tmp/story_hero.log || { echo "    FAIL: hero"; exit 1; }
	@echo "  [8/13] curve + ratio cap (gentle, fair, capped) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/curvetest.loft | tee /tmp/story_curve.log
	@grep -q "CURVE OK" /tmp/story_curve.log || { echo "    FAIL: curve"; exit 1; }
	@echo "  [9/13] items (gold + drops + pickup) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/itemtest.loft | tee /tmp/story_item.log
	@grep -q "ITEM OK" /tmp/story_item.log || { echo "    FAIL: items"; exit 1; }
	@echo "  [10/13] equipment (wield + effects) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/equiptest.loft | tee /tmp/story_equip.log
	@grep -q "EQUIP OK" /tmp/story_equip.log || { echo "    FAIL: equipment"; exit 1; }
	@echo "  [11/13] save points (checkpoint respawn + grave) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/savetest.loft | tee /tmp/story_save.log
	@grep -q "SAVE OK" /tmp/story_save.log || { echo "    FAIL: save points"; exit 1; }
	@echo "  [12/13] FOV (facing-cone fog-of-war) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/fovtest.loft | tee /tmp/story_fov.log
	@grep -q "FOV OK" /tmp/story_fov.log || { echo "    FAIL: FOV"; exit 1; }
	@echo "  [13/13] compile gate (parse + bytecode) ..."
	@$(LOFT) --interpret --check $(LOFTFLAGS) $(SRC) >/dev/null 2>&1 || { echo "    FAIL: compile"; exit 1; }
	@echo "  [bundles] regenerate index + character-bundle test ..."
	@python3 tools/gen_bundles.py >/dev/null
	@$(LOFT) --interpret $(LOFTFLAGS) src/bundletest.loft | tee /tmp/story_bundle.log
	@grep -q "BUNDLE OK" /tmp/story_bundle.log || { echo "    FAIL: bundles"; exit 1; }
	@echo "  [bundle-defs] world bundle enemies/items -> catalog merge ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/bundledeftest.loft | tee /tmp/story_bundledef.log
	@grep -q "BUNDLEDEF OK" /tmp/story_bundledef.log || { echo "    FAIL: bundle-defs"; exit 1; }
	@echo "  [defs] class/race/item tables — races now per-bundle via race_catalog ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/deftest.loft | tee /tmp/story_defs.log
	@grep -q "DEFS OK" /tmp/story_defs.log || { echo "    FAIL: defs"; exit 1; }
	@echo "  [rooms] rooms bundle -> room registry ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/roomtest.loft | tee /tmp/story_rooms.log
	@grep -q "ROOMS OK" /tmp/story_rooms.log || { echo "    FAIL: rooms"; exit 1; }
	@echo "  [items] item-use (Explorer potions: heal + custom detect) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/itemusetest.loft | tee /tmp/story_itemuse.log
	@grep -q "ITEM-USE OK" /tmp/story_itemuse.log || { echo "    FAIL: item-use"; exit 1; }
	@echo "  [clock] monster energy/speed (1.0x vs 1.5x) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/clocktest.loft | tee /tmp/story_clock.log
	@grep -q "CLOCK OK" /tmp/story_clock.log || { echo "    FAIL: clock"; exit 1; }
	@echo "  [status] timed statuses (slow / stun, pre-calc expiry) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/statustest.loft | tee /tmp/story_status.log
	@grep -q "STATUS OK" /tmp/story_status.log || { echo "    FAIL: status"; exit 1; }
	@echo "  [persist] dungeon delta round-trip (death-only; regenerate + replay) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/persisttest.loft | tee /tmp/story_persist.log
	@grep -q "PERSIST OK" /tmp/story_persist.log || { echo "    FAIL: persist"; exit 1; }
	@echo "  [surface] depth-0 desert + dungeon entrance (SLICE step 1+2) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/surfacetest.loft | tee /tmp/story_surface.log
	@grep -q "SURFACE OK" /tmp/story_surface.log || { echo "    FAIL: surface"; exit 1; }
	@echo "  [skills] passive melee skill (level + STR -> damage) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/skilltest.loft | tee /tmp/story_skill.log
	@grep -q "SKILL OK" /tmp/story_skill.log || { echo "    FAIL: skill"; exit 1; }
	@echo "  [depth] beginner-dungeon spawn pool is depth-gentle (no lich at 1-3) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/depthtest.loft | tee /tmp/story_depth.log
	@grep -q "DEPTH OK" /tmp/story_depth.log || { echo "    FAIL: depth"; exit 1; }
	@echo "  [ranged] launcher fire action (bow + ammo -> shoot) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/rangedtest.loft | tee /tmp/story_ranged.log
	@grep -q "RANGED OK" /tmp/story_ranged.log || { echo "    FAIL: ranged"; exit 1; }
	@echo "  [quickslot] type-routed auto-slot + bind + press-to-use dispatch ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/quickslottest.loft | tee /tmp/story_quickslot.log
	@grep -q "QUICKSLOT OK" /tmp/story_quickslot.log || { echo "    FAIL: quickslot"; exit 1; }
	@echo "  [quest] desert_surprise overlay: throne set-piece + grant + boss -> infestation ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/questtest.loft | tee /tmp/story_quest.log
	@grep -q "QUEST OK" /tmp/story_quest.log || { echo "    FAIL: quest"; exit 1; }
	@echo "  [msg] message log: ring buffer + event lines (kill/level/descend/nothing) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/msgtest.loft | tee /tmp/story_msg.log
	@grep -q "MSG OK" /tmp/story_msg.log || { echo "    FAIL: msg"; exit 1; }
	@echo "  [invhub] inventory hub: two ring slots + equipped names + reslot bind ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/invhubtest.loft | tee /tmp/story_invhub.log
	@grep -q "INVHUB OK" /tmp/story_invhub.log || { echo "    FAIL: invhub"; exit 1; }
	@echo "  [effect] use-item effects: blink / heal / restore / magic-mapping ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/effecttest.loft | tee /tmp/story_effect.log
	@grep -q "EFFECT OK" /tmp/story_effect.log || { echo "    FAIL: effect"; exit 1; }
	@echo "  [special] monster specials: gaze paralysis + venom + antivenin ward (+ deadlock/struggle) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/specialtest.loft | tee /tmp/story_special.log
	@grep -q "SPECIAL OK" /tmp/story_special.log || { echo "    FAIL: special"; exit 1; }
	@echo "  [unknown] unknown items: per-game flavours / identify-on-use / carry / IF_KNOWN exempt ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/unknowntest.loft | tee /tmp/story_unknown.log
	@grep -q "UNKNOWN OK" /tmp/story_unknown.log || { echo "    FAIL: unknown"; exit 1; }
	@echo "  [race] chosen race applies: stat block / hit-die HP / skills / save / free-action gate ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/racetest.loft | tee /tmp/story_race.log
	@grep -q "RACE OK" /tmp/story_race.log || { echo "    FAIL: race"; exit 1; }
	@echo "  [class] classes from bundles: apply / SP pool / the spell chain (routine-by-id) ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/classtest.loft | tee /tmp/story_class.log
	@grep -q "CLASS OK" /tmp/story_class.log || { echo "    FAIL: class"; exit 1; }
	@echo "  [crystal] the shrine re-spec: bump = interact / apply race+class / roster ..."
	@$(LOFT) --interpret $(LOFTFLAGS) src/crystaltest.loft | tee /tmp/story_crystal.log
	@grep -q "CRYSTAL OK" /tmp/story_crystal.log || { echo "    FAIL: crystal"; exit 1; }
	@echo "  PASS"

# ── Screenshot (Xvfb, mirrors loft's snap_smoke) ──────────────────────────

shot:
	@for t in xvfb-run xdotool import convert; do \
	    command -v $$t >/dev/null 2>&1 || { \
	        echo "  shot: missing '$$t' — install: apt install xvfb xdotool imagemagick"; \
	        exit 1; }; \
	done
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  shot: loft not found ($(LOFT))"; exit 1; }
	@echo "  capturing one frame under Xvfb -> $(SHOT) ..."
	@xvfb-run -a -s "-screen 0 800x600x24" \
	    tools/snap.sh "$(SHOT)" "$(LOFT)" "$(SRC)" "$(LOFTFLAGS)" || { \
	    echo "  shot: FAILED"; exit 1; }
	@echo "  wrote $(abspath $(SHOT))"

# ── Housekeeping ──────────────────────────────────────────────────────────

fmt:
	@for f in src/*.loft; do $(LOFT) --format $$f; done
	@echo "  formatted src/*.loft"

clean:
	@rm -rf src/.loft .loft $(HTML) $(SHOT) /tmp/story_*.log
	@echo "  cleaned: $(HTML) $(SHOT) caches"
