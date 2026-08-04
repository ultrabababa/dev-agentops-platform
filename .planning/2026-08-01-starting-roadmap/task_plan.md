# DevAgentOps Starting Roadmap

## Goal

以秋招交付为近期目标，把 DevAgentOps 建设成可运行、可复现、可评测的 CI/Test Failure Triage 系统原型；长期积累 Agent Learning Systems、Evals & Environments、Runtime 和 Post-training Data Infrastructure 能力。

## Current Status — 2026-08-04

- [x] Issue #2：确认 V1 Failure Type taxonomy 与 Offline Case policy。
- [x] PR #7：合并策略文档和五个文档契约测试。
- [ ] Issue #3：Bootstrap CLI、SQLite、FastAPI 和 React/Vite smoke path（当前主线）。
- [ ] Issue #4：Evaluation Matrix 与 Effective Condition。
- [ ] Issue #5：Component Registry 与 Freeze。
- [ ] Issue #6：Offline Case Package 与 Evaluation Suite。

## Current Slice

Issue #3 的第一个纵向切片已于 2026-08-04 完成：

```text
CLI db init
→ Alembic migration
→ local SQLite
→ read-only status
→ offline tests
```

- `status` 在数据库不存在时保持只读，不创建目录或文件；
- `db init` 可以重复执行，并通过 Alembic 维护 Schema 版本；
- 正常初始化、重复初始化、非法路径和空数据库均有自动化测试；
- Issue #2 与当前 Slice 的测试合计 12 个测试、30 个子测试通过。

下一切片是 FastAPI health/version 与 SQLite read endpoint；React/Vite 在 API smoke path 稳定后接入。

## Working Principles

1. 项目优先：先交付可运行的纵向切片，书本与实验按需穿插。
2. 最小闭环：先让 Environment、Runtime、Trajectory、Grader 和 Data 各有最小版本。
3. 螺旋升级：依赖关系决定起点，真实反馈决定下一轮投入，不孤立地把单个模块做到极致。
4. V1 克制：只做调查、证据、Trace、Runtime 对比、Eval 和 Badcase，不做 Mutation、真实 CI 或训练闭环。
5. 可验证交付：每个 Slice 都必须有可执行命令、自动化测试和明确的失败边界。
6. 来源权威：实现只依赖 GitHub Issue、PRD、Active ADR、`CONTEXT.md` 和代码测试；个人 Issue Note 不作为需求来源。

## Book Experiments — Just in Time

- Issue #4/#6：Chapter 6 `public-health-reporting-eval`。
- Trace 与 scorer：Chapter 8 `trajectory-verifier`。
- Pipeline/ReAct runtime：Chapter 5 `log-diagnosis`，只提取结构，不复制其超出 V1 的修复闭环。
- 成本记录：Chapter 6 `agent-cost-analysis`。
- Tool、Context 实验只在工具数量或上下文长度成为真实瓶颈后进行。

## Success Criteria

- 项目能本地端到端运行；
- Case、组件与评测条件可复现；
- Trajectory、Evidence 和失败原因可检查；
- Pipeline 与 Agent Runtime 可公平比较；
- 至少一次改进由新 Formal Evaluation Run 与 Badcase Carryover 验证；
- 能清楚解释架构、取舍、失败场景和后续演进。

## Errors Encountered

| Error | Attempt | Resolution |
|---|---:|---|
| 沙箱内安装依赖时无法访问 PyPI | 1 | 获得授权后安装声明的 SQLAlchemy、Alembic 与 pytest 依赖，并完成离线测试。 |
