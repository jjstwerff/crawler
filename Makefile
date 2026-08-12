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
#   make libcheck Library seam (ADOPTION.md P4): the lock names every declared
#                 dep, no --lib tree shadows a locked package, no module is a
#                 fork of one, no type name collides with one.  ~1 s, no build.
#
#   make doccheck Doc seam: every relative link resolves, every backticked
#                 crawler path exists, every root doc is in CLAUDE.md's routing
#                 table, every nested doc is pointed at.  ~1 s, no build.
#
#   make check-native
#                 Validate the NATIVE / wasm codegen path (run before
#                 `make game`).  Needs the loft toolchain's rlibs to match
#                 your system rustc — rebuild loft if it reports E0514.
#
#   make shot     Render one frame under Xvfb and save story.png.
#
#   make probe    Pixel-probe gate (plan #7 P0): render the probe scenes
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
#                     (engine_host, plan #6) until it is registry-published.
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
# LIB_DEPS — ONE RESOLUTION PATH (ADOPTION.md P3, 2026-08-09).
#
# THE REGISTRY IS AUTHORITATIVE. Every published package crawler uses resolves from
# loft.lock and nowhere else; a --lib sibling tree OUTRANKS the registry copy, so each
# one here is a silent override waiting to happen. Two paths that can disagree without
# a word is what this line used to be: `random` was locked at 0.1.0 while the build
# quietly took the working tree's 0.2.0 — and the source uses 0.2.0's `RandStream`, so
# the LOCK DESCRIBED A BUILD THAT COULD NOT COMPILE. Nothing reported it, because the
# path that worked was never the path that was written down.
#
# ⚠ THE ONLY LEGAL --lib IS A PACKAGE THAT IS NOT PUBLISHED, and it must say why here.
#   ../loft/lib   — engine_host (@PLN18 games kernel, story's loop since plan #6 K1).
#                   Not on the registry; its natives ride the installed loft binary.
#                   Drop this the day engine_host is published.
# Removed when their packages went to the registry, as the previous note here
# anticipated ("after a registry release these move to version deps"):
#   ../loft-libs-core-main  — random/regex/crypto/cbor/arguments, all published.
#   ../loft-libs-world      — the hex_* family, all published.
# To test against an unreleased sibling, add --lib ON THE COMMAND LINE for that run.
# Do not put it back here: an override that outlives the experiment is the bug above.
LIB_DEPS    := --lib ../loft/lib/
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

.PHONY: apidoc apidoc-check help play game serve test check check-native shot probe ovshot viewer viewer-release viewer-gold viewer-gold-talus bundles fmt clean all loft-doctor region region-bin near-test hydro-test trimesh-test rivers-test phony-check libcheck doccheck

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

# LIBRARIES.md — the signature index for every declared dependency, regenerated from the
# registry copies the build actually resolves. Looking a signature up used to mean reading
# the package (~500 lines of source for ~20 signatures, measured over one session).
apidoc:
	@tools/api_index.sh

# ⚠ AND THE CHECK IS WHAT KEEPS IT HONEST. A generated file nobody verifies is a hand-kept
# file with extra steps: it drifts the first time a dependency moves and reads exactly as
# authoritative while it lies. Same shape as `make bundles`' round-trip.
apidoc-check:
	@tools/api_index.sh /tmp/story_apidoc.md >/dev/null
	@diff -q LIBRARIES.md /tmp/story_apidoc.md >/dev/null || { \
	    echo "    FAIL: LIBRARIES.md is stale — run 'make apidoc' and commit the result."; \
	    diff LIBRARIES.md /tmp/story_apidoc.md | head -20; exit 1; }
	@echo "  [apidoc] LIBRARIES.md matches the registry"

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

# ⚠ THE ENTRY POINTS ARE PLURAL, AND ONLY ONE OF THEM USED TO BE COMPILED. $(SRC) is the
# game; the render scenes are separate `main`s that nothing else builds, so a fault in one
# waited for a ten-minute `make probe` to surface — or never surfaced at all, because a
# WARNING fails nothing. src/worldprobe.loft carried a lost write for two months exactly that
# way: it bound `vv = s.vis` and mutated the COPY, so the scene rendered 0 remembered cells
# and two probes in probes/ asserted a state it had stopped building. The evidence that it
# was the SCENE and never the goldens: with the write fixed, `rem_grass` passes again at the
# coordinate measured 2026-06-12, at dmax=0.
#
# So this gate now compiles every entry point, and it FAILS ON `lost-write`. That warning is
# never intentional — the compiler is saying a mutation does nothing — which is what earns it
# a hard failure, unlike `redundant-coalesce` (CLAUDE.md says leave those alone).
#
# ⚠ WHICH ENTRY POINTS, AND WHY NOT ALL OF THEM. The rule is: EVERYTHING A GATE OR A COMMITTED
# ASSET DEPENDS ON. That is the game, the four scenes `make probe` renders, and ovshot (which
# draws README.md's headline world map — it had rotted the same way, six undischarged `float?`
# divides and a `float` default on a vector<single>, and nothing had compiled it since the loft
# rule tightened). src/ has ~130 `fn main()`s; the rest are one-off tools and diagnostic scenes
# whose breakage costs one run, not a false-green gate. Sweep them on demand — they take ~1.4 s
# each and two of eighteen were broken when this was written:
#   for f in src/*.loft; do loft --interpret --check $(LOFTFLAGS) $$f >/dev/null || echo $$f; done
# src/viewer.loft is deliberately out: it needs $(VIEWER_FLAGS), not $(LOFTFLAGS), and compiling
# its generated per-region data module takes minutes. `make viewer` is its gate.
CHECK_ENTRIES = $(SRC) src/gpushot.loft $(PROBE_SCENES) src/ovshot.loft

check: src/bundles.loft
	@echo "  compiling (parse + bytecode gate) ..."
	@fail=0; for e in $(CHECK_ENTRIES); do \
	    out=$$($(LOFT) --interpret --check $(LOFTFLAGS) $$e 2>&1); \
	    if [ $$? -ne 0 ]; then \
	        echo "    FAIL: compile $$e"; echo "$$out" | grep -E '^error' | head -5; fail=1; \
	    elif echo "$$out" | grep -q 'warning\[lost-write\]'; then \
	        echo "    FAIL: $$e — a write that goes nowhere (loft C86: a whole-value bind COPIES)"; \
	        echo "$$out" | grep -A4 'warning\[lost-write\]' | head -24; fail=1; \
	    else echo "    ok  $$e"; fi; \
	done; [ $$fail -eq 0 ] || exit 1

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

# ⚠ A .PHONY NAME WITH NO RECIPE IS A SILENT NO-OP — `make` prints "Nothing to be done" and
# exits 0, so a gate passes by not running. That happened on 2026-08-11: an edit adding `ovshot`
# REPLACED this target instead of landing beside it, and the break survived a commit because the
# session had already run the gate before the edit. `phony-check` asserts every .PHONY name is
# really defined; the gate runs it first, so the gate can no longer be deleted quietly.
phony-check:
	@mk=$(firstword $(MAKEFILE_LIST)); \
	  phony=$$(grep -h '^\.PHONY:' $$mk | sed 's/^\.PHONY://'); \
	  miss=""; for t in $$phony; do grep -qE "^$$t:" $$mk || miss="$$miss $$t"; done; \
	  [ -z "$$miss" ] || { echo "  FAIL: .PHONY names with no target:$$miss"; exit 1; }; \
	  echo "  ok  every .PHONY name resolves to a real target"

test: phony-check
	@tools/run_tests.sh "$(LOFT)" "$(LOFTFLAGS)" "$(KTEST)" "$(CHECK_ENTRIES)"

# ── README's world maps ──────────────────────────────────────────────────
# `make ovshot` re-draws doc/world_loft.png (the flat map) and doc/world_ortho.png (the
# orthographic relief) straight from overland.loft at 10 m/px, in the in-game palette.
#
# ⚠ NATIVE, NOT BY PREFERENCE. Interpreted this samples 1350x910 px through the overland and
# runs past ten minutes; --native-release does it in ~35 s. That is the documented 7-22x, and
# it is why this target exists at all: there was none, so the invocation had to be
# reconstructed each time — and the file quietly stopped compiling for two months (six
# undischarged `float?` divides from a tightened rule) with nothing to notice.
#
# ⚠ AND THE OUTPUT IS A ROUND-TRIP CHECK, LIKE `make bundles`. Re-running it must leave
# doc/*.png BYTE-IDENTICAL unless the world derivation genuinely changed — `git status doc/`
# is the assertion. It held across two months and a backend change (2026-08-11: regenerated
# native, identical to the June images built by the interpreter), which is a real statement
# about the world being deterministic. A diff here is either a deliberate worldgen change or
# a bug; either way, look at the picture before committing it.
ovshot:
	@echo "  [ovshot] doc/world_loft.png + doc/world_ortho.png (native, ~35 s) ..."
	@$(LOFT) --native-release $(LOFTFLAGS) $(BUNDLE_LIBS) src/ovshot.loft 2>&1 | grep '^ovshot:'
	@if [ -n "$$(git status --porcelain doc/ 2>/dev/null)" ]; then \
	    echo "  ⚠ doc/ CHANGED — the world derivation moved. Look at the images before committing:"; \
	    git status --short doc/; \
	else echo "  doc/ byte-identical — the world has not moved"; fi

# The library seam on its own (ADOPTION.md P4). `make test` runs it too; this is the
# ~1 s standalone form for when you have just touched loft.toml, the lock, LIB_DEPS,
# or added a module. Reads committed files only — no toolchain, no network, no build.
libcheck:
	@python3 tools/libcheck.py

# The doc seam. `make test` runs it too; this is the standalone form for when you have just
# moved, renamed or deleted a file a doc names. Reads committed markdown only — no toolchain,
# no network, no build.
#
# ⚠ IT EXISTS BECAUSE THE HAND AUDITS WERE WRONG. Two doc passes on 2026-08-11 fixed the same
# rot class by hand, and one of those audits miscounted its own evidence. The invariants a
# command can settle — a link that resolves, a path that exists, a doc something points at —
# should not be anyone's job to remember.
doccheck:
	@python3 tools/doccheck.py

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

# ── Pixel probes (Xvfb; plan #7 P0) ───────────────────────────────────
# Render side: gpushot (the R1+R3 scene) + every src/*probe.loft, each a
# deterministic scene -> gl_screenshot. Assert side: tools/probe.py per
# probes/*.probe spec (point colors / ramps / golden diffs); exit 1 on FAIL.
# gl_screenshot reads the GL framebuffer — reliable under Xvfb (the
# positional caveat applies only to `make shot`'s X11 window grab).

# ⚠ THE GATE'S SCENES ARE NAMED, NOT GLOBBED — `src/*probe.loft` is not the gate.
# A scene belongs here only if it is HEADLESS (renders, screenshots, exits on its own) and
# produces a PNG that some `probes/*.probe` asserts. `src/reloadprobe.loft` matches the old
# glob and is neither: it is plan #6 K3's live-reload verification, a WINDOWED program that
# waits for Esc. Under Xvfb with no input it never exits, so `make probe` HUNG — and a hang
# reads as progress, which is why it went unnoticed longer than a failure would have.
# (Found in plan #16 `M4`: three undischarged `float?` divides in gpushot.loft aborted the
# target one step earlier and MASKED the hang. Two rots stacked, the first hiding the second.)
PROBE_SCENES  := src/bootprobe.loft src/postprobe.loft src/worldprobe.loft
PROBE_TIMEOUT := 180

probe:
	@command -v xvfb-run >/dev/null 2>&1 || { \
	    echo "  probe: missing xvfb-run — install: apt install xvfb"; exit 1; }
	@python3 tools/probe.py --selftest >/dev/null || { \
	    echo "  probe: harness self-test FAILED"; exit 1; }
	@echo "  [render] src/gpushot.loft -> /tmp/gpu_r3.png ..."
	@timeout $(PROBE_TIMEOUT) xvfb-run -a -s "-screen 0 800x600x24" \
	    $(LOFT) --interpret $(LOFTFLAGS) src/gpushot.loft >/dev/null 2>&1 || { \
	    echo "  probe: gpushot render FAILED or timed out (>$(PROBE_TIMEOUT)s)"; exit 1; }
	@for p in $(PROBE_SCENES); do [ -e "$$p" ] || continue; \
	    echo "  [render] $$p ..."; \
	    timeout $(PROBE_TIMEOUT) xvfb-run -a -s "-screen 0 800x600x24" \
	        $(LOFT) --interpret $(LOFTFLAGS) $$p >/dev/null 2>&1 || { \
	        echo "  probe: $$p render FAILED or timed out (>$(PROBE_TIMEOUT)s)"; exit 1; }; done
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
# Viewer-side libs added on top of LOFTFLAGS: src/realworld/ (region.loft, hydro.loft,
# trimesh.loft) and src/regions/ (ortler.loft = the generated per-region data module).
VIEWER_FLAGS := --lib src/realworld/ --lib src/regions/
VIEWER_GOLD  := tools/golden/viewer_s5e.png
VIEWER_GOLD_TALUS := tools/golden/viewer_s5e_talus.png

viewer:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  viewer: loft not found ($(LOFT))"; exit 1; }
	@echo "  [viewer] DEFAULT: real 80x80 Ortler dual screen — left = PER-TRIANGLE OSM landcover (18"
	@echo "           tri/hex), right = PER-CELL elevation-band model (@PLN1 adequacy comparison)."
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

# ── Real-world region data (doc/viewer-design.md §9) ─────────────────────
#
# Pipeline: data/regions/<name>.bin (raw little-endian binary, packed by the
# tiny Python step) → src/regions/<name>.loft (numeric-literal module, written
# by src/realworld/build_region.loft in LOFT). Every consumer just
#   use regions::<name>;
# and loft's program cache mmaps the compiled image on every launch.
#
#   make region-bin   — one-time NPZ → .bin packing (the only remaining Python)
#                       REGION=<name>, default ortler.
#   make region       — runs the LOFT builder: read .bin, write the .loft.
#                       REGION=<name>, default ortler.
#
# After both: data/regions/<name>.bin + src/regions/<name>.loft are committed
# so a fresh clone needs neither step to run the viewer.
#
# Adding a new region (e.g. the Welsh sea-cliff coast):
#   1. extend plans/1-ortler-worldgen-fixture/dump_region_bin.py with a
#      `dump_wales()` per-region branch (or the next-gen loft fetcher).
#   2. `make region-bin REGION=wales` writes data/regions/wales.bin.
#   3. `make region     REGION=wales` writes src/regions/wales.loft.
#   4. commit both.
REGION ?= ortler

region-bin:
	@python3 plans/1-ortler-worldgen-fixture/dump_region_bin.py --region $(REGION)

region:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  region: loft not found ($(LOFT))"; exit 1; }
	@LOFT_REGION=$(REGION) $(LOFT) --interpret --lib src/realworld/ $(LOFTFLAGS) build_region.loft

# Standalone hydrology smoke: pit-fill + flow + acc + I-FLOW validation on
# the active region. The viewer will fold the same call into its startup once
# wired (design doc §11 step 5).
# @PLN48 consumer validation: crawler stores enemies as a flat vector<Enemy>, so every
# proximity query is a linear scan. This asks whether `spatial<Mob[q,r]>` answers the same
# question by walking only the Morton interval — against a brute-force oracle, on 2000 mobs
# and 500 queries. It is crawler's evidence FOR loft, not a crawler feature, which is why it
# is a named target rather than a gate row.
#
# ⚠ It had never compiled. It was written against the upstream PLAN's spelling — `spacial`,
# which is how plans/48-spacial-index/ is named — and the feature shipped as `spatial`, which
# the parser rejects the other way round. One word, sixteen cascading errors, and no target
# and no gate ever built it, so the validation simply never ran. Its own header promised
# `make near-test`; that target did not exist either. It does now.
near-test:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  near-test: loft not found ($(LOFT))"; exit 1; }
	@$(LOFT) --interpret $(LOFTFLAGS) near_mobs_test.loft

hydro-test:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  hydro-test: loft not found ($(LOFT))"; exit 1; }
	@LOFT_REGION=$(REGION) $(LOFT) --interpret --lib src/realworld/ --lib src/regions/ $(LOFTFLAGS) hydro_test.loft

# Standalone trimesh smoke: build the 18-tri-per-hex VBO for the active
# region and print its size + a watertight spot-check.
trimesh-test:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  trimesh-test: loft not found ($(LOFT))"; exit 1; }
	@LOFT_REGION=$(REGION) $(LOFT) --interpret --lib src/realworld/ --lib src/regions/ $(LOFTFLAGS) trimesh_test.loft

# Standalone rivers smoke: build the river-ribbon mesh for the active region
# (hydro + polyline + textured quad strip) and print its size + a width-check
# against the max-accumulation cell.
rivers-test:
	@command -v $(LOFT) >/dev/null 2>&1 || { echo "  rivers-test: loft not found ($(LOFT))"; exit 1; }
	@LOFT_REGION=$(REGION) $(LOFT) --interpret --lib src/realworld/ --lib src/regions/ $(LOFTFLAGS) rivers_test.loft

# ── Housekeeping ──────────────────────────────────────────────────────────

fmt:
	@for f in src/*.loft; do $(LOFT) --format $$f; done
	@echo "  formatted src/*.loft"

clean:
	@rm -rf src/.loft .loft $(HTML) $(SHOT) /tmp/story_*.log
	@echo "  cleaned: $(HTML) $(SHOT) caches"
