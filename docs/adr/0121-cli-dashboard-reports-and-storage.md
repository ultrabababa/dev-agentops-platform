# CLI, Dashboard, Reports, and Storage

## Status

Accepted. Refined for L4 trajectory persistence by ADR 0128.

## Context

Formal evaluation should be repeatable and scriptable. The dashboard is useful for reviewing persisted results but is not the V1 job-orchestration layer.

## Decision

V1 formal evaluation is CLI-driven. SQLite remains the queryable source for run/sample evaluation state and Trace events; generated JSON/Markdown artifacts remain ignored by default unless a milestone is deliberately exported.

L4 adds one important storage distinction:

```text
Run Trace
= structured execution/lifecycle events

Agent Trajectory
= complete ordered per-sample User/Assistant/ToolResult messages
```

The complete L4 trajectory must be persisted separately from Trace so badcase analysis can reconstruct the Agent's actual conversation without turning the Trace event table into a transcript dump.

## L4 persistence requirement

Use the smallest sample-scoped extension compatible with existing run/sample ownership and Alembic migrations. A recommended shape is one row per message:

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

The exact table/file naming is an implementation detail, but the following are frozen:

- trajectory is linear and sample-scoped;
- full finalized AssistantMessage content, including provider-returned thinking and opaque continuation fields needed for replay, is preserved;
- Trace does not duplicate complete message bodies;
- no Pi-style session tree, branch, resume or conversation-management subsystem is added in V1.

## Consequences

- operational Trace queries remain compact/readable;
- L4 badcase review can inspect exact tool/thinking/message progression;
- the existing scheduler, Sample identity and SQLite ownership model remain reusable;
- trajectory persistence does not become Agent memory or cross-run state.

## Implementation Notes

- formal runner still runs `eval doctor` first;
- existing run/sample outcomes, reports, scores, aggregates and Trace remain intact;
- L4 trajectory persistence is additive and must not rewrite historical L1/L2/Oracle rows;
- dashboard support for rendering full L4 trajectories is optional for Issue #52 unless needed for acceptance; persistence/auditability is required;
- generated reports/artifacts remain ignored unless deliberately exported as milestones.

## Consolidates

Micro ADRs: `0088`, `0089`, `0091`, `0092`, `0093`, `0094`, `0095`.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md).
