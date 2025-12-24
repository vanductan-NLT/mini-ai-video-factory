"""
Authentication manager for Mini Video Factory with Supabase integration
"""

import os
import logging
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
from models.user import User


class AuthManager:
    """Manages user authentication with Supabase backend"""
    
    def __init__(self):
        """Initialize AuthManager with Supabase client"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Supabase client
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            self.logger.error("Supabase configuration missing - check SUPABASE_URL and SUPABASE_KEY")
            raise ValueError("Supabase configuration required")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.logger.info("AuthManager initialized with Supabase client")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password
        
        Args:
            username: User's username
            password: User's plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Query user from Supabase
            response = self.supabase.table('users').select('*').eq('username', username).execute()
            
            if not response.data:
                self.logger.warning(f"Authentication failed: user '{username}' not found")
                return None
            
            user_data = response.data[0]
            user = User.from_dict(user_data)
            
            # Verify password
            if check_password_hash(user.password_hash, password):
                # Update last login timestamp
                user.update_last_login()
                self._update_last_login(user.id, user.last_login)
                
                self.logger.info(f"User '{username}' authenticated successfully")
                return user
            else:
                self.logger.warning(f"Authentication failed: invalid password for user '{username}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Authentication error for user '{username}': {str(e)}")
            return None
    
    def create_user(self, username: str, password: str) -> Optional[User]:
        """
        Create a new user account
        
        Args:
            username: Desired username
            password: Plain text password
            
        Returns:
            User object if creation successful, None otherwise
        """
        try:
            # Check if username already exists
            existing = self.supabase.table('users').select('id').eq('username', username).execute()
            if existing.data:
                self.logger.warning(f"User creation failed: username '{username}' already exists")
                return None
            
            # Create new user
            password_hash = generate_password_hash(password)
            user = User.create_new(username, password_hash)
            
            # Insert into database
            response = self.supabase.table('users').insert(user.to_dict()).execute()
            
            if response.data:
                self.logger.info(f"User '{username}' created successfully")
                return user
            else:
                self.logger.error(f"Failed to create user '{username}': no data returned")
                return None
                
        except Exception as e:
            self.logger.error(f"User creation error for '{username}': {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Retrieve user by ID
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User object if found, None otherwise
        """
        try:
            response = self.supabase.table('users').select('*').eq('id', user_id).execute()
            
            if response.data:
                return User.from_dict(response.data[0])
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error retrieving user {user_id}: {str(e)}")
            return None
    
    def _update_last_login(self, user_id: str, last_login) -> None:
        """Update user's last login timestamp in database"""
        try:
            self.supabase.table('users').update({
                'last_login': last_login.isoformat()
            }).eq('id', user_id).execute()
        except Exception as e:
            self.logger.error(f"Failed to update last login for user {user_id}: {str(e)}")
    
    def validate_session(self, user_id: str) -> bool:
        """
        Validate if user session is still valid
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            user = self.get_user_by_id(user_id)
            return user is not None
        except Exception as e:
            self.logger.error(f"Session validation error for user {user_id}: {str(e)}")
            return False