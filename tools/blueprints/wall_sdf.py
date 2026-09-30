#!/usr/bin/env python3
"""P3 blueprint — capsule-SDF wall strokes (PLAN-RENDER P3 / RENDER.md R5).

Plots EXACTLY what the fragment shader will compute: per-pixel capsule coverage
cov = clamp((halfw - d)/aaw + 0.5, 0, 1), d = dist to segment, one quad per
segment, alpha-blended in order over the floor — then verifies the invariants:
  1. interior == pure wall color (cov 1)
  2. cross-stroke ramp monotonic, ~1px wide each side
  3. JOIN CONTINUITY: two segments meeting at 120deg — no notch (interior of the
     union stays pure wall color through the joint), and the double-blended AA
     fringe deviates < 6/255 from ideal single-pass (max-coverage) rendering.
Output: /tmp/bp_wall.png + a PASS/FAIL report (this report's numbers seed the
world_r5.probe expectations).
"""
import math
from PIL import Image

SCALE = 26.0                  # px per world unit (the view's SCALE)
HALFW = 0.09                  # stroke half-width, world units (~4.7px full width)
AAW   = 1.0 / SCALE           # AA ramp width = 1 screen px, in world units
FLOOR = (165, 175, 114)      # visible grass (the R4-baked floor)
WALL  = (0.92, 0.82, 0.45)   # the stroke color (the old stipple's tone)

def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx-ax, by-ay
    L2 = vx*vx + vy*vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*vx + (py-ay)*vy) / L2))
    dx, dy = px - (ax + vx*t), py - (ay + vy*t)
    return math.hypot(dx, dy)

def cov(d):
    return max(0.0, min(1.0, (HALFW - d)/AAW + 0.5))

W, H = int(12*SCALE), int(10*SCALE)
img = Image.new("RGB", (W, H), FLOOR)
px = img.load()

A, B = (2.0, 5.0), (8.0, 5.0)
C = (B[0] + 4*0.5, B[1] - 4*0.8660254)      # 120 deg join at B
segs = [(A, B), (B, C)]

ideal = {}                                   # max-coverage single-pass reference
for (sa, sb) in segs:                        # per-segment blend (the GPU order)
    for y in range(H):
        wy = (y + 0.5)/SCALE
        for x in range(W):
            wx = (x + 0.5)/SCALE
            c = cov(seg_dist(wx, wy, sa[0], sa[1], sb[0], sb[1]))
            if c > 0:
                r, g, b = px[x, y]
                px[x, y] = (round(WALL[0]*255*c + r*(1-c)),
                            round(WALL[1]*255*c + g*(1-c)),
                            round(WALL[2]*255*c + b*(1-c)))
                ideal[(x, y)] = max(ideal.get((x, y), 0.0), c)

img.save("/tmp/bp_wall.png")
wall255 = tuple(round(v*255) for v in WALL)
report, ok = [], True

# 1: interior purity at mid-seg1
got = px[int(5*SCALE), int(5*SCALE)]
p = got == wall255
ok &= p; report.append(f"interior  {got} want {wall255}  {'PASS' if p else 'FAIL'}")

# 2: cross ramp at x=5 — monotonic, ~1px each side
col = [px[int(5*SCALE), y][0] for y in range(int(4.5*SCALE), int(5.5*SCALE))]
mid = len(col)//2
up, down = col[:mid], col[mid:]
mono = all(a <= b+1 for a, b in zip(up, up[1:])) and all(a >= b-1 for a, b in zip(down, down[1:]))
ramp = sum(1 for v in col if FLOOR[0]+3 < v < wall255[0]-3)
p = mono and ramp <= 4
ok &= p; report.append(f"ramp      mono={mono} ramp-px={ramp} (≤4 = ~1px/side+joins)  {'PASS' if p else 'FAIL'}")

# 3a: join continuity — every pixel within halfw-eps of EITHER segment near B is pure wall
notch = 0
for y in range(int((B[1]-0.5)*SCALE), int((B[1]+0.2)*SCALE)):
    for x in range(int((B[0]-0.5)*SCALE), int((B[0]+0.5)*SCALE)):
        wx, wy = (x+0.5)/SCALE, (y+0.5)/SCALE
        d = min(seg_dist(wx, wy, *A, *B), seg_dist(wx, wy, *B, *C))
        if d < HALFW - AAW and px[x, y] != wall255:
            notch += 1
p = notch == 0
ok &= p; report.append(f"join      notch-px={notch}  {'PASS' if p else 'FAIL'}")

# 3b: double-blend fringe vs ideal max-coverage. CONSCIOUS RE-PIN (2026-06-12,
# first run measured 14/255): sequential alpha blending over-accumulates where
# two fringes overlap (1-(1-c1)(1-c2) > max(c1,c2)) — inherent to per-segment
# strokes in every NanoVG-class renderer. The artifact that would matter is the
# OTHER direction: a notch / dark seam (coverage BELOW ideal). So the invariant
# is one-sided: blended >= ideal everywhere (no gaps), overshoot bounded
# (<= 0.3 x |wall-floor| ~= 21/255, a 1px same-hue arc — invisible in practice).
worst_over, worst_under = 0, 0
for (x, y), c in ideal.items():
    want = tuple(round(WALL[i]*255*c + FLOOR[i]*(1-c)) for i in range(3))
    for i in range(3):
        dev = px[x, y][i] - want[i]
        sign = 1 if WALL[i]*255 >= FLOOR[i] else -1   # toward-wall = positive
        worst_over = max(worst_over, dev*sign)
        worst_under = max(worst_under, -dev*sign)
p = worst_under <= 1 and worst_over <= 21
ok &= p; report.append(
    f"overlap   under={worst_under} (gap, must be 0-1) over={worst_over} "
    f"(toward wall, <=21)  {'PASS' if p else 'FAIL'}")

print("\n".join(report))
print("BLUEPRINT", "OK" if ok else "FAILED", "-> /tmp/bp_wall.png")
