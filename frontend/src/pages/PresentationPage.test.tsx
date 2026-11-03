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
    expect(screen.getByText(/不只回答「Agent 做对了吗」/)).toBeInTheDocument();
  });

  it("navigates with keyboard arrows and updates the shareable slide number", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByRole("heading", { name: "先明确：我们在评测怎样的 Agent？" })).toBeInTheDocument();
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

  it("clamps navigation at the final slide", () => {
    render(<PresentationPage />);
    fireEvent.keyDown(window, { key: "End" });
    expect(screen.getByText("09 / 09")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一页" })).toBeDisabled();
  });
});
