"""Independent recheck of stage 2, Part 1 (pair silencing), using only Python's standard library.

  python3 -I stage2_recheck.py development | confirmation
  python3 -I stage2_recheck.py strother      Part 2's report.json: stage 1's primary comparisons with the
                                             supplement's, and the Fig. S2B rows of prediction R1, recomputed from
                                             the two comparisons.csv files (stage 1's recheck checks those files)

Shares no code with the scorers (common.py, score.py, stage2_score.py). It reuses stage 1's independent checker
(recheck.py, itself standard-library only), reads the raw pair records with its own .npz reader, recomputes every
per-model pair ratio, ensemble category and stage-2 score, and compares them with results/stage2/scores/<split>/.
Categories and counts must match exactly, real values to 1e-9, permutation p-values within Monte Carlo error.
"""
import csv
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import recheck as R  # noqa: E402  (stage 1's independent checker; standard library only)

STUDY = R.STUDY
PAIRS = ["Tm1+Tm2", "Tm1+Tm4", "Tm1+Tm9", "Tm2+Tm4", "Tm2+Tm9", "Tm4+Tm9"]
READOUTS = R.READOUT_ORDER


def baseline_arrays(model, key):
    path = R.AI06 / "study/results/runs" / model / key / "baseline.npz"
    out = {}
    for name in ("peaks", "dsi", "denominator"):
        flat, shape = R.read_npy_from_npz(path, name)
        out[name] = (flat, shape)
    return out


def pair_effects(split):
    eff = {}
    folder = STUDY / "results/stage2" / split
    for model_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        model = model_dir.name
        for key in ("final_slow", "dev_fast"):
            base = baseline_arrays(model, key)
            intensity = R.stimulus_info(key)
            bpk, bshape = base["peaks"]
            for path in sorted((model_dir / key).glob("s*-*.npz")):
                meta = json.loads(path.with_suffix(".json").read_text())
                pk, shape = R.read_npy_from_npz(path, "peaks")
                dsi, _ = R.read_npy_from_npz(path, "dsi")
                den, _ = R.read_npy_from_npz(path, "denominator")
                cell = "+".join(meta["names"])
                for r, ro in enumerate(READOUTS):
                    want = 1 if ro.startswith("T4") else 0
                    rows = [i for i in range(shape[0]) if intensity[i] == want]
                    after = sum(float(pk[i * shape[1] + r]) for i in rows)
                    before = sum(float(bpk[i * bshape[1] + r]) for i in rows)
                    responsive = base["denominator"][0][r] > 1e-8
                    defined = responsive and den[r] > 1e-8 and math.isfinite(dsi[r])
                    eff[(model, key, float(meta["strength"]), ro, cell)] = (
                        after / before if before > 1e-8 else None, float(base["dsi"][0][r]),
                        float(dsi[r]) - float(base["dsi"][0][r]) if defined else None, 0.0,
                        bool(responsive and den[r] <= 1e-8), bool(defined))
    return eff


def pair_name(text):
    return "+".join(sorted(p.strip() for p in text.replace(" ", "").split("+")))


def main(split):
    settings = json.loads((STUDY / "results/development/settings.json").read_text())
    delta, pooling = settings["delta"], settings["pooling"]
    half, full = R.CFG["partial_strength"], R.CFG["primary_strength"]
    table = R.read_csv(STUDY / "extraction/merged-table.csv")
    eff = pair_effects(split)
    singles = R.load_effects(split)
    models = sorted({k[0] for k in eff})
    names, S, Rch = R.connectivity_matrix()
    mine = []
    for r in table:
        role = r.get("role", "")
        if role not in ("pair", "partial"):
            continue
        cell = pair_name(r["silenced_types"]) if role == "pair" else R.silenced(r)
        if role == "pair" and cell not in PAIRS:
            continue
        exp = r.get("amplitude_category", "")
        if exp not in R.CATS:
            continue
        fams = R.letters_for(r, "amplitude")
        stims = R.stimuli_for(r.get("speeds", ""))
        source = eff if role == "pair" else singles
        rec = {"row_id": r["row_id"], "role": role, "cell": cell, "experiment": exp, "polarity": r["polarity"],
               "direction": r["direction"], "lptc": r["readout"] != "behaviour", "matched": bool(cell and fams)}
        if rec["matched"]:
            for label, strength in (("half", half), ("full", full)):
                vals = {m: R.amp(source, m, cell, fams, stims, strength, pooling) for m in models}
                c, share, n = R.consensus(list(vals.values()), delta)
                valid = [v for v in vals.values() if v is not None]
                rec[label] = c
                rec[f"share_{label}"] = share
                rec[f"median_{label}"] = statistics.median(valid) if valid else None
                if label == "half":
                    rec["per_model"] = {m: (R.cat(v, delta) if v is not None else None) for m, v in vals.items()}
            tot, reach = 0.0, False
            for t in cell.split("+"):
                j = names.index(t)
                for fam, letters in fams.items():
                    for L in letters:
                        i = names.index(fam + L)
                        tot += S[i][j]
                        reach = reach or Rch[i][j] > 0
            rec["connectivity"] = "unchanged" if (not reach or tot == 0.0) else ("reduced" if tot > 0 else "increased")
        mine.append(rec)

    out = STUDY / "results/stage2/scores" / split
    summary = json.loads((out / "summary.json").read_text())
    theirs = {r["row_id"]: r for r in R.read_csv(out / "comparisons.csv")}
    problems, checked = [], []
    for rec in mine:
        t = theirs.get(rec["row_id"])
        if t is None:
            problems.append(f"{rec['row_id']} missing from comparisons.csv")
            continue
        for a, b in (("half", "model_half"), ("full", "model_full"), ("connectivity", "connectivity")):
            va = "" if rec.get(a) is None else str(rec.get(a))
            if va != t[b]:
                problems.append(f"{rec['row_id']} {a}: recheck {va!r} vs score {t[b]!r}")
        for a in ("share_half", "median_half", "share_full", "median_full"):
            if rec.get(a) is not None and abs(rec[a] - float(t[a])) > 1e-9:
                problems.append(f"{rec['row_id']} {a} differs")
    if len(theirs) != len(mine):
        problems.append(f"comparison count {len(theirs)} vs {len(mine)}")

    def check_block(name, items, field, ref, perm=False):
        pairs = [(c["experiment"], c[field]) for c in items if c.get(field) is not None]
        x, y = [p for p, _ in pairs], [q for _, q in pairs]
        n, k = len(x), sum(p == q for p, q in pairs)
        if (ref["n"], ref["agree"]) != (n, k):
            problems.append(f"{name}: n/agree {ref['n']}/{ref['agree']} vs {n}/{k}")
        if n:
            lo, hi = R.cp_interval(k, n)
            if abs(lo - ref["ci95"][0]) > 1e-9 or abs(hi - ref["ci95"][1]) > 1e-9:
                problems.append(f"{name}: interval differs")
        kap = R.kappa(x, y, R.CATS)
        if (kap is None) != (ref["kappa"] is None) or (kap is not None and abs(kap - ref["kappa"]) > 1e-9):
            problems.append(f"{name}: kappa {ref['kappa']} vs {kap}")
        if perm and n and "kappa_p_one_sided" in ref:
            p = R.perm_p(x, y, R.CFG["permutations"], R.CFG["seed"])
            se = math.sqrt(max(p * (1 - p), 1e-12) / R.CFG["permutations"])
            if abs(p - ref["kappa_p_one_sided"]) > 5 * se + 2e-5:
                problems.append(f"{name}: permutation p {ref['kappa_p_one_sided']} vs {p}")
        checked.append(name)

    lptc = [c for c in mine if c["role"] == "pair" and c["lptc"] and c["matched"]]
    beh = [c for c in mine if c["role"] == "pair" and not c["lptc"] and c["matched"]]
    part = [c for c in mine if c["role"] == "partial" and c["matched"]]
    check_block("primary", lptc, "half", summary["primary"], perm=True)
    check_block("a_full", lptc, "full", summary["a_full"], perm=True)
    check_block("b_with_singles", lptc + part, "half", summary["b_with_singles"], perm=True)
    check_block("d_behaviour", beh, "half", summary["d_behaviour"])
    check_block("e_connectivity", lptc, "connectivity", summary["e_connectivity"]["connectivity"], perm=True)
    for pol in ("ON", "OFF", "both"):
        check_block(f"polarity_{pol}", [c for c in lptc if c["polarity"] == pol], "half", summary["primary_by_polarity"][pol])
    # (2c) pairs beyond singles.
    six = {c["cell"]: c for c in lptc if c["polarity"] == "OFF" and c["direction"] == "both"}
    single = {c["cell"]: c for c in part if c["polarity"] == "OFF" and c["direction"] == "both"}
    for label in ("half", "full"):
        count = 0
        for p in PAIRS:
            a, b = p.split("+")
            if p in six and a in single and b in single:
                count += six[p][f"median_{label}"] < min(single[a][f"median_{label}"], single[b][f"median_{label}"])
        if count != summary["c_beyond_singles"][label]["beyond"]:
            problems.append(f"c_beyond_singles {label}: {summary['c_beyond_singles'][label]['beyond']} vs {count}")
    checked.append("c_beyond_singles")
    # (2f) per model.
    for m in models:
        sc = [(c["experiment"], c["per_model"][m]) for c in lptc if c["per_model"][m] is not None]
        rate = sum(x == y for x, y in sc) / len(sc) if sc else None
        ref = summary["f_per_model"]["rates"][m]
        if (rate is None) != (ref is None) or (rate is not None and abs(rate - ref) > 1e-12):
            problems.append(f"f_per_model {m}: {ref} vs {rate}")
    checked.append("f_per_model")
    # (2g) with stage 1.
    if split == "confirmation":
        s1 = [r for r in R.read_csv(STUDY / "results/confirmation/comparisons.csv") if r["role"] == "primary" and r["model"]]
        items = [{"experiment": r["experiment"], "half": r["model"]} for r in s1] + lptc
        check_block("g_with_stage1", items, "half", summary["g_with_stage1"], perm=True)
    report = {"split": split, "comparisons": len(mine), "checked": checked, "problems": problems, "pass": not problems}
    (out / "recheck.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: report[k] for k in ("split", "comparisons", "pass")}), f"{len(checked)} blocks checked")
    for p in problems:
        print("PROBLEM", p)
    return 0 if not problems else 1


def strother():
    root = STUDY / "results/stage2/strother/results/confirmation"
    rep = json.loads((root / "report.json").read_text())
    table = {r["row_id"]: r for r in R.read_csv(STUDY / rep["table"])}

    def primary(path):
        return [r for r in R.read_csv(path) if r["role"] == "primary" and r["matched"] == "True"
                and r["speed_unmatched"] == "False" and r["model"]]
    old, new = primary(STUDY / "results/confirmation/comparisons.csv"), primary(root / "comparisons.csv")
    problems = []
    x = [r["experiment"] for r in old + new]
    y = [r["model"] for r in old + new]
    n, k = len(x), sum(a == b for a, b in zip(x, y))
    ref = rep["stage1_plus_supplement_primary"]
    if (ref["n"], ref["agree"], rep["stage1_primary_n"], rep["supplement_primary_n"]) != (n, k, len(old), len(new)):
        problems.append(f"counts {ref['n']}/{ref['agree']} vs {n}/{k}")
    lo, hi = R.cp_interval(k, n)
    if abs(lo - ref["ci95"][0]) > 1e-9 or abs(hi - ref["ci95"][1]) > 1e-9:
        problems.append("interval differs")
    kap = R.kappa(x, y, R.CATS)
    if abs(kap - ref["kappa"]) > 1e-9:
        problems.append(f"kappa {ref['kappa']} vs {kap}")
    p = R.perm_p(x, y, R.CFG["permutations"], R.CFG["seed"])
    se = math.sqrt(max(p * (1 - p), 1e-12) / R.CFG["permutations"])
    if abs(p - ref["kappa_p_one_sided"]) > 5 * se + 2e-5:
        problems.append(f"permutation p {ref['kappa_p_one_sided']} vs {p}")
    r1 = sorted((r["cell"], r["experiment"], r["model"]) for r in new
                if table[r["row_id"]]["experiment"] == "ST-S2B" and r["readout"] == "T4_calcium" and r["polarity"] == "ON")
    if r1 != sorted((r["cell"], r["fly"], r["model"]) for r in rep["r1_rows"]):
        problems.append("R1 rows differ")
    out = {"split": "strother", "checked": ["stage1_plus_supplement_primary", "r1_rows"], "problems": problems,
           "pass": not problems}
    (root / "recheck-report.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"split": "strother", "n": n, "pass": not problems}))
    for msg in problems:
        print("PROBLEM", msg)
    return 0 if not problems else 1


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("development", "confirmation", "strother"):
        sys.exit(__doc__)
    sys.exit(strother() if sys.argv[1] == "strother" else main(sys.argv[1]))
