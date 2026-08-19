# Oracle Evidence Diagnostic Condition

## Status

Accepted and implemented for the V1 Formal Suite.

Oracle execution and its MiniMax-M3 20×3 milestone are complete. A real L4 `self_built_react` 20×3 formal artifact now also exists, so the earlier sequencing guard on Oracle-vs-L4 pairing is satisfied. Generic Pair Validator / Agent-System Realization Gap machinery remains to be implemented.

## Context

DevAgentOps compares Fixed Pipeline, model-backed diagnostic conditions, ReAct, retrieval, prompt, tool-policy, and model ablations, but an Agent failure can still combine two bottlenecks: acquiring decisive evidence and reasoning correctly once evidence is available.

## Decision

V1 defines Oracle Evidence as a controlled diagnostic intervention, not a Product Runtime and not a capability-ladder rung.

For each eligible Case, Oracle bypasses ordinary evidence discovery and directly supplies the source-faithful Physical Artifact spans referenced by Human-reviewed `required_evidence_ids`. Stable Evidence IDs may be included so the model can produce ordinary report citations, but all evaluator labels, Expected Answer fields, curator reasoning, selection rationale, scorer labels, fix information, and other answer-bearing metadata remain hidden.

The Required Evidence set is Human-reviewed as inclusion-minimal and sufficient for deriving the Expected Diagnosis under the fixed diagnosis/report contract. Minimality and sufficiency are review judgments, not properties tuned from an Oracle model pass.

Evidence ordering and delivery wrappers are deterministic, versioned, and fingerprinted. Oracle runtime input is derived from the existing Case package at execution time; no independent permanent `oracle-evidence.json` is frozen.

Oracle performance is a conditional diagnostic estimate when ordinary discovery difficulty is removed. It is **not** proof of context-independent model capability and is **not** a theoretical upper bound on every Agent metric.

## Implementation Status

Issue #19 implemented the Oracle foundation and formal Matrix v2 execution path. The preserved MiniMax-M3 formal milestone completed：

```text
20 Cases × 3 repeats
60/60 scored Samples
0 execution failures
60 model calls
```

See [Oracle MiniMax-M3 Full-Suite Milestone](../evaluation/milestones/oracle-minimax-m3-full-suite-2026-08-15.md).

The implementation includes deterministic Required-Evidence resolution, source hash verification, answer-neutral delivery guards, explicit evidence-delivery Treatment identity, exact context preflight, and reuse of the existing scheduler/persistence/Trace/scorer path.

L4 later completed its own MiniMax-M3 formal milestone：

```text
20 Cases × 3 repeats
59/60 scored Samples
1 provider execution failure
Failure Type Exact Match = 88.33%
Evidence Hit Rate = 65.51%
Protocol Validity = 81.36%
```

See [L4 MiniMax-M3 Full-Suite Milestone](../evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md).

## Agent-System Realization Gap

The earlier decision to defer generic Oracle-versus-Agent pairing until a real L4 Agent Product Runtime artifact exists has now served its purpose. The artifact exists; gap implementation is now allowed, but must remain a separate controlled evaluation slice rather than being folded into Oracle or L4 execution.

For a valid higher-is-better diagnosis metric `m`：

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

It must be reported as metric-specific paired differences, not a composite capability score.

Pairing is valid only when declared controls such as Suite/Case, model, diagnosis Task Contract/report contract, scorer, inference settings, and other relevant Treatment fields are compatible and the remaining intended intervention is explicit.

The first implementation should therefore introduce a **Pair Validator** before computing gaps. If controls differ beyond the intended intervention, report a combined difference rather than a false isolated causal claim.

Operational signals such as tool count, Agent steps, token usage and latency may explain a gap, but they do not belong inside a model-capability composite score.

## L4 Refinement

ADR 0128 allows L4 V1 to receive the complete **answer-neutral Canonical coordinate vocabulary** at episode start as citation vocabulary while withholding all Physical Artifact content until tools are used and withholding all Required Evidence labels/evaluator artifacts.

This does not collapse L4 into Oracle：

- L4 receives all neutral coordinates but must discover physical facts itself；
- Oracle receives only the reviewed Required Evidence source content and bypasses discovery。

The first L4 formal milestone also shows why this distinction matters operationally: several L4 reports inspected useful physical spans but invented unavailable Canonical Evidence IDs in the final report. A future coordinate-assistance ablation would therefore be an explicit new Agent-visible behavior, not Oracle behavior and not a silent evaluator repair.

## Alternatives Considered

- Infer model capability from ReAct versus Pipeline alone: evidence acquisition remains entangled.
- Expose Expected Answer: this becomes answer reproduction and violates the Trusted Evaluator boundary.
- Treat Oracle as a Product Runtime: incorrect; it is an evaluator intervention.
- Collapse gaps into one score: V1 has no defensible composite weighting.
- Treat Oracle as a strict upper bound: invalid; its evidence-delivery intervention can help some metrics while adaptive investigation may outperform it on others.

## Consequences

Oracle provides a clean evidence-conditioned diagnostic and preserves one Evidence Ground Truth source of truth. With L4 now available, the project can measure realization gaps while retaining Case-level trajectory evidence for attribution.

The comparison still requires careful pairing and variance interpretation before causal claims are made.

## Implementation Guide

See [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../evaluation/oracle-evidence-diagnostic-condition.md).

## Refines

ADRs: `0113`, `0115`, `0116`, `0118`, `0122`, `0123`, `0125`, `0126`.

## Refined By

- [ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md) for L4 coordinate-vocabulary visibility and Agent pairing boundary.
- [ADR 0129: L4 Provider-Reported Context Accounting](0129-l4-provider-reported-context-accounting.md) for current L4 context-accounting semantics.
