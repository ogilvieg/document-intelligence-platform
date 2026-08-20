export type AnalysisCategoryId =
  | "general"
  | "resume"
  | "contract"
  | "report"
  | "research-paper";

export interface AnalysisSuggestion {
  id: string;
  label: string;
  query: string;
}

export interface AnalysisCategory {
  id: AnalysisCategoryId;
  label: string;
  suggestions: readonly AnalysisSuggestion[];
}

export const MAX_ANALYSIS_GOAL_LENGTH = 2_000;

export type AnalysisGoalValidation =
  | { valid: true; normalized: string; error: null }
  | { valid: false; normalized: string; error: "empty" | "too-long" };

export function normalizeAnalysisGoal(goal: string): string {
  return goal.trim();
}

export function validateAnalysisGoal(goal: string): AnalysisGoalValidation {
  const normalized = normalizeAnalysisGoal(goal);
  if (normalized.length === 0) {
    return { valid: false, normalized, error: "empty" };
  }
  if (normalized.length > MAX_ANALYSIS_GOAL_LENGTH) {
    return { valid: false, normalized, error: "too-long" };
  }
  return { valid: true, normalized, error: null };
}

export const STRUCTURED_ASSESSMENT: AnalysisSuggestion = {
  id: "structured-assessment",
  label: "Structured Assessment",
  query:
    "Provide a comprehensive assessment including overall fit, strengths, gaps, risk factors, and recommended focus areas.",
};

export const ANALYSIS_CATEGORIES: readonly AnalysisCategory[] = [
  {
    id: "general",
    label: "General",
    suggestions: [
      {
        id: "general-summary",
        label: "Key takeaways",
        query: "Summarize the key claims, supporting evidence, and recommended next actions.",
      },
      {
        id: "general-critique",
        label: "Critical review",
        query: "Critically assess this document for clarity, completeness, assumptions, and risks.",
      },
    ],
  },
  {
    id: "resume",
    label: "Resume",
    suggestions: [
      {
        id: "resume-role-fit",
        label: "Role fit",
        query: "Assess this resume's strongest qualifications, gaps, and evidence of impact for a target role.",
      },
      {
        id: "resume-improvements",
        label: "Improvement opportunities",
        query: "Identify concrete ways to improve this resume's clarity, positioning, achievements, and credibility.",
      },
    ],
  },
  {
    id: "contract",
    label: "Contract",
    suggestions: [
      {
        id: "contract-obligations",
        label: "Obligations",
        query: "Identify the parties' material obligations, deadlines, dependencies, and remedies.",
      },
      {
        id: "contract-risk",
        label: "Risk review",
        query: "Assess termination, liability, indemnity, confidentiality, renewal, and dispute risks in this contract.",
      },
    ],
  },
  {
    id: "report",
    label: "Report",
    suggestions: [
      {
        id: "report-findings",
        label: "Findings",
        query: "Summarize the report's principal findings, evidence, limitations, and recommendations.",
      },
      {
        id: "report-decisions",
        label: "Decision brief",
        query: "Turn this report into a decision brief with options, tradeoffs, risks, and next actions.",
      },
    ],
  },
  {
    id: "research-paper",
    label: "Research Paper",
    suggestions: [
      {
        id: "research-methods",
        label: "Methods review",
        query: "Evaluate the research question, methodology, evidence, limitations, and reproducibility.",
      },
      {
        id: "research-contribution",
        label: "Contribution",
        query: "Explain this paper's central contribution, supporting results, assumptions, and open questions.",
      },
    ],
  },
];

export function resolveAnalysisSelection(
  goal: string,
  selectedId: string,
): string {
  const selected = [
    STRUCTURED_ASSESSMENT,
    ...ANALYSIS_CATEGORIES.flatMap((category) => category.suggestions),
  ].find((suggestion) => suggestion.id === selectedId);

  return selected && goal === selected.query ? selectedId : "custom";
}
