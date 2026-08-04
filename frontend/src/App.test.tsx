import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const responses: Record<string, object> = {
  "/api/health": { status: "ok" },
  "/api/version": { version: "0.1.0" },
  "/api/storage/status": {
    path: "/tmp/devagentops.db",
    exists: true,
    initialized: true,
    schema_version: "1",
    table_count: 2,
    tables: ["alembic_version", "devagentops_metadata"],
  },
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("DevAgentOps status dashboard", () => {
  it("renders health, version, and fixture SQLite status from the API", async () => {
    const fetchMock = vi.fn(async (input: string | URL | Request) => ({
      ok: true,
      json: async () => responses[String(input)],
    }));
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(await screen.findByText("API 在线")).toBeInTheDocument();
    expect(screen.getByText("v0.1.0")).toBeInTheDocument();
    expect(screen.getByText("已初始化")).toBeInTheDocument();
    expect(screen.getByText("devagentops_metadata")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith("/api/health");
    expect(fetchMock).toHaveBeenCalledWith("/api/version");
    expect(fetchMock).toHaveBeenCalledWith("/api/storage/status");
  });

  it("shows a useful error when the backend is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 503 })),
    );

    render(<App />);

    expect(await screen.findByText("无法读取后端状态")).toBeInTheDocument();
    expect(screen.getByText("HTTP 503")).toBeInTheDocument();
  });
});
