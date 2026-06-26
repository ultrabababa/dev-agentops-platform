# Badcase Review and Regression

## Status

Accepted.

## Context

Badcases are useful only when they are produced from reproducible formal evaluation and can guide prompt, retrieval, tool, runtime, case, or scorer improvements.

## Decision

V1 badcases come from formal evaluation runs. Debug findings may inform development but do not become regression-tracked badcases until reproduced formally. Badcases use structured primary and secondary reasons, may store scorer-suggested and human-reviewed reasons, and can be reviewed in a minimal dashboard flow.

## Alternatives Considered

- Let users manually tag any debug issue as a badcase. This makes regression analysis unstable.
- Store only free-form notes. This makes aggregation and improvement prioritization weak.
- Overbuild issue workflow in V1. This distracts from the evaluation loop.

## Consequences

Badcases become a reliable regression asset. Old badcases are preserved, and new condition versions compare carryover rather than overwriting history.

## Implementation Notes

- Minimal badcase review lets a reviewer inspect trace, report, expected answer, suggested reasons, and save reviewed reasons plus notes.
- Badcase fix loop is draft change, subset debug, freeze new component version, update matrix condition, run formal eval.
- Carryover compares by case, failing metric, and primary reason to distinguish resolved issues, persistent issues, and new regressions.
- Expected-answer or scorer mistakes are preserved as badcases under the current suite and fixed through new suite or method versions.

## Consolidates

Micro ADRs: `0033`, `0034`, `0035`, `0036`, `0037`, `0039`, `0059`, `0060`, `0061`, `0062`.
