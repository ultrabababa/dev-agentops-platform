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
| `evidence-reference-canonicalization-2026-08-19.md` | **Current completed experiment milestone** | Records implementation validation, zero-model-cost historical replay, fresh L1/L2/Oracle/L4 `20×3` formal generation, causal interpretation boundaries, residual invalid-report audit, and the decision to accept `canonical-line-range-normalization-v1`. |
| `evidence-reference-canonicalization-results-2026-08-19.json` | **Machine-readable result snapshot** | Preserves the historical baselines, offline replay results, fresh formal Run IDs/fingerprints/metrics, execution failures, protocol-invalid details, and experiment conclusions used by the milestone report. |

## Supersession rule

When a dated milestone contains a forward-looking recommendation that conflicts with a newer current-facing document or a newer completed milestone, preserve the measured historical result but treat the older recommendation as superseded.

In particular, the following earlier direction is no longer current:

```text
L4-only physical-span -> Canonical-coordinate assistance
with no post-generation Runtime normalization
```

Shared canonicalization is now implemented and experimentally validated:

```text
shared deterministic Evidence Reference Canonicalization
    -> historical L1/L2/Oracle/L4 offline replay complete
    -> fresh L1/L2/Oracle/L4 20x3 formal generation complete
    -> canonical-line-range-normalization-v1 accepted
```

The current next independent Runtime experiment is:

```text
L4 single + sequential Tool Policy
    -> batch + parallel ToolCalls
    -> compare Model Decisions / tool-call handling / tokens / wall-clock
    -> verify quality and protocol do not regress materially
```

Historical artifacts, fingerprints, metrics, and run identities must not be rewritten to make old runs appear to have used newer behavior.
