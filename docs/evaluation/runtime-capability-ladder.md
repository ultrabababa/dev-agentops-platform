# Runtime Capability Ladder 与 Model-backed Diagnostic Conditions

> Current-state note (2026-08-19): L1、L2、Oracle 与 L4 MiniMax-M3 historical formal milestones 均已完成。Oracle↔L4 Pair Analysis 也已完成。当前优先工作是 shared deterministic Evidence Reference Canonicalization，并在统一 output-resolution capability 下重新生成 L1/L2/Oracle/L4 20×3 对比；随后单独评估 L4 batch+parallel Tool Policy 的效率收益。

DevAgentOps 使用 capability ladder 做**能力归因**：它回答“一个 condition 增加了什么能力、应与谁比较、结果能说明什么”，而不是规定所有能力必须按编号实现。

## 1. Ladder 总览

| Level | Capability condition | Model | 控制流 | Evidence acquisition | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| L0 | deterministic pipeline | 无 | 程序固定 | deterministic fixed access | Product Runtime baseline 已实现；历史 runtime identity 保持 `pipeline_baseline` |
| L1 | `full_context_one_shot` | 单次调用 | 固定 Prompt，无循环 | 完整 Agent-visible Universe upfront | historical 20×3 formal milestone complete；待 shared canonicalization 后生成新 comparison result |
| L2 | `fixed_model_workflow` | 多阶段调用 | 程序固定 stages | 固定显式 input flow | historical 20×3 formal milestone complete；待 shared canonicalization 后生成新 comparison result |
| L3 | `static_retrieval` | model-backed | 程序固定 | 静态 Retrieval | 尚未实现；optional diagnostic，不阻塞 L4/L5+ |
| L4 | `self_built_react` | model-backed | 模型 adaptive next-action / stop | `read/grep/find/ls` Tool loop | historical live + 20×3 formal milestone complete；shared canonicalization 后重跑 |
| L5+ | incremental Agent capabilities | model-backed | 逐步增强 | evidence-driven context/retrieval/planning/etc. | future controlled evolution |

Oracle Evidence 与 ladder 正交，不是 rung。它的 historical MiniMax-M3 20×3 milestone 已完成，用于估计 ordinary evidence-discovery difficulty 被移除后的 diagnosis capacity；它也会在 shared canonicalization 下重新跑，以保持新一代 comparison 的 output-realization contract 一致。

L0–L5+ 是 capability-attribution structure，不是 mandatory delivery order。

## 2. 当前实验基础

截至 2026-08-19：

- `triage-suite-v1` 已冻结：20 个 Schema V2 Formal Cases，五类 Failure Type 各 4 个；
- Canonicalization Profile v1 已冻结；
- historical L1 MiniMax-M3 formal milestone：60 scored，0 execution failures；
- historical L2 MiniMax-M3 formal milestone：60 scored / 120 model calls，0 execution failures；
- historical Oracle MiniMax-M3 formal milestone：60 scored，0 execution failures；
- historical L4 MiniMax-M3 formal milestone：60 planned，59 scored / 1 provider execution failure；
- Oracle↔L4 Pair Analyzer 已落地并完成真实 20-Case pair analysis。

Historical L4 Suite-level metrics：

| Metric | L4 |
| --- | ---: |
| Execution Coverage | `98.33%` |
| Failure Type Exact Match | `88.33%` |
| Evidence Hit Rate | `65.51%` |
| Required Fields Completeness | `96.67%` |
| Protocol Validity | `81.36%` |

完整历史结果见 [L4 MiniMax-M3 Full-Suite Milestone](milestones/l4-minimax-m3-full-suite-2026-08-19.md)。Dated milestone 的状态先看 [Milestone Status Index](milestones/README.md)。

## 3. 各层现行语义

### L0 — deterministic pipeline

- 无模型、无 Agent；
- 程序控制访问、诊断与报告；
- 已发布 runtime identity 保持 `pipeline_baseline`；
- `deterministic_pipeline` 是 capability 名，不 retroactively rename 历史 identity。

### L1 — full-context one-shot

- 完整 Agent-visible Evidence Universe 一次性进入固定 Task Contract；
- exactly one model call；
- 无工具、Retrieval、自主 loop；
- 是 diagnostic/comparison condition，不是 Product Runtime。

L1 不允许 silent truncation。当前正式 MiniMax 路径继续执行 exact input-token preflight；若完整请求加 reserved completion 无法放入 context，则在 provider call 前形成 context-feasibility execution failure，不截断、拆分、summary 或 repair。

### L2 — fixed model workflow

L2 是程序控制的 fixed multi-stage model orchestration，不是 Agent：

```text
evidence_analysis
    -> explicit handoff
    -> report_synthesis
    -> stop
```

模型不决定下一 stage，也没有自主 Tool loop。L1→L2 应解释为 controlled combined treatment difference，而不是简单声称“纯 orchestration causal uplift”。

### L3 — static retrieval

L3 是可选的 evidence-acquisition diagnostic：程序控制 versioned retrieval，再进入固定 model path。

它仍有研究价值，可用于拆分 static evidence acquisition 与 adaptive investigation 的差异；但它不是 L4 或后续 Runtime evolution 的前置依赖，也不把 Canonical Evidence Units 强制当 Retrieval chunks。

### L4 — self-built ReAct

L4 是第一个 Agentic Product Runtime，也是长期 self-built Agent Runtime kernel lineage 的 baseline。

核心边界：

```text
Model Decision
    -> Runtime validates action / policy / schema / budget
    -> optional read-only Tool execution
    -> ToolResult observation
    -> typed conversation update
    -> next Model Decision or terminal report
```

L4 V1 native tools：

```text
read
grep
find
ls
```

`submit_report` 不是 native tool。0 ToolCalls 表示模型尝试终止，Runtime 将 visible assistant text 解析为 Structured Triage Report candidate。

Historical baseline Tool Policy：

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Agent hard budget：`max_steps=100`。V1 不增加 cumulative-token hard budget、sample wall-clock hard budget或 automatic compaction。

L4 first input 提供完整 answer-neutral Canonical coordinate vocabulary 用于 citation，但不提供 Physical Artifact content、Required Evidence 标签、Expected Answer 或 evaluator artifacts。Physical facts 必须通过 tools 调查。

### Shared final-report Evidence Reference Canonicalization

Pair Analysis 之后，Canonical reference normalization 不再被定义成 L4-only capability。它是新一代 L1/L2/Oracle/L4 共同拥有的 final-report/output-realization behavior：

```text
raw candidate document
    -> deterministic Evidence Reference Canonicalization
    -> report validation
    -> frozen scorer
```

Resolver 只允许：

- exact Canonical ID -> preserve；
- same-family explicit line range -> deterministic overlap mapping to frozen Canonical units；
- deduplicate resolved IDs；
- unresolvable -> keep invalid。

它不得使用 Required Evidence、Expected Answer、semantic/fuzzy matching，也不额外检查 Agent trajectory/read-history。这个变化不创造新的 Runtime rung，也不把 Oracle 变成更高层 Runtime。

### L4 context accounting — ADR 0129

L4 Runtime 不再做 mandatory local exact-token preflight：

```text
step-budget check
    -> build logical request
    -> provider-request execution
    -> successful AssistantMessage.usage
    -> provider-reported per-step accounting
```

Treatment context identity记录：

```text
assessment = provider_reported
method = provider_response_usage
policy = observe_provider_usage_no_local_preflight
```

L1/L2/Oracle 的 exact-token behavior 不受 ADR 0129 影响。

Historical formal L4 milestone 最大观察到 `98,893` provider-reported input tokens，没有出现 context-limit rejection，因此当前没有证据要求在 baseline 中加入 compaction 或 predictive local budgeting。

### L5+

L5+ 不是预定义功能包。Context management、retrieval、planning、verifier、skills、experience、memory、multi-agent 等只有在真实 L4 trajectory / badcase 证明需要时才作为独立、可归因的增量进入。

## 4. Product Runtime 与 diagnostic condition

V1 Product Runtime：

1. Fixed Pipeline；
2. self-built ReAct。

L1、L2、L3 是 diagnostic/comparison conditions。Oracle 是 orthogonal diagnostic intervention。

## 5. 受控比较与解释边界

优先固定 Case、Suite、Ground Truth、Scorer、base model、Task Contract 与相关 inference settings，只改变目标 Treatment。无法固定时必须按 combined difference 解释。

| 比较 | 主要问题 |
| --- | --- |
| L0 vs L1 | 引入 model-backed full-context diagnosis 后发生什么？ |
| L1 vs L2 | fixed staged workflow package 带来什么？ |
| L2/L3 vs L4 | adaptive Agent investigation/control 带来什么？ |
| Normal vs Oracle | evidence acquisition 难度被移除后，固定模型能做到什么？ |
| Oracle vs L4 | Agent System 实际实现了多少 evidence-conditioned diagnosis capacity？ |

Oracle-vs-L4 不能仅凭两个 Suite aggregate 做 causal claim。当前 Pair Analyzer 已将比较单位固定为 Case aggregate，并保留各 condition 的独立 repeats、Execution Coverage 与 metric-vector gaps；A/B/C 仅用于 Human/AI review，不是自动标签体系。

新一代 L1/L2/Oracle/L4 formal comparison 必须全部拥有相同的 shared Evidence Reference Canonicalization capability，避免把 output-realization 差异误当 Runtime/evidence-acquisition 差异。

## 6. Trace、Trajectory 与 Provider boundary

L4 必须区分：

```text
Run Trace
= execution/lifecycle events, attempts, usage, latency, tool events, terminal/failure metadata

Agent Trajectory
= per-sample complete ordered UserMessage / AssistantMessage / ToolResultMessage history
```

Provider-returned thinking/reasoning 可保存在 trajectory 供 badcase analysis，但不是 deterministic score input，也不要求复制进 Trace。

L4 provider contract 使用 typed provider-neutral messages；MiniMax-specific Chat Completions serialization、ToolCalls 与 reasoning continuation 由 `MiniMaxProvider` adapter 负责。

## 7. Pi reference boundary

`earendil-works/pi` 是 L4 设计阶段使用的 reference architecture。Pi：

- 不是 dependency；
- 不是 compatibility target；
- 不是 DevAgentOps semantics source；
- 不复制它的完整 product/session/framework surface。

DevAgentOps 借鉴 typed messages、Agent loop、ToolResult recovery、read/search bounds、provider seam 与 session/event separation等结构，但保留自己的 strict malformed-argument semantics、Trace/trajectory boundary、minimal tool surface 和 no-compaction baseline。

## 8. Post-L4 evidence-driven work

Pair Analysis 已完成，因此这里不再保留“先做 Pair Validator、再决定下一 ablation”的旧路线。

### 8.1 已确认的当前优先级

```text
shared Evidence Reference Canonicalization
    -> historical L1/L2/Oracle/L4 offline replay
    -> new L1/L2/Oracle/L4 20×3 formal comparison generation
    -> separate L4 batch + parallel Tool Policy efficiency experiment
```

第一个变化解决 deterministic citation/report realization failure；第二个 L4-only 变化解决已观察到的 action-execution friction 和高 repeated-context cost。Historical L4 run 已记录 `26` 个 `multiple_tool_calls_rejected` ToolCall IDs、`802` 个 successful Model Decisions、约 `24.72M` prompt tokens 和约 `35m01s` wall-clock，因此 batch+parallel 已有真实 evidence 支持，但必须和 canonicalization 分开实现/比较。

### 8.2 仍然 evidence-gated

- L3 retrieval design；
- dynamic context-exhaustion handling；
- compaction / predictive context budgeting；
- oversized single-line read slicing；
- planner/verifier/reflection；
- skills/MCP/memory/multi-agent。

## 9. 相关决策与结果

- [ADR 0002: Build a Lightweight ReAct Runtime First](../adr/0002-self-built-react-runtime-first.md)
- [ADR 0112: V1 Runtime Scope](../adr/0112-v1-runtime-scope.md)
- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](../adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129: L4 Provider-Reported Context Accounting](../adr/0129-l4-provider-reported-context-accounting.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
- [L4 Self-built ReAct Runtime Design](l4-self-built-react-runtime-design.md)
- [Oracle ↔ L4 Pair Analysis Findings](milestones/oracle-l4-pair-analysis-2026-08-19.md)
- [Milestone Status Index](milestones/README.md)
