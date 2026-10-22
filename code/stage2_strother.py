"""Stage 2, Part 2: score Strother's supplement findings with stage 1's frozen scorer, unchanged.

  python -B stage2_strother.py score <table>       code/score.py (confirmation) on the supplement table, with its
                                                   output folder redirected to results/stage2/strother/results/
  python3 -I stage2_strother.py recheck <table>    stage 1's recheck.py on the same outputs and table
  python -B stage2_strother.py report <table>      the descriptive Part 2 numbers (report.json beside the scores):
                                                   stage 1's primary comparisons together with the supplement's, and
                                                   the four Fig. S2B comparisons that prediction R1 names

Nothing in stage 1's code is changed: score.py and recheck.py are imported as they are, and only the folder they
read their settings from and write their outputs to is redirected. The frozen settings file is copied byte for byte
and checked against FREEZE.json. Scoring is refused unless FREEZE.json and FREEZE-STAGE2-STROTHER.json match.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
STUDY = CODE.parent
ROOT = STUDY / "results/stage2/strother"          # plays the role of the study folder for score.py's outputs
SETTINGS = "results/development/settings.json"
sys.path.insert(0, str(STUDY / "tools"))
import release_paths as _release_paths  # noqa: E402  (release: documented changes pass the checks)


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_freezes(table: Path) -> None:
    stage1 = json.loads((STUDY / "FREEZE.json").read_text())
    for rel, digest in stage1["files_sha256"].items():
        if not _release_paths.matches(STUDY / rel, digest):
            sys.exit(f"stage 1 frozen file changed: {rel}")
    record = STUDY / "FREEZE-STAGE2-STROTHER.json"
    if not record.exists():
        sys.exit("FREEZE-STAGE2-STROTHER.json does not exist: the supplement table is not frozen.")
    frozen = json.loads(record.read_text())
    for rel, digest in frozen["files_sha256"].items():
        if not _release_paths.matches(STUDY / rel, digest):
            sys.exit(f"stage-2 Strother frozen file changed: {rel}")
    if str(table.resolve().relative_to(STUDY)) not in frozen["files_sha256"]:
        sys.exit("the table to score is not in FREEZE-STAGE2-STROTHER.json")


def prepare() -> None:
    target = ROOT / SETTINGS
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STUDY / SETTINGS, target)
    stage1 = json.loads((STUDY / "FREEZE.json").read_text())
    if sha256(target) != stage1["files_sha256"][SETTINGS]:
        sys.exit("copied settings differ from the frozen settings")


def score(table: Path) -> None:
    check_freezes(table)
    prepare()
    sys.path.insert(0, str(CODE))
    import common as C
    import score as S
    C.RESULTS = ROOT / "results"
    S.main("confirmation", str(table))


def report(table: Path) -> None:
    """STAGE2-PROTOCOL.md, Part 2: stage 1's primary comparisons plus the supplement's, descriptively."""
    check_freezes(table)
    sys.path.insert(0, str(CODE))
    import common as C
    out = ROOT / "results/confirmation"
    summary = json.loads((out / "summary.json").read_text())
    if summary["table_sha256"] != sha256(table):
        sys.exit("the scores were not made from this table")

    def primary(path):
        with path.open(newline="") as f:
            return [r for r in csv.DictReader(f) if r["role"] == "primary" and r["matched"] == "True"
                    and r["speed_unmatched"] == "False" and r["model"]]
    old, new = primary(STUDY / "results/confirmation/comparisons.csv"), primary(out / "comparisons.csv")
    codes = {r["row_id"]: r["experiment"] for r in C.read_table(table)}
    r1 = [{"row_id": r["row_id"], "cell": r["cell"], "polarity": r["polarity"], "fly": r["experiment"],
           "model": r["model"], "share": float(r["share"]), "median": float(r["median"]), "agree": r["experiment"] == r["model"]}
          for r in new if codes[r["row_id"]] == "ST-S2B" and r["readout"] == "T4_calcium" and r["polarity"] == "ON"]
    combined = C.agreement_block([r["experiment"] for r in old + new], [r["model"] for r in old + new], C.CATEGORIES,
                                 C.CONFIG["permutations"], C.CONFIG["seed"])
    result = {"table": str(table.relative_to(STUDY)), "table_sha256": sha256(table),
              "supplement_primary": summary["primary"]["all"], "supplement_behaviour": summary["secondary"]["h_behaviour"],
              "stage1_primary_n": len(old), "supplement_primary_n": len(new),
              "stage1_plus_supplement_primary": combined, "r1_rows": r1}
    (out / "report.json").write_text(json.dumps(result, indent=1, default=float) + "\n")
    print(json.dumps({"stage1_plus_supplement_primary": combined}, default=float))


def recheck(table: Path) -> int:
    sys.path.insert(0, str(CODE))
    import recheck as R
    R.STUDY = ROOT
    return R.main("confirmation", str(table))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("score", "recheck", "report"):
        sys.exit(__doc__)
    table = Path(sys.argv[2]).resolve()
    if sys.argv[1] == "score":
        score(table)
    elif sys.argv[1] == "report":
        report(table)
    else:
        sys.exit(recheck(table))
