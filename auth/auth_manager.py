"""
Simple Supabase Auth Manager for Mini Video Factory
Uses Supabase Auth directly for authentication
"""

import os
import logging
from typing import Optional
from supabase import create_client, Client
from models.user import User


class AuthManager:
    """Simple authentication manager using Supabase Auth"""
    
    def __init__(self):
        """Initialize with Supabase client"""
        self.logger = logging.getLogger(__name__)
        
        # Get Supabase credentials
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        
        # Create Supabase client (without proxy argument for compatibility)
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.logger.info("AuthManager initialized with Supabase")
        except Exception as e:
            self.logger.error(f"Failed to create Supabase client: {str(e)}")
            raise
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password using Supabase Auth
        
        Args:
            email: User's email (used as username)
            password: User's password
            
        Returns:
            User object if successful, None otherwise
        """
        try:
            # Sign in with Supabase Auth
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Get user data from public.users table
                user_data = self._get_user_profile(response.user.id)
                if user_data:
                    self.logger.info(f"User '{email}' authenticated successfully")
                    return User.from_dict(user_data)
            
            self.logger.warning(f"Authentication failed for '{email}'")
            return None
            
        except Exception as e:
            self.logger.error(f"Authentication error for '{email}': {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID from public.users table
        
        Args:
            user_id: User's auth ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            user_data = self._get_user_profile(user_id)
            if user_data:
                return User.from_dict(user_data)
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {str(e)}")
            return None
    
    def _get_user_profile(self, auth_id: str) -> Optional[dict]:
        """Get user profile from public.users table"""
        try:
            response = self.supabase.table('users').select('*').eq('auth_id', auth_id).execute()
            
            if response.data:
                return response.data[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user profile for {auth_id}: {str(e)}")
            return None
    
    def validate_session(self, user_id: str) -> bool:
        """
        Validate if user session is still valid
        
        Args:
            user_id: User's auth ID
            
        Returns:
            True if valid, False otherwise
        """
        try:
            user = self.get_user_by_id(user_id)
            return user is not None
        except Exception as e:
            self.logger.error(f"Session validation error for {user_id}: {str(e)}")
            return False