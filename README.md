# DevAgentOps

DevAgentOps 是一个面向 **CI / Test Failure Triage** 的 Agent Runtime 与 Formal Evaluation 平台。

**Live Demo:** https://devagentops.onrender.com

它把真实工程失败冻结为可重放的 Offline Case Environment，让不同 Runtime、Evidence Acquisition 与 Agent-control Treatment 在同一 Suite、同一 Ground Truth 和同一 Scorer 下运行，并把执行、评分和归因证据完整保留下来。

项目不是单纯追求“Agent 分数更高”，而是回答两个工程问题：

> 一个 Agent System 实际实现了多少模型诊断能力？
>
> 当它失败时，损失发生在 Evidence acquisition、Evidence utilization / citation、report protocol，还是 Runtime / provider infrastructure？

当前 V1 范围是**只读诊断**：不编辑代码、不执行测试、不重跑 CI，也不自动提交修复。

## Evaluation-driven development

DevAgentOps 的核心闭环是：

```text
Frozen Case / Environment
    -> Runtime / Agent execution
    -> Trace + complete Agent trajectory
    -> deterministic validation / scoring
    -> Case-first aggregation / Oracle diagnostics
    -> badcase attribution
    -> controlled experiment / ablation
    -> evidence-driven Runtime evolution
    -> next Evaluation
```

Evaluation 不是最后一张成绩单，而是下一轮工程决策的起点。

## Runtime / condition ladder

Capability ladder 用于做归因，而不是把所有能力塞进一个“Agent”黑盒：

| Level | Condition | Control | Evidence acquisition | Status |
| --- | --- | --- | --- | --- |
| L0 | deterministic pipeline | program-controlled | deterministic fixed access | implemented |
| L1 | `full_context_one_shot` | one model call | full visible universe upfront | formal milestone complete |
| L2 | `fixed_model_workflow` | fixed multi-stage program | fixed explicit input flow | formal milestone complete |
| L3 | `static_retrieval` | program-controlled | static retrieval | formal 20×3 complete |
| L4 | `self_built_react` | model adaptive next-action / stop | read/search/list tool loop | formal milestones + Batch/Parallel replication complete |

Oracle Evidence 与 ladder 正交。它是 evaluator-side diagnostic intervention：绕过普通 Evidence discovery，由 evaluator 定位 source-faithful 原始证据片段供模型使用；模型不会看到 Required Evidence 标签、隐藏参考答案、selection rationale、scorer labels 或 fix information。

Oracle **不是 L5、不是产品 Runtime、也不是理论上限**。

详见 [Runtime Capability Ladder](docs/evaluation/runtime-capability-ladder.md) 与 [Oracle Evidence Diagnostic Condition](docs/evaluation/oracle-evidence-diagnostic-condition.md)。

## L4 self-built ReAct Runtime

L4 是当前 Agent Runtime kernel 的基线实现：

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

- provider-neutral typed messages；
- Runtime 拥有 authoritative execution state、Tool Policy、budget 与 terminal handling；
- Trace 与完整 Agent Trajectory 分离持久化；
- provider retry 属于 Runtime Trace，不伪装成 Agent Decision；
- ToolResult 有 hard bound，避免单次无限读取；
- historical baseline Tool Policy 保留 `single + sequential + reject-all multi-call`；
- current recommended L4 Tool Policy 使用 `batch + parallel + independent-call handling`；
- `max_steps = 100`，一个 Model Decision 无论包含多少 ToolCalls 仍只消耗一个 step；
- `submit_report` 不是 native tool，0 ToolCalls 表示尝试提交 Structured Triage Report。

完整设计见 [ADR 0128](docs/adr/0128-l4-self-built-react-runtime-contract.md)、[ADR 0129](docs/adr/0129-l4-provider-reported-context-accounting.md) 与 [L4 Runtime Design](docs/evaluation/l4-self-built-react-runtime-design.md)。

## Formal Evaluation

Formal Evaluation 统一复用：

```text
Matrix v2
    -> doctor-first validation
    -> frozen Component / Suite / Case identity
    -> repeated Sample scheduler
    -> Runtime execution
    -> Trace + Trajectory persistence
    -> Structured Triage Report validation
    -> deterministic scorer
    -> Sample -> Case -> Failure Type / Suite aggregation
    -> JSON / Markdown artifacts
```

同一 `triage-suite-v1` 包含 20 个 Human-reviewed Formal Cases，每个 Case 重复 3 次。

### Representative canonicalized formal results

| Condition | Execution Coverage | Failure Type Exact Match | Report Evidence Hit Rate | Required Fields Completeness | Protocol Validity |
| --- | ---: | ---: | ---: | ---: | ---: |
| L1 | 98.33% | 80.00% | 52.16% | 99.79% | 96.61% |
| L2 | 96.67% | 83.33% | 54.15% | 98.33% | 98.28% |
| **L3 static retrieval** | **100.00%** | **88.33%** | 50.67% | **99.79%** | **98.33%** |
| **L4 self-built ReAct** | **100.00%** | **81.67%** | **71.83%** | **99.58%** | **93.33%** |
| Oracle diagnostic intervention | 100.00% | 83.33% | 85.40% | 96.67% | 96.67% |

这些 representative Runs 是 fresh hosted-model generation。普通 Run-vs-Run 差异不能直接当成单变量因果效应。

## Four experiments that drove Runtime evolution

### 1. Evidence Reference Canonicalization

历史 raw model output 保持完全不变，只改变 deterministic Evidence reference canonicalization，再使用同一 validator / scorer 重放。

L4 fixed-output replay：

```text
Protocol Validity        81.36% -> 96.61%
unknown Evidence IDs     12     -> 0
Failure Type Exact Match 88.33% -> 88.33%  (unchanged)
```

这提供了最强的 causal isolation：一部分 Protocol / Evidence badcase 来自 report-validation infrastructure，而不是模型诊断本身。

详见 [Shared Evidence Reference Canonicalization Milestone](docs/evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md)。

### 2. L4 Tool Policy: Single + Sequential vs Batch + Parallel

保持 Suite、模型配置、evaluation method、output contract、code revision 与 L4 Runtime identity 一致，改变 Tool Policy，并做 fresh back-to-back replication。

Clean replication：

```text
Model Decisions        877 -> 571     (-34.89%)
Executed ToolCalls      809 -> 775     (-4.20%)
Wall time            978.27s -> 806.69s (-17.54%)
Mean sample latency                -26.60%
P95 sample latency                 -28.07%
```

质量差值：

```text
Failure Type Exact Match      +3.33pp
Report Evidence Hit Rate      -1.14pp
Required Fields Completeness  +4.79pp
Protocol Validity             -1.67pp
```

效率收益在 replication 中再次出现；没有观察到可复现的实质质量回退。由于两边都是 fresh generation，质量指标的小幅变化只作为观测结果，不作为 Tool Policy 改变诊断质量的因果证据。

详见 [L4 Batch + Parallel ToolCalls Milestone](docs/evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md)。

### 3. L3 Static Retrieval attribution

L3 没有展示相对 L1 / L2 的 Report Evidence Hit uplift，因此继续拆 Evidence pipeline：

```text
Required Evidence
    -> Retrieval Acquisition
    -> Acquired Evidence Utilization
    -> Final Report Citation
```

正式诊断结果：

```text
Retrieval Acquisition Recall              76.56%
Acquired Required Evidence Utilization    66.18%
Final Report Evidence Hit                 50.67%
```

结论不是简单的“Retrieval 没找到证据”：损失同时发生在 acquisition 和拿到证据后的 utilization / citation。

详见 [L3 Static Retrieval V1 Formal Milestone](docs/evaluation/milestones/l3-static-retrieval-2026-08-24.md)。

### 4. Oracle Evidence Intervention

Oracle 暂时绕过普通 Evidence discovery，模型仍只看到 source-faithful 原始 Evidence，而不是隐藏答案或 Required Evidence 标签。

Representative Report Evidence Hit Rate：

```text
L1      52.16%
L2      54.15%
L3      50.67%
L4      71.83%
Oracle  85.40%
```

这给出强诊断信号，支持把 Evidence discovery / acquisition 列为重点瓶颈候选；它用于 diagnosis / hypothesis formation，不是严格的 Run-level causal estimate。

## Public Evaluation Explorer

公网展示：**https://devagentops.onrender.com**

Explorer 是只读的 interviewer-facing evidence surface，覆盖：

- 项目概览与 Evaluation-driven development 主线；
- L1 / L2 / L3 / L4 / Oracle Conditions；
- 12 个 catalogued formal Runs；
- Case-first / Sample drill-down；
- Structured Report 与 Evidence；
- Agent Trajectory 与 Runtime Trace 的显式分离；
- Experiment & Attribution：Canonicalization、L4 Tool Policy、L3 Retrieval、Oracle 四个 curated case studies。

Public data layer 通过 `showcase-data/catalog.json` 索引 12 个正式 Run，并查询 9 个经过确定性净化的 frozen SQLite snapshot。公开 API 为 GET-only，不暴露 raw `.devagentops/` databases、Expected Answer body、provider reasoning/thinking、opaque continuation state 或未净化 raw message/manifest JSON。

部署结构：

```text
https://devagentops.onrender.com
        React / Vite Static Site
                 |
                 v
https://devagentops-showcase-api.onrender.com/api
        FastAPI read-only API
                 |
                 v
        sanitized frozen showcase data
```

部署说明见 [Public Showcase Deployment](docs/showcase-deployment.md)，数据边界见 [ADR 0131](docs/adr/0131-public-evaluation-explorer-data-boundary.md) 与 [showcase-data/README](showcase-data/README.md)。

> Render Free API 可能在闲置后冷启动；这属于 hosting behavior，不是 DevAgentOps Runtime benchmark latency。

## Repository layout

```text
src/devagentops/
├── runtime/        # typed messages, ReAct loop, Tool Policy, read/grep/find/ls
├── conditions/     # L1 / L2 / L3 / L4 / Oracle
├── providers/      # provider-neutral contract + MiniMax adapter
├── evaluation/     # Matrix, scheduler, Trace, scoring, aggregation, artifacts
├── explorer/       # public read-only Evaluation Explorer service
└── storage/        # SQLite / migrations / trajectory persistence

components/         # frozen behavior components + registry
evaluation/         # suites, cases, matrices, formal evaluation inputs
showcase-data/      # sanitized public Run snapshots + catalog
docs/               # ADRs, methodology, milestones, deployment
frontend/           # React/Vite public Evaluation Explorer
```

## Quick start

Python 3.11+：

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest -q -p no:cacheprovider
```

Validate the current recommended L4 Tool Policy without calling the model：

```bash
.venv/bin/devagentops eval doctor \
  --matrix evaluation/matrices/l4-minimax-m3-batch-parallel-canonicalized-v1.json \
  --registry components/registry.json \
  --suite evaluation/suites/triage-v1/suite.json
```

Run the local API：

```bash
DEVAGENTOPS_SHOWCASE_CATALOG_PATH=showcase-data/catalog.json \
  .venv/bin/python -m uvicorn devagentops.api:app --host 127.0.0.1 --port 8000
```

Run the frontend：

```bash
cd frontend
npm ci
npm run dev
```

## Documentation map

Current-facing docs：

1. [CONTEXT.md](CONTEXT.md) — compact current project context and terminology;
2. [Formal Evaluation Methodology](docs/evaluation/formal-evaluation-methodology.md) — Case / evidence / trust model;
3. [Evaluation Matrix & Component Registry](docs/evaluation/evaluation-matrix-and-component-registry.md) — experiment identity;
4. [Runtime Capability Ladder](docs/evaluation/runtime-capability-ladder.md) — controlled capability comparisons;
5. [L4 Runtime Design](docs/evaluation/l4-self-built-react-runtime-design.md) — frozen historical L4 V1 Runtime contract;
6. [L4 Batch + Parallel ToolCalls Milestone](docs/evaluation/milestones/l4-batch-parallel-toolcalls-2026-08-19.md) — current Tool Policy evidence;
7. [L3 Static Retrieval V1 Formal Milestone](docs/evaluation/milestones/l3-static-retrieval-2026-08-24.md) — retrieval attribution;
8. [Oracle Evidence Diagnostic Condition](docs/evaluation/oracle-evidence-diagnostic-condition.md) — Oracle semantic boundary;
9. [Shared Evidence Reference Canonicalization Milestone](docs/evaluation/milestones/evidence-reference-canonicalization-2026-08-19.md) — fixed-output causal isolation;
10. [Public Showcase Deployment](docs/showcase-deployment.md) — deployed Explorer topology and operations;
11. [Milestone Status Index](docs/evaluation/milestones/README.md) — dated formal experiment history.

Historical ADRs, dated milestone docs, Case review packets and merged PR discussions intentionally preserve historical wording and are not retroactively rewritten.

## Current direction

Shared Evidence Reference Canonicalization、L4 Batch + Parallel ToolCalls、L3 Static Retrieval formal qualification 和 public Evaluation Explorer 均已完成。

Current evidence does not justify adding arbitrary batch caps, forced-batching prompts, vector databases, rerankers, planner/verifier, memory or multi-agent complexity to V1.

The next large Product Runtime capability direction is **executable repair / sandboxed remediation**：

```text
investigate
    -> diagnose
    -> mutate / edit
    -> execute / test
    -> observe
    -> retry
    -> verify
    -> report
```

它属于当前 read-only triage V1 之后的独立阶段，不应 retroactively 改写现有 frozen L1–L4 / Oracle contracts 或正式实验结果。
