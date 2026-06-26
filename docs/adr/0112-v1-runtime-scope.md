# V1 Runtime Scope

## Status

Accepted.

## Context

DevAgentOps needs a V1 that demonstrates a real CI/Test Failure Triage AgentOps loop without turning the first implementation into a full agent platform. The project also needs later comparison points for framework runtimes, MCP, skill packages, multi-agent workflows, and memory.

## Decision

V1 will implement a fixed pipeline baseline and a self-built single-agent ReAct runtime as separate runtime variants. V1 will not implement real MCP integration, full skill packaging, multi-agent triage, or cross-run agent memory. These capabilities remain explicit future runtime variants, ablation conditions, or candidate conditions, and V1 will record `mcp_server_set_version: none_v1` and `skill_registry_version: none_v1` where applicable.

## Alternatives Considered

- Build every advanced capability in V1. This would obscure the core runtime, trace, eval, tool policy, retrieval, and badcase loop.
- Treat each V1/V2 as a separate copied project directory. This would make evaluation and comparison harder than treating implementations as runtime variants.

## Consequences

V1 stays small enough to implement and evaluate. Future features can still be compared fairly by entering the evaluation matrix as explicit runtime variants, component versions, or ablation conditions.

## Implementation Notes

- Runtime variants include `pipeline_baseline` and `self_built_react`.
- Defer real MCP server lifecycle, tool discovery, auth, and schema drift.
- Defer skill package loading and dependency management; keep V1 tool registry separate from skills.
- Do not expose previous run results, badcases, or eval artifacts as agent memory.

## Consolidates

Micro ADRs: `0070`, `0071`, `0072`, `0073`, `0074`.
