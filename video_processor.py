"""
Video Processor Module
Wraps the existing youtube_video_generator.py as a module for use in the worker
"""

import sys
from pathlib import Path
from typing import Tuple, Optional
import tempfile
import shutil

# Add parent directory to path to import youtube_video_generator
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions from existing video generator
from youtube_video_generator import (
    generate_voiceover,
    compile_background_videos,
    generate_word_timestamps,
    create_ass_subtitles,
    render_final_video,
    check_dependencies
)


class VideoProcessor:
    """Process videos using the existing youtube_video_generator functions"""
    
    def __init__(self, video_folder: Path, whisper_model: str = "base", voice: Optional[str] = None):
        """
        Initialize video processor
        
        Args:
            video_folder: Path to folder containing background videos
            whisper_model: Whisper model to use (tiny, base, small, medium, large)
            voice: Edge-TTS voice to use (None = auto-select)
        """
        if not check_dependencies():
            raise RuntimeError("Required dependencies not installed")
        
        self.video_folder = video_folder
        self.whisper_model = whisper_model
        self.voice = voice
        self.temp_dir = None
        self.voiceover_path = None
    
    def generate_voiceover_only(self, script_text: str, output_path: Path) -> Tuple[bool, Optional[float]]:
        """
        Generate only the voiceover (MP3) from script text
        
        Args:
            script_text: The video script text
            output_path: Where to save the voiceover MP3 file
        
        Returns:
            (success: bool, duration: float or None)
        """
        # Create temp directory for intermediate files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="youtube_automation_"))
        self.voiceover_path = None
        
        try:
            # Generate voiceover
            success, duration = generate_voiceover(script_text, output_path, self.voice)
            if not success:
                return False, None
            
            # Store voiceover path for later access
            self.voiceover_path = output_path
            
            return True, duration
            
        except Exception as e:
            print(f"❌ Error generating voiceover: {e}")
            import traceback
            traceback.print_exc()
            return False, None
        # Note: Don't cleanup temp_dir here - let the caller handle it
    
    def process_video(self, script_text: str, output_path: Path, voiceover_path: Optional[Path] = None) -> Tuple[bool, Optional[float]]:
        """
        Process a complete video from script text (OPTIMIZED with parallelization)
        
        Args:
            script_text: The video script text
            output_path: Where to save the final video
            voiceover_path: Optional path to existing voiceover file (if None, will generate)
        
        Returns:
            (success: bool, duration: float or None)
        """
        from concurrent.futures import ThreadPoolExecutor
        
        # Create temp directory for intermediate files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="youtube_automation_"))
        self.voiceover_path = None
        
        try:
            # Step 1: Use existing voiceover or generate new one
            if voiceover_path and voiceover_path.exists():
                # Use existing voiceover file
                import shutil
                audio_path = self.temp_dir / "voiceover.mp3"
                shutil.copy2(voiceover_path, audio_path)
                # Get duration from existing file
                import moviepy.editor as mp
                audio_clip = mp.AudioFileClip(str(audio_path))
                duration = audio_clip.duration
                audio_clip.close()
                self.voiceover_path = audio_path
            else:
                # Generate voiceover
                audio_path = self.temp_dir / "voiceover.mp3"
                success, duration = generate_voiceover(script_text, audio_path, self.voice)
                if not success:
                    return False, None
                
                # Store voiceover path for later access
                self.voiceover_path = audio_path
            
            print(f"  ⚡ Starting parallel processing (background video + timestamps)...")
            
            # Steps 2 & 3: Run in parallel (both only need audio_path and duration)
            video_clip = None
            word_timestamps = None
            errors = []
            
            def compile_videos():
                """Compile background videos"""
                try:
                    return compile_background_videos(self.video_folder, duration)
                except Exception as e:
                    errors.append(f"Background video compilation: {e}")
                    import traceback
                    traceback.print_exc()
                    return None
            
            def extract_timestamps():
                """Extract word timestamps"""
                try:
                    return generate_word_timestamps(audio_path, self.whisper_model)
                except Exception as e:
                    errors.append(f"Timestamp extraction: {e}")
                    import traceback
                    traceback.print_exc()
                    return None
            
            # Use ThreadPoolExecutor with increased workers (10) for better parallelization
            # Note: ProcessPoolExecutor requires picklable functions, but nested functions aren't picklable
            # ThreadPoolExecutor works fine for I/O-bound and some CPU-bound tasks with GIL release
            from concurrent.futures import ThreadPoolExecutor
            import multiprocessing
            
            # Use 10 workers (or CPU count, whichever is less) for better parallelization
            max_workers = min(10, multiprocessing.cpu_count())
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_video = executor.submit(compile_videos)
                future_timestamps = executor.submit(extract_timestamps)
                
                # Wait for both to complete
                video_clip = future_video.result()
                word_timestamps = future_timestamps.result()
            
            # Check for errors
            if errors:
                print(f"  ❌ Errors during parallel processing:")
                for error in errors:
                    print(f"     - {error}")
                return False, None
            
            if video_clip is None:
                print(f"  ❌ Background video compilation failed")
                return False, None
            
            if word_timestamps is None:
                print(f"  ❌ Word timestamp extraction failed")
                return False, None
            
            print(f"  ✅ Parallel processing complete!")
            
            # Step 4: Create ASS subtitles (fast, sequential)
            subtitle_path = self.temp_dir / "subtitles.ass"
            if not create_ass_subtitles(script_text, word_timestamps, subtitle_path):
                return False, None
            
            # Step 5: Render final video (optimized single-pass)
            if not render_final_video(video_clip, audio_path, subtitle_path, output_path):
                return False, None
            
            return True, duration
            
        except Exception as e:
            print(f"❌ Error processing video: {e}")
            import traceback
            traceback.print_exc()
            return False, None
        
        finally:
            # Cleanup temp directory
            if self.temp_dir and self.temp_dir.exists():
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
    
    def get_voiceover_path(self) -> Optional[Path]:
        """Get the path to the generated voiceover file (if available)"""
        if self.voiceover_path and self.voiceover_path.exists():
            return self.voiceover_path
        return None
    
    def cleanup(self):
        """Manually cleanup temp files"""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass

