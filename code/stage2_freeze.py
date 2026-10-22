"""Stage 2 freeze records (STAGE2-PROTOCOL.md, Section 1.4 and Part 2).

  python -B stage2_freeze.py freeze             write FREEZE-STAGE2.json (refuses to overwrite)
  python -B stage2_freeze.py freeze-strother    write FREEZE-STAGE2-STROTHER.json, the supplement table and its merge
                                                record, after FREEZE-STAGE2.json (refuses to overwrite)
  python -B stage2_freeze.py check              verify every file in FREEZE-STAGE2.json (and FREEZE-STAGE2-STROTHER.json
                                                once it exists)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDY / "tools"))
import release_paths as _release_paths  # noqa: E402  (release: documented changes pass the checks)
RECORD = STUDY / "FREEZE-STAGE2.json"
FILES = ["STAGE2-PROTOCOL.md", "STAGE2-PREDICTIONS.md", "STAGE2-RECORD.json", "STAGE2-AMENDMENTS.md",
         "FREEZE.json", "FREEZE-BASELINES.json", "code/stage2_simulate.py", "code/stage2_run.sh", "code/stage2_score.py",
         "code/stage2_freeze.py", "code/stage2_recheck.py", "code/stage2_strother.py", "code/stage2_predictions.py",
         "code/stage2_integrity.py", "code/stage2_units.py", "code/stage2_merge.py", "code/stage2_s3h_markers.py",
         "results/stage2/integrity-confirmation.json", "results/stage2/logs/confirmation-ended.json",
         "results/stage2/replay-check.json", "results/stage2/development-run.json", "results/stage2/confirmation-run.json",
         "results/stage2/logs/audit-replay.json", "results/stage2/logs/audit-development.json",
         "results/stage2/logs/audit-confirmation.json", "results/stage2/scores/development/summary.json"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest() -> dict:
    """SHA-256 of every confirmation pair record and its metadata, checked against the hash in that metadata."""
    out = {}
    for path in sorted((STUDY / "results/stage2/confirmation").glob("*/*/*.npz")):
        meta = json.loads(path.with_suffix(".json").read_text())
        digest = sha256(path)
        if meta["sha256"] != digest:
            raise SystemExit(f"record does not match its metadata: {path}")
        out[str(path.relative_to(STUDY))] = digest
        out[str(path.with_suffix(".json").relative_to(STUDY))] = sha256(path.with_suffix(".json"))
    return out


def freeze() -> None:
    if RECORD.exists():
        sys.exit("FREEZE-STAGE2.json already exists; records are written once.")
    missing = [f for f in FILES if not (STUDY / f).exists()]
    if missing:
        sys.exit(f"cannot freeze, missing: {missing}")
    run = json.loads((STUDY / "results/stage2/confirmation-run.json").read_text())
    if "finished_utc" not in run or len(run["models"]) != 46:
        sys.exit("the confirmation run is not complete")
    records = manifest()
    if len(records) != 46 * 2 * 12 * 2:
        sys.exit(f"expected {46 * 2 * 12 * 2} record files, found {len(records)}")
    record = {"written_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "files_sha256": {f: sha256(STUDY / f) for f in FILES}, "records_sha256": records,
              "note": "Recorded before any per-type summary of the 46 confirmation models' pair silencing was computed."}
    RECORD.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote FREEZE-STAGE2.json: {len(FILES)} files, {len(records)} record files; sha256 {sha256(RECORD)}")


STROTHER_RECORD = STUDY / "FREEZE-STAGE2-STROTHER.json"
STROTHER_FILES = ["FREEZE-STAGE2.json", "STAGE2-AMENDMENTS.md", "sources/strother-2017-supplement.pdf",
                  "results/development/settings.json",
                  "extraction/A/table-stage2.csv", "extraction/A/notes-stage2.md", "extraction/A/SHA256SUMS-stage2",
                  "extraction/B/table-stage2.csv", "extraction/B/notes-stage2.md", "extraction/B/SHA256SUMS-stage2",
                  "extraction/stage2/supplement-table.csv", "extraction/stage2/settlements.json",
                  "extraction/stage2/repeats.csv", "extraction/stage2/MERGE-DECISIONS.md",
                  "code/stage2_units.py", "code/stage2_merge.py", "code/stage2_s3h_markers.py", "code/stage2_strother.py",
                  "code/stage2_predictions.py", "code/stage2_recheck.py", "code/stage2_freeze.py"]


def freeze_strother() -> None:
    if STROTHER_RECORD.exists():
        sys.exit("FREEZE-STAGE2-STROTHER.json already exists; records are written once.")
    check()
    work = sorted(str(p.relative_to(STUDY)) for p in (STUDY / "extraction/stage2/merge-work").iterdir() if p.is_file())
    files = STROTHER_FILES + work
    missing = [f for f in files if not (STUDY / f).exists()]
    if missing:
        sys.exit(f"cannot freeze, missing: {missing}")
    record = {"written_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "files_sha256": {f: sha256(STUDY / f) for f in files},
              "note": "Recorded before any supplement finding was compared with any model value."}
    STROTHER_RECORD.write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote FREEZE-STAGE2-STROTHER.json: {len(files)} files; sha256 {sha256(STROTHER_RECORD)}")


def check() -> dict:
    if not RECORD.exists():
        sys.exit("FREEZE-STAGE2.json does not exist: stage-2 confirmation scoring is locked until the freeze.")
    record = json.loads(RECORD.read_text())
    bad = [f for f, h in record["files_sha256"].items() if not _release_paths.matches(STUDY / f, h)]
    bad += [f for f, h in record["records_sha256"].items() if not _release_paths.matches(STUDY / f, h)]
    if STROTHER_RECORD.exists():
        bad += [f for f, h in json.loads(STROTHER_RECORD.read_text())["files_sha256"].items()
                if not _release_paths.matches(STUDY / f, h)]
    if bad:
        sys.exit(f"stage-2 frozen files changed: {bad[:10]}")
    return record


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "freeze":
        freeze()
    elif command == "freeze-strother":
        freeze_strother()
    elif command == "check":
        check()
        print("all stage-2 frozen files match")
    else:
        sys.exit(__doc__)
