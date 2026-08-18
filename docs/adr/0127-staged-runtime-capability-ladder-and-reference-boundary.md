# Staged Runtime Capability Ladder and Reference Boundary

## Status

Accepted. L4 concrete design is now refined by ADR 0128.

## Context

Comparing only deterministic Pipeline and full ReAct cannot isolate model reasoning, fixed orchestration, evidence acquisition and adaptive control. DevAgentOps therefore uses a capability ladder for attribution while keeping the Product Runtime surface small.

## Decision

| Level | Capability | Role | Current state |
| --- | --- | --- | --- |
| L0 | deterministic pipeline | Product Runtime baseline | implemented; shipped runtime identity remains `pipeline_baseline` |
| L1 | `full_context_one_shot` | diagnostic/comparison | MiniMax-M3 formal milestone complete |
| L2 | `fixed_model_workflow` | diagnostic/comparison | MiniMax-M3 formal milestone complete |
| L3 | `static_retrieval` | evidence-acquisition diagnostic | not implemented; not required before L4 |
| L4 | `self_built_react` | first Agentic Product Runtime | ADR 0128/design Human-frozen; implementation pending |
| L5+ | incremental Agent capabilities | future Runtime evolution / controlled conditions | deferred |

The ladder is a semantic attribution model, not a mandatory implementation order. L3 does not block L4.

V1 Product Runtimes remain Fixed Pipeline and self-built ReAct. L1/L2/L3 remain diagnostic conditions. Oracle Evidence is orthogonal to the ladder and its MiniMax formal milestone is already complete.

## Task Contract vs Runtime Control

The shared Task Contract defines diagnosis taxonomy, grounding/citation requirements and final Structured Triage Report semantics.

Evidence delivery, tool surface, loop behavior, budgets and stopping belong to Runtime/Treatment identity.

For L4 ADR 0128 concretely freezes a separate Runtime-control `prompt` component for stable model-visible tool/loop/stopping instructions, rather than hiding them in Case `runtime_input` or Tool Policy.

## L1 full-context integrity

L1 must deliver the complete Agent-visible physical universe in one fixed request. It cannot truncate and retain `full_context_one_shot` identity.

The current MiniMax path uses exact preflight; an infeasible complete request terminates before provider execution as context-feasibility execution failure.

## Oracle is orthogonal

Oracle bypasses ordinary discovery by resolving hidden reviewed Required Evidence to source-faithful Physical Artifact content. It is not L1/L2/L3/L4 and not a Product Runtime.

Oracle execution is implemented; generic Oracle-vs-L4 pairing / realization-gap machinery waits for a real L4 formal artifact.

## Pi reference-architecture boundary

`earendil-works/pi` is the current canonical Agent Runtime reference. Pi is:

- a reference architecture only;
- not an implementation dependency;
- not a compatibility target;
- not the source of DevAgentOps Runtime semantics.

Pi has now been concretely studied during L4 design. ADR 0128 records where DevAgentOps borrows patterns and where it intentionally differs, including strict malformed-argument handling, Trace/trajectory separation, minimal tool surface, no Pi session tree and no baseline compaction.

Earlier wording that said a Pi reference matrix or concrete ReAct design would be created “later” is superseded by ADR 0128 and the L4 implementation guide.

## L4 current boundary

L4 V1 is the smallest self-built adaptive Runtime:

```text
Model Decision
    -> Runtime policy/schema/budget validation
    -> optional read-only Tool
    -> ToolResult
    -> typed history update
    -> next Model Decision or terminal report
```

Native tools: `read`, `grep`, `find`, `ls`. Report submission is a terminal Runtime action, not a native tool. Baseline Tool Policy is `single + sequential`, hard Agent budget is `max_steps=100`, and automatic compaction/planner/verifier/memory/multi-agent are deferred.

L4 may receive the full answer-neutral Canonical coordinate vocabulary as citation vocabulary while all Physical Artifact contents remain tool-acquired and all evaluator labels remain hidden.

## Consequences

- evaluation can distinguish broad capability classes without inflating Product Runtime count;
- L4 can evolve from an explicit self-built kernel;
- references to Pi remain informative without inheriting an external framework contract;
- current L1/L2/Oracle milestones provide pre-L4 diagnostic baselines.

## Non-Decisions

Still not frozen here:

- L3 retrieval internals;
- L5+ capability numbering/packaging;
- dynamic context-exhaustion handling;
- future compaction/planning/verifier/memory designs;
- generic Oracle-vs-L4 gap implementation.

Concrete L4 semantics are not a non-decision anymore; they are owned by ADR 0128.

## Implementation Guide

See [Runtime Capability Ladder](../evaluation/runtime-capability-ladder.md) and [L4 Self-built ReAct Runtime Design](../evaluation/l4-self-built-react-runtime-design.md).

## Refines

ADRs: `0002`, `0112`, `0113`, `0124`, `0125`.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md).
