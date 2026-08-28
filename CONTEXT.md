# DevAgentOps — Current Project Context

> Updated 2026-08-28. This file is a current-orientation document, not a historical log. Dated milestone documents, merged PR bodies, Case review packets, and `docs/adr/archive/` preserve historical state and may intentionally contain superseded wording.

## Project

DevAgentOps is a developer-focused **CI / Test Failure Triage Agent Runtime and Formal Evaluation system**.

Live public Explorer: https://devagentops.onrender.com

The central question is:

> How much diagnosis capability can different Runtime / Evidence Acquisition / Agent-control treatments realize on the same frozen engineering failures, and where does performance get lost when the system fails?

Current end-to-end loop:

```text
Frozen Case / Environment
    -> Runtime / Agent execution
    -> Trace + complete Agent trajectory
    -> deterministic validation / scoring
    -> Case-first aggregation / Oracle diagnostics
    -> badcase attribution
    -> controlled experiment / ablation
    -> evidence-driven Runtime evolution
    -> next Evaluation
```

The current V1 domain is read-only diagnosis. It does not edit code, rerun tests/CI, open PRs, or deploy fixes.

## Current completed state

Completed and frozen where applicable:

- Offline Case Schema V2;
- `triage-suite-v1`: 20 Human-reviewed Cases, 4 per V1 Failure Type;
- Canonical Evidence coordinates, hidden Evidence Ground Truth, hidden Diagnosis Ground Truth;
- Structured Triage Report and deterministic scorer;
- Matrix v2, Component Registry, doctor-first formal execution;
- repeated Sample scheduler, Case-first aggregation, SQLite, Trace, Trajectory and artifacts;
- L1 `full_context_one_shot` formal milestone;
- L2 `fixed_model_workflow` formal milestone;
- L3 `static_retrieval` implementation and clean live `20×3` formal milestone;
- L4 `self_built_react` Runtime, historical single/sequential formal milestone, canonicalized formal generation and Batch + Parallel replication;
- Oracle Evidence diagnostic condition;
- shared deterministic Evidence Reference Canonicalization;
- Oracle↔L4 pair analysis and badcase attribution;
- public sanitized Evaluation Explorer data layer;
- interviewer-facing React/Vite Evaluation Explorer;
- public Render deployment with read-only FastAPI backend and static frontend.

## Runtime / condition ladder

```text
L0 deterministic pipeline
L1 full-context one-shot
L2 fixed model workflow
L3 static retrieval
L4 self-built ReAct
```

The ladder is an attribution framework, not a required implementation order.

Oracle is orthogonal to the ladder. It is an evaluator-side diagnostic intervention that bypasses ordinary Evidence discovery by selecting source-faithful raw Evidence spans. The model sees those source spans, not Required Evidence labels, hidden Expected Answer content, selection rationale, scorer labels, or fix information.

Oracle is **not L5, not a Product Runtime, and not a theoretical upper bound**.

## Representative canonicalized formal results

```text
Condition  Execution  Failure Type Exact  Evidence Hit  Required Fields  Protocol
L1          98.33%         80.00%            52.16%        99.79%         96.61%
L2          96.67%         83.33%            54.15%        98.33%         98.28%
L3         100.00%         88.33%            50.67%        99.79%         98.33%
L4         100.00%         81.67%            71.83%        99.58%         93.33%
Oracle     100.00%         83.33%            85.40%        96.67%         96.67%
```

These representative Runs are fresh hosted-model generations. Ordinary Run-to-Run metric differences are not automatically causal.

## Key experiment conclusions

### Evidence Reference Canonicalization

The strongest causal-isolation result is fixed-output offline replay: the exact same historical model outputs were revalidated after changing only deterministic Evidence reference canonicalization.

L4 replay:

```text
Protocol Validity        81.36% -> 96.61%
unknown Evidence IDs     12     -> 0
Failure Type Exact Match 88.33% -> 88.33%  unchanged
```

Interpretation: some Protocol / Evidence badcases were infrastructure-level reference-realization failures rather than improved model diagnosis.

The resolver only maps references that can be determined from frozen source identity and physical line ranges. It does not read Required Evidence / Expected Answer, perform fuzzy source correction, or repair semantics.

### L3 Static Retrieval

L3 formal result did **not** demonstrate Report Evidence Hit uplift over L1/L2.

Evaluator-side decomposition:

```text
Retrieval Acquisition Recall              76.56%
Acquired Required Evidence Utilization    66.18%
Final Report Evidence Hit                 50.67%
```

Loss occurs at both acquisition and utilization/citation stages. Future retrieval work should separately test acquisition/ranking and utilization/citation hypotheses on an independent calibration/dev set rather than tuning on the frozen Formal Suite.

### L4 Batch + Parallel Tool Policy

Historical reference Tool Policy:

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Recommended forward L4 Tool Policy:

```text
call_mode = batch
execution_mode = parallel
multiple_calls = accept_independently
```

Clean replication:

```text
Model Decisions        877 -> 571      (-34.89%)
Executed ToolCalls      809 -> 775      (-4.20%)
Wall time            978.27s -> 806.69s (-17.54%)
Mean sample latency                  -26.60%
P95 sample latency                   -28.07%
```

Quality deltas were small and mixed:

```text
Failure Type Exact Match      +3.33pp
Report Evidence Hit Rate      -1.14pp
Required Fields Completeness  +4.79pp
Protocol Validity             -1.67pp
```

Efficiency improvement reproduced. No reproducible material quality regression was demonstrated. Because the compared Runs are fresh generation, the quality deltas are observations rather than causal proof that Tool Policy improved or degraded diagnosis quality.

## L4 Runtime contract

L4 is the self-built Agent Runtime kernel:

```text
Model Decision
    -> Runtime validates schema / policy / budget
    -> optional Tool execution
    -> ToolResult observation
    -> authoritative message-state update
    -> next Model Decision or terminal report
```

Native investigation tools are exactly:

```text
read
grep
find
ls
```

Core boundaries:

- Model proposes actions; Runtime owns execution authority;
- Trace and Agent Trajectory are different artifacts;
- provider retries remain Trace and are not synthetic Agent Decisions;
- `submit_report` is not a native tool;
- 0 ToolCalls means the model attempts terminal Structured Triage Report submission;
- ToolResults are bounded;
- `max_steps = 100` counts Model Decisions, not individual ToolCalls;
- unexpected Runtime/tool/workspace defects are infrastructure failures rather than Agent observations.

## Case and evidence model

A Formal Case has four deliberately separated layers:

```text
Physical Artifacts
    raw.log + bounded exact-revision repository snapshot

Canonical Evidence
    answer-neutral stable source-span coordinates

Evidence Ground Truth
    hidden evaluator-only required-evidence.json

Diagnosis Ground Truth
    hidden evaluator-only expected-answer.json
```

Physical Artifacts are the sole fact source. Canonical Evidence provides stable citation / measurement coordinates; it is not an editable copy of truth and is not equivalent to Retrieval chunks.

Normal model-backed conditions never read evaluator-only Ground Truth artifacts.

## Public Evaluation Explorer

Frontend: https://devagentops.onrender.com

Backend API: https://devagentops-showcase-api.onrender.com/api

Public Explorer coverage:

- Overview / Evaluation-driven development narrative;
- Conditions L1 / L2 / L3 / L4 / Oracle;
- 12 catalogued formal Runs;
- Cases and Samples;
- Structured Report and Evidence;
- Agent Trajectory;
- Runtime Trace;
- Experiment & Attribution curated case studies for Canonicalization, L4 Tool Policy, L3 Retrieval and Oracle.

Public data is frozen and sanitized:

- 9 SQLite snapshots;
- 12 catalogued Runs;
- GET-only FastAPI Explorer routes;
- no evaluation execution endpoint;
- no public writes;
- no raw `.devagentops/` databases;
- no Expected Answer body;
- no provider reasoning/thinking or opaque continuation state;
- no unsanitized raw manifest/message dump.

The static frontend and FastAPI backend are deployed separately on Render. Free-tier backend cold start is hosting behavior only and must never be interpreted as DevAgentOps Runtime latency.

Deployment details: `docs/showcase-deployment.md`.

Public data boundary: `docs/adr/0131-public-evaluation-explorer-data-boundary.md` and `showcase-data/README.md`.

## Source-of-truth rules

Current-facing architecture and methodology live in:

- `README.md`;
- `CONTEXT.md`;
- active ADRs under `docs/adr/`;
- `docs/evaluation/formal-evaluation-methodology.md`;
- `docs/evaluation/runtime-capability-ladder.md`;
- current milestone reports under `docs/evaluation/milestones/`;
- `docs/showcase-deployment.md` for the deployed public Explorer.

Historical milestone docs, archived ADRs, merged PR bodies and Case review packets intentionally preserve historical wording and should not be retroactively rewritten to match later Treatments.

## Current direction

Do not widen the canonicalizer or Batch policy without new evidence.

Current evidence also does not justify adding vector DBs, embedding/reranking stacks, forced batching, planner/verifier, memory, MCP/skills, or multi-agent complexity to V1 merely for feature count.

The next large Product Runtime capability direction is **executable repair / sandboxed remediation**:

```text
investigate
    -> diagnose
    -> mutate / edit
    -> execute / test
    -> observe
    -> retry
    -> verify
    -> report
```

That work is a new stage beyond the current read-only triage V1 and must not retroactively change frozen L1–L4 / Oracle experiment identities or results.
