# 理解应用工厂中的闭包与 JSON 边界

用户已经理解 `create_app(database_path)` 内部的路由函数会通过闭包记住外层传入的数据库路径，因此不同 app 实例可以绑定不同存储。用户也能区分 `StorageStatus.as_dict()` 负责将数据类转换成稳定的字典结构，而 FastAPI 随后负责把字典编码成 JSON。

## Evidence

用户完成了 `/storage/status` 的缺失数据库测试与实现，并能够复述外层参数被内层函数记住以及数据类到字典再到 JSON 的两阶段转换。
