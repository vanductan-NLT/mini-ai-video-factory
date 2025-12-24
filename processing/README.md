# Video Processing Module

This module handles the complete video processing pipeline for Mini Video Factory.

## Overview

The video processing pipeline consists of the following steps:

1. **Auto-editing**: Remove silent segments using auto-editor
2. **Audio extraction**: Extract audio from the edited video using FFmpeg
3. **Transcription**: Generate subtitles using OpenAI Whisper
4. **Subtitle embedding**: Embed subtitles into the final video using FFmpeg

## Components

### VideoProcessor

The main class that orchestrates the entire processing pipeline.

**Key Methods:**
- `process_video(job, progress_callback)`: Process a complete video through the pipeline
- `get_processing_status(job_id)`: Get current processing status
- `cleanup_temp_files(job_id)`: Clean up temporary files

### Dependencies

**Required Tools:**
- `auto-editor`: For removing silent segments
- `ffmpeg`: For audio extraction and subtitle embedding
- `whisper`: For audio transcription

**Python Packages:**
- `openai-whisper`: OpenAI's Whisper model
- `auto-editor`: Automatic video editing tool

## Configuration

The processor can be configured via environment variables:

- `WHISPER_MODEL`: Whisper model to use (default: 'base')
- `AUTO_EDITOR_ARGS`: Additional arguments for auto-editor (default: '--no_open --margin 0.2')
- `TEMP_FOLDER`: Temporary processing directory (default: './data/temp')
- `OUTPUT_FOLDER`: Output directory (default: './data/output')

## Usage

```python
from processing.video_processor import VideoProcessor
from models.processing_job import ProcessingJob

# Initialize processor
processor = VideoProcessor(storage_manager)

# Create a processing job
job = ProcessingJob.create_new(user_id, filename)

# Process video with progress callback
def progress_callback(message, progress):
    print(f"Progress: {message} ({progress}%)")

success = processor.process_video(job, progress_callback)
```

## Error Handling

The processor includes comprehensive error handling for:

- Missing tools (auto-editor, ffmpeg)
- File I/O errors
- Processing failures
- Storage errors

All errors are logged and propagated as `VideoProcessingError` exceptions.

## Temporary Files

The processor creates temporary directories for each job and automatically cleans them up after processing. Temporary files include:

- Downloaded input video
- Auto-edited video
- Extracted audio
- Generated subtitle files
- Final processed video (before upload)

## Performance Considerations

- Processing is CPU-intensive and may take several minutes for longer videos
- Whisper model loading is done on-demand and cached
- Temporary files are stored locally during processing
- Final output is uploaded to cloud storage or saved locally