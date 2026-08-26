export const conditionCopy = {
  L1: {
    name: "Full Context / One Shot",
    question: "完整上下文一次性给模型时，基础诊断能力如何？",
  },
  L2: {
    name: "Fixed Model Workflow",
    question: "固定多阶段 workflow 是否能稳定提升结构化诊断？",
  },
  L3: {
    name: "Static Retrieval",
    question: "静态 Retrieval 在哪里丢失 Required Evidence？",
  },
  L4: {
    name: "Self-built ReAct Runtime",
    question: "自主 ToolUse Runtime 能否更有效地获取并使用证据？",
  },
  Oracle: {
    name: "Evaluator-controlled Evidence intervention",
    question: "当 Required Evidence 由 evaluator 直接提供时，模型上限如何？",
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
  ["Evaluator Isolation", "Expected Answer / Required Evidence 不进入 Agent input"],
  ["Deterministic Scoring", "Structured Report 由确定性 validator / scorer 评分"],
  ["Reproducible Provenance", "Run / Suite / Condition / Treatment fingerprints 保留实验身份"],
] as const;
