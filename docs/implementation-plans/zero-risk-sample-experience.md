# Zero-Risk Sample Experience - Implementation Plan

Status: Source implementation complete; deployment closeout pending
Date: 2026-08-20
Issue: https://github.com/ogilvieg/document-intelligence-platform/issues/7

## Goal

Let a first-time visitor inspect a representative, clearly labeled DocSage
analysis without uploading a file, while disclosing the public demo's actual
retention boundary before any file is selected.

## Current State and Evidence

- `frontend/app/page.tsx::Home` exposes only the file-input path; analysis is
  unavailable until `useDocumentUpload` returns a document.
- `frontend/app/page.tsx::AnalysisPanel` already renders structured output,
  retrieved chunks, similarity scores, citations, tokens, model metadata, and
  cost from a `RAGAnalysisResponse`.
- `frontend/app/page.test.tsx` provides React Testing Library coverage for the
  homepage upload and analysis transitions, while
  `frontend/app/analysis-panel.test.tsx` covers result evidence.
- Original uploads are parsed in request memory by the backend, while document
  text, chunks, metadata, and embeddings are persisted. No repository evidence
  supports claims of deletion, encryption, tenant isolation, or confidentiality.
- Source validation after implementation passes backend tests, all frontend
  tests, TypeScript, and the production build. Full ESLint remains at the
  pre-existing main-branch baseline of eight errors and one warning in
  `page.tsx` and the API clients; issue #7 adds no new lint finding.
- Local browser verification at 390 x 844 reports `scrollWidth=387` and
  `clientWidth=387`, with the sample control and disclosure visible. With the
  backend stopped, sample activation shows the cold-start/outage explanation
  and a visible Retry sample control while upload remains available.

## Confirmed Decisions

1. Use a deterministic, version-controlled backend fixture exposed through an
   authenticated read-only endpoint and the existing Next proxy. This adds no
   public database records, seed lifecycle, embedding/LLM cost, or cross-user
   mutation risk while making backend cold start/outage visible.
2. Keep the sample visibly labeled in both its source summary and result area;
   it must never create an uploaded-document identity or enable analysis against
   a sample document ID.
3. If sample loading fails during backend cold start or outage, retain the upload
   path and show a clear inline error with retry. Real upload/analysis errors
   continue through their existing error surfaces.
4. Selecting or dropping a real file exits sample mode before upload begins and
   clears sample state; clearing a user upload returns to the neutral state.

## Assumptions and Open Questions

- Assumption: issue #9 owns broader responsive redesign; this change must still
  remain usable at the existing mobile breakpoint.
- Assumption: static sample content is synthetic and contains no personal or
  confidential data.
- Open question: deployment verification is outside a source-only change; the
  release owner must verify the deployed desktop/mobile experience and link the
  next homepage ticket.

## Requirements

| ID | Requirement |
| --- | --- |
| REQ-001 | A visitor can activate a clearly labeled synthetic sample and inspect structured output, retrieved chunks, similarity scores, citations, token usage, and cost without uploading or invoking database, embedding, retrieval, or LLM work. |
| REQ-002 | Sample loading has explicit pending, failure, retry, and reset behavior; it works when the backend is warm and clearly reports cold-start or outage failure while leaving real upload available. |
| REQ-003 | Selecting or dropping a real file exits sample mode, clears sample errors/results, and follows the existing upload-to-analysis flow without confusing sample data with user data. |
| REQ-004 | Before file selection, the upload area states that original files are processed in memory and not retained, that extracted text, chunks, and embeddings are stored, and that confidential material must not be uploaded to the public demo. |
| REQ-005 | Sample provenance is visible in both the source summary and result area; representative metrics are not presented as a live run, and no unsupported security or retention claim appears. |
| REQ-006 | New controls are keyboard operable and readable without horizontal overflow at 390 px; rollout, abuse controls, reset, rollback, deployed desktop/mobile verification, and next-ticket linkage are recorded. |

## Non-Goals

- Adding a database seed, public sample-document API, authentication, deletion,
  encryption, tenant isolation, or new retention guarantees.
- Changing upload persistence, ingestion, retrieval, or LLM behavior.
- Allowing visitors to mutate or rerun the deterministic sample.

## Constraints and Invariants

- The fixture contains synthetic content only and never enters persistence.
- Sample activation may call only the bounded fixture endpoint; it must not call
  upload, database, embedding, retrieval, or LLM services.
- Existing user changes and backend/API contracts remain untouched.
- New controls are keyboard accessible and must not introduce horizontal
  overflow at the existing 520 px breakpoint.

## Target Architecture or Change Map

The homepage owns a small sample state machine (`idle` / `loading` / `ready` /
`error`). A focused backend module supplies synthetic provenance plus a typed
`RAGAnalysisResponse` through an authenticated GET endpoint and the existing
Next proxy. Ready state reuses `AnalysisPanel`; real file selection resets
sample state before delegating to the existing upload hook.

## Module Breakdown

| Module or Work Package | Responsibility | Owning Surfaces | Interfaces and Dependencies | Independent Validation |
| --- | --- | --- | --- | --- |
| Sample fixture endpoint | Supply immutable synthetic provenance and representative analysis data without downstream work. | Focused backend fixture module, `backend/app/api/routes.py`, `backend/tests/test_rag_endpoints.py` | Existing API-key dependency; `RAGAnalysisResponse`-compatible JSON; no DB/service dependency | Endpoint test proves provenance, evidence shape, determinism, auth, and absence of downstream calls |
| Sample client lifecycle | Fetch the sample through the existing proxy and own latest-request-safe loading/error/reset state. | `frontend/lib/secure-api-client.ts`, `frontend/lib/hooks.ts`, focused tests | GET proxy; typed sample response | Client/hook tests cover success, rejection, retry, and invalidation |
| Homepage sample flow | Own entry, sample labeling, and transition to upload. | `frontend/app/page.tsx`, `frontend/app/page.test.tsx` | Sample hook; existing upload and analysis hooks; `AnalysisPanel` | Component tests for entry, failure/retry, labeling, and upload transition |
| Upload disclosure | Present accurate persistence and confidentiality copy before selection. | `frontend/app/page.tsx`, `frontend/app/page.test.tsx` | Current backend ingestion/persistence behavior | Visibility test asserts each material persistence boundary |
| Responsive presentation | Keep new sample/disclosure controls keyboard operable and readable in the existing visual language. | `frontend/app/page.tsx`, `frontend/app/globals.css`, component tests | Existing 520 px breakpoint | Accessible-name/keyboard tests plus 390 px no-overflow review |
| Release closeout | Verify deployed behavior and link the next homepage work without changing runtime code. | Issue #7 closeout or release notes | Backend-first ordering; desktop/mobile deployment; issue #8 | Recorded deployed checks, rollback readiness, and #8 link |

## Implementation Phases

### Phase 1 - Sample Contract

**P1.1 [REQ-001, REQ-002, REQ-005] Add a deterministic synthetic sample endpoint and provenance.**

- Primary module or work package: Sample fixture endpoint.
- TDD the authenticated representative response shape, explicit synthetic label,
  complete retrieval/citation/token/cost evidence, and absence of database,
  embedding, retrieval, and LLM calls before adding the fixture.

**P1.2 [REQ-001, REQ-002, REQ-003] Add the sample proxy client and invalidatable lifecycle.**

- Primary module or work package: Sample client lifecycle.
- TDD GET serialization and the success, rejection, retry, and reset lifecycle;
  a late response after upload/reset must not restore sample state.

### Phase 2 - Homepage Behavior

**P2.1 [REQ-001, REQ-002, REQ-003, REQ-005] Integrate the sample state machine and safe transitions.**

- Primary module or work package: Homepage sample flow.
- TDD one vertical behavior at a time: entry without upload/analysis calls,
  rejected load with retry, and both file selection and drop resetting sample
  state before the upload spy is invoked. Label both the synthetic source
  summary and rendered result, including that metrics are representative.

**P2.2 [REQ-004] Add accurate upload-retention disclosure before file selection.**

- Primary module or work package: Upload disclosure.
- Add focused visibility coverage first, then place concise copy adjacent to
  the upload action without making unsupported guarantees.

**P2.3 [REQ-006] Integrate accessible responsive styling and source validation.**

- Primary module or work package: Responsive presentation.
- Keep controls fluid at the existing breakpoint, test accessible names and
  keyboard activation, and use `scrollWidth <= clientWidth` at 390 px as the
  explicit deployed no-overflow criterion.

### Phase 3 - Release Closeout

**P3.1 [REQ-006] Verify deployment and link the next homepage ticket.**

- Primary module or work package: Release closeout.
- After backend-first rollout, verify entry, failure messaging, disclosure, and
  upload transition on desktop and at 390 px; record results in issue #7 and
  link issue #8 as the next trust-focused homepage ticket. This external gate
  remains incomplete during source-only work.

## Task Breakdown

### Phase 1 Tasks

- [x] T001 [Plan:P1.1] Add a failing endpoint test for auth, synthetic provenance, full evidence, determinism, and no downstream calls; implement the fixture endpoint and verify green.
- [x] T002 [Plan:P1.2] Add failing client/hook tests for proxy GET, success, rejection/retry, and invalidation; implement the typed client lifecycle and verify green.

### Phase 2 Tasks

- [x] T003 [Plan:P2.1] Add a failing homepage test for sample entry and no upload/analysis calls, implement the loading/ready state, and verify green.
- [x] T004 [Plan:P2.1] Add failing homepage tests for sample failure/retry and transition to a real upload, implement the minimum reset/error behavior, and verify green.
- [x] T005 [Plan:P2.2] Add a failing retention-copy visibility test, implement the disclosure next to upload, and verify green.
- [x] T006 [Plan:P2.3] Add keyboard/responsive coverage and styles, then run backend/frontend tests, type checking, lint, and production build.

### Phase 3 Tasks

- [ ] T007 [Plan:P3.1] After deployment, verify desktop and 390 px behavior including the no-overflow criterion, record rollback readiness, and link issue #8 from issue #7 closeout.

## Commit Checkpoints

| After Tasks | Commit Scope | Required Validation |
| --- | --- | --- |
| T001 | Synthetic sample endpoint | Focused backend endpoint test |
| T002 | Sample proxy and lifecycle | Focused frontend client/hook tests |
| T003-T005 | Homepage sample and disclosure behavior | Homepage and analysis-panel tests plus type checking |
| T006 | Accessible responsive source completion | Backend tests; full frontend tests, lint, type check, and build |
| T007 | Deployment closeout | Recorded desktop/mobile checks and issue #8 link |

## Validation Matrix

| Requirement | Scenario | Validation | Expected Evidence |
| --- | --- | --- | --- |
| REQ-001 | First visit activates sample | Endpoint and component tests | Analysis evidence renders; upload/analysis and backend downstream services are not invoked |
| REQ-002 | Loader rejects and visitor retries | Component test | Inline error appears, upload stays available, retry can reach ready |
| REQ-003 | Visitor chooses a real file after sample | Component test | Sample label/result clear before existing upload call |
| REQ-004 | Visitor reviews upload area | Component test | All three retention/confidentiality facts are visible before selection |
| REQ-005 | Visitor inspects sample | Endpoint and component tests | Source and result identify synthetic precomputed data and representative metrics |
| REQ-006 | Keyboard, 390 px, and release closeout | Component tests plus deployed checks | Keyboard entry works, no horizontal overflow, rollback is ready, and #8 is linked |

## Abuse Controls, Data Provenance, and Reset

- Abuse: the bounded GET performs no database, embedding, LLM, or persistence
  work, so it cannot amplify model cost or create shared mutable records. The
  existing proxy/API key boundary applies; immutable payload size bounds work.
- Provenance: all names, excerpts, identifiers, timestamps, scores, and output
  are synthetic, version-controlled demo data and are labeled as such.
- Reset: upload selection/drop exits sample mode; sample retry replaces error
  state; user clear returns through the existing upload/analysis reset path.

## Rollout and Rollback

- Rollout: deploy the backend fixture endpoint before the frontend entry point,
  run automated validation, then verify
  sample entry/error affordances, disclosure visibility, and transition to
  upload in deployed desktop and mobile layouts. Confirm the next appropriate
  homepage ticket link in release notes or the issue closeout.
- Rollback: revert the fixture, homepage state/UI, tests, and styles together.
  No database cleanup, migration, seed removal, or backend rollback is needed.

## Definition of Done

- [ ] Every requirement has passing validation evidence.
- [x] Every plan item has one primary module or work package.
- [x] Both traceability checkpoints validate with no unmapped IDs.
- [x] Sample entry, failure/retry, upload transition, and disclosure are tested.
- [ ] Backend and frontend tests, type checking, lint, and production build pass. (All pass except the unchanged full-lint baseline.)
- [ ] Desktop/mobile deployment verification and issue #8 linkage are recorded by the release owner.
