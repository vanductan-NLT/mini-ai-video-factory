"""
Video Processing Pipeline for Mini Video Factory

This module handles the complete video processing workflow:
1. Auto-editing to remove silent segments (placeholder)
2. Audio transcription using Whisper (placeholder)
3. Subtitle embedding using FFmpeg (placeholder)
"""

import os
import subprocess
import tempfile
import shutil
import logging
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import json

# Import whisper and auto-editor only if available
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

from models.processing_job import ProcessingJob, ProcessingStatus, save_processing_job
from storage.storage_manager import StorageManager

logger = logging.getLogger(__name__)

class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""
    pass

class VideoProcessor:
    """Main video processing class that orchestrates the entire pipeline"""
    
    def __init__(self, storage_manager: Optional[StorageManager] = None):
        self.storage_manager = storage_manager
        self.whisper_model = None
        self.temp_dir = None
        
        # Configuration from environment
        self.whisper_model_name = os.environ.get('WHISPER_MODEL', 'base')
        self.auto_editor_args = os.environ.get('AUTO_EDITOR_ARGS', '--no_open --margin 0.2').split()
        self.temp_folder = os.environ.get('TEMP_FOLDER', './data/temp')
        self.output_folder = os.environ.get('OUTPUT_FOLDER', './data/output')
        
        # Ensure directories exist
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        logger.info(f"VideoProcessor initialized with Whisper model: {self.whisper_model_name}")
    
    def _load_whisper_model(self):
        """Load Whisper model on demand"""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available - using placeholder mode")
            return
            
        if self.whisper_model is None:
            try:
                logger.info(f"Loading Whisper model: {self.whisper_model_name}")
                self.whisper_model = whisper.load_model(self.whisper_model_name)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise VideoProcessingError(f"Failed to load Whisper model: {e}")
    
    def _create_temp_directory(self, job_id: str) -> str:
        """Create a temporary directory for processing this job"""
        temp_dir = os.path.join(self.temp_folder, f"job_{job_id}")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def _cleanup_temp_directory(self, temp_dir: str):
        """Clean up temporary directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
    
    def _download_input_file(self, job: ProcessingJob, temp_dir: str) -> str:
        """Download input file to temporary directory"""
        local_path = os.path.join(temp_dir, f"input_{job.original_filename}")
        
        # Check if file already exists (for retry)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            logger.info(f"Input file already exists, skipping download: {local_path}")
            return local_path

        if job.input_storage_key and self.storage_manager:
            # Download from Wasabi storage
            if self.storage_manager.download_file(job.input_storage_key, local_path):
                logger.info(f"Downloaded input file from storage: {job.input_storage_key}")
                return local_path
            else:
                raise VideoProcessingError(f"Failed to download file from storage: {job.input_storage_key}")
        
        elif job.input_file_path and os.path.exists(job.input_file_path):
            # Copy from local storage
            shutil.copy2(job.input_file_path, local_path)
            logger.info(f"Copied input file from local storage: {job.input_file_path}")
            return local_path
        
        else:
            raise VideoProcessingError("No valid input file path found")
    
    def _run_auto_editor(self, input_path: str, output_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """Run auto-editor to remove silent segments - placeholder mode"""
        try:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Edited video already exists, skipping auto-editor: {output_path}")
                return True

            logger.info(f"Auto-editor placeholder: {input_path} -> {output_path}")
            
            # Placeholder: just copy the file
            shutil.copy2(input_path, output_path)
            logger.info("Auto-editor placeholder completed - file copied")
            return True
            
        except Exception as e:
            logger.error(f"Auto-editor placeholder failed: {e}")
            return False
                
        except FileNotFoundError:
            raise VideoProcessingError("auto-editor command not found. Please ensure it's installed with: pip install auto-editor")
        except Exception as e:
            logger.error(f"Auto-editor error: {e}")
            raise VideoProcessingError(f"Auto-editor failed: {e}")
    
    def _extract_audio(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video for transcription"""
        try:
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                logger.info(f"Audio file already exists, skipping extraction: {audio_path}")
                return True

            logger.info(f"Extracting audio: {video_path} -> {audio_path}")
            
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM audio for Whisper
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Audio extraction completed successfully")
                return True
            else:
                logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
                raise VideoProcessingError(f"Audio extraction failed: {result.stderr}")
                
        except FileNotFoundError:
            raise VideoProcessingError("ffmpeg command not found. Please ensure it's installed. On Ubuntu: sudo apt install ffmpeg")
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            raise VideoProcessingError(f"Audio extraction failed: {e}")
    
    def _transcribe_audio(self, audio_path: str, srt_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """Transcribe audio using Whisper and generate SRT file - placeholder mode"""
        try:
            if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
                 logger.info(f"Subtitle file already exists, skipping transcription: {srt_path}")
                 # Ensure we can read it though? Assuming yes.
                 return True

            logger.info(f"Transcription placeholder: {audio_path} -> {srt_path}")
            
            if not WHISPER_AVAILABLE:
                # Create placeholder subtitle
                srt_content = """1
00:00:00,000 --> 00:00:05,000
Video processing completed (placeholder mode)

2
00:00:05,000 --> 00:00:10,000
Whisper transcription will be enabled in production

"""
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write(srt_content)
                
                logger.info("Placeholder transcription completed")
                return True
            
            # Load Whisper model if available
            self._load_whisper_model()
            
            # Transcribe audio
            if progress_callback:
                progress_callback("Transcribing audio...")
            
            result = self.whisper_model.transcribe(audio_path)
            
            # Generate SRT content
            srt_content = self._generate_srt(result)
            
            # Write SRT file
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info("Transcription completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Fallback to placeholder
            srt_content = """1
00:00:00,000 --> 00:00:05,000
Transcription failed - placeholder mode

"""
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            return True
    
    def _generate_srt(self, transcription_result: Dict[str, Any]) -> str:
        """Generate SRT subtitle format from Whisper transcription result"""
        srt_content = []
        
        for i, segment in enumerate(transcription_result['segments'], 1):
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between subtitles
        
        return "\n".join(srt_content)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp for SRT format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _embed_subtitles(self, video_path: str, srt_path: str, output_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """Embed subtitles into video using FFmpeg"""
        try:
            logger.info(f"Embedding subtitles: {video_path} + {srt_path} -> {output_path}")
            
            if progress_callback:
                progress_callback("Embedding subtitles...")
            
            # Ensure paths use forward slashes for FFmpeg compatibility
            video_path_norm = video_path.replace('\\', '/')
            srt_path_norm = srt_path.replace('\\', '/')
            output_path_norm = output_path.replace('\\', '/')
            
            # Verify SRT file exists
            if not os.path.exists(srt_path):
                raise VideoProcessingError(f"Subtitle file not found: {srt_path}")
            
            cmd = [
                'ffmpeg', '-i', video_path_norm,
                '-vf', f"subtitles={srt_path_norm}",
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-y',  # Overwrite output
                output_path_norm
            ]
            
            logger.info(f"FFmpeg subtitle command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Subtitle embedding completed successfully")
                return True
            else:
                logger.error(f"FFmpeg subtitle embedding failed: {result.stderr}")
                raise VideoProcessingError(f"Subtitle embedding failed: {result.stderr}")
                
        except FileNotFoundError:
            raise VideoProcessingError("ffmpeg command not found. Please ensure it's installed. On Ubuntu: sudo apt install ffmpeg")
        except subprocess.TimeoutExpired:
            raise VideoProcessingError("FFmpeg subtitle embedding timed out")
        except Exception as e:
            logger.error(f"Subtitle embedding error: {e}")
            raise VideoProcessingError(f"Subtitle embedding failed: {e}")
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video file information using FFprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # Extract relevant information
                format_info = info.get('format', {})
                video_stream = None
                
                # Find video stream
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break
                
                video_info = {
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0)),
                    'format': format_info.get('format_name', '').split(',')[0],
                    'bitrate': int(format_info.get('bit_rate', 0))
                }
                
                if video_stream:
                    video_info.update({
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                        'codec': video_stream.get('codec_name', '')
                    })
                
                return video_info
            else:
                logger.warning(f"FFprobe failed for {video_path}: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.warning(f"Failed to get video info for {video_path}: {e}")
            return {}
    
    def _upload_output_file(self, job: ProcessingJob, local_output_path: str) -> str:
        """Upload processed video to storage"""
        if self.storage_manager and self.storage_manager.is_available:
            # Upload to Wasabi storage
            storage_key = f"outputs/{job.user_id}/{job.id}_processed_{job.original_filename}"
            
            if self.storage_manager.upload_file(local_output_path, storage_key):
                logger.info(f"Uploaded output file to storage: {storage_key}")
                return storage_key
            else:
                logger.warning("Failed to upload to Wasabi, using local storage")
        
        # Fallback to local storage
        output_filename = f"{job.id}_processed_{job.original_filename}"
        final_output_path = os.path.join(self.output_folder, output_filename)
        shutil.copy2(local_output_path, final_output_path)
        logger.info(f"Saved output file locally: {final_output_path}")
        return final_output_path
    
    def process_video(self, job: ProcessingJob, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        Process a video through the complete pipeline:
        1. Auto-edit silent parts
        2. Transcribe audio
        3. Analyze transcript for scenes (LLM)
        4. Generate Remotion video with effects
        5. Upload result
        """
        temp_dir = None
        
        try:
            logger.info(f"Starting video processing for job {job.id}")
            
            # Create temporary directory
            temp_dir = self._create_temp_directory(job.id)
            
            # Update progress callback wrapper
            def update_progress(message: str, progress: int = None):
                if progress is not None:
                    job.progress = progress
                if progress_callback:
                    progress_callback(message, job.progress)
                save_processing_job(job)
            
            # Step 1: Download input file
            update_progress("Downloading input file...", 10)
            input_path = self._download_input_file(job, temp_dir)
            
            # Step 2: Auto-edit video (remove silent segments)
            job.update_status(ProcessingStatus.AUTO_EDITING, progress=20)
            update_progress("Removing silent segments...", 20)
            
            edited_path = os.path.join(temp_dir, f"edited_{job.original_filename}")
            self._run_auto_editor(input_path, edited_path, lambda msg: update_progress("Auto-editing...", None))
            
            # Step 3: Extract audio for transcription
            job.update_status(ProcessingStatus.TRANSCRIBING, progress=50)
            update_progress("Extracting audio...", 50)
            
            audio_path = os.path.join(temp_dir, "audio.wav")
            self._extract_audio(edited_path, audio_path)
            
            # Step 4: Transcribe audio
            update_progress("Transcribing audio...", 50)
            srt_path = os.path.join(temp_dir, "subtitles.srt")
            self._transcribe_audio(audio_path, srt_path, lambda msg: update_progress(msg, None))
            
            # Retrieve transcript text
            # Since _transcribe_audio doesn't return the text directly in the current implementation,
            # we can read the SRT/text (or ideally, refactor to get the text directly).
            # For now, let's assume we read from the SRT or re-transcribe.
            # To respect existing flow, we'll read the parsed SRT content or assume a simple mapping.
            # Ideally, we should modify _transcribe_audio to return the text.
            # Let's read the SRT file and extract text lines for now.
            transcript_text = ""
            if os.path.exists(srt_path):
                 with open(srt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Very naive SRT text extraction
                        if "-->" not in line and line.strip() and not line.strip().isdigit():
                            transcript_text += line.strip() + " "
            
            # Step 5: Analyze Content & Generate Remotion
            job.update_status(ProcessingStatus.ADDING_SUBTITLES, progress=60) # Keeping similar enum status for compatibility
            update_progress("Analyzing content with AI...", 60)
            
            # Dynamic imports
            from processing.transcript_analyzer import TranscriptAnalyzer
            from processing.remotion_generator import RemotionGenerator
            
            analyzer = TranscriptAnalyzer()
            remotion_gen = RemotionGenerator(remotion_dir=os.path.abspath("./remotion-video"))
            
            scenes = analyzer.analyze(transcript_text)
            update_progress(f"Generating video scenes...", 70)
            
            remotion_gen.generate_composition(scenes, video_path=edited_path)
            
            # Step 6: Render Final Video with Remotion
            update_progress("Rendering pro video with Remotion...", 80)
            final_output_filename = f"final_{job.id}.mp4"
            final_output_path = remotion_gen.render_video("GeneratedVideo", final_output_filename) # Will be in remotion-video/out/
            
            # Step 7: Collect processed video metadata
            update_progress("Collecting video metadata...", 90)
            processed_video_info = self._get_video_info(final_output_path)
            if processed_video_info:
                job.set_processed_video_info(processed_video_info)
            
            # Step 8: Upload output file
            update_progress("Uploading processed video...", 95)
            output_location = self._upload_output_file(job, final_output_path)
            
            # Update job with output information
            if output_location.startswith('/') or output_location.startswith('.'):
                job.output_file_path = output_location
                job.output_storage_key = None
            else:
                job.output_file_path = None
                job.output_storage_key = output_location
            
            # Mark as completed
            job.update_status(ProcessingStatus.COMPLETED, progress=100)
            update_progress("Processing completed!", 100)
            
            # Cleanup temp directory ONLY on success
            self._cleanup_temp_directory(temp_dir)
            
            logger.info(f"Video processing completed successfully for job {job.id}")
            return True
            
        except VideoProcessingError as e:
            logger.error(f"Video processing failed for job {job.id}: {e}")
            job.update_status(ProcessingStatus.FAILED, error_message=str(e))
            if progress_callback:
                progress_callback(f"Processing failed: {e}", job.progress)
            save_processing_job(job)
            # NOT cleaning up temp dir to allow retry
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error processing job {job.id}: {e}")
            job.update_status(ProcessingStatus.FAILED, error_message=f"Unexpected error: {e}")
            if progress_callback:
                progress_callback(f"Processing failed: {e}", job.progress)
            save_processing_job(job)
            # NOT cleaning up temp dir to allow retry
            return False
            
        # finally block removed to preserve files on error
    
    def get_processing_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current processing status for a job"""
        from models.processing_job import get_processing_job
        
        job = get_processing_job(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.id,
            'status': job.status.value,
            'status_display': job.get_status_display(),
            'progress': job.progress,
            'error_message': job.error_message,
            'completed': job.is_completed()
        }
    
    def cleanup_temp_files(self, job_id: str):
        """Clean up temporary files for a specific job"""
        temp_dir = os.path.join(self.temp_folder, f"job_{job_id}")
        self._cleanup_temp_directory(temp_dir)