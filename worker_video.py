#!/usr/bin/env python3
"""
Video Rendering Worker
Only handles video rendering
Dependencies: script, voiceover_url
"""

import sys
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from base_worker import BaseWorker
from config import VIDEO_FOLDER, WHISPER_MODEL, EDGE_TTS_VOICE
from video_processor import VideoProcessor


class VideoWorker(BaseWorker):
    """Worker that renders videos from scripts and voiceovers"""
    
    def __init__(self):
        super().__init__("Video Worker")
        self.video_processor = VideoProcessor(
            video_folder=VIDEO_FOLDER,
            whisper_model=WHISPER_MODEL,
            voice=EDGE_TTS_VOICE
        )
        print("✅ Video Worker initialized")
    
    def check_dependencies(self, job: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if job has all required dependencies for video rendering
        
        Dependencies: script, voiceover_url
        """
        missing = []
        
        # Script is required
        if not job.get("script"):
            missing.append("script")
        
        # Voiceover path/URL is required (can be local path or URL)
        if not job.get("voiceover_url"):
            missing.append("voiceover_url")
        
        return len(missing) == 0, missing
    
    def process_job(self, job: Dict[str, Any]) -> bool:
        """Process video rendering job"""
        job_id = job["id"]
        script = job.get("script")
        voiceover_url = job.get("voiceover_url")
        
        if not script:
            print(f"❌ Script not found for job {job_id}")
            return False
        
        if not voiceover_url:
            print(f"❌ Voiceover path not found for job {job_id}")
            return False
        
        # Check if voiceover_url is a local path or URL
        if voiceover_url.startswith('http://') or voiceover_url.startswith('https://'):
            # Download from Supabase (backward compatibility for old jobs)
            print(f"  📥 Downloading voiceover from URL (backward compatibility)...")
            import requests
            temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            voiceover_path = temp_dir / "voiceover.mp3"
            
            response = requests.get(voiceover_url, stream=True)
            response.raise_for_status()
            
            with open(voiceover_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  ✅ Voiceover downloaded from URL")
        else:
            # Use local file path
            voiceover_path = Path(voiceover_url)
            if not voiceover_path.exists():
                print(f"❌ Voiceover file not found at: {voiceover_url}")
                return False
            print(f"  ✅ Using local voiceover: {voiceover_path}")
        
        try:
            print(f"\n[1/3] Rendering video...")
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            current_metadata["sub_status"] = "rendering_video"
            self.supabase.update_job_status(job_id, "rendering_video", metadata=current_metadata)
            
            # Create temp directory for this job (use unique name to avoid conflicts)
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            temp_dir = Path(f"/tmp/youtube_automation_{job_id}_{unique_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = temp_dir / "video.mp4"
            
            # Process video using existing voiceover file (single attempt, no retries)
            success, duration = self.video_processor.process_video(script, video_path, voiceover_path=voiceover_path)
            
            if not success:
                raise Exception("Video processing failed")
            
            if not video_path.exists():
                raise Exception("Video file not found after processing")
            
            # Update sub-status to saving
            print(f"\n[2/3] Saving video locally...")
            current_metadata["sub_status"] = "saving_video"
            self.supabase.update_job_status(job_id, status=None, metadata=current_metadata)
            
            # Save video locally with unique name
            video_path_local = self.supabase.save_video_path(video_path, job_id)
            print(f"  ✅ Video saved locally: {video_path_local}")
            
            # Clear sub_status
            current_metadata.pop("sub_status", None)
            
            # Video creation is complete - check if all steps are done except YouTube upload
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            
            # Clear original_action and missing_dependencies
            current_metadata.pop("original_action", None)
            current_metadata.pop("missing_dependencies", None)
            
            # Check if all steps are complete except YouTube upload
            # If script, voiceover, and video exist but no YouTube URL, set status to "ready"
            # Do NOT set action_needed - user must manually click "Post to YouTube" button
            if (current_job.get("script") and 
                current_job.get("voiceover_url") and 
                current_job.get("video_url") and 
                not current_job.get("youtube_url")):
                # Clear action_needed - workflow stops after video creation, no automatic YouTube upload
                current_metadata.pop("action_needed", None)
                self.supabase.update_job_status(job_id, "ready", metadata=current_metadata)
            else:
                # Clear action_needed - workflow stops after video creation
                current_metadata.pop("action_needed", None)
                self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
            
            # Cleanup
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
            
            print(f"\n✅ Video creation complete - ready for YouTube upload")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Video creation failed: {error_msg}")
            import traceback
            traceback.print_exc()
            
            self.supabase.update_job_status(
                job_id,
                "failed",
                error_message=error_msg
            )
            return False


def main():
    """Main entry point"""
    worker = VideoWorker()
    worker.run("create_video")


if __name__ == "__main__":
    main()

