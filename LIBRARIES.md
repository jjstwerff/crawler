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

## `graphics` 0.13.3

```
const BLEND_DST_ALPHA = 4;
const BLEND_ONE = 1;
const BLEND_ONE_MINUS_DST_ALPHA = 5;
const BLEND_ONE_MINUS_SRC_ALPHA = 3;
const BLEND_SRC_ALPHA = 2;
const BLEND_ZERO = 0;
const DRAW_LINES = 1;
const DRAW_POINTS = 2;
const DRAW_TRIANGLES = 0;
const EV_KEY_DOWN = 1;
const EV_KEY_UP = 2;
const EV_MOUSE_DOWN = 4;
const EV_MOUSE_MOVE = 6;
const EV_MOUSE_UP = 5;
const EV_NONE = 0;
const EV_RESIZE = 11;
const EV_TEXT = 3;
const EV_TOUCH_BEGIN = 8;
const EV_TOUCH_END = 10;
const EV_TOUCH_MOVE = 9;
const EV_WHEEL = 7;
const GL_BLEND = 2;
const GL_CULL_FACE = 3;
const GL_DEPTH_TEST = 1;
const GL_SCISSOR_TEST = 4;
const KEY_0 = 48;
const KEY_1 = 49;
const KEY_2 = 50;
const KEY_3 = 51;
const KEY_4 = 52;
const KEY_5 = 53;
const KEY_6 = 54;
const KEY_7 = 55;
const KEY_8 = 56;
const KEY_9 = 57;
const KEY_A = 97;
const KEY_BACKSPACE = 8;
const KEY_CTRL = 133;
const KEY_D = 100;
const KEY_DELETE = 147;
const KEY_DOWN = 129;
const KEY_E = 101;
const KEY_END = 150;
const KEY_ENTER = 13;
const KEY_ESCAPE = 27;
const KEY_F = 102;  // lower-layer
const KEY_F1  = 135;
const KEY_F10 = 144;
const KEY_F11 = 145;
const KEY_F12 = 146;
const KEY_F2  = 136;
const KEY_F3  = 137;
const KEY_F4  = 138;
const KEY_F5  = 139;
const KEY_F6  = 140;
const KEY_F7  = 141;
const KEY_F8  = 142;
const KEY_F9  = 143;
const KEY_HOME = 149;
const KEY_INSERT = 148;
const KEY_LBRACKET = 91;   // [
const KEY_LEFT = 130;
const KEY_O = 111;  // occlusion toggle
const KEY_PAGEDOWN = 152;
const KEY_PAGEUP = 151;
const KEY_Q = 113;
const KEY_R = 114;  // raise-layer
const KEY_RBRACKET = 93;   // ]
const KEY_RIGHT = 131;
const KEY_S = 115;
const KEY_SHIFT = 132;
const KEY_SPACE = 32;
const KEY_TAB = 9;
const KEY_UP = 128;
const KEY_W = 119;
const KEY_Y = 121;  // redo (with Ctrl)
const KEY_Z = 122;  // undo (with Ctrl)
const MOD_ALT = 4;
const MOD_CTRL = 2;
const MOD_SHIFT = 1;
const MOD_SUPER = 8;
fn ascent(self: const Font, size: float) -> float
fn attach(self: const Framebuffer, t: const Texture)
fn bind(self: const Texture, unit: integer)
fn blend(dst: integer, src: integer) -> integer
fn blend_pixel(self: Canvas, bx: integer, by: integer, color: integer)
fn blend(self: const Window, src: integer, dst: integer)
fn canvas(cw: integer, ch: integer, fill_color: integer) -> Canvas
fn capture(self: const Window) -> Canvas
fn clear(self: Canvas, color: integer)
fn clear(self: const Window, color: integer)
fn close(self: Window)
fn color_a(color: integer) -> integer
fn color_b(color: integer) -> integer
fn color_g(color: integer) -> integer
fn color_r(color: integer) -> integer
fn count(self: const GroupMeshes) -> integer
fn cull(self: const Window, face: integer)
fn depth_texture(self: const Window, width: integer, height: integer) -> Texture
fn depth_write(self: const Window, on: boolean)
fn disable(self: const Window, cap: integer)
fn draw_aa_line(self: Canvas, ax0: integer, ay0: integer, ax1: integer, ay1: integer, color: integer)
fn draw_all(self: const GroupMeshes, shader: const Shader)
fn draw_bezier(self: Canvas, bx0: integer, by0: integer, bx1: integer, by1: integer, bx2: integer, by2: integer, bx3: integer, by3: integer, color: integer)
fn draw_circle(self: Canvas, ccx: integer, ccy: integer, radius: integer, color: integer)
fn draw_ellipse(self: Canvas, ecx: integer, ecy: integer, erx: integer, ery: integer, color: integer)
fn draw_indexed(self: const GpuMesh, shader: const Shader, mode: integer)
fn draw_instanced(self: const GpuMesh, shader: const Shader, count: integer)
fn draw_line(self: Canvas, lx0: integer, ly0: integer, lx1: integer, ly1: integer, color: integer)
fn draw_mode(self: const GpuMesh, shader: const Shader, mode: integer)
fn draw_rect(self: Canvas, drx: integer, dry: integer, drw: integer, drh: integer, color: integer)
fn draw(self: const GpuMesh, shader: const Shader)
fn draw(self: const Sprites, mvp: const vector<float>, index: integer)
fn draw_text(
fn enabled(self: const Window, cap: integer) -> boolean
fn enable(self: const Window, cap: integer)
fn events(self: const Window) -> vector<Event>
fn fill_circle(self: Canvas, fcx: integer, fcy: integer, radius: integer, color: integer)
fn fill_ellipse(self: Canvas, fex: integer, fey: integer, ferx: integer, fery: integer, color: integer)
fn fill_polygon(self: Canvas, pts: const vector<Coord>, color: integer)
fn fill_rect(self: Canvas, rx: integer, ry: integer, rw: integer, rh: integer, color: integer)
fn fill_triangle(self: Canvas, tx0: integer, ty0: integer, tx1: integer, ty1: integer, tx2: integer, ty2: integer, color: integer)
fn filter(self: const Texture, nearest: boolean)
fn finish(self: const Window)
fn framebuffer(self: const Window) -> Framebuffer
fn get_pixel(self: const Canvas, gx: integer, gy: integer) -> integer
fn group_meshes(stride: integer, mode: integer) -> GroupMeshes
fn has(self: const GroupMeshes, gk: integer) -> boolean
fn height(self: const Texture) -> integer
fn height(self: const Window) -> integer
fn hline(self: Canvas, hx0: integer, hx1: integer, hy: integer, color: integer)
fn image(self: const Painter, t: const Texture, x: float, y: float, w: float, h: float)
fn indices(self: const GpuMesh, list: const vector<integer>)
fn instance_attrib(
fn instances(self: const Window, data: const vector<single>) -> InstanceBuffer
fn key_down(self: const Window, key: integer) -> boolean
fn line_height(self: const Font, size: float) -> integer
fn line_width(self: const Window, width: float)
fn load_font(path: text) -> Font?
fn load_texture(self: const Window, path: text) -> Texture?
fn measure(self: const Font, content: text, size: float) -> float
fn mipmaps(self: const Texture)
fn mouse_buttons(self: const Window) -> integer
fn mouse_x(self: const Window) -> float
fn mouse_y(self: const Window) -> float
fn open_fullscreen(title: text) -> Window?
fn open_window(width: integer, height: integer, title: text) -> Window?
fn painter(self: const Window) -> Painter?
fn point_size(self: const Window, size: float)
fn poll(self: const Window) -> boolean
fn put(self: const Texture, x: integer, y: integer, image: const Canvas)
fn quad(self: const Window) -> GpuMesh
fn rasterize(self: const Font, c: character, size: float) -> Glyph
fn rasterize_text(self: const Font, content: text, size: float) -> Glyph
fn rect(
fn render_to(self: const Window, target: const Framebuffer)
fn render_to_window(self: const Window)
fn resize_bicubic(self: const Canvas, ow: integer, oh: integer) -> Canvas
fn resize_lanczos(self: const Canvas, ow: integer, oh: integer) -> Canvas
fn resize(self: Painter, width: integer, height: integer)
fn rgba(cr: integer, cg: integer, cb: integer, ca: integer) -> integer
fn rgb(cr: integer, cg: integer, cb: integer) -> integer
fn save_png(self: const Canvas, path: text) -> boolean
fn scissor(self: const Window, x: integer, y: integer, width: integer, height: integer)
fn set_float(self: const Shader, name: text, v: float)
fn set_int(self: const Shader, name: text, v: integer)
fn set_mat4(self: const Shader, name: text, m: const vector<float>)
fn set_pixel(self: Canvas, sx: integer, sy: integer, color: integer)
fn set_vec2(self: const Shader, name: text, x: float, y: float)
fn set_vec3(self: const Shader, name: text, x: float, y: float, z: float)
fn set_vec4(self: const Shader, name: text, x: float, y: float, z: float, w: float)
fn shader(self: const Window, vertex: text, fragment: text) -> Shader?
fn sprite(
fn sprites(self: const Window, atlas: const Canvas, cols: integer, rows: integer) -> Sprites?
fn swap(self: const Window)
fn text_texture(self: const Window, font: const Font, content: text, size: float, color: integer) -> Texture
fn texture_from(self: const Window, image: const Canvas) -> Texture
fn texture(self: const Window, width: integer, height: integer) -> Texture
fn update(self: const GpuMesh, data: const vector<single>)
fn update(self: const InstanceBuffer, data: const vector<single>)
fn upload(self: const Window, data: const vector<single>, stride: integer) -> GpuMesh
fn upsert(
fn viewport(self: const Window, x: integer, y: integer, width: integer, height: integer)
fn vline(self: Canvas, vx: integer, vy0: integer, vy1: integer, color: integer)
fn width(self: const Texture) -> integer
fn width(self: const Window) -> integer
struct Canvas
struct Coord
struct Font
struct Framebuffer
struct Glyph
struct GpuMesh
struct GroupMeshes
struct InstanceBuffer
struct Painter
struct Shader
struct Sprites
struct Texture
struct Window
```

## `hex_grid` 0.1.4

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

## `hex_terrain` 0.1.8

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

## `random` 0.5.2

```
fn bits31(self: Rand32) -> i32
fn get32(self: Rand32, lo: i32, hi: i32) -> i32?
fn get(self: RandStream, lo: integer, hi: integer) -> integer?
fn indices32(self: Rand32, n: i32) -> vector<i32>
fn indices(self: RandStream, n: integer) -> vector<integer>
fn rand32(lo: i32, hi: i32) -> i32?
fn rand32_seed(seed: integer)
fn rand32_unit() -> single
fn rand_below(m: integer) -> integer;
fn rand_indices(n: integer) -> vector<integer>
fn rand(lo: integer, hi: integer) -> integer?
fn rand_seed(seed: integer);
fn seed32(seed: integer) -> Rand32
fn seed_hw() -> integer?
fn seed_stream(seed: integer) -> RandStream
fn unit32(self: Rand32) -> single
struct Rand32
struct RandStream
```

## `glb` 0.1.8

```
fn save_glb(m: Mesh, path: text)
fn save_scene_glb(sc: Scene, path: text)
```

## `hex_field` 0.1.11

```
const EDGE_MAT_MAX = 255;
const HXF_BAD_EXTENT    = 7;   // w or h impossible for a file this size
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
fn edgeset_refused(e: EdgeSet) -> integer
fn edgeset_surf_count(e: EdgeSet) -> integer
fn edge_set_surf(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer,
fn edgeset_w(e: EdgeSet) -> integer
fn edge_surf(e: EdgeSet, qa: integer, ra: integer, qb: integer, rb: integer) -> integer
fn form_circle(w: integer, radius: float) -> HexSet
fn form_hexdisk(w: integer, n: integer) -> HexSet
fn form_octagon(w: integer, apothem: float) -> HexSet
fn height_get(f: const Heights, q: integer, r: integer) -> float
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
fn label_get(f: const Labels, q: integer, r: integer) -> integer
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
fn outline_count(v: VecMap) -> integer
fn shoelace2(v: VecMap, i: integer) -> integer
fn shoelace_total(v: VecMap) -> integer
fn stencil_from(s: HexSet, hz: Heights, lb: Labels, has_h: boolean, has_l: boolean) -> Stencil
fn stencil_has_edges(st: const Stencil) -> boolean
fn stencil_has_heights(st: const Stencil) -> boolean
fn stencil_has_labels(st: const Stencil) -> boolean
fn stencil_mirror(st: Stencil) -> Stencil
fn stencil_rotate_deg(st: Stencil, deg: integer) -> Stencil
fn stencil_rotate(st: Stencil, n: integer) -> Stencil
fn stencil_stamp(
fn stencil_stamp_all(
fn stencil_stamp_edges(
fn stencil_stamp_layers(
fn stencil_unstamp(
fn stencil_unstamp_all(
fn stencil_unstamp_layers(
fn stencil_with_edges(s: HexSet, hz: Heights, lb: Labels, eg: EdgeSet,
fn trace_edges(s: HexSet) -> EdgeMap
fn trace(s: HexSet) -> VecMap
fn validate(v: VecMap, cells: integer) -> integer
fn wall_count(s: HexSet) -> integer
struct EdgeMap
struct EdgeSet
struct Heights
struct HexDoc
struct HexSet
struct Labels
struct Layers
struct Stencil
struct VecMap
```

## `hex_edge` 0.2.7

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
fn sweep_path_from(e: EdgeSet, sq: integer, sr: integer,
struct Features
struct Junctions
struct Materials
struct Surfaces
```

## `hex_way` 0.1.7

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

## `hex_roof` 0.1.10

```
const ROOF_CONE    = 2;
const ROOF_DOME    = 3;   // rf_z = base, rf_slope = sphere radius
const ROOF_PLANE   = 1;
const ROOF_RIDGE   = 4;   // rf_x,rf_y = one end; rf_x2,rf_y2 = the other
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
fn roof_ridge_fit(s: HexSet, f: Heights) -> RoofFit
fn roof_ridge(s: HexSet, f: Heights, t: Track,
fn vault_arc(s: HexSet, f: Heights, t: Track, spring: float, radius: float)
fn vault_cloister(s: HexSet, f: Heights, t1: Track, t2: Track,
fn vault_groin(s: HexSet, f: Heights, t1: Track, t2: Track,
struct RoofFit
```

