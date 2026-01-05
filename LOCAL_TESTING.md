# Local Testing Guide

## Quick Start: Test the Fixes Locally

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (if not already done)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install/update dependencies
pip install -r requirements.txt

# Create .env file (if not exists)
cp .env.example .env
```

Edit `backend/.env`:

```bash
# Required for testing
OPENAI_API_KEY=your-openai-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-key

# Optional for local testing (leave empty to disable auth)
API_KEY=

# Other settings
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

**Run backend:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend should start at: http://localhost:8000

### 2. Frontend Setup

Open a **new terminal**:

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Create .env.local file
cp .env.local.example .env.local
```

Edit `frontend/.env.local`:

```bash
# For local testing with secure proxy
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
API_KEY=  # Leave empty for local testing (backend has auth disabled)
BACKEND_API_URL=http://localhost:8000/api/v1
```

**Run frontend:**

```bash
npm run dev
```

Frontend should start at: http://localhost:3000

### 3. Test the Upload Flow

1. Open browser to http://localhost:3000
2. Open DevTools (F12) → Console and Network tabs
3. Try uploading a PDF document

**Check backend terminal for logs:**

- Should see: `document_upload_requested`
- Should see: `document_upload_completed` (not errors!)
- Should show chunk count and metadata

**Check frontend Network tab:**

- Request to `/api/proxy?endpoint=/documents/upload`
- Status: 200 or 201 (success!)
- Response should have document ID and metadata

### 4. What Success Looks Like

**Backend logs:**

```
INFO document_upload_requested filename=test.pdf content_type=application/pdf
INFO chunking_service_initialized chunk_size=512 chunk_overlap=50
INFO document_upload_completed document_id=xxx-xxx-xxx total_chunks=5
```

**Frontend response:**

```json
{
  "id": "xxx-xxx-xxx",
  "title": "test.pdf",
  "type": "pdf",
  "metadata": {
    "chunks": {
      "total_chunks": 5,
      "average_chunk_size": 480
    }
  }
}
```

### 5. If You See Errors

#### "Cannot connect to database" or Supabase errors

- These are expected if you haven't set up Supabase yet
- The chunking should still work and return success
- Document won't be persisted (that's OK for testing the fix)

#### Still getting "missing doc_type" error

- Make sure you pulled the latest code: `git pull origin main`
- Restart the backend server
- Check that `backend/app/api/routes.py` has the `doc_type=doc_type.value` line

#### "proxy" parameter error

- Make sure `httpx==0.25.2` is installed
- Run: `pip install httpx==0.25.2`
- Restart backend

### 6. Quick Verification Commands

**Check if backend is running:**

```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**Check if the fix is in place:**

```bash
grep -A 2 "chunking_result = await chunking_service.chunk_document" backend/app/api/routes.py
# Should show: doc_type=doc_type.value
```

### 7. When to Deploy

✅ Deploy when:

- Backend starts without errors
- Upload endpoint returns 200/201
- You see `document_upload_completed` in logs
- No TypeError about missing doc_type
- No TypeError about proxy parameter

❌ Don't deploy if:

- Backend crashes on startup
- Upload returns 500 errors
- Still seeing TypeError in logs

---

## Troubleshooting

### Port already in use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Module not found errors

```bash
cd backend
pip install -r requirements.txt
```

### Frontend proxy not working locally

- Make sure both BACKEND_API_URL and API_KEY are in .env.local
- Restart frontend: Ctrl+C then `npm run dev`

---

## After Local Testing Succeeds

1. **Commit any remaining changes:**

   ```bash
   git add .
   git commit -m "Final fixes tested locally"
   git push origin main
   ```

2. **Deploy to Render:**

   - Push triggers auto-deploy (if enabled)
   - Or manually deploy in Render dashboard

3. **Test production:**
   - Wait for Render to finish deploying
   - Try upload on your Vercel deployment
   - Check Render logs for success messages

**Good luck! 🚀**
