# Evaluation Comparison Model

## Status

Accepted. Current formal path uses Matrix schema v2.

L1/L2/Oracle/L4 Matrix v2 formal milestones are now complete. ADR 0129 further refines L4 context-accounting identity.

## Context

DevAgentOps must compare deterministic Pipeline, model-backed diagnostic conditions, ReAct, retrieval, model and future Runtime variants without confusing Runtime behavior, evidence access, prompt/control, Tool Policy, model configuration, Suite identity, execution mechanics or scoring method.

## Decision

V1 compares systems through repository-defined Evaluation Matrix conditions. Current new formal conditions use **Matrix v2**, not the earlier Defaults/one-level-`extends` Matrix v1 shape.

Matrix v2 condition identity includes：

```text
type
runtime_variant
suite
evaluation_method
treatment_fingerprint
```

Treatment explicitly contains provider/model/reasoning/generation/contracts/context. Execution Policy is separately fingerprinted and enters Run Configuration identity together with Suite/Case selection, code revision and dirty state.

Therefore：

```text
Condition Fingerprint
!= complete Run identity
```

Historical Matrix v1 files remain compatibility/history and must not be silently reinterpreted as Matrix v2.

The L0–L5+ Runtime Capability Ladder defines attribution semantics, not a mandatory Matrix order. L1/L2/L3 are diagnostics, L4 is the first Agentic Product Runtime, and Oracle Evidence is orthogonal.

Current implementation state：

- L1 Matrix v2 formal milestone complete；
- L2 Matrix v2 formal milestone complete；
- Oracle Matrix v2 formal milestone complete；
- L4 Matrix v2 implementation, live qualification and formal milestone complete；
- L3 remains optional/unimplemented；
- Oracle-vs-L4 Pair Validator / Realization Gap is the next evaluation-analysis slice, not part of ordinary same-condition comparison。

## L4 Treatment refinement

L4 formal identity Registry-validates：

- shared Task Contract prompt；
- separate Runtime-control prompt；
- Tool Registry；
- Tool Policy；
- provider/model/reasoning/generation/context contracts。

Runtime code is not a Component Registry component; implementation provenance remains：

```text
runtime_variant + code_revision
```

Execution Policy is outer evaluation/request mechanics, not Agent Tool Policy.

For L4, current `execution_policy.retry_count` is used by the L4 path as **same-logical-provider-request retry count**. It must never be treated as whole-sample retry.

ADR 0129 also freezes L4 context identity as：

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

The L4 Runtime critical path therefore does not perform mandatory local exact-token preflight. This does not change historical L1/L2/Oracle exact-token behavior.

## Comparison interpretation

Meaningful direct or paired comparison requires explicit compatibility checks on the controls relevant to the question. When more than the intended variable changes, describe the result as a **combined treatment difference** rather than a single-feature causal uplift.

Examples：

```text
L1 vs L2
-> controlled combined difference between one-shot and fixed staged workflow Treatment

L2 vs L4
-> fixed workflow vs adaptive Runtime/evidence acquisition difference

Oracle vs L4
-> requires dedicated Pair Validator because Condition/Treatment identities intentionally differ
```

Oracle-versus-Agent realization-gap analysis is not an ordinary same-condition leaderboard comparison. A real L4 artifact now exists, so the next step is to validate whether the intended pairing controls are compatible and then report Case-level metric-vector gaps with variance preserved.

Oracle is not a theoretical upper bound. For example, the first L4 milestone's Suite Failure Type Exact Match (`88.33%`) exceeded Oracle (`85.00%`), while Oracle Evidence Hit Rate (`89.29%`) remained much higher than L4 (`65.51%`). The comparison must remain metric-specific.

## Alternatives Considered

- Compare by project version only: too coarse.
- Test every feature combination: unmanageable Cartesian grid.
- Use one global leaderboard across methods/suites/models: misleading.
- Rewrite historical Matrix v1 identities to v2: destroys reproducibility.
- Treat Oracle as a global upper bound: invalid because it is one controlled evidence-delivery intervention.

## Consequences

Current experiments have explicit Treatment and execution identities while historical runs remain interpretable. L4 adds Tool/Runtime-control component references without inventing a new top-level Runtime identity system.

Future Runtime/evidence changes must create explicit new identities rather than mutating the recorded L4 baseline. Pairwise realization-gap machinery can build on existing formal artifacts without changing either source run.

## Implementation Guide

See：

- [Evaluation Matrix, Component Registry and Formal Evaluation Identity](../evaluation/evaluation-matrix-and-component-registry.md)
- [Runtime Capability Ladder](../evaluation/runtime-capability-ladder.md)
- [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../evaluation/oracle-evidence-diagnostic-condition.md)

## Consolidates

Micro ADRs: `0014`, `0015`, `0016`, `0017`, `0023`, `0044`, `0045`, `0046`, `0047`, `0048`, `0049`, `0050`, `0051`, `0052`, `0053`, `0054`, `0055`, `0056`, `0057`, `0058`.

## Refined By

- ADR 0127 — capability ladder semantics；
- ADR 0128 — concrete L4 Treatment / Tool / retry identity；
- ADR 0129 — L4 provider-reported context-accounting identity。
