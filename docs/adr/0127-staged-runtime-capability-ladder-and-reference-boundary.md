# Staged Runtime Capability Ladder and Reference Boundary

## Status

Accepted and active.

L3 concrete V1 design is refined by ADR 0130. Its deterministic static-retrieval implementation, Component/Matrix validation, clean live `20×3` formal milestone, and evaluator-side acquisition analysis are complete. L4 concrete historical V1 design is refined by ADR 0128; L4 context accounting is further refined by ADR 0129. The L4 `self_built_react` implementation, live qualification, historical/fresh formal milestones, shared Evidence Reference Canonicalization, and Batch + Parallel Tool Policy experiment with replication are complete. The later Batch milestone refines the recommended forward Tool Policy without changing L4's rung identity or rewriting the historical single/sequential baseline.

## Context

Comparing only deterministic Pipeline and full ReAct cannot isolate model reasoning, fixed orchestration, evidence acquisition and adaptive control. DevAgentOps therefore uses a capability ladder for attribution while keeping the Product Runtime surface small.

## Decision

| Level | Capability | Role | Current state |
| --- | --- | --- | --- |
| L0 | deterministic pipeline | Product Runtime baseline | implemented; shipped runtime identity remains `pipeline_baseline` |
| L1 | `full_context_one_shot` | diagnostic/comparison | historical milestone + canonicalized fresh generation complete |
| L2 | `fixed_model_workflow` | diagnostic/comparison | historical milestone + canonicalized fresh generation complete |
| L3 | `static_retrieval` | evidence-acquisition diagnostic | **V1 implementation + live 20×3 formal milestone + acquisition analysis complete** |
| L4 | `self_built_react` | first Agentic Product Runtime | **implemented; historical/fresh milestones + Batch/Parallel replication complete** |
| L5+ | incremental Agent capabilities | future Runtime evolution / controlled conditions | evidence-gated |

The ladder is a semantic attribution model, not a mandatory implementation order. L3 does not block L4 or later evidence-driven Runtime evolution.

V1 Product Runtimes remain Fixed Pipeline and self-built ReAct. L1/L2/L3 remain diagnostic conditions. Oracle Evidence is orthogonal to the ladder and is not a rung.

Batch + Parallel is a same-L4 Tool Policy Treatment, not L5 and not a new Product Runtime.

## Task Contract vs Runtime Control

The shared Task Contract defines diagnosis taxonomy, grounding/citation requirements and final Structured Triage Report semantics.

Evidence delivery, tool surface, loop behavior, budgets and stopping belong to Runtime/Treatment identity.

For L4 ADR 0128 froze a separate Runtime-control `prompt` component for stable model-visible tool/loop/stopping instructions. The later Batch Treatment freezes its own matching Runtime-control prompt because the historical prompt explicitly constrained ToolCalls to zero-or-one.

Runtime-specific control instructions must not be hidden inside Case `runtime_input`; they remain explicit Runtime/Treatment identity.

## L1 full-context integrity

L1 must deliver the complete Agent-visible physical universe in one fixed request. It cannot truncate and retain `full_context_one_shot` identity.

The current MiniMax L1 path uses exact preflight; an infeasible complete request terminates before provider execution as context-feasibility execution failure.

This L1 rule must not be generalized to L4. ADR 0129 explicitly removes mandatory local exact-token preflight from the L4 Runtime critical path and uses provider-reported usage as observed accounting.

## Oracle is orthogonal

Oracle bypasses ordinary discovery by resolving hidden reviewed Required Evidence to source-faithful Physical Artifact content. It is not L1/L2/L3/L4 and not a Product Runtime.

Oracle execution and Oracle↔L4 Pair Analysis are complete. Oracle is not a theoretical upper bound on every metric; it is a controlled evidence-delivery intervention.

## Pi reference-architecture boundary

`earendil-works/pi` is the Agent Runtime reference studied during L4 design. Pi is:

- a reference architecture only;
- not an implementation dependency;
- not a compatibility target;
- not the source of DevAgentOps Runtime semantics.

ADR 0128 records where DevAgentOps borrows patterns and where it intentionally differs, including strict malformed-argument handling, Trace/trajectory separation, minimal tool surface, no Pi session tree and no baseline compaction.

## L4 current boundary

L4 is the self-built adaptive Runtime lineage:

```text
Model Decision
    -> Runtime policy / schema / budget validation
    -> optional read-only Tool execution
    -> ToolResult observation
    -> typed history update
    -> next Model Decision or terminal report
```

Native read-only tools remain `read`, `grep`, `find`, `ls`. Report submission is a terminal Runtime action, not a native tool. Hard Agent budget remains `max_steps=100`; automatic compaction/planner/verifier/memory/multi-agent are absent from the current read-only L4 treatment.

Historical Tool Policy reference:

```text
single + sequential + reject-all multi-call
```

Recommended forward Tool Policy:

```text
batch + parallel + independent-call handling
```

The Batch treatment keeps `runtime_variant=self_built_react`. It executes valid same-decision siblings concurrently, waits at a barrier, and materializes ToolResults in original model-authored order. Expected/malformed errors are isolated per call; unexpected Runtime/tool defects remain Sample-level infrastructure failures. There is no arbitrary ordinary ToolCall count cap, and one N-call Model Decision still consumes one step.

L4 may receive the full answer-neutral Canonical coordinate vocabulary as citation vocabulary while all Physical Artifact contents remain tool-acquired and all evaluator labels remain hidden.

L4 same-logical-request provider retry is infrastructure handling, not whole-sample retry.

### Context accounting

ADR 0129 current semantics:

```text
no mandatory local exact-token preflight
provider-reported usage = observed accounting
no automatic compaction / trimming
```

The historical L4 formal milestone observed maximum provider-reported input context of `98,893` tokens and no context-limit rejection.

## L4 empirical evidence

Historical L4 reference:

```text
20 Cases × 3 repeats = 60 planned Samples
59 scored
1 provider execution failure
Execution Coverage       = 98.33%
Failure Type Exact Match = 88.33%
Evidence Hit Rate        = 65.51%
Protocol Validity        = 81.36%
```

The historical single execution failure was a provider HTTP 529 sequence after initial + 3 frozen same-request retries. It did not expose a Runtime implementation defect.

Pair Analysis then identified citation/report realization as one distinct failure mechanism. Shared `canonical-line-range-normalization-v1` was implemented and validated through fixed-output historical replay plus fresh four-condition generation.

The subsequent independent Batch + Parallel experiment found:

```text
initial:     Model Decisions 798 -> 547 (-31.45%)
replication: Model Decisions 877 -> 571 (-34.89%)
replication: ToolCalls       809 -> 775 (-4.20%)
replication: wall time       978.27s -> 806.69s (-17.54%)
```

The initial apparent Batch quality drop did not reproduce; taxonomy and Required Fields reversed direction in the fresh back-to-back replication, and paired Case-level diagnostic intervals span zero. Current evidence therefore does not demonstrate a material Batch-induced quality regression.

## Consequences

- evaluation can distinguish broad capability classes without inflating Product Runtime count;
- L4 provides an explicit self-built kernel for controlled evolution;
- same-L4 Tool Policy changes remain attributable through frozen Treatment identities;
- references to Pi remain informative without inheriting an external framework contract;
- L1/L2/L3/Oracle/L4 milestones provide an empirical basis for capability-gap and badcase attribution;
- L5+ changes should be chosen from evidence rather than from a prewritten Agent feature checklist.

## Non-Decisions / evidence-gated work

Still not frozen here:

- L3 retrieval optimization or post-V1 quality metrics;
- dynamic context-exhaustion handling;
- future compaction / predictive budgeting;
- planner/verifier/memory designs unless later repair-loop evidence requires them;
- skills/MCP/multi-agent packaging;
- executable repair / sandbox implementation details.

Batch/parallel Tool Policy is no longer a non-decision; its frozen semantics and experiment decision are recorded in Issue #61 / PR #62 and the Batch milestone. Concrete historical L4 V1 semantics remain owned by ADR 0128 + ADR 0129 and preserved as reference evidence.

## Implementation Guide

See:

- [Runtime Capability Ladder](../evaluation/runtime-capability-ladder.md)
- [L3 Static Retrieval V1 Formal Milestone](../evaluation/milestones/l3-static-retrieval-2026-08-24.md)
- [L4 Self-built ReAct Runtime Design](../evaluation/l4-self-built-react-runtime-design.md)
- [L4 MiniMax-M3 Full-Suite Milestone](../evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md)
- [L4 Batch + Parallel ToolCalls Milestone](../evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md)
- [Shared Evidence Reference Canonicalization Milestone](../evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md)
- [Oracle Evidence Diagnostic Condition and Agent-System Realization Gap](../evaluation/oracle-evidence-diagnostic-condition.md)

## Refines

ADRs: `0002`, `0112`, `0113`, `0124`, `0125`.

## Refined By

- [ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](0129-l4-provider-reported-context-accounting.md)
- [L4 Batch + Parallel ToolCalls Milestone](../evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) — later same-L4 Tool Policy decision and replication evidence
- [L3 Static Retrieval V1 Formal Milestone](../evaluation/milestones/l3-static-retrieval-2026-08-24.md) — completed live qualification and acquisition-vs-report diagnostic
