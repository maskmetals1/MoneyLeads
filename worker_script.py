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
        
        try:
            print(f"\n[1/4] Generating script...")
            self.supabase.update_job_status(job_id, "generating_script")
            
            # Generate script
            script = self.script_generator.generate_script(topic)
            
            # Save script immediately
            self.supabase.update_job_status(job_id, status=None, script=script)
            print(f"  ✅ Script generated and saved ({len(script)} chars)")
            
            # Generate title, description, tags
            print(f"\n[2/4] Generating title...")
            title, description, tags = self.script_generator.generate_title_and_description(script)
            
            # Save title immediately
            self.supabase.update_job_status(job_id, status=None, title=title)
            print(f"  ✅ Title generated and saved: {title}")
            
            # Save description immediately
            print(f"\n[3/4] Generating description...")
            self.supabase.update_job_status(job_id, status=None, description=description)
            print(f"  ✅ Description generated and saved")
            
            # Save tags immediately
            print(f"\n[4/4] Generating tags...")
            self.supabase.update_job_status(job_id, status=None, tags=tags)
            print(f"  ✅ Tags generated and saved: {len(tags)} tags")
            
            # Update action_needed based on original action
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            original_action = current_metadata.get("action_needed", "")
            
            # If it was "run_all", set next action to "generate_voiceover"
            # Otherwise, clear action_needed (job is done with script step)
            if original_action == "run_all":
                current_metadata["action_needed"] = "generate_voiceover"
            else:
                current_metadata.pop("action_needed", None)
            
            current_metadata.pop("missing_dependencies", None)
            self.supabase.update_job_status(job_id, "pending", metadata=current_metadata)
            
            print(f"\n✅ Script generation complete - ready for voiceover")
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

