# DocSage

**Intelligent document analysis powered by RAG — every answer cites exactly where it came from.**

Organizations need to quickly extract insights from large volumes of unstructured documents. Manual review is slow, keyword search misses semantically related content, and black-box AI answers can't be trusted without knowing their sources.

This system solves that with a **Retrieval-Augmented Generation (RAG)** pipeline: documents are chunked, embedded as vectors, and stored in a database. Queries retrieve the most semantically relevant chunks, which are passed as grounded context to an LLM — so every answer cites exactly where it came from, with full cost and retrieval transparency.

> **🌐 Live Demo:** [https://docsage.phoenix7.dev](https://docsage.phoenix7.dev)  
> **📚 Backend API:** [https://docsage-api.phoenix7.dev](https://docsage-api.phoenix7.dev)
>
> **Status:** ✅ Fully deployed and operational

## 🚀 Features

### Document Processing Pipeline

- ✅ **Document Upload & Processing**: PDF, Markdown, HTML, and text file ingestion
- ✅ **Intelligent Chunking**: Semantic document splitting with configurable parameters
- ✅ **Structured LLM Analysis**: JSON-mode analysis with confidence scoring
- ✅ **Cost Tracking**: Token usage and cost estimation for every operation
- ✅ **Modern UI**: Next.js frontend with real-time analysis display

### RAG with Semantic Search & Full Traceability

- ✅ **Vector Embeddings**: OpenAI text-embedding-3-small with Supabase storage
- ✅ **Semantic Search**: pgvector similarity search with metadata filtering (threshold: 0.3)
- ✅ **Retrieval Pipeline**: Query embedding → vector search → ranked results with logging
- ✅ **Citation Tracking**: Every analysis includes source chunk references
- ✅ **Retrieval Traceability**: Full visibility into which chunks influenced the response
- ✅ **Advanced Filtering**: Filter by document type, specific documents, or metadata
- ✅ **Frontend Visualization**: Interactive display of retrieved chunks with similarity scores
- ✅ **Automatic Embeddings**: Documents are automatically embedded after upload
- ✅ **Production Deployment**: Backend on Render, Frontend on Vercel, Database on Supabase
- ✅ **Secure API Proxy**: Server-side proxy hides API keys from client

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Production Deployment](#production-deployment)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [RAG Pipeline](#rag-pipeline)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  - Document Upload UI    - RAG Analysis Interface               │
│  - Retrieval Traceability Visualization                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Document    │  │  Chunking    │  │  Embedding   │         │
│  │  Service     │→ │  Service     │→ │  Service     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                            │                     │
│                                            ▼                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Retrieval  │← │    Vector    │← │  Supabase    │         │
│  │   Service    │  │   Search     │  │  + pgvector  │         │
│  └──────┬───────┘  └──────────────┘  └──────────────┘         │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │     LLM      │  (OpenAI GPT-4o)                             │
│  │   Service    │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### RAG Pipeline Flow

1. **Query Embedding**: User query → OpenAI embeddings (1536 dimensions)
2. **Vector Search**: Semantic similarity search via pgvector with cosine distance
3. **Filtering**: Apply document_ids, doc_type, or custom metadata filters
4. **Ranking**: Sort by similarity score, apply threshold (default: 0.3)
5. **Context Building**: Format top-k chunks with source references
6. **LLM Analysis**: GPT-4o generates response with chunk citations
7. **Traceability**: Return full metadata (chunks used, scores, tokens, cost)

### Why This Stack

| Component              | Chosen                 | Alternative Considered | Key Reason                                                                          |
| ---------------------- | ---------------------- | ---------------------- | ----------------------------------------------------------------------------------- |
| **Vector DB**          | pgvector + Supabase    | Pinecone, Weaviate     | One platform for relational + vector data — no separate service to operate          |
| **API Framework**      | FastAPI                | Flask, Django          | Native async, auto-generated OpenAPI docs, Pydantic models shared with DB layer     |
| **Embedding Model**    | text-embedding-3-small | text-embedding-3-large | 5× cheaper; no measurable retrieval quality difference at this document scale       |
| **LLM**                | GPT-4o                 | GPT-4o-mini, Claude    | Best structured JSON output quality; cost acceptable at low query volume            |
| **Retrieval Approach** | RAG                    | Fine-tuning            | Documents are dynamic and traceability is required — fine-tuning can't cite sources |

---

## 🌐 Production Deployment

### Live System

- **Frontend**: https://docsage.phoenix7.dev (Vercel)
- **Backend API**: https://docsage-api.phoenix7.dev (Render)
- **Database**: Supabase PostgreSQL with pgvector extension

### Infrastructure

**Frontend (Vercel):**

- Next.js 14 with TypeScript and Tailwind CSS
- Server-side API proxy (`/api/proxy`) to hide API keys
- Automatic deployments from main branch
- Environment variables: `API_KEY`, `BACKEND_API_URL`

**Backend (Render):**

- FastAPI with Python 3.12
- Auto-deploy from GitHub on push to main
- Environment variables: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `API_KEY`, `CORS_ORIGINS`
- Free tier with auto-sleep after inactivity (cold starts ~30s)

**Database (Supabase):**

- PostgreSQL 15 with pgvector 0.5.1
- Tables: `documents`, `chunks`, `embeddings`
- HNSW vector index for fast similarity search
- Foreign key constraints and cascade deletes

### Production Challenges & Debugging

Each of these was found in live deployment — not caught by tests. The pattern: symptom in prod → trace to root cause → targeted fix.

**UUID Serialization Failure**

- _Symptom_: Embedding generation endpoint returned 500 errors on every insert
- _Root cause_: Pydantic's `.dict()` preserved Python `UUID` objects; PostgreSQL rejected them as non-JSON-serializable types
- _Fix_: Switched to `model_dump(mode='json')` to coerce all values to JSON-serializable primitives before DB write

**Null Bytes in PDF Text**

- _Symptom_: PDF uploads crashed with PostgreSQL `invalid byte sequence` error
- _Root cause_: PyMuPDF extracts `\x00` null bytes from some PDFs; PostgreSQL text columns reject them entirely
- _Fix_: Added `.replace('\x00', '')` sanitization in the chunking pipeline before any DB write

**Vectors Stored as Strings**

- _Symptom_: Similarity search returned errors or wrong scores on documents that had been re-queried
- _Root cause_: pgvector returns vectors as comma-delimited strings in query results; code passed them directly into cosine distance as if they were Python lists
- _Fix_: Added `json.loads()` conversion step to parse DB vectors back to float lists before similarity calculation

**Similarity Threshold Too Strict (0.5 → 0.3)**

- _Symptom_: Queries on short documents (1–2 pages) consistently returned zero results
- _Root cause_: Default threshold of 0.5 was calibrated for longer documents with more semantic overlap; short docs produced lower similarity scores across the board
- _Fix_: Lowered to 0.3 after manually testing recall on real uploaded documents of different lengths

**Dependency Version Conflict on Deployment**

- _Symptom_: Render deployment failed with `ImportError` on startup — worked fine locally
- _Root cause_: `supabase 2.x` required `httpx >=0.27`; local env had been upgraded but `requirements.txt` was pinned to `0.24`
- _Fix_: Upgraded to `supabase==2.10.0` and `httpx==0.27.2`, both explicitly pinned in `requirements.txt`

**Manual Embedding Step (UX Failure)**

- _Symptom_: Users uploaded documents and immediately queried — got zero results
- _Root cause_: Embedding generation was a separate manual step; no feedback to indicate it hadn't run
- _Fix_: Auto-trigger embedding generation immediately after successful upload; added `match_chunks()` SQL function to support the vector search

### Security Features

- API keys stored server-side only (never exposed to client)
- Next.js API routes act as secure proxy
- CORS restricted to frontend domain
- Supabase service keys protected via environment variables

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account with pgvector enabled
- OpenAI API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   OPENAI_API_KEY=sk-...
#   SUPABASE_URL=https://xxx.supabase.co
#   SUPABASE_KEY=eyJhbG...

# Run database migrations
# (Ensure pgvector extension is enabled in Supabase)

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

Visit http://localhost:3000 to use the application.

---

## 📚 API Reference

Base URL: `http://localhost:8000/api/v1`

### Document Management

#### Upload Document

```http
POST /documents/upload
Content-Type: multipart/form-data

file: <binary>
doc_type: "resume" | "cover_letter" | "other"
```

**Response:**

```json
{
  "id": "uuid",
  "filename": "resume.pdf",
  "doc_type": "resume",
  "file_size": 45678,
  "upload_date": "2026-01-04T14:30:00Z"
}
```

#### Generate Embeddings

```http
POST /documents/{document_id}/generate-embeddings
```

**Response:**

```json
{
  "document_id": "uuid",
  "chunks_embedded": 12,
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "cost": 0.00015
}
```

### RAG Operations

#### Search Chunks

```http
POST /search/chunks
Content-Type: application/json

{
  "query": "What are the candidate's Python skills?",
  "top_k": 5,
  "similarity_threshold": 0.5,
  "filters": {
    "document_ids": ["uuid1", "uuid2"],
    "doc_type": "resume"
  }
}
```

**Response:**

```json
{
  "chunks": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "John_Doe_Resume.pdf",
      "doc_type": "resume",
      "chunk_index": 3,
      "text": "Python: 5 years experience with Django, FastAPI...",
      "similarity_score": 0.89
    }
  ],
  "metadata": {
    "chunks_retrieved": 5,
    "query_embedding_model": "text-embedding-3-small",
    "timestamp": "2026-01-04T14:35:00Z",
    "filters_applied": { "doc_type": "resume" }
  }
}
```

#### Analyze with RAG

```http
POST /analyze-rag
Content-Type: application/json

{
  "query": "Evaluate the candidate's qualifications for a senior backend role",
  "document_ids": ["uuid1"],
  "top_k": 5,
  "similarity_threshold": 0.5,
  "temperature": 0.7
}
```

**Response:**

```json
{
  "analysis_id": "uuid",
  "query": "Evaluate the candidate's qualifications...",
  "output": {
    "summary": "Strong backend engineer with 5+ years Python...",
    "key_points": ["..."],
    "confidence_score": 0.85
  },
  "citations": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "resume.pdf",
      "chunk_index": 3,
      "text": "Python: 5 years with Django..."
    }
  ],
  "retrieved_chunks": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_title": "resume.pdf",
      "doc_type": "resume",
      "chunk_index": 3,
      "text": "Python: 5 years...",
      "similarity_score": 0.89
    }
  ],
  "retrieval_metadata": {
    "chunks_retrieved": 5,
    "query_embedding_model": "text-embedding-3-small",
    "timestamp": "2026-01-04T14:35:00Z"
  },
  "llm_metadata": {
    "model": "gpt-4o-2024-11-20",
    "temperature": 0.7,
    "prompt_tokens": 850,
    "completion_tokens": 320,
    "total_tokens": 1170
  },
  "cost": {
    "embedding_cost": 0.00002,
    "llm_cost": 0.00585,
    "total_cost": 0.00587
  }
}
```

---

## 🔍 RAG Pipeline

### How It Works

The RAG (Retrieval-Augmented Generation) pipeline combines semantic search with LLM reasoning for accurate, source-grounded analysis:

1. **Query Processing**
   - User submits natural language query
   - Query is embedded using OpenAI's text-embedding-3-small (1536 dims)

2. **Semantic Retrieval**
   - Vector similarity search via pgvector (cosine distance)
   - Optional filters: document IDs, doc types, metadata
   - Returns top-k most relevant chunks above similarity threshold

3. **Context Construction**
   - Retrieved chunks formatted with source metadata
   - Example: `[CHUNK 1] [Doc: resume.pdf, Chunk 3] Python: 5 years...`

4. **LLM Analysis**
   - GPT-4o receives query + formatted context
   - Generates structured response citing source chunks
   - Configured temperature (default: 0.7) for creativity vs. precision

5. **Traceability Response**
   - Complete chunk details with similarity scores
   - Token usage and cost breakdown
   - Embedding and LLM model metadata

### Key Features

- **Citation Tracking**: Every claim links to source chunks
- **Similarity Scores**: Understand retrieval confidence (0.0-1.0)
- **Cost Transparency**: Embedding + LLM costs per request
- **Flexible Filtering**: Narrow search by document or type
- **Configurable Parameters**: Control top_k, threshold, temperature

---

## ⚖️ Design Decisions & Tradeoffs

The decisions below are the ones most likely to surface in a technical discussion. Each includes the tradeoff and the reasoning behind the choice made.

### Chunk Size (~500 tokens)

- **Tradeoff**: Larger chunks give the LLM more context per retrieval but reduce precision — a 2000-token chunk might match a query on a single sentence while flooding the context with irrelevant text. Smaller chunks improve precision but risk splitting semantically complete ideas across boundaries.
- **Decision**: ~500 tokens as a starting point. Short enough for targeted retrieval, large enough to preserve sentence-level coherence. The right value is corpus-dependent and should be evaluated against real queries.

### Similarity Threshold (0.3)

- **Tradeoff**: Higher threshold = higher precision, lower recall. A threshold of 0.5 filtered out relevant chunks on short documents; 0.1 returns noisy, semantically distant results.
- **Decision**: 0.3 — empirically tuned by running queries against real uploaded documents and checking whether returned chunks were actually relevant. This is a parameter that should be re-evaluated as document volume grows.

### pgvector vs. Dedicated Vector DB (Pinecone, Weaviate)

- **Tradeoff**: Pinecone offers managed vector search with better performance at scale and richer filtering, but adds another service to operate, another SDK, another cost center, and another failure point.
- **Decision**: pgvector keeps everything in one Supabase instance. At this scale (thousands of chunks, not billions), the performance difference is negligible. Operational simplicity wins. If this needed to scale to millions of chunks with sub-10ms latency SLAs, Pinecone would be the right call.

### RAG vs. Fine-Tuning

- **Tradeoff**: Fine-tuning bakes knowledge into model weights — fast inference, no retrieval step, no context window pressure. But it requires retraining whenever documents change, is expensive to iterate on, and cannot cite sources.
- **Decision**: RAG is the right choice when documents are dynamic and answer traceability is a requirement. Fine-tuning would be better for stable, high-volume Q&A on a fixed, well-curated corpus.

### text-embedding-3-small vs. text-embedding-3-large

- **Tradeoff**: The large model produces better embeddings but costs 5× more per token. At low query volume, the absolute cost difference is small — but it compounds quickly with large document ingestion.
- **Decision**: Small model. No measurable retrieval quality difference was observed on this dataset. Revisit if the corpus scales significantly or if retrieval quality degrades on niche technical content.

### Configuration Options

| Parameter              | Type   | Default  | Description                                 |
| ---------------------- | ------ | -------- | ------------------------------------------- |
| `query`                | string | required | Natural language question                   |
| `document_ids`         | UUID[] | null     | Limit search to specific docs               |
| `doc_type`             | string | null     | Filter by type (resume, cover_letter, etc.) |
| `top_k`                | int    | 5        | Number of chunks to retrieve                |
| `similarity_threshold` | float  | 0.3      | Minimum cosine similarity (0.0-1.0)         |
| `temperature`          | float  | 0.7      | LLM creativity (0.0=focused, 1.0=creative)  |

---

## ⚙️ Configuration

### Environment Variables

**Backend (`backend/.env`):**

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbG...

# Optional
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

**Frontend (`frontend/.env.local`):**

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database Setup

Enable pgvector extension in Supabase:

```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

Schema includes:

- `documents`: Uploaded files metadata
- `chunks`: Chunked document content
- `embeddings`: Vector embeddings (1536 dimensions)

---

## 🛠️ Development

### Project Structure

```
document-intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── services/     # Business logic
│   │   │   ├── chunking_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── retrieval.py      # RAG retrieval pipeline
│   │   │   └── llm_service.py    # LLM with citations
│   │   ├── models/       # Pydantic models
│   │   └── database/     # Supabase client
│   ├── tests/            # 37 comprehensive tests
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js pages
│   ├── lib/
│   │   ├── api-client.ts # Typed API client
│   │   └── hooks.ts      # React hooks (useRAGAnalysis)
│   └── package.json
└── README.md
```

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test suites
pytest tests/test_retrieval.py          # Retrieval pipeline (12 tests)
pytest tests/test_llm_service_rag.py    # LLM RAG features (13 tests)
pytest tests/test_rag_endpoints.py      # API endpoints (12 tests)
```

**Test Coverage:**

- ✅ 37 total tests
- ✅ Retrieval pipeline with filters
- ✅ LLM analysis with citations
- ✅ API endpoints with error handling
- ✅ Vector search operations
- ✅ Cost tracking and metadata

---

## 🧪 Testing

### Test Philosophy

All core functionality is tested with comprehensive coverage:

1. **Unit Tests**: Services tested in isolation with mocks
2. **Integration Tests**: API endpoints with TestClient
3. **Traceability Tests**: Verify complete metadata in responses
4. **Error Handling**: Invalid inputs, missing data, edge cases

### Example Test Output

```bash
$ pytest tests/test_rag_endpoints.py -v

tests/test_rag_endpoints.py::test_generate_embeddings_success PASSED
tests/test_rag_endpoints.py::test_search_chunks_basic PASSED
tests/test_rag_endpoints.py::test_search_chunks_with_filters PASSED
tests/test_rag_endpoints.py::test_analyze_rag_basic PASSED
tests/test_rag_endpoints.py::test_analyze_rag_with_document_filter PASSED
tests/test_rag_endpoints.py::test_rag_endpoint_traceability PASSED
...
======================== 12 passed in 2.34s =========================
```

---

## 📊 Frontend Features

### RAG Analysis Interface

The frontend provides rich visualization of RAG operations:

- **Query Input**: Natural language question entry
- **Filter Controls**: Select documents, types, parameters
- **Analysis Display**: Structured output with confidence scores
- **Retrieval Pipeline Section** (collapsible):
  - Chunks retrieved count
  - Embedding model used
  - LLM token usage (prompt/completion/total)
  - Temperature setting
  - Applied filters (JSON display)
- **Retrieved Chunks Section**:
  - Document title and chunk index badges
  - Similarity scores with visual progress bars
  - Chunk text preview (expandable)
  - Doc type indicators

### Example Screenshot Flow

1. Upload resume and cover letter
2. Generate embeddings for both documents
3. Ask: "What makes this candidate qualified for a backend role?"
4. View:
   - Retrieved 5 chunks (similarity: 0.85-0.92)
   - LLM analysis citing specific sections
   - Cost: $0.00587 total

---

## 🚦 Roadmap

### ✅ Phase 1: Document Processing (Complete)

- Document upload & processing
- Chunking with configurable parameters
- LLM analysis with structured outputs
- Basic frontend

### ✅ Phase 2: RAG + Traceability (Complete)

- Vector embeddings with Supabase
- Semantic search with pgvector
- Retrieval pipeline with comprehensive logging
- Citation tracking
- Frontend traceability visualization

### 📋 Phase 3: Evaluation & Advanced Features (Planned)

- Batch evaluation framework
- Retrieval quality metrics (Precision@k, MRR)
- LLM response evaluation
- A/B testing for retrieval parameters
- Performance optimization

### 📋 Phase 4: Production Hardening (Planned)

- Authentication & authorization (JWT)
- Rate limiting & caching (Redis)
- Monitoring & alerting
- API documentation (OpenAPI/Swagger)

---

## 📄 License

MIT License - See LICENSE file for details
