import copy
import importlib.util
import json
from pathlib import Path

import pytest
from catalogmesh.evaluation import summarize

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_eval", ROOT / "scripts/check_eval.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def baseline():
    return json.loads((ROOT / "evals/baseline.json").read_text())


def test_all_72_evaluation_decisions_are_reproducible_from_saved_inputs():
    report = baseline()
    assert check.verify(report)["decisions"] == 72


@pytest.mark.parametrize("mutation", ["drop", "duplicate", "label", "response", "metric"])
def test_eval_integrity_detects_tampering(mutation):
    report = baseline()
    if mutation == "drop":
        report["rows"].pop()
    elif mutation == "duplicate":
        report["rows"][-1] = copy.deepcopy(report["rows"][0])
    elif mutation == "label":
        report["rows"][0]["expected_id"] = "unmatched"
    elif mutation == "response":
        report["rows"][0]["category_id"] = "unmatched"
    else:
        report["summary"]["accuracy"] = 1.0
    with pytest.raises(ValueError):
        check.verify(report)


def test_failed_predictions_stay_in_metric_denominator():
    report = baseline()
    rows = copy.deepcopy(report["rows"])
    for row in rows:
        row["error"] = "Upstream unavailable"
    result = summarize(rows, report["policy"])
    assert result["accuracy"] == 0
    assert result["decisions"] == 72
    assert result["gates"]["no_execution_errors"] is False


def test_case_level_regression_is_detected_even_if_aggregate_accuracy_is_unchanged():
    before = baseline()
    after = copy.deepcopy(before)
    good = next(
        r
        for r in after["rows"]
        if r["category_id"] == r["expected_id"] and r["expected_id"] != "unmatched"
    )
    bad = next(r for r in after["rows"] if r["category_id"] != r["expected_id"])
    good["category_id"] = "unmatched"
    bad["category_id"] = bad["expected_id"]
    assert len(check.regressions(after, before)) == 1


def test_demo_and_regression_titles_are_disjoint_and_groups_are_explicit():
    report = baseline()
    showcase = json.loads((ROOT / "recordings/showcase.json").read_text())
    assert not {r["product"]["title"] for r in report["rows"]} & {
        r["product"]["title"] for r in showcase["rows"]
    }
    assert all(r["group"] and r["slice"] for r in report["rows"])
