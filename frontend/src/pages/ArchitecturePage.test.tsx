import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ArchitecturePage } from "./ArchitecturePage";

describe("ArchitecturePage", () => {
  it("renders the three frozen architecture views and switches the interactive viewer", () => {
    render(<ArchitecturePage />);

    expect(screen.getByRole("heading", { name: "从系统边界到 Agent loop，三层看清 DevAgentOps。" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /系统由什么组成/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTitle("High-Level System Architecture interactive diagram")).toHaveAttribute(
      "src",
      "/architecture-assets/system.html?embed=1&theme=light",
    );

    fireEvent.click(screen.getByRole("tab", { name: /Agent Runtime 内部怎么循环/ }));

    expect(screen.getByRole("tab", { name: /Agent Runtime 内部怎么循环/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTitle("L4 ReAct Runtime Sequence interactive diagram")).toHaveAttribute(
      "src",
      "/architecture-assets/l4-runtime.html?embed=1&theme=light",
    );
    expect(screen.getByRole("link", { name: "打开完整交互图 ↗" })).toHaveAttribute(
      "href",
      "/architecture-assets/l4-runtime.html",
    );
  });
});
