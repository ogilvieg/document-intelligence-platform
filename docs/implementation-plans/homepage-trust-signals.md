# Homepage Trust and Portfolio Signals - Implementation Plan

Status: In progress
Date: 2026-08-20
Issue: https://github.com/ogilvieg/document-intelligence-platform/issues/8

## Goal

Make the homepage immediately explain that DocSage lets visitors ask questions
of a document and verify answers against retrieved evidence, while ensuring its
operational status, project links, and social previews are specific and
evidence-backed.

## Current State and Evidence

- `frontend/app/page.tsx::Home` leads with a dismissible "What is DocSage?"
  implementation explanation and renders a hardcoded `ONLINE` badge before any
  health signal succeeds.
- `frontend/lib/secure-api-client.ts::checkHealth` exists, but calls the shared
  proxy with `/health`. Because `frontend/app/api/proxy/route.ts` appends that
  path to `BACKEND_API_URL`, production configuration ending in `/api/v1`
  targets `/api/v1/health`; `backend/app/main.py` exposes liveness at root
  `/health` instead.
- `backend/app/main.py::health` is process liveness only. It returns
  `status: healthy` without checking the asynchronously initialized database,
  so the frontend must label a successful result as API availability rather
  than full demo readiness.
- `frontend/app/layout.tsx::metadata` defines only a title and description.
  `frontend/public` has no representative social-card asset.
- The rendered homepage has no links. Repository-backed destinations exist for
  source, the `DEMO.md` project brief, the README architecture section, and
  production API documentation; `README.md` and `DEMO.md` identify the canonical
  production site as `https://docsage.phoenix7.dev`.
- `frontend/app/page.test.tsx`, `frontend/lib/hooks.test.tsx`, and
  `frontend/app/api/proxy/route.test.ts` provide the closest Vitest/Testing
  Library validation surfaces. `npm test`, `npx tsc --noEmit`, `npm run lint`,
  and `npm run build` are repository-native frontend checks; any pre-existing
  lint findings must be compared with and recorded against the main baseline.
- Source validation after implementation passes 47 frontend tests, TypeScript,
  and the production build. ESLint remains at the pre-existing main baseline of
  eight errors and one warning, with no finding added by issue #8. Browser QA
  confirms the benefit-first desktop layout and a 390 px layout with
  `scrollWidth = clientWidth = 387`, stacked supporting steps, and four project
  links. The 1200 x 630 Open Graph PNG was rendered and visually inspected.

## Confirmed Decisions

1. Keep `/health` as backend liveness and describe a valid response as `API
   online`; do not imply database or end-to-end analysis readiness.
2. Route health through a focused same-origin Next endpoint that derives the
   backend origin correctly from the configured `/api/v1` base, uses no-store
   semantics, and enforces a bounded timeout.
3. Model `connecting`, `delayed`, `online`, and `unavailable` explicitly. A
   pending request becomes delayed with a cold-start explanation, may still
   become online, and only a successful well-formed healthy response can report
   online.
4. Use stable, repository-backed external destinations: repository root,
   `DEMO.md` as the project brief/case study, README `#architecture-overview`,
   and `https://docsage-api.phoenix7.dev/docs`.
5. Generate the representative social card with a Next.js Open Graph image
   route so its paper-and-ink presentation stays versioned with the frontend.

## Assumptions and Open Questions

- Assumption: `https://docsage.phoenix7.dev` remains the canonical production
  origin documented in the current repository and should not vary on preview
  deployments.
- Assumption: the Render service may take long enough to wake that a pending
  probe needs explanatory delayed state rather than being treated immediately
  as an outage.
- Open question: production social-crawler rendering and all external targets
  must be rechecked after deployment because source tests cannot prove remote
  availability or crawler behavior.

## Requirements

| ID | Requirement |
| --- | --- |
| REQ-001 | A first-time visitor encounters a persistent, concise benefit statement about asking document questions and verifying answers before implementation terminology; the ingest, retrieve, and analyze explanation remains supporting content. |
| REQ-002 | Operational status begins as connecting, reports online only after a well-formed successful API liveness response, reports delayed while a probe exceeds the cold-start threshold, and reports unavailable after a bounded failure. |
| REQ-003 | Delayed and unavailable states explain possible Render startup latency without asserting that every delay is a cold start, and an unavailable visitor can retry without a page reload. |
| REQ-004 | The homepage exposes restrained, valid links to the repository, project brief/case study, API documentation, and architecture documentation. |
| REQ-005 | The canonical production URL, Open Graph fields, Twitter card fields, and a representative public preview image are configured and renderable. |
| REQ-006 | New trust signals preserve the paper-and-ink visual language, remain keyboard/focus accessible, communicate status without color alone, and wrap without horizontal overflow at 390 px. |
| REQ-007 | Source and deployed validation cover health transitions, link and metadata configuration, healthy/cold-start/unavailable presentation, external targets, and social preview behavior with a recorded rollback path. |

## Non-Goals

- Changing backend `/health` into a database readiness probe or claiming that a
  live API guarantees upload, persistence, retrieval, or LLM availability.
- Creating a new portfolio site, analytics integration, monitoring service,
  database migration, or authentication flow.
- Redesigning the analysis workflow or replacing the established visual system.

## Constraints and Invariants

- No state may render `online` before a current probe returns HTTP success with
  the expected healthy payload; stale or aborted probes cannot overwrite a
  newer state.
- Health probes are same-origin from the browser, non-cached at the Next route,
  bounded in duration, and do not expose backend configuration or secrets.
- Core benefit copy is persistent even when the existing implementation
  explanation is dismissed from local storage.
- External URLs are centralized constants and open safely; visible link text
  and status text do not rely on icons or color alone.

## Target Architecture or Change Map

The browser calls a focused same-origin health route. That route derives the
backend origin from `BACKEND_API_URL`, calls root `/health` with no-store and a
timeout, and returns only the result needed by the client. A dedicated hook owns
the race-safe temporal state machine and retry action. The homepage consumes the
hook through a small status presentation, while persistent hero copy and a
project-link group remain independent of the health lifecycle. Static Next
metadata and an Open Graph image route own crawler-facing trust signals.

## Module Breakdown

| Module or Work Package | Responsibility | Owning Surfaces | Interfaces and Dependencies | Independent Validation |
| --- | --- | --- | --- | --- |
| Health transport | Reach production root liveness safely from the same-origin frontend. | Focused Next health route; `frontend/lib/secure-api-client.ts` | `BACKEND_API_URL`; backend root `/health`; `HealthResponse` | Route/client tests prove URL derivation, no-store behavior, success validation, and bounded failures |
| Health lifecycle | Own temporal state, delayed threshold, failure, retry, cancellation, and stale-response protection. | `frontend/lib/hooks.ts`, `frontend/lib/hooks.test.tsx` | `secureApiClient.checkHealth`; timers and abort lifecycle | Fake-timer hook tests cover all state transitions and races |
| Homepage trust presentation | Present persistent benefit, honest live status, cold-start guidance, retry, and project navigation. | `frontend/app/page.tsx`, `frontend/app/globals.css`, `frontend/app/page.test.tsx` | Health hook; centralized link constants; existing intro and responsive styles | Component tests assert semantic behavior, accessible navigation, and status actions |
| Social metadata | Configure production identity and render a representative card. | `frontend/app/layout.tsx`, focused metadata test, Next Open Graph image route | Canonical origin; Next Metadata/ImageResponse contracts | Export tests, production build, image response inspection, and deployed crawler preview |
| Release verification | Prove integrated source and deployed behavior and preserve a safe rollback. | Frontend validation commands, preview/production deployment, issue closeout | All preceding work packages | Full tests/type/build plus healthy/delayed/unavailable and crawler/link checks |

## Implementation Phases

### Phase 1 - Honest Health Signal

**P1.1 [REQ-002, REQ-007] Correct and bound the production health transport.**

- Primary module or work package: Health transport.
- TDD the configured `/api/v1` base resolving to root `/health`, valid healthy
  payload handling, no-store behavior, and timeout/error normalization before
  changing the client transport.

**P1.2 [REQ-002, REQ-003, REQ-007] Implement the race-safe health lifecycle.**

- Primary module or work package: Health lifecycle.
- Drive connecting, delayed, online, unavailable, retry, abort, and stale-probe
  behavior with fake timers. Expose semantic state and retry data without
  coupling the hook to homepage copy or presentation.

### Phase 2 - Visitor and Evaluator Trust

**P2.1 [REQ-001, REQ-006] Lead with a persistent benefit statement while retaining implementation context.**

- Primary module or work package: Homepage trust presentation.
- Add semantic, non-dismissible hero content before the existing supporting
  ingest/retrieve/analyze explanation and preserve established styling.

**P2.2 [REQ-002, REQ-003, REQ-006, REQ-007] Present honest accessible API status and recovery guidance.**

- Primary module or work package: Homepage trust presentation.
- Consume the health lifecycle through a polite textual status that calls a
  successful signal `API online`, conditionally explains possible cold-start
  delay, exposes retry on failure, and wraps at the mobile breakpoint.

**P2.3 [REQ-004, REQ-006, REQ-007] Add centralized project navigation with verified repository-backed targets.**

- Primary module or work package: Homepage trust presentation.
- Add repository, project brief, API docs, and architecture links with visible
  focus treatment, safe external-link behavior, and responsive wrapping.

### Phase 3 - Shareable Project Identity

**P3.1 [REQ-005, REQ-007] Add canonical and social metadata plus a representative Open Graph image.**

- Primary module or work package: Social metadata.
- TDD exported title/description/canonical/Open Graph/Twitter values, add a
  1200 x 630 paper-and-ink image route, and verify its response through the
  production build and rendered preview.

### Phase 4 - Integrated Delivery

**P4.1 [REQ-003, REQ-004, REQ-005, REQ-006, REQ-007] Validate source and deployed trust signals with rollback readiness.**

- Primary module or work package: Release verification.
- Run focused and full frontend checks, inspect desktop and 390 px states with
  deterministic healthy/delayed/unavailable responses, then verify deployed
  links, metadata, card rendering, and live status before closing the issue.

## Task Breakdown

### Phase 1 Tasks

- [x] T001 [Plan:P1.1] Add a failing focused route/client test for configured root-health URL derivation, healthy payload validation, no-store semantics, and bounded failure; implement the minimum health transport and verify green.
- [x] T002 [Plan:P1.2] Add one failing hook test for connecting-to-online and implement the initial lifecycle tracer bullet.
- [x] T003 [Plan:P1.2] Add failing fake-timer tests for delayed-to-online, timeout/network/error-to-unavailable, retry, unmount, and stale responses; implement and refactor the complete lifecycle.
- [x] T004 [Plan:P2.2] Add failing homepage tests for honest accessible status and retry/cold-start guidance; replace the hardcoded badge and verify green.

### Phase 2 Tasks

- [x] T005 [Plan:P2.1] Add a failing semantic homepage test for a persistent benefit-first heading and supporting ingest/retrieve/analyze content; implement the hero and verify green.
- [x] T006 [Plan:P2.3] Add failing accessible-link tests for all four centralized destinations; implement project navigation and responsive focus styles and verify green.

### Phase 3 Tasks

- [x] T007 [Plan:P3.1] Add a failing metadata configuration test; implement canonical, Open Graph, and Twitter metadata and verify green.
- [x] T008 [Plan:P3.1] Add a failing image-route response test for the public image contract, content type, and 1200 x 630 dimensions; implement and refactor the Open Graph image route, then verify its response and production build.

### Phase 4 Tasks

- [x] T009 [Plan:P4.1] Run all frontend tests, type checking, lint comparison, and production build; inspect healthy, delayed, unavailable, retry, focus, and 390 px behavior locally.
- [ ] T010 [Plan:P4.1] After deployment, verify production external targets, canonical/OG/Twitter tags, social-card rendering, and live health transitions; record results and rollback readiness on issue #8.

## Commit Checkpoints

| After Tasks | Commit Scope | Required Validation |
| --- | --- | --- |
| T001 | Correct root health transport | Focused route/client tests |
| T002-T003 | Health lifecycle | Hook tests plus type checking |
| T004 | Honest homepage status | Homepage tests plus type checking |
| T005-T006 | Benefit-first homepage and project navigation | Homepage tests and 390 px structural review |
| T007-T008 | Canonical/social metadata and image | Metadata test, image response inspection, and production build |
| T009 | Source integration checkpoint | Full tests, type checking, lint comparison, build, and local state review |
| T010 | Deployment closeout | Production link, metadata, card, state, responsive, and rollback record |

## Validation Matrix

| Requirement | Scenario | Validation | Expected Evidence |
| --- | --- | --- | --- |
| REQ-001 | First visit and dismissed supporting intro | Homepage component test and browser inspection | Persistent primary heading explains asking and verifying before implementation terms; supporting pipeline explanation remains available |
| REQ-002 | Fast healthy, slow healthy, timeout, network/non-2xx, malformed/unhealthy payload, stale request | Route/client and fake-timer hook tests | Only current valid health becomes online; pending becomes delayed; bounded failures become unavailable |
| REQ-003 | Delayed probe succeeds and unavailable probe retries | Hook/component tests and local state inspection | Delayed guidance is conditional, late success becomes online, and retry starts a fresh connecting probe |
| REQ-004 | Technical evaluator opens each project destination | Component href assertions and deployed HTTP/browser check | Repository, project brief, API docs, and architecture targets are present, descriptive, and reachable |
| REQ-005 | Production page is shared | Metadata export and image-route response tests, build, image inspection, and crawler preview | Production canonical, intentional OG/Twitter values, and a public 1200 x 630 representative image render |
| REQ-006 | Keyboard, screen-reader status, desktop, and 390 px use | Role/live-region/focus tests plus browser inspection | Status is textual and polite, links focus visibly, controls operate by keyboard, and no horizontal overflow appears |
| REQ-007 | Source and production release gates | Full validation commands and issue closeout record | Automated suite passes or known baseline is documented; deployed checks and rollback result are recorded |

## Rollout and Rollback

- Rollout: ship the frontend-only health route, lifecycle, presentation, links,
  and metadata together to a preview; exercise deterministic health states and
  inspect the card before promoting. Production liveness remains backward
  compatible because backend `/health` is unchanged.
- Rollback: revert the frontend deployment/commit as one compatible unit. No
  schema, persisted data, API contract, secret, or backend deployment requires
  reversal.

## Definition of Done

- [ ] Every requirement has passing validation evidence.
- [ ] Every plan item has one primary module or work package.
- [ ] Module boundaries, interfaces, dependencies, and integration checks are explicit.
- [ ] Applicable implementation units are committed at coherent, validated checkpoints.
- [ ] Both traceability checkpoints validate with no unmapped IDs.
- [ ] Healthy, delayed, unavailable, retry, external link, metadata, social-card, focus, desktop, and 390 px deployed checks are recorded on issue #8.
