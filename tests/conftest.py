"""
Test configuration and fixtures for Mini Video Factory tests
"""

import pytest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch
from flask import Flask
from app import app as flask_app
from models.user import User
from models.processing_job import ProcessingJob, ProcessingStatus


@pytest.fixture
def app():
    """Create and configure a test Flask app"""
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'MAX_CONTENT_LENGTH': 10 * 1024 * 1024,  # 10MB for testing
        'UPLOAD_FOLDER': './test_data/uploads',
        'TEMP_FOLDER': './test_data/temp',
        'OUTPUT_FOLDER': './test_data/output'
    })
    
    # Create test directories
    os.makedirs('./test_data/uploads', exist_ok=True)
    os.makedirs('./test_data/temp', exist_ok=True)
    os.makedirs('./test_data/output', exist_ok=True)
    
    yield flask_app
    
    # Cleanup test directories
    if os.path.exists('./test_data'):
        shutil.rmtree('./test_data')


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return User(
        id='test-user-123',
        username='testuser@example.com',
        email='testuser@example.com',
        created_at=None,
        last_login=None
    )


@pytest.fixture
def mock_processing_job():
    """Create a mock processing job for testing"""
    return ProcessingJob.create_new('test-user-123', 'test_video.mp4')


@pytest.fixture
def temp_video_file():
    """Create a temporary video file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        # Write minimal MP4 header for testing
        f.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom')
        f.write(b'\x00' * 100)  # Pad with zeros
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_auth_manager():
    """Create a mock auth manager"""
    mock = Mock()
    mock.authenticate_user.return_value = User(
        id='test-user-123',
        username='testuser@example.com',
        email='testuser@example.com',
        created_at=None,
        last_login=None
    )
    mock.get_user_by_id.return_value = User(
        id='test-user-123',
        username='testuser@example.com',
        email='testuser@example.com',
        created_at=None,
        last_login=None
    )
    mock.validate_session.return_value = True
    return mock


@pytest.fixture
def mock_storage_manager():
    """Create a mock storage manager"""
    mock = Mock()
    mock.is_available = True
    mock.upload_file.return_value = True
    mock.download_file.return_value = True
    mock.delete_file.return_value = True
    mock.generate_download_url.return_value = 'https://example.com/download/test'
    mock.file_exists.return_value = True
    mock.get_file_info.return_value = {
        'size': 1024,
        'last_modified': '2023-01-01T00:00:00Z',
        'content_type': 'video/mp4'
    }
    return mock


@pytest.fixture
def mock_video_processor():
    """Create a mock video processor"""
    mock = Mock()
    mock.process_video.return_value = True
    mock.get_processing_status.return_value = {
        'job_id': 'test-job-123',
        'status': 'completed',
        'progress': 100,
        'error_message': None,
        'completed': True
    }
    return mock