import type { ConditionId } from "../api/types";

export type ConditionEditorial = {
  id: ConditionId;
  name: string;
  runtimeVariant: string;
  explanation: string;
  question: string;
  change: string;
  interpretation: string;
  modelVisible: string[];
  runtimeObservability?: string[];
  evaluatorOnly: string[];
};

export const ladderIds: ConditionId[] = ["L1", "L2", "L3", "L4"];

export const conditionEditorial: Record<ConditionId, ConditionEditorial> = {
  L1: {
    id: "L1",
    name: "Full Context / One Shot",
    runtimeVariant: "full_context_one_shot",
    explanation: "把整个 Case 的日志和代码上下文一次性给模型，只调用一次模型生成最终报告。",
    question: "如果模型一次就看到全部上下文，它能把故障诊断到什么程度？",
    change: "L1 是最简单的基线：不做 Retrieval、不调用工具，也没有多轮 Agent 调查。程序只把完整 Case 上下文整理成一次请求，模型直接生成最终报告。",
    interpretation: "L1 告诉我们“一次性把全部上下文给模型”能做到什么。它是后续实验的参照，但某个指标比其他 Condition 低，并不能直接说明模型本身能力更弱，因为后续 Condition 还改变了信息供给和运行方式。",
    modelVisible: ["Case 基本信息与只读限制", "完整日志和冻结代码快照", "用于引用证据的 answer-neutral Canonical Evidence 坐标", "Structured Report 输出格式"],
    evaluatorOnly: ["Expected Answer", "哪些证据属于 Required Evidence", "scorer ground truth", "curator rationale 与 fix information"],
  },
  L2: {
    id: "L2",
    name: "Fixed Model Workflow",
    runtimeVariant: "fixed_model_workflow",
    explanation: "仍然给模型完整上下文，但固定调用两次：先分析证据，再根据分析结果生成最终报告。",
    question: "把“先分析证据、再写报告”固定成两步，结果会有什么变化？",
    change: "L2 不增加 Retrieval 或工具。程序固定先执行 evidence_analysis，再把这一步的可见输出作为 handoff，连同完整 Evidence 一起交给 report_synthesis。模型不能自己加步骤、跳步骤或改变流程。",
    interpretation: "这组数字说明固定两阶段 workflow 本身能跑到什么水平。但 L1→L2 不只是“多了一步思考”：调用结构、每阶段的输出合同和 handoff 都变了，所以只能把它们看成两种整体方案的差异，不能说差异一定由“两阶段”这一点单独造成。",
    modelVisible: ["两个阶段都会收到完整 Evidence Universe", "用于引用证据的 answer-neutral Canonical Evidence 坐标", "Stage 1 的可见输出会作为 Stage 2 handoff", "每个阶段自己的固定任务与输出格式"],
    evaluatorOnly: ["Expected Answer", "哪些证据属于 Required Evidence", "scorer ground truth", "curator rationale 与 fix information"],
  },
  L3: {
    id: "L3",
    name: "Static Retrieval",
    runtimeVariant: "static_retrieval",
    explanation: "不再把全部上下文交给模型：程序先按固定规则检索出一部分证据，再调用模型一次。",
    question: "先自动找证据再让模型诊断时，证据主要丢在“没找出来”还是“找到了但没写进报告”？",
    change: "L3 把“完整上下文”换成确定性的 Retrieval 结果。检索规则、排序和 packing 都由程序固定；模型不会生成 retrieval query，也不能追加搜索。这样可以单独观察“证据获取”这一步到底损失了多少信息。",
    interpretation: "结果说明两类损失同时存在：一部分 Required Evidence 根本没有被 Retriever 找到；已经找出来的证据，也不是都会在最终报告里被正确引用。L3 的价值是把这两个问题拆开，并没有证明它的 Report Evidence Hit 高于 L1/L2。",
    modelVisible: ["Case 基本信息与只读限制", "Static Retriever 选中并 packing 后的原始证据片段", "source path、物理行号范围和原始内容", "与这些片段重叠的 answer-neutral Canonical Evidence 坐标 / IDs", "Structured Report 输出格式"],
    evaluatorOnly: ["Required Evidence IDs 和是否命中的判定", "检索结果与 Required Evidence 的事后 intersection 分析", "Expected Answer", "scorer ground truth 与 curator rationale"],
  },
  L4: {
    id: "L4",
    name: "Self-built ReAct Runtime",
    runtimeVariant: "self_built_react",
    explanation: "模型不再一次性接收固定证据上下文，而是在只读 workspace 里自己决定下一步查什么、什么时候提交报告。",
    question: "让模型自己决定下一步查什么、什么时候停止，会发生什么？",
    change: "L4 第一次把调查过程的控制权交给模型。每一轮模型可以选择 read / grep / find / ls，或者直接提交报告；Runtime 负责检查请求、执行工具、控制预算、记录 Trace / Trajectory，并决定是否还能继续。当前代表 Run 使用 Single + Sequential policy：Runtime 每轮最多接受并执行 1 个 ToolCall；如果模型同轮给出多个 ToolCalls，这些调用会被全部拒绝并返回 policy-error ToolResults。",
    interpretation: "这组结果说明自适应工具循环已经能作为一个完整的诊断 Runtime 运行，但不能据此说“Agent 一定优于固定流程”。这里的五项指标来自 Single + Sequential 的代表 Run；Batch + Parallel 是后来单独做的运行效率优化实验，属于同一个 L4 Runtime family，但不是这组代表指标的来源。",
    modelVisible: ["Case 基本信息、workspace 路径与只读限制", "用于最终引用的 answer-neutral Canonical Evidence 坐标词表", "按顺序累积的 ToolCall / ToolResult 对话", "最终 Structured Report 输出格式"],
    runtimeObservability: ["Trace：工具执行和 Runtime 生命周期事件", "provider request attempts、latency 与 token usage", "预算消耗与终止原因", "tool execution metadata"],
    evaluatorOnly: ["Expected Answer", "哪些证据属于 Required Evidence", "scorer ground truth", "curator rationale 与 fix information"],
  },
  Oracle: {
    id: "Oracle",
    name: "Selected Source Evidence / One Shot",
    runtimeVariant: "model_one_shot",
    explanation: "评测侧先定位关键原始证据片段，再把这些片段作为 evidence context 交给模型；模型不知道它们为什么被选中。",
    question: "如果跳过“自己找证据”这一步，直接给模型关键原始证据片段，它还能诊断到什么程度？",
    change: "Oracle 不让模型自己做 Evidence discovery。评测侧用 required_evidence_ids 定位冻结文件里的原始 source spans；模型的 evidence context 只包含这些选中的原始片段，同时仍保留正常的 Case 基本信息和报告合同。模型看不到 Required Evidence 标签、Expected Answer，也看不到选择这些片段的理由。",
    interpretation: "Oracle 回答的是一个条件性问题：如果普通的“找证据”难度被拿掉，模型还能做到什么。它不是 L5、不是 Product Runtime，也不是理论上界；它只是帮助我们区分“证据没找到”和“证据已经给到模型但诊断仍然失败”这两类问题。",
    modelVisible: ["被选中的原始证据片段：evidence_id / source / span / content", "Case 基本信息与只读限制", "一次模型调用", "与其他 Conditions 相同的最终报告格式"],
    evaluatorOnly: ["required_evidence_ids selector set", "Expected Answer", "哪些片段被选中的 evaluator-side 语义", "curator reasoning / selection rationale", "scorer labels 与 fix information"],
  },
};

export const ladderDimensions = [
  { label: "给模型的 Evidence", values: ["全部上下文", "全部上下文", "程序先检索一部分", "模型用工具按需读取"] },
  { label: "模型调用方式", values: ["一次", "固定两阶段", "一次", "多轮循环"] },
  { label: "工具使用", values: ["无", "无", "无", "模型发起 ToolCall"] },
  { label: "下一步由谁决定", values: ["程序固定结束", "程序固定流程", "程序固定检索后结束", "模型决定继续调查或提交报告"] },
] as const;
