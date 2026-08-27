import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import type {
  CaseMetadata,
  Overview,
  Run,
  RunCaseAggregate,
  Sample,
  TraceResponse,
  TrajectoryResponse,
} from "./api/types";

const metricVector = {
  execution_coverage: 1,
  failure_type_exact_match: 0.75,
  report_evidence_hit_rate: 0.5,
  required_fields_completeness: 1,
  protocol_validity_rate: 1,
};

const run: Run = {
  run_id: "run-l4-representative-00000001",
  status: "completed_with_sample_failures",
  condition_id: "l4-minimax-m3-canonicalized-development-v1",
  runtime_variant: "self_built_react",
  suite_id: "triage-suite",
  suite_version: "1",
  started_at: "2026-08-20T08:00:00Z",
  completed_at: "2026-08-20T08:05:00Z",
  planned_samples: 60,
  scored_samples: 59,
  failed_samples: 1,
  catalog: {
    stage: "canonicalization",
    role: "fresh_canonicalized",
    condition_family: "L4",
    representative: true,
    comparison_group: "formal-v1",
  },
  manifest: {
    schema_version: "6",
    run_kind: "formal_evaluation",
    model_configuration: { provider: "minimax-official", model: "MiniMax-M3" },
    output_contract: { id: "structured-report", version: "1", schema_version: "1" },
    code_revision: "revision0123456789abcdef",
    git_dirty: false,
    suite_fingerprint: "suite0123456789abcdef",
    treatment_fingerprint: "treatment0123456789abcdef",
    condition_fingerprint: "condition0123456789abcdef",
    execution_policy_fingerprint: "policy0123456789abcdef",
    run_configuration_fingerprint: "config0123456789abcdef",
    evaluation_method: "formal-fixed-100",
    structured_report_schema_version: "1",
  },
  manifest_sha256: "manifest0123456789abcdef",
  suite_aggregate: {
    run_id: "run-l4-representative-00000001",
    requested_sample_count: 60,
    scored_sample_count: 59,
    execution_failed_sample_count: 1,
    execution_coverage: 0.9833,
    protocol_validity_rate: 1,
    quality_status: "complete",
    formal_metric_vector: metricVector,
  },
  failure_type_aggregates: [],
};

const runCase: RunCaseAggregate = {
  run_id: run.run_id,
  case_id: "case-public-001",
  case_sequence: 1,
  case_fingerprint: "case0123456789abcdef",
  failure_type: "lint_or_type_failure",
  suite_weight: 1,
  requested_sample_count: 3,
  scored_sample_count: 2,
  execution_failed_sample_count: 1,
  execution_coverage: 0.6667,
  protocol_validity_rate: 1,
  quality_status: "partial",
  formal_metric_vector: metricVector,
  scored_repeat_indices_json: "[0,1]",
  failed_repeat_indices_json: "[2]",
};

const publicCase: CaseMetadata = {
  case_id: "case-public-001",
  failure_type: "lint_or_type_failure",
  weight: 1,
  case_schema_version: "2",
  case_fingerprint: "case0123456789abcdef",
  provenance: {
    source_type: "public_repository",
    source_url_or_construction_note: "Public permitted source",
    license_or_permission: "Apache-2.0",
  },
  sanitization: { status: "reviewed_sanitized" },
};

const overview: Overview = {
  benchmark: { case_count: 20, repeats_per_case: 3, samples_per_formal_run: 60, failure_type_count: 5 },
  representative_conditions: {
    L1: { run_id: "l1", runtime_variant: "full_context_one_shot" },
    L2: { run_id: "l2", runtime_variant: "fixed_model_workflow" },
    L3: { run_id: "l3", runtime_variant: "static_retrieval" },
    L4: { run_id: run.run_id, runtime_variant: "self_built_react" },
    Oracle: { run_id: "oracle", runtime_variant: "model_one_shot" },
  },
  experiment_evolution_endpoint: "/api/experiments/evolution",
  featured_findings: {
    canonicalization: {
      artifact_id: "canonicalization",
      authority: "fixed_output_offline_replay",
      l4: {
        protocol_validity_before: 0,
        protocol_validity_after: 1,
        unknown_evidence_ids_before: 2,
        unknown_evidence_ids_after: 0,
        failure_type_exact_match_before: 0.5,
        failure_type_exact_match_after: 0.75,
      },
    },
    runtime_optimization: {
      artifact_id: "runtime",
      authority: "formal_trace_metrics_and_replication",
      run_ids: ["before", "after"],
      model_decisions: [4, 2],
      executed_tool_calls: [3, 1],
      run_wall_seconds: [100, 50],
      interpretation: "bounded",
    },
    retrieval_attribution: {
      artifact_id: "retrieval",
      authority: "formal_l3_result_snapshot",
      run_id: "l3",
      retrieval_acquisition_recall: 0.8,
      acquired_required_evidence_utilization: 0.5,
      report_evidence_hit_rate: 0.5,
      report_evidence_improvement_over_l1_l2: "not_demonstrated",
    },
  },
};

const sample: Sample = {
  identity: { run_id: run.run_id, case_id: publicCase.case_id, repeat_index: 1 },
  outcome: {
    sample_sequence: 2,
    suite_weight: 1,
    evaluation_failure_type: "lint_or_type_failure",
    status: "scored",
    failure_code: null,
    failure_stage: null,
    failure_message: null,
  },
  report: {
    schema_version: "1",
    case_id: publicCase.case_id,
    classification_status: "classified",
    failure_type: "lint_or_type_failure",
    summary: "工具返回了明确的权限错误。",
    root_cause: "调用缺少所需权限。",
    recommended_action: "修正权限后重试。",
    confidence: 0.9,
    evidence_references: [{ evidence_id: "EV-PUBLIC-02" }, { evidence_id: "EV-PUBLIC-01" }],
  },
  validation: { valid: true, errors: [] },
  score: {
    failure_type_exact_match: 1,
    report_evidence_hit_rate: 0.5,
    required_fields_completeness: 1,
  },
  diagnostics: { expected_answer: "MUST NEVER RENDER", required_evidence_targets: ["HIDDEN-EV"] },
  trajectory_available: true,
  trace_available: true,
};

const trajectory: TrajectoryResponse = {
  run_id: run.run_id,
  case_id: publicCase.case_id,
  repeat_index: 1,
  messages: [
    {
      message_index: 0,
      role: "user",
      visible_content: "请检查公开错误证据。",
      tool_calls: [],
      tool_name: null,
      tool_call_id: null,
      is_error: null,
      stop_reason: null,
      raw_stop_reason: null,
      response_model: null,
      usage: null,
    },
    {
      message_index: 1,
      role: "assistant",
      visible_content: "我会读取日志。",
      tool_calls: [{ tool_call_id: "call-1", tool_name: "read_log", arguments: { path: "public.log" } }],
      tool_name: null,
      tool_call_id: null,
      is_error: null,
      stop_reason: "tool_calls",
      raw_stop_reason: "tool_calls",
      response_model: "Qwen/Qwen3.5-4B",
      usage: { input_tokens: 10, output_tokens: 5, total_tokens: 15 },
    },
    {
      message_index: 2,
      role: "tool_result",
      visible_content: "permission denied",
      tool_calls: [],
      tool_name: "read_log",
      tool_call_id: "call-1",
      is_error: true,
      stop_reason: null,
      raw_stop_reason: null,
      response_model: null,
      usage: null,
    },
  ],
};

const trace: TraceResponse = {
  run_id: run.run_id,
  case_id: publicCase.case_id,
  repeat_index: 1,
  events: [
    {
      sequence: 4,
      event_type: "tool_call_completed",
      occurred_at: "2026-08-20T08:01:02Z",
      payload: { step: 1, latency_ms: 42, status: "error", tool_name: "read_log", quality_metrics: { truncated: false } },
    },
  ],
};

type FixtureMap = Record<string, unknown>;

function defaultResponses(): FixtureMap {
  const samplePath = `/api/runs/${run.run_id}/cases/${publicCase.case_id}/1`;
  return {
    "/api/runs": [run],
    [`/api/runs/${run.run_id}`]: run,
    [`/api/runs/${run.run_id}/cases`]: [runCase],
    "/api/cases": [publicCase],
    [`/api/cases/${publicCase.case_id}`]: {
      ...publicCase,
      expected_answer: "MUST NEVER RENDER",
      required_evidence: ["HIDDEN-EV"],
    },
    "/api/overview": overview,
    [samplePath]: sample,
    [`${samplePath}/trajectory`]: trajectory,
    [`${samplePath}/trace`]: trace,
  };
}

function stubApi(overrides: FixtureMap = {}, failures: ReadonlySet<string> = new Set()) {
  const responses = { ...defaultResponses(), ...overrides };
  const mock = vi.fn(async (input: string | URL | Request) => {
    const path = String(input);
    if (failures.has(path) || !(path in responses)) {
      return { ok: false, status: failures.has(path) ? 503 : 404, json: async () => ({}) };
    }
    return { ok: true, status: 200, json: async () => responses[path] };
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

function renderRoute(path: string) {
  window.history.pushState({}, "", path);
  return render(<App />);
}

function sampleRoute(repeat = 1) {
  return `/runs/${run.run_id}/cases/${publicCase.case_id}/${repeat}`;
}

async function openTab(name: "Evidence" | "Trajectory" | "Trace" | "Provenance") {
  fireEvent.click(await screen.findByRole("tab", { name }));
  return screen.findByRole("tabpanel");
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.history.pushState({}, "", "/");
});

describe("Phase 2C public Evaluation Explorer", () => {
  it("renders public Runs, representative state, honest completion, and exact formal metric terms", async () => {
    stubApi();
    renderRoute("/runs");

    expect(await screen.findByRole("heading", { name: "正式实验 Runs" })).toBeInTheDocument();
    expect(screen.getByText("Self-built ReAct Runtime")).toBeInTheDocument();
    expect(screen.getByText("Representative")).toBeInTheDocument();
    expect(screen.getByText("Run completed")).toBeInTheDocument();
    expect(screen.getByText("sample failures: 1")).toBeInTheDocument();
    for (const term of ["Execution Coverage", "Failure Type Exact Match", "Report Evidence Hit Rate", "Required Fields Completeness", "Protocol Validity"]) {
      expect(screen.getByText(term)).toBeInTheDocument();
    }
    expect(screen.queryByText(/Diagnosis Accuracy|Root Cause Accuracy/i)).not.toBeInTheDocument();
  });

  it("renders Run metrics, public provenance, and Case aggregates with derived repeats", async () => {
    const fetchMock = stubApi();
    renderRoute(`/runs/${run.run_id}`);

    expect(await screen.findByRole("heading", { name: "正式评测结果" })).toBeInTheDocument();
    expect(screen.getByText("Provider / Model")).toBeInTheDocument();
    expect(screen.getByText("minimax-official / MiniMax-M3")).toBeInTheDocument();
    expect(screen.getByText("Suite fingerprint")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Frozen Cases" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: publicCase.case_id })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Repeat [012]/ })).toHaveLength(3);
    expect(fetchMock).toHaveBeenCalledWith(`/api/runs/${run.run_id}/cases`);
  });

  it("renders frozen Case catalog metadata", async () => {
    stubApi();
    renderRoute("/cases");

    expect(await screen.findByText("20 个正式实验共享的 frozen benchmark 输入。这里展示输入身份、failure type 与公开 provenance，不展示模型输出或隐藏评分目标。")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: publicCase.case_id })).toBeInTheDocument();
    expect(screen.getAllByText("lint_or_type_failure")).toHaveLength(2);
    expect(screen.getByText("Schema v2")).toBeInTheDocument();
    expect(screen.getByText("reviewed / sanitized")).toHaveAttribute("title", "reviewed_sanitized");
  });

  it("renders Case provenance and cross-Run entry without hidden evaluator material", async () => {
    stubApi();
    renderRoute(`/cases/${publicCase.case_id}`);

    expect(await screen.findByRole("heading", { name: "Case" })).toBeInTheDocument();
    expect(screen.getAllByText(publicCase.case_id).length).toBeGreaterThan(0);
    expect(screen.getByText("Public permitted source")).toBeInTheDocument();
    expect(screen.getByText("Apache-2.0")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "在不同 Run 中查看这个 Case" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2" })).toBeInTheDocument();
    expect(screen.queryByText(/MUST NEVER RENDER|Expected Answer|HIDDEN-EV/i)).not.toBeInTheDocument();
  });

  it("renders Structured Report and ordered cited Evidence without diagnostics", async () => {
    stubApi();
    renderRoute(sampleRoute());

    expect(await screen.findByRole("heading", { name: "Sample · Repeat 1" })).toBeInTheDocument();
    expect(screen.getAllByText(publicCase.case_id).length).toBeGreaterThan(0);
    expect(screen.getByText("工具返回了明确的权限错误。")).toBeInTheDocument();
    expect(screen.getByText("调用缺少所需权限。")).toBeInTheDocument();
    expect(screen.getByText("修正权限后重试。")).toBeInTheDocument();
    expect(screen.getByText("Valid")).toBeInTheDocument();

    const panel = await openTab("Evidence");
    const evidenceIds = within(panel).getAllByText(/^EV-PUBLIC-/).map((node) => node.textContent);
    expect(evidenceIds).toEqual(["EV-PUBLIC-02", "EV-PUBLIC-01"]);
    expect(within(panel).getByText("Failure Type Exact Match")).toBeInTheDocument();
    expect(screen.queryByText(/MUST NEVER RENDER|HIDDEN-EV|Expected Answer/i)).not.toBeInTheDocument();
  });

  it("lazy-loads and preserves ordered Trajectory messages, ToolCall, and ToolResult", async () => {
    const fetchMock = stubApi();
    renderRoute(sampleRoute());
    await screen.findByRole("heading", { name: "Sample · Repeat 1" });
    expect(fetchMock).not.toHaveBeenCalledWith(`/api${sampleRoute()}/trajectory`);

    const panel = await openTab("Trajectory");
    await within(panel).findByText("模型实际看到的交互历史");
    const messages = within(panel).getAllByRole("listitem");
    expect(messages).toHaveLength(3);
    expect(messages[0]).toHaveTextContent("请检查公开错误证据。");
    expect(messages[1]).toHaveTextContent("TOOL CALL");
    expect(messages[1]).toHaveTextContent("read_log");
    expect(messages[2]).toHaveTextContent("TOOL RESULT");
    expect(messages[2]).toHaveTextContent("permission denied");
    expect(panel).not.toHaveTextContent(/chain of thought|reasoning|thinking/i);
  });

  it("presents unavailable Trajectory as a valid empty state, not an API error", async () => {
    const trajectoryPath = `/api${sampleRoute()}/trajectory`;
    stubApi({ [trajectoryPath]: { ...trajectory, messages: [] } });
    renderRoute(sampleRoute());

    const panel = await openTab("Trajectory");
    expect(await within(panel).findByRole("heading", { name: "此 Run 没有可公开展示的 Trajectory。" })).toBeInTheDocument();
    expect(within(panel).getByText(/有效的历史数据状态，不是 API 错误/)).toBeInTheDocument();
    expect(within(panel).queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders a chronological Trace timeline and explicitly distinguishes it from Trajectory", async () => {
    stubApi();
    renderRoute(sampleRoute());

    const panel = await openTab("Trace");
    expect(await within(panel).findByText("Runtime 另外记录的执行事件，不是对话")).toBeInTheDocument();
    expect(within(panel).getByText("tool_call_completed")).toBeInTheDocument();
    expect(within(panel).getByText("004")).toBeInTheDocument();
    expect(within(panel).getByText("latency_ms")).toBeInTheDocument();
    expect(within(panel).getByRole("button", { name: "更多公开 event fields" })).toHaveAttribute("aria-expanded", "false");
    expect(within(panel).queryByText("模型实际看到的交互历史")).not.toBeInTheDocument();
  });

  it("renders Sample provenance fingerprints and code revision as accessible full values", async () => {
    stubApi();
    renderRoute(sampleRoute());

    const panel = await openTab("Provenance");
    await within(panel).findByRole("heading", { name: "这份报告来自哪一套输入、Runtime 和评分合同？" });
    for (const label of ["Suite fingerprint", "Condition fingerprint", "Treatment fingerprint", "Execution policy", "Run configuration", "Code revision", "Manifest SHA"]) {
      expect(within(panel).getByText(label)).toBeInTheDocument();
    }
    expect(within(panel).getByText(`完整值：${run.manifest.code_revision}`)).toBeInTheDocument();
    expect(within(panel).queryByText(/Expected Answer|HIDDEN-EV/i)).not.toBeInTheDocument();
  });

  it("handles an execution-failed Sample with no report honestly", async () => {
    const failedSample: Sample = {
      ...sample,
      outcome: {
        ...sample.outcome,
        status: "execution_failed",
        failure_code: "provider_timeout",
        failure_stage: "model_request",
        failure_message: "The request timed out.",
      },
      report: null,
      validation: null,
      score: null,
      trajectory_available: false,
    };
    stubApi({ [`/api${sampleRoute()}`]: failedSample });
    renderRoute(sampleRoute());

    expect(await screen.findByRole("heading", { name: "这次 Sample 没有生成 Structured Report。" })).toBeInTheDocument();
    expect(screen.getByText(/执行在 model_request 失败/)).toBeInTheDocument();
    expect(screen.getByText("provider_timeout")).toBeInTheDocument();
    expect(screen.queryByText("0.00%")).not.toBeInTheDocument();
  });

  it("never invents formal metrics when the Runs API fails", async () => {
    stubApi({}, new Set(["/api/runs"]));
    renderRoute("/runs");

    expect(await screen.findByRole("alert")).toHaveTextContent("公开实验数据读取失败");
    expect(screen.getByText(/不会用静态值或推测结果替代 API 响应/)).toBeInTheDocument();
    expect(screen.queryByText("Execution Coverage")).not.toBeInTheDocument();
    expect(screen.queryByText(/Diagnosis Accuracy|Root Cause Accuracy/i)).not.toBeInTheDocument();
  });

  it("supports keyboard navigation across the five tabs", async () => {
    stubApi();
    renderRoute(sampleRoute());
    const structured = await screen.findByRole("tab", { name: "Structured Report" });
    structured.focus();

    fireEvent.keyDown(structured, { key: "ArrowRight" });
    const evidence = screen.getByRole("tab", { name: "Evidence" });
    expect(evidence).toHaveFocus();
    expect(evidence).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(evidence, { key: "End" });
    const provenance = screen.getByRole("tab", { name: "Provenance" });
    expect(provenance).toHaveFocus();
    expect(provenance).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(provenance, { key: "Home" });
    expect(structured).toHaveFocus();
    expect(structured).toHaveAttribute("aria-selected", "true");
  });
});
