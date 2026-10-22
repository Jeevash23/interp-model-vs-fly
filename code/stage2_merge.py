"""Stage 2, Part 2: build the table of supplement findings and the comparison of repeated points with stage 1
(STAGE2-AMENDMENTS.md, S4).

  python -B stage2_merge.py     writes extraction/stage2/supplement-table.csv and extraction/stage2/repeats.csv

Every finding that both extractors coded with the same category is agreed. Every other finding needs an entry in
extraction/stage2/settlements.json: "settle" (settled against the source) or "left_out" (a tie that the text does not
decide; it stays in the table as mixed and so is not scored). Anything else stops the build. Roles follow S4 rule 6.
Fig. S3H's units are checked against the markers read from the PDF's vector paths (merge-work/s3h-markers.csv), and
the points that repeat a stage-1 condition (S4 rule 5) are compared with stage 1's category for that condition.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter

import common as C
import merge_findings as MF
import stage2_units as V

ROOT = C.STUDY / "extraction" / "stage2"
COLUMNS = MF.COLUMNS + ["lines", "conditions"]
DIRECTION = {"abolished": "decrease", "reduced": "decrease", "unchanged": "unchanged", "increased": "increase"}
STAGE1_NAME = {"T4T5": "T4a-d+T5a-d"}


def role_of(exp: str, genotype: str, readout: str) -> tuple[str, str]:
    if genotype == "T4T5":
        return "excluded", "T4 and T5 silenced together: no confirmation counterpart"
    if exp in ("ST-S3A", "ST-S3B"):
        return "excluded", ("contrast series: the model's stimuli are at full contrast, and the full-contrast grating at "
                            "these speeds is stage 1's Fig. 4B (STAGE2-AMENDMENTS.md, S4 rule 6)")
    if readout == "behaviour":
        return "behaviour", "behaviour: secondary score (h)"
    return "primary", ""


def read_markers() -> dict:
    path = ROOT / "merge-work" / "s3h-markers.csv"
    return {(r["line"], r["stimulus"], int(r["speed_deg_s"])): r for r in C.read_table(path)}


def marker_category(rec: dict) -> str:
    if rec["marker"] == "open":
        return "unchanged"
    return "increased" if rec["against_control"] == "above" else "reduced"


def check_s3h(units: dict, markers: dict) -> list[str]:
    """Every Fig. S3H unit of both extractors against the vector-path reading of the same marker."""
    problems = []
    for x, items in units.items():
        for u in items:
            if u["experiment"] != "ST-S3H":
                continue
            rec = markers[(f"{u['genotype']}-{u['line']}", f"{u['polarity']} {u['condition']}", int(u["speed"]))]
            if marker_category(rec) != u["amplitude"]:
                problems.append(f"{u['row_id']}: {u['amplitude']} but the marker reads {marker_category(rec)}")
    return problems


def compare(supplement: str, stage1: str) -> tuple[str, str]:
    """S4 rule 8: the same category, or the same direction where stage 1's category is an abolition from the text."""
    if supplement == stage1:
        return "yes", "same category"
    if stage1 == "abolished":
        same = DIRECTION[supplement] == DIRECTION[stage1]
        return ("yes" if same else "no"), "direction compared: stage 1's abolition comes from the text, which marks cannot show"
    return "no", "different category"


def repeats(units: dict, markers: dict, spec: dict, merged1: list[dict]) -> list[dict]:
    stage1_units = {}
    for x in "AB":
        for r in C.read_table(C.STUDY / "extraction/merge-work" / f"units-{x}.csv"):
            if r["speed"] not in ("mean", "all"):
                stage1_units.setdefault((r["experiment"], r["genotype"], r["polarity"], float(r["speed"])), {})[x] = r

    def stage1_rows(exp, genotype, polarity, speed):
        name = STAGE1_NAME.get(genotype, genotype)
        return [r for r in merged1 if r["experiment"] == exp and r["silenced_types"] == name and r["polarity"] == polarity
                and (r["speeds"] in ("all", "mean") or speed in [float(s) for s in r["speeds"].split(";")])]

    out = []
    seen = set()
    for x in "AB":
        for u in units[x]:
            if u["repeat"] != "Fig. 4B":
                continue
            key = (u["genotype"], u["speed"])
            if key in seen:
                raise SystemExit(f"two extractions give the repeated point {key}; compare them before merging")
            seen.add(key)
            ref = stage1_units[("ST-4B", u["genotype"], "both", u["speed"])]
            if ref["A"]["amplitude"] != ref["B"]["amplitude"]:
                raise SystemExit(f"stage 1's extractions differ at Fig. 4B {key}")
            same, how = compare(u["amplitude"], ref["A"]["amplitude"])
            rows = stage1_rows("ST-4B", u["genotype"], "both", u["speed"])
            out.append({"repeat_of": "Fig. 4B", "panel": u["experiment"], "genotype": u["genotype"], "line": "main",
                        "polarity": u["polarity"], "speed_deg_s": f"{u['speed']:g}", "condition": u["condition"],
                        "supplement_category": u["amplitude"], "supplement_basis": f"extractor {x}, row {u['row_id']}",
                        "stage1_category": ref["A"]["amplitude"],
                        "stage1_basis": f"stage-1 units {ref['A']['row_id']} (A), {ref['B']['row_id']} (B); "
                                        f"finding {', '.join(r['row_id'] + ' ' + r['amplitude_category'] for r in rows)}",
                        "compared": "yes", "same": same, "how": how})
    s3h = spec["repeats_s3h"]
    for genotype in s3h["points"]:
        for stimulus in s3h["stimuli"]:
            polarity = stimulus.split()[0]
            rec = markers[(f"{genotype}-{s3h['line']}", stimulus, s3h["speed_deg_s"])]
            rows = stage1_rows("ST-3E", genotype, polarity, float(s3h["speed_deg_s"]))
            if len(rows) != 1:
                raise SystemExit(f"stage-1 Fig. 3E finding for {genotype} {polarity}: {len(rows)} rows")
            supplement = marker_category(rec)
            same, how = compare(supplement, rows[0]["amplitude_category"])
            out.append({"repeat_of": "Fig. 3E", "panel": "ST-S3H", "genotype": genotype, "line": s3h["line"],
                        "polarity": polarity, "speed_deg_s": str(s3h["speed_deg_s"]), "condition": stimulus.split()[1],
                        "supplement_category": supplement,
                        "supplement_basis": f"vector paths: {rec['marker']} marker, {rec['against_control']} control"
                                            + ("; centre covered in the image" if rec["centre_covered"] else ""),
                        "stage1_category": rows[0]["amplitude_category"], "stage1_basis": f"finding {rows[0]['row_id']}",
                        "compared": "yes", "same": same, "how": how})
    for genotype, row_id in spec["repeats_s4bd"]["points"].items():
        row = next(r for r in merged1 if r["row_id"] == row_id)
        out.append({"repeat_of": "text (Figs. S4C-D)", "panel": "ST-S4BD", "genotype": genotype, "line": "main",
                    "polarity": "both", "speed_deg_s": "30", "condition": "direction selectivity",
                    "supplement_category": "", "supplement_basis": "histograms tested against shuffled data, not control",
                    "stage1_category": f"ds {row['ds_category']}", "stage1_basis": f"finding {row_id}, from the text",
                    "compared": "no", "same": "", "how": "no category in the supplement: consistent (selectivity remains)"})
    return out


def main() -> None:
    spec = json.loads((ROOT / "settlements.json").read_text())
    data = V.compute()
    units, found = data["units"], data["finding_keyed"]
    tables = {x: {r["row_id"]: r for r in C.read_table(C.STUDY / "extraction" / x / "table-stage2.csv")} for x in "AB"}
    markers = read_markers()
    problems = check_s3h(units, markers)
    if problems:
        sys.exit("Fig. S3H units differ from the vector-path markers: " + "; ".join(problems))
    out, used = [], set()
    for key in sorted(set(found["A"]) | set(found["B"]), key=str):
        a, b = found["A"].get(key), found["B"].get(key)
        k = MF.keystr(key)
        settle, leave = spec["settle"].get(k), spec["left_out"].get(k)
        exp, genotype, polarity, direction, bin_ = key
        if a and b and (a["amplitude"], a["ds"]) == (b["amplitude"], b["ds"]) and a["amplitude"] != "mixed":
            if settle or leave:
                sys.exit(f"{k}: agreed, but settlements.json has an entry for it")
            amplitude, ds, how = a["amplitude"], a["ds"], "agreed"
        elif settle and (a or b):
            base = a or b
            amplitude, ds, how = settle.get("amplitude", base["amplitude"]), settle.get("ds", base["ds"]), "settled: " + settle["reason"]
        elif leave and a and b and a["amplitude"] == b["amplitude"] == "mixed":
            amplitude, ds, how = "mixed", a["ds"], "left out of scoring: " + leave["reason"]
        else:
            sys.exit(f"no settlement for {k}: A={a and (a['amplitude'], a['ds'])} B={b and (b['amplitude'], b['ds'])}")
        if settle or leave:
            used.add(k)
        members = {x: (found[x].get(key) or {"members": []})["members"] for x in "AB"}
        rows = {x: sorted({r for m in members[x] for r in m["row_id"].split(";")}) for x in "AB"}
        src = [tables["A"][r] for r in rows["A"]] + [tables["B"][r] for r in rows["B"]]
        speeds = sorted({m["speed"] for x in "AB" for m in members[x]})
        speed_text = ";".join(f"{s:g}" for s in speeds)
        lines = sorted({m["line"] for x in "AB" for m in members[x]} - {""})
        conditions = sorted({m["condition"] for x in "AB" for m in members[x]} - {""},
                            key=lambda c: float(c.split("%")[0].split()[0]))
        readout = MF.first(src, "readout")
        role, why = role_of(exp, genotype, readout)
        out.append({"experiment": exp, "source": V.SOURCE, "locator": " | ".join(sorted({r["locator"] for r in src}))[:400],
                    "silenced_types": STAGE1_NAME.get(genotype, genotype), "method": MF.first(src, "method"),
                    "readout": readout, "polarity": polarity, "stimulus": MF.first(src, "stimulus"),
                    "speed_deg_s": speed_text, "direction": direction, "measure": MF.first(src, "measure"),
                    "amplitude_category": amplitude, "ds_category": ds, "numeric_value": "", "numeric_unit": "",
                    "speeds": speed_text, "layers": "", "strength_class": "full", "role": role, "score_a": "",
                    "role_reason": why, "origin_A": ";".join(rows["A"]), "origin_B": ";".join(rows["B"]),
                    "settlement": how, "lines": ";".join(lines), "conditions": ";".join(conditions)})
    unused = (set(spec["settle"]) | set(spec["left_out"])) - used
    if unused:
        sys.exit(f"settlements not used: {sorted(unused)}")
    out.sort(key=lambda r: (r["experiment"], r["silenced_types"], r["polarity"], r["direction"], r["speeds"]))
    for i, row in enumerate(out, 1):
        row["row_id"] = f"SM{i:03d}"
    with (ROOT / "supplement-table.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(out)
    merged1 = C.read_table(C.STUDY / "extraction" / "merged-table.csv")
    rep = repeats(units, markers, spec, merged1)
    with (ROOT / "repeats.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rep[0]))
        writer.writeheader()
        writer.writerows(rep)
    roles = Counter(r["role"] for r in out)
    print(f"supplement-table.csv: {len(out)} findings; roles {dict(roles)}; "
          f"settled {sum(r['settlement'].startswith('settled') for r in out)}, "
          f"left out as mixed {sum(r['amplitude_category'] == 'mixed' for r in out)}")
    print(f"Fig. S3H units checked against the vector-path markers: "
          f"{sum(u['experiment'] == 'ST-S3H' for x in 'AB' for u in units[x])}, no differences")
    compared = [r for r in rep if r["compared"] == "yes"]
    print(f"repeats.csv: {len(rep)} points, {len(compared)} compared, {sum(r['same'] == 'yes' for r in compared)} the same")


if __name__ == "__main__":
    main()
