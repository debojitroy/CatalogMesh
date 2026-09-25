# Laya → Bedrock cascade benchmark

Question: **How many Bedrock calls can Laya avoid while preserving accurate product
category decisions?**

Read [REPORT.md](REPORT.md) for the measured verdict, cost arithmetic and limitations.

## Frozen experiment

- 24 existing regression products × three destination taxonomies = 72 decisions.
- 24 new authored products × the same three taxonomies = 72 prospective decisions.
- Accept Laya only for a valid, non-`unmatched` category with top score ≥0.95.
- Escalate every other decision, including Laya errors, to Claude Sonnet 4.6.
- Bedrock receives all 11–16 categories in the destination taxonomy, independently of
  Laya's five-candidate shortlist. Expected labels and Laya predictions never enter
  Bedrock's request.
- One live call to each provider per decision, no accuracy-based retries, no prompt
  changes after seeing predictions. The fallback result is derived from paired calls;
  we do not make a second paid call to simulate the cascade.
- Converse uses a forced `map_product` tool response. Category IDs, status consistency
  and completion state are validated locally. Evidence text is a model-generated
  justification, not an independently verified explanation.

The [protocol](protocol.json) and prompt/data hashes were saved in a manifest before
benchmark inference. The [fresh labels](fresh-cases.jsonl) were authored before inference.
The 0.95 threshold was chosen after inspecting the existing regression set; that set
cannot validate the threshold independently. New examples use familiar concepts and
fictional taxonomies, and their labels have not received independent expert review.
Multiple destination decisions share products and are correlated.

The recorded artifact is [bedrock-sonnet-4-6.json](bedrock-sonnet-4-6.json). The original
manifest is [bedrock-sonnet-4-6.manifest.json](bedrock-sonnet-4-6.manifest.json).

## Repeat with your AWS profile

Start the Laya worker as described in the root README. Then:

```sh
uv sync --extra dev --extra bedrock
uv run python scripts/benchmark_cascade.py \
  --profile YOUR_AWS_PROFILE \
  --output data/cascade-candidate.json
```

This command makes **144 paid Bedrock calls** and 144 local Laya calls. It uses
`global.anthropic.claude-sonnet-4-6`, Standard on-demand inference, starting in `us-east-2`.
Global cross-region inference may process requests outside the starting region.
Use an AWS profile permitted to invoke that inference profile and its backing models.
Profile names, account identity and AWS HTTP response headers are not saved in the report.

The model, region, temperature, output token limit and decision thresholds are in
`protocol.json`. For a new experiment, version the protocol and preserve previous results.
Changing the protocol invalidates verification of an older report against that new protocol.
The script refuses to overwrite an existing output file. Partial runs remain on disk;
access/configuration failures stop the run rather than producing fabricated answers.
There is no resume mode. Use a new output path for a new run.

## Verify without AWS, a GPU, or paid calls

```sh
uv sync --extra dev
uv run python scripts/benchmark_cascade.py \
  --verify evals/cascade/bedrock-sonnet-4-6.json
uv run python scripts/benchmark_cascade.py \
  --verify evals/cascade/bedrock-sonnet-4-6.json --quality
```

The first command checks exact case coverage, labels, request reconstruction, raw response
decoding, token usage consistency and recomputed metrics. The second additionally checks
the experiment's declared quality criteria: ≥95% exact decision accuracy, zero wrong
Laya-accepted mappings, no execution errors and ≥10% Bedrock call reduction, separately
for both datasets. These are experiment criteria, not calibrated reliability guarantees.
The `cascade-quality-gate` CI job runs that same check and currently fails the fresh
set's call-reduction requirement; software integrity checks remain separate.

Software tests detect dropped/duplicated cases, changed annotations, invented categories,
incomplete tool responses, incorrect routing, token-accounting mistakes and altered
metrics. Offline verification proves artifact consistency, not continued model quality:
rerun live inference before trusting a model, prompt, taxonomy or routing change.
The original Laya-only quality gates remain unchanged.

## Read the metrics correctly

- **Exact decision accuracy:** expected category ID, or `unmatched`, across all decisions.
  Provider failures remain in the denominator.
- **Mapping precision:** correctness among decisions assigning a real category.
- **Unresolved:** no suitable category or insufficient information. Bedrock preserves
  these as distinct statuses, but both normalize to `unmatched` for the original labels.
  The benchmark does not separately grade the distinction between those two statuses.
- **Laya accepted:** calls avoided by the fixed policy, including any confidently wrong
  choices. A wrong accepted choice cannot be rescued by the cascade.
- **Latency:** per-call wall time including client/network/model/response processing;
  retrieval and prompt assembly are excluded. Cascade timings add the saved Laya and
  Bedrock times for escalations. This is a sequential paired-call estimate, not a
  deployed cascade, concurrency or throughput benchmark.
- **Cost:** AWS Standard on-demand token charges estimated from returned usage and the
  [saved public pricing evidence](pricing.json). No caching, batch or flex discounts.
  Laya compute, idle hardware, review, storage, networking and taxes are excluded.
  Any failed calls without returned usage have unknown charges.

This small-taxonomy experiment is a system comparison, not an isolated model comparison:
Bedrock gets the full destination taxonomy and a different response format. A marketplace
with thousands of categories would need a separately evaluated retrieval strategy.
