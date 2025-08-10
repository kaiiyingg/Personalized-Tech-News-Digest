import pytest
from unittest.mock import Mock, patch
from src.services.user_service import UserService
from src.models.user import User


class TestUserService:
    """Test cases for user service functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.user_service = UserService()
    
    def test_create_user_success(self):
        """Test successful user creation"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            result = self.user_service.create_user(
                username="testuser",
                email="test@example.com",
                password="testpass123"
            )
            
            assert result is not None
            mock_cursor.execute.assert_called()
    
    def test_authenticate_user_valid(self):
        """Test user authentication with valid credentials"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = {
                'id': 1,
                'username': 'testuser',
                'password_hash': 'hashed_password'
            }
            mock_db.return_value.cursor.return_value = mock_cursor
            
            with patch('bcrypt.checkpw', return_value=True):
                result = self.user_service.authenticate_user("testuser", "testpass123")
                
                assert result is not None
                assert result['username'] == 'testuser'
    
    def test_authenticate_user_invalid(self):
        """Test user authentication with invalid credentials"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = None
            mock_db.return_value.cursor.return_value = mock_cursor
            
            result = self.user_service.authenticate_user("wronguser", "wrongpass")
            
            assert result is None
    
    def test_get_user_by_id(self):
        """Test retrieving user by ID"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchone.return_value = {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com'
            }
            mock_db.return_value.cursor.return_value = mock_cursor
            
            result = self.user_service.get_user_by_id(1)
            
            assert result is not None
            assert result['username'] == 'testuser'
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            result = self.user_service.update_user_profile(
                user_id=1,
                email="newemail@example.com"
            )
            
            assert result is True
            mock_cursor.execute.assert_called()
