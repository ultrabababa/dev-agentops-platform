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
    expect(screen.getByText(/怎么评、怎么归因、怎么用实验证明改进有效/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Agent 评测与实验归因实践/ })).toBeInTheDocument();
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
    expect(screen.getByText(/结论正确、证据不全、报告格式有错/)).toBeInTheDocument();
  });

  it("keeps Oracle separate from the L1-L4 conditions", () => {
    window.history.replaceState({}, "", "/presentation?slide=5");
    render(<PresentationPage />);
    expect(screen.getByText("Oracle ≠ L5")).toBeInTheDocument();
    expect(screen.getByText(/L3 分类准确率/)).toBeInTheDocument();
    expect(screen.getByText(/这些|以上为代表性正式运行的观测数据/)).toBeInTheDocument();
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

  it("clamps navigation at the final slide", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "End" });
    expect(screen.getByText("09 / 09")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
  });
});
