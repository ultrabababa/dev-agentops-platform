# 理解运行依赖与开发依赖的分类标准

用户已经能够根据“生产程序正常运行时是否必须使用”区分依赖：SQLAlchemy 与生产代码使用的 HTTP client 属于正式运行依赖，pytest 与仅由 TestClient 使用的 HTTP client 属于开发依赖。用户理解分类取决于使用场景，而不是库名本身。

## Evidence

用户正确完成了 SQLAlchemy、pytest 和生产 HTTPX 三个依赖分类场景。
