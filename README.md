# Document Intelligence Platform

A production-ready AI system for intelligent document analysis using **Retrieval-Augmented Generation (RAG)** with comprehensive traceability. The platform ingests documents, performs semantic search with pgvector, and delivers structured analysis with full citation tracking and cost transparency.

> **🌐 Live Demo:** [https://document-intelligence-platform.vercel.app](https://document-intelligence-platform.vercel.app)  
> **📚 Backend API:** [https://document-intelligence-platform.onrender.com](https://document-intelligence-platform.onrender.com)
>
> **Status:** ✅ Fully deployed and operational

## 🚀 Features

### Week 1: MVP Foundation

- ✅ **Document Upload & Processing**: PDF, Markdown, HTML, and text file ingestion
- ✅ **Intelligent Chunking**: Semantic document splitting with configurable parameters
- ✅ **Structured LLM Analysis**: JSON-mode analysis with confidence scoring
- ✅ **Cost Tracking**: Token usage and cost estimation for every operation
- ✅ **Modern UI**: Next.js frontend with real-time analysis display

### Week 2: RAG with Full Traceability ✅

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
4. **Ranking**: Sort by similarity score, apply threshold (default: 0.5)
5. **Context Building**: Format top-k chunks with source references
6. **LLM Analysis**: GPT-4o generates response with chunk citations
7. **Traceability**: Return full metadata (chunks used, scores, tokens, cost)

---

## 🌐 Production Deployment

### Live System

- **Frontend**: https://document-intelligence-platform.vercel.app (Vercel)
- **Backend API**: https://document-intelligence-platform.onrender.com (Render)
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

### Recent Production Fixes

✅ **Dependency Compatibility**: Upgraded to supabase 2.10.0, httpx 0.27.2  
✅ **UUID Serialization**: Fixed `model_dump(mode='json')` for PostgreSQL  
✅ **Null Byte Sanitization**: Strip `\x00` from PDF text before DB insert  
✅ **Vector Parsing**: Convert DB string vectors back to lists with `json.loads()`  
✅ **Similarity Threshold**: Lowered from 0.5 to 0.3 for better recall  
✅ **Auto-Embedding**: Documents automatically embedded after upload  
✅ **Vector Search Function**: Added `match_chunks()` SQL function for semantic search

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

### ✅ Week 1: MVP (Complete)

- Document upload & processing
- Chunking with configurable parameters
- LLM analysis with structured outputs
- Basic frontend

### ✅ Week 2: RAG + Traceability (Complete)

- Vector embeddings with Supabase
- Semantic search with pgvector
- Retrieval pipeline with comprehensive logging
- Citation tracking
- Frontend traceability visualization

### 📋 Week 3: Evaluation & Advanced Features (Planned)

- Batch evaluation framework
- Retrieval quality metrics
- LLM response evaluation
- A/B testing infrastructure
- Performance optimization

### 📋 Week 4: Production Readiness (Planned)

- Authentication & authorization
- Rate limiting & caching
- Monitoring & alerting
- Deployment configuration
- API documentation (OpenAPI/Swagger)

---

## 🤝 Contributing

Contributions welcome! This project follows a test-driven development approach:

1. Write tests for new features
2. Implement functionality
3. Ensure all tests pass (including existing ones)
4. Update documentation
5. Submit pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **OpenAI**: GPT-4o and text-embedding-3-small models
- **Supabase**: PostgreSQL + pgvector hosting
- **FastAPI**: High-performance Python API framework
- **Next.js**: React framework for production-ready frontends

---

**Built with ❤️ for production-grade document intelligence**
