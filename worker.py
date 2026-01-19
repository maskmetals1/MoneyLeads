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
        action_needed = metadata.get("action_needed")
        
        print(f"\n{'='*60}")
        print(f"📹 Processing Job: {job_id}")
        print(f"📝 Topic: {topic}")
        if is_manual_upload:
            print(f"📤 Type: Manual Upload")
        if action_needed:
            print(f"🎯 Action: {action_needed}")
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
                privacy_status = metadata.get("privacy_status", "public")
                
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
                
                # Save YouTube video info immediately
                self.supabase.save_youtube_video(job_id, youtube_video_id, title, description)
                self.supabase.update_job_with_youtube(job_id, youtube_video_id, youtube_url)
                
                print(f"  ✅ Uploaded to YouTube and saved: {youtube_url}")
                
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
            
            # Check if this is a post-to-youtube action (video already exists)
            if action_needed == "post_to_youtube":
                # Post existing video to YouTube
                print(f"\n[1/1] Posting existing video to YouTube...")
                self.supabase.update_job_status(job_id, "uploading")
                
                video_url = job.get("video_url")
                if not video_url:
                    raise Exception("Video URL not found - cannot post to YouTube")
                
                # Download video from Supabase Storage
                import requests
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
                title = job.get("title", job.get("topic", "Untitled Video"))
                description = job.get("description", "")
                tags = job.get("tags", [])
                privacy_status = metadata.get("privacy_status", "public")
                
                # Upload to YouTube
                youtube_result = self.youtube_uploader.upload_video(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags if isinstance(tags, list) else [],
                    privacy_status=privacy_status
                )
                
                youtube_video_id = youtube_result["video_id"]
                youtube_url = youtube_result["video_url"]
                
                # Save YouTube video info immediately
                self.supabase.save_youtube_video(job_id, youtube_video_id, title, description)
                self.supabase.update_job_with_youtube(job_id, youtube_video_id, youtube_url)
                
                print(f"  ✅ Posted to YouTube and saved: {youtube_url}")
                
                # Cleanup
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except:
                    pass
                
                print(f"\n✅ Job completed successfully!")
                print(f"   YouTube: {youtube_url}")
                
                return True
            
            # Check what action is needed
            script = job.get("script")
            voiceover_url = job.get("voiceover_url")
            video_url = job.get("video_url")
            
            # Determine starting point based on action_needed or current state
            start_from_script = action_needed == "generate_script" or (not script and not action_needed)
            start_from_voiceover = action_needed == "generate_voiceover" or (script and not voiceover_url and not action_needed)
            start_from_video = action_needed == "create_video" or (voiceover_url and not video_url and not action_needed)
            run_all = action_needed == "run_all"
            
            # Normal flow - generate script, create video
            if start_from_script or run_all:
                # Step 1: Generate script, title, description
                print(f"\n[1/5] Generating script and metadata...")
                self.supabase.update_job_status(job_id, "generating_script")
            
                # Generate script first
                script = self.script_generator.generate_script(topic)
                
                # Save script immediately
                self.supabase.update_job_status(job_id, status=None, script=script)
                print(f"  ✅ Script generated and saved ({len(script)} chars)")
                
                # Generate title, description, tags
                title, description, tags = self.script_generator.generate_title_and_description(script)
                
                # Save title immediately
                self.supabase.update_job_status(job_id, status=None, title=title)
                print(f"  ✅ Title generated and saved: {title}")
                
                # Save description immediately
                self.supabase.update_job_status(job_id, status=None, description=description)
                print(f"  ✅ Description generated and saved")
                
                # Save tags immediately
                self.supabase.update_job_status(job_id, status=None, tags=tags)
                print(f"  ✅ Tags generated and saved: {len(tags)} tags")
                
                # If this was a single-step action, mark as ready for next step
                if action_needed == "generate_script" and not run_all:
                    # Clear action_needed from metadata
                    current_job = self.supabase.get_job(job_id)
                    current_metadata = current_job.get("metadata", {}) if current_job else {}
                    current_metadata.pop("action_needed", None)
                    self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
                    print(f"  ✅ Script generation complete - ready for next step")
            else:
                # Use existing script
                script = job.get("script")
                title = job.get("title", topic)
                description = job.get("description", "")
                tags = job.get("tags", [])
                if not script:
                    raise Exception("Script required but not found")
                print(f"  ✅ Using existing script ({len(script)} chars)")
            
            if start_from_voiceover or (run_all and not voiceover_url):
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
                    
                    # Save voiceover locally with unique name
                    if not job.get("voiceover_url"):
                        voiceover_path_local = self.supabase.save_voiceover_path(voiceover_path, job_id)
                        voiceover_url = voiceover_path_local  # Use local path
                        print(f"  ✅ Voiceover saved locally: {voiceover_url}")
                    else:
                        voiceover_url = job.get("voiceover_url")
                        print(f"  ✅ Voiceover already exists")
                    
                    # If this was a single-step action, mark as ready for next step
                    if action_needed == "generate_voiceover" and not run_all:
                        # Clear action_needed from metadata
                        current_job = self.supabase.get_job(job_id)
                        current_metadata = current_job.get("metadata", {}) if current_job else {}
                        current_metadata.pop("action_needed", None)
                        self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
                        print(f"  ✅ Voiceover generation complete - ready for next step")
                else:
                    raise Exception("Voiceover file not found after processing")
            else:
                # Use existing voiceover or skip to video
                temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                if voiceover_url:
                    # Check if voiceover_url is a local path or URL
                    if voiceover_url.startswith('http://') or voiceover_url.startswith('https://'):
                        # Download from Supabase (backward compatibility for old jobs)
                        import requests
                        voiceover_path = temp_dir / "voiceover.mp3"
                        response = requests.get(voiceover_url, stream=True)
                        response.raise_for_status()
                        with open(voiceover_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"  ✅ Downloaded existing voiceover from URL")
                    else:
                        # Use local file path
                        voiceover_path = Path(voiceover_url)
                        if not voiceover_path.exists():
                            raise Exception(f"Voiceover file not found at local path: {voiceover_url}")
                        print(f"  ✅ Using existing local voiceover: {voiceover_path}")
                else:
                    raise Exception("Voiceover required but not found")
            
            if start_from_video or (run_all and not video_url):
                # Step 3: Upload files to Supabase Storage
                print(f"\n[3/5] Uploading files to storage...")
                self.supabase.update_job_status(job_id, "rendering_video")
                
                # Ensure voiceover is saved locally if it wasn't already
                if voiceover_path and voiceover_path.exists() and not job.get("voiceover_url"):
                    voiceover_path_local = self.supabase.save_voiceover_path(voiceover_path, job_id)
                    voiceover_url = voiceover_path_local  # Use local path
                    print(f"  ✅ Voiceover saved locally: {voiceover_url}")
                else:
                    voiceover_url = job.get("voiceover_url")
                
                if not video_path.exists():
                    raise Exception("Video file not found after processing")
                
                # Save video locally with unique name
                video_path_local = self.supabase.save_video_path(video_path, job_id)
                video_url = video_path_local  # Use local path
                print(f"  ✅ Video saved locally: {video_url}")
                
                # If this was a single-step action, mark as ready for next step
                if action_needed == "create_video" and not run_all:
                    # Clear action_needed from metadata
                    current_job = self.supabase.get_job(job_id)
                    current_metadata = current_job.get("metadata", {}) if current_job else {}
                    current_metadata.pop("action_needed", None)
                    self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
                    print(f"  ✅ Video creation complete - ready for next step")
            else:
                # Use existing video
                video_url = job.get("video_url")
                if not video_url:
                    raise Exception("Video required but not found")
                print(f"  ✅ Using existing video")
            
            # Step 4: Upload to YouTube (if not already uploaded)
            if not job.get("youtube_url"):
                print(f"\n[4/5] Uploading to YouTube...")
                self.supabase.update_job_status(job_id, "uploading")
                
                # Download video if needed (if we're using existing video)
                if not video_path.exists() and video_url:
                    import requests
                    print(f"  📥 Downloading video from storage...")
                    response = requests.get(video_url, stream=True)
                    response.raise_for_status()
                    with open(video_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"  ✅ Video downloaded")
                
                youtube_result = self.youtube_uploader.upload_video(
                    video_path=video_path,
                    title=title,
                    description=description,
                    tags=tags if isinstance(tags, list) else [],
                    privacy_status="public"  # Default to public
                )
                
                youtube_video_id = youtube_result["video_id"]
                youtube_url = youtube_result["video_url"]
                
                # Save YouTube video info immediately
                self.supabase.save_youtube_video(job_id, youtube_video_id, title, description)
                self.supabase.update_job_with_youtube(job_id, youtube_video_id, youtube_url)
                
                print(f"  ✅ Uploaded to YouTube and saved: {youtube_url}")
            else:
                print(f"  ✅ Video already uploaded to YouTube")
                youtube_url = job.get("youtube_url")
            
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

