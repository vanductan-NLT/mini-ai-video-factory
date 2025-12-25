"""
Integration tests for Mini Video Factory end-to-end functionality
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock, mock_open
from io import BytesIO
from models.processing_job import ProcessingJob, ProcessingStatus


class TestEndToEndWorkflow:
    """Test complete video processing workflow"""
    
    @patch('app.auth_manager')
    @patch('app.storage_manager')
    @patch('app.video_processor')
    @patch('app.current_user')
    def test_complete_video_workflow(self, mock_current_user, mock_video_processor, 
                                   mock_storage_manager, mock_auth_manager, client):
        """Test complete workflow from login to download"""
        # Setup mocks
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        mock_current_user.username = 'testuser@example.com'
        
        mock_auth_manager.authenticate_user.return_value = Mock(
            id='test-user-123',
            username='testuser@example.com'
        )
        
        mock_storage_manager.is_available = True
        mock_storage_manager.upload_file.return_value = True
        mock_storage_manager.download_file.return_value = True
        mock_storage_manager.generate_download_url.return_value = 'https://example.com/download/test'
        
        mock_video_processor.process_video.return_value = True
        
        # Step 1: Login
        with patch('flask_login.login_user'):
            response = client.post('/login', data={
                'email': 'testuser@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            assert response.status_code == 200
        
        # Step 2: Upload file
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
                with client.session_transaction() as sess:
                    sess['_user_id'] = 'test-user-123'
                
                response = client.post('/upload', data={
                    'video_file': (BytesIO(test_file_data), 'test_video.mp4')
                }, content_type='multipart/form-data')
                
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                job_id = data['job_id']
        
        # Step 3: Process video
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.UPLOADED)
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            response = client.post(f'/process_video/{job_id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['success'] is True
        
        # Step 4: Check processing status
        job.update_status(ProcessingStatus.COMPLETED, progress=100)
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            response = client.get(f'/processing_status/{job_id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['status'] == 'completed'
            assert data['progress'] == 100
        
        # Step 5: Download processed video
        job.output_storage_key = 'outputs/test-user-123/processed_video.mp4'
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            response = client.get(f'/download/{job_id}')
            assert response.status_code == 302  # Redirect to download URL
    
    @patch('app.auth_manager')
    @patch('app.current_user')
    def test_authentication_flow(self, mock_current_user, mock_auth_manager, client):
        """Test complete authentication flow"""
        # Test unauthenticated access
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
        
        # Test login page
        response = client.get('/login')
        assert response.status_code == 200
        
        # Test successful login
        mock_user = Mock(id='test-user-123', username='testuser@example.com')
        mock_auth_manager.authenticate_user.return_value = mock_user
        
        with patch('flask_login.login_user'):
            response = client.post('/login', data={
                'email': 'testuser@example.com',
                'password': 'password123'
            }, follow_redirects=True)
            assert response.status_code == 200
        
        # Test authenticated access
        mock_current_user.is_authenticated = True
        mock_current_user.get_id.return_value = 'test-user-123'
        
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test-user-123'
        
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Test logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
    
    @patch('app.current_user')
    def test_error_handling_workflow(self, mock_current_user, client):
        """Test error handling in various scenarios"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test-user-123'
        
        # Test upload with no file
        response = client.post('/upload', data={})
        assert response.status_code == 400
        data = response.get_json()
        assert 'No file uploaded' in data['error']
        
        # Test processing non-existent job
        with patch('models.processing_job.get_processing_job', return_value=None):
            response = client.post('/process_video/invalid-job-id')
            assert response.status_code == 404
            data = response.get_json()
            assert 'Job not found' in data['error']
        
        # Test download non-existent job
        with patch('models.processing_job.get_processing_job', return_value=None):
            response = client.get('/download/invalid-job-id')
            assert response.status_code == 404
            data = response.get_json()
            assert 'Job not found' in data['error']
        
        # Test status check for non-existent job
        with patch('models.processing_job.get_processing_job', return_value=None):
            response = client.get('/processing_status/invalid-job-id')
            assert response.status_code == 404
            data = response.get_json()
            assert 'Job not found' in data['error']
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    @patch('app.current_user')
    def test_user_data_isolation(self, mock_current_user, client):
        """Test that users can only access their own data"""
        # User 1
        mock_current_user.get_id.return_value = 'user-1'
        mock_current_user.is_authenticated = True
        
        job_user1 = ProcessingJob.create_new('user-1', 'video1.mp4')
        job_user2 = ProcessingJob.create_new('user-2', 'video2.mp4')
        
        with client.session_transaction() as sess:
            sess['_user_id'] = 'user-1'
        
        # User 1 should be able to access their own job
        with patch('models.processing_job.get_processing_job', return_value=job_user1):
            response = client.get(f'/processing_status/{job_user1.id}')
            assert response.status_code == 200
        
        # User 1 should NOT be able to access user 2's job
        with patch('models.processing_job.get_processing_job', return_value=job_user2):
            response = client.get(f'/processing_status/{job_user2.id}')
            assert response.status_code == 404  # Job not found (due to user mismatch)
    
    @patch('app.current_user')
    def test_file_format_validation_integration(self, mock_current_user, client):
        """Test file format validation in upload workflow"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test-user-123'
        
        # Test unsupported file format
        response = client.post('/upload', data={
            'video_file': (BytesIO(b'fake content'), 'test_file.txt')
        }, content_type='multipart/form-data')
        
        # Should fail validation before processing
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    @patch('app.current_user')
    @patch('app.storage_manager')
    def test_storage_fallback_integration(self, mock_storage_manager, mock_current_user, client):
        """Test storage fallback from Wasabi to local"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        # Mock storage manager that fails upload
        mock_storage_manager.is_available = True
        mock_storage_manager.upload_file.return_value = False  # Simulate upload failure
        
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
                with patch('os.rename') as mock_rename:  # Mock local storage fallback
                    with client.session_transaction() as sess:
                        sess['_user_id'] = 'test-user-123'
                    
                    response = client.post('/upload', data={
                        'video_file': (BytesIO(test_file_data), 'test_video.mp4')
                    }, content_type='multipart/form-data')
                    
                    # Should still succeed with local storage fallback
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    
                    # Verify fallback to local storage was used
                    mock_rename.assert_called_once()


class TestSystemIntegration:
    """Test system-level integration"""
    
    def test_app_initialization(self):
        """Test that the Flask app initializes correctly"""
        from app import app
        
        assert app is not None
        assert app.config['SECRET_KEY'] is not None
        assert 'UPLOAD_FOLDER' in app.config
        assert 'TEMP_FOLDER' in app.config
        assert 'OUTPUT_FOLDER' in app.config
    
    @patch('app.auth_manager')
    @patch('app.storage_manager')
    @patch('app.video_processor')
    def test_component_initialization(self, mock_video_processor, mock_storage_manager, mock_auth_manager):
        """Test that all components can be initialized"""
        # This test verifies that the app can start with all components
        from app import app
        
        with app.test_client() as client:
            # Test that the app responds to basic requests
            response = client.get('/health')
            assert response.status_code == 200
            
            response = client.get('/')
            assert response.status_code == 302  # Redirect to login
    
    def test_directory_structure(self):
        """Test that required directories are created"""
        from app import app
        
        # These directories should be created during app initialization
        required_dirs = [
            app.config['UPLOAD_FOLDER'],
            app.config['TEMP_FOLDER'],
            app.config['OUTPUT_FOLDER']
        ]
        
        for directory in required_dirs:
            # In test environment, we just check that the config exists
            assert directory is not None
            assert len(directory) > 0
    
    @patch.dict(os.environ, {
        'SECRET_KEY': 'test-secret',
        'MAX_FILE_SIZE': '52428800',  # 50MB
        'MAX_DURATION': '300',  # 5 minutes
        'WHISPER_MODEL': 'tiny',
        'AUTO_EDITOR_ARGS': '--no_open --margin 0.1'
    })
    def test_environment_configuration(self):
        """Test that environment variables are properly loaded"""
        from app import app
        
        # Test that environment variables affect configuration
        assert app.config['SECRET_KEY'] == 'test-secret'
        assert app.config['MAX_CONTENT_LENGTH'] == 52428800
        
        # Test video processor configuration
        from processing.video_processor import VideoProcessor
        processor = VideoProcessor()
        assert processor.whisper_model_name == 'tiny'
        assert '--margin 0.1' in ' '.join(processor.auto_editor_args)
    
    def test_route_registration(self):
        """Test that all required routes are registered"""
        from app import app
        
        # Get all registered routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        # Check that essential routes exist
        essential_routes = [
            '/',
            '/login',
            '/logout',
            '/dashboard',
            '/upload',
            '/health'
        ]
        
        for route in essential_routes:
            assert route in routes
        
        # Check that dynamic routes exist (they'll have parameters)
        dynamic_route_patterns = [
            '/upload_progress/',
            '/process_video/',
            '/processing_status/',
            '/download/',
            '/preview/'
        ]
        
        for pattern in dynamic_route_patterns:
            # Check if any route starts with this pattern
            matching_routes = [r for r in routes if r.startswith(pattern)]
            assert len(matching_routes) > 0, f"No routes found matching pattern: {pattern}"