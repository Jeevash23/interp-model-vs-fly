"""Score the hashed predictions (PREDICTIONS.md, PREDICTIONS-ADDENDUM.md) against results/<split>/.

  python -B score_predictions.py development | confirmation

Each prediction is "holds", "does not hold" or "not testable". A prediction about a type's rows holds when every
matching comparison has the predicted ensemble category; the counts are printed beside it. Written before the
confirmation set was scored, and frozen with the code.
"""
from __future__ import annotations

import csv
import json
import sys

import common as C


def load(split):
    out = C.RESULTS / split
    summary = json.loads((out / "summary.json").read_text())
    with (out / "comparisons.csv").open(newline="") as f:
        comps = list(csv.DictReader(f))
    for c in comps:
        c["sets"] = json.loads(c["sets"]) if c["sets"] not in ("", "null") else None
    return summary, comps


def verdict(flag):
    return "not testable" if flag is None else ("holds" if flag else "does not hold")


def type_rows(comps, cell, measure, polarity, stimuli=None):
    rows = [c for c in comps if c["role"] == "primary" and c["matched"] == "True" and c["model"]
            and c["speed_unmatched"] != "True" and c["cell"] == cell and c["measure"] == measure
            and c["sets"] and list(c["sets"]) == [polarity]]
    if stimuli is not None:
        rows = [c for c in rows if c["stimuli"] == stimuli]
    return rows


def all_are(rows, category):
    if not rows:
        return None, "no rows"
    counts = {}
    for c in rows:
        counts[c["model"]] = counts.get(c["model"], 0) + 1
    return all(c["model"] == category for c in rows), f"{len(rows)} rows: " + ", ".join(f"{k} {v}" for k, v in counts.items())


def main(split):
    s, comps = load(split)
    P, S = s["primary"]["all"], s["secondary"]
    res = []

    def add(pid, quantity, flag, detail=""):
        res.append({"id": pid, "quantity": quantity, "verdict": verdict(flag), "detail": detail})

    rate = P["rate"]
    add("P1", "four-category agreement in [0.40, 0.75]", None if rate is None else 0.40 <= rate <= 0.75, f"{rate}")
    add("P2a", "kappa > 0", None if P["kappa"] is None else P["kappa"] > 0, f"{P['kappa']}")
    add("P2b", "kappa permutation p < 0.05", None if P.get("kappa_p_one_sided") is None else P["kappa_p_one_sided"] < 0.05,
        f"{P.get('kappa_p_one_sided')}")
    d3 = S["e_direction"]["exact_all"]["rate"]
    add("P3", "three-category minus four-category agreement >= 0.10",
        None if d3 is None or rate is None else d3 - rate >= 0.10 - 1e-12, f"{d3} - {rate}")
    flag, det = all_are(type_rows(comps, "Mi1", "amplitude", "ON"), "abolished")
    add("P4a", "Mi1 ON amplitude rows abolished", flag, det)
    rows = type_rows(comps, "Mi1", "amplitude", "ON")
    add("P4b", "... with at least 70% of models", None if not rows else all(float(c["share"]) >= 0.70 for c in rows),
        ", ".join(f"{c['row_id']} {float(c['share']):.2f}" for c in rows))
    add("P5", "Mi1 OFF amplitude rows unchanged", *all_are(type_rows(comps, "Mi1", "amplitude", "OFF"), "unchanged"))
    add("P6", "Tm3 ON amplitude rows at 110.2 deg/s reduced", *all_are(type_rows(comps, "Tm3", "amplitude", "ON", C.FAST), "reduced"))
    add("P7", "Tm3 ON amplitude rows at 27.55 deg/s reduced", *all_are(type_rows(comps, "Tm3", "amplitude", "ON", C.SLOW), "reduced"))
    add("P8", "Tm3 OFF amplitude rows unchanged", *all_are(type_rows(comps, "Tm3", "amplitude", "OFF"), "unchanged"))
    for t in ("Mi4", "Mi9"):
        add(f"P9.{t}", f"{t} ON amplitude rows increased", *all_are(type_rows(comps, t, "amplitude", "ON"), "increased"))
    for t in ("Mi4", "Mi9"):
        add(f"P10.{t}", f"{t} T4 direction-selectivity rows reduced", *all_are(type_rows(comps, t, "ds", "ON"), "reduced"))
    for t, cat in (("Tm9", "reduced"), ("Tm1", "reduced"), ("Tm2", "reduced"), ("Tm4", "unchanged")):
        add(f"P11.{t}", f"{t} OFF amplitude rows {cat}", *all_are(type_rows(comps, t, "amplitude", "OFF"), cat))
    rows = [c for t in ("Tm1", "Tm2", "Tm4", "Tm9") for c in type_rows(comps, t, "amplitude", "ON")]
    add("P12", "Tm1, Tm2, Tm4, Tm9 ON amplitude rows unchanged", *all_are(rows, "unchanged"))

    a = S["a_serbe_order"]
    add("Sa1", "Serbe order rho > 0", a["rho"] > 0 if a.get("testable") else None, f"{a.get('rho')}")
    add("Sa2", "Serbe order rho = 1", a["rho"] > 1 - 1e-12 if a.get("testable") else None, f"{a.get('rho')}")
    b = S["b_speed"]["Tm3"]
    if b.get("testable"):
        m = b["mappings"][0]
        add("Sb1", "Tm3 fast below slow in more than half of models", m["fast_lower"] > m["models"] / 2,
            f"{m['fast_lower']} of {m['models']}")
        add("Sb2", "... and sign test p < 0.05", m["fast_lower"] > m["models"] / 2 and (m["sign_test_p"] or 1) < 0.05,
            f"p = {m['sign_test_p']}")
    else:
        add("Sb1", "Tm3 fast below slow in more than half of models", None)
        add("Sb2", "... and sign test p < 0.05", None)
    c = S["c_first_order"]
    if c["testable"]:
        add("Sc1", "first-order agreement lower than exact on DS comparisons", c["first_order"]["rate"] < c["exact"]["rate"],
            f"{c['first_order']['rate']} vs {c['exact']['rate']}")
        p = c["mcnemar"]["p_two_sided"]
        add("Sc2", "McNemar p < 0.05", p is not None and p < 0.05, f"{p}")
    else:
        add("Sc1", "first-order agreement lower than exact on DS comparisons", None)
        add("Sc2", "McNemar p < 0.05", None)
    add("Sc3", "not testable for lack of DS comparisons", not c["testable"], f"n = {c['n']}")
    d = S["d_connectivity"]
    add("Sd1", "connectivity four-category agreement >= exact", None if not d["n"] else
        d["connectivity"]["rate"] >= d["exact_same_comparisons"]["rate"],
        f"{d['connectivity']['rate']} vs {d['exact_same_comparisons']['rate']}")
    e = S["e_direction"]
    add("Sd2", "connectivity three-category agreement below exact", None if not d["n"] else
        e["connectivity_amplitude"]["rate"] < e["exact_amplitude"]["rate"],
        f"{e['connectivity_amplitude']['rate']} vs {e['exact_amplitude']['rate']}")
    rates = [v["rate"] for v in S["f_delta"].values() if v["rate"] is not None]
    add("Sf", "agreement varies by at most 0.15 across delta", None if len(rates) < 3 else max(rates) - min(rates) <= 0.15 + 1e-12,
        f"{min(rates) if rates else None}-{max(rates) if rates else None}")
    g = S["g_half"]["all_primary"]["rate"]
    add("Sg", "half-strength agreement >= full", None if g is None or rate is None else g >= rate - 1e-12, f"{g} vs {rate}")
    i = S["i_per_model"]
    add("Si", "per-model median within 0.10 of the ensemble", None if i["median"] is None or rate is None else
        abs(i["median"] - rate) <= 0.10 + 1e-12, f"{i['median']} vs {rate}")

    agreement_path = C.STUDY / "extraction" / "merge-work" / "agreement.json"
    if agreement_path.exists():
        # "Matched rows" are the rows expanded to elementary units (AMENDMENTS.md, Amendment 1.2); findings shown beside.
        full = json.loads(agreement_path.read_text())
        ag, fa = full["units"]["amplitude"], full["findings"]["amplitude"]
        add("E1a", "extractor agreement on amplitude >= 0.8", ag["share"] >= 0.8 - 1e-12,
            f"units {ag['share']}; findings {fa['share']}")
        add("E1b", "extractor kappa >= 0.6", None if ag["kappa"] is None else ag["kappa"] >= 0.6 - 1e-12,
            f"units {ag['kappa']}; findings {fa['kappa']}")
        table = C.read_table(C.STUDY / "extraction" / "merged-table.csv")
        lptc = ("LPTC_voltage_pooled", "HS_voltage", "VS_voltage")
        def pick(src, cell, pol):
            # The key's rows cite Ammer Fig. 2 (preferred direction, B01-B02) and Serbe Fig. 5 (B03).
            panel = {"Ammer": "AM-2", "Serbe": "SE-5"}[src]
            return [r for r in table if src in r["source"] and r["silenced_types"] == cell and r["polarity"] == pol
                    and r["readout"] in lptc and r.get("experiment") == panel and r["amplitude_category"] in C.CATEGORIES]
        ok, notes = True, []
        for r in pick("Ammer", "Mi1", "ON"):
            ok &= r["amplitude_category"] == "reduced"; notes.append(f"{r['row_id']} Mi1 {r['amplitude_category']}")
        for r in pick("Ammer", "Tm3", "ON"):
            speeds = C.model_speed_keys(r.get("speeds", ""))
            want = "unchanged" if speeds == [C.SLOW] else "reduced" if speeds == [C.FAST] else None
            if want:
                ok &= r["amplitude_category"] == want; notes.append(f"{r['row_id']} Tm3 {r['amplitude_category']}")
        for t in ("Tm1", "Tm2", "Tm4", "Tm9"):
            for r in pick("Serbe", t, "OFF"):
                ok &= r["amplitude_category"] == "reduced"; notes.append(f"{r['row_id']} {t} {r['amplitude_category']}")
        add("E2", "merged categories match the key (B01-B03)", ok if notes else None, "; ".join(notes))

    serbe = {}
    for c in comps:
        if (c["role"] == "primary" and c["matched"] == "True" and c["model"] and "Serbe" in c["source"]
                and c["measure"] == "amplitude" and c["sets"] and list(c["sets"]) == ["OFF"]
                and c["readout"] in ("LPTC_voltage_pooled", "HS_voltage", "VS_voltage")
                and c["cell"] in ("Tm1", "Tm2", "Tm4", "Tm9")):
            serbe.setdefault(c["cell"], []).append(c["model"])
    majority = {t: max(set(v), key=v.count) for t, v in serbe.items()}
    add("D1", "Serbe OFF rows unchanged for at least three of four types",
        None if len(majority) < 4 else sum(v == "unchanged" for v in majority.values()) >= 3, json.dumps(majority))
    add("D2", "four-category agreement in [0.15, 0.55]", None if rate is None else 0.15 <= rate <= 0.55, f"{rate}")
    add("D3", "connectivity agrees more often than exact (amplitude)", None if not d["n"] else
        d["connectivity"]["rate"] > d["exact_same_comparisons"]["rate"],
        f"{d['connectivity']['rate']} vs {d['exact_same_comparisons']['rate']}")
    if b.get("testable"):
        m = b["mappings"][0]
        add("D4", "Tm3 fast below slow in at most half of models", m["fast_lower"] <= m["models"] / 2,
            f"{m['fast_lower']} of {m['models']}")
    else:
        add("D4", "Tm3 fast below slow in at most half of models", None)
    add("D5", "Serbe order rho > 0", a["rho"] > 0 if a.get("testable") else None, f"{a.get('rho')}")

    out = C.RESULTS / split / "predictions-scored.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    for r in res:
        print(f"{r['id']:8} {r['verdict']:14} {r['quantity']}  [{r['detail']}]")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("development", "confirmation"):
        sys.exit(__doc__)
    main(sys.argv[1])
