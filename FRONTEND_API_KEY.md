# Frontend API Key Configuration

## ⚠️ Security Warning from Vercel

If you see: **"This key, which is prefixed with NEXT*PUBLIC* and includes the term KEY, might expose sensitive information to the browser"**

This is correct! Environment variables prefixed with `NEXT_PUBLIC_` are **exposed to the browser** and visible in:

- Browser DevTools Network tab
- JavaScript bundle source
- Anyone inspecting your frontend

## Two Approaches

### Approach 1: Direct Backend Calls (Quick Demo) ⚡

**Best for**: Private demos, portfolio projects, controlled access

**Pros**: Simple, fast to implement  
**Cons**: API key visible in browser

This is what's currently implemented. It's **acceptable for demo purposes** where you:

- Share the link privately
- Rotate the API key after demos
- Monitor usage

### Approach 2: Next.js API Proxy (Recommended) 🔒

**Best for**: Portfolio projects, semi-public deployments

**Pros**: API key stays server-side, more secure  
**Cons**: Requires Next.js API routes

I've created the proxy implementation for you. See "Switching to Secure Proxy" below.

---

## Current Setup (Approach 1)

The frontend now sends the API key via the `X-API-Key` header for authentication with the backend.

## Setup Steps

### 1. Get Your Backend API Key

Your backend API key is configured in the Render dashboard as the `API_KEY` environment variable. If you haven't set this yet:

```bash
# Generate a secure API key
openssl rand -hex 32
```

### 2. Add API Key to Vercel

1. Go to your Vercel dashboard: https://vercel.com/dashboard
2. Select your deployed project
3. Go to **Settings** → **Environment Variables**
4. Add a new environment variable:
   - **Name**: `NEXT_PUBLIC_API_KEY`
   - **Value**: Your API key from the backend (same value as backend's `API_KEY`)
   - **Environments**: Select all (Production, Preview, Development)
5. Click **Save**

### 3. Redeploy Frontend

After adding the environment variable, Vercel will automatically trigger a new deployment. If it doesn't:

1. Go to **Deployments** tab
2. Click the three dots on the latest deployment
3. Select **Redeploy**

## Local Development

For local development, create a `.env.local` file in the `frontend` directory:

```bash
cd frontend
cp .env.local.example .env.local
```

Then edit `.env.local` and add your API key:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_KEY=your-actual-api-key-here
```

**Important**: Never commit `.env.local` to git. It's already in `.gitignore`.

## How It Works

The `ApiClient` class now:

1. Accepts an optional `apiKey` parameter in the constructor
2. Falls back to `process.env.NEXT_PUBLIC_API_KEY` if not provided
3. Includes the API key in the `X-API-Key` header for all authenticated requests

Example usage:

```typescript
// Uses NEXT_PUBLIC_API_KEY from environment
const client = new APIClient();

// Or pass explicitly
const client = new APIClient(API_BASE_URL, "your-api-key");
```

## Testing

After deployment, test the authentication:

```bash
# Should fail without API key (401)
curl https://your-backend.onrender.com/api/v1/documents/upload \
  -X POST

# Should work with API key
curl https://your-backend.onrender.com/api/v1/documents/upload \
  -X POST \
  -H "X-API-Key: your-api-key-here"
```

## Security Notes

- The API key is exposed in the frontend (browser can see it in Network tab)
- This is acceptable for demo purposes where you control who has access
- For production with untrusted users, consider:
  - Moving to server-side API routes in Next.js
  - Implementing user authentication (OAuth, JWT)
  - Rate limiting per user/session
  - Monitoring API usage

## Troubleshooting

### "Unauthorized" or 401 errors

- Check that `NEXT_PUBLIC_API_KEY` is set in Vercel environment variables
- Verify it matches your backend's `API_KEY` exactly
- Redeploy after adding the environment variable

### API key not being sent

- Check browser DevTools → Network tab → Request Headers
- Should see: `X-API-Key: your-key-here`
- If missing, the environment variable wasn't loaded (redeploy needed)

### CORS errors

- Update your backend's `CORS_ORIGINS` environment variable in Render
- Add your Vercel frontend URL: `https://your-app.vercel.app`
- Render will auto-redeploy with the new CORS settings

---

## Switching to Secure Proxy (Approach 2)

If you want to keep the API key server-side, follow these steps:

### 1. Update Environment Variables in Vercel

**Remove:**

- `NEXT_PUBLIC_API_KEY` (delete this variable)

**Add:**

- `API_KEY` (without NEXT*PUBLIC* prefix - your backend API key)
- `BACKEND_API_URL` (your Render backend URL, e.g., `https://your-app.onrender.com/api/v1`)

### 2. Update Your Components

Replace the API client import in your React components:

```typescript
// OLD: Direct API calls
import { apiClient } from "@/lib/api-client";

// NEW: Secure proxy
import { secureApiClient } from "@/lib/secure-api-client";

// Usage stays the same
const result = await secureApiClient.uploadDocument(file);
```

### 3. How the Proxy Works

```
Browser → Next.js API Route (/api/proxy) → Backend (with API key)
```

- Browser calls `/api/proxy?endpoint=/documents/upload`
- Next.js server adds `X-API-Key` header (from `API_KEY` env var)
- Backend receives authenticated request
- API key never reaches the browser

### 4. Files Created for You

- `frontend/app/api/proxy/route.ts` - Next.js API route handler
- `frontend/lib/secure-api-client.ts` - Client that uses the proxy

### 5. Testing

```bash
# API key should NOT be visible in browser Network tab
# Check that requests go to /api/proxy instead of backend directly
```

### 6. Benefits

- ✅ API key stays server-side
- ✅ No Vercel security warnings
- ✅ More professional for portfolio
- ✅ Easy to add rate limiting later
- ✅ Centralized error handling

---

## Decision Guide

**Use Approach 1 (Current)** if:

- ✅ Quick demo for specific people
- ✅ You'll rotate the API key after
- ✅ You want simplicity

**Use Approach 2 (Proxy)** if:

- ✅ Portfolio piece for job applications
- ✅ Semi-public deployment
- ✅ Want professional best practices
- ✅ Planning to add rate limiting
