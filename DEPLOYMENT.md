# Deployment Guide

This guide will help you deploy the Document Intelligence Platform to production.

## 🎯 Quick Deploy Overview

**Frontend:** Vercel (recommended for Next.js)  
**Backend:** Railway or Render (with PostgreSQL support)  
**Database:** Supabase (already cloud-hosted with pgvector)

**Total deployment time:** ~30-45 minutes

---

## 📋 Prerequisites

Before deploying, ensure you have:

- [x] GitHub account (to connect repositories)
- [x] Supabase account with project created
- [x] OpenAI API key with credits
- [x] Vercel account (free tier works)
- [x] Railway or Render account (free tier works)

---

## Step 1: Prepare Supabase (Database)

### 1.1 Enable pgvector Extension

In your Supabase SQL Editor, run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 1.2 Run Database Migrations

Execute the schema SQL found in `backend/app/database/schema.sql` (or create tables manually):

```sql
-- Your documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    doc_type TEXT,
    file_size INTEGER,
    upload_date TIMESTAMP DEFAULT NOW()
);

-- Your chunks table
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Your embeddings table with pgvector
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID REFERENCES chunks(id) ON DELETE CASCADE,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for similarity search
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

### 1.3 Get Connection Details

From Supabase Dashboard > Settings > API:

- Copy `Project URL` (SUPABASE_URL)
- Copy `anon public` key (SUPABASE_KEY)
- Copy `service_role` key (SUPABASE_SERVICE_KEY) - keep this secret!

---

## Step 2: Deploy Backend (Railway or Render)

### Option A: Railway (Recommended)

1. **Create New Project**

   - Go to [railway.app](https://railway.app)
   - Click "New Project" > "Deploy from GitHub repo"
   - Select your `document-intelligence-platform` repo
   - Railway will auto-detect the Dockerfile

2. **Configure Build**

   - Set root directory: `/backend`
   - Dockerfile path: `/backend/Dockerfile`

3. **Add Environment Variables**

   ```
   OPENAI_API_KEY=sk-your-key-here
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   LOG_LEVEL=INFO
   CORS_ORIGINS=https://your-frontend-domain.vercel.app
   ```

4. **Deploy**

   - Railway will automatically build and deploy
   - Get your backend URL from Railway dashboard
   - Example: `https://your-app.up.railway.app`

5. **Verify Deployment**
   - Visit: `https://your-app.up.railway.app/health`
   - Should return: `{"status": "healthy"}`
   - Visit: `https://your-app.up.railway.app/docs` for API documentation

### Option B: Render

1. **Create New Web Service**

   - Go to [render.com](https://render.com)
   - Click "New+" > "Web Service"
   - Connect your GitHub repository
   - Select `document-intelligence-platform`

2. **Configure Service**

   - Name: `doc-intelligence-api`
   - Root Directory: `backend`
   - Environment: `Docker`
   - Instance Type: `Free` or `Starter`

3. **Add Environment Variables** (same as Railway above)

4. **Deploy**
   - Render will build and deploy automatically
   - Get your backend URL: `https://your-app.onrender.com`

---

## Step 3: Deploy Frontend (Vercel)

### 3.1 Deploy to Vercel

1. **Import Project**

   - Go to [vercel.com](https://vercel.com)
   - Click "Add New..." > "Project"
   - Import your `document-intelligence-platform` repository

2. **Configure Build**

   - Framework Preset: `Next.js` (auto-detected)
   - Root Directory: `frontend`
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

3. **Add Environment Variable**

   ```
   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
   ```

   (Use your Railway/Render backend URL from Step 2)

4. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Your frontend URL: `https://your-app.vercel.app`

### 3.2 Update Backend CORS

Go back to your backend environment variables and update:

```
CORS_ORIGINS=https://your-app.vercel.app
```

Redeploy backend for CORS changes to take effect.

---

## Step 4: Add Basic Authentication (Recommended)

### 4.1 Generate API Key

```bash
# Generate a secure random key
openssl rand -hex 32
```

### 4.2 Add to Backend Environment

Add this environment variable to Railway/Render:

```
API_KEY=your-generated-secure-key-here
```

### 4.3 Update Backend Code (Optional)

If you want to enforce API key authentication, you'll need to add a middleware. Here's a simple example:

```python
# In backend/app/main.py, add:

from fastapi import Header, HTTPException
import os

async def verify_api_key(x_api_key: str = Header(None)):
    expected_key = os.getenv("API_KEY")
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Then add dependency to protected routes:
@router.post("/analyze-rag", dependencies=[Depends(verify_api_key)])
async def analyze_with_rag(...):
    ...
```

### 4.4 Update Frontend

Add API key header in `frontend/lib/api-client.ts`:

```typescript
const headers: Record<string, string> = {
  "Content-Type": "application/json",
};

// Add API key if configured
const apiKey = process.env.NEXT_PUBLIC_API_KEY;
if (apiKey) {
  headers["X-API-Key"] = apiKey;
}
```

---

## Step 5: Test Your Deployment

### 5.1 Backend Health Check

Visit: `https://your-backend-url.com/health`

Expected response:

```json
{
  "status": "healthy"
}
```

### 5.2 Backend API Docs

Visit: `https://your-backend-url.com/docs`

You should see the FastAPI Swagger UI with all endpoints documented.

### 5.3 Frontend Application

Visit: `https://your-app.vercel.app`

Test the full workflow:

1. Upload a document (PDF or text)
2. Generate embeddings
3. Run RAG analysis
4. Verify retrieval traceability is displayed

---

## Step 6: Create Demo Documentation

Create a `DEMO.md` file with:

- **Live Demo URL**: Link to your Vercel deployment
- **Screenshots**: Key features and UI
- **Sample Documents**: What documents to try
- **Tech Stack**: Highlight RAG, pgvector, OpenAI, etc.
- **Features**: List Week 1 and Week 2 capabilities

---

## 🎨 Optional Enhancements

### Add Custom Domain (Vercel)

1. Go to Vercel Project Settings > Domains
2. Add your custom domain
3. Update DNS records as instructed

### Add Monitoring (Recommended)

- **Vercel**: Built-in analytics and logs
- **Railway**: Built-in logs and metrics
- **Sentry**: Add error tracking
  ```bash
  npm install @sentry/nextjs @sentry/node
  ```

### Add Rate Limiting

Protect against abuse with rate limiting:

- Use `slowapi` for FastAPI
- Add to `requirements.txt`: `slowapi==0.1.9`

---

## 📊 Cost Estimate (Monthly)

| Service                  | Tier          | Cost    |
| ------------------------ | ------------- | ------- |
| Vercel (Frontend)        | Hobby         | $0      |
| Railway/Render (Backend) | Free/Starter  | $0-5    |
| Supabase                 | Free          | $0      |
| OpenAI API               | Pay-as-you-go | $5-20\* |

\*OpenAI costs depend on usage. For demo purposes with limited traffic, expect $5-20/month.

---

## 🚨 Security Checklist

Before sharing publicly:

- [ ] API key authentication enabled
- [ ] CORS properly configured (only your frontend URL)
- [ ] Supabase service key is secret (not in frontend)
- [ ] OpenAI API key is secret
- [ ] File upload size limits enforced
- [ ] Rate limiting configured (optional but recommended)
- [ ] Environment variables not committed to Git

---

## 🎯 Production-Ready Checklist

- [ ] Backend deployed and healthy
- [ ] Frontend deployed and accessible
- [ ] Full RAG workflow tested end-to-end
- [ ] DEMO.md created with screenshots
- [ ] README.md has live demo link
- [ ] GitHub repository is public
- [ ] Sample documents prepared for demo

---

## 📞 Troubleshooting

### Backend won't start

- Check logs in Railway/Render dashboard
- Verify all environment variables are set
- Ensure Supabase connection details are correct

### Frontend can't reach backend

- Check CORS_ORIGINS in backend
- Verify NEXT_PUBLIC_API_URL in frontend
- Check backend /health endpoint

### "Unauthorized" errors

- Verify API key matches on both frontend and backend
- Check X-API-Key header is being sent

### Embeddings failing

- Check OpenAI API key is valid
- Verify you have credits in OpenAI account
- Check OpenAI API logs for errors

---

## 🚀 Next Steps After Deployment

1. **Add demo data**: Pre-load sample resumes/documents
2. **Record demo video**: Screen recording of key features
3. **Create LinkedIn post**: Share your deployed project
4. **Share your work**: Add link to live demo in your portfolio

---

**Congratulations!** Your RAG-powered document intelligence platform is now live! 🎉
