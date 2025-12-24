"""
Storage Manager for Wasabi S3-compatible storage

Handles file operations with Wasabi cloud storage including upload, download, and cleanup.
"""

import os
import boto3
import logging
from typing import Optional, Dict, Any
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
    
    def upload_file(self, local_path: str, remote_key: str) -> bool:
        """
        Upload a file to Wasabi storage
        
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
            self._client.upload_file(local_path, self.bucket_name, remote_key)
            logger.info(f"Successfully uploaded {local_path} to {remote_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file {local_path}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file {local_path}: {str(e)}")
            return False
    
    def download_file(self, remote_key: str, local_path: str) -> bool:
        """
        Download a file from Wasabi storage
        
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
            
            self._client.download_file(self.bucket_name, remote_key, local_path)
            logger.info(f"Successfully downloaded {remote_key} to {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download file {remote_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading file {remote_key}: {str(e)}")
            return False
    
    def delete_file(self, remote_key: str) -> bool:
        """
        Delete a file from Wasabi storage
        
        Args:
            remote_key: S3 key (path) of the file to delete
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        if not self.is_available:
            logger.error("Storage manager not available")
            return False
        
        try:
            self._client.delete_object(Bucket=self.bucket_name, Key=remote_key)
            logger.info(f"Successfully deleted {remote_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {remote_key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file {remote_key}: {str(e)}")
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
            response = self._client.head_object(Bucket=self.bucket_name, Key=remote_key)
            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag', '').strip('"')
            }
        except ClientError as e:
            logger.error(f"Failed to get file info for {remote_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file info for {remote_key}: {str(e)}")
            return None