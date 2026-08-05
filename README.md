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

Evaluation Matrix 与 Component Registry 已形成正式评测配置的两层身份边界：前者定义一次实验实际使用的完整配置，后者证明配置引用的组件版本仍对应原来的行为内容。它们仍是正式评测的前置能力；当前尚不执行 Agent、模型调用或评分流程。下一实施主线是 Offline Case Package / Evaluation Suite。

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
  --registry components/registry.json
```

完整规则、示例、失败条件和当前边界见 [Evaluation Matrix 与 Component Registry](docs/evaluation/evaluation-matrix-and-component-registry.md)。具体 Manifest 字段和 Freeze 命令也可查阅 [components/README.md](components/README.md)。

运行后端与前端测试及前端生产构建：

```bash
.venv/bin/python -m pytest -q -p no:cacheprovider
cd frontend
npm test
npm run build
```

## 当前执行顺序

```text
#2 V1 taxonomy 与 Offline Case policy（已完成）
→ #3 应用 smoke path（已完成）
→ #4 Evaluation Matrix（已完成）
→ #5 Component Registry（已完成）
→ #6 Offline Case Package / Evaluation Suite（下一步）
```

《AI Agent Book》及其实验按当前 Issue 的具体问题穿插使用，不作为项目开工前置课程。
