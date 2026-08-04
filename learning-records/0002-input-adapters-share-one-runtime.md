# 不同输入适配器共享同一个 Agent Runtime

用户已经理解 CLI、网页表单和自然语言聊天只是表层任务提交方式不同，应先转换为统一任务契约，再交给同一个 Agent Runtime 执行；这避免重复实现 Agent Loop、Tool Policy、Trace 和 Evaluation 逻辑，并让不同入口的行为仍可比较和治理。

## Evidence

用户明确回答“把自然语言任务转换后交给现有 Agent Runtime”，并能用“表面提交方式不同、底层调用一致”解释原因。
