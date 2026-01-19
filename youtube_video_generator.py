#!/usr/bin/env python3
"""
YouTube Video Auto Generator
Creates YouTube videos from text scripts with voiceover, background footage, and word-highlighted captions.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# Fix for PIL.Image.ANTIALIAS compatibility issue with newer Pillow versions
# This must be done before importing moviepy
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass


def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import edge_tts
    except ImportError:
        missing.append("edge-tts")
    
    try:
        import moviepy.editor as mp
    except ImportError:
        missing.append("moviepy")
    
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    
    if missing:
        print("❌ Missing required dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nInstall with: pip install " + " ".join(missing))
        return False
    
    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  FFmpeg not found. Install with: brew install ffmpeg")
        print("   (Required for video rendering)")
        return False
    
    return True


def generate_voiceover(script_text: str, output_path: Path, voice: str = None) -> Tuple[bool, float]:
    """
    Generate voiceover from text using edge-tts
    
    Returns:
        (success: bool, duration: float)
    """
    try:
        import edge_tts
        import asyncio
        
        async def _generate():
            # Handle empty string as None (auto-select)
            if voice is None or voice == "":
                # Get list of voices and select a natural-sounding one
                voices = await edge_tts.list_voices()
                # Prefer English voices that sound natural
                preferred_voices = [
                    v for v in voices 
                    if "en" in v.get("Locale", "").lower() 
                    and "natural" in v.get("ShortName", "").lower()
                ]
                if preferred_voices:
                    selected_voice = preferred_voices[0]["ShortName"]
                else:
                    # Fallback to any English voice
                    english_voices = [v for v in voices if "en" in v.get("Locale", "").lower()]
                    selected_voice = english_voices[0]["ShortName"] if english_voices else "en-US-AriaNeural"
            else:
                selected_voice = voice
            
            print(f"  🎤 Using voice: {selected_voice}")
            print(f"  🎵 Generating voiceover...")
            
            communicate = edge_tts.Communicate(script_text, selected_voice)
            await communicate.save(str(output_path))
            
            # Get duration from the generated file
            import moviepy.editor as mp
            audio = mp.AudioFileClip(str(output_path))
            duration = audio.duration
            audio.close()
            
            return duration
        
        duration = asyncio.run(_generate())
        print(f"  ✅ Voiceover generated: {duration:.2f} seconds")
        return True, duration
        
    except Exception as e:
        print(f"  ❌ Error generating voiceover: {e}")
        import traceback
        traceback.print_exc()
        return False, 0.0


def compile_background_videos(folder_path: Path, target_duration: float, output_resolution: Tuple[int, int] = (1920, 1080)) -> Optional[object]:
    """
    Optimized: Use WebsiteBackground.mp4 if available (pre-rendered, fastest option)
    Otherwise use longest video
    Picks a random segment from the video to use as background
    Handles edge cases where random spot + duration would exceed video length
    
    Background video preprocessing: WebsiteBackground.mp4 is already pre-combined,
    so we just need to extract a random segment - much faster than compiling on-the-fly.
    
    Returns:
        VideoFileClip object or None
    """
    try:
        import moviepy.editor as mp
        import random
        
        print(f"  📁 Loading videos from: {folder_path}")
        
        # Check for WebsiteBackground.mp4 first (preferred - already pre-rendered/combined)
        # This is the background video preprocessing optimization - using pre-combined video
        website_bg = folder_path / "WebsiteBackground.mp4"
        if website_bg.exists():
            print(f"  ✅ Using WebsiteBackground.mp4 (pre-rendered, optimized!)")
            video_file = website_bg
        else:
            # Fallback: Find the longest video
            video_extensions = {".mp4", ".mov", ".avi", ".webm", ".m4v"}
            video_files = [
                f for f in folder_path.iterdir()
                if f.is_file() and f.suffix.lower() in video_extensions
            ]
            
            if not video_files:
                print(f"  ❌ No video files found in {folder_path}")
                return None
            
            # Use longest video (by file size as proxy for duration)
            video_file = max(video_files, key=lambda f: f.stat().st_size)
            print(f"  📹 Using longest video: {video_file.name}")
        
        # Load video once for background, once for foreground
        bg_source = mp.VideoFileClip(str(video_file))
        fg_source = mp.VideoFileClip(str(video_file))
        original_duration = bg_source.duration
        
        # Pick a random start point, ensuring we can get the full duration needed
        crop_duration = min(target_duration, original_duration)
        
        if original_duration >= crop_duration:
            # Calculate max start point to ensure we don't go past the end
            max_start_point = original_duration - crop_duration
            
            if max_start_point > 0:
                # Pick random start point
                random_start = random.uniform(0, max_start_point)
                random_end = random_start + crop_duration
                print(f"  🎲 Random segment: {random_start:.2f}s - {random_end:.2f}s (duration: {crop_duration:.2f}s)")
                print(f"     Video length: {original_duration:.2f}s, available range: 0 - {max_start_point:.2f}s")
            else:
                # Video is exactly the right length or shorter, use from start
                random_start = 0
                random_end = crop_duration
                print(f"  ✂️  Using from start: 0s - {crop_duration:.2f}s (video is {original_duration:.2f}s)")
        else:
            # Video is shorter than needed, use entire video
            random_start = 0
            random_end = original_duration
            crop_duration = original_duration
            print(f"  ⚠️  Video shorter than needed: using full video ({original_duration:.2f}s < {target_duration:.2f}s)")
        
        # Extract the random segment
        bg_segment = bg_source.subclip(random_start, random_end)
        fg_segment = fg_source.subclip(random_start, random_end)
        segment_duration = bg_segment.duration
        
        # Loop the segments to match target duration if needed
        if segment_duration < target_duration:
            # Calculate how many loops we need
            loops_needed = int(target_duration / segment_duration) + 1
            print(f"  🔄 Looping video segment {loops_needed} times to match audio duration ({target_duration:.2f}s)")
            
            # Loop the background segment
            bg_clips = [bg_segment] * loops_needed
            bg_looped = mp.concatenate_videoclips(bg_clips, method="compose")
            bg_looped = bg_looped.subclip(0, target_duration)  # Trim to exact duration
            
            # Loop the foreground segment
            fg_clips = [fg_segment] * loops_needed
            fg_looped = mp.concatenate_videoclips(fg_clips, method="compose")
            fg_looped = fg_looped.subclip(0, target_duration)  # Trim to exact duration
        else:
            # Segment is long enough, just trim to exact duration
            bg_looped = bg_segment.subclip(0, target_duration)
            fg_looped = fg_segment.subclip(0, target_duration)
        
        # Create scaled background layer (no blur)
        scale_factor = output_resolution[0] / bg_looped.w
        scale_factor = max(scale_factor, 1.15)
        
        bg_clip = bg_looped.resize(scale_factor)
        # Crop to exact resolution if needed
        if bg_clip.w > output_resolution[0] or bg_clip.h > output_resolution[1]:
            x_center = bg_clip.w / 2
            y_center = bg_clip.h / 2
            bg_clip = bg_clip.crop(
                x_center=x_center,
                y_center=y_center,
                width=output_resolution[0],
                height=output_resolution[1]
            )
        
        # Create foreground layer (original clip, centered)
        fg_clip = fg_looped.resize(height=output_resolution[1])
        fg_clip = fg_clip.set_position(('center', 'center'))
        
        # Ensure both clips have the exact same duration as target
        bg_clip = bg_clip.set_duration(target_duration)
        fg_clip = fg_clip.set_duration(target_duration)
        
        # Composite: background + foreground
        final_clip = mp.CompositeVideoClip(
            [bg_clip, fg_clip],
            size=output_resolution,
            duration=target_duration  # Explicitly set duration
        )
        
        # Final safety check: ensure duration matches exactly
        if abs(final_clip.duration - target_duration) > 0.1:
            print(f"  ⚠️  Duration mismatch: {final_clip.duration:.2f}s vs {target_duration:.2f}s, fixing...")
            final_clip = final_clip.set_duration(target_duration)
        
        print(f"  ✅ Background video ready: {final_clip.duration:.2f}s (matches audio: {target_duration:.2f}s)")
        return final_clip
        
    except Exception as e:
        print(f"  ❌ Error compiling background videos: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_word_timestamps(audio_path: Path, model_name: str = "base") -> Optional[List[Dict]]:
    """
    Extract word-level timestamps from audio using Whisper
    
    Returns:
        List of word dictionaries with 'word', 'start', 'end' keys
    """
    try:
        import whisper
        
        print(f"  🎤 Extracting word-level timestamps (model: {model_name})...")
        
        # Always use CPU (no GPU support)
        model = whisper.load_model(model_name, device="cpu")
        result = model.transcribe(
            str(audio_path),
            word_timestamps=True,
            fp16=False  # Disable fp16 for better compatibility
        )
        
        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info["word"].strip(),
                    "start": word_info["start"],
                    "end": word_info["end"]
                })
        
        print(f"  ✅ Extracted {len(words)} word timestamps")
        return words
        
    except Exception as e:
        print(f"  ❌ Error extracting word timestamps: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_ass_subtitles(script_text: str, word_timestamps: List[Dict], output_path: Path) -> bool:
    """
    Create ASS subtitle file showing one word at a time at bottom center
    """
    try:
        print(f"  📝 Creating ASS subtitles (one word at a time)...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write ASS header
            f.write("[Script Info]\n")
            f.write("Title: YouTube Video Subtitles\n")
            f.write("ScriptType: v4.00+\n\n")
            
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            # Style: white text, 24pt font, bold, with outline
            # Alignment values: 1=bottom-left, 2=bottom-center, 3=bottom-right
            # Alignment=2 means bottom center
            # MarginV=20 means 20 pixels from bottom edge (very bottom)
            f.write("Style: Word,Arial,24,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,10,10,20,1\n\n")
            
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            if not word_timestamps:
                print("  ⚠️  No word timestamps available")
                return False
            
            # Create one subtitle entry per word - no fade, same position
            # Use ASS alignment (Alignment=2) for bottom center positioning
            word_count = 0
            
            for i, word_info in enumerate(word_timestamps):
                word = word_info["word"].strip()
                if not word:
                    continue
                
                word_start = word_info["start"]
                # End time: either the word's end time, or the start of the next word (whichever comes first)
                # This ensures no overlap - one word disappears exactly when next appears
                if i + 1 < len(word_timestamps):
                    next_word_start = word_timestamps[i + 1]["start"]
                    word_end = min(word_info["end"], next_word_start)
                else:
                    word_end = word_info["end"]
                
                # Format timestamps - no overlap
                start_time = format_ass_timestamp(word_start)
                end_time = format_ass_timestamp(word_end)
                
                # Write single word subtitle - no fade, using style alignment
                # Alignment=2 in style means bottom center
                # No \pos override - let the style handle positioning
                f.write(f"Dialogue: 0,{start_time},{end_time},Word,,0,0,0,,{word}\n")
                word_count += 1
            
            print(f"  ✅ Created {word_count} word subtitle(s)")
        
        print(f"  ✅ ASS subtitle file created: {output_path.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error creating ASS subtitles: {e}")
        import traceback
        traceback.print_exc()
        return False


def format_ass_timestamp(seconds: float) -> str:
    """Format seconds to ASS timestamp format (H:MM:SS.cc)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def render_final_video(
    video_clip: object,
    audio_path: Path,
    subtitle_path: Path,
    output_path: Path,
    resolution: Tuple[int, int] = (1920, 1080)
) -> bool:
    """
    Combine background video, voiceover audio, and captions into final video
    OPTIMIZED: Single-pass FFmpeg rendering (saves 1-2 minutes)
    """
    try:
        import moviepy.editor as mp
        
        print(f"  🎬 Rendering final video (optimized single-pass)...")
        
        # Load audio to get duration
        audio_clip = mp.AudioFileClip(str(audio_path))
        audio_duration = audio_clip.duration
        audio_clip.close()  # Close immediately to free memory
        
        # Make sure video duration matches audio duration
        if abs(video_clip.duration - audio_duration) > 0.1:
            print(f"  ⚠️  Duration mismatch detected: video={video_clip.duration:.2f}s, audio={audio_duration:.2f}s")
            print(f"  🔧 Adjusting video duration to match audio...")
            video_clip = video_clip.set_duration(audio_duration)
        
        # Save video (without audio) to temp file for FFmpeg
        temp_video = output_path.parent / f".temp_{output_path.name}"
        print(f"  📹 Saving video clip (duration: {audio_duration:.2f}s)...")
        video_clip.write_videofile(
            str(temp_video),
            codec='libx264',
            audio=False,  # No audio - we'll add it with FFmpeg
            fps=24,
            preset='ultrafast',  # Fastest preset for speed
            threads=multiprocessing.cpu_count(),  # Use all CPU cores
            verbose=False,
            logger=None,
            write_logfile=False  # Disable logfile to avoid file conflicts
        )
        
        # Close video clip to free memory
        video_clip.close()
        
        # Single-pass FFmpeg: combine video + audio + subtitles in one pass
        print(f"  🚀 Combining video, audio, and subtitles (single-pass)...")
        # Escape the subtitle path for ffmpeg (handle spaces and special chars)
        subtitle_path_escaped = str(subtitle_path).replace("\\", "\\\\").replace(":", "\\:")
        
        cmd = [
            "ffmpeg",
            "-i", str(temp_video),  # Video input
            "-i", str(audio_path),   # Audio input
            "-vf", f"subtitles={subtitle_path_escaped}:force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20,Bold=1'",
            "-c:v", "libx264",
            "-preset", "ultrafast",  # Fastest encoding preset
            "-crf", "23",  # Quality setting (18-28 range, 23 is good quality, higher = faster)
            "-tune", "fastdecode",  # Optimize for fast decoding
            "-profile:v", "high",  # High profile for better quality
            "-level", "4.0",  # H.264 level for compatibility
            "-pix_fmt", "yuv420p",  # Ensure compatibility
            "-c:a", "aac",
            "-b:a", "192k",  # High quality audio bitrate (192k is standard for good quality)
            "-ar", "48000",  # High quality audio sample rate
            "-threads", str(multiprocessing.cpu_count()),  # Use all CPU cores
            "-shortest",  # Ensure output duration matches shortest input (video or audio)
            "-y",
            str(output_path)
        ]
        
        # Run ffmpeg (single attempt, no retries)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,  # Prevent stdin issues
            stderr=subprocess.PIPE,    # Capture stderr separately
            stdout=subprocess.PIPE     # Capture stdout separately
        )
        
        # Cleanup temp file
        if temp_video.exists():
            temp_video.unlink()
        
        if result.returncode == 0:
            print(f"  ✅ Final video rendered: {output_path.name}")
            return True
        else:
            error_output = result.stderr if result.stderr else result.stdout
            print(f"  ❌ FFmpeg error: {error_output}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error rendering final video: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate YouTube videos from text scripts with voiceover, background footage, and captions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python youtube_video_generator.py script.txt
  
  # Specify output file
  python youtube_video_generator.py script.txt -o my_video.mp4
  
  # Use different video folder
  python youtube_video_generator.py script.txt --video-folder ./videos/
  
  # Use different Whisper model for better accuracy
  python youtube_video_generator.py script.txt --whisper-model medium
        """
    )
    
    parser.add_argument(
        "script",
        type=Path,
        help="Text file containing the script"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output video file (default: script_name_video.mp4)"
    )
    
    parser.add_argument(
        "--video-folder",
        type=Path,
        default=Path("/Users/phill/Desktop/instagram_downloads"),
        help="Folder containing background videos (default: instagram_downloads)"
    )
    
    parser.add_argument(
        "--whisper-model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model for word timestamp extraction (default: base)"
    )
    
    parser.add_argument(
        "--voice",
        type=str,
        default=None,
        help="Edge-TTS voice to use (default: auto-select natural voice)"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Validate script file
    script_path = args.script
    if not script_path.exists():
        print(f"❌ Script file not found: {script_path}")
        sys.exit(1)
    
    # Read script
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_text = f.read().strip()
    except Exception as e:
        print(f"❌ Error reading script file: {e}")
        sys.exit(1)
    
    if not script_text:
        print(f"❌ Script file is empty")
        sys.exit(1)
    
    print(f"📄 Script loaded: {len(script_text)} characters")
    
    # Set output path
    if args.output:
        output_path = args.output
    else:
        output_path = script_path.parent / f"{script_path.stem}_video.mp4"
    
    # Create temp directory for intermediate files
    temp_dir = Path(tempfile.mkdtemp(prefix="youtube_gen_"))
    print(f"📁 Using temp directory: {temp_dir}")
    
    try:
        # Step 1: Generate voiceover
        print(f"\n{'='*60}")
        print("STEP 1: Generating Voiceover")
        print(f"{'='*60}")
        audio_path = temp_dir / "voiceover.mp3"
        success, duration = generate_voiceover(script_text, audio_path, args.voice)
        if not success:
            print("❌ Failed to generate voiceover")
            sys.exit(1)
        
        # Step 2: Compile background videos
        print(f"\n{'='*60}")
        print("STEP 2: Compiling Background Videos")
        print(f"{'='*60}")
        video_clip = compile_background_videos(args.video_folder, duration)
        if video_clip is None:
            print("❌ Failed to compile background videos")
            sys.exit(1)
        
        # Step 3: Generate word timestamps
        print(f"\n{'='*60}")
        print("STEP 3: Extracting Word Timestamps")
        print(f"{'='*60}")
        word_timestamps = generate_word_timestamps(audio_path, args.whisper_model)
        if word_timestamps is None:
            print("❌ Failed to extract word timestamps")
            sys.exit(1)
        
        # Step 4: Create ASS subtitles
        print(f"\n{'='*60}")
        print("STEP 4: Creating Subtitles")
        print(f"{'='*60}")
        subtitle_path = temp_dir / "subtitles.ass"
        if not create_ass_subtitles(script_text, word_timestamps, subtitle_path):
            print("❌ Failed to create subtitles")
            sys.exit(1)
        
        # Step 5: Render final video
        print(f"\n{'='*60}")
        print("STEP 5: Rendering Final Video")
        print(f"{'='*60}")
        if not render_final_video(video_clip, audio_path, subtitle_path, output_path):
            print("❌ Failed to render final video")
            sys.exit(1)
        
        print(f"\n{'='*60}")
        print("✅ SUCCESS!")
        print(f"{'='*60}")
        print(f"📹 Video created: {output_path}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
    finally:
        # Cleanup temp directory
        import shutil
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temp files")
        except:
            pass


if __name__ == "__main__":
    main()

