import type { CaseMetadata, ComparisonPreset, Condition, Evolution, HomepageData, Overview, Run, RunCaseAggregate, RunComparison, Sample, TraceResponse, TrajectoryResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  constructor(path: string, status: number) {
    super(`无法读取 ${path}（HTTP ${status}）`);
    this.name = "ApiError";
  }
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new ApiError(path, response.status);
  return response.json() as Promise<T>;
}

export async function getHomepageData(): Promise<HomepageData> {
  const [overview, conditions, evolution] = await Promise.all([
    fetchJson<Overview>("/overview"),
    fetchJson<Condition[]>("/conditions"),
    fetchJson<Evolution>("/experiments/evolution"),
  ]);
  const requiredStages: Evolution["stages"][number]["stage"][] = [
    "baseline", "canonicalization", "runtime_optimization", "retrieval_attribution",
  ];
  const availableStages = new Set(evolution.stages.map((stage) => stage.stage));
  if (requiredStages.some((stage) => !availableStages.has(stage))) {
    throw new Error("实验演进 API 响应不完整");
  }
  if (conditions.length !== 5 || !conditions.some((condition) => condition.condition === "Oracle")) {
    throw new Error("Condition API 响应不完整");
  }
  return { overview, conditions, evolution };
}

export async function getConditions(): Promise<Condition[]> {
  const conditions = await fetchJson<Condition[]>("/conditions");
  if (conditions.length !== 5 || !conditions.some((condition) => condition.condition === "Oracle")) {
    throw new Error("Condition API 响应不完整");
  }
  return conditions;
}

export async function getCondition(condition: Condition["condition"]): Promise<Condition> {
  const detail = await fetchJson<Condition>(`/conditions/${condition.toLowerCase()}`);
  if (detail.condition !== condition) throw new Error(`Condition API 返回了错误身份：${detail.condition}`);
  return detail;
}

export async function getEvolution(): Promise<Evolution> {
  return fetchJson<Evolution>("/experiments/evolution");
}

export const getOverview = () => fetchJson<Overview>("/overview");
export const getRuns = () => fetchJson<Run[]>("/runs");
export const getComparisons = () => fetchJson<ComparisonPreset[]>("/comparisons");
export const compareRuns = (runA: string, runB: string) => fetchJson<RunComparison>(`/compare?run_a=${encodeURIComponent(runA)}&run_b=${encodeURIComponent(runB)}`);
export const getRun = (runId: string) => fetchJson<Run>(`/runs/${encodeURIComponent(runId)}`);
export const getRunCases = (runId: string) => fetchJson<RunCaseAggregate[]>(`/runs/${encodeURIComponent(runId)}/cases`);
export const getCases = () => fetchJson<CaseMetadata[]>("/cases");
export const getCase = (caseId: string) => fetchJson<CaseMetadata>(`/cases/${encodeURIComponent(caseId)}`);
export const getSample = (runId: string, caseId: string, repeat: number) => fetchJson<Sample>(`/runs/${encodeURIComponent(runId)}/cases/${encodeURIComponent(caseId)}/${repeat}`);
export const getTrajectory = (runId: string, caseId: string, repeat: number) => fetchJson<TrajectoryResponse>(`/runs/${encodeURIComponent(runId)}/cases/${encodeURIComponent(caseId)}/${repeat}/trajectory`);
export const getTrace = (runId: string, caseId: string, repeat: number) => fetchJson<TraceResponse>(`/runs/${encodeURIComponent(runId)}/cases/${encodeURIComponent(caseId)}/${repeat}/trace`);
