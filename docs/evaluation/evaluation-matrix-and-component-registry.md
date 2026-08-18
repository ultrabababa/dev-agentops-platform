# Evaluation Matrix、Component Registry 与 Formal Evaluation Identity

> Current-state note (2026-08-18): 当前正式 L1/L2/Oracle 路径使用 **Matrix schema v2**。本文已把 Matrix v2 放到主叙事；早期 Defaults/`extends` Matrix v1 仅作为历史兼容路径，不再作为 L4 实现模板。

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

## 1. 当前 Matrix v2

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

`type` 为：

```text
anchor | ablation | candidate
```

### 1.1 Treatment

当前 Treatment 顶层严格包含：

```text
provider
model
reasoning
generation
contracts
context
```

Provider 当前字段：

```text
id
transport
profile
base_url
```

L1 MiniMax development Matrix 是当前可执行示例，而不是早期文档中的 hypothetical `defaults/components/budgets/repeats` Matrix。

### 1.2 Execution Policy

当前严格字段：

```text
repeat_count
max_case_concurrency
retry_count
request_timeout_seconds
```

这里的 execution policy 是 outer evaluation/request execution mechanics，不是 Agent Tool Policy。

历史 L1/L2/Oracle 条件使用 `retry_count=0`。ADR 0128 对 L4 冻结了 **same-logical-provider-request retry** 语义；Issue #52 实现必须避免把当前 `retry_count` 偷偷解释为 whole-sample restart。可以通过明确迁移/重命名为 `provider_request_retry_count` 等方式收口，但历史 fingerprint 不得被静默改写。

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
- Condition/Treatment/Execution Policy fingerprints；
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

Component Registry schema V1 仍支持六类：

| Type | behavior contract |
| --- | --- |
| `prompt` | `template`, optional `variables` |
| `tool_registry` | `tools[]` |
| `retriever_config` | `strategy`, `settings` |
| `tool_policy` | `rules[]`, optional `default_action` |
| `mcp_server_set` | `servers[]` |
| `skill_registry` | `skills[]` |

Component fingerprint 仍然只 hash canonicalized `manifest.behavior`。`metadata` 是 review/provenance 信息，不影响 behavior fingerprint。

当前 Registry 中只有共享 `structured-triage-task-contract-v1` prompt 已冻结；L4 的 Runtime-control prompt、Tool Registry 与 Tool Policy 尚未创建，因为 Issue #52 implementation 尚未开始。这是预期状态，不表示 L4 设计未冻结。

## 3. L4 Treatment identity

ADR 0128 冻结 L4 需要显式引用：

1. shared Task Contract `prompt`；
2. separate L4 Runtime-control `prompt`；
3. L4 `tool_registry`；
4. L4 `tool_policy`；
5. provider/model/reasoning/generation/context contract。

Runtime implementation 自身不新增 `runtime` Component type。实现 provenance 继续由：

```text
runtime_variant + code_revision
```

表示。

### 3.1 Tool Registry

L4 Tool Registry 是 provider-visible Tool contract 的唯一冻结来源，必须 fingerprint：

- `read / grep / find / ls` names；
- descriptions；
- complete parameter JSON Schemas；
- workspace/search semantics；
- output/count/line caps；
- truncation/continuation semantics。

例如 `grep.max_matches: 100 -> 200` 属于 Tool Registry behavior change。

### 3.2 Tool Policy

L4 baseline Tool Policy 只描述跨 ToolCall execution semantics：

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

Tool availability 已由 Tool Registry 定义，因此 L4 V1 不需要在 Tool Policy 中复制第二套 allowlist，也不使用 `default_action`。

### 3.3 Runtime-control prompt

Shared Task Contract 保持 Runtime-neutral。L4-specific tool-use、loop、stopping、report-submission instructions 是**第二个 frozen `prompt` component**，在 Treatment 的 `contracts.runtime_control` 下记录 version + fingerprint。

不要把这些 instruction 藏在：

- Case `runtime_input`；
- Tool Registry description；
- Tool Policy；
- unversioned Python constant。

## 4. 当前 Formal Registry validation 的 gap

Matrix v2 当前 formal loader 只 Registry-validates shared Task prompt reference。Issue #52 必须扩展 doctor/formal validation，使以下引用都通过 Component Registry resolution + fingerprint check：

```text
Task prompt
Runtime-control prompt
Tool Registry
Tool Policy
```

这是 L4 implementation acceptance requirement，不是需要再设计的新架构问题。

## 5. Evidence delivery 与 Canonical vocabulary

Case/Suite identity 继续冻结 Physical Artifacts、Canonical coordinates、Evaluator Ground Truth 与 provenance。

Evidence acquisition/delivery 属于 condition/Treatment 语义。特别是 L4 V1：

- Tool filesystem 只暴露 `/raw.log` 和 `/repository/...` physical workspace；
- full answer-neutral Canonical coordinate vocabulary 可作为 initial model input 的 citation vocabulary；
- Canonical content、Required Evidence labels、Expected Answer/evaluator artifacts 不暴露；
- physical facts 仍由 Agent tool acquisition 获得。

因此不能把“Canonical coordinates 存在于 Case Package”与“某 condition 是否把坐标 vocabulary 发送给模型”混为一个 Case schema 问题。

## 6. Legacy Matrix v1

仓库仍保留历史 Matrix v1 兼容路径和早期文档/实验身份。早期 schema 使用 Defaults、一层 `extends`、`components`、`budgets`、`repeats` 等结构。

这些历史文件用于重放/解释旧 run，不是当前 L4 新条件的模板。不要：

- 用 Matrix v1 示例推断 Matrix v2 字段；
- 为了“统一”而重写历史 fingerprints；
- 把旧 `budgets` container 直接映射成 L4 Runtime budgets。

L4 应从现行 Matrix v2 + ADR 0128 设计出发。

## 7. Source of truth reading order

当文档冲突时，L4 实现按以下优先级阅读：

1. [ADR 0128 — L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md)
2. [L4 Self-built ReAct Runtime Design](l4-self-built-react-runtime-design.md)
3. current `src/devagentops/evaluation/matrix_v2.py` / `components.py`
4. current checked-in Matrix v2 files；
5. earlier Matrix v1 documentation only for historical compatibility。

## 8. 不应静默改变的历史身份

Issue #52 不应为了 L4 convenience 静默改变：

- frozen Suite / Case fingerprints；
- historical L1/L2/Oracle Treatment/Condition/Execution fingerprints；
- existing scorer/report contract；
- previous milestone artifacts。

任何 schema migration 都要以新配置身份表达，而不是 retroactively reinterpret old runs。
