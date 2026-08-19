# Staged Runtime Capability Ladder and Reference Boundary

## Status

Accepted and active.

L4 concrete design is refined by ADR 0128; L4 context accounting is further refined by ADR 0129. The L4 `self_built_react` implementation, live qualification and first MiniMax-M3 20×3 formal milestone are complete.

## Context

Comparing only deterministic Pipeline and full ReAct cannot isolate model reasoning, fixed orchestration, evidence acquisition and adaptive control. DevAgentOps therefore uses a capability ladder for attribution while keeping the Product Runtime surface small.

## Decision

| Level | Capability | Role | Current state |
| --- | --- | --- | --- |
| L0 | deterministic pipeline | Product Runtime baseline | implemented; shipped runtime identity remains `pipeline_baseline` |
| L1 | `full_context_one_shot` | diagnostic/comparison | MiniMax-M3 formal milestone complete |
| L2 | `fixed_model_workflow` | diagnostic/comparison | MiniMax-M3 formal milestone complete |
| L3 | `static_retrieval` | evidence-acquisition diagnostic | not implemented; optional and not required before L4/L5+ |
| L4 | `self_built_react` | first Agentic Product Runtime | **implemented; live qualification + formal milestone complete** |
| L5+ | incremental Agent capabilities | future Runtime evolution / controlled conditions | evidence-gated |

The ladder is a semantic attribution model, not a mandatory implementation order. L3 does not block L4 or later evidence-driven Runtime evolution.

V1 Product Runtimes remain Fixed Pipeline and self-built ReAct. L1/L2/L3 remain diagnostic conditions. Oracle Evidence is orthogonal to the ladder; its MiniMax-M3 formal milestone is complete.

## Task Contract vs Runtime Control

The shared Task Contract defines diagnosis taxonomy, grounding/citation requirements and final Structured Triage Report semantics.

Evidence delivery, tool surface, loop behavior, budgets and stopping belong to Runtime/Treatment identity.

For L4 ADR 0128 freezes a separate Runtime-control `prompt` component for stable model-visible tool/loop/stopping instructions, rather than hiding them in Case `runtime_input` or Tool Policy.

## L1 full-context integrity

L1 must deliver the complete Agent-visible physical universe in one fixed request. It cannot truncate and retain `full_context_one_shot` identity.

The current MiniMax L1 path uses exact preflight; an infeasible complete request terminates before provider execution as context-feasibility execution failure.

This L1 rule must not be generalized to L4. ADR 0129 explicitly removes mandatory local exact-token preflight from the L4 Runtime critical path and uses provider-reported usage as observed accounting.

## Oracle is orthogonal

Oracle bypasses ordinary discovery by resolving hidden reviewed Required Evidence to source-faithful Physical Artifact content. It is not L1/L2/L3/L4 and not a Product Runtime.

Oracle execution is implemented. The earlier sequencing rule deferred generic Oracle-vs-L4 pairing / realization-gap machinery until a real L4 formal artifact existed. That precondition is now satisfied, so Pair Validator / gap analysis is current work rather than blocked future work.

Oracle is not a theoretical upper bound on every metric. It is a controlled evidence-delivery intervention.

## Pi reference-architecture boundary

`earendil-works/pi` is the Agent Runtime reference studied during L4 design. Pi is：

- a reference architecture only；
- not an implementation dependency；
- not a compatibility target；
- not the source of DevAgentOps Runtime semantics。

ADR 0128 records where DevAgentOps borrows patterns and where it intentionally differs, including strict malformed-argument handling, Trace/trajectory separation, minimal tool surface, no Pi session tree and no baseline compaction.

## L4 current boundary

L4 V1 is the smallest self-built adaptive Runtime：

```text
Model Decision
    -> Runtime policy / schema / budget validation
    -> optional read-only Tool
    -> ToolResult
    -> typed history update
    -> next Model Decision or terminal report
```

Native tools：`read`, `grep`, `find`, `ls`.

Report submission is a terminal Runtime action, not a native tool. Baseline Tool Policy is `single + sequential`; hard Agent budget is `max_steps=100`; automatic compaction/planner/verifier/memory/multi-agent are absent from the baseline.

L4 may receive the full answer-neutral Canonical coordinate vocabulary as citation vocabulary while all Physical Artifact contents remain tool-acquired and all evaluator labels remain hidden.

L4 same-logical-request provider retry is infrastructure handling, not whole-sample retry.

### Context accounting

ADR 0129 current semantics：

```text
no mandatory local exact-token preflight
provider-reported usage = observed accounting
no automatic compaction / trimming
```

The first L4 formal milestone observed maximum provider-reported input context of `98,893` tokens and no context-limit rejection.

## L4 formal evidence

The first controlled MiniMax-M3 L4 milestone completed：

```text
20 Cases × 3 repeats = 60 planned Samples
59 scored
1 provider execution failure
Execution Coverage       = 98.33%
Failure Type Exact Match = 88.33%
Evidence Hit Rate        = 65.51%
Protocol Validity        = 81.36%
```

The single execution failure was a provider HTTP 529 sequence after initial + 3 frozen same-request retries. It did not expose a Runtime implementation defect.

The milestone also exposed a baseline weakness: protocol-invalid outputs are dominated by invented/unknown Evidence IDs, even when the model has inspected relevant physical spans. This provides evidence for future controlled citation-coordinate assistance experiments.

## Consequences

- evaluation can distinguish broad capability classes without inflating Product Runtime count；
- L4 now provides an explicit self-built kernel for future controlled evolution；
- references to Pi remain informative without inheriting an external framework contract；
- L1/L2/Oracle/L4 milestones now provide a real empirical basis for capability-gap and badcase attribution；
- L5+ changes should be chosen from evidence rather than from a prewritten Agent feature checklist。

## Non-Decisions / evidence-gated work

Still not frozen here：

- L3 retrieval internals；
- exact Oracle-vs-L4 Pair Validator / gap-report implementation shape；
- dynamic context-exhaustion handling；
- future compaction / predictive budgeting；
- planner/verifier/memory designs；
- batch/parallel Tool Policy；
- skills/MCP/multi-agent packaging。

Concrete L4 semantics are no longer a non-decision; they are owned by ADR 0128 + ADR 0129 and validated by the recorded milestone.

## Implementation Guide

See：

- [Runtime Capability Ladder](../evaluation/runtime-capability-ladder.md)
- [L4 Self-built ReAct Runtime Design](../evaluation/l4-self-built-react-runtime-design.md)
- [L4 MiniMax-M3 Full-Suite Milestone](../evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md)
- [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../evaluation/oracle-evidence-diagnostic-condition.md)

## Refines

ADRs: `0002`, `0112`, `0113`, `0124`, `0125`.

## Refined By

- [ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](0129-l4-provider-reported-context-accounting.md)
