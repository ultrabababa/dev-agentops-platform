# Trace, Step Protocol, and Tool Calling

## Status

Accepted.

## Context

DevAgentOps needs auditable trace behavior without depending on hidden chain-of-thought or brittle free-form ReAct transcripts.

## Decision

V1 run traces will capture structured events and visible outputs, not full hidden chain-of-thought. The self-built ReAct runtime will use a structured step protocol. Provider-native tool calling is the default tool call protocol when supported, with strict JSON action fallback available but outside the minimal V1 matrix unless needed.

## Alternatives Considered

- Store full chain-of-thought. This is unstable, provider-specific, and not necessary for AgentOps review.
- Require literal Thought/Action/Observation text. This is brittle and less comparable with function-calling or future framework runtimes.
- Use JSON fallback as default even when native tool calling exists. Native tool calling gives better schema alignment and trace structure.

## Consequences

Traces remain reviewable, structured, and provider-portable. Tool call protocol differences are explicit in evaluation conditions and run manifests.

## Implementation Notes

- Trace events include lifecycle, model calls, tool calls, observations, selected evidence, report submission, evaluation, and failures.
- Model call events record metadata such as prompt/version/hash, token counts, latency, finish reason, visible output, and tool call JSON.
- Step protocol records step index, tool call, arguments, observation summary, selected evidence, and final report.
- JSON action fallback is implemented for portability and explicit ablations, not included in the minimal V1 matrix by default.
- SSE observes existing runs created by CLI; it does not imply dashboard-triggered jobs.

## Consolidates

Micro ADRs: `0096`, `0097`, `0098`, `0099`, `0100`, `0101`.
