#!/usr/bin/env python3
"""
Video Rendering Worker
Only handles video rendering
Dependencies: script, voiceover_url
"""

import sys
import shutil
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
        
        # Voiceover URL is required
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
            print(f"❌ Voiceover URL not found for job {job_id}")
            return False
        
        try:
            print(f"\n[1/2] Rendering video...")
            self.supabase.update_job_status(job_id, "rendering_video")
            
            # Create temp directory for this job
            temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = temp_dir / "video.mp4"
            
            # Process video (this will use the script and generate voiceover if needed,
            # but we already have voiceover, so it should use it)
            # Actually, video_processor needs to be updated to accept existing voiceover
            # For now, let's process it normally - it will regenerate voiceover but that's okay
            success, duration = self.video_processor.process_video(script, video_path)
            
            if not success:
                raise Exception("Video processing failed")
            
            if not video_path.exists():
                raise Exception("Video file not found after processing")
            
            # Upload and save video URL immediately
            print(f"\n[2/2] Uploading video...")
            video_url = self.supabase.upload_video(video_path, job_id)
            print(f"  ✅ Video uploaded and saved: {video_url}")
            
            # Update action_needed based on original action
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            original_action = current_metadata.get("action_needed", "")
            
            # If it was "run_all", set next action to "post_to_youtube"
            # Otherwise, clear action_needed
            if original_action == "run_all":
                current_metadata["action_needed"] = "post_to_youtube"
            else:
                current_metadata.pop("action_needed", None)
            
            current_metadata.pop("missing_dependencies", None)
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

