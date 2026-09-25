"""Run a paired live comparison, or verify a saved experiment without credentials."""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
from catalogmesh.cascade import (
    PROMPT,
    bedrock_request,
    summarize_cascade,
    validate_bedrock,
    verify_cascade,
)
from catalogmesh.fixtures import demo_catalog
from catalogmesh.mapping import digest, prepare, validate_prediction

ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    protocol = json.loads((ROOT / "evals/cascade/protocol.json").read_text())
    if protocol["accept_unmatched_from_laya"] is not False:
        raise ValueError("This experiment only accepts actual category mappings from Laya")
    if not 0 <= protocol["threshold"] <= 1:
        raise ValueError("Routing threshold must be between zero and one")
    datasets = {
        name: [json.loads(line) for line in (ROOT / path).read_text().splitlines() if line]
        for name, path in protocol["datasets"].items()
    }
    _, markets, _ = demo_catalog()
    for cases in datasets.values():
        if len({c["id"] for c in cases}) != len(cases):
            raise ValueError("Duplicate case ID")
        for case in cases:
            for market in markets:
                allowed = {c["id"] for c in market["categories"]} | {"unmatched"}
                if case["expected"][market["id"]] not in allowed:
                    raise ValueError("Invalid expected annotation")
    return protocol, datasets, markets


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def run(args, protocol, datasets, markets):
    # Optional dependency: software CI can replay and validate without AWS credentials.
    import boto3
    import botocore
    from botocore.config import Config
    from botocore.exceptions import BotoCoreError, ClientError

    if args.output.exists():
        raise ValueError("Output already exists; choose a new path to preserve prior evidence")
    session = boto3.Session(profile_name=args.profile, region_name=protocol["region"])
    runtime = session.client(
        "bedrock-runtime",
        config=Config(
            connect_timeout=15,
            read_timeout=180,
            retries={"mode": "standard", "total_max_attempts": 1},
        ),
    )
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "protocol": protocol,
        "protocol_hash": digest(protocol),
        "datasets_hash": digest(datasets),
        "taxonomy_hash": digest(markets),
        "prompt_hash": digest(PROMPT),
        "boto3_version": boto3.__version__,
        "botocore_version": botocore.__version__,
        "authentication": "Named AWS profile (profile name and account identity not recorded)",
    }
    report = {"format": "catalogmesh.cascade.v1", "manifest": manifest, "rows": [], "summaries": {}}
    # This file is persisted BEFORE model calls, fixing labels/protocol hashes prospectively.
    save(args.output.with_suffix(".manifest.json"), manifest)
    with httpx.Client(base_url=args.laya_url, timeout=120, follow_redirects=False) as laya:
        health = laya.get("/health")
        health.raise_for_status()
        manifest["laya_metadata"] = health.json()
        save(args.output.with_suffix(".manifest.json"), manifest)
        total = sum(len(c) for c in datasets.values()) * len(markets)
        for name, cases in datasets.items():
            for case in cases:
                for market in markets:
                    prepared = prepare(case["product"], market)
                    laya_input = {"state": prepared["state"], "questions": prepared["questions"]}
                    request = bedrock_request(case["product"], market, protocol)
                    row = {
                        "dataset": name,
                        "case_id": case["id"],
                        "marketplace_id": market["id"],
                        "expected_id": case["expected"][market["id"]],
                        "group": case["group"],
                        "slice": case["slice"],
                        "laya_request": laya_input,
                        "bedrock_request": request,
                    }
                    result = {}
                    start = time.perf_counter()
                    try:
                        response = laya.post("/predict", json=laya_input)
                        response.raise_for_status()
                        payload = response.json()
                        result["raw_response"] = payload["result"]
                        result.update(validate_prediction(payload["result"], prepared))
                        result["model_ms"] = payload["model_ms"]
                    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                        result.update(error=type(exc).__name__, category_id=None)
                    result["wall_ms"] = round((time.perf_counter() - start) * 1000, 3)
                    row["laya"] = result
                    result = {}
                    start = time.perf_counter()
                    try:
                        response = runtime.converse(**request)
                        # Preserve model output/usage while excluding account/request HTTP metadata.
                        result["raw_response"] = {
                            k: v for k, v in response.items() if k != "ResponseMetadata"
                        }
                        result["usage"] = response.get("usage", {})
                        result.update(validate_bedrock(response, market))
                    except ClientError as exc:
                        result.update(error=exc.response["Error"]["Code"], category_id=None)
                    except (BotoCoreError, ValueError, KeyError, TypeError) as exc:
                        result.update(error=type(exc).__name__, category_id=None)
                    result["wall_ms"] = round((time.perf_counter() - start) * 1000, 3)
                    row["bedrock"] = result
                    report["rows"].append(row)
                    save(args.output, report)
                    print(
                        f"{len(report['rows'])}/{total} {name} {case['id']}/{market['id']} "
                        f"Laya={row['laya'].get('category_id')} "
                        f"Bedrock={result.get('category_id')} error={result.get('error')}",
                        flush=True,
                    )
                    # Stop systemic access failures before spending on a whole broken run.
                    if result.get("error") in {
                        "AccessDeniedException",
                        "UnrecognizedClientException",
                        "ExpiredTokenException",
                        "ValidationException",
                    }:
                        raise RuntimeError(
                            f"Bedrock setup failed: {result['error']}; report retained"
                        )
    report["summaries"] = {
        name: summarize_cascade([r for r in report["rows"] if r["dataset"] == name], protocol)
        for name in datasets
    }
    save(args.output, report)
    verify_cascade(report, protocol, datasets, markets)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="AWS profile for live calls; omitted uses SDK defaults")
    parser.add_argument("--laya-url", default="http://127.0.0.1:8120")
    parser.add_argument("--output", type=Path, default=ROOT / "data/cascade-candidate.json")
    parser.add_argument("--verify", type=Path, help="Verify a report offline; makes no model calls")
    parser.add_argument("--quality", action="store_true", help="Fail when experiment gates fail")
    args = parser.parse_args()
    protocol, datasets, markets = load_inputs()
    if args.verify:
        report = json.loads(args.verify.read_text())
        verify_cascade(report, protocol, datasets, markets)
    else:
        report = run(args, protocol, datasets, markets)
    print(json.dumps(report["summaries"], indent=2))
    if args.quality and not all(
        all(summary["gates"].values()) for summary in report["summaries"].values()
    ):
        raise SystemExit(1)
