import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AnalysisComposer } from "./analysis-composer";

describe("AnalysisComposer", () => {
  it("exposes analysis failures as an alert", () => {
    render(
      <AnalysisComposer
        documentId="document-123"
        isAnalyzing={false}
        analysisError="Analysis service timed out"
        onAnalyze={vi.fn()}
      />,
    );

    expect(screen.getByRole("alert").textContent).toContain("timed out");
  });

  it("submits the normalized editable goal for exactly the active document", async () => {
    const onAnalyze = vi.fn().mockResolvedValue(null);
    render(
      <AnalysisComposer
        documentId="document-123"
        isAnalyzing={false}
        analysisError={null}
        onAnalyze={onAnalyze}
      />,
    );

    const goal = screen.getByRole("textbox", { name: /analysis goal/i });
    await userEvent.clear(goal);
    await userEvent.type(goal, "  Compare termination risks.  ");
    await userEvent.keyboard("{Control>}{Enter}{/Control}");

    expect(onAnalyze).toHaveBeenCalledWith("Compare termination risks.", {
      document_ids: ["document-123"],
      top_k: 5,
      similarity_threshold: 0.3,
      temperature: 0.7,
    });
  });

  it("populates a category suggestion and marks manual edits as Custom", async () => {
    render(
      <AnalysisComposer
        documentId="document-123"
        isAnalyzing={false}
        analysisError={null}
        onAnalyze={vi.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Contract" }));
    await userEvent.click(screen.getByRole("button", { name: "Risk review" }));

    const goal = screen.getByRole("textbox", { name: /analysis goal/i });
    expect((goal as HTMLTextAreaElement).value).toContain("termination");
    expect(screen.getByText("Risk review")).toBeTruthy();

    await userEvent.type(goal, " Include governing law.");
    expect(screen.getByText(/selected goal: custom/i)).toBeTruthy();
  });

  it("associates invalid input with the goal and does not analyze", async () => {
    const onAnalyze = vi.fn();
    render(
      <AnalysisComposer
        documentId="document-123"
        isAnalyzing={false}
        analysisError={null}
        onAnalyze={onAnalyze}
      />,
    );

    const goal = screen.getByRole("textbox", { name: /analysis goal/i });
    await userEvent.clear(goal);
    await userEvent.type(goal, "   ");
    await userEvent.click(screen.getByRole("button", { name: /run analysis/i }));

    expect(goal.getAttribute("aria-invalid")).toBe("true");
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(onAnalyze).not.toHaveBeenCalled();
  });
});
