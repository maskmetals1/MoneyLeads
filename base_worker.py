#!/usr/bin/env python3
"""
Base Worker Class
Shared functionality for all specialized workers
"""

import time
import sys
from typing import List, Dict, Any, Optional, Tuple
from config import WORKER_POLL_INTERVAL, WORKER_MAX_CONCURRENT_JOBS
from supabase_client import SupabaseClient


class BaseWorker:
    """Base class for all specialized workers"""
    
    def __init__(self, worker_name: str):
        """Initialize base worker"""
        self.worker_name = worker_name
        self.supabase = SupabaseClient()
        print(f"🚀 Initializing {worker_name}...")
    
    def check_dependencies(self, job: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if job has all required dependencies
        
        Returns:
            (is_ready, missing_fields) - tuple of (bool, list of missing field names)
        """
        raise NotImplementedError("Subclasses must implement check_dependencies")
    
    def process_job(self, job: Dict[str, Any]) -> bool:
        """
        Process a single job
        
        Args:
            job: Job dictionary from Supabase
        
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement process_job")
    
    def get_pending_jobs(self, action_needed: str) -> List[Dict[str, Any]]:
        """
        Get pending jobs that need this worker's action
        
        Args:
            action_needed: The action this worker handles (e.g., 'generate_script')
        
        Returns:
            List of jobs ready to be processed
        """
        # Get all pending jobs
        all_jobs = self.supabase.get_pending_jobs(limit=WORKER_MAX_CONCURRENT_JOBS * 10)
        
        # Filter jobs that need this action
        ready_jobs = []
        for job in all_jobs:
            metadata = job.get("metadata", {})
            job_action = metadata.get("action_needed")
            
            # Check if this job needs our action
            # Also handle "run_all" - each worker processes it in sequence
            # Also check for original_action in metadata (preserved from run_all)
            original_action = metadata.get("original_action")
            should_process = (
                job_action == action_needed or
                (action_needed == "generate_script" and (job_action == "run_all" or original_action == "run_all")) or
                (action_needed == "generate_voiceover" and (job_action == "run_all" or original_action == "run_all")) or
                (action_needed == "create_video" and (job_action == "run_all" or original_action == "run_all")) or
                (action_needed == "post_to_youtube" and (job_action == "run_all" or original_action == "run_all"))
            )
            
            if should_process:
                # Check dependencies
                is_ready, missing = self.check_dependencies(job)
                if is_ready:
                    ready_jobs.append(job)
                else:
                    # Update job with missing dependencies info
                    current_metadata = job.get("metadata", {})
                    current_metadata["missing_dependencies"] = missing
                    self.supabase.update_job_status(
                        job["id"],
                        status=None,
                        metadata=current_metadata,
                        error_message=f"Missing dependencies: {', '.join(missing)}"
                    )
        
        return ready_jobs[:WORKER_MAX_CONCURRENT_JOBS]
    
    def run(self, action_needed: str):
        """
        Main worker loop - polls for jobs and processes them
        
        Args:
            action_needed: The action this worker handles
        """
        print(f"\n🔄 {self.worker_name} started - polling every {WORKER_POLL_INTERVAL} seconds")
        print(f"   Looking for jobs with action: {action_needed}")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Get jobs ready for this worker
                jobs = self.get_pending_jobs(action_needed)
                
                if jobs:
                    for job in jobs:
                        print(f"\n{'='*60}")
                        print(f"📹 {self.worker_name} processing Job: {job['id']}")
                        print(f"{'='*60}")
                        self.process_job(job)
                else:
                    print(f"⏳ No ready jobs for {self.worker_name}... (checking again in {WORKER_POLL_INTERVAL}s)")
                
                # Wait before next poll
                time.sleep(WORKER_POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 {self.worker_name} stopped by user")
        except Exception as e:
            print(f"\n❌ {self.worker_name} error: {e}")
            import traceback
            traceback.print_exc()

