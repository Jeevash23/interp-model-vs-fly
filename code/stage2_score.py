"""Stage 2, Part 1: score the pair findings against simulated pair silencing (STAGE2-PROTOCOL.md, Section 1.3).

  python -B stage2_score.py development    the four development models (code test)
  python -B stage2_score.py confirmation   the 46 confirmation models (refused unless FREEZE-STAGE2.json matches)

Reuses stage 1's frozen matching, categories and statistics (code/common.py, imported unchanged); only adds pair
silencing as a "cell" and reads the stage-2 raw records. Writes results/stage2/scores/<split>/summary.json,
comparisons.csv and per-model.csv.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

import common as C
sys.path.insert(0, str(C.STUDY / "tools"))
import release_paths as _release_paths  # noqa: E402  (release: documented changes pass the checks)

PAIRS = ["Tm1+Tm2", "Tm1+Tm4", "Tm1+Tm9", "Tm2+Tm4", "Tm2+Tm9", "Tm4+Tm9"]
SINGLES = ["Tm1", "Tm2", "Tm4", "Tm9"]
STAGE2 = C.RESULTS / "stage2"
READOUTS = ["T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d"]
_frozen_model_cell = C.model_cell


def pair_cell(row: dict) -> str | None:
    """Serbe's six pairs become model 'cells'; everything else follows stage 1's frozen rule."""
    name = "+".join(sorted(p.strip() for p in row["silenced_types"].replace(" ", "").split("+")))
    return name if name in PAIRS else _frozen_model_cell(row)


C.model_cell = pair_cell   # runtime binding only; common.py itself is unchanged


@lru_cache(maxsize=256)
def baseline(model: str, stimulus: str) -> dict:
    with np.load(C.AI06 / "study/results/runs" / model / stimulus / "baseline.npz", allow_pickle=False) as a:
        return {k: a[k].astype(np.float64) for k in ("peaks", "dsi", "denominator")}


def pair_effects(split: str) -> dict:
    """(model, stimulus, strength, readout, pair) -> the fields stage 1's functions use, computed as AI-06 did."""
    folder = STAGE2 / split
    cut = 1e-8
    effects = {}
    for model_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        model = model_dir.name
        for stimulus in ("final_slow", "dev_fast"):
            base = baseline(model, stimulus)
            intensity = C.stimulus_arrays(stimulus)["intensity"]
            for path in sorted((model_dir / stimulus).glob("s*-*.npz")):
                meta = json.loads(path.with_suffix(".json").read_text())
                if meta["sha256"] != C.sha256(path) and not _release_paths.matches(path, meta["sha256"]):
                    raise SystemExit(f"record changed: {path}")
                with np.load(path, allow_pickle=False) as rec:
                    peaks, dsi, den = rec["peaks"].astype(np.float64), rec["dsi"].astype(np.float64), rec["denominator"].astype(np.float64)
                pair = "+".join(meta["names"])
                for r, name in enumerate(READOUTS):
                    preferred = intensity == (1 if r < 4 else 0)
                    base_sum = float(base["peaks"][preferred, r].sum())
                    responsive = base["denominator"][r] > cut
                    defined = bool(responsive and den[r] > cut and np.isfinite(dsi[r]))
                    effects[(model, stimulus, float(meta["strength"]), name, pair)] = {
                        "ratio": float(peaks[preferred, r].sum() / base_sum) if base_sum > cut else None,
                        "baseline_dsi": float(base["dsi"][r]),
                        "exact": float(dsi[r] - base["dsi"][r]) if defined else None,
                        "prediction": 0.0, "abolished": bool(responsive and den[r] <= cut), "defined": defined}
    return effects


def ensemble_for(effects, models, comp, strength, settings, delta):
    values = {m: C.amplitude_value(effects, m, comp, strength, settings["pooling"]) for m in models}
    return values, C.ensemble(list(values.values()), delta)


def main(split: str) -> dict:
    if split not in ("development", "confirmation"):
        sys.exit(__doc__)
    if split == "confirmation":
        import stage2_freeze
        stage2_freeze.check()
    import freeze
    freeze.check()                                          # stage 1's frozen files still match
    settings = json.loads((C.RESULTS / "development/settings.json").read_text())
    delta, n_perm, seed = settings["delta"], C.CONFIG["permutations"], C.CONFIG["seed"]
    out = STAGE2 / "scores" / split
    if split == "confirmation" and (out / "summary.json").exists():
        sys.exit("stage-2 confirmation scores already exist; they are written once.")
    out.mkdir(parents=True, exist_ok=True)
    table_path = C.STUDY / "extraction/merged-table.csv"
    table = C.read_table(table_path)
    effects = pair_effects(split)
    models = sorted({k[0] for k in effects})
    singles = C.load_effects(split)                         # AI-06's single-type results, for (2b) and (2c)
    half, full = C.CONFIG["partial_strength"], C.CONFIG["primary_strength"]
    comps = [c for c in C.comparisons(table, roles=("pair",)) if c["cell"] in PAIRS]
    partial = [c for c in C.comparisons(table, roles=("partial",))]
    rows, per_model = [], []
    for c in comps + partial:
        source = effects if c["cell"] in PAIRS else singles
        vh, eh = ensemble_for(source, models, c, half, settings, delta)
        vf, ef = ensemble_for(source, models, c, full, settings, delta)
        c.update(model_half=eh["category"], share_half=eh["share"], median_half=eh["median"], counts_half=eh["counts"],
                 model_full=ef["category"], share_full=ef["share"], median_full=ef["median"],
                 per_model_half={m: (C.category(v, delta) if v is not None else None) for m, v in vh.items()},
                 lptc=c["readout"] != "behaviour", connectivity=connectivity(c))
        for m in models:
            per_model.append({"row_id": c["row_id"], "cell": c["cell"], "model": m, "value_half": vh[m], "value_full": vf[m]})
    pair_lptc = [c for c in comps if c["lptc"] and c["matched"]]
    pair_beh = [c for c in comps if not c["lptc"] and c["matched"]]
    single_partial = [c for c in partial if c["matched"]]

    def block(items, field, perm=False, labels=C.CATEGORIES, mapping=None):
        pairs = [(i["experiment"], i[field]) for i in items if i.get(field) is not None]
        if mapping:
            pairs = [(mapping[a], mapping[b]) for a, b in pairs]
        return C.agreement_block([a for a, _ in pairs], [b for _, b in pairs], labels, n_perm if perm else 0, seed)

    summary = {"split": split, "models": models, "n_models": len(models), "table_sha256": C.sha256(table_path),
               "settings": settings, "strengths": {"primary": half, "secondary": full},
               "counts": {"pair_comparisons": len(comps), "pair_lptc": len(pair_lptc), "pair_behaviour": len(pair_beh),
                          "single_partial": len(single_partial),
                          "unmatched": [c["row_id"] for c in comps if not c["matched"]]}}
    summary["primary"] = block(pair_lptc, "model_half", perm=True)
    summary["primary_by_polarity"] = {p: block([c for c in pair_lptc if c["polarity"] == p], "model_half")
                                      for p in ("ON", "OFF", "both")}
    summary["a_full"] = block(pair_lptc, "model_full", perm=True)
    summary["b_with_singles"] = block(pair_lptc + single_partial, "model_half", perm=True)
    summary["c_beyond_singles"] = beyond_singles(pair_lptc, single_partial)
    summary["d_behaviour"] = block(pair_beh, "model_half")
    summary["e_connectivity"] = {"connectivity": block(pair_lptc, "connectivity", perm=True),
                                 "exact_half_same": block(pair_lptc, "model_half"),
                                 "mcnemar": C.mcnemar_exact([c["connectivity"] == c["experiment"] for c in pair_lptc],
                                                            [c["model_half"] == c["experiment"] for c in pair_lptc])}
    rates = {}
    for m in models:
        scored = [(c["experiment"], c["per_model_half"][m]) for c in pair_lptc if c["per_model_half"][m] is not None]
        rates[m] = sum(a == b for a, b in scored) / len(scored) if scored else None
    valid = sorted(v for v in rates.values() if v is not None)
    summary["f_per_model"] = {"rates": rates, "median": statistics.median(valid) if valid else None,
                              "min": valid[0] if valid else None, "max": valid[-1] if valid else None}
    summary["g_with_stage1"] = with_stage1(pair_lptc, split, n_perm, seed)
    summary["category_counts"] = {
        "experiment": {k: sum(c["experiment"] == k for c in pair_lptc) for k in C.CATEGORIES},
        "model_half": {k: sum(c["model_half"] == k for c in pair_lptc) for k in C.CATEGORIES},
        "model_full": {k: sum(c["model_full"] == k for c in pair_lptc) for k in C.CATEGORIES}}

    fields = ["row_id", "experiment_code", "cell", "readout", "polarity", "direction", "stimuli", "sets", "matched",
              "experiment", "model_half", "share_half", "median_half", "counts_half", "model_full", "share_full",
              "median_full", "connectivity"]
    trows = {r["row_id"]: r for r in table}
    with (out / "comparisons.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for c in comps + partial:
            w.writerow({**c, "experiment_code": trows[c["row_id"]]["experiment"], "stimuli": ";".join(c["stimuli"]),
                        "sets": json.dumps(c["sets"], sort_keys=True), "counts_half": json.dumps(c.get("counts_half", {}))})
    with (out / "per-model.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_model[0]))
        w.writeheader()
        w.writerows(per_model)
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n")
    print(json.dumps({"split": split, "primary": summary["primary"]}, default=float))
    return summary


def connectivity(comp: dict) -> str | None:
    """Score (2e): the sign of the summed signed drive of both silenced types (stage 1's rule, both types)."""
    if not comp["matched"] or comp["measure"] != "amplitude":
        return None
    names, s_sum, reach = C.signed_paths()
    total, reachable = 0.0, False
    for cell in comp["cell"].split("+"):
        j = names.index(cell)
        for polarity, letters in comp["sets"].items():
            for letter in letters:
                i = names.index(C.POLARITY_CELL[polarity] + letter)
                total += s_sum[i, j]
                reachable |= bool(reach[i, j])
    if not reachable or total == 0.0:
        return "unchanged"
    return "reduced" if total > 0 else "increased"


def beyond_singles(pair_lptc: list, single_partial: list) -> dict:
    """Score (2c): for each pair's Fig. 6 OFF finding, is the models' median below both singles' medians?"""
    six = {c["cell"]: c for c in pair_lptc if c["polarity"] == "OFF" and c["direction"] == "both"}
    single = {c["cell"]: c for c in single_partial if c["polarity"] == "OFF" and c["direction"] == "both"}
    out = {}
    for strength in ("half", "full"):
        rows = []
        for pair in PAIRS:
            if pair not in six:
                continue
            a, b = pair.split("+")
            if a not in single or b not in single:
                continue
            pm = six[pair][f"median_{strength}"]
            sa, sb = single[a][f"median_{strength}"], single[b][f"median_{strength}"]
            rows.append({"pair": pair, "pair_median": pm, "single_medians": [sa, sb], "beyond": pm < min(sa, sb)})
        out[strength] = {"pairs": rows, "beyond": sum(r["beyond"] for r in rows), "n": len(rows)}
    return out


def with_stage1(pair_lptc: list, split: str, n_perm: int, seed: int) -> dict | None:
    """Score (2g): stage 1's 64 primary comparisons (saved categories) plus the 42 pair comparisons, descriptive."""
    path = C.RESULTS / split / "comparisons.csv"
    if split != "confirmation" or not path.exists():
        return None
    with path.open(newline="") as f:
        stage1 = [r for r in csv.DictReader(f) if r["role"] == "primary" and r["model"]]
    exp = [r["experiment"] for r in stage1] + [c["experiment"] for c in pair_lptc]
    mod = [r["model"] for r in stage1] + [c["model_half"] for c in pair_lptc]
    return C.agreement_block(exp, mod, C.CATEGORIES, n_perm, seed)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
