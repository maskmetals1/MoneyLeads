#!/usr/bin/env python3
"""
Loop a video multiple times to create a longer video
"""

import subprocess
from pathlib import Path
import tempfile

def loop_video(input_file: Path, output_file: Path, loops: int = 4):
    """Loop a video multiple times using ffmpeg"""
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        return False
    
    print(f"📹 Input: {input_file.name}")
    print(f"🔄 Looping {loops} times...")
    
    # Create file list for ffmpeg concat
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        concat_file = f.name
        escaped_path = str(input_file.absolute()).replace("'", "'\\''")
        for _ in range(loops):
            f.write(f"file '{escaped_path}'\n")
    
    print(f"\n💾 Creating: {output_file.name}")
    print(f"   Using stream copy (no re-encoding) - this will be fast!")
    
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
    input_file = Path("/Users/phill/Desktop/instagram_downloads/WebsiteBackground.mp4")
    output_file = Path("/Users/phill/Desktop/instagram_downloads/WebsiteBackground.mp4")
    loops = 4
    
    print("=" * 60)
    print("🔄 Video Looper")
    print("=" * 60)
    print()
    
    # Create temp output first
    temp_output = input_file.parent / "WebsiteBackground_temp.mp4"
    
    success = loop_video(input_file, temp_output, loops)
    
    if success:
        # Replace original with looped version
        if temp_output.exists():
            input_file.unlink()  # Delete original
            temp_output.rename(input_file)  # Rename temp to original
            print(f"\n✅ WebsiteBackground.mp4 now looped {loops} times!")
        else:
            print("\n❌ Failed to create looped video")
    else:
        print("\n❌ Failed!")
        if temp_output.exists():
            temp_output.unlink()
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()

