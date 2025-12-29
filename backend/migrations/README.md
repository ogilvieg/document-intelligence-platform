# Database Setup Guide

This guide walks you through setting up Supabase with pgvector for the Document Intelligence Platform.

## Prerequisites

- A Supabase account (free tier is fine)
- The Supabase CLI (optional but recommended)

## Step 1: Create a Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Fill in:
   - **Name**: document-intelligence-platform
   - **Database Password**: (generate a strong password - save this!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free tier is fine for development
4. Click "Create new project" (takes ~2 minutes)

## Step 2: Get Your Credentials

Once your project is created:

1. Go to **Settings** → **API**
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: `eyJxxx...` (safe for frontend)
   - **service_role key**: `eyJxxx...` (secret - backend only)

## Step 3: Update Environment Variables

Update your `backend/.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJxxx...your-anon-key...
SUPABASE_SERVICE_KEY=eyJxxx...your-service-role-key...
```

## Step 4: Run Database Migrations

You have two options:

### Option A: Using Supabase Dashboard (Easiest)

1. Go to **SQL Editor** in your Supabase dashboard
2. Click "New Query"
3. Copy and paste the contents of `migrations/001_initial_schema.sql`
4. Click "Run" (or press Cmd/Ctrl + Enter)
5. Repeat for `migrations/002_vector_search_function.sql`

### Option B: Using Supabase CLI

```bash
# Install Supabase CLI (if not already installed)
brew install supabase/tap/supabase  # macOS
# or npm install -g supabase          # npm

# Login to Supabase
supabase login

# Link your project
supabase link --project-ref your-project-id

# Push migrations
supabase db push
```

## Step 5: Verify Setup

### Check Tables

Go to **Table Editor** in Supabase dashboard and verify you see:

- ✅ `documents`
- ✅ `chunks`
- ✅ `embeddings`

### Check pgvector Extension

Go to **SQL Editor** and run:

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

You should see one row with `vector` extension.

### Check Vector Search Function

```sql
SELECT proname FROM pg_proc WHERE proname = 'match_chunks';
```

You should see `match_chunks` function.

## Step 6: Test Connection

From your backend directory:

```bash
cd backend
python -c "from app.services.database import db_service; print('✅ Database connection successful!')"
```

If you see the success message, you're all set!

## Troubleshooting

### "Connection refused" or "Could not connect"

- Check that `SUPABASE_URL` is correct
- Verify your project is not paused (free tier projects pause after 1 week of inactivity)

### "Authentication failed"

- Make sure you're using the correct API keys
- For backend operations, use `SUPABASE_SERVICE_KEY` (not the anon key)

### "relation 'documents' does not exist"

- Migrations weren't run. Go back to Step 4.

### "function match_chunks does not exist"

- The vector search function wasn't created. Run migration 002.

## Database Schema Overview

```
documents
├── id (uuid, primary key)
├── title (text)
├── doc_type (text)
├── source (text)
├── version (text)
├── content_hash (text)
├── metadata (jsonb)
├── created_at (timestamptz)
└── updated_at (timestamptz)

chunks
├── id (uuid, primary key)
├── document_id (uuid, foreign key → documents)
├── chunk_index (integer)
├── text (text)
├── token_count (integer)
├── metadata (jsonb)
└── created_at (timestamptz)

embeddings
├── id (uuid, primary key)
├── chunk_id (uuid, foreign key → chunks)
├── vector (vector(1536))  ← pgvector
├── model_name (text)
└── created_at (timestamptz)
```

## Next Steps

Once your database is set up:

1. ✅ Update ChunkingService to persist chunks
2. ✅ Create EmbeddingService
3. ✅ Build RetrievalService
4. ✅ Test end-to-end flow

See the main project README for implementation details.
