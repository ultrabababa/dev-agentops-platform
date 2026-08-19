# Evaluation Milestones — Status Index

This directory contains dated experiment and analysis records. Dated milestone files are historical snapshots: they preserve what was run, observed, and concluded at that point in time. They are not automatically current architecture guidance.

Use current-facing documents (`README.md`, `CONTEXT.md`, active ADRs, and `docs/evaluation/*.md`) for current behavior and roadmap decisions.

## Current status

| Document | Status | How to read it now |
| --- | --- | --- |
| `l1-minimax-m3-full-suite-2026-08-14.md` | Historical baseline | Immutable L1 formal result. A new comparison generation is planned after shared Evidence Reference Canonicalization is implemented. |
| `l2-minimax-m3-full-suite-2026-08-15.md` | Historical baseline | Immutable L2 formal result. A new comparison generation is planned after shared Evidence Reference Canonicalization is implemented. |
| `oracle-minimax-m3-full-suite-2026-08-15.md` | Historical baseline | Immutable Oracle formal result. Oracle remains a diagnostic condition, not a Runtime rung. A new comparison generation is planned under the shared output-resolution contract. |
| `l4-minimax-m3-full-suite-2026-08-19.md` | Historical baseline | Immutable L4 V1 formal result. Its original follow-up recommendation for L4-only coordinate assistance is superseded. |
| `oracle-l4-pair-analysis-2026-08-19.md` | **Current analysis / decision record** | Records the completed Oracle↔L4 badcase analysis and the current decision: shared deterministic final-report Evidence Reference Canonicalization for L1/L2/Oracle/L4, followed by a fresh fair comparison generation; L4 batch+parallel Tool Policy is a separate later efficiency optimization. |

## Supersession rule

When a dated milestone contains a forward-looking recommendation that conflicts with a newer current-facing document or with `oracle-l4-pair-analysis-2026-08-19.md`, treat the dated recommendation as superseded while preserving the measured historical result.

In particular, the following earlier direction is no longer current:

```text
L4-only physical-span -> Canonical-coordinate assistance
with no post-generation Runtime normalization
```

The current direction is:

```text
shared deterministic Evidence Reference Canonicalization
    -> offline replay of historical L1/L2/Oracle/L4 raw outputs
    -> new L1/L2/Oracle/L4 20x3 formal comparison generation
    -> separate L4 batch + parallel Tool Policy efficiency experiment
```

Historical artifacts, fingerprints, metrics, and run identities must not be rewritten to make old runs appear to have used the new behavior.
