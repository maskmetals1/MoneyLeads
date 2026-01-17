"""
YouTube API Uploader
Handles uploading videos to YouTube using YouTube Data API v3
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import pickle
from config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET


# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeUploader:
    """Handle YouTube video uploads"""
    
    def __init__(self, credentials_path: Optional[Path] = None, token_path: Optional[Path] = None):
        """
        Initialize YouTube uploader
        
        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to store/load OAuth token
        """
        self.credentials_path = credentials_path or Path.home() / ".youtube_credentials.json"
        self.token_path = token_path or Path.home() / ".youtube_token.pickle"
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube API"""
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Check if credentials file exists, or try using env vars
                if not self.credentials_path.exists():
                    # Try using environment variables if file doesn't exist
                    if YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET:
                        # Create a temporary credentials dict
                        import json
                        import tempfile
                        creds_dict = {
                            "installed": {
                                "client_id": YOUTUBE_CLIENT_ID,
                                "client_secret": YOUTUBE_CLIENT_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": ["http://localhost"]
                            }
                        }
                        # Create temp file for credentials
                        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                        json.dump(creds_dict, temp_file)
                        temp_file.close()
                        credentials_file = temp_file.name
                    else:
                        raise FileNotFoundError(
                            f"OAuth credentials file not found: {self.credentials_path}\n"
                            "Either:\n"
                            "  1. Download credentials from Google Cloud Console and save as ~/.youtube_credentials.json\n"
                            "  2. Or set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env file\n"
                            "See YOUTUBE_API_SETUP.md for detailed instructions"
                        )
                else:
                    credentials_file = str(self.credentials_path)
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
                # Clean up temp file if we created one
                if not self.credentials_path.exists() and YOUTUBE_CLIENT_ID:
                    import os
                    try:
                        os.unlink(credentials_file)
                    except:
                        pass
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('youtube', 'v3', credentials=creds)
    
    def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[list] = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "private",  # private, unlisted, or public
        thumbnail_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Upload a video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (default: 22 = People & Blogs)
            privacy_status: private, unlisted, or public
            thumbnail_path: Optional path to thumbnail image
        
        Returns:
            Dictionary with video_id and video_url
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }
        
        # Create media upload object
        media = MediaFileUpload(
            str(video_path),
            chunksize=-1,
            resumable=True,
            mimetype='video/mp4'
        )
        
        try:
            # Insert video
            insert_request = self.service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Execute upload
            response = None
            while response is None:
                status, response = insert_request.next_chunk()
                if status:
                    print(f"  📤 Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Upload thumbnail if provided
            if thumbnail_path and thumbnail_path.exists():
                try:
                    self.service.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(str(thumbnail_path))
                    ).execute()
                    print(f"  ✅ Thumbnail uploaded")
                except HttpError as e:
                    print(f"  ⚠️  Failed to upload thumbnail: {e}")
            
            return {
                "video_id": video_id,
                "video_url": video_url,
                "title": title
            }
            
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            error_msg = error_details.get('message', str(e))
            raise Exception(f"YouTube API error: {error_msg}")
    
    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get information about an uploaded video"""
        try:
            response = self.service.videos().list(
                part='snippet,statistics,status',
                id=video_id
            ).execute()
            
            if not response['items']:
                return None
            
            video = response['items'][0]
            return {
                "video_id": video_id,
                "title": video['snippet']['title'],
                "description": video['snippet']['description'],
                "published_at": video['snippet']['publishedAt'],
                "view_count": int(video['statistics'].get('viewCount', 0)),
                "like_count": int(video['statistics'].get('likeCount', 0)),
                "comment_count": int(video['statistics'].get('commentCount', 0)),
                "privacy_status": video['status']['privacyStatus']
            }
        except HttpError as e:
            print(f"Error getting video info: {e}")
            return None

