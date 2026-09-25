"""Check saved report integrity, absolute quality bars, and candidate regressions."""

import argparse
import json
from pathlib import Path

from catalogmesh.evaluation import summarize
from catalogmesh.fixtures import demo_catalog
from catalogmesh.mapping import digest, prepare, validate_prediction

ROOT = Path(__file__).resolve().parents[1]


def verify(report):
    cases = [
        json.loads(line) for line in (ROOT / "evals/cases.jsonl").read_text().splitlines() if line
    ]
    _, markets, _ = demo_catalog()
    expected_keys = {(c["id"], m["id"]) for c in cases for m in markets}
    actual_keys = [(r["case_id"], r["marketplace_id"]) for r in report["rows"]]
    if len(actual_keys) != len(expected_keys) or set(actual_keys) != expected_keys:
        raise ValueError("Evaluation cases are missing, duplicated or unexpected")
    if report["dataset_hash"] != digest(cases) or report["taxonomy_hash"] != digest(markets):
        raise ValueError(
            "Dataset or taxonomy changed. Record and review a new baseline explicitly."
        )
    by_case = {c["id"]: c for c in cases}
    by_market = {m["id"]: m for m in markets}
    for row in report["rows"]:
        case, market = by_case[row["case_id"]], by_market[row["marketplace_id"]]
        prepared = prepare(case["product"], market)
        if row["expected_id"] != case["expected"][market["id"]]:
            raise ValueError("Report expected labels disagree with the versioned eval set")
        for key in ("fingerprint", "state", "questions", "candidates", "option_ids", "baseline_id"):
            if row[key] != prepared[key]:
                raise ValueError(f"Pipeline drift in {row['case_id']}/{market['id']}: {key}")
        if not row.get("error"):
            decoded = validate_prediction(row["raw_response"], prepared)
            if any(row[key] != value for key, value in decoded.items()):
                raise ValueError("Stored prediction disagrees with the original model response")
    policy = json.loads((ROOT / "evals/policy.json").read_text())
    if report["policy"] != policy or report["summary"] != summarize(report["rows"], policy):
        raise ValueError("Metrics or policy changed without a corresponding result")
    return report["summary"]


def regressions(candidate, baseline):
    before = {(r["case_id"], r["marketplace_id"]): r for r in baseline["rows"]}
    lost = []
    for row in candidate["rows"]:
        old = before[(row["case_id"], row["marketplace_id"])]
        if (
            old.get("category_id") == old["expected_id"]
            and row.get("category_id") != row["expected_id"]
        ):
            lost.append(f"{row['case_id']}/{row['marketplace_id']}")
    return lost


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "evals/baseline.json")
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--quality", action="store_true")
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    summary = verify(report)
    print(f"Integrity passed: {summary['decisions']} genuine recorded decisions.")
    print(
        f"Laya {summary['accuracy']:.1%}; lexical {summary['baseline_accuracy']:.1%}; quality {'PASS' if summary['passed'] else 'FAIL'}."
    )
    failed = args.quality and not summary["passed"]
    if args.compare:
        baseline = json.loads(args.compare.read_text())
        verify(baseline)
        lost = regressions(report, baseline)
        print("Previously correct decisions lost:", lost)
        failed = failed or bool(lost)
    if failed:
        raise SystemExit(1)
