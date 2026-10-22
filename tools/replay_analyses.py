"""Rerun the study's merge, scoring, prediction scoring and independent rechecks, and compare every output with the
shipped file.

    python tools/replay_analyses.py          # after tools/unpack.py; NumPy and SciPy; exit status 1 on a difference

Every step runs in one temporary copy of the release, in the order the study ran them, after the outputs the steps
write have been removed from the copy (the scorers write each confirmation result once and refuse to overwrite it):

- the merge of the two blind extractions into findings and the merged table (stage 1 and the supplement);
- stage 1 on the development and confirmation models (score.py, recheck.py) and its confirmation predictions
  (score_predictions.py);
- stage 2's pair scores (stage2_score.py), the supplement's scores and report (stage2_strother.py), the stage-2
  confirmation predictions (stage2_predictions.py) and the rechecks (stage2_recheck.py, stage2_strother.py recheck).

The two development-set prediction files are not rerun: they were scored during development, before the merged table
and the confirmation run existed, so scoring them now gives more verdicts than the saved files hold.

The rechecks use only Python's standard library and run in isolated mode, as in the study. The scorers first check the
freeze records (the release's documented changes pass). Outputs are compared byte for byte, except that the
supplement recheck's record names its table by absolute path: there the copy's root is replaced by the placeholder
that the shipped record carries.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RELEASE = Path(__file__).resolve().parents[1]
TABLE = "../extraction/stage2/supplement-table.csv"
SCORES = ["comparisons.csv", "per-model.csv", "summary.json"]
WORK = ["units-A.csv", "units-B.csv", "findings-A.csv", "findings-B.csv", "unit-comparison.csv",
        "finding-comparison.csv", "agreement.json"]
S2 = "results/stage2/scores"
SUP = "results/stage2/strother/results"
STEPS = [  # (interpreter flag, arguments run in code/, outputs)
    ("-B", ["units.py"], [f"extraction/merge-work/{f}" for f in WORK]),
    ("-B", ["merge_findings.py"], ["extraction/merged-table.csv"]),
    ("-B", ["stage2_units.py"], [f"extraction/stage2/merge-work/{f}" for f in WORK]),
    ("-B", ["stage2_merge.py"], ["extraction/stage2/supplement-table.csv", "extraction/stage2/repeats.csv"]),
    ("-B", ["score.py", "development"], [f"results/development/{f}" for f in SCORES]),
    ("-I", ["recheck.py", "development"], ["results/development/recheck.json"]),
    ("-B", ["score.py", "confirmation"], [f"results/confirmation/{f}" for f in SCORES]),
    ("-B", ["score_predictions.py", "confirmation"], ["results/confirmation/predictions-scored.json"]),
    ("-I", ["recheck.py", "confirmation"], ["results/confirmation/recheck.json"]),
    ("-B", ["stage2_score.py", "development"], [f"{S2}/development/{f}" for f in SCORES]),
    ("-I", ["stage2_recheck.py", "development"], [f"{S2}/development/recheck.json"]),
    ("-B", ["stage2_score.py", "confirmation"], [f"{S2}/confirmation/{f}" for f in SCORES]),
    ("-B", ["stage2_strother.py", "score", TABLE],
     [f"{SUP}/development/settings.json"] + [f"{SUP}/confirmation/{f}" for f in SCORES]),
    ("-B", ["stage2_strother.py", "report", TABLE], [f"{SUP}/confirmation/report.json"]),
    ("-B", ["stage2_predictions.py", "confirmation"], [f"{S2}/confirmation/predictions-scored.json"]),
    ("-I", ["stage2_recheck.py", "confirmation"], [f"{S2}/confirmation/recheck.json"]),
    ("-I", ["stage2_strother.py", "recheck", TABLE], [f"{SUP}/confirmation/recheck.json"]),
    ("-I", ["stage2_recheck.py", "strother"], [f"{SUP}/confirmation/recheck-report.json"]),
]
ABSOLUTE = {f"{SUP}/confirmation/recheck.json"}     # records that name a file by absolute path


def skip(folder, names):
    """Leave out caches, environments, the FlyVis models and, at the top level, the packed archives."""
    out = {n for n in names if n in ("__pycache__", ".cache", "flyvis-root", "gpu.lock") or n.startswith(".venv")}
    if Path(folder).resolve() == RELEASE:
        out |= {n for n in names if n in ("data", "models")}
    return out


def main():
    if not (RELEASE / "results/stage2/scores/confirmation/summary.json").exists():
        sys.exit("saved outputs missing; run tools/unpack.py (make unpack) first")
    failed = 0
    with tempfile.TemporaryDirectory(prefix="replay-") as tmp:
        work = Path(tmp) / "release"
        shutil.copytree(RELEASE, work, symlinks=True, ignore=skip)
        root = str(work.resolve())
        for _, _, outs in STEPS:
            for o in outs:
                (work / o).unlink(missing_ok=True)
        for flag, args, outs in STEPS:
            run = subprocess.run([sys.executable, flag, *args], cwd=work / "code", capture_output=True, text=True)
            name = " ".join(args).replace(TABLE, "<table>")
            if run.returncode != 0:
                failed += 1
                print(f"FAIL  {name} exited with {run.returncode}")
                print("      " + (run.stdout + run.stderr).strip().replace("\n", "\n      ")[-2000:])
                continue
            for o in outs:
                mine = (work / o).read_bytes() if (work / o).exists() else None
                if mine is not None and o in ABSOLUTE:
                    mine = mine.replace(root.encode(), b"<project>")
                same = mine == (RELEASE / o).read_bytes()
                failed += not same
                print(f"{'identical' if same else 'DIFFERENT'}  {o}  ({name})")
    print(f"{len(STEPS)} steps rerun from the saved inputs: "
          + ("every output identical to the shipped file" if not failed else f"{failed} problem(s)"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
