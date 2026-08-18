# Runtime Capability Ladder 与 Model-backed Diagnostic Conditions

> Current-state note (2026-08-18): 本文已按已完成的 L1/L2/Oracle formal milestones 与 ADR 0128 的 L4 Human Freeze 更新。历史 PR、milestone 文档与 archived micro ADR 仍记录当时状态，不应覆盖本文与当前 Active ADR 的现行语义。

本文把 DevAgentOps 的 Runtime 演进组织成可归因的 capability ladder。它回答“这个条件增加了什么能力、应与谁比较、结果能说明什么”，不是规定所有能力必须按编号实现。

## 1. Ladder 总览

| Level | Capability condition | Model | 控制流 | Evidence acquisition | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| L0 | `deterministic_pipeline` | 无 | 程序固定 | deterministic fixed access | Product Runtime baseline 已实现；历史 runtime identity 仍为 `pipeline_baseline` |
| L1 | `full_context_one_shot` | 单次调用 | 固定 Prompt，无循环 | 完整 Agent-visible Universe upfront | MiniMax-M3 20 Case × 3 formal milestone 已完成 |
| L2 | `fixed_model_workflow` | 多阶段调用 | 程序固定 stages | 固定显式 input flow | MiniMax-M3 20 Case × 3 formal milestone 已完成 |
| L3 | `static_retrieval` | model-backed | 程序固定 | 静态 Retrieval | 尚未实现；不阻塞 L4 |
| L4 | `self_built_react` | model-backed | 模型 adaptive next-action/stop | read/search/list Tool loop | ADR 0128 + implementation guide 已 Human-freeze，Issue #52 实现待开始 |
| L5+ | incremental Agent capabilities | model-backed | 逐步增强 | retrieval/context/planning 等 | 后续增量 |

Oracle Evidence 是与 ladder 正交的 diagnostic intervention，不是 rung。MiniMax-M3 Oracle 20 Case × 3 formal milestone 已完成；Oracle-vs-L4 pairing / realization-gap machinery 继续等真实 L4 formal artifact 后再做。

L0–L5+ 是 capability-attribution structure，不是 mandatory delivery order。

## 2. 当前实验基础

截至 2026-08-18：

- `triage-suite-v1` 已冻结：20 个 Schema V2 Formal Cases，五类 Failure Type 各 4 个；
- Canonicalization Profile v1 已冻结；
- L1 MiniMax-M3 formal milestone：60 scored Samples，0 execution failures；
- L2 MiniMax-M3 formal milestone：60 scored Samples / 120 model calls，0 execution failures；
- Oracle MiniMax-M3 formal milestone：60 scored Samples，0 execution failures；
- L4 的 Runtime contract 已由 ADR 0128 Human-freeze，但尚未实现/运行 formal milestone。

因此旧文档中“Formal Suite 尚未冻结”“Canonicalization Profile 待 calibration”“Oracle 尚未实现”“正式 ReAct design 未来再决定”等表述，只能按其历史时间点理解。

## 3. 各层现行语义

### L0 — deterministic pipeline

- 无模型、无 Agent；
- 程序控制访问、诊断与报告；
- 已发布 runtime identity 保持 `pipeline_baseline`；
- `deterministic_pipeline` 只是 capability 名，不做历史 rename。

### L1 — full-context one-shot

- 完整 Agent-visible Evidence Universe 一次性进入固定 Task Contract；
- exactly one model call；
- 无工具、Retrieval、自主 loop；
- 是 diagnostic/comparison condition，不是 Product Runtime。

L1 不允许 silent truncation。当前正式 MiniMax 路径执行 exact input-token preflight；若完整请求加 reserved completion 无法放入 context，则零 provider call 并记录 execution/context-feasibility failure，不截断、拆分、summary 或 repair。

### L2 — fixed model workflow

L2 是程序控制的 fixed multi-stage model orchestration，不是 Agent。当前正式 MiniMax-M3 条件使用固定：

```text
evidence_analysis
    -> explicit handoff
    -> report_synthesis
    -> stop
```

模型不决定下一 stage，也没有自主 Tool loop。L1→L2 仍应解释成 controlled combined treatment difference，不能简单声称是“纯 orchestration causal uplift”。

### L3 — static retrieval

L3 仍是可选的 evidence-acquisition diagnostic：程序控制 versioned retrieval，再进入固定 model path。它不要求先于 L4 实现，也不把 Canonical Evidence Units 强制当 Retrieval chunks。

### L4 — self-built ReAct

L4 是第一个 Agentic Product Runtime，也是长期 Agent Runtime kernel lineage 的起点。详细现行语义由 [ADR 0128](../adr/0128-l4-self-built-react-runtime-contract.md) 与 [L4 implementation guide](l4-self-built-react-runtime-design.md) 定义。

核心边界：

```text
Model Decision
    -> Runtime validates action/policy/budget
    -> optional read-only tool execution
    -> ToolResult observation
    -> typed conversation update
    -> next Model Decision or terminal report
```

L4 V1 的 native Tool surface 只有：

```text
read
grep
find
ls
```

`submit_report` 不是 native tool。0 ToolCalls 表示模型尝试终止，Runtime 把 visible assistant text 当 Structured Triage Report candidate。

Baseline Tool Policy 为 `single + sequential`。Agent hard budget 只有 `max_steps=100`；另外继续受 provider request timeout、context/output limits 和每个 ToolResult hard bounds 约束。V1 不新增 cumulative-token hard budget、sample wall-clock hard budget或自动 compaction。

L4 first input 可以提供**完整 answer-neutral Canonical coordinate vocabulary**用于最终 citation，但不提供 Canonical content、Required Evidence 标签、Expected Answer 或 evaluator artifacts。Physical facts 仍必须通过工具调查。这是 ADR 0128 对更早“不要把 Canonical list 当 episode-start menu”的一般原则的明确 L4 refinement。

### L5+

Context compaction、retrieval、planning、verifier、skills、experience、memory 等只有在真实 L4 trajectory/badcase 证明需要时再作为独立增量进入，不预建。

## 4. Product Runtime 与 diagnostic condition

V1 Product Runtime 仍只有：

1. Fixed Pipeline；
2. self-built ReAct。

L1、L2、L3 是 diagnostic/comparison conditions。Oracle 是 orthogonal diagnostic intervention。

## 5. 受控比较与解释边界

优先固定 Case、Suite、Ground Truth、Scorer、base model、Task Contract 与 inference settings，只改变目标 treatment；无法固定时必须按 combined difference 解释。

| 比较 | 主要问题 |
| --- | --- |
| L0 vs L1 | 引入 model-backed full-context diagnosis 后发生什么？ |
| L1 vs L2 | fixed staged workflow package 带来什么？ |
| L2/L3 vs L4 | adaptive Agent investigation/control 带来什么？ |
| Normal vs Oracle | evidence acquisition 难度移除后，固定模型能做到什么？ |

L3 尚未实现不妨碍直接进行 L1/L2/Oracle/L4 的受控分析，只是 attribution claim 要与实际 treatment difference 一致。

## 6. Trace、Trajectory 与 Provider boundary

从 ADR 0128 起必须区分：

```text
Run Trace
= execution/lifecycle events, attempts, usage, latency, tool events, terminal/failure metadata

Agent Trajectory
= per-sample complete ordered UserMessage / AssistantMessage / ToolResultMessage history
```

L4 provider-returned thinking/reasoning可以保存在 trajectory 供 badcase analysis，但不是 deterministic score input，也不要求复制进 Trace。

L4 provider contract 使用 typed provider-neutral messages；MiniMax-specific Chat Completions serialization、tool calls 与 reasoning continuation 由 MiniMaxProvider adapter 负责。`count_input_tokens()` 与 `complete()` 必须共用同一 model-visible serialization path，避免 preflight 与真实请求发生 token-accounting drift。

## 7. Pi reference boundary

当前 reference upstream 是 `earendil-works/pi`。Pi 已用于正式 L4 设计调研，例如 typed messages、Agent loop、ToolResult recovery、read/search tool bounds、provider seam 与 session/event separation。

Pi 仍然只是 reference architecture：

- 不是 dependency；
- 不是 compatibility target；
- 不是 DevAgentOps semantics source；
- 不复制它的完整 product/session/framework surface。

ADR 0128 记录了采用与有意偏离的地方，例如 DevAgentOps 不对 malformed tool arguments 做 semantic repair，也不在 V1 引入 Pi-style session tree/compaction。

## 8. 当前未决但不阻塞 L4 实现的事项

- L3 的 retrieval design；
- dynamic context exhaustion 的 terminal classification；
- 是否在真实 trajectory 需要时加入 compaction；
- oversized single-line read slicing；
- batch sequential / batch parallel ablation；
- Oracle-vs-L4 pairing/gap implementation；
- 部分实现命名，例如 ProviderErrorKind、Trace event 名和 SQLite trajectory table 最终名字。

这些都不应被误读成 L4 core contract 尚未冻结。

## 9. 相关决策

- [ADR 0002: Build a Lightweight ReAct Runtime First](../adr/0002-self-built-react-runtime-first.md)
- [ADR 0112: V1 Runtime Scope](../adr/0112-v1-runtime-scope.md)
- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](../adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
- [L4 Self-built ReAct Runtime Design](l4-self-built-react-runtime-design.md)
