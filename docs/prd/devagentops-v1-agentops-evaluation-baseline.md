# PRD: DevAgentOps V1 AgentOps Evaluation Baseline

> Current-state revision: 2026-08-18. This PRD describes the **current V1 target and already-delivered foundation**. Earlier versions of this PRD and historical PR/milestone documents may describe pre-Matrix-v2, pre-Suite-freeze, pre-Oracle, or pre-L4-design states.

## 1. Problem Statement

DevAgentOps V1 must be more than a one-off Agent demo. It needs a reproducible CI/Test Failure Triage AgentOps system where runtime behavior, evidence acquisition, model usage, tool policy, reports and badcases can be compared honestly across controlled conditions.

The system must answer questions such as:

- does adaptive ReAct investigation outperform fixed model-backed conditions on the same failures?
- when an Agent fails, was decisive evidence never found, found but not cited, or cited but reasoned about incorrectly?
- did a runtime/prompt/tool-policy change improve quality without changing benchmark identity?
- when Oracle evidence is supplied, how much diagnosis capability is available to be realized by the Agent system?
- are apparent failures Agent capability outcomes or infrastructure execution failures?

## 2. V1 Product Boundary

V1 Product Runtimes are limited to:

1. deterministic Fixed Pipeline (`runtime_variant="pipeline_baseline"` historically);
2. L4 self-built ReAct (`runtime_variant="self_built_react"`).

L1 Full-context One-shot, L2 Fixed Model Workflow and optional L3 Static Retrieval are diagnostic/comparison conditions, not Product Runtimes. Oracle Evidence is an orthogonal evaluator intervention.

V1 remains diagnosis-only. It does not edit code, run tests, rerun CI, create PRs, deploy, or otherwise mutate the development workflow.

## 3. Delivered Foundation

As of 2026-08-18, the following foundation is implemented:

- Offline Case Schema V2 with Physical / Canonical / Evaluator separation;
- frozen `triage-suite-v1`, exactly 20 Cases and 4 Cases per V1 Failure Type;
- frozen Canonicalization Profile v1;
- Structured Triage Report V1 and deterministic per-Case scorer;
- Evaluation Matrix v2;
- Treatment, Condition, Execution Policy and Run Configuration identities;
- Component Registry / frozen Component fingerprints;
- doctor-first formal preflight;
- repeated-sample execution engine and bounded cross-Case concurrency;
- Case-first Suite / Failure-Type aggregation;
- SQLite persistence, Trace, JSON/Markdown artifacts;
- MiniMax-M3 provider profile and exact local context/token accounting;
- L1 MiniMax-M3 20×3 formal milestone: 60 scored, 0 execution failures;
- L2 MiniMax-M3 20×3 formal milestone: 60 scored / 120 model calls, 0 execution failures;
- Oracle MiniMax-M3 20×3 formal milestone: 60 scored, 0 execution failures.

L4 architecture is Human-frozen by ADR 0128 and its implementation guide; implementation/formal milestone are pending.

## 4. Runtime Capability Ladder

```text
L0 deterministic pipeline
    -> L1 full-context one-shot
    -> L2 fixed model workflow
    -> L3 static retrieval
    -> L4 self-built ReAct
    -> L5+ incremental Agent capabilities
```

The ladder is a capability-attribution model, not a mandatory implementation sequence. L3 does not block L4.

## 5. Core User Needs

### Reproducible evaluation

The project builder needs:

- immutable Suite/Case identities;
- explicit Matrix conditions;
- versioned/fingerprinted behavior-affecting components;
- recorded code revision / dirty state;
- repeatable Sample identity and aggregation;
- formal/debug separation;
- no hidden repair/regeneration or unrecorded retries.

### Agent observability and badcase analysis

The reviewer needs both:

```text
Run Trace
= execution events / attempts / timing / usage / tool lifecycle / terminal & failure metadata

Agent Trajectory
= complete ordered per-sample User / Assistant / ToolResult message history
```

Trace must remain operationally readable and must not become a duplicate transcript store. L4 provider-returned thinking/reasoning may be persisted in the Agent trajectory for badcase analysis. It is not deterministic score input and is not claimed to expose faithful hidden neural computation.

### Evidence-grounded diagnosis

Reports must cite stable Evidence IDs and be scored against hidden Human-reviewed Ground Truth without exposing evaluator labels to the normal Agent.

The system must preserve the distinction:

```text
Physical Artifacts       -> facts
Canonical Evidence       -> neutral coordinates
Required Evidence        -> hidden Evidence Ground Truth
Expected Answer          -> hidden Diagnosis Ground Truth
```

### Controlled safety

V1 Agent actions are diagnosis-only and read-oriented. Mutation behavior remains forbidden. Tool policy must prevent invalid/forbidden actions before execution where applicable and make policy outcomes visible in trajectory/Trace.

## 6. Formal Case / Evidence Contract

A Formal Case V2 contains:

```text
<case-id>/
├── case.json
├── physical-artifacts/
│   ├── raw.log
│   ├── repository-manifest.json
│   └── repository/...
├── canonical-evidence/
│   ├── log-units.json
│   └── repository-units.json
└── evaluator/
    ├── required-evidence.json
    └── expected-answer.json
```

The Evidence Universe is authentic, frozen, offline and bounded-but-realistic. It preserves natural neighboring information rather than being curator-reduced to only Required Evidence.

Project Knowledge is not part of the current Formal Case Physical Universe and may only enter later as an independently versioned Runtime/Retrieval treatment.

## 7. L4 Self-built ReAct Product Requirement

L4 is the first Agentic Runtime and the long-lived Agent Runtime kernel lineage starting point.

```text
Model Decision
    -> Runtime validates action / policy / budget
    -> optional read-only Tool execution
    -> ToolResult observation
    -> authoritative typed message-state update
    -> next Model Decision or terminal report
```

The model chooses what to investigate next; the Runtime owns execution authority, safety, budgets, persistence, Trace and forced stop.

### 7.1 Native tools

L4 V1 exposes exactly:

```text
read
grep
find
ls
```

No Bash/edit/write tools.

`submit_report` is **not** a native provider tool. Report submission is a semantic terminal Runtime action: an AssistantMessage with 0 ToolCalls attempts to terminate, and its visible text is parsed as Structured Triage Report V1.

The older governance vocabulary may still call report persistence/report submission “report-write”; this classification must not be read as requiring a `submit_report` ToolCall in L4.

### 7.2 Agent-visible workspace

```text
/raw.log
/repository/...
```

Repository manifest metadata, Canonical Evidence files, evaluator directories and other package internals are not tool-readable.

The first model-visible input may include the complete **answer-neutral Canonical coordinate vocabulary** for citation. It must not disclose Physical Artifact contents, Required/Optional labels, Expected Answer or evaluator reasoning. The Agent must discover facts through tools and map them to neutral citation coordinates itself.

### 7.3 Tool Registry / Tool Policy

Tool Registry freezes what the tools are and how their ToolResults behave: provider-visible description/schema, workspace/search semantics, deterministic ordering, hard output bounds and truncation behavior.

Tool Policy freezes cross-call execution semantics. Baseline:

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Do not duplicate a second tool allowlist in L4 Tool Policy.

### 7.4 Tool output bounds

- shared ToolResult text hard cap: 50 KiB;
- `read`: max 2000 lines, 1-based pagination;
- `grep`: max 100 matches, max 500 chars per emitted source line;
- `find`: max 1000 results;
- `ls`: max 500 entries, one level, alphabetical, dotfiles included, dirs suffixed `/`;
- `grep/find/ls` operate over frozen workspace membership and do not re-apply `.gitignore`.

Truncation must be visible to the model and recorded in Trace metadata.

### 7.5 Budget and stop

L4 V1 hard Agent budget:

```text
max_steps = 100
```

One step = one successful provider completion normalized into a valid Model Decision / AssistantMessage.

Failed provider attempts do not consume steps.

The Runtime checks before the next model request. Decision #100 may execute a valid ToolAction, but no #101 request is made. Exhaustion is a scored Agent capability outcome, not an infrastructure failure.

V1 does not add cumulative token hard budget, a new sample wall-clock hard budget, forced finalization call, or automatic compaction.

### 7.6 Tool/action errors

Recoverable model/tool-use errors become Agent-visible error ToolResults and allow self-repair:

- unknown/disallowed tool;
- malformed/invalid arguments;
- expected tool-domain error;
- `length + ToolCall`;
- multiple calls under `single` policy.

Runtime does not semantically repair malformed model arguments. Unexpected Runtime/workspace/tool implementation exceptions are infrastructure failures.

### 7.7 Terminal/sample semantics

`SampleResult.status` remains:

```text
scored | execution_failed
```

Scored Agent/capability terminals:

- valid `report_submitted`;
- `model_stopped_without_valid_report`;
- `max_steps_exhausted`.

Execution failures are reserved for infrastructure conditions such as exhausted provider-request failure, unexpected Runtime/workspace/tool defects, static context-preflight infeasibility, or evaluation/persistence failures.

This distinction prevents survivorship bias from dropping weak Agent trajectories while also avoiding penalizing the Agent for infrastructure defects.

## 8. Provider Contract

The Runtime uses provider-neutral typed messages:

```text
UserMessage
AssistantMessage
  -> TextContent | ThinkingContent | ToolCall
ToolResultMessage
```

`ToolCall` preserves parsed arguments and raw provider/model argument text so malformed JSON remains measurable capability behavior rather than being repaired or misclassified as provider failure.

Successful `CompletionProvider.complete()` returns `AssistantMessage` directly. Provider failures before a valid Model Decision raise typed provider errors.

L4 V1 keeps the qualified route:

```text
MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

Provider-specific reasoning/tool continuation fields remain adapter-owned opaque state from the Runtime perspective.

## 9. Exact Token / Context Accounting

Every L4 logical model request must run exact preflight.

`count_input_tokens()` and `complete()` must share one model-visible MiniMax serialization path covering the same system prompt, ToolDefinitions, full typed history, continuation fields, thinking mode and chat-template/generation prompt.

Do not create an independent approximate counter that can diverge from the request actually sent.

Dynamic context exhaustion/compaction behavior is deliberately deferred until real L4 trajectories show it matters.

## 10. Provider-request Retry

L4 request retry is infrastructure handling for the same logical Model Decision, not whole-sample restart.

- ordinary transient errors: up to 3 retries after initial, 2s/4s/8s backoff;
- request timeout: at most 1 retry;
- auth/billing/invalid request/context-token limit/deterministic protocol or config error/policy block/abort: no same-request retry;
- SDK/provider hidden retries remain disabled;
- failed attempts are Trace events only, do not enter trajectory and do not consume Agent steps;
- exhausted request retry -> `execution_failed / provider_request_failed`.

## 11. Matrix v2 / Treatment Requirements

New Formal conditions use Matrix v2:

```text
id
type
runtime_variant
suite
evaluation_method
treatment
execution_policy
```

L4 Treatment must reference and Registry-validate:

- shared Task Contract prompt;
- separate L4 Runtime-control prompt;
- Tool Registry;
- Tool Policy;
- provider/model/reasoning/generation/context contracts.

Runtime implementation itself is not a Component Registry type; identity remains `runtime_variant + code_revision`.

The existing execution-policy `retry_count` must not silently become whole-sample retry. If reused for L4 it means provider-request retry, or the schema must migrate to a more explicit name.

## 12. Oracle Evidence

Oracle Evidence is already implemented and formally evaluated. It supplies the Human-reviewed Required Evidence source content while withholding labels/answers, thereby removing ordinary discovery difficulty.

Oracle is not L4 and not a Product Runtime.

Generic Oracle-vs-L4 pairing / Agent-System Realization Gap remains deferred until a real L4 formal milestone exists.

## 13. Evaluation Requirements for L4

Before a full live milestone:

1. deterministic fake-provider tests must prove multi-step adaptive execution, error recovery, policy rejection, max-step stop, invalid-report scoring and infrastructure failure semantics;
2. workspace/tool tests must prove bounded read-only access and evaluator non-leakage;
3. provider qualification must prove MiniMax-M3 native function calling, full assistant continuation/reasoning round-trip, exact token accounting, Trace/trajectory persistence;
4. only after qualification PASS should one controlled 20 Case × 3 L4 formal milestone be run;
5. model-quality failures are observations, not reasons to tune and rerun the formal milestone.

## 14. V1 Non-goals

- code edits / patch generation / CI reruns / PR creation / deployment;
- L4 Bash or mutation tools;
- planner/verifier/reflection framework;
- multi-agent / subagents;
- cross-run memory;
- MCP/skills as required V1 runtime capabilities;
- OS-level sandbox;
- automatic context compaction before evidence justifies it;
- external observability products as source of truth;
- composite overall capability score;
- model training / automatic post-training loop.

## 15. Source-of-truth order

When earlier PRD wording conflicts with current implementation/architecture, use:

1. Active ADRs;
2. ADR 0128 for L4;
3. `docs/evaluation/l4-self-built-react-runtime-design.md`;
4. current Matrix/Registry/source contracts;
5. current methodology docs.

Dated milestone docs, merged PR bodies, Case review packets and archived micro ADRs are historical evidence and should not override current Active ADR semantics.
