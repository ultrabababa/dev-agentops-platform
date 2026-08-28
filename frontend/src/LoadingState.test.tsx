import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  window.history.pushState({}, "", "/");
});

describe("homepage cold-start loading state", () => {
  it("shows real elapsed wait time and phased Render cold-start guidance without fake percentage progress", async () => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn(() => new Promise(() => undefined)));

    render(<App />);

    expect(screen.getByRole("heading", { name: "正在连接 Evaluation API" })).toBeInTheDocument();
    expect(screen.getByText("00:00")).toBeInTheDocument();
    expect(screen.getByRole("progressbar", { name: "Evaluation API 请求进行中" })).not.toHaveAttribute("aria-valuenow");

    await act(async () => { vi.advanceTimersByTime(8_000); });
    expect(screen.getByRole("heading", { name: "正在唤醒 Evaluation API" })).toBeInTheDocument();
    expect(screen.getByText("00:08")).toBeInTheDocument();
    expect(screen.getByText(/Render 免费实例可能正在从休眠中唤醒/)).toBeInTheDocument();

    await act(async () => { vi.advanceTimersByTime(42_000); });
    expect(screen.getByRole("heading", { name: "仍在等待 Evaluation API" })).toBeInTheDocument();
    expect(screen.getByText("00:50")).toBeInTheDocument();
    expect(screen.getByText(/当前请求仍在进行/)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/\b\d{1,3}%\b/);
  });
});
