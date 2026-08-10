# Parked patches

Work set aside but kept so it can be replayed later. Each entry records the
**base commit** the diff applies onto and the **source commit** that contains
the full version.

## `town-gates-reachability.patch`

**The town wall had no gates, and that is why the mine was unreachable.** Built and
measured 2026-08-10; parked **not because it is wrong but because it works**, and what it
uncovers is a design call rather than a bug fix. → `STATE.md` → *the town was sealed*.

What it contains, in one diff:

- **Six gates cut through the wall ring**, one per hex direction, ±2 either side so a
  lookout tower standing on that bearing cannot re-seal the gate it was stamped after.
  Walking `wrad` steps out from the centre lands exactly on the ring by construction, so
  there is no rounding to get wrong. Roads still open the ring where they cross it — that
  intent is kept; it simply never fired.
- **The mine sited by `walk_reach`** (reachable first, nearest second) with the gatherer's
  farthest-reachable fallback, plus the same filter on the beyond-the-window branch.
- **`WORK_MAX_D = 22`** — reachable is not workable; a site nobody can round-trip in a
  working day is as useless as one with no path.
- **The furnace and the miners move to the ore face** (a mining camp) instead of the
  miners commuting from town to whatever face worldgen found.
- **`incursiontest` row 7 watches the work the raid CHOSE**, not the gatherer's
  specifically — `raid_objective` aims at the most exposed work and which trade that is
  belongs to the world.

Measured effect: the town's walkable window goes **498 → 8951 of 9801 hexes**, and
civilians who cannot walk their own route go **13 of 21 → 4 of 20** (the remainder are
three penned livestock and one guard's outer leg). The gatherer's throughput **doubles**
(3 → 6 deliveries in four days).

⚠ **Why it is parked.** Opening the window changes *which work is most exposed*, and that
is what `I-SAFE`'s end-to-end A/B is measured on. With the map connected, the den's raids
press the **ore face** rather than the picking ground, so `stocktest` row 7 reads 6
deliveries at peace against 6 under pressure — danger stops cutting the alchemy chain, and
the chain it now presses (the forge) is unarmed because the camp out at the rock is unsafe
1600 of 1600 ticks and delivers nothing. Capping the mine to `WORK_MAX_D` instead removes
the mine altogether, which takes the surface **cave mouth** with it and turns `cavetest`
red. So the gate cannot go green without deciding *where a valley town's industry lives and
what the raids press* — plan #17 `S7`'s territory (pickets over outlying work), and the
user's call.

- **base (apply onto):** `3b890e0` — the S6 tree, gate green at 101 rows.
- Replay: `git apply patches/town-gates-reachability.patch`

## `wallgeo-douglas-peucker.diff`

The Douglas–Peucker wall-straightening rewrite of `src/wallgeo.loft` (collapse
the per-hex wobble into straight runs, keep sharp corners — the "no rounding"
direction). It compiled but panicked at runtime in the loft of that day (a
store / `keys.rs` index-out-of-bounds via the corner graph's nested vector
field) — **those loft bugs are now fixed** (probe-verified on the installed
toolchain 2026-06-11), so the diff should replay directly. The active
`wallgeo.loft` was reverted to the earlier averaged (slightly rounded)
version so the game runs.

- **base (apply onto):** `60d523cae96e4d3d582d1f2201007c5276099286` — the
  averaged/rounded `wallgeo.loft` currently in the tree.
- **source (full DP version):** `8fcedc36012ac5319794c3cabcd94d1acaba001b`.

Replay (reconstruct the DP version from the rounded base):

```sh
git checkout 60d523c -- src/wallgeo.loft
git apply patches/wallgeo-douglas-peucker.diff
```

Or grab the DP version straight from its commit:

```sh
git checkout 8fcedc3 -- src/wallgeo.loft
```

Next steps when revisited (also in DESIGN / memory): fix the runtime panic
(swap the corner graph's nested vector field for scalar edge slots), then place
each corner at the **intersection of its two adjoining wall lines** rather than
on the original hex vertex. (May be moot if the map moves to a 90° grid, where
wall silhouettes are already straight with right-angle corners.)

**2026-06-08 — rigorous re-test (engineering-rigor skill); two corrections:**
1. The **active/rounded `wallgeo.loft` is healthy** — `build_walls` runs headless
   with no panic (`sim_new` → 241 segs, `sim_new_gen(1234,1)` → 586). An earlier
   "panic at `wallgeo:302`" was a **stale build artifact** (the DP version's cached
   bytecode), not a real regression — the instrument's calibration trap.
2. The nested-vector fix is **necessary but NOT sufficient.** After swapping the
   corner graph's `inc: vector<integer>` for scalar slots (`deg` + `i0..i3`), the DP
   version **still panics** — now a `keys.rs` index-OOB (the lookup hash desyncs:
   corners grew to 241, hash len 18). But the **active version uses the same
   `hash<CornerRef[ck]>` + struct-field-append pattern and does NOT panic** — so the
   residual fault is **DP-specific, not the shared store pattern**. Root cause still
   unknown; needs a **boundary-matrix minimal repro** before filing upstream (don't
   file a half-localized cause). Until then the DP straightener stays parked, and
   "nicer walls" should come from **refining the active version** (e.g. a
   12/24-direction snap — aligned with the placement-direction model) rather than
   resurrecting this diff.
