# 理解数据库初始化的编排主干

用户已经能够从实际代码中识别 `initialize_database()` 的核心流程：通过 `command.upgrade(config, "head")` 让 Alembic 将数据库迁移到最新版本，然后调用 `inspect_database()` 读取迁移后的数据库状态并返回给 CLI。下一步可以继续区分“执行迁移是否成功”和“读取应用级状态是否完整”这两个不同判断。

## Evidence

用户阅读实现后，主动指出了 `command.upgrade(_alembic_config(path), "head")` 与随后 `inspect_database(path)` 的调用链。
