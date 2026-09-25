import statistics
from collections import defaultdict


def summarize(rows, policy):
    """Failures remain in the denominator. Unknown catalog labels are never treated as correct."""
    if not rows:
        raise ValueError("Evaluation requires at least one result")
    correct = lambda r: r.get("category_id") == r["expected_id"] and not r.get("error")
    accuracy = sum(bool(correct(r)) for r in rows) / len(rows)
    baseline = sum(r["baseline_id"] == r["expected_id"] for r in rows) / len(rows)
    matched = [r for r in rows if r["expected_id"] != "unmatched"]
    unmatched = [r for r in rows if r["expected_id"] == "unmatched"]
    recall = (
        sum(r["expected_id"] in [c["id"] for c in r["candidates"]] for r in matched) / len(matched)
        if matched
        else None
    )
    unknown_recall = (
        sum(bool(correct(r)) for r in unmatched) / len(unmatched) if unmatched else None
    )
    times = sorted(r["model_ms"] for r in rows if not r.get("error"))
    slices = defaultdict(list)
    for row in rows:
        slices[row["slice"]].append(row)
    gates = {
        "accuracy": accuracy >= policy["minimum_accuracy"],
        "shortlist_recall": recall is not None and recall >= policy["minimum_shortlist_recall"],
        "lift_over_lexical": accuracy - baseline >= policy["minimum_lift_over_lexical"],
        "unmatched_recall": unknown_recall is not None
        and unknown_recall >= policy["minimum_unmatched_recall"],
        "no_execution_errors": all(not r.get("error") for r in rows),
    }
    return {
        "decisions": len(rows),
        "accuracy": accuracy,
        "baseline_accuracy": baseline,
        "lift": accuracy - baseline,
        "shortlist_recall": recall,
        "unmatched_recall": unknown_recall,
        "p50_model_ms": statistics.median(times) if times else None,
        "p95_model_ms": times[min(len(times) - 1, int(len(times) * 0.95))] if times else None,
        "slices": {
            name: {
                "count": len(group),
                "accuracy": sum(bool(correct(r)) for r in group) / len(group),
            }
            for name, group in slices.items()
        },
        "gates": gates,
        "passed": all(gates.values()),
    }
