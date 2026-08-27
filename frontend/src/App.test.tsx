import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const vector = { execution_coverage: 1, failure_type_exact_match: 0.8833, report_evidence_hit_rate: 0.5067, required_fields_completeness: 0.9979, protocol_validity_rate: 0.9833 };
const canonicalization = { artifact_id: "canonicalization", authority: "fixed_output_offline_replay", l4: { protocol_validity_before: 0.8136, protocol_validity_after: 0.9661, unknown_evidence_ids_before: 12, unknown_evidence_ids_after: 0, failure_type_exact_match_before: 0.8833, failure_type_exact_match_after: 0.8833 } };
const runtime = { artifact_id: "runtime", authority: "formal_trace_metrics_and_replication", run_ids: ["a", "b"], model_decisions: [877, 571], executed_tool_calls: [809, 775], run_wall_seconds: [978.27, 806.69], interpretation: "efficiency_reproduced" };
const retrieval = { artifact_id: "retrieval", authority: "formal_l3_result_snapshot", run_id: "l3", retrieval_acquisition_recall: 0.7656, acquired_required_evidence_utilization: 0.6618, report_evidence_hit_rate: 0.5067, report_evidence_improvement_over_l1_l2: "not_demonstrated" };
const responses: Record<string, object> = {
  "/api/overview": { benchmark: { case_count: 20, repeats_per_case: 3, samples_per_formal_run: 60, failure_type_count: 5 }, representative_conditions: {}, experiment_evolution_endpoint: "/api/experiments/evolution", featured_findings: { canonicalization, runtime_optimization: runtime, retrieval_attribution: retrieval } },
  "/api/conditions": ["L1", "L2", "L3", "L4", "Oracle"].map((condition) => ({ condition, runtime_variant: condition === "Oracle" ? "model_one_shot" : `${condition.toLowerCase()}_runtime`, representative_run: { run_id: condition, status: "completed", planned_samples: 60, scored_samples: 60, failed_samples: 0 }, formal_metric_vector: vector, related_run_ids: [], comparison_group: "fixture" })),
  "/api/experiments/evolution": { stages: [
    { stage: "baseline", run_ids: ["l1", "l2", "oracle", "l4"], artifact_id: null, key_observation: null },
    { stage: "canonicalization", run_ids: [], artifact_id: "canonicalization", key_observation: canonicalization },
    { stage: "runtime_optimization", run_ids: [], artifact_id: "runtime", key_observation: runtime },
    { stage: "retrieval_attribution", run_ids: [], artifact_id: "retrieval", key_observation: retrieval },
  ] },
};

for (const condition of responses["/api/conditions"] as Array<Record<string, unknown>>) {
  const id = String(condition.condition).toLowerCase();
  const runtimeVariants: Record<string, string> = { l1: "full_context_one_shot", l2: "fixed_model_workflow", l3: "static_retrieval", l4: "self_built_react", oracle: "model_one_shot" };
  responses[`/api/conditions/${id}`] = { ...condition, runtime_variant: runtimeVariants[id] };
}

afterEach(() => { cleanup(); vi.unstubAllGlobals(); window.history.pushState({}, "", "/"); });
function stubSuccess() { const mock = vi.fn(async (input: string | URL | Request) => ({ ok: true, json: async () => responses[String(input)] })); vi.stubGlobal("fetch", mock); return mock; }
function renderRoute(path: string) { window.history.pushState({}, "", path); return render(<App />); }

describe("Public Evaluation Explorer", () => {
  it("renders the homepage from API fixtures with all four evolution stages", async () => {
    const fetchMock = stubSuccess(); render(<App />);
    expect(await screen.findByRole("heading", { name: /Agent Runtime.*Formal Evaluation/ })).toBeInTheDocument(); expect(screen.getByText("20")).toBeInTheDocument();
    ["建立第一组可比较的诊断基线", "修复 Evidence Reference 的表示错误", "减少不必要的 Model Decision 轮次", "拆开“没找到”与“找到但没用好”"].forEach((title) => expect(screen.getByRole("heading", { name: title })).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith("/api/overview"); expect(fetchMock).toHaveBeenCalledWith("/api/conditions"); expect(fetchMock).toHaveBeenCalledWith("/api/experiments/evolution");
  });
  it("renders representative API-backed values and canonical terminology", async () => {
    stubSuccess(); render(<App />); await screen.findAllByText("96.61%");
    expect(screen.getAllByText("877").length).toBeGreaterThan(0); expect(screen.getAllByText("571").length).toBeGreaterThan(0); expect(screen.getAllByText("76.56%").length).toBeGreaterThan(0); expect(screen.getAllByText("Failure Type Exact Match").length).toBeGreaterThan(0);
    expect(document.body.textContent).not.toContain("Diagnosis Accuracy"); expect(document.body.textContent).not.toContain("Root Cause Accuracy");
  });
  it("keeps Oracle separate from the L1-L4 ladder and never calls it L5", async () => {
    stubSuccess(); render(<App />); const oracle = await screen.findByRole("complementary"); expect(within(oracle).getByText("独立诊断条件")).toBeInTheDocument(); expect(within(oracle).getByText("不属于 L1–L4")).toBeInTheDocument(); expect(document.body.textContent).not.toContain("L5"); expect(document.body.textContent).not.toContain("ORTHOGONAL DIAGNOSTIC INTERVENTION");
  });
  it("states the Oracle source-evidence exception without exposing evaluator labels", async () => {
    stubSuccess(); render(<App />); await screen.findByText("Evaluator Isolation");
    expect(screen.getByText(/Oracle 仅暴露该 selection 定位出的原始证据片段/)).toBeInTheDocument();
    expect(document.body.textContent).toContain("绕过证据查找，提供关键原始证据片段");
    expect(document.body.textContent).not.toContain("直接提供 Required Evidence");
    expect(document.body.textContent).not.toContain("Expected Answer / Required Evidence 不进入 Agent input");
  });
  it("does not invent metric values when the API fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 503 }))); render(<App />);
    expect(await screen.findByText("产品说明仍可阅读，实验事实暂不展示。")).toBeInTheDocument(); expect(screen.getByText(/HTTP 503/)).toBeInTheDocument(); expect(document.body.textContent).not.toContain("96.61%"); expect(document.body.textContent).not.toContain("877");
  });

  it("renders /conditions from the real Condition API contract", async () => {
    const fetchMock = stubSuccess(); renderRoute("/conditions");
    expect(await screen.findByRole("heading", { name: /我们怎样一步步改变 Agent/ })).toBeInTheDocument();
    expect(screen.getAllByText("full_context_one_shot").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Failure Type Exact Match").length).toBeGreaterThan(0);
    expect(fetchMock).toHaveBeenCalledWith("/api/conditions");
    expect(document.body.textContent).not.toContain("Phase 2B");
    expect(document.body.textContent).not.toContain("PHASE 2B");
    expect(document.body.textContent).not.toContain("Diagnosis Accuracy");
    expect(document.body.textContent).not.toContain("Root Cause Accuracy");
  });

  it("renders L1 identity, one-shot architecture, and API-backed metrics", async () => {
    const fetchMock = stubSuccess(); renderRoute("/conditions/l1");
    expect(await screen.findByRole("heading", { name: "Full Context / One Shot" })).toBeInTheDocument();
    expect(screen.getByText("单次模型调用")).toBeInTheDocument();
    expect(screen.getByText("88.33%")).toBeInTheDocument();
    expect(screen.getByText(/一次把全部上下文交给模型/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/conditions/l1");
  });

  it("describes L2 as the fixed evidence_analysis to report_synthesis workflow", async () => {
    stubSuccess(); renderRoute("/conditions/l2");
    await screen.findByRole("heading", { name: "Fixed Model Workflow" });
    expect(screen.getAllByText(/evidence_analysis/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/report_synthesis/).length).toBeGreaterThan(0);
    expect(screen.getByText(/程序不提供工具或 Retrieval，也没有额外的 verifier \/ repair stage/)).toBeInTheDocument();
    const evaluatorLane = screen.getAllByText(/模型看不到 \/ 仅评测侧/).map((label) => label.closest(".diagram-evaluator-rail")).find(Boolean);
    expect(evaluatorLane).not.toBeNull();
    expect(evaluatorLane).not.toHaveTextContent("verifier");
    expect(document.body.textContent).toContain("先分析证据、再写报告");
  });

  it("keeps L3 acquisition and utilization denominators distinct", async () => {
    stubSuccess(); renderRoute("/conditions/l3");
    await screen.findByRole("heading", { name: "Static Retrieval" });
    expect(screen.getByText("76.56%")).toBeInTheDocument();
    expect(screen.getByText("66.18%")).toBeInTheDocument();
    expect(screen.getByText(/Retrieval Acquisition Recall.*分母：全部 Required Evidence/)).toBeInTheDocument();
    expect(screen.getByText(/Acquired Required Evidence Utilization.*分母：已被 Retrieval 获取的 Required Evidence/)).toBeInTheDocument();
    expect(document.body.textContent).toContain("并没有证明它的 Report Evidence Hit 高于 L1/L2");
    expect(document.body.textContent).toContain("answer-neutral Canonical Evidence 坐标 / IDs");
    expect(document.body.textContent).toContain("Evidence context 只含检索片段");
  });

  it("identifies L4 as the self-built ReAct Runtime and separates Trace from Trajectory", async () => {
    stubSuccess(); renderRoute("/conditions/l4");
    await screen.findByRole("heading", { name: "Self-built ReAct Runtime" });
    expect(screen.getByText("Runtime 每轮最多接受 1 个 ToolCall")).toBeInTheDocument();
    expect(screen.getByText(/全部不执行；每个调用收到 policy-error ToolResult/)).toBeInTheDocument();
    expect(screen.getAllByText(/Single \+ Sequential/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Batch \+ Parallel/).length).toBeGreaterThan(0);
    expect(screen.getByText(/上面的代表性指标也不是这次优化实验的结果/)).toBeInTheDocument();
    expect(screen.getByText(/TRAJECTORY · 模型交互轨迹/)).toBeInTheDocument();
    expect(screen.getByText(/TRACE · Runtime 运行记录/)).toBeInTheDocument();
    expect(screen.getByText(/Trace ≠ Trajectory/)).toBeInTheDocument();
    const runtimeLane = screen.getByText(/Runtime 自己记录 · RUNTIME OBSERVABILITY/).closest(".visibility-lane");
    const evaluatorLane = screen.getAllByText(/模型看不到 \/ 仅评测侧 · EVALUATOR ONLY/).at(-1)?.closest(".visibility-lane");
    expect(runtimeLane).toHaveTextContent("Trace：工具执行和 Runtime 生命周期事件");
    expect(evaluatorLane).not.toHaveTextContent("Trace：工具执行和 Runtime 生命周期事件");
    expect(evaluatorLane).toHaveTextContent("scorer ground truth");
  });

  it("renders the Oracle evaluator selector and model-visible source-evidence boundary without forbidden wording", async () => {
    stubSuccess(); renderRoute("/conditions/oracle");
    await screen.findByRole("heading", { name: "Selected Source Evidence / One Shot" });
    expect(screen.getByText("独立诊断条件 · 不属于 L1–L4")).toBeInTheDocument();
    expect(screen.getByText("required_evidence_ids")).toBeInTheDocument();
    expect(screen.getByText("选中的原始 Source Evidence")).toBeInTheDocument();
    expect(screen.getByText("只有原始证据片段通过")).toBeInTheDocument();
    expect(document.body.textContent).toContain("它不是 L5、不是 Product Runtime，也不是理论上界");
    expect(document.body.textContent).not.toContain("directly provides Required Evidence");
    expect(document.body.textContent).not.toContain("直接提供 Required Evidence");
    expect(document.body.textContent).not.toContain("Oracle is L5");
  });

  it("keeps editorial architecture visible but invents no formal metrics after a Condition API failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 503 })));
    renderRoute("/conditions/l1");
    expect(await screen.findByRole("heading", { name: "Full Context / One Shot" })).toBeInTheDocument();
    expect(screen.getByText("单次模型调用")).toBeInTheDocument();
    expect(await screen.findByText(/正式实验数据读取失败/)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("88.33%");
    expect(document.body.textContent).not.toContain("50.67%");
  });
});
