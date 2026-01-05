# Secure Proxy Deployment Checklist

Follow this checklist to complete your secure proxy setup.

## ✅ Completed (Already Done)

- [x] Code updated to use secure proxy
- [x] Proxy route created (`frontend/app/api/proxy/route.ts`)
- [x] Secure API client created (`frontend/lib/secure-api-client.ts`)
- [x] Hooks updated to use `secureApiClient`
- [x] Changes committed and pushed to GitHub

## 📋 Your Action Items

### 1. Get Your Backend URL from Render

- [ ] Go to [Render Dashboard](https://dashboard.render.com)
- [ ] Find your backend service
- [ ] Copy the URL (e.g., `https://your-service.onrender.com`)
- [ ] Add `/api/v1` to the end
- [ ] Full URL example: `https://document-intelligence-backend-xyz.onrender.com/api/v1`

**Your Backend URL:** `_________________________________`

### 2. Get Your API Key from Render

- [ ] In Render Dashboard → Your Backend Service
- [ ] Go to "Environment" tab
- [ ] Find the `API_KEY` variable value
- [ ] Copy it (should be a long hex string)

**Your API Key (keep secure):** `_________________________________`

### 3. Update Vercel Environment Variables

- [ ] Go to [Vercel Dashboard](https://vercel.com/dashboard)
- [ ] Select your frontend project
- [ ] Go to **Settings** → **Environment Variables**

#### Delete Old Variable:

- [ ] Delete `NEXT_PUBLIC_API_KEY` (if it exists)

#### Add New Variables:

- [ ] Add `API_KEY`
  - Value: (paste your API key from Render)
  - Environments: ✓ Production ✓ Preview ✓ Development
- [ ] Add `BACKEND_API_URL`

  - Value: (paste your backend URL from step 1)
  - Environments: ✓ Production ✓ Preview ✓ Development

- [ ] Click **Save** after each variable

### 4. Trigger Vercel Redeploy

- [ ] Vercel should auto-deploy after environment changes
- [ ] If not: Deployments tab → Click ⋯ → **Redeploy**
- [ ] Wait for deployment to complete (check status)

### 5. Test the Deployment

- [ ] Open your deployed frontend URL
- [ ] Open Browser DevTools (F12 or right-click → Inspect)
- [ ] Go to **Network** tab
- [ ] Try uploading a test document

**Check these:**

- [ ] Request URL is `/api/proxy?endpoint=/documents/upload` (not direct backend URL)
- [ ] No `X-API-Key` header visible in request (it's server-side now!)
- [ ] Upload succeeds with 200 OK status
- [ ] Document appears in the interface

### 6. Test RAG Analysis

- [ ] Upload a PDF document
- [ ] Try the RAG analysis feature
- [ ] Verify results appear correctly
- [ ] Check Network tab - should use `/api/proxy?endpoint=/analyze-rag`

### 7. Update Backend CORS (Important!)

- [ ] Go back to Render Dashboard
- [ ] Find your backend service
- [ ] Go to **Environment** tab
- [ ] Find `CORS_ORIGINS` variable
- [ ] Update value to your Vercel URL: `https://your-app.vercel.app`
- [ ] Save (Render will auto-redeploy backend)

**Your Vercel URL:** `_________________________________`

### 8. Final Verification

- [ ] No Vercel security warnings about `NEXT_PUBLIC_API_KEY`
- [ ] Frontend loads without errors
- [ ] Can upload documents successfully
- [ ] Can run RAG analysis
- [ ] API key not visible in browser Network tab
- [ ] All requests go through `/api/proxy`

## 🎉 Success Criteria

When everything works:

- ✅ No API key visible in browser
- ✅ No security warnings from Vercel
- ✅ Upload and analysis work perfectly
- ✅ Professional, secure architecture

## 🐛 If Something Goes Wrong

### 401 Unauthorized Errors

**Problem:** API key mismatch  
**Fix:** Make sure `API_KEY` in Vercel exactly matches Render's `API_KEY`

### Network/Fetch Errors

**Problem:** Backend URL incorrect  
**Fix:** Check `BACKEND_API_URL` ends with `/api/v1`

### CORS Errors

**Problem:** Backend rejecting frontend requests  
**Fix:** Update `CORS_ORIGINS` in Render with your Vercel URL

### Environment Variables Not Working

**Problem:** Variables not loaded  
**Fix:** Must redeploy after adding environment variables

### Still Seeing Security Warning

**Problem:** Old `NEXT_PUBLIC_API_KEY` still exists  
**Fix:** Delete it from Vercel, redeploy

---

## 📞 Need Help?

Refer to these guides:

- `SETUP_SECURE_PROXY.md` - Detailed setup guide
- `FRONTEND_API_KEY.md` - Full documentation with troubleshooting
- `DEPLOYMENT.md` - General deployment information

---

**Date Started:** ******\_\_\_******  
**Date Completed:** ******\_\_\_******  
**Deployment URL:** ******\_\_\_******
