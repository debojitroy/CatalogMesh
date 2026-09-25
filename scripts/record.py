"""Record genuine model results; expected labels never enter the inference request."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
from catalogmesh.evaluation import summarize
from catalogmesh.fixtures import demo_catalog
from catalogmesh.mapping import ALGORITHM, REPRESENTATION, digest, prepare, validate_prediction

ROOT = Path(__file__).resolve().parents[1]


async def record(kind, url, output):
    suppliers, markets, expected = demo_catalog()
    cases = (
        [
            {
                "id": p["id"],
                "group": s["id"],
                "slice": "showcase",
                "product": p,
                "expected": expected[p["id"]],
            }
            for s in suppliers
            for p in s["products"]
        ]
        if kind == "showcase"
        else [
            json.loads(line)
            for line in (ROOT / "evals/cases.jsonl").read_text().splitlines()
            if line
        ]
    )
    rows = []
    async with httpx.AsyncClient(base_url=url, timeout=120, follow_redirects=False) as client:
        metadata_response = await client.get("/health")
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        warm = prepare(cases[0]["product"], markets[0])
        response = await client.post(
            "/predict", json={"state": warm["state"], "questions": warm["questions"]}
        )
        response.raise_for_status()
        for case in cases:
            for market in markets:
                prepared = prepare(case["product"], market)
                row = {
                    **prepared,
                    "case_id": case["id"],
                    "product": case["product"],
                    "marketplace_id": market["id"],
                    "taxonomy": market,
                    "expected_id": case["expected"][market["id"]],
                    "group": case["group"],
                    "slice": case["slice"],
                }
                response = await client.post(
                    "/predict",
                    json={"state": prepared["state"], "questions": prepared["questions"]},
                )
                if response.status_code != 200:
                    row.update(
                        error=f"Inference HTTP {response.status_code}", category_id=None, model_ms=0
                    )
                else:
                    data = response.json()
                    row.update(validate_prediction(data["result"], prepared))
                    row.update(model_ms=data["model_ms"], raw_response=data["result"])
                rows.append(row)
                print(
                    f"{kind} {len(rows)}/{len(cases) * len(markets)} {case['id']} → {market['id']}: {row['category_id']} (expected {row['expected_id']})",
                    flush=True,
                )
    policy = json.loads((ROOT / "evals/policy.json").read_text())
    report = {
        "format": "catalogmesh.recording.v1",
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": kind,
        "dataset_hash": digest(cases),
        "taxonomy_hash": digest(markets),
        "retrieval": ALGORITHM,
        "representation": REPRESENTATION,
        "metadata": metadata,
        "warmup_calls": 1,
        "methodology": "Authored English development examples, one warm sequential call per product/destination, no independent human label review. No training performed. Probabilities are uncalibrated and conditional on retrieved candidates.",
        "policy": policy,
        "summary": summarize(rows, policy),
        "rows": rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["summary"], indent=2))
    return report["summary"]["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["showcase", "eval"], default="eval")
    parser.add_argument("--url", default="http://127.0.0.1:8120")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or ROOT / "data" / f"{args.kind}-candidate.json"
    passed = asyncio.run(record(args.kind, args.url, output))
    if args.kind == "eval" and not passed:
        raise SystemExit(1)
