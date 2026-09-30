#!/usr/bin/env python3
"""lock_probe.py — the falsification probes for draw.py's `Lock` brush, and the goldens the
loft port pins (`loft-libs-graphics/drawing/tests/lock.loft`).

    python3 tools/lock_probe.py            # run every probe; exit 1 on the first that fails
    python3 tools/lock_probe.py --goldens  # print the two golden scenes' RGBA hex for the loft test

Each probe renders a scene through draw.py itself (`--once`) and measures the PNG, so it
tests the real tool and its real grammar. The claims are the design's, stated as
measurements: a lock is narrower where it grows than in its body, its underside is darker
than its upper side, its end splits into `tips` spikes, a lock painted later covers one
painted earlier, `dark=` shifts the shadow's HUE (white hair, blue shadow), and the render
is deterministic. The goldens are the same renderer's bytes for two tiny scenes — one on a
transparent sprite, one on an opaque ground — which is what lets the loft test run without
Python: `drawing`'s invariant is that it draws draw.py's picture, byte for byte.

Rules (formal/draw.md): the goldens are @FR-Oracle-Golden; the same-bytes probe is
@FR-Scene-Reproducible; the shape probes measure @FR-Lock-Profile, @FR-Brush-Ramp and
@FR-Brush-Layer.
"""
import os, subprocess, sys, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DRAW = os.path.join(HERE, "draw.py")


def render(src_text, tag):
    d = tempfile.mkdtemp(prefix="lock_probe_" + tag)
    src = os.path.join(d, tag + ".draw")
    with open(src, "w") as f:
        f.write(src_text)
    out = os.path.join(d, "out")
    r = subprocess.run([sys.executable, DRAW, "--once", src], capture_output=True, text=True,
                       env={**os.environ, "SKETCH_OUT": out})
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit(f"{tag}: draw.py --once failed")
    return Image.open(os.path.join(out, "canvas.png"))


def painted(px, x, y, bg=128, tol=20):
    c = px[x, y]
    return max(abs(c[0] - bg), abs(c[1] - bg), abs(c[2] - bg)) > tol


def runs_down(px, x, h):
    """How many separate painted runs a column crosses."""
    n, inside = 0, False
    for y in range(h):
        p = painted(px, x, y)
        if p and not inside:
            n += 1
        inside = p
    return n


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def band_mean(px, x0, x1, y0, y1):
    n = (x1 - x0 + 1) * (y1 - y0 + 1)
    acc = [0, 0, 0]
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c = px[x, y]
            acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]
    return (round(acc[0] / n), round(acc[1] / n), round(acc[2] / n))


fails = 0


def check(cond, what):
    global fails
    print(("  ok   " if cond else "  FAIL ") + what)
    if not cond:
        fails += 1


LOCK = """size 120x60
Background top=0.5 bottom=0.5
Lock (0.05,0.5) (0.95,0.5) w0=2 w=20 tips=3 tipvar=0 spread=0 rgb=120,80,40
"""
LAYERS = """size 120x60
Background top=0.5 bottom=0.5
Lock (0.05,0.40) (0.95,0.40) w0=20 w=20 swell=0 body=1 tips=0 rgb=200,40,40
Lock (0.05,0.60) (0.95,0.60) w0=20 w=20 swell=0 body=1 tips=0 rgb=40,40,200
"""
WHITE = """size 120x60
Background top=0.5 bottom=0.5
Lock (0.05,0.5) (0.95,0.5) w0=20 w=20 swell=0 body=1 tips=0 rgb=235,235,240 dark=140,155,200
"""
GOLDEN_SPRITE = """size 24x16
Background transparent
Lock (0.1,0.5) (0.9,0.5) w0=1 w=6 tips=2 rgb=120,80,40
"""
GOLDEN_GROUND = """size 20x12
Background top=0.5 bottom=0.5
Lock (0.1,0.3) (0.6,0.5)~ (0.9,0.9) w0=1 w=5 tips=2 rgb=200,200,210 dark=100,110,160
"""


def hexdump(im):
    im = im.convert("RGBA")
    return "".join("%02x%02x%02x%02x" % im.getpixel((x, y))
                   for y in range(im.height) for x in range(im.width))


def main():
    if "--goldens" in sys.argv[1:]:
        for name, src in (("sprite", GOLDEN_SPRITE), ("ground", GOLDEN_GROUND)):
            im = render(src, name)
            print(f"// {name}: {im.width}x{im.height}")
            h = hexdump(im)
            for i in range(0, len(h), 96):
                print('"' + h[i:i + 96] + '" +')
        return
    print("lock probes")
    im = render(LOCK, "lock")
    px = im.load()
    W, H = im.size
    # the lock runs x = 6..114; body from t=0 to 0.8 => x <= 92.4; tail 21.6 px
    root = sum(painted(px, 8, y) for y in range(H))
    body = sum(painted(px, 60, y) for y in range(H))
    check(root < body / 2, f"narrower where it grows: root column {root} px vs body {body} px")
    top = [lum(px[x, y]) for x in range(20, 80) for y in range(0, 30) if painted(px, x, y)]
    bot = [lum(px[x, y]) for x in range(20, 80) for y in range(31, H) if painted(px, x, y)]
    tm, bm = sum(top) / len(top), sum(bot) / len(bot)
    check(tm > bm + 20, f"upper side brighter than the underside: {tm:.0f} vs {bm:.0f}")
    check(runs_down(px, 94, H) == 1, f"one body just past its end: {runs_down(px, 94, H)} run(s) at x=94")
    check(runs_down(px, 105, H) == 3, f"three spikes further out: {runs_down(px, 105, H)} run(s) at x=105")
    check(not painted(px, 118, 30), "nothing beyond the longest spike")
    im2 = render(LOCK, "lock_again")
    check(im2.tobytes() == im.tobytes(), "the same scene renders the same bytes")

    # Bands, not single pixels: a third of the brush's channels are thin translucent
    # strands by design (`gap`), so any one pixel may sit on one.
    im = render(LAYERS, "layers")
    px = im.load()
    a, b = band_mean(px, 40, 80, 27, 33), band_mean(px, 40, 80, 18, 24)   # both / red only
    check(a[2] > a[0] + 30, f"the later (blue) lock covers the earlier one where they overlap: {a}")
    check(b[0] > b[2] + 30, f"the earlier (red) lock is untouched where they do not: {b}")

    im = render(WHITE, "white")
    px = im.load()
    under, upper = band_mean(px, 40, 80, 33, 37), band_mean(px, 40, 80, 22, 26)
    check(under[2] > under[0] + 10, f"white hair's underside is bluish: {under}")
    check(min(upper) > 160 and abs(upper[2] - upper[0]) < 12, f"its upper side is white: {upper}")

    print("lock probes: " + ("ALL OK" if fails == 0 else f"{fails} FAILED"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
