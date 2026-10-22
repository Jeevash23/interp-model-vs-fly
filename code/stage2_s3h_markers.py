"""Read the markers of Strother's Fig. S3H from the supplement's vector paths (STAGE2-AMENDMENTS.md, S4 rule 7).

  python3 -I stage2_s3h_markers.py      writes extraction/stage2/merge-work/s3h-markers.csv

In the image some markers of one driver line are covered by the other line's marker. The PDF stores every marker as
its own path, so each one's fill can be read. The page is converted with pdftocairo into a temporary folder; each
circle (a path of four Bezier curves) gives its centre, fill and stroke. A filled circle is significant and an open
one is not (legend, supplement p. 8). "above" or "below" compares the marker with the control's marker at the same
point (empty split-GAL4, black); higher on the page is more turning. A marker's centre is "covered" when a marker of
the other line, drawn later, contains that centre. Only the standard library and poppler's pdftocairo are used.
"""
import csv
import math
import re
import subprocess
import tempfile
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
PDF = STUDY / "sources/strother-2017-supplement.pdf"
OUT = STUDY / "extraction/stage2/merge-work/s3h-markers.csv"
PAGE = 7
# Stroke colours of the eight lines, as in the S3H legend (main lines in the colours of panels A-G).
LINES = {"70.22": "Mi1-1", "93.34": "Mi1-2", "94.25": "Tm3-1", "97.73": "Tm3-2", "24.87": "Mi4-1", "36.13": "Mi4-2",
         "30.99": "Mi9-1", "39.20": "Mi9-2", "13.72": "control"}
COLUMNS = [("OFF 43%", [204.26, 227.03, 248.90]), ("ON 29%", [266.47, 289.35, 311.10]),
           ("ON 38%", [331.22, 353.99, 375.80]), ("ON 44%", [397.42, 420.19, 442.06])]
SPEEDS = [30, 90, 270]                                   # 0.4, 1.3 and 4.0 Hz in 67.5-degree windows
ROWS = {"Mi1": (515, 565), "Tm3": (565, 615), "Mi4": (615, 660), "Mi9": (660, 700)}


def colour_key(value):
    if not value or value == "none":
        return None
    first = re.findall(r"[\d.]+", value)[0]
    return "white" if value.startswith("rgb(100%") else first[:5]


def circles(svg: str):
    body = svg.split("</defs>", 1)[1]
    for order, m in enumerate(re.finditer(r"<path ([^>]*)/>", body)):
        attrs = m.group(1)
        path = re.search(r'\bd="([^"]*)"', attrs).group(1)
        if path.count("C") != 4:
            continue
        nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", path)]
        xs, ys = nums[0::2], nums[1::2]
        t = re.search(r'transform="matrix\(([^)]*)\)"', attrs)
        a, b, c, d, e, f = [float(x) for x in t.group(1).split(",")] if t else (1, 0, 0, 1, 0, 0)
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        fill = re.search(r'\bfill="([^"]*)"', attrs)
        stroke = re.search(r'\bstroke="([^"]*)"', attrs)
        yield {"x": a * cx + c * cy + e, "y": b * cx + d * cy + f, "r": (max(xs) - min(xs)) / 2, "order": order,
               "fill": colour_key(fill.group(1)) if fill else None,
               "stroke": colour_key(stroke.group(1)) if stroke else None}


def main():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "page.svg"
        subprocess.run(["pdftocairo", "-svg", "-f", str(PAGE), "-l", str(PAGE), str(PDF), str(target)], check=True)
        svg = target.read_text()
    marks = []
    for c in circles(svg):
        series = LINES.get(c["stroke"]) or LINES.get(c["fill"])
        column = next(((name, i) for name, xs in COLUMNS for i, x in enumerate(xs) if abs(c["x"] - x) < 0.5), None)
        row = next((t for t, (lo, hi) in ROWS.items() if lo <= c["y"] < hi), None)
        if series is None or column is None or row is None:
            continue
        if series == "control" and c["fill"] is None:
            continue                                      # the control's outline, drawn over its filled marker
        if series != "control" and not series.startswith(row):
            continue
        marks.append({**c, "series": series, "stimulus": column[0], "speed": SPEEDS[column[1]], "type": row})
    control = {(m["type"], m["stimulus"], m["speed"]): m["y"] for m in marks if m["series"] == "control"}
    rows = []
    for m in sorted((m for m in marks if m["series"] != "control"), key=lambda m: (m["series"], m["stimulus"], m["speed"])):
        covered = any(o["series"] != m["series"] and o["series"] != "control" and o["order"] > m["order"]
                      and math.hypot(o["x"] - m["x"], o["y"] - m["y"]) < o["r"] for o in marks)
        ref = control[(m["type"], m["stimulus"], m["speed"])]
        rows.append({"line": m["series"], "stimulus": m["stimulus"], "speed_deg_s": m["speed"],
                     "marker": "open" if m["fill"] == "white" else "filled",
                     "against_control": "above" if m["y"] < ref else "below", "centre_covered": "yes" if covered else "",
                     "y_pt": f"{m['y']:.2f}", "control_y_pt": f"{ref:.2f}"})
    if len(rows) != 96:
        raise SystemExit(f"expected 96 line markers (8 lines x 4 stimuli x 3 speeds), found {len(rows)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{OUT.relative_to(STUDY)}: {len(rows)} markers, {sum(r['marker'] == 'filled' for r in rows)} filled, "
          f"{sum(r['centre_covered'] == 'yes' for r in rows)} with the centre covered by the other line's marker")


if __name__ == "__main__":
    main()
