# L4 Self-built ReAct Runtime Design

This document is the implementation guide for Issue #52, ADR 0128, and the
accepted ADR 0129 Human amendment.

ADR 0129 supersedes only ADR 0128's mandatory **L4 local exact-token
preflight** requirement. The rest of the Human-frozen L4 V1 contract remains
unchanged. In particular, L4 keeps full provider-origin conversation replay,
`max_steps=100`, bounded read-only tools, Tool Registry / Tool Policy identity,
same-logical-request retry, Trace / trajectory separation, and no compaction.

## 1. Goal

Implement the smallest trustworthy adaptive Agent Runtime for one frozen
CI/test-failure Case:

```text
case/workspace + citation coordinates
        -> model decision
        -> optional read-only tool action
        -> bounded observation
        -> updated typed conversation
        -> next decision or final Structured Triage Report V1
```

L4 is the first Agentic Product Runtime. It is not a framework-building
exercise and does not attempt to implement L5+ capabilities.

## 2. Architectural boundary

Use this ownership model:

```text
LLM / Provider
  proposes AssistantMessage

ReAct Runtime
  owns loop, state, action interpretation, policy, budgets, stop

Tools
  own bounded read/search/list behavior over RuntimeCaseWorkspace

Environment
  is the frozen Case Investigation Workspace

Trace
  owns execution/lifecycle observations

Trajectory persistence
  owns complete ordered Agent messages

Evaluator
  owns hidden Required Evidence, Expected Answer, report validation, scoring
```

The Runtime must never read `evaluator/required-evidence.json` or
`evaluator/expected-answer.json` through normal Agent paths.

A Runtime action is:

```text
ToolAction | SubmitReportAction
```

`SubmitReportAction` is semantic Runtime behavior, not a native tool.

## 3. Code shape

Keep the implementation compact under the existing Runtime package:

```text
src/devagentops/runtime/
├── workspace.py
├── messages.py
├── react.py
├── tool_policy.py
└── tools/
    ├── __init__.py
    ├── read.py
    ├── grep.py
    ├── find.py
    └── ls.py

src/devagentops/conditions/l4/
├── __init__.py
└── react_condition.py
```

Do not split state/context/stopping into a framework hierarchy unless later
evidence makes that complexity necessary.

## 4. Provider-neutral messages and requests

The canonical Runtime-facing types are provider-neutral.

```python
@dataclass(frozen=True)
class TextContent:
    text: str

@dataclass(frozen=True)
class ThinkingContent:
    thinking: str

@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, JsonValue] | None
    raw_arguments: str | None

AssistantContent = TextContent | ThinkingContent | ToolCall

@dataclass(frozen=True)
class UserMessage:
    content: str

@dataclass(frozen=True)
class AssistantMessage:
    content: tuple[AssistantContent, ...]
    response_id: str | None
    response_model: str | None
    usage: TokenUsage
    stop_reason: Literal["stop", "length", "tool_use"]
    raw_stop_reason: str | None
    provider_fields: dict[str, JsonValue]

@dataclass(frozen=True)
class ToolResultMessage:
    tool_call_id: str
    tool_name: str
    content: str
    is_error: bool
```

`provider_fields` is opaque to Runtime code. Only the provider adapter may
interpret or reconstruct provider continuation state.

The logical request shape is:

```python
@dataclass(frozen=True)
class LogicalCompletionRequest:
    model: str
    system_prompt: str | None
    messages: tuple[Message, ...]
    tools: tuple[ToolDefinition, ...]
    reasoning: dict[str, Any]
    generation: dict[str, Any]
```

`CompletionProvider.complete(request)` returns one normalized
`AssistantMessage` or raises a typed provider error before a Model Decision is
created.

`count_input_tokens()` may remain on provider implementations where L1/L2/Oracle
or offline diagnostics require exact local counting, but **L4 `run_react()` must
not call it on the critical path**.

## 5. MiniMax adapter boundary

Keep the qualified route:

```text
MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

The transport owns one HTTP/JSON attempt. It does not own Agent retry or hidden
SDK retry.

`MiniMaxProvider` owns:

1. typed-message and ToolDefinition serialization;
2. native `tools` serialization;
3. visible text / thinking / ToolCall parsing;
4. strict parsing of `function.arguments` while preserving the exact raw
   provider string;
5. full provider continuation replay, including MiniMax reasoning fields;
6. usage/model/request/finish metadata normalization;
7. provider-level response-status interpretation where applicable.

Malformed inner `function.arguments` is not a malformed outer provider
envelope. If the provider returns such a ToolCall, Runtime preserves the raw
AssistantMessage and follows the recoverable Agent-action path.

Do not broaden Issue #52 into a generic multi-provider framework.

## 6. L4 context accounting — ADR 0129

L4 V1 does **not** perform mandatory local exact-token preflight before a Model
Decision.

The critical path is:

```text
build logical request
    -> complete_with_request_retry(request)
    -> provider processes request
    -> AssistantMessage.usage records observed usage
```

For completed requests:

- provider-reported `usage.input_tokens` is the authoritative observed input
  token count;
- Trace records provider usage per successful Model Decision;
- the Sample result records the per-step observed input-token sequence;
- Treatment retains the advertised context-window metadata;
- Runtime does not block solely on a locally reconstructed token count.

The frozen Matrix context identity is:

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

L4 still performs no compaction, summarization, history trimming, or automatic
context compression.

A real context-limit rejection is provider/execution evidence. Predictive
budgeting or compaction is deferred until real trajectories justify a new ADR.

Pinned MiniMax tokenizer/chat-template assets and local exact counting remain
available for existing L1/L2/Oracle behavior and offline diagnostics. They are
not L4 Agent Treatment behavior and are not part of the L4 critical execution
path.

## 7. Initial model-visible input and Runtime-control identity

The shared diagnosis Task Contract remains the existing frozen Runtime-neutral
`prompt` component.

L4-specific instructions for tool use, investigation semantics, loop behavior,
stopping, and final report submission are a **separate frozen `prompt`
component** referenced under `contracts.runtime_control`.

The first user message contains:

- Case ID and public Case metadata needed for triage;
- Agent-visible workspace description (`/raw.log`, `/repository/...`);
- an explicit statement that physical contents must be acquired through tools;
- the complete answer-neutral Canonical Evidence coordinate universe usable for
  final citations.

It must not expose:

- Required Evidence;
- Expected Answer;
- evaluator labels;
- curator/reviewer reasoning;
- package-internal evaluator filenames or scorer state.

## 8. Tool surface and hard bounds

Expose exactly four read-only investigation tools.

### `read(path, offset?, limit?)`

- Agent-visible path only;
- `offset` is 1-based;
- `limit` range is `1..2000`;
- output <= 2000 lines and <= 50 KiB;
- when complete lines remain, include an explicit continuation notice and next
  offset;
- a single source line larger than the hard cap returns a bounded error/notice
  rather than byte slicing.

### `grep(pattern, path?, glob?, ignore_case?, literal?, context?, limit?)`

- maximum 100 matches;
- output <= 50 KiB;
- each emitted source line <= 500 characters;
- match and context lines are distinguishable;
- truncation/limit notices are model-visible;
- operate over frozen visible workspace membership; do not re-apply
  `.gitignore`.

### `find(pattern, path?, limit?)`

- glob path matching;
- deterministic output over visible workspace membership;
- maximum 1000 results;
- output <= 50 KiB;
- relative paths only.

### `ls(path?, limit?)`

- one directory layer;
- maximum 500 entries;
- output <= 50 KiB;
- deterministic alphabetical order;
- directories suffixed with `/`;
- dotfiles included.

Tool truncation is both Agent-visible and represented in Trace metadata.

## 9. Tool Registry and Tool Policy identity

The frozen `tool_registry` is the single source of truth for provider-visible
tool contracts and deterministic tool behavior. Its behavior identity includes:

- names and descriptions;
- complete parameter JSON Schemas;
- workspace/search semantics;
- ordering;
- output/count/line limits;
- truncation/continuation behavior.

Implementation paths and review notes are not behavior identity.

Baseline Tool Policy is:

```json
{
  "rules": [
    {
      "scope": "model_decision",
      "call_mode": "single",
      "execution_mode": "sequential",
      "multiple_calls": "reject_all_with_error_results"
    }
  ]
}
```

Tool availability comes from Tool Registry; do not maintain a second per-tool
allowlist in Tool Policy.

If one AssistantMessage emits multiple ToolCalls under baseline `single`:

- execute none;
- preserve the AssistantMessage;
- emit one policy-error ToolResult for every declared ToolCall ID;
- allow the next Model Decision.

Future `batch + sequential` / `batch + parallel` behavior is an explicit
same-L4 ablation, not baseline behavior.

## 10. ReAct loop

```text
messages = [initial_user_message]
steps = 0

while True:
    if steps >= max_steps:
        return scored(max_steps_exhausted, report=None)

    request = build_request(system_prompt, messages, tools)
    assistant = complete_with_request_retry(request)

    steps += 1
    persist assistant in trajectory
    trace provider-reported completion metadata and usage

    tool_calls = assistant ToolCall blocks

    if tool_calls is empty:
        report = parse_structured_report(assistant_text(assistant))
        if report valid:
            return scored(report_submitted, report)
        return scored(model_stopped_without_valid_report, raw_report)

    if assistant.stop_reason == length:
        execute none
        append one error ToolResult for every declared ToolCall
        continue

    if policy rejects the call set:
        execute none
        append policy-error ToolResult for every declared ToolCall
        continue

    selected_call = the single allowed call

    if raw arguments malformed or schema invalid:
        append error ToolResult
        continue

    try:
        result = execute_tool(selected_call)
    except ExpectedToolDomainError as exc:
        append error ToolResult
        continue
    except Exception:
        raise infrastructure failure

    append successful ToolResult
```

`max_steps = 100` is the only Agent-level hard budget in V1.

One step is one successfully returned provider completion normalized into a
valid AssistantMessage. Failed provider attempts do not consume steps or enter
trajectory.

The 100th Model Decision is allowed. If it submits a valid report, accept it. If
it executes a legal ToolAction, execute and persist the ToolResult, then stop
before any 101st Model Decision with `max_steps_exhausted`.

## 11. Provider-request retry

Retry is infrastructure handling of the **same logical request**, not Agent
behavior and not whole-sample restart.

For ordinary retryable provider/network failures:

```text
attempt 1 -> failure
wait 2s
attempt 2 -> failure
wait 4s
attempt 3 -> failure
wait 8s
attempt 4 -> success or terminal failure
```

Request timeout is allowed at most one retry.

Auth/billing/invalid request/context-limit/deterministic protocol or config
errors/policy block/explicit abort are non-retryable.

Every attempt is recorded in Trace. Only the successful AssistantMessage enters
trajectory. Exhaustion becomes:

```text
execution_failed / provider_request_failed
```

Matrix `execution_policy.retry_count` means provider-request retry for L4. It
must not trigger whole-sample replay.

## 12. Error and terminal boundaries

### Recoverable Agent-visible action errors

Examples:

- unknown/disallowed tool;
- schema-invalid arguments;
- malformed raw arguments;
- expected tool-domain failure such as path-not-found;
- `length + ToolCall`;
- multiple calls under baseline `single`.

Runtime emits error ToolResult messages and allows another Model Decision.
Runtime does not semantically repair the model action.

### Capability terminals

```text
valid final report
  -> report_submitted
  -> status=scored

zero ToolCalls + invalid/missing report
  -> model_stopped_without_valid_report
  -> status=scored

no report before max_steps
  -> max_steps_exhausted
  -> status=scored
```

`stop_reason=length` with zero ToolCalls follows the same final-report parse
rule. There is no rescue/regeneration call.

### Infrastructure terminals

Examples:

- provider request failure after frozen retry policy;
- malformed provider envelope that yields no AssistantMessage;
- Runtime/workspace invariant defect;
- unexpected tool implementation exception;
- evaluator/scorer/persistence defect.

Result:

```text
status=execution_failed
```

L4 no longer has a local static exact-preflight infeasibility terminal. A real
provider context-limit rejection is surfaced through the provider/execution
error path under ADR 0129.

## 13. Trace vs Agent trajectory

These are separate records.

```text
Trace
= lifecycle / execution observations
  request attempts
  provider usage / latency / IDs
  tool lifecycle / errors / truncation
  budgets / terminals / infrastructure failures

Agent trajectory
= complete ordered UserMessage / AssistantMessage / ToolResultMessage history
```

Persist complete normalized AssistantMessages needed for badcase analysis,
including visible text, provider-returned thinking, ToolCalls, metadata, and
opaque provider continuation fields required for replay.

Provider-returned thinking is diagnostic trajectory evidence. It is not a
score input and is not claimed to be faithful hidden neural chain-of-thought.

Reuse the existing Trace recorder/table. The trajectory store must remain the
smallest sample-scoped linear persistence extension required to reconstruct one
sample; do not add sessions, branches, parent pointers, resume state, or a
second storage subsystem.

## 14. Matrix and Treatment integration

L4 remains Matrix v2:

```text
runtime_variant = self_built_react
```

Treatment identity references the frozen:

- shared Task Contract prompt;
- L4 Runtime-control prompt;
- Tool Registry;
- Tool Policy;
- provider/model/reasoning/generation/context contract.

Formal validation resolves and checks the Task prompt, Runtime-control prompt,
Tool Registry, and Tool Policy against Component Registry.

Runtime implementation is **not** a Component Registry component. Implementation
provenance remains:

```text
runtime_variant + code_revision
```

Execution policy, including concurrency and provider-request retry, remains
outside Treatment/Condition behavior identity and participates in Run
Configuration identity as already frozen.

## 15. Canonical Evidence and citation behavior

The complete Canonical coordinate universe is disclosed as answer-neutral
citation vocabulary in the initial input. This is different from exposing
Canonical Evidence content or hidden Required Evidence.

The Agent must:

1. acquire physical content through tools;
2. reason over that content;
3. map relevant physical facts to an exact exposed Evidence ID;
4. cite only IDs in the frozen vocabulary.

Badcase analysis distinguishes:

```text
A. required physical content not found/seen
   -> acquisition/tool-use problem

B. physical content found but correct Evidence ID not cited
   -> mapping/evidence-selection/report problem

C. correct Evidence ID cited but diagnosis wrong
   -> reasoning problem
```

No dynamic physical-span -> Evidence-ID mapping helper exists in the L4 V1
baseline.

## 16. Deterministic testing

Before live qualification, deterministic fake-provider tests cover at minimum:

1. multi-step tool trajectory ending in a valid report;
2. model stops without valid report;
3. exact max-step semantics;
4. unknown tool recovery;
5. schema-invalid arguments;
6. malformed raw arguments and next-turn recovery;
7. `length + ToolCall` rejection;
8. multi-ToolCall rejection under `single`;
9. expected tool-domain error recovery;
10. unexpected Runtime/tool exception -> execution failure;
11. transient provider failure -> same-request retry -> success;
12. retry exhaustion -> execution failure;
13. Trace / trajectory separation and persistence;
14. evaluator/package leakage boundary;
15. 50 KiB/count/line truncation semantics;
16. L4 `run_react()` does **not** call `count_input_tokens()`;
17. provider-reported input usage is recorded per successful Model Decision;
18. MiniMax assistant continuation fields and raw ToolCall arguments round-trip;
19. Matrix doctor rejects missing/mismatched Runtime-control, Tool Registry, or
    Tool Policy identity.

Existing L1/L2/Oracle exact-token tests remain unchanged.

## 17. Live qualification

Before the formal full-Suite milestone, one small real MiniMax-M3 qualification
must prove:

- native function calling through the existing OpenAI Chat Completions route;
- full assistant `reasoning_details` / provider continuation replay;
- raw ToolCall replay preserving protocol-significant fields;
- one real multi-step read-only tool trajectory;
- provider-reported usage recorded without a local preflight gate;
- correct Trace / trajectory persistence;
- no evaluator leakage.

A model capability failure in the final diagnosis/report does not invalidate the
qualification if provider protocol, Runtime loop, Tool execution, persistence,
and information boundaries are functioning as designed.

Only after qualification PASS may the project run the one controlled 20 Case x
3 L4 formal milestone.

## 18. Formal milestone interpretation

The formal L4 milestone reuses the existing formal evaluation stack:

- doctor-first validation;
- full frozen Suite;
- repeated Sample scheduler;
- bounded cross-Case concurrency;
- Trace;
- SQLite persistence;
- Case-first aggregation;
- JSON/Markdown artifacts;
- existing Structured Triage Report scorer.

Do not build a parallel L4 evaluator.

Capability outcomes remain scored even when the report is invalid. Provider /
Runtime infrastructure failures remain `execution_failed` and remain visible in
execution coverage.

The development milestone is evidence for Runtime behavior and diagnostic
quality. It is not a final benchmark freeze or leaderboard result.

## 19. Deferred features

Do not implement until real evidence justifies them:

- compaction / summary / history trimming;
- predictive local context budgeting;
- planner/verifier;
- retrieval optimization;
- Bash/edit/write/CI rerun;
- batch/parallel baseline tool calls;
- dynamic skills/MCP;
- long-term memory/experience;
- oversized-line slicing;
- whole-sample retry;
- dynamic context-exhaustion terminal taxonomy.

Future behavior changes require explicit Treatment/ADR decisions rather than
silent mutation of the recorded L4 baseline.

## 20. Final L4 V1 acceptance checklist

The implementation is acceptable when the following are represented in
code/config/tests according to ADR 0128 + ADR 0129:

- [x] provider-neutral typed messages and logical completion request;
- [x] MiniMax native ToolCall and continuation round-trip;
- [x] provider-reported L4 context accounting with no mandatory local preflight;
- [x] shared Task Contract plus separate frozen Runtime-control prompt;
- [x] bounded `read/grep/find/ls` contracts;
- [x] frozen Tool Registry and Tool Policy;
- [x] baseline `single + sequential` policy;
- [x] exact `max_steps=100` semantics;
- [x] same-logical-request provider retry;
- [x] scored capability vs `execution_failed` infrastructure taxonomy;
- [x] complete linear trajectory persistence separate from Trace;
- [x] full answer-neutral Canonical coordinate vocabulary in initial input;
- [x] no compaction or L5+ mechanism in baseline;
- [x] deterministic test gate;
- [x] live MiniMax qualification;
- [x] one controlled formal 20 Case x 3 milestone.
