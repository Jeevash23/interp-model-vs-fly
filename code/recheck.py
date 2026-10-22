"""Independent recheck of AI-11's scores (PROTOCOL.md Section 9).

Written separately from common.py and score.py and using only Python's standard library: it reads the experimental
table, AI-06's effects.csv, AI-06's baseline records (for weighted pooling) and the connectome directly, recomputes
every per-comparison category and every score, and compares them with results/<split>/summary.json and
comparisons.csv. Categories and counts must match exactly, real values to 1e-9, permutation p-values within
Monte Carlo error.

  python3 -I recheck.py development | confirmation
"""
import ast
import csv
import itertools
import json
import math
import random
import statistics
import struct
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
CFG = json.loads((STUDY / "config.json").read_text())
AI06 = (STUDY / CFG["ai06_root"]).resolve()
CATS = ["abolished", "reduced", "unchanged", "increased"]
SLOW_KEY, FAST_KEY = "final_slow", "dev_fast"
READOUT_ORDER = ["T4a", "T4b", "T4c", "T4d", "T5a", "T5b", "T5c", "T5d"]


# ------------------------------------------------------------------------------------------------------- reading
def read_csv(path):
    with open(path, newline="") as f:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f)]


def read_npy_from_npz(path, name):
    with zipfile.ZipFile(path) as z:
        raw = z.read(name + ".npy")
    assert raw[:6] == b"\x93NUMPY"
    major = raw[6]
    if major == 1:
        hlen = struct.unpack("<H", raw[8:10])[0]
        start = 10
    else:
        hlen = struct.unpack("<I", raw[8:12])[0]
        start = 12
    header = ast.literal_eval(raw[start:start + hlen].decode("latin1"))
    data = raw[start + hlen:]
    code = {"<f4": "f", "<f8": "d", "<i8": "q"}[header["descr"]]
    size = struct.calcsize("<" + code)
    count = len(data) // size
    flat = struct.unpack("<" + code * count, data)
    shape = header["shape"]
    assert not header["fortran_order"]
    return flat, shape


def stimulus_info(key):
    manifest = json.loads((AI06 / "03-Data/stage1/stimulus-manifest.json").read_text())
    path = AI06 / [m["path"] for m in manifest if m["key"] == key][0]
    intensity, _ = read_npy_from_npz(path, "intensity")
    return intensity


BASE_CACHE = {}


def base_sum(model, key, readout):
    if (model, key) not in BASE_CACHE:
        flat, shape = read_npy_from_npz(AI06 / "study/results/runs" / model / key / "baseline.npz", "peaks")
        BASE_CACHE[(model, key)] = (flat, shape, stimulus_info(key))
    flat, shape, intensity = BASE_CACHE[(model, key)]
    col = READOUT_ORDER.index(readout)
    want = 1 if readout.startswith("T4") else 0
    return sum(float(flat[i * shape[1] + col]) for i in range(shape[0]) if intensity[i] == want)


def load_effects(split):
    out = {}
    for r in read_csv(AI06 / CFG["effects"][split]):
        def num(x):
            return None if x in ("", "None") else float(x)
        out[(r["model"], r["stimulus"], float(r["strength"]), r["readout"], r["cell"])] = (
            num(r["preferred_amplitude_ratio"]), float(r["baseline_dsi"]), num(r["exact"]), float(r["prediction"]),
            r["abolished"] == "True", r["defined"] == "True")
    return out


# ------------------------------------------------------------------------------------------------------- matching
def stimuli_for(speeds):
    s = speeds.strip().lower()
    if s in ("", "all", "mean", "not_reported", "na", "n/a"):
        return [SLOW_KEY, FAST_KEY]
    found = []
    for part in s.replace(",", ";").split(";"):
        key = FAST_KEY if float(part) >= CFG["speed_boundary_deg_s"] else SLOW_KEY
        if key not in found:
            found.append(key)
    return [k for k in (SLOW_KEY, FAST_KEY) if k in found]


def letters_for(r, measure):
    """Return {cell family: letters} or None, following the table in PROTOCOL.md Section 5.3."""
    ro, pol, dr = r["readout"], r["polarity"], r["direction"]
    layers = "".join(ch for ch in r.get("layers", "") if ch in "abcd")
    if pol not in ("ON", "OFF", "both") or dr not in ("PD", "ND", "both"):
        return None
    fams = {"ON": "T4", "OFF": "T5"}
    pols = ["ON", "OFF"] if pol == "both" else [pol]
    if ro in ("T4_calcium", "T4_voltage", "T5_calcium", "T5_voltage"):
        own = "ON" if ro[:2] == "T4" else "OFF"
        if pol not in (own, "both") or (measure == "amplitude" and dr == "ND"):
            return None
        return {fams[own]: layers or "abcd"}
    lptc = {"HS_voltage": ("a", "b", "ab"), "VS_voltage": ("d", "c", "cd"),
            "LPTC_voltage_pooled": ("ad", "bc", "abcd"), "behaviour": ("a", "b", "ab")}
    if ro not in lptc:
        return None
    if measure == "ds":
        pd_only = {"HS_voltage": "a", "VS_voltage": "d", "LPTC_voltage_pooled": "ad"}
        return {fams[p]: pd_only[ro] for p in pols} if ro in pd_only else None
    idx = {"PD": 0, "ND": 1, "both": 2}[dr]
    return {fams[p]: lptc[ro][idx] for p in pols}


def silenced(r):
    t = r["silenced_types"].replace(" ", "")
    if not t or t == "CT1" or any(ch in t for ch in "+;,/&"):
        return None
    return t


def mean_or_none(xs):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return sum(xs) / len(xs) if xs else None


def amp(eff, model, cell, fams, stims, strength, pooling):
    per_stim = []
    for st in stims:
        per_fam = []
        for fam, letters in fams.items():
            got = []
            for L in letters:
                e = eff.get((model, st, strength, fam + L, cell))
                if e is not None and e[0] is not None:
                    got.append((fam + L, e[0]))
            if not got:
                continue
            if pooling == "weighted":
                w = [base_sum(model, st, ro) for ro, _ in got]
                per_fam.append(sum(wi * v for wi, (_, v) in zip(w, got)) / sum(w))
            else:
                per_fam.append(sum(v for _, v in got) / len(got))
        per_stim.append(mean_or_none(per_fam))
    return mean_or_none(per_stim)


def dsq(eff, model, cell, fams, stims, strength, use_prediction=False):
    per_stim = []
    for st in stims:
        per_fam = []
        for fam, letters in fams.items():
            q = []
            for L in letters:
                e = eff.get((model, st, strength, fam + L, cell))
                if e is None or e[1] < CFG["min_baseline_dsi"]:
                    continue
                ratio, b, exact, pred, abol, defined = e
                ok = abol or (defined and exact is not None)
                if not ok:
                    continue
                if use_prediction:
                    q.append((b + pred) / b)
                else:
                    q.append(0.0 if abol else (b + exact) / b)
            per_fam.append(mean_or_none(q))
        per_stim.append(mean_or_none(per_fam))
    return mean_or_none(per_stim)


def cat(v, delta):
    if v <= CFG["abolished_cut"]:
        return "abolished"
    if v < 1 - delta:
        return "reduced"
    if v <= 1 + delta:
        return "unchanged"
    return "increased"


def consensus(vals, delta):
    vals = [v for v in vals if v is not None and math.isfinite(v)]
    if not vals:
        return None, None, 0
    counts = {c: 0 for c in CATS}
    for v in vals:
        counts[cat(v, delta)] += 1
    best = max(counts.values())
    tied = [c for c in CATS if counts[c] == best]
    med = statistics.median(vals)
    if len(tied) == 1:
        pick = tied[0]
    else:
        mc = cat(med, delta)
        pick = mc if mc in tied else sorted(tied, key=lambda c: (abs(CATS.index(c) - CATS.index(mc)), CATS.index(c)))[0]
    return pick, counts[pick] / len(vals), len(vals)


# ------------------------------------------------------------------------------------------------- connectivity
def connectivity_matrix():
    con = json.loads((AI06 / CFG["connectome"]).read_text())
    names = [n["name"] for n in con["nodes"]]
    n = len(names)
    cnt = [[0.0] * n for _ in range(n)]
    sgn = [[0.0] * n for _ in range(n)]
    for e in con["edges"]:
        t, s = names.index(e["tar"]), names.index(e["src"])
        c = sum(o[1] for o in e["offsets"])
        cnt[t][s] += c
        sgn[t][s] += (1 if e["alpha"] > 0 else -1 if e["alpha"] < 0 else 0) * c
    W = [[(sgn[t][s] / sum(cnt[t])) if sum(cnt[t]) > 0 else 0.0 for s in range(n)] for t in range(n)]
    A = [[1.0 if cnt[t][s] > 0 else 0.0 for s in range(n)] for t in range(n)]

    def mul(X, Y):
        Yt = list(zip(*Y))
        return [[sum(a * b for a, b in zip(row, col)) for col in Yt] for row in X]
    S = [[0.0] * n for _ in range(n)]
    R = [[0.0] * n for _ in range(n)]
    P = W
    Q = A
    for hop in range(CFG["connectivity_hops"]):
        if hop:
            P = mul(P, W)
            Q = mul(Q, A)
        S = [[S[i][j] + P[i][j] for j in range(n)] for i in range(n)]
        R = [[R[i][j] + Q[i][j] for j in range(n)] for i in range(n)]
    return names, S, R


# --------------------------------------------------------------------------------------------------- statistics
def binom_pmf(k, n, p):
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def cp_interval(k, n, alpha=0.05):
    if n == 0:
        return (float("nan"), float("nan"))

    def solve(f, target):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda p: sum(binom_pmf(i, n, p) for i in range(k, n + 1)), alpha / 2)
    upper = 1.0 if k == n else solve(lambda p: -sum(binom_pmf(i, n, p) for i in range(0, k + 1)), -alpha / 2)
    return (lower, upper)


def kappa(x, y, labels):
    n = len(x)
    if not n:
        return None
    po = sum(a == b for a, b in zip(x, y)) / n
    pe = sum(x.count(l) * y.count(l) for l in labels) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def perm_p(x, y, n_perm, seed):
    obs = sum(a == b for a, b in zip(x, y))
    rng = random.Random(seed + 1)          # a different generator and stream from score.py's
    yy = list(y)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(yy)
        if sum(a == b for a, b in zip(x, yy)) >= obs:
            hits += 1
    return (1 + hits) / (1 + n_perm)


def binom_two_sided(k, n):
    """Exact two-sided binomial p at p=0.5 (sum of outcomes no more likely than the observed one)."""
    if n == 0:
        return None
    pk = binom_pmf(k, n, 0.5)
    return min(1.0, sum(binom_pmf(i, n, 0.5) for i in range(n + 1) if binom_pmf(i, n, 0.5) <= pk * (1 + 1e-7)))


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def pearson(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den


def spearman_perm(x, y):
    rx, ry = ranks(x), ranks(y)
    obs = pearson(rx, ry)
    perms = list(itertools.permutations(ry))
    return obs, sum(pearson(rx, list(p)) >= obs - 1e-12 for p in perms) / len(perms)


# ---------------------------------------------------------------------------------------------------- recheck
def main(split, table_override=None):
    settings = json.loads((STUDY / "results/development/settings.json").read_text())
    delta, pooling = settings["delta"], settings["pooling"]
    table_path = Path(table_override) if table_override else \
        STUDY / ("code/standin_table.csv" if split == "development" else "extraction/merged-table.csv")
    table = read_csv(table_path)
    eff = load_effects(split)
    models = sorted({k[0] for k in eff})
    full, half = CFG["primary_strength"], CFG["partial_strength"]
    names, S, R = connectivity_matrix()
    mine = []
    for r in table:
        role = r.get("role", "primary")
        if role not in ("primary", "behaviour", "partial"):
            continue
        cell = silenced(r)
        for measure, field in (("amplitude", "amplitude_category"), ("ds", "ds_category")):
            exp = r.get(field, "")
            if exp not in CATS:
                continue
            fams = letters_for(r, measure) if cell else None
            stims = stimuli_for(r.get("speeds", ""))
            rec = {"row_id": r["row_id"], "measure": measure, "experiment": exp, "role": role, "source": r["source"],
                   "direction": r["direction"],
                   "matched": bool(cell and fams), "cell": cell, "fams": fams, "stims": stims}
            if settings.get("speed_rule") == "unmatched-secondary":
                text = r.get("speeds", "").lower()
                if text not in ("", "all", "mean", "not_reported"):
                    vals = [float(v) for v in text.replace(",", ";").split(";")]
                    rec["speed_unmatched"] = any(v < 27.55 or v > 110.2 for v in vals)
            if rec["matched"]:
                strength = half if (r.get("strength_class") or "full") == "partial" else full
                if measure == "amplitude":
                    vals = {m: amp(eff, m, cell, fams, stims, strength, pooling) for m in models}
                    hvals = {m: amp(eff, m, cell, fams, stims, half, pooling) for m in models}
                    fo = None
                else:
                    vals = {m: dsq(eff, m, cell, fams, stims, strength) for m in models}
                    hvals = {m: dsq(eff, m, cell, fams, stims, half) for m in models}
                    fo = consensus([dsq(eff, m, cell, fams, stims, strength, True) for m in models], delta)[0]
                c, share, nm = consensus(list(vals.values()), delta)
                rec.update(model=c, share=share, n_models=nm, half=consensus(list(hvals.values()), delta)[0],
                           first_order=fo, per_model={m: (cat(v, delta) if v is not None else None) for m, v in vals.items()},
                           vals=vals, **{f"d{d}": consensus(list(vals.values()), d)[0] for d in CFG["delta_sensitivity"]})
                if measure == "amplitude" and cell in names:
                    j = names.index(cell)
                    tot, reach = 0.0, False
                    fam_letters = [(f, L) for f, letters in fams.items() for L in letters]
                    for f, L in fam_letters:
                        i = names.index(f + L)
                        tot += S[i][j]
                        reach = reach or R[i][j] > 0
                    rec["connectivity"] = "unchanged" if (not reach or tot == 0.0) else ("reduced" if tot > 0 else "increased")
                else:
                    rec["connectivity"] = None
            mine.append(rec)

    primary = [c for c in mine if c["role"] == "primary" and c["matched"] and not c.get("speed_unmatched")
               and c.get("model") is not None]
    problems = []

    # Per-comparison categories against comparisons.csv.
    theirs = read_csv(STUDY / "results" / split / "comparisons.csv")
    if len(theirs) != len(mine):
        problems.append(f"comparison count {len(theirs)} != {len(mine)}")
    for a, b in zip(mine, theirs):
        for key_a, key_b in (("row_id", "row_id"), ("measure", "measure"), ("model", "model"), ("half", "model_half"),
                             ("first_order", "first_order"), ("connectivity", "connectivity"),
                             (f"d{CFG['delta_sensitivity'][0]}", f"model_delta_{CFG['delta_sensitivity'][0]}"),
                             (f"d{CFG['delta_sensitivity'][1]}", f"model_delta_{CFG['delta_sensitivity'][1]}")):
            va, vb = a.get(key_a), b.get(key_b)
            va = "" if va is None else str(va)
            if va != vb:
                problems.append(f"{a['row_id']}:{a['measure']} {key_a}: recheck {va!r} vs score {vb!r}")
        if a.get("share") is not None and abs(a["share"] - float(b["share"])) > 1e-9:
            problems.append(f"{a['row_id']}:{a['measure']} share differs")

    summary = json.loads((STUDY / "results" / split / "summary.json").read_text())

    def check_block(name, comps, field, labels=CATS, mapping=None, perm=False, ref=None):
        pairs = [(c["experiment"], c[field]) for c in comps if c.get(field) is not None]
        if mapping:
            pairs = [(mapping[x], mapping[y]) for x, y in pairs]
        x, y = [p[0] for p in pairs], [p[1] for p in pairs]
        n, k = len(x), sum(p == q for p, q in pairs)
        lo, hi = cp_interval(k, n)
        kap = kappa(x, y, labels)
        if ref is None:
            problems.append(f"{name}: missing in summary")
            return
        if ref["n"] != n or ref["agree"] != k:
            problems.append(f"{name}: n/agree {ref['n']}/{ref['agree']} vs {n}/{k}")
        if n:
            for got, want, what in ((lo, ref["ci95"][0], "ci low"), (hi, ref["ci95"][1], "ci high")):
                if abs(got - want) > 1e-9:
                    problems.append(f"{name}: {what} {want} vs {got}")
        if (kap is None) != (ref["kappa"] is None) or (kap is not None and abs(kap - ref["kappa"]) > 1e-9):
            problems.append(f"{name}: kappa {ref['kappa']} vs {kap}")
        if perm and n and "kappa_p_one_sided" in ref:
            p = perm_p(x, y, CFG["permutations"], CFG["seed"])
            se = math.sqrt(max(p * (1 - p), 1e-12) / CFG["permutations"])
            if abs(p - ref["kappa_p_one_sided"]) > 5 * se + 2e-5:
                problems.append(f"{name}: permutation p {ref['kappa_p_one_sided']} vs {p}")
        checked.append(name)

    checked = []
    P = summary["primary"]
    check_block("primary.all", primary, "model", perm=True, ref=P["all"])
    for s, ref in P["by_source"].items():
        check_block(f"primary.source.{s}", [c for c in primary if c["source"] == s], "model", perm=True, ref=ref)
    for m in ("amplitude", "ds"):
        check_block(f"primary.measure.{m}", [c for c in primary if c["measure"] == m], "model", perm=True,
                    ref=P["by_measure"][m])
    sec = summary["secondary"]
    three = {"abolished": "decrease", "reduced": "decrease", "unchanged": "unchanged", "increased": "increased"}
    labels3 = ["decrease", "unchanged", "increased"]
    amp_c = [c for c in primary if c["measure"] == "amplitude" and c.get("connectivity") is not None]
    check_block("d.connectivity", amp_c, "connectivity", perm=True, ref=sec["d_connectivity"]["connectivity"])
    check_block("d.exact", amp_c, "model", ref=sec["d_connectivity"]["exact_same_comparisons"])
    check_block("e.exact_all", primary, "model", labels3, three, perm=True, ref=sec["e_direction"]["exact_all"])
    check_block("e.connectivity", amp_c, "connectivity", labels3, three, ref=sec["e_direction"]["connectivity_amplitude"])
    check_block("e.exact_amplitude", amp_c, "model", labels3, three, ref=sec["e_direction"]["exact_amplitude"])
    for d in CFG["delta_sensitivity"]:
        check_block(f"f.delta{d}", primary, f"d{d}", ref=sec["f_delta"][str(d)])
    check_block("g.all_primary", primary, "half", ref=sec["g_half"]["all_primary"])
    check_block("g.partial", [c for c in mine if c["role"] == "partial" and c["matched"]], "model",
                ref=sec["g_half"]["partial_rows"])
    check_block("h.behaviour", [c for c in mine if c["role"] == "behaviour" and c["matched"]], "model",
                ref=sec["h_behaviour"])
    ds_c = [c for c in primary if c["measure"] == "ds" and c.get("first_order") is not None]
    check_block("c.first_order", ds_c, "first_order", ref=sec["c_first_order"]["first_order"])
    check_block("c.exact", ds_c, "model", ref=sec["c_first_order"]["exact"])
    b_ = sum((c["first_order"] == c["experiment"]) and not (c["model"] == c["experiment"]) for c in ds_c)
    c_ = sum((c["model"] == c["experiment"]) and not (c["first_order"] == c["experiment"]) for c in ds_c)
    mc = sec["c_first_order"]["mcnemar"]
    if (mc["first_only"], mc["second_only"]) != (b_, c_):
        problems.append("c.mcnemar counts differ")
    elif b_ + c_ and abs(binom_two_sided(min(b_, c_), b_ + c_) - mc["p_two_sided"]) > 1e-9:
        problems.append("c.mcnemar p differs")
    b2 = sum((c["connectivity"] == c["experiment"]) and not (c["model"] == c["experiment"]) for c in amp_c)
    c2 = sum((c["model"] == c["experiment"]) and not (c["connectivity"] == c["experiment"]) for c in amp_c)
    md = sec["d_connectivity"]["mcnemar"]
    if (md["first_only"], md["second_only"]) != (b2, c2):
        problems.append("d.mcnemar counts differ")
    elif b2 + c2 and abs(binom_two_sided(min(b2, c2), b2 + c2) - md["p_two_sided"]) > 1e-9:
        problems.append("d.mcnemar p differs")

    # (a) Serbe's order.
    a_ref = sec["a_serbe_order"]
    rows = {r["row_id"]: r for r in table}
    flagged = [c for c in primary if c["measure"] == "amplitude" and rows[c["row_id"]].get("score_a") == "1"]
    key_b03 = {"Tm1": 53.98, "Tm2": 39.22, "Tm4": 70.59, "Tm9": 25.69}
    by = {}
    printed = {}
    for c in flagged:
        by.setdefault(c["cell"], c)
        try:
            printed.setdefault(c["cell"], []).append(float(rows[c["row_id"]]["numeric_value"]))
        except ValueError:
            pass
    types = sorted(key_b03)
    if set(by) == set(types):
        rem = [sum(printed[t]) / len(printed[t]) for t in types] if set(printed) == set(types) else [key_b03[t] for t in types]
        meds = [statistics.median([v for v in by[t]["vals"].values() if v is not None]) for t in types]
        rho, p = spearman_perm(rem, meds)
        if not a_ref.get("testable") or abs(rho - a_ref["rho"]) > 1e-9 or abs(p - a_ref["p_one_sided"]) > 1e-12:
            problems.append(f"a: rho/p {a_ref.get('rho')}/{a_ref.get('p_one_sided')} vs {rho}/{p}")
        for got, want in zip(meds, a_ref["model_median"]):
            if abs(got - want) > 1e-9:
                problems.append("a: model medians differ")
        pos = one = scored = 0
        for m in models:
            xs = [by[t]["vals"][m] for t in types]
            if all(x is not None for x in xs):
                r_m = spearman_perm(rem, xs)[0]
                scored += 1
                pos += r_m > 0
                one += r_m > 1 - 1e-12
        if (pos, one, scored) != (a_ref["models_rho_positive"], a_ref["models_rho_one"], a_ref["models_scored"]):
            problems.append("a: per-model counts differ")
        checked.append("a")
    elif a_ref.get("testable"):
        problems.append("a: testable in summary but not in recheck")

    # (b) speed dependence.
    for cell in ("Tm3", "Mi1"):
        ref = sec["b_speed"][cell]
        rows_b = [c for c in primary if c["cell"] == cell and c["measure"] == "amplitude" and "T4" in c["fams"]
                  and "Ammer" in c["source"]]
        rows_b = [c for c in rows_b if c["direction"] == "PD"] + [c for c in rows_b if c["direction"] != "PD"]
        if not rows_b:
            if ref.get("testable"):
                problems.append(f"b.{cell}: testable in summary only")
            continue
        seen = []
        for c in rows_b:
            if c["fams"] not in seen:
                seen.append(c["fams"])
        for fams, res in zip(seen, ref["mappings"]):
            pairs = []
            for m in models:
                f = amp(eff, m, cell, fams, [FAST_KEY], full, pooling)
                s = amp(eff, m, cell, fams, [SLOW_KEY], full, pooling)
                if f is not None and s is not None:
                    pairs.append((f, s))
            lower = sum(f < s for f, s in pairs)
            ties = sum(f == s for f, s in pairs)
            p = binom_two_sided(lower, len(pairs) - ties)
            if (res["models"], res["fast_lower"], res["ties"]) != (len(pairs), lower, ties):
                problems.append(f"b.{cell}: counts differ")
            if (p is None) != (res["sign_test_p"] is None) or (p is not None and abs(p - res["sign_test_p"]) > 1e-9):
                problems.append(f"b.{cell}: sign test differs {res['sign_test_p']} vs {p}")
        checked.append(f"b.{cell}")

    # (i) per-model agreement.
    for m in models:
        sc = [(c["experiment"], c["per_model"][m]) for c in primary if c["per_model"][m] is not None]
        rate = sum(x == y for x, y in sc) / len(sc) if sc else None
        ref = sec["i_per_model"]["rates"][m]
        if (rate is None) != (ref is None) or (rate is not None and abs(rate - ref) > 1e-12):
            problems.append(f"i: model {m} rate {ref} vs {rate}")
    checked.append("i")

    report = {"split": split, "table": str(table_path.relative_to(STUDY)) if table_path.is_relative_to(STUDY) else str(table_path), "comparisons": len(mine),
              "checked": checked, "problems": problems, "pass": not problems}
    (STUDY / "results" / split / "recheck.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: report[k] for k in ("split", "comparisons", "pass")}), f"{len(checked)} blocks checked")
    for p in problems:
        print("PROBLEM", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in ("development", "confirmation"):
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None))
