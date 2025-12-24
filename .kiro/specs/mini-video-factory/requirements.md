# Requirements Document

## Introduction

Mini Video Factory is a self-hosted web application that automatically processes user-uploaded videos by removing silent segments and adding subtitles. The system provides a complete workflow from video upload to processed video download, packaged as a Docker container for easy deployment.

## Glossary

- **System**: The Mini Video Factory web application
- **User**: End user who uploads and processes videos
- **Admin**: Developer who deploys and manages the system
- **Auto_Editor**: Tool for automatically removing silent segments from videos
- **Whisper**: OpenAI's speech-to-text model for generating subtitles
- **Processed_Video**: Video that has been auto-edited and has subtitles added
- **Upload_Session**: A single video processing workflow from upload to download

## Requirements

### Requirement 1: User Authentication

**User Story:** As a user, I want to log in with provided credentials, so that I can access the video processing service.

#### Acceptance Criteria

1. WHEN a user visits the application THEN the System SHALL display a login interface
2. WHEN a user enters valid credentials THEN the System SHALL authenticate them and redirect to the main interface
3. WHEN a user enters invalid credentials THEN the System SHALL display an error message and remain on the login page
4. WHILE a user is authenticated THEN the System SHALL maintain their session until logout or timeout

### Requirement 2: Video Upload

**User Story:** As a user, I want to upload videos of 3-5 minutes duration, so that I can process them with auto-editing and subtitles.

#### Acceptance Criteria

1. WHEN a user selects a video file THEN the System SHALL validate the file format is supported (MP4, AVI, MOV)
2. WHEN a user uploads a video THEN the System SHALL display a progress bar showing upload status
3. IF a video exceeds 10 minutes duration THEN the System SHALL reject the upload and display an error message
4. WHEN upload completes successfully THEN the System SHALL store the video in the data directory and initiate processing

### Requirement 3: Video Processing

**User Story:** As a user, I want my uploaded video to be automatically edited and have subtitles added, so that I get an improved final product.

#### Acceptance Criteria

1. WHEN a video is uploaded THEN the Auto_Editor SHALL remove silent segments and pauses automatically
2. WHEN auto-editing completes THEN the Whisper SHALL transcribe the audio and generate subtitle files
3. WHEN transcription completes THEN the System SHALL embed subtitles into the processed video
4. WHILE processing occurs THEN the System SHALL display processing status and progress to the user
5. WHEN processing fails THEN the System SHALL log the error and notify the user with a descriptive message

### Requirement 4: Video Preview and Download

**User Story:** As a user, I want to preview the processed video and download it, so that I can verify the results and obtain the final product.

#### Acceptance Criteria

1. WHEN video processing completes THEN the System SHALL display a preview interface for the processed video
2. WHEN a user clicks the preview THEN the System SHALL play the processed video with embedded subtitles
3. WHEN a user clicks download THEN the System SHALL provide the processed video as an MP4 file
4. WHEN download initiates THEN the System SHALL track download progress and completion

### Requirement 5: Storage Management

**User Story:** As an admin, I want the system to manage video storage efficiently, so that storage costs remain minimal and the system performs well.

#### Acceptance Criteria

1. WHEN videos are uploaded THEN the System SHALL store them in Wasabi cloud storage
2. WHEN processing completes THEN the System SHALL store processed videos in the same storage location
3. WHEN storage operations occur THEN the System SHALL use the free tier limits efficiently
4. THE System SHALL clean up temporary files after processing completion

### Requirement 6: System Deployment

**User Story:** As an admin, I want to deploy the system as a Docker container, so that I can easily host it on any VPS with consistent behavior.

#### Acceptance Criteria

1. THE System SHALL be packaged as a Docker container with all dependencies included
2. WHEN the container starts THEN the System SHALL initialize all required services (web server, processing tools)
3. WHEN environment variables are provided THEN the System SHALL configure storage credentials and other settings
4. THE System SHALL expose a web interface on a configurable port for external access
5. WHEN the container is deployed THEN the System SHALL persist data through volume mapping to the host

### Requirement 7: User Management

**User Story:** As an admin, I want to manage user accounts and access, so that I can control who uses the system and provide credentials to authorized users.

#### Acceptance Criteria

1. THE System SHALL support multiple user accounts with unique credentials
2. WHEN an admin configures user accounts THEN the System SHALL store credentials securely
3. WHEN users are created THEN the System SHALL allow independent access for each user
4. THE System SHALL prevent unauthorized access to user data and processing results

### Requirement 8: Web Interface

**User Story:** As a user, I want a simple web interface for all operations, so that I can easily upload, process, and download videos without technical complexity.

#### Acceptance Criteria

1. THE System SHALL provide a single-page web interface combining frontend and backend
2. WHEN the interface loads THEN the System SHALL display all necessary controls (login, upload, progress, preview, download)
3. WHEN user interactions occur THEN the System SHALL provide immediate visual feedback
4. THE System SHALL maintain a clean, simple design focused on core functionality
5. WHEN errors occur THEN the System SHALL display user-friendly error messages