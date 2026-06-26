# Require a Batch Eval Runner in V1

V1 will include a batch evaluation runner that executes a named evaluation suite and emits machine-readable and human-readable reports. This is required because DevAgentOps is defined by repeatable AgentOps comparison, not by one-off agent demos; the runner is how baseline versus ReAct behavior, metric changes, and badcases become visible.
