#!/usr/bin/env python3
"""
Script Generation Worker
Only handles script, title, description, and tags generation
Dependencies: topic (always available)
"""

import sys
from typing import List, Dict, Any, Tuple
from base_worker import BaseWorker
from script_generator import ScriptGenerator


class ScriptWorker(BaseWorker):
    """Worker that generates scripts, titles, descriptions, and tags"""
    
    def __init__(self):
        super().__init__("Script Worker")
        self.script_generator = ScriptGenerator()
        print("✅ Script Worker initialized")
    
    def check_dependencies(self, job: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if job has all required dependencies for script generation
        
        Dependencies: topic (always required, should always be present)
        """
        missing = []
        
        # Topic is required
        if not job.get("topic"):
            missing.append("topic")
        
        # Script should not already exist (unless regenerating)
        # This is handled by the action_needed check
        
        return len(missing) == 0, missing
    
    def process_job(self, job: Dict[str, Any]) -> bool:
        """Process script generation job"""
        job_id = job["id"]
        topic = job["topic"]
        
        # Double-check job hasn't been processed already (race condition protection)
        current_job = self.supabase.get_job(job_id)
        if current_job and current_job.get("script"):
            print(f"  ⚠️  Job {job_id[:8]} already has a script. Skipping to prevent overwrite.")
            # Still update action_needed if it's run_all
            metadata = current_job.get("metadata", {})
            original_action = metadata.get("original_action", "")
            current_action = metadata.get("action_needed", "")
            if original_action == "run_all" or current_action == "run_all":
                metadata["action_needed"] = "generate_voiceover"
                metadata["original_action"] = "run_all"
                self.supabase.update_job_status(job_id, status=None, metadata=metadata)
            return True
        
        try:
            # Step 1: Generate title and description first (separate API call)
            print(f"\n[1/3] Generating title and description...")
            # Status already set to generating_script by base_worker when claiming job
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            current_metadata["sub_status"] = "generating_title_description"
            self.supabase.update_job_status(job_id, status=None, metadata=current_metadata)
            
            title, description, tags = self.script_generator.generate_title_and_description(topic)
            
            # Save title immediately
            self.supabase.update_job_status(job_id, status=None, title=title)
            print(f"  ✅ Title generated and saved: {title}")
            
            # Save description immediately
            self.supabase.update_job_status(job_id, status=None, description=description)
            print(f"  ✅ Description generated and saved")
            
            # Save tags immediately
            self.supabase.update_job_status(job_id, status=None, tags=tags)
            print(f"  ✅ Tags generated and saved: {len(tags)} tags")
            
            # Step 2: Generate script using title as context (separate API call)
            print(f"\n[2/3] Generating script (using title as context)...")
            current_metadata["sub_status"] = "generating_script"
            self.supabase.update_job_status(job_id, status=None, metadata=current_metadata)
            
            script = self.script_generator.generate_script(topic, title=title)
            
            # Save script immediately
            self.supabase.update_job_status(job_id, status=None, script=script)
            print(f"  ✅ Script generated and saved ({len(script)} chars)")
            
            # Clear sub_status
            current_metadata.pop("sub_status", None)
            
            # Update action_needed based on original action
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            original_action = current_metadata.get("original_action", "")
            current_action = current_metadata.get("action_needed", "")
            
            # If it was "run_all", preserve it and set next action to "generate_voiceover"
            # This ensures voiceover worker knows to continue the run_all flow
            if original_action == "run_all" or current_action == "run_all":
                current_metadata["action_needed"] = "generate_voiceover"
                current_metadata["original_action"] = "run_all"  # Preserve for subsequent workers
            else:
                current_metadata.pop("action_needed", None)
                current_metadata.pop("original_action", None)
            
            current_metadata.pop("missing_dependencies", None)
            self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
            
            print(f"\n[3/3] ✅ Script generation complete - ready for voiceover")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Script generation failed: {error_msg}")
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
    worker = ScriptWorker()
    worker.run("generate_script")


if __name__ == "__main__":
    main()

