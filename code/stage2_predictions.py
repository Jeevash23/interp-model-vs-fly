"""Score the stage-2 predictions (STAGE2-PREDICTIONS.md) against results/stage2/scores/<split>/.

  python -B stage2_predictions.py development | confirmation

Written and frozen before the stage-2 confirmation scoring. A pair's category over its three dark-edge (OFF)
tangential-cell findings (Fig. 6 preferred minus null, Fig. S4 preferred and null directions) is the most common one;
if all three differ, the pair has no category. R1 and R2 (Part 2) are scored in the confirmation split once the
supplement is scored: R1 from results/stage2/strother/results/confirmation/report.json (the four Fig. S2B comparisons
with bright edges), R2 from extraction/stage2/repeats.csv (STAGE2-AMENDMENTS.md, S4 rule 8).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
PAIRS = ["Tm1+Tm2", "Tm1+Tm4", "Tm1+Tm9", "Tm2+Tm4", "Tm2+Tm9", "Tm4+Tm9"]


def verdict(flag):
    return "not testable" if flag is None else ("holds" if flag else "does not hold")


def pair_categories(comps, field):
    out = {}
    for pair in PAIRS:
        cats = [c[field] for c in comps if c["cell"] == pair and c["polarity"] == "OFF"
                and c["readout"] == "LPTC_voltage_pooled" and c["experiment_code"] in ("SE-6", "SE-S4")]
        if len(cats) != 3:
            out[pair] = None
            continue
        top = Counter(cats).most_common()
        out[pair] = top[0][0] if len(top) == 1 or top[0][1] > top[1][1] else None
    return out


def main(split):
    folder = STUDY / "results/stage2/scores" / split
    s = json.loads((folder / "summary.json").read_text())
    with (folder / "comparisons.csv").open(newline="") as f:
        comps = [r for r in csv.DictReader(f) if r["cell"] in PAIRS]
    lptc = [c for c in comps if c["readout"] != "behaviour"]
    beh = [c for c in comps if c["readout"] == "behaviour"]
    res = []

    def add(pid, quantity, flag, detail=""):
        res.append({"id": pid, "quantity": quantity, "verdict": verdict(flag), "detail": detail})

    half, full = pair_categories(lptc, "model_half"), pair_categories(lptc, "model_full")
    add("Q1", "OFF findings at half strength unchanged for at least 5 of 6 pairs",
        sum(v == "unchanged" for v in half.values()) >= 5, json.dumps(half))
    p = s["primary"]
    add("Q2", "primary agreement between 0.40 and 0.65", 0.40 <= p["rate"] <= 0.65, f"{p['rate']}")
    add("Q3", "primary kappa at most 0.10", None if p["kappa"] is None else p["kappa"] <= 0.10 + 1e-12, f"{p['kappa']}")
    add("Q4", "OFF findings at full strength reduced for at least 2 of 6 pairs",
        sum(v == "reduced" for v in full.values()) >= 2, json.dumps(full))
    add("Q5", "agreement at full strength at least that at half", s["a_full"]["rate"] >= p["rate"] - 1e-12,
        f"{s['a_full']['rate']} vs {p['rate']}")
    c = s["c_beyond_singles"]["half"]
    add("Q6", "pair below both singles (Fig. 6 OFF, half) for at least 5 of 6", None if c["n"] < 6 else c["beyond"] >= 5,
        f"{c['beyond']} of {c['n']}")
    replay = json.loads((STUDY / "results/stage2/replay-check.json").read_text())
    add("Q7", "replay within 1e-4 in every case", bool(replay["pass"]), f"worst {replay['worst_normalised_gap']:.2e}")
    gaps = []
    for name in ("development-run.json", "confirmation-run.json"):
        path = STUDY / "results/stage2" / name
        if path.exists():
            gaps.append(json.loads(path.read_text()).get("worst_baseline_gap"))
    gaps += [g for case in replay["cases"] if "baseline_gap" in case for g in case["baseline_gap"].values()]
    add("Q8", "baseline re-simulation within 1e-4 everywhere", None if None in gaps else max(gaps) <= 1e-4,
        f"worst {max(g for g in gaps if g is not None):.2e}")
    add("Q9", "behaviour pair findings unchanged in at least 5 of 7 (half)",
        sum(c["model_half"] == "unchanged" for c in beh) >= 5 if len(beh) == 7 else None,
        f"{sum(c['model_half'] == 'unchanged' for c in beh)} of {len(beh)}")
    on = [c for c in lptc if c["polarity"] == "ON"]
    add("Q10", "ON pair findings unchanged in at least 15 of 18 (half)",
        sum(c["model_half"] == "unchanged" for c in on) >= 15 if len(on) == 18 else None,
        f"{sum(c['model_half'] == 'unchanged' for c in on)} of {len(on)}")
    part2 = STUDY / "results/stage2/strother/results/confirmation/report.json"
    if split == "confirmation" and part2.exists():
        rows = {r["cell"]: r["agree"] for r in json.loads(part2.read_text())["r1_rows"]}
        expected = {"Mi1": True, "Tm3": True, "Mi4": False, "Mi9": True}
        add("R1", "supplement T4 findings at 30 deg/s: 3 of 4 agree (Mi4 not)",
            rows == expected if set(rows) == set(expected) else None,
            json.dumps({cell: ("agree" if ok else "disagree") for cell, ok in sorted(rows.items())}))
        with (STUDY / "extraction/stage2/repeats.csv").open(newline="") as f:
            reps = [r for r in csv.DictReader(f) if r["compared"] == "yes"]
        by_direction = sum(r["same"] == "yes" and r["how"] != "same category" for r in reps)
        add("R2", "supplement findings that repeat stage 1 keep stage 1's category",
            all(r["same"] == "yes" for r in reps) if reps else None,
            f"{sum(r['same'] == 'yes' for r in reps)} of {len(reps)} the same ({by_direction} by direction)")
    else:
        add("R1", "supplement T4 findings at 30 deg/s: 3 of 4 agree (Mi4 not)", None, "Part 2 not scored in this split")
        add("R2", "supplement findings that repeat stage 1 keep stage 1's category", None, "Part 2 not scored in this split")
    (folder / "predictions-scored.json").write_text(json.dumps(res, indent=1) + "\n")
    for r in res:
        print(f"{r['id']:4} {r['verdict']:14} {r['quantity']}  [{r['detail']}]")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("development", "confirmation"):
        sys.exit(__doc__)
    main(sys.argv[1])
