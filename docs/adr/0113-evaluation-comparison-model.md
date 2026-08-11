# Evaluation Comparison Model

## Status

Accepted.

## Context

DevAgentOps must compare deterministic Pipeline, model-backed diagnostic conditions, ReAct, retrieval, model, and future framework variants without confusing changes in runtime, prompt, orchestration, evidence access, adaptive control, tool descriptions, model configuration, suite content, or scoring method.

## Decision

V1 will compare systems through repository-defined evaluation matrix conditions. Direct leaderboard comparison requires the same evaluation method version, evaluation suite version, model configuration, and condition fingerprint. Matrix conditions may use defaults and one-level `extends`, but every run manifest must store the fully resolved effective condition and condition fingerprint.

The L0-L5+ Runtime Capability Ladder defines attribution semantics, not a mandatory Matrix shape or implementation order. L1 full-context one-shot, L2 fixed model workflow, and L3 static retrieval are diagnostic/comparison conditions; L4 self-built ReAct is the first Agentic Runtime. Oracle Evidence is an orthogonal diagnostic intervention. ADR 0127 does not modify the current Matrix/Registry schema or freeze future field names.

## Alternatives Considered

- Compare by V1/V2 project version only. This hides the actual runtime and component variables.
- Test every feature combination. This creates an unmanageable Cartesian grid.
- Use one global leaderboard across scoring methods, suites, or models. This produces misleading rankings.

## Consequences

Comparison becomes explicit and reproducible. Matrix changes only require rerunning conditions whose effective condition changes, while anchor conditions can be rerun when evaluation method or suite versions change.

## Implementation Notes

- Keep evaluation matrix files in the repository.
- Matrix entries include condition type, runtime variant, suite, method, model, component versions, budgets, and repeats.
- Use anchor, ablation, and candidate condition types.
- Preserve the Pipeline anchor and Product Runtime comparison between `pipeline_baseline` and `self_built_react`.
- Add L1/L2/L3 only through future explicit diagnostic/ablation condition designs; do not infer that ladder numbering mandates Matrix order or that L3 must precede L4 implementation.
- Model changes are tested only through ablation conditions.
- Repeated runs are configured in the matrix and reported as stability analysis, not silently averaged into ordinary leaderboard rows.

## Implementation Guide

See [Evaluation Matrix 与 Component Registry](../evaluation/evaluation-matrix-and-component-registry.md) for the currently implemented Matrix schema, resolution rules, fingerprints, CLI modes, and boundaries.

## Consolidates

Micro ADRs: `0014`, `0015`, `0016`, `0017`, `0023`, `0044`, `0045`, `0046`, `0047`, `0048`, `0049`, `0050`, `0051`, `0052`, `0053`, `0054`, `0055`, `0056`, `0057`, `0058`.

## Refined By

[ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](0127-staged-runtime-capability-ladder-and-reference-boundary.md).
