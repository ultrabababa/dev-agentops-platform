# 走通真实 CLI 初始化与状态查询闭环

用户已经通过安装后的 `devagentops` 命令完成 `db init → status` smoke path：初始化创建 SQLite 文件与两张基础表，返回 `initialized=true` 和成功退出码；随后只读 status 返回完全相同的结构化状态。这证明 console entrypoint、argparse、Storage、Alembic 与 SQLite 的最小链路已经真实连通。

## Evidence

用户提供了 init/status 的两组相同 JSON、两个 `exit=0` 结果，以及目录中新建的 SQLite 文件信息。
