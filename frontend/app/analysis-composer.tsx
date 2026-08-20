"use client";

import { useState } from "react";

import {
  ANALYSIS_CATEGORIES,
  AnalysisCategoryId,
  STRUCTURED_ASSESSMENT,
  resolveAnalysisSelection,
  validateAnalysisGoal,
} from "@/lib/analysis-prompts";

export interface AnalysisRequestOptions {
  document_ids: string[];
  top_k: number;
  similarity_threshold: number;
  temperature: number;
}

interface AnalysisComposerProps {
  documentId: string;
  isAnalyzing: boolean;
  analysisError: string | null;
  onAnalyze: (
    query: string,
    options: AnalysisRequestOptions,
  ) => Promise<unknown>;
}

export function AnalysisComposer({
  documentId,
  isAnalyzing,
  analysisError,
  onAnalyze,
}: AnalysisComposerProps) {
  const [goal, setGoal] = useState(STRUCTURED_ASSESSMENT.query);
  const [categoryId, setCategoryId] =
    useState<AnalysisCategoryId>("general");
  const [selectionId, setSelectionId] = useState(STRUCTURED_ASSESSMENT.id);
  const [validationError, setValidationError] = useState<string | null>(null);
  const category = ANALYSIS_CATEGORIES.find((item) => item.id === categoryId)!;
  const selectedLabel =
    selectionId === STRUCTURED_ASSESSMENT.id
      ? STRUCTURED_ASSESSMENT.label
      : category.suggestions.find((item) => item.id === selectionId)?.label ??
        "Custom";

  const submit = async () => {
    const validation = validateAnalysisGoal(goal);
    if (!validation.valid) {
      setValidationError(
        validation.error === "empty"
          ? "Enter an analysis goal."
          : "Keep the analysis goal within 2,000 characters.",
      );
      return;
    }
    setValidationError(null);
    await onAnalyze(validation.normalized, {
      document_ids: [documentId],
      top_k: 5,
      similarity_threshold: 0.3,
      temperature: 0.7,
    });
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
      className="analysis-composer"
    >
      <fieldset>
        <legend>Document category</legend>
        <div className="analysis-choice-grid analysis-category-grid">
          {ANALYSIS_CATEGORIES.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={categoryId === item.id}
              onClick={() => setCategoryId(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </fieldset>
      <fieldset>
        <legend>Suggested goals</legend>
        <div className="analysis-choice-grid">
          <button
            type="button"
            aria-pressed={selectionId === STRUCTURED_ASSESSMENT.id}
            onClick={() => {
              setGoal(STRUCTURED_ASSESSMENT.query);
              setSelectionId(STRUCTURED_ASSESSMENT.id);
            }}
          >
            {STRUCTURED_ASSESSMENT.label}
          </button>
          {category.suggestions.map((suggestion) => (
            <button
              key={suggestion.id}
              type="button"
              aria-pressed={selectionId === suggestion.id}
              onClick={() => {
                setGoal(suggestion.query);
                setSelectionId(suggestion.id);
              }}
            >
              {suggestion.label}
            </button>
          ))}
        </div>
      </fieldset>
      <div className="analysis-goal-heading">
        <label htmlFor="analysis-goal">Analysis goal</label>
        <span>{goal.length} / 2,000</span>
      </div>
      <textarea
        id="analysis-goal"
        value={goal}
        maxLength={2_001}
        aria-describedby={validationError ? "analysis-goal-error" : undefined}
        aria-invalid={validationError ? true : undefined}
        onChange={(event) => {
          const nextGoal = event.target.value;
          setGoal(nextGoal);
          setSelectionId(resolveAnalysisSelection(nextGoal, selectionId));
        }}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            void submit();
          }
        }}
        className="analysis-goal-input"
      />
      <p className="analysis-selection-status" aria-live="polite">
        Selected goal: {selectedLabel}
      </p>
      {validationError ? (
        <p id="analysis-goal-error" role="alert">
          {validationError}
        </p>
      ) : null}
      {analysisError ? <p role="alert">{analysisError}</p> : null}
      <button className="analysis-submit" type="submit" disabled={isAnalyzing}>
        {isAnalyzing ? "Analyzing" : "Run analysis"}
      </button>
    </form>
  );
}
