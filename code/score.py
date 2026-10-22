"""Score an experimental table against AI-06's saved silencing results (PROTOCOL.md Section 7).

  python -B score.py development    the 2 October key as stand-in table, the four development models
  python -B score.py confirmation   the frozen merged table, the 46 confirmation models (refused without FREEZE.json)

Writes results/<split>/comparisons.csv (one line per comparison), per-model.csv and summary.json.
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

import common as C

KEY_B03 = {"Tm1": 53.98, "Tm2": 39.22, "Tm4": 70.59, "Tm9": 25.69}   # fallback for score (a), 2 October key


def settings_for(split: str) -> dict:
    path = C.RESULTS / "development" / "settings.json"
    if split == "confirmation":
        return json.loads(path.read_text())          # frozen with FREEZE.json
    if path.exists():
        return json.loads(path.read_text())
    return {"delta": C.CONFIG["delta"], "pooling": C.CONFIG["pooling"], "speed_rule": "log-nearest"}


def table_for(split: str, table_path: str | None) -> tuple[Path, list[dict]]:
    if table_path:
        path = Path(table_path)
    elif split == "development":
        path = C.CODE / "standin_table.csv"
    else:
        path = C.STUDY / "extraction" / "merged-table.csv"
    return path, C.read_table(path)


def apply_speed_rule(comps: list[dict], table: list[dict], settings: dict) -> None:
    """Speed-unmatched rule (Section 6): used only if development switched to it."""
    if settings.get("speed_rule", "log-nearest") != "unmatched-secondary":
        return
    rows = {row["row_id"]: row for row in table}
    for comp in comps:
        text = rows[comp["row_id"]].get("speeds", "").lower()
        if text in ("", "all", "mean", "not_reported"):
            continue
        values = [float(v) for v in text.replace(",", ";").split(";")]
        if any(v < C.SPEEDS[C.SLOW] or v > C.SPEEDS[C.FAST] for v in values):
            comp["speed_unmatched"] = True


def per_model_values(effects, models, comp, strength, settings, estimator="exact"):
    if not comp["matched"]:
        return {m: None for m in models}
    if comp["measure"] == "amplitude":
        return {m: C.amplitude_value(effects, m, comp, strength, settings["pooling"]) for m in models}
    return {m: C.ds_value(effects, m, comp, strength, estimator) for m in models}


def number(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def serbe_order(primary, table, effects, models, settings, strength) -> dict:
    """Score (a): rows flagged score_a=1 give the model mapping and the printed remaining OFF response per type.
    If the flagged rows carry no printed value for every type, the 2 October key's B03 values are used."""
    rows = {r["row_id"]: r for r in table}
    flagged = [c for c in primary if c["measure"] == "amplitude" and rows[c["row_id"]].get("score_a", "") == "1"]
    types = sorted(KEY_B03)
    comp_for, printed = {}, {}
    for c in flagged:
        comp_for.setdefault(c["cell"], c)
        value = number(rows[c["row_id"]].get("numeric_value"))
        if value is not None:
            printed.setdefault(c["cell"], []).append(value)
    if set(comp_for) != set(types):
        return {"testable": False, "reason": "flagged single-block rows do not cover Tm1, Tm2, Tm4 and Tm9",
                "flagged": sorted(comp_for)}
    if set(printed) == set(types):
        source, remaining = "merged table", [statistics.mean(printed[t]) for t in types]
    else:
        source, remaining = "2 October key (B03)", [KEY_B03[t] for t in types]
    values = {t: per_model_values(effects, models, comp_for[t], strength, settings) for t in types}
    medians = [statistics.median([v for v in values[t].values() if v is not None]) for t in types]
    rhos = []
    for m in models:
        xs = [values[t][m] for t in types]
        if all(x is not None for x in xs):
            rhos.append(C.spearman_exact(remaining, xs)["rho"])
    return {"testable": True, "source_of_values": source, "types": types, "rows": [comp_for[t]["row_id"] for t in types],
            "remaining_response": remaining, "model_median": medians, **C.spearman_exact(remaining, medians),
            "models_rho_positive": sum(r > 0 for r in rhos), "models_rho_one": sum(r > 1 - 1e-12 for r in rhos),
            "models_scored": len(rhos)}


def block(comps, field, labels=C.CATEGORIES, n_perm=0, seed=0, mapping=None):
    pairs = [(c["experiment"], c[field]) for c in comps if c.get(field) is not None]
    if mapping:
        pairs = [(mapping[e], mapping[m]) for e, m in pairs]
    return C.agreement_block([e for e, _ in pairs], [m for _, m in pairs], labels, n_perm, seed)


def main(split: str, table_path: str | None = None) -> dict:
    if split not in ("development", "confirmation"):
        sys.exit(__doc__)
    if split == "confirmation":
        import freeze
        freeze.check()                                    # every frozen file must still match
    settings = settings_for(split)
    delta, n_perm, seed = settings["delta"], C.CONFIG["permutations"], C.CONFIG["seed"]
    path, table = table_for(split, table_path)
    effects = C.load_effects(split)
    models = C.models_in(split)
    out_dir = C.RESULTS / split
    if split == "confirmation" and (out_dir / "summary.json").exists():
        sys.exit("confirmation results already exist; they are written once.")
    out_dir.mkdir(parents=True, exist_ok=True)

    roles = ("primary", "behaviour", "partial")
    comps = C.comparisons(table, roles)
    apply_speed_rule(comps, table, settings)
    full, half = C.CONFIG["primary_strength"], C.CONFIG["partial_strength"]
    per_model_rows = []
    for comp in comps:
        strength = half if comp["strength_class"] == "partial" else full     # one-copy blocks (Amendment 1.4)
        values = per_model_values(effects, models, comp, strength, settings)
        half_values = per_model_values(effects, models, comp, half, settings)
        ens = C.ensemble(list(values.values()), delta)
        comp.update({"strength": strength, "model": ens["category"], "share": ens["share"], "n_models": ens["n_models"],
                     "median": ens["median"], "counts": ens["counts"],
                     "model_half": C.ensemble(list(half_values.values()), delta)["category"],
                     "connectivity": C.connectivity_category(comp)})
        for d in C.CONFIG["delta_sensitivity"]:
            comp[f"model_delta_{d}"] = C.ensemble(list(values.values()), d)["category"]
        if comp["measure"] == "ds" and comp["matched"]:
            fo = per_model_values(effects, models, comp, strength, settings, estimator="prediction")
            comp["first_order"] = C.ensemble(list(fo.values()), delta)["category"]
        else:
            comp["first_order"] = None
        comp["per_model"] = {m: (C.category(v, delta) if v is not None else None) for m, v in values.items()}
        for m in models:
            per_model_rows.append({"row_id": comp["row_id"], "measure": comp["measure"], "model": m,
                                   "value": values[m], "category": comp["per_model"][m],
                                   "value_half": half_values[m]})

    primary = [c for c in comps if c["role"] == "primary" and c["matched"] and not c.get("speed_unmatched")
               and c["model"] is not None]
    shown = str(path.resolve().relative_to(C.STUDY)) if path.resolve().is_relative_to(C.STUDY) else str(path)
    summary = {"split": split, "table": shown, "table_sha256": C.sha256(path),
               "settings": settings, "models": models, "n_models": len(models)}
    summary["counts"] = {
        "rows": len(table),
        "rows_by_role": {r: sum(row.get("role", "primary") == r for row in table)
                         for r in sorted({row.get("role", "primary") for row in table})},
        "comparisons": len(comps),
        "primary_matched": len(primary),
        "primary_unmatched": [c["row_id"] + ":" + c["measure"] for c in comps
                              if c["role"] == "primary" and not c["matched"]],
        "speed_unmatched": [c["row_id"] + ":" + c["measure"] for c in comps if c.get("speed_unmatched")],
        "no_model_value": [c["row_id"] + ":" + c["measure"] for c in comps if c["matched"] and c["model"] is None],
    }
    # Primary (Section 7).
    summary["primary"] = {
        "all": block(primary, "model", n_perm=n_perm, seed=seed),
        "by_source": {s: block([c for c in primary if c["source"] == s], "model", n_perm=n_perm, seed=seed)
                      for s in sorted({c["source"] for c in primary})},
        "by_measure": {m: block([c for c in primary if c["measure"] == m], "model", n_perm=n_perm, seed=seed)
                       for m in ("amplitude", "ds")},
    }
    secondary = {"a_serbe_order": serbe_order(primary, table, effects, models, settings, full)}
    # (b) Speed dependence within Tm3 (and Mi1, descriptive).
    secondary["b_speed"] = {}
    for cell in ("Tm3", "Mi1"):
        rows_b = [c for c in primary if c["cell"] == cell and c["measure"] == "amplitude" and "ON" in c["sets"]
                  and "Ammer" in c["source"]]
        # Ammer's speed result is the preferred-direction velocity tuning: those rows' mapping comes first and is the
        # one scored (Amendment 1.6); the other mappings are descriptive.
        rows_b = sorted(rows_b, key=lambda c: c["direction"] != "PD")
        if not rows_b:
            secondary["b_speed"][cell] = {"testable": False}
            continue
        mappings = {}
        for c in rows_b:
            mappings.setdefault(json.dumps(c["sets"], sort_keys=True), c)
        results = []
        for key, c in mappings.items():
            fast = {m: C.amplitude_value(effects, m, {**c, "stimuli": [C.FAST]}, full, settings["pooling"]) for m in models}
            slow = {m: C.amplitude_value(effects, m, {**c, "stimuli": [C.SLOW]}, full, settings["pooling"]) for m in models}
            pairs = [(fast[m], slow[m]) for m in models if fast[m] is not None and slow[m] is not None]
            lower = sum(f < s for f, s in pairs)
            ties = sum(f == s for f, s in pairs)
            results.append({"sets": c["sets"], "rows": [r["row_id"] for r in rows_b if r["sets"] == c["sets"]],
                            "models": len(pairs), "fast_lower": lower, "ties": ties,
                            "sign_test_p": C.sign_test(lower, len(pairs) - ties),
                            "median_fast": statistics.median([f for f, _ in pairs]) if pairs else None,
                            "median_slow": statistics.median([s for _, s in pairs]) if pairs else None})
        secondary["b_speed"][cell] = {"testable": True, "mappings": results}
    # (c) First-order against exact on direction-selectivity comparisons.
    ds = [c for c in primary if c["measure"] == "ds" and c["first_order"] is not None and c["model"] is not None]
    secondary["c_first_order"] = {
        "n": len(ds), "testable": len(ds) >= 3,
        "exact": block(ds, "model"), "first_order": block(ds, "first_order"),
        "mcnemar": C.mcnemar_exact([c["first_order"] == c["experiment"] for c in ds],
                                   [c["model"] == c["experiment"] for c in ds])}
    # (d) Connectivity baseline on amplitude comparisons; (e) three-category direction agreement.
    amp = [c for c in primary if c["measure"] == "amplitude" and c["connectivity"] is not None]
    secondary["d_connectivity"] = {
        "n": len(amp), "connectivity": block(amp, "connectivity", n_perm=n_perm, seed=seed),
        "exact_same_comparisons": block(amp, "model"),
        "mcnemar": C.mcnemar_exact([c["connectivity"] == c["experiment"] for c in amp],
                                   [c["model"] == c["experiment"] for c in amp])}
    labels3 = ["decrease", "unchanged", "increased"]
    secondary["e_direction"] = {
        "exact_all": block(primary, "model", labels3, n_perm, seed, C.DIRECTION3),
        "connectivity_amplitude": block(amp, "connectivity", labels3, 0, 0, C.DIRECTION3),
        "exact_amplitude": block(amp, "model", labels3, 0, 0, C.DIRECTION3)}
    # (f) Sensitivity to delta.
    secondary["f_delta"] = {str(d): block(primary, f"model_delta_{d}") for d in C.CONFIG["delta_sensitivity"]}
    secondary["f_delta"][str(delta)] = block(primary, "model")
    # (g) Half strength: partial-block rows, and all primary comparisons (descriptive).
    partial = [c for c in comps if c["role"] == "partial" and c["matched"]]
    secondary["g_half"] = {"partial_rows": block(partial, "model"), "all_primary": block(primary, "model_half")}
    # (h) Behaviour.
    behaviour = [c for c in comps if c["role"] == "behaviour" and c["matched"]]
    secondary["h_behaviour"] = block(behaviour, "model")
    # (i) Per model.
    rates = {}
    for m in models:
        scored = [(c["experiment"], c["per_model"][m]) for c in primary if c["per_model"][m] is not None]
        rates[m] = sum(e == x for e, x in scored) / len(scored) if scored else None
    valid = sorted(v for v in rates.values() if v is not None)
    ens_rate = summary["primary"]["all"]["rate"]
    secondary["i_per_model"] = {
        "rates": rates, "median": statistics.median(valid) if valid else None,
        "min": valid[0] if valid else None, "max": valid[-1] if valid else None,
        "quartiles": statistics.quantiles(valid, n=4) if len(valid) >= 2 else None,
        "models_at_or_above_ensemble": sum(v >= ens_rate - 1e-12 for v in valid) if ens_rate is not None else None}
    summary["secondary"] = secondary

    fields = ["row_id", "source", "role", "measure", "cell", "readout", "polarity", "direction", "speeds", "stimuli",
              "sets", "matched", "speed_unmatched", "strength", "experiment", "model", "share", "n_models", "median",
              "counts", "model_half", "first_order", "connectivity"] + [f"model_delta_{d}" for d in C.CONFIG["delta_sensitivity"]]
    with (out_dir / "comparisons.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for c in comps:
            writer.writerow({**c, "stimuli": ";".join(c["stimuli"]), "sets": json.dumps(c["sets"], sort_keys=True),
                             "counts": json.dumps(c.get("counts", {})), "speed_unmatched": c.get("speed_unmatched", False)})
    with (out_dir / "per-model.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(per_model_rows[0]) if per_model_rows else ["row_id"])
        writer.writeheader()
        writer.writerows(per_model_rows)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=float) + "\n")
    print(json.dumps({"split": split, "primary": summary["primary"]["all"]}, default=float))
    return summary


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "", sys.argv[2] if len(sys.argv) > 2 else None)
