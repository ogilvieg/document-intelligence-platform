# Responsive and Accessible Landing Experience - Implementation Plan

Status: Ready for implementation
Date: 2026-08-20
Issue: https://github.com/ogilvieg/document-intelligence-platform/issues/9

## Goal

Make the complete DocSage landing workflow readable and operable across 320 px,
390 px, 768 px, and desktop viewports, including keyboard and screen-reader use,
without losing the established paper-and-ink visual design.

## Current State and Evidence

- `frontend/app/page.tsx::Home` constrains the main content to 860 px, but the
  header, uploader, indexed statistics, footer, and several result layouts use
  fixed inline flex/grid rules that cannot respond through CSS breakpoints.
- `frontend/app/globals.css` stacks `.intro-steps` and analysis choices below
  520 px, but there are no shared responsive rules for retrieval statistics,
  retrieval details, result quadrants, citations, or indexed-document metadata.
- The upload surface is a clickable `div` that programmatically clicks a hidden
  file input. Drag/drop works, but the visible surface is not a native keyboard
  control and the input has no accessible name.
- The page has one `h1`; major upload, indexed-document, analysis, result, and
  citation labels are `span` or `p` elements, weakening document navigation.
- Health and goal-selection state use live regions, while uploading, indexing,
  analyzing, completion, and async errors do not share a coherent announcement
  model. Upload and analysis errors use visual presentation without consistently
  exposing alert semantics.
- `blink`, `spin`, `scanH`, `pulseAmber`, and `fadeInUp` animations have no
  `prefers-reduced-motion` override. Focus rules cover only some controls, and
  several inline buttons have small targets or no visible focus styling.
- `frontend/app/page.test.tsx`, `frontend/app/analysis-panel.test.tsx`, and
  `frontend/app/analysis-composer.test.tsx` provide Vitest/Testing Library
  coverage. Repository-native validation is `npm test`, `npx tsc --noEmit`,
  `npm run lint`, and `npm run build` from `frontend/`.

## Confirmed Decisions

1. Preserve drag-and-drop while keeping the native file input visible and
   keyboard-focusable inside the drop surface; do not substitute a label or a
   `display: none` input for the actual focusable file-selection control.
2. Move responsive ownership into descriptive CSS classes rather than viewport
   checks in React so server/client markup stays stable and media queries can
   cover all requested widths.
3. Use native headings and controls first; add ARIA only for names,
   relationships, current async state, and alerts not conveyed natively.
4. Keep all work frontend-only; no API, persisted-data, or deployment contract
   changes are required.

## Assumptions and Open Questions

- Assumption: existing visual colors are the intended palette; implementation
  may strengthen muted/disabled foreground tokens where contrast inspection
  shows risk, without redesigning the palette.
- Assumption: persistent empty/indexed/result states can be reached with local
  services or the existing synthetic sample; transient/error states remain
  automated component-test evidence unless a documented browser fixture is
  added without production code or a new runtime dependency.
- Open question: automated DOM tests cannot prove pixel overflow or computed
  contrast, so those acceptance points require rendered browser evidence.

## Requirements

| ID | Requirement |
| --- | --- |
| REQ-001 | The complete workflow has no horizontal scrolling and retains readable, non-collapsed content at 320 px, 390 px, 768 px, and desktop widths. |
| REQ-002 | The explainer, indexed-document statistics, retrieval statistics/details, result quadrants, citations, header, uploader, and footer reflow through explicit responsive structural rules. |
| REQ-003 | File selection and clearing, query entry and analysis, and retrieval-detail expansion are keyboard operable with meaningful accessible names and visible focus. |
| REQ-004 | Major page and result sections expose a logical native heading structure without changing their visual hierarchy. |
| REQ-005 | Screen-reader users receive meaningful polite status announcements for the truthful combined upload-and-index request, the resulting indexed state, analyzing, and completion, plus assertive alerts for upload and analysis failures. |
| REQ-006 | Interactive targets are at least 44 by 44 CSS pixels unless a documented inline-text exception applies; normal text reaches 4.5:1 contrast, large text and UI/focus indicators reach 3:1, and state is not communicated by color alone. |
| REQ-007 | Blinking, scanning, spinning, entrance, pulse, and progress animations are disabled or reduced when the user prefers reduced motion. |
| REQ-008 | Automated accessibility/interaction coverage and manual desktop/mobile screenshots plus a keyboard-only pass provide release evidence. |

## Non-Goals

- Changing upload, indexing, retrieval, or analysis API behavior.
- Replacing the established typography, paper texture, or information content.
- Adding a component library, CSS-in-JS dependency, automated visual-regression
  service, or full WCAG audit tooling.

## Constraints and Invariants

- Existing pointer drag/drop and click-based file selection must continue to
  work while keyboard semantics improve.
- Responsive changes must not hide workflow content or require horizontal
  scrolling to reach controls or evidence.
- Live regions must avoid duplicate or constantly repeated announcements.
- No secrets, database migrations, backend rollout, or compatibility migration
  is involved.

## Target Architecture or Change Map

`Home` and `AnalysisPanel` retain state and rendering ownership while their
major layout surfaces gain semantic class names. `globals.css` owns viewport,
focus, touch-target, contrast, overflow, and reduced-motion behavior. Focused
Testing Library tests validate native roles, names, keyboard paths, headings,
and live-region state; browser inspection validates layout and visual states.

## Module Breakdown

| Module or Work Package | Responsibility | Owning Surfaces | Interfaces and Dependencies | Independent Validation |
| --- | --- | --- | --- | --- |
| Responsive layout | Reflow every fixed multi-column or wide flex surface without overflow. | `frontend/app/page.tsx`, `frontend/app/globals.css` | Existing React output and CSS media queries | Structural class tests plus screenshots at four widths and scroll-width checks |
| Upload interaction | Expose native file selection, drag/drop, clear, focus, and adequate target behavior. | `frontend/app/page.tsx`, `frontend/app/page.test.tsx` | Focusable file input and upload/reset hooks | DOM upload/drop/clear tests plus real-browser Tab and picker-activation check |
| Semantic workflow | Supply headings, accessible names, statuses, and errors across async states. | `frontend/app/page.tsx`, `frontend/app/analysis-composer.tsx`, focused tests | Existing hook state and result data | Role/name/heading/live-region component tests |
| Inclusive visual states | Apply consistent focus, legibility, touch-target, and reduced-motion rules. | `frontend/app/globals.css` | CSS custom properties and semantic classes | Source assertions plus rendered focus/motion/contrast inspection |
| Integrated verification | Exercise the complete workflow at target widths and by keyboard. | Frontend validation commands and browser session | All preceding work packages | Tests, typecheck, lint baseline, build, screenshots, keyboard pass |

## Implementation Phases

### Phase 1 - Responsive and Operable Foundations

**P1.1 [REQ-001, REQ-002] Establish responsive ownership for all fixed landing and result layouts.**

- Primary module or work package: Responsive layout.
- Add descriptive classes to the header, content shell, explainer, uploader,
  indexed statistics, retrieval statistics/details, result quadrants,
  citations, and footer; define desktop/tablet/mobile layout transitions and
  intrinsic overflow safeguards in `globals.css`.

**P1.2 [REQ-003, REQ-006] Replace the pointer-only upload trigger and normalize interactive targets.**

- Primary module or work package: Upload interaction.
- Keep the native file input visible and focusable within a non-click-simulating
  drag/drop surface, preserve upload/drop/reset behavior, and give
  clear/expand/dismiss controls names, focus treatment, and 44 px targets.

### Phase 2 - Semantic and Announced Workflow

**P2.1 [REQ-004] Introduce a logical native heading hierarchy for workflow and result regions.**

- Primary module or work package: Semantic workflow.
- Refactor reusable section labels and result labels to native headings while
  retaining their presentational typography through CSS/reset styles. The
  expected outline is one benefit `h1`; `h2` headings for Ingest, Indexed
  document (when present), Analysis, and the result Analysis region; and `h3`
  headings within results for Retrieval pipeline, Retrieved chunks, Overall
  assessment, Strengths, Gaps, Risk factors, Focus areas, and Source citations
  when their corresponding content renders, in DOM reading order.

**P2.2 [REQ-005] Announce asynchronous progress, completion, and failure states.**

- Primary module or work package: Semantic workflow.
- Add one coherent status region that truthfully calls the current single hook
  operation "uploading and indexing," then announces indexed, analyzing, and
  completed states; expose errors as alerts and avoid unchanged instructions.

### Phase 3 - Inclusive Visual Behavior

**P3.1 [REQ-006, REQ-007] Strengthen focus, target, contrast, and reduced-motion behavior.**

- Primary module or work package: Inclusive visual states.
- Centralize `:focus-visible` treatment and 44 by 44 px targets (documenting
  any inline-text exception), then verify foreground/background pairs against
  the 4.5:1 text and 3:1 large-text/UI thresholds. Add a
  `prefers-reduced-motion: reduce` override for all named animations and
  nonessential transitions.

### Phase 4 - Integrated Delivery

**P4.1 [REQ-001, REQ-003, REQ-005, REQ-006, REQ-007, REQ-008] Validate automated and rendered acceptance scenarios with rollback readiness.**

- Primary module or work package: Integrated verification.
- Run source checks; capture empty and populated/result screenshots at 320,
  390, 768, and 1440 px where the state is deterministically reachable; record
  scroll, contrast, target, focus, and motion measurements in
  `docs/implementation-notes/issue-9-accessibility-verification.md`; store
  screenshots under `docs/implementation-notes/issue-9-screenshots/`; and
  perform the complete keyboard-only workflow including native file-picker
  activation and retrieval expansion.

## Task Breakdown

### Phase 1 Tasks

- [x] T001 [Plan:P1.1] Add a failing table-driven structural test for responsive ownership of the header, content shell, explainer, uploader, and footer; implement their layout classes and mobile/tablet rules and verify green.
- [x] T002 [Plan:P1.1] Add a failing table-driven structural test for indexed statistics, retrieval statistics/details, result quadrants, and citations; implement their intrinsic/responsive classes and verify green.
- [x] T003 [Plan:P1.2] Add a failing accessible-name/file-upload test; replace the click-simulating upload `div` and hidden input with a visible focusable native file input inside the drop surface while preserving drag/drop and verify green.
- [x] T004 [Plan:P1.2] Add failing keyboard/name/expanded-state assertions for clear, intro dismissal, and retrieval expansion; normalize native button labels, `aria-expanded`/control relationships, and target classes and verify green.

### Phase 2 Tasks

- [x] T005 [Plan:P2.1] Add a failing level/name/DOM-order test for the explicit h1/h2/h3 outline in empty and populated result states; implement native headings and verify green.
- [x] T006 [Plan:P2.2] Add failing combined upload-and-index/indexed and upload-error announcement tests; implement the smallest truthful live status/alert behavior and verify green.
- [x] T007 [Plan:P2.2] Add failing analyzing/completion and analysis-error announcement tests; integrate composer/result states without duplicate announcements and verify green.

### Phase 3 Tasks

- [x] T008 [Plan:P3.1] Add a failing focus/target contract for every interactive control class; implement shared focus-visible styling and 44 by 44 px targets, documenting inline project-resource links as the exception because their adjacent whitespace enlarges the usable line target.
- [x] T009 [Plan:P3.1] Measure current foreground/background and UI-state contrast pairs, record failing evidence, adjust tokens/usages, and record computed ratios meeting 4.5:1 text and 3:1 large-text/UI thresholds.
- [x] T010 [Plan:P3.1] Add a failing reduced-motion stylesheet contract covering blink, scan, spin, pulse, entrance, confidence progress, and other nonessential transitions; implement the media-query override and verify it in browser emulation.

### Phase 4 Tasks

- [x] T011 [Plan:P4.1] Run focused tests, the full frontend suite, TypeScript, lint comparison, and the production build; resolve regressions and record any pre-existing lint baseline.
- [x] T012 [Plan:P4.1] Capture empty and populated/result screenshots at 320, 390, 768, and 1440 px where deterministically reachable, verify `scrollWidth <= clientWidth`, and record screenshots and measurements in the named issue-9 evidence paths.
- [ ] T013 [Plan:P4.1] Complete and record a keyboard-only pass for native file-picker activation, clearing, query editing, analysis, and retrieval expansion; inspect focus, announcements, target sizes, contrast ratios, and reduced-motion emulation, filing any consciously deferred WCAG gap as a follow-up issue.

## Commit Checkpoints

| After Tasks | Commit Scope | Required Validation |
| --- | --- | --- |
| T001-T004 | Responsive layout and operable upload/controls | Focused homepage and analysis-panel tests plus TypeScript |
| T005-T007 | Semantic heading and async announcement model | Focused homepage, composer, and panel tests plus full frontend tests |
| T008-T011 | Inclusive CSS behavior and source integration | Focus/target and motion contracts, recorded contrast ratios, full tests, typecheck, lint comparison, and build |
| T012-T013 | Rendered and keyboard release evidence | Eight-state/viewport screenshots where reachable, scroll measurements, keyboard/focus/status/target/contrast/motion pass |

## Validation Matrix

| Requirement | Scenario | Validation | Expected Evidence |
| --- | --- | --- | --- |
| REQ-001 | Landing, indexed, composing, and result states at four target widths | Browser screenshots and `scrollWidth <= clientWidth` checks | No horizontal scroll; content remains readable and reachable |
| REQ-002 | Every named fixed layout reaches tablet/mobile breakpoints | Structural tests and rendered inspection | Classes exist and computed grids/flex rows stack or wrap appropriately |
| REQ-003 | Keyboard-only file choice, clear, query entry/submit, and details expansion | Testing Library plus manual keyboard pass | Native controls have meaningful names, visible focus, and perform each action |
| REQ-004 | Screen-reader heading navigation | Role/level/DOM-order component tests | One benefit `h1`, workflow/result `h2`s, and conditional result `h3`s match the specified outline |
| REQ-005 | Uploading, indexed, analyzing, completed, and failures | Live-region/alert component tests and screen-reader-oriented inspection | Progress/success use status semantics; failures use alerts; key state is announced once |
| REQ-006 | Focus, touch, muted/disabled, and pressed/expanded states | Computed target/contrast measurements and rendered focus inspection | Non-exempt targets are at least 44 by 44 px; ratios meet 4.5:1 text and 3:1 large-text/UI; state has non-color cues |
| REQ-007 | Reduced-motion preference enabled | CSS contract and browser emulation | Named animations/transitions stop or become effectively instantaneous |
| REQ-008 | Release gate | Full commands, screenshots, and keyboard checklist | Evidence is recorded; any deliberate gap has a linked follow-up issue |

## Rollout and Rollback

- Rollout: push the issue branch to obtain the Vercel preview configured by
  `frontend/vercel.json`; require source checks plus the recorded reachable-state
  viewport/keyboard evidence before merging to `main`, then smoke-check the
  production heading, file chooser, health status, and sample/result expansion.
- Rollback: redeploy the Vercel deployment associated with the pre-merge `main`
  commit SHA or revert the issue merge, then repeat the same production smoke
  check. No API, schema, persisted data, secret, or backend rollback is required.

## Definition of Done

- [ ] Every requirement has passing validation evidence.
- [ ] Every plan item has one primary module or work package.
- [ ] Module boundaries, interfaces, dependencies, and integration checks are explicit.
- [ ] Applicable implementation units are committed at coherent, validated checkpoints.
- [ ] Both traceability checkpoints validate with no unmapped IDs.
- [ ] Automated tests, four viewport screenshots, scroll measurements, and the keyboard-only pass are recorded; deliberate residual WCAG gaps have follow-up issues.
