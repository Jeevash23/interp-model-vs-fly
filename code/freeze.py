"""Hash records for AI-11.

  predictions  write PREDICTIONS-RECORD.json (protocol, approval, predictions; before development)
  freeze       write FREEZE.json (table, extractions, code, configuration, notes, AI-06 inputs; before confirmation)
  check        verify that every file in FREEZE.json still matches its hash
Each record refuses to be overwritten.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
AI06 = (STUDY / "reference/flyvis-first-order").resolve()  # release: the reference study's files
sys.path.insert(0, str(STUDY / "tools"))
import release_paths as _release_paths  # noqa: E402  (release: documented changes pass the checks)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, record: dict) -> None:
    if path.exists():
        sys.exit(f"{path.name} already exists; records are written once.")
    path.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {path.name}: sha256 {sha256(path)}")


def predictions() -> None:
    files = ["PROTOCOL.md", "PREDICTIONS.md", "AUTHOR-APPROVAL.txt", "PROTOCOL-DRAFT.md",
             "extraction/EXTRACTION-RULES.md", "config.json"]
    record = {
        "written_at_utc": utc_now(),
        "files_sha256": {name: sha256(STUDY / name) for name in files},
        "sources_sha256": {path.name: sha256(path) for path in sorted((STUDY / "sources").glob("*.pdf"))},
        "ai06_inputs_sha256": {rel: sha256(AI06 / rel) for rel in (
            "study/results/analysis/development/effects.csv",
            "study/results/analysis/confirmation/effects.csv",
            "03-Data/biology-key.csv",
            "05-Notes/BIOLOGY-ANSWER-KEY.md")},
        "predictions_text": (STUDY / "PREDICTIONS.md").read_text(),
        "note": ("Recorded after the author approved the protocol (18 October 2026) and before any AI-11 quantity "
                 "was computed on any model, development or confirmation."),
    }
    write_once(STUDY / "PREDICTIONS-RECORD.json", record)


FROZEN = [
    "PROTOCOL.md", "PREDICTIONS.md", "AUTHOR-APPROVAL.txt", "PREDICTIONS-RECORD.json", "config.json",
    "DEVELOPMENT-NOTES.md", "extraction/EXTRACTION-RULES.md", "extraction/merged-table.csv",
    "extraction/MERGE-DECISIONS.md", "Makefile",
]
OPTIONAL = ["PREDICTIONS-ADDENDUM.md", "PREDICTIONS-ADDENDUM-RECORD.json", "AMENDMENTS.md",
            "results/development/settings.json", "results/development/dev-checks.json"]


def frozen_files() -> list[str]:
    names = list(FROZEN) + [name for name in OPTIONAL if (STUDY / name).exists()]
    names += sorted(str(p.relative_to(STUDY)) for p in (STUDY / "code").glob("*.py"))
    names += sorted(str(p.relative_to(STUDY)) for p in (STUDY / "code").glob("*.csv"))
    names += sorted(str(p.relative_to(STUDY)) for p in (STUDY / "extraction").glob("[AB]/*") if p.is_file())
    names += sorted(str(p.relative_to(STUDY)) for p in (STUDY / "extraction").glob("merge-work/*") if p.is_file())
    return names


def freeze(name: str = "FREEZE.json") -> None:
    missing = [n for n in FROZEN if not (STUDY / n).exists()]
    if missing:
        sys.exit(f"cannot freeze, missing: {missing}")
    config = json.loads((STUDY / "config.json").read_text())
    ai06 = [config["effects"]["development"], config["effects"]["confirmation"], config["connectome"]]
    record = {
        "written_at_utc": utc_now(),
        "files_sha256": {n: sha256(STUDY / n) for n in frozen_files()},
        "ai06_inputs_sha256": {rel: sha256(AI06 / rel) for rel in ai06},
        "sources_sha256": {path.name: sha256(path) for path in sorted((STUDY / "sources").glob("*.pdf"))},
        "note": "Recorded before any per-type summary of the 46 confirmation models was computed.",
    }
    write_once(STUDY / name, record)


def check(name: str = "FREEZE.json") -> dict:
    path = STUDY / name
    if not path.exists():
        sys.exit(f"{name} does not exist: the confirmation set is locked until the freeze.")
    record = json.loads(path.read_text())
    bad = [n for n, h in record["files_sha256"].items() if not _release_paths.matches(STUDY / n, h)]
    bad += [n for n, h in record["ai06_inputs_sha256"].items() if not _release_paths.matches(AI06 / n, h)]
    if bad:
        sys.exit(f"frozen files changed: {bad}")
    return record


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "predictions":
        predictions()
    elif command == "freeze":
        freeze()
    elif command == "check":
        check()
        print("all frozen files match")
    else:
        sys.exit(__doc__)
