# DevAgentOps

DevAgentOps 是一个用于求职展示和系统研究的、可评测的 CI/Test Failure Triage AgentOps 原型。它把真实失败组织成可重放的 Offline Case，通过不同 Runtime/Condition 产生 Structured Triage Report，并用统一的 Trace、Persistence、Scorer 与 Formal Evaluation 比较系统能力。

它不是通用 Coding Agent，也不把尚未验证的原型包装成成熟商业产品。当前技术主线是：

```text
Frozen Case / Environment
    -> Runtime / Agent execution
    -> Trace + complete Agent trajectory
    -> deterministic scoring / Oracle diagnostics
    -> badcase analysis
    -> controlled runtime evolution
```

## Current state — 2026-08-18

当前已经完成并冻结的关键基础：

- V1 Failure Type taxonomy；
- Offline Case Schema V2 与 Public/Trusted Evaluator boundary；
- `triage-suite-v1`：20 个 Human-reviewed Formal Cases，五类 Failure Type 各 4 个；
- Canonicalization Profile v1；
- Structured Triage Report V1 + deterministic scorer；
- Matrix v2、Treatment / Execution Policy / Run Configuration fingerprints；
- Component Registry；
- doctor-first formal execution、repeated Sample scheduler、Case-first aggregation；
- Run Manifest、Trace、SQLite persistence、JSON/Markdown artifacts；
- MiniMax-M3 provider path + exact local context/token accounting；
- L1 `full_context_one_shot` formal milestone：20 Case × 3，60/60 scored，0 execution failures；
- L2 `fixed_model_workflow` formal milestone：20 Case × 3，60/60 scored / 120 model calls，0 execution failures；
- Oracle Evidence formal milestone：20 Case × 3，60/60 scored，0 execution failures。

L4 `self_built_react`：

- [ADR 0128](docs/adr/0128-l4-self-built-react-runtime-contract.md) 与 [L4 implementation design](docs/evaluation/l4-self-built-react-runtime-design.md) 已 Human-freeze；
- Issue #52 implementation 尚未开始；
- L4 formal milestone 尚未运行；
- Oracle-vs-L4 realization-gap machinery 等真实 L4 formal artifact 后再实现。

如果早期文档写着“Formal Suite 尚未冻结”“Canonicalization Profile 待 calibration”“Oracle 未来实现”“L4 design 尚未决定”，应按其历史日期理解，不代表当前状态。

## Runtime Capability Ladder

```text
L0 deterministic pipeline
    -> L1 full-context one-shot
    -> L2 fixed model workflow
    -> L3 static retrieval
    -> L4 self-built ReAct
    -> L5+ incremental Agent capabilities
```

这是一套 capability-attribution framework，不是 mandatory implementation order。

| Level | Role | Current state |
| --- | --- | --- |
| L0 | deterministic Product Runtime baseline | implemented |
| L1 | one-shot model diagnostic | formal milestone complete |
| L2 | fixed multi-stage model diagnostic | formal milestone complete |
| L3 | static retrieval diagnostic | not implemented; does not block L4 |
| L4 | first Agentic Product Runtime | design frozen; implementation pending |
| Oracle | orthogonal evidence-conditioned diagnostic | formal milestone complete |

详见 [Runtime Capability Ladder](docs/evaluation/runtime-capability-ladder.md)。

## L4 frozen design in one view

L4 是最小 self-built ReAct Agent Runtime，不采用 LangChain/LangGraph/Pi 作为 dependency。Pi 只作为 reference architecture。

```text
Model Decision
    -> Runtime validates action/policy/budget
    -> optional Tool execution
    -> ToolResult observation
    -> typed conversation state update
    -> next Model Decision or terminal report
```

V1 native tools：

```text
read
grep
find
ls
```

`submit_report` **不是** native tool。0 ToolCalls 表示模型尝试终止，由 Runtime 解析 visible assistant text 为 Structured Triage Report candidate。

Agent-visible filesystem：

```text
/raw.log
/repository/...
```

L4 initial input 可携带完整 answer-neutral Canonical Evidence coordinate vocabulary 作为 citation vocabulary；Physical Artifact content 仍必须通过 tools 获取，Required Evidence / Expected Answer / evaluator metadata 永不暴露给正常 Agent。

Baseline Tool Policy：

```text
call_mode = single
execution_mode = sequential
multiple_calls = reject_all_with_error_results
```

Hard Agent budget：`max_steps=100`。V1 不提前增加 planner、verifier、memory、multi-agent、Bash/edit/write、MCP、skills 或 automatic compaction。

## Trace vs Agent trajectory

不要把两者混为一份数据：

```text
Run Trace
= runtime execution events / attempts / token usage / latency / tool events / terminal & failure metadata

Agent Trajectory
= one Sample 的完整 ordered UserMessage / AssistantMessage / ToolResultMessage history
```

L4 可以持久化 provider-returned thinking/reasoning 到 trajectory 用于 badcase analysis；它不是 deterministic score input，也不需要把完整 message body 再复制进 Trace。

## Provider and token accounting

当前 formal model foundation 是 MiniMax-M3。L4 继续使用：

```text
DevAgentOps
    -> MiniMaxProvider
    -> OpenAICompatibleChatCompletionsTransport
    -> MiniMax OpenAI Chat Completions API
```

Runtime/message contract 保持 provider-neutral。MiniMax-specific tool calls、reasoning continuation 与 wire JSON 只属于 adapter。

L4 每轮 context preflight 要求 `count_input_tokens()` 与真实 `complete()` 共用同一 model-visible MiniMax serialization path，避免 tools/history/reasoning continuation 在“计算的 context”和“真正发给模型的 context”之间漂移。

## Formal evaluation identity

当前正式新条件使用 Matrix v2：

```text
condition
├── runtime_variant
├── suite
├── evaluation_method
├── treatment
│   ├── provider/model
│   ├── reasoning/generation
│   ├── contracts
│   └── context
└── execution_policy
```

L4 Treatment 需要 Registry-validated：

- shared Task Contract prompt；
- separate Runtime-control prompt；
- Tool Registry；
- Tool Policy。

Tool Registry 定义“tools 是什么以及 ToolResult 如何表现”；Tool Policy 定义“一个 Model Decision 中 ToolCalls 如何执行”。Runtime implementation identity 继续由 `runtime_variant + code_revision` 表示，不新增 `runtime` Component type。

详见 [Matrix / Component Registry guide](docs/evaluation/evaluation-matrix-and-component-registry.md)。

## Evaluation data model

Formal Case V2：

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

- Physical Artifacts = sole fact source；
- Canonical Evidence = deterministic answer-neutral coordinates；
- `required-evidence.json` = hidden Evidence Ground Truth；
- `expected-answer.json` = hidden Diagnosis Ground Truth。

## Reading order for current architecture

发生文档冲突时，优先按：

1. [Active ADR index](docs/adr/README.md)
2. [ADR 0128 — L4 contract](docs/adr/0128-l4-self-built-react-runtime-contract.md)
3. [L4 implementation design](docs/evaluation/l4-self-built-react-runtime-design.md)
4. [Runtime Capability Ladder](docs/evaluation/runtime-capability-ladder.md)
5. [Formal Evaluation Methodology](docs/evaluation/formal-evaluation-methodology.md)
6. [Matrix / Component Registry guide](docs/evaluation/evaluation-matrix-and-component-registry.md)
7. current source/schema/checked-in Matrix files

`docs/adr/archive/`、dated milestone docs、Case review packets、merged PR bodies 记录的是历史决策/实验，不应作为最新 contract 覆盖 Active ADR。

## V1 scope boundary

V1 不做：

- 修改代码、生成/提交 Patch；
- 执行测试、重跑 CI、创建 PR 或部署；
- real CI provider integration；
- OS-level sandbox；
- multi-agent；
- cross-run Agent memory；
- automatic post-training loop。

## Local smoke path

Python 3.11+：

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/devagentops db init --database .devagentops/devagentops.db
.venv/bin/devagentops status --database .devagentops/devagentops.db
.venv/bin/python -m pytest -q -p no:cacheprovider
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

## Current next step

```text
PR #53: Human-freeze L4 design + active-doc consistency audit
    -> merge
    -> implement Issue #52 from ADR 0128 / L4 design
    -> deterministic fake-provider tests
    -> one small live MiniMax tool/continuation qualification
    -> only after PASS: one controlled 20 Case × 3 L4 formal milestone
    -> then consider Oracle-vs-L4 pairing/gap
```
