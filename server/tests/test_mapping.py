import copy
import json
from pathlib import Path

import pytest
from catalogmesh.fixtures import demo_catalog
from catalogmesh.mapping import prepare, validate_prediction
from catalogmesh.models import Marketplace

ROOT = Path(__file__).resolve().parents[2]
SUPPLIERS, MARKETS, _ = demo_catalog()


def test_opaque_category_ids_do_not_enter_model_input():
    product = SUPPLIERS[0]["products"][0]
    original = prepare(product, MARKETS[0])
    changed = copy.deepcopy(MARKETS[0])
    for index, category in enumerate(changed["categories"]):
        category["id"] = f"arbitrary-{index}"
    new = prepare(product, changed)
    assert new["questions"] == original["questions"]
    assert new["state"] == original["state"]
    assert new["option_ids"] != original["option_ids"]
    assert new["fingerprint"] != original["fingerprint"]


def test_definition_and_product_changes_invalidate_recorded_results():
    product, market = copy.deepcopy(SUPPLIERS[0]["products"][0]), copy.deepcopy(MARKETS[0])
    original = prepare(product, market)["fingerprint"]
    market["categories"][0]["description"] += " Excludes all accessories."
    assert prepare(product, market)["fingerprint"] != original
    product["description"] += " Earbuds not included."
    assert prepare(product, MARKETS[0])["fingerprint"] != original


@pytest.mark.parametrize("bad_value", [True, float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_model_probabilities_are_rejected(bad_value):
    p = prepare(SUPPLIERS[0]["products"][0], MARKETS[0])
    keys = list(p["option_ids"])
    result = {
        "answers": {
            "category": {"choice": keys[0], "probabilities": dict.fromkeys(keys, bad_value)}
        }
    }
    with pytest.raises(ValueError):
        validate_prediction(result, p)


def test_unknown_label_is_not_accepted():
    p = prepare(SUPPLIERS[0]["products"][0], MARKETS[0])
    with pytest.raises(ValueError):
        validate_prediction(
            {"answers": {"category": {"choice": "invented", "probabilities": {"invented": 1.0}}}}, p
        )


def test_duplicate_category_paths_are_rejected():
    market = copy.deepcopy(MARKETS[0])
    market["categories"][1]["path"] = market["categories"][0]["path"]
    with pytest.raises(ValueError):
        Marketplace.model_validate(market)


def test_recorded_showcase_matches_current_inputs_and_raw_predictions():
    report = json.loads((ROOT / "recordings/showcase.json").read_text())
    assert len(report["rows"]) == 54
    for row in report["rows"]:
        prepared = prepare(row["product"], row["taxonomy"])
        assert row["fingerprint"] == prepared["fingerprint"]
        assert (
            row["category_id"] == validate_prediction(row["raw_response"], prepared)["category_id"]
        )
        request = json.dumps({"state": prepared["state"], "questions": prepared["questions"]})
        assert "expected_id" not in request
        assert row["model_ms"] > 0
