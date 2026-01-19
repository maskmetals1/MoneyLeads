"""
Supabase Client Module
Handles all Supabase database and storage operations
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, STORAGE_BUCKET_VOICEOVERS, STORAGE_BUCKET_RENDERS, STORAGE_BUCKET_SCRIPTS, LOCAL_VIDEOS_DIR, LOCAL_VOICEOVERS_DIR
import uuid
import shutil
from datetime import datetime


class SupabaseClient:
    """Client for interacting with Supabase database and storage"""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase URL and Service Key must be set in config")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    # ========== Job Management ==========
    
    def create_job(self, topic: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new video job"""
        job_data = {
            "topic": topic,
            "status": "pending",
            "metadata": metadata or {}
        }
        
        result = self.client.table("video_jobs").insert(job_data).execute()
        return result.data[0] if result.data else None
    
    def get_pending_jobs(self, limit: int = 1) -> List[Dict[str, Any]]:
        """Get pending jobs (for worker to process)"""
        result = self.client.table("video_jobs")\
            .select("*")\
            .eq("status", "pending")\
            .order("created_at", desc=False)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []
    
    def update_job_status(self, job_id: str, status: Optional[str] = None, error_message: Optional[str] = None, **updates) -> bool:
        """Update job status and other fields"""
        update_data = {
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Only update status if provided (not None)
        if status is not None:
            update_data["status"] = status
            
            # Set started_at if status is not pending
            if status != "pending" and "started_at" not in updates:
                existing = self.get_job(job_id)
                if existing and not existing.get("started_at"):
                    update_data["started_at"] = datetime.utcnow().isoformat()
            
            # Set completed_at if status is completed or failed
            if status in ["completed", "failed"]:
                update_data["completed_at"] = datetime.utcnow().isoformat()
        
        if error_message:
            update_data["error_message"] = error_message
        
        # Merge any additional updates
        update_data.update(updates)
        
        result = self.client.table("video_jobs")\
            .update(update_data)\
            .eq("id", job_id)\
            .execute()
        
        return len(result.data) > 0
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a single job by ID"""
        result = self.client.table("video_jobs")\
            .select("*")\
            .eq("id", job_id)\
            .execute()
        
        return result.data[0] if result.data else None
    
    def get_all_jobs(self, limit: int = 100, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all jobs, optionally filtered by status"""
        query = self.client.table("video_jobs").select("*")
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        return result.data if result.data else []
    
    # ========== File Storage ==========
    
    def upload_file(self, file_path: Path, bucket: str, file_name: Optional[str] = None) -> str:
        """Upload a file to Supabase Storage and return the public URL"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate unique filename if not provided
        if not file_name:
            file_name = f"{uuid.uuid4()}{file_path.suffix}"
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Upload to storage
        result = self.client.storage.from_(bucket).upload(
            path=file_name,
            file=file_content,
            file_options={"content-type": self._get_content_type(file_path.suffix)}
        )
        
        # Get public URL
        url_result = self.client.storage.from_(bucket).get_public_url(file_name)
        return url_result
    
    def save_voiceover_path(self, file_path: Path, job_id: str) -> str:
        """Save voiceover file locally with unique name and return the local path"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate unique filename: job_id_timestamp_uuid.mp3
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{job_id}_{timestamp}_{unique_id}.mp3"
        
        # Save to local storage directory
        local_path = LOCAL_VOICEOVERS_DIR / filename
        
        # Copy file to local storage
        shutil.copy2(file_path, local_path)
        
        # Store absolute path in database
        absolute_path = str(local_path.absolute())
        self.update_job_status(job_id, status=None, voiceover_url=absolute_path)
        
        return absolute_path
    
    def save_video_path(self, file_path: Path, job_id: str) -> str:
        """Save video file locally with unique name and return the local path"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate unique filename: job_id_timestamp_uuid.mp4
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{job_id}_{timestamp}_{unique_id}.mp4"
        
        # Save to local storage directory
        local_path = LOCAL_VIDEOS_DIR / filename
        
        # Copy file to local storage
        shutil.copy2(file_path, local_path)
        
        # Store absolute path in database
        absolute_path = str(local_path.absolute())
        self.update_job_status(job_id, status=None, video_url=absolute_path)
        
        return absolute_path
    
    # Keep old methods for backward compatibility (if needed)
    def upload_voiceover(self, file_path: Path, job_id: str) -> str:
        """Legacy method - now saves locally instead of uploading"""
        return self.save_voiceover_path(file_path, job_id)
    
    def upload_video(self, file_path: Path, job_id: str) -> str:
        """Legacy method - now saves locally instead of uploading"""
        return self.save_video_path(file_path, job_id)
    
    def upload_script(self, file_path: Path, job_id: str) -> str:
        """Upload script text file (optional)"""
        file_name = f"{job_id}/script.txt"
        url = self.upload_file(file_path, STORAGE_BUCKET_SCRIPTS, file_name)
        
        # Update job with script URL
        self.update_job_status(job_id, status=None, script_url=url)
        
        return url
    
    def _get_content_type(self, suffix: str) -> str:
        """Get content type from file extension"""
        content_types = {
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".txt": "text/plain",
            ".ass": "text/x-ass"
        }
        return content_types.get(suffix.lower(), "application/octet-stream")
    
    # ========== YouTube Integration ==========
    
    def save_youtube_video(self, job_id: str, youtube_video_id: str, title: str, 
                          description: Optional[str] = None) -> Dict[str, Any]:
        """Save YouTube video information"""
        video_data = {
            "job_id": job_id,
            "video_id": youtube_video_id,
            "title": title,
            "description": description,
            "published_at": datetime.utcnow().isoformat()
        }
        
        result = self.client.table("youtube_videos").insert(video_data).execute()
        return result.data[0] if result.data else None
    
    def update_job_with_youtube(self, job_id: str, youtube_video_id: str, youtube_url: str):
        """Update job with YouTube video information"""
        self.update_job_status(
            job_id,
            status="completed",
            youtube_video_id=youtube_video_id,
            youtube_url=youtube_url
        )
    
    # ========== Helper Methods ==========
    
    def update_job_script(self, job_id: str, script: str, title: str, description: str, tags: List[str]):
        """Update job with generated script, title, description, and tags"""
        self.update_job_status(
            job_id,
            status=None,
            script=script,
            title=title,
            description=description,
            tags=tags
        )

