#!/usr/bin/env python3
"""
Check if workers are running and processing jobs
"""

import subprocess
import sys
from pathlib import Path
from supabase_client import SupabaseClient
from config import validate_config

def check_running_processes():
    """Check if worker processes are running"""
    print("=" * 60)
    print("🔍 Checking Running Worker Processes")
    print("=" * 60)
    print()
    
    workers = [
        "worker_script.py",
        "worker_voiceover.py",
        "worker_video.py",
        "worker_youtube.py",
        "worker.py"  # Old worker
    ]
    
    running_workers = []
    
    for worker in workers:
        try:
            # Check if process is running
            result = subprocess.run(
                ["pgrep", "-f", worker],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        # Get process details
                        ps_result = subprocess.run(
                            ["ps", "-p", pid, "-o", "pid,etime,command"],
                            capture_output=True,
                            text=True
                        )
                        if ps_result.returncode == 0:
                            lines = ps_result.stdout.strip().split('\n')
                            if len(lines) > 1:
                                running_workers.append({
                                    "worker": worker,
                                    "pid": pid,
                                    "info": lines[1]
                                })
        except Exception as e:
            pass
    
    if running_workers:
        print("✅ Running Workers:")
        for w in running_workers:
            print(f"   📌 {w['worker']} (PID: {w['pid']})")
            print(f"      {w['info']}")
        print()
    else:
        print("❌ No workers are currently running")
        print()
        print("💡 To start workers, run:")
        print("   source venv/bin/activate")
        print("   python3 worker_script.py &")
        print("   python3 worker_voiceover.py &")
        print("   python3 worker_video.py &")
        print("   python3 worker_youtube.py &")
        print()
    
    return len(running_workers) > 0

def check_job_status():
    """Check job status in Supabase"""
    print("=" * 60)
    print("📊 Checking Job Status in Database")
    print("=" * 60)
    print()
    
    try:
        # Skip full validation - we just need Supabase connection
        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Supabase configuration missing")
            return
        client = SupabaseClient()
        
        # Get all jobs
        all_jobs = client.get_all_jobs(limit=20)
        
        if not all_jobs:
            print("ℹ️  No jobs found in database")
            return
        
        # Count by status
        status_counts = {}
        pending_jobs = []
        processing_jobs = []
        
        for job in all_jobs:
            status = job.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status == "pending":
                metadata = job.get("metadata", {})
                action_needed = metadata.get("action_needed")
                pending_jobs.append({
                    "id": job["id"][:8],
                    "topic": job.get("topic", "N/A"),
                    "action": action_needed or "next step"
                })
            elif status in ["generating_script", "creating_voiceover", "rendering_video", "uploading"]:
                processing_jobs.append({
                    "id": job["id"][:8],
                    "topic": job.get("topic", "N/A"),
                    "status": status
                })
        
        print("📈 Job Status Summary:")
        for status, count in sorted(status_counts.items()):
            emoji = {
                "pending": "⏳",
                "generating_script": "📝",
                "creating_voiceover": "🎤",
                "rendering_video": "🎬",
                "uploading": "📤",
                "completed": "✅",
                "failed": "❌"
            }.get(status, "📋")
            print(f"   {emoji} {status}: {count}")
        print()
        
        if pending_jobs:
            print(f"⏳ Pending Jobs ({len(pending_jobs)}):")
            for job in pending_jobs[:5]:  # Show first 5
                print(f"   • {job['id']}... - {job['topic']} (needs: {job['action']})")
            if len(pending_jobs) > 5:
                print(f"   ... and {len(pending_jobs) - 5} more")
            print()
        
        if processing_jobs:
            print(f"🔄 Currently Processing ({len(processing_jobs)}):")
            for job in processing_jobs:
                print(f"   • {job['id']}... - {job['topic']} ({job['status']})")
            print()
        else:
            if pending_jobs:
                print("⚠️  There are pending jobs but none are being processed")
                print("   Make sure workers are running!")
                print()
        
    except Exception as e:
        print(f"❌ Error checking job status: {e}")
        import traceback
        traceback.print_exc()

def check_recent_activity():
    """Check for recent job updates"""
    print("=" * 60)
    print("🕐 Recent Activity (Last 10 Jobs)")
    print("=" * 60)
    print()
    
    try:
        client = SupabaseClient()
        jobs = client.get_all_jobs(limit=10)
        
        if not jobs:
            print("ℹ️  No jobs found")
            return
        
        from datetime import datetime
        
        print("Recent Jobs:")
        for job in jobs:
            job_id = job["id"][:8]
            topic = job.get("topic", "N/A")[:30]
            status = job.get("status", "unknown")
            updated = job.get("updated_at", job.get("created_at", ""))
            
            # Parse timestamp
            try:
                if updated:
                    dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    time_ago = datetime.now(dt.tzinfo) - dt
                    if time_ago.total_seconds() < 60:
                        time_str = f"{int(time_ago.total_seconds())}s ago"
                    elif time_ago.total_seconds() < 3600:
                        time_str = f"{int(time_ago.total_seconds() / 60)}m ago"
                    else:
                        time_str = f"{int(time_ago.total_seconds() / 3600)}h ago"
                else:
                    time_str = "unknown"
            except:
                time_str = "unknown"
            
            emoji = {
                "pending": "⏳",
                "generating_script": "📝",
                "creating_voiceover": "🎤",
                "rendering_video": "🎬",
                "uploading": "📤",
                "completed": "✅",
                "failed": "❌"
            }.get(status, "📋")
            
            print(f"   {emoji} {job_id}... | {topic} | {status} | {time_str}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🔍 Worker & Job Status Checker")
    print("=" * 60)
    print()
    
    # Check running processes
    workers_running = check_running_processes()
    
    # Check job status
    check_job_status()
    
    # Check recent activity
    check_recent_activity()
    
    # Summary
    print("=" * 60)
    if workers_running:
        print("✅ Workers are running")
    else:
        print("⚠️  No workers detected - jobs won't be processed")
        print("   Start workers to process pending jobs")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()

