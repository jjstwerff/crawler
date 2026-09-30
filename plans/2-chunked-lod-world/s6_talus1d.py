#!/usr/bin/env python3
"""plan #2 S6 blueprint — the TALUS model, pinned in the cheapest medium (1-D cliff cross-section).

Each cell has BEDROCK + a RUBBLE layer. Rubble can't hold a slope steeper than the angle of
repose, so it slides to lower neighbours (a sandpile relaxation) until every rubble surface is
<= repose. Where bedrock alone is steeper than repose the rubble strips away -> BARE ROCK FACE;
the shed rubble piles at the base -> SCREE apron. Cliff placement/height = the bedrock step to
neighbours (neighbour-coupled). This pins the invariants before the mesh + loft port.

Run: python3 s6_talus1d.py
"""
import math

DX = 1.0                       # cell spacing (abstract units)
REPOSE_DEG = 35.0              # angle of repose for scree
SR = math.tan(math.radians(REPOSE_DEG)) * DX   # max rubble height-step per cell
FACE_RUB = 0.3                 # rubble below this = bedrock exposed (rock face)


def relax(bed, rub, iters=5000):
    """Gauss-Seidel sandpile: move rubble downhill until no surface step exceeds repose."""
    n = len(bed)
    for _ in range(iters):
        moved = 0.0
        for i in range(n - 1):
            sa = bed[i] + rub[i]
            sb = bed[i + 1] + rub[i + 1]
            d = sa - sb
            if d > SR and rub[i] > 0:          # i higher -> shed to i+1
                m = min(rub[i], (d - SR) / 2)
                rub[i] -= m; rub[i + 1] += m; moved += m
            elif -d > SR and rub[i + 1] > 0:   # i+1 higher -> shed to i
                m = min(rub[i + 1], (-d - SR) / 2)
                rub[i + 1] -= m; rub[i] += m; moved += m
        if moved < 1e-7:
            return _
    return iters


def classify(bed, rub):
    """per cell: F=rock face (stripped + steep bedrock), S=scree (rubble on a slope), .=soil."""
    n = len(bed)
    out = []
    for i in range(n):
        # local bedrock steepness = max step to a neighbour
        steps = []
        if i > 0:
            steps.append(abs(bed[i] - bed[i - 1]))
        if i < n - 1:
            steps.append(abs(bed[i] - bed[i + 1]))
        bed_steep = max(steps) > SR
        if rub[i] < FACE_RUB and bed_steep:
            out.append("F")
        elif rub[i] >= FACE_RUB and bed_steep:
            out.append("S")
        else:
            out.append(".")
    return out


def show(bed, rub, tag, title):
    print(f"\n{title}")
    surf = [bed[i] + rub[i] for i in range(len(bed))]
    top = max(surf)
    for level in range(int(top), int(min(bed)) - 1, -2):
        row = ""
        for i in range(len(bed)):
            s = surf[i]; b = bed[i]
            if level <= b:
                row += "#"          # bedrock
            elif level <= s:
                row += ":"          # rubble
            else:
                row += " "
        print(f"{level:4d} |{row}")
    print(f"     |{''.join(tag)}")
    print(f"     |{''.join(str(i % 10) for i in range(len(bed)))}")


def main():
    print(f"=== S6 talus model (1-D) — repose={REPOSE_DEG}deg, max rubble step SR={SR:.2f}/cell ===")
    # bedrock: high plateau (0-6), a steep CLIFF down (7-9), a valley floor rising gently (10-19)
    bed = [100.0] * 7 + [78.0, 55.0, 33.0] + [30.0 + 0.4 * k for k in range(10)]
    rub = [3.0] * len(bed)                       # uniform 3-unit weathered mantle
    rub0 = sum(rub)

    tag0 = classify(bed, rub)
    show(bed, rub, tag0, "BEFORE settling (uniform 3-unit rubble mantle):")

    relax(bed, rub)
    tag = classify(bed, rub)
    show(bed, rub, tag, "AFTER settling (rubble shed off the cliff, piled as talus below):")

    # invariants
    rub1 = sum(rub)
    n = len(bed)
    max_rub_step = 0.0
    for i in range(n - 1):
        if rub[i] > FACE_RUB and rub[i + 1] > FACE_RUB:   # rubble-on-rubble step
            max_rub_step = max(max_rub_step, abs((bed[i] + rub[i]) - (bed[i + 1] + rub[i + 1])))
    faces = tag.count("F"); scree = tag.count("S")
    print(f"\n[invariant] rubble conserved: before={rub0:.2f} after={rub1:.2f} "
          f"(delta {abs(rub1-rub0):.2e})")
    print(f"[invariant] max rubble-on-rubble step={max_rub_step:.2f} (<= repose SR={SR:.2f}? "
          f"{max_rub_step <= SR + 1e-6})")
    print(f"[result] {faces} rock-face cells (cliff), {scree} scree cells (talus apron)")
    print(f"[result] rubble depth after: {[round(r,1) for r in rub]}")


if __name__ == "__main__":
    main()
