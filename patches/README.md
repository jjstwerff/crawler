# Parked patches

Work set aside but kept so it can be replayed later. Each entry records the
**base commit** the diff applies onto and the **source commit** that contains
the full version.

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
