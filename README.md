# YouTube Automation System

Automated YouTube video creation and posting system using Supabase, AI script generation, and local video processing.

## Architecture

- **Web UI (Vercel)**: Create jobs, view status
- **Supabase**: Database and file storage
- **Local Worker**: Processes videos on your machine
- **YouTube API**: Automatic video uploads

## Setup

### 1. Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Run the SQL schema in `supabase_schema.sql` in your Supabase SQL Editor
3. Create Storage buckets:
   - `voiceovers` (public or authenticated)
   - `renders` (public or authenticated)
   - `scripts` (optional, public or authenticated)
4. Get your Supabase URL and API keys from Settings > API

### 2. Python Environment

```bash
cd youtube_automation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

1. Copy `.env.example` to `.env`
2. Fill in all required values:
   - Supabase URL and keys
   - OpenAI or Claude API key
   - YouTube API credentials
   - Video folder path

### 4. YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable YouTube Data API v3
3. Create OAuth 2.0 credentials (Desktop app)
4. Download credentials JSON and save as `~/.youtube_credentials.json`
5. Run the worker once - it will open a browser for OAuth authorization
6. The token will be saved to `~/.youtube_token.pickle`

### 5. Run the Worker

```bash
python worker.py
```

The worker will:
- Poll Supabase for pending jobs every 10 seconds
- Generate scripts using AI
- Create voiceovers and videos
- Upload to Supabase Storage
- Upload to YouTube

## Web Dashboard

The web dashboard is a Next.js app that can be deployed to Vercel. See `dashboard/` directory.

### Local Development

```bash
cd dashboard
npm install
npm run dev
```

### Environment Variables (Vercel)

- `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase anon key

## Workflow

1. User creates a job via web UI with a topic
2. Job is saved to Supabase with status `pending`
3. Worker picks up the job
4. Worker generates script, title, description using AI
5. Worker creates voiceover (MP3)
6. Worker renders video with captions
7. Worker uploads files to Supabase Storage
8. Worker uploads video to YouTube
9. Job status updated to `completed`
10. Web UI shows completed video with YouTube link

## Status Flow

- `pending` → `generating_script` → `creating_voiceover` → `rendering_video` → `uploading` → `completed`
- If any step fails: `failed` (with error message)

## File Structure

```
youtube_automation/
├── worker.py              # Main worker script
├── supabase_client.py    # Supabase operations
├── script_generator.py    # AI script generation
├── video_processor.py     # Video rendering wrapper
├── youtube_uploader.py    # YouTube API integration
├── config.py             # Configuration
├── requirements.txt       # Python dependencies
├── supabase_schema.sql   # Database schema
├── .env.example          # Environment variables template
└── dashboard/            # Next.js web dashboard
```

## Troubleshooting

### Worker can't connect to Supabase
- Check your `.env` file has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Verify Supabase project is active

### YouTube upload fails
- Ensure OAuth credentials are set up correctly
- Check that YouTube Data API v3 is enabled
- Verify token file exists at `~/.youtube_token.pickle`

### Video processing fails
- Ensure `ffmpeg` is installed: `brew install ffmpeg`
- Check that video folder exists and contains MP4 files
- Verify all Python dependencies are installed

### AI script generation fails
- Check your OpenAI or Claude API key is valid
- Ensure you have API credits/quota available

