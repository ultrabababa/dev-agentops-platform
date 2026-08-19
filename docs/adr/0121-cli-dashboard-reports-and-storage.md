# CLI, Dashboard, Reports, and Storage

## Status

Accepted and implemented. Refined for L4 trajectory persistence by ADR 0128.

## Context

Formal evaluation should be repeatable and scriptable. The dashboard is useful for reviewing persisted results but is not the V1 job-orchestration layer.

## Decision

V1 formal evaluation is CLI-driven. SQLite remains the queryable source for run/sample evaluation state and Trace events; generated JSON/Markdown artifacts remain ignored by default unless a milestone is deliberately exported.

L4 adds one important storage distinction：

```text
Run Trace
= structured execution / lifecycle events

Agent Trajectory
= complete ordered per-sample User / Assistant / ToolResult messages
```

The complete L4 trajectory is persisted separately from Trace so badcase analysis can reconstruct the Agent's actual model-visible conversation without turning the Trace event table into a transcript dump.

## L4 trajectory persistence

Issue #52 implemented the sample-scoped trajectory table through Alembic migration `0006_add_sample_trajectory_messages.py`.

Current logical shape：

```text
evaluation_sample_trajectory_messages
- run_id
- case_id
- repeat_index
- message_index
- message_role
- message_json
- message_sha256
```

The following boundaries remain frozen：

- trajectory is linear and sample-scoped；
- full finalized AssistantMessage content, including provider-returned thinking and opaque continuation fields needed for replay, is preserved；
- Trace does not duplicate complete message bodies；
- trajectory rows use existing run/sample ownership；
- no Pi-style session tree, branch, resume or conversation-management subsystem is added in V1；
- trajectory persistence is not Agent memory and creates no cross-run state。

## Formal-run evidence

The first L4 20×3 milestone exercised the storage path with real multi-turn trajectories, including：

- hundreds of Model Decisions；
- native ToolCalls and ToolResults；
- provider continuation state；
- recoverable tool/policy errors；
- one exhausted provider-retry infrastructure failure；
- final scored reports and invalid-report capability terminals。

The formal run completed without a persistence-level execution failure, providing end-to-end evidence that trajectory storage coexists with the existing Trace, scheduler and formal artifacts.

## Consequences

- operational Trace queries remain compact/readable；
- L4 badcase review can inspect exact tool/thinking/message progression；
- the existing scheduler, Sample identity and SQLite ownership model remain reusable；
- full Agent conversation evidence is available for Oracle-vs-L4 gap attribution；
- trajectory persistence does not become Agent memory or a product session subsystem。

## Implementation Notes

- formal runner still runs `eval doctor` first；
- existing run/sample outcomes, reports, scores, aggregates and Trace remain intact；
- L4 trajectory persistence is additive and does not rewrite historical L1/L2/Oracle rows；
- dashboard rendering of full trajectories is optional; persistence/auditability is the contract；
- generated reports/artifacts remain ignored unless deliberately exported as milestones；
- future gap/badcase tooling should read the existing persisted trajectory rather than inventing a second transcript store。

## Consolidates

Micro ADRs: `0088`, `0089`, `0091`, `0092`, `0093`, `0094`, `0095`.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md).
