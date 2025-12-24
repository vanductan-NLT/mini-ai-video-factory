"""
File validation utilities for video uploads

Provides validation functions for file format, size, and duration.
"""

import os
import magic
import subprocess
import logging
import json
from typing import Tuple, Optional, Dict, Any
from werkzeug.datastructures import FileStorage

logger = logging.getLogger(__name__)

# Supported video formats and their MIME types
SUPPORTED_FORMATS = {
    'video/mp4': ['.mp4'],
    'video/x-msvideo': ['.avi'],
    'video/quicktime': ['.mov'],
    'video/mpeg': ['.mpeg', '.mpg'],
    'video/x-ms-wmv': ['.wmv']
}

# Flatten supported extensions
SUPPORTED_EXTENSIONS = []
for extensions in SUPPORTED_FORMATS.values():
    SUPPORTED_EXTENSIONS.extend(extensions)

class ValidationError(Exception):
    """Custom exception for file validation errors"""
    pass

def validate_file_format(file: FileStorage) -> bool:
    """
    Validate that the uploaded file is a supported video format
    
    Args:
        file: Uploaded file object
        
    Returns:
        bool: True if format is supported
        
    Raises:
        ValidationError: If format is not supported
    """
    if not file or not file.filename:
        raise ValidationError("No file provided")
    
    # Check file extension
    filename = file.filename.lower()
    file_ext = os.path.splitext(filename)[1]
    
    if file_ext not in SUPPORTED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file format: {file_ext}. "
            f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # Check MIME type using python-magic
    try:
        # Read first 2048 bytes to determine MIME type
        file.seek(0)
        file_header = file.read(2048)
        file.seek(0)  # Reset file pointer
        
        mime_type = magic.from_buffer(file_header, mime=True)
        
        if mime_type not in SUPPORTED_FORMATS:
            raise ValidationError(
                f"File content does not match expected video format. "
                f"Detected MIME type: {mime_type}"
            )
        
        logger.info(f"File format validation passed: {filename} ({mime_type})")
        return True
        
    except Exception as e:
        logger.error(f"Error validating file format for {filename}: {str(e)}")
        raise ValidationError(f"Unable to validate file format: {str(e)}")

def validate_file_size(file: FileStorage, max_size_bytes: int) -> bool:
    """
    Validate that the uploaded file size is within limits
    
    Args:
        file: Uploaded file object
        max_size_bytes: Maximum allowed file size in bytes
        
    Returns:
        bool: True if size is within limits
        
    Raises:
        ValidationError: If file is too large
    """
    if not file:
        raise ValidationError("No file provided")
    
    # Get file size by seeking to end
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > max_size_bytes:
        size_mb = file_size / (1024 * 1024)
        max_size_mb = max_size_bytes / (1024 * 1024)
        raise ValidationError(
            f"File too large: {size_mb:.1f}MB. Maximum allowed: {max_size_mb:.1f}MB"
        )
    
    logger.info(f"File size validation passed: {file.filename} ({file_size} bytes)")
    return True

def get_video_duration(file_path: str) -> float:
    """
    Get video duration using FFprobe
    
    Args:
        file_path: Path to video file
        
    Returns:
        float: Duration in seconds
        
    Raises:
        ValidationError: If unable to determine duration
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise ValidationError(f"FFprobe failed: {result.stderr}")
        
        probe_data = json.loads(result.stdout)
        
        duration = float(probe_data['format']['duration'])
        logger.info(f"Video duration determined: {file_path} ({duration} seconds)")
        return duration
        
    except subprocess.TimeoutExpired:
        raise ValidationError("Timeout while determining video duration")
    except json.JSONDecodeError:
        raise ValidationError("Invalid response from FFprobe")
    except KeyError:
        raise ValidationError("Unable to extract duration from video metadata")
    except Exception as e:
        logger.error(f"Error getting video duration for {file_path}: {str(e)}")
        raise ValidationError(f"Unable to determine video duration: {str(e)}")

def validate_video_duration(file_path: str, max_duration_seconds: int) -> bool:
    """
    Validate that video duration is within limits
    
    Args:
        file_path: Path to video file
        max_duration_seconds: Maximum allowed duration in seconds
        
    Returns:
        bool: True if duration is within limits
        
    Raises:
        ValidationError: If duration exceeds limit
    """
    duration = get_video_duration(file_path)
    
    if duration > max_duration_seconds:
        duration_minutes = duration / 60
        max_duration_minutes = max_duration_seconds / 60
        raise ValidationError(
            f"Video too long: {duration_minutes:.1f} minutes. "
            f"Maximum allowed: {max_duration_minutes:.1f} minutes"
        )
    
    logger.info(f"Video duration validation passed: {file_path} ({duration} seconds)")
    return True

def get_video_info(file_path: str) -> Dict[str, Any]:
    """
    Get comprehensive video information using FFprobe
    
    Args:
        file_path: Path to video file
        
    Returns:
        dict: Video information including duration, resolution, codec, etc.
        
    Raises:
        ValidationError: If unable to get video information
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise ValidationError(f"FFprobe failed: {result.stderr}")
        
        probe_data = json.loads(result.stdout)
        
        # Extract video stream information
        video_stream = None
        for stream in probe_data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise ValidationError("No video stream found in file")
        
        format_info = probe_data.get('format', {})
        
        info = {
            'duration': float(format_info.get('duration', 0)),
            'size': int(format_info.get('size', 0)),
            'format_name': format_info.get('format_name', ''),
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'codec': video_stream.get('codec_name', ''),
            'fps': eval(video_stream.get('r_frame_rate', '0/1')),  # Convert fraction to float
            'bitrate': int(format_info.get('bit_rate', 0))
        }
        
        logger.info(f"Video info extracted: {file_path} - {info}")
        return info
        
    except subprocess.TimeoutExpired:
        raise ValidationError("Timeout while getting video information")
    except json.JSONDecodeError:
        raise ValidationError("Invalid response from FFprobe")
    except Exception as e:
        logger.error(f"Error getting video info for {file_path}: {str(e)}")
        raise ValidationError(f"Unable to get video information: {str(e)}")

def validate_video_file(file: FileStorage, temp_path: str, max_size_bytes: int, max_duration_seconds: int) -> Dict[str, Any]:
    """
    Comprehensive validation of uploaded video file
    
    Args:
        file: Uploaded file object
        temp_path: Path where file is temporarily saved
        max_size_bytes: Maximum allowed file size
        max_duration_seconds: Maximum allowed duration
        
    Returns:
        dict: Video information if validation passes
        
    Raises:
        ValidationError: If any validation fails
    """
    # Reset file pointer to beginning for format validation
    file.seek(0)
    
    # Validate file format
    validate_file_format(file)
    
    # Validate file size
    validate_file_size(file, max_size_bytes)
    
    # Validate video duration and get info using the saved temp file
    validate_video_duration(temp_path, max_duration_seconds)
    video_info = get_video_info(temp_path)
    
    logger.info(f"Complete video validation passed: {file.filename}")
    return video_info