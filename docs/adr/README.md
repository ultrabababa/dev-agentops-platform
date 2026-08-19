# ADR Index

This directory keeps active architecture decisions for DevAgentOps.

> Current-state note (2026-08-19): L4 `self_built_react` is implemented and has completed historical/fresh formal milestones. ADR 0129 supersedes only ADR 0128's mandatory **L4 local exact-token preflight** requirement. ADR 0128 remains the frozen historical L4 V1 base contract; the later L4 Batch + Parallel ToolCalls experiment explicitly refines the recommended forward Tool Policy from historical `single + sequential + reject-all` to `batch + parallel + independent-call handling` without creating a new Runtime rung or rewriting historical identities.

## Reading Order

1. Read the foundational ADRs `0001` through `0013` for stack, runtime, trace, retrieval, dashboard, storage, eval runner, and baseline decisions.
2. Read the consolidated topic ADRs `0112` through `0127` for the current V1 evaluation and AgentOps architecture.
3. For the historical L4 V1 base contract, read **ADR 0128 together with ADR 0129**. Do not apply ADR 0128's original exact-preflight section without the ADR 0129 amendment.
4. For the current recommended same-L4 Tool Policy, read the [L4 Batch + Parallel ToolCalls Milestone](../evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) together with current `README.md` / `CONTEXT.md` and the frozen Batch Runtime-control / Tool Policy components.
5. Use `archive/micro-decisions/` only when you need the detailed discussion trail behind the consolidated decisions.
6. Use dated milestone reports for immutable experiment evidence; only an explicitly referenced later milestone decision may refine a forward recommendation without retroactively changing older measurements.

## Active Foundational ADRs

- [0001 Python/FastAPI Primary Stack](0001-python-fastapi-primary-stack.md)
- [0002 Lightweight ReAct Runtime First](0002-self-built-react-runtime-first.md)
- [0003 OpenAI-Compatible LLM Provider](0003-openai-compatible-llm-provider.md)
- [0004 Structured Triage Report Contract](0004-structured-triage-report-contract.md)
- [0005 Minimal Run Trace First](0005-minimal-run-trace-first.md)
- [0006 SQLite First, PostgreSQL Later](0006-sqlite-first-postgresql-later.md)
- [0007 Lightweight Hybrid Retrieval First](0007-lightweight-hybrid-retrieval-first.md)
- [0008 React/Vite Dashboard](0008-react-vite-dashboard.md)
- [0009 Defer Auth/RBAC](0009-defer-auth-rbac.md)
- [0010 SSE Trace Stream](0010-sse-trace-stream.md)
- [0011 Thin Docker Compose for V1](0011-thin-docker-compose-for-v1.md)
- [0012 Batch Eval Runner Required](0012-batch-eval-runner-required.md)
- [0013 Pipeline Baseline for Runtime Comparison](0013-pipeline-baseline-for-runtime-comparison.md)

## Active Consolidated ADRs

- [0112 V1 Runtime Scope](0112-v1-runtime-scope.md)
- [0113 Evaluation Comparison Model](0113-evaluation-comparison-model.md)
- [0114 Component Versioning and Run Manifests](0114-component-versioning-and-run-manifests.md)
- [0115 Evaluation Suite and Case Artifacts](0115-evaluation-suite-and-case-artifacts.md)
- [0116 Metrics, Quality Gate, and Leaderboard](0116-metrics-quality-gate-and-leaderboard.md)
- [0117 Badcase Review and Regression](0117-badcase-review-and-regression.md)
- [0118 Retrieval Corpus and Evidence Scope](0118-retrieval-corpus-and-evidence-scope.md)
- [0119 Tool Policy and Sandbox](0119-tool-policy-and-sandbox.md)
- [0120 Trace, Step Protocol, and Tool Calling](0120-trace-step-protocol-and-tool-calling.md)
- [0121 CLI, Dashboard, Reports, and Storage](0121-cli-dashboard-reports-and-storage.md)
- [0122 Structured Report and Evidence Contract](0122-structured-report-and-evidence-contract.md)
- [0123 Case Provenance and Sanitization](0123-case-provenance-and-sanitization.md)
- [0124 Oracle Evidence Diagnostic Condition](0124-oracle-evidence-diagnostic-condition.md)
- [0125 Formal Evaluation Evidence Universe and Access](0125-formal-evaluation-evidence-universe-and-access.md)
- [0126 Offline Case Schema V2 Physical Artifacts and Canonical Evidence](0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)
- [0127 Staged Runtime Capability Ladder and Reference Boundary](0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [0128 L4 Self-built ReAct Runtime Contract](0128-l4-self-built-react-runtime-contract.md)
- [0129 L4 Provider-Reported Context Accounting](0129-l4-provider-reported-context-accounting.md)

## Current empirical / refinement references

- [L4 MiniMax-M3 Full-Suite Milestone — historical V1 reference](../evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md)
- [Shared Evidence Reference Canonicalization Milestone](../evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md)
- [L4 Batch + Parallel ToolCalls Milestone — current forward Tool Policy decision](../evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md)

## Archived Micro ADRs

Micro ADRs `0014` through `0111` have been consolidated into the topic ADRs above and moved to [archive/micro-decisions/](archive/micro-decisions/). They are retained as decision history, not as the primary implementation guide.
