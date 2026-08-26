# DevAgentOps

DevAgentOps 是一个面向 **CI/Test Failure Triage** 的 Agent Runtime 与 Formal Evaluation 平台。

它把真实工程失败冻结为可重放的 Offline Case Environment，让不同 Runtime、Evidence Acquisition 与 Agent-control Treatment 在同一 Suite、同一 Ground Truth 和同一 Scorer 下运行，并记录完整执行证据，从而回答两个问题：

> 一个 Agent System 实际实现了多少模型诊断能力？
>
> 当它失败时，问题出在 evidence acquisition、citation/mapping、reasoning，还是 Runtime / provider infrastructure？

项目当前的核心闭环是：

```text
Frozen Case / Environment
    -> Runtime / Agent execution
    -> Trace + complete Agent trajectory
    -> deterministic validation / scoring
    -> Case-first aggregation / Oracle diagnostics
    -> badcase attribution
    -> controlled Runtime evolution
```

当前范围是**只读诊断**。L4 V1 不编辑代码、不执行测试、不重跑 CI，也不自动提交修复。

## Core architecture

### 1. Frozen Case Environment

Formal Case 使用 Offline Case Schema V2：

```text
<case-id>/
├── case.json
├── physical-artifacts/
│   ├── raw.log
│   ├── repository-manifest.json
│   └── repository/...
├── canonical-evidence/
│   ├── log-units.json
│   └── repository-units.json
└── evaluator/
    ├── required-evidence.json
    └── expected-answer.json
```

四层边界是刻意分开的：

- **Physical Artifacts**：唯一事实来源；
- **Canonical Evidence**：answer-neutral 的稳定 source-span coordinate，用于 citation 和 measurement；
- **Evidence Ground Truth**：隐藏的 `required-evidence.json`；
- **Diagnosis Ground Truth**：隐藏的 `expected-answer.json`。

Normal model-backed conditions 永远不能直接读取 evaluator-only artifacts。

### 2. Runtime / condition ladder

DevAgentOps 使用 capability ladder 做归因，而不是把所有能力塞进一个“Agent”黑盒：

| Level | Condition | Control | Evidence acquisition | Status |
| --- | --- | --- | --- | --- |
| L0 | deterministic pipeline | program-controlled | deterministic fixed access | implemented |
| L1 | `full_context_one_shot` | one model call | full visible universe upfront | formal milestone complete |
| L2 | `fixed_model_workflow` | fixed multi-stage program | fixed explicit input flow | formal milestone complete |
| L3 | `static_retrieval` | program-controlled | static retrieval | **implemented + live 20×3 formal milestone complete** |
| L4 | `self_built_react` | model adaptive next-action / stop | read/search/list tool loop | **implemented + formal milestones + Batch/Parallel replication complete** |
| L5+ | incremental Agent capabilities | evidence-driven evolution | context/retrieval/planning/etc. | future work |

Oracle Evidence 与 ladder 正交：它直接向固定模型提供 Human-reviewed Required Evidence source content，用来估计“去掉 ordinary evidence-discovery difficulty 后还能做到什么”。

详见 [Runtime Capability Ladder](docs/evaluation/runtime-capability-ladder.md)。

## L4 self-built ReAct Runtime

L4 是第一个 Agentic Product Runtime，也是当前 Agent Runtime kernel 的基线实现。

```text
Model Decision
    -> Runtime validates action / schema / policy / budget
    -> optional read-only Tool execution
    -> ToolResult observation
    -> authoritative typed conversation update
    -> next Model Decision or terminal report
```

V1 native tools：

```text
read
grep
find
ls
```

Agent-visible filesystem：

```text
/raw.log
/repository/...
```

关键 Runtime contract：

- provider-neutral `UserMessage / AssistantMessage / ToolResultMessage`；
- MiniMax native ToolCall + `reasoning_details` continuation round-trip；
- `Tool Registry` 冻结 provider-visible tool contract 与 deterministic behavior；
- historical baseline `Tool Policy = single + sequential + reject-all multi-call` 保留为不可改写的 reference；
- current recommended forward L4 treatment 使用 `batch + parallel + independent-call handling`：同一 Model Decision 的合法 sibling ToolCalls 并发执行，barrier 后按原 ToolCall 顺序返回 ToolResults；
- 普通 ToolCall 数不设置任意 cap；模型无需被 prompt 强制 batching；
- `max_steps = 100`，一个 Model Decision 无论含多少 ToolCalls 仍只消耗一个 step；
- provider transient failure 使用 **same-logical-request retry**，不是 whole-sample retry；
- Trace 与完整 Agent trajectory 分离持久化；
- 每个 ToolResult 有 hard bound，避免模型一次读取无限 workspace；
- 0 ToolCalls 表示尝试提交 Structured Triage Report；`submit_report` 不是 native tool。

L4 context accounting 由 [ADR 0129](docs/adr/0129-l4-provider-reported-context-accounting.md) 定义：Runtime **不做 mandatory local exact-token preflight**，成功请求以 provider-reported usage 作为 observed accounting。L1/L2/Oracle 原有 exact-token path 不受影响；后续实现的 L3 明确复用 L1-style exact-token preflight。

完整设计见：

- [ADR 0128 — L4 Self-built ReAct Runtime Contract](docs/adr/0128-l4-self-built-react-runtime-contract.md) — historical frozen L4 V1 baseline contract；
- [ADR 0129 — L4 Provider-Reported Context Accounting](docs/adr/0129-l4-provider-reported-context-accounting.md)；
- [L4 Self-built ReAct Runtime Design](docs/evaluation/l4-self-built-react-runtime-design.md) — historical V1 implementation guide；
- [L4 Batch + Parallel ToolCalls Milestone](docs/evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) — current Tool Policy experiment decision and replication evidence。

## Formal evaluation

Formal Evaluation 统一复用：

```text
Matrix v2
    -> doctor-first validation
    -> frozen Component / Suite / Case identity
    -> repeated Sample scheduler
    -> Runtime execution
    -> Trace + trajectory persistence
    -> Structured Triage Report validation
    -> deterministic scorer
    -> Sample -> Case -> Failure Type / Suite aggregation
    -> JSON / Markdown artifacts
```

Behavior-affecting Treatment components通过 Component Registry version + fingerprint 固定；完整 run identity 还包含 Execution Policy、Suite fingerprint、code revision 与 git state。

### Historical MiniMax-M3 baseline generation

同一 `triage-suite-v1` 包含 20 个 Human-reviewed Formal Cases，每个 Case 重复 3 次。下表是保留的**历史 pre-canonicalization baseline generation**；这些 run 不会被后续 output normalization retroactively 改写。

| Condition | Execution Coverage | Failure Type Exact Match | Evidence Hit Rate | Required Fields Completeness | Protocol Validity |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 Full-context One-shot | 100.00% | 76.67% | 51.38% | 96.67% | 96.67% |
| L2 Fixed Model Workflow | 100.00% | 85.00% | 55.57% | 99.58% | 90.00% |
| **L4 self-built ReAct** | **98.33%** | **88.33%** | **65.51%** | **96.67%** | **81.36%** |
| Oracle Evidence | 100.00% | 85.00% | 89.29% | 100.00% | 100.00% |

L4 historical formal milestone：

- Run ID: `dd8ca829-5051-43b6-a0c2-b3c2889acae0`
- `20 Cases × 3 repeats = 60 Samples`
- `59 scored / 1 execution_failed`
- 唯一 execution failure 是 provider HTTP 529 在 initial + 3 same-request retries 后耗尽；
- `802` successful Model Decisions；
- `733` executed tool calls started；
- `283` truncated ToolResults；
- 最大 provider-reported input context：`98,893` tokens。

历史 L4 V1 中最明显的 realization defect 是：模型已经得到或定位到一个物理 line range 后，仍可能自行拼接不存在的 Canonical Evidence ID。Oracle↔L4 Pair Analysis 因此推动了共享 deterministic Evidence Reference Canonicalization，而不是 L4-only coordinate hint。

### Shared Evidence Reference Canonicalization result

`canonical-line-range-normalization-v1` 已作为 L1/L2/L3/Oracle/L4 共享 final-report/output infrastructure 实现；L1/L2/Oracle/L4 完成了专门的 canonicalization replay/fresh 实验，后续 L3 formal milestone 使用同一 output contract。

历史 raw candidate 的 zero-model-cost offline replay 提供因果隔离结果：

| Condition | Protocol before → after | Evidence Hit before → after | Canonicalization effect |
| --- | ---: | ---: | --- |
| L1 | 96.67% → 96.67% | 51.38% → 51.38% | 0 changed Samples |
| L2 | 90.00% → **95.00%** | 55.57% → **59.46%** | 3 invalid Samples recovered |
| Oracle | 100.00% → 100.00% | 89.29% → 89.29% | 0 changed Samples |
| L4 | 81.36% → **96.61%** | 65.51% → **75.88%** | 9 invalid Samples recovered; unknown IDs 12 → 0 |

L1/L2/Oracle/L4 fresh `20×3` canonicalized generation 与后续 L3 `20×3` formal generation 均已完成：

| Condition | Execution Coverage | Failure Type Exact Match | Evidence Hit Rate | Required Fields Completeness | Protocol Validity |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 canonicalized | 98.33% | 80.00% | 52.16% | 99.79% | 96.61% |
| L2 canonicalized | 96.67% | 83.33% | 54.15% | 98.33% | **98.28%** |
| **L3 static retrieval** | **100.00%** | **88.33%** | 50.67% | **99.79%** | **98.33%** |
| Oracle canonicalized | 100.00% | 83.33% | 85.40% | 96.67% | 96.67% |
| **L4 canonicalized** | **100.00%** | **81.67%** | **71.83%** | **99.58%** | **93.33%** |

Fresh generation 不能作为 canonicalizer 的单变量 causal estimate：Oracle 在 `canonicalization_changed_samples = 0` 的情况下仍发生 metric drift，说明重新调用 hosted model/provider 本身存在 regeneration variance。因果结论以固定历史 raw candidate 的 offline replay 为准；fresh generation 用于 operational confirmation。

Resolver 只处理可从 frozen source identity + physical line range 确定映射的引用。Source identity typo、缺失字段或其他报告错误仍由正常 validator 判 invalid；不做 fuzzy matching 或语义修复。

完整实验报告与 machine-readable result snapshot：

- [Shared Evidence Reference Canonicalization Milestone](docs/evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md)
- [Canonicalization Result Snapshot](docs/evaluation/milestones/evidence-reference-canonicalization-results-2026-08-19.json)

### L3 Static Retrieval result

L3 V1 已完成 clean live full-Suite qualification：

```text
20 Cases × 3 repeats = 60 Samples
60 scored / 0 execution failures
taxonomy             88.33%
report evidence      50.67%
required fields      99.79%
protocol             98.33%
wall time            ~5m28s
```

Trace 与 hidden Required Evidence 的 zero-model-cost evaluator-side intersection 进一步把 Evidence loss 拆开：

```text
retrieval acquisition recall       76.56%  (Case-first)
final Report Evidence Hit          50.67%
utilization of acquired evidence   66.18%
```

20/20 Cases 的三次重复具有相同 `runtime_input_sha256`，证明静态 retrieval 输入可复现。结果同时表明 acquisition miss 和 acquired-but-not-cited loss 都存在：L3 是有效、可归因的 deterministic retrieval baseline，但没有展示相对 L1/L2 的 Report Evidence Hit 提升。不得使用 frozen Formal Suite hidden Ground Truth 静默调参；未来若优化 retrieval，应先建立独立 calibration/dev set，再冻结新 Treatment。

完整结果见 [L3 Static Retrieval V1 Formal Milestone](docs/evaluation/milestones/l3-static-retrieval-2026-08-24.md) 与 [machine-readable snapshot](docs/evaluation/milestones/l3-static-retrieval-results-2026-08-24.json)。

### L4 Batch + Parallel ToolCalls result

Batch + Parallel 已完成实现、首轮 formal run 和一组 fresh back-to-back replication。最稳定的信号是 Runtime efficiency，而不是单轮 hosted quality 百分比：

```text
initial comparison
Model Decisions 798 -> 547   (-31.45%)

fresh replication
Model Decisions 877 -> 571   (-34.89%)
executed ToolCalls 809 -> 775 (-4.20%)
wall time 978.27s -> 806.69s (-17.54%)
```

Replication quality：

| Metric | Single / Sequential | Batch + Parallel |
| --- | ---: | ---: |
| Failure Type Exact | 71.67% | **75.00%** |
| Evidence Hit | **74.64%** | 73.50% |
| Required Fields | 93.33% | **98.13%** |
| Protocol Validity | **93.33%** | 91.67% |

首轮 Batch 的明显 taxonomy / required-fields 下降没有复现，方向在 replication 中反转；paired Case-level uncertainty 也没有显示 material quality regression。相反，Model Decision reduction 在两轮 fresh Batch run 中稳定复现。因此 Batch + Parallel 现在是**新 L4 evaluation / Runtime evolution 的推荐 Tool Policy**，而 historical single/sequential 仍保留为不可改写的 reference Treatment。

完整结果见 [L4 Batch + Parallel ToolCalls Milestone](docs/evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) 与 [machine-readable snapshot](docs/evaluation/milestones/l4-batch-parallel-toolcalls-results-2026-08-19.json)。

Oracle 不是“更高一级 Runtime”，也不应该被解释成 L4 必须整体超过的 benchmark rung。它是 evidence-conditioned diagnostic intervention。

完整历史结果见 [L4 MiniMax-M3 Full-Suite Milestone](docs/evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md)。Pair Analysis 见 [Oracle ↔ L4 Pair Analysis Findings](docs/evaluation/milestones/oracle-l4-pair-analysis-2026-08-19.md)。

## Public Evaluation Explorer data layer

Phase 1 的 public Explorer foundation 已加入只读 FastAPI 数据层。它通过
`showcase-data/catalog.json` 统一索引 12 个正式 Run，并直接查询 9 个经确定性
净化的 frozen SQLite snapshot；实验专属诊断继续读取现有 machine-readable
milestone JSON，不复制成 Dashboard 指标表。

公开 API 位于 `/api`，覆盖 Overview、Conditions、Experiment Evolution、Run、
Case/Sample、Trajectory、Trace 与 Comparison。Trajectory 和 Trace 使用显式公开
字段边界，不返回 provider thinking/reasoning、opaque continuation state 或 raw
manifest/message JSON。所有 Explorer 路由均为 GET-only；现有 health/version/storage
接口保持不变。

数据生成、验证和 authority 说明见 [showcase-data/README](showcase-data/README.md)
与 [ADR 0131](docs/adr/0131-public-evaluation-explorer-data-boundary.md)。最终 React/Vite
展示界面属于 Phase 2，未在本阶段实现。

## Repository layout

```text
src/devagentops/
├── runtime/        # typed messages, ReAct loop, Tool Policy, read/grep/find/ls
├── conditions/     # L1 / L2 / L3 / L4 / Oracle execution conditions
├── providers/      # provider-neutral request contract + MiniMax adapter
├── evaluation/     # Matrix, scheduler, Trace, scoring, aggregation, artifacts
└── storage/        # SQLite / migrations / trajectory persistence

components/         # frozen behavior components + registry
evaluation/         # suites, cases, matrices, formal evaluation inputs
docs/adr/           # active architecture decisions + archived decision history
docs/evaluation/    # methodology, Runtime design, milestone reports
frontend/           # read/review UI
```

## Quick start

Python 3.11+：

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest -q -p no:cacheprovider
```

Initialize local persistence：

```bash
.venv/bin/devagentops db init --database .devagentops/devagentops.db
.venv/bin/devagentops status --database .devagentops/devagentops.db
```

Validate the recommended current L4 Tool Policy configuration without running the model：

```bash
.venv/bin/devagentops eval doctor \
  --matrix evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json \
  --registry components/registry.json \
  --suite evaluation/suites/triage-v1/suite.json
```

The historical/fresh single-sequential reference matrix remains `evaluation/matrices/l4-minimax-m3-canonicalized-v2.json` for controlled comparison; it is not rewritten.

FastAPI：

```bash
.venv/bin/python -m uvicorn devagentops.api:app --host 127.0.0.1 --port 8000
```

Frontend：

```bash
cd frontend
npm ci
npm run dev
```

Live/formal MiniMax execution additionally requires the provider credential expected by the current Matrix/provider path.

## Documentation map

Current architecture / methodology should be read in roughly this order：

1. [CONTEXT.md](CONTEXT.md) — compact current project context and terminology;
2. [Active ADR Index](docs/adr/README.md) — architecture decision source of truth;
3. [Formal Evaluation Methodology](docs/evaluation/formal-evaluation-methodology.md) — Case/evidence/trust model;
4. [Evaluation Matrix & Component Registry](docs/evaluation/evaluation-matrix-and-component-registry.md) — experiment identity;
5. [Runtime Capability Ladder](docs/evaluation/runtime-capability-ladder.md) — controlled capability comparisons;
6. [L4 Runtime Design](docs/evaluation/l4-self-built-react-runtime-design.md) — frozen historical L4 V1 self-built Agent Runtime contract;
7. [L3 Static Retrieval V1 Formal Milestone](docs/evaluation/milestones/l3-static-retrieval-2026-08-24.md) — deterministic retrieval baseline, live 20×3 result, and acquisition-vs-report diagnostic;
8. [L4 Batch + Parallel ToolCalls Milestone](docs/evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) — current recommended Tool Policy evidence and replication;
9. [Oracle Evidence Diagnostic Condition](docs/evaluation/oracle-evidence-diagnostic-condition.md) — evidence-conditioned diagnostic boundary;
10. [Shared Evidence Reference Canonicalization Milestone](docs/evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md) — completed replay + fresh four-condition comparison and interpretation;
11. [Oracle ↔ L4 Pair Analysis Findings](docs/evaluation/milestones/oracle-l4-pair-analysis-2026-08-19.md) — historical badcase analysis that motivated canonicalization;
12. [Milestone Status Index](docs/evaluation/milestones/README.md) — classifies dated milestone documents and points to the current completed experiment.

`docs/adr/archive/`、dated milestone docs、Case review packets 和 merged PR discussions 是历史记录；它们不覆盖当前 current-facing docs。历史 L4 V1 ADR/Design 继续作为 frozen baseline contract 阅读，不应被 retroactively 改写成 Batch + Parallel。

## Current roadmap

Shared deterministic Evidence Reference Canonicalization、L4 Batch + Parallel ToolCalls 与 L3 Static Retrieval formal qualification 均已完成。当前结论是：

```text
shared Evidence Reference Canonicalization
    -> accepted shared output infrastructure

historical L4 Tool Policy
single + sequential + reject-all
    -> preserved immutable reference

recommended forward L4 Tool Policy
batch + parallel + independent-call handling
    -> two fresh runs reproduce ~31-35% Model Decision reduction
    -> fresh replication reduces wall time 17.5%
    -> no reproducible material quality regression demonstrated

L3 static retrieval baseline
    -> deterministic 20/20 Case runtime inputs across repeats
    -> acquisition recall 76.56%
    -> final Report Evidence Hit 50.67%
    -> acquisition and evidence-selection loss both observed
```

当前 canonicalizer 只根据 frozen Canonical coordinates 做确定性映射：exact legal ID 原样保留；source identity 一致且 line range 可解析时，替换为实际覆盖到的 Canonical Evidence IDs 并稳定去重；无法确定映射的引用继续由 validator 判 invalid。它不读取 Required Evidence / Expected Answer，不做 fuzzy source correction，也不替模型进行语义 Evidence selection。

实验同时暴露了一个独立 metric limitation：一个极宽的合法 physical line range 可以展开为大量 Canonical IDs，而当前 recall-oriented Evidence Hit 不惩罚 broad over-citation。如果后续 evidence 表明该问题重要，应单独研究 Evidence Precision / Citation Specificity，而不是往 resolver 中加入任意宽度阈值。

Batch + Parallel 不需要继续扩 batch cap、forced-batching prompt、scheduler heuristic 或 output repair。下一项大的 Product Runtime 能力方向转向 **executable repair / sandboxed remediation**：`investigate -> diagnose -> mutate/edit -> execute/test -> observe -> retry -> verify -> report`。这属于 V1 read-only triage 之后的独立阶段，不应静默改写现有 L4 historical contracts。

L3 V1 的 live full-suite qualification 已完成。当前结果不支持在 frozen Formal Suite 上继续调参，也不支持立即引入 embedding、reranker、query LLM 或 vector database；未来 retrieval optimization 必须使用独立 calibration/dev set 并冻结新 Treatment。Context management、planner/verifier、skills/MCP、memory/multi-agent 等仍保持 evidence-gated。当前没有证据要求把这些能力与 repair/sandbox 或 Batch + Parallel 混在同一轮实现里。
