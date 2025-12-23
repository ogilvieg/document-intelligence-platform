# Week 1 MVP - User Demo Guide

## Setup Instructions

### 1. Start Backend Server

```bash
cd backend
source venv/bin/activate
python -m app.main
```

Backend will be available at: http://localhost:8000

### 2. Start Frontend Server

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:3000

### 3. Verify Both Servers

- Backend health: http://localhost:8000/health
- Frontend: http://localhost:3000

## Demo Walkthrough

### Step 1: Upload a Document

1. Open http://localhost:3000 in your browser
2. **Option A:** Drag and drop a file onto the upload zone
   - Supports: PDF, Markdown (.md), HTML, Text files
   - Max size: 10MB
3. **Option B:** Click the upload zone to browse files
4. Watch the upload progress spinner
5. See document metadata displayed:
   - Title and filename
   - Document type
   - Text length
   - Number of chunks created
   - Average chunk size

### Step 2: Run Analysis

1. Click the "Run Analysis" button
2. Watch the "Analyzing..." loading state
3. Wait for analysis to complete (~10 seconds)

### Step 3: View Results

Results are displayed in color-coded sections:

#### 🔵 Overall Assessment (Blue)

- Summary of the analysis
- Confidence score with visual progress bar

#### ✅ Strengths (Green)

- Key strengths identified
- Positive findings

#### ⚠️ Gaps & Areas for Improvement (Amber)

- Areas needing attention
- Improvement opportunities

#### ⚡ Risk Factors (Red)

- Potential concerns
- Risk identification

#### → Recommended Focus Areas (Purple)

- Action items
- Priority recommendations

#### 📚 Source Citations

- Chunk references
- Relevance scores
- Source document info

### Step 4: Performance Metrics

At the top of results:

- ⚡ **Latency:** Time taken for analysis
- 💰 **Cost:** API cost in USD

### Step 5: Upload Another Document

Click "Clear & Upload New" to reset and try another file

## Test Files Available

Located in `/backend/test_files/`:

1. **test.md** - Short markdown document (~600 chars)

   - Creates 2 chunks
   - Good for quick testing

2. **long_test.md** - Long markdown document (~3.5KB)

   - Creates 9 chunks
   - Tests chunking with multiple sections

3. **test.html** - HTML document with formatting

   - Tests HTML parsing and cleaning
   - Removes scripts and styles

4. **test.pdf** - PDF document
   - Tests PDF parsing
   - Shows page count

## Features to Highlight

### 1. Intelligent Chunking

- Documents are automatically split into chunks
- Sentence-boundary aware
- Configurable overlap (50 chars default)
- Metadata displayed in upload confirmation

### 2. Schema-Validated Analysis

- Structured output format
- Consistent results every time
- Type-safe throughout

### 3. Cost & Latency Tracking

- Real-time cost calculation
- Latency monitoring
- Displayed with every analysis

### 4. Error Handling

Try these scenarios:

- Upload a very large file (>10MB) → See size error
- Upload an unsupported file type → See type error
- Run analysis without backend running → See connection error

### 5. Responsive Design

- Try on mobile, tablet, desktop
- Dark mode support (system preference)
- Smooth animations and transitions

## API Endpoints Demonstrated

### POST /api/v1/documents/upload

Request:

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test.md" \
  -F "title=Test Document"
```

Response:

```json
{
  "id": "uuid",
  "title": "Test Document",
  "type": "markdown",
  "metadata": {
    "text_length": 597,
    "chunks": {
      "total_chunks": 2,
      "average_chunk_size": 323.0
    }
  }
}
```

### POST /api/v1/analyze

Request:

```json
{
  "document_ids": ["uuid"],
  "options": {
    "context": "Additional context..."
  }
}
```

Response:

```json
{
  "id": "uuid",
  "output": {
    "overall_fit": "Assessment text...",
    "strengths": ["..."],
    "gaps": ["..."],
    "risk_factors": ["..."],
    "confidence": 0.85,
    "recommended_focus": ["..."]
  },
  "citations": [...],
  "latency_ms": 9738,
  "cost": 0.01055
}
```

### GET /health

Response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-12-22T..."
}
```

## Technical Highlights

### Backend Architecture

- **FastAPI** for high-performance API
- **Pydantic** for schema validation
- **OpenAI GPT-4 Turbo** for analysis
- **pdfplumber + PyPDF2** for PDF parsing
- **BeautifulSoup** for HTML parsing
- **Structured logging** with structlog

### Frontend Architecture

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **React Hooks** for state management
- **Custom API client** with error handling

### Testing

- **29 backend tests passing**
- **Manual frontend testing complete**
- **End-to-end flow verified**

## Common Issues & Solutions

### Backend not starting?

```bash
cd backend
source venv/bin/activate
python -m app.main
```

### Frontend not starting?

```bash
cd frontend
npm install
npm run dev
```

### CORS errors?

- Ensure backend has CORS enabled for localhost:3000
- Check NEXT_PUBLIC_API_URL in .env.local

### Upload failing?

- Check file size (<10MB)
- Verify file type (PDF, MD, HTML, TXT)
- Check backend logs for errors

### Analysis not working?

- Verify OPENAI_API_KEY in backend/.env
- Check backend logs for API errors
- Ensure document was uploaded successfully

## Next Steps (Week 2)

Coming soon:

- ✅ Database integration (Supabase)
- ✅ Vector embeddings
- ✅ Semantic search
- ✅ Real citation retrieval
- ✅ Document management UI
- ✅ Analysis history

---

**Week 1 Status:** ✅ **COMPLETE**

All core functionality implemented and tested:

- ✅ Document upload (PDF, MD, HTML)
- ✅ Intelligent chunking
- ✅ LLM analysis
- ✅ Results display
- ✅ Error handling
- ✅ Performance tracking
