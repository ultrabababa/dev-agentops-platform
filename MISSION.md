# Mission: 掌握 DevAgentOps 的最小工程闭环

## Why

为了秋招中能够独立实现并讲清自己的 Agent 项目，而不是只展示 AI 生成的代码；长期形成建设 Agent Runtime、Evals、Environments 和可验证数据闭环所需的工程能力。

## Success looks like

- 不看现成实现，能画出并解释 `CLI → Storage → Migration → SQLite → JSON` 数据流。
- 能从空文件实现一个不会意外创建数据库的只读 `status`，并用测试证明。
- 能解释 Alembic 为什么让初始化可重复、Schema 为什么需要版本。
- 能读懂失败测试，自己定位到 Path、SQLite、Migration 或 CLI 边界。
- 能在面试中说明这一切如何服务于可复现 Evaluation，而不是只背框架 API。

## Constraints

- 学习必须落到当前 DevAgentOps 代码和可运行练习。
- 每次只学一个小闭环，控制在 30–60 分钟。
- 先回忆、预测和动手，AI 在第一次尝试前不直接给完整答案。
- 现成实现只作为完成练习后的对照和反馈。

## Out of scope

- CLI/SQLite 基础未掌握前，不进入 FastAPI、React、LLM、RAG 或复杂 Agent Runtime。
- 当前不学习模型训练、RL 算法或自动 Post-training 闭环。
- 算法面试训练在 `leetcode-hot-100` 使用独立学习轨道，不与本项目课程混在一起。
