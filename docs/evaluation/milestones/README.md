# Evaluation Milestones — Status Index

This directory contains dated experiment and analysis records. Dated milestone files are historical snapshots: they preserve what was run, observed, and concluded at that point in time. They are not automatically current architecture guidance.

Use current-facing documents (`README.md`, `CONTEXT.md`, active ADRs, and `docs/evaluation/*.md`) for current behavior and roadmap decisions.

## Current status

| Document | Status | How to read it now |
| --- | --- | --- |
| `l1-minimax-m3-full-suite-2026-08-14.md` | Historical baseline | Immutable pre-canonicalization L1 formal result. |
| `l2-minimax-m3-full-suite-2026-08-15.md` | Historical baseline | Immutable pre-canonicalization L2 formal result. |
| `oracle-minimax-m3-full-suite-2026-08-15.md` | Historical baseline | Immutable pre-canonicalization Oracle formal result. Oracle remains a diagnostic condition, not a Runtime rung. |
| `l4-minimax-m3-full-suite-2026-08-19.md` | Historical baseline | Immutable L4 V1 formal result. Its original follow-up recommendation for L4-only coordinate assistance is superseded. |
| `oracle-l4-pair-analysis-2026-08-19.md` | Historical analysis / decision input | Records the completed Oracle↔L4 badcase analysis that motivated shared deterministic final-report Evidence Reference Canonicalization. |
| `evidence-reference-canonicalization-2026-08-19.md` | **Completed experiment milestone** | Records implementation validation, zero-model-cost historical replay, fresh L1/L2/Oracle/L4 `20×3` formal generation, causal interpretation boundaries, residual invalid-report audit, and the decision to accept `canonical-line-range-normalization-v1`. |
| `evidence-reference-canonicalization-results-2026-08-19.json` | Machine-readable result snapshot | Preserves the historical baselines, offline replay results, fresh formal Run IDs/fingerprints/metrics, execution failures, protocol-invalid details, and experiment conclusions used by the canonicalization milestone. |
| `l4-batch-parallel-toolcalls-2026-08-19.md` | **Current completed Runtime experiment milestone** | Records Issue #61 / PR #62, deterministic gates, the initial Batch + Parallel formal run, a fresh back-to-back single/sequential vs Batch + Parallel replication block, quality/efficiency interpretation, and the decision to recommend Batch + Parallel for new L4 evaluations while preserving the historical baseline. |
| `l4-batch-parallel-toolcalls-results-2026-08-19.json` | **Machine-readable result snapshot** | Preserves both Batch runs, both comparison references, run identities/fingerprints, quality metrics, Model Decision / batch / ToolCall observations, provider usage, latency, protocol-invalid details, paired Case-level uncertainty, and the final recommendation. |
| `l3-static-retrieval-2026-08-24.md` | **Completed diagnostic-condition milestone** | Records L3 V1 deterministic/live gates, the clean MiniMax-M3 20×3 formal run, evaluator-side Required Evidence acquisition analysis, badcase attribution, and the decision to accept L3 as a reproducible baseline without claiming an Evidence Hit uplift. |
| `l3-static-retrieval-results-2026-08-24.json` | **Machine-readable result snapshot** | Preserves L3 run identity/fingerprints, formal metrics, provider usage, protocol details, acquisition-vs-report diagnostics, Case-level results, and the no-hidden-Ground-Truth-tuning decision. |

## Supersession rule

When a dated milestone contains a forward-looking recommendation that conflicts with a newer current-facing document or a newer completed milestone, preserve the measured historical result but treat the older recommendation as superseded.

Shared canonicalization is implemented and experimentally validated:

```text
shared deterministic Evidence Reference Canonicalization
    -> historical L1/L2/Oracle/L4 offline replay complete
    -> fresh L1/L2/Oracle/L4 20x3 formal generation complete
    -> canonical-line-range-normalization-v1 accepted
```

The independent Batch + Parallel Runtime experiment and replication are also complete:

```text
historical reference
single + sequential + reject-all

initial Batch run
798 reference -> 547 Model Decisions (-31.45%)
quality lower, with 8 invalid_report_type Samples

fresh back-to-back replication
877 -> 571 Model Decisions (-34.89%)
809 -> 775 executed ToolCalls (-4.20%)
wall time 978.27s -> 806.69s (-17.54%)
taxonomy 71.67% -> 75.00%
evidence 74.64% -> 73.50%
protocol 93.33% -> 91.67%
```

The initial apparent taxonomy/required-field regression did not reproduce; quality deltas changed direction while the efficiency mechanism reproduced at similar magnitude. Current evidence does not demonstrate a material Batch-induced quality regression. Batch + Parallel is therefore the recommended forward L4 Tool Policy for new evaluations, while historical single/sequential matrices, fingerprints, artifacts, and milestone results remain immutable references.

L3 Static Retrieval V1 implementation and live qualification are also complete:

```text
60 / 60 Samples scored
taxonomy 88.33%
Report Evidence Hit 50.67%
retrieval acquisition recall 76.56%
acquired-evidence utilization 66.18%
20 / 20 Case inputs deterministic across repeats
```

This accepts L3 as a reproducible evidence-acquisition diagnostic baseline. It does not demonstrate an Evidence Hit improvement over L1/L2 and does not authorize tuning against hidden `triage-suite-v1` Ground Truth.

This decision does not justify arbitrary batch caps, forced batching, output repair, scheduler heuristics, or a new Runtime rung. Both policies remain `runtime_variant = self_built_react` treatments.

Historical artifacts, fingerprints, metrics, and run identities must not be rewritten to make old runs appear to have used newer behavior.
