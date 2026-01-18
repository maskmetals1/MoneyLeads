#!/usr/bin/env python3
"""
Voiceover Generation Worker
Only handles voiceover (MP3) generation
Dependencies: script
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from base_worker import BaseWorker
from config import VIDEO_FOLDER, WHISPER_MODEL, EDGE_TTS_VOICE
from video_processor import VideoProcessor


class VoiceoverWorker(BaseWorker):
    """Worker that generates voiceovers from scripts"""
    
    def __init__(self):
        super().__init__("Voiceover Worker")
        self.video_processor = VideoProcessor(
            video_folder=VIDEO_FOLDER,
            whisper_model=WHISPER_MODEL,
            voice=EDGE_TTS_VOICE
        )
        print("✅ Voiceover Worker initialized")
    
    def check_dependencies(self, job: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if job has all required dependencies for voiceover generation
        
        Dependencies: script
        """
        missing = []
        
        # Script is required
        if not job.get("script"):
            missing.append("script")
        
        return len(missing) == 0, missing
    
    def process_job(self, job: Dict[str, Any]) -> bool:
        """Process voiceover generation job"""
        job_id = job["id"]
        script = job.get("script")
        
        if not script:
            print(f"❌ Script not found for job {job_id}")
            return False
        
        try:
            print(f"\n[1/1] Generating voiceover...")
            self.supabase.update_job_status(job_id, "creating_voiceover")
            
            # Create temp directory for this job
            temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate voiceover directly to temp directory
            voiceover_path = temp_dir / "voiceover.mp3"
            
            # Generate voiceover only (no video processing)
            success, duration = self.video_processor.generate_voiceover_only(script, voiceover_path)
            
            if not success:
                raise Exception("Voiceover generation failed")
            
            # Verify voiceover file exists
            if not voiceover_path.exists():
                raise Exception("Voiceover file not found after processing")
            
            # Use the voiceover path directly (no need to copy)
            worker_voiceover_path = voiceover_path
            
            # Upload and save voiceover URL immediately
            voiceover_url = self.supabase.upload_voiceover(worker_voiceover_path, job_id)
            print(f"  ✅ Voiceover uploaded and saved: {voiceover_url}")
            
            # Update action_needed based on original action
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            original_action = current_metadata.get("action_needed", "")
            
            # If it was "run_all", set next action to "create_video"
            # Otherwise, clear action_needed
            if original_action == "run_all":
                current_metadata["action_needed"] = "create_video"
            else:
                current_metadata.pop("action_needed", None)
            
            current_metadata.pop("missing_dependencies", None)
            self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
            
            # Cleanup temp files (keep voiceover in temp_dir for video worker if needed)
            # Actually, let's keep it for now in case video worker needs it
            
            print(f"\n✅ Voiceover generation complete - ready for video creation")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Voiceover generation failed: {error_msg}")
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
    worker = VoiceoverWorker()
    worker.run("generate_voiceover")


if __name__ == "__main__":
    main()

