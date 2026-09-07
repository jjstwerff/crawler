# formal/draw.md — the drawing routines (rules, then deviations)

**Scope:** the `.draw` scene language and everything that renders it — `tools/draw.py`
(Python; grammar in its docstring) and the `drawing` library
(`../loft-libs-graphics/drawing`, loft) — plus the primitive crawler keeps beside them
(`src/sprite_draw.loft`). Cited from code as `@FR-<Name>`; `make rules` checks that every
citation resolves ([README](README.md)).

**The two implementations have different jobs** (user, 2026-09-07). `draw.py` is the
**oracle**: the reference an algorithm is designed, probed and tested against, cheap to
change and to look at. The `drawing` library is **production**: what assets are rendered
with, in every project that consumes it. A new routine is born in the oracle and is not
finished until the library draws it byte for byte; the oracle is never what ships.

> **Why these routines carry formal rules.** They are the backbone for the FIRST version of
> many game assets — the sprites now, footprints and props next, the creatures the 3D move
> needs after that. A human reworks an asset later, sometimes wholly; that does not lower the
> bar on the routines, it raises it. Code that thousands of assets pass through is exactly the
> code whose behaviour has to be stated once and enforced at every site, because the day it
> drifts every asset drifts with it and nobody can say which change was intended. The rules
> below are the contract those assets are drawn against, and the two renderers are held to
> one another by it.

## Notation

- **paper** — the scene's `size`, W×H pixels; **fraction** — a coordinate in `0..1` of it.
- **canvas** — the supersampled surface a scene is drawn on, `3×` the paper.
- **`s`** — a brush stroke's across-coordinate, `-1..1` from the right edge to the left,
  walking root→tip; **`u`** — a spike's own fraction, `0` at the body, `1` at its point.
- **the oracle** — `tools/draw.py`. What it renders is, by definition, the picture.

## Rules

### The scene

```
  (Scene-Fraction)  A mark's coordinates are fractions of the paper — 0..1, origin
                    top-left, y down — and the only pixel count in a scene is `size`.
                    Pixels appear once, at the raster call; a parsed mark carries none.
  (Scene-Order)     The grammar is the ORDER its commands are tried in — the oracle's
                    `parse`: `size`, `Circle`, `Petals`, `Fronds`, `Brush`, `Lock`,
                    `Poly`, `Line` last. A renderer keeps that order, and a new command
                    is inserted at its place in the oracle first: a grammar this loose is
                    defined by which alternative wins.
  (Scene-Unparsed)  A line no command accepts is reported with its line number, never
                    dropped; a line that names something the scene has not defined (a
                    `brush=`) is unparsed too. A typo reads as a syntax problem, not a
                    geometry one.
  (Scene-Deferred)  A mark a renderer recognises but does not draw is listed as
                    deferred with its line, and a scene with a deferred mark is not
                    whole: `--once` fails on it.
  (Scene-Reproducible)  A scene renders the same bytes on every run and every machine.
                    Nothing it draws from is read from a clock, a PRNG, the environment
                    or the host; every varying number comes from the scene text, through
                    (Seed-Hash).
```

### The picture

```
  (Oracle-Bytes)    The picture of a scene is the one `tools/draw.py` renders, byte for
                    byte. Any other renderer of the grammar is measured by a byte diff
                    against it over decoded pixels, never by "close enough": a difference
                    is a defect in that renderer or a change to the oracle, and a change
                    to the oracle re-blesses every golden.
  (Oracle-Golden)   A renderer's own gate embeds the oracle's bytes for a scene small
                    enough to read, so it runs with no oracle present; the corpus diff is
                    the same claim at scale.
  (Oracle-Order)    Where a renderer reproduces the oracle's floating-point arithmetic it
                    uses the same expressions in the same order — `sqrt` of a sum of
                    squares rather than `hypot`, a running sum rather than a compensated
                    one, degrees times `PI / 180.0`, truncating casts — so that two
                    implementations on one libm give the same bits; only the expression
                    order can separate them.
  (Raster-Supersample)  A scene is drawn at 3× its paper and resampled to size with
                    Lanczos. The factor and the filter are part of the contract; a scene
                    drawn at any other factor is a different picture.
  (Raster-Pillow)   A polygon fills the pixels whose centres fall inside its outline,
                    even-odd, with edge slopes and scanline crossings carried in 32-bit
                    float and ROUND_UP / ROUND_DOWN mirrored about zero — Pillow's rule,
                    which the oracle inherits from `ImageDraw`. A filler with another rule
                    (integer crossings, inclusive spans) is a different picture however
                    good it is.
  (Raster-Gradient) A gradient fill is computed on a 100×100 grid over the shape's
                    bounding box and enlarged to the box bicubically; the ramp is never
                    computed at final size.
  (Raster-Transparent)  A transparent scene renders on transparent pixels, so the
                    resample anti-aliases edges against alpha and the sprite composites
                    over anything with no colour key.
```

### Marks

```
  (Mark-Deposit)    A fill and a pen stroke deposit their colour opaquely over whatever is
                    beneath; the paint does not interact with the canvas. Only the brush
                    stroke composites.
  (Mark-Ribbon)     A stroke with a width per point is a filled band: each point is
                    offset along its local normal by half its width to both sides, and
                    the band between the two sides is filled as one polygon, butt-capped,
                    with a half-width of at least half a pixel.
  (Mark-Smooth)     A point flagged `~` curves with a Catmull-Rom tangent of half its
                    neighbours' chord, expanded in ten samples per segment; a corner uses
                    the segment chord, so a segment between two corners is exactly
                    straight and an outline with no `~` is its control points.
  (Seed-Hash)       Every seeded variation — jitter, clumping, fray, a lock's shares,
                    lengths, drift and tile phase — comes from `hash01(seed, i, salt)`,
                    the 32-bit masked integer hash with a real final division, never from
                    a PRNG or a clock. A salt names one use, so adding a use never moves
                    another.
  (Seed-NonUniform) A repeated mark is never a uniform row: an array places its members
                    on the seeded low-frequency field (clumps and gaps, not white noise),
                    ramps its trend along the run, jitters each member and frays its
                    ends, all by default. Only zeroing them makes a man-made comb.
```

### The brush

```
  (Brush-Image)     A brush is an RGBA image. Its columns map ACROSS the stroke, stretched
                    to the local width, column 0 on the stroke's right side walking
                    root→tip (`flip` mirrors); its rows map ALONG the stroke, one row per
                    canvas pixel unless `period` says otherwise, tiled from a seeded phase
                    per stroke. A sample is bilinear, clamped across and wrapped along.
                    The built-in `hair` footprint is channels of 1–3 bristles with their
                    own values, a `gap` share of thin strands that fade in and out along
                    the run, and soft outermost columns.
  (Brush-Layer)     A brush stroke is built in its own layer over its bounding box and
                    composited over the canvas exactly once. Within the layer every
                    pixel keeps the sample from the centreline it is transversally
                    closest to — the smallest |s| — whatever order the ribbons are laid
                    in; a ribbon segment claims the pixels whose centres project onto it
                    within its interpolated half-width, the projection clamped to the
                    segment's ends (round joins).
  (Brush-Over)      The composite is straight-alpha OVER in integer arithmetic, one
                    formula for an opaque ground and a transparent sprite: with
                    t = A·(255−a) and o = a·255 + t, each channel is
                    (c·a·255 + C·t + o/2) / o and the alpha is (o + 127) / 255, integer
                    division throughout. A pixel whose stroke alpha is 0 is untouched.
  (Brush-Ramp)      Across its width a stroke is shaded as a half-cylinder against the
                    light: the surface normal at s is (s·n̂, √(1−s²)), its Lambert term
                    against the unit light picks a colour on a three-stop ramp — `dark`
                    at 0, the base colour at the crest (the light's z), `lit` at 1 — and
                    the footprint's value multiplies in. `dark` and `lit` are COLOURS,
                    never factors of the base: the shadow of white hair may be blue. A
                    spike shades as its own cylinder in proportion to u.
  (Lock-Profile)    A lock is `w0` wide where it grows, `w` from fraction `swell` of its
                    length on (a sine ease between), body to fraction `body`; the
                    remaining length is `tips` spikes. The body's end is shared out
                    between them unevenly by (Seed-Hash); each spike continues the
                    path's own curve at its offset, drifts by its own angle within
                    ±`spread`, ends at its own length within ±`tipvar` of the tail, and
                    is its full share wide leaving the body and a point at its end
                    (1 − u², so no notch opens at the base).
  (Lock-Streak)     A spike keeps its slice of the body's across axis when it samples
                    the footprint, so the bristle streaks run on from body into spike
                    without a break; the spike's own across-coordinate serves its
                    shading only.
```

### The performance pass

```
  (Perf-Weight)     Every public routine has a benchmark row — a fixed workload, timed,
                    with a hash of its output — and every routine that defines the
                    picture has a PURE-RUST reference computing the same workload with
                    the same arithmetic. The hash must agree across the interpreter,
                    the native build and the reference, or the routine is not one
                    algorithm and its speeds are not comparable; and loft-native must
                    run within the bar of the reference, or the routine does not pull
                    its weight and that is a defect in it, not a fact of the language.
                    The pass is `bench/` in the library, joined by `bench/compare.py`;
                    the bar and the measured table live in its README, dated.
```

## Deviations

OPEN: **2**.

### D-draw-2 — loft-native runs 15–40× behind the Rust reference on every raster routine (OPEN)

- **Violates:** Perf-Weight
- **Where:** not in `drawing`'s code — the hashes agree across the interpreter, the native
  build and the reference, so the algorithm is one. The gap is the loft native runtime and
  codegen: measured 2026-09-07, best of 3 (`drawing/bench/compare.py`, bar 4×),
  loft-native / Rust = `hair` 4.3, `hash` 10.9 (100 000 calls: ~7 ns of each is the
  entry instrumentation every generated function carries, release build included),
  `fill_circle` 17, `fill_star` 17, `wide_line` 17, `composite` 26, `lock` 30,
  `lock_curved` 34, `fronds` 49, `smooth` 262 (61 points: per-call cost). **Isolated:**
  the brush inlined into one standalone program gives the same numbers, so the library
  boundary is not the cause; `--native-emit` shows the cause — every vector element
  read or written through the store runtime with a null-record test (1 read + 7 writes
  per painted pixel), struct scalars re-read per pixel, NaN-aware float comparisons,
  sentinel integer helpers. Hash-preserving loft-side rewrites (hoist, inline the
  per-pixel call, pass the arrays) recover ~10 %: 30.2 → 27.0 ms against Rust's 1.03.
  loft's own `PERFORMANCE.md` measures the class at 18–25× on matrix / sort and names it
  **N1** (collections through the store), with **N2/N4** (per-call instrumentation) on top.
- **Effect:** a sprite that plain Rust renders in 1 ms takes loft 30 ms. Fine for a build
  step, not for anything that draws at runtime.
- **Status:** OPEN — the removal is loft's (the standing grant is to FILE it, not fix it):
  filed as [loft#1426](https://github.com/loft-lang/loft/issues/1426); the harness is the
  reproduction.
- **Removal:** loft codegen/runtime work on this workload class — vectors of floats and
  structs in tight loops, `??`-discharged arithmetic, cross-library calls. Re-run the pass;
  close when every judged routine is within the bar.

### D-draw-1 — `src/sprite_draw.loft` renders the marks by rules of its own (OPEN)

- **Violates:** Oracle-Bytes, Raster-Pillow, Raster-Supersample
- **Where:** `src/sprite_draw.loft` — `fill_polygon` (a pixel is inside when its centre lies
  in an odd span, crossings rounded in 64-bit), `downscale` (a box average, not Lanczos),
  `stroke_path`. Written before the `drawing` library existed, as an in-loft port of the
  same primitives.
- **Effect:** an in-loft sprite from it is only MEAN-close to the oracle's, so its parity
  is a dev probe rather than a gate — and today nothing draws a sprite with it. The world
  texture's use of `fill_polygons` (plan #11 P3b, I-PAINT) is not at issue: that rasterises
  `hex_field` loops on the lattice and is held to the geometry, not to a `.draw` scene.
- **Status:** OPEN
- **Removal:** draw sprites in loft through `drawing` (it needs `graphics >= 0.8`, which
  ADOPTION.md's frozen-renderer ruling gates) and keep `fill_polygons` for the lattice; or
  retire the sprite half of the module.
