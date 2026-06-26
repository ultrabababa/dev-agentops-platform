# Do Not Store Full Chain of Thought

V1 run traces will not store full hidden chain-of-thought. Trace events will capture auditable behavior such as lifecycle events, model call metadata, visible model outputs, tool call requests and results, selected evidence, structured report submission, evaluation, and failures, avoiding dependence on provider-specific hidden reasoning text while preserving the information needed for AgentOps review.
