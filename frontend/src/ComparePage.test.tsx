import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import type { Condition, Overview, Run, RunComparison } from "./api/types";

const vectors = {
  L1: { execution_coverage: 1, failure_type_exact_match: .7, report_evidence_hit_rate: .521561, required_fields_completeness: .92, protocol_validity_rate: .9 },
  L2: { execution_coverage: 1, failure_type_exact_match: .72, report_evidence_hit_rate: .541468, required_fields_completeness: .94, protocol_validity_rate: .92 },
  L3: { execution_coverage: 1, failure_type_exact_match: .73, report_evidence_hit_rate: .506653, required_fields_completeness: .95, protocol_validity_rate: .93 },
  L4: { execution_coverage: 1, failure_type_exact_match: .75, report_evidence_hit_rate: .7183, required_fields_completeness: .98, protocol_validity_rate: .92 },
  Oracle: { execution_coverage: 1, failure_type_exact_match: .8, report_evidence_hit_rate: .853955, required_fields_completeness: .99, protocol_validity_rate: .97 },
};

function makeRun(side: "a" | "b"): Run {
  const reference = side === "a";
  return {
    run_id: reference ? "b6ad2a0f-1b40-49e2-8ce6-28b14f8b2df8" : "d76ac5ca-22a3-4c67-acf3-c33bba68f0d5",
    status: "completed", condition_id: reference ? "l4-reference" : "l4-treatment", runtime_variant: "self_built_react",
    suite_id: "triage-suite-v1", suite_version: "1", started_at: "2026-08-19T12:30:38Z", completed_at: "2026-08-19T13:01:13Z",
    planned_samples: 60, scored_samples: 60, failed_samples: 0,
    catalog: { stage: "runtime_optimization", role: reference ? "replication_reference" : "replication_treatment", condition_family: "L4", representative: false, comparison_group: "l4_replication" },
    manifest: {
      schema_version: "2", run_kind: "formal_full_suite", model_configuration: { provider: "minimax-official", model: "MiniMax-M3" },
      output_contract: { id: "structured-triage-report-json", version: "development-v2", schema_version: "1" }, code_revision: "2e1ff851",
      git_dirty: true, suite_fingerprint: "suite-fingerprint", treatment_fingerprint: reference ? "treatment-a" : "treatment-b",
      condition_fingerprint: reference ? "condition-a" : "condition-b", execution_policy_fingerprint: "policy",
      run_configuration_fingerprint: reference ? "config-a" : "config-b", evaluation_method: "triage-method-v1", structured_report_schema_version: "1",
    },
    manifest_sha256: reference ? "manifest-a" : "manifest-b",
    suite_aggregate: { run_id: reference ? "run-a" : "run-b", requested_sample_count: 60, scored_sample_count: 60, execution_failed_sample_count: 0, execution_coverage: 1, protocol_validity_rate: reference ? .933333 : .916667, quality_status: "complete", formal_metric_vector: vectors.L4 },
    failure_type_aggregates: [],
  };
}

const runA = makeRun("a");
const runB = makeRun("b");

const comparison: RunComparison = {
  run_a: runA, run_b: runB,
  compatibility: { same_suite: true, same_suite_fingerprint: true, same_model_configuration: true, same_evaluation_method: true, same_output_contract: true, same_code_revision: true, same_runtime_variant: true, same_treatment: false },
  semantic_category: "controlled_fresh_generation_comparison", causal_claim_supported: false, causal_reference: null,
  formal_metrics: {
    execution_coverage: { label: "Execution Coverage", a: 1, b: 1, delta_pp: 0 },
    failure_type_exact_match: { label: "Failure Type Exact Match", a: .716667, b: .75, delta_pp: 3.333333 },
    report_evidence_hit_rate: { label: "Report Evidence Hit Rate", a: .746402, b: .73504, delta_pp: -1.136243 },
    required_fields_completeness: { label: "Required Fields Completeness", a: .933333, b: .98125, delta_pp: 4.791667 },
    protocol_validity_rate: { label: "Protocol Validity", a: .933333, b: .916667, delta_pp: -1.666667 },
  },
  runtime_optimization: {
    artifact_id: "l4-batch-parallel-toolcalls-2026-08-19", authority: "milestone_artifact",
    interpretation: "efficiency_reproduced_no_reproducible_material_quality_regression_demonstrated",
    metrics: {
      model_decisions: { a: 877, b: 571 }, executed_tool_calls: { a: 809, b: 775 }, input_tokens: { a: 23448236, b: 15696354 },
      output_tokens: { a: 301898, b: 286089 }, total_tokens: { a: 23750134, b: 15982443 }, run_wall_time_seconds: { a: 978.270385, b: 806.685981 },
      mean_sample_latency_seconds: { a: 77.91716755, b: 57.19310078 }, p50_sample_latency_seconds: { a: 63.134314, b: 45.8250175 }, p95_sample_latency_seconds: { a: 184.51134615, b: 132.7258861 },
    },
  },
};

const conditions: Condition[] = (["L1", "L2", "L3", "L4", "Oracle"] as const).map((condition) => ({
  condition,
  runtime_variant: condition === "Oracle" ? "model_one_shot" : condition === "L3" ? "static_retrieval" : condition === "L4" ? "self_built_react" : condition === "L2" ? "fixed_model_workflow" : "full_context_one_shot",
  representative_run: { run_id: condition === "Oracle" ? "023d5960-c450-42e1-a516-a874106673f4" : `${condition.toLowerCase()}-run`, status: "completed", planned_samples: 60, scored_samples: 60, failed_samples: 0 },
  formal_metric_vector: vectors[condition], related_run_ids: [], comparison_group: "representative",
}));

const overview: Overview = {
  benchmark: { case_count: 20, repeats_per_case: 3, samples_per_formal_run: 60, failure_type_count: 5 },
  representative_conditions: { L1: { run_id: "l1-run", runtime_variant: "full_context_one_shot" }, L2: { run_id: "l2-run", runtime_variant: "fixed_model_workflow" }, L3: { run_id: "a9d5bce2-d635-4573-baf1-d26c391fedf8", runtime_variant: "static_retrieval" }, L4: { run_id: "l4-run", runtime_variant: "self_built_react" }, Oracle: { run_id: "023d5960-c450-42e1-a516-a874106673f4", runtime_variant: "model_one_shot" } },
  experiment_evolution_endpoint: "/api/experiments/evolution",
  featured_findings: {
    canonicalization: { artifact_id: "evidence-reference-canonicalization-2026-08-19", authority: "fixed_output_offline_replay", l4: { protocol_validity_before: .813559, protocol_validity_after: .966102, unknown_evidence_ids_before: 12, unknown_evidence_ids_after: 0, failure_type_exact_match_before: .883333, failure_type_exact_match_after: .883333 } },
    runtime_optimization: { artifact_id: "runtime", authority: "formal_trace_metrics_and_replication", run_ids: [runA.run_id, runB.run_id], model_decisions: [877, 571], executed_tool_calls: [809, 775], run_wall_seconds: [978.270385, 806.685981], interpretation: "bounded" },
    retrieval_attribution: { artifact_id: "l3-static-retrieval-2026-08-24", authority: "formal_l3_result_snapshot", run_id: "a9d5bce2-d635-4573-baf1-d26c391fedf8", retrieval_acquisition_recall: .765595, acquired_required_evidence_utilization: .661825, report_evidence_hit_rate: .506653, report_evidence_improvement_over_l1_l2: "not_demonstrated" },
  },
};

const preset = { id: "l4-replication", run_a: runA.run_id, run_b: runB.run_id, category: "controlled_fresh_generation_comparison", artifact: "runtime_optimization" } as const;
function json(value: unknown, status = 200) { return Promise.resolve(new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } })); }
function mockApi() { return vi.spyOn(globalThis, "fetch").mockImplementation((input) => { const url = String(input); if (url === "/api/overview") return json(overview); if (url === "/api/conditions") return json(conditions); if (url === "/api/comparisons") return json([preset]); if (url.startsWith("/api/compare?")) return json(comparison); return json({ detail: "not found" }, 404); }); }
function renderCompare() { window.history.pushState({}, "", "/compare"); return render(<App />); }

afterEach(() => { cleanup(); vi.restoreAllMocks(); window.history.pushState({}, "", "/"); });

describe("Phase 2D Experiment & Attribution page", () => {
  it("presents the EDD loop and four curated cases instead of an arbitrary Run picker", async () => {
    mockApi(); renderCompare();
    expect(await screen.findByRole("heading", { name: "实验与归因" })).toBeInTheDocument();
    const loop = screen.getByRole("list", { name: "Evaluation-driven development 闭环" });
    for (const stage of ["Formal Evaluation", "Failure Attribution", "Controlled Experiment / Ablation", "Evidence → Runtime Evolution"]) expect(within(loop).getByText(stage)).toBeInTheDocument();
    expect(within(loop).getByText(/badcase/)).toBeInTheDocument();
    expect(within(loop).getByText(/hypothesis/)).toBeInTheDocument();
    for (const title of ["Evidence 引用规范化", "L4 工具执行策略", "L3 静态检索归因", "Oracle 证据干预"]) expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    expect(screen.queryByText("探索其他 Run 对比")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /更换 Run/ })).not.toBeInTheDocument();
  });

  it("teaches canonicalization as a fixed-output causal isolation experiment", async () => {
    mockApi(); renderCompare(); await screen.findByRole("heading", { name: "Evidence 引用规范化" });
    expect(screen.getByText(/我们没有重新调用模型/)).toBeInTheDocument();
    expect(screen.getByText("模型输出完全不变")).toBeInTheDocument();
    expect(screen.getByText(/81.36%/)).toBeInTheDocument();
    expect(screen.getAllByText(/12/).length).toBeGreaterThan(0);
    expect(screen.getByText(/88.33%/)).toBeInTheDocument();
    expect(screen.getByText("unchanged")).toBeInTheDocument();
    expect(screen.getByText(/优先修复基础设施/)).toBeInTheDocument();
    expect(screen.getByText(/模型的 Failure Type 判断没变/)).toBeInTheDocument();
  });

  it("shows authoritative L4 efficiency, quality, and non-causal boundaries", async () => {
    mockApi(); renderCompare(); await screen.findByRole("heading", { name: "L4 工具执行策略" });
    expect(screen.getByText("Single + Sequential")).toBeInTheDocument();
    expect(screen.getByText("Batch + Parallel")).toBeInTheDocument();
    expect(screen.getByText("877 → 571")).toBeInTheDocument();
    expect(screen.getByText("809 → 775")).toBeInTheDocument();
    expect(screen.getByText("978.27s → 806.69s")).toBeInTheDocument();
    for (const name of ["Execution Coverage", "Failure Type Exact Match", "Report Evidence Hit Rate", "Required Fields Completeness", "Protocol Validity"]) expect(screen.getAllByText(name).length).toBeGreaterThan(0);
    expect(screen.getByText(/效率收益在 replication 中再次出现；没有观察到可复现的实质质量回退/)).toBeInTheDocument();
    expect(screen.getByText(/不作为 Tool Policy 改变诊断质量的因果证据/)).toBeInTheDocument();
    expect(screen.getByText(/causal_claim_supported = false/)).toBeInTheDocument();
    expect(screen.queryByText("Diagnosis Accuracy")).not.toBeInTheDocument();
    expect(screen.queryByText("Root Cause Accuracy")).not.toBeInTheDocument();
  });

  it("attributes L3 Evidence loss across acquisition and utilization stages", async () => {
    mockApi(); renderCompare(); await screen.findByRole("heading", { name: "L3 静态检索归因" });
    expect(screen.getAllByText("52.16%").length).toBeGreaterThan(0); expect(screen.getAllByText("54.15%").length).toBeGreaterThan(0);
    expect(screen.getByText("正式结果没有显示出 L3 的 Evidence Hit 提升。")).toBeInTheDocument();
    expect(screen.getByText("Retrieval Acquisition Recall")).toBeInTheDocument();
    expect(screen.getByText("Acquired Required Evidence Utilization")).toBeInTheDocument();
    expect(screen.getAllByText("Report Evidence Hit Rate").length).toBeGreaterThan(0);
    expect(screen.getByText("76.56%")).toBeInTheDocument(); expect(screen.getByText("66.18%")).toBeInTheDocument(); expect(screen.getAllByText("50.67%").length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /Evidence 的损失不只发生在 Retrieval/ })).toBeInTheDocument();
  });

  it("keeps Oracle an answer-safe diagnostic intervention rather than L5 or a causal estimate", async () => {
    mockApi(); renderCompare(); await screen.findByRole("heading", { name: "Oracle 证据干预" });
    expect(screen.getByText("Oracle 不是 L5")).toBeInTheDocument();
    expect(screen.getByText("不是产品 Runtime")).toBeInTheDocument();
    expect(screen.getByText("不是理论上限")).toBeInTheDocument();
    for (const hidden of ["Required Evidence 标签", "隐藏参考答案", "scorer label / selection rationale", "fix information"]) expect(screen.getByText(hidden)).toBeInTheDocument();
    expect(screen.getByText("85.40%")).toBeInTheDocument();
    expect(screen.getByText(/不是严格的 Run-level causal estimate/)).toBeInTheDocument();
    expect(screen.getByText(/只用于 diagnosis \/ hypothesis formation/)).toBeInTheDocument();
  });

  it("keeps secondary metrics and methodology explanation progressively disclosed", async () => {
    mockApi(); renderCompare(); await screen.findByRole("heading", { name: "四个实验，不是四次“比谁分数高”。" });
    fireEvent.click(screen.getByText("查看完整 Runtime 指标"));
    expect(screen.getByText("Input Tokens")).toBeInTheDocument();
    expect(screen.getByText("Mean Sample Latency")).toBeInTheDocument();
    expect(screen.getByText("P95 Sample Latency")).toBeInTheDocument();
    fireEvent.click(screen.getByText("为什么不同问题要用不同实验方法？"));
    for (const method of ["固定输出 Replay", "控制变量 Ablation", "Replication", "Badcase attribution", "Diagnostic intervention"]) expect(screen.getAllByText(method).length).toBeGreaterThan(0);
  });

  it("provides restrained evidence drill-down navigation", async () => {
    mockApi(); renderCompare(); await screen.findByRole("heading", { name: "实验与归因" });
    expect(screen.getByRole("link", { name: "查看全部正式 Runs →" })).toHaveAttribute("href", "/runs");
    expect(screen.getByRole("link", { name: "查看 Cases / Samples →" })).toHaveAttribute("href", "/cases");
    expect(screen.getByRole("link", { name: /Agent Trajectory \/ Runtime Trace/ })).toHaveAttribute("href", `/runs/${runB.run_id}`);
  });

  it("shows an honest API error and never invents experiment metrics", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => { const url = String(input); if (url === "/api/overview") return json(overview); if (url === "/api/conditions") return json(conditions); if (url === "/api/comparisons") return json([preset]); if (url.startsWith("/api/compare?")) return json({ detail: "unavailable" }, 503); return json({}, 404); });
    renderCompare();
    expect(await screen.findByText(/无法读取 \/compare\?/)).toBeInTheDocument();
    expect(screen.queryByText("877 → 571")).not.toBeInTheDocument();
    expect(screen.queryByText("Retrieval Acquisition Recall")).not.toBeInTheDocument();
  });
});
