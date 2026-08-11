# Runtime Capability Ladder 与 Model-backed Diagnostic Conditions

本文把 DevAgentOps 的 Runtime 演进组织成可归因的 capability ladder。它回答的是“这个条件增加了什么能力、应与谁比较、结果能说明什么”，不是规定所有能力必须按编号实现。

## 1. 为什么需要 capability ladder

只比较 deterministic Pipeline 与完整 ReAct，会一次引入模型推理、Prompt、分阶段处理、证据获取、工具循环、上下文管理和停止决策。即使 ReAct 得分更高，也无法判断 uplift 主要来自哪一项。

Ladder 通过受控条件逐层描述能力，使 paired per-Case comparison 可以尽量固定 Case、Evidence Universe、base model、诊断 Prompt、Report Contract、Scorer、Inference Settings 和其他声明的控制变量，只改变目标能力。它是 capability attribution framework，不是“编号越大一定越好”的排名，也不是强制 implementation dependency graph。

## 2. Ladder 总览

| Level | Capability condition | Model | 控制流 | Evidence acquisition | 定位 |
| --- | --- | --- | --- | --- | --- |
| L0 | `deterministic_pipeline` | 无 | 程序固定 | deterministic fixed access | Fixed Pipeline Product Runtime baseline |
| L1 | `full_context_one_shot` | 单次调用 | 固定 Prompt，无循环 | 完整 Agent-visible Universe 一次性提供 | diagnostic/comparison condition |
| L2 | `fixed_model_workflow` | 多阶段调用 | 程序决定阶段与下一步 | 固定、显式的输入流 | diagnostic/comparison condition |
| L3 | `static_retrieval` | model-backed | 程序固定 | 静态 Retrieval 选择证据 | evidence-acquisition diagnostic condition |
| L4 | `self_built_react` | model-backed | 模型参与 adaptive next-action/stop decision | search/open/tool observation loop | 第一个 Agentic Product Runtime |
| L5+ | incremental Agent capabilities | model-backed | 逐步增强 | retrieval/context/planning 等逐步演化 | Agent Runtime kernel lineage 后续演进 |

L0–L5+ 描述能力增量，不强制交付顺序。尤其是 L3 是否必须早于 L4 实现，当前不冻结。

## 3. 各层冻结语义

### L0 — deterministic pipeline

- 无模型调用，无 Agent。
- Runtime 控制流与报告生成完全确定。
- Issue #16 已发布的身份仍是 `runtime_variant="pipeline_baseline"`。
- `deterministic_pipeline` 只是 capability-level 名称，不触发历史 rename，也不要求 Matrix/Registry schema 变化。

L0 回答：在没有模型推理和 Agent 控制的情况下，当前固定流程与 scorer/trace/persistence baseline 能做到什么。

### L1 — full-context one-shot

- 将该条件下完整的 Agent-visible Evidence Universe 放入固定 Prompt。
- 恰好一次 model call。
- 不提供自主工具循环，也不允许模型决定下一阶段。
- 是非 Agentic diagnostic condition，不是 Product Runtime。

“Full-context” 是结果身份的一部分，不能 silent truncation。如果完整可见 Universe 超出固定 context budget，截断后的 run 不得继续宣称自己是 L1 full-context condition。当前 L1 tracer bullet 对完整 rendered request 做精确 preflight；超出 `262144` context capability 时以零 provider call 的 execution failure 结束，不 truncation、summarization、splitting、retry 或 relabel。

L1 回答：移除 evidence acquisition 难度、但不给予多阶段 orchestration 或 Agent loop 时，单次模型推理能做到什么。

### L2 — fixed model workflow

- model-backed，并允许固定的多阶段调用。
- 所有阶段、阶段顺序、输入流和终止条件由程序决定。
- 模型不自主循环，也不决定下一项工具或下一阶段。
- 是非 Agentic diagnostic/comparison condition。

当前 L2 tracer bullet 固定为：

```text
evidence_analysis -> report_synthesis -> stop
```

两个 stage 均复用 `structured-triage-task-contract-v1`、完整 Agent-visible Evidence Universe、SiliconFlow `Qwen/Qwen3.5-4B` 与相同 inference settings。每个 stage 各有 exactly one `user` message 和一次独立 context preflight。Stage 1 返回 versioned structured memo；只要 provider 成功返回 string（包括 malformed 或 empty），程序就把 exact visible string 作为显式 case-scoped handoff 交给 Stage 2，不用 parse/validation gate、repair 或 retry。Stage 2 再次获得完整 Universe 与 memo，产生最终 Structured Triage Report 后程序固定 stop。任一 provider/transport/protocol failure 或对应 stage 的 context infeasibility 才停止执行。

这个 tracer bullet 没有 tools、Retrieval、evidence selection、adaptive transition、autonomous loop 或 verifier。L2 回答的是固定 two-stage workflow package 相对 L1 的 combined difference；它同时改变 call count、stage controls、intermediate representation、重复 evidence exposure、aggregate output allowance、cost/latency 和 failure surface，不能把差异强归因于单一 capability。

### L3 — static retrieval

- 在 model-backed fixed path 前加入 versioned static retrieval。
- Retrieval 对 Physical Evidence Universe 建立或查询自己的 Runtime chunks，再将实际 physical spans 映射到 Canonical Evidence coordinates。
- 程序控制 retrieval 和后续流程；没有 adaptive Agent loop。
- 是 evidence-acquisition diagnostic condition，不是 Product Runtime。

本文不冻结 chunking、query generation、top-k、reranker、index 或 prompt 机制，也不规定 L3 必须先于 L4 实现。L3 回答：静态 evidence acquisition 相对 full-context/fixed workflow 带来什么收益或损失。

### L4 — self-built ReAct

- 第一个真正 Agentic 的 Runtime。
- 形成 adaptive decision → tool → observation → context update → next action/stop → report loop。
- 模型可以在 tool policy、step/token/time budgets 和 Runtime validation 约束内决定下一步调查行为。
- 是 V1 的第二个 Product Runtime，也是后续 Agent Runtime kernel lineage 的起点。

L4 不是对外部 Runtime 的包装。DevAgentOps 自己实现 state、loop、tool/event/provider/stop/context seams，并保持既有安全和评测边界。

### L5+ — incremental Agent capabilities

Retrieval、context management、planning、verifier、skills、experience 与后续能力应作为明确增量进入 Agent Runtime kernel 或受控实验条件。具体 level 编号、组合、产品化状态与实现顺序由未来 ADR/Issue 决定，不由本文预先冻结。

## 4. Product Runtime 与 diagnostic condition

V1 Product Runtime 只有：

1. Fixed Pipeline（当前 `pipeline_baseline`）；
2. self-built ReAct（L4）。

L1、L2、L3 用于解释性能来源。它们可以拥有可执行的 condition、trace 和 manifest，但不因此成为第三、第四或第五种 Product Runtime。当前 L2 tracer bullet 把 workflow、stage controls、memo schema 与 handoff 的 version/fingerprint 写入 Run Manifest，但不扩 Matrix/Registry schema。

因此当前 Condition Fingerprint 单独不能代表完整 L2 treatment identity；解释 tracer-bullet run 时必须同时使用 Condition Fingerprint、L2 Manifest identity block 和 code revision。这个 limitation 必须在 Formal L1→L2 comparison 前关闭，当前 tiny fixture 结果不得作为正式 quality/uplift evidence。

## 5. 与 Evidence Universe、Workspace 和 Oracle 的关系

Evidence Universe 定义 Case 世界中存在什么；Investigation Workspace 是 Runtime-facing view；Evidence Acquisition Condition 定义一个 Runtime 如何观察这个世界。L1 的“一次性完整提供”是一个明确 diagnostic delivery condition，不会改变 Physical Artifacts、Canonical Evidence 或 Trusted Evaluator 的边界，也不把 evaluator-only artifacts 变为 Agent-visible。

Normal L1/L2/L3/L4 都不得读取 `evaluator/required-evidence.json` 或 `evaluator/expected-answer.json`。Canonical Evidence 仍是 measurement/citation coordinates，不自动成为 Prompt menu 或 Retrieval chunks。

Oracle Evidence 是与 ladder 正交的 diagnostic intervention：它用 Trusted Builder 从 Required Evidence IDs 解析 Minimal Sufficient Evidence Set，绕过普通 discovery。Oracle 不占 rung，不是 Product Runtime，也不能与 L1 full-context 混同：L1 接收完整 Agent-visible Universe，Oracle 接收 hidden Ground Truth 导出的最小充分证据。

## 6. 受控比较与解释边界

有意义的比较应优先形成单能力差异，并明确记录未能固定的变量：

| 比较 | 主要归因问题 |
| --- | --- |
| L0 vs L1 | 引入固定单次模型推理后发生什么？ |
| L1 vs L2 | 固定多阶段 orchestration 带来什么？ |
| L2 vs L3 | 静态 evidence acquisition 带来什么？ |
| L3 vs L4 | adaptive Agent control 带来什么？ |
| Normal condition vs Oracle | evidence discovery/management 与已知关键证据时的诊断能力之间差多少？ |

实际实验不必按这张表的顺序实现或运行。若两个条件同时改变多个变量，结果只能解释为组合差异，不能宣称单项能力的因果 uplift。

## 7. Pi reference architecture

当前 canonical upstream 是 [`earendil-works/pi`](https://github.com/earendil-works/pi)。`badlogic/pi-mono` 仅作为 historical lineage / old repository name 记录，不是当前 canonical reference。

正式 ReAct design 可以参考 Pi 的：

- Agent state 与 loop decomposition；
- tool interface 与 event flow；
- model-provider seam；
- stop condition 与 budget enforcement；
- context management。

边界同样明确：Pi 不是 dependency、compatibility target 或 DevAgentOps Runtime semantics 来源；本 Issue 不复制或冻结 Pi API。正式 ReAct design 时再建立 reference matrix，并逐项说明采用、自研或拒绝的理由。

DevAgentOps 始终保留 bounded Investigation Workspace、evaluation-first、Trusted Evaluator/leakage boundary、explicit tool policy 与 diagnosis-only scope。

## 8. 本文不决定什么

- L3/L4 的实现、provider 或 Prompt；
- L2 tracer bullet 之后的通用 workflow 表示；
- Formal L2 comparison 所需的 Matrix/Registry fingerprint representation；
- L3 chunk/query/top-k/index/reranker；
- L3 与 L4 的实现先后；
- L5+ 的具体 level 分配；
- Matrix、Registry、Run Manifest 或 Runtime schema 的新字段名；
- Pi API/reference matrix。

## 9. 相关决策

- [ADR 0002: Build a Lightweight ReAct Runtime First](../adr/0002-self-built-react-runtime-first.md)
- [ADR 0112: V1 Runtime Scope](../adr/0112-v1-runtime-scope.md)
- [ADR 0113: Evaluation Comparison Model](../adr/0113-evaluation-comparison-model.md)
- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](../adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [Formal Evaluation Methodology: Evidence Universe and Access Conditions](formal-evaluation-methodology.md)
