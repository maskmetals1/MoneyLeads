#!/usr/bin/env python3
"""
Download YouTube Video Thumbnails
Downloads all thumbnails from a YouTube playlist or channel
"""

import sys
import requests
from pathlib import Path
from typing import List, Optional
import argparse
import re
from urllib.parse import urlparse, parse_qs

# Try to use YouTube API if available
try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle
    from config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("⚠️  YouTube API not available - will use direct URL method")

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']


def get_youtube_service():
    """Get authenticated YouTube API service"""
    if not YOUTUBE_API_AVAILABLE:
        return None
    
    creds = None
    token_path = Path.home() / ".youtube_token.pickle"
    credentials_path = Path.home() / ".youtube_credentials.json"
    
    # Load existing token
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print("❌ YouTube credentials not found. Please set up YouTube API first.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('youtube', 'v3', credentials=creds)


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from YouTube URL"""
    # Handle different URL formats
    patterns = [
        r'[?&]list=([a-zA-Z0-9_-]+)',
        r'/playlist\?list=([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def extract_channel_id(url: str) -> Optional[str]:
    """Extract channel ID from YouTube URL"""
    patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
        r'youtube\.com/user/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_video_ids_from_playlist_api(playlist_id: str, service) -> List[str]:
    """Get all video IDs from a playlist using YouTube API"""
    video_ids = []
    next_page_token = None
    
    try:
        while True:
            request = service.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    except Exception as e:
        print(f"❌ Error fetching playlist: {e}")
        return []


def get_video_ids_from_channel_api(channel_id: str, service) -> List[str]:
    """Get all video IDs from a channel using YouTube API"""
    video_ids = []
    next_page_token = None
    
    try:
        while True:
            request = service.search().list(
                part='id',
                channelId=channel_id,
                type='video',
                maxResults=50,
                pageToken=next_page_token,
                order='date'
            )
            response = request.execute()
            
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                video_ids.append(video_id)
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        
        return video_ids
    except Exception as e:
        print(f"❌ Error fetching channel videos: {e}")
        return []


def get_video_ids_from_url(url: str, service=None) -> List[str]:
    """Get video IDs from a YouTube URL (playlist or channel)"""
    playlist_id = extract_playlist_id(url)
    if playlist_id:
        print(f"📋 Found playlist ID: {playlist_id}")
        if service:
            return get_video_ids_from_playlist_api(playlist_id, service)
        else:
            print("⚠️  YouTube API not available - cannot fetch playlist videos")
            print("   Please install YouTube API credentials or use yt-dlp")
            return []
    
    channel_id = extract_channel_id(url)
    if channel_id:
        print(f"📺 Found channel ID: {channel_id}")
        if service:
            return get_video_ids_from_channel_api(channel_id, service)
        else:
            print("⚠️  YouTube API not available - cannot fetch channel videos")
            print("   Please install YouTube API credentials or use yt-dlp")
            return []
    
    # Try to extract video ID if it's a single video
    video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
    if video_id_match:
        return [video_id_match.group(1)]
    
    print(f"❌ Could not extract playlist/channel ID from URL: {url}")
    return []


def download_thumbnail(video_id: str, output_dir: Path, quality: str = "maxresdefault") -> bool:
    """
    Download thumbnail for a video ID
    
    Quality options:
    - maxresdefault: 1280x720 (best quality)
    - sddefault: 640x480
    - hqdefault: 480x360
    - mqdefault: 320x180
    - default: 120x90
    """
    url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
    
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Check if we got a valid image (YouTube returns a placeholder if thumbnail doesn't exist)
        if response.headers.get('content-type', '').startswith('image/'):
            output_path = output_dir / f"{video_id}_{quality}.jpg"
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            print(f"  ⚠️  No thumbnail available for {video_id}")
            return False
    except Exception as e:
        print(f"  ❌ Error downloading thumbnail for {video_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube video thumbnails from a playlist or channel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from a playlist
  python download_thumbnails.py "https://www.youtube.com/playlist?list=PLxxxxx"
  
  # Download from a channel
  python download_thumbnails.py "https://www.youtube.com/@channelname"
  
  # Download from a single video
  python download_thumbnails.py "https://www.youtube.com/watch?v=xxxxx"
  
  # Use lower quality thumbnails (faster)
  python download_thumbnails.py "https://www.youtube.com/playlist?list=PLxxxxx" --quality hqdefault
        """
    )
    
    parser.add_argument(
        "url",
        type=str,
        help="YouTube playlist, channel, or video URL"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path(__file__).parent / "thumbnails",
        help="Output directory for thumbnails (default: ./thumbnails)"
    )
    
    parser.add_argument(
        "-q", "--quality",
        type=str,
        default="maxresdefault",
        choices=["maxresdefault", "sddefault", "hqdefault", "mqdefault", "default"],
        help="Thumbnail quality (default: maxresdefault)"
    )
    
    args = parser.parse_args()
    
    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {args.output}")
    
    # Try to get YouTube API service
    service = None
    if YOUTUBE_API_AVAILABLE:
        try:
            service = get_youtube_service()
            if service:
                print("✅ YouTube API authenticated")
        except Exception as e:
            print(f"⚠️  Could not authenticate YouTube API: {e}")
            print("   Will try to extract video IDs from URL directly...")
    
    # Get video IDs
    print(f"\n🔍 Extracting video IDs from: {args.url}")
    video_ids = get_video_ids_from_url(args.url, service)
    
    if not video_ids:
        print("❌ No video IDs found. Please check the URL.")
        return 1
    
    print(f"✅ Found {len(video_ids)} video(s)")
    
    # Download thumbnails
    print(f"\n📥 Downloading thumbnails (quality: {args.quality})...")
    success_count = 0
    failed_count = 0
    
    for i, video_id in enumerate(video_ids, 1):
        print(f"  [{i}/{len(video_ids)}] Downloading {video_id}...", end=" ")
        if download_thumbnail(video_id, args.output, args.quality):
            print("✅")
            success_count += 1
        else:
            print("❌")
            failed_count += 1
    
    print(f"\n✅ Complete!")
    print(f"   Success: {success_count}")
    if failed_count > 0:
        print(f"   Failed: {failed_count}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

