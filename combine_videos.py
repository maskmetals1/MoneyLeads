#!/usr/bin/env python3
"""
Combine all videos in instagram_downloads folder into one video using ffmpeg
This is much faster than using moviepy!
"""

import subprocess
from pathlib import Path
import tempfile

def combine_videos_ffmpeg(input_folder: Path, output_file: Path):
    """Combine all videos using ffmpeg (much faster!)"""
    
    print(f"📁 Loading videos from: {input_folder}")
    
    # Get all video files
    video_extensions = {".mp4", ".mov", ".avi", ".webm", ".m4v"}
    video_files = sorted([
        f for f in input_folder.iterdir()
        if f.is_file() and f.suffix.lower() in video_extensions
    ])
    
    if not video_files:
        print(f"❌ No video files found in {input_folder}")
        return False
    
    print(f"📹 Found {len(video_files)} video(s)")
    
    # Create file list for ffmpeg concat
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        for video_file in video_files:
            # Escape single quotes and special characters for ffmpeg
            escaped_path = str(video_file.absolute()).replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    print(f"\n🔗 Concatenating {len(video_files)} video(s) using ffmpeg...")
    print(f"   This is much faster than moviepy!")
    
    try:
        # Use ffmpeg concat demuxer (fastest method)
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',  # Copy streams (no re-encoding = very fast!)
            '-y',  # Overwrite output file
            str(output_file)
        ]
        
        print(f"\n💾 Creating: {output_file.name}")
        print(f"   Using stream copy (no re-encoding) - this will be fast!")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Cleanup
        Path(concat_file).unlink()
        
        if output_file.exists():
            file_size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"\n✅ Successfully created: {output_file.name}")
            print(f"   File size: {file_size_mb:.2f} MB")
            
            # Get duration
            duration_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(output_file)
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            if duration_result.returncode == 0:
                duration = float(duration_result.stdout.strip())
                print(f"   Duration: {duration:.2f}s ({duration/60:.2f} minutes)")
            
            return True
        else:
            print(f"❌ Output file was not created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error:")
        print(f"   {e.stderr}")
        Path(concat_file).unlink()
        return False
    except FileNotFoundError:
        print(f"❌ FFmpeg not found. Install with: brew install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        if Path(concat_file).exists():
            Path(concat_file).unlink()
        return False

def main():
    input_folder = Path("/Users/phill/Desktop/instagram_downloads")
    output_file = input_folder / "WebsiteBackground.mp4"
    
    print("=" * 60)
    print("🎬 Video Combiner (FFmpeg - Fast!)")
    print("=" * 60)
    print()
    
    if output_file.exists():
        response = input(f"⚠️  {output_file.name} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    success = combine_videos_ffmpeg(input_folder, output_file)
    
    if success:
        print("\n✅ Done! WebsiteBackground.mp4 is ready!")
    else:
        print("\n❌ Failed!")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
