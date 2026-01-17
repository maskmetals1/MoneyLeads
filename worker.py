#!/usr/bin/env python3
"""
YouTube Automation Worker
Polls Supabase for pending jobs and processes them locally
"""

import time
import sys
from pathlib import Path
from typing import Optional
from config import (
    validate_config, VIDEO_FOLDER, WHISPER_MODEL, EDGE_TTS_VOICE,
    WORKER_POLL_INTERVAL, WORKER_MAX_CONCURRENT_JOBS
)
from supabase_client import SupabaseClient
from script_generator import ScriptGenerator
from video_processor import VideoProcessor
from youtube_uploader import YouTubeUploader


class Worker:
    """Main worker that processes video jobs"""
    
    def __init__(self):
        """Initialize worker with all required clients"""
        print("🚀 Initializing YouTube Automation Worker...")
        
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            sys.exit(1)
        
        # Initialize clients
        self.supabase = SupabaseClient()
        self.script_generator = ScriptGenerator()
        self.video_processor = VideoProcessor(
            video_folder=VIDEO_FOLDER,
            whisper_model=WHISPER_MODEL,
            voice=EDGE_TTS_VOICE
        )
        self.youtube_uploader = YouTubeUploader()
        
        print("✅ Worker initialized successfully")
    
    def process_job(self, job: dict) -> bool:
        """
        Process a single video job
        
        Args:
            job: Job dictionary from Supabase
        
        Returns:
            True if successful, False otherwise
        """
        job_id = job["id"]
        topic = job["topic"]
        metadata = job.get("metadata", {})
        is_manual_upload = metadata.get("manual_upload", False)
        
        print(f"\n{'='*60}")
        print(f"📹 Processing Job: {job_id}")
        print(f"📝 Topic: {topic}")
        if is_manual_upload:
            print(f"📤 Type: Manual Upload")
        print(f"{'='*60}")
        
        try:
            # Check if this is a manual upload (video already uploaded)
            if is_manual_upload:
                # Manual upload flow - skip script generation, go straight to YouTube upload
                print(f"\n[1/3] Processing manual upload...")
                self.supabase.update_job_status(job_id, "uploading")
                
                # Get video URL from job
                video_url = job.get("video_url")
                if not video_url:
                    raise Exception("Video URL not found for manual upload")
                
                # Download video from Supabase Storage
                import requests
                import tempfile
                temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                video_path = temp_dir / "video.mp4"
                print(f"  📥 Downloading video from storage...")
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  ✅ Video downloaded")
                
                # Get metadata from job
                title = job.get("title", topic)
                description = job.get("description", "")
                tags = job.get("tags", [])
                privacy_status = metadata.get("privacy_status", "private")
                
                # Upload to YouTube
                print(f"\n[2/3] Uploading to YouTube...")
                youtube_result = self.youtube_uploader.upload_video(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags if isinstance(tags, list) else [],
                    privacy_status=privacy_status
                )
                
                youtube_video_id = youtube_result["video_id"]
                youtube_url = youtube_result["video_url"]
                
                # Save YouTube video info
                self.supabase.save_youtube_video(job_id, youtube_video_id, title, description)
                self.supabase.update_job_with_youtube(job_id, youtube_video_id, youtube_url)
                
                print(f"  ✅ Uploaded to YouTube: {youtube_url}")
                
                # Cleanup
                print(f"\n[3/3] Cleaning up...")
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
                
                print(f"\n✅ Job completed successfully!")
                print(f"   YouTube: {youtube_url}")
                
                return True
            
            # Normal flow - generate script, create video
            # Step 1: Generate script, title, description
            print(f"\n[1/5] Generating script and metadata...")
            self.supabase.update_job_status(job_id, "generating_script")
            
            script = self.script_generator.generate_script(topic)
            title, description, tags = self.script_generator.generate_title_and_description(script)
            
            # Save script, title, description to database
            self.supabase.update_job_script(job_id, script, title, description, tags)
            print(f"  ✅ Script generated ({len(script)} chars)")
            print(f"  ✅ Title: {title}")
            
            # Step 2: Generate voiceover and render video
            print(f"\n[2/5] Generating voiceover and rendering video...")
            self.supabase.update_job_status(job_id, "creating_voiceover")
            
            # Create temp directory for this job
            temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = temp_dir / "video.mp4"
            success, duration = self.video_processor.process_video(script, video_path)
            
            if not success:
                raise Exception("Video processing failed")
            
            # Get voiceover path and copy to our temp dir (processor may clean up its temp dir)
            voiceover_path = self.video_processor.get_voiceover_path()
            if voiceover_path and voiceover_path.exists():
                # Copy to worker's temp dir to ensure it persists
                import shutil
                worker_voiceover_path = temp_dir / "voiceover.mp3"
                shutil.copy2(voiceover_path, worker_voiceover_path)
                voiceover_path = worker_voiceover_path
            
            # Step 3: Upload files to Supabase Storage
            print(f"\n[3/5] Uploading files to storage...")
            self.supabase.update_job_status(job_id, "rendering_video")
            
            if voiceover_path and voiceover_path.exists():
                voiceover_url = self.supabase.upload_voiceover(voiceover_path, job_id)
                print(f"  ✅ Voiceover uploaded: {voiceover_url}")
            
            if not video_path.exists():
                raise Exception("Video file not found after processing")
            
            video_url = self.supabase.upload_video(video_path, job_id)
            print(f"  ✅ Video uploaded: {video_url}")
            
            # Step 4: Upload to YouTube
            print(f"\n[4/5] Uploading to YouTube...")
            self.supabase.update_job_status(job_id, "uploading")
            
            youtube_result = self.youtube_uploader.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags,
                privacy_status="private"  # Start as private, can change later
            )
            
            youtube_video_id = youtube_result["video_id"]
            youtube_url = youtube_result["video_url"]
            
            # Save YouTube video info
            self.supabase.save_youtube_video(job_id, youtube_video_id, title, description)
            self.supabase.update_job_with_youtube(job_id, youtube_video_id, youtube_url)
            
            print(f"  ✅ Uploaded to YouTube: {youtube_url}")
            
            # Step 5: Cleanup
            print(f"\n[5/5] Cleaning up...")
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
            
            print(f"\n✅ Job completed successfully!")
            print(f"   YouTube: {youtube_url}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Job failed: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Update job status to failed
            self.supabase.update_job_status(
                job_id,
                "failed",
                error_message=error_msg
            )
            
            return False
    
    def run(self):
        """Main worker loop - polls for jobs and processes them"""
        print(f"\n🔄 Worker started - polling every {WORKER_POLL_INTERVAL} seconds")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get pending jobs
                jobs = self.supabase.get_pending_jobs(limit=WORKER_MAX_CONCURRENT_JOBS)
                
                if jobs:
                    for job in jobs:
                        self.process_job(job)
                else:
                    print(f"⏳ No pending jobs... (checking again in {WORKER_POLL_INTERVAL}s)")
                
                # Wait before next poll
                time.sleep(WORKER_POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Worker stopped by user")
        except Exception as e:
            print(f"\n❌ Worker error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    worker = Worker()
    worker.run()


if __name__ == "__main__":
    main()

