# V1 Runtime Scope

## Status

Accepted.

## Context

DevAgentOps needs a V1 that demonstrates a real CI/Test Failure Triage AgentOps loop without turning the first implementation into a full agent platform. The project also needs later comparison points for framework runtimes, MCP, skill packages, multi-agent workflows, and memory.

## Decision

V1 will implement a fixed pipeline baseline and a self-built single-agent ReAct runtime as its two Product Runtime variants. Model-backed full-context one-shot, fixed model workflow, and static retrieval may be implemented as diagnostic/comparison conditions; they do not expand the Product Runtime list. ReAct is the first Agentic Runtime and the start of the self-built Agent Runtime kernel lineage. The capability ladder guides attribution but does not freeze implementation order, including whether static retrieval precedes ReAct.

V1 will not implement real MCP integration, full skill packaging, multi-agent triage, or cross-run agent memory. These capabilities remain explicit future runtime variants, ablation conditions, or candidate conditions, and V1 will record `mcp_server_set_version: none_v1` and `skill_registry_version: none_v1` where applicable.

## Alternatives Considered

- Build every advanced capability in V1. This would obscure the core runtime, trace, eval, tool policy, retrieval, and badcase loop.
- Treat each V1/V2 as a separate copied project directory. This would make evaluation and comparison harder than treating implementations as runtime variants.

## Consequences

V1 stays small enough to implement and evaluate. Future features can still be compared fairly by entering the evaluation matrix as explicit runtime variants, component versions, or ablation conditions.

## Implementation Notes

- Runtime variants include `pipeline_baseline` and `self_built_react`.
- Preserve the shipped `pipeline_baseline` identity; the L0 name `deterministic_pipeline` is a capability label, not a runtime rename.
- Treat L1/L2/L3 as diagnostic/comparison conditions and Oracle Evidence as an orthogonal diagnostic intervention.
- Defer real MCP server lifecycle, tool discovery, auth, and schema drift.
- Defer skill package loading and dependency management; keep V1 tool registry separate from skills.
- Do not expose previous run results, badcases, or eval artifacts as agent memory.

## Consolidates

Micro ADRs: `0070`, `0071`, `0072`, `0073`, `0074`.

## Refined By

[ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](0127-staged-runtime-capability-ladder-and-reference-boundary.md).
