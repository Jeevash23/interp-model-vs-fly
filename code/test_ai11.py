"""Unit tests for AI-11's matching and scoring (toy tables and the development set only).

  python -B test_ai11.py
"""
from __future__ import annotations

import json
import math
import sys

import common as C


def approx(a, b, tol=1e-9):
    return abs(a - b) <= tol


def test_categories():
    d = 0.2
    assert C.category(0.0, d) == "abolished"
    assert C.category(0.1, d) == "abolished"
    assert C.category(0.1000001, d) == "reduced"
    assert C.category(0.7999999, d) == "reduced"
    assert C.category(0.8, d) == "unchanged"
    assert C.category(1.2, d) == "unchanged"
    assert C.category(1.2000001, d) == "increased"
    assert C.category(-3.0, d) == "abolished"


def test_speeds():
    assert C.model_speed_keys("12.5") == [C.SLOW]
    assert C.model_speed_keys("55.0") == [C.SLOW]
    assert C.model_speed_keys("55.1") == [C.FAST]
    assert C.model_speed_keys("300") == [C.FAST]
    assert C.model_speed_keys("all") == [C.SLOW, C.FAST]
    assert C.model_speed_keys("mean") == [C.SLOW, C.FAST]
    assert C.model_speed_keys("") == [C.SLOW, C.FAST]
    assert C.model_speed_keys("12.5;300") == [C.SLOW, C.FAST]
    assert C.model_speed_keys("6.25;12.5;25;50") == [C.SLOW]


def row(**kw):
    base = {"row_id": "x", "source": "s", "silenced_types": "Mi1", "readout": "LPTC_voltage_pooled", "polarity": "ON",
            "direction": "PD", "speeds": "all", "layers": "", "role": "primary",
            "amplitude_category": "reduced", "ds_category": "not_reported"}
    base.update(kw)
    return base


def test_mapping():
    assert C.subtype_sets(row(readout="HS_voltage"), "amplitude") == {"ON": "a"}
    assert C.subtype_sets(row(readout="HS_voltage", direction="ND"), "amplitude") == {"ON": "b"}
    assert C.subtype_sets(row(readout="VS_voltage", polarity="OFF", direction="both"), "amplitude") == {"OFF": "cd"}
    assert C.subtype_sets(row(direction="PD"), "amplitude") == {"ON": "ad"}
    assert C.subtype_sets(row(direction="ND"), "amplitude") == {"ON": "bc"}
    assert C.subtype_sets(row(polarity="both", direction="both"), "amplitude") == {"ON": "abcd", "OFF": "abcd"}
    assert C.subtype_sets(row(readout="T4_calcium"), "amplitude") == {"ON": "abcd"}
    assert C.subtype_sets(row(readout="T4_calcium", layers="c"), "amplitude") == {"ON": "c"}
    assert C.subtype_sets(row(readout="T4_calcium", direction="ND"), "amplitude") is None
    assert C.subtype_sets(row(readout="T4_calcium", direction="ND"), "ds") == {"ON": "abcd"}
    assert C.subtype_sets(row(readout="T4_calcium", polarity="OFF"), "amplitude") is None
    assert C.subtype_sets(row(readout="T4_calcium", polarity="both"), "amplitude") == {"ON": "abcd"}
    assert C.subtype_sets(row(readout="T5_calcium", polarity="both", direction="both"), "ds") == {"OFF": "abcd"}
    assert C.subtype_sets(row(readout="T5_voltage", polarity="OFF", layers="a;b"), "amplitude") == {"OFF": "ab"}
    assert C.subtype_sets(row(readout="HS_voltage"), "ds") == {"ON": "a"}
    assert C.subtype_sets(row(readout="behaviour"), "ds") is None
    assert C.subtype_sets(row(readout="behaviour", direction="both", polarity="OFF"), "amplitude") == {"OFF": "ab"}
    assert C.subtype_sets(row(readout="unknown"), "amplitude") is None
    assert C.model_cell(row(silenced_types="Tm1+Tm2")) is None
    assert C.model_cell(row(silenced_types="CT1")) is None
    assert C.model_cell(row(silenced_types="Tm9")) == "Tm9"


def test_comparisons():
    table = [row(row_id="r1", ds_category="reduced", readout="T4_calcium"),
             row(row_id="r2", amplitude_category="not_reported"),
             row(row_id="r3", silenced_types="Tm1+Tm2", role="pair"),
             row(row_id="r4", readout="T4_calcium", direction="ND")]
    comps = C.comparisons(table)
    ids = [(c["row_id"], c["measure"], c["matched"]) for c in comps]
    assert all(c["strength_class"] == "full" for c in comps)
    assert ids == [("r1", "amplitude", True), ("r1", "ds", True), ("r4", "amplitude", False)], ids


def toy_effects():
    e = {}
    def put(model, stim, readout, cell, ratio, base=0.5, exact=0.0, pred=0.0, abolished=False):
        e[(model, stim, 1.0, readout, cell)] = {"ratio": ratio, "baseline_dsi": base, "exact": None if abolished else exact,
                                                "prediction": pred, "abolished": abolished, "defined": not abolished}
    for stim in (C.SLOW, C.FAST):
        put("m1", stim, "T4a", "Mi1", 0.5, base=0.5, exact=-0.25, pred=-0.4)
        put("m1", stim, "T4d", "Mi1", 1.5, base=0.1, exact=0.05, pred=0.0)
        put("m1", stim, "T4b", "Mi1", None, base=0.0)
        put("m1", stim, "T4c", "Mi1", 0.0, base=0.6, abolished=True, pred=-0.1)
    return e


def test_values():
    e = toy_effects()
    comp = {"cell": "Mi1", "sets": {"ON": "ad"}, "stimuli": [C.SLOW, C.FAST]}
    assert approx(C.amplitude_value(e, "m1", comp, 1.0, "mean"), 1.0)
    comp_b = {"cell": "Mi1", "sets": {"ON": "b"}, "stimuli": [C.SLOW]}
    assert C.amplitude_value(e, "m1", comp_b, 1.0) is None
    # DS: T4d is below the 0.2 baseline floor, T4c abolished counts as 0, T4a gives 0.25/0.5.
    comp_ds = {"cell": "Mi1", "sets": {"ON": "acd"}, "stimuli": [C.SLOW]}
    assert approx(C.ds_value(e, "m1", comp_ds, 1.0), (0.5 + 0.0) / 2)
    assert approx(C.ds_value(e, "m1", comp_ds, 1.0, "prediction"), ((0.5 - 0.4) / 0.5 + (0.6 - 0.1) / 0.6) / 2)


def test_ensemble():
    out = C.ensemble([0.5, 0.5, 1.0, None], 0.2)
    assert out["category"] == "reduced" and approx(out["share"], 2 / 3) and out["n_models"] == 3
    tie = C.ensemble([0.5, 0.7, 1.0, 1.1], 0.2)     # 2 reduced, 2 unchanged; median 0.85 is unchanged
    assert tie["category"] == "unchanged" and tie["share"] == 0.5
    assert C.ensemble([None], 0.2)["category"] is None


def test_statistics():
    assert C.cohen_kappa(["a", "b", "a"], ["a", "b", "a"], ["a", "b"]) == 1.0
    # Textbook example: 2x2 with 20 yes-yes, 5 yes-no, 10 no-yes, 15 no-no; kappa = 0.4.
    a = ["y"] * 25 + ["n"] * 25
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    assert approx(C.cohen_kappa(a, b, ["y", "n"]), 0.4)
    low, high = C.clopper_pearson(5, 10)
    assert approx(low, 0.18708602844739, 1e-9) and approx(high, 0.81291397155261, 1e-9)
    assert C.clopper_pearson(0, 8)[0] == 0.0 and C.clopper_pearson(8, 8)[1] == 1.0
    s = C.spearman_exact([1, 2, 3, 4], [10, 20, 30, 40])
    assert approx(s["rho"], 1.0) and approx(s["p_one_sided"], 1 / 24)
    s = C.spearman_exact([1, 2, 3, 4], [40, 30, 20, 10])
    assert approx(s["rho"], -1.0) and approx(s["p_one_sided"], 1.0)
    p = C.kappa_permutation(["a", "b"] * 10, ["a", "b"] * 10, ["a", "b"], 2000, 1)
    assert 0 < p < 0.01
    m = C.mcnemar_exact([True, True, False, True], [False, True, False, False])
    assert m["first_only"] == 2 and m["second_only"] == 0 and approx(m["p_two_sided"], 0.5)
    assert approx(C.sign_test(10, 10), 2 * 0.5**10)


def test_connectivity():
    names, s_sum, reach = C.signed_paths()
    i, j = names.index("T4c"), names.index("Mi1")
    assert s_sum[i, j] > 0 and reach[i, j]
    comp = {"matched": True, "measure": "amplitude", "cell": "Mi1", "sets": {"ON": "abcd"}}
    assert C.connectivity_category(comp) == "reduced"
    assert C.connectivity_category({**comp, "measure": "ds"}) is None
    # The photoreceptors are histaminergic: R1-R6 inhibit L1 in the connectome, so W is negative there.
    k, r1 = names.index("L1"), names.index("R1")
    assert s_sum[k, r1] < 0


def test_development_scoring():
    import score
    summary = score.main("development")
    assert summary["models"] == sorted(C.CONFIG["development_models"])
    assert summary["primary"]["all"]["n"] == 8
    assert summary["counts"]["rows_by_role"] == {"pair": 1, "primary": 8}


def test_confirmation_locked():
    import freeze
    if (C.STUDY / "FREEZE.json").exists():
        return
    try:
        freeze.check()
    except SystemExit as exc:
        assert "locked" in str(exc)
    else:
        raise AssertionError("confirmation set not locked before the freeze")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"ok    {test.__name__}")
        except Exception as exc:   # noqa: BLE001
            failed += 1
            print(f"FAIL  {test.__name__}: {exc!r}")
    print(f"{len(tests) - failed} of {len(tests)} tests pass")
    sys.exit(1 if failed else 0)
