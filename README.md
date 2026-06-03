# crawler

A clean-room, ZAngband-style **hex roguelike** written in the
[loft](https://github.com/jjstwerff/loft) language — playable in 2D today, and
built so the *same* renderer-agnostic simulation kernel can drive a 3D browser
version later.

(The loft package is named `story`; `crawler` is the project/repo.)

## Why — the anti-moros

`crawler` shares its world model with **moros** (the hex world + heights/layers +
walls/buildings/castles/roads/rock-faces, via `moros_map`/`moros_render`) — but
where moros builds that world **by hand through an editor** (a long content tail),
`crawler` reaches a **working, playable foundation much faster by *generating*
the world procedurally**. Same destination world; code- and generation-driven,
no editor dependency.

## The idea

- **Egocentric, continuous controls.** You glide and turn smoothly; the *world*
  rotates around you (you stay ~70% down the screen, facing up).
- **Distance-driven clock.** Time advances by how far you *travel* — every
  hex-length you move, the world ticks once. **Turning is free.**
- **Hex terrain + overlay structures.** Collision lives on the hex grid (cells,
  edge-walls, height); walls/buildings (12-dir, sharp 90°), roads (24-dir,
  rounded), castles (2-hex ramparts + round towers) and rock faces are a
  render overlay on top.
- **World-keyed & procedural.** Each place is generated deterministically from
  its world position; once visited its state persists, so re-entering restores
  it — and travelling to harder **zones** (not just deeper) drives difficulty.

See **[DESIGN.md](DESIGN.md)** for the full design.

## Controls

| Key | Action |
|---|---|
| `W` / `S` | glide forward / back |
| `A` / `D` | turn left / right (free — no time passes) |
| `.` / `Space` | wait one tick |
| `Esc` | quit |

## Build & run

Needs the **loft toolchain** checked out alongside this repo (defaults to
`../loft`; override with `make play LOFT_REPO=/path/to/loft`).

```sh
make play     # run the game in a window
make test     # headless, deterministic self-tests + compile gate
make game     # build a single self-contained story.html for the browser
make help     # list all targets
```

## Status

**M0 vertical slice runs:** generated hex map, continuous WASD with the rotating
egocentric view, a hex-locked enemy that ticks on your travel distance, wall
collision with sliding + a player radius. Built and tested alongside it:
clean-room **monster / class / race / item** data tables and a **procedural
dungeon generator** (rooms + corridors, world-keyed). Next: combat + HP, the
facing-cone FOV, a HUD, and wiring the generator into the live game.

## Layout

```
src/hexgeo.loft   hex geometry (axial)                 — kernel
src/gridgeo.loft  square geometry for 90° walls          — kernel
src/sim.loft      world + player + enemies + clock + collision — kernel (no graphics)
src/gen.loft      procedural dungeon generator           — kernel
src/monsters|classes|races|items.loft   clean-room data tables — kernel
src/wallgeo.loft  wall outline (rounded active; DP parked in patches/) — derived geometry
src/view.loft     2D egocentric renderer                 — view
src/story.loft    entry: window + game loop + input       — view
src/*test.loft    headless tests
```

The `hexgeo`/`gridgeo`/`sim`/`gen`/data modules import no graphics; `view`/`story`
are the swappable 2D front-end. That invariant is what lets the same kernel drive
a 3D renderer (`moros_render`) later.

## License

LGPL-3.0-or-later, consistent with the loft ecosystem.
