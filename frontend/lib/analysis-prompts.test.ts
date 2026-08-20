import { describe, expect, it } from "vitest";

import {
  ANALYSIS_CATEGORIES,
  MAX_ANALYSIS_GOAL_LENGTH,
  STRUCTURED_ASSESSMENT,
  resolveAnalysisSelection,
  normalizeAnalysisGoal,
  validateAnalysisGoal,
} from "./analysis-prompts";

describe("analysis prompt catalog", () => {
  it("exposes the five semantic document categories and an explicit preset", () => {
    expect(ANALYSIS_CATEGORIES.map((category) => category.id)).toEqual([
      "general",
      "resume",
      "contract",
      "report",
      "research-paper",
    ]);
    expect(STRUCTURED_ASSESSMENT.id).toBe("structured-assessment");
    expect(STRUCTURED_ASSESSMENT.query.length).toBeGreaterThan(0);
  });

  it("provides deterministic examples for every category", () => {
    for (const category of ANALYSIS_CATEGORIES) {
      expect(category.suggestions.length).toBeGreaterThanOrEqual(2);
      expect(category.suggestions.every((item) => item.query.trim().length > 0)).toBe(
        true,
      );
    }
  });

  it("normalizes valid goals and rejects empty or oversized goals", () => {
    expect(normalizeAnalysisGoal("  Compare the key risks.  ")).toBe(
      "Compare the key risks.",
    );
    expect(validateAnalysisGoal("   ").valid).toBe(false);
    expect(validateAnalysisGoal("x".repeat(MAX_ANALYSIS_GOAL_LENGTH + 1)).valid).toBe(
      false,
    );
    expect(validateAnalysisGoal("  Compare the key risks.  ")).toEqual({
      valid: true,
      normalized: "Compare the key risks.",
      error: null,
    });
  });

  it("keeps a selected suggestion until its populated goal is edited", () => {
    const suggestion = ANALYSIS_CATEGORIES[1].suggestions[0];
    expect(resolveAnalysisSelection(suggestion.query, suggestion.id)).toBe(
      suggestion.id,
    );
    expect(resolveAnalysisSelection(`${suggestion.query} Add context.`, suggestion.id)).toBe(
      "custom",
    );
  });
});
