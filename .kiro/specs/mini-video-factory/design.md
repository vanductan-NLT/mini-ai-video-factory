# Design Document: Mini Video Factory

## Overview

Mini Video Factory is a self-hosted web application that provides automated video processing capabilities. The system accepts user-uploaded videos, automatically removes silent segments using auto-editor, generates subtitles using Whisper, and delivers processed videos with embedded subtitles. The application is designed as a monolithic web service packaged in Docker for easy deployment.

The architecture prioritizes simplicity and ease of deployment while providing a complete video processing pipeline. All components are integrated into a single Python Flask application that handles both web interface and video processing tasks.

## Architecture

```mermaid
graph TB
    subgraph "Docker Container"
        subgraph "Flask Application"
            WEB[Web Interface]
            API[REST API]
            AUTH[Authentication]
            PROC[Processing Engine]
        end
        
        subgraph "Processing Tools"
            AE[Auto-Editor]
            WH[Whisper]
            FF[FFmpeg]
        end
        
        subgraph "Local Storage"
            DATA[/data/ Volume]
            TEMP[Temporary Files]
        end
    end
    
    subgraph "External Services"
        WAS[Wasabi Storage]
        SUP[Supabase DB]
    end
    
    USER[User Browser] --> WEB
    WEB --> API
    API --> AUTH
    API --> PROC
    PROC --> AE
    PROC --> WH
    PROC --> FF
    PROC --> DATA
    API --> WAS
    AUTH --> SUP
    
    DATA -.-> HOST[Host /data Volume]
```

### Key Architectural Decisions

1. **Monolithic Design**: Single Flask application handles all functionality to minimize complexity
2. **Synchronous Processing**: Video processing runs synchronously with progress updates via WebSocket or polling
3. **Volume Mapping**: Critical data persisted through Docker volume mapping to host filesystem
4. **External Storage**: Wasabi S3-compatible storage for scalable file storage
5. **Database**: Supabase for user management and processing metadata

## Components and Interfaces

### Web Interface Component
- **Purpose**: Provides user-facing HTML interface for all operations
- **Technology**: Flask templates with vanilla JavaScript
- **Responsibilities**:
  - User authentication forms
  - Video upload interface with progress tracking
  - Processing status display
  - Video preview and download interface

### Authentication Component
- **Purpose**: Manages user login and session management
- **Technology**: Flask-Login with Supabase backend
- **Interface**:
  ```python
  class AuthManager:
      def authenticate_user(username: str, password: str) -> bool
      def create_session(user_id: str) -> str
      def validate_session(session_token: str) -> bool
      def logout_user(session_token: str) -> None
  ```

### Video Processing Component
- **Purpose**: Orchestrates the video processing pipeline
- **Technology**: Python with subprocess calls to external tools
- **Interface**:
  ```python
  class VideoProcessor:
      def process_video(input_path: str, user_id: str) -> ProcessingResult
      def get_processing_status(job_id: str) -> ProcessingStatus
      def cleanup_temp_files(job_id: str) -> None
  ```

### Storage Component
- **Purpose**: Manages file operations with Wasabi storage
- **Technology**: boto3 S3 client
- **Interface**:
  ```python
  class StorageManager:
      def upload_file(local_path: str, remote_key: str) -> str
      def download_file(remote_key: str, local_path: str) -> bool
      def delete_file(remote_key: str) -> bool
      def generate_download_url(remote_key: str) -> str
  ```

### Auto-Editor Integration
- **Purpose**: Removes silent segments from videos
- **Technology**: auto-editor CLI tool
- **Interface**: Command-line execution with progress monitoring

### Whisper Integration
- **Purpose**: Generates subtitles from audio
- **Technology**: OpenAI Whisper (self-hosted)
- **Interface**: Python API calls with local model

## Data Models

### User Model
```python
@dataclass
class User:
    id: str
    username: str
    password_hash: str
    created_at: datetime
    last_login: datetime
```

### Processing Job Model
```python
@dataclass
class ProcessingJob:
    id: str
    user_id: str
    original_filename: str
    status: ProcessingStatus  # UPLOADED, PROCESSING, COMPLETED, FAILED
    progress: int  # 0-100
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    input_file_path: str
    output_file_path: Optional[str]
```

### File Metadata Model
```python
@dataclass
class FileMetadata:
    id: str
    job_id: str
    filename: str
    file_size: int
    duration: float
    storage_key: str
    file_type: FileType  # ORIGINAL, PROCESSED
    created_at: datetime
```

### Processing Status Enum
```python
class ProcessingStatus(Enum):
    UPLOADED = "uploaded"
    AUTO_EDITING = "auto_editing"
    TRANSCRIBING = "transcribing"
    ADDING_SUBTITLES = "adding_subtitles"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Database Schema

### Supabase Tables

**users**
- id (uuid, primary key)
- username (text, unique)
- password_hash (text)
- created_at (timestamp)
- last_login (timestamp)

**processing_jobs**
- id (uuid, primary key)
- user_id (uuid, foreign key)
- original_filename (text)
- status (text)
- progress (integer)
- created_at (timestamp)
- completed_at (timestamp, nullable)
- error_message (text, nullable)
- input_storage_key (text)
- output_storage_key (text, nullable)

**file_metadata**
- id (uuid, primary key)
- job_id (uuid, foreign key)
- filename (text)
- file_size (bigint)
- duration (float)
- storage_key (text)
- file_type (text)
- created_at (timestamp)

## Processing Pipeline

### Video Processing Workflow

1. **Upload Phase**
   - User selects video file through web interface
   - File uploaded to temporary local storage
   - File validation (format, size, duration)
   - Upload to Wasabi storage
   - Create processing job record

2. **Auto-Editing Phase**
   - Download video from Wasabi to local temp directory
   - Execute auto-editor with silence removal
   - Monitor progress and update job status
   - Save edited video to temp storage

3. **Transcription Phase**
   - Extract audio from edited video
   - Run Whisper transcription
   - Generate SRT subtitle file
   - Update processing progress

4. **Subtitle Integration Phase**
   - Use FFmpeg to embed subtitles into video
   - Generate final MP4 output
   - Upload processed video to Wasabi
   - Update job status to completed

5. **Cleanup Phase**
   - Remove temporary local files
   - Keep processing metadata in database
   - Generate download URL for user

### Error Handling Strategy

- **Validation Errors**: Return immediate feedback to user
- **Processing Errors**: Log detailed error, update job status, notify user
- **Storage Errors**: Retry with exponential backoff, fallback to local storage
- **Tool Failures**: Capture stderr output, provide diagnostic information

## Environment Configuration

### Required Environment Variables

```bash
# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Storage Configuration
WASABI_ACCESS_KEY=your_wasabi_access_key
WASABI_SECRET_KEY=your_wasabi_secret_key
WASABI_BUCKET=your_bucket_name
WASABI_REGION=us-east-1

# Application Configuration
SECRET_KEY=your_flask_secret_key
MAX_FILE_SIZE=104857600  # 100MB in bytes
MAX_DURATION=600  # 10 minutes in seconds
UPLOAD_FOLDER=/app/data/uploads
TEMP_FOLDER=/app/data/temp
OUTPUT_FOLDER=/app/data/output

# Processing Configuration
WHISPER_MODEL=base  # base, small, medium, large
AUTO_EDITOR_ARGS=--no_open --margin 0.2
```

### Docker Volume Mapping

```yaml
volumes:
  - ./data:/app/data  # Persistent storage for uploads and outputs
  - ./logs:/app/logs  # Application logs
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Based on the prework analysis and property reflection to eliminate redundancy, the following properties must be validated through property-based testing:

### Authentication Properties

**Property 1: Valid credential authentication**
*For any* valid username and password combination, authentication should succeed and redirect the user to the main interface
**Validates: Requirements 1.2**

**Property 2: Invalid credential rejection**
*For any* invalid username or password combination, authentication should fail and display an error message while remaining on the login page
**Validates: Requirements 1.3**

**Property 3: Session persistence**
*For any* authenticated user session, the session should remain valid until explicit logout or timeout occurs
**Validates: Requirements 1.4**

### File Upload Properties

**Property 4: File format validation**
*For any* uploaded file, the system should accept supported formats (MP4, AVI, MOV) and reject unsupported formats with appropriate error messages
**Validates: Requirements 2.1**

**Property 5: Upload progress tracking**
*For any* video upload operation, the system should display accurate progress updates from 0% to 100% completion
**Validates: Requirements 2.2**

**Property 6: Upload completion workflow**
*For any* successfully uploaded video, the system should store the file in the data directory and automatically initiate processing
**Validates: Requirements 2.4**

### Video Processing Properties

**Property 7: Auto-editing execution**
*For any* uploaded video, the auto-editor should process the video and remove silent segments automatically
**Validates: Requirements 3.1**

**Property 8: Transcription generation**
*For any* auto-edited video, Whisper should generate subtitle files from the audio content
**Validates: Requirements 3.2**

**Property 9: Subtitle embedding**
*For any* transcribed video, the system should embed the generated subtitles into the final processed video
**Validates: Requirements 3.3**

**Property 10: Processing status updates**
*For any* video being processed, the system should display current processing status and progress updates to the user
**Validates: Requirements 3.4**

**Property 11: Processing error handling**
*For any* processing failure, the system should log the error details and display a descriptive error message to the user
**Validates: Requirements 3.5**

### Video Output Properties

**Property 12: Preview interface display**
*For any* completed video processing job, the system should display a preview interface for the processed video
**Validates: Requirements 4.1**

**Property 13: Video playback with subtitles**
*For any* processed video in preview mode, the video should play with embedded subtitles visible
**Validates: Requirements 4.2**

**Property 14: Download functionality**
*For any* processed video, the download operation should provide the video as an MP4 file with progress tracking
**Validates: Requirements 4.3, 4.4**

### Storage Properties

**Property 15: Cloud storage operations**
*For any* video file (original or processed), the system should store it in Wasabi cloud storage and retrieve it successfully
**Validates: Requirements 5.1, 5.2**

**Property 16: Temporary file cleanup**
*For any* completed processing job, the system should remove all temporary files from local storage
**Validates: Requirements 5.4**

### Deployment Properties

**Property 17: Container service initialization**
*For any* container startup, all required services (web server, processing tools) should initialize successfully
**Validates: Requirements 6.2**

**Property 18: Environment configuration**
*For any* set of provided environment variables, the system should configure storage credentials and application settings correctly
**Validates: Requirements 6.3**

**Property 19: Data persistence**
*For any* data written during container operation, the data should persist through container restarts via volume mapping
**Validates: Requirements 6.5**

### User Management Properties

**Property 20: Multi-user support**
*For any* number of user accounts, the system should support unique credentials and independent access for each user
**Validates: Requirements 7.1, 7.3**

**Property 21: Credential security**
*For any* user account creation, the system should store password credentials securely using proper hashing
**Validates: Requirements 7.2**

**Property 22: Access control**
*For any* user data or processing results, the system should prevent unauthorized access from other users
**Validates: Requirements 7.4**

### User Interface Properties

**Property 23: Interface completeness**
*For any* interface load, the system should display all necessary controls (login, upload, progress, preview, download)
**Validates: Requirements 8.2**

**Property 24: User interaction feedback**
*For any* user interaction, the system should provide immediate visual feedback and appropriate error messages when errors occur
**Validates: Requirements 8.3, 8.5**

## Error Handling

### Error Categories and Responses

**File Upload Errors**
- Invalid file format: Return HTTP 400 with format requirements
- File too large: Return HTTP 413 with size limits
- Duration too long: Return HTTP 400 with duration limits
- Storage failure: Return HTTP 500 with retry instructions

**Processing Errors**
- Auto-editor failure: Log stderr output, update job status to failed
- Whisper transcription failure: Log error details, provide fallback options
- FFmpeg subtitle embedding failure: Log command output, retry with different parameters
- Storage upload failure: Retry with exponential backoff, fallback to local storage

**Authentication Errors**
- Invalid credentials: Return HTTP 401 with generic error message
- Session expired: Return HTTP 401 with redirect to login
- Database connection failure: Return HTTP 503 with maintenance message

**System Errors**
- Disk space full: Return HTTP 507 with cleanup instructions
- Memory exhaustion: Return HTTP 503 with resource limit message
- External service unavailable: Return HTTP 503 with retry timing

### Error Recovery Strategies

1. **Automatic Retry**: Network operations, storage uploads, external API calls
2. **Graceful Degradation**: Continue processing without non-essential features
3. **User Notification**: Clear error messages with actionable next steps
4. **Logging**: Comprehensive error logging for debugging and monitoring

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
- Test specific file format validations
- Test authentication with known credentials
- Test processing pipeline with sample videos
- Test error conditions with invalid inputs

**Property Tests**: Verify universal properties across all inputs
- Test authentication behavior across all credential combinations
- Test file processing across all supported video formats
- Test storage operations across all file types and sizes
- Test user isolation across all user account combinations

### Property-Based Testing Configuration

**Testing Framework**: Use Hypothesis for Python property-based testing
- Minimum 100 iterations per property test
- Each property test references its design document property
- Tag format: **Feature: mini-video-factory, Property {number}: {property_text}**

**Test Data Generation**:
- Generate random video files with varying formats, sizes, and durations
- Generate random user credentials and session tokens
- Generate random file paths and storage keys
- Generate random processing job states and error conditions

**Integration Testing**:
- Test complete video processing pipeline end-to-end
- Test Docker container deployment and configuration
- Test storage integration with Wasabi S3
- Test database integration with Supabase

### Test Environment Requirements

**Dependencies**:
- Docker for containerized testing
- Test video files of various formats and durations
- Mock Wasabi S3 service for storage testing
- Test Supabase instance for database testing

**Performance Testing**:
- Test processing performance with various video sizes
- Test concurrent user handling
- Test storage bandwidth limitations
- Test memory usage during processing