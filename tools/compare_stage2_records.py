"""Compare stage-2 pair-silencing records simulated again (in a copy of the release) with the saved records.

    python tools/compare_stage2_records.py <copy> development|confirmation      (make stage2-rerun runs it)

Every saved record of the phase needs a record of the same model, stimulus, strength and pair in <copy>. Peaks are
compared as the study's replay check compared them: the largest absolute difference divided by the largest saved
peak, against the study's tolerance of 1e-4. Direction selectivity and denominators are reported by their largest
absolute difference. The saved records are the release's reduced copies (every array except the time trace).
Exit status 1 if a record is missing or a peak gap exceeds the tolerance.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

RELEASE = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-4


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("development", "confirmation"):
        sys.exit(__doc__)
    copy, phase = Path(sys.argv[1]), sys.argv[2]
    saved = sorted((RELEASE / "results/stage2" / phase).glob("*/*/s*-*.npz"))
    if not saved:
        sys.exit("saved records missing; run tools/unpack.py (make unpack) first")
    worst = {"peaks": 0.0, "dsi": 0.0, "denominator": 0.0}
    missing, over = [], []
    for path in saved:
        rel = path.relative_to(RELEASE)
        new = copy / rel
        if not new.exists():
            missing.append(str(rel))
            continue
        with np.load(path, allow_pickle=False) as a, np.load(new, allow_pickle=False) as b:
            old_peaks, new_peaks = a["peaks"].astype(np.float64), b["peaks"].astype(np.float64)
            gap = float(np.max(np.abs(new_peaks - old_peaks))) / max(float(np.max(old_peaks)), 1e-8)
            worst["peaks"] = max(worst["peaks"], gap)
            for key in ("dsi", "denominator"):
                worst[key] = max(worst[key], float(np.max(np.abs(b[key].astype(np.float64) - a[key].astype(np.float64)))))
        if gap > TOLERANCE:
            over.append(f"{rel}: {gap:.2e}")
    print(f"{phase}: {len(saved) - len(missing)} of {len(saved)} records compared; worst normalised peak gap "
          f"{worst['peaks']:.2e} (tolerance {TOLERANCE:g}); largest difference in direction selectivity "
          f"{worst['dsi']:.2e}, in denominators {worst['denominator']:.2e}")
    for m in missing[:20]:
        print("MISSING", m)
    for o in over[:20]:
        print("OVER TOLERANCE", o)
    sys.exit(1 if missing or over else 0)


if __name__ == "__main__":
    main()
