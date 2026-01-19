#!/usr/bin/env python3
"""
Base Worker Class
Shared functionality for all specialized workers
"""

import time
import sys
import threading
from typing import List, Dict, Any, Optional, Tuple
from config import WORKER_POLL_INTERVAL, WORKER_MAX_CONCURRENT_JOBS
from supabase_client import SupabaseClient


class BaseWorker:
    """Base class for all specialized workers"""
    
    def __init__(self, worker_name: str):
        """Initialize base worker"""
        self.worker_name = worker_name
        self.supabase = SupabaseClient()
        self.active_jobs = set()  # Track jobs currently being processed
        self.active_jobs_lock = threading.Lock()  # Lock for thread-safe access
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
            # Skip jobs that are already being processed (not pending)
            if job.get("status") != "pending":
                continue
            
            metadata = job.get("metadata", {})
            job_action = metadata.get("action_needed")
            
            # Check if this job needs our action
            # Also handle "run_all" - each worker processes it in sequence
            # Also check for original_action in metadata (preserved from run_all)
            original_action = metadata.get("original_action")
            
            # For run_all flow:
            # - Script worker: action_needed should be "generate_script" (set by frontend) OR original_action is "run_all"
            # - Voiceover worker: action_needed should be "generate_voiceover" (set by script worker) AND original_action is "run_all"
            # - Video worker: action_needed should be "create_video" (set by voiceover worker) AND original_action is "run_all"
            should_process = (
                job_action == action_needed or
                (action_needed == "generate_script" and (job_action == "generate_script" and original_action == "run_all")) or
                (action_needed == "generate_voiceover" and (job_action == "generate_voiceover" and original_action == "run_all")) or
                (action_needed == "create_video" and (job_action == "create_video" and original_action == "run_all"))
                # Note: post_to_youtube is NOT included in run_all - YouTube posting must be done manually
            )
            
            if should_process:
                # Check dependencies
                is_ready, missing = self.check_dependencies(job)
                if is_ready:
                    # Immediately mark as processing to prevent duplicate pickup
                    # This is a critical step to prevent race conditions
                    processing_status = {
                        "generating_script": "generating_script",
                        "generate_voiceover": "creating_voiceover",
                        "create_video": "rendering_video",
                        "post_to_youtube": "uploading"
                    }.get(action_needed, "pending")
                    
                    # Try to claim the job by updating status atomically
                    # If update fails, another worker already claimed it
                    try:
                        updated = self.supabase.update_job_status(
                            job["id"],
                            status=processing_status,
                            metadata=metadata  # Preserve metadata
                        )
                        if updated:
                            ready_jobs.append(job)
                        else:
                            print(f"  ⚠️  Job {job['id'][:8]} already claimed by another worker")
                    except Exception as e:
                        print(f"  ⚠️  Failed to claim job {job['id'][:8]}: {e}")
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
    
    def _process_job_thread(self, job: Dict[str, Any], action_needed: str):
        """Process a single job in a separate thread"""
        job_id = job["id"]
        try:
            print(f"\n{'='*60}")
            print(f"📹 {self.worker_name} processing Job: {job_id[:8]}...")
            print(f"{'='*60}")
            self.process_job(job)
        except Exception as e:
            print(f"\n❌ {self.worker_name} error processing job {job_id[:8]}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Remove from active jobs when done
            with self.active_jobs_lock:
                self.active_jobs.discard(job_id)
    
    def run(self, action_needed: str):
        """
        Main worker loop - polls for jobs and processes them in parallel
        
        Args:
            action_needed: The action this worker handles
        """
        max_concurrent = max(1, WORKER_MAX_CONCURRENT_JOBS)  # At least 1
        print(f"\n🔄 {self.worker_name} started - polling every {WORKER_POLL_INTERVAL} seconds")
        print(f"   Looking for jobs with action: {action_needed}")
        print(f"   Max concurrent jobs: {max_concurrent}")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check how many jobs we can start
                with self.active_jobs_lock:
                    available_slots = max_concurrent - len(self.active_jobs)
                
                if available_slots > 0:
                    # Get jobs ready for this worker (up to available slots)
                    jobs = self.get_pending_jobs(action_needed)
                    
                    # Filter out jobs already being processed
                    with self.active_jobs_lock:
                        new_jobs = [job for job in jobs if job["id"] not in self.active_jobs]
                    
                    # Start processing new jobs (up to available slots)
                    for job in new_jobs[:available_slots]:
                        job_id = job["id"]
                        with self.active_jobs_lock:
                            self.active_jobs.add(job_id)
                        
                        # Start job in a separate thread
                        thread = threading.Thread(
                            target=self._process_job_thread,
                            args=(job, action_needed),
                            daemon=True
                        )
                        thread.start()
                        print(f"🚀 Started processing job {job_id[:8]}... (active: {len(self.active_jobs)}/{max_concurrent})")
                
                # Wait before next poll
                time.sleep(WORKER_POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 {self.worker_name} stopped by user")
            # Wait for active jobs to complete
            with self.active_jobs_lock:
                if self.active_jobs:
                    print(f"⏳ Waiting for {len(self.active_jobs)} active job(s) to complete...")
                    while self.active_jobs:
                        time.sleep(1)
        except Exception as e:
            print(f"\n❌ {self.worker_name} error: {e}")
            import traceback
            traceback.print_exc()

