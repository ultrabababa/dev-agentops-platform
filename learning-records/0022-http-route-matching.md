# 理解 HTTP 路由由 method 与 path 共同匹配

用户已经能够预测：`GET /health` 命中已登记路由并成功，`POST /health` 因 path 存在但 method 不匹配而得到 method not allowed，`GET /unknown` 因 path 未登记而得到 not found。这为理解 FastAPI path operation decorator 提供了正确基础。

## Evidence

用户在实现 FastAPI 代码前，独立正确预测了三种请求结果。
