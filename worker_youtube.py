#!/usr/bin/env python3
"""
YouTube Upload Worker
Only handles YouTube uploads
Dependencies: title, description, video_url
"""

import sys
import requests
import shutil
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from base_worker import BaseWorker
from youtube_uploader import YouTubeUploader
from config import THUMBNAILS_DIR


class YouTubeWorker(BaseWorker):
    """Worker that uploads videos to YouTube"""
    
    def __init__(self):
        super().__init__("YouTube Worker")
        self.youtube_uploader = YouTubeUploader()
        print("✅ YouTube Worker initialized")
    
    def check_dependencies(self, job: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if job has all required dependencies for YouTube upload
        
        Dependencies: title, description, video_url
        """
        missing = []
        
        # Title is required
        if not job.get("title"):
            missing.append("title")
        
        # Description is required (can be empty string, but field should exist)
        if job.get("description") is None:
            missing.append("description")
        
        # Video URL is required
        if not job.get("video_url"):
            missing.append("video_url")
        
        return len(missing) == 0, missing
    
    def get_random_thumbnail(self) -> Optional[Path]:
        """
        Get a random thumbnail from the thumbnails folder
        Converts WEBP to JPG if needed (YouTube API doesn't accept WEBP)
        
        Returns:
            Path to thumbnail file (converted to JPG if needed), or None if no thumbnails found
        """
        if not THUMBNAILS_DIR.exists():
            print(f"  ⚠️  Thumbnails directory not found: {THUMBNAILS_DIR}")
            return None
        
        # Get all image files (webp, jpg, jpeg, png)
        image_extensions = {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        thumbnails = [
            f for f in THUMBNAILS_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
            and not f.name.startswith('.')  # Skip hidden files like .DS_Store
        ]
        
        if not thumbnails:
            print(f"  ⚠️  No thumbnails found in {THUMBNAILS_DIR}")
            return None
        
        # Select random thumbnail
        selected = random.choice(thumbnails)
        print(f"  🖼️  Selected thumbnail: {selected.name}")
        
        # YouTube API accepts: JPG, PNG, GIF, BMP (not WEBP)
        # Convert WEBP to JPG if needed
        if selected.suffix.lower() == '.webp':
            try:
                from PIL import Image
                import tempfile
                
                # Convert WEBP to JPG
                print(f"  🔄 Converting WEBP to JPG for YouTube compatibility...")
                img = Image.open(selected)
                # Convert RGBA to RGB if needed (JPG doesn't support transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as JPG to temp file
                temp_jpg = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_jpg_path = Path(temp_jpg.name)
                img.save(temp_jpg_path, 'JPEG', quality=95)
                temp_jpg.close()
                
                print(f"  ✅ Converted to JPG: {temp_jpg_path.name}")
                return temp_jpg_path
            except ImportError:
                print(f"  ⚠️  PIL/Pillow not available, cannot convert WEBP. Skipping thumbnail.")
                return None
            except Exception as e:
                print(f"  ⚠️  Failed to convert WEBP to JPG: {e}. Skipping thumbnail.")
                return None
        
        # Return original if already in supported format
        return selected
    
    def process_job(self, job: Dict[str, Any]) -> bool:
        """Process YouTube upload job"""
        job_id = job["id"]
        title = job.get("title")
        description = job.get("description", "")
        video_url = job.get("video_url")
        tags = job.get("tags", [])
        metadata = job.get("metadata", {})
        privacy_status = metadata.get("privacy_status", "public")  # Default to public
        
        if not title:
            print(f"❌ Title not found for job {job_id}")
            return False
        
        if not video_url:
            print(f"❌ Video URL not found for job {job_id}")
            return False
        
        try:
            print(f"\n[1/2] Locating video file...")
            self.supabase.update_job_status(job_id, "uploading")
            
            temp_dir = None
            # Check if video_url is a local path or URL
            if video_url.startswith('http://') or video_url.startswith('https://'):
                # Download from URL (backward compatibility)
                print(f"  📥 Downloading video from URL...")
                temp_dir = Path(f"/tmp/youtube_automation_{job_id}")
                temp_dir.mkdir(parents=True, exist_ok=True)
                video_path = temp_dir / "video.mp4"
                
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  ✅ Video downloaded")
            else:
                # Use local file path directly
                video_path = Path(video_url)
                if not video_path.exists():
                    raise FileNotFoundError(f"Video file not found at local path: {video_path}")
                print(f"  ✅ Using local video: {video_path}")
            
            # Get random thumbnail
            thumbnail_path = self.get_random_thumbnail()
            
            # Upload to YouTube
            print(f"\n[2/2] Uploading to YouTube...")
            youtube_result = self.youtube_uploader.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags if isinstance(tags, list) else [],
                privacy_status=privacy_status,
                thumbnail_path=thumbnail_path
            )
            
            youtube_video_id = youtube_result["video_id"]
            youtube_url = youtube_result["video_url"]
            
            # Save YouTube video info immediately
            self.supabase.save_youtube_video(job_id, youtube_video_id, title, description)
            self.supabase.update_job_with_youtube(job_id, youtube_video_id, youtube_url)
            
            print(f"  ✅ Uploaded to YouTube and saved: {youtube_url}")
            
            # Clear action_needed
            current_job = self.supabase.get_job(job_id)
            current_metadata = current_job.get("metadata", {}) if current_job else {}
            current_metadata.pop("action_needed", None)
            current_metadata.pop("missing_dependencies", None)
            self.supabase.update_job_status(job_id, "completed", metadata=current_metadata)
            
            # Cleanup temp files
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            # Cleanup converted thumbnail temp file if it was created (WEBP -> JPG conversion)
            if thumbnail_path and thumbnail_path.exists() and '/tmp' in str(thumbnail_path) and thumbnail_path.suffix.lower() == '.jpg':
                try:
                    thumbnail_path.unlink()
                    print(f"  🗑️  Cleaned up temporary thumbnail file")
                except:
                    pass
            
            print(f"\n✅ YouTube upload complete!")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ YouTube upload failed: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Cleanup temp files even on error
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            
            # Cleanup converted thumbnail temp file if it was created
            if 'thumbnail_path' in locals() and thumbnail_path and thumbnail_path.exists() and '/tmp' in str(thumbnail_path) and thumbnail_path.suffix.lower() == '.jpg':
                try:
                    thumbnail_path.unlink()
                except:
                    pass
            
            self.supabase.update_job_status(
                job_id,
                "failed",
                error_message=error_msg
            )
            return False


def main():
    """Main entry point"""
    worker = YouTubeWorker()
    worker.run("post_to_youtube")


if __name__ == "__main__":
    main()

