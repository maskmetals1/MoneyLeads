-- Supabase Database Schema for YouTube Automation System
-- Run this in your Supabase SQL Editor

-- Main job tracking table
CREATE TABLE IF NOT EXISTS video_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    script TEXT,
    title TEXT,
    description TEXT,
    tags TEXT[], -- Array of tags
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    voiceover_url TEXT, -- Supabase Storage URL
    video_url TEXT, -- Supabase Storage URL
    script_url TEXT, -- Supabase Storage URL (optional)
    youtube_video_id TEXT, -- YouTube video ID after upload
    youtube_url TEXT, -- Full YouTube URL
    metadata JSONB -- Additional metadata (duration, file sizes, etc.)
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_video_jobs_status ON video_jobs(status);
CREATE INDEX IF NOT EXISTS idx_video_jobs_created_at ON video_jobs(created_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_video_jobs_updated_at 
    BEFORE UPDATE ON video_jobs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- YouTube videos tracking (separate table for analytics)
CREATE TABLE IF NOT EXISTS youtube_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES video_jobs(id) ON DELETE CASCADE,
    video_id TEXT UNIQUE NOT NULL, -- YouTube video ID
    title TEXT NOT NULL,
    description TEXT,
    published_at TIMESTAMPTZ,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_youtube_videos_job_id ON youtube_videos(job_id);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_video_id ON youtube_videos(video_id);

-- Trigger for youtube_videos updated_at
CREATE TRIGGER update_youtube_videos_updated_at 
    BEFORE UPDATE ON youtube_videos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE video_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE youtube_videos ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow public read, authenticated write - adjust as needed)
-- For now, allow all operations (you can restrict later)
CREATE POLICY "Allow all operations on video_jobs" ON video_jobs
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Allow all operations on youtube_videos" ON youtube_videos
    FOR ALL USING (true) WITH CHECK (true);

-- Storage buckets will be created via Supabase Dashboard or API
-- Buckets needed:
-- - voiceovers (public or authenticated)
-- - renders (public or authenticated)
-- - scripts (optional, public or authenticated)

