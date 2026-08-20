# Query-Driven DocSage Homepage - Implementation Plan

Status: Ready for implementation
Date: 2026-08-20
Issue: https://github.com/ogilvieg/document-intelligence-platform/issues/6

## Goal

Let a visitor choose and visibly edit the analysis goal used for an uploaded
document, while keeping the active document scope, structured analysis output,
retrieval evidence, citations, token usage, and cost traceability intact.

## Current State and Evidence

- `frontend/app/page.tsx::handleAnalyze` constructs a hidden, resume-shaped
  prompt and submits hard-coded retrieval options. The page has no query state,
  category selection, preset selection, validation, or result-to-query label.
- `frontend/lib/hooks.ts::useRAGAnalysis` accepts an arbitrary query and owns a
  single loading/error/result lifecycle, but it has no request identity or
  cancellation guard against a late response after clear, re-upload, or repeat.
- Both `frontend/lib/secure-api-client.ts::analyzeWithRAG` and
  `frontend/lib/api-client.ts::analyzeWithRAG` accept arbitrary queries but use
  `||` defaults, which replace valid `0.0` threshold and temperature values.
- `backend/app/api/routes.py::RAGAnalysisRequest` accepts the query and options,
  `/analyze-rag` scopes retrieval by `document_ids`, echoes `query`, and returns
  citations, retrieved chunks, retrieval metadata, LLM metadata, and cost. It
  does not constrain blank/oversized queries or numeric ranges.
- `backend/app/services/retrieval.py::retrieve_chunks` also replaces an explicit
  `0.0` threshold through a truthiness fallback.
- The frontend `RetrievalMetadata`/`LLMMetadata` types do not exactly match the
  backend response keys (`retrieval_timestamp`, `filters_applied`,
  `latency_ms`, `cost_usd`, and `created_at`), so contract fixtures must come
  from the actual route response rather than the drifted TypeScript types.
- `DocumentUploadResponse.type` is a storage/file format (`pdf`, `markdown`,
  `html`, `text`, `other`), not a semantic category such as contract or resume.
- `frontend/package.json` has no test script or component-test dependencies.
  The current full frontend lint baseline has eight errors and one warning that
  predate #6; type checking passes with
  `frontend/node_modules/.bin/tsc --noEmit --incremental false`.
- Next.js documents Vitest with jsdom and React Testing Library as a supported
  unit/component-test setup for synchronous client components:
  https://nextjs.org/docs/app/guides/testing/vitest.
- The backend retrieval characterization command passes 12 tests from the repo
  root:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend OPENAI_API_KEY=test backend/venv/bin/pytest -p no:cacheprovider backend/tests/test_retrieval.py -q`.

## Confirmed Decisions

1. #6 remains a structured-analysis workflow. Custom goals change the query
   used for retrieval and generation, but the existing `AnalysisOutput` schema
   remains stable. A general free-form answer schema is outside this issue.
2. Prompt suggestions use an explicit semantic category selector with
   `general` as the default. They do not infer semantic kind from MIME type,
   filename, or the existing file-format `type`.
3. The existing assessment prompt becomes a visible, editable preset. No hidden
   prompt is submitted.
4. The active uploaded document ID remains mandatory for every homepage
   analysis request. Semantic category is UI prompt context and is not sent as
   the backend `doc_type` filter.
5. Query text is trimmed, must contain at least one non-whitespace character,
   and is capped at 2,000 characters in both the UI and API boundary.
6. Only omitted options receive defaults. Explicit `0.0` values for
   `similarity_threshold` and `temperature` must survive every layer.
7. The paper-and-ink design remains; #9 owns broader homepage responsive and
   accessibility remediation. New #6 controls must still be keyboard-operable,
   labeled, and readable at 390 px.

## Assumptions and Open Questions

- Assumption: five categories are sufficient for this issue: General, Resume,
  Contract, Report, and Research Paper. Adding categories later is a data-only
  prompt-catalog change.
- Assumption: a 2,000-character goal cap provides enough room for useful
  instructions while bounding accidental embedding/LLM cost.
- Assumption: when a repeat analysis fails, the prior successful result remains
  visible and correctly labeled; the new error and draft remain available for
  retry.
- Open question for implementation evidence: whether `AbortController` can
  cancel the deployed proxy/backend path reliably. Request identity remains the
  required stale-response guard even if transport cancellation is added.

## Requirements

| ID | Requirement |
| --- | --- |
| REQ-001 | After upload, the visitor can see and edit the complete analysis goal; the trimmed visible value is the exact query sent to `/analyze-rag`, echoed by the response, and shown with the completed result. |
| REQ-002 | The visitor can select General, Resume, Contract, Report, or Research Paper and choose deterministic category-appropriate examples or the explicit Structured Assessment preset; selecting a suggestion populates the editable goal and manual edits produce a Custom state. |
| REQ-003 | The UI and API reject blank, whitespace-only, or longer-than-2,000-character goals without invoking embedding, retrieval, or generation, and expose actionable validation. |
| REQ-004 | Every homepage analysis request contains exactly the active uploaded document ID for custom, preset, retry, and repeat flows; semantic category never substitutes for the retrieval filter, while generic API clients remain backward compatible with unfiltered and `doc_type` callers. |
| REQ-005 | Custom and preset analyses preserve the existing structured output, citations, retrieved chunks, retrieval metadata, LLM metadata, token usage, cost, and backend-echoed query. |
| REQ-006 | Only the latest active analysis may change visible loading, error, or result state; clear or document replacement invalidates in-flight work, duplicate submission is prevented, failed repeat runs preserve the prior labeled success, and reset clears all #6 state. |
| REQ-007 | Omitted retrieval/generation options receive defaults, while explicit `similarity_threshold=0.0` and `temperature=0.0` survive both TypeScript clients, proxy serialization, API validation, retrieval/generation calls, and response metadata. Invalid numeric ranges receive 422 responses before external work. |
| REQ-008 | New goal, category, suggestion, validation, progress, and retry controls have programmatic labels, keyboard operation, visible focus, accessible status/error association, and a readable no-overflow layout at 390 px. |
| REQ-009 | A repository-native frontend test command covers prompt-catalog logic, request serialization, composer interaction, and lifecycle races; focused backend tests cover query/option validation and zero preservation. |

## Non-Goals

- Retuning threshold, `top_k`, temperature, chunk size, or production defaults;
  #5 owns evidence generation and any later tuning decision.
- Introducing a free-form answer response schema or replacing
  `AnalysisOutput`.
- Persisting semantic category or query text to the database or browser storage.
- Re-embedding, migrating, or backfilling existing documents.
- Broad homepage redesign, sample-document flow (#7), general responsive and
  accessibility remediation (#9), or trust/navigation work (#8).
- Automatic retries of analysis POSTs, which could duplicate LLM cost.

## Constraints and Invariants

- Existing stored documents, chunks, embeddings, and database schema remain
  untouched.
- Existing API response fields remain backward compatible.
- The browser continues to call the server-side proxy; backend credentials stay
  out of client code.
- A semantic prompt category must not be passed as `SearchFilters.doc_type`,
  because that field currently represents stored file type.
- Raw query text must not be added to local storage. Existing server logging of
  raw queries is residual privacy risk for #7 unless a bounded #6 change is
  required to test the new validation path.
- The current unrelated full-lint failures are recorded baseline debt. #6 must
  add no new lint errors and must pass focused lint for new/modified test and
  prompt-composer surfaces; a clean full lint is not claimed unless explicitly
  repaired.

## Target Architecture or Change Map

```text
semantic category + prompt catalog + editable goal
                         |
                         v
               homepage composer state
                         |
        active document id + normalized goal + options
                         |
                         v
              useRAGAnalysis request guard
                         |
                         v
          SecureAPIClient -> Next proxy -> /analyze-rag
                         |
                         v
 structured result + echoed query + retrieval/LLM/cost evidence
```

## Module Breakdown

| Module or Work Package | Responsibility | Owning Surfaces | Interfaces and Dependencies | Independent Validation |
| --- | --- | --- | --- | --- |
| Frontend test foundation | Provide deterministic unit/component tests before behavior changes. | `frontend/package.json`, lockfile, Vitest config/setup, frontend test files | Next.js 16 client component; jsdom; React Testing Library/user-event | A smoke component test and pure-unit test run through `npm test` |
| Prompt domain | Own semantic categories, deterministic examples, the assessment preset, normalization, length validation, and selection state rules. | Proposed focused module under `frontend/lib/` | Consumed by composer/page; no backend or persistence dependency | Table-driven pure tests for five categories, preset, Custom transition, trim, empty, and length cap |
| RAG request contract | Preserve zero-valued options, normalize and bound API input, and keep homepage-only document scoping separate from generic client compatibility. | Both frontend API clients, Next proxy route, `RAGAnalysisRequest`, retrieval fallback | Proxy JSON pass-through; retrieval and LLM services; homepage request builder | Client/proxy serialization tests plus FastAPI/retrieval regression tests proving exact values and no service calls on 422 |
| Composer UI | Render category, suggestions, editable goal, validation, submission, progress, and retry within the existing visual language. | Focused client component integrated by `frontend/app/page.tsx` | Prompt domain; `useRAGAnalysis`; active `DocumentUploadResponse` | Component tests for keyboard selection/edit/submit and 390 px structural smoke check |
| Analysis lifecycle | Prevent stale results and define clear, re-upload, failure, retry, and repeat transitions. | `frontend/lib/hooks.ts`, page integration | Request identity and optional abort signal; upload/reset lifecycle | Deferred-promise tests resolving requests out of order and reset/re-upload tests |
| Result traceability | Tie a completed result to the backend-echoed query without losing existing evidence. | `AnalysisPanel` in `frontend/app/page.tsx` or extracted result component | Existing `RAGAnalysisResponse` contract | Component/contract fixture asserts query, citations, chunks, metadata, tokens, and cost remain visible |

## Implementation Phases

### Phase 0 - TDD Foundation and Characterization

**P0.1 [REQ-009] Establish the frontend test foundation with a passing smoke test.**

- Primary module or work package: Frontend test foundation.
- Add the official Next.js-compatible Vitest, jsdom, React Testing Library, and
  user-event setup, a non-watch test script, and a minimal synchronous client
  component test before feature behavior changes.

**P0.2 [REQ-004, REQ-005] Characterize the existing request and response contracts.**

- Primary module or work package: RAG request contract.
- Add passing characterization coverage for arbitrary query forwarding, the
  generic clients' intentionally optional `document_ids`, current homepage
  one-document scoping, and an actual `/analyze-rag` response fixture. Do not
  encode the drifted TypeScript metadata keys as the expected contract.

### Phase 1 - Prompt Domain and Request Safety

**P1.1 [REQ-003, REQ-007] Enforce the request contract and nullish fallback semantics.**

- Primary module or work package: RAG request contract.
- Complete one vertical red-green-refactor cycle at a time for frontend client
  defaults, proxy pass-through, canonical API query trimming/bounds, numeric
  bounds and temperature propagation, and retrieval threshold fallback. The
  API must trim before validating 1..2,000 characters and must pass the same
  normalized query to retrieval, generation, and the echoed response.

**P1.2 [REQ-002, REQ-003, REQ-008] Implement the typed prompt catalog and goal validation.**

- Primary module or work package: Prompt domain.
- Represent the five semantic categories and their deterministic examples as
  typed data, keep Structured Assessment explicit, normalize goal input, expose
  the 2,000-character rule, and model suggestion-to-Custom transitions without
  inferring category from file format. Complete each catalog/validation
  behavior through its own vertical red-green-refactor cycle.

### Phase 2 - Query-Driven Interaction

**P2.1 [REQ-001, REQ-002, REQ-003, REQ-008] Add the visible, accessible analysis-goal composer.**

- Primary module or work package: Composer UI.
- Render category selection, category examples, Structured Assessment, the
  editable labeled goal, inline validation, and submit/retry controls after a
  successful upload. Selection populates the visible field; submission sends
  only its normalized value and exactly the active document ID. Generic API
  callers remain free to omit `document_ids` or use `doc_type`.

**P2.2 [REQ-004, REQ-006] Make analysis lifecycle transitions latest-request-safe.**

- Primary module or work package: Analysis lifecycle.
- Prevent duplicate submission, associate pending/error/result states with the
  submitted query, ignore late invalidated responses, preserve a prior success
  on repeat failure, and reset category/goal/validation/request identity on
  clear or document replacement.

**P2.3 [REQ-001, REQ-005, REQ-006] Bind completed results to their submitted query while preserving evidence.**

- Primary module or work package: Result traceability.
- Show `analysisResult.query` as the authoritative completed goal and verify the
  existing structured output, citations, chunks, retrieval details, LLM
  details, token counts, and cost remain intact for preset and custom runs.
  Reconcile the TypeScript response types to the actual backend keys and assert
  each contract field rather than deep-equality against a fabricated fixture.

### Phase 3 - Integration, Delivery, and Handoff

**P3.1 [REQ-008, REQ-009] Validate the complete workflow and document the delivery boundary.**

- Primary module or work package: Frontend test foundation.
- Run focused frontend/backend tests, type checking, changed-surface lint,
  production build, keyboard checks, a 390 px browser pass, and live smoke tests
  for normal and explicit-zero requests. Record the known full-lint baseline,
  deployment order, rollback command, and next homepage issue in the PR/issue.

## Task Breakdown

### Phase 0 Tasks

- [x] T001 [Plan:P0.1] Add Vitest/jsdom/React Testing Library/user-event configuration, scripts, lockfile changes, and a passing client-component smoke test.
- [x] T002 [Plan:P0.2] Add passing characterization tests for arbitrary query forwarding, generic-client optional filters, current homepage one-document scoping, and the actual `/analyze-rag` response shape.

### Phase 1 Tasks

- [x] T003 [Plan:P1.1] Complete vertical red-green-refactor cycles proving both frontend API clients preserve explicit `0.0` threshold/temperature values while omitted values keep current defaults.
- [x] T004 [Plan:P1.1] Complete a vertical red-green-refactor cycle proving the Next proxy preserves explicit zero values when it parses and re-serializes the JSON request.
- [x] T005 [Plan:P1.1] Complete sequential red-green-refactor cycles for API-side trim-before-validation, 1..2,000 query length, numeric bounds, normalized query forwarding, and `temperature=0.0` propagation into generation and response metadata.
- [x] T006 [Plan:P1.1] Complete a vertical red-green-refactor cycle replacing retrieval truthiness fallback with explicit `None` handling for `similarity_threshold=0.0` without changing the default.
- [x] T007 [Plan:P1.2] Complete a tracer red-green-refactor cycle for the typed five-category catalog and explicit Structured Assessment preset.
- [x] T008 [Plan:P1.2] Complete vertical red-green-refactor cycles for category examples, normalization, empty/length validation, and suggestion-to-Custom transitions.

### Phase 2 Tasks

- [x] T009 [Plan:P2.1] Complete a tracer red-green-refactor cycle that renders an editable labeled goal, submits its normalized value with exactly the active document ID, and supports keyboard submission.
- [x] T010 [Plan:P2.1] Complete vertical red-green-refactor cycles for category/suggestion/preset selection, manual Custom editing, inline validation/status association, and readable 390 px composition.
- [x] T011 [Plan:P2.2] Complete vertical red-green-refactor cycles for duplicate-submit prevention and latest-request identity when responses resolve out of order.
- [x] T012 [Plan:P2.2] Complete vertical red-green-refactor cycles for clear during analysis, document replacement, repeat success/failure, prior-success preservation, and deterministic retry/reset.
- [x] T013 [Plan:P2.3] Complete a vertical red-green-refactor cycle that labels a completed result with the backend-echoed query for both custom and preset runs.
- [x] T014 [Plan:P2.3] Complete vertical red-green-refactor cycles aligning TypeScript metadata types to the real response and preserving each structured output, citation, chunk, retrieval, LLM, token, cost, and creation-time field.

### Phase 3 Tasks

- [x] T015 [Plan:P3.1] Run the complete focused frontend and backend test suites, TypeScript checking, changed-surface lint, and the production frontend build; record the pre-existing full-lint failures separately.
- [x] T016 [Plan:P3.1] Verify keyboard operation and the new #6 controls at 390 px and desktop widths, then smoke-test normal, retry, repeat, and explicit-zero requests against the deployed contract.
- [ ] T017 [Plan:P3.1] Update issue #6 and the delivery PR with validation evidence, deployment/rollback notes, residual risks linked to #7/#9, and the next actionable homepage issue.

## Commit Checkpoints

| After Tasks | Commit Scope | Required Validation |
| --- | --- | --- |
| T001 | P0.1 frontend test foundation | Smoke test passes through the new non-watch test command; package/lock diff contains test-only dev dependencies. |
| T002 | P0.2 characterization | Passing characterization locks the current arbitrary-query, generic-filter, homepage-scope, and real response contracts. |
| T003-T006 | P1.1 request safety | Every behavior completes red-green-refactor before the next begins; client/proxy/FastAPI/retrieval suites are green and defaults are unchanged. |
| T007-T008 | P1.2 prompt domain | Every catalog/validation behavior completes red-green-refactor; prompt-domain tests and type checking pass. |
| T009-T010 | P2.1 composer | Every interaction behavior completes red-green-refactor; component, keyboard, scoping, and prompt-domain tests pass. |
| T011-T012 | P2.2 lifecycle | Every lifecycle behavior completes red-green-refactor; deferred-promise suite has no stale result/error transitions. |
| T013-T014 | P2.3 result traceability | Every result/contract behavior completes red-green-refactor; real-shape fixtures pass for custom and preset runs. |
| T015-T017 | P3.1 delivery evidence | Focused suites, type check, build, changed-surface lint, browser checks, and smoke evidence are recorded. |

## Validation Matrix

| Requirement | Scenario | Validation | Expected Evidence |
| --- | --- | --- | --- |
| REQ-001 | Custom and preset goal submission | Component test plus request mock and response fixture | Normalized visible goal equals request query, response query, and completed-result label. |
| REQ-002 | Five semantic categories and Custom transition | Table-driven prompt-domain and component tests | Each category exposes deterministic examples; preset populates the field; editing changes state to Custom. |
| REQ-003 | Blank, whitespace, oversized, and valid goals | UI component tests and FastAPI endpoint tests | Invalid goals cause no client request and no backend service calls; valid trimmed goal proceeds. |
| REQ-004 | Custom, preset, retry, and repeat scoping | Homepage request-builder/component assertions and backend filter assertion | Every homepage request contains exactly the active document UUID; generic clients remain backward compatible. |
| REQ-005 | Existing structured response evidence | Actual-route contract fixture and result component tests with field-by-field assertions | Output, citations, chunks, real retrieval/LLM metadata keys, tokens, cost, creation time, and query render without loss. |
| REQ-006 | Clear/re-upload/repeat races | Deferred-promise hook/component tests | Only latest valid request updates state; prior success remains labeled on repeat failure; reset clears #6 state. |
| REQ-007 | Explicit zero and invalid numeric values | Both client tests, proxy route test, FastAPI generation/metadata assertions, and retrieval test | `0.0` survives every layer; omitted values default; invalid values return 422 before services run. |
| REQ-008 | Keyboard and narrow viewport | Component accessibility assertions plus manual keyboard/390 px pass | Labels, focus, error/status association, keyboard actions, and no overflow are observed for new controls. |
| REQ-009 | Repeatable automated validation | `npm test`, focused pytest, type check, build, changed-surface ESLint | Commands are documented and pass; known unrelated full-lint baseline is not misreported. |

## Rollout and Rollback

- Rollout: land API validation/nullish fixes before or with the frontend; deploy
  backend to Render, verify the existing structured-assessment call and explicit
  zero values, then deploy the frontend to Vercel and exercise custom, preset,
  retry, repeat, keyboard, and narrow-screen flows.
- Observability: use existing request/retrieval completion logs and client error
  surfaces, but do not add raw query persistence. Record 422, no-chunks, and
  server-error behavior during smoke testing.
- Rollback: revert the #6 frontend/backend commits. No schema rollback,
  document migration, re-embedding, or stored-data cleanup is required.
- Compatibility: existing callers that omit new UI state continue using current
  API response fields and defaults. Invalid inputs that previously reached paid
  services will now receive 422 responses by design.

## Definition of Done

- [ ] Every requirement has passing validation evidence.
- [ ] Every plan item has one primary module or work package.
- [ ] Module boundaries, interfaces, dependencies, and integration checks are explicit.
- [ ] Applicable implementation units are committed at coherent, validated checkpoints.
- [ ] Both traceability checkpoints validate with no unmapped IDs.
- [ ] No production retrieval default is retuned and no stored data is migrated.
- [ ] Issue #6 records validation evidence, rollback guidance, residual risks, and the next homepage ticket.
