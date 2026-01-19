#!/usr/bin/env python3
"""
Download YouTube Video Thumbnails
Downloads all thumbnails from a YouTube playlist or channel using yt-dlp
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional
import argparse
import shutil


def check_yt_dlp() -> bool:
    """Check if yt-dlp is installed"""
    return shutil.which("yt-dlp") is not None


def download_thumbnails_yt_dlp(url: str, output_dir: Path) -> bool:
    """
    Download thumbnails using yt-dlp
    
    Args:
        url: YouTube playlist, channel, or video URL
        output_dir: Directory to save thumbnails
    
    Returns:
        True if successful, False otherwise
    """
    if not check_yt_dlp():
        print("❌ yt-dlp is not installed!")
        print("   Install with: pip install yt-dlp")
        print("   Or: brew install yt-dlp")
        return False
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to output directory so yt-dlp saves files there
    original_cwd = Path.cwd()
    
    try:
        # Change to output directory
        import os
        os.chdir(output_dir)
        
        # Build yt-dlp command
        # --no-download: Don't download video
        # --write-thumbnail: Download thumbnail
        # -w: Don't overwrite existing files
        # -o: Output filename template
        cmd = [
            "yt-dlp",
            "--no-download",
            "--write-thumbnail",
            "-w",  # Don't overwrite existing files
            "-o", "%(title)s(%(id)s).%(ext)s",  # Format: Title(VideoID).jpg
            url
        ]
        
        print(f"📥 Downloading thumbnails from: {url}")
        print(f"📁 Saving to: {output_dir}")
        print(f"⏳ This may take a while for large playlists/channels...\n")
        
        # Run yt-dlp
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Count downloaded files
            thumbnail_files = list(output_dir.glob("*.jpg")) + list(output_dir.glob("*.webp"))
            print(f"\n✅ Successfully downloaded {len(thumbnail_files)} thumbnail(s)")
            return True
        else:
            print(f"❌ Error running yt-dlp:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Change back to original directory
        import os
        os.chdir(original_cwd)


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube video thumbnails from a playlist or channel using yt-dlp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from a playlist
  python download_thumbnails.py "https://www.youtube.com/playlist?list=PLxxxxx"
  
  # Download from a channel
  python download_thumbnails.py "https://www.youtube.com/@channelname"
  
  # Download from a single video
  python download_thumbnails.py "https://www.youtube.com/watch?v=xxxxx"
  
  # Custom output folder
  python download_thumbnails.py "https://www.youtube.com/playlist?list=PLxxxxx" -o ./my_thumbnails

Note: Requires yt-dlp to be installed
  Install with: pip install yt-dlp
  Or: brew install yt-dlp
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
    
    args = parser.parse_args()
    
    # Download thumbnails using yt-dlp
    success = download_thumbnails_yt_dlp(args.url, args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

