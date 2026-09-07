# LIBRARIES.md — the public surface of every package crawler consumes

**GENERATED — do not edit. `make apidoc` rewrites it; `make apidoc-check` fails if it is stale.**

One line per public name, read from the registry copy `loft.lock` pins. This exists
because looking a signature up used to mean reading the package: ~500 lines of source
for ~20 signatures, measured over one session. Read this instead, and open the package
only when you need the *reasoning* — which is what its comments are for.

⚠ Signatures only. **Why** a routine exists, and the traps around it, live in the
package's own comments and in `EXTRACTION.md` / `ADOPTION.md`.

⚠ **Only the packages crawler DECLARES.** This file cannot answer *"is there already a
library that does X?"* — it once said there was no PNG decoder while `imaging` had
shipped one. That question goes to the loft tree, which validates what is written:
`../loft/doc/claude/LIBRARIES.md` (every published library and its public API —
*check here before implementing*), `LIBRARY_BRANCHES.md` beside it (unmerged work in
flight), and `loft api --registry` / `.loft/api/_available.api` (the live catalogue).
Found one? Declare it in `loft.toml`, compile once, check `loft.lock` names it, and
`make apidoc` — then it is in here.

## `graphics` 0.5.0

```
fn audio_load(path: text) -> integer;
fn audio_play(clip: integer, volume: float) -> integer;
fn audio_play_raw(samples: vector<single>, sample_rate: integer, volume: float) -> integer;
fn audio_set_volume(sink: integer, volume: float);
fn audio_stop(sink: integer);
fn blend(dst: integer, src: integer) -> integer
fn blend_pixel(self: Canvas, bx: integer, by: integer, color: integer)
fn canvas(cw: integer, ch: integer, fill_color: integer) -> Canvas
fn clear(self: Canvas, color: integer)
fn color_a(color: integer) -> integer
fn color_b(color: integer) -> integer
fn color_g(color: integer) -> integer
fn color_r(color: integer) -> integer
fn create_painter_2d(screen_w: float, screen_h: float) -> Painter2D
fn create_renderer(rw: integer, rh: integer, title: text) -> Renderer
fn create_sprite_sheet(atlas: const Canvas, cols: integer, rows: integer, vao: integer) -> SpriteSheet
fn create_text_texture(font: integer, content: text, size: float, color: integer) -> integer
fn destroy(self: Renderer)
fn draw_aa_line(self: Canvas, ax0: integer, ay0: integer, ax1: integer, ay1: integer, color: integer)
fn draw_bezier(self: Canvas, bx0: integer, by0: integer, bx1: integer, by1: integer, bx2: integer, by2: integer, bx3: integer, by3: integer, color: integer)
fn draw_circle(self: Canvas, ccx: integer, ccy: integer, radius: integer, color: integer)
fn draw_ellipse(self: Canvas, ecx: integer, ecy: integer, erx: integer, ery: integer, color: integer)
fn draw_line(self: Canvas, lx0: integer, ly0: integer, lx1: integer, ly1: integer, color: integer)
fn draw_rect_at(painter: const Painter2D, x: float, y: float, w: float, h: float,
fn draw_rect(self: Canvas, drx: integer, dry: integer, drw: integer, drh: integer, color: integer)
fn draw_sprite_at(sheet: const SpriteSheet, painter: const Painter2D,
fn draw_sprite(sheet: const SpriteSheet, mvp: const vector<float>, sp_idx: integer)
fn draw_text(self: Canvas, font: integer, content: text, size: float,
fn draw_texture_at(painter: const Painter2D, tex: integer,
fn elapsed(self: const Renderer) -> float
fn fill_circle(self: Canvas, fcx: integer, fcy: integer, radius: integer, color: integer)
fn fill_ellipse(self: Canvas, fex: integer, fey: integer, ferx: integer, fery: integer, color: integer)
fn fill_rect(self: Canvas, rx: integer, ry: integer, rw: integer, rh: integer, color: integer)
fn fill_triangle(self: Canvas, tx0: integer, ty0: integer, tx1: integer, ty1: integer, tx2: integer, ty2: integer, color: integer)
fn get_pixel(self: const Canvas, gx: integer, gy: integer) -> integer
fn gl_bind_framebuffer(fbo: integer);
fn gl_bind_texture(texture_id: integer, unit: integer);
fn gl_blend_func(src: integer, dst: integer);
fn gl_clear(color: integer);
fn gl_create_color_texture(width: integer, height: integer) -> integer;
fn gl_create_depth_texture(width: integer, height: integer) -> integer;
fn gl_create_framebuffer() -> integer;
fn gl_create_fullscreen_window(title: text) -> boolean;
fn gl_create_shader(vertex_source: text, fragment_source: text) -> integer;
fn gl_create_window(width: integer, height: integer, title: text) -> boolean;
fn gl_cull_face(face: integer);
fn gl_delete_framebuffer(fbo: integer);
fn gl_delete_shader(program: integer);
fn gl_delete_texture(texture_id: integer);
fn gl_delete_vao(vao: integer);
fn gl_depth_mask(write: boolean);
fn gl_destroy_window();
fn gl_disable(cap: integer);
fn gl_draw_elements(vao: integer, index_count: integer, mode: integer);
fn gl_draw_fullscreen_quad();
fn gl_draw_instanced(vao: integer, vertex_count: integer, instance_count: integer);
fn gl_draw_mode(vao: integer, vertex_count: integer, mode: integer);
fn gl_draw(vao: integer, vertex_count: integer);
fn gl_enable(cap: integer);
fn gl_event_button() -> integer;
fn gl_event_key() -> integer;
fn gl_event_mods() -> integer;
fn gl_event_repeat() -> boolean;
fn gl_event_text() -> text;
fn gl_event_touch_id() -> integer;
fn gl_event_wheel() -> integer;
fn gl_event_x() -> float;
fn gl_event_y() -> float;
fn gl_font_ascent(font: integer, size: float) -> float;
fn gl_framebuffer_texture(fbo: integer, attachment: integer, tex: integer);
fn gl_generate_mipmap(tex: integer);
fn gl_instance_attrib(vao: integer, ivbo: integer, location: integer, components: integer, stride_floats: integer, offset_floats: integer);
fn gl_key_pressed(key_code: integer) -> boolean;
fn gl_line_width(width: float);
fn gl_load_font(path: text) -> integer;
fn gl_load_texture(path: text) -> integer;
fn gl_measure_text(font: integer, content: text, size: float) -> float;
fn gl_mouse_button() -> integer;
fn gl_mouse_wheel() -> integer;
fn gl_mouse_x() -> float;
fn gl_mouse_y() -> float;
fn gl_next_event() -> integer;
fn gl_point_size(size: float);
fn gl_poll_events() -> boolean;
fn gl_scissor(x: integer, y: integer, w: integer, h: integer);
fn gl_screenshot(width: integer, height: integer, path: text) -> boolean;
fn gl_set_fullscreen(on: boolean);
fn gl_set_uniform_float(program: integer, name: text, val: float);
fn gl_set_uniform_int(program: integer, name: text, val: integer);
fn gl_set_uniform_mat4(program: integer, name: text, mat: vector<float>);
fn gl_set_uniform_vec2(program: integer, name: text, x: float, y: float);
fn gl_set_uniform_vec3(program: integer, name: text, x: float, y: float, z: float);
fn gl_set_uniform_vec4(program: integer, name: text, x: float, y: float, z: float, w: float);
fn gl_swap_buffers();
fn gl_text_height(font: integer, size: float) -> integer;
fn gl_texture_filter(tex: integer, nearest: boolean);
fn gl_texture_subimage(tex: integer, x: integer, y: integer, w: integer, h: integer, data: vector<integer>);
fn gl_update_buffer(vbo: integer, data: vector<single>);
fn gl_upload_canvas(data: vector<integer>, width: integer, height: integer) -> integer;
fn gl_upload_indices(vao: integer, data: vector<integer>) -> integer;
fn gl_upload_instance_buffer(data: vector<single>) -> integer;
fn gl_upload_vertices(data: vector<single>, stride: integer) -> integer;
fn gl_use_shader(program: integer);
fn gl_viewport(x: integer, y: integer, w: integer, h: integer);
fn gl_window_height() -> integer;
fn gl_window_width() -> integer;
fn group_vbos_destroy(set: GroupVboSet)
fn group_vbos_draw_all(set: GroupVboSet)
fn group_vbos_new(stride: integer, draw_mode: integer) -> GroupVboSet
fn group_vbos_upsert(set: GroupVboSet, gk: integer, verts: vector<single>,
fn hline(self: Canvas, hx0: integer, hx1: integer, hy: integer, color: integer)
fn painter_vao(self: const Painter2D) -> integer
fn render_frame_no_swap(self: Renderer, sc: const scene::Scene,
fn render_frame(self: Renderer, sc: const scene::Scene,
fn render_loop(self: Renderer, sc: const scene::Scene, cam: const scene::Camera)
fn rgba(cr: integer, cg: integer, cb: integer, ca: integer) -> integer
fn rgb(cr: integer, cg: integer, cb: integer) -> integer
fn save_png(self: const Canvas, path: text) -> boolean
fn set_pixel(self: Canvas, sx: integer, sy: integer, color: integer)
fn sfx_beep(sb_freq: single, sb_dur: single, sb_vol: single) -> integer
fn sfx_bounce(sp_freq: single, sp_vol: single) -> integer
fn sfx_chirp(sc_f0: single, sc_f1: single, sc_dur: single, sc_vol: single) -> integer
fn sfx_descend(sd_f0: single, sd_f1: single, sd_dur: single, sd_vol: single) -> integer
fn sfx_noise(sn_dur: single, sn_vol: single) -> integer
fn upload_scene(self: Renderer, sc: const scene::Scene)
fn vline(self: Canvas, vx: integer, vy0: integer, vy1: integer, color: integer)
struct Canvas
struct GroupVboSet
struct Painter2D
struct Renderer
struct SpriteSheet
```

## `hex_grid` 0.1.0

```
const GRID_LEN  = 1.0;   // distance between adjacent cells = the distance-clock unit
const GRID_SIZE = 1.0;
const HEX_LEN  = 1.7320508075688772;   // = SQRT3 * HEX_SIZE; one hex step
const HEX_SIZE = 1.0;
const SQRT3    = 1.7320508075688772;
fn cell_canon_edge(q: integer, r: integer, dir: integer) -> (integer, integer, integer)
fn cell_corner_offset(i: integer) -> (float, float)
fn cell_corner_px(q: integer, r: integer, i: integer) -> (float, float)
fn cell_distance(q1: integer, r1: integer, q2: integer, r2: integer) -> integer
fn cell_edge_corners(dir: integer) -> (integer, integer)
fn cell_neighbor_dir(q1: integer, r1: integer, q2: integer, r2: integer) -> integer
fn cell_neighbor(q: integer, r: integer, dir: integer) -> (integer, integer)
fn cell_to_px(q: integer, r: integer) -> (float, float)
fn hex_canon_edge(q: integer, r: integer, dir: integer) -> (integer, integer, integer)
fn hex_corner_offset(i: integer) -> (float, float)
fn hex_corner_px(q: integer, r: integer, i: integer) -> (float, float)
fn hex_distance(q1: integer, r1: integer, q2: integer, r2: integer) -> integer
fn hex_edge_corners(dir: integer) -> (integer, integer)
fn hex_neighbor_dir(q1: integer, r1: integer, q2: integer, r2: integer) -> integer
fn hex_neighbor(q: integer, r: integer, dir: integer) -> (integer, integer)
fn hex_round(qf: float, rf: float) -> (integer, integer)
fn hex_to_px(q: integer, r: integer) -> (float, float)
fn px_to_cell(x: float, y: float) -> (integer, integer)
fn px_to_hex(x: float, y: float) -> (integer, integer)
```

## `hex_terrain` 0.1.1

```
fn terrain_blend_h(t: Terrain, p: TerrainParams, x: float, y: float) -> float
fn terrain_center(p: TerrainParams, c: integer, r: integer) -> (float, float)
fn terrain_control_pt(p: TerrainParams, c: integer, r: integer) -> (float, float)
fn terrain_detail_at(p: TerrainParams, x: float, y: float) -> float
fn terrain_edge_cross(p: TerrainParams, ca: integer, ra: integer, cb: integer, rb: integer) -> (float, float)
fn terrain_fbm(seed: integer, x: float, y: float, wl0: float, octaves: integer, ch: integer) -> float
fn terrain_flow_to(t: Terrain, c: integer, r: integer) -> (integer, integer)
fn terrain_hash01(seed: integer, ix: integer, iy: integer, ch: integer) -> float
fn terrain_hydrology(t: Terrain, p: TerrainParams, lake_mat: integer)
fn terrain_idx(t: Terrain, c: integer, r: integer) -> integer
fn terrain_lake_field(p: TerrainParams, x: float, y: float, lakey: float) -> float
fn terrain_new(nx: integer, ny: integer) -> Terrain
fn terrain_params(seed: integer, tile: float) -> TerrainParams
fn terrain_relief_pass(t: Terrain, types: vector<TerrainType>, p: TerrainParams)
fn terrain_ridge_at(p: TerrainParams, x: float, y: float) -> float
fn terrain_rivers(t: Terrain, types: vector<TerrainType>, p: TerrainParams) -> vector<TerrainRiver>
fn terrain_sample(t: Terrain, types: vector<TerrainType>, p: TerrainParams, rivers: vector<TerrainRiver>, x: float, y: float) -> TerrainSample
fn terrain_surface_at(t: Terrain, types: vector<TerrainType>, p: TerrainParams, x: float, y: float) -> TerrainSurf
fn terrain_vnoise(seed: integer, x: float, y: float, wl: float, ch: integer) -> float
fn terrain_water_at(t: Terrain, types: vector<TerrainType>, p: TerrainParams, x: float, y: float) -> boolean
struct Terrain
struct TerrainParams
struct TerrainRiver
struct TerrainSample
struct TerrainSurf
struct TerrainType
```

## `random` 0.3.0

```
fn get(self: RandStream, lo: integer, hi: integer) -> integer?
fn indices(self: RandStream, n: integer) -> vector<integer>
fn rand_indices(n: integer) -> vector<integer>;
fn rand(lo: integer, hi: integer) -> integer?;
fn rand_seed(seed: integer);
fn seed_stream(seed: integer) -> RandStream
struct RandStream
```

## `glb` 0.1.2

```
fn save_glb(m: Mesh, path: text)
fn save_scene_glb(sc: Scene, path: text)
```

## `hex_field` 0.1.0

```
const HXF_BAD_MAGIC     = 1;
const HXF_BAD_RESERVED  = 3;
const HXF_BAD_SCHEMA    = 2;
const HXF_BAD_SECTION   = 4;   // section length disagrees with w·h
const HXF_HEADER  = 32;
const HXF_MAGIC   = 0x31465848;   // 'HXF1' little-endian
const HXF_MISSING_OCCU  = 6;
const HXF_OK            = 0;
const HXF_SCHEMA  = 1;
const HXF_TRUNCATED     = 5;
const ROT_NOT_MULTIPLE = 1;
const ROT_OK           = 0;
const TAG_EDGE = 0x45474445;      // 'EDGE' — the wall layer
const TAG_HGHT = 0x54484748;      // 'HGHT'
const TAG_LABL = 0x4C42414C;      // 'LABL'
const TAG_LAYR = 0x5259414C;
const TAG_OCCU = 0x5543434F;      // 'OCCU'
fn cell_mirror(q: integer, r: integer) -> (integer, integer)
fn cell_rot(q: integer, r: integer, n: integer) -> (integer, integer)
fn corner_k(i: integer) -> integer
fn corner_m(i: integer) -> integer
fn doc_read(path: text) -> HexDoc
fn doc_write(
fn doc_write_all(
fn doc_write_edges(
fn edge_key(qa: integer, ra: integer, qb: integer, rb: integer) -> (integer, integer)
fn edge_mat(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer) -> integer
fn edge_set_both(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer,
fn edgeset_bytes(e: EdgeSet) -> integer
fn edgeset_count_all(e: EdgeSet) -> integer
fn edgeset_count(e: EdgeSet) -> integer
fn edgeset_digest(e: EdgeSet) -> integer
fn edgeset_equal(a: EdgeSet, b: EdgeSet) -> boolean
fn edgeset_h(e: EdgeSet) -> integer
fn edge_set_mat(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer, mat: integer)
fn edgeset_new(q0: integer, r0: integer, w: integer, h: integer) -> EdgeSet
fn edgeset_q0(e: EdgeSet) -> integer
fn edgeset_r0(e: EdgeSet) -> integer
fn edgeset_surf_count(e: EdgeSet) -> integer
fn edge_set_surf(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer,
fn edgeset_w(e: EdgeSet) -> integer
fn edge_surf(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer) -> integer
fn form_circle(w: integer, radius: float) -> HexSet
fn form_hexdisk(w: integer, n: integer) -> HexSet
fn form_octagon(w: integer, apothem: float) -> HexSet
fn height_get(f: Heights, q: integer, r: integer) -> float
fn height_set(f: Heights, q: integer, r: integer, z: float)
fn heights_new(q0: integer, r0: integer, w: integer, h: integer) -> Heights
fn hex_at(px: float, py: float) -> (integer, integer)
fn hexdisk_into(s: HexSet, cq: integer, cr: integer, n: integer)
fn hex_dist(q1: integer, r1: integer, q2: integer, r2: integer) -> integer
fn hexset_chunk(q0: integer, r0: integer, w: integer, h: integer) -> HexSet
fn hexset_count(s: HexSet) -> integer
fn hexset_get(s: HexSet, q: integer, r: integer) -> boolean
fn hexset_h(s: HexSet) -> integer
fn hexset_new(w: integer) -> HexSet
fn hexset_q0(s: HexSet) -> integer
fn hexset_r0(s: HexSet) -> integer
fn hexset_set(s: HexSet, q: integer, r: integer, on: boolean)
fn hexset_w(s: HexSet) -> integer
fn label_get(f: Labels, q: integer, r: integer) -> integer
fn label_set(f: Labels, q: integer, r: integer, v: integer)
fn labels_new(q0: integer, r0: integer, w: integer, h: integer) -> Labels
fn lattice_k(q: integer, r: integer) -> integer
fn lattice_m(_q: integer, r: integer) -> integer
fn lattice_rot60(k: integer, m: integer) -> (integer, integer)
fn lattice_to_cell(k: integer, m: integer) -> (integer, integer)
fn layer_add(ls: Layers, name: text) -> integer
fn layer_count(ls: Layers) -> integer
fn layer_get_at(ls: Layers, li: integer, q: integer, r: integer) -> integer
fn layer_get(ls: Layers, name: text, q: integer, r: integer) -> integer
fn layer_index(ls: Layers, name: text) -> integer
fn layer_name(ls: Layers, i: integer) -> text
fn layer_set_at(ls: Layers, li: integer, q: integer, r: integer, v: integer)
fn layer_set(ls: Layers, name: text, q: integer, r: integer, v: integer)
fn layers_h(ls: Layers) -> integer
fn layers_new(q0: integer, r0: integer, w: integer, h: integer) -> Layers
fn layers_q0(ls: Layers) -> integer
fn layers_r0(ls: Layers) -> integer
fn layers_w(ls: Layers) -> integer
fn nb_q(q: integer, r: integer, d: integer) -> integer
fn nb_r(_q: integer, r: integer, d: integer) -> integer
fn shoelace2(v: VecMap, i: integer) -> integer
fn shoelace_total(v: VecMap) -> integer
fn stencil_from(s: HexSet, hz: Heights, lb: Labels, has_h: boolean, has_l: boolean) -> Stencil
fn stencil_mirror(st: Stencil) -> Stencil
fn stencil_rotate_deg(st: Stencil, deg: integer) -> Stencil
fn stencil_rotate(st: Stencil, n: integer) -> Stencil
fn stencil_stamp(
fn stencil_stamp_all(
fn stencil_stamp_edges(
fn stencil_stamp_layers(
fn stencil_with_edges(s: HexSet, hz: Heights, lb: Labels, eg: EdgeSet,
fn trace(s: HexSet) -> VecMap
fn validate(v: VecMap, cells: integer) -> integer
fn wall_count(s: HexSet) -> integer
struct EdgeSet
struct Heights
struct HexDoc
struct HexSet
struct Labels
struct Layers
struct Stencil
struct VecMap
```

## `hex_edge` 0.1.0

```
const FEAT_DOOR     = 1;
const FEAT_LOOPHOLE = 3;
const FEAT_WINDOW   = 2;
const JOIN_CORNER = 2;      // a deliberate angle — a corner on purpose
const JOIN_SMOOTH = 1;      // G1 intended — tangents must agree
const SURF_NONE = 65535;
fn apply_features(e: EdgeSet, sf: Surfaces, f: Features,
fn collide(e: EdgeSet, s: Surfaces,
fn edge_block_arb(e: EdgeSet, sf: Surfaces, qa: integer, ra: integer,
fn edge_blocked(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer) -> boolean
fn edge_block(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer)
fn edge_block_full(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer,
fn edge_block_surf(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer,
fn edge_k(qa: integer, ra: integer, qb: integer, rb: integer) -> integer
fn edge_m(qa: integer, ra: integer, qb: integer, rb: integer) -> integer
fn edge_point(qa: integer, ra: integer, qb: integer, rb: integer) -> (float, float)
fn edges_cut(s: HexSet, e: EdgeSet)
fn edges_halfplane(e: EdgeSet, q0: integer, r0: integer, w: integer, h: integer,
fn edges_halfplane_surf(e: EdgeSet, q0: integer, r0: integer, w: integer, h: integer,
fn edges_solid(s: HexSet, e: EdgeSet)
fn feature_add(f: Features, surf: integer, s0: float, s1: float,
fn features_new() -> Features
fn junction_add(j: Junctions, sa: integer, sb: integer, kind: integer,
fn junction_g0(j: Junctions, i: integer, sf: Surfaces, tol: float) -> boolean
fn junction_ok(j: Junctions, i: integer, sf: Surfaces) -> boolean
fn junctions_new() -> Junctions
fn mat_bounce(m: Materials, id: integer) -> float
fn material_add(m: Materials, solid: boolean, height: float, opacity: float,
fn material_set_solid(m: Materials, id: integer, solid: boolean)
fn materials_new() -> Materials
fn mat_height(m: Materials, id: integer) -> float
fn mat_opacity(m: Materials, id: integer) -> float
fn mat_perm(m: Materials, id: integer) -> float
fn mat_solid(m: Materials, id: integer) -> boolean
fn mat_sound(m: Materials, id: integer) -> float
fn passable(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer) -> boolean
fn sight_clear(e: EdgeSet, m: Materials, x0: float, y0: float, z0: float,
fn surfaces_new() -> Surfaces
fn surf_arc(s: Surfaces, cx: float, cy: float, r: float) -> integer
fn surf_distance(s: Surfaces, id: integer, px: float, py: float) -> float
fn surf_normal(s: Surfaces, id: integer, px: float, py: float) -> (float, float)
fn surf_param(s: Surfaces, id: integer, px: float, py: float) -> float
fn surf_point(s: Surfaces, id: integer, t: float) -> (float, float)
fn surf_straight(s: Surfaces, nx: float, ny: float, c: float) -> integer
fn sweep_path(e: EdgeSet, x0: float, y0: float, x1: float, y1: float)
struct Features
struct Junctions
struct Materials
struct Surfaces
```

## `hex_way` 0.1.0

```
const WAY_ARC      = 2;
const WAY_STRAIGHT = 1;
fn cut_arb(s: HexSet, e: EdgeSet, sf: Surfaces, nsurf: integer, mat: integer)
fn nearest_seg(t: Track, px: float, py: float) -> integer
fn offset_legal(t: Track, d: float) -> boolean
fn seg_curvature(t: Track, i: integer) -> float
fn seg_distance(t: Track, i: integer, px: float, py: float) -> float
fn seg_len(t: Track, i: integer) -> float
fn seg_param(t: Track, i: integer, px: float, py: float) -> float
fn seg_point(t: Track, i: integer, s: float) -> (float, float)
fn seg_tangent(t: Track, i: integer, s: float) -> (float, float)
fn track_arc(t: Track, cx: float, cy: float, r: float, a0: float, a1: float)
fn track_distance(t: Track, px: float, py: float) -> float
fn track_len(t: Track) -> float
fn track_new() -> Track
fn track_offset(t: Track, d: float) -> Track
fn track_straight(t: Track, x0: float, y0: float, x1: float, y1: float)
fn way_mark(t: Track, halfwidth: float, s: HexSet)
fn way_param(t: Track, px: float, py: float) -> float
fn way_stamp(t: Track, halfwidth: float, s: HexSet, e: EdgeSet,
fn way_steps(t: Track, s: HexSet, f: Heights, rise: float, tread: float)
fn way_surfaces(t: Track, sf: Surfaces) -> integer
struct Track
```

## `hex_roof` 0.1.0

```
const ROOF_CONE    = 2;
const ROOF_DOME    = 3;   // rf_z = base, rf_slope = sphere radius
const ROOF_PLANE   = 1;
const ROOF_UNKNOWN = 0;
fn clear_height(fl: Heights, so: Heights, q: integer, r: integer) -> float
fn dome(s: HexSet, f: Heights, cx: float, cy: float, base: float, radius: float)
fn eave_spread(s: HexSet, f: Heights) -> float
fn roof_cone_fit(s: HexSet, f: Heights) -> RoofFit
fn roof_cone(s: HexSet, f: Heights, cx: float, cy: float,
fn roof_dome_fit(s: HexSet, f: Heights) -> RoofFit
fn roof_eval(fit: RoofFit, x: float, y: float) -> float
fn roof_hip(s: HexSet, f: Heights, eave: float, per_ring: float) -> integer
fn roof_match(s: HexSet, f: Heights, tol: float) -> RoofFit
fn roof_plane_fit(s: HexSet, f: Heights) -> RoofFit
fn roof_ponds(s: HexSet, f: Heights) -> integer
fn roof_ridge(s: HexSet, f: Heights, t: Track,
fn vault_arc(s: HexSet, f: Heights, t: Track, spring: float, radius: float)
fn vault_cloister(s: HexSet, f: Heights, t1: Track, t2: Track,
fn vault_groin(s: HexSet, f: Heights, t1: Track, t2: Track,
struct RoofFit
```

