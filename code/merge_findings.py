"""Build the merged experimental table of findings (AMENDMENTS.md, Amendment 1).

  python -B merge_findings.py     writes extraction/merged-table.csv

Every finding both extractors recorded with the same categories is taken as agreed. Every other finding needs an
entry in extraction/merge-work/settlements.json (settled against the source text), or is a direction-specific
grating finding covered by the S5 rule there; anything else stops the build. Roles, strength classes and the
score (a) flag follow Amendment 1.4.
"""
from __future__ import annotations

import csv
import json
import sys

import common as C
import units as U

COLUMNS = ["row_id", "experiment", "source", "locator", "silenced_types", "method", "readout", "polarity", "stimulus",
           "speed_deg_s", "direction", "measure", "amplitude_category", "ds_category", "numeric_value",
           "numeric_unit", "speeds", "layers", "strength_class", "role", "score_a", "role_reason", "origin_A",
           "origin_B", "settlement"]
ONE_COPY = {"SE-6", "SE-7B", "SE-7C", "SE-7D"}


def keystr(key) -> str:
    return "|".join(str(k) for k in key)


def role_of(exp: str, genotype: str, readout: str) -> tuple[str, str]:
    if "+" in genotype:
        return "pair", "pair block: AI-06 simulated pairs only in the development models"
    if genotype == "T4T5":
        return "excluded", "T4 and T5 silenced together: no confirmation counterpart"
    if exp == "AM-1GH":
        return "excluded", "contrast series: the model's edges are at full contrast (Amendment 1.4)"
    if readout == "behaviour":
        return "behaviour", "behaviour: secondary score (h)"
    if exp in ONE_COPY:
        return "partial", "one-copy shibire single block: secondary score (g), half strength"
    return "primary", ""


def first(rows: list[dict], field: str) -> str:
    return next((r[field] for r in rows if r.get(field)), "")


def main() -> None:
    root = C.STUDY / "extraction"
    spec = json.loads((root / "merge-work" / "settlements.json").read_text())
    tables = {x: {r["row_id"]: r for r in C.read_table(root / x / "table.csv")} for x in "AB"}
    found = {}
    for x in "AB":
        unit_keyed = U.keyed(U.units(x), U.UNIT_KEY)
        by_unit = [{**dict(zip(U.UNIT_KEY, k)), "bin": U.bin_of(k[-1]), "amplitude": v["amplitude"], "ds": v["ds"],
                    "row_id": ";".join(v["rows"])} for k, v in unit_keyed.items()]
        found[x] = U.keyed(by_unit, U.FINDING_KEY)
    out, used = [], set()
    for key in sorted(set(found["A"]) | set(found["B"]), key=str):
        a, b = found["A"].get(key), found["B"].get(key)
        k = keystr(key)
        settle = spec["settle"].get(k)
        exp, genotype, polarity, direction, bin_ = key
        if a and b and (a["amplitude"], a["ds"]) == (b["amplitude"], b["ds"]) and a["amplitude"] != "mixed":
            amplitude, ds, how = a["amplitude"], a["ds"], "agreed"
            if settle:
                amplitude, ds = settle.get("amplitude", amplitude), settle.get("ds", ds)
                how = "agreed; settled: " + settle["reason"]
        elif settle and (a or b):
            base = a or b
            amplitude, ds = settle.get("amplitude", base["amplitude"]), settle.get("ds", base["ds"])
            how = "settled: " + settle["reason"]
        elif exp == "SE-S5" and direction in ("PD", "ND") and b and not a:
            continue                                              # the S5 rule: one finding per genotype
        elif exp == "SE-S5" and direction == "both" and a and not b:
            amplitude, ds, how = a["amplitude"], a["ds"], "settled: " + spec["s5_rule"]["reason"]
        else:
            sys.exit(f"no settlement for {k}: A={a and (a['amplitude'], a['ds'])} B={b and (b['amplitude'], b['ds'])}")
        if settle:
            used.add(k)
        rows = {x: sorted({r for m in (found[x].get(key) or {"members": []})["members"] for r in m["row_id"].split(";")})
                for x in "AB"}
        src = [tables["A"][r] for r in rows["A"]] + [tables["B"][r] for r in rows["B"]]
        speeds = sorted({m["speed"] for x in "AB" for m in (found[x].get(key) or {"members": []})["members"]},
                        key=lambda s: (isinstance(s, str), s if not isinstance(s, str) else 0))
        speed_text = speeds[0] if speeds and isinstance(speeds[0], str) else ";".join(f"{s:g}" for s in speeds)
        readout = first(src, "readout")
        role, why = role_of(exp, genotype, readout)
        values = {r["numeric_value"].split()[0] for r in src if r["numeric_value"].strip()}
        if len(values) > 1 and not all(abs(float(v) - float(min(values))) < 0.011 for v in values):
            sys.exit(f"{k}: printed values differ between rows: {values}")
        numeric = sorted(values, key=len)[-1] if values else ""
        out.append({"experiment": exp, "source": first(src, "source") and U.source_of(first(src, "source")),
                    "locator": " | ".join(sorted({r["locator"] for r in src}))[:400],
                    "silenced_types": "T4a-d+T5a-d" if genotype == "T4T5" else genotype,
                    "method": first(src, "method"), "readout": readout, "polarity": polarity,
                    "stimulus": first(src, "stimulus"), "speed_deg_s": speed_text, "direction": direction,
                    "measure": first(src, "measure"), "amplitude_category": amplitude, "ds_category": ds,
                    "numeric_value": numeric, "numeric_unit": "% of control" if numeric else "", "speeds": speed_text,
                    "layers": "", "strength_class": "partial" if exp in ONE_COPY else "full", "role": role,
                    "score_a": "1" if exp == "SE-5" and polarity == "OFF" and "+" not in genotype else "",
                    "role_reason": why, "origin_A": ";".join(rows["A"]), "origin_B": ";".join(rows["B"]),
                    "settlement": how})
    for item in spec["add"]:
        exp, genotype, polarity, direction, bin_ = item["key"].split("|")
        out.append({"experiment": exp, "source": "Ammer 2015", "locator": "text, Ammer PDF p. 48 (Figs. 2-3)",
                    "silenced_types": genotype, "method": "Kir2.1 (10xUAS-Kir2.1-EGFP)", "readout": "LPTC_voltage_pooled",
                    "polarity": polarity, "stimulus": "single OFF edges, PD and ND, 12 speeds", "speed_deg_s": "all",
                    "direction": direction, "measure": "directional tuning of OFF responses (authors' statement)",
                    "amplitude_category": item["amplitude"], "ds_category": item["ds"], "numeric_value": "",
                    "numeric_unit": "", "speeds": item["speeds"], "layers": "", "strength_class": "full",
                    "role": "primary", "score_a": "", "role_reason": "", "origin_A": item["rows_A"],
                    "origin_B": item["rows_B"], "settlement": "added: " + item["reason"]})
        used.add(item["key"])
    unused = set(spec["settle"]) - used
    if unused:
        sys.exit(f"settlements not used: {sorted(unused)}")
    order = {"Ammer 2015": 0, "Serbe 2016": 1, "Strother 2017": 2}
    out.sort(key=lambda r: (order[r["source"]], r["experiment"], r["silenced_types"], r["polarity"], r["direction"],
                            r["speeds"]))
    for i, row in enumerate(out, 1):
        row["row_id"] = f"M{i:03d}"
    with (root / "merged-table.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(out)
    from collections import Counter
    print(f"merged-table.csv: {len(out)} findings; roles {dict(Counter(r['role'] for r in out))}; "
          f"settled {sum(r['settlement'] != 'agreed' for r in out)}")


if __name__ == "__main__":
    main()
