# Deploy with API Key Authentication

## Quick Setup Guide

### Step 1: Generate API Key

```bash
openssl rand -hex 32
```

Example output: `092cf417739113fbda1167bfcadb95f10309905ecf3598482ac5279a99a9325c`

**Keep this secure!** Don't commit it to Git.

---

### Step 2: Deploy Backend (Render)

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo: `ogilvieg/document-intelligence-platform`
3. Configure:

   - **Name:** `doc-intelligence-api`
   - **Root Directory:** `backend`
   - **Environment:** Docker
   - **Instance Type:** Free (or Starter)

4. **Add Environment Variables:**

   ```
   OPENAI_API_KEY=sk-your-openai-key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_SERVICE_KEY=your-service-key
   API_KEY=092cf417739113fbda1167bfcadb95f10309905ecf3598482ac5279a99a9325c
   CORS_ORIGINS=https://your-app.vercel.app
   LOG_LEVEL=INFO
   ```

5. Deploy! ✅

**Your backend URL:** `https://doc-intelligence-api.onrender.com`

---

### Step 3: Deploy Frontend (Vercel)

1. Go to https://vercel.com → Add New → Project
2. Import `ogilvieg/document-intelligence-platform`
3. Configure:

   - **Root Directory:** `frontend`
   - **Framework:** Next.js (auto-detected)

4. **Add Environment Variable:**

   ```
   NEXT_PUBLIC_API_URL=https://doc-intelligence-api.onrender.com
   ```

5. Deploy! ✅

**Your frontend URL:** `https://your-app.vercel.app`

---

### Step 4: Update Backend CORS

Go back to Render → Environment Variables → Update:

```
CORS_ORIGINS=https://your-app.vercel.app
```

Redeploy backend.

---

### Step 5: Test with API Key

#### Test Backend Health (No Auth Required)

```bash
curl https://doc-intelligence-api.onrender.com/health
```

#### Test Protected Endpoint (Auth Required)

```bash
curl -X POST https://doc-intelligence-api.onrender.com/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 092cf417739113fbda1167bfcadb95f10309905ecf3598482ac5279a99a9325c" \
  -d '{"query": "Test query", "document_context": "Test context"}'
```

**Expected without API key:**

```json
{
  "detail": "API key required. Please provide X-API-Key header."
}
```

**Expected with valid API key:**

```json
{
  "analysis": "...",
  "confidence": 0.95
}
```

---

## Sharing with Others

### Option A: Private Access Only

**Don't publish the live URL publicly.** Instead, share it via:

1. **Email/LinkedIn** to specific contacts:

   > "Live demo available at: https://your-app.vercel.app
   > API Key: `092cf...9325c` (for authenticated access)"

2. **Resume** (password-protected PDF)

3. **Portfolio website** (behind login if possible)

### Option B: Public with Instructions

In your README or DEMO.md:

```markdown
## Live Demo

**Frontend:** https://your-app.vercel.app

**Note:** API requests require authentication. Contact me for an API key.
```

Then share the key privately with interested parties.

---

## Security Best Practices

### ✅ DO:

- Generate unique API keys for different users
- Rotate keys periodically
- Monitor usage via Render logs
- Use rate limiting (see DEPLOYMENT.md)

### ❌ DON'T:

- Commit API keys to Git
- Share keys publicly on GitHub/Reddit/forums
- Use the same key for dev and production
- Leave auth disabled in production

---

## Monitoring API Usage

### Check Render Logs

```
Render Dashboard → Your Service → Logs
```

Look for:

- `api_key_verified` - Successful auth
- `api_key_invalid` - Failed attempts
- `api_key_missing` - Missing header

### Track OpenAI Costs

https://platform.openai.com/usage

---

## Revoking Access

### Rotate API Key

1. Generate new key: `openssl rand -hex 32`
2. Update Render environment variable
3. Redeploy backend
4. Share new key with authorized users only

**Old key immediately invalidated!**

---

## Troubleshooting

### "API key required" on all endpoints

✅ **Expected!** This means auth is working.

- Share the `X-API-Key` header with users

### Frontend can't reach backend

- Check CORS_ORIGINS includes your Vercel URL
- Verify NEXT_PUBLIC_API_URL is correct

### 403 Forbidden with key

- Double-check the key matches Render environment variable
- No extra spaces or quotes in the key

---

**You're ready to deploy! 🚀**

Follow DEPLOYMENT.md for complete step-by-step instructions.
