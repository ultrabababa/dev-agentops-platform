import type { Condition, Evolution, HomepageData, Overview } from "./types";

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
