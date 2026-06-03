# Parked patches

Work set aside but kept so it can be replayed later. Each entry records the
**base commit** the diff applies onto and the **source commit** that contains
the full version.

## `wallgeo-douglas-peucker.diff`

The Douglas–Peucker wall-straightening rewrite of `src/wallgeo.loft` (collapse
the per-hex wobble into straight runs, keep sharp corners — the "no rounding"
direction). It **compiles but panics at runtime** in the current loft
interpreter (a store / `keys.rs` index-out-of-bounds via the corner graph's
nested vector field), pending loft master fixes. The active `wallgeo.loft` was
reverted to the earlier averaged (slightly rounded) version so the game runs.

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
