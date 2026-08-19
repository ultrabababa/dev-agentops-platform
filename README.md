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
| L3 | `static_retrieval` | program-controlled | static retrieval | not implemented; optional diagnostic |
| L4 | `self_built_react` | model adaptive next-action / stop | read/search/list tool loop | **implemented + formal milestone complete** |
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
- baseline `Tool Policy = single + sequential`；
- multiple ToolCalls under `single` 时 execute none，并为每个 call ID 返回 error ToolResult；
- `max_steps = 100`；
- provider transient failure 使用 **same-logical-request retry**，不是 whole-sample retry；
- Trace 与完整 Agent trajectory 分离持久化；
- 每个 ToolResult 有 hard bound，避免模型一次读取无限 workspace；
- 0 ToolCalls 表示尝试提交 Structured Triage Report；`submit_report` 不是 native tool。

L4 context accounting 由 [ADR 0129](docs/adr/0129-l4-provider-reported-context-accounting.md) 定义：Runtime **不做 mandatory local exact-token preflight**，成功请求以 provider-reported usage 作为 observed accounting。L1/L2/Oracle 原有 exact-token path 不受影响。

完整设计见：

- [ADR 0128 — L4 Self-built ReAct Runtime Contract](docs/adr/0128-l4-self-built-react-runtime-contract.md)
- [ADR 0129 — L4 Provider-Reported Context Accounting](docs/adr/0129-l4-provider-reported-context-accounting.md)
- [L4 Self-built ReAct Runtime Design](docs/evaluation/l4-self-built-react-runtime-design.md)

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

同一 `triage-suite-v1` 包含 20 个 Human-reviewed Formal Cases，每个 Case 重复 3 次。下表是当前保留的**历史 baseline generation**，用于解释已经完成的 L1/L2/Oracle/L4 runs；它不会被后续 shared output normalization retroactively 改写。

| Condition | Execution Coverage | Failure Type Exact Match | Evidence Hit Rate | Required Fields Completeness | Protocol Validity |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 Full-context One-shot | 100.00% | 76.67% | 51.38% | 96.67% | 96.67% |
| L2 Fixed Model Workflow | 100.00% | 85.00% | 55.57% | 99.58% | 90.00% |
| **L4 self-built ReAct** | **98.33%** | **88.33%** | **65.51%** | **96.67%** | **81.36%** |
| Oracle Evidence | 100.00% | 85.00% | 89.29% | 100.00% | 100.00% |

L4 formal milestone：

- Run ID: `dd8ca829-5051-43b6-a0c2-b3c2889acae0`
- `20 Cases × 3 repeats = 60 Samples`
- `59 scored / 1 execution_failed`
- 唯一 execution failure 是 provider HTTP 529 在 initial + 3 same-request retries 后耗尽；
- `802` successful Model Decisions；
- `733` executed tool calls started；
- `283` truncated ToolResults；
- 最大 provider-reported input context：`98,893` tokens。

相对 L2，L4 提升了 taxonomy exact match 与 Evidence Hit Rate，但降低了 final protocol validity。历史 L4 V1 中最明显的 realization defect 是：模型已经得到或定位到一个物理 line range 后，仍可能自行拼接不存在的 Canonical Evidence ID。历史 run 没有做任何 post-generation repair；Pair Analysis 之后的当前决策则是把 deterministic Evidence Reference Canonicalization 提升为 **L1/L2/Oracle/L4 共享的 final-report/output infrastructure**，并在统一能力下重新生成公平的四条件比较结果。

Oracle 不是“更高一级 Runtime”，也不应该被解释成 L4 必须整体超过的 benchmark rung。它是 evidence-conditioned diagnostic intervention。

完整历史结果见 [L4 MiniMax-M3 Full-Suite Milestone](docs/evaluation/milestones/l4-minimax-m3-full-suite-2026-08-19.md)。当前分析与后续决策见 [Oracle ↔ L4 Pair Analysis Findings](docs/evaluation/milestones/oracle-l4-pair-analysis-2026-08-19.md)。

## Repository layout

```text
src/devagentops/
├── runtime/        # typed messages, ReAct loop, Tool Policy, read/grep/find/ls
├── conditions/     # L1 / L2 / L4 / Oracle execution conditions
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

Validate the current L4 formal configuration without running the model：

```bash
.venv/bin/devagentops eval doctor \
  --matrix evaluation/matrices/l4-minimax-m3-development-v2.json \
  --registry components/registry.json \
  --suite evaluation/suites/triage-v1/suite.json
```

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
6. [L4 Runtime Design](docs/evaluation/l4-self-built-react-runtime-design.md) — frozen L4 V1 self-built Agent Runtime contract;
7. [Oracle Evidence Diagnostic Condition](docs/evaluation/oracle-evidence-diagnostic-condition.md) — evidence-conditioned diagnostic boundary;
8. [Oracle ↔ L4 Pair Analysis Findings](docs/evaluation/milestones/oracle-l4-pair-analysis-2026-08-19.md) — current badcase analysis and next-decision record;
9. [Milestone Status Index](docs/evaluation/milestones/README.md) — tells which dated milestone documents are historical baselines versus current decision records.

`docs/adr/archive/`、dated milestone docs、Case review packets 和 merged PR discussions 是历史记录；它们不覆盖当前 Active ADR 与 current-facing docs。直接阅读 dated milestone 前先看 Milestone Status Index。

## Current roadmap

Oracle↔L4 Pair Analysis 已完成，当前工作不再是“再做一次 L4-only coordinate-assistance ablation”。最新顺序是：

```text
Shared deterministic Evidence Reference Canonicalization
    -> offline replay of historical L1/L2/Oracle/L4 raw candidate outputs
    -> validate normalization correctness and counterfactual metric recovery
    -> new L1/L2/Oracle/L4 20×3 formal comparison generation
    -> establish the new fair shared-output baseline
    -> separate L4 batch + parallel Tool Policy efficiency experiment
```

Shared canonicalization 只把 model-authored、可确定解析的 same-family line-range reference 映射到 frozen Canonical IDs；exact ID 原样保留，不做 fuzzy matching，不读取 Required Evidence / Expected Answer，也不根据语义替模型选择“应该引用什么”。无法确定解析的引用仍由正常 validation 判 invalid。

L4 的第二个已观察到的工程瓶颈是执行效率：历史 formal run 有 `26` 个 `multiple_tool_calls_rejected` ToolCall IDs，且 `802` 个 successful Model Decisions 产生 `24.72M` prompt tokens。Canonicalization 稳定后，再单独把 Tool Policy 从 `single + sequential` 演进到 `batch + parallel`，测 Model Decisions、tokens、wall-clock 与质量指标变化。

L3 static retrieval、context management、planner/verifier、skills/MCP、memory 等仍保持 evidence-gated；当前没有证据要求把这些能力与上述两个已确认问题混在同一轮实现里。
