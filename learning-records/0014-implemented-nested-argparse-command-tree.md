# 能实现嵌套 argparse 命令树

用户已经能够独立实现并通过测试验证 `db init --database PATH` 的两层 argparse 命令树，包括两个必需 subparser、`command` 与 `db_command` 的目标属性，以及通过 `_database_path` 将字符串转换为 `Path`。

## Evidence

练习中的 `test_parser_maps_nested_commands_and_database_path` 已实际运行通过。
