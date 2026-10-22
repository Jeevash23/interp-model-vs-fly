"""Elementary units and findings from the two blind extractions (AMENDMENTS.md, Amendment 1), and their agreement.

  python -B units.py      writes extraction/merge-work/: units-A.csv, units-B.csv, findings-A.csv, findings-B.csv,
                          unit-comparison.csv, finding-comparison.csv and agreement.json

An elementary unit is one experiment, genotype, driver line, polarity, direction and speed. A finding pools the units
of one experiment, genotype, polarity and direction whose speeds fall in the same model-speed bin; its category is
the most common category among its units, and a tie is "mixed".
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict

import common as C

LABELS = ["abolished", "reduced", "unchanged", "increased", "not_reported", "mixed"]
SOURCE = {"ammer": "Ammer 2015", "serbe": "Serbe 2016", "strother": "Strother 2017"}
AMMER_SPEEDS = [6.25, 12.5, 25, 50, 75, 100, 150, 200, 300, 500, 700, 900]
# Speeds of each experiment, from the papers' figures and methods as both extractors recorded them.
SPEEDS = {
    "AM-1EF": [50], "AM-1GH": [50], "AM-2": AMMER_SPEEDS, "AM-3": AMMER_SPEEDS,
    "AM-4": [20, 40, 80, 160, 320, 640],
    "SE-5": ["mean"], "SE-6": ["mean"], "SE-7D": ["mean"], "SE-S4": ["all"], "SE-S5": ["all"], "SE-7C": ["all"],
    "SE-7B": [40],
    "ST-3C": [90], "ST-3E": [90], "ST-4A": [30, 90, 180, 270, 810, 2430], "ST-4B": [30, 90, 180, 270, 810],
    "ST-4C": [30, 60, 90, 180, 270, 540, 810, 1080], "ST-4D": [30, 60, 90, 180, 270, 540, 810, 1080],
    "ST-4E": [90, 180, 270, 540, 810, 1080], "ST-DS": [30],
}
OPPOSING = {"AM-4": "ON", "SE-7B": "OFF", "SE-7C": "OFF", "SE-7D": "OFF"}   # impaired pathway named by the authors
FLIP = {"increased": "reduced", "reduced": "increased", "unchanged": "unchanged", "abolished": "abolished",
        "not_reported": "not_reported"}


def source_of(text: str) -> str:
    t = text.lower()
    return next(v for k, v in SOURCE.items() if k in t)


def experiment(source: str, locator: str) -> str:
    if source == "Strother 2017" and locator.strip().lower().startswith("text"):
        return "ST-DS"
    m = re.search(r"Fig\.?\s*(S?\d+)([A-Z]?)", locator)
    fig, panel = m.group(1), m.group(2)
    if source == "Ammer 2015":
        if fig == "1":
            return "AM-1EF" if panel in ("E", "F") else "AM-1GH"
        return f"AM-{fig}"
    if source == "Serbe 2016":
        return f"SE-7{panel}" if fig == "7" else f"SE-{fig}"
    return f"ST-{fig}{panel}"


def genotype(row: dict, source: str) -> tuple[str, str]:
    text = row["silenced_types"]
    if "T4" in text and "T5" in text:
        return "T4T5", ""
    base = re.split(r"\s*\(", text)[0]
    parts = sorted(p.strip() for p in re.split(r"\s*[+/]\s*", base) if p.strip())
    name = "+".join(parts)
    line = ""
    if source == "Ammer 2015" and name == "Tm3":
        both = text + " " + row["method"]
        line = ("pooled" if "pooled" in both else "a" if "R55D08" in both else "b" if "R59C10" in both
                else "c" if "R13E12" in both else "?")
    return name, line


def speeds_of(row: dict, exp: str) -> list:
    listed = SPEEDS[exp]
    if listed in (["mean"], ["all"]) or len(listed) == 1:
        return listed
    field = row["speed_deg_s"]
    each = re.search(r"each of (\d+)", field)
    if each:
        n = int(each.group(1))
        lo_hi = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", field.split("(")[0])]
        chosen = [s for s in listed if min(lo_hi) <= s <= max(lo_hi)]
        if len(chosen) != n:
            raise ValueError(f"{row['row_id']}: 'each of {n}' does not match the listed speeds {chosen}")
        return chosen
    value = float(re.findall(r"\d+(?:\.\d+)?", field)[0])
    if value not in listed:
        raise ValueError(f"{row['row_id']}: speed {value} not in {exp}'s list")
    return [value]


def bin_of(speed) -> str:
    if speed in ("mean", "all"):
        return "both"
    return "fast" if float(speed) >= C.CONFIG["speed_boundary_deg_s"] else "slow"


def units(letter: str) -> list[dict]:
    out = []
    for row in C.read_table(C.STUDY / "extraction" / letter / "table.csv"):
        source = source_of(row["source"])
        exp = experiment(source, row["locator"])
        name, line = genotype(row, source)
        polarity = {"ON+OFF": "both"}.get(row["polarity"], row["polarity"])
        amplitude, ds = row["amplitude_category"], row["ds_category"]
        if exp in OPPOSING:
            polarity = OPPOSING[exp]
            if letter == "A":
                amplitude = FLIP[amplitude]
        for speed in speeds_of(row, exp):
            out.append({"extractor": letter, "row_id": row["row_id"], "source": source, "experiment": exp,
                        "genotype": name, "line": line, "readout": row["readout"], "polarity": polarity,
                        "direction": row["direction"], "speed": speed, "bin": bin_of(speed),
                        "amplitude": amplitude, "ds": ds})
    return out


def combine(categories: list[str]) -> str:
    counts = Counter(categories)
    top = max(counts.values())
    tied = [c for c, n in counts.items() if n == top]
    return tied[0] if len(tied) == 1 else "mixed"


def keyed(items: list[dict], fields: tuple) -> dict:
    groups = defaultdict(list)
    for item in items:
        groups[tuple(item[f] for f in fields)].append(item)
    out = {}
    for k, members in groups.items():
        out[k] = {"amplitude": combine([m["amplitude"] for m in members]), "ds": combine([m["ds"] for m in members]),
                  "rows": sorted({m["row_id"] for m in members}), "members": members}
    return out


UNIT_KEY = ("experiment", "genotype", "line", "polarity", "direction", "speed")
FINDING_KEY = ("experiment", "genotype", "polarity", "direction", "bin")


def agreement(a: dict, b: dict) -> dict:
    common = sorted(set(a) & set(b), key=str)
    block = {"A": len(a), "B": len(b), "matched": len(common), "A_only": len(set(a) - set(b)),
             "B_only": len(set(b) - set(a))}
    for field in ("amplitude", "ds"):
        x = [a[k][field] for k in common]
        y = [b[k][field] for k in common]
        agree = sum(p == q for p, q in zip(x, y))
        specific = {}
        for label in LABELS:
            both = sum(p == label and q == label for p, q in zip(x, y))
            na, nb = x.count(label), y.count(label)
            if na + nb:
                specific[label] = {"A": na, "B": nb, "both": both, "specific": 2 * both / (na + nb)}
        block[field] = {"agree": agree, "share": agree / len(common) if common else None,
                        "kappa": C.cohen_kappa(x, y, LABELS), "specific": specific,
                        "confusion": dict(Counter(f"{p}|{q}" for p, q in zip(x, y) if p != q))}
    return block


def main() -> None:
    out = C.STUDY / "extraction" / "merge-work"
    out.mkdir(exist_ok=True)
    u = {x: units(x) for x in "AB"}
    unit_keyed = {x: keyed(u[x], UNIT_KEY) for x in "AB"}
    # Findings pool driver lines and speeds within a bin; each finding's category comes from its units' categories.
    finding_keyed = {}
    for x in "AB":
        by_unit = [{**dict(zip(UNIT_KEY, k)), "bin": bin_of(k[-1]), "amplitude": v["amplitude"], "ds": v["ds"],
                    "row_id": ";".join(v["rows"])} for k, v in unit_keyed[x].items()]
        finding_keyed[x] = keyed(by_unit, FINDING_KEY)
    raw = {x: len(C.read_table(C.STUDY / "extraction" / x / "table.csv")) for x in "AB"}
    result = {"raw_rows": raw, "units": agreement(unit_keyed["A"], unit_keyed["B"]),
              "findings": agreement(finding_keyed["A"], finding_keyed["B"])}
    for x in "AB":
        with (out / f"units-{x}.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(u[x][0]))
            w.writeheader()
            w.writerows(u[x])
        with (out / f"findings-{x}.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(list(FINDING_KEY) + ["amplitude", "ds", "units", "rows"])
            for k, v in sorted(finding_keyed[x].items(), key=str):
                w.writerow(list(k) + [v["amplitude"], v["ds"], len(v["members"]),
                                      ";".join(sorted({r for m in v["members"] for r in m["row_id"].split(";")}))])
    for level, data, fields in (("unit", unit_keyed, UNIT_KEY), ("finding", finding_keyed, FINDING_KEY)):
        with (out / f"{level}-comparison.csv").open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(list(fields) + ["A_amplitude", "B_amplitude", "A_ds", "B_ds", "status", "A_rows", "B_rows"])
            for k in sorted(set(data["A"]) | set(data["B"]), key=str):
                a, b = data["A"].get(k), data["B"].get(k)
                if a and b:
                    status = "agree" if (a["amplitude"], a["ds"]) == (b["amplitude"], b["ds"]) else "DISAGREE"
                else:
                    status = "A only" if a else "B only"
                rows_of = lambda v: ";".join(sorted({r for m in v["members"] for r in m["row_id"].split(";")})) if v else ""  # noqa: E731
                w.writerow(list(k) + [a["amplitude"] if a else "", b["amplitude"] if b else "", a["ds"] if a else "",
                                      b["ds"] if b else "", status, rows_of(a), rows_of(b)])
    (out / "agreement.json").write_text(json.dumps(result, indent=1) + "\n")
    for level in ("units", "findings"):
        r = result[level]
        print(f"{level}: A {r['A']}, B {r['B']}, matched {r['matched']}, A only {r['A_only']}, B only {r['B_only']}; "
              f"amplitude {r['amplitude']['agree']}/{r['matched']} kappa {r['amplitude']['kappa']}; "
              f"ds {r['ds']['agree']}/{r['matched']} kappa {r['ds']['kappa']}")


if __name__ == "__main__":
    main()
