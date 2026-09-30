#!/usr/bin/env python3
"""BLUEPRINT — the `Fronds` primitive for draw.py: a LINEAR ARRAY of tapered strokes
rooted along a spine path (veins on a midrib, barbs, fur clumps, grass, a leg-fringe,
hatching). The generalisation of `Petals` (radial) to a path; the companion verify phase.

Per DESIGN-PROTOCOL (exact-invariant geometry): plot the concrete ANSWER, read the
invariant off it, pin it with falsification probes that REUSE draw.py's real _ribbon /
_smooth_pts BEFORE porting — so the verified construction ports unchanged.

THE PREDICTION (written before probing):
  Invariant — each frond is the template stroke ROOTED at parameter u_i along the spine
  and tilted forward by ang(t) off the spine normal, where:
   • placement u_i = (i+0.5)/n shifted by a SEEDED LOW-FREQUENCY FIELD (so fronds bunch in
     CLUMPS, not an even comb, not white noise); field=0 → exactly uniform (reachable).
   • size/angle follow a deterministic TREND ramp (len→len2, w→w2, ang→ang2 over t=u_i)
     ± SEEDED JITTER (per-element hash, bounded) — trend carries the form, jitter breaks
     the mechanical read; they are independent.
   • MIRROR pairs share the SAME sample (u,len,ang) reflected across the spine — equal
     across the axis (a lopsided leaf reads damaged); jitter the symmetric UNIT.
   • density FRAYS toward the ends (end fronds shorten) — no clean termination line.
   • all randomness is an explicit integer hash of (seed,i) — NEVER random()/hash() — so
     renders are reproducible; vary `seed` per call so two Fronds don't share wobble.
  Re-assertion sites: ONE loop in ONE helper (N=1). The default output is non-uniform +
  construction-hiding; uniform (field=jitter=fray=0) is the man-made special case.

Run:  python3 tools/fronds_blueprint.py     # CHECKS + /tmp/fronds_blueprint/*.png
"""
import os, math, tempfile, importlib.util
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("draw", os.path.join(HERE, "draw.py"))
draw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draw)
OUT = os.path.join(tempfile.gettempdir(), "fronds_blueprint")
os.makedirs(OUT, exist_ok=True)


# ── deterministic noise (NO random()/hash() — reproducible) ───────────────────
def _h(seed, i, salt):
    """A reproducible pseudo-random float in [-1,1) from small non-negative ints."""
    x = ((seed * 73856093) ^ (i * 19349663) ^ (salt * 83492791)) & 0xFFFFFFFF
    x = (x ^ (x >> 13)) & 0xFFFFFFFF
    x = (x * 1274126177) & 0xFFFFFFFF
    return (x / 0xFFFFFFFF) * 2.0 - 1.0


def _field(seed, u):
    """A smooth LOW-FREQUENCY wave in ~[-1,1]: two low harmonics with seed-derived
    phases. Smooth in u ⇒ neighbouring fronds correlate ⇒ clumps + gaps, not white noise."""
    p1 = _h(seed, 0, 11) * math.pi
    p2 = _h(seed, 0, 22) * math.pi
    return 0.6 * math.sin(2 * math.pi * 1.0 * u + p1) + \
           0.4 * math.sin(2 * math.pi * 2.0 * u + p2)


# ── THE CONSTRUCTION ──────────────────────────────────────────────────────────
def fronds(x1, y1, x2, y2, n, length, length2, w, w2, ang, ang2,
           mirror, jitter, field, fray, seed, bow, W, H, depth=1, sub=0.32):
    """List of fronds, each (centerline_pts_frac, widths, side, i). Built in PIXEL space
    (lengths scale by W) so fronds are visually consistent + correct on non-square paper.
    FRACTAL: depth>1 re-applies Fronds to EACH frond's centerline as a spine (a smaller
    array scaled by `sub`) — venation is self-similar (midrib→primaries→secondaries→…).
    depth=1 is the single-level construction, byte-identical to before."""
    P1 = (x1 * W, y1 * H)
    P2 = (x2 * W, y2 * H)
    dx, dy = P2[0] - P1[0], P2[1] - P1[1]
    Ln = math.hypot(dx, dy) or 1e-9
    d = (dx / Ln, dy / Ln)
    nrm = (-d[1], d[0])
    base = []
    for i in range(n):
        ub = (i + 0.5) / n
        u = ub + field * _field(seed, ub) * (0.5 / n)        # clumping shift (≤ half a step)
        u = min(1.0, max(0.0, u))
        t = u
        Ltr = length + (length2 - length) * t                # trend ramp
        dte = min(u, 1 - u)
        frayf = 1 - fray * max(0.0, 1 - dte / 0.25)           # ends shorten
        Lj = 1 + jitter * 0.4 * _h(seed, i, 1)                # seeded jitter
        Lpx = Ltr * frayf * Lj * W
        an = (ang + (ang2 - ang) * t) + jitter * 15.0 * _h(seed, i, 2)
        phi = math.radians(an)
        wi = (w + (w2 - w) * t) * (1 + jitter * 0.3 * _h(seed, i, 3))
        Rx, Ry = P1[0] + u * dx, P1[1] + u * dy
        for side in ([1, -1] if mirror else [1]):
            nx, ny = nrm[0] * side, nrm[1] * side
            fx = nx * math.cos(phi) + d[0] * math.sin(phi)    # tilt the normal forward (→P2)
            fy = ny * math.cos(phi) + d[1] * math.sin(phi)
            Tx, Ty = Rx + Lpx * fx, Ry + Lpx * fy
            pts = [(Rx / W, Ry / H), (Tx / W, Ty / H)]
            wid = [wi, max(0.5, wi * 0.15)]                   # taper root→tip
            if bow != 0.0:                                    # curved frond (flow follows form)
                px, py = -fy, fx                              # perp to frond dir
                Mx = (Rx + Tx) / 2 + bow * Lpx * px
                My = (Ry + Ty) / 2 + bow * Lpx * py
                pts = [pts[0], (Mx / W, My / H), pts[1]]
                wid = [wi, (wi + wid[1]) / 2, wid[1]]
            base.append((pts, wid, side, i))
    if depth <= 1:
        return base
    # FRACTAL recursion: each frond's centerline (root→tip) is the spine of a smaller array.
    out = list(base)
    cn = max(2, round(n * 0.55))
    for k, (pts, wid, _s, _i) in enumerate(base):
        (rx, ry), (tx, ty) = pts[0], pts[-1]                  # this frond's root, tip (frac)
        out += fronds(rx, ry, tx, ty, cn, length * sub, length * sub * 0.5,
                      w * 0.5, max(0.6, w2 * 0.5), ang, ang2, 1, jitter, field, fray,
                      seed * 31 + k + 1, bow, W, H, depth - 1, sub)
    return out


# ── RENDER (gestalt) via draw.py's real _ribbon ───────────────────────────────
def render(path, draw_calls, W=256, H=256, bg=(228, 224, 210)):
    S = 3
    BW, BH = W * S, H * S
    img = Image.new("RGB", (BW, BH), bg)
    dd = ImageDraw.Draw(img)
    for (spine, fr_args, fr_color, spine_color) in draw_calls:
        if spine:                                            # draw the spine (e.g. a midrib)
            (a, b), sw = spine
            draw._ribbon(dd, [a, b], sw, spine_color, BW, BH, S)
        dep = fr_args[17] if len(fr_args) > 17 else 1
        sb = fr_args[18] if len(fr_args) > 18 else 0.32
        for (pts, wid, side, i) in fronds(*fr_args[:17], W=W, H=H, depth=dep, sub=sb):
            cl = draw._smooth_pts(pts, [False] + [True] * (len(pts) - 2) + [False], False) \
                 if len(pts) > 2 else pts
            ww = wid if len(cl) == len(wid) else [wid[0]] + [wid[1]] * (len(cl) - 2) + [wid[-1]]
            draw._ribbon(dd, cl, ww if len(ww) == len(cl) else wid, fr_color, BW, BH, S)
    img.resize((W, H), Image.LANCZOS).save(path)


# ── PROBES (try to FALSIFY each load-bearing claim) ───────────────────────────
def _reflect_across_spine(pt, P1, P2):
    """Reflect a fractional point across the spine line P1-P2 (fractional)."""
    ax, ay = P1; bx, by = P2
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-9
    t = ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / L2
    fx, fy = ax + t * dx, ay + t * dy           # foot of perpendicular
    return (2 * fx - pt[0], 2 * fy - pt[1])


def run():
    res = []
    chk = lambda name, ok, det="": res.append((name, ok, det))
    W = H = 256

    # P-place: field=jitter=fray=0 → roots exactly at u=(i+0.5)/n along the spine
    fr = fronds(0.2, 0.5, 0.8, 0.5, 6, 0.1, 0.1, 3, 3, 30, 30, 0, 0, 0, 0, 7, 0, W, H)
    exp = [0.2 + (i + 0.5) / 6 * 0.6 for i in range(6)]
    got = [p[0][0][0] for p in fr]
    chk("P-place uniform reachable (field=jit=0)", max(abs(a - b) for a, b in zip(exp, got)) < 1e-9,
        f"max dev {max(abs(a-b) for a,b in zip(exp,got)):.2e}")

    # P-trend: len2=2·len, monotone increasing frond length, first≈len last≈len2
    fr = fronds(0.5, 0.9, 0.5, 0.1, 10, 0.06, 0.12, 3, 3, 0, 0, 0, 0, 0, 0, 7, 0, W, H)
    Ls = [math.hypot((p[0][1][0] - p[0][0][0]) * W, (p[0][1][1] - p[0][0][1]) * H) for p in fr]
    mono = all(Ls[i] <= Ls[i + 1] + 1e-9 for i in range(len(Ls) - 1))
    chk("P-trend length ramps len→len2 monotonically", mono and Ls[-1] > 1.8 * Ls[0],
        f"first={Ls[0]:.1f}px last={Ls[-1]:.1f}px ratio={Ls[-1]/Ls[0]:.2f}")

    # P-jitter: reproducible (same seed identical), seed-sensitive, bounded
    a1 = fronds(0.2, 0.5, 0.8, 0.5, 8, 0.1, 0.1, 3, 3, 30, 30, 0, 0.5, 0, 0, 7, 0, W, H)
    a2 = fronds(0.2, 0.5, 0.8, 0.5, 8, 0.1, 0.1, 3, 3, 30, 30, 0, 0.5, 0, 0, 7, 0, W, H)
    a3 = fronds(0.2, 0.5, 0.8, 0.5, 8, 0.1, 0.1, 3, 3, 30, 30, 0, 0.5, 0, 0, 8, 0, W, H)
    same = all(a1[i][0] == a2[i][0] for i in range(len(a1)))
    diff = any(a1[i][0] != a3[i][0] for i in range(len(a1)))
    chk("P-jitter reproducible (same seed) + seed-sensitive", same and diff,
        f"same={same} diff_on_seed={diff}")

    # P-symmetry (THE load-bearing one): mirror fronds are exact reflections across spine
    P1, P2 = (0.5, 0.9), (0.5, 0.1)
    fr = fronds(*P1, *P2, 9, 0.1, 0.05, 3, 3, 25, 55, 1, 0.6, 0.7, 0.3, 7, 0, W, H)
    plus = [f for f in fr if f[2] == 1]
    minus = [f for f in fr if f[2] == -1]
    worst = 0.0
    for fp, fm in zip(plus, minus):
        r = _reflect_across_spine(fp[0][1], P1, P2)         # reflect +side tip
        worst = max(worst, math.hypot((r[0] - fm[0][1][0]) * W, (r[1] - fm[0][1][1]) * H))
    chk("P-symmetry mirror pairs equal across the axis", worst < 1e-6,
        f"worst tip mismatch {worst:.2e}px (jitter+field+fray all on)")

    # P-clump (field ≠ white noise): field placement is SMOOTHER (small 2nd difference)
    # than an equal-amplitude white-noise placement → neighbours correlate (clumps).
    n = 40
    uf = []
    for i in range(n):
        ub = (i + 0.5) / n
        uf.append(ub + 0.9 * _field(7, ub) * (0.5 / n))
    uw = []
    for i in range(n):
        ub = (i + 0.5) / n
        uw.append(ub + 0.9 * _h(7, i, 99) * (0.5 / n))      # white-noise control
    d2 = lambda s: sum(abs(s[i + 1] - 2 * s[i] + s[i - 1]) for i in range(1, len(s) - 1))
    chk("P-clump field is correlated (smoother than white noise)", d2(uf) < 0.35 * d2(uw),
        f"field Σ|Δ²|={d2(uf):.4f}  white={d2(uw):.4f}")

    # P-fray: end fronds shorter than middle fronds
    fr = fronds(0.1, 0.5, 0.9, 0.5, 20, 0.1, 0.1, 3, 3, 30, 30, 0, 0, 0, 0.8, 7, 0, W, H)
    Ls = [math.hypot((p[0][1][0] - p[0][0][0]) * W, (p[0][1][1] - p[0][0][1]) * H) for p in fr]
    ends = (Ls[0] + Ls[1] + Ls[-1] + Ls[-2]) / 4
    mid = sum(Ls[8:12]) / 4
    chk("P-fray ends shorter than middle", ends < 0.8 * mid, f"ends={ends:.1f}px mid={mid:.1f}px")

    # P-depth1 BACKWARD-COMPAT (critical): depth=1 is byte-identical to a no-depth call.
    A = (0.5, 0.9, 0.5, 0.1, 9, 0.12, 0.05, 3, 2, 25, 55, 1, 0.5, 0.6, 0.4, 7, 0.18)
    d0 = fronds(*A, W, H)
    d1 = fronds(*A, W, H, 1, 0.32)
    chk("P-depth1 identical to single-level (backward compat)", d0 == d1 and len(d0) == 18,
        f"{len(d0)} fronds, equal={d0==d1}")

    # P-depth2 ROOTS-ON-PARENT: every secondary roots ON its primary's centerline segment.
    d2 = fronds(*A, W, H, 2, 0.32)
    prim = d2[:len(d0)]                                   # the primaries == the depth-1 set
    cn = max(2, round(9 * 0.55)); per = cn * 2            # children per primary (mirror)
    worst = 0.0
    for k, pr in enumerate(prim):
        seg0, seg1 = pr[0][0], pr[0][-1]                 # primary root, tip (frac)
        kids = d2[len(d0) + k * per: len(d0) + (k + 1) * per]
        for kid in kids:
            r = kid[0][0]                                # child root (frac)
            # distance (px) from child root to the primary segment
            ax, ay = seg0[0]*W, seg0[1]*H; bx, by = seg1[0]*W, seg1[1]*H
            vx, vy = bx-ax, by-ay; L2 = vx*vx+vy*vy or 1e-9
            tt = max(0, min(1, ((r[0]*W-ax)*vx + (r[1]*H-ay)*vy)/L2))
            worst = max(worst, math.hypot(r[0]*W-(ax+tt*vx), r[1]*H-(ay+tt*vy)))
    chk("P-depth2 secondaries root ON their primary", worst < 1e-6, f"worst {worst:.2e}px")

    # P-selfsimilar: mean secondary length ≈ sub × mean primary length
    plen = lambda f: math.hypot((f[0][-1][0]-f[0][0][0])*W, (f[0][-1][1]-f[0][0][1])*H)
    mp = sum(plen(p) for p in prim) / len(prim)
    sec = d2[len(d0):]
    ms = sum(plen(s) for s in sec) / len(sec)
    chk("P-selfsimilar secondary≈sub×primary length", abs(ms/mp - 0.32) < 0.12,
        f"ratio={ms/mp:.3f} (sub=0.32)")

    # P-depth2 determinism + per-parent variation (sub-arrays of different primaries differ)
    e1 = fronds(*A, W, H, 2, 0.32)
    e2 = fronds(*A, W, H, 2, 0.32)
    k0 = d2[len(d0): len(d0)+per]; k1 = d2[len(d0)+per: len(d0)+2*per]
    chk("P-depth2 reproducible + sub-seeds vary per parent",
        e1 == e2 and [x[0] for x in k0] != [x[0] for x in k1],
        f"repro={e1==e2}")

    return res


if __name__ == "__main__":
    print("=== FRONDS BLUEPRINT — falsification probes ===")
    res = run()
    for name, ok, det in res:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:48} {det}")
    print(f"  {sum(1 for _,ok,_ in res if ok)}/{len(res)} pass")

    # gestalt renders — eyeball that it reads as the natural forms
    green = (84, 120, 64)
    midrib = (((0.5, 0.92), (0.5, 0.16)), [4, 1.5])
    # a veined LEAF: fronds mirrored on a midrib, shortening + angling forward to the tip,
    # clumped + jittered + frayed + bowed (curve follows form)
    leaf = (midrib, (0.5, 0.9, 0.5, 0.2, 9, 0.14, 0.05, 3.5, 2.0, 28, 58, 1,
                     0.5, 0.6, 0.4, 3, 0.18), green, green)
    render(os.path.join(OUT, "leaf.png"), [leaf])
    # the FRACTAL leaf (depth=2): primaries off the midrib, secondaries off each primary —
    # the self-similar venation of a real leaf (compare ref/flora/leaf_pinnate_venation_pecan)
    leaf2 = (midrib, (0.5, 0.9, 0.5, 0.2, 9, 0.14, 0.05, 3.5, 2.0, 28, 58, 1,
                      0.5, 0.6, 0.4, 3, 0.18, 2, 0.34), green, green)
    render(os.path.join(OUT, "leaf_fractal.png"), [leaf2])
    # a FUR tuft / grass row: one-sided, upright, high jitter, clumped, frayed
    fur = (None, (0.15, 0.7, 0.85, 0.7, 26, 0.16, 0.16, 3, 3, 8, 8, 0,
                  0.9, 0.8, 0.6, 5, 0.05), (70, 54, 44), (0, 0, 0))
    render(os.path.join(OUT, "fur_grass.png"), [fur])
    # a UNIFORM comb (field=jit=fray=0) — the man-made special case, for contrast
    comb = (None, (0.15, 0.5, 0.85, 0.5, 16, 0.14, 0.14, 3, 3, 0, 0, 0,
                   0, 0, 0, 1, 0), (60, 60, 70), (0, 0, 0))
    render(os.path.join(OUT, "uniform_comb.png"), [comb])
    print(f"  renders → {OUT}/  (leaf, fur_grass, uniform_comb)")
