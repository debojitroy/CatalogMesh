# Bedrock fallback verdict

**The fallback corrected every observed Laya error, but the fixed 95% threshold avoided only 2.8% of Bedrock calls on fresh products.** The current experiment supports testing the architecture further; it does not establish a compelling or reliable Laya cost advantage on new catalogs.

Recorded 2026-09-25T11:34:05.904694+00:00. Laya English checkpoint `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851` on Tesla T4; Claude Sonnet 4.6 through Amazon Bedrock Converse, global cross-region inference starting in `us-east-2`. Both providers were called live for every decision.

## Results

| Dataset | Laya alone | Bedrock alone | Laya → Bedrock | Bedrock calls avoided | Wrong Laya acceptances |
|---|---:|---:|---:|---:|---:|
| Existing regression | 52/72 (72.2%) | 72/72 (100.0%) | 72/72 (100.0%) | 10/72 (13.9%) | 0 |
| Fresh authored products | 44/72 (61.1%) | 72/72 (100.0%) | 72/72 (100.0%) | 2/72 (2.8%) | 0 |

Accuracy counts both correct category assignments and correct `unmatched` decisions. The combined system assigned categories to **60/72 regression decisions and 54/72 fresh decisions**. It correctly left **12 regression and 18 fresh decisions unmatched**. Those products still need supplier information, a supported destination category or a human workflow. They are not successfully categorized products.

All 144 Bedrock calls returned valid structured decisions. The cascade corrected all 20 Laya errors in the regression set and all 28 Laya errors in the fresh set. No retries, expected-answer prompts or post-result threshold changes were used.

The two fresh Laya acceptances were **F09, Alder mineral removal sachets**, for Harbor and Mercury. They are two destination decisions about one product, not two independent confirmations of general reliability.

## Frozen quality criteria

| Criterion | Existing regression | Fresh authored products |
|---|---|---|
| At least 95% exact decision accuracy | PASS | PASS |
| Zero wrong accepted Laya mappings | PASS | PASS |
| Zero execution errors | PASS | PASS |
| At least 10% fewer Bedrock calls | PASS | FAIL |

**The experiment fails its fresh-data call-reduction criterion.** The threshold stays at 0.95 and the failed gate remains visible. The existing Laya-only accuracy/rejection gates are unchanged.

## Latency

| Dataset | Laya p50 call | Bedrock p50 call | Derived cascade p50 | Bedrock / cascade p95 |
|---|---:|---:|---:|---:|
| Regression | 45.4 ms | 2.059 s | 2.073 s | 3.899 / 3.944 s |
| Fresh | 44.9 ms | 2.028 s | 2.068 s | 3.409 / 3.459 s |

The accepted Laya cases take roughly 45 ms locally, but most cases still incur Bedrock latency plus the Laya first pass. Median latency did not improve. These are sequential provider-call measurements, excluding retrieval and prompt construction. Cascade latency adds the paired call durations for escalations; a deployed cascade and concurrent throughput were not measured.

## Cost

**USD, STANDARD ON DEMAND, global cross-region inference, uncached short-context requests.** The verified AWS rate is **$3 per million input tokens and $15 per million output tokens**. See [pricing evidence](pricing.json) and [AWS Bedrock pricing](https://aws.amazon.com/bedrock/pricing/).

| Dataset / path | Input tokens | Output tokens | Estimated Bedrock charge | Scaled per 1,000 decisions |
|---|---:|---:|---:|---:|
| Regression / bedrock | 106,422 | 8,190 | $0.442116 | $6.140 |
| Regression / cascade | 90,846 | 7,032 | $0.378018 | $5.250 |
| Fresh / bedrock | 106,866 | 8,281 | $0.444813 | $6.178 |
| Fresh / cascade | 103,748 | 8,067 | $0.432249 | $6.003 |

Calculation breakdowns:

- Regression / bedrock: 106,422 × $3 / 1,000,000 + 8,190 × $15 / 1,000,000 = **$0.442116**.
- Regression / cascade: 90,846 × $3 / 1,000,000 + 7,032 × $15 / 1,000,000 = **$0.378018**.
- Fresh / bedrock: 106,866 × $3 / 1,000,000 + 8,281 × $15 / 1,000,000 = **$0.444813**.
- Fresh / cascade: 103,748 × $3 / 1,000,000 + 8,067 × $15 / 1,000,000 = **$0.432249**.
- Regression savings: **$0.064098 per 72 decisions (14.50%)**, equivalent to **$0.8902 per 1,000** with the same workload mix.
- Fresh savings: **$0.012564 per 72 decisions (2.82%)**, equivalent to **$0.1745 per 1,000** with the same workload mix.

Actual benchmark invocation usage: **213,288 input tokens + 16,471 output tokens** over 144 paid calls. Estimated Bedrock inference charge: **$0.886929 (about $0.89)**. The combined-system costs are derived from those recorded calls; we did not pay to invoke the fallback a second time.

The fresh-data saving is only **$0.1745 per 1,000 decisions before Laya costs**. Local inference and any additional operating costs must fit within that saving for a net cost reduction. We did not measure GPU utilization, idle cost, production concurrency or review labor. Scaling to 1,000 is arithmetic using this sample mix, not a throughput or production-volume experiment.

Excluded: Laya GPU/CPU and idle hardware, human review, storage, networking, taxes, discounts, caching and any unreported provider charges. This is a token-based estimate, not an AWS invoice.

## What this proves and what remains open

- A Bedrock escalation path can correct the semantic mapping and no-destination failures observed here.
- The 95% Laya threshold preserved decision accuracy in this run, but accepted very few fresh cases.
- Zero observed accepted errors does not establish certainty. The fresh acceptance evidence comes from one product.
- The regression threshold was chosen after examining that set. Fresh labels were frozen before inference but authored with prior failure modes in mind; neither set has independent expert review.
- These are familiar concepts in three fictional taxonomies with 11–16 categories. Bedrock saw the full taxonomy, so this is a system comparison rather than an isolated model comparison. It does not prove performance across arbitrary suppliers or marketplaces.
- More independently reviewed real catalog data is needed to calibrate routing and quantify coverage at a fixed error target. Any subsequent threshold tuning needs a separate validation set and untouched test set.
- The web workbench still uses Laya alone. This benchmark does not enable automatic publishing or add a live Bedrock UI mode.

## Reproduce and inspect

See [benchmark instructions](README.md), [frozen protocol](protocol.json), [raw paired results](bedrock-sonnet-4-6.json) and [pre-inference manifest](bedrock-sonnet-4-6.manifest.json). Offline verification recomputes coverage, requests, decoded predictions and summary metrics. A live rerun is required to test a changed model or prompt.
