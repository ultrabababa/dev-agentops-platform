import type { ReactNode } from "react";

import type { FormalMetricVector, PublicRunManifest, Run } from "../api/types";

export const metricEntries: Array<[keyof FormalMetricVector, string]> = [
  ["execution_coverage", "Execution Coverage"],
  ["failure_type_exact_match", "Failure Type Exact Match"],
  ["report_evidence_hit_rate", "Report Evidence Hit Rate"],
  ["required_fields_completeness", "Required Fields Completeness"],
  ["protocol_validity_rate", "Protocol Validity"],
];

export const stageLabels = {
  baseline: "基线",
  canonicalization: "规范化",
  runtime_optimization: "Runtime 优化",
  retrieval_attribution: "Retrieval 归因",
} as const;

export const roleLabels: Record<string, string> = {
  historical_baseline: "历史基线",
  fresh_canonicalized: "规范化代表 Run",
  initial_treatment: "Runtime 优化首轮",
  replication_reference: "复现实验 · 原策略",
  replication_treatment: "复现实验 · 新策略",
  representative_condition: "正式代表 Run",
};

export const runtimeLabels: Record<string, string> = {
  full_context_one_shot: "Full Context / One Shot",
  fixed_model_workflow: "Fixed Model Workflow",
  static_retrieval: "Static Retrieval",
  self_built_react: "Self-built ReAct Runtime",
  model_one_shot: "Selected Source Evidence / One Shot",
};

export const failureTypeLabels: Record<string, string> = {
  test_assertion_failure: "Test assertion",
  lint_or_type_failure: "Lint / type",
  dependency_or_install_failure: "Dependency / install",
  config_or_environment_failure: "Config / environment",
  timeout_or_flaky_failure: "Timeout / flaky",
};

export const shortId = (value: string) => `${value.slice(0, 8)}…`;
export const percent = (value: number | null | undefined) => value == null ? "—" : `${(value * 100).toFixed(2)}%`;
export const dateTime = (value: string | null) => value ? new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)) : "—";

export function PageIntro({ eyebrow, title, identity, description, meta }: { eyebrow: string; title: string; identity?: ReactNode; description: string; meta?: ReactNode }) {
  return <header className="explorer-intro"><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{identity ? <div className="explorer-canonical-identity">{identity}</div> : null}<p>{description}</p>{meta ? <div className="explorer-intro-meta">{meta}</div> : null}</header>;
}

export function FailureTypeLabel({ value, showCanonical = false }: { value: string; showCanonical?: boolean }) {
  return <span className="failure-type-display" title={value}><span>{failureTypeLabels[value] ?? value}</span>{showCanonical ? <code>{value}</code> : null}</span>;
}

export function ExplorerLoading({ label = "正在读取公开实验数据…" }: { label?: string }) {
  return <div className="explorer-state" aria-busy="true"><span className="state-index">···</span><div><h2>{label}</h2><p>数据直接来自只读 Evaluation Explorer API。</p></div></div>;
}

export function ExplorerError({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="explorer-state error" role="alert"><span className="state-index">!</span><div><h2>公开实验数据读取失败</h2><p>页面不会用静态值或推测结果替代 API 响应。</p><code>{message}</code>{retry ? <button type="button" onClick={retry}>重新读取</button> : null}</div></div>;
}

export function RunStatus({ run }: { run: Pick<Run, "status" | "failed_samples"> }) {
  if (run.status === "completed_with_sample_failures") return <span className="run-status warning"><b>Run 已完成<span className="sr-only">Run completed</span></b><small>{run.failed_samples} 个 Sample 执行失败<span className="sr-only">sample failures: {run.failed_samples}</span></small></span>;
  return <span className="run-status"><b>{run.status === "completed" ? <>Run 已完成<span className="sr-only">Run completed</span></> : run.status}</b>{run.failed_samples > 0 ? <small>{run.failed_samples} 个 Sample 执行失败<span className="sr-only">sample failures: {run.failed_samples}</span></small> : null}</span>;
}

export function FormalMetrics({ metrics, compact = false }: { metrics: FormalMetricVector | null; compact?: boolean }) {
  if (!metrics) return <p className="empty-inline">Formal metric vector unavailable · 未使用推测值替代</p>;
  return <dl className={`explorer-metrics ${compact ? "compact" : ""}`}>
    {metricEntries.map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{percent(metrics[key])}</dd></div>)}
  </dl>;
}

export function MetricGuide() {
  return <div className="metric-guide" aria-label="五项正式指标怎么读">
    <div><strong>Execution Coverage</strong><span>计划 Sample 中，实际完成并进入评分的比例。</span></div>
    <div><strong>Failure Type Exact Match</strong><span>模型给出的故障类型与冻结标签完全一致的比例。</span></div>
    <div><strong>Report Evidence Hit Rate</strong><span>最终报告命中冻结 Required Evidence 的比例。</span></div>
    <div><strong>Required Fields Completeness</strong><span>Structured Report 必填字段的完整度。</span></div>
    <div><strong>Protocol Validity</strong><span>报告通过输出协议与结构校验的比例。</span></div>
  </div>;
}

export function HashValue({ value }: { value: string | null | undefined }) {
  if (!value) return <span>—</span>;
  return <code className="hash-value" title={value} tabIndex={0}>{shortId(value)}<span className="sr-only">完整值：{value}</span></code>;
}

export function ProvenanceSheet({ run, sampleIdentity }: { run: Run; sampleIdentity?: { case_id: string; repeat_index: number } }) {
  const manifest: PublicRunManifest = run.manifest;
  const fields: Array<[string, ReactNode, string?]> = [
    ["Run", <HashValue value={run.run_id} />],
    ...(sampleIdentity ? [["Case", <code>{sampleIdentity.case_id}</code>], ["Repeat", <code>{sampleIdentity.repeat_index}</code>]] as Array<[string, ReactNode]> : []),
    ["Condition", run.catalog.condition_family], ["Runtime", runtimeLabels[run.runtime_variant] ?? run.runtime_variant],
    ["实验阶段 / 角色", `${stageLabels[run.catalog.stage]} / ${roleLabels[run.catalog.role] ?? run.catalog.role}`],
    ["Provider / Model", `${manifest.model_configuration.provider ?? "—"} / ${manifest.model_configuration.model ?? "—"}`],
    ["Suite", `${run.suite_id} / v${run.suite_version}`], ["Suite fingerprint", <HashValue value={manifest.suite_fingerprint} />],
    ["Condition fingerprint", <HashValue value={manifest.condition_fingerprint} />], ["Treatment fingerprint", <HashValue value={manifest.treatment_fingerprint} />],
    ["Execution policy", <HashValue value={manifest.execution_policy_fingerprint} />], ["Run configuration", <HashValue value={manifest.run_configuration_fingerprint} />],
    ["Code revision", <HashValue value={manifest.code_revision} />], ["Evaluation method", manifest.evaluation_method ?? "—"],
    ["Output contract", `${manifest.output_contract.id ?? "—"} / ${manifest.output_contract.version ?? "—"}`], ["Manifest SHA", <HashValue value={run.manifest_sha256} />],
  ];
  return <dl className="provenance-sheet">{fields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>;
}
