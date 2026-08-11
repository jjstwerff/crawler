#!/usr/bin/env bash
# The headless deterministic test gate (extracted from the Makefile `test` target;
# `make test` delegates here). Same steps, same labels, same /tmp/story_*.log
# files — one table row per test, specials (kernel self-test, compile gate,
# bundle regeneration, the seam grep) written out where they sit in the order.
#
# Args: $1 = loft binary   $2 = loft flags (word-split: --path/--lib …)
#       $3 = kernel selftest .loft   $4 = game entry .loft
set -u
trim() { local s="$1"; s="${s#"${s%%[![:space:]]*}"}"; printf '%s' "${s%"${s##*[![:space:]]}"}"; }
LOFT="$(trim "${1:?loft binary required}")"
FLAGS="${2-}"
KTEST="$(trim "${3:?kernel selftest .loft required}")"
SRC="$(trim "${4:?game entry .loft required}")"

# ── WHICH COMPILER PRODUCED THIS LOG ────────────────────────────────────────
#
# ⚠ `loft --version` IS NOT PROVENANCE. The installed binary reports "2026.8.0" while
# being ../loft's WORKING-TREE build, 15 commits past that tag and sometimes dirty —
# `loft verify-self` says "not a release bundle". It is rebuilt by another agent while
# our gates run: measured 2026-08-09, the binary changed mid-session and cdylibs were
# recompiled DURING a run, whose cargo output landed in this log.
#
# So the hash is the identity. Two logs with different md5 are NOT comparable, and a
# diff between them is not evidence about our code — which cost real time twice before
# this line existed (a warning that appeared once and never again; eight that arrived
# with no source change).
bin="$(command -v "$LOFT" 2>/dev/null || echo "$LOFT")"
echo "  [toolchain] $("$LOFT" --version 2>/dev/null | head -1) · md5 $(md5sum "$bin" 2>/dev/null | cut -c1-12) · $bin · built $(date -r "$bin" '+%Y-%m-%d %H:%M' 2>/dev/null)"
if [ -d ../loft/.git ]; then
  gd=$(git -C ../loft describe --tags --always --dirty 2>/dev/null)
  sib=$(md5sum ../loft/target/release/loft 2>/dev/null | cut -c1-12)
  if [ -n "$sib" ] && [ "$sib" = "$(md5sum "$bin" 2>/dev/null | cut -c1-12)" ]; then
    echo "              IS ../loft's working-tree build: ${gd:-?}  — not a release; provenance is that tree"
  else
    echo "              ../loft describe: ${gd:-?} (the installed binary is NOT that tree's build)"
  fi
fi
if [ -n "${GATE_NO_NATIVE:-}" ]; then
  echo "  [mode] every test --interpret (GATE_NO_NATIVE=1)"
else
  echo "  [mode] 13 heavy tests + playtest run --native-release (·native rows); the rest --interpret."
  echo "         First run after a kernel edit or a loft reinstall pays ~10 s rustc per affected row."
fi

# ── QUIET ON PASS, LOUD ON FAIL, AND ALWAYS SAY WHERE THE TIME WENT ─────────
#
# ⚠ A GREEN TEST'S OUTPUT IS NOISE, AND THE NOISE HID THINGS. `tee`ing every test's
# stdout made a gate log ~100,000 lines, 98% of it compiler advice from runs that
# passed. Diffing two runs — the way a behaviour-preserving change is actually proved
# — meant filtering that by hand every time, and twice this month a real difference
# sat inside it unnoticed for an hour. loft's own Goal F is the rule: a tool that
# reports its good health teaches the reader to skip the line where it eventually
# reports the opposite.
#
# So a passing test prints ONE line, a failing one prints everything that matters,
# and the full output is still on disk per test (/tmp/story_<name>.log) — which is a
# BETTER diff target than the old combined stream, because it cannot interleave.
#
# ⚠ THE SECONDS ARE NOT DECORATION. A suite that takes minutes has to say where they
# went or nobody can shorten it: measured, six of 88 tests hold most of the wall time
# (quest 51s, travel 30s, replay 26s, surface 26s, sweep 22s, mesh 20s) and most of
# the rest are under two. That is only actionable if the gate prints it — and it was
# acted on: that printout is where NATIVE_TESTS below came from.
#
# GATE_VERBOSE=1 restores the old streaming behaviour for a single run.
GATE_T0=$(date +%s)
GATE_SLOW=$(mktemp)

# ── WHICH TESTS COMPILE, AND WHY ONLY THESE ─────────────────────────────────
#
# `--native-release` runs 7-22x faster than `--interpret` but costs ~10 s of rustc
# the first time a test's generated Rust changes. So the mode is a per-test choice,
# not a gate-wide flag: compiling a 1 s test to save 0.8 s loses nine seconds, while
# compiling questtest saves seventy-three.
#
# Measured 2026-08-10, all 97 tests both ways, back-to-back per test so box load hit both
# arms alike (commit 3bf82be carries the finding; totals below are wall time for the whole
# roster). ⚠ The per-test table is NOT kept anywhere, on purpose — it would rot, and it is
# reproducible on demand: `GATE_NO_NATIVE=1 make test` regenerates the interpreted baseline
# for every row, which is the number you need to decide whether one belongs on this list.
#
#     --interpret                      593 s      what this gate used to be
#     --native-release, cache warm      88 s      6.7x — but only when nothing changed
#     --native-release, kernel edit    518 s      1.1x — 40 tests recompile, a wash
#     --native-release, all cold      1058 s      0.6x — SLOWER than interpreting
#     hybrid (this list)          239-380 s      1.6-2.5x, and it cannot lose
#
# The blanket flip is the trap: the cache key hashes the generated Rust AND the
# installed libloft.rlib mtime, so a `make install` in ../loft resets all 97 to cold,
# and any sim.loft edit resets the 40 that transitively use it. The hybrid can't lose,
# because the long tail of 1-3 s tests never pays for rustc at all.
#
# THE RULE: a test earns a place here by costing MORE THAN ~10 s interpreted — that is
# the compile, so below it the trade is negative. The gate prints every row's seconds
# and lists everything over 5 s on the way out, which is how you re-check the list
# without a profiling session: a native row that still reports double digits, or an
# interpreted row that climbs past ten, is the signal to move it.
#
# ⚠ THESE ROWS NOW EXERCISE A SECOND COMPILER. All 97 passed identically both ways on
# 2026-08-10, so today the modes agree — but a native-codegen bug (LOFT-HANDOFF N1 is
# one) would now surface HERE rather than in `make game`, and it is not our code. That
# is what GATE_NO_NATIVE=1 is for: re-run the red test interpreted, and if it goes
# green the divergence is the backend's, which is a loft ticket, not a crawler fix.
NATIVE_TESTS="questtest stocktest traveltest surfacetest replaytest safetytest
              meshtest fieldtest crystaltest effecttest cavetest roofmatchtest
              sweeptest playtest incursiontest militiatest worldtextest
              horizontest"
# ⚠ NORMALISE THE SEPARATORS, OR THE LIST SILENTLY LIES. The names are written on three
# lines to stay readable, so what separates the LAST name on a line from the first on the
# next is a NEWLINE — and the `case " $NATIVE_TESTS "` membership test below matches on
# SPACES. Unnormalised, exactly the line-final entries fall through to --interpret: the
# first run of this gate ran safetytest (23.8 s) and roofmatchtest interpreted while
# reporting a green PASS, and the only visible trace was a missing ·native tag on two
# rows. Word-splitting collapses every run of whitespace, newlines included, to one space.
# shellcheck disable=SC2086  # the word-splitting IS the normalisation
NATIVE_TESTS=$(printf '%s ' $NATIVE_TESTS)

# ── HOW MANY AT ONCE, AND WHY THE ROWS STILL PRINT IN ORDER ─────────────────
#
# The tests are genuinely independent — separate processes, separate /tmp logs, no
# shared output file (figtest's build/figure.glb is the only write, and it is its
# own) — so the 24 cores were sitting idle for the whole gate. At GATE_JOBS=8 the
# roster takes ~50 s of wall clock against ~4 min serially.
#
# ⚠ THIS WAS BLOCKED, AND THE BLOCK WAS REAL: LOFT-HANDOFF's cdylib-wiring defect
# made a parallel suite fail a DIFFERENT test each run (`-P8` killed fieldtest, `-P4`
# killed wheeltest+linktest, and pre-warming did not help). A suite that is red at
# random is worse than a slow one, so the gate stayed serial. Re-probed 2026-08-10 on
# toolchain 2026.8.0: 9 full passes at -P4/-P8/-P16/-P24 plus one with every native row
# compiling concurrently — all green. That is what re-opened this, and it is also why
# GATE_JOBS=1 stays one word away: if a row ever goes red under load and green alone,
# suspect the defect FIRST, and say so in the ticket rather than editing the test.
#
# ⚠ ORDERED OUTPUT IS NOT COSMETIC. Rows finish out of order, but the log is the
# artifact you diff to prove a change behaviour-preserving (see the note above), and a
# log whose line order depends on scheduling cannot be diffed at all. So workers write
# results to files and ONE printer walks the roster in order, blocking on each row in
# turn — the output is byte-for-byte what the serial gate produced, arriving as fast as
# the pool allows. Do not "simplify" this into printing from the workers.
if [ -n "${GATE_VERBOSE:-}" ]; then
  # The old streaming mode tees each test's stdout as it runs; interleaved across 8
  # workers that is unreadable, so verbose implies serial. It is a debugging mode.
  GATE_JOBS=1
fi
# TWO BOUNDS, AND THEY MEAN DIFFERENT THINGS — cores - 2, capped at 8.
#
# `cores - 2` is COURTESY: this box runs several agents, and the gate is not entitled to all
# of it. It also keeps a 2-core machine from running 8 loft processes at once, which the old
# hardcoded 8 would have done on any box but this one.
#
# The cap of 8 is MEASURED, and it is not a core count — do not "fix" it to track nproc.
# Over 13 full passes: P4 61-91 s · P8 46-109 s · P16 53-67 s · P24 46-63 s. The spread
# inside each column is other agents' load, and it is WIDER than the gap between the
# columns: past 8 the curve is flat, because what is left is one long test (stocktest ~15 s)
# and not many short ones. Amdahl, not thrift — raising the cap buys nothing until the
# slowest row gets faster, and a 64-core box would just run 64 processes to the same finish.
cores=$( { nproc || getconf _NPROCESSORS_ONLN; } 2>/dev/null | head -1 )
case "$cores" in ''|*[!0-9]*) cores=4 ;; esac      # unknown machine: assume small, not huge
auto=$(( cores > 10 ? 8 : (cores > 2 ? cores - 2 : 1) ))
GATE_JOBS=${GATE_JOBS:-$auto}
# ⚠ A BAD OVERRIDE MUST NOT LIMP. GATE_JOBS lands in `[ … -ge "$GATE_JOBS" ]` inside the
# dispatch loop, so a typo ("GATE_JOBS=eight", "GATE_JOBS=0") would either error once per
# row for the whole run or spin the launcher forever. Refuse it here, where the message can
# still say what happened.
case "$GATE_JOBS" in
  ''|*[!0-9]*|0) echo "  [jobs] GATE_JOBS='$GATE_JOBS' is not a positive integer — using $auto"; GATE_JOBS=$auto ;;
esac
echo "  [jobs] ${GATE_JOBS}-wide (GATE_JOBS=1 forces serial; GATE_VERBOSE=1 implies it)"
ROSTER=$(mktemp)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK" "$ROSTER" "$GATE_SLOW"' EXIT

# collect <<EOF — file|marker|log|fail-text|label   (order = the order rows PRINT in)
# collect_one <file> <marker> <log> <fail-text> <label> [program-arg]
#
# ⚠ THE OPTIONAL 6th ARG IS WHAT LETS ONE PROGRAM BE SEVERAL TESTS. playtest.loft is a
# driver; each scripts/*.play is a different claim. Without it they would all report as
# "playtest" and a red one would not say which playthrough broke. It is also why
# playtest earns the native list above its 10 s bar: ONE compile serves all three rows.
#
# ⚠ THE FREE-TEXT LABEL GOES LAST, AND THAT IS LOad-BEARING. Labels contain prose, and
# prose contains pipes: stairtest's is `min tread = sqrt(3)*max|cos|; nosing …`. A reader
# that splits into a fixed number of fields hands the leftovers to whatever variable comes
# last — so with the label in the middle, `cos` landed in the PROGRAM-ARGUMENT slot and
# the row ran as `stairtest cos`, printing itself as `stairtest:cos`. It stayed green only
# because stairtest ignores argv; the same leak into playtest would have silently run a
# different playthrough than the one the row claims. Keeping the label last restores what
# the old 5-field read got for free: the remainder belongs to the prose.
collect_one() { printf '%s|%s|%s|%s|%s|%s\n' "$1" "$2" "$3" "$4" "${6:-}" "$5" >> "$ROSTER"; }
collect() {
  while IFS='|' read -r file marker log fail label; do
    [ -n "$file" ] || continue
    collect_one "$file" "$marker" "$log" "$fail" "$label"
  done
}

# run_one <index> <roster-line> — runs one row and writes its verdict for the printer.
# The result file is written via mv so the printer can never read a half-written line.
run_one() {
  idx=$1
  IFS='|' read -r file marker log fail arg label <<<"$2"
  stem=$(basename "$file" .loft)
  mode=--interpret
  tag=
  if [ -z "${GATE_NO_NATIVE:-}" ]; then
    case " $NATIVE_TESTS " in
      *" $stem "*) mode=--native-release; tag=' ·native' ;;
    esac
  fi
  t0=$(date +%s%N)
  if [ -n "${GATE_VERBOSE:-}" ]; then
    echo "  $label"
    # shellcheck disable=SC2086  # FLAGS must word-split into --path/--lib
    "$LOFT" $mode $FLAGS "$file" ${arg:+"$arg"} | tee "$log"
  else
    # shellcheck disable=SC2086
    "$LOFT" $mode $FLAGS "$file" ${arg:+"$arg"} > "$log" 2>&1
  fi
  ms=$(( ($(date +%s%N) - t0) / 1000000 ))
  name=$stem
  [ -z "$arg" ] || name="$name:$(basename "$arg" .play)"
  st=ok
  grep -q "$marker" "$log" || st=FAIL
  printf '%s|%s|%s|%s|%s|%s\n' "$ms" "$st" "$name" "$tag" "$log" "$fail" > "$WORK/$idx.tmp"
  mv "$WORK/$idx.tmp" "$WORK/$idx.res"
}

# drain — run every collected row through a pool of GATE_JOBS workers, printing each in
# roster order as its verdict lands. Returns non-zero if any row went red.
#
# ⚠ IT REPORTS EVERY FAILURE, NOT THE FIRST. The serial gate exited on the first red,
# which was right when a red cost you the rest of a 13-minute run; at 50 s the whole
# roster is cheaper than a second trip, and "these four broke" is a different diagnosis
# from "this one broke" — especially for a change that touches the kernel.
drain() {
  (
    i=0
    while IFS= read -r line; do
      i=$((i + 1))
      while [ "$(jobs -rp | wc -l)" -ge "$GATE_JOBS" ]; do wait -n; done
      run_one "$i" "$line" &
    done < "$ROSTER"
    wait
  ) &
  pool=$!
  reds=0
  i=0
  while IFS= read -r line; do
    i=$((i + 1))
    # ⚠ NEVER BLOCK FOREVER ON A VERDICT THAT IS NOT COMING. A worker killed outright
    # (OOM, a loft abort that takes the shell with it) writes no result file, and a
    # printer that only waits would hang the gate with no output and no exit code —
    # strictly worse than the failure it is reporting. Once the pool is gone, a missing
    # verdict IS the verdict.
    while [ ! -f "$WORK/$i.res" ]; do
      kill -0 "$pool" 2>/dev/null || break
      sleep 0.1
    done
    if [ ! -f "$WORK/$i.res" ]; then
      printf '  FAIL    ----  %s — worker produced no verdict (killed?); log: %s\n' \
        "$(basename "${line%%|*}" .loft)" "$(echo "$line" | cut -d'|' -f3)"
      reds=$((reds + 1))
      continue
    fi
    IFS='|' read -r ms st name tag log fail < "$WORK/$i.res"
    printf '%s %s\n' "$ms" "$name" >> "$GATE_SLOW"
    if [ "$st" = ok ]; then
      [ -n "${GATE_VERBOSE:-}" ] || printf '  ok %6d.%ds  %s%s\n' "$((ms / 1000))" "$(( (ms % 1000) / 100 ))" "$name" "$tag"
    else
      # ⚠ A FAILURE PRINTS ITS EVIDENCE. The old form printed only "FAIL: <text>" and
      # left the reader to go find the log; the run had already scrolled past.
      printf '  FAIL %4d.%ds  %s%s — %s\n' "$((ms / 1000))" "$(( (ms % 1000) / 100 ))" "$name" "$tag" "$fail"
      echo "       ---- $log (tail, compiler noise stripped) ----"
      grep -vE '^advice|^note:|^warning|^ *[0-9]+ \||^ *\||^ *-->|^ *\^|^$' "$log" | tail -12 | sed 's/^/       /'
      # ⚠ SAY WHOSE BUG IT MIGHT BE. This row ran through rustc, so a red here has two
      # possible authors; the one-line re-run separates them before anyone starts reading
      # crawler diffs for a fault that is in the native backend.
      [ -z "$tag" ] || echo "       (ran --native-release; GATE_NO_NATIVE=1 make test re-runs it interpreted — green there = a loft codegen divergence, not our change)"
      # ⚠ AND WHETHER IT MIGHT BE THE SCHEDULE. Parallel is new; a row that is red here
      # and green alone is the cdylib defect above, not a change to this test.
      [ "$GATE_JOBS" -eq 1 ] || echo "       (ran with GATE_JOBS=$GATE_JOBS; GATE_JOBS=1 make test re-runs the gate serially — green there = the cdylib concurrency defect, LOFT-HANDOFF)"
      reds=$((reds + 1))
    fi
  done < "$ROSTER"
  wait "$pool"
  [ "$reds" -eq 0 ]
}

# ── THE SERIAL PRELUDE: everything the parallel rows are allowed to ASSUME ──
#
# Four preconditions, in order, before any test starts. Three of them were previously
# scattered BETWEEN the tables, which only worked because execution was serial.
#
# ⚠ THE BUNDLE REGENERATION IS THE ONE THAT HAD TO MOVE. It rewrites the generated
# src/*_gen.loft registries that ~45 tests read, so with a worker pool it cannot sit in
# the middle of the roster — a test would read a registry being rewritten under it, and
# the failure would look like a content bug and move between runs. Hoisting it also
# fixes something the serial order got away with: the rows that used to run BEFORE it
# were reading whatever registries happened to be on disk. Now every row sees freshly
# generated ones, which is what `make play` sees.
#
# The self-test is first because it is the kernel's own claim: if that is broken, the
# other 97 rows are 97 restatements of the same fault. The compile gate and the two
# seam checks are pure reads — they are here so a broken build fails in seconds rather
# than after the pool has run.

echo "  [prelude 1/4] kernel self-test (headless, deterministic) ..."
# shellcheck disable=SC2086
if [ -n "${GATE_VERBOSE:-}" ]; then
  "$LOFT" --interpret $FLAGS "$KTEST" | tee /tmp/story_selftest.log
else
  "$LOFT" --interpret $FLAGS "$KTEST" > /tmp/story_selftest.log 2>&1
fi
grep -q "ALL CHECKS PASS" /tmp/story_selftest.log || {
  echo "  FAIL  kernel self-test did not pass — /tmp/story_selftest.log"
  grep -vE '^advice|^note:|^warning|^ *[0-9]+ \||^ *\||^ *-->|^ *\^|^$' /tmp/story_selftest.log | tail -12 | sed 's/^/       /'
  exit 1; }

echo "  [prelude 2/4] compile gate (parse + bytecode) ..."
# shellcheck disable=SC2086
"$LOFT" --interpret --check $FLAGS "$SRC" >/dev/null 2>&1 || {
  echo "    FAIL: compile"; exit 1; }

echo "  [prelude 3/4] regenerate bundle registries (before any row reads them) ..."
"$LOFT" --interpret src/genbundles.loft >/dev/null 2>&1

echo "  [prelude 4/4] seams: no engine spawn by monster key (plan #4 A) · library seam (ADOPTION.md P4) ..."
if grep -n 'mon_find("' src/*.loft | grep -v spawn_crystal | grep -q .; then
  echo "    FAIL: engine references a monster key:"
  grep -n 'mon_find("' src/*.loft | grep -v spawn_crystal
  exit 1
fi
python3 tools/libcheck.py || exit 1

collect <<'EOF'
src/combattest.loft|COMBAT OK|/tmp/story_combat.log|combat loop|[2/14] combat loop (player melee + enemy attacks) ...
src/wiretest.loft|WIRING OK|/tmp/story_wire.log|dungeon wiring|[3/14] dungeon wiring (procedural gen + DB monsters) ...
src/aitest.loft|AI OK|/tmp/story_ai.log|monster AI|[4/14] monster AI (awareness + never-move) ...
src/placetest.loft|PLACEMENT OK|/tmp/story_place.log|placement|[5/14] placement (budget + weighted + start-safe) ...
src/leveltest.loft|LEVEL OK|/tmp/story_level.log|levels|[6/14] levels (stairs + descent) ...
src/herotest.loft|HERO OK|/tmp/story_hero.log|hero|[7/14] hero (XP + level-up) ...
src/curvetest.loft|CURVE OK|/tmp/story_curve.log|curve|[8/14] curve + ratio cap (gentle, fair, capped) ...
src/itemtest.loft|ITEM OK|/tmp/story_item.log|items|[9/14] items (gold + drops + pickup) ...
src/equiptest.loft|EQUIP OK|/tmp/story_equip.log|equipment|[10/14] equipment (wield + effects) ...
src/savetest.loft|SAVE OK|/tmp/story_save.log|save points|[11/14] save points (checkpoint respawn + grave) ...
src/fovtest.loft|FOV OK|/tmp/story_fov.log|FOV|[12/14] FOV (facing-cone fog-of-war) ...
src/sprite_drawtest.loft|SPRITE OK|/tmp/story_sprite.log|sprite rasterizer|[13/14] sprite rasterizer (fill_polygon scanline) ...
EOF

collect_one src/bundletest.loft "BUNDLE OK" /tmp/story_bundle.log "bundles" \
  "[bundles] character-bundle test ..."

collect <<'EOF'
src/bundledeftest.loft|BUNDLEDEF OK|/tmp/story_bundledef.log|bundle-defs|[bundle-defs] world bundle enemies/items -> catalog merge ...
src/deftest.loft|DEFS OK|/tmp/story_defs.log|defs|[defs] class/race/item tables — races now per-bundle via race_catalog ...
src/montest.loft|ENEMY DB OK|/tmp/story_mondb.log|enemy-database|[mondb] the engine monster table: the depth filter actually filters; uniques + final boss ...
src/gentest.loft|GEN OK|/tmp/story_gen.log|dungeon-generator|[gen] rooms + FULL connectivity by flood-fill + seed determinism (the world-key model rests on it) ...
src/producttest.loft|PRODUCT OK|/tmp/story_product.log|production|[production] I-PROD: engine repertoire then bundles', indexed modulo the total (BUNDLE.md) ...
src/roomtest.loft|ROOMS OK|/tmp/story_rooms.log|rooms|[rooms] rooms bundle -> room registry ...
src/itemusetest.loft|ITEM-USE OK|/tmp/story_itemuse.log|item-use|[items] item-use (Explorer potions: heal + custom detect) ...
src/clocktest.loft|CLOCK OK|/tmp/story_clock.log|clock|[clock] monster energy/speed (1.0x vs 1.5x) ...
src/statustest.loft|STATUS OK|/tmp/story_status.log|status|[status] timed statuses (slow / stun, pre-calc expiry) ...
src/persisttest.loft|PERSIST OK|/tmp/story_persist.log|persist|[persist] dungeon delta round-trip (death-only; regenerate + replay) ...
src/surfacetest.loft|SURFACE OK|/tmp/story_surface.log|surface|[surface] depth-0 desert + dungeon entrance (SLICE step 1+2) ...
src/skilltest.loft|SKILL OK|/tmp/story_skill.log|skill|[skills] passive melee skill (level + STR -> damage) ...
src/depthtest.loft|DEPTH OK|/tmp/story_depth.log|depth|[depth] beginner-dungeon spawn pool is depth-gentle (no lich at 1-3) ...
src/rangedtest.loft|RANGED OK|/tmp/story_ranged.log|ranged|[ranged] launcher fire action (bow + ammo -> shoot) ...
src/quickslottest.loft|QUICKSLOT OK|/tmp/story_quickslot.log|quickslot|[quickslot] type-routed auto-slot + bind + press-to-use dispatch ...
src/questtest.loft|QUEST OK|/tmp/story_quest.log|quest|[quest] desert_surprise overlay: throne set-piece + grant + boss -> infestation ...
src/msgtest.loft|MSG OK|/tmp/story_msg.log|msg|[msg] message log: ring buffer + event lines (kill/level/descend/nothing) ...
src/invhubtest.loft|INVHUB OK|/tmp/story_invhub.log|invhub|[invhub] inventory hub: two ring slots + equipped names + reslot bind ...
src/effecttest.loft|EFFECT OK|/tmp/story_effect.log|effect|[effect] use-item effects: blink / heal / restore / magic-mapping ...
src/specialtest.loft|SPECIAL OK|/tmp/story_special.log|special|[special] monster specials: gaze paralysis + venom + antivenin ward (+ deadlock/struggle) ...
src/unknowntest.loft|UNKNOWN OK|/tmp/story_unknown.log|unknown|[unknown] unknown items: per-game flavours / identify-on-use / carry / IF_KNOWN exempt ...
src/racetest.loft|RACE OK|/tmp/story_race.log|race|[race] chosen race applies: stat block / hit-die HP / skills / save / free-action gate ...
src/classtest.loft|CLASS OK|/tmp/story_class.log|class|[class] classes from bundles: apply / SP pool / the spell chain (routine-by-id) ...
src/derivetest.loft|DERIVE OK|/tmp/story_derive.log|derive|[derive] the eight axes and what each drives: re-key matrix / Speed clock + clamp / I-POOL ...
src/crystaltest.loft|CRYSTAL OK|/tmp/story_crystal.log|crystal|[crystal] the shrine re-spec: bump = interact / apply race+class / roster ...
src/overlandtest.loft|OVERLAND OK|/tmp/story_overland.log|overland|[overland] the contract wilderness: invariants / walked scale / towns+roads ...
src/cavetest.loft|CAVE OK|/tmp/story_cave.log|cave|[cave] natural caves: mouths on the surface, narrow winding levels ...
EOF

collect <<'EOF'
src/traveltest.loft|TRAVEL OK|/tmp/story_travel.log|travel|[travel] window crossing + the desert gate ...
src/idletest.loft|IDLESKIP OK|/tmp/story_idle.log|idle-skip|[idle-skip] scene key: hold when idle, bump on events (plan #7 P1) ...
src/pointstest.loft|POINTS OK|/tmp/story_points.log|railway-points|[points] turnout + reverse curve: 15-deg sweeps, G1, order-free (plan #5) ...
src/crossingtest.loft|CROSSING OK|/tmp/story_crossing.log|crossings|[cross] diamonds + double slips: R_max bound, slip invisible in cells (plan #5) ...
src/levelxtest.loft|LEVELX OK|/tmp/story_levelx.log|level-crossings|[levelx] road x rail at grade; barrier toggle keeps the L2 cache (plan #5) ...
src/platformtest.loft|PLATFORM OK|/tmp/story_platform.log|platforms|[plat] concentric platform exact, chord costs L^2/8R (plan #5) ...
src/sighttest.loft|SIGHT OK|/tmp/story_sight.log|signal-sighting|[sight] opacity-not-solidity, height, curve cutback D^2/8R (plan #5) ...
src/bridgetest.loft|BRIDGE OK|/tmp/story_bridge.log|bridges-tunnels|[bridge] levels: same ways, crossing vs bridge; bore leaves no mark (plan #5) ...
src/stairtest.loft|STAIR OK|/tmp/story_stair.log|stairs|[stair] per-cell height; min tread = sqrt(3)*max|cos|; nosing = sight line (plan #5) ...
src/spiraltest.loft|SPIRAL OK|/tmp/story_spiral.log|spiral-stairs|[spiral] sector treads; inner going is the bound; small spiral is sub-grid (plan #5) ...
src/rooftest.loft|ROOF OK|/tmp/story_roof.log|roofs-arches|[roof] one distance mechanism; cone eave; arch clear height (plan #5) ...
src/roofmatchtest.loft|ROOFMATCH OK|/tmp/story_roofmatch.log|roof-matching|[rmatch] recover the cone; planar roofs just interpolate (plan #5) ...
src/vaulttest.loft|VAULT OK|/tmp/story_vault.log|domes-vaults|[vault] dome slope ceiling; groin vs cloister is one operator (plan #5) ...
src/canopytest.loft|CANOPY OK|/tmp/story_canopy.log|canopy-partition|[canopy] exact-integer argmax partition: contested cells to the biggest tree, symmetric pair (plan #9 T1) ...
src/canopyvoltest.loft|CANOPYVOL OK|/tmp/story_canopyvol.log|canopy-volume|[canopyvol] canopy interval; crowding raises the bole (plan #9 T2) ...
src/canopyleantest.loft|CANOPYLEAN OK|/tmp/story_canopylean.log|canopy-lean|[canopylean] lean bound is a theorem; Case B signs (plan #9 T3) ...
src/canopyskeltest.loft|CANOPYSKEL OK|/tmp/story_canopyskel.log|canopy-skeleton|[canopyskel] shortest-path skeleton; I-REACH/I-NOTRESPASS controls (plan #9 T4) ...
src/canopypipetest.loft|CANOPYPIPE OK|/tmp/story_canopypipe.log|canopy-pipe|[canopypipe] r = k*sqrt(load); da Vinci is the pipe model (plan #9 T5) ...
src/canopyrelaxtest.loft|CANOPYRELAX OK|/tmp/story_canopyrelax.log|canopy-relax|[canopyrelax] termination detected, not assumed; exclusion emerges (plan #9 T6) ...
src/canopylighttest.loft|CANOPYLIGHT OK|/tmp/story_canopylight.log|canopy-light|[canopylight] volumetric sky fraction; gap regeneration; levels (plan #9 T7) ...
src/scaletest.loft|SCALE OK|/tmp/story_scale.log|scale-contract|[scale] one grid, two readings; every threshold checked in metres ...
src/horizontest.loft|HORIZON OK|/tmp/story_horizon.log|near-horizon|[horizon] plan #11 P6: I-HORIZON — near == far exactly, the surface has no cracks, standing == drawing ...
src/parallaxtest.loft|PARALLAX OK|/tmp/story_parallax.log|parallax-cache|[parallax] plan #11 P6b: I-PARALLAX — a layer is valid while its error is sub-pixel; the compression is a term ...
src/primtest.loft|PRIM OK|/tmp/story_prim.log|axis-primitives|[prim] drums about any axis; a wheel is a tower on its side (plan #10 P1) ...
src/proptest.loft|PART OK|/tmp/story_part.log|part-lists|[part] a cart is six parts and two mechanisms (plan #10 P2) ...
src/seattest.loft|SEAT OK|/tmp/story_seat.log|seated-props|[seat] chimney cut on the pitch, posts plumb, pipe length derived (plan #10 P3) ...
src/proplevtest.loft|PROPLEV OK|/tmp/story_proplev.log|prop-level|[proplev] props on their own sheet; a cart cannot alter a gate (plan #10 P4) ...
src/propgentest.loft|PROPGEN OK|/tmp/story_propgen.log|derived-props|[propgen] a village furnishes itself: one door per opening (plan #10 P5) ...
src/hingetest.loft|HINGE OK|/tmp/story_hinge.log|hinged-state|[hinge] one number swings the leaf and sets the material (plan #10 P6) ...
src/wheeltest.loft|WHEEL OK|/tmp/story_wheel.log|wheel-state|[wheel] no-slip: the arc turned equals the ground covered (plan #10 P7) ...
src/linktest.loft|LINK OK|/tmp/story_link.log|linkage-state|[link] the con-rod does not stretch, over 360 crank angles (plan #10 P8) ...
src/canopyfloortest.loft|CANOPYFLOOR OK|/tmp/story_canopyfloor.log|canopy-floor|[canopyfloor] field vs object at R = 2*sqrt(3), by fork test (plan #9 T8) ...
src/canopycardtest.loft|CANOPYCARD OK|/tmp/story_canopycard.log|canopy-cards|[canopycard] branch-aligned cards; the heading fix was the basis (plan #9 T9) ...
src/canopyopactest.loft|CANOPYOPAC OK|/tmp/story_canopyopac.log|canopy-opacity|[canopyopac] I-OPACITY: drawn density == simulated density (plan #9 T10) ...
src/cachetest.loft|CACHE OK|/tmp/story_cache.log|field-cache|[cache] L2 region cache: cached == freshly derived (plan #5 P6) ...
src/feattest.loft|FEAT OK|/tmp/story_feat.log|features|[feat] doors + windows as surface intervals (plan #5 P5) ...
src/matrixtest.loft|MATRIX OK|/tmp/story_matrix.log|junction-matrix|[matrix] every shape pair through six invariants (plan #5 P4) ...
src/jointest.loft|JOIN OK|/tmp/story_join.log|junctions|[join] junction arbitration is order-independent (plan #5 P3) ...
src/matchtest.loft|MATCH OK|/tmp/story_match.log|matcher|[match] cells -> surfaces: cell-authored content gets normals (plan #5 P2) ...
src/towertest.loft|TOWER OK|/tmp/story_tower.log|towers|[tower] plan #11 P5: the shipped world's towers carry the arc the builder recorded, seal, and open ...
src/waytest.loft|WAY OK|/tmp/story_way.log|ways|[ways] exact curves -> cells + edges + surface ids, one pass (plan #5 P1) ...
src/edgetest.loft|EDGE OK|/tmp/story_edge.log|edge-collision|[edge] wall collision as an EDGE cut — 1 edge blocks in all 24 headings (plan #5) ...
src/safetytest.loft|SAFETY OK|/tmp/story_safety.log|safety|[safety] plan #17 S1/S2: the safety category, and a worker will not enter it ...
src/stocktest.loft|STOCK OK|/tmp/story_stock.log|stock|[stock] plan #17 S3: stock == raised - drawn; empty means no output (armed both ways) ...
src/incursiontest.loft|INCURSION OK|/tmp/story_incursion.log|incursion|[incursion] plan #17 S5: pressure ARRIVES from a source, and clearing the source ends it ...
src/mendtest.loft|MEND OK|/tmp/story_mend.log|mend|[mend] plan #17 S6: damage is an EVENT, repair is its exact inverse, and no seam launders it ...
src/militiatest.loft|MILITIA OK|/tmp/story_militia.log|militia|[militia] plan #17 S7: standing is earned locally, and the militia it raises holds ground ...
src/fieldtest.loft|FIELD OK|/tmp/story_field.log|field-differential|[field] plan #11 P2: old passability model == new, every hex and direction ...
src/sweeptest.loft|SWEEP OK|/tmp/story_sweep.log|swept-movement|[sweep] plan #11 P2b: a PATH crosses walls, not a probe point — same walls at any dt ...
src/scenetest.loft|SCENE OK|/tmp/story_scene.log|camera|[scene] plan #11 P3: hex -> pixel -> the same hex; metric parity (I-STAND) ...
src/painttest.loft|PAINT OK|/tmp/story_paint.log|world texture|[paint] plan #11 P3b: the raster and the field agree EXACTLY (I-PAINT); hole + tie-free scale ...
src/worldtextest.loft|WORLDTEX OK|/tmp/story_worldtex.log|world texture (live)|[worldtex] plan #11 P3b: I-PAINT on the SHIPPED world — point-sample vs trace+fill, and the shader's frame ...
src/formtest.loft|FORM OK|/tmp/story_form.log|forms|[forms] hex->vector map vs the python golden (plan #5, exact integer contract) ...
src/gridtest.loft|GRID OK|/tmp/story_grid.log|grid-geometry|[grid] the square 90-degree half of hex_grid: cell<->px round-trip, directions, canonical edge ...
src/walltest.loft|WALL OK|/tmp/story_wall.log|wall-straightener|[wall] the DP straightener runs: room-line snap emits segments, no nested-vector panic (loft#250) ...
src/figtest.loft|FIGURE OK|/tmp/story_fig.log|reference-figure|[fig] the 1.75 m reference figure is 2.0207 wu and writes build/figure.glb (the scale eyeball) ...
src/meshtest.loft|MESH OK|/tmp/story_mesh.log|world-mesh|[mesh] world mesh: counts + exact R4 tint-bake colors (plan #7 P2) ...
src/replaytest.loft|REPLAY OK|/tmp/story_replay.log|replay|[replay] K2 replica invariant: intents + wire codec -> identical worlds ...
src/playtest.loft|PLAY OK|/tmp/story_play.log|playthrough|[play] scripts/walk.play: walk the world through flow_* and assert while walking ...
EOF

# ⚠ ONE ROW PER SCRIPT, NOT A LOOP OVER scripts/*.play. A glob would let a script be
# added and silently never run if it failed to match, and would hide WHICH playthrough
# broke behind one label. Each is named here, and each names what it claims.
collect_one src/playtest.loft "PLAY OK" /tmp/story_play_descend.log "playthrough: descend" \
  "[play] scripts/descend.play: walking onto a stair rebuilds the level, the character crosses ..." \
  scripts/descend.play
collect_one src/playtest.loft "PLAY OK" /tmp/story_play_respawn.log "playthrough: respawn" \
  "[play] scripts/respawn.play: death is a setback — checkpoint respawn keeps the kit (DESIGN 3a) ..." \
  scripts/respawn.play
collect_one src/playtest.loft "PLAY OK" /tmp/story_play_mend.log "playthrough: mend" \
  "[play] scripts/mend.play: plan #17 S6 — the shipped town has a smith, and a bump is the whole interface ..." \
  scripts/mend.play
collect_one src/playtest.loft "PLAY OK" /tmp/story_play_militia.log "playthrough: militia" \
  "[play] scripts/militia.play: plan #17 S7 — a stranger is turned down, a trusted player raises the watch, at zero keys ..." \
  scripts/militia.play

collect <<'EOF'
src/chunktest.loft|CHUNK OK|/tmp/story_chunk.log|chunk|[chunk] @PLN2 detail chunk: base+0.1m round-trip / watertight seam / 32x32 addressing ...
src/chunkgeotest.loft|CHUNKGEO OK|/tmp/story_chunkgeo.log|chunk-geo|[chunk-geo] @PLN2 S1 two-tier map: overworld hex + detail raster round-trips / tier sizes ...
src/chunkgentest.loft|CHUNKGEN OK|/tmp/story_chunkgen.log|chunk-gen|[chunk-gen] @PLN2 S2 overworld chunk from the engine: faithful sample + deterministic ...
src/detailtest.loft|DETAIL OK|/tmp/story_detail.log|detail|[detail] @PLN2 S3 detail LOD tier: round-trip / deterministic / watertight seam / LOD-consistent ...
src/meshchunktest.loft|MESHCHUNK OK|/tmp/story_meshchunk.log|mesh-chunk|[mesh-chunk] @PLN2 S4 chunk heightfield mesh: count / follows-data / watertight / deterministic ...
src/talustest.loft|TALUS OK|/tmp/story_talus.log|talus|[talus] @PLN2 S6.2 angle-of-repose talus on the detail tier: rubble conserved / repose / deterministic / faces+scree ...
EOF

# ── RUN THE ROSTER ──────────────────────────────────────────────────────────
# Everything above only COLLECTED rows; this is the one place they execute. The tables
# stay written out one row per line because that is still the roster (a glob would let a
# test be added and silently never run) — parallelism changed how they are dispatched,
# not what the gate claims to cover.
GATE_RED=0
echo "  [tests] $(wc -l < "$ROSTER") rows, $GATE_JOBS at a time (GATE_JOBS=1 for serial) ..."
drain || GATE_RED=1

# The games kernel (@PLN18 engine_host) lives in the sibling loft checkout — its
# natives ride the installed binary, the lib surface rides ../loft/lib. Skip (not
# fail) where the sibling is absent: the kernel dep is opt-in until registry-published.
if [ -d ../loft/lib/engine_host ]; then
  echo "  [kernel] engine_host consumable: natives + schema table (plan #6 K0) ..."
  # shellcheck disable=SC2086
  if [ -n "${GATE_VERBOSE:-}" ]; then
    "$LOFT" --interpret $FLAGS --lib ../loft/lib/ src/kerneltest.loft | tee /tmp/story_kernel.log
  else
    "$LOFT" --interpret $FLAGS --lib ../loft/lib/ src/kerneltest.loft > /tmp/story_kernel.log 2>&1
  fi
  grep -q "KERNEL OK" /tmp/story_kernel.log || {
    echo "  FAIL  kernel (engine_host) — /tmp/story_kernel.log"
    grep -vE '^advice|^note:|^warning|^ *[0-9]+ \||^ *\||^ *-->|^ *\^|^$' /tmp/story_kernel.log | tail -12 | sed 's/^/       /'
    exit 1; }
else
  echo "  [kernel] SKIP — ../loft/lib not present (sibling-checkout dep, plans/6-games-kernel/)"
fi

# ── WHERE THE MINUTES WENT ──────────────────────────────────────────────────
# Printed on the way out, so shortening the gate is a decision anyone can make from
# its own output rather than from a profiling session nobody runs. The threshold is
# absolute (5 s) rather than a top-N: a top-N always prints something and so says
# nothing, while a fixed bar goes SILENT once the suite is uniformly fast, which is
# the state we want it to be able to report.
#
# ⚠ THE PER-ROW SECONDS ARE NOW WALL TIME UNDER CONTENTION, not the cost of the test.
# With GATE_JOBS workers sharing 24 cores a row reports longer than it would alone, and
# the sum of the rows exceeds the gate's own wall clock. They still rank the roster —
# which is all this list is for — but do NOT quote one as a measurement. Measure a test
# by running it by itself, the way you iterate on it anyway.
#
# ⚠ AND THE 5 s BAR ONLY MEANS SOMETHING SERIALLY. Under the pool every row's wall time
# inflates — measured at 8-wide, matrixtest went 1.0 s -> 16.9 s — so the absolute bar
# named FIFTY-ONE rows on the first parallel run: a list that long is the "always prints
# something, therefore says nothing" failure the paragraph above rejects, arrived at from
# the other direction. What sets a PARALLEL gate's clock is its longest rows, so that is
# what it reports; the absolute bar survives unchanged where it is still valid, at
# GATE_JOBS=1. Either way the line goes silent when nothing is slow, which is the point.
if [ -s "$GATE_SLOW" ]; then
  total=$(( $(date +%s) - GATE_T0 ))
  n=$(wc -l < "$GATE_SLOW")
  if [ "$GATE_JOBS" -eq 1 ]; then
    slow=$(sort -rn "$GATE_SLOW" | awk '$1 >= 5000 {printf "%s%s %d.%ds", sep, $2, $1/1000, ($1%1000)/100; sep=" · "}')
    if [ -n "$slow" ]; then
      printf '  %d tests in %dm%02ds · over 5s: %s\n' "$n" "$((total / 60))" "$((total % 60))" "$slow"
    else
      printf '  %d tests in %dm%02ds · none over 5s\n' "$n" "$((total / 60))" "$((total % 60))"
    fi
  else
    slow=$(sort -rn "$GATE_SLOW" | head -6 | awk '$1 >= 5000 {printf "%s%s %d.%ds", sep, $2, $1/1000, ($1%1000)/100; sep=" · "}')
    if [ -n "$slow" ]; then
      printf '  %d rows in %dm%02ds at %d-wide · the tail that sets the clock (wall, contended): %s\n' \
        "$n" "$((total / 60))" "$((total % 60))" "$GATE_JOBS" "$slow"
    else
      printf '  %d rows in %dm%02ds at %d-wide · none over 5s\n' "$n" "$((total / 60))" "$((total % 60))" "$GATE_JOBS"
    fi
  fi
fi
rm -f "$GATE_SLOW"

# ⚠ THE EXIT STATUS IS THE POINT. drain() reports every red row rather than dying on the
# first, so the run reaches here either way — without this check a broken gate would
# print its failures and still exit 0, which is the one failure mode a gate may not have.
[ "$GATE_RED" -eq 0 ] || { echo "  FAILED"; exit 1; }

echo "  PASS"
