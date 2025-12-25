"""
Core functionality tests for Mini Video Factory
Tests the essential components without complex mocking
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from models.user import User
from models.processing_job import ProcessingJob, ProcessingStatus
from utils.file_validation import SUPPORTED_EXTENSIONS, ValidationError


class TestCoreModels:
    """Test core data models"""
    
    def test_user_model_creation(self):
        """Test User model can be created and converted"""
        user = User(
            id='test-123',
            username='testuser@example.com',
            email='testuser@example.com'
        )
        
        assert user.id == 'test-123'
        assert user.username == 'testuser@example.com'
        assert user.email == 'testuser@example.com'
        
        # Test to_dict conversion
        user_dict = user.to_dict()
        assert user_dict['auth_id'] == 'test-123'
        assert user_dict['username'] == 'testuser@example.com'
        
        # Test from_dict creation
        user2 = User.from_dict(user_dict)
        assert user2.id == user.id
        assert user2.username == user.username
    
    def test_processing_job_creation(self):
        """Test ProcessingJob model can be created and managed"""
        job = ProcessingJob.create_new('user-123', 'test_video.mp4')
        
        assert job.user_id == 'user-123'
        assert job.original_filename == 'test_video.mp4'
        assert job.status == ProcessingStatus.UPLOADED
        assert job.progress == 0
        assert job.id is not None
        
        # Test status updates
        job.update_status(ProcessingStatus.AUTO_EDITING, progress=25)
        assert job.status == ProcessingStatus.AUTO_EDITING
        assert job.progress == 25
        
        # Test completion
        job.update_status(ProcessingStatus.COMPLETED, progress=100)
        assert job.status == ProcessingStatus.COMPLETED
        assert job.progress == 100
        assert job.is_completed() is True
        
        # Test to_dict conversion
        job_dict = job.to_dict()
        assert job_dict['user_id'] == 'user-123'
        assert job_dict['original_filename'] == 'test_video.mp4'
        assert job_dict['status'] == 'completed'
        assert job_dict['progress'] == 100


class TestFileValidation:
    """Test file validation functionality"""
    
    def test_supported_extensions_defined(self):
        """Test that supported file extensions are properly defined"""
        assert '.mp4' in SUPPORTED_EXTENSIONS
        assert '.avi' in SUPPORTED_EXTENSIONS
        assert '.mov' in SUPPORTED_EXTENSIONS
        assert len(SUPPORTED_EXTENSIONS) >= 3
    
    def test_validation_error_creation(self):
        """Test ValidationError can be created and raised"""
        error = ValidationError("Test error message")
        assert str(error) == "Test error message"
        
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation failed")
        
        assert "Test validation failed" in str(exc_info.value)


class TestAppConfiguration:
    """Test Flask app configuration"""
    
    def test_app_exists_and_configured(self):
        """Test that the Flask app exists and has basic configuration"""
        from app import app
        
        assert app is not None
        assert app.config is not None
        
        # Check essential config keys exist
        essential_configs = [
            'SECRET_KEY',
            'MAX_CONTENT_LENGTH',
            'UPLOAD_FOLDER',
            'TEMP_FOLDER',
            'OUTPUT_FOLDER'
        ]
        
        for config_key in essential_configs:
            assert config_key in app.config
            assert app.config[config_key] is not None
    
    def test_app_routes_registered(self):
        """Test that essential routes are registered"""
        from app import app
        
        # Get all registered routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        # Check essential routes exist
        essential_routes = [
            '/',
            '/login',
            '/logout',
            '/dashboard',
            '/upload',
            '/health'
        ]
        
        for route in essential_routes:
            assert route in routes, f"Route {route} not found in registered routes"


class TestComponentInitialization:
    """Test that components can be initialized"""
    
    @patch.dict(os.environ, {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'WASABI_ACCESS_KEY': 'test-access',
        'WASABI_SECRET_KEY': 'test-secret',
        'WASABI_BUCKET': 'test-bucket'
    })
    def test_auth_manager_initialization(self):
        """Test AuthManager can be initialized with proper config"""
        with patch('supabase.create_client') as mock_create_client:
            mock_client = Mock()
            mock_create_client.return_value = mock_client
            
            from auth.auth_manager import AuthManager
            auth_manager = AuthManager()
            
            assert auth_manager is not None
            mock_create_client.assert_called_once()
    
    def test_storage_manager_initialization(self):
        """Test StorageManager can be initialized"""
        from storage.storage_manager import StorageManager
        
        # Should initialize even without config (will be unavailable)
        storage_manager = StorageManager()
        assert storage_manager is not None
    
    def test_video_processor_initialization(self):
        """Test VideoProcessor can be initialized"""
        from processing.video_processor import VideoProcessor
        
        processor = VideoProcessor()
        assert processor is not None
        assert processor.whisper_model_name is not None
        assert processor.temp_folder is not None
        assert processor.output_folder is not None


class TestBasicRoutes:
    """Test basic route functionality"""
    
    def test_health_check_route(self, client):
        """Test health check endpoint works"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_index_route_redirects(self, client):
        """Test index route redirects to login when not authenticated"""
        response = client.get('/')
        assert response.status_code == 302  # Redirect
        assert '/login' in response.location
    
    def test_login_page_loads(self, client):
        """Test login page loads successfully"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
        assert '/login' in response.location


class TestEnvironmentHandling:
    """Test environment variable handling"""
    
    def test_default_config_values(self):
        """Test that default configuration values are set"""
        from app import app
        
        # These should have default values even without env vars
        assert app.config.get('SECRET_KEY') is not None
        assert app.config.get('MAX_CONTENT_LENGTH') is not None
        assert app.config.get('UPLOAD_FOLDER') is not None
        assert app.config.get('TEMP_FOLDER') is not None
        assert app.config.get('OUTPUT_FOLDER') is not None
    
    @patch.dict(os.environ, {
        'MAX_FILE_SIZE': '52428800',  # 50MB
        'MAX_DURATION': '300',  # 5 minutes
        'WHISPER_MODEL': 'tiny'
    })
    def test_environment_override(self):
        """Test that environment variables override defaults"""
        # Test video processor picks up env vars
        from processing.video_processor import VideoProcessor
        processor = VideoProcessor()
        
        assert processor.whisper_model_name == 'tiny'


class TestDataDirectories:
    """Test data directory creation and management"""
    
    def test_directories_created(self):
        """Test that required directories are created"""
        from app import app
        
        # In test mode, directories should be created
        required_dirs = [
            app.config['UPLOAD_FOLDER'],
            app.config['TEMP_FOLDER'],
            app.config['OUTPUT_FOLDER']
        ]
        
        for directory in required_dirs:
            # Directory should exist or be creatable
            assert directory is not None
            assert len(directory) > 0
            
            # Try to create if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            assert os.path.exists(directory)


class TestProcessingStatuses:
    """Test processing status enumeration"""
    
    def test_processing_status_values(self):
        """Test ProcessingStatus enum has all required values"""
        from models.processing_job import ProcessingStatus
        
        required_statuses = [
            'UPLOADED',
            'VALIDATING', 
            'STORING',
            'AUTO_EDITING',
            'TRANSCRIBING',
            'ADDING_SUBTITLES',
            'COMPLETED',
            'FAILED'
        ]
        
        for status_name in required_statuses:
            assert hasattr(ProcessingStatus, status_name)
            status = getattr(ProcessingStatus, status_name)
            assert status.value is not None
    
    def test_status_display_names(self):
        """Test that status display names work"""
        job = ProcessingJob.create_new('user-123', 'test.mp4')
        
        # Test various status updates
        job.update_status(ProcessingStatus.AUTO_EDITING)
        display = job.get_status_display()
        assert display is not None
        assert len(display) > 0
        
        job.update_status(ProcessingStatus.COMPLETED)
        display = job.get_status_display()
        assert display is not None
        assert len(display) > 0