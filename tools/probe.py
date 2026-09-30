#!/usr/bin/env python3
"""Pixel-probe harness over rendered PNGs (PLAN-RENDER P0).

The render side (a src/*probe.loft program, or gpushot) draws a deterministic
scene and gl_screenshots it; this tool asserts pixels against a spec and prints
a draw.py-style report — exact judgment moved off the eye onto measurement.
Exit 1 on any FAIL (CI-able).

Usage:
  python3 probe.py <spec.probe>     # run a spec
  python3 probe.py --selftest       # verify every command form on synthetic PNGs

Spec commands (# comments allowed; coords are PIXELS, origin TOP-LEFT, y down):
  image <path>                                  the PNG under test (first)
  probe <name> <x> <y> <r> <g> <b> [tol N]      point color (default tol 8)
  ramp <name> <x1> <y1> <x2> <y2> <inc|dec> [chan r|g|b|lum] [samples N] [tol N]
        sampled line must be monotonic (within tol per step) in the channel
  diff <name> <other.png> [tol N] [maxfrac F] [out path]
        compare image vs other: a pixel differs when any channel delta > tol
        (default 3); PASS when differing fraction <= maxfrac (default 0.0);
        out= writes a visualization (differing pixels red on the dimmed image)
"""
import sys, os
from PIL import Image

DEFAULT_TOL = 8


def load(path):
    return Image.open(path).convert("RGB")


def lum(px):
    return 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]


def run_spec(path):
    img = None
    img_path = None
    results = []  # (name, ok, text)

    def fail(name, text):
        results.append((name, False, text))

    for lineno, raw in enumerate(open(path).read().splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        t = s.split()
        cmd = t[0].lower()
        try:
            if cmd == "image":
                img_path = t[1]
                img = load(img_path)
            elif cmd == "probe":
                name = t[1]
                x, y = int(t[2]), int(t[3])
                want = (int(t[4]), int(t[5]), int(t[6]))
                tol = int(t[t.index("tol") + 1]) if "tol" in t else DEFAULT_TOL
                got = img.getpixel((x, y))
                d = max(abs(got[i] - want[i]) for i in range(3))
                ok = d <= tol
                results.append((name, ok,
                    f"probe {name} ({x},{y}) -> {got} want {want} dmax={d} tol={tol}"
                    f"  {'PASS' if ok else 'FAIL'}"))
            elif cmd == "ramp":
                name = t[1]
                x1, y1, x2, y2 = (int(t[i]) for i in range(2, 6))
                direction = t[6].lower()
                chan = t[t.index("chan") + 1] if "chan" in t else "lum"
                samples = int(t[t.index("samples") + 1]) if "samples" in t else 16
                tol = int(t[t.index("tol") + 1]) if "tol" in t else 2
                vals = []
                for k in range(samples):
                    f = k / (samples - 1)
                    px = img.getpixel((round(x1 + (x2 - x1) * f),
                                       round(y1 + (y2 - y1) * f)))
                    vals.append(lum(px) if chan == "lum"
                                else px[{"r": 0, "g": 1, "b": 2}[chan]])
                sign = 1 if direction == "inc" else -1
                bad = sum(1 for a, b in zip(vals, vals[1:])
                          if sign * (b - a) < -tol)
                ok = bad == 0 and sign * (vals[-1] - vals[0]) > 0
                results.append((name, ok,
                    f"ramp {name} ({x1},{y1})-({x2},{y2}) {chan} {direction}: "
                    f"{vals[0]:.0f}..{vals[-1]:.0f} violations={bad}"
                    f"  {'PASS' if ok else 'FAIL'}"))
            elif cmd == "diff":
                name = t[1]
                other = load(t[2])
                tol = int(t[t.index("tol") + 1]) if "tol" in t else 3
                maxfrac = float(t[t.index("maxfrac") + 1]) if "maxfrac" in t else 0.0
                out = t[t.index("out") + 1] if "out" in t else None
                if other.size != img.size:
                    fail(name, f"diff {name}: size {other.size} != {img.size}  FAIL")
                    continue
                a, b = img.load(), other.load()
                w, h = img.size
                ndiff = 0
                vis = img.point(lambda v: v // 3).convert("RGB") if out else None
                vp = vis.load() if out else None
                for yy in range(h):
                    for xx in range(w):
                        pa, pb = a[xx, yy], b[xx, yy]
                        if any(abs(pa[i] - pb[i]) > tol for i in range(3)):
                            ndiff += 1
                            if out:
                                vp[xx, yy] = (255, 0, 0)
                frac = ndiff / (w * h)
                ok = frac <= maxfrac
                if out:
                    vis.save(out)
                results.append((name, ok,
                    f"diff {name} vs {t[2]}: {ndiff}px ({100*frac:.3f}%) "
                    f"tol={tol} maxfrac={maxfrac}  {'PASS' if ok else 'FAIL'}"
                    + (f"  -> {out}" if out else "")))
            else:
                fail(f"line{lineno}", f"UNPARSED line {lineno}: {s}  FAIL")
        except Exception as e:  # a malformed line is a FAIL, never a crash
            fail(f"line{lineno}", f"ERROR line {lineno}: {s}  ({e})  FAIL")

    npass = sum(1 for _, ok, _ in results if ok)
    print(f"PROBE {os.path.basename(path)}  image={img_path}")
    for _, _, text in results:
        print("  " + text)
    print(f"  CHECKS {npass}/{len(results)} pass")
    return npass == len(results) and len(results) > 0


def selftest():
    """Exercise every command form on synthetic PNGs; expected FAILs included."""
    import tempfile
    d = tempfile.mkdtemp(prefix="probe_self_")
    w, h = 64, 64
    img = Image.new("RGB", (w, h), (10, 20, 30))
    for x in range(w):                       # horizontal luminance ramp rows 0..15
        for y in range(16):
            img.putpixel((x, y), (4 * x, 4 * x, 4 * x))
    for x in range(32, 48):                  # a flat colored block
        for y in range(32, 48):
            img.putpixel((x, y), (200, 100, 50))
    p1 = os.path.join(d, "a.png"); img.save(p1)
    img2 = img.copy()
    for x in range(56, 60):                  # 16px difference patch
        for y in range(56, 60):
            img2.putpixel((x, y), (255, 255, 255))
    p2 = os.path.join(d, "b.png"); img2.save(p2)

    spec = os.path.join(d, "self.probe")
    open(spec, "w").write(f"""
image {p1}
probe block 40 40 200 100 50 tol 0
probe bg 2 60 10 20 30
ramp grad 0 8 63 8 inc chan lum
diff same {p1} tol 0 maxfrac 0
""")
    ok_pass = run_spec(spec)
    open(spec, "w").write(f"""
image {p1}
probe wrong 40 40 0 255 0 tol 4
ramp notdec 0 8 63 8 dec
diff differs {p2} tol 0 maxfrac 0
""")
    ok_fail = run_spec(spec)
    if ok_pass and not ok_fail:
        print("SELFTEST OK (pass-spec passed, fail-spec failed)")
        return True
    print("SELFTEST FAILED")
    return False


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(0 if run_spec(sys.argv[1]) else 1)


if __name__ == "__main__":
    main()
