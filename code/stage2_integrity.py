"""Integrity of the stage-2 confirmation pair records, before the stage-2 freeze.

  python -B stage2_integrity.py      writes results/stage2/integrity-confirmation.json

Checks only completeness, hashes, the code signature, metadata, the run and hardware records, the write audit and
that every stored array is finite. It computes no ratio, category or other comparison of the models with each other or
with the flies.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

STUDY = Path(__file__).resolve().parents[1]
S2 = STUDY / "results/stage2"
PAIRS = ["Tm1+Tm2", "Tm1+Tm4", "Tm1+Tm9", "Tm2+Tm4", "Tm2+Tm9", "Tm4+Tm9"]
STIMULI = ["final_slow", "dev_fast"]
STRENGTHS = [0.5, 1.0]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    run = json.loads((S2 / "confirmation-run.json").read_text())
    replay = json.loads((S2 / "replay-check.json").read_text())
    development = json.loads((S2 / "development-run.json").read_text())
    audit = json.loads((S2 / "logs/audit-confirmation.json").read_text())
    ended = json.loads((S2 / "logs/confirmation-ended.json").read_text())
    models = sorted(run["models"])
    problems = []
    if len(models) != 46 or "finished_utc" not in run:
        problems.append(f"run record: {len(models)} models, finished {'finished_utc' in run}")
    signatures = {run["simulation_signature"], replay["simulation_signature"], development["simulation_signature"]}
    if len(signatures) != 1:
        problems.append("the replay, development and confirmation runs used different code")
    expected, found, nonfinite = 0, 0, []
    arrays_checked = 0
    for model in models:
        for stimulus in STIMULI:
            for strength in STRENGTHS:
                for pair in PAIRS:
                    expected += 1
                    path = S2 / "confirmation" / model / stimulus / f"s{round(100 * strength):03d}-{pair}.npz"
                    meta_path = path.with_suffix(".json")
                    if not path.exists() or not meta_path.exists():
                        problems.append(f"missing: {path.relative_to(STUDY)}")
                        continue
                    found += 1
                    meta = json.loads(meta_path.read_text())
                    if meta["sha256"] != sha256(path):
                        problems.append(f"hash mismatch: {path.relative_to(STUDY)}")
                    if meta["simulation_signature"] != run["simulation_signature"]:
                        problems.append(f"signature differs: {path.relative_to(STUDY)}")
                    if (meta["model"], meta["stimulus"], float(meta["strength"]), "+".join(meta["names"])) != (model, stimulus, strength, pair):
                        problems.append(f"metadata does not match path: {path.relative_to(STUDY)}")
                    with np.load(path, allow_pickle=False) as rec:
                        for key in rec.files:
                            arrays_checked += 1
                            if not np.all(np.isfinite(rec[key])):
                                nonfinite.append(f"{path.relative_to(STUDY)}:{key}")
                        if rec["trace"].shape[0] != 24 or rec["peaks"].shape != (24, 8):
                            problems.append(f"shape: {path.relative_to(STUDY)}")
    extra = sorted(str(p.relative_to(STUDY)) for p in (S2 / "confirmation").glob("*/*/*.npz")
                   if p.parent.parent.name not in models or p.stem.split("-", 1)[1] not in PAIRS)
    if extra:
        problems.append(f"unexpected records: {extra[:5]}")
    if nonfinite:
        problems.append(f"non-finite values in {len(nonfinite)} arrays")
    if audit.get("files_changed_under_AI06") != 0:
        problems.append("the write audit found changes under AI-06")
    gaps = [g for r in run["models"].values() for g in r["baseline_gap"].values()]
    if max(gaps) > 1e-4:
        problems.append(f"baseline gap above tolerance: {max(gaps)}")
    seconds = [r["seconds"] for r in run["models"].values()]
    report = {"checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": len(models),
              "records_expected": expected, "records_found": found, "arrays_checked": arrays_checked,
              "nonfinite": nonfinite, "simulation_signature": run["simulation_signature"],
              "same_code_as_replay_and_development": len(signatures) == 1,
              "run_started_utc": run["started_utc"], "run_finished_utc": run.get("finished_utc"),
              "watcher_ended_utc": ended.get("ended_utc"), "environment": run["environment"],
              "seconds_per_model": {"median": float(np.median(seconds)), "min": min(seconds), "max": max(seconds),
                                    "total": sum(seconds)},
              "worst_baseline_gap": max(gaps), "replay_pass": replay["pass"], "replay_worst_gap": replay["worst_normalised_gap"],
              "write_audit_files_changed_under_AI06": audit.get("files_changed_under_AI06"),
              "problems": problems, "pass": not problems}
    (S2 / "integrity-confirmation.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: report[k] for k in ("models", "records_expected", "records_found", "arrays_checked",
                                             "same_code_as_replay_and_development", "worst_baseline_gap",
                                             "write_audit_files_changed_under_AI06", "pass")}))
    print("environment:", report["environment"])
    print("seconds per model:", report["seconds_per_model"], "| run", report["run_started_utc"], "->", report["run_finished_utc"])
    for p in problems:
        print("PROBLEM", p)


if __name__ == "__main__":
    main()
