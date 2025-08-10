"""
Comprehensive tests for user_service.py

Tests all functions in the user service including:
- User registration and authentication
- Password management and security
- TOTP two-factor authentication
- User preferences and topics
- Profile management
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import bcrypt
import pyotp

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.services import user_service


class TestUserService:
    """Test class for user service functions"""

    def setup_method(self):
        """Setup test data for each test method"""
        self.sample_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.sample_user_id = 1

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_create_user_success(self, mock_close_conn, mock_get_conn):
        """Test successful user creation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [self.sample_user_id]
        
        with patch('bcrypt.hashpw') as mock_hash:
            mock_hash.return_value = b'hashed_password'
            result = user_service.create_user(**self.sample_user_data)
            
        assert result == self.sample_user_id
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_create_user_duplicate_email(self, mock_close_conn, mock_get_conn):
        """Test user creation with duplicate email"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate unique violation
        from psycopg2 import errors as pg_errors
        mock_cursor.execute.side_effect = pg_errors.UniqueViolation("duplicate email")
        
        with patch('bcrypt.hashpw') as mock_hash:
            mock_hash.return_value = b'hashed_password'
            result = user_service.create_user(**self.sample_user_data)
            
        assert result is None
        mock_conn.rollback.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_authenticate_user_success(self, mock_close_conn, mock_get_conn):
        """Test successful user authentication"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        hashed_password = bcrypt.hashpw('TestPassword123!'.encode('utf-8'), bcrypt.gensalt())
        mock_cursor.fetchone.return_value = (self.sample_user_id, hashed_password)
        
        result = user_service.authenticate_user('test@example.com', 'TestPassword123!')
        
        assert result == self.sample_user_id
        mock_cursor.execute.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_authenticate_user_wrong_password(self, mock_close_conn, mock_get_conn):
        """Test authentication with wrong password"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        hashed_password = bcrypt.hashpw('DifferentPassword'.encode('utf-8'), bcrypt.gensalt())
        mock_cursor.fetchone.return_value = (self.sample_user_id, hashed_password)
        
        result = user_service.authenticate_user('test@example.com', 'WrongPassword')
        
        assert result is None

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_authenticate_user_not_found(self, mock_close_conn, mock_get_conn):
        """Test authentication with non-existent user"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        result = user_service.authenticate_user('nonexistent@example.com', 'password')
        
        assert result is None

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_get_user_by_id_success(self, mock_close_conn, mock_get_conn):
        """Test retrieving user by ID"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = (
            self.sample_user_id, 'testuser', 'test@example.com', 
            'Test', 'User', datetime.now(), None
        )
        
        user = user_service.get_user_by_id(self.sample_user_id)
        
        assert user is not None
        assert user['id'] == self.sample_user_id
        assert user['username'] == 'testuser'
        assert user['email'] == 'test@example.com'

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_get_user_by_id_not_found(self, mock_close_conn, mock_get_conn):
        """Test retrieving non-existent user by ID"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        user = user_service.get_user_by_id(999)
        
        assert user is None

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_update_user_password_success(self, mock_close_conn, mock_get_conn):
        """Test successful password update"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('bcrypt.hashpw') as mock_hash:
            mock_hash.return_value = b'new_hashed_password'
            result = user_service.update_user_password(
                self.sample_user_id, 'NewPassword123!'
            )
            
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_update_user_email_success(self, mock_close_conn, mock_get_conn):
        """Test successful email update"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = user_service.update_user_email(
            self.sample_user_id, 'newemail@example.com'
        )
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_update_user_profile_success(self, mock_close_conn, mock_get_conn):
        """Test successful profile update"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = user_service.update_user_profile(
            self.sample_user_id, 
            username='newusername',
            first_name='NewFirst',
            last_name='NewLast'
        )
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_setup_totp_secret(self, mock_close_conn, mock_get_conn):
        """Test TOTP secret setup"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('pyotp.random_base32') as mock_random:
            mock_random.return_value = 'TESTSECRET123456'
            secret = user_service.setup_totp_secret(self.sample_user_id)
            
        assert secret == 'TESTSECRET123456'
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_verify_totp_success(self, mock_close_conn, mock_get_conn):
        """Test successful TOTP verification"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = ['TESTSECRET123456']
        
        with patch('pyotp.TOTP') as mock_totp_class:
            mock_totp = Mock()
            mock_totp.verify.return_value = True
            mock_totp_class.return_value = mock_totp
            
            result = user_service.verify_totp(self.sample_user_id, '123456')
            
        assert result is True

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_verify_totp_failure(self, mock_close_conn, mock_get_conn):
        """Test failed TOTP verification"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = ['TESTSECRET123456']
        
        with patch('pyotp.TOTP') as mock_totp_class:
            mock_totp = Mock()
            mock_totp.verify.return_value = False
            mock_totp_class.return_value = mock_totp
            
            result = user_service.verify_totp(self.sample_user_id, '000000')
            
        assert result is False

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_get_user_topics_success(self, mock_close_conn, mock_get_conn):
        """Test retrieving user topics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            ('AI & ML',), 
            ('Cybersecurity & Privacy',),
            ('Cloud Computing & DevOps',)
        ]
        
        topics = user_service.get_user_topics(self.sample_user_id)
        
        assert len(topics) == 3
        assert 'AI & ML' in topics
        assert 'Cybersecurity & Privacy' in topics

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_update_user_topics_success(self, mock_close_conn, mock_get_conn):
        """Test updating user topics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        new_topics = ['AI & ML', 'Data Science & Analytics']
        
        result = user_service.update_user_topics(self.sample_user_id, new_topics)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_check_email_exists_true(self, mock_close_conn, mock_get_conn):
        """Test checking if email exists (returns True)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]
        
        exists = user_service.check_email_exists('test@example.com')
        
        assert exists is True

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_check_email_exists_false(self, mock_close_conn, mock_get_conn):
        """Test checking if email exists (returns False)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        exists = user_service.check_email_exists('nonexistent@example.com')
        
        assert exists is False

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_check_username_exists_true(self, mock_close_conn, mock_get_conn):
        """Test checking if username exists (returns True)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]
        
        exists = user_service.check_username_exists('testuser')
        
        assert exists is True

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_check_username_exists_false(self, mock_close_conn, mock_get_conn):
        """Test checking if username exists (returns False)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        exists = user_service.check_username_exists('nonexistentuser')
        
        assert exists is False

    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password"""
        valid_passwords = [
            'TestPassword123!',
            'MySecure@Pass456',
            'Complex$Password789'
        ]
        
        for password in valid_passwords:
            is_valid, message = user_service.validate_password_strength(password)
            assert is_valid is True
            assert message == "Password is strong"

    def test_validate_password_strength_too_short(self):
        """Test password strength validation with short password"""
        is_valid, message = user_service.validate_password_strength('Short1!')
        assert is_valid is False
        assert "at least 8 characters" in message

    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase"""
        is_valid, message = user_service.validate_password_strength('lowercase123!')
        assert is_valid is False
        assert "uppercase letter" in message

    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation without lowercase"""
        is_valid, message = user_service.validate_password_strength('UPPERCASE123!')
        assert is_valid is False
        assert "lowercase letter" in message

    def test_validate_password_strength_no_digit(self):
        """Test password strength validation without digit"""
        is_valid, message = user_service.validate_password_strength('Password!')
        assert is_valid is False
        assert "digit" in message

    def test_validate_password_strength_no_special(self):
        """Test password strength validation without special character"""
        is_valid, message = user_service.validate_password_strength('Password123')
        assert is_valid is False
        assert "special character" in message

    def test_validate_email_format_valid(self):
        """Test email format validation with valid emails"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'firstname+lastname@company.org'
        ]
        
        for email in valid_emails:
            assert user_service.validate_email_format(email) is True

    def test_validate_email_format_invalid(self):
        """Test email format validation with invalid emails"""
        invalid_emails = [
            'invalid.email',
            '@domain.com',
            'user@',
            'user name@domain.com',
            'user@domain'
        ]
        
        for email in invalid_emails:
            assert user_service.validate_email_format(email) is False

    def test_sanitize_input(self):
        """Test input sanitization"""
        dirty_input = "<script>alert('xss')</script>Hello World"
        clean_input = user_service.sanitize_input(dirty_input)
        
        assert '<script>' not in clean_input
        assert 'Hello World' in clean_input

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_delete_user_success(self, mock_close_conn, mock_get_conn):
        """Test successful user deletion"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = user_service.delete_user(self.sample_user_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.user_service.get_db_connection')
    @patch('src.services.user_service.close_db_connection')
    def test_get_user_statistics(self, mock_close_conn, mock_get_conn):
        """Test retrieving user statistics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock multiple fetchone calls for different stats
        mock_cursor.fetchone.side_effect = [
            [25],  # articles_read
            [10],  # articles_liked
            [datetime.now()]  # last_activity
        ]
        
        stats = user_service.get_user_statistics(self.sample_user_id)
        
        assert 'articles_read' in stats
        assert 'articles_liked' in stats
        assert 'last_activity' in stats
        assert stats['articles_read'] == 25
        assert stats['articles_liked'] == 10
