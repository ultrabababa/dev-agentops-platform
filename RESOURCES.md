# DevAgentOps Engineering Resources

## Knowledge

- [Python 官方 Argparse Tutorial](https://docs.python.org/3/howto/argparse.html)
  Python 标准库对命令、位置参数、可选参数和自动帮助信息的入门说明。用于理解 `devagentops db init` 与 `status` 如何从字符串参数变成程序状态。
- [Python 官方 pathlib 文档](https://docs.python.org/3/library/pathlib.html)
  文件路径对象、存在性和文件类型检查的权威参考。用于实现不会误写目录或非法路径的 Storage Boundary。
- [Python 官方 sqlite3 文档](https://docs.python.org/3/library/sqlite3.html)
  SQLite 连接、事务和 DB-API 行为的权威说明。用于理解“连接可能创建数据库文件”以及测试为何必须验证只读行为。
- [SQLAlchemy 2.0 Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html)
  SQLAlchemy Engine、Dialect、Pool 和 SQLite URL 的官方解释。用于理解项目为何把文件路径转换成 Engine，并在连接后才真正访问数据库。
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
  Migration Environment、Revision 和 `upgrade head` 的官方教程。用于理解 Schema 演进和可重复初始化。
- [Alembic Commands API](https://alembic.sqlalchemy.org/en/latest/api/commands.html)
  `command.upgrade(config, "head")` 等编程式迁移接口的官方定义。用于对照当前 `initialize_database` 实现。
- [pytest Getting Started](https://docs.pytest.org/en/stable/getting-started.html)
  pytest 的断言、测试发现和失败报告入门。用于把需求转成可执行反馈，而不是靠手工点测。
- [Python Packaging Entry Points 规范](https://packaging.python.org/en/latest/specifications/entry-points/)
  PyPA 对 console script 包装器、对象引用和退出码传播的权威说明。用于理解 `[project.scripts]` 如何把终端命令连接到 Python 函数。

## Wisdom (Communities)

- [SQLAlchemy GitHub Discussions](https://github.com/sqlalchemy/sqlalchemy/discussions)
  由项目维护者和使用者讨论真实设计问题。遇到 Engine、Transaction 或 Dialect 行为不确定时，用最小复现提问。
- [Python Discuss](https://discuss.python.org/)
  Python 官方社区讨论区。适合验证标准库、Packaging 和语言行为的理解。

## Gaps

- 等进入 FastAPI Slice 后，再补充官方 FastAPI、ASGI 与测试资源；现在提前阅读会增加无关认知负担。
