# 理解真实 HTTP server smoke path

用户已经能够安装并运行 Uvicorn，理解 `devagentops.api:app` 分别指向 Python 模块与其中的应用对象，并能区分进程内 `TestClient` 测试和通过真实监听端口执行的 `Uvicorn + curl` smoke test。

## Evidence

用户启动 Uvicorn 0.52.1，手工验证全部接口成功，并正确解释了 Uvicorn import string 以及是否真正启动服务这一核心差异。
