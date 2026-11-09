import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { PresentationPage } from "./PresentationPage";

describe("PresentationPage", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/presentation");
  });

  it("starts with an evaluation-led cover and a nine-slide counter", () => {
    render(<PresentationPage />);
    expect(screen.getByText("01 / 09")).toBeInTheDocument();
    expect(screen.getByText(/评测基准 · 失败归因 · 实验验证 · 工程优化/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Agent 评测与\s*实验归因实践/ })).toBeInTheDocument();
  });

  it("navigates with keyboard arrows and updates the shareable slide number", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByRole("heading", { name: "CI 失败诊断：从错误现象到证据链" })).toBeInTheDocument();
    expect(screen.getByText(/AssertionError: expected 5, got 6/)).toBeInTheDocument();
    expect(window.location.search).toContain("slide=2");
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(screen.getByText("01 / 09")).toBeInTheDocument();
  });

  it("never exposes private presenter notes in the projected UI", () => {
    const { container } = render(<PresentationPage />);
    expect(screen.queryByRole("button", { name: "Notes" })).not.toBeInTheDocument();
    expect(container.querySelector(".pres-speaker-notes")).not.toBeInTheDocument();
    fireEvent.keyDown(window, { key: "n" });
    expect(container.querySelector(".pres-speaker-notes")).not.toBeInTheDocument();
  });

  it("shows a professional diagnostic conclusion, not a script cue", () => {
    window.history.replaceState({}, "", "/presentation?slide=2");
    render(<PresentationPage />);
    expect(screen.getByText(/仅识别「测试断言失败」属于故障分类/)).toBeInTheDocument();
    expect(screen.queryByText(/说出「断言失败」/)).not.toBeInTheDocument();
  });

  it("explains scoring with a clearly labelled teaching example", () => {
    window.history.replaceState({}, "", "/presentation?slide=4");
    render(<PresentationPage />);
    expect(screen.getByText(/简化教学示例 · 非正式评测 Case/)).toBeInTheDocument();
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByText(/分类正确 ≠ 证据充分 ≠ 输出合法/)).toBeInTheDocument();
  });

  it("shows all five conditions in one comparison table while identifying Oracle as diagnostic", () => {
    window.history.replaceState({}, "", "/presentation?slide=5");
    const { container } = render(<PresentationPage />);
    const rows = container.querySelectorAll(".pres-chart-table .pres-chart-row");
    expect(rows).toHaveLength(5);
    expect(Array.from(rows).map((row) => row.querySelector("strong")?.textContent)).toEqual([
      "L1", "L2", "L3", "L4", "Oracle",
    ]);
    expect(container.querySelector(".pres-oracle-row")).toBeInTheDocument();
    expect(container.querySelectorAll(".pres-metric-cell")).toHaveLength(10);
    expect(screen.getByText(/Oracle ≠ L5/)).toBeInTheDocument();
    expect(screen.getByText(/L3 分类准确率/)).toBeInTheDocument();
  });

  it("distinguishes missing acquisition from missing citation", () => {
    window.history.replaceState({}, "", "/presentation?slide=6");
    render(<PresentationPage />);
    expect(screen.getByText("BADCASE A · 获取缺失")).toBeInTheDocument();
    expect(screen.getByText("BADCASE B · 引用缺失")).toBeInTheDocument();
    expect(screen.getByText("76.56%")).toBeInTheDocument();
    expect(screen.getByText("66.18%")).toBeInTheDocument();
    expect(screen.getByText("50.67%")).toBeInTheDocument();
  });

  it("displays experimental controls before fixed-output replay metrics", () => {
    window.history.replaceState({}, "", "/presentation?slide=7");
    render(<PresentationPage />);
    expect(screen.getByText("只改一处")).toBeInTheDocument();
    expect(screen.getByText("重新验证")).toBeInTheDocument();
    expect(screen.getByText("12 → 0")).toBeInTheDocument();
  });

  it("labels the fixed-output replay as a distinct L4 experiment", () => {
    window.history.replaceState({}, "", "/presentation?slide=7");
    render(<PresentationPage />);
    expect(screen.getByText(/和上一页 L4 代表性正式运行不是同一组结果/)).toBeInTheDocument();
  });

  it("keeps projected slide text free of presenter-only phrasing", () => {
    const { container } = render(<PresentationPage />);
    const banned = /讲述主线|讲者备注|按 N|说出「断言失败」/;
    for (let i = 0; i < 9; i += 1) {
      expect(container.querySelector(".pres-slide")?.textContent).not.toMatch(banned);
      fireEvent.keyDown(window, { key: "ArrowRight" });
    }
  });

  it("clamps navigation at the final slide", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "End" });
    expect(screen.getByText("09 / 09")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
  });
});
