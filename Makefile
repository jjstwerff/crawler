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
#   make probe    Pixel-probe gate (PLAN-RENDER P0): render the probe scenes
#                 under Xvfb (gpushot + any src/*probe.loft), then assert known
#                 pixels via tools/probe.py against each probes/*.probe spec.
#
#   make fmt      Format src/*.loft in place.
#   make clean    Remove generated artifacts (story.html, story.png, caches).
#   make help     Print this overview again.
#
# Configuration (override on the command line, e.g. make play LOFT_REPO=...):
#
#   (default)         Run the system-installed `loft` (on PATH): it self-locates
#                     its stdlib (/usr/local/share/loft) and auto-loads registry
#                     libraries (e.g. `graphics`, declared in loft.toml) on `use`.
#                     The ../loft SIBLING checkout is required for the games kernel
#                     (engine_host, PLAN-KERNEL) until it is registry-published.
#                     Keep the installed binary current with
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
# LIB_DEPS: extracted library packages crawler consumes during development (EXTRACTION.md).
# ../loft-libs-core-main is a read-only `git worktree` of that repo's origin/main (create:
# `git -C ../loft-libs-core worktree add ../loft-libs-core-main origin/main`) so crawler
# tracks the MERGED lib state regardless of which branch the working repo has checked out.
# After a registry release these move to version deps and the worktree flag drops.
# ../loft/lib carries the @PLN18 games kernel (engine_host — story's loop since
# PLAN-KERNEL K1); its natives ride the installed loft binary. Sibling checkout
# required until engine_host is registry-published.
# NOTE (PLAN-RENDER L0): consuming the `graphics` sibling (--lib ../loft-libs-graphics/)
# is VERIFIED to outrank the registry copy — but the installed 0.8.5 has the #322
# stale-program-cache bug, so it keeps the registry binding until the cache is busted.
# Wire it at P5 (when the §6(a) substrate edits begin) AFTER a toolchain refresh past
# the #322 fix; until then it'd make resolution cache-state-dependent for no gain.
LIB_DEPS    := --lib ../loft-libs-core-main/ --lib ../loft-libs-world/ --lib ../loft/lib/
BUNDLE_LIBS := $(addprefix --lib ,$(wildcard bundles/*/) $(wildcard bundles/*/items/))
LOFTFLAGS := $(LOFTFLAGS) $(LIB_DEPS) $(BUNDLE_LIBS)

# Which loft repo `make loft-doctor` compares the installed binary against.
REF_REPO ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../loft2)

# Game entry (window + loop) · headless kernel self-test · build artifacts.
# (Comments live ABOVE the assignments: a trailing `# …` keeps the spaces
# before it IN the value, which breaks quoted "$(VAR)" uses.)
SRC   := src/story.loft
KTEST := src/selftest.loft
HTML  := story.html
SHOT  := story.png

.PHONY: help play game serve test check check-native shot probe viewer viewer-release viewer-gold viewer-gold-talus bundles fmt clean all loft-doctor

# Default target: print the overview above.
help:
	@sed -n '/^# ==== What can this Makefile do for you/,/^# ====/p' Makefile \
	  | sed 's/^# \{0,1\}//'

# Convenience: format + compile gate.
all: fmt check

# ── Run ────────────────────────────────────────────────────────────────

# The bundle registries regenerate whenever a manifest changed — drop a bundle
# dir and `make play` wires it (BUNDLE.md § Game-start coherence; the test gate
# re-scans regardless).
src/bundles.loft: $(wildcard bundles/*/bundle.json) src/genbundles.loft
	@$(LOFT) --interpret src/genbundles.loft 2>/dev/null | grep gen_bundles: || true
	@echo "  bundles: registries regenerated"

bundles: src/bundles.loft

play: src/bundles.loft
	@echo "  [1/2] checking loft toolchain ..."
	@command -v $(LOFT) >/dev/null 2>&1 || { \
	    echo "    FAIL: loft not found ($(LOFT))."; \
	    echo "    Install it:  ( cd ../loft && make install )   then: make loft-doctor"; \
	    echo "    Or use a repo build:  make play LOFT_REPO=../loft2"; \
	    exit 1; }
	@echo "  [2/2] launching story (Esc quits; N = next world — re-scans bundles) ..."
	@while :; do \
	    $(LOFT) $(LOFTFLAGS) $(SRC); \
	    [ -f .story_next ] || break; \
	    echo "  next world (bundles re-scanned; the restart IS the loading beat) ..."; \
	done

# ── Browser build ────────────────────────────────────────────────────────

game: src/bundles.loft
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

check: src/bundles.loft
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
	@tools/run_tests.sh "$(LOFT)" "$(LOFTFLAGS)" "$(KTEST)" "$(SRC)"

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

# ── Pixel probes (Xvfb; PLAN-RENDER P0) ───────────────────────────────────
# Render side: gpushot (the R1+R3 scene) + every src/*probe.loft, each a
# deterministic scene -> gl_screenshot. Assert side: tools/probe.py per
# probes/*.probe spec (point colors / ramps / golden diffs); exit 1 on FAIL.
# gl_screenshot reads the GL framebuffer — reliable under Xvfb (the
# positional caveat applies only to `make shot`'s X11 window grab).

probe:
	@command -v xvfb-run >/dev/null 2>&1 || { \
	    echo "  probe: missing xvfb-run — install: apt install xvfb"; exit 1; }
	@python3 tools/probe.py --selftest >/dev/null || { \
	    echo "  probe: harness self-test FAILED"; exit 1; }
	@echo "  [render] src/gpushot.loft -> /tmp/gpu_r3.png ..."
	@xvfb-run -a -s "-screen 0 800x600x24" \
	    $(LOFT) --interpret $(LOFTFLAGS) src/gpushot.loft >/dev/null 2>&1 || { \
	    echo "  probe: gpushot render FAILED"; exit 1; }
	@for p in src/*probe.loft; do [ -e "$$p" ] || continue; \
	    echo "  [render] $$p ..."; \
	    xvfb-run -a -s "-screen 0 800x600x24" \
	        $(LOFT) --interpret $(LOFTFLAGS) $$p >/dev/null 2>&1 || { \
	        echo "  probe: $$p render FAILED"; exit 1; }; done
	@fail=0; for s in probes/*.probe; do \
	    python3 tools/probe.py $$s || fail=1; done; \
	    [ $$fail -eq 0 ] || { echo "  probe: FAILURES"; exit 1; }
	@echo "  probe: all specs green"

# ── @PLN2 chunked-LOD terrain viewer (S5) ─────────────────────────────────
# `make viewer`      — interactive dual split (left detail | right overworld);
#                      WASD pan, Q/E zoom the detail (left) camera, Esc quits.
# `make viewer-gold` — headless: render the dual frame under Xvfb, diff vs the
#                      golden (imagemagick `compare`, fuzz-tolerant). On first run
#                      (no golden) it prints the copy command to adopt the frame.
# `make viewer-release` — the NATIVE (rustc -O) viewer: ~22x the interpreter on the chunk hot
#                      path (measured: per-chunk 1024ms -> 46ms; startup ~38s -> ~2s). loft
#                      --native-release builds-if-needed (caches the compiled binary; recompiles
#                      only when src changes) then runs. Native GL from a *consumer* project is
#                      currently gated upstream (graphics P269 registration + a `cfg_if`
#                      StableCrateId link collision — see plans/2-chunked-lod-world/
#                      s5-viewer-smooth.md). This target is NATIVE-ONLY: it sets
#                      LOFT_REQUIRE_NATIVE=1 (loft hard-errors instead of silently interpreting any
#                      library) and never falls back to the interpreter — if native is unavailable
#                      it reports why and exits non-zero. Use `make viewer` for the interpreter.
# The viewer resolves entirely from installed libs: graphics/hex_grid/hex_terrain from the
# registry (declared in loft.toml), math from the installed stdlib. No sibling --lib dirs — so
# it doesn't depend on ../loft-libs-* checkouts and avoids the source-lib native-compile fallback.
# (story/test still need $(LIB_DEPS): engine_host is sibling-only, not registry-published.)
VIEWER_FLAGS :=
VIEWER_GOLD  := tools/golden/viewer_s5e.png
VIEWER_GOLD_TALUS := tools/golden/viewer_s5e_talus.png

viewer:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  viewer: loft not found ($(LOFT))"; exit 1; }
	@echo "  [viewer] DEFAULT: real 80x80 Ortler dual screen — left = real OSM landcover, right ="
	@echo "           our model's elevation bands (@PLN1 adequacy comparison) over the real DEM."
	@echo "           FREE CAM: mouse = look around, WASD = pan, Shift = faster, Space = brake; Esc quits."
	@echo "           Opt-in: VIEWER_FLYKEYS=1 (keyboard-only fly), VIEWER_OVERWORLD=1 (procedural"
	@echo "           full landscape), VIEWER_DETAIL=1 (detail slice, +VIEWER_TALUS=1 talus pane) ..."
	@$(LOFT) --interpret $(VIEWER_FLAGS) src/viewer.loft

# Native (rustc -O) viewer — NATIVE ONLY. Runs --native-release directly (the real build, which
# `--check --native` does NOT fully exercise — it false-passes on P269), with LOFT_REQUIRE_NATIVE=1
# so loft hard-errors instead of silently interpreting any library. NO interpreter fallback: on a
# native failure it prints why and exits non-zero. Use `make viewer` for the interpreter.
# Currently upstream-gated: registry graphics isn't registered for --native (loft#396), and a
# coherent-tree build needs the graphics native cdylib rebuilt for the current rustc (E0514).
viewer-release:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  viewer-release: loft not found ($(LOFT))"; exit 1; }
	@echo "  [viewer-release] NATIVE (rustc -O) viewer — no interpreter fallback; WASD/QE pan-zoom, Esc quits ..."
	@LOFT_REQUIRE_NATIVE=1 $(LOFT) --native-release $(VIEWER_FLAGS) src/viewer.loft || { \
	    echo ""; \
	    echo "  viewer-release: NATIVE build FAILED — not falling back to the interpreter (by design)."; \
	    echo "    Native GL from a consumer is upstream-gated: graphics #native not registered for"; \
	    echo "    --native (loft#396); a coherent-tree build needs the graphics native cdylib rebuilt"; \
	    echo "    for the current rustc (E0514). See plans/2-chunked-lod-world/s5-viewer-smooth.md."; \
	    exit 1; \
	  }

viewer-gold:
	@command -v xvfb-run >/dev/null 2>&1 || { echo "  viewer-gold: missing xvfb-run"; exit 1; }
	@command -v compare  >/dev/null 2>&1 || { echo "  viewer-gold: missing imagemagick 'compare'"; exit 1; }
	@echo "  [viewer-gold] rendering dual frame under Xvfb ..."
	@rm -f /tmp/viewer_s5e.png
	@VIEWER_SMOKE=1 xvfb-run -a -s "-screen 0 800x600x24" \
	    $(LOFT) --interpret $(VIEWER_FLAGS) src/viewer.loft >/dev/null 2>&1 || { \
	    echo "  viewer-gold: render FAILED"; exit 1; }
	@test -f /tmp/viewer_s5e.png || { echo "  viewer-gold: no frame produced"; exit 1; }
	@if [ ! -f $(VIEWER_GOLD) ]; then \
	    echo "  viewer-gold: no golden yet. Review /tmp/viewer_s5e.png; if good:"; \
	    echo "      mkdir -p tools/golden && cp /tmp/viewer_s5e.png $(VIEWER_GOLD)"; \
	    exit 1; \
	  fi
	@d=$$(compare -metric AE -fuzz 6% $(VIEWER_GOLD) /tmp/viewer_s5e.png /tmp/viewer_s5e_diff.png 2>&1 || true); \
	  d=$${d%% *}; \
	  echo "  viewer-gold: differing pixels (fuzz 6%) = $$d"; \
	  case "$$d" in ''|*[!0-9]*) echo "  viewer-gold: compare error: $$d"; exit 1;; esac; \
	  if [ "$$d" -gt 800 ]; then echo "  viewer-gold: GOLDEN MISMATCH (>800 px) — see /tmp/viewer_s5e_diff.png"; exit 1; fi; \
	  echo "  viewer-gold: golden OK"

# `make viewer-gold-talus` — like viewer-gold but VIEWER_TALUS=1, so the RIGHT pane is the S6
# talus model (talus_chunk: relax + flow_accumulate). Gates that geomorphology path against its
# own golden; the model golden (viewer-gold) covers the plain pane.
viewer-gold-talus:
	@command -v xvfb-run >/dev/null 2>&1 || { echo "  viewer-gold-talus: missing xvfb-run"; exit 1; }
	@command -v compare  >/dev/null 2>&1 || { echo "  viewer-gold-talus: missing imagemagick 'compare'"; exit 1; }
	@echo "  [viewer-gold-talus] rendering dual frame (talus B-pane) under Xvfb ..."
	@rm -f /tmp/viewer_s5e.png
	@VIEWER_SMOKE=1 VIEWER_TALUS=1 xvfb-run -a -s "-screen 0 800x600x24" \
	    $(LOFT) --interpret $(VIEWER_FLAGS) src/viewer.loft >/dev/null 2>&1 || { \
	    echo "  viewer-gold-talus: render FAILED"; exit 1; }
	@test -f /tmp/viewer_s5e.png || { echo "  viewer-gold-talus: no frame produced"; exit 1; }
	@cp /tmp/viewer_s5e.png /tmp/viewer_s5e_talus.png
	@if [ ! -f $(VIEWER_GOLD_TALUS) ]; then \
	    echo "  viewer-gold-talus: no golden yet. Review /tmp/viewer_s5e_talus.png; if good:"; \
	    echo "      mkdir -p tools/golden && cp /tmp/viewer_s5e_talus.png $(VIEWER_GOLD_TALUS)"; \
	    exit 1; \
	  fi
	@d=$$(compare -metric AE -fuzz 6% $(VIEWER_GOLD_TALUS) /tmp/viewer_s5e_talus.png /tmp/viewer_s5e_talus_diff.png 2>&1 || true); \
	  d=$${d%% *}; \
	  echo "  viewer-gold-talus: differing pixels (fuzz 6%) = $$d"; \
	  case "$$d" in ''|*[!0-9]*) echo "  viewer-gold-talus: compare error: $$d"; exit 1;; esac; \
	  if [ "$$d" -gt 800 ]; then echo "  viewer-gold-talus: GOLDEN MISMATCH (>800 px) — see /tmp/viewer_s5e_talus_diff.png"; exit 1; fi; \
	  echo "  viewer-gold-talus: golden OK"

# ── Housekeeping ──────────────────────────────────────────────────────────

fmt:
	@for f in src/*.loft; do $(LOFT) --format $$f; done
	@echo "  formatted src/*.loft"

clean:
	@rm -rf src/.loft .loft $(HTML) $(SHOT) /tmp/story_*.log
	@echo "  cleaned: $(HTML) $(SHOT) caches"
