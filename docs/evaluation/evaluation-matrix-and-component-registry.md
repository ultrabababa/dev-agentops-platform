# Evaluation Matrix、Component Registry 与 Formal Evaluation Identity

> Current-state note (2026-08-19): L1/L2/Oracle/L4 historical formal paths均使用 Matrix schema v2。L4 Runtime-control prompt、Tool Registry 与 Tool Policy 已冻结并进入 Component Registry。Oracle↔L4 Pair Analysis 已完成，当前下一代 comparison 将增加 shared deterministic Evidence Reference Canonicalization，并以新 output-realization identity 统一应用到 L1/L2/Oracle/L4；历史 fingerprints 不改写。

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
- historical L4 中 `retry_count=3` 由 L4 executor 解释为 **same-logical-provider-request retries after the initial attempt**；
- 它绝不能触发 whole-sample replay；
- cross-Case concurrency 与 repeat count 不进入 Treatment identity；
- Execution Policy fingerprint 进入 Run Configuration identity。

L4 historical formal milestone 已真实覆盖该语义：一次 transient HTTP 529 在 retry 后恢复；另一次 529 sequence 在 initial + 3 retries 后形成 `execution_failed / provider_request_failed`，没有重跑整个 Sample。

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

Historical L4 相关 frozen components：

```text
prompt
├── structured-triage-task-contract-v1
└── l4-react-runtime-control-v1

tool_registry
└── l4-investigation-tools-v1

tool_policy
└── l4-single-sequential-tool-policy-v1
```

L4 formal doctor/loader 会解析并验证：

```text
Task prompt
Runtime-control prompt
Tool Registry
Tool Policy
```

缺失版本、类型不符或 fingerprint mismatch 都必须在 formal execution 前失败。

## 3. L4 Treatment identity

Historical L4 Treatment 显式引用：

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

Historical L4 baseline Tool Policy 只描述跨 ToolCall execution semantics：

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

Tool availability 已由 Tool Registry 定义，因此 L4 V1 不在 Tool Policy 中复制第二套 allowlist，也不使用 `default_action`。

当前已经有真实 formal evidence 支持后续测试 `batch + parallel`：historical L4 run 记录了 `26` 个 `multiple_tool_calls_rejected` ToolCall IDs。该变化属于新的 Tool Policy behavior / Treatment，不是 Runtime 内部无身份变化的开关；同时必须更新 Runtime-control prompt，因为 historical prompt 明确规定 zero-or-one ToolCall。

### 3.3 Runtime-control prompt

Shared Task Contract 保持 Runtime-neutral。L4-specific tool-use、loop、stopping、report-submission instructions 是独立 frozen `prompt` component，通过 Treatment 的 `contracts.runtime_control` 记录 version + fingerprint。

这些 instruction 不应隐藏在：

- Case `runtime_input`；
- Tool Registry metadata；
- Tool Policy metadata；
- unversioned Python constants。

## 4. L4 context identity — ADR 0129

ADR 0129 改变了 L4 的 context-accounting Treatment identity，但没有改 L1/L2/Oracle 的 exact-token path。

Historical/current L4 V1 context contract：

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
- no compaction / no automatic trimming remains part of the baseline behavior。

任何未来 predictive budgeting、compaction 或 provider/server truncation policy 都必须以显式 Treatment / ADR change 表达。

## 5. Evidence delivery、Canonical vocabulary 与 shared output resolution

Case/Suite identity 冻结 Physical Artifacts、Canonical coordinates、Evaluator Ground Truth 与 provenance。

Evidence acquisition/delivery 属于 condition/Treatment semantics。Historical L4 V1：

- Tool filesystem 只暴露 `/raw.log` 和 `/repository/...` physical workspace；
- full answer-neutral Canonical coordinate vocabulary 作为 initial model input 的 citation vocabulary；
- Canonical content、Required Evidence labels、Expected Answer/evaluator artifacts 不暴露；
- physical facts 仍由 Agent tool acquisition 获得。

因此不能把“Canonical coordinates 存在于 Case Package”与“某 condition 是否把 coordinate vocabulary 发送给模型”混成一个 Case schema 问题。

Historical L4 milestone 暴露了一个重要 output-realization defect：模型可能已经定位到一个物理 line range，却生成不存在的 aggregate Evidence ID。最初曾计划把它做成 L4-only physical-span -> Canonical-coordinate assistance；该方向已被后续 Pair Analysis **supersede**。

当前决策是：**Deterministic Evidence Reference Canonicalization 是 shared final-report/output infrastructure，统一用于新一代 L1/L2/Oracle/L4 comparison。** 它不改变各 condition 的 `runtime_variant` 或 evidence-acquisition semantics。

概念链：

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

same-family explicit line range
    -> deterministic overlap mapping to frozen Canonical unit(s)
    -> deduplicate

unresolvable
    -> remain invalid
```

它不得读取 Required Evidence / Expected Answer，不做 fuzzy/semantic repair，也不根据 diagnosis 选择“应该引用”的 Evidence。Raw model candidate 与 resolved candidate 应保留可审计边界。

### 5.1 Identity placement

Shared canonicalization 不是新的 `runtime_variant`，也不是 L4 Tool Registry / Tool Policy。它改变 final output realization behavior，因此必须进入新的显式 output/Treatment identity，并在 L1/L2/Oracle/L4 的新 comparison generation 中一致引用。

当前 Matrix v2 `treatment.contracts` 已承载 shared output contract identity；具体新 version/fingerprint 在实现时冻结。若现有 output contract representation 不足以表达 resolution semantics，应做最小必要 schema/contract identity extension，而不是把行为藏在 Python 常量里。

Historical L1/L2/Oracle/L4 Treatment/Condition fingerprints 绝不能 retroactively 改写。

## 6. Formal doctor validation

当前 doctor/formal path 在任何 model cost 发生前验证至少包括：

- Matrix v2 schema / condition selection；
- frozen Component existence/type/fingerprint；
- Suite / Case identity and fingerprints；
- applicable Treatment invariants；
- L4 Task/Runtime-control/Tool Registry/Tool Policy references；
- run configuration construction prerequisites。

Shared canonicalization 落地后，新 comparison generation 的 doctor 还必须验证各 condition 引用同一目标 output-resolution contract identity；旧 historical matrices 继续保持原样可解释。

Historical L4 formal 20×3 run 使用：

```text
condition = l4-minimax-m3-adaptive-development-v1
runtime_variant = self_built_react
repeat_count = 3
max_case_concurrency = 6
retry_count = 3
request_timeout_seconds = 600
```

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
6. [Oracle ↔ L4 Pair Analysis Findings](milestones/oracle-l4-pair-analysis-2026-08-19.md) for the current badcase-driven decision；
7. [Milestone Status Index](milestones/README.md) before using other dated milestone files；
8. earlier Matrix v1 material only for historical compatibility。

## 9. 不应静默改变的历史身份

后续 Runtime evolution 不应为了 convenience 静默改变：

- frozen Suite / Case fingerprints；
- historical L1/L2/Oracle/L4 Treatment/Condition/Execution fingerprints；
- historical scorer/report/output-realization contract；
- previous milestone artifacts。

Shared canonicalization、batch+parallel Tool Policy 或其他新 capability 都必须以新配置身份表达。新行为生成新结果；旧 run 继续代表旧 contract，不能 retroactively reinterpret。
