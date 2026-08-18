# Oracle Evidence Diagnostic Condition

## Status

Accepted and implemented for the V1 Formal Suite.

## Context

DevAgentOps compares Fixed Pipeline, model-backed diagnostic conditions, ReAct, retrieval, prompt, tool-policy, and model ablations, but an Agent failure can still combine two bottlenecks: acquiring decisive evidence and reasoning correctly once evidence is available.

## Decision

V1 defines Oracle Evidence as a controlled diagnostic intervention, not a Product Runtime and not a capability-ladder rung.

For each eligible Case, Oracle bypasses ordinary evidence discovery and directly supplies the source-faithful Physical Artifact spans referenced by Human-reviewed `required_evidence_ids`. Stable Evidence IDs may be included so the model can produce ordinary report citations, but all evaluator labels, Expected Answer fields, curator reasoning, selection rationale, scorer labels, fix information, and other answer-bearing metadata remain hidden.

The Required Evidence set is Human-reviewed as inclusion-minimal and sufficient for deriving the Expected Diagnosis under the fixed diagnosis/report contract. Minimality and sufficiency are review judgments, not properties tuned from an Oracle model pass.

Evidence ordering and delivery wrappers are deterministic, versioned, and fingerprinted. Oracle runtime input is derived from the existing Case package at execution time; no independent permanent `oracle-evidence.json` is frozen.

Oracle performance is a conditional diagnostic estimate when ordinary discovery difficulty is removed. It is not proof of context-independent model capability.

## Implementation Status

Issue #19 implemented the Oracle foundation and formal Matrix v2 execution path. The preserved MiniMax-M3 formal milestone completed:

```text
20 Cases × 3 repeats
60/60 scored Samples
0 execution failures
60 model calls
```

See [Oracle MiniMax-M3 Full-Suite Milestone](../evaluation/milestones/oracle-minimax-m3-full-suite-2026-08-15.md).

The implementation includes deterministic Required-Evidence resolution, source hash verification, answer-neutral delivery guards, explicit evidence-delivery Treatment identity, exact context preflight, and reuse of the existing scheduler/persistence/Trace/scorer path.

## Agent-System Realization Gap

The generic Oracle-versus-Agent pairing/gap machinery remains intentionally deferred until a real L4 Agent Product Runtime formal artifact exists.

For a valid higher-is-better diagnosis metric `m`, the future diagnostic remains:

```text
realization_gap(case, m)
  = oracle_score(case, m) - agent_score(case, m)
```

It must be reported as metric-specific paired differences, not a composite capability score. Pairing is valid only when declared controls such as Suite/Case, model, diagnosis Task Contract/report contract, scorer, inference settings, and other relevant treatment fields are compatible and the remaining intended intervention is explicit.

## L4 Refinement

ADR 0128 allows L4 V1 to receive the complete **answer-neutral Canonical coordinate vocabulary** at episode start as citation vocabulary while withholding all Physical Artifact content until tools are used and withholding all Required Evidence labels/evaluator artifacts.

This does not collapse L4 into Oracle:

- L4 receives all neutral coordinates but must discover physical facts itself;
- Oracle receives only the reviewed Required Evidence source content and bypasses discovery.

## Alternatives Considered

- Infer model capability from ReAct versus Pipeline alone: evidence acquisition remains entangled.
- Expose Expected Answer: this becomes answer reproduction and violates the Trusted Evaluator boundary.
- Treat Oracle as a Product Runtime: incorrect; it is an evaluator intervention.
- Collapse gaps into one score: V1 has no defensible composite weighting.

## Consequences

Oracle provides a clean evidence-conditioned diagnostic and preserves one Evidence Ground Truth source of truth. It also requires careful pairing and variance interpretation before causal claims are made.

## Implementation Guide

See [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../evaluation/oracle-evidence-diagnostic-condition.md).

## Refines

ADRs: `0113`, `0115`, `0116`, `0118`, `0122`, `0123`, `0125`, `0126`.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md) for L4 coordinate-vocabulary visibility and future pairing boundary.
