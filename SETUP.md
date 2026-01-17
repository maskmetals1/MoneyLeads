# Setup Guide

Complete setup instructions for the YouTube Automation System.

## Prerequisites

- Python 3.8+
- Node.js 18+ (for dashboard)
- FFmpeg installed (`brew install ffmpeg` on macOS)
- Supabase account (free tier works)
- OpenAI or Claude API key
- Google Cloud account with YouTube Data API v3 enabled

## Step 1: Supabase Setup

### 1.1 Create Supabase Project

1. Go to https://supabase.com and sign up/login
2. Click "New Project"
3. Fill in:
   - Project name: `youtube-automation` (or your choice)
   - Database password: (save this securely)
   - Region: Choose closest to you
4. Wait for project to be created (~2 minutes)

### 1.2 Create Database Tables

1. In Supabase dashboard, go to **SQL Editor**
2. Click **New Query**
3. Copy and paste the entire contents of `supabase_schema.sql`
4. Click **Run** (or press Cmd/Ctrl + Enter)
5. Verify tables were created:
   - Go to **Table Editor**
   - You should see `video_jobs` and `youtube_videos` tables

### 1.3 Create Storage Buckets

1. Go to **Storage** in Supabase dashboard
2. Click **New bucket**
3. Create three buckets:

   **Bucket 1: voiceovers**
   - Name: `voiceovers`
   - Public: ✅ Yes (or No if you want authenticated access)
   - Click **Create bucket**

   **Bucket 2: renders**
   - Name: `renders`
   - Public: ✅ Yes
   - Click **Create bucket**

   **Bucket 3: scripts** (optional)
   - Name: `scripts`
   - Public: ✅ Yes
   - Click **Create bucket**

### 1.4 Get API Keys

1. Go to **Settings** → **API**
2. Copy these values (you'll need them for `.env`):
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY` (keep this secret!)

## Step 2: Python Environment Setup

### 2.1 Create Virtual Environment

```bash
cd /Users/phill/Desktop/youtube_automation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Configure Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and fill in:
```bash
# Supabase (from Step 1.4)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...

# AI Provider (choose one)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Or use Claude
# AI_PROVIDER=claude
# CLAUDE_API_KEY=sk-ant-...

# Video Processing
VIDEO_FOLDER=/Users/phill/Desktop/instagram_downloads
WHISPER_MODEL=base
```

## Step 3: YouTube API Setup

### 3.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **Select a project** → **New Project**
3. Name: `YouTube Automation`
4. Click **Create**

### 3.2 Enable YouTube Data API v3

1. In Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "YouTube Data API v3"
3. Click on it and click **Enable**

### 3.3 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: `YouTube Automation`
   - User support email: (your email)
   - Developer contact: (your email)
   - Click **Save and Continue**
   - Scopes: Click **Save and Continue** (no scopes needed)
   - Test users: Click **Save and Continue**
   - Summary: Click **Back to Dashboard**

4. Create OAuth client:
   - Application type: **Desktop app**
   - Name: `YouTube Automation Client`
   - Click **Create**

5. Download the credentials JSON:
   - Click the download icon next to your OAuth client
   - Save as `~/.youtube_credentials.json` (or any path you prefer)

6. Update `.env`:
```bash
YOUTUBE_CLIENT_ID=xxxxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xxxxx
```

### 3.4 Authorize Application

The first time you run the worker, it will:
1. Open a browser window
2. Ask you to sign in to Google
3. Ask for permission to manage your YouTube account
4. Save the token to `~/.youtube_token.pickle`

You only need to do this once!

## Step 4: Test the Worker

### 4.1 Run Worker

```bash
cd /Users/phill/Desktop/youtube_automation
source venv/bin/activate
python worker.py
```

You should see:
```
🚀 Initializing YouTube Automation Worker...
✅ Worker initialized successfully

🔄 Worker started - polling every 10 seconds
   Press Ctrl+C to stop
```

### 4.2 Create a Test Job (via Supabase)

1. Go to Supabase dashboard → **Table Editor** → `video_jobs`
2. Click **Insert** → **Insert row**
3. Fill in:
   - `topic`: "How to start a side hustle"
   - `status`: `pending`
4. Click **Save**

The worker should pick it up and start processing!

## Step 5: Web Dashboard Setup

### 5.1 Install Dependencies

```bash
cd dashboard
npm install
```

### 5.2 Configure Environment

1. Copy `.env.local.example` to `.env.local`:
```bash
cp .env.local.example .env.local
```

2. Edit `.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
```

### 5.3 Run Locally

```bash
npm run dev
```

Open http://localhost:3000

### 5.4 Deploy to Vercel

1. Push your code to GitHub
2. Go to https://vercel.com
3. Click **New Project**
4. Import your GitHub repository
5. Select the `dashboard` folder as root
6. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
7. Click **Deploy**

## Troubleshooting

### Worker can't connect to Supabase
- Check `.env` file has correct values
- Verify Supabase project is active
- Test connection: `python -c "from supabase_client import SupabaseClient; c = SupabaseClient(); print(c.get_all_jobs())"`

### YouTube OAuth fails
- Ensure credentials file is at `~/.youtube_credentials.json`
- Check YouTube Data API v3 is enabled
- Delete `~/.youtube_token.pickle` and re-authenticate

### Video processing fails
- Check FFmpeg is installed: `ffmpeg -version`
- Verify video folder exists and contains MP4 files
- Check Python dependencies: `pip list | grep -E "moviepy|edge-tts|whisper"`

### Dashboard shows no jobs
- Check Supabase RLS policies allow public read
- Verify environment variables in `.env.local`
- Check browser console for errors

## Next Steps

1. ✅ Supabase setup complete
2. ✅ Python worker running
3. ✅ Web dashboard deployed
4. 🎬 Start creating videos!

Create a job via the web dashboard and watch the worker process it!

