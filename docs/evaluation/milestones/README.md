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
| `l4-batch-parallel-toolcalls-2026-08-19.md` | **Current completed Runtime experiment milestone** | Records Issue #61 / PR #62, deterministic gates, fresh `20×3` Batch + Parallel formal generation, runtime-mechanism evidence, quality caveats, long-tail analysis, and the decision to retain the treatment without yet promoting it to the default L4 baseline. |
| `l4-batch-parallel-toolcalls-results-2026-08-19.json` | **Machine-readable result snapshot** | Preserves candidate Run identity, validation results, fresh canonicalized reference metrics, Model Decision / batch / ToolCall observations, provider usage, timeout straggler evidence, protocol-invalid details, and the experiment decision. |

## Supersession rule

When a dated milestone contains a forward-looking recommendation that conflicts with a newer current-facing document or a newer completed milestone, preserve the measured historical result but treat the older recommendation as superseded.

Shared canonicalization is implemented and experimentally validated:

```text
shared deterministic Evidence Reference Canonicalization
    -> historical L1/L2/Oracle/L4 offline replay complete
    -> fresh L1/L2/Oracle/L4 20x3 formal generation complete
    -> canonical-line-range-normalization-v1 accepted
```

The independent Batch + Parallel Runtime experiment is also complete:

```text
single + sequential + reject-all
    -> batch + parallel + independent-call handling
    -> 60/60 Samples completed
    -> 257 multi-call decisions across 55/60 Samples
    -> successful Model Decisions 798 reference -> 547 candidate
    -> no multiple_tool_calls_rejected
    -> fresh quality lower, dominated by invalid_report_type realization failures
    -> treatment retained; default-baseline promotion deferred
```

This result does not justify arbitrary batch caps, forced batching, output repair, or scheduler changes. It also does not redefine L4 as a new capability rung: both policies remain `runtime_variant = self_built_react` treatments.

Historical artifacts, fingerprints, metrics, and run identities must not be rewritten to make old runs appear to have used newer behavior.
