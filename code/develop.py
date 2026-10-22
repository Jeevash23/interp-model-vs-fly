"""Development checks and settings (PROTOCOL.md Section 6), on the four development models only.

Writes results/development/dev-checks.json and results/development/settings.json (delta, pooling, speed rule).
No setting is chosen by its agreement with the stand-in table: the rules below look only at boundary crowding,
at the difference between two pooling rules, and at how well the two model speeds stand in for 12.5 and 300 deg/s.
"""
from __future__ import annotations

import datetime as dt
import json
import math

import numpy as np

import common as C

READOUTS = ["T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d"]
CELL_INDEX = {"Mi1": 20, "Tm3": 45}                       # AI-06's cell numbering (network-structure.json)
STAGE1 = C.AI06 / "04-Results/stage1"


def crowding(values: list[float], delta: float, band: float) -> float:
    near = [v for v in values if abs(v - (1 - delta)) <= band or abs(v - (1 + delta)) <= band]
    return len(near) / len(values)


def stage1_folder(model: str, key: str):
    for split in ("development", "final"):
        folder = STAGE1 / split / model / key
        if (folder / "baseline.npz").exists():
            return folder
    return None


def peaks(path) -> np.ndarray:
    with np.load(path, allow_pickle=False) as archive:
        return archive["peaks"].astype(np.float64)


def stage1_ratio(model: str, key: str, cell: str, letters: str, pooling: str) -> float | None:
    """Preferred-polarity (ON) summed-peak ratio of T4 subtypes from AI-06's stage-1 records."""
    folder = stage1_folder(model, key)
    if folder is None or not (folder / f"s100-cell{CELL_INDEX[cell]:02d}.npz").exists():
        return None
    stim = C.stimulus_arrays(key)
    on = stim["intensity"] == 1
    base, after = peaks(folder / "baseline.npz"), peaks(folder / f"s100-cell{CELL_INDEX[cell]:02d}.npz")
    ratios, weights = [], []
    for letter in letters:
        r = READOUTS.index("T4" + letter)
        b = base[on, r].sum()
        if b > 1e-8:
            ratios.append(after[on, r].sum() / b)
            weights.append(b)
    if not ratios:
        return None
    if pooling == "weighted":
        return float(sum(w * x for w, x in zip(weights, ratios)) / sum(weights))
    return float(np.mean(ratios))


def preferred_angle(model: str, stimulus: str) -> dict:
    folder = C.AI06 / "study/results/runs" / model / stimulus
    base = peaks(folder / "baseline.npz")
    stim = C.stimulus_arrays(stimulus)
    out = {}
    for r, name in enumerate(READOUTS):
        select = stim["intensity"] == (1 if name.startswith("T4") else 0)
        response = base[select, r]
        angles = np.deg2rad(stim["angle"][select].astype(float))
        vector = (response * np.exp(1j * angles)).sum()
        out[name] = None if response.sum() <= 1e-8 else round(float(np.rad2deg(np.angle(vector)) % 360), 1)
    return out


def angle_gap(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def main() -> None:
    effects = C.load_effects("development")
    models = C.models_in("development")
    assert models == sorted(C.CONFIG["development_models"]), models
    table = C.read_table(C.CODE / "standin_table.csv")
    comps = [c for c in C.comparisons(table) if c["matched"] and c["measure"] == "amplitude"]
    full = C.CONFIG["primary_strength"]
    band = C.CONFIG["boundary_band"]
    checks = {"models": models, "standin_rows": [c["row_id"] for c in comps]}

    # Delta: boundary crowding of the (row, model) values under mean pooling.
    values = {(c["row_id"], m): C.amplitude_value(effects, m, c, full, "mean") for c in comps for m in models}
    finite = [v for v in values.values() if v is not None]
    default = C.CONFIG["delta"]
    shares = {str(d): crowding(finite, d, band) for d in [default] + C.CONFIG["delta_candidates"]}
    delta = default
    if shares[str(default)] > C.CONFIG["boundary_crowding_limit"]:
        delta = min(C.CONFIG["delta_candidates"], key=lambda d: (shares[str(d)], abs(d - default)))
    checks["delta"] = {"values": {f"{k[0]}|{k[1]}": v for k, v in values.items()}, "n_values": len(finite),
                       "share_within_band": shares, "band": band, "limit": C.CONFIG["boundary_crowding_limit"],
                       "chosen": delta}

    # Pooling: mean of ratios against the baseline-weighted ratio, categories at the chosen delta.
    weighted = {(c["row_id"], m): C.amplitude_value(effects, m, c, full, "weighted") for c in comps for m in models}
    differ = [k for k in values if values[k] is not None and weighted[k] is not None
              and C.category(values[k], delta) != C.category(weighted[k], delta)]
    n_pairs = sum(values[k] is not None and weighted[k] is not None for k in values)
    pooling = "weighted" if len(differ) / n_pairs > C.CONFIG["pooling_switch_limit"] else "mean"
    weighted_finite = [v for v in weighted.values() if v is not None]
    checks["pooling"] = {"weighted_values": {f"{k[0]}|{k[1]}": v for k, v in weighted.items()},
                         "pairs": n_pairs, "categories_differ": [f"{k[0]}|{k[1]}" for k in differ],
                         "share_differ": len(differ) / n_pairs, "limit": C.CONFIG["pooling_switch_limit"],
                         "chosen": pooling,
                         # The delta rule was applied to mean-pooled values; repeated here on the weighted values.
                         "delta_share_within_band_weighted": {str(d): crowding(weighted_finite, d, band)
                                                              for d in [default] + C.CONFIG["delta_candidates"]}}
    if pooling == "weighted" and checks["pooling"]["delta_share_within_band_weighted"][str(default)] > C.CONFIG["boundary_crowding_limit"]:
        raise SystemExit("delta rule gives a different answer under weighted pooling: decide by amendment")

    # Speed proxy: 27.55 and 110.2 deg/s against 12.5 and 300 deg/s (AI-06 stage-1 records), Mi1 and Tm3, ON edges.
    # First, confirm that the stage-1 peaks give AI-06's revision ratio where the same stimulus exists.
    validation = []
    for m in models:
        for key in (C.FAST, C.SLOW):
            for cell in CELL_INDEX:
                for letter in "abcd":
                    s1 = stage1_ratio(m, key, cell, letter, "mean")
                    rev = effects.get((m, key, full, "T4" + letter, cell), {}).get("ratio")
                    if s1 is not None and rev is not None:
                        validation.append(abs(s1 - rev))
    pairs_proxy = []
    standin_letters = "ad"                                  # pooled HS/VS, preferred direction, ON edges (K01, K02)
    for m in models:
        for cell in CELL_INDEX:
            for proxy, true in ((C.SLOW, "bio_slow"), (C.FAST, "bio_fast")):
                comp = {"cell": cell, "sets": {"ON": standin_letters}, "stimuli": [proxy]}
                v_proxy = C.amplitude_value(effects, m, comp, full, pooling)
                v_true = stage1_ratio(m, true, cell, standin_letters, pooling)
                per_subtype = {letter: (C.amplitude_value(effects, m, {"cell": cell, "sets": {"ON": letter}, "stimuli": [proxy]}, full, "mean"),
                                        stage1_ratio(m, true, cell, letter, "mean")) for letter in "abcd"}
                pairs_proxy.append({"model": m, "cell": cell, "proxy": proxy, "true": true, "proxy_value": v_proxy,
                                    "true_value": v_true,
                                    "same_category": None if v_proxy is None or v_true is None else
                                    C.category(v_proxy, delta) == C.category(v_true, delta),
                                    "per_subtype": per_subtype})
    scored = [p for p in pairs_proxy if p["same_category"] is not None]
    differ_share = sum(not p["same_category"] for p in scored) / len(scored)
    subtype_pairs = [(a, b) for p in pairs_proxy for a, b in p["per_subtype"].values() if a is not None and b is not None]
    subtype_same = sum(C.category(a, delta) == C.category(b, delta) for a, b in subtype_pairs)
    speed_rule = "unmatched-secondary" if differ_share > C.CONFIG["speed_proxy_limit"] else "log-nearest"
    checks["speed"] = {"stage1_vs_revision_max_abs_ratio_difference": max(validation) if validation else None,
                       "stage1_vs_revision_checked": len(validation),
                       "comparisons": pairs_proxy, "share_differ": differ_share, "limit": C.CONFIG["speed_proxy_limit"],
                       "per_subtype_same": subtype_same, "per_subtype_total": len(subtype_pairs), "chosen": speed_rule}

    # Mapping by name: preferred directions of the eight readouts in the intact development models.
    tuning = {m: {s: preferred_angle(m, s) for s in (C.SLOW, C.FAST)} for m in models}
    opposite = {"ab": [], "cd": []}
    for m in models:
        for s in (C.SLOW, C.FAST):
            for cell in ("T4", "T5"):
                t = tuning[m][s]
                for pair in ("ab", "cd"):
                    x, y = t[cell + pair[0]], t[cell + pair[1]]
                    if x is not None and y is not None:
                        opposite[pair].append(angle_gap(x, y))
    checks["tuning"] = {"preferred_angle_deg": tuning,
                        "pair_angle_gap_deg": {k: {"median": float(np.median(v)), "min": min(v), "max": max(v), "n": len(v)}
                                               for k, v in opposite.items()}}

    settings = {"delta": delta, "pooling": pooling, "speed_rule": speed_rule,
                "decided_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "rules": "PROTOCOL.md Section 6; none chosen by agreement with the stand-in table",
                "evidence": {"delta_share_within_band": shares[str(default)], "pooling_share_differ": len(differ) / n_pairs,
                             "speed_share_differ": differ_share}}
    out = C.RESULTS / "development"
    out.mkdir(parents=True, exist_ok=True)
    (out / "dev-checks.json").write_text(json.dumps(checks, indent=1, default=float) + "\n")
    (out / "settings.json").write_text(json.dumps(settings, indent=1) + "\n")
    print(json.dumps(settings, indent=1))
    print("pair angle gaps:", json.dumps(checks["tuning"]["pair_angle_gap_deg"]))
    print("stage-1 vs revision max |ratio diff|:", checks["speed"]["stage1_vs_revision_max_abs_ratio_difference"],
          "over", len(validation))


if __name__ == "__main__":
    main()
