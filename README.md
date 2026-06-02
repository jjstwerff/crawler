# crawler

A clean-room, ZAngband-style **hex roguelike** written in the
[loft](https://github.com/jjstwerff/loft) language — playable in 2D today, and
architected so the *same* renderer-agnostic simulation kernel can drive a 3D
browser version later.

(The loft package is named `story` — see `loft.toml`; `crawler` is the project.)

## The idea

- **Egocentric, continuous controls.** You glide and turn smoothly; the *world*
  rotates around you (you stay anchored ~70% down the screen, always facing up),
  leaving a margin of rear visibility.
- **Distance-driven clock.** Time advances by how far you *travel* — every
  hex-length you move, the world ticks once and enemies take a step. **Turning
  is free**: it covers no distance, so no time passes.
- **Hex world, two wall kinds.** Solid full-hex walls (the classic Angband
  granite cell) *plus* thin edge walls — with axis-separated sliding and a
  collision radius so you glide along walls instead of sticking or clipping.

See **[DESIGN.md](DESIGN.md)** for the full design: the kernel/renderer split,
the distance clock, the wall model + 12-direction smoothing, the layered
height-based world target, and the milestone roadmap.

## Controls

| Key | Action |
|---|---|
| `W` / `S` | glide forward / back |
| `A` / `D` | turn left / right (free — no time passes) |
| `.` / `Space` | wait one tick in place |
| `Esc` | quit |

## Build & run

Needs the **loft toolchain** checked out alongside this repo (defaults to
`../loft`; override with `make play LOFT_REPO=/path/to/loft`).

```sh
make play     # run the game in a window
make test     # headless, deterministic kernel self-test + compile gate
make game     # build a single self-contained story.html for the browser
make help     # list all targets
```

## Status

**M0 vertical slice complete:** generated hex map, continuous WASD movement with
the rotating egocentric view, one hex-locked enemy that ticks on your travel
distance, both wall kinds with sliding + radius collision, and a headless
self-test that verifies the core invariants (turning is free, movement ticks the
world, the enemy chases, walls block, the player slides and stops at the wall
face). Next: bump-combat + HP, field-of-view, a HUD.

## Layout

```
src/hexgeo.loft   pure hex geometry (axial coords, corners, edges)   — kernel
src/sim.loft      world + continuous player + hex enemies + clock     — kernel (no graphics)
src/view.loft     2D egocentric renderer                              — view
src/story.loft    entry: window + game loop + input                   — view
src/selftest.loft headless deterministic kernel test
tools/snap.sh     Xvfb screenshot helper (used by `make shot`)
```

The `hexgeo`/`sim` kernel imports no graphics; `view`/`story` are the swappable
2D front-end. That invariant is what lets the same kernel drive a 3D renderer.

## License

LGPL-3.0-or-later, consistent with the loft ecosystem.
