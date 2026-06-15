#!/usr/bin/env python3
"""@PLN2 S6.1 — the TALUS model in 2-D, weathering-driven rubble, on a fine alpine patch
representative of the loft DETAIL tier (a base relief + fbm — the same shape ov_sample produces).

Why not the real Ortler bedrock: at any samplable resolution it is too smooth to exceed the angle
of repose (a 2 km drop over 13 km is ~8 deg, nowhere near 35) — talus only forms where there are
FINE local steps, which is precisely the detail tier. So we prototype on the fine field here; S6.2
runs the same relaxation on the actual loft ov_sample field.

Model: bedrock + WEATHERING-driven rubble (more debris from high/cold bedrock above the treeline).
Rubble can't hold > angle of repose, so it slides to lower neighbours (2-D sandpile). Where bedrock
alone exceeds repose the rubble strips -> K_FACE; the shed rubble piles below at repose -> K_SCREE.

Run: python3 s6_talus2d.py
"""
import math
import numpy as np

H, W = 44, 64
CELL_M = 2.0                     # detail-tier cell size (~ loft DETAIL_CELL_M scale)
REPOSE_DEG = 35.0
SR = math.tan(math.radians(REPOSE_DEG)) * CELL_M   # max rubble height-step between ortho neighbours
TREELINE = 70.0                  # above -> bare/frost-shattered (rubble-producing); below -> forest
FACE_RUB = 0.3                   # rubble below this = bedrock exposed


def synth_bedrock():
    """a fine alpine patch: tilt + a steep escarpment (the cliff) + a peak + fbm roughness."""
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    bed = 110.0 - 0.6 * yy                                   # gentle regional tilt
    bed -= 48.0 * np.clip((yy - H * 0.42) / (H * 0.10), 0, 1)  # ESCARPMENT: ~48 m drop over ~4 rows
    bed += 30.0 * np.exp(-(((xx - W * 0.32) ** 2 + (yy - H * 0.16) ** 2) / (2 * (W * 0.11) ** 2)))  # peak
    rng = np.random.default_rng(0)
    nz = np.zeros((H, W))
    for oct in range(3):                                     # cheap fbm: summed upsampled noise
        s = 2 ** (oct + 2)
        coarse = rng.standard_normal((H // s + 2, W // s + 2))
        up = np.kron(coarse, np.ones((s, s)))[:H, :W]
        nz += up * (5.0 / (oct + 1))
    return bed + nz


def weathering_rubble(bed):
    """frost-shattering: production rises above the treeline (cold, bare). A mantle, then it settles."""
    return 1.0 + 6.0 * np.clip((bed - TREELINE) / 40.0, 0, 1)


def relax2d(bed, rub, iters=4000):
    """4-neighbour Gauss-Seidel sandpile (in-place, exactly conservative). Rubble -> lower neighbour
    until no rubble-on-rubble step exceeds repose."""
    for it in range(iters):
        moved = 0.0
        for r in range(H):
            for c in range(W):
                if rub[r, c] <= 1e-9:
                    continue
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= H or nc < 0 or nc >= W:
                        continue
                    d = (bed[r, c] + rub[r, c]) - (bed[nr, nc] + rub[nr, nc])
                    if d > SR and rub[r, c] > 1e-9:
                        m = min(rub[r, c], (d - SR) / 2.0)
                        rub[r, c] -= m; rub[nr, nc] += m; moved += m
        if moved < 1e-5:
            return it
    return iters


def classify(bed, rub, rub0):
    """K_FACE / K_SCREE / soil per cell. ZAngband zone gate: below the treeline -> forest holds the
    rubble (no faces); above -> rock is exposed where stripped, scree where rubble piled up."""
    tag = np.full((H, W), ".", dtype="<U1")
    for r in range(H):
        for c in range(W):
            below_tree = bed[r, c] < TREELINE
            # local bedrock steepness = max step to an in-bounds neighbour
            steep = False
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and abs(bed[r, c] - bed[nr, nc]) > SR:
                    steep = True
            if below_tree:
                tag[r, c] = "f" if (rub[r, c] < FACE_RUB and steep) else "T"  # forest (T=trees)
            elif rub[r, c] < FACE_RUB and steep:
                tag[r, c] = "F"                                  # bare rock face
            elif rub[r, c] - rub0[r, c] > 0.5:
                tag[r, c] = "s"                                  # scree (net accumulation = talus)
            else:
                tag[r, c] = "."                                  # alpine soil / meadow
    return tag


def main():
    print(f"=== S6.1 — 2-D talus, weathering-driven rubble (repose={REPOSE_DEG}deg, "
          f"cell={CELL_M}m, SR={SR:.2f}m/cell, treeline={TREELINE:.0f}m) ===")
    bed = synth_bedrock()
    rub0 = weathering_rubble(bed)
    rub = rub0.copy()
    tot0 = rub.sum()

    its = relax2d(bed, rub)
    tag = classify(bed, rub, rub0)

    # invariants
    tot1 = rub.sum()
    max_step = 0.0
    for r in range(H):
        for c in range(W):
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if nr < H and nc < W and rub[r, c] > FACE_RUB and rub[nr, nc] > FACE_RUB:
                    max_step = max(max_step, abs((bed[r, c] + rub[r, c]) - (bed[nr, nc] + rub[nr, nc])))
    nF = int((tag == "F").sum()); ns = int((tag == "s").sum())
    nf = int((tag == "f").sum()); nT = int((tag == "T").sum())

    print(f"\nclassification map (F=rock face, s=scree talus, .=alpine soil, T=forest, "
          f"f=forest cliff)  — converged in {its} iters")
    for r in range(H):
        print("  " + "".join(tag[r]))

    print(f"\n[invariant] rubble conserved: {tot0:.2f} -> {tot1:.2f} (delta {abs(tot1-tot0):.2e})")
    print(f"[invariant] max rubble-on-rubble step = {max_step:.3f}  (<= repose SR={SR:.2f}? "
          f"{max_step <= SR + 1e-4})")
    print(f"[result] faces={nF} scree={ns} alpine-soil={int((tag=='.').sum())} "
          f"forest={nT} forest-cliff={nf}")
    print(f"[result] faces sit on the escarpment; scree pools just BELOW it (the talus apron).")


if __name__ == "__main__":
    main()
