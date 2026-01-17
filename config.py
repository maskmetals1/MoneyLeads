"""
Configuration file for YouTube Automation System
Store your API keys and configuration here
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")  # Service role key for worker
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")  # Anon key for web UI

# Storage Bucket Names
STORAGE_BUCKET_VOICEOVERS = "voiceovers"
STORAGE_BUCKET_RENDERS = "renders"
STORAGE_BUCKET_SCRIPTS = "scripts"

# OpenAI/Claude API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # "openai" or "claude"

# YouTube API Configuration
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")  # OAuth refresh token

# Video Processing Configuration
VIDEO_FOLDER = Path(os.getenv("VIDEO_FOLDER", "/Users/phill/Desktop/instagram_downloads"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", None)  # None = auto-select

# Worker Configuration
WORKER_POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", "10"))  # seconds
WORKER_MAX_CONCURRENT_JOBS = int(os.getenv("WORKER_MAX_CONCURRENT_JOBS", "1"))

# File Paths
LOCAL_TEMP_DIR = Path(os.getenv("LOCAL_TEMP_DIR", "/tmp/youtube_automation"))

def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is required")
    if not SUPABASE_SERVICE_KEY:
        errors.append("SUPABASE_SERVICE_KEY is required")
    if not SUPABASE_ANON_KEY:
        errors.append("SUPABASE_ANON_KEY is required")
    if not OPENAI_API_KEY and not CLAUDE_API_KEY:
        errors.append("Either OPENAI_API_KEY or CLAUDE_API_KEY is required")
    if not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET:
        errors.append("YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET are required")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True

