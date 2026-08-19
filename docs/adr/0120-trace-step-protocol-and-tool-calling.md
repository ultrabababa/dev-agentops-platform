# Trace, Step Protocol, and Tool Calling

## Status

Accepted and implemented for the L4 V1 path.

## Context

DevAgentOps needs auditable Runtime behavior without depending on hidden chain-of-thought or brittle free-form ReAct transcripts.

## Decision

V1 Run Trace captures structured execution events and visible execution metadata without treating Trace as a full conversation store.

L4 `self_built_react` uses typed provider-neutral messages and provider-native structured ToolCalls through the MiniMax adapter. Strict JSON action fallback remains a portability/ablation option, not part of the L4 baseline.

ADR 0128 refines the persistence boundary：the complete finalized provider-neutral Agent trajectory is persisted separately from Trace for badcase analysis, including provider-returned thinking content and opaque provider continuation fields required for replay.

Provider-exposed thinking is diagnostic trajectory evidence only. It is not deterministic score input and is not treated as hidden/private neural chain-of-thought.

Trace remains the compact lifecycle/execution record and does not duplicate complete message bodies.

## Current L4 step protocol

```text
Model Decision / AssistantMessage
    -> Runtime action interpretation
    -> optional ToolCall validation / policy
    -> Tool execution
    -> ToolResultMessage
    -> next Model Decision or terminal report
```

One Agent step is one successfully returned provider completion normalized into a valid `AssistantMessage`.

Failed provider attempts are Trace events but do not enter Agent trajectory and do not consume `max_steps`.

Tool-call recovery is explicit：

- unknown/disallowed tool -> error ToolResult；
- schema-invalid/malformed arguments -> error ToolResult；
- `length + ToolCall` -> execute none, error ToolResult(s)；
- multiple ToolCalls under baseline `single` -> execute none, close every call ID with policy-error ToolResult；
- expected tool-domain failure -> error ToolResult；
- unexpected Runtime/tool defect -> infrastructure failure, not ToolResult。

## Trace vs trajectory

```text
Trace
= request attempts / usage / latency / IDs
+ tool lifecycle / errors / truncation
+ budgets / terminals / infrastructure failures
+ evaluation lifecycle

Agent trajectory
= complete ordered UserMessage / AssistantMessage / ToolResultMessage history
```

The first L4 formal milestone exercised both records across `802` successful Model Decisions and `733` executed tool calls started, including real provider retry, policy rejection, tool argument errors, truncation, and scored invalid-report terminals.

## Alternatives Considered

- Store the complete conversation only inside Trace: duplicates message state into an event log and couples replay/audit semantics to event structure.
- Depend on hidden/private chain-of-thought: unstable, provider-specific, and unnecessary for AgentOps review.
- Require literal Thought/Action/Observation text: brittle and less comparable with function-calling runtimes.
- Use JSON fallback as default even when native tool calling exists: native tool calling provides stronger schema/protocol alignment.

## Consequences

Traces remain reviewable, structured, and provider-portable. L4 badcase analysis can reconstruct the exact model-visible trajectory without turning Trace into a transcript database.

Tool call protocol differences remain explicit Treatment/runtime behavior rather than hidden implementation details.

The separation also enables future Oracle-vs-L4 gap attribution to ask whether decisive evidence actually entered model-visible history before the final diagnosis.

## Implementation Notes

- Trace events include lifecycle, model-call attempts/completions, tool calls, observations, budgets, report submission, evaluation, and failures.
- Model call events record usage/token metadata, latency, response/request IDs, stop reason, and applicable tool-call execution metadata without copying complete message bodies.
- Complete finalized `UserMessage` / `AssistantMessage` / `ToolResultMessage` bodies belong to sample trajectory persistence.
- Provider-returned thinking may be stored in trajectory for diagnostic analysis; it is not scored and is not claimed to be faithful hidden neural reasoning.
- JSON action fallback remains a portability/ablation option, not part of the L4 V1 baseline.
- SSE observes existing runs created by CLI; it does not imply dashboard-triggered jobs.
- ADR 0129 changes L4 context accounting, not the Trace/trajectory boundary: successful provider usage is recorded as observed accounting without a mandatory local preflight gate.

## Consolidates

Micro ADRs: `0096`, `0097`, `0098`, `0099`, `0100`, `0101`.

## Refined By

- [ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](0129-l4-provider-reported-context-accounting.md)
