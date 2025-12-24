"""
Storage configuration for Wasabi S3-compatible storage

Manages connection settings and credentials for Wasabi cloud storage.
"""

import os
from typing import Dict, Any

class WasabiConfig:
    """Configuration class for Wasabi storage settings"""
    
    def __init__(self):
        """Initialize Wasabi configuration from environment variables"""
        self.endpoint = os.environ.get('WASABI_ENDPOINT')
        self.region = os.environ.get('WASABI_REGION', 'us-east-1')
        self.bucket = os.environ.get('WASABI_BUCKET')
        self.access_key_id = os.environ.get('WASABI_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('WASABI_SECRET_ACCESS_KEY')
        
        # Validate required settings
        self._validate_config()
    
    def _validate_config(self):
        """Validate that all required Wasabi settings are provided"""
        required_settings = {
            'WASABI_ENDPOINT': self.endpoint,
            'WASABI_BUCKET': self.bucket,
            'WASABI_ACCESS_KEY_ID': self.access_key_id,
            'WASABI_SECRET_ACCESS_KEY': self.secret_access_key
        }
        
        missing_settings = [
            key for key, value in required_settings.items() 
            if not value
        ]
        
        if missing_settings:
            raise ValueError(
                f"Missing required Wasabi configuration: {', '.join(missing_settings)}"
            )
    
    def get_boto3_config(self) -> Dict[str, Any]:
        """
        Get boto3 client configuration for Wasabi
        
        Returns:
            Dict containing boto3 client configuration
        """
        return {
            'endpoint_url': self.endpoint,
            'region_name': self.region,
            'aws_access_key_id': self.access_key_id,
            'aws_secret_access_key': self.secret_access_key
        }
    
    def get_bucket_name(self) -> str:
        """
        Get the configured bucket name
        
        Returns:
            str: Bucket name
        """
        return self.bucket
    
    @property
    def is_configured(self) -> bool:
        """
        Check if Wasabi is properly configured
        
        Returns:
            bool: True if all required settings are present
        """
        try:
            self._validate_config()
            return True
        except ValueError:
            return False

# Global instance
wasabi_config = WasabiConfig()