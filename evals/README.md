# Evaluation set v1

This is an **authored regression suite**, not proof of production accuracy.

`cases.jsonl` contains 24 English product examples, evaluated against three fictional
marketplace taxonomies: **72 decisions**. Every case has a group, challenge slice, product
record and expected destination category ID for each marketplace.

The expected category is not sent to retrieval or Laya. A separate evaluator compares the
prediction with the label after inference. Related product pairs share a `group`; keep
groups together if making future training/validation/test splits. No fine-tuning was
performed for this release.

## What it exercises

- Complete devices versus compatible accessories and replacement parts.
- Source categories that disagree with the item actually sold.
- Nearby categories such as coffee grinders and espresso machines.
- Bare power tools sold without batteries.
- Unspecified products for which there is not enough evidence.
- Products for which the target taxonomy has no valid destination.
- Similar batteries or cases for different equipment.
- Different destination granularity and hierarchy.

The showcase's 18 product titles are disjoint from these 24 titles. Both sets use the
same taxonomy definitions and related concepts. The eval suite was inspected while
diagnosing an initial adapter failure; **it is no longer an untouched holdout**. Labels
were authored during implementation and have not received independent domain-expert review.
An independently reviewed supplier-held-out set is required before making generalization claims.

## Frozen pilot bars

`policy.json` was created before the first eval run:

| Gate | Requirement |
|---|---|
| Exact destination accuracy | ≥80% |
| Correct-category shortlist recall | ≥95%, excluding genuinely unmatched products |
| Lift over lexical top candidate | ≥5 percentage points |
| Recall on expected unmatched decisions | ≥50% |
| Execution errors | Zero |

The initial English baseline gets **52/72 correct (72.2%)**, versus **45/72 (62.5%)**
for lexical top-candidate selection. The shortlist contains every expected in-taxonomy
category. Unmatched recall is **5/12 (41.7%)**.

Therefore the absolute quality gate **fails**. Thresholds and expected answers were not
weakened to pass it. No confidence threshold has been calibrated for auto-acceptance.

## Recorded history

| Run | Exact accuracy | Purpose |
|---|---:|---|
| Multilingual, opaque category-ID option labels | 25.0% | Initial adapter failure |
| Multilingual, readable semantic option labels | 70.8% | Identified representation sensitivity |
| English, readable semantic option labels | 72.2% | Current regression baseline |

Historical runs live in `history/` with their original questions, outputs, metadata and
metrics. The English checkpoint was chosen after comparing the separate showcase
(88.9% English versus 79.6% multilingual). Its harder eval failures remain visible.

## How regression checking works

`scripts/check_eval.py`:

1. Requires the complete case × marketplace set, without omissions or duplicates.
2. Verifies dataset and taxonomy hashes.
3. Recreates retrieval and model questions from current code.
4. Checks recorded fingerprints, candidate lists and baseline selections.
5. Decodes original Laya responses and verifies the stored prediction.
6. Recalculates metrics and verifies the committed quality policy.
7. Optionally compares a new live candidate report to the baseline, failing if any
   previously correct case becomes wrong.
8. With `--quality`, fails when any absolute pilot bar is missed.

Software CI verifies these contracts without a GPU. It cannot establish that a new
checkpoint behaves correctly; run live inference and compare the reports for model,
tokenizer, prompt, runtime or numerical changes. Future decision-schema changes will
invalidate old input fingerprints and require an explicit reviewed baseline update.

## Next evidence to collect

- Independently reviewed product labels from licensed real supplier feeds.
- Completely unseen suppliers, brands and product families.
- Unseen destination taxonomies and taxonomy revisions.
- Option-order stability, multiple runs and numerical/runtime variation.
- Multilingual and incomplete listings; image-only evidence remains unsupported.
- Calibration and selective acceptance on a separate validation split.
- Batch throughput, queue latency and total serving cost under sustained load.

Even a passing eval cannot make a classifier “regression-proof.” This suite makes
specific regressions observable and blocks known quality failures.
