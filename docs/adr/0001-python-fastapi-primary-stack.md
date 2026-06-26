# Use Python and FastAPI as the Primary Stack

DevAgentOps will use Python and FastAPI as the primary stack for V1-V3 because the core work is agent runtime, tool orchestration, retrieval, trace collection, evaluation, and dataset processing. Java, Spring Boot, and Go are deferred so the project does not dilute its AgentOps learning loop across multiple backend stacks; Go may be introduced later for standalone services such as a trace collector, tool gateway, CI log ingestion service, sandbox runner, or MCP sidecar when those workloads justify it.
