"""
Tests for video processing functionality
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from processing.video_processor import VideoProcessor, VideoProcessingError
from models.processing_job import ProcessingJob, ProcessingStatus


class TestVideoProcessor:
    """Test cases for VideoProcessor"""
    
    def test_init(self):
        """Test VideoProcessor initialization"""
        processor = VideoProcessor()
        assert processor.whisper_model_name == 'base'
        assert processor.temp_folder == './data/temp'
        assert processor.output_folder == './data/output'
    
    def test_init_with_storage_manager(self, mock_storage_manager):
        """Test VideoProcessor initialization with storage manager"""
        processor = VideoProcessor(mock_storage_manager)
        assert processor.storage_manager == mock_storage_manager
    
    @patch('whisper.load_model')
    def test_load_whisper_model_success(self, mock_load_model):
        """Test successful Whisper model loading"""
        mock_model = Mock()
        mock_load_model.return_value = mock_model
        
        processor = VideoProcessor()
        processor._load_whisper_model()
        
        assert processor.whisper_model == mock_model
        mock_load_model.assert_called_once_with('base')
    
    @patch('whisper.load_model')
    def test_load_whisper_model_failure(self, mock_load_model):
        """Test Whisper model loading failure"""
        mock_load_model.side_effect = Exception("Model not found")
        
        processor = VideoProcessor()
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._load_whisper_model()
        
        assert "Failed to load Whisper model" in str(exc_info.value)
    
    def test_create_temp_directory(self):
        """Test temporary directory creation"""
        processor = VideoProcessor()
        
        with patch('os.makedirs') as mock_makedirs:
            temp_dir = processor._create_temp_directory('test-job-123')
            
            expected_path = os.path.join(processor.temp_folder, 'job_test-job-123')
            assert temp_dir == expected_path
            mock_makedirs.assert_called_once_with(expected_path, exist_ok=True)
    
    @patch('shutil.rmtree')
    @patch('os.path.exists')
    def test_cleanup_temp_directory(self, mock_exists, mock_rmtree):
        """Test temporary directory cleanup"""
        mock_exists.return_value = True
        
        processor = VideoProcessor()
        processor._cleanup_temp_directory('/test/temp/dir')
        
        mock_rmtree.assert_called_once_with('/test/temp/dir')
    
    def test_download_input_file_from_storage(self, mock_storage_manager):
        """Test downloading input file from storage"""
        processor = VideoProcessor(mock_storage_manager)
        
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.input_storage_key = 'uploads/test-user-123/test_video.mp4'
        
        mock_storage_manager.download_file.return_value = True
        
        with patch('os.path.join', return_value='/temp/input_test_video.mp4'):
            result = processor._download_input_file(job, '/temp')
            
            assert result == '/temp/input_test_video.mp4'
            mock_storage_manager.download_file.assert_called_once()
    
    def test_download_input_file_from_local(self):
        """Test downloading input file from local storage"""
        processor = VideoProcessor()
        
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.input_file_path = '/uploads/test_video.mp4'
        
        with patch('os.path.exists', return_value=True):
            with patch('shutil.copy2') as mock_copy:
                with patch('os.path.join', return_value='/temp/input_test_video.mp4'):
                    result = processor._download_input_file(job, '/temp')
                    
                    assert result == '/temp/input_test_video.mp4'
                    mock_copy.assert_called_once()
    
    def test_download_input_file_no_source(self):
        """Test downloading input file with no valid source"""
        processor = VideoProcessor()
        
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        # No input_storage_key or input_file_path set
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._download_input_file(job, '/temp')
        
        assert "No valid input file path found" in str(exc_info.value)
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_run_auto_editor_success(self, mock_exists, mock_run):
        """Test successful auto-editor execution"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Auto-editor completed"
        mock_run.return_value.stderr = ""
        mock_exists.return_value = True
        
        processor = VideoProcessor()
        result = processor._run_auto_editor('/input.mp4', '/output.mp4')
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check that auto-editor was called with correct arguments
        call_args = mock_run.call_args[0][0]
        assert 'auto-editor' in call_args
        assert '/input.mp4' in call_args
        assert '/output.mp4' in call_args
    
    @patch('subprocess.run')
    def test_run_auto_editor_failure(self, mock_run):
        """Test auto-editor execution failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Auto-editor failed"
        
        processor = VideoProcessor()
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._run_auto_editor('/input.mp4', '/output.mp4')
        
        assert "Auto-editor failed" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_run_auto_editor_timeout(self, mock_run):
        """Test auto-editor timeout"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired('auto-editor', 300)
        
        processor = VideoProcessor()
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._run_auto_editor('/input.mp4', '/output.mp4')
        
        assert "timed out" in str(exc_info.value)
    
    @patch('subprocess.run')
    def test_extract_audio_success(self, mock_run):
        """Test successful audio extraction"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        processor = VideoProcessor()
        result = processor._extract_audio('/video.mp4', '/audio.wav')
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check that ffmpeg was called with correct arguments
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '/video.mp4' in call_args
        assert '/audio.wav' in call_args
    
    @patch('subprocess.run')
    def test_extract_audio_failure(self, mock_run):
        """Test audio extraction failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "FFmpeg failed"
        
        processor = VideoProcessor()
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._extract_audio('/video.mp4', '/audio.wav')
        
        assert "Audio extraction failed" in str(exc_info.value)
    
    def test_transcribe_audio_success(self):
        """Test successful audio transcription"""
        processor = VideoProcessor()
        
        # Mock Whisper model and transcription result
        mock_model = Mock()
        mock_transcription = {
            'segments': [
                {'start': 0.0, 'end': 5.0, 'text': 'Hello world'},
                {'start': 5.0, 'end': 10.0, 'text': 'This is a test'}
            ]
        }
        mock_model.transcribe.return_value = mock_transcription
        processor.whisper_model = mock_model
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = processor._transcribe_audio('/audio.wav', '/subtitles.srt')
            
            assert result is True
            mock_model.transcribe.assert_called_once_with('/audio.wav')
            mock_file.assert_called_once_with('/subtitles.srt', 'w', encoding='utf-8')
    
    def test_generate_srt(self):
        """Test SRT subtitle generation"""
        processor = VideoProcessor()
        
        transcription_result = {
            'segments': [
                {'start': 0.0, 'end': 5.0, 'text': 'Hello world'},
                {'start': 5.0, 'end': 10.0, 'text': 'This is a test'}
            ]
        }
        
        srt_content = processor._generate_srt(transcription_result)
        
        assert '1' in srt_content
        assert '00:00:00,000 --> 00:00:05,000' in srt_content
        assert 'Hello world' in srt_content
        assert '2' in srt_content
        assert '00:00:05,000 --> 00:00:10,000' in srt_content
        assert 'This is a test' in srt_content
    
    def test_format_timestamp(self):
        """Test timestamp formatting for SRT"""
        processor = VideoProcessor()
        
        # Test various timestamps
        assert processor._format_timestamp(0.0) == "00:00:00,000"
        assert processor._format_timestamp(65.5) == "00:01:05,500"
        assert processor._format_timestamp(3661.123) == "01:01:01,123"
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_embed_subtitles_success(self, mock_exists, mock_run):
        """Test successful subtitle embedding"""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        processor = VideoProcessor()
        result = processor._embed_subtitles('/video.mp4', '/subtitles.srt', '/output.mp4')
        
        assert result is True
        mock_run.assert_called_once()
        
        # Check that ffmpeg was called with correct arguments
        call_args = mock_run.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '/video.mp4' in call_args
        assert '/output.mp4' in call_args
    
    @patch('os.path.exists')
    def test_embed_subtitles_no_srt_file(self, mock_exists):
        """Test subtitle embedding with missing SRT file"""
        mock_exists.return_value = False
        
        processor = VideoProcessor()
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._embed_subtitles('/video.mp4', '/subtitles.srt', '/output.mp4')
        
        assert "Subtitle file not found" in str(exc_info.value)
    
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_embed_subtitles_failure(self, mock_exists, mock_run):
        """Test subtitle embedding failure"""
        mock_exists.return_value = True
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "FFmpeg subtitle embedding failed"
        
        processor = VideoProcessor()
        
        with pytest.raises(VideoProcessingError) as exc_info:
            processor._embed_subtitles('/video.mp4', '/subtitles.srt', '/output.mp4')
        
        assert "Subtitle embedding failed" in str(exc_info.value)


class TestVideoProcessingRoutes:
    """Test cases for video processing routes"""
    
    @patch('app.current_user')
    @patch('app.video_processor')
    def test_process_video_success(self, mock_video_processor, mock_current_user, client):
        """Test successful video processing request"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        mock_video_processor.process_video.return_value = True
        
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.UPLOADED)
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.post(f'/process_video/{job.id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
            assert data['job_id'] == job.id
    
    @patch('app.current_user')
    def test_process_video_not_found(self, mock_current_user, client):
        """Test video processing with invalid job ID"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        with patch('models.processing_job.get_processing_job', return_value=None):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.post('/process_video/invalid-job-id')
            assert response.status_code == 404
            
            data = response.get_json()
            assert 'Job not found' in data['error']
    
    @patch('app.current_user')
    def test_process_video_wrong_status(self, mock_current_user, client):
        """Test video processing with job in wrong status"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.COMPLETED)  # Wrong status
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.post(f'/process_video/{job.id}')
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'not ready for processing' in data['error']
    
    @patch('app.current_user')
    def test_processing_status_success(self, mock_current_user, client):
        """Test processing status endpoint"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.AUTO_EDITING, progress=25)
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get(f'/processing_status/{job.id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['job_id'] == job.id
            assert data['status'] == 'auto_editing'
            assert data['progress'] == 25