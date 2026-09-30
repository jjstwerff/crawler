#!/usr/bin/env python3
"""collision_fit.py — pick each tower footprint by BEST COLLISION MATCH, not by radius.

The objective is NOT "reproduce a circle of radius r".  The rasterisation threshold is
just a knob for generating candidates; what matters is that the resulting hex footprint
is the best circle a collision query can experience.  So:

    * sweep the threshold to generate candidate footprints (each must pass the
      validity battery: no enclosed gaps, wall one hex thick, nested in the size below);
    * for each candidate, ray-cast the emitted outline to get the effective radius
      r(theta) a collision query actually sees;
    * fit the circle that minimises the residual -- for a centred shape that is simply
      R = mean(r(theta)), which provably minimises sum (r-R)^2;
    * choose the candidate with the smallest WORST-CASE error max|r(theta) - R|,
      because collision is felt at its worst point, not on average.

The published number per size is then the EFFECTIVE COLLISION RADIUS R -- an output of
the fit, not an input.  Errors are in hex widths (1.0 = one whole hex out of place).

    python3 plans/5-geometry/collision_fit.py
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hexforms import (SQ3, bfs, wall_one_thick, enclosed_gaps,
                      f_hexdisk, f_circle, f_octagon)
from roundness import outline_radii

HEXW = SQ3
SAMPLES = 720


def collision_fit(form):
    """Effective radius + worst-case / rms error, as a collision query experiences it."""
    rs = [r for _, r in outline_radii(form, samples=SAMPLES)]
    R = sum(rs) / len(rs)                      # minimises sum (r-R)^2 for a centred shape
    worst = max(abs(r - R) for r in rs) / HEXW
    rms = math.sqrt(sum((r - R) ** 2 for r in rs) / len(rs)) / HEXW
    aniso = max(rs) / min(rs)
    return R, worst, rms, aniso


def main():
    dist = bfs(16)
    SIZES = range(2, 11)

    print("Objective: minimise WORST-CASE collision error against the best-fit circle.")
    print("The threshold is a knob; the published radius R is an OUTPUT of the fit.")
    print("Errors in hex widths (1.0 = one whole hex out of place).\n")

    print(f"{'N':>2} | {'A hex-disk':^26} | {'B best-collision fit':^42}")
    print(f"{'':>2} | {'R':>7} {'worst':>7} {'rms':>7} | {'thresh':>7} {'R':>7} "
          f"{'worst':>7} {'rms':>7} {'cells':>6} {'gain':>6}")
    print("-" * 76)

    chosen, prev = {}, None
    for N in SIZES:
        A = f_hexdisk(N, dist)
        Ra, wa, ra, _ = collision_fit(A)

        best = None
        t = (N - 0.5) * SQ3
        while t <= (N + 1.0) * SQ3:
            f = f_circle(N, dist, t)
            if f and not enclosed_gaps(f, dist) and wall_one_thick(f) \
               and (prev is None or prev <= f):
                R, w, rms, aniso = collision_fit(f)
                if best is None or w < best[2]:
                    best = (t, R, w, rms, len(f), f, aniso)
            t += 0.02

        if best is None:
            print(f"{N:>2} | {Ra:>7.3f} {wa:>7.3f} {ra:>7.3f} |  (no legal candidate)")
            continue
        t, R, w, rms, nc, f, aniso = best
        gain = wa / w if w > 0 else float("inf")
        print(f"{N:>2} | {Ra:>7.3f} {wa:>7.3f} {ra:>7.3f} | {t:>7.3f} {R:>7.3f} "
              f"{w:>7.3f} {rms:>7.3f} {nc:>6} {gain:>5.2f}x")
        chosen[N] = (t, R, w, nc)
        prev = f

    print("\nchosen thresholds and the EFFECTIVE COLLISION RADIUS to publish per size:")
    print(f"{'N':>2} {'threshold':>10} {'R_eff':>8} {'R_eff/N':>8} {'worst err':>10} {'cells':>6}")
    for N, (t, R, w, nc) in chosen.items():
        print(f"{N:>2} {t:>10.3f} {R:>8.3f} {R/N:>8.3f} {w:>10.3f} {nc:>6}")

    if chosen:
        ratios = [R / N for _, (_, R, _, _) in chosen.items()]
        print(f"\nR_eff/N is {'stable' if max(ratios)-min(ratios) < 0.12 else 'NOT stable'}: "
              f"{min(ratios):.3f}..{max(ratios):.3f}  (mean {sum(ratios)/len(ratios):.3f})")
        print("A hex-disk worst-case error for comparison — note it never improves:")
        for N in (4, 7, 10):
            _, w, _, _ = collision_fit(f_hexdisk(N, dist))
            print(f"   N={N:<2} worst={w:.3f} hex widths")


if __name__ == "__main__":
    main()
