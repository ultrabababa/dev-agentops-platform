# ADR Index

This directory keeps active architecture decisions for DevAgentOps.

## Reading Order

1. Read the foundational ADRs `0001` through `0013` for stack, runtime, trace, retrieval, dashboard, storage, eval runner, and baseline decisions.
2. Read the consolidated topic ADRs `0112` through `0122` for the current V1 evaluation and AgentOps design.
3. Use `archive/micro-decisions/` only when you need the detailed discussion trail behind the consolidated decisions.

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

## Archived Micro ADRs

Micro ADRs `0014` through `0111` have been consolidated into the topic ADRs above and moved to [archive/micro-decisions/](archive/micro-decisions/). They are retained as decision history, not as the primary implementation guide.
