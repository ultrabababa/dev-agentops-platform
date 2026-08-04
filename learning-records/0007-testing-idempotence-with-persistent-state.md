# 能用持久化状态测试初始化幂等性

用户已经能够编写并修正一条完整的回归测试：第一次初始化后提交 marker 数据，再次初始化同一数据库，最后分别验证 marker 仍然存在且 Alembic revision 保持为 `0001`。这表明用户不仅能口头解释幂等初始化，还能用事务提交、查询取值和具体断言证明初始化不会清空已有数据。

## Evidence

练习测试 `test_repeated_initialization_preserves_existing_data` 已实际运行通过；用户在反馈后正确处理了显式提交、Cursor 取值、参数绑定，以及应用 Schema 版本与 Alembic revision 的区别。
