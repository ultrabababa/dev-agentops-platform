# Evaluation Matrix、Component Registry 与 Formal Evaluation Identity

> Current-state note (2026-08-24): L1/L2/L3/Oracle/L4 formal paths 均使用 Matrix schema v2。Shared deterministic Evidence Reference Canonicalization 已作为五个 model-backed conditions 的共同 output-realization identity 落地；L3 Static Retrieval V1 已完成 clean live `20×3` formal milestone 与 evaluator-side acquisition analysis。L4 Batch + Parallel Tool Policy 也已完成 initial formal run 与 fresh replication；它现在是 new L4 evaluations / Runtime evolution 的推荐 Tool Policy。Historical fingerprints、single/sequential matrices 与 milestone artifacts 不改写。

本文说明当前 Formal Evaluation 的配置身份链：

```text
Matrix v2 condition
    -> Treatment identity
    -> Execution Policy identity
    -> frozen Component references
    -> Suite / Case identity
    -> code revision + git state
    -> Run Configuration fingerprint
```

Formal result 的可解释性依赖这条身份链。不能只记录一个 condition name，也不能把 behavior-affecting change 藏进未版本化代码常量。

## 1. Matrix v2

当前 `src/devagentops/evaluation/matrix_v2.py` 对 condition 使用严格字段：

```text
id
type
runtime_variant
suite
evaluation_method
treatment
execution_policy
```

`type`：

```text
anchor | ablation | candidate
```

### 1.1 Treatment

Treatment 顶层严格包含：

```text
provider
model
reasoning
generation
contracts
context
```

Provider 字段：

```text
id
transport
profile
base_url
```

Treatment 表达**会改变 Agent/model-visible behavior、model execution semantics 或 output-realization semantics 的条件身份**。它不是 execution scheduler 配置，也不是整个 run manifest。

### 1.2 Execution Policy

当前严格字段：

```text
repeat_count
max_case_concurrency
retry_count
request_timeout_seconds
```

Execution Policy 属于 formal execution mechanics，不是 Agent Tool Policy。

当前语义：

- L1/L2/Oracle historical formal conditions 保持 `retry_count=0`；
- L4 中 `retry_count=3` 由 L4 executor 解释为 **same-logical-provider-request retries after the initial attempt**；
- 它绝不能触发 whole-sample replay；
- cross-Case concurrency 与 repeat count 不进入 Treatment identity；
- Execution Policy fingerprint 进入 Run Configuration identity。

Historical L4 milestone 已真实覆盖 transient 529 recovery 和 retry exhaustion；initial Batch + Parallel formal run 还覆盖了一个 `600 s` provider timeout 后 same-request retry 成功。Replication block 没有 provider retry failure。

### 1.3 Fingerprints

当前 v2：

```text
treatment_fingerprint
= SHA256(canonical treatment)

execution_policy_fingerprint
= SHA256(canonical execution_policy)

condition_fingerprint
= SHA256({
    type,
    runtime_variant,
    suite,
    evaluation_method,
    treatment_fingerprint
  })
```

Execution Policy 不进入 Condition Fingerprint，但会进入 Run Configuration identity。

Run Configuration 还覆盖：

- Matrix identity；
- Condition / Treatment / Execution Policy fingerprints；
- Suite fingerprint；
- selected Cases；
- `code_revision`；
- `git_dirty`；
- applicable run kind。

因此：

```text
Condition fingerprint
!= complete run identity
```

## 2. Component Registry

Component Registry schema V1 当前支持六类：

| Type | behavior contract |
| --- | --- |
| `prompt` | `template`, optional `variables` |
| `tool_registry` | `tools[]` |
| `retriever_config` | `strategy`, `settings` |
| `tool_policy` | `rules[]`, optional `default_action` |
| `mcp_server_set` | `servers[]` |
| `skill_registry` | `skills[]` |

Component fingerprint 只 hash canonicalized `manifest.behavior`。`metadata` 是 review/provenance 信息，不影响 behavior fingerprint。

Current L4 相关 frozen components 保留两组显式 Tool Policy Treatment：

```text
shared task prompt
└── structured-triage-task-contract-v1

historical L4 reference
├── prompt: l4-react-runtime-control-v1
└── tool_policy: l4-single-sequential-tool-policy-v1

recommended forward L4 treatment
├── prompt: l4-react-runtime-control-batch-parallel-v1
└── tool_policy: l4-batch-parallel-tool-policy-v1

shared tool_registry
└── l4-investigation-tools-v1
```

L4 formal doctor/loader 会解析并验证：

```text
Task prompt
Runtime-control prompt
Tool Registry
Tool Policy
```

缺失版本、类型不符、fingerprint mismatch 或不支持的 Runtime-control/Tool Policy pairing 都必须在 formal execution 前失败。

## 3. L4 Treatment identity

L4 Treatment 显式引用：

1. shared Task Contract `prompt`；
2. L4 Runtime-control `prompt`；
3. L4 `tool_registry`；
4. L4 `tool_policy`；
5. provider/model/reasoning/generation/context contract。

Runtime implementation 自身不新增 `runtime` Component type。Implementation provenance 由：

```text
runtime_variant + code_revision
```

表示。

### 3.1 Tool Registry

L4 Tool Registry 是 provider-visible Tool contract 与 deterministic Tool behavior 的冻结来源，包括：

- `read / grep / find / ls` names；
- descriptions；
- complete parameter JSON Schemas；
- workspace/search semantics；
- output/count/line caps；
- ordering；
- truncation/continuation semantics。

例如：

```text
grep.max_matches: 100 -> 200
```

是 behavior change，必须改变 Tool Registry identity，而不能只改 Python 实现。

### 3.2 Tool Policy

Historical L4 baseline Tool Policy：

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

Recommended forward L4 Tool Policy：

```json
{
  "rules": [
    {
      "scope": "model_decision",
      "call_mode": "batch",
      "execution_mode": "parallel",
      "multiple_calls": "accept_independently"
    }
  ]
}
```

Tool availability 已由 Tool Registry 定义，因此 Tool Policy 不复制第二套 allowlist，也不使用 `default_action`。

Batch + Parallel semantics are part of Treatment identity, not an unversioned Runtime switch. The matching Runtime-control prompt is also separately frozen because the historical prompt explicitly required zero-or-one ToolCall.

The accepted Batch semantics are:

- zero/one/multiple ToolCalls per Model Decision;
- no arbitrary ordinary-call count cap;
- malformed / expected errors isolated per call;
- valid siblings execute concurrently;
- no dedupe of duplicate calls;
- barrier before next Model Decision;
- ToolResults materialized in model-authored order;
- one Model Decision still consumes one `max_steps` unit;
- unexpected Runtime/workspace/tool defects remain Sample-level infrastructure failures;
- `stop_reason=length` still executes none of the calls;
- prompt exposes capability neutrally and does not say to prefer batching.

The fresh replication observed `228` multi-call decisions across `49/60` Samples, including two size-5 batches, with no arbitrary cap and no `multiple_tool_calls_rejected` events.

### 3.3 Runtime-control prompt

Shared Task Contract 保持 Runtime-neutral。L4-specific tool-use、loop、stopping、report-submission instructions 是独立 frozen `prompt` component，通过 Treatment 的 `contracts.runtime_control` 记录 version + fingerprint。

这些 instruction 不应隐藏在：

- Case `runtime_input`；
- Tool Registry metadata；
- Tool Policy metadata；
- unversioned Python constants。

Historical and Batch Runtime-control prompts remain separate frozen identities. Do not pair the Batch Tool Policy with the historical zero-or-one Runtime-control prompt or vice versa.

## 4. L4 context identity — ADR 0129

ADR 0129 改变了 L4 的 context-accounting Treatment identity，但没有改 L1/L2/Oracle 的 exact-token path；L3 后续冻结为 L1-style exact-token preflight identity。

Current L4 context contract：

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
context_window_tokens = 1_000_000
```

因此：

- L4 Runtime critical path 不以 `count_input_tokens()` 作为 request gate；
- provider-returned `usage.input_tokens` 是 completed Model Decision 的 observed accounting；
- tokenizer/chat-template assets 不属于 L4 context Treatment identity；
- context-window metadata 仍是 Treatment identity；
- no compaction / no automatic trimming remains part of current L4 behavior。

任何未来 predictive budgeting、compaction 或 provider/server truncation policy 都必须以显式 Treatment / ADR change 表达。

## 5. Evidence delivery、Canonical vocabulary 与 shared output resolution

Case/Suite identity 冻结 Physical Artifacts、Canonical coordinates、Evaluator Ground Truth 与 provenance。

Evidence acquisition/delivery 属于 condition/Treatment semantics。L4：

- Tool filesystem 只暴露 `/raw.log` 和 `/repository/...` physical workspace；
- full answer-neutral Canonical coordinate vocabulary 作为 initial model input 的 citation vocabulary；
- Canonical content、Required Evidence labels、Expected Answer/evaluator artifacts 不暴露；
- physical facts 仍由 Agent tool acquisition 获得。

因此不能把“Canonical coordinates 存在于 Case Package”与“某 condition 是否把 coordinate vocabulary 发送给模型”混成一个 Case schema 问题。

Historical L4 milestone 暴露了一个重要 output-realization defect：模型可能已经定位到一个物理 line range，却生成不存在的 aggregate Evidence ID。Pair Analysis 决定将修复放在 shared final-report/output infrastructure，而不是 L4-only helper。

`canonical-line-range-normalization-v1` 现在已作为 shared behavior 落地：

```text
runtime-specific raw candidate document
    -> shared Evidence Reference Canonicalization
    -> Structured Report validation
    -> frozen scorer
```

Resolver 只做 representation normalization：

```text
exact Canonical ID
    -> preserve

same source identity + explicit line range
    -> deterministic overlap mapping to frozen Canonical unit(s)
    -> deduplicate

unresolvable
    -> remain invalid
```

它不得读取 Required Evidence / Expected Answer，不做 fuzzy/semantic repair，也不根据 diagnosis 选择“应该引用”的 Evidence。Raw model candidate 与 resolved candidate 保留可审计边界。

### 5.1 Identity placement

Shared canonicalization 不是新的 `runtime_variant`，也不是 L4 Tool Registry / Tool Policy。它改变 final output realization behavior，因此进入显式 output/Treatment identity。Current canonicalized L1/L2/L3/Oracle/L4 matrices use output contract `development-v2` with resolver identity `canonical-line-range-normalization-v1`.

Historical L1/L2/Oracle/L4 Treatment/Condition fingerprints 绝不能 retroactively 改写。

## 6. Formal doctor validation

当前 doctor/formal path 在任何 model cost 发生前验证至少包括：

- Matrix v2 schema / condition selection；
- frozen Component existence/type/fingerprint；
- Suite / Case identity and fingerprints；
- applicable Treatment invariants；
- L4 Task/Runtime-control/Tool Registry/Tool Policy references；
- L3 retriever component existence/type/fingerprint and static-retrieval Treatment invariants；
- supported L4 Runtime-control / Tool Policy pairing；
- run configuration construction prerequisites。

Shared canonicalization matrices 显式引用相同目标 output-resolution contract identity；historical matrices 继续保持原样可解释。

Recommended new L4 formal configuration uses:

```text
matrix = l4-minimax-m3-batch-parallel-canonicalized-v1.json
condition = l4-minimax-m3-batch-parallel-canonicalized-development-v1
runtime_variant = self_built_react
repeat_count = 3
max_case_concurrency = 6
retry_count = 3
request_timeout_seconds = 600
```

The canonicalized single/sequential Matrix remains a controlled reference, not a file to rewrite into the new policy.

## 7. Legacy Matrix v1

仓库仍保留历史 Matrix v1 兼容路径和早期文档/实验身份。早期 schema 使用 Defaults、一层 `extends`、`components`、`budgets`、`repeats` 等结构。

这些历史文件用于重放/解释旧 run，不是当前新 condition 的模板。不要：

- 用 Matrix v1 示例推断 Matrix v2 字段；
- 为了“统一”而重写历史 fingerprints；
- 把旧 `budgets` container 直接映射成 L4 Runtime budgets。

## 8. Source of truth reading order

当身份/配置文档冲突时，优先按：

1. [Active ADR Index](../adr/README.md)；
2. `README.md` / `CONTEXT.md` current-facing orientation；
3. [Formal Evaluation Methodology](formal-evaluation-methodology.md)；
4. [ADR 0128 — L4 Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md) + [ADR 0129 — L4 Context Accounting](../adr/0129-l4-provider-reported-context-accounting.md) for historical/frozen L4 V1 behavior；
5. current `src/devagentops/evaluation/matrix_v2.py` / Registry validation / checked-in Matrix v2 files；
6. [L4 Batch + Parallel ToolCalls Milestone](milestones/l4-batch-parallel-toolcalls-2026-08-19.md) for the current Tool Policy recommendation and replication evidence；
7. [Shared Evidence Reference Canonicalization Milestone](milestones/evidence-reference-canonicalization-2026-08-19.md) for the completed shared output-resolution decision；
8. [Oracle ↔ L4 Pair Analysis Findings](milestones/oracle-l4-pair-analysis-2026-08-19.md) for the historical badcase-driven input；
9. [Milestone Status Index](milestones/README.md) before using other dated milestone files；
10. earlier Matrix v1 material only for historical compatibility。

## 9. 不应静默改变的历史身份

后续 Runtime evolution 不应为了 convenience 静默改变：

- frozen Suite / Case fingerprints；
- historical L1/L2/Oracle/L4 Treatment/Condition/Execution fingerprints；
- historical single/sequential Runtime-control / Tool Policy identities；
- historical scorer/report/output-realization contract；
- previous milestone artifacts。

Shared canonicalization、Batch + Parallel Tool Policy 或其他新 capability 都必须以新配置身份表达。新行为生成新结果；旧 run 继续代表旧 contract，不能 retroactively reinterpret。
