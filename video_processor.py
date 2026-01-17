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
    
    def process_video(self, script_text: str, output_path: Path) -> Tuple[bool, Optional[float]]:
        """
        Process a complete video from script text
        
        Args:
            script_text: The video script text
            output_path: Where to save the final video
        
        Returns:
            (success: bool, duration: float or None)
        """
        # Create temp directory for intermediate files
        self.temp_dir = Path(tempfile.mkdtemp(prefix="youtube_automation_"))
        self.voiceover_path = None
        
        try:
            # Step 1: Generate voiceover
            audio_path = self.temp_dir / "voiceover.mp3"
            success, duration = generate_voiceover(script_text, audio_path, self.voice)
            if not success:
                return False, None
            
            # Store voiceover path for later access
            self.voiceover_path = audio_path
            
            # Step 2: Compile background videos
            video_clip = compile_background_videos(self.video_folder, duration)
            if video_clip is None:
                return False, None
            
            # Step 3: Generate word timestamps
            word_timestamps = generate_word_timestamps(audio_path, self.whisper_model)
            if word_timestamps is None:
                return False, None
            
            # Step 4: Create ASS subtitles
            subtitle_path = self.temp_dir / "subtitles.ass"
            if not create_ass_subtitles(script_text, word_timestamps, subtitle_path):
                return False, None
            
            # Step 5: Render final video
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

