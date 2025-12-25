"""
Tests for storage functionality
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock, call
from botocore.exceptions import ClientError
from storage.storage_manager import StorageManager


class TestStorageManager:
    """Test cases for StorageManager"""
    
    @patch('storage.storage_manager.wasabi_config')
    @patch('boto3.client')
    def test_init_success(self, mock_boto_client, mock_config):
        """Test successful StorageManager initialization"""
        mock_config.is_configured = True
        mock_config.get_bucket_name.return_value = 'test-bucket'
        mock_config.get_boto3_config.return_value = {
            'aws_access_key_id': 'test-key',
            'aws_secret_access_key': 'test-secret',
            'endpoint_url': 'https://s3.wasabisys.com',
            'region_name': 'us-east-1'
        }
        
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        storage_manager = StorageManager()
        
        assert storage_manager.is_available is True
        assert storage_manager.bucket_name == 'test-bucket'
        assert storage_manager._client == mock_client
    
    @patch('storage.storage_manager.wasabi_config')
    def test_init_not_configured(self, mock_config):
        """Test StorageManager initialization when not configured"""
        mock_config.is_configured = False
        
        storage_manager = StorageManager()
        
        assert storage_manager.is_available is False
        assert storage_manager._client is None
    
    @patch('storage.storage_manager.wasabi_config')
    @patch('boto3.client')
    def test_init_client_error(self, mock_boto_client, mock_config):
        """Test StorageManager initialization with client error"""
        mock_config.is_configured = True
        mock_config.get_boto3_config.return_value = {}
        mock_boto_client.side_effect = Exception("Client creation failed")
        
        storage_manager = StorageManager()
        
        assert storage_manager.is_available is False
        assert storage_manager._client is None
    
    def test_upload_file_success(self, mock_storage_manager):
        """Test successful file upload"""
        mock_storage_manager.upload_file.return_value = True
        
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b'test content')
            temp_file.flush()
            
            result = mock_storage_manager.upload_file(temp_file.name, 'test/file.txt')
            assert result is True
    
    def test_upload_file_not_available(self):
        """Test file upload when storage not available"""
        storage_manager = StorageManager()
        storage_manager._client = None
        
        result = storage_manager.upload_file('/fake/file.txt', 'test/file.txt')
        assert result is False
    
    def test_upload_file_not_exists(self, mock_storage_manager):
        """Test file upload with non-existent file"""
        storage_manager = StorageManager()
        storage_manager._client = Mock()
        
        result = storage_manager.upload_file('/non/existent/file.txt', 'test/file.txt')
        assert result is False
    
    @patch('storage.storage_manager.wasabi_config')
    @patch('boto3.client')
    def test_upload_file_with_retry(self, mock_boto_client, mock_config):
        """Test file upload with retry logic"""
        mock_config.is_configured = True
        mock_config.get_bucket_name.return_value = 'test-bucket'
        mock_config.get_boto3_config.return_value = {}
        
        mock_client = Mock()
        # First call fails, second succeeds
        mock_client.upload_file.side_effect = [
            ClientError({'Error': {'Code': 'ServiceUnavailable'}}, 'upload_file'),
            None
        ]
        mock_boto_client.return_value = mock_client
        
        storage_manager = StorageManager()
        
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b'test content')
            temp_file.flush()
            
            with patch('time.sleep'):  # Speed up test
                result = storage_manager.upload_file(temp_file.name, 'test/file.txt')
                assert result is True
                assert mock_client.upload_file.call_count == 2
    
    def test_download_file_success(self, mock_storage_manager):
        """Test successful file download"""
        mock_storage_manager.download_file.return_value = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, 'downloaded_file.txt')
            result = mock_storage_manager.download_file('test/file.txt', local_path)
            assert result is True
    
    def test_download_file_not_available(self):
        """Test file download when storage not available"""
        storage_manager = StorageManager()
        storage_manager._client = None
        
        result = storage_manager.download_file('test/file.txt', '/local/file.txt')
        assert result is False
    
    @patch('storage.storage_manager.wasabi_config')
    @patch('boto3.client')
    @patch('os.makedirs')
    def test_download_file_creates_directory(self, mock_makedirs, mock_boto_client, mock_config):
        """Test that download creates local directory if needed"""
        mock_config.is_configured = True
        mock_config.get_bucket_name.return_value = 'test-bucket'
        mock_config.get_boto3_config.return_value = {}
        
        mock_client = Mock()
        mock_client.download_file.return_value = None
        mock_boto_client.return_value = mock_client
        
        storage_manager = StorageManager()
        
        local_path = '/some/deep/path/file.txt'
        result = storage_manager.download_file('test/file.txt', local_path)
        
        assert result is True
        mock_makedirs.assert_called_once_with('/some/deep/path', exist_ok=True)
    
    def test_delete_file_success(self, mock_storage_manager):
        """Test successful file deletion"""
        mock_storage_manager.delete_file.return_value = True
        
        result = mock_storage_manager.delete_file('test/file.txt')
        assert result is True
    
    def test_delete_file_not_available(self):
        """Test file deletion when storage not available"""
        storage_manager = StorageManager()
        storage_manager._client = None
        
        result = storage_manager.delete_file('test/file.txt')
        assert result is False
    
    def test_generate_download_url_success(self, mock_storage_manager):
        """Test successful download URL generation"""
        mock_storage_manager.generate_download_url.return_value = 'https://example.com/download/test'
        
        url = mock_storage_manager.generate_download_url('test/file.txt')
        assert url == 'https://example.com/download/test'
    
    def test_generate_download_url_not_available(self):
        """Test download URL generation when storage not available"""
        storage_manager = StorageManager()
        storage_manager._client = None
        
        url = storage_manager.generate_download_url('test/file.txt')
        assert url is None
    
    @patch('storage.storage_manager.wasabi_config')
    @patch('boto3.client')
    def test_generate_download_url_with_expiration(self, mock_boto_client, mock_config):
        """Test download URL generation with custom expiration"""
        mock_config.is_configured = True
        mock_config.get_bucket_name.return_value = 'test-bucket'
        mock_config.get_boto3_config.return_value = {}
        
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = 'https://example.com/download/test'
        mock_boto_client.return_value = mock_client
        
        storage_manager = StorageManager()
        
        url = storage_manager.generate_download_url('test/file.txt', expiration=7200)
        
        assert url == 'https://example.com/download/test'
        mock_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': 'test/file.txt'},
            ExpiresIn=7200
        )
    
    def test_file_exists_success(self, mock_storage_manager):
        """Test successful file existence check"""
        mock_storage_manager.file_exists.return_value = True
        
        exists = mock_storage_manager.file_exists('test/file.txt')
        assert exists is True
    
    def test_file_exists_not_found(self):
        """Test file existence check for non-existent file"""
        storage_manager = StorageManager()
        mock_client = Mock()
        mock_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404'}}, 'head_object'
        )
        storage_manager._client = mock_client
        
        exists = storage_manager.file_exists('test/nonexistent.txt')
        assert exists is False
    
    def test_get_file_info_success(self, mock_storage_manager):
        """Test successful file info retrieval"""
        expected_info = {
            'size': 1024,
            'last_modified': '2023-01-01T00:00:00Z',
            'content_type': 'video/mp4'
        }
        mock_storage_manager.get_file_info.return_value = expected_info
        
        info = mock_storage_manager.get_file_info('test/file.txt')
        assert info == expected_info
    
    def test_get_file_info_not_available(self):
        """Test file info retrieval when storage not available"""
        storage_manager = StorageManager()
        storage_manager._client = None
        
        info = storage_manager.get_file_info('test/file.txt')
        assert info is None
    
    @patch('os.walk')
    @patch('os.path.exists')
    def test_cleanup_temp_files(self, mock_exists, mock_walk):
        """Test temporary file cleanup"""
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/temp', [], ['old_file.txt', 'new_file.txt'])
        ]
        
        storage_manager = StorageManager()
        
        with patch('os.path.getmtime') as mock_getmtime:
            with patch('os.remove') as mock_remove:
                # Mock old file (should be removed)
                mock_getmtime.side_effect = lambda path: 1000 if 'old_file' in path else 9999999999
                
                count = storage_manager.cleanup_temp_files('/temp', max_age_hours=24)
                
                assert count == 1
                mock_remove.assert_called_once()
    
    @patch('shutil.rmtree')
    @patch('os.path.exists')
    def test_cleanup_job_temp_files_success(self, mock_exists, mock_rmtree):
        """Test successful job temp file cleanup"""
        mock_exists.return_value = True
        
        storage_manager = StorageManager()
        result = storage_manager.cleanup_job_temp_files('test-job-123', '/temp')
        
        assert result is True
        mock_rmtree.assert_called_once_with('/temp/job_test-job-123')
    
    @patch('os.path.exists')
    def test_cleanup_job_temp_files_not_exists(self, mock_exists):
        """Test job temp file cleanup when directory doesn't exist"""
        mock_exists.return_value = False
        
        storage_manager = StorageManager()
        result = storage_manager.cleanup_job_temp_files('test-job-123', '/temp')
        
        assert result is True  # Should return True if directory doesn't exist
    
    @patch('os.walk')
    @patch('os.path.exists')
    def test_get_local_storage_usage(self, mock_exists, mock_walk):
        """Test local storage usage calculation"""
        mock_exists.return_value = True
        mock_walk.return_value = [
            ('/data', ['subdir'], ['file1.txt', 'file2.txt']),
            ('/data/subdir', [], ['file3.txt'])
        ]
        
        storage_manager = StorageManager()
        
        with patch('os.stat') as mock_stat:
            # Mock file stats
            mock_stat.return_value.st_size = 1024
            mock_stat.return_value.st_mtime = 1640995200  # 2022-01-01
            
            usage = storage_manager.get_local_storage_usage('/data')
            
            assert usage['total_size'] == 3072  # 3 files * 1024 bytes
            assert usage['file_count'] == 3
            assert usage['directory_count'] == 1
            assert usage['largest_file']['size'] == 1024
    
    @patch('os.path.exists')
    def test_get_local_storage_usage_not_exists(self, mock_exists):
        """Test local storage usage for non-existent directory"""
        mock_exists.return_value = False
        
        storage_manager = StorageManager()
        usage = storage_manager.get_local_storage_usage('/nonexistent')
        
        assert usage['total_size'] == 0
        assert usage['file_count'] == 0
        assert usage['directory_count'] == 0


class TestStorageRoutes:
    """Test cases for storage-related routes"""
    
    @patch('app.current_user')
    @patch('app.storage_manager')
    def test_download_video_success(self, mock_storage_manager, mock_current_user, client):
        """Test successful video download"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        mock_storage_manager.is_available = True
        mock_storage_manager.generate_download_url.return_value = 'https://example.com/download/test'
        
        from models.processing_job import ProcessingJob, ProcessingStatus
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.COMPLETED)
        job.output_storage_key = 'outputs/test-user-123/processed_video.mp4'
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get(f'/download/{job.id}')
            assert response.status_code == 302  # Redirect to download URL
    
    @patch('app.current_user')
    def test_download_video_not_found(self, mock_current_user, client):
        """Test video download with invalid job ID"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        with patch('models.processing_job.get_processing_job', return_value=None):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get('/download/invalid-job-id')
            assert response.status_code == 404
            
            data = response.get_json()
            assert 'Job not found' in data['error']
    
    @patch('app.current_user')
    def test_download_video_not_completed(self, mock_current_user, client):
        """Test video download for incomplete job"""
        mock_current_user.get_id.return_value = 'test-user-123'
        mock_current_user.is_authenticated = True
        
        from models.processing_job import ProcessingJob, ProcessingStatus
        job = ProcessingJob.create_new('test-user-123', 'test_video.mp4')
        job.update_status(ProcessingStatus.AUTO_EDITING)  # Not completed
        
        with patch('models.processing_job.get_processing_job', return_value=job):
            with client.session_transaction() as sess:
                sess['_user_id'] = 'test-user-123'
            
            response = client.get(f'/download/{job.id}')
            assert response.status_code == 400
            
            data = response.get_json()
            assert 'not completed' in data['error']