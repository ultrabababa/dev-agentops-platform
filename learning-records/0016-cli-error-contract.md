# 能实现 CLI 的结构化错误契约

用户已经能够在 CLI 边界捕获 `StorageError`，把结构化错误 JSON 写入 stderr 并返回退出码 `2`，同时保持成功 JSON 只写入 stdout 并返回 `0`。至此用户完成了参数解析、命令分发、成功输出和失败输出的最小 CLI 进程契约。

## Evidence

Lesson 0003 的 parser、成功路径和错误路径三个测试已全部实际运行通过。
