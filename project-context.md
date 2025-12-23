# Document Intelligence Platform - Project Context

**Living Technical Specification**  
**Last Updated:** December 21, 2025  
**Status:** Initial Setup  
**Original Vision:** See `game_plan.md`

---

## Project Overview

An AI-powered document intelligence decision support system that ingests multiple documents (PDF/MD/HTML), performs retrieval + reasoning, and returns **structured, traceable outputs** with evaluation and operational guardrails.

**Current Phase:** Pre-implementation  
**Target Timeline:** 3-4 weeks to production MVP

---

## Core Objectives

1. **Document ingestion + normalization** pipeline (PDF/MD/HTML)
2. **Embeddings + vector search** with metadata filters
3. **Retrieval + reranking** with full traceability
4. **Schema-validated outputs** (JSON) with retry logic
5. **Evaluation framework** (golden tests + regression checks)
6. **Production hardening** (latency/cost/reliability controls)
7. **Clean UI + end-to-end deployment**

---

## Tech Stack (Actual Decisions)

### Frontend

- **Framework:** Next.js 14+ with App Router, TypeScript ✅
- **UI Library:** Tailwind CSS + shadcn/ui (optional components)
- **State Management:** React Server Components + Server Actions (built-in)
- **Deployment:** Vercel (free tier)

### Backend

- **Framework:** FastAPI (Python 3.11+) ✅
- **Language:** Python ✅
- **API Design:** RESTful with OpenAPI/Swagger auto-docs
- **Document Parsing Libraries:**
  - PDF: PyPDF2 / pdfplumber
  - HTML: Beautiful Soup 4
  - Markdown: markdown / python-markdown
- **Deployment:** Render (free tier)

### Data Layer

- **Primary Database:** PostgreSQL via Supabase ✅
- **Vector Database:** pgvector extension on Supabase PostgreSQL ✅
- **Alternatives Considered:** Pinecone (cost), Weaviate (complexity), Chroma (separate service)
- **Decision Rationale:** Single database simplifies architecture, pgvector sufficient for MVP scale
- **Storage:** Supabase Storage (S3-compatible, integrated with database)

### AI/ML

- **LLM Provider:** OpenAI (GPT-4 for reasoning, GPT-3.5 for cost-sensitive operations)
- **Embedding Model:** OpenAI text-embedding-3-small (or text-embedding-ada-002)
- **Schema Validation:** Pydantic v2 (Python native, excellent with FastAPI)
- **Retry Logic:** tenacity library for LLM call retries

### Infrastructure

- **Queue System:** Redis + RQ (Week 3+) or Supabase pg_cron for simple async jobs
- **Deployment Architecture:**
  - Frontend: Vercel (free tier, automatic CI/CD from GitHub)
  - Backend: Render (free tier, Python support)
  - Database: Supabase (free tier, 500MB database, 1GB storage)
- **Observability:**
  - Structured logging: Python logging + structlog
  - Metrics: Basic request timing, token counting
  - Future: Consider Sentry for error tracking

---

## Data Model

### Document

```
- id: UUID
- title: string
- type: enum (resume/jd/notes/policy/etc.)
- source: string
- version: string
- created_at: timestamp
- metadata: JSON
```

### Chunk

```
- id: UUID
- document_id: UUID (FK)
- chunk_index: integer
- text: text
- metadata: JSON
- embedding: vector
- created_at: timestamp
```

### AnalysisRun

```
- id: UUID
- inputs: JSON (doc ids + options)
- output_json: JSON
- citations: JSON
- latency_ms: integer
- cost: decimal
- created_at: timestamp
- status: enum
```

---

## Architecture Decisions

### Decision Log

| Date       | Decision                              | Rationale                                                                                                                                               | Trade-offs                                                                                                            |
| ---------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 2025-12-21 | Initialize project-context.md         | Track actual implementation vs. original plan                                                                                                           | N/A                                                                                                                   |
| 2025-12-21 | Python + FastAPI backend              | Superior document parsing libraries (PyPDF2, pdfplumber, BeautifulSoup), Pydantic for schema validation, faster MVP development for doc-heavy workflows | Learning curve if unfamiliar with Python; separate language from frontend                                             |
| 2025-12-21 | Next.js 14+ frontend                  | Industry standard for React, Server Components reduce client JS, great DX, Vercel deployment is zero-config                                             | App Router learning curve; could use simpler Vite+React but Next.js shows production-ready thinking                   |
| 2025-12-21 | PostgreSQL + pgvector (Supabase)      | Single database for relational + vector data, simpler architecture, free tier available, already have Supabase account                                  | Not as optimized as dedicated vector DBs (Pinecone/Weaviate) for massive scale; sufficient for MVP and interview demo |
| 2025-12-21 | Supabase + Render + Vercel deployment | Leverages existing free tier accounts, separation of concerns (DB/API/Frontend), independent scaling, mature ecosystems                                 | More moving parts than monolithic deployment; acceptable trade-off for clean architecture story                       |
| 2025-12-21 | pdfplumber over pypdf2 primary        | Better text extraction with layout preservation; pypdf2 as fallback ensures robustness                                                                  | Slightly larger dependency footprint; worth it for better PDF parsing quality                                         |
| 2025-12-21 | Updated DocumentType enum             | Changed from domain-specific (resume/jd) to format-based (pdf/markdown/html) for better generalization and Week 1 MVP focus                             | Less domain-specific metadata initially; can add document categorization in Week 2+                                   |
| 2025-12-22 | Sentence-boundary chunking            | Tries to break chunks at sentence endings for better semantic coherence; falls back to word boundaries if needed                                        | Slightly more complex than pure character-based chunking; better quality justifies complexity                         |
| 2025-12-22 | Chunk validation method               | Provides quality checks (size distribution, overlap verification) to catch chunking issues early                                                        | Additional code overhead; valuable for debugging and ensuring chunking quality                                        |

---

## Implementation Status

### Week 1 - MVP Foundations (In Progress)

- [x] Repo + service skeleton setup
  - [x] Backend: FastAPI structure with models, services, API routes
  - [x] Frontend: Next.js 14 with App Router and Tailwind CSS
  - [x] Configuration management (Pydantic settings)
  - [x] Environment variable templates
  - [x] README documentation for both frontend and backend
- [x] Document ingestion (PDF + Markdown + HTML)
  - [x] DocumentIngestionService with multi-format support
  - [x] PDF parsing (pdfplumber with PyPDF2 fallback)
  - [x] Markdown parsing (markdown library with HTML generation)
  - [x] HTML parsing (BeautifulSoup with script/style removal)
  - [x] File validation (size + type checking)
  - [x] /api/v1/documents/upload endpoint functional
  - [x] Unit tests (9 passing tests)
  - [x] Tested with real files (PDF, Markdown, HTML)
- [x] LLM reasoning v1 (schema-validated JSON outputs)
  - [x] OpenAI GPT-4 Turbo integration
  - [x] Schema validation with Pydantic AnalysisOutput
  - [x] Retry logic with exponential backoff
  - [x] Cost tracking and latency monitoring
  - [x] /api/v1/analyze endpoint functional and tested
- [x] Basic chunking v1 (fixed-size with overlap)
  - [x] ChunkingService with configurable chunk_size and overlap
  - [x] Sentence-boundary aware chunking (breaks at periods when possible)
  - [x] Word-boundary fallback for cleaner breaks
  - [x] Chunk metadata tracking (index, start/end positions)
  - [x] Integrated with document upload endpoint
  - [x] Validation method for chunk quality
  - [x] Unit tests (17 passing tests)
  - [x] Tested with documents of varying lengths (2-9 chunks generated)
- [x] Frontend: upload + analyze + display results
  - [x] UI layout and design
  - [x] API client library with TypeScript types
  - [x] React hooks for upload and analysis state management
  - [x] Functional drag-and-drop upload component
  - [x] Document upload display with metadata
  - [x] Analysis results display with color-coded sections
  - [x] Loading states and error handling
  - [x] Cost and latency display
  - [x] Citations display with relevance scores
  - [x] Responsive design with dark mode support

### Week 2 - Retrieval Pipeline (Not Started)

- [ ] Embeddings generation pipeline
- [ ] Vector search with metadata filters
- [ ] Traceability (chunk citations)
- [ ] Hybrid retrieval (optional)
- [ ] Reranking v1 (optional)

### Week 3 - Production Hardening (Not Started)

- [ ] Evaluation framework (10-20 golden test cases)
- [ ] Cost + latency controls
- [ ] Caching (embeddings + retrieval results)
- [ ] Async ingestion (background jobs)
- [ ] Reliability + security basics

### Week 4 - Polish & Deployment (Not Started)

- [ ] README polish with architecture diagram
- [ ] UI polish (cards, citations, download)
- [ ] Deployment (frontend + backend)
- [ ] Demo script + optional video

---

## Known Constraints & Non-Goals

### Explicitly Out of Scope

- ❌ Auto-applying to jobs
- ❌ Web scraping (LinkedIn, etc.)
- ❌ Building a "chatbot personality"
- ❌ Full-blown multi-tenant auth/billing
- ❌ Training models

### Current Constraints

- **Timeline:** 3-4 weeks total
- **Budget:** TBD
- **Resources:** Solo developer (Gawaineogilvie)

---

## Quality & Evaluation Strategy

### Evaluation Metrics (Week 3)

- Retrieval precision (manual labeling acceptable)
- Schema validity rate
- Confidence calibration heuristics
- Latency per request
- Cost per analysis run
- Token usage

### Golden Test Cases

- Target: 10-20 test cases with input docs + expected properties
- Location: `/eval` folder (to be created)

---

## Open Questions & Decisions Needed

1. **Tech Stack Finalization**

   - Confirm Next.js vs. alternatives for frontend
   - Confirm FastAPI vs. Node/NestJS for backend
   - Confirm pgvector vs. dedicated vector DB

2. **Document Types Priority**

   - Which 2 document types to start with? (PDF + Markdown recommended)

3. **Schema Design**

   - What specific output fields are needed for initial analysis?
   - Example from game plan: `overall_fit`, `strengths`, `gaps`, `risk_factors`, `confidence`, `recommended_focus`

4. **Deployment Strategy**
   - Confirm hosting providers
   - Environment setup requirements

---

## Resources & References

- **Original Vision:** [game_plan.md](./game_plan.md)
- **Repository:** document-intelligence-platform
- **Backend Documentation:** [backend/README.md](./backend/README.md)
- **Frontend Documentation:** [frontend/README.md](./frontend/README.md)
- **Documentation:** This file is the living spec - update as decisions are made

---

## Project Structure

```
document-intelligence-platform/
├── backend/                  # FastAPI Python service
│   ├── app/
│   │   ├── main.py          # FastAPI application entry
│   │   ├── config.py        # Settings & environment config
│   │   ├── models/          # Pydantic schemas & database models
│   │   ├── services/        # Business logic (document processing, LLM)
│   │   └── api/             # API route handlers
│   ├── tests/               # Backend tests
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/                # Next.js application
│   ├── app/                # App Router pages & layouts
│   │   ├── page.tsx       # Main upload & analysis page
│   │   └── layout.tsx     # Root layout
│   ├── components/         # React components (to be added)
│   ├── lib/               # Utilities & API client (to be added)
│   ├── package.json
│   └── .env.local.example
├── docs/                   # Additional documentation
├── _bmad/                  # BMAD workflow system
├── game_plan.md           # Original project vision
├── project-context.md     # This file - living technical spec
└── README.md              # Main project README
```

---

## Notes for BMAD Agents

> **Important:** This `project-context.md` file is the single source of truth for all BMAD agents working on this project. Always reference this file when making implementation decisions. When the actual implementation deviates from the game plan, update this document with rationale.

---

## Change Log

| Date       | Author    | Changes                                                                                                                            |
| ---------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 2025-12-21 | BMad Team | Initial project-context.md created based on game_plan.md                                                                           |
| 2025-12-21 | BMad Team | Finalized tech stack decisions (Python/FastAPI, Next.js, Supabase+pgvector)                                                        |
| 2025-12-21 | BMad Team | Week 1 scaffold complete: Backend skeleton (FastAPI + models + routes), Frontend (Next.js + UI layout), READMEs, project structure |
