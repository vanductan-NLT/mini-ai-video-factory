"""
Tests for authentication functionality
"""

import pytest
from unittest.mock import patch, Mock
from auth.auth_manager import AuthManager
from models.user import User


class TestAuthManager:
    """Test cases for AuthManager"""
    
    def test_authenticate_user_success(self, mock_auth_manager):
        """Test successful user authentication"""
        # Test with valid credentials
        user = mock_auth_manager.authenticate_user('testuser@example.com', 'password123')
        
        assert user is not None
        assert user.username == 'testuser@example.com'
        assert user.id == 'test-user-123'
    
    def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        with patch('auth.auth_manager.create_client') as mock_create_client:
            mock_supabase = Mock()
            mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
            mock_create_client.return_value = mock_supabase
            
            auth_manager = AuthManager()
            user = auth_manager.authenticate_user('invalid@example.com', 'wrongpassword')
            
            assert user is None
    
    def test_get_user_by_id_success(self, mock_auth_manager):
        """Test successful user retrieval by ID"""
        user = mock_auth_manager.get_user_by_id('test-user-123')
        
        assert user is not None
        assert user.id == 'test-user-123'
        assert user.username == 'testuser@example.com'
    
    def test_get_user_by_id_not_found(self):
        """Test user retrieval with invalid ID"""
        with patch('auth.auth_manager.create_client') as mock_create_client:
            mock_supabase = Mock()
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create_client.return_value = mock_supabase
            
            auth_manager = AuthManager()
            user = auth_manager.get_user_by_id('invalid-user-id')
            
            assert user is None
    
    def test_validate_session_success(self, mock_auth_manager):
        """Test successful session validation"""
        is_valid = mock_auth_manager.validate_session('test-user-123')
        assert is_valid is True
    
    def test_validate_session_failure(self):
        """Test failed session validation"""
        with patch('auth.auth_manager.create_client') as mock_create_client:
            mock_supabase = Mock()
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_create_client.return_value = mock_supabase
            
            auth_manager = AuthManager()
            is_valid = auth_manager.validate_session('invalid-session')
            
            assert is_valid is False


class TestAuthRoutes:
    """Test cases for authentication routes"""
    
    @patch('app.auth_manager')
    def test_login_get(self, mock_auth_manager, client):
        """Test GET request to login page"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    @patch('app.auth_manager')
    def test_login_post_success(self, mock_auth_manager, client, mock_user):
        """Test successful login POST request"""
        mock_auth_manager.authenticate_user.return_value = mock_user
        
        response = client.post('/login', data={
            'email': 'testuser@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        mock_auth_manager.authenticate_user.assert_called_once_with('testuser@example.com', 'password123')
    
    @patch('app.auth_manager')
    def test_login_post_failure(self, mock_auth_manager, client):
        """Test failed login POST request"""
        mock_auth_manager.authenticate_user.return_value = None
        
        response = client.post('/login', data={
            'email': 'invalid@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    @patch('app.auth_manager')
    def test_login_missing_credentials(self, mock_auth_manager, client):
        """Test login with missing credentials"""
        response = client.post('/login', data={
            'email': '',
            'password': ''
        })
        
        assert response.status_code == 200
        assert b'Please enter both email and password' in response.data
    
    def test_logout(self, client):
        """Test logout functionality"""
        with client.session_transaction() as sess:
            sess['_user_id'] = 'test-user-123'
        
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication"""
        response = client.get('/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_index_redirect(self, client):
        """Test index route redirects appropriately"""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login when not authenticated