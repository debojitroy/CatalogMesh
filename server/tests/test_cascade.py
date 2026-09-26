import copy
import json
from pathlib import Path

import pytest
from catalogmesh.cascade import (
    accept_laya,
    bedrock_request,
    summarize_cascade,
    validate_bedrock,
    verify_cascade,
)
from catalogmesh.fixtures import demo_catalog

ROOT = Path(__file__).resolve().parents[2]


def protocol():
    return json.loads((ROOT / "evals/cascade/protocol.json").read_text())


def test_routing_never_accepts_errors_unmatched_or_invalid_scores():
    assert accept_laya({"category_id": "H-101", "selected_probability": 0.95}, 0.95)
    for score in (0.9499, True, None, float("nan"), float("inf"), 1.1):
        assert not accept_laya({"category_id": "H-101", "selected_probability": score}, 0.95)
    assert not accept_laya({"category_id": "unmatched", "selected_probability": 0.99}, 0.95)
    assert not accept_laya(
        {"category_id": "H-101", "selected_probability": 0.99, "error": "Timeout"}, 0.95
    )


def test_bedrock_gets_all_categories_and_no_annotations_or_laya_prediction():
    suppliers, markets, _ = demo_catalog()
    product = {**suppliers[0]["products"][0], "expected": "SECRET", "laya": "SECRET"}
    request = bedrock_request(product, markets[0], protocol())
    serialized = json.dumps(request)
    assert "SECRET" not in serialized
    assert "expected" not in serialized
    payload = json.loads(request["messages"][0]["content"][0]["text"])
    assert payload["destination"]["categories"] == markets[0]["categories"]


def response(category="H-101", status="mapped"):
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "name": "map_product",
                            "input": {
                                "category_id": category,
                                "status": status,
                                "evidence": "Two complete wireless earpieces are supplied.",
                            },
                        }
                    }
                ]
            }
        },
    }


@pytest.mark.parametrize(
    ("category", "status"),
    [("invented", "mapped"), ("unmatched", "mapped"), ("H-101", "no_match")],
)
def test_invalid_bedrock_category_and_status_cannot_count_as_a_valid_decision(category, status):
    _, markets, _ = demo_catalog()
    with pytest.raises(ValueError):
        validate_bedrock(response(category, status), markets[0])


def test_incomplete_generation_cannot_be_accepted_even_with_parseable_output():
    _, markets, _ = demo_catalog()
    raw = response()
    raw["stopReason"] = "max_tokens"
    with pytest.raises(ValueError):
        validate_bedrock(raw, markets[0])


def test_cascade_counts_confident_errors_and_does_not_charge_for_avoided_calls():
    def prediction(category, score=0.99, **extra):
        return {
            "category_id": category,
            "selected_probability": score,
            "wall_ms": 10,
            **extra,
        }

    rows = [
        {
            "expected_id": "A",
            "laya": prediction("WRONG"),
            "bedrock": prediction("A", usage={"inputTokens": 100, "outputTokens": 20}),
        },
        {
            "expected_id": "A",
            "laya": prediction("A", 0.8),
            "bedrock": prediction("A", usage={"inputTokens": 200, "outputTokens": 30}),
        },
        {
            "expected_id": "unmatched",
            "laya": prediction("unmatched"),
            "bedrock": prediction("unmatched", usage={"inputTokens": 300, "outputTokens": 40}),
        },
        {
            "expected_id": "A",
            "laya": prediction(None, error="Timeout"),
            "bedrock": prediction(None, error="Timeout"),
        },
    ]
    result = summarize_cascade(rows, protocol())
    assert result["cascade"]["correct"] == 2
    assert result["cascade"]["accuracy"] == 0.5
    assert result["cascade"]["unresolved"] == 1
    assert result["cascade"]["errors"] == 1
    assert result["cascade"]["bedrock_calls"] == 3
    assert result["cascade"]["bedrock_input_tokens"] == 500
    assert result["routing"]["wrong_laya_accepted"] == 1
    assert result["gates"]["wrong_laya_accepted"] is False
    assert result["gates"]["execution_errors"] is False


def test_fresh_cases_have_separate_names_and_valid_labels():
    cases = [
        json.loads(line)
        for line in (ROOT / "evals/cascade/fresh-cases.jsonl").read_text().splitlines()
    ]
    old = [json.loads(line) for line in (ROOT / "evals/cases.jsonl").read_text().splitlines()]
    assert len(cases) == 24
    assert len({c["id"] for c in cases}) == len(cases)
    assert not {c["product"]["title"] for c in cases} & {c["product"]["title"] for c in old}
    assert not {c["group"] for c in cases} & {c["group"] for c in old}
    _, markets, _ = demo_catalog()
    for case in cases:
        for market in markets:
            assert case["expected"][market["id"]] in {c["id"] for c in market["categories"]} | {
                "unmatched"
            }


def test_saved_cascade_is_reproducible_and_tampering_is_detected():
    path = ROOT / "evals/cascade/bedrock-sonnet-4-6.json"
    report = json.loads(path.read_text())
    p = protocol()
    datasets = {
        name: [json.loads(line) for line in (ROOT / file).read_text().splitlines()]
        for name, file in p["datasets"].items()
    }
    _, markets, _ = demo_catalog()
    assert set(verify_cascade(report, p, datasets, markets)) == {"regression", "fresh"}
    for mutation in ("drop", "duplicate", "label", "prediction", "request", "metric"):
        changed = copy.deepcopy(report)
        if mutation == "drop":
            changed["rows"].pop()
        elif mutation == "duplicate":
            changed["rows"][-1] = copy.deepcopy(changed["rows"][0])
        elif mutation == "label":
            changed["rows"][0]["expected_id"] = "unmatched"
        elif mutation == "prediction":
            changed["rows"][0]["bedrock"]["category_id"] = "invented"
        elif mutation == "request":
            changed["rows"][0]["bedrock_request"]["system"] = []
        else:
            changed["summaries"]["regression"]["cascade"]["accuracy"] = -1
        with pytest.raises(ValueError):
            verify_cascade(changed, p, datasets, markets)
