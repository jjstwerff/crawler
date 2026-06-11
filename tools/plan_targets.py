#!/usr/bin/env python3
"""Candidate TARGET plots for PLAN-GEOMETRY.md steps 1.0 / 2.0.

Hand-constructed pictures of the intended END RESULT (not algorithm output):
the user confirms/amends these before any port. Light floor, dark walls
(CLAUDE.md palette).

    python3 tools/plan_targets.py     # writes tools/wallproto/out/target_*.png
"""
import math, os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "wallproto", "out")
os.makedirs(OUT, exist_ok=True)

FLOOR = (214, 196, 158)   # warm aged stone
WALL = (62, 54, 48)
ROAD = (150, 128, 96)
ACCENT = (170, 60, 40)
GRID = (196, 178, 140)

SNAP = math.pi / 12.0     # 15 degrees


def canvas(w=640, h=480):
    im = Image.new("RGB", (w, h), FLOOR)
    d = ImageDraw.Draw(im)
    for x in range(0, w, 32):
        d.line([(x, 0), (x, h)], fill=GRID)
    for y in range(0, h, 32):
        d.line([(0, y), (w, y)], fill=GRID)
    return im, d


def snap_leg(x, y, ang_steps, length):
    a = ang_steps * SNAP
    return x + length * math.cos(a), y + length * math.sin(a)


def thick_leg(d, ax, ay, bx, by, w, color=WALL):
    """A wall band as its two offset faces + fill."""
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    d.polygon([(ax + nx, ay + ny), (bx + nx, by + ny),
               (bx - nx, by - ny), (ax - nx, ay - ny)], fill=color)


def tangent_trim(ax, ay, bx, by, cx, cy, r):
    """Trim segment end (b) back so it stops ON the circle (the attach rule)."""
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    # project the centre on the leg, step back by the chord half-length
    t = (cx - ax) * ux + (cy - ay) * uy
    px, py = ax + t * ux, ay + t * uy
    h = math.hypot(cx - px, cy - py)
    back = math.sqrt(max(r * r - h * h, 0.0))
    return ax, ay, ax + (t - back) * ux, ay + (t - back) * uy


def t1_curtain():
    im, d = canvas()
    w = 14.0
    pts = [(80, 380)]
    for steps, ln in [(-1, 180), (-4, 150), (1, 170), (-6, 120)]:
        x, y = pts[-1]
        pts.append(snap_leg(x, y, steps, ln))
    r = 26
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        # trim both ends back onto the corner-tower circles, then draw the band
        _, _, tx, ty = tangent_trim(ax, ay, bx, by, bx, by, r)
        _, _, sx, sy = tangent_trim(bx, by, ax, ay, ax, ay, r)
        thick_leg(d, sx, sy, tx, ty, w)
    for x, y in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=WALL)
        d.ellipse([x - r + 6, y - r + 6, x + r - 6, y + r - 6], fill=FLOOR)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=ACCENT)
    d.text((12, 8), "T1 curtain wall: 15deg legs, ROUND corner towers,"
                    " bands STOP on the circle (tangent attach)", fill=WALL)
    im.save(os.path.join(OUT, "target_curtain.png"))


def t2_road():
    im, d = canvas()
    w = 22.0
    pts = [(40, 420)]
    for steps, ln in [(-2, 200), (0, 150), (-3, 180)]:
        x, y = pts[-1]
        pts.append(snap_leg(x, y, steps, ln))
    # road surface then the two offset OUTLINES with rounded elbows
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        thick_leg(d, ax, ay, bx, by, w, color=ROAD)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        d.line([(ax + nx, ay + ny), (bx + nx, by + ny)], fill=WALL, width=2)
        d.line([(ax - nx, ay - ny), (bx - nx, by - ny)], fill=WALL, width=2)
    for x, y in pts[1:-1]:
        d.arc([x - w / 2, y - w / 2, x + w / 2, y + w / 2], 0, 360, fill=WALL)
    # a fork
    fx, fy = pts[2]
    gx, gy = snap_leg(fx, fy, -5, 140)
    thick_leg(d, fx, fy, gx, gy, w, color=ROAD)
    dxy = math.hypot(gx - fx, gy - fy)
    nx, ny = -(gy - fy) / dxy * w / 2, (gx - fx) / dxy * w / 2
    d.line([(fx + nx, fy + ny), (gx + nx, gy + ny)], fill=WALL, width=2)
    d.line([(fx - nx, fy - ny), (gx - nx, gy - ny)], fill=WALL, width=2)
    d.text((12, 8), "T2 road: 24-dir centerline, parallel offset outlines,"
                    " rounded junction elbows + a fork", fill=WALL)
    im.save(os.path.join(OUT, "target_road.png"))


def t3_fence():
    im, d = canvas()
    # a building corner (90deg, dir-12 placement)
    d.polygon([(120, 120), (300, 120), (300, 240), (120, 240)], outline=WALL, width=6)
    # fence: thin band at odd 15deg angles, attached to the building corner
    pts = [(300, 240)]
    for steps, ln in [(1, 150), (3, 120), (0, 130)]:
        x, y = pts[-1]
        pts.append(snap_leg(x, y, steps, ln))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        d.line([(ax, ay), (bx, by)], fill=WALL, width=3)
    for x, y in pts:
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=WALL)
    d.text((12, 8), "T3 fence: thin 15deg-snapped band, posts at vertices,"
                    " attached to a building corner", fill=WALL)
    im.save(os.path.join(OUT, "target_fence.png"))


def t_layers():
    im = Image.new("RGB", (880, 460), FLOOR)
    d = ImageDraw.Draw(im)
    for pane, (ox, label) in enumerate([(20, "LAYER 0 ground"), (460, "LAYER 1 rampart")]):
        d.rectangle([ox, 40, ox + 400, 440], outline=WALL, width=2)
        d.text((ox + 6, 44), label, fill=WALL)
        # curtain rectangle, 2-hex wide
        for off in (0, 18):
            d.rectangle([ox + 60 + off, 100 + off, ox + 340 - off, 380 - off],
                        outline=WALL, width=4)
        if pane == 0:
            d.rectangle([ox + 60 + 4, 100 + 4, ox + 340 - 4, 380 - 4],
                        outline=None)  # band solid at ground:
            d.rectangle([ox + 64, 104, ox + 336, 118], fill=WALL)
            d.rectangle([ox + 64, 362, ox + 336, 376], fill=WALL)
            d.rectangle([ox + 64, 104, ox + 78, 376], fill=WALL)
            d.rectangle([ox + 322, 104, ox + 336, 376], fill=WALL)
            d.rectangle([ox + 180, 362, ox + 220, 376], fill=ROAD)  # the gate
            d.text((ox + 168, 388), "gate", fill=WALL)
            # the keep: SEALED at ground
            d.rectangle([ox + 160, 200, ox + 240, 280], fill=WALL)
            d.text((ox + 150, 284), "keep (sealed)", fill=ACCENT)
        else:
            # rampart: the band TOP is walkable floor with parapet edges
            d.rectangle([ox + 64, 104, ox + 336, 118], fill=ROAD)
            d.rectangle([ox + 64, 362, ox + 336, 376], fill=ROAD)
            d.rectangle([ox + 64, 104, ox + 78, 376], fill=ROAD)
            d.rectangle([ox + 322, 104, ox + 336, 376], fill=ROAD)
            # keep roof open from above
            d.rectangle([ox + 160, 200, ox + 240, 280], outline=WALL, width=4)
            d.rectangle([ox + 188, 228, ox + 212, 252], fill=ROAD)
            d.text((ox + 246, 232), "drop-in", fill=ACCENT)
        # corner towers exist on both panes (solid / upper floor)
        for cx, cy in [(ox + 70, 110), (ox + 330, 110), (ox + 70, 370), (ox + 330, 370)]:
            d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=WALL)
            if pane == 1:
                d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=ROAD)
        # stairs in the gate tower
        sx, sy = ox + 330, 370
        d.text((sx - 14, sy - 6), "S", fill=ACCENT)
    # traversal path: climb (pane 0 S) -> cross rampart -> drop into keep (pane 1)
    d.line([(350, 370), (440, 370), (480, 370)], fill=ACCENT, width=3)
    d.line([(790, 370), (790, 240), (690, 240), (660, 240)], fill=ACCENT, width=3)
    d.text((300, 8), "TARGET 2.0: climb gate-tower stairs (S, layer0->1), cross the"
                     " rampart, drop into the sealed keep", fill=WALL)
    im.save(os.path.join(OUT, "target_layers.png"))


t1_curtain()
t2_road()
t3_fence()
t_layers()
print("targets written to", OUT)
