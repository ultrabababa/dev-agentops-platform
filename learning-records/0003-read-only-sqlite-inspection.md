# 实现无副作用的 SQLite 状态检查

用户已经能够使用 `Path.resolve(strict=False)` 规范化路径，区分缺失路径与非法目录，并通过 SQLite URI `mode=ro` 查询 `sqlite_master` 后在 `finally` 中关闭连接。这建立了“观察状态不改变状态”的 Storage Boundary 基础，可以继续学习幂等初始化与 Alembic Migration。

## Evidence

用户独立完成 `inspect_existing_sqlite`，数据库缺失、目录拒绝和已有数据库表名排序三个自动化测试全部通过。
