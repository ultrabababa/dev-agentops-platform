# 理解 FastAPI 响应测试的两个维度

用户已经能够编写 FastAPI `TestClient` 测试，并说明 `response.status_code` 验证 HTTP 请求的处理结果，`response.json()` 验证响应内容是否符合接口契约。这意味着后续可以在相同测试结构上增加存储状态接口的不同场景。

## Evidence

用户独立完成 `/health` 与 `/version` 的正式测试，全量测试通过，并正确解释了状态码断言和 JSON 内容断言各自验证的内容。
