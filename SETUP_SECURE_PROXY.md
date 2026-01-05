# Quick Start Guide: Secure Proxy Setup

This guide will help you switch from direct backend calls to the secure proxy approach.

## ✅ What's Been Done

1. **Updated Code**:

   - ✅ `frontend/lib/hooks.ts` - Now uses `secureApiClient`
   - ✅ `frontend/app/api/proxy/route.ts` - Proxy route created
   - ✅ `frontend/lib/secure-api-client.ts` - Secure client created

2. **Files Ready to Deploy**:
   - All code changes committed to main branch
   - Vercel will auto-deploy when you push

## 🚀 Your Action Items

### 1. Update Vercel Environment Variables

Go to: https://vercel.com/dashboard → Your Project → Settings → Environment Variables

**DELETE this variable:**

- ❌ `NEXT_PUBLIC_API_KEY`

**ADD these variables:**

| Variable Name     | Value                                           | Environments                     |
| ----------------- | ----------------------------------------------- | -------------------------------- |
| `API_KEY`         | Your backend API key (same as Render's API_KEY) | Production, Preview, Development |
| `BACKEND_API_URL` | `https://your-app.onrender.com/api/v1`          | Production, Preview, Development |

**Example values:**

```
API_KEY=092cf417739113fbda1167bfcadb95f10309905ecf3598482ac5279a99a9325c
BACKEND_API_URL=https://document-intelligence-backend-xyz.onrender.com/api/v1
```

### 2. Get Your Render Backend URL

1. Go to your Render dashboard
2. Click on your backend service
3. Copy the URL (looks like: `https://your-service-name.onrender.com`)
4. Add `/api/v1` to the end
5. Use this as your `BACKEND_API_URL` value

### 3. Redeploy Frontend

After saving the environment variables:

- Vercel should automatically trigger a redeploy
- If not, go to Deployments tab → Click ⋯ → Redeploy

### 4. Test the Deployment

Once redeployed, test your app:

1. **Open browser DevTools** (F12)
2. **Go to Network tab**
3. **Upload a document**
4. **Check the request**:
   - ✅ URL should be `/api/proxy?endpoint=/documents/upload`
   - ✅ Headers should NOT show `X-API-Key` (it's server-side now)
   - ✅ Request should succeed with 200 OK

## 🔍 How to Verify It's Working

### Good Signs ✅

- Requests go to `/api/proxy` URLs
- No `X-API-Key` visible in browser Network tab
- Upload and analysis work normally
- No Vercel security warnings

### Bad Signs ❌

- Still seeing direct backend URLs (like `onrender.com`)
- `X-API-Key` visible in request headers
- 401 Unauthorized errors (API_KEY not set correctly)
- CORS errors (BACKEND_API_URL incorrect)

## 🐛 Troubleshooting

### "Network Error" or "Failed to fetch"

- Check `BACKEND_API_URL` is correct
- Make sure it includes `/api/v1`
- Verify your Render backend is running

### "Unauthorized" or 401 errors

- `API_KEY` in Vercel doesn't match backend's `API_KEY`
- Check both values are identical
- Redeploy after fixing

### "CORS Error"

- Your proxy should handle CORS
- Make sure `BACKEND_API_URL` is correct
- Check Render backend logs for errors

### Environment variables not working

- After adding variables, you MUST redeploy
- Check the deployment logs for any errors
- Variables without `NEXT_PUBLIC_` prefix are only available server-side (which is what we want!)

## 📝 Local Development

For local testing, create `frontend/.env.local`:

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
API_KEY=your-local-api-key
BACKEND_API_URL=http://localhost:8000/api/v1
```

Run locally:

```bash
cd frontend
npm run dev
```

## ✨ Benefits You Now Have

1. **Security**: API key hidden from browser
2. **Professional**: No security warnings
3. **Portfolio-ready**: Shows best practices
4. **Flexible**: Easy to add rate limiting later
5. **Centralized**: All API calls go through one route

## 🎯 Next Steps

After this works:

1. ✅ Test full workflow (upload → analyze → RAG)
2. ✅ Update CORS_ORIGINS in Render with your Vercel URL
3. ✅ Optional: Add rate limiting to proxy route
4. ✅ Optional: Add error tracking (Sentry)

---

**Need help?** Check the main documentation in `FRONTEND_API_KEY.md`
