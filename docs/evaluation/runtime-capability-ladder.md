# Runtime Capability Ladder 与 Model-backed Diagnostic Conditions

> Current-state note (2026-08-23): L1、L2、Oracle 与 L4 MiniMax-M3 historical formal milestones 均已完成。L3 `static_retrieval` V1 已按 ADR 0130 实现，并通过 deterministic tests、Component/Matrix doctor 与 tiny fake-provider formal-path qualification；尚未运行真实 20-Case × 3 repeats L3 model evaluation。Oracle↔L4 Pair Analysis、shared deterministic Evidence Reference Canonicalization、fresh four-condition generation，以及 L4 Batch + Parallel Tool Policy 初始实验与 replication 均已完成。Batch + Parallel 现在是新 L4 evaluation / Runtime evolution 的推荐 Tool Policy；historical single/sequential 仍是 immutable reference，不 retroactively 改写。

DevAgentOps 使用 capability ladder 做**能力归因**：它回答“一个 condition 增加了什么能力、应与谁比较、结果能说明什么”，而不是规定所有能力必须按编号实现。

## 1. Ladder 总览

| Level | Capability condition | Model | 控制流 | Evidence acquisition | 当前状态 |
| --- | --- | --- | --- | --- | --- |
| L0 | deterministic pipeline | 无 | 程序固定 | deterministic fixed access | Product Runtime baseline 已实现；历史 runtime identity 保持 `pipeline_baseline` |
| L1 | `full_context_one_shot` | 单次调用 | 固定 Prompt，无循环 | 完整 Agent-visible Universe upfront | historical milestone + canonicalized fresh generation complete |
| L2 | `fixed_model_workflow` | 多阶段调用 | 程序固定 stages | 固定显式 input flow | historical milestone + canonicalized fresh generation complete |
| L3 | `static_retrieval` | model-backed | 程序固定 | 静态 Retrieval | V1 已实现并完成 deterministic/tiny fake qualification；尚无 live full-suite result |
| L4 | `self_built_react` | model-backed | 模型 adaptive next-action / stop | `read/grep/find/ls` Tool loop | historical/fresh milestones complete；Batch + Parallel replication complete；recommended forward Tool Policy accepted |
| L5+ | incremental Agent capabilities | model-backed | 逐步增强 | evidence-driven context/retrieval/planning/etc. | future controlled evolution |

Oracle Evidence 与 ladder 正交，不是 rung。它的 historical 与 canonicalized fresh MiniMax-M3 20×3 results 均已完成，用于估计 ordinary evidence-discovery difficulty 被移除后的 diagnosis capacity。

L0–L5+ 是 capability-attribution structure，不是 mandatory delivery order。

## 2. 当前实验基础

截至 2026-08-23：

- `triage-suite-v1` 已冻结：20 个 Schema V2 Formal Cases，五类 Failure Type 各 4 个；
- Canonicalization Profile v1 已冻结；
- historical L1 MiniMax-M3 formal milestone：60 scored，0 execution failures；
- historical L2 MiniMax-M3 formal milestone：60 scored / 120 model calls，0 execution failures；
- historical Oracle MiniMax-M3 formal milestone：60 scored，0 execution failures；
- historical L4 MiniMax-M3 formal milestone：60 planned，59 scored / 1 provider execution failure；
- Oracle↔L4 Pair Analyzer 已落地并完成真实 20-Case pair analysis；
- `canonical-line-range-normalization-v1` 已完成 historical offline replay + fresh L1/L2/Oracle/L4 20×3 generation；
- L4 Batch + Parallel ToolCalls 已完成实现、deterministic gates、initial 20×3 run 和 back-to-back replication。

Historical L4 Suite-level metrics：

| Metric | L4 |
| --- | ---: |
| Execution Coverage | `98.33%` |
| Failure Type Exact Match | `88.33%` |
| Evidence Hit Rate | `65.51%` |
| Required Fields Completeness | `96.67%` |
| Protocol Validity | `81.36%` |

Fresh canonicalized L4 generation：

| Metric | L4 canonicalized |
| --- | ---: |
| Execution Coverage | `100.00%` |
| Failure Type Exact Match | `81.67%` |
| Evidence Hit Rate | `71.83%` |
| Required Fields Completeness | `99.58%` |
| Protocol Validity | `93.33%` |

Batch + Parallel fresh replication, single/sequential -> Batch：

```text
Model Decisions       877 -> 571   (-34.89%)
Executed ToolCalls     809 -> 775   (-4.20%)
Wall time            978.27s -> 806.69s (-17.54%)
Taxonomy              71.67% -> 75.00%
Evidence              74.64% -> 73.50%
Required Fields       93.33% -> 98.13%
Protocol              93.33% -> 91.67%
```

The initial Batch quality drop did not reproduce, while Model Decision reduction reproduced in both fresh Batch runs (`798 -> 547`, then `877 -> 571`). Current evidence therefore supports Batch + Parallel as an efficiency improvement without demonstrated material diagnosis-quality regression.

完整历史结果见 [L4 MiniMax-M3 Full-Suite Milestone](milestones/l4-minimax-m3-full-suite-2026-08-19.md)。Batch 结果见 [L4 Batch + Parallel ToolCalls Milestone](milestones/l4-batch-parallel-toolcalls-2026-08-19.md)。Dated milestone 的状态先看 [Milestone Status Index](milestones/README.md)。

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

Recommended forward Tool Policy：

```text
call_mode = batch
execution_mode = parallel
multiple_calls = accept_independently
```

Batch + Parallel 仍然是 `runtime_variant=self_built_react` 的同一 L4 lineage，不是新的 capability rung。合法 sibling calls 并发执行，barrier 后按 model-authored ToolCall order materialize ToolResults；expected/malformed errors 按 call 隔离；unexpected Runtime/tool defects 仍是 Sample-level infrastructure failure。普通 ToolCall 数没有 arbitrary cap，一个 N-call Model Decision 仍只消耗一个 `max_steps` unit。

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
- source identity 一致且显式 line range 可解析 -> deterministic overlap mapping to frozen Canonical units；
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
| L4 single/sequential vs Batch/Parallel | same-L4 Tool Policy 对 Model Decisions、tool execution、latency、tokens 与 quality 有什么影响？ |
| Normal vs Oracle | evidence acquisition 难度被移除后，固定模型能做到什么？ |
| Oracle vs L4 | Agent System 实际实现了多少 evidence-conditioned diagnosis capacity？ |

Oracle-vs-L4 不能仅凭两个 Suite aggregate 做 causal claim。当前 Pair Analyzer 已将比较单位固定为 Case aggregate，并保留各 condition 的独立 repeats、Execution Coverage 与 metric-vector gaps；A/B/C 仅用于 Human/AI review，不是自动标签体系。

新一代 L1/L2/Oracle/L4 formal comparison 必须全部拥有相同的 shared Evidence Reference Canonicalization capability，避免把 output-realization 差异误当 Runtime/evidence-acquisition 差异。

Batch + Parallel replication 同样不能把单轮 hosted quality delta 当严格 causal effect。当前结论依赖两轮 fresh efficiency signal 的重复出现和质量退化未复现，而不是一个 Suite aggregate 的方向。

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

Pair Analysis、shared canonicalization 与 Batch + Parallel Tool Policy 实验均已完成，不再把它们列为未来工作。

### 8.1 已完成的 evidence-driven sequence

```text
Oracle↔L4 Pair Analysis
    -> shared Evidence Reference Canonicalization
    -> historical offline replay
    -> fresh L1/L2/Oracle/L4 20×3 generation
    -> L4 Batch + Parallel Tool Policy
    -> fresh single/sequential vs Batch replication
```

Batch experiment 的核心结论：Model Decision reduction 在两轮 fresh Batch run 中稳定复现（约 `31–35%`）；clean replication 同时降低 wall time `17.54%`，而 executed ToolCalls 只减少 `4.20%`；初始明显 quality drop 没有复现。因此当前推荐 new L4 evaluations 使用 Batch + Parallel Treatment，historical single/sequential 继续作为 reference。

### 8.2 当前大的 Runtime direction

下一项大的 Product Runtime 能力方向是 executable repair / sandboxed remediation：

```text
investigate
    -> diagnose
    -> mutate/edit
    -> execute/test
    -> observe
    -> retry
    -> verify
    -> report
```

它应复用 self-built ReAct kernel，但作为 read-only V1 之后的显式新阶段，不 silent mutate 已冻结的 L4 historical Treatment。

### 8.3 仍然 evidence-gated

- L3 live full-suite qualification、retrieval optimization 或新 quality metric；
- dynamic context-exhaustion handling；
- compaction / predictive context budgeting；
- oversized single-line read slicing；
- planner/verifier/reflection，除非 repair-loop evidence 要求；
- skills/MCP/memory/multi-agent。

## 9. 相关决策与结果

- [ADR 0002: Build a Lightweight ReAct Runtime First](../adr/0002-self-built-react-runtime-first.md)
- [ADR 0112: V1 Runtime Scope](../adr/0112-v1-runtime-scope.md)
- [ADR 0124: Oracle Evidence Diagnostic Condition](../adr/0124-oracle-evidence-diagnostic-condition.md)
- [ADR 0125: Formal Evaluation Evidence Universe and Access](../adr/0125-formal-evaluation-evidence-universe-and-access.md)
- [ADR 0127: Staged Runtime Capability Ladder and Reference Boundary](../adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md)
- [ADR 0128: L4 Self-built ReAct Runtime Contract](../adr/0128-l4-self-built-react-runtime-contract.md) — historical frozen L4 V1 baseline
- [ADR 0129: L4 Provider-Reported Context Accounting](../adr/0129-l4-provider-reported-context-accounting.md)
- [Formal Evaluation Methodology](formal-evaluation-methodology.md)
- [L4 Self-built ReAct Runtime Design](l4-self-built-react-runtime-design.md)
- [L4 Batch + Parallel ToolCalls Milestone](milestones/l4-batch-parallel-toolcalls-2026-08-19.md)
- [Shared Evidence Reference Canonicalization Milestone](milestones/evidence-reference-canonicalization-2026-08-19.md)
- [Oracle ↔ L4 Pair Analysis Findings](milestones/oracle-l4-pair-analysis-2026-08-19.md)
- [Milestone Status Index](milestones/README.md)
