"""Write paper/generated/numbers.tex and the generated tables from the saved study outputs.

Every study number in the manuscript is a macro defined here, computed from: the configuration and development
settings; the merged experimental table and the extractors' agreement; the confirmation summary, comparisons,
per-model records, scored predictions and recheck; and the freeze records. Stage 2 adds the pair scores, the
supplement's table, agreement, scores, report and repeats, the replay and integrity checks, and the stage-2 freeze
records. `--check` recomputes everything in memory and fails if a written file differs.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

PAPER = Path(__file__).resolve().parent
STUDY = PAPER.parent
RES = STUDY / "results"


def load(path: Path):
    return json.loads(path.read_text())


def rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


CONFIG = load(STUDY / "config.json")
SETTINGS = load(RES / "development/settings.json")
DEVCHECK = load(RES / "development/dev-checks.json")
SUMMARY = load(RES / "confirmation/summary.json")
RECHECK = load(RES / "confirmation/recheck.json")
PRED = load(RES / "confirmation/predictions-scored.json")
AGREE = load(STUDY / "extraction/merge-work/agreement.json")
FREEZE = load(STUDY / "FREEZE.json")
PRED_RECORD = load(STUDY / "PREDICTIONS-RECORD.json")
TABLE = rows(STUDY / "extraction/merged-table.csv")
COMPS = rows(RES / "confirmation/comparisons.csv")
TROWS = {r["row_id"]: r for r in TABLE}
PRIMARY = [c for c in COMPS if c["role"] == "primary" and c["model"]]
# Stage 2 (STAGE2-PROTOCOL.md): Part 1, pair silencing; Part 2, Strother's supplement.
S2DIR = RES / "stage2"
S2 = load(S2DIR / "scores/confirmation/summary.json")
S2COMPS = rows(S2DIR / "scores/confirmation/comparisons.csv")
S2PRED = load(S2DIR / "scores/confirmation/predictions-scored.json")
S2RECHECK = load(S2DIR / "scores/confirmation/recheck.json")
S2REPLAY = load(S2DIR / "replay-check.json")
S2INTEGRITY = load(S2DIR / "integrity-confirmation.json")
S2RECORD = load(STUDY / "STAGE2-RECORD.json")
FREEZE2 = load(STUDY / "FREEZE-STAGE2.json")
FREEZE2S = load(STUDY / "FREEZE-STAGE2-STROTHER.json")
SUPDIR = S2DIR / "strother/results/confirmation"
SUP = load(SUPDIR / "summary.json")
SUPCOMPS = rows(SUPDIR / "comparisons.csv")
SUPREPORT = load(SUPDIR / "report.json")
SUPRECHECK = load(SUPDIR / "recheck.json")
SUPREPORTCHECK = load(SUPDIR / "recheck-report.json")
SUPTABLE = rows(STUDY / "extraction/stage2/supplement-table.csv")
SUPAGREE = load(STUDY / "extraction/stage2/merge-work/agreement.json")
SUPUNITS = {x: rows(STUDY / f"extraction/stage2/merge-work/units-{x}.csv") for x in "AB"}
REPEATS = rows(STUDY / "extraction/stage2/repeats.csv")
S3H = rows(STUDY / "extraction/stage2/merge-work/s3h-markers.csv")
PAIR_COMPS = [c for c in S2COMPS if "+" in c["cell"]]
PAIR_LPTC = [c for c in PAIR_COMPS if c["readout"] != "behaviour"]
WORDS = ["none", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


# ------------------------------------------------------------------------------------------------ formatting
def f(x, d=2):
    text = f"{x:.{d}f}"
    if float(text) == 0:
        text = f"{0:.{d}f}"
    return "\\ensuremath{-}" + text[1:] if text.startswith("-") else text


def pct(x, d=0):
    return f(100 * x, d)


def num(n):
    return f"{int(n):,}"


def word(n):
    return WORDS[n] if 0 <= n <= 10 else num(n)


def pval(p):
    if p < 0.001:
        return "\\ensuremath{<}0.001"
    return f(p, 3) if p < 0.1 else f(p, 2)


def prel(p):
    """A p-value with its relation, for running text: =0.012 or <0.001."""
    return "\\ensuremath{<}0.001" if p < 0.001 else "=" + pval(p)


def cap(text):
    return text[0].upper() + text[1:]


def sci(x):
    mantissa, exponent = f"{x:.1e}".split("e")
    return f"\\ensuremath{{{mantissa}\\times10^{{{int(exponent)}}}}}"


# ------------------------------------------------------------------------------------------------ groups
def group(c: dict) -> str:
    """The rows of the by-type table: silenced type and the pathway of the readout."""
    t = TROWS[c["row_id"]]
    if c["measure"] == "ds":
        return "DS-" + ("T4" if t["readout"].startswith("T4") else "LPTC")
    cell = c["cell"]
    if t["readout"].startswith("T4"):
        path = "ON"
    else:
        path = {"ON": "ON", "OFF": "OFF", "both": "grating"}[c["polarity"]]
    if cell in ("Tm1", "Tm2", "Tm4", "Tm9"):
        cell = "TmOFF"
    return f"{cell}-{path}"


GROUP_ORDER = [("Mi1-ON", "Mi1", "ON (T4)"), ("Mi1-OFF", "Mi1", "OFF (T5)"), ("Tm3-ON", "Tm3", "ON (T4)"),
               ("Tm3-OFF", "Tm3", "OFF (T5)"), ("Mi4-ON", "Mi4", "ON (T4)"), ("Mi9-ON", "Mi9", "ON (T4)"),
               ("TmOFF-OFF", "Tm1, Tm2, Tm4, Tm9", "OFF (T5)"), ("TmOFF-grating", "Tm1, Tm2, Tm4, Tm9", "gratings"),
               ("TmOFF-ON", "Tm1, Tm2, Tm4, Tm9", "ON (T4)"), ("DS-LPTC", "Mi1, Tm3", "OFF direction selectivity"),
               ("DS-T4", "Mi4, Mi9", "T4 direction selectivity")]


def by_group() -> dict[str, list[dict]]:
    out = {}
    for c in PRIMARY:
        out.setdefault(group(c), []).append(c)
    return out


def cats(items, field):
    counts = Counter(c[field] for c in items)
    order = ["abolished", "reduced", "unchanged", "increased"]
    parts = [f"{k} {counts[k]}" if len(counts) > 1 else k for k in order if counts.get(k)]
    return ", ".join(parts)


def med_range(items):
    meds = sorted(float(c["median"]) for c in items)
    return f(meds[0]) if f(meds[0]) == f(meds[-1]) else f"{f(meds[0])}--{f(meds[-1])}"


# ---------------------------------------------------------------------------------------------------- macros
def macros() -> dict[str, str]:
    m = {}
    s, sec = SUMMARY, SUMMARY["secondary"]
    P = s["primary"]["all"]
    # Design.
    m.update(NModels=str(s["n_models"] + len(CONFIG["development_models"])), NConfModels=str(s["n_models"]),
             NDevModels=word(len(CONFIG["development_models"])), SpeedSlow=f(CONFIG["model_speeds"]["final_slow"], 2),
             SpeedFast=f(CONFIG["model_speeds"]["dev_fast"], 1), SpeedBoundary=f(CONFIG["speed_boundary_deg_s"], 1),
             MarginDelta=f(SETTINGS["delta"], 1), AbolishedCut=f(CONFIG["abolished_cut"], 1),
             AbolishedPct=pct(CONFIG["abolished_cut"]),
             UnchangedLow=f(1 - SETTINGS["delta"], 1), UnchangedHigh=f(1 + SETTINGS["delta"], 1),
             MinDsi=f(CONFIG["min_baseline_dsi"], 1), NPerm=num(CONFIG["permutations"]), Hops=word(CONFIG["connectivity_hops"]),
             DeltaLow=f(CONFIG["delta_sensitivity"][0], 1), DeltaHigh=f(CONFIG["delta_sensitivity"][1], 1),
             DeltaPct=pct(SETTINGS["delta"]))
    m.update(DevPoolingDifferPct=pct(DEVCHECK["pooling"]["share_differ"]),
             DevPoolingPairs=str(DEVCHECK["pooling"]["pairs"]), DevPoolingDiffer=str(len(DEVCHECK["pooling"]["categories_differ"])),
             DevPoolingLimitPct=pct(DEVCHECK["pooling"]["limit"]),
             DevMaxMeanRatio=f(max(v for v in DEVCHECK["delta"]["values"].values() if v is not None), 0),
             DevSpeedDiffer=str(sum(1 for p in DEVCHECK["speed"]["comparisons"] if p["same_category"] is False)),
             DevSpeedTotal=str(sum(1 for p in DEVCHECK["speed"]["comparisons"] if p["same_category"] is not None)))
    # Extraction and agreement.
    u, fi = AGREE["units"], AGREE["findings"]
    m.update(RowsA=str(AGREE["raw_rows"]["A"]), RowsB=str(AGREE["raw_rows"]["B"]),
             UnitsMatched=str(u["matched"]), UnitsAgree=str(u["amplitude"]["agree"]), UnitsAgreePct=pct(u["amplitude"]["share"], 1),
             UnitsKappa=f(u["amplitude"]["kappa"]), UnitsDsKappa=f(u["ds"]["kappa"]),
             FindMatched=str(fi["matched"]), FindAgree=str(fi["amplitude"]["agree"]), FindAgreePct=pct(fi["amplitude"]["share"], 1),
             FindKappa=f(fi["amplitude"]["kappa"]), FindDsKappa=f(fi["ds"]["kappa"]),
             UnitsDsDisagree=str(u["matched"] - u["ds"]["agree"]))
    roles = Counter(r["role"] for r in TABLE)
    settled = sum(r["settlement"] != "agreed" for r in TABLE)
    m.update(NFindings=str(len(TABLE)), NPrimaryFindings=str(roles["primary"]), NPartial=word(roles["partial"]),
             NBehaviourFindings=str(roles["behaviour"]), NPairs=str(roles["pair"]), NExcluded=str(roles["excluded"]),
             NSettled=str(settled), NUnmatched=word(len(s["counts"]["primary_unmatched"])))
    statement = 0
    tables = {x: {r["row_id"]: r for r in rows(STUDY / "extraction" / x / "table.csv")} for x in "AB"}
    for r in TABLE:
        if r["role"] != "primary":
            continue
        ids = [i for i in (r["origin_A"] + ";" + r["origin_B"]).split(";") if i]
        src = [tables["A"].get(i) or tables["B"].get(i) for i in ids]
        if any(x and "no test" in (x["notes"] + x["statistics"]).lower() for x in src):
            statement += 1
    m.update(NStatementOnly=str(statement))
    exp = Counter(c["experiment"] for c in PRIMARY)
    mod = Counter(c["model"] for c in PRIMARY)
    m.update(NComparisons=str(P["n"]), ExpReduced=str(exp["reduced"]), ExpUnchanged=str(exp["unchanged"]),
             ModUnchanged=str(mod["unchanged"]), ModReduced=str(mod["reduced"]), ModIncreased=word(mod["increased"]),
             ModAbolished=word(mod["abolished"]), NAmplitude=str(s["primary"]["by_measure"]["amplitude"]["n"]),
             NDs=word(s["primary"]["by_measure"]["ds"]["n"]))
    conf = Counter((c["experiment"], c["model"]) for c in PRIMARY)
    m.update(ConfBothUnchanged=str(conf[("unchanged", "unchanged")]), ConfBothReduced=str(conf[("reduced", "reduced")]),
             ConfRedUnch=str(conf[("reduced", "unchanged")]), ConfUnchRed=word(conf[("unchanged", "reduced")]),
             ConfUnchInc=word(conf[("unchanged", "increased")]), ConfUnchAbol=word(conf[("unchanged", "abolished")]))
    # Primary.
    m.update(AgreeN=str(P["agree"]), AgreePct=pct(P["rate"], 1), AgreeLow=pct(P["ci95"][0], 1), AgreeHigh=pct(P["ci95"][1], 1),
             Kappa=f(P["kappa"]), KappaP=prel(P["kappa_p_one_sided"]))
    for key, label in (("Ammer 2015", "Ammer"), ("Serbe 2016", "Serbe"), ("Strother 2017", "Strother")):
        b = s["primary"]["by_source"][key]
        m.update({f"{label}N": str(b["n"]), f"{label}Agree": str(b["agree"]), f"{label}Pct": pct(b["rate"]),
                  f"{label}Kappa": f(b["kappa"]), f"{label}KappaP": prel(b["kappa_p_one_sided"])})
    amp, ds = s["primary"]["by_measure"]["amplitude"], s["primary"]["by_measure"]["ds"]
    m.update(AmpAgree=str(amp["agree"]), AmpPct=pct(amp["rate"]), AmpKappa=f(amp["kappa"]), AmpKappaP=prel(amp["kappa_p_one_sided"]),
             DsAgree=word(ds["agree"]))
    g = by_group()
    for key, short in (("Mi1-ON", "MiOneOn"), ("Mi1-OFF", "MiOneOff"), ("Tm3-ON", "TmThreeOn"), ("Tm3-OFF", "TmThreeOff"),
                       ("Mi4-ON", "MiFourOn"), ("Mi9-ON", "MiNineOn"), ("TmOFF-OFF", "TmOff"), ("TmOFF-ON", "TmOn"),
                       ("TmOFF-grating", "TmGrating")):
        items = g[key]
        m.update({f"{short}N": word(len(items)), f"{short}Agree": word(sum(c["experiment"] == c["model"] for c in items)),
                  f"{short}Med": med_range(items)})
    ab = [json.loads(c["counts"])["abolished"] for c in g["Mi1-ON"]]
    m.update(MiOneOnAbolLow=str(min(ab)), MiOneOnAbolHigh=str(max(ab)),
             MiOneOnShareLow=pct(min(float(c["share"]) for c in g["Mi1-ON"])),
             MiOneOnShareHigh=pct(max(float(c["share"]) for c in g["Mi1-ON"])))
    inc = [c for c in g["Mi1-OFF"] if c["model"] == "increased"]
    m.update(MiOneOffInc=word(len(inc)), MiOneOffIncMed=med_range(inc),
             MiOneOffIncModelsLow=str(min(json.loads(c["counts"])["increased"] for c in inc)),
             MiOneOffIncModelsHigh=str(max(json.loads(c["counts"])["increased"] for c in inc)))
    vals = sorted(float(TROWS[c["row_id"]]["numeric_value"]) for c in PRIMARY if TROWS[c["row_id"]]["score_a"] == "1")
    m.update(SerbeRemainLow=f(vals[0], 0), SerbeRemainHigh=f(vals[-1], 0))
    # Secondary.
    a = sec["a_serbe_order"]
    names = {"Tm1": "One", "Tm2": "Two", "Tm4": "Four", "Tm9": "Nine"}
    for t, med, rem in zip(a["types"], a["model_median"], a["remaining_response"]):
        m[f"SerbeMed{names[t]}"] = f(med)
        m[f"SerbeRem{names[t]}"] = f(rem, 1)
    m.update(SerbeRho=f(a["rho"], 1), SerbeRhoP=f(a["p_one_sided"], 3), SerbeRhoPositive=str(a["models_rho_positive"]),
             SerbeRhoOne=word(a["models_rho_one"]), SerbePermNum=str(round(a["p_one_sided"] * a["n_orders"])),
             SerbeOrders=str(a["n_orders"]))
    b = sec["b_speed"]["Tm3"]["mappings"][0]
    m.update(TmThreeFastLower=str(b["fast_lower"]), TmThreeTies=word(b["ties"]), TmThreeSignP=f(b["sign_test_p"], 3),
             TmThreeMedFast=f(b["median_fast"]), TmThreeMedSlow=f(b["median_slow"]))
    b1 = sec["b_speed"]["Mi1"]["mappings"][0]
    m.update(MiOneFastLower=str(b1["fast_lower"]), MiOneTies=word(b1["ties"]), MiOneSignP=prel(b1["sign_test_p"]),
             MiOneMedFast=f(b1["median_fast"]), MiOneMedSlow=f(b1["median_slow"]))
    c = sec["c_first_order"]
    m.update(FoAgree=word(c["first_order"]["agree"]), FoExactAgree=word(c["exact"]["agree"]), FoN=word(c["n"]),
             FoMcNemarP=f(c["mcnemar"]["p_two_sided"], 1))
    d = sec["d_connectivity"]
    m.update(ConnAgree=str(d["connectivity"]["agree"]), ConnN=str(d["n"]), ConnPct=pct(d["connectivity"]["rate"]),
             ConnKappa=f(d["connectivity"]["kappa"]), ConnKappaP=prel(d["connectivity"]["kappa_p_one_sided"]),
             ConnExactAgree=str(d["exact_same_comparisons"]["agree"]), ConnExactPct=pct(d["exact_same_comparisons"]["rate"]),
             ConnOnly=str(d["mcnemar"]["first_only"]), ExactOnly=str(d["mcnemar"]["second_only"]),
             ConnMcNemarP=f(d["mcnemar"]["p_two_sided"], 2))
    e = sec["e_direction"]["exact_all"]
    m.update(DirAgree=str(e["agree"]), DirKappa=f(e["kappa"]), DirKappaP=prel(e["kappa_p_one_sided"]))
    fd = sec["f_delta"]
    m.update(DeltaLowAgree=str(fd[str(CONFIG["delta_sensitivity"][0])]["agree"]),
             DeltaHighAgree=str(fd[str(CONFIG["delta_sensitivity"][1])]["agree"]))
    gh = sec["g_half"]
    m.update(PartialAgree=word(gh["partial_rows"]["agree"]), PartialN=word(gh["partial_rows"]["n"]),
             HalfAgree=str(gh["all_primary"]["agree"]), HalfPct=pct(gh["all_primary"]["rate"]), HalfKappa=f(gh["all_primary"]["kappa"]))
    h = sec["h_behaviour"]
    m.update(BehAgree=str(h["agree"]), BehN=str(h["n"]), BehPct=pct(h["rate"]), BehKappa=f(h["kappa"]))
    i = sec["i_per_model"]
    m.update(PerModelMedian=f(i["median"]), PerModelQLow=f(i["quartiles"][0]), PerModelQHigh=f(i["quartiles"][2]),
             PerModelMin=f(i["min"]), PerModelMax=f(i["max"]), PerModelAtLeast=str(i["models_at_or_above_ensemble"]))
    # Predictions.
    groups = {"P": [], "S": [], "E": [], "D": []}
    for r in PRED:
        groups[r["id"][0]].append(r)
    for k, name in (("P", "Main"), ("S", "Sec"), ("E", "Ext"), ("D", "Add")):
        m[f"Pred{name}N"] = word(len(groups[k]))
        m[f"Pred{name}Hold"] = word(sum(r["verdict"] == "holds" for r in groups[k]))
    # Checks and times.
    m.update(RecheckBlocks=str(len(RECHECK["checked"])), RecheckComparisons=str(RECHECK["comparisons"]),
             FrozenFiles=str(len(FREEZE["files_sha256"])), FreezeTime=FREEZE["written_at_utc"][11:16],
             PredTime=PRED_RECORD["written_at_utc"][11:16])
    m.update(stage2_macros())
    return m


def stage2_macros() -> dict[str, str]:
    m = {}
    P = S2["primary"]
    lptc = PAIR_LPTC
    m.update(STwoN=str(P["n"]), STwoAgree=str(P["agree"]), STwoPct=pct(P["rate"], 1), STwoLow=pct(P["ci95"][0], 1),
             STwoHigh=pct(P["ci95"][1], 1), STwoKappa=f(P["kappa"]))
    exp = Counter(c["experiment"] for c in lptc)
    half = Counter(c["model_half"] for c in lptc)
    m.update(STwoExpReduced=str(exp["reduced"]), STwoExpUnchanged=str(exp["unchanged"]),
             STwoModHalfUnchanged=str(half["unchanged"]))
    meds = sorted(float(c["median_half"]) for c in lptc)
    m.update(STwoHalfMedLow=f(meds[0]), STwoHalfMedHigh=f(meds[-1]))
    on, off, grating = ([c for c in lptc if c["polarity"] == p] for p in ("ON", "OFF", "both"))
    agree_half = lambda items: sum(c["experiment"] == c["model_half"] for c in items)  # noqa: E731
    m.update(STwoOnN=str(len(on)), STwoOnAgree=str(agree_half(on)), STwoOffN=str(len(off)), STwoOffAgree=word(agree_half(off)),
             STwoOffExpReduced=str(sum(c["experiment"] == "reduced" for c in off)), STwoGratN=word(len(grating)),
             STwoOffAgreeNames=" and ".join(sorted({c["cell"] for c in off if c["experiment"] == c["model_half"]})),
             STwoGratAgree=word(agree_half(grating)),
             STwoOffFullReduced=word(sum(c["model_full"] == "reduced" for c in off)),
             STwoOnFullReduced=word(sum(c["model_full"] == "reduced" for c in on)),
             STwoOffFullMedLow=f(min(float(c["median_full"]) for c in off)),
             STwoOffFullMedHigh=f(max(float(c["median_full"]) for c in off)))
    a = S2["a_full"]
    m.update(STwoFullAgree=str(a["agree"]), STwoFullPct=pct(a["rate"], 1), STwoFullKappa=f(a["kappa"]),
             STwoFullKappaP=prel(a["kappa_p_one_sided"]))
    b = S2["b_with_singles"]
    m.update(STwoSinglesAgree=str(b["agree"]), STwoSinglesN=str(b["n"]), STwoSinglesKappa=f(b["kappa"]))
    for label, key in (("Half", "half"), ("Full", "full")):
        c = S2["c_beyond_singles"][key]
        pair_meds = [r["pair_median"] for r in c["pairs"]]
        single_meds = [v for r in c["pairs"] for v in r["single_medians"]]
        m.update({f"STwoBeyond{label}": word(c["beyond"]), f"STwoBeyond{label}N": word(c["n"]),
                  f"STwoPairMed{label}Low": f(min(pair_meds)), f"STwoPairMed{label}High": f(max(pair_meds)),
                  f"STwoSingleMed{label}Low": f(min(single_meds)), f"STwoSingleMed{label}High": f(max(single_meds))})
    d = S2["d_behaviour"]
    m.update(STwoBehAgree=word(d["agree"]), STwoBehN=word(d["n"]))
    e = S2["e_connectivity"]
    m.update(STwoConnAgree=str(e["connectivity"]["agree"]), STwoConnKappa=f(e["connectivity"]["kappa"]),
             STwoConnKappaP=prel(e["connectivity"]["kappa_p_one_sided"]))
    fm = S2["f_per_model"]
    m.update(STwoPerModelMedian=f(fm["median"]), STwoPerModelMin=f(fm["min"]), STwoPerModelMax=f(fm["max"]))
    g = S2["g_with_stage1"]
    m.update(STwoBothAgree=str(g["agree"]), STwoBothN=str(g["n"]), STwoBothKappa=f(g["kappa"]),
             STwoBothKappaP=prel(g["kappa_p_one_sided"]))
    q4 = json.loads(next(r for r in S2PRED if r["id"] == "Q4")["detail"])
    reduced_pairs = [p for p, cat_ in q4.items() if cat_ == "reduced"]
    m.update(STwoFullPairsReduced=word(len(reduced_pairs)), STwoFullPairsNames=" and ".join(reduced_pairs))
    # Checks, records and times.
    m.update(STwoReplayCases=str(sum(1 for c in S2REPLAY["cases"] if "pair" in c)),
             STwoReplayWorst=sci(S2REPLAY["worst_normalised_gap"]), STwoBaselineWorst=sci(S2INTEGRITY["worst_baseline_gap"]),
             STwoRecords=num(S2INTEGRITY["records_found"]), STwoRecordTime=S2RECORD["written_at_utc"][11:16],
             STwoFreezeTime=FREEZE2["written_at_utc"][11:16], STwoFrozenRecords=num(len(FREEZE2["records_sha256"])),
             STwoFrozenFiles=str(len(FREEZE2["files_sha256"])), STwoSupFrozenFiles=str(len(FREEZE2S["files_sha256"])),
             STwoRecheckComparisons=str(S2RECHECK["comparisons"]), STwoRecheckBlocks=str(len(S2RECHECK["checked"])),
             STwoSupRecheckComparisons=str(SUPRECHECK["comparisons"]), STwoSupRecheckBlocks=str(len(SUPRECHECK["checked"])))
    if not (S2RECHECK["pass"] and SUPRECHECK["pass"] and SUPREPORTCHECK["pass"] and S2INTEGRITY["pass"] and S2REPLAY["pass"]):
        raise SystemExit("a stage-2 check did not pass")
    # Part 2: the supplement.
    u, fi = SUPAGREE["units"], SUPAGREE["findings"]
    m.update(STwoSupRowsA=str(SUPAGREE["raw_rows"]["A"]), STwoSupRowsB=str(SUPAGREE["raw_rows"]["B"]),
             STwoSupUnitsMatched=str(u["matched"]), STwoSupUnitsAgree=str(u["amplitude"]["agree"]),
             STwoSupUnitsKappa=f(u["amplitude"]["kappa"]), STwoSupFindMatched=str(fi["matched"]),
             STwoSupFindAgree=str(fi["amplitude"]["agree"]), STwoSupFindKappa=f(fi["amplitude"]["kappa"]),
             STwoSupFindDiffer=word(fi["matched"] - fi["amplitude"]["agree"]),
             STwoSupTies=word(fi["amplitude"]["specific"]["mixed"]["both"]))
    roles = Counter(r["role"] for r in SUPTABLE)
    m.update(STwoSupFindings=str(len(SUPTABLE)), STwoSupPrimary=word(roles["primary"]), STwoSupBehaviour=str(roles["behaviour"]),
             STwoSupExcluded=str(roles["excluded"]),
             STwoSupMixed=word(sum(r["amplitude_category"] == "mixed" for r in SUPTABLE)),
             STwoSupSettledText=word(sum(r["settlement"].startswith("settled") and "text" in r["settlement"] for r in SUPTABLE)))
    sp = SUP["primary"]["all"]
    m.update(STwoSupN=word(sp["n"]), STwoSupAgree=word(sp["agree"]), STwoSupKappa=f(sp["kappa"]),
             STwoSupKappaP=prel(sp["kappa_p_one_sided"]))
    r1 = {r["cell"]: r for r in SUPREPORT["r1_rows"]}
    m.update(STwoMiFourMed=f(r1["Mi4"]["median"]), STwoMiFourShare=pct(r1["Mi4"]["share"]))
    comb = SUPREPORT["stage1_plus_supplement_primary"]
    m.update(STwoCombAgree=str(comb["agree"]), STwoCombN=str(comb["n"]), STwoCombPct=pct(comb["rate"], 1),
             STwoCombKappa=f(comb["kappa"]), STwoCombKappaP=prel(comb["kappa_p_one_sided"]))
    h = SUP["secondary"]["h_behaviour"]
    m.update(STwoSupBehAgree=str(h["agree"]), STwoSupBehN=str(h["n"]), STwoSupBehPct=pct(h["rate"]), STwoSupBehKappa=f(h["kappa"]))
    mi4 = [c for c in SUPCOMPS if c["role"] == "behaviour" and c["matched"] == "True" and c["cell"] == "Mi4"]
    m.update(STwoSupMiFourBehN=str(len(mi4)), STwoSupMiFourBehInc=str(sum(c["model"] == "increased" for c in mi4)),
             STwoSupMiFourBehFlyUnch=str(sum(c["experiment"] == "unchanged" for c in mi4)),
             STwoSupMiFourBehFlyInc=word(sum(c["experiment"] == "increased" for c in mi4)))
    compared = [r for r in REPEATS if r["compared"] == "yes"]
    m.update(STwoRepeatsN=str(len(compared)), STwoRepeatsSame=str(sum(r["same"] == "yes" for r in compared)),
             STwoRepeatsDirection=word(sum(r["same"] == "yes" and r["how"] != "same category" for r in compared)))
    m.update(STwoSthMarkers=str(len(S3H)), STwoSthCovered=str(sum(r["centre_covered"] == "yes" for r in S3H)),
             STwoSthUnits=str(sum(r["experiment"] == "ST-S3H" for x in "AB" for r in SUPUNITS[x])))
    m.update(STwoPredN=str(len(S2PRED)), STwoPredHold=str(sum(r["verdict"] == "holds" for r in S2PRED)))
    return m


# ---------------------------------------------------------------------------------------------------- tables
def table_types() -> str:
    g = by_group()
    out = []
    for key, cell, path in GROUP_ORDER:
        items = g[key]
        n, k = len(items), sum(c["experiment"] == c["model"] for c in items)
        out.append(f"{cell} & {path} & {n} & {cats(items, 'experiment')} & {cats(items, 'model')} & "
                   f"{med_range(items)} & {k} \\\\")
    return "\n".join(out) + "\n"


def table_sources() -> str:
    s = SUMMARY["primary"]
    lines = []
    for key in ("Ammer 2015", "Serbe 2016", "Strother 2017"):
        b = s["by_source"][key]
        lines.append(f"{key.replace(' 2', ' et al.\\ 2')} & {b['n']} & {b['agree']} & {f(b['rate'])} & {f(b['kappa'])} & "
                     f"{pval(b['kappa_p_one_sided'])} \\\\")
    lines.append("\\midrule")
    for key, label in (("amplitude", "Response amplitude"), ("ds", "Direction selectivity")):
        b = s["by_measure"][key]
        lines.append(f"{label} & {b['n']} & {b['agree']} & {f(b['rate'])} & {f(b['kappa'])} & "
                     f"{pval(b['kappa_p_one_sided'])} \\\\")
    lines.append("\\midrule")
    a = s["all"]
    lines.append(f"All & {a['n']} & {a['agree']} & {f(a['rate'])} & {f(a['kappa'])} & {pval(a['kappa_p_one_sided'])} \\\\")
    return "\n".join(lines) + "\n"


EXPERIMENT_LABEL = {"AM-1EF": "Ammer 1E--F", "AM-2": "Ammer 2", "AM-3": "Ammer 3", "AM-23DS": "Ammer 2--3 (text)",
                    "SE-5": "Serbe 5", "SE-S4": "Serbe S4", "SE-S5": "Serbe S5", "ST-3C": "Strother 3C",
                    "ST-4A": "Strother 4A", "ST-DS": "Strother (text)"}


def table_comparisons() -> str:
    out = []
    for c in PRIMARY:
        t = TROWS[c["row_id"]]
        speeds = t["speeds"]
        speed = {"mean": "mean", "all": "all"}.get(speeds, speeds.replace(";", ", ") if speeds.count(";") < 2
                                                   else f"{speeds.split(';')[0]}--{speeds.split(';')[-1]}")
        readout = {"LPTC_voltage_pooled": "HS/VS", "T4_calcium": "T4 Ca"}[t["readout"]]
        measure = "DS" if c["measure"] == "ds" else "amp."
        polarity = {"both": "ON+OFF"}.get(c["polarity"], c["polarity"])
        direction = {"both": "--"}.get(c["direction"], c["direction"])
        ok = "\\checkmark" if c["experiment"] == c["model"] else ""
        out.append(f"{c['row_id']} & {EXPERIMENT_LABEL[t['experiment']]} & {c['cell']} & {readout} & {polarity} & "
                   f"{direction} & {speed} & {measure} & {c['experiment']} & {c['model']} & {f(float(c['share']))} & "
                   f"{f(float(c['median']))} & {ok} \\\\")
    return "\n".join(out) + "\n"


def table_predictions() -> str:
    texts = {
        "P1": "Agreement between 0.40 and 0.75", "P2a": "$\\kappa > 0$", "P2b": "$\\kappa$ permutation $p < 0.05$",
        "P3": "Three-category agreement at least 0.10 above four-category", "P4a": "Mi1, ON: abolished",
        "P4b": "Mi1, ON: at least 70\\% of models abolished", "P5": "Mi1, OFF: unchanged",
        "P6": "Tm3, ON, fast: reduced", "P7": "Tm3, ON, slow: reduced", "P8": "Tm3, OFF: unchanged",
        "P9.Mi4": "Mi4, ON: increased", "P9.Mi9": "Mi9, ON: increased", "P10.Mi4": "Mi4, T4 DS: reduced",
        "P10.Mi9": "Mi9, T4 DS: reduced", "P11.Tm9": "Tm9, OFF: reduced", "P11.Tm1": "Tm1, OFF: reduced",
        "P11.Tm2": "Tm2, OFF: reduced", "P11.Tm4": "Tm4, OFF: unchanged", "P12": "Tm1, Tm2, Tm4, Tm9, ON: unchanged",
        "Sa1": "Serbe's order: $\\rho > 0$", "Sa2": "Serbe's order: $\\rho = 1$",
        "Sb1": "Tm3: fast below slow in more than half of models", "Sb2": "Tm3: and sign test $p < 0.05$",
        "Sc1": "First-order agrees less often than exact (DS)", "Sc2": "First-order against exact: McNemar $p < 0.05$",
        "Sc3": "First-order against exact not testable", "Sd1": "Connectivity at least exact (four categories)",
        "Sd2": "Connectivity below exact (three categories)", "Sf": "Agreement varies by at most 0.15 across $\\delta$",
        "Sg": "Half strength at least full", "Si": "Per-model median within 0.10 of the ensemble",
        "E1a": "Extractors agree on at least 80\\% of units", "E1b": "Extractors' $\\kappa$ at least 0.6",
        "E2": "Merged table matches the earlier extraction", "D1": "Serbe's OFF rows unchanged for at least three types",
        "D2": "Agreement between 0.15 and 0.55", "D3": "Connectivity agrees more often than exact",
        "D4": "Tm3: fast below slow in at most half of models", "D5": "Serbe's order: $\\rho > 0$"}
    out = []
    for r in PRED:
        verdict = {"holds": "holds", "does not hold": "does not hold", "not testable": "not testable"}[r["verdict"]]
        out.append(f"{r['id']} & {texts[r['id']]} & {verdict} \\\\")
    return "\n".join(out) + "\n"


def table_stage2_pairs() -> str:
    """Stage 2: pair findings by stimulus, with the flies' and the models' categories at half and full strength."""
    groups = [("Bright edges", [c for c in PAIR_LPTC if c["polarity"] == "ON"]),
              ("Dark edges", [c for c in PAIR_LPTC if c["polarity"] == "OFF"]),
              ("Gratings", [c for c in PAIR_LPTC if c["polarity"] == "both"]),
              ("All tangential-cell findings", PAIR_LPTC),
              ("Behaviour (secondary)", [c for c in PAIR_COMPS if c["readout"] == "behaviour"])]
    out = []
    for i, (label, items) in enumerate(groups):
        if i in (3, 4):
            out.append("\\midrule")
        half = sum(c["experiment"] == c["model_half"] for c in items)
        full = sum(c["experiment"] == c["model_full"] for c in items)
        out.append(f"{label} & {len(items)} & {cats(items, 'experiment')} & {cats(items, 'model_half')} & {half} & "
                   f"{cats(items, 'model_full')} & {full} \\\\")
    return "\n".join(out) + "\n"


def table_stage2_predictions() -> str:
    texts = {
        "Q1": "Dark-edge findings at half strength unchanged for at least five of the six pairs",
        "Q2": "Agreement at half strength between 0.40 and 0.65", "Q3": "$\\kappa$ at most 0.10",
        "Q4": "Dark-edge findings at full strength reduced for at least two pairs",
        "Q5": "Agreement at full strength at least that at half strength",
        "Q6": "Each pair below both its single blocks (dark edges, half strength) for at least five pairs",
        "Q7": "Replay of the companion study's pair records within $10^{-4}$",
        "Q8": "Intact responses within $10^{-4}$ of the saved records",
        "Q9": "Behavioural pair findings unchanged in at least five of seven",
        "Q10": "Bright-edge pair findings unchanged in at least 15 of 18",
        "R1": "Supplement, T4 at 30\\degs: three of four agree, all but Mi4",
        "R2": "Repeated supplementary points keep the first stage's category"}
    return "\n".join(f"{r['id']} & {texts[r['id']]} & {r['verdict']} \\\\" for r in S2PRED) + "\n"


def numbers_tex(m: dict[str, str]) -> str:
    lines = ["% Generated by make_numbers.py from the saved study outputs. Do not edit."]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(m.items())]
    return "\n".join(lines) + "\n"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    out = {PAPER / "generated/numbers.tex": numbers_tex(macros()),
           PAPER / "generated/table-types.tex": table_types(),
           PAPER / "generated/table-sources.tex": table_sources(),
           PAPER / "generated/table-comparisons.tex": table_comparisons(),
           PAPER / "generated/table-predictions.tex": table_predictions(),
           PAPER / "generated/table-stage2-pairs.tex": table_stage2_pairs(),
           PAPER / "generated/table-stage2-predictions.tex": table_stage2_predictions()}
    if args.check:
        bad = [str(k) for k, v in out.items() if not k.exists() or k.read_text() != v]
        if bad:
            raise SystemExit(f"generated files differ: {bad}")
        print("generated files match")
        return
    for path, text in out.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(f"wrote {len(out)} files")


if __name__ == "__main__":
    main()
