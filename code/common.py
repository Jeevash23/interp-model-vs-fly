"""Shared definitions for AI-11: matching experimental rows to AI-06's saved model results (PROTOCOL.md Sections 5, 7).

AI-06 is read, never written. Run with `python -B`.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from functools import lru_cache
from itertools import permutations
from pathlib import Path

import numpy as np
from scipy import stats

CODE = Path(__file__).resolve().parent
STUDY = CODE.parent
CONFIG = json.loads((STUDY / "config.json").read_text())
AI06 = (STUDY / CONFIG["ai06_root"]).resolve()
RESULTS = STUDY / "results"
CATEGORIES = CONFIG["categories"]                     # abolished, reduced, unchanged, increased
DIRECTION3 = {"abolished": "decrease", "reduced": "decrease", "unchanged": "unchanged", "increased": "increased"}
SLOW, FAST = "final_slow", "dev_fast"                 # 27.55 and 110.2 degrees per second
SPEEDS = {SLOW: CONFIG["model_speeds"][SLOW], FAST: CONFIG["model_speeds"][FAST]}
POLARITY_CELL = {"ON": "T4", "OFF": "T5"}

# Tangential cells and behaviour, by stimulus direction (Section 5.3). Letters are T4/T5 subtypes (lobula plate layers).
LPTC_MAP = {
    "HS_voltage": {"PD": "a", "ND": "b", "both": "ab"},
    "VS_voltage": {"PD": "d", "ND": "c", "both": "cd"},
    "LPTC_voltage_pooled": {"PD": "ad", "ND": "bc", "both": "abcd"},
    "behaviour": {"PD": "a", "ND": "b", "both": "ab"},
}
LPTC_DS = {"HS_voltage": "a", "VS_voltage": "d", "LPTC_voltage_pooled": "ad"}
T4T5_READOUTS = {"T4_calcium", "T4_voltage", "T5_calcium", "T5_voltage"}
EXCLUDED_TYPES = {"CT1"}                              # two compartments, silenced together only in development


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ----------------------------------------------------------------------------------------------- the experimental table
def read_table(path: Path) -> list[dict]:
    with Path(path).open(newline="") as stream:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(stream)]


def model_speed_keys(speeds: str) -> list[str]:
    """Experimental speeds -> model stimuli, nearest on a log scale (boundary 55.1 deg/s); 'all' or none -> both."""
    text = speeds.strip().lower()
    if text in ("", "all", "mean", "not_reported", "na", "n/a"):      # "mean" and "all": both model speeds
        return [SLOW, FAST]
    keys = set()
    for item in text.replace(",", ";").split(";"):
        value = float(item)
        keys.add(FAST if value >= CONFIG["speed_boundary_deg_s"] else SLOW)
    return sorted(keys, key=[SLOW, FAST].index)


def subtype_sets(row: dict, measure: str) -> dict[str, str] | None:
    """Model polarity -> subtype letters for one row and measure ('amplitude' or 'ds'); None if no counterpart."""
    readout, polarity, direction = row["readout"], row["polarity"], row["direction"]
    layers = row.get("layers", "").replace(";", "").replace(",", "").replace(" ", "")
    polarities = ["ON", "OFF"] if polarity == "both" else [polarity]
    if polarity not in ("ON", "OFF", "both") or direction not in ("PD", "ND", "both"):
        return None
    if readout in T4T5_READOUTS:
        cell_polarity = "ON" if readout.startswith("T4") else "OFF"
        if polarity not in (cell_polarity, "both"):   # the ratio covers only the readout's preferred polarity;
            return None                               # gratings (both) drive it through that polarity (Amendment 1.4)
        if measure == "amplitude" and direction == "ND":
            return None                          # no null-direction amplitude in the summed ratio (Section 5.2)
        return {cell_polarity: layers or "abcd"}
    if readout in LPTC_MAP:
        if measure == "ds":
            if readout == "behaviour" or readout not in LPTC_DS:
                return None
            return {p: LPTC_DS[readout] for p in polarities}
        return {p: LPTC_MAP[readout][direction] for p in polarities}
    return None


def model_cell(row: dict) -> str | None:
    types = row["silenced_types"].replace(" ", "")
    if not types or any(sep in types for sep in "+;,/&") or types in EXCLUDED_TYPES:
        return None
    return types


def comparisons(table: list[dict], roles=("primary",)) -> list[dict]:
    """One comparison per row and reported measure that has a model counterpart."""
    out = []
    for row in table:
        if row.get("role", "primary") not in roles:
            continue
        cell = model_cell(row)
        for measure, field in (("amplitude", "amplitude_category"), ("ds", "ds_category")):
            category = row.get(field, "not_reported")
            if category not in CATEGORIES:
                continue
            sets = subtype_sets(row, measure) if cell else None
            out.append({"row_id": row["row_id"], "source": row["source"], "cell": cell, "measure": measure,
                        "experiment": category, "sets": sets, "stimuli": model_speed_keys(row.get("speeds", "")),
                        "role": row.get("role", "primary"), "readout": row["readout"], "polarity": row["polarity"],
                        "direction": row["direction"], "speeds": row.get("speeds", ""),
                        "strength_class": row.get("strength_class", "full") or "full",
                        "matched": bool(cell and sets)})
    return out


# ------------------------------------------------------------------------------------------------- AI-06 saved results
@lru_cache(maxsize=4)
def load_effects(split: str) -> dict:
    """(model, stimulus, strength, readout, cell) -> fields used by AI-11, from AI-06's effects.csv."""
    path = AI06 / CONFIG["effects"][split]
    table = {}
    with path.open(newline="") as stream:
        for r in csv.DictReader(stream):
            key = (r["model"], r["stimulus"], float(r["strength"]), r["readout"], r["cell"])
            table[key] = {
                "ratio": float(r["preferred_amplitude_ratio"]) if r["preferred_amplitude_ratio"] not in ("", "None") else None,
                "baseline_dsi": float(r["baseline_dsi"]),
                "exact": float(r["exact"]) if r["exact"] not in ("", "None") else None,
                "prediction": float(r["prediction"]),
                "abolished": r["abolished"] == "True",
                "defined": r["defined"] == "True",
            }
    return table


def models_in(split: str) -> list[str]:
    return sorted({key[0] for key in load_effects(split)})


@lru_cache(maxsize=512)
def baseline_peak_sum(model: str, stimulus: str, readout: str) -> float:
    """Summed preferred-polarity peaks of a readout in the intact model (AI-06 run record; weighted pooling only)."""
    folder = AI06 / "study/results/runs" / model / stimulus
    with np.load(folder / "baseline.npz", allow_pickle=False) as archive:
        peaks = archive["peaks"].astype(np.float64)
    stim = stimulus_arrays(stimulus)
    index = ["T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d"].index(readout)
    preferred = stim["intensity"] == (1 if readout.startswith("T4") else 0)
    return float(peaks[preferred, index].sum())


@lru_cache(maxsize=8)
def stimulus_arrays(stimulus: str) -> dict:
    manifest = json.loads((AI06 / "03-Data/stage1/stimulus-manifest.json").read_text())
    path = AI06 / next(item["path"] for item in manifest if item["key"] == stimulus)
    with np.load(path, allow_pickle=False) as archive:
        return {"angle": archive["angle"].copy(), "intensity": archive["intensity"].copy()}


def _mean(values):
    values = [v for v in values if v is not None and math.isfinite(v)]
    return sum(values) / len(values) if values else None


def amplitude_value(effects, model, comp, strength, pooling="mean"):
    """Per-model value of an amplitude comparison: mean over speeds of the mean over polarities of the pooled ratio."""
    per_speed = []
    for stimulus in comp["stimuli"]:
        per_polarity = []
        for polarity, letters in comp["sets"].items():
            readouts = [POLARITY_CELL[polarity] + letter for letter in letters]
            entries = [(r, effects.get((model, stimulus, strength, r, comp["cell"]))) for r in readouts]
            entries = [(r, e["ratio"]) for r, e in entries if e is not None and e["ratio"] is not None]
            if not entries:
                continue
            if pooling == "weighted":
                weights = [baseline_peak_sum(model, stimulus, r) for r, _ in entries]
                per_polarity.append(sum(w * v for w, (_, v) in zip(weights, entries)) / sum(weights))
            else:
                per_polarity.append(_mean([v for _, v in entries]))
        per_speed.append(_mean(per_polarity))
    return _mean(per_speed)


def ds_value(effects, model, comp, strength, estimator="exact"):
    """Per-model DSI ratio (after/before) for a direction-selectivity comparison (Section 5.8; 5.9 for 'prediction')."""
    floor = CONFIG["min_baseline_dsi"]
    per_speed = []
    for stimulus in comp["stimuli"]:
        per_polarity = []
        for polarity, letters in comp["sets"].items():
            qs = []
            for letter in letters:
                e = effects.get((model, stimulus, strength, POLARITY_CELL[polarity] + letter, comp["cell"]))
                if e is None or e["baseline_dsi"] < floor:
                    continue
                if estimator == "exact":
                    if e["abolished"]:
                        qs.append(0.0)
                    elif e["defined"] and e["exact"] is not None:
                        qs.append((e["baseline_dsi"] + e["exact"]) / e["baseline_dsi"])
                else:
                    if e["abolished"] or (e["defined"] and e["exact"] is not None):
                        qs.append((e["baseline_dsi"] + e["prediction"]) / e["baseline_dsi"])
            per_polarity.append(_mean(qs))
        per_speed.append(_mean(per_polarity))
    return _mean(per_speed)


def category(value: float, delta: float) -> str:
    if value <= CONFIG["abolished_cut"]:
        return "abolished"
    if value < 1 - delta:
        return "reduced"
    if value <= 1 + delta:
        return "unchanged"
    return "increased"


def ensemble(values: list[float | None], delta: float) -> dict:
    """Most common per-model category; ties go to the category of the median value (Section 5.7)."""
    valid = [v for v in values if v is not None and math.isfinite(v)]
    if not valid:
        return {"category": None, "share": None, "n_models": 0, "median": None, "counts": {}}
    counts = Counter(category(v, delta) for v in valid)
    top = max(counts.values())
    tied = [c for c in CATEGORIES if counts.get(c, 0) == top]
    median = float(np.median(valid))
    chosen = tied[0] if len(tied) == 1 else category(median, delta)
    if chosen not in tied:                     # the median's category is not among the tied ones: take the tied one
        chosen = min(tied, key=lambda c: abs(CATEGORIES.index(c) - CATEGORIES.index(category(median, delta))))
    return {"category": chosen, "share": counts[chosen] / len(valid), "n_models": len(valid),
            "median": median, "counts": {c: counts.get(c, 0) for c in CATEGORIES}}


# ------------------------------------------------------------------------------------------------ connectivity baseline
@lru_cache(maxsize=1)
def signed_paths() -> tuple[list[str], np.ndarray, np.ndarray]:
    """Types, S = W + W^2 + W^3 (signed, input-normalised) and 3-step reachability, from the pinned connectome."""
    connectome = json.loads((AI06 / CONFIG["connectome"]).read_text())
    names = [node["name"] for node in connectome["nodes"]]
    counts = np.zeros((len(names), len(names)))
    signed = np.zeros_like(counts)
    for edge in connectome["edges"]:
        t, s = names.index(edge["tar"]), names.index(edge["src"])
        n = sum(count for _, count in edge["offsets"])
        counts[t, s] += n
        signed[t, s] += np.sign(edge["alpha"]) * n
    total = counts.sum(axis=1, keepdims=True)
    w = np.divide(signed, total, out=np.zeros_like(signed), where=total > 0)
    a = (counts > 0).astype(float)
    s_sum, power, reach, apower = np.zeros_like(w), np.eye(len(names)), np.zeros_like(w), np.eye(len(names))
    for _ in range(CONFIG["connectivity_hops"]):
        power = power @ w
        apower = apower @ a
        s_sum += power
        reach += apower
    return names, s_sum, reach > 0


def connectivity_category(comp: dict) -> str | None:
    if not comp["matched"] or comp["measure"] != "amplitude":
        return None
    names, s_sum, reach = signed_paths()
    if comp["cell"] not in names:
        return None
    j = names.index(comp["cell"])
    total, reachable = 0.0, False
    for polarity, letters in comp["sets"].items():
        for letter in letters:
            i = names.index(POLARITY_CELL[polarity] + letter)
            total += s_sum[i, j]
            reachable |= bool(reach[i, j])
    if not reachable or total == 0.0:
        return "unchanged"
    return "reduced" if total > 0 else "increased"


# ------------------------------------------------------------------------------------------------------- statistics
def clopper_pearson(k: int, n: int, level: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return (math.nan, math.nan)
    alpha = 1 - level
    low = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    high = 1.0 if k == n else float(stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return (low, high)


def cohen_kappa(a: list[str], b: list[str], labels: list[str]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[label] * cb[label] for label in labels) / n**2
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def kappa_permutation(experiment: list[str], model: list[str], labels: list[str], n_perm: int, seed: int) -> float | None:
    """One-sided p for kappa at least the observed, permuting the model's categories across comparisons."""
    observed = cohen_kappa(experiment, model, labels)
    if observed is None:
        return None
    rng = np.random.default_rng(seed)
    codes = {label: i for i, label in enumerate(labels)}
    e = np.array([codes[x] for x in experiment])
    m = np.array([codes[x] for x in model])
    n = len(e)
    # kappa's expected agreement is invariant to permutation, so kappa >= observed iff matches >= observed matches.
    matches_obs = int((e == m).sum())
    hits = 0
    for _ in range(n_perm):
        if int((e == m[rng.permutation(n)]).sum()) >= matches_obs:
            hits += 1
    return (1 + hits) / (1 + n_perm)


def spearman_exact(x: list[float], y: list[float]) -> dict:
    """Spearman rho and the exact one-sided permutation p (rho at least the observed) over all orders of y."""
    rx, ry = stats.rankdata(x), stats.rankdata(y)
    def rho(a, b):
        a, b = np.asarray(a, float), np.asarray(b, float)
        a, b = a - a.mean(), b - b.mean()
        return float((a * b).sum() / math.sqrt((a * a).sum() * (b * b).sum()))
    observed = rho(rx, ry)
    perms = list(permutations(ry))
    p = sum(rho(rx, perm) >= observed - 1e-12 for perm in perms) / len(perms)
    return {"rho": observed, "p_one_sided": p, "n_orders": len(perms)}


def sign_test(k: int, n: int) -> float | None:
    return float(stats.binomtest(k, n, 0.5).pvalue) if n else None


def mcnemar_exact(first_right: list[bool], second_right: list[bool]) -> dict:
    b = sum(x and not y for x, y in zip(first_right, second_right))
    c = sum(y and not x for x, y in zip(first_right, second_right))
    p = float(stats.binomtest(min(b, c), b + c, 0.5).pvalue) if b + c else None
    return {"first_only": b, "second_only": c, "p_two_sided": p}


def agreement_block(experiment: list[str], model: list[str], labels: list[str], n_perm=0, seed=0) -> dict:
    n = len(experiment)
    k = sum(x == y for x, y in zip(experiment, model))
    low, high = clopper_pearson(k, n)
    block = {"n": n, "agree": k, "rate": k / n if n else None, "ci95": [low, high],
             "kappa": cohen_kappa(experiment, model, labels)}
    if n_perm and n:
        block["kappa_p_one_sided"] = kappa_permutation(experiment, model, labels, n_perm, seed)
    return block
