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
    expect(screen.getByText(/评测标准怎么设计、分数不理想时怎么分析原因/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Agent 评测与\s*实验归因实践/ })).toBeInTheDocument();
  });

  it("navigates with keyboard arrows and updates the shareable slide number", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByRole("heading", { name: "一条测试失败日志，Agent 到底要做什么？" })).toBeInTheDocument();
    expect(screen.getByText(/AssertionError: expected 5, got 6/)).toBeInTheDocument();
    expect(window.location.search).toContain("slide=2");
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(screen.getByText("01 / 09")).toBeInTheDocument();
  });

  it("shows and hides speaker notes", () => {
    render(<PresentationPage />);
    fireEvent.click(screen.getByRole("button", { name: "Notes" }));
    expect(screen.getByText(/讲者备注（按 N 关闭）/)).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "n" });
    expect(screen.queryByText(/讲者备注（按 N 关闭）/)).not.toBeInTheDocument();
  });

  it("explains scoring with a clearly labelled teaching example", () => {
    window.history.replaceState({}, "", "/presentation?slide=4");
    render(<PresentationPage />);
    expect(screen.getByText(/简化教学示例 · 非正式评测 Case/)).toBeInTheDocument();
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByText(/分类正确，不代表整个任务做好了/)).toBeInTheDocument();
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
    expect(screen.getByText("BADCASE A · 没找到")).toBeInTheDocument();
    expect(screen.getByText("BADCASE B · 找到了没用")).toBeInTheDocument();
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

  it("shows read-aloud cues on the slide itself without requiring the Notes overlay", () => {
    const { container } = render(<PresentationPage />);
    expect(container.querySelector(".pres-cover-desc")?.textContent).toMatch(/今天重点不是 Agent 怎么实现/);
    expect(container.querySelector(".pres-speaker-notes")).not.toBeInTheDocument();

    fireEvent.keyDown(window, { key: "ArrowRight" });
    const track = container.querySelector(".pres-talk-track");
    expect(track).toBeInTheDocument();
    expect(track?.textContent).toMatch(/只看日志，我们知道断言失败了/);
    expect(container.querySelector(".pres-speaker-notes")).not.toBeInTheDocument();
  });

  it("has a visible spoken cue on every content slide", () => {
    const { container } = render(<PresentationPage />);
    for (let slide = 2; slide <= 9; slide += 1) {
      fireEvent.keyDown(window, { key: "ArrowRight" });
      // Re-query the currently rendered page after each keyboard action.
      expect(container.querySelector(".pres-talk-track")).toBeInTheDocument();
    }
  });

  it("clamps navigation at the final slide", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "End" });
    expect(screen.getByText("09 / 09")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
  });
});
