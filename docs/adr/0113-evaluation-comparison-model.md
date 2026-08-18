# Evaluation Comparison Model

## Status

Accepted. Current formal path uses Matrix schema v2.

## Context

DevAgentOps must compare deterministic Pipeline, model-backed diagnostic conditions, ReAct, retrieval, model and future runtime variants without confusing runtime behavior, evidence access, prompt/control, tool policy, model configuration, Suite identity, execution mechanics or scoring method.

## Decision

V1 compares systems through repository-defined Evaluation Matrix conditions. Current new formal conditions use **Matrix v2**, not the earlier Defaults/one-level-`extends` Matrix v1 shape.

Matrix v2 condition identity includes:

```text
type
runtime_variant
suite
evaluation_method
treatment_fingerprint
```

Treatment explicitly contains provider/model/reasoning/generation/contracts/context. Execution Policy is separately fingerprinted and enters Run Configuration identity together with Suite/Case selection, code revision and dirty state.

Therefore `Condition Fingerprint` is not by itself the complete run identity.

Historical Matrix v1 files remain compatibility/history and must not be silently reinterpreted as Matrix v2.

The L0-L5+ Runtime Capability Ladder defines attribution semantics, not a mandatory Matrix order. L1/L2/L3 are diagnostics, L4 is the first Agentic Product Runtime, and Oracle Evidence is orthogonal.

Current implementation state:

- L1 Matrix v2 formal milestone complete;
- L2 Matrix v2 formal milestone complete;
- Oracle Matrix v2 formal milestone complete;
- L4 Matrix v2 Treatment contract frozen by ADR 0128, implementation pending.

## L4 Treatment refinement

L4 formal identity must Registry-validate:

- shared Task Contract prompt;
- separate Runtime-control prompt;
- Tool Registry;
- Tool Policy;
- provider/model/reasoning/generation/context contracts.

Runtime code is not a Component Registry component; implementation provenance remains `runtime_variant + code_revision`.

Execution Policy is outer evaluation/request mechanics, not Agent Tool Policy. In particular, current `retry_count` must never be silently treated as whole-sample retry for L4; ADR 0128 freezes same-logical-provider-request retry semantics.

## Comparison interpretation

Meaningful direct or paired comparison requires explicit compatibility checks on the controls relevant to the question. When more than the intended variable changes, describe the result as a combined treatment difference rather than a single-feature causal uplift.

Oracle-versus-Agent realization-gap analysis uses dedicated pairing checks because Oracle and Agent Condition Fingerprints are expected to differ; it is not an ordinary same-condition leaderboard comparison.

## Alternatives Considered

- Compare by project version only: too coarse.
- Test every feature combination: unmanageable Cartesian grid.
- Use one global leaderboard across methods/suites/models: misleading.
- Rewrite historical Matrix v1 identities to v2: destroys reproducibility.

## Consequences

Current experiments have explicit Treatment and execution identities while historical runs remain interpretable. L4 can add Tool/Runtime-control component references without inventing a new top-level Runtime identity system.

## Implementation Guide

See [Evaluation Matrix, Component Registry and Formal Evaluation Identity](../evaluation/evaluation-matrix-and-component-registry.md).

## Consolidates

Micro ADRs: `0014`, `0015`, `0016`, `0017`, `0023`, `0044`, `0045`, `0046`, `0047`, `0048`, `0049`, `0050`, `0051`, `0052`, `0053`, `0054`, `0055`, `0056`, `0057`, `0058`.

## Refined By

- ADR 0127 — capability ladder semantics;
- ADR 0128 — concrete L4 Treatment / Tool / retry identity.
