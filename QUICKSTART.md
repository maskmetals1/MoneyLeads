# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.8+ installed
- [ ] FFmpeg installed (`brew install ffmpeg`)
- [ ] Supabase account (free tier works)
- [ ] OpenAI API key (or Claude)

## Step 1: Supabase (5 min)

1. Create project at https://supabase.com
2. Run `supabase_schema.sql` in SQL Editor
3. Create storage buckets: `voiceovers`, `renders`
4. Copy API keys from Settings → API

## Step 2: Python Setup (2 min)

```bash
cd /Users/phill/Desktop/youtube_automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase keys and OpenAI key
```

## Step 3: YouTube API (5 min)

1. Google Cloud Console → Create project
2. Enable YouTube Data API v3
3. Create OAuth credentials (Desktop app)
4. Download JSON → save as `~/.youtube_credentials.json`
5. Add client ID/secret to `.env`

## Step 4: Test It!

```bash
# Terminal 1: Start worker
source venv/bin/activate
python worker.py

# Terminal 2: Create test job in Supabase
# Go to Table Editor → video_jobs → Insert row
# topic: "test video"
# status: "pending"
```

Watch the worker process it! 🎬

## Step 5: Web Dashboard (Optional)

```bash
cd dashboard
npm install
cp .env.local.example .env.local
# Add Supabase keys to .env.local
npm run dev
```

Open http://localhost:3000 and create jobs via the UI!

## That's It!

Your system is ready. Create jobs and watch them get processed automatically.

For detailed setup, see [SETUP.md](SETUP.md)

