# 理解嵌套 CLI 子命令

用户已经能够读取两层 argparse 子命令：解析 `db init` 后，第一层选择值 `db` 保存到 `args.command`，第二层选择值 `init` 保存到 `args.db_command`。这为实现 CLI dispatch 条件提供了直接基础。

## Evidence

用户正确指出 `db`、`init` 分别命中 `command`、`db_command`。
