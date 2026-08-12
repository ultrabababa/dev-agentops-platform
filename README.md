# DevAgentOps

DevAgentOps 是一个用于秋招展示和系统研究的、可评测的 CI/Test Failure Triage 系统原型。它把 CI 与测试失败组织成可重放的 Offline Case，通过固定 Pipeline 或 Single Triage Agent 收集证据、生成 Structured Triage Report，并比较诊断质量、工具路径、成本和稳定性。

它不是通用 Coding Agent，也不把尚未验证的原型包装成成熟商业产品。项目当前关注的问题是：如何让 Agent 在真实研发任务中的执行过程可复现、可追踪、可评测，并逐步沉淀为高质量、可验证的轨迹和学习信号。

## 当前阶段

当前已完成：

- V1 Failure Type taxonomy；
- Offline Case 来源、权限和脱敏策略；
- 首版 20 个等权 Case 的平衡目标；
- Failure Type、failure stage、因果分析和 inconclusive 状态的边界；
- CLI、SQLite、FastAPI 与 React/Vite 的只读 application smoke path；
- Evaluation Matrix 的 Defaults、一层继承、Effective Condition 与 Fingerprint；
- 六类 Component Manifest 的校验、Freeze、Registry 与 Version Pollution 检测。
- 显式 Offline Case Package / Evaluation Suite Loader 与 Case/Suite Fingerprint；
- Structured Triage Report Schema V1 校验与确定性单 Case Metric Vector。
- Issue #16 deterministic Pipeline tracer bullet，包括 doctor-first、Trace、Run Manifest、SQLite persistence、artifact 与既有 scorer 的端到端路径。

Evaluation Matrix、Component Registry 与 Offline Case Schema V2 Loader 已形成评测配置和数据的身份链；Structured Triage Report Scorer 可以对候选报告执行单 Case 确定性评分。Schema V2 Loader 会验证 Physical Artifact membership/integrity、Canonical source span、Evidence/Diagnosis Ground Truth split、Provenance、Sanitization、Case/Suite Fingerprint，并通过 `PublicCaseView` 与公共 CLI 错误阻断 Evaluator 数据泄漏。Schema V1 已退役，不再提供兼容 Loader；当前五个 Batch-1 V1 packages 仍只作 calibration drafts，Issue #15 的 B04 V2 calibration 已通过 Human Review，下一步先校准共享 Canonicalization Profile，再扩展 Formal Case construction。当前可运行无模型、无 Agent 的 deterministic Pipeline tracer bullet；仍不执行 Agent、模型调用、Suite 聚合、Quality Gate、Leaderboard 或 Badcase。

## V1 承诺

V1 将形成以下闭环：

```text
Offline Case Package
→ Pipeline Baseline / Single Triage Agent
→ Evidence-backed Structured Triage Report
→ Run Trace and Run Manifest
→ Metric Vector and Quality Gate
→ Badcase Review and Carryover
```

V1 的成功标准是：

- 系统能在本地端到端运行；
- Failure Case、组件和评测条件可以复现；
- 决策轨迹、工具调用和证据引用可以检查；
- Pipeline 与 Agent Runtime 可以在同一 Evaluation Suite 上公平比较；
- 至少展示一次由评测和 Badcase 驱动、并经过新 Formal Evaluation Run 验证的改进；
- 项目的架构、取舍、失败场景和演进边界能够被清楚解释。

V1 明确不做：

- 修改代码、生成或提交 Patch；
- 执行测试、重跑 CI 或创建 Pull Request；
- 接入真实 CI Provider；
- OS 级 Sandbox、Multi-Agent Triage 或跨运行 Agent Memory；
- 模型训练或自动 Post-training 闭环。

完整范围以 [V1 PRD](docs/prd/devagentops-v1-agentops-evaluation-baseline.md) 和 [Active ADRs](docs/adr/README.md) 为准。

## Evaluation Methodology

Runtime 能力按 L0 deterministic Pipeline、L1 Full-context One-shot、L2 Fixed Model Workflow、L3 Static Retrieval、L4 self-built ReAct、L5+ incremental capabilities 建立 attribution ladder。它用于区分 model reasoning、fixed orchestration、evidence acquisition 与 adaptive Agent control，不是强制 implementation order；L3 是否必须先于 L4 实现不冻结。V1 Product Runtime 仍只有 Fixed Pipeline 与 self-built ReAct，L1/L2/L3 是 diagnostic/comparison conditions，Oracle 是正交 diagnostic intervention。详见 [Runtime Capability Ladder 与 Model-backed Diagnostic Conditions](docs/evaluation/runtime-capability-ladder.md) 和 [ADR 0127](docs/adr/0127-staged-runtime-capability-ladder-and-reference-boundary.md)。

每个 Formal Case V2 定义一个 authentic、frozen、offline、bounded-but-realistic Evidence Universe，只包含完整或自然有界的 raw log 与 bounded exact-revision repository snapshot。Package 分为唯一事实源 `physical-artifacts/`、以 source span 和 resolved hash 指回事实源的 `canonical-evidence/`、以及只对可信 Evaluator 可见的 `evaluator/`；Project Knowledge 不属于当前 Case Universe，可在未来作为独立 Runtime/Retrieval ablation 输入。`required-evidence.json` 是唯一 Evidence Ground Truth，`expected-answer.json` 只保存 Diagnosis Ground Truth。各 ladder condition 与 Oracle 如何观察同一世界由各自 Evidence Acquisition Condition 决定；L1 Full-context 不得 silent truncation 后仍保留 full-context identity，具体 over-budget policy 留给未来实现 Issue。详见 [Formal Evaluation Methodology：Evidence Universe 与 Access Conditions](docs/evaluation/formal-evaluation-methodology.md) 和 [ADR 0126](docs/adr/0126-offline-case-schema-v2-physical-artifacts-and-canonical-evidence.md)。

V1 评测方法增加 Oracle Evidence Diagnostic Condition：在保持 Suite、Model、诊断 Prompt、Report Contract、Scorer 与 Inference Settings 尽量一致的配对实验中，绕过普通 Evidence Discovery，只向模型提供经过 Human Review 的 Minimal Sufficient Evidence Set。Oracle input 在运行时由 Required Evidence IDs 经 Canonical Coordinates 解析 Physical Artifacts，不冻结独立 `oracle-evidence.json`；它不会提供 Evidence Ground Truth、Expected Answer、Failure Type Label、答案文本、Tool Path、Scorer Label 或 Curator Reasoning。

Oracle 与正常 Agent 的差异按 Case、Metric 和 Failure Type 报告为 Agent-System Realization Gap，不合成为单一能力分，也不作为普通 Leaderboard 的同 Fingerprint 直接排名。该方法当前仅完成文档与 ADR 设计，尚未实现 Oracle Matrix Schema、Runner、Oracle delivery guard 或 Gap Report；详见 [Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap](docs/evaluation/oracle-evidence-diagnostic-condition.md)。

## 长期演进

DevAgentOps 的长期价值不是停留在 Agent 应用外壳，而是作为一个小型 Agent Learning Systems 原型，逐步研究：

```text
可复现任务环境
→ Agent 执行与完整 Trajectory
→ Verifier / Grader
→ Failure Analysis 与 Hard-case Mining
→ 高价值轨迹和评测数据
→ 候选学习信号
→ 回归评测
```

演进采用螺旋方式：先完成每一环的最小版本，再根据真实反馈共同升级 Environment、Runtime、Trajectory、Grader 和 Data，而不是先把单个模块孤立地做到极致。

这条路线服务于长期向 Agent Systems、Evals & Environments、Agent Runtime、Post-training Data Infrastructure 和 Research Engineering 深入；它不会反向扩大当前 V1 的交付范围。

## 求职价值

项目用于证明以下可迁移能力：

- Python 后端与本地数据工程；
- Agent Runtime、Tool Policy 和执行状态设计；
- 可复现 Case、Trace、Evidence 和 Evaluation Contract；
- 多 Runtime 实验设计、Badcase 分析与回归评测；
- 可靠性、安全边界和人类治理意识。

## 本地 application smoke path

要求 Python 3.11 或更高版本。

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/devagentops db init --database .devagentops/devagentops.db
.venv/bin/devagentops status --database .devagentops/devagentops.db
.venv/bin/pytest
```

`db init` 可以重复执行；它只初始化本地 SQLite Schema。`status` 是只读操作，在数据库不存在时不会创建文件。命令不需要模型 API、网络服务或外部数据库。

启动只读 FastAPI：

```bash
.venv/bin/python -m uvicorn devagentops.api:app --host 127.0.0.1 --port 8000
```

在另一个终端启动 React/Vite dashboard：

```bash
cd frontend
npm ci
npm run dev
```

浏览器打开 `http://127.0.0.1:5173`。Vite 在本地把 `/api/*` 请求代理到 `127.0.0.1:8000`；页面只读取 health、version 和 SQLite 状态，不初始化数据库，也不触发 Agent 或 Eval。

不要直接双击 `frontend/index.html` 或使用 `file://` 打开它。该文件是 Vite 应用入口，必须由 `npm run dev` 提供模块和样式资源；直接打开时页面会显示启动提示，而不是 dashboard。

## Formal Evaluation Configuration

Issue #4 与 #5 共同定义了可复现的正式评测配置：Matrix 解析 Defaults 和一层继承，生成 Effective Condition；Registry 把 Component Version 解析到 Frozen Manifest 并重算 Fingerprint；正式 Condition Fingerprint 同时覆盖 Effective Condition 与已验证的 Component Fingerprints。

```bash
.venv/bin/devagentops component validate --manifest path/to/draft.json
.venv/bin/devagentops component freeze \
  --manifest path/to/draft.json \
  --registry components/registry.json \
  --version component-v1
.venv/bin/devagentops eval doctor \
  --matrix path/to/evaluation-matrix.json \
  --registry components/registry.json \
  --suite path/to/suite.json
.venv/bin/devagentops eval score \
  --case path/to/case.json \
  --report path/to/report.json
```

配置、数据和 Fingerprint 规则见 [Evaluation Matrix、Component Registry 与 Offline Evaluation Suite](docs/evaluation/evaluation-matrix-and-component-registry.md)；Runtime capability attribution 见 [Runtime Capability Ladder 与 Model-backed Diagnostic Conditions](docs/evaluation/runtime-capability-ladder.md)；Evidence Universe、Canonical Evidence 与条件访问语义见 [Formal Evaluation Methodology：Evidence Universe 与 Access Conditions](docs/evaluation/formal-evaluation-methodology.md)；报告校验、单 Case 指标、CLI 和信任边界见 [Structured Triage Report 校验与单 Case 确定性评分](docs/evaluation/structured-triage-report-and-per-case-scoring.md)；Oracle 配对条件与 Gap 解释见 [Oracle Evidence Diagnostic Condition 与 Agent-System Realization Gap](docs/evaluation/oracle-evidence-diagnostic-condition.md)。具体 Component Manifest 字段和 Freeze 命令也可查阅 [components/README.md](components/README.md)。

运行后端与前端测试及前端生产构建：

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider
cd frontend
npm test
npm run build
```

## 当前执行顺序

```text
#2 V1 taxonomy / Case Policy（已完成）
→ #3 Application smoke path（已完成）
→ #4 Evaluation Matrix（已完成）
→ #5 Component Registry（已完成）
→ #6 Offline Case Schema V1 Loader（已完成）
→ #14 Structured Report / Per-Case Scoring（已完成）
→ #21 Evidence Methodology + Schema V2 architecture（已完成）
→ #22 Offline Case Schema V2 implementation（已完成）
→ #16 deterministic Pipeline tracer bullet（已完成）
→ #15 B04 V2 Human Review（已通过）
→ #28 Runtime Capability Ladder docs/design（当前）
→ #15 shared Canonicalization Profile v1 calibration / Human freeze（下一步）
→ #15 Formal Suite Case Construction / Human freeze
```

《AI Agent Book》及其实验按当前 Issue 的具体问题穿插使用，不作为项目开工前置课程。
