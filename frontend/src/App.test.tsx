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

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function stubSuccess() { const mock = vi.fn(async (input: string | URL | Request) => ({ ok: true, json: async () => responses[String(input)] })); vi.stubGlobal("fetch", mock); return mock; }

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
  it("states the Oracle exception to ordinary evaluator isolation", async () => {
    stubSuccess(); render(<App />); await screen.findByText("Evaluator Isolation");
    expect(screen.getByText(/Oracle 是显式标记的诊断干预例外/)).toBeInTheDocument();
    expect(document.body.textContent).not.toContain("Expected Answer / Required Evidence 不进入 Agent input");
  });
  it("does not invent metric values when the API fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 503 }))); render(<App />);
    expect(await screen.findByText("产品说明仍可阅读，实验事实暂不展示。")).toBeInTheDocument(); expect(screen.getByText(/HTTP 503/)).toBeInTheDocument(); expect(document.body.textContent).not.toContain("96.61%"); expect(document.body.textContent).not.toContain("877");
  });
});
