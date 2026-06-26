# Build a Minimal Run Trace Before External Observability

V1 will persist a minimal internal run trace with structured events for run lifecycle, LLM calls, tool calls, report submission, evaluation, and failures. Full observability platforms such as LangSmith or Langfuse are deferred until the project has a stable trace contract and triage eval loop, so external tooling can become an export or comparison layer rather than replacing the core AgentOps implementation.
