#!/usr/bin/env python3
"""BLUEPRINT — the `Petals` authoring primitive for draw.py (geometry verify phase).

Per DESIGN-PROTOCOL: this is exact-invariant geometry, so the instrument is
CONSTRUCTIVE — plot a concrete instance of the ANSWER, read the invariant off it,
and pin it with falsification probes BEFORE porting to draw.py. Reuses draw.py's REAL
_smooth_pts / _paint_polygon / circle_pts so what's verified here is byte-for-byte what
the port produces; porting is then just wiring a parse op.

THE PREDICTION (written before probing — the thing the probes try to break):
  Invariant: every petal is the SAME canonical teardrop, built once, placed by a rigid
  rotation of phi_i = a0 + i*(2pi/n) about the centre (base at radius r, tip at r+len),
  the whole construction done in PIXEL space (each of r/len/w scaled by the single
  reference dim W) so petals are visually congruent at every orientation and round-correct
  on non-square paper — exactly circle_pts' intent. The set {i*2pi/n} is closed under
  negation, so the arrangement is mirror-symmetric about the vertical for ANY n, with a
  petal pointing straight up at phi=0. Correctness is "one petal, rotated"; any per-petal
  divergence (length, width, asymmetry) is a BUG, not a special case.
  Re-assertion sites: ONE loop in ONE helper (N=1) — not a spray.

Run:  python3 tools/petal_blueprint.py        # prints CHECKS, writes /tmp/petal_blueprint/*.png
"""
import os, math, tempfile, importlib.util
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
# import draw.py's real geometry/paint so the blueprint == the eventual port
spec = importlib.util.spec_from_file_location("draw", os.path.join(HERE, "draw.py"))
draw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draw)

OUT = os.path.join(tempfile.gettempdir(), "petal_blueprint")
os.makedirs(OUT, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# THE CONSTRUCTION  (the candidate invariant, made concrete)
# ─────────────────────────────────────────────────────────────────────────────
def petal_template(length, w, bulge):
    """One petal in LOCAL (across a, along b) fractional-of-W units, base at b=0,
    tip at b=length, widest (|a|=w) at b=bulge*length. A 6-point closed outline →
    smoothed into a rounded-tip teardrop. Pointing along +b (outward)."""
    bw = bulge * length
    return [
        (0.0,      0.0),          # base point (rounded cusp at the centre)
        (-w,       bw),           # left waist
        (-w * 0.6, length * 0.93),# left shoulder (rounds the tip)
        (0.0,      length),       # tip
        (w * 0.6,  length * 0.93),# right shoulder
        (w,        bw),           # right waist
    ]


def petals(cx, cy, n, r, length, w, bulge, a0, W, H):
    """N petal outlines (each a list of FRACTIONAL (x,y) control points), built in
    pixel space then divided back — the pinned construction from THE PREDICTION."""
    tmpl = petal_template(length, w, bulge)
    cxp, cyp = cx * W, cy * H
    rp = r * W                       # all radial sizes scale by the SINGLE ref dim W
    out = []
    for i in range(n):
        phi = a0 + i * (2 * math.pi / n)
        # outward (length) dir d, and across dir p, with phi measured CW from "up"
        d = (math.sin(phi), -math.cos(phi))
        p = (math.cos(phi), math.sin(phi))
        poly = []
        for (a, b) in tmpl:
            ap, bp = a * W, b * W    # local → pixels (isotropic: scale by W)
            ox = ap * p[0] + (rp + bp) * d[0]
            oy = ap * p[1] + (rp + bp) * d[1]
            poly.append(((cxp + ox) / W, (cyp + oy) / H))   # pixels → fractions
        out.append(poly)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# RENDER  (gestalt channel — does it read as a flower?) via draw.py's real paint
# ─────────────────────────────────────────────────────────────────────────────
def render_flower(path, n, r, length, w, bulge, a0, petal_rgb, disc_rgb,
                  W=256, H=256, bg=(228, 224, 210)):
    S = 3
    BW, BH = W * S, H * S
    img = Image.new("RGB", (BW, BH), bg)
    cx, cy = 0.5, 0.5
    # petals first (under the disc), each via the SAME machinery draw.py uses
    for poly in petals(cx, cy, n, r, length, w, bulge, a0, W, H):
        sm = draw._smooth_pts(poly, [True] * len(poly), closed=True)
        draw._paint_polygon(img, sm, ("solid", petal_rgb), BW, BH)
    # centre disc
    disc = draw.circle_pts(cx, cy, r * 1.15, 28, 0.0, W, H)
    draw._paint_polygon(img, disc, ("radial", disc_rgb,
                        tuple(int(c * 0.7) for c in disc_rgb), None), BW, BH)
    img.resize((W, H), Image.LANCZOS).save(path)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# PROBES  (try to FALSIFY each load-bearing claim)
# ─────────────────────────────────────────────────────────────────────────────
def _seg_pixlen(poly, W, H, i0, i1):
    """pixel distance between control points i0,i1 of a fractional poly."""
    ax, ay = poly[i0][0] * W, poly[i0][1] * H
    bx, by = poly[i1][0] * W, poly[i1][1] * H
    return math.hypot(bx - ax, by - ay)


def run_probes():
    res = []

    def chk(name, ok, detail=""):
        res.append((name, ok, detail))

    # ---- P3: base at r, tip at r+len (template idx 0 = base, idx 3 = tip), up petal ----
    W = H = 256
    ps = petals(0.5, 0.5, 5, 0.05, 0.18, 0.06, 0.55, 0.0, W, H)
    up = ps[0]
    base_d = math.hypot((up[0][0] - 0.5) * W, (up[0][1] - 0.5) * H)
    tip_d = math.hypot((up[3][0] - 0.5) * W, (up[3][1] - 0.5) * H)
    chk("P3 base at r (px)", abs(base_d - 0.05 * W) < 0.5, f"{base_d:.2f} vs {0.05*W:.2f}")
    chk("P3 tip at r+len (px)", abs(tip_d - 0.23 * W) < 0.5, f"{tip_d:.2f} vs {0.23*W:.2f}")
    chk("P3 top petal points straight UP", abs(up[3][0] - 0.5) < 1e-9 and up[3][1] < 0.5,
        f"tip=({up[3][0]:.4f},{up[3][1]:.4f})")

    # ---- P2: the DRAWN UNION is mirror-symmetric about the vertical (the renderable
    #       claim). Per-petal, left/right are mirror images with REVERSED winding (fill
    #       is winding-indifferent), so test the point MULTISET, not same-index pairs:
    #       mirroring every petal point across x=cx must reproduce the same multiset. ----
    def multiset(polys):
        return sorted((round(x, 6), round(y, 6)) for pl in polys for (x, y) in pl)
    orig = multiset(ps)
    mirr = multiset([[(1.0 - x, y) for (x, y) in pl] for pl in ps])   # cx=0.5
    chk("P2 drawn union mirror-symmetric about vertical (n=5)", orig == mirr,
        f"{sum(a!=b for a,b in zip(orig,mirr))} mismatched pts")

    # ---- P1 (cleanest claim): petals CONGRUENT at every orientation, incl NON-SQUARE.
    #       This is the falsifier for the aspect-correction: build on 256x128 and compare
    #       the pixel length+width of the up-petal vs a side-petal. Equal => construction
    #       is isotropic (correct); unequal => fractional-space bug. ----
    for (W2, H2, tag) in [(256, 256, "square"), (256, 128, "wide"), (128, 256, "tall")]:
        q = petals(0.5, 0.5, 4, 0.05, 0.18, 0.06, 0.55, 0.0, W2, H2)
        lens = [_seg_pixlen(pt, W2, H2, 0, 3) for pt in q]      # base→tip pixel length
        wids = [_seg_pixlen(pt, W2, H2, 1, 5) for pt in q]      # waist width (l→r)
        lok = max(lens) - min(lens) < 0.5
        wok = max(wids) - min(wids) < 0.5
        chk(f"P1 congruent petals [{tag} {W2}x{H2}] length", lok,
            f"len spread={max(lens)-min(lens):.3f}px")
        chk(f"P1 congruent petals [{tag} {W2}x{H2}] width", wok,
            f"wid spread={max(wids)-min(wids):.3f}px")

    # ---- P4 (over-unification guard): "Petals is just sugar emitting N standard fill
    #       ops" — confirm a single petal, fed through draw.py's smoother, yields a
    #       closed polygon with the same shape as a hand-written smoothed Poly would
    #       (i.e. _smooth_pts accepts it unchanged in kind). And degenerate n=1/n=2
    #       don't crash and stay symmetric. ----
    one = petals(0.5, 0.5, 1, 0.0, 0.2, 0.07, 0.55, 0.0, 256, 256)
    sm = draw._smooth_pts(one[0], [True] * len(one[0]), closed=True)
    chk("P4 single petal smooths to a dense closed loop", len(sm) > len(one[0]) and sm[0] == one[0][0],
        f"{len(one[0])}→{len(sm)} pts")
    two = petals(0.5, 0.5, 2, 0.05, 0.18, 0.06, 0.55, 0.0, 256, 256)
    two_sym = abs((two[0][3][0] - 0.5)) < 1e-9 and abs((two[1][3][0] - 0.5)) < 1e-9
    chk("P4 n=2 degenerate stays on-axis (no crash)", two_sym,
        f"tips x={two[0][3][0]:.3f},{two[1][3][0]:.3f}")

    return res


if __name__ == "__main__":
    print("=== PETAL BLUEPRINT — falsification probes ===")
    res = run_probes()
    npass = sum(1 for _, ok, _ in res if ok)
    for name, ok, detail in res:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:48} {detail}")
    print(f"  {npass}/{len(res)} pass")

    # gestalt renders — eyeball that the construction READS as flowers
    render_flower(os.path.join(OUT, "daisy5.png"), 5, 0.05, 0.18, 0.06, 0.55, 0.0,
                  (236, 236, 230), (224, 196, 70))
    render_flower(os.path.join(OUT, "rosette6.png"), 6, 0.04, 0.16, 0.07, 0.5, 0.0,
                  (196, 90, 150), (210, 160, 60))
    render_flower(os.path.join(OUT, "daisy12.png"), 12, 0.06, 0.14, 0.035, 0.6, 0.0,
                  (240, 240, 236), (226, 198, 72))
    # a non-square render to SEE congruence holds
    render_flower(os.path.join(OUT, "wide5_256x128.png"), 5, 0.05, 0.18, 0.06, 0.55, 0.0,
                  (236, 236, 230), (224, 196, 70), W=256, H=128)
    print(f"  renders → {OUT}/  (daisy5, rosette6, daisy12, wide5_256x128)")
