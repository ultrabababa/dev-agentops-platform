# L4 Self-built ReAct Runtime Design

This document is the implementation guide for Issue #52 and ADR 0128. It records the Human-frozen L4 V1 design so implementation can proceed without re-deciding semantics in code.

## 1. Goal

Implement the smallest trustworthy adaptive Agent Runtime for one frozen CI/test-failure Case:

```text
case/workspace + citation coordinates
        -> model decision
        -> optional read-only tool action
        -> bounded observation
        -> updated typed conversation
        -> next decision or final Structured Triage Report V1
```

L4 is the first Agentic Product Runtime. It is not a framework-building exercise and does not attempt to implement L5+ capabilities.

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

The Runtime must never read `evaluator/required-evidence.json` or `evaluator/expected-answer.json` through normal Agent paths.

## 3. Proposed code shape

Prefer a compact implementation under the existing runtime package rather than a new framework hierarchy:

```text
src/devagentops/runtime/
├── workspace.py                 # existing
├── messages.py                  # provider-neutral message/tool types
├── react.py                     # state + loop + terminal result
├── tool_policy.py               # generic single/batch policy interpreter
└── tools/
    ├── __init__.py
    ├── read.py
    ├── grep.py
    ├── find.py
    └── ls.py

src/devagentops/conditions/l4/
├── __init__.py
└── react_condition.py           # Matrix/evaluation integration
```

Do not split state/context/stopping into separate modules unless implementation proves the file has become materially difficult to reason about.

## 4. Provider-neutral types

The following is illustrative shape, not a demand for exact Python spelling.

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

Message = UserMessage | AssistantMessage | ToolResultMessage
```

`provider_fields` is opaque to Runtime code. Only the provider adapter may interpret or reconstruct it.

The common request shape is:

```python
@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, JsonValue]

@dataclass(frozen=True)
class LogicalCompletionRequest:
    model: str
    system_prompt: str | None
    messages: tuple[Message, ...]
    tools: tuple[ToolDefinition, ...]
    reasoning: dict[str, Any]
    generation: dict[str, Any]
```

The provider protocol becomes:

```python
class CompletionProvider(Protocol):
    def count_input_tokens(self, request: LogicalCompletionRequest) -> ExactTokenCount: ...
    def complete(self, request: LogicalCompletionRequest) -> AssistantMessage: ...
```

L1/L2/Oracle should use a small `assistant_text()` helper rather than `CompletionObservation.visible_output` once migrated.

## 5. MiniMax adapter migration

Keep the current transport boundary:

```text
MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
```

The transport remains responsible only for one HTTP attempt and generic HTTP/JSON-envelope errors.

`MiniMaxProvider` must:

1. serialize `system_prompt`, typed messages, and ToolDefinitions into MiniMax OpenAI Chat Completions wire objects;
2. send native `tools` rather than rejecting them;
3. parse visible content, reasoning, tool calls, usage, model/id, and finish reason into `AssistantMessage`;
4. strict-parse `function.arguments` while preserving the exact raw string;
5. retain full provider continuation fields needed for subsequent assistant-message replay, including MiniMax reasoning fields;
6. inspect MiniMax provider-level response status such as `base_resp` where applicable and raise typed provider errors before returning a successful AssistantMessage.

Do not broaden this into a generic multi-provider framework.

## 6. Exact token counting

There must be one logical MiniMax serialization path used by both:

```text
count_input_tokens(request)
complete(request)
```

A recommended implementation pattern is:

```text
LogicalCompletionRequest
        ↓
MiniMaxProvider._serialize_request(...)
        ↓
provider messages + tools + thinking mode
        ├─ render through frozen M3 chat template for token count
        └─ convert to HTTP payload for completion
```

The token count must include the same:

- system prompt;
- complete typed message history;
- ToolDefinitions;
- provider continuation fields that affect replay;
- thinking mode;
- generation prompt.

Do not maintain a separate hand-written approximation for L4.

Preflight is run before every logical Model Decision:

```text
exact_input_tokens + reserved_max_completion_tokens <= context_window
```

Dynamic context exhaustion is not otherwise special-cased in V1.

## 7. Initial model-visible input

The stable condition-level system prompt contains L4 Runtime/tool-use/stopping instructions. The shared Task Contract remains runtime-neutral.

The first user message contains:

- Case ID and public Case metadata needed for the task;
- Agent-visible workspace description (`/raw.log`, `/repository/...`);
- explicit statement that physical contents must be acquired through tools;
- full answer-neutral Canonical Evidence coordinate universe usable for final citations.

Do not place Required Evidence, Expected Answer, evaluator labels, curator reasoning, or package-internal filenames in this message.

## 8. Tool contracts

### 8.1 `read`

```text
read(path, offset?, limit?)
```

Rules:

- Agent-visible relative path only;
- `offset` is 1-based;
- `limit` range is 1..2000;
- output <= 2000 lines and <= 50 KiB;
- when more complete lines remain, append an explicit continuation notice with next offset;
- a single source line larger than 50 KiB does not bypass the hard cap; return a clear bounded error/notice rather than adding a new slicing API in V1.

### 8.2 `grep`

```text
grep(pattern, path?, glob?, ignore_case?, literal?, context?, limit?)
```

Rules:

- maximum 100 matches;
- output <= 50 KiB;
- each emitted source line <= 500 characters;
- matching line format is distinguishable from context-line format;
- truncation/limit notices are model-visible;
- no `.gitignore` filtering beyond the already-frozen workspace membership.

### 8.3 `find`

```text
find(pattern, path?, limit?)
```

Rules:

- glob path matching;
- deterministic output over visible workspace membership;
- maximum 1000 results;
- output <= 50 KiB;
- relative paths only.

### 8.4 `ls`

```text
ls(path?, limit?)
```

Rules:

- one directory layer;
- maximum 500 entries;
- output <= 50 KiB;
- deterministic alphabetical ordering;
- directories end with `/`;
- dotfiles are included.

## 9. Tool Registry manifest semantics

The frozen `tool_registry` behavior must include for each tool:

- name;
- provider-visible description;
- complete parameter JSON Schema;
- deterministic workspace/search semantics;
- all output/count/line limits;
- truncation and continuation behavior.

These are behavior-affecting and therefore participate in the component fingerprint.

Implementation class paths and review notes do not belong in behavior identity.

## 10. Tool Policy manifest semantics

Baseline L4 policy:

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

Do not duplicate per-tool allowlist rules in Tool Policy. Availability is defined by Tool Registry.

Future same-L4 ablations may change only policy behavior to `batch + sequential`, then `batch + parallel`.

## 11. Loop pseudocode

```text
messages = [initial_user_message]
steps = 0

while True:
    if steps >= max_steps:
        return scored(max_steps_exhausted, report=None)

    request = build_request(system_prompt, messages, tools)
    exact_preflight(request)

    assistant = complete_with_request_retry(request)
    steps += 1
    persist assistant in trajectory
    trace model completion metadata

    tool_calls = assistant ToolCall blocks

    if tool_calls is empty:
        report = parse_structured_report(assistant_text(assistant))
        if report valid:
            return scored(report_submitted, report)
        return scored(model_stopped_without_valid_report, raw_report)

    if assistant.stop_reason == length:
        append one error ToolResult for every declared ToolCall
        continue

    if policy rejects the call set:
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

The 100th decision may execute its legal ToolAction. The next loop check stops before a 101st model call.

## 12. Provider retry algorithm

A request retry does not mutate Agent-visible state.

```text
logical step N
  attempt 1 -> retryable infra failure
  wait 2s
  attempt 2 -> retryable infra failure
  wait 4s
  attempt 3 -> retryable infra failure
  wait 8s
  attempt 4 -> success
```

Only the successful AssistantMessage is appended to trajectory. Trace records every attempt.

Timeout is a separate one-retry class because the configured per-request deadline can already be long.

Do not perform whole-sample retry automatically.

## 13. Error boundaries

Use three distinct concepts.

### Recoverable Agent-visible error

Examples:

- path not found from a syntactically valid Agent action;
- unknown/disallowed tool;
- invalid args;
- malformed raw arguments;
- multiple calls under single mode;
- truncated ToolCall.

Result: error ToolResult, then another Model Decision.

### Capability terminal

Examples:

- valid report submitted;
- model stops with invalid report;
- max steps exhausted.

Result: `status=scored`.

### Infrastructure terminal

Examples:

- provider request failure after retry policy;
- malformed provider protocol envelope that cannot produce an AssistantMessage;
- Runtime/workspace invariant defect;
- unexpected tool implementation exception;
- static context preflight infeasible;
- scorer/persistence infrastructure defect.

Result: `status=execution_failed` with existing `failure_stage`, `failure_code`, and `failure_message` fields.

## 14. Trace contract

Reuse the existing Trace recorder/table. Add only L4-relevant event payloads, for example:

```text
model_call_started
model_call_failed
model_call_completed
tool_call_started
tool_call_completed
tool_call_error
budget_exhausted
report_submitted
agent_terminal
```

Exact event names can follow existing naming conventions during implementation, but the information boundary is fixed.

Trace should record:

- step index;
- request attempt index;
- provider/model IDs already known from Treatment;
- response/request IDs where available;
- exact token counts/usage;
- latency;
- stop reason;
- tool name/arguments or stable hashes where existing Trace policy requires;
- tool truncation metadata;
- terminal reason;
- infrastructure failure metadata.

Trace does not need to duplicate full AssistantMessage thinking/text bodies when the trajectory store already contains them.

## 15. Trajectory persistence

Add the smallest sample-scoped persistence slice that can reconstruct the exact ordered linear trajectory.

Recommended shape:

```text
evaluation_sample_trajectory_messages
- run_id
- case_id
- repeat_index
- message_index
- message_role
- message_json
- message_sha256
PRIMARY KEY(run_id, case_id, repeat_index, message_index)
```

`message_json` stores the canonical serialized provider-neutral message, including provider-returned thinking and opaque continuation fields. A normalized multi-table content-block schema is unnecessary for V1.

Use the existing SQLite/Alembic migration chain. Do not create session IDs, branch IDs, parent pointers, resume state, conversation trees, or a second storage subsystem.

If implementation shows that a file artifact is materially simpler while preserving run/sample ownership and formal artifact integrity, that can be used instead, but the complete trajectory must be persisted and addressable per sample.

## 16. Matrix and Treatment integration

L4 remains a Matrix v2 condition with `runtime_variant="self_built_react"`.

Treatment identity must reference the frozen:

- Task Contract;
- Tool Registry;
- Tool Policy;
- Runtime-specific model-visible control/instruction identity;
- provider/model/reasoning/generation/context contract.

The current Matrix v2 formal validator only Registry-validates the Task prompt. Issue #52 implementation must extend formal validation so referenced Tool Registry and Tool Policy versions/fingerprints are checked against Component Registry rather than merely embedded as unverified JSON.

Runtime code itself is not a Component Registry component in V1. `runtime_variant + code_revision` represents implementation provenance.

### Retry field

Existing Matrix v2 contains `execution_policy.retry_count`. For L4, this must mean provider-request retry only if retained. A clearer future field name such as `provider_request_retry_count` is preferable, but changing Matrix v2 schema is an implementation migration choice. It must never silently mean whole-sample retry.

## 17. Canonical Evidence and citation behavior

For L4 V1 the complete Canonical coordinate universe is disclosed as answer-neutral citation vocabulary in the initial model-visible input. This is intentionally different from providing Canonical Evidence content or hidden Required Evidence.

The Agent still has to discover physical facts through tools and map those facts to the exposed coordinates itself.

Badcase analysis distinguishes:

```text
A. required physical content not found/seen
   -> acquisition/tool-use problem

B. physical content found but correct Evidence ID not cited
   -> mapping/evidence-selection/report problem

C. correct Evidence ID cited but diagnosis wrong
   -> reasoning problem
```

No dynamic Runtime span-to-Evidence-ID helper is added in L4 baseline.

## 18. Testing plan

Before live qualification, deterministic fake-provider tests should cover at minimum:

1. multi-step read/search trajectory ending in valid report;
2. model stops without valid report;
3. max-steps exhaustion;
4. unknown tool;
5. schema-invalid tool args;
6. malformed raw tool args;
7. `length + ToolCall` rejection and self-repair;
8. multiple ToolCalls under single policy;
9. expected tool-domain error recovery;
10. unexpected tool/runtime exception -> execution failure;
11. transient provider failure then same-request retry success;
12. retry exhaustion -> execution failure;
13. trajectory/Trace separation and persistence;
14. evaluator/package boundary enforcement;
15. 50 KiB/count truncation semantics;
16. exact token counting includes tools and full typed history;
17. MiniMax assistant continuation fields round-trip losslessly.

## 19. Live qualification

Use a very small live qualification before any full Suite run. It must prove:

- MiniMax-M3 native function calling through the existing OpenAI Chat Completions route;
- full assistant `reasoning_details`/continuation round-trip;
- exact token count alignment with the serialized request;
- one real multi-step tool trajectory;
- correct Trace and trajectory persistence;
- no evaluator leakage.

Only after qualification passes should the project run the one planned controlled 20 Case x 3 L4 formal milestone.

## 20. Deferred features

Do not implement until real evidence justifies them:

- compaction/summary/history trimming;
- planner/verifier;
- retrieval optimization;
- Bash/edit/write/CI rerun;
- multi-call sequential/parallel baseline;
- dynamic skills/MCP;
- long-term memory/experience;
- oversized-line slicing;
- whole-sample retry;
- dynamic context-exhaustion special semantics.

## 21. Human Freeze checklist

The implementation may begin when the following are represented in code/config/tests exactly as frozen:

- [ ] typed provider-neutral message contract;
- [ ] MiniMax native-tool and continuation serializer/parser;
- [ ] exact per-turn token counting from the same serializer;
- [ ] `read/grep/find/ls` contracts and hard bounds;
- [ ] frozen Tool Registry and Tool Policy manifests;
- [ ] `single + sequential` policy;
- [ ] `max_steps=100` semantics;
- [ ] request-level retry semantics;
- [ ] terminal `scored/execution_failed` taxonomy;
- [ ] complete linear trajectory persistence separate from Trace;
- [ ] full answer-neutral Canonical coordinate vocabulary in initial input;
- [ ] no compaction or L5+ mechanisms.
