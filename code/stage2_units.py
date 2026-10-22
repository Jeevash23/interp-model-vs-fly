"""Stage 2, Part 2: elementary units and findings from the two blind extractions of Strother's supplement
(STAGE2-AMENDMENTS.md, S4), and their agreement.

  python -B stage2_units.py      writes extraction/stage2/merge-work/: units-A.csv, units-B.csv, findings-A.csv,
                                 findings-B.csv, unit-comparison.csv, finding-comparison.csv and agreement.json

Stage 1's rules (code/units.py, imported unchanged) with S4's additions: one experiment per supplementary panel, the
stimulus condition (contrast or OFF reset) as part of the unit, and repeats of stage-1 conditions kept in the agreement
but left out of the findings.
"""
from __future__ import annotations

import csv
import json
import re

import common as C
import units as U

STAGE2 = C.STUDY / "extraction" / "stage2"
SOURCE = "Strother 2017"
# Speeds of each panel, from the article's methods (p. e5-e6); S3D-E speeds are temporal frequency x spatial period.
SPEEDS = {
    "ST-S2B": [30], "ST-S3A": [30], "ST-S3B": [270], "ST-S3C": [30, 90, 180, 270, 810],
    "ST-S3D": [15, 22.5, 30, 60], "ST-S3E": [135, 202.5, 270, 540],
    "ST-S3F": [30, 60, 90, 180, 270, 540, 810, 1080], "ST-S3G": [30, 60, 90, 180, 270, 540, 810, 1080],
    "ST-S3H": [30, 90, 270], "ST-S4A": [90, 540],
}
CONTRAST_PANELS = {"ST-S3A", "ST-S3B", "ST-S3H"}           # panels that vary contrast at a fixed speed
UNIT_KEY = ("experiment", "genotype", "line", "polarity", "direction", "speed", "condition")
FINDING_KEY = U.FINDING_KEY


def panels(locator: str) -> list[str]:
    found = [f"ST-S{figure}" for figure in re.findall(r"Fig\.?\s*S(\d[A-H])", locator)]
    if not found:
        raise ValueError(f"no supplementary panel in locator: {locator[:60]}")
    return list(dict.fromkeys(found))


def speeds_of(row: dict, exp: str) -> list[float]:
    listed = SPEEDS[exp]
    field = row["speed_deg_s"]
    values = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", field.split("(")[0])]
    each = re.search(r"each of (\d+)", field)
    if each:
        chosen = [s for s in listed if min(values) <= s <= max(values)]
        if len(chosen) != int(each.group(1)):
            raise ValueError(f"{row['row_id']}: 'each of {each.group(1)}' does not match {exp}'s speeds {chosen}")
        return chosen
    if not values or any(v not in listed for v in values):
        raise ValueError(f"{row['row_id']}: speeds {values} not all in {exp}'s list {listed}")
    return values                                             # one speed, or a list such as "30 and 270 (each)"


def conditions_of(row: dict, exp: str) -> list[str]:
    text = row["stimulus"]
    if exp in CONTRAST_PANELS:
        listed = re.search(r"contrast\s+([\d.,\sand]+)%\s*\(each\)", text)
        if listed:
            return [f"{float(v):g}%" for v in re.findall(r"\d+(?:\.\d+)?", listed.group(1))]
        single = set(re.findall(r"(\d+(?:\.\d+)?)%\s*(?:Michelson\s+)?contrast", text))
        if len(single) != 1:
            raise ValueError(f"{row['row_id']}: contrast not found in '{text[:80]}'")
        return [f"{float(single.pop()):g}%"]
    if exp == "ST-S4A":
        listed = re.search(r"lasting\s+([\d,\sor]+)\s*ms\s*\(each\)", text)
        if listed:
            return [f"{v} ms" for v in re.findall(r"\d+", listed.group(1))]
        single = set(re.findall(r"(\d+)\s*ms\s+OFF", text))
        if len(single) != 1:
            raise ValueError(f"{row['row_id']}: OFF reset not found in '{text[:80]}'")
        return [f"{single.pop()} ms"]
    return [""]


def line_of(row: dict, exp: str, name: str) -> str:
    """Driver line in Fig. S3H ('1' or '2'); one line elsewhere. A names it in `method`, B in `silenced_types`."""
    if exp != "ST-S3H":
        return ""
    found = set(re.findall(rf"via split-GAL4 line {name}-([12])\b", row["method"]))
    found |= set(re.findall(rf"'{name}-([12])'", row["silenced_types"]))
    if len(found) != 1:
        raise ValueError(f"{row['row_id']}: driver line of {name} not found")
    return found.pop()


def repeat_of(unit: dict) -> str:
    """S4 rule 5: points that repeat a stage-1 condition."""
    if unit["experiment"] in ("ST-S3A", "ST-S3B") and unit["condition"] == "100%":
        return "Fig. 4B"
    if (unit["experiment"] == "ST-S3H" and unit["line"] == "1" and unit["speed"] == 90
            and (unit["polarity"], unit["condition"]) in (("ON", "44%"), ("OFF", "43%"))):
        return "Fig. 3E"
    return ""


def units(letter: str) -> list[dict]:
    out = []
    for row in C.read_table(C.STUDY / "extraction" / letter / "table-stage2.csv"):
        name, _ = U.genotype(row, SOURCE)
        polarity = {"ON+OFF": "both"}.get(row["polarity"], row["polarity"])
        for exp in panels(row["locator"]):
            line = line_of(row, exp, name)
            for speed in speeds_of(row, exp):
                for condition in conditions_of(row, exp):
                    unit = {"extractor": letter, "row_id": row["row_id"], "source": SOURCE, "experiment": exp,
                            "genotype": name, "line": line, "readout": row["readout"], "polarity": polarity,
                            "direction": row["direction"], "speed": speed, "condition": condition,
                            "bin": U.bin_of(speed), "amplitude": row["amplitude_category"], "ds": row["ds_category"]}
                    unit["repeat"] = repeat_of(unit)
                    out.append(unit)
    return out


def findings(unit_keyed: dict) -> dict:
    """Findings pool units (not repeats) of one experiment, genotype, polarity and direction within a speed bin."""
    by_unit = []
    for k, v in unit_keyed.items():
        if v["members"][0]["repeat"]:
            continue
        by_unit.append({**dict(zip(UNIT_KEY, k)), "bin": U.bin_of(k[UNIT_KEY.index("speed")]),
                        "amplitude": v["amplitude"], "ds": v["ds"], "row_id": ";".join(v["rows"])})
    return U.keyed(by_unit, FINDING_KEY)


def compute() -> dict:
    u = {x: units(x) for x in "AB"}
    unit_keyed = {x: U.keyed(u[x], UNIT_KEY) for x in "AB"}
    finding_keyed = {x: findings(unit_keyed[x]) for x in "AB"}
    return {"units": u, "unit_keyed": unit_keyed, "finding_keyed": finding_keyed}


def rows_of(value: dict | None) -> str:
    if not value:
        return ""
    return ";".join(sorted({r for m in value["members"] for r in m["row_id"].split(";")}))


def main() -> None:
    out = STAGE2 / "merge-work"
    out.mkdir(parents=True, exist_ok=True)
    data = compute()
    u, unit_keyed, finding_keyed = data["units"], data["unit_keyed"], data["finding_keyed"]
    raw = {x: len(C.read_table(C.STUDY / "extraction" / x / "table-stage2.csv")) for x in "AB"}
    result = {"raw_rows": raw, "units": U.agreement(unit_keyed["A"], unit_keyed["B"]),
              "findings": U.agreement(finding_keyed["A"], finding_keyed["B"]),
              "repeat_units": {x: sum(1 for v in unit_keyed[x].values() if v["members"][0]["repeat"]) for x in "AB"}}
    for x in "AB":
        with (out / f"units-{x}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(u[x][0]))
            w.writeheader()
            w.writerows(u[x])
        with (out / f"findings-{x}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(list(FINDING_KEY) + ["amplitude", "ds", "units", "rows"])
            for k, v in sorted(finding_keyed[x].items(), key=str):
                w.writerow(list(k) + [v["amplitude"], v["ds"], len(v["members"]), rows_of(v)])
    for level, data_, fields in (("unit", unit_keyed, UNIT_KEY), ("finding", finding_keyed, FINDING_KEY)):
        with (out / f"{level}-comparison.csv").open("w", newline="") as f:
            w = csv.writer(f)
            extra = ["repeat"] if level == "unit" else []
            w.writerow(list(fields) + ["A_amplitude", "B_amplitude", "A_ds", "B_ds", "status", "A_rows", "B_rows"] + extra)
            for k in sorted(set(data_["A"]) | set(data_["B"]), key=str):
                a, b = data_["A"].get(k), data_["B"].get(k)
                if a and b:
                    status = "agree" if (a["amplitude"], a["ds"]) == (b["amplitude"], b["ds"]) else "DISAGREE"
                else:
                    status = "A only" if a else "B only"
                tail = [(a or b)["members"][0]["repeat"]] if level == "unit" else []
                w.writerow(list(k) + [a["amplitude"] if a else "", b["amplitude"] if b else "", a["ds"] if a else "",
                                      b["ds"] if b else "", status, rows_of(a), rows_of(b)] + tail)
    (out / "agreement.json").write_text(json.dumps(result, indent=1) + "\n")
    for level in ("units", "findings"):
        r = result[level]
        print(f"{level}: A {r['A']}, B {r['B']}, matched {r['matched']}, A only {r['A_only']}, B only {r['B_only']}; "
              f"amplitude {r['amplitude']['agree']}/{r['matched']} kappa {r['amplitude']['kappa']}")
    print("repeat units:", result["repeat_units"])


if __name__ == "__main__":
    main()
