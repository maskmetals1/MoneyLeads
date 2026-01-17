# Manual Video Upload & Post Feature

## Overview

The dashboard now includes a **"Upload & Post Video"** section that allows you to:
- Select a video file from your computer
- Enter title, description, tags, and privacy settings
- Upload directly to YouTube without AI generation

## How It Works

1. **Upload Section**: New card in the dashboard with file upload form
2. **File Upload**: Video is uploaded to Supabase Storage
3. **Job Creation**: A job is created with status "pending"
4. **Worker Processing**: The worker detects manual uploads and:
   - Downloads the video from Supabase Storage
   - Uploads directly to YouTube with your metadata
   - Updates job status to "completed"

## Usage

### Step 1: Access the Dashboard
Navigate to your dashboard (localhost:3000 or your Vercel URL)

### Step 2: Use Upload Section
1. Scroll to **"Upload & Post Video"** card
2. Click **"Choose File"** and select your video
3. Fill in:
   - **Title** (required)
   - **Description** (optional)
   - **Tags** (comma-separated, optional)
   - **Privacy Status** (Private/Unlisted/Public)
4. Click **"Upload & Post to YouTube"**

### Step 3: Monitor Progress
- Job appears in "Video Jobs" section
- Status updates in real-time:
  - `pending` → `uploading` → `completed`
- Once completed, you'll see the YouTube link

## Features

- ✅ **File Size Validation**: Max 2GB
- ✅ **Auto-fill Title**: Uses filename if title is empty
- ✅ **Real-time Updates**: See status changes live
- ✅ **Error Handling**: Clear error messages
- ✅ **Progress Tracking**: Watch upload progress

## Technical Details

### API Route
- **Endpoint**: `/api/upload`
- **Method**: POST
- **Handles**: File upload, job creation, Supabase Storage upload

### Worker Logic
- Detects `manual_upload: true` in job metadata
- Skips script generation and video rendering
- Downloads video from Supabase Storage
- Uploads directly to YouTube

### File Storage
- Videos stored in `renders` bucket
- Path: `{job_id}/video.{extension}`
- Public URLs for easy access

## Limitations

- **File Size**: 2GB maximum (Supabase Storage limit)
- **Supported Formats**: Any video format supported by YouTube
- **Processing Time**: Depends on video size and upload speed

## Troubleshooting

### "File size must be less than 2GB"
- Compress your video or use a smaller file
- Consider using video compression tools

### "Failed to upload file"
- Check Supabase Storage bucket permissions
- Verify `renders` bucket exists and is public
- Check browser console for detailed errors

### "Worker not processing"
- Make sure worker is running: `python worker.py`
- Check worker logs for errors
- Verify job status in database

## Next Steps

After uploading:
1. ✅ Video appears in YouTube (based on privacy setting)
2. ✅ Job shows as "completed" in dashboard
3. ✅ YouTube link available in job details
4. ✅ Can download original video from Supabase Storage

