# Trace, Step Protocol, and Tool Calling

## Status

Accepted.

## Context

DevAgentOps needs auditable trace behavior without depending on hidden chain-of-thought or brittle free-form ReAct transcripts.

## Decision

V1 run traces will capture structured execution events and visible outputs without treating Trace as a full conversation store. The self-built ReAct runtime will use a structured step protocol. Provider-native tool calling is the default tool call protocol when supported, with strict JSON action fallback available but outside the minimal V1 matrix unless needed.

ADR 0128 refines the L4 persistence boundary: the complete finalized provider-neutral Agent trajectory is persisted separately from Trace for badcase analysis, including provider-returned thinking content and opaque provider continuation fields required for replay. This provider-exposed trajectory evidence is not deterministic score input and is not treated as hidden/private neural chain-of-thought. Trace remains the compact lifecycle/execution record and should not duplicate complete message bodies.

## Alternatives Considered

- Store the complete conversation only inside Trace. This duplicates message state into an event log and makes replay/audit semantics unnecessarily coupled to event structure.
- Depend on hidden/private chain-of-thought. This is unstable, provider-specific, and not necessary for AgentOps review.
- Require literal Thought/Action/Observation text. This is brittle and less comparable with function-calling or future framework runtimes.
- Use JSON fallback as default even when native tool calling exists. Native tool calling gives better schema alignment and trace structure.

## Consequences

Traces remain reviewable, structured, and provider-portable. L4 badcase analysis can reconstruct the exact model-visible trajectory without turning Trace into a transcript database. Tool call protocol differences remain explicit in evaluation conditions and run manifests.

## Implementation Notes

- Trace events include lifecycle, model-call attempts/completions, tool calls, observations, budgets, report submission, evaluation, and failures.
- Model call events record metadata such as prompt/version/hash or equivalent request identity, token counts, latency, response/request IDs, stop reason, and tool-call execution metadata.
- Complete finalized `UserMessage` / `AssistantMessage` / `ToolResultMessage` bodies belong to the L4 sample trajectory persistence defined by ADR 0128, not to duplicated Trace payloads.
- Provider-returned thinking may be stored in that trajectory for diagnostic analysis when the provider exposes it; it is not scored and is not claimed to be faithful hidden neural reasoning.
- JSON action fallback remains a portability/ablation option, not part of the minimal L4 V1 baseline.
- SSE observes existing runs created by CLI; it does not imply dashboard-triggered jobs.

## Consolidates

Micro ADRs: `0096`, `0097`, `0098`, `0099`, `0100`, `0101`.

## Refined By

[ADR 0128: L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md).
