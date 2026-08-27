export const conditionCopy = {
  L1: {
    name: "Full Context / One Shot",
    question: "完整上下文一次性给模型时，基础诊断能力如何？",
  },
  L2: {
    name: "Fixed Model Workflow",
    question: "把一次模型调用拆成固定的“分析 → 报告”两阶段后，结果会出现什么差异？",
  },
  L3: {
    name: "Static Retrieval",
    question: "加入确定性的 Static Retrieval 后，Required Evidence 主要丢在哪一步？",
  },
  L4: {
    name: "Self-built ReAct Runtime",
    question: "让模型自己决定何时调用 read / grep / find / ls 等工具后，诊断过程会发生什么变化？",
  },
  Oracle: {
    name: "Evaluator-controlled Evidence intervention",
    question: "如果直接把关键 Evidence 提供给模型，模型本身还能做到什么？",
  },
} as const;

export const metricLabels = [
  ["execution_coverage", "Execution Coverage"],
  ["failure_type_exact_match", "Failure Type Exact Match"],
  ["report_evidence_hit_rate", "Report Evidence Hit Rate"],
  ["required_fields_completeness", "Required Fields Completeness"],
  ["protocol_validity_rate", "Protocol Validity"],
] as const;

export const evaluationPrinciples = [
  ["Frozen Inputs", "冻结输入，避免 benchmark 在运行间漂移"],
  ["Evaluator Isolation", "普通 Conditions 中，Expected Answer 与 evaluator Required Evidence 不进入模型输入；Oracle 是显式标记的诊断干预例外。"],
  ["Deterministic Scoring", "Structured Report 由确定性的 validator / scorer 评分，避免人工主观打分。"],
  ["Reproducible Provenance", "保存 Run / Suite / Condition / Treatment fingerprints，让每个结果都能追溯到具体实验配置。"],
] as const;
