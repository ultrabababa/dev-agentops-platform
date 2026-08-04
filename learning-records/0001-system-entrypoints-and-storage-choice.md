# 区分系统入口、观察界面与持久化选择

用户已经能够正确判断：Formal Evaluation Run 应由 CLI 启动，诊断失败应从 Run Trace 入手，多 Worker 并发写入时应从 SQLite 迁移到 PostgreSQL。下一步需要继续巩固的边界是：自然语言属于 Agent 的任务输入和推理层，CLI 属于可复现的系统操作入口，二者可以同时存在，并非互相替代。

## Evidence

用户正确回答了 CLI、Trace 和 PostgreSQL 三个场景判断题，并主动指出此前把 Agent 默认理解为自然语言交互产品。
