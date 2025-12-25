"""
Tests for file upload functionality
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock, mock_open
from io import BytesIO
from utils.file_validation import validate_video_file, ValidationError, SUPPORTED_EXTENSIONS
from models.processing_job import ProcessingJob, ProcessingStatus


class TestFileValidation:
    """Test cases for file validation"""
    
    def test_supported_extensions(self):
        """Test that supported extensions are defined"""
        assert '.mp4' in SUPPORTED_EXTENSIONS
        assert '.avi' in SUPPORTED_EXTENSIONS
        assert '.mov' in SUPPORTED_EXTENSIONS
    
    def test_validate_video_file_success(self, temp_video_file):
        """Test successful video file validation"""
        # Create a mock file object
        mock_file = Mock()
        mock_file.filename = 'test_video.mp4'
        
        # Mock ffprobe output for valid video
        mock_ffprobe_output = {
            'format': {
                'duration': '120.5',
                'size': '1048576',
                'format_name': 'mp4,m4a,3gp,3g2,mj2'
            },
            'streams': [{
                'codec_type': 'video',
                'width': 1920,
                'height': 1080,
                'codec_name': 'h264'
            }]
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = str(mock_ffprobe_output).replace("'", '"')
            
            with patch('json.loads', return_value=mock_ffprobe_output):
                video_info = validate_video_file(mock_file, temp_video_file, 10*1024*1024, 600)
                
                assert video_info['duration'] == 120.5
                assert video_info['format'] == 'mp4'
                assert video_info['width'] == 1920
                assert video_info['height'] == 1080
    
    def test_validate_video_file_unsupported_format(self):
        """Test validation with unsupported file format"""
        mock_file = Mock()
        mock_file.filename = 'test_video.txt'
        
        with pytest.raises(ValidationError) as exc_info:
            validate_video_file(mock_file, '/fake/path', 10*1024*1024, 600)
        
        assert 'Unsupported file format' in str(exc_info.value)
    
    def test_validate_video_file_too_large(self, temp_video_file):
        """Test validation with file too large"""
        mock_file = Mock()
        mock_file.filename = 'test_video.mp4'
        
        # Mock a large file size
        with patch('os.path.getsize', return_value=20*1024*1024):  # 20MB
            with pytest.raises(ValidationError) as exc_info:
                validate_video_file(mock_file, temp_video_file, 10*1024*1024, 600)  # 10MB limit
            
            assert 'File size exceeds maximum' in str(exc_info.value)
    
    def test_validate_video_file_too_long(self, temp_video_file):
        """Test validation with video too long"""
        mock_file = Mock()
        mock_file.filename = 'test_video.mp4'
        
        # Mock ffprobe output for long video
        mock_ffprobe_output = {
            'format': {
                'duration': '900.0',  # 15 minutes
                'size': '1048576',
                'format_name': 'mp4'
            }
        }
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = str(mock_ffprobe_output).replace("'", '"')
            
            with patch('json.loads', return_value=mock_ffprobe_output):
                with pytest.raises(ValidationError) as exc_info:
                    validate_video_file(mock_file, temp_video_file, 10*1024*1024, 600)  # 10 minute limit
                
                assert 'Video duration exceeds maximum' in str(exc_info.value)


class TestFileUploadRoutes:
    """Test cases for file upload routes"""
    
    @patch('app.auth_manager')
    @patch('app.storage_manager')
    @patch('app.current_user')
    def test_upload_file_success(self, mock_current_user, mock_storage_manager, mock_auth_manager, client, mock_user):
        """Test successful file upload"""
        # Setup mocks
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        mock_storage_manager.is_available = True
        mock_storage_manager.upload_file.return_value = True
        
        # Create test file data
        test_file_data = b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom' + b'\x00' * 100
        
        with patch('utils.file_validation.validate_video_file') as mock_validate:
            mock_validate.return_value = {
                'duration': 120.5,
                'format': 'mp4',
                'width': 1920,
                'height': 1080,
                'size': len(test_file_data)
            }
            
            with patch('models.processing_job.save_processing_job'):
                # Simulate logged in user
                with client.session_transaction() as sess:
                    sess['_user_id'] = 'test-user-123'
                
                response = client.post('/upload', data={
                    'video_file': (BytesIO(test_file_data), 'test_video.mp4')
                }, content_type='multipart/form-data')
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert 'job_id' in data
    
    def test_upload_file_no_file(self, client):
        """Test upload with no file"""
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test-user-123'
        
        response = client.post('/upload', data={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'No file uploaded' in data['error']
    
    def test_upload_file_empty_filename(self, client):
        """Test upload with empty filename"""
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test-user-123'
        
        response = client.post('/upload', data={
            'video_file': (BytesIO(b''), '')
        }, content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'No file selected' in data['error']
    
    @patch('app.current_user')
    def test_upload_progress_success(self, mock_current_user, client):
        """Test upload progress endpoint"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        # Create a test job
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.UPLOADED, progress=50)
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get(f'/upload_progress/{job.id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['job_id'] == job.id
            assert data['status'] == 'uploaded'
            assert data['progress'] == 50
    
    @patch('app.current_user')
    def test_upload_progress_not_found(self, mock_current_user, client):
        """Test upload progress with invalid job ID"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        with patch('models.processing_job.get_processing_job', return_value=None):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get('/upload_progress/invalid-job-id')
            assert response.status_code == 404
            
            data = response.get_json()
            assert 'Job not found' in data['error']
    
    @patch('app.current_user')
    def test_user_jobs_success(self, mock_current_user, client):
        """Test user jobs endpoint"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        # Create test jobs
        job1 = ProcessingJob.create_new('test-user-123', 'video1.mp4')
        job2 = ProcessingJob.create_new('test-user-123', 'video2.mp4')
        
        with patch('models.processing_job.get_user_jobs', return_value=[job1, job2]):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get('/user_jobs')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['jobs']) == 2
            assert data['jobs'][0]['original_filename'] == 'video1.mp4'
            assert data['jobs'][1]['original_filename'] == 'video2.mp4'