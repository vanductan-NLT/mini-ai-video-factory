"""
Storage Manager for Wasabi S3-compatible storage

Handles file operations with Wasabi cloud storage including upload, download, and cleanup.
Includes retry logic, temporary file management, and usage tracking.
"""

import os
import time
import shutil
import glob
import boto3
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from config.storage import wasabi_config

logger = logging.getLogger(__name__)

class StorageManager:
    """Manages file operations with Wasabi S3-compatible storage"""
    
    def __init__(self):
        """Initialize StorageManager with Wasabi configuration"""
        self.config = wasabi_config
        self.bucket_name = self.config.get_bucket_name()
        self._client = None
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 60.0  # Maximum delay between retries
        
        # Usage tracking
        self._usage_cache = {}
        self._cache_expiry = None
        self._cache_duration = timedelta(minutes=5)  # Cache usage data for 5 minutes
        
        if self.config.is_configured:
            try:
                self._client = boto3.client('s3', **self.config.get_boto3_config())
                logger.info("StorageManager initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {str(e)}")
                self._client = None
        else:
            logger.warning("Wasabi storage not configured - StorageManager will not be available")
    
    @property
    def is_available(self) -> bool:
        """Check if storage manager is available and configured"""
        return self._client is not None
    
    def _retry_with_backoff(self, operation, *args, **kwargs):
        """
        Execute an operation with exponential backoff retry logic
        
        Args:
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation if successful
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except ClientError as e:
                last_exception = e
                error_code = e.response.get('Error', {}).get('Code', '')
                
                # Don't retry on certain errors
                if error_code in ['NoSuchBucket', 'InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                    logger.error(f"Non-retryable error: {error_code}")
                    raise e
                
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Operation failed (attempt {attempt + 1}/{self.max_retries}), retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"Operation failed after {self.max_retries} attempts: {str(e)}")
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    logger.warning(f"Unexpected error (attempt {attempt + 1}/{self.max_retries}), retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"Unexpected error after {self.max_retries} attempts: {str(e)}")
        
        raise last_exception
    
    def upload_file(self, local_path: str, remote_key: str) -> bool:
        """
        Upload a file to Wasabi storage with retry logic
        
        Args:
            local_path: Path to local file to upload
            remote_key: S3 key (path) for the uploaded file
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return False
        
        if not os.path.exists(local_path):
            logger.error(f"Local file does not exist: {local_path}")
            return False
        
        try:
            def _upload_operation():
                self._client.upload_file(local_path, self.bucket_name, remote_key)
                return True
            
            result = self._retry_with_backoff(_upload_operation)
            logger.info(f"Successfully uploaded {local_path} to {remote_key}")
            return result
        except Exception as e:
            logger.error(f"Failed to upload file {local_path} after all retries: {str(e)}")
            return False
    
    def download_file(self, remote_key: str, local_path: str) -> bool:
        """
        Download a file from Wasabi storage with retry logic
        
        Args:
            remote_key: S3 key (path) of the file to download
            local_path: Local path where file should be saved
            
        Returns:
            bool: True if download successful, False otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return False
        
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            def _download_operation():
                self._client.download_file(self.bucket_name, remote_key, local_path)
                return True
            
            result = self._retry_with_backoff(_download_operation)
            logger.info(f"Successfully downloaded {remote_key} to {local_path}")
            return result
        except Exception as e:
            logger.error(f"Failed to download file {remote_key} after all retries: {str(e)}")
            return False
    
    def delete_file(self, remote_key: str) -> bool:
        """
        Delete a file from Wasabi storage with retry logic
        
        Args:
            remote_key: S3 key (path) of the file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return False
        
        try:
            def _delete_operation():
                self._client.delete_object(Bucket=self.bucket_name, Key=remote_key)
                return True
            
            result = self._retry_with_backoff(_delete_operation)
            logger.info(f"Successfully deleted {remote_key}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete file {remote_key} after all retries: {str(e)}")
            return False
    
    def generate_download_url(self, remote_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file
        
        Args:
            remote_key: S3 key (path) of the file
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL if successful, None otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return None
        
        try:
            url = self._client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': remote_key},
                ExpiresIn=expiration
            )
            logger.info(f"Generated download URL for {remote_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate download URL for {remote_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating download URL for {remote_key}: {str(e)}")
            return None
    
    def file_exists(self, remote_key: str) -> bool:
        """
        Check if a file exists in Wasabi storage
        
        Args:
            remote_key: S3 key (path) of the file to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return False
        
        try:
            self._client.head_object(Bucket=self.bucket_name, Key=remote_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking if file exists {remote_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking if file exists {remote_key}: {str(e)}")
            return False
    
    def get_file_info(self, remote_key: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata information about a file in storage
        
        Args:
            remote_key: S3 key (path) of the file
            
        Returns:
            dict: File metadata if successful, None otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return None
        
        try:
            def _get_info_operation():
                return self._client.head_object(Bucket=self.bucket_name, Key=remote_key)
            
            response = self._retry_with_backoff(_get_info_operation)
            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"')
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {remote_key} after all retries: {str(e)}")
            return None
    
    # Temporary file management methods
    
    def cleanup_temp_files(self, temp_dir: str, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age
        
        Args:
            temp_dir: Directory containing temporary files
            max_age_hours: Maximum age of files to keep (default: 24 hours)
            
        Returns:
            int: Number of files cleaned up
        """
        if not os.path.exists(temp_dir):
            logger.warning(f"Temporary directory does not exist: {temp_dir}")
            return 0
        
        cleaned_count = 0
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            # Clean up files in temp directory
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.debug(f"Cleaned up temp file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to remove temp file {file_path}: {str(e)}")
                
                # Clean up empty directories
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # Directory is empty
                            os.rmdir(dir_path)
                            logger.debug(f"Cleaned up empty temp directory: {dir_path}")
                    except OSError as e:
                        logger.debug(f"Could not remove directory {dir_path}: {str(e)}")
            
            logger.info(f"Cleaned up {cleaned_count} temporary files from {temp_dir}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {str(e)}")
            return cleaned_count
    
    def cleanup_job_temp_files(self, job_id: str, temp_base_dir: str) -> bool:
        """
        Clean up temporary files for a specific processing job
        
        Args:
            job_id: Processing job ID
            temp_base_dir: Base temporary directory
            
        Returns:
            bool: True if cleanup successful, False otherwise
        """
        job_temp_dir = os.path.join(temp_base_dir, f"job_{job_id}")
        
        if not os.path.exists(job_temp_dir):
            logger.debug(f"Job temp directory does not exist: {job_temp_dir}")
            return True
        
        try:
            shutil.rmtree(job_temp_dir)
            logger.info(f"Successfully cleaned up job temp directory: {job_temp_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to clean up job temp directory {job_temp_dir}: {str(e)}")
            return False
    
    def get_local_storage_usage(self, directory: str) -> Dict[str, Any]:
        """
        Get storage usage information for a local directory
        
        Args:
            directory: Directory to analyze
            
        Returns:
            dict: Storage usage information
        """
        if not os.path.exists(directory):
            return {
                'total_size': 0,
                'file_count': 0,
                'directory_count': 0,
                'largest_file': None,
                'oldest_file': None,
                'newest_file': None
            }
        
        total_size = 0
        file_count = 0
        directory_count = 0
        largest_file = {'path': None, 'size': 0}
        oldest_file = {'path': None, 'mtime': float('inf')}
        newest_file = {'path': None, 'mtime': 0}
        
        try:
            for root, dirs, files in os.walk(directory):
                directory_count += len(dirs)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        file_mtime = stat.st_mtime
                        
                        total_size += file_size
                        file_count += 1
                        
                        if file_size > largest_file['size']:
                            largest_file = {'path': file_path, 'size': file_size}
                        
                        if file_mtime < oldest_file['mtime']:
                            oldest_file = {'path': file_path, 'mtime': file_mtime}
                        
                        if file_mtime > newest_file['mtime']:
                            newest_file = {'path': file_path, 'mtime': file_mtime}
                            
                    except OSError as e:
                        logger.warning(f"Could not stat file {file_path}: {str(e)}")
            
            return {
                'total_size': total_size,
                'file_count': file_count,
                'directory_count': directory_count,
                'largest_file': largest_file if largest_file['path'] else None,
                'oldest_file': oldest_file if oldest_file['path'] else None,
                'newest_file': newest_file if newest_file['path'] else None
            }
            
        except Exception as e:
            logger.error(f"Error analyzing directory {directory}: {str(e)}")
            return {
                'total_size': 0,
                'file_count': 0,
                'directory_count': 0,
                'largest_file': None,
                'oldest_file': None,
                'newest_file': None
            }
    
    # Storage quota and usage tracking methods
    
    def get_bucket_usage(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get storage usage information for the Wasabi bucket
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            dict: Bucket usage information if successful, None otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return None
        
        # Check cache first
        now = datetime.now()
        if not force_refresh and self._cache_expiry and now < self._cache_expiry:
            logger.debug("Returning cached bucket usage data")
            return self._usage_cache.copy()
        
        try:
            def _list_objects_operation():
                paginator = self._client.get_paginator('list_objects_v2')
                return paginator.paginate(Bucket=self.bucket_name)
            
            page_iterator = self._retry_with_backoff(_list_objects_operation)
            
            total_size = 0
            object_count = 0
            largest_object = {'key': None, 'size': 0}
            oldest_object = {'key': None, 'last_modified': None}
            newest_object = {'key': None, 'last_modified': None}
            
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        size = obj['Size']
                        last_modified = obj['LastModified']
                        key = obj['Key']
                        
                        total_size += size
                        object_count += 1
                        
                        if size > largest_object['size']:
                            largest_object = {'key': key, 'size': size}
                        
                        if oldest_object['last_modified'] is None or last_modified < oldest_object['last_modified']:
                            oldest_object = {'key': key, 'last_modified': last_modified}
                        
                        if newest_object['last_modified'] is None or last_modified > newest_object['last_modified']:
                            newest_object = {'key': key, 'last_modified': last_modified}
            
            usage_data = {
                'total_size': total_size,
                'object_count': object_count,
                'largest_object': largest_object if largest_object['key'] else None,
                'oldest_object': oldest_object if oldest_object['key'] else None,
                'newest_object': newest_object if newest_object['key'] else None,
                'last_updated': now
            }
            
            # Update cache
            self._usage_cache = usage_data.copy()
            self._cache_expiry = now + self._cache_duration
            
            logger.info(f"Retrieved bucket usage: {object_count} objects, {total_size} bytes")
            return usage_data
            
        except Exception as e:
            logger.error(f"Failed to get bucket usage after all retries: {str(e)}")
            return None
    
    def check_storage_quota(self, quota_bytes: int) -> Dict[str, Any]:
        """
        Check current storage usage against quota
        
        Args:
            quota_bytes: Storage quota in bytes
            
        Returns:
            dict: Quota check results
        """
        usage_data = self.get_bucket_usage()
        
        if usage_data is None:
            return {
                'quota_bytes': quota_bytes,
                'used_bytes': 0,
                'available_bytes': quota_bytes,
                'usage_percentage': 0.0,
                'quota_exceeded': False,
                'warning_threshold_reached': False,
                'error': 'Could not retrieve usage data'
            }
        
        used_bytes = usage_data['total_size']
        available_bytes = max(0, quota_bytes - used_bytes)
        usage_percentage = (used_bytes / quota_bytes) * 100 if quota_bytes > 0 else 0.0
        quota_exceeded = used_bytes > quota_bytes
        warning_threshold_reached = usage_percentage >= 80.0  # 80% warning threshold
        
        return {
            'quota_bytes': quota_bytes,
            'used_bytes': used_bytes,
            'available_bytes': available_bytes,
            'usage_percentage': usage_percentage,
            'quota_exceeded': quota_exceeded,
            'warning_threshold_reached': warning_threshold_reached,
            'object_count': usage_data['object_count'],
            'last_updated': usage_data['last_updated']
        }
    
    def list_files_by_prefix(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List files in storage with optional prefix filter
        
        Args:
            prefix: Prefix to filter files (default: empty for all files)
            max_keys: Maximum number of files to return
            
        Returns:
            list: List of file information dictionaries
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return []
        
        try:
            def _list_operation():
                return self._client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=max_keys
                )
            
            response = self._retry_with_backoff(_list_operation)
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'].strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD')
                    })
            
            logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files with prefix '{prefix}' after all retries: {str(e)}")
            return []