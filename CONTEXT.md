# DevAgentOps — Current Project Context

> Updated 2026-08-18. This file is a current-orientation document, not a historical log. For architectural authority use Active ADRs, especially ADR 0128 for L4. Dated milestone documents, merged PR bodies, Case review packets, and `docs/adr/archive/` preserve historical state and may intentionally contain superseded wording.

## Project

DevAgentOps is a developer-focused CI/Test Failure Triage AgentOps system for learning, evaluation, and job-seeking demonstration. It is not a generic coding assistant or auto-remediation agent.

Current research/product question:

> How much model capability can different Runtime / evidence-acquisition / Agent-control treatments realize on the same frozen engineering failures, and how can failures be traced and attributed honestly?

## Current state

Completed:

- Offline Case Schema V2;
- frozen `triage-suite-v1`, 20 Cases, exactly 4 per V1 Failure Type;
- Canonicalization Profile v1;
- Structured Triage Report V1 and deterministic scorer;
- Matrix v2, Component Registry, doctor-first formal execution;
- repeated Sample scheduler, Case-first aggregation, SQLite/Trace/artifacts;
- MiniMax-M3 exact-token formal provider path;
- L1 20×3 formal milestone: 60 scored, 0 execution failures;
- L2 20×3 formal milestone: 60 scored / 120 model calls, 0 execution failures;
- Oracle 20×3 formal milestone: 60 scored, 0 execution failures.

Current work:

- Issue #52 L4 `self_built_react`;
- ADR 0128 + detailed L4 design Human-frozen in PR #53;
- implementation pending;
- L3 is not required before L4;
- Oracle-vs-L4 pairing/gap remains deferred until a real L4 formal artifact exists.

## Core terminology

### LLM / Model

Decision and reasoning engine only. It proposes assistant content/tool actions; it does not own execution authority.

### Agent Runtime

The L4 system kernel that owns authoritative state, loop execution, tool validation/execution, policy, budgets, Trace hooks, and terminal handling.

### Agent System

```text
Model
+ Agent Runtime
+ Tools
+ Environment
+ Prompt / State
```

“Agent” normally refers to this whole system, not only the model.

### Product Runtime

A supported runtime lineage. V1 Product Runtimes are Fixed Pipeline and L4 self-built ReAct. L1/L2/L3 are diagnostic/comparison conditions, not Product Runtimes.

### Runtime Capability Ladder

```text
L0 deterministic pipeline
L1 full-context one-shot
L2 fixed model workflow
L3 static retrieval
L4 self-built ReAct
L5+ incremental Agent capabilities
```

The ladder is an attribution framework, not a required implementation order.

## Case and evidence model

### Evidence Universe

The authentic, frozen, offline, bounded-but-realistic physical world of a Formal Case:

```text
raw failure log
+ bounded exact-revision repository snapshot
```

### Physical Artifact

Sole fact source. Current Formal Case V2 physical artifacts are `raw.log` and manifest-declared repository files.

### Canonical Evidence Unit

Deterministic, answer-neutral source-span coordinate over a Physical Artifact. It provides stable IDs for citation/measurement; it is not a second copy of source truth and not a mandatory Retrieval chunk.

### Evidence Ground Truth

Hidden evaluator-only `required-evidence.json`, containing Human-reviewed Required/Optional Canonical IDs. Never directly visible to normal model-backed conditions.

### Diagnosis Ground Truth

Hidden evaluator-only `expected-answer.json` containing expected diagnosis semantics. Separate from Evidence Ground Truth.

### L4 Canonical vocabulary refinement

L4 V1 may receive the complete **answer-neutral Canonical coordinate vocabulary** in its initial model-visible input so it can cite valid Evidence IDs.

That does **not** expose evidence content or Ground Truth:

```text
visible upfront:
- all neutral coordinate IDs / source-span vocabulary

not visible upfront:
- Physical Artifact contents
- which IDs are required/optional
- Expected Answer
- evaluator metadata
```

The Agent must still discover physical facts through tools and map them to the visible coordinate vocabulary itself.

## L4 frozen Runtime contract

### Control

```text
Model proposes Action
    -> Runtime validates policy/schema/budget
    -> Runtime optionally executes Tool
    -> ToolResult returned
    -> Runtime appends authoritative message state
    -> next Model Decision or terminal
```

### Native tools

Exactly four read-only investigation tools in L4 V1:

```text
read
grep
find
ls
```

There is no Bash/edit/write tool.

`submit_report` is **not** a native L4 tool. Report submission is a semantic terminal Runtime action: 0 ToolCalls means the model attempts to finish; visible assistant text is parsed as Structured Triage Report V1.

### Agent-visible workspace

```text
/raw.log
/repository/...
```

Evaluator directories, canonical-evidence files, package metadata, and repository manifest are not tool-readable.

### Tool Registry

Frozen provider-visible contracts and deterministic Tool behavior: names, descriptions, parameter JSON Schemas, workspace/search semantics, output bounds, ordering and truncation. Behavior changes alter Tool Registry fingerprint.

### Tool Policy

Only cross-ToolCall execution semantics. L4 baseline:

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Tool availability is already defined by Tool Registry; do not duplicate a second allowlist in Tool Policy.

### Tool bounds

- shared ToolResult hard cap: 50 KiB text;
- `read`: max 2000 lines/call, 1-based offset, explicit continuation;
- `grep`: max 100 matches, 500 chars per emitted source line;
- `find`: max 1000 results;
- `ls`: max 500 entries, one level, deterministic alphabetical, dotfiles included, dirs `/` suffixed;
- `grep/find/ls` do not re-apply `.gitignore` beyond frozen workspace membership.

### Agent step

One `step` = one successfully returned provider/model completion that normalizes into a valid `AssistantMessage` Model Decision.

Failed provider/transport attempts do not consume steps.

Hard V1 Agent limit:

```text
max_steps = 100
```

No global token hard budget, no new sample wall-clock budget, no automatic compaction baseline.

### Tool/action recovery

Agent-visible recoverable errors return `ToolResult(is_error=True)` and allow another Model Decision:

- unknown/disallowed tool;
- invalid schema arguments;
- malformed raw argument JSON;
- expected tool/domain errors;
- `length + ToolCall` (execute none);
- multiple ToolCalls under `single` policy (execute none, error result per call).

Unexpected Runtime/workspace/tool implementation exceptions are infrastructure failures, not Agent observations.

### Terminal taxonomy

`SampleResult.status` stays:

```text
scored | execution_failed
```

Scored capability terminals:

- `report_submitted`;
- `model_stopped_without_valid_report`;
- `max_steps_exhausted`.

Execution failures include exhausted provider-request infra failure, unexpected Runtime/workspace/tool defect, static context/preflight failure, and evaluator/persistence infrastructure failure.

Dynamic context exhaustion classification remains intentionally deferred until observed.

## Provider-neutral message contract

L4 uses typed messages, not provider wire dicts:

```text
UserMessage
AssistantMessage
  content[]:
    TextContent
    ThinkingContent
    ToolCall
ToolResultMessage
```

`ToolCall` preserves both strictly parsed `arguments` and raw provider/model `raw_arguments`. Malformed JSON is therefore a measurable model action rather than something the Runtime silently repairs.

`AssistantMessage` carries normalized response/usage/stop metadata plus opaque adapter-owned `provider_fields` for exact continuation. Runtime must not interpret provider-specific continuation state.

Successful `CompletionProvider.complete()` returns `AssistantMessage` directly. Provider infrastructure failures before a valid Model Decision raise typed provider errors.

## MiniMax route

L4 V1 preserves:

```text
DevAgentOps
    -> MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

MiniMax-specific `tool_calls`, `reasoning_content`, `reasoning_details`, `base_resp` and wire serialization stay inside `MiniMaxProvider`.

## Exact token accounting

`count_input_tokens()` and `complete()` must share the same model-visible MiniMax serialization path.

The count must reflect the same:

- system prompt;
- complete typed history;
- ToolDefinitions;
- provider continuation fields that affect replay;
- thinking mode;
- chat template / generation prompt.

This prevents context preflight from counting a different request than the one actually sent.

## Request retry

Request retry is infrastructure handling, not whole-sample retry and not Agent behavior.

- ordinary transient errors: initial attempt + up to 3 retries, backoff 2s/4s/8s;
- request timeout: at most one retry;
- auth/billing/invalid request/context-token limit/deterministic config or protocol error/policy block/abort: no same-request retry;
- SDK/provider hidden retries remain 0;
- failed attempts do not enter trajectory or consume `max_steps`;
- exhausted retry -> `execution_failed / provider_request_failed`.

The same logical request must preserve model/system/tools/messages/reasoning/generation exactly.

## Trace vs Agent Trajectory

### Run Trace

Structured execution/event record:

- model request attempts;
- usage / latency / response IDs;
- tool-call lifecycle;
- truncation metadata;
- budgets/terminal reasons;
- failures/evaluation lifecycle.

Trace is **not** the complete conversation store.

### Agent Trajectory

Complete ordered per-sample conversation:

```text
UserMessage
AssistantMessage
ToolResultMessage
...
```

It includes finalized assistant text, provider-returned thinking, ToolCalls and opaque continuation fields needed for replay/badcase analysis.

Provider-exposed thinking is diagnostic trajectory evidence only: it is not deterministic score input and not claimed to be faithful hidden neural computation.

## Prompt / Treatment identity

Shared diagnosis Task Contract stays Runtime-neutral.

L4-specific system instructions for tools/loop/stopping/report semantics are a separate frozen `prompt` component referenced as `contracts.runtime_control`.

L4 Treatment must Registry-validate:

- shared Task prompt;
- Runtime-control prompt;
- Tool Registry;
- Tool Policy。

Do not add a `runtime` Component type; Runtime implementation provenance remains `runtime_variant + code_revision`.

## Matrix v2

Active formal condition shape:

```text
id
type
runtime_variant
suite
evaluation_method
treatment
execution_policy
```

Treatment contains provider/model/reasoning/generation/contracts/context. Execution Policy currently contains repeat count, case concurrency, retry field, and request timeout. Legacy Defaults/`extends` Matrix v1 remains historical compatibility, not the L4 template.

## Oracle

Oracle Evidence is implemented and has a preserved 20×3 MiniMax-M3 formal milestone. It supplies reviewed Required Evidence source content while hiding labels/answers, thereby bypassing ordinary discovery.

L4 is different: it receives the broad physical workspace + neutral citation vocabulary and must discover facts itself.

Generic Oracle-vs-L4 pairing/gap machinery is deferred until real L4 formal results exist.

## Deferred / evidence-gated

Do not prebuild without real badcase evidence:

- compaction / summarization / history trimming;
- dynamic context-exhaustion policy;
- planner/verifier/reflection;
- multi-agent / subagents;
- memory / skills / MCP;
- read byte/column slicing for oversized single lines;
- batch/parallel ToolCall policy beyond explicit ablation.

## Current source-of-truth order

When sources disagree, use:

1. `docs/adr/README.md` Active ADR index;
2. ADR 0128 for L4;
3. `docs/evaluation/l4-self-built-react-runtime-design.md`;
4. current Matrix/Registry/source code contracts;
5. active evaluation methodology docs;
6. dated milestone/history only for historical facts.

Archived micro ADRs and old PR bodies must not override active decisions.
