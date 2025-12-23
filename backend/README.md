# Document Intelligence Platform - Backend

FastAPI backend service for AI-powered document intelligence and decision support.

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension (via Supabase)
- OpenAI API key

### Installation

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

### Required Environment Variables

See `.env.example` for all required variables. Key ones:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase anon key
- `OPENAI_API_KEY` - Your OpenAI API key

## Running the Server

Development mode with auto-reload:

```bash
python -m app.main
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## API Endpoints

### Health Check

- `GET /` - Root health check
- `GET /health` - Health check endpoint

### Documents (Week 1 - To be implemented)

- `POST /api/v1/documents/upload` - Upload a document
- `GET /api/v1/documents` - List all documents
- `GET /api/v1/documents/{id}` - Get specific document

### Analysis (Week 1 - To be implemented)

- `POST /api/v1/analyze` - Run analysis on documents

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Configuration & settings
│   ├── models/           # Pydantic & database models
│   │   ├── schemas.py    # Request/response models
│   │   └── database.py   # Database models
│   ├── services/         # Business logic (to be implemented)
│   │   ├── document_ingestion.py
│   │   ├── chunking.py
│   │   └── llm_service.py
│   └── api/              # API routes
│       └── routes.py
├── tests/                # Tests (to be implemented)
├── requirements.txt      # Python dependencies
└── .env.example         # Example environment variables
```

## Week 1 Implementation Plan

- [x] Project structure created
- [x] FastAPI application skeleton
- [x] Configuration management
- [x] Pydantic models for validation
- [x] API route stubs
- [ ] Document upload implementation
- [ ] Document parsing (PDF, Markdown, HTML)
- [ ] Basic chunking
- [ ] LLM integration with schema validation
- [ ] Database integration with Supabase

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
flake8 app/
```

## Deployment

This backend is designed to deploy on Render:

1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy automatically from main branch

## Next Steps

See `project-context.md` in the root directory for the full implementation roadmap.
