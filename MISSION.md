# Mission: 建立可解释、可评测的 Agent Runtime 工程闭环

## Why

DevAgentOps 的目标不是只实现一个能调用模型和工具的 Agent，而是把 Agent Runtime、Environment、Trace、Evaluation 与 Badcase Analysis 连接成一个可复现、可验证、可持续演进的工程闭环。

项目中的实现和学习都应服务于一个核心能力：

> 能独立理解、实现、验证并解释一个 Agent System 为什么工作，以及它在什么地方失败。

## Success looks like

- 能从代码层解释 Case / Environment 如何进入 Runtime，并最终形成可评分的 Structured Triage Report。
- 能解释 Model 与 Runtime 的控制边界，而不是把“Agent”当成一个不可拆解的黑盒。
- 能理解并实现 typed conversation、ToolCall / ToolResult、retry、budget、Trace、trajectory persistence 等 Runtime 核心机制。
- 能解释 Matrix / Treatment / Component / Suite / code revision 如何共同形成 formal experiment identity。
- 能从 formal artifact 和 trajectory 中区分 evidence acquisition、citation/mapping、reasoning 与 infrastructure failure。
- 能依据真实 badcase 决定下一项 Runtime capability，而不是按功能清单堆 planner、memory、multi-agent 等机制。

## Working principles

- 所有关键结论尽量落到当前 DevAgentOps 的真实代码、Case、Trace 或 formal artifact。
- 先建立最小可信实现，再通过端到端反馈增加能力。
- Behavior-affecting change 必须显式 version / fingerprint / Treatment 化，不静默修改已经记录的 baseline。
- TDD 用于验证 deterministic software contract；Formal Eval / EBDD 用于验证 Agent/System behavior。
- 历史实验和决策记录保留原貌；current-facing docs 负责维护当前架构事实。

## Current technical focus

L4 self-built ReAct Runtime baseline 已完成。当前重点从“把 Runtime 跑起来”转向：

```text
formal run
    -> Oracle / L4 pairing
    -> realization-gap analysis
    -> badcase attribution
    -> controlled ablation
    -> next Runtime capability
```

后续 context management、retrieval、planner/verifier、skills/MCP、memory、multi-agent 等能力都应由真实 trajectory / badcase 证据触发，而不是预先堆入 baseline。
