# 🚀 DocSage - Live Demo

> **A production-grade AI system demonstrating Retrieval-Augmented Generation (RAG) with full traceability**

---

## 📍 Live Demo

**Frontend**: [https://docsage.phoenix7.dev](https://docsage.phoenix7.dev)  
**API Documentation**: [https://docsage-api.phoenix7.dev/docs](https://docsage-api.phoenix7.dev/docs)  
**GitHub Repository**: [https://github.com/ogilvieg/document-intelligence-platform](https://github.com/ogilvieg/document-intelligence-platform)

---

## 🎯 What This Demonstrates

This project showcases **production-ready full-stack AI development** with:

### Document Processing Pipeline

- **Document Processing**: Multi-format ingestion (PDF, Markdown, HTML, text)
- **Intelligent Chunking**: Semantic text splitting with configurable parameters
- **LLM Analysis**: GPT-4o with structured JSON outputs and confidence scoring
- **Cost Tracking**: Complete token usage and cost transparency
- **Modern Stack**: FastAPI + Next.js + TypeScript

### RAG with Semantic Search & Full Traceability ⭐ _(Demo Focus)_

- **Vector Embeddings**: OpenAI text-embedding-3-small with 1536 dimensions
- **Semantic Search**: pgvector + Supabase for sub-second similarity search
- **RAG Pipeline**: Complete retrieval-augmented generation with logging
- **Citation Tracking**: Every AI response includes source chunk references
- **Retrieval Transparency**: Full visibility into which chunks influenced responses
- **Advanced Filtering**: Search by document type, specific documents, or metadata
- **Interactive UI**: Real-time analysis with collapsible metadata sections

---

## 🎥 How to Use the Demo

### 1️⃣ Upload Documents

- Click **"Choose File"** and select a PDF, Markdown, HTML, or text file
- Select document type: Resume, Cover Letter, or Other
- Click **"Upload Document"**
- **Example files to try**: Upload a resume, job description, or technical document

### 2️⃣ Generate Embeddings

- After upload, click **"Generate Embeddings"**
- Watch as the system creates 1536-dimensional vector embeddings
- See chunk count, embedding model, and cost breakdown

### 3️⃣ Run RAG Analysis

- Enter a natural language query in the analysis box
- Examples:
  - "What are the candidate's strongest technical skills?"
  - "How does this candidate demonstrate leadership?"
  - "What relevant experience does this person have with Python?"
- Click **"Analyze with RAG"**

### 4️⃣ Explore Retrieval Traceability

- **Analysis Results**: See the AI-generated insights with confidence scores
- **Retrieval Pipeline** (collapsible): View:
  - Number of chunks retrieved
  - Embedding model used
  - LLM token usage (prompt/completion/total)
  - Temperature setting
  - Applied filters (JSON)
- **Retrieved Chunks**: See exactly which document sections influenced the response:
  - Document title and chunk index
  - Similarity scores (0.0-1.0) with visual progress bars
  - Original text from each chunk
  - Document type badges

---

## 💡 Key Features to Highlight

### Technical Architecture

**Backend Architecture** 🏗️

- **FastAPI** with async/await for high performance
- **Supabase + pgvector** for vector similarity search
- **OpenAI GPT-4o** for analysis, text-embedding-3-small for embeddings
- **Pydantic** for type-safe data validation
- **Structured logging** with comprehensive traceability

**Frontend Excellence** 🎨

- **Next.js 14** with React Server Components
- **TypeScript** throughout for type safety
- **Custom React hooks** (useRAGAnalysis, useDocumentUpload)
- **Responsive design** with Tailwind CSS
- **Real-time updates** and interactive UI elements

**Testing & Quality** ✅

- **37 comprehensive tests** (100% passing)
- **Unit tests** for services (retrieval, embeddings, LLM)
- **Integration tests** for API endpoints
- **pytest** with fixtures and mocks for isolated testing

**Production Ready** 🚀

- **Docker** containerization for consistent deployments
- **Environment-based configuration**
- **CORS** security properly configured
- **Health checks** and monitoring ready
- **Comprehensive documentation** (README, API docs, deployment guide)

### Business Use Cases

**Problem Solved** 🎯
Organizations need to quickly analyze multiple documents to extract insights and find relevant information. This system uses AI to:

- Instantly search across all uploaded documents
- Provide accurate, source-cited answers
- Show exactly where information came from (traceability)
- Compare and analyze documents efficiently

**Business Value** 💼

- **Time Savings**: What takes hours manually takes seconds
- **Accuracy**: AI-powered semantic search finds relevant info even with different wording
- **Transparency**: Every answer shows its sources (builds trust)
- **Scalability**: Handles hundreds of documents instantly

---

## 📊 Technical Stack

| Layer          | Technology                            | Purpose                               |
| -------------- | ------------------------------------- | ------------------------------------- |
| **Frontend**   | Next.js 14, React, TypeScript         | Modern SPA with server-side rendering |
| **Backend**    | FastAPI, Python 3.11, Uvicorn         | High-performance async API            |
| **Database**   | Supabase (PostgreSQL) + pgvector      | Cloud database with vector search     |
| **AI/ML**      | OpenAI GPT-4o, text-embedding-3-small | Language model and embeddings         |
| **Testing**    | pytest, FastAPI TestClient            | Comprehensive automated testing       |
| **Deployment** | Vercel (frontend), Render (backend)   | Cloud-native deployment               |
| **DevOps**     | Docker, docker-compose                | Containerization for consistency      |

---

## 📈 Metrics & Performance

**Test Coverage**

- ✅ 37 tests (12 retrieval + 13 LLM RAG + 12 endpoints)
- ✅ 100% pass rate
- ✅ Full coverage of critical paths

**Performance**

- ⚡ Embedding generation: ~2-3 seconds per document
- ⚡ Semantic search: <100ms for 1000s of chunks
- ⚡ RAG analysis: ~3-5 seconds end-to-end
- ⚡ API response time: <50ms (excluding AI calls)

**Code Quality**

- 📏 3,679 lines of production code
- 📚 500+ lines of comprehensive documentation
- 🎯 Type hints throughout (Python + TypeScript)
- 🧪 Integration + unit tests for all services

---

## 🔧 Engineering Decisions

### Production Challenges Solved

1. **PDF Null Byte Handling**: Sanitized `\x00` bytes extracted by PyMuPDF before PostgreSQL insert — these aren't caught in testing with clean PDFs
2. **Vector Type Mismatch**: pgvector returns vectors as strings in query results; added explicit parsing before cosine distance calculation
3. **Retrieval Threshold Tuning**: Lowered similarity threshold from 0.5 → 0.3 after diagnosing zero-result queries on short documents
4. **UUID Serialization**: Switched to `model_dump(mode='json')` after Pydantic's `.dict()` preserved non-serializable UUID types that PostgreSQL rejected
5. **Async Performance**: FastAPI's async/await for concurrent embedding generation and DB writes

### Architecture Decisions

- **pgvector over Pinecone**: One platform for relational + vector data — no separate service to operate at this scale
- **RAG over fine-tuning**: Documents are dynamic and every answer must cite its source — fine-tuning can't do either
- **text-embedding-3-small**: 5× cheaper than the large variant with no measurable quality difference on this corpus
- **FastAPI**: Native async, auto-generated OpenAPI docs, Pydantic models shared across DB and API layers

---

## 🔮 Planned Enhancements

### Next Phase

- **Batch Evaluation Framework**: Systematic testing of retrieval quality
- **Retrieval Metrics**: Precision@k, recall, MRR for search quality
- **LLM Response Eval**: Automated quality scoring for AI responses
- **A/B Testing**: Compare different retrieval parameters
- **Multi-tenant Auth**: JWT-based authentication for multiple users
- **Rate Limiting**: Protect against API abuse
- **Caching Layer**: Redis for frequently accessed embeddings
- **Async Processing**: Background jobs for long-running operations

---

**Thank you for checking out this project!** 🙏

---

_Last Updated: May 7, 2026_  
_Project Status: ✅ Production-Ready Demo_
