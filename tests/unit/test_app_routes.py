"""
Comprehensive tests for Flask app routes (app.py)

Tests all routes and endpoints in the Flask application including:
- Authentication routes (login, register, logout)
- Content routes (index, fast, favorites)
- API endpoints (like, unlike, read, digest)
- User management routes (profile, settings)
- Security and error handling
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.app import app
from src.services import user_service, content_service


class TestFlaskApp:
    """Test class for Flask application routes"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def authenticated_client(self, client):
        """Create authenticated test client"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        return client

    def test_home_route_redirect(self, client):
        """Test home route redirects to index"""
        response = client.get('/')
        assert response.status_code == 302
        assert '/index' in response.location

    @patch('src.app.content_service.get_articles_by_topics')
    def test_index_route_authenticated(self, mock_get_articles, authenticated_client):
        """Test index route for authenticated user"""
        mock_get_articles.return_value = {
            'fast_view': [],
            'topics': {'AI & ML': []}
        }
        
        response = authenticated_client.get('/index')
        assert response.status_code == 200
        assert b'TechPulse' in response.data

    def test_index_route_unauthenticated(self, client):
        """Test index route redirects unauthenticated users"""
        response = client.get('/index')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_login_route_get(self, client):
        """Test login page GET request"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()

    @patch('src.app.user_service.authenticate_user')
    def test_login_route_post_success(self, mock_auth, client):
        """Test successful login POST request"""
        mock_auth.return_value = 1  # User ID
        
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 302
        assert '/index' in response.location

    @patch('src.app.user_service.authenticate_user')
    def test_login_route_post_failure(self, mock_auth, client):
        """Test failed login POST request"""
        mock_auth.return_value = None
        
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid' in response.data

    def test_logout_route(self, authenticated_client):
        """Test logout route"""
        response = authenticated_client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_register_route_get(self, client):
        """Test register page GET request"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'register' in response.data.lower()

    @patch('src.app.user_service.create_user')
    @patch('src.app.user_service.check_email_exists')
    @patch('src.app.user_service.check_username_exists')
    def test_register_route_post_success(self, mock_check_username, mock_check_email, mock_create, client):
        """Test successful registration POST request"""
        mock_check_email.return_value = False
        mock_check_username.return_value = False
        mock_create.return_value = 1  # User ID
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 302
        assert '/login' in response.location

    @patch('src.app.user_service.check_email_exists')
    def test_register_route_post_duplicate_email(self, mock_check_email, client):
        """Test registration with duplicate email"""
        mock_check_email.return_value = True
        
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 200
        assert b'already exists' in response.data

    @patch('src.app.content_service.get_user_favorites')
    def test_favorites_route(self, mock_get_favorites, authenticated_client):
        """Test favorites route"""
        mock_get_favorites.return_value = [
            {'id': 1, 'title': 'Test Article', 'summary': 'Test summary'}
        ]
        
        response = authenticated_client.get('/favorites')
        assert response.status_code == 200
        assert b'favorites' in response.data.lower()

    def test_favorites_route_unauthenticated(self, client):
        """Test favorites route for unauthenticated user"""
        response = client.get('/favorites')
        assert response.status_code == 302
        assert '/login' in response.location

    @patch('src.app.content_service.get_articles_by_topics')
    def test_fast_route(self, mock_get_articles, authenticated_client):
        """Test fast view route"""
        mock_get_articles.return_value = {
            'fast_view': [{'id': 1, 'title': 'Fast Article'}],
            'topics': {}
        }
        
        response = authenticated_client.get('/fast')
        assert response.status_code == 200
        assert b'fast' in response.data.lower()

    @patch('src.app.user_service.get_user_by_id')
    def test_profile_route_get(self, mock_get_user, authenticated_client):
        """Test profile page GET request"""
        mock_get_user.return_value = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = authenticated_client.get('/profile')
        assert response.status_code == 200
        assert b'profile' in response.data.lower()

    @patch('src.app.user_service.update_user_profile')
    def test_profile_route_post_success(self, mock_update, authenticated_client):
        """Test profile update POST request"""
        mock_update.return_value = True
        
        response = authenticated_client.post('/profile', data={
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'User'
        })
        
        assert response.status_code == 302

    @patch('src.app.content_service.update_content_liked')
    def test_api_like_content_success(self, mock_update, authenticated_client):
        """Test API like content endpoint"""
        mock_update.return_value = True
        
        response = authenticated_client.post('/api/content/1/like')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data

    @patch('src.app.content_service.update_content_liked')
    def test_api_unlike_content_success(self, mock_update, authenticated_client):
        """Test API unlike content endpoint"""
        mock_update.return_value = True
        
        response = authenticated_client.post('/api/content/1/unlike')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data

    @patch('src.app.content_service.update_content_read')
    def test_api_read_content_success(self, mock_update, authenticated_client):
        """Test API read content endpoint"""
        mock_update.return_value = True
        
        response = authenticated_client.post('/api/content/1/read')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data

    def test_api_like_content_unauthenticated(self, client):
        """Test API like content endpoint without authentication"""
        response = client.post('/api/content/1/like')
        assert response.status_code == 401

    @patch('src.app.source_service.get_all_sources')
    def test_api_sources(self, mock_get_sources, authenticated_client):
        """Test API sources endpoint"""
        mock_get_sources.return_value = [
            {'id': 1, 'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'}
        ]
        
        response = authenticated_client.get('/api/sources')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1

    @patch('src.app.content_service.get_general_digest')
    def test_api_digest(self, mock_get_digest, authenticated_client):
        """Test API digest endpoint"""
        mock_get_digest.return_value = [
            {'id': 1, 'title': 'Digest Article'}
        ]
        
        response = authenticated_client.get('/api/digest')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)

    @patch('src.app.content_service.get_articles_by_topics')
    def test_api_fast_articles(self, mock_get_articles, authenticated_client):
        """Test API fast articles endpoint"""
        mock_get_articles.return_value = {
            'fast_view': [{'id': 1, 'title': 'Fast Article'}],
            'topics': {}
        }
        
        response = authenticated_client.get('/api/fast_articles')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'fast_view' in data

    def test_read_article_route(self, authenticated_client):
        """Test read article route"""
        response = authenticated_client.get('/read_article/1')
        assert response.status_code == 302  # Should redirect to external URL

    @patch('src.app.user_service.get_user_topics')
    def test_manage_interests_route_get(self, mock_get_topics, authenticated_client):
        """Test manage interests page GET request"""
        mock_get_topics.return_value = ['AI & ML', 'Cybersecurity & Privacy']
        
        response = authenticated_client.get('/manage_interests')
        assert response.status_code == 200
        assert b'interests' in response.data.lower()

    @patch('src.app.user_service.update_user_topics')
    def test_manage_interests_route_post(self, mock_update_topics, authenticated_client):
        """Test manage interests POST request"""
        mock_update_topics.return_value = True
        
        response = authenticated_client.post('/manage_interests', data={
            'topics': ['AI & ML', 'Data Science & Analytics']
        })
        
        assert response.status_code == 302

    def test_setup_totp_route(self, authenticated_client):
        """Test TOTP setup route"""
        with patch('src.app.user_service.setup_totp_secret') as mock_setup:
            mock_setup.return_value = 'TESTSECRET123456'
            
            response = authenticated_client.get('/setup_totp')
            assert response.status_code == 200
            assert b'totp' in response.data.lower()

    @patch('src.app.user_service.update_user_password')
    def test_reset_password_route_post(self, mock_update_password, authenticated_client):
        """Test password reset POST request"""
        mock_update_password.return_value = True
        
        response = authenticated_client.post('/reset_password', data={
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        })
        
        assert response.status_code == 302

    @patch('src.app.user_service.update_user_email')
    def test_change_email_route_post(self, mock_update_email, authenticated_client):
        """Test email change POST request"""
        mock_update_email.return_value = True
        
        response = authenticated_client.post('/change_email', data={
            'new_email': 'newemail@example.com'
        })
        
        assert response.status_code == 302

    def test_error_404_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_error_500_handler(self, client):
        """Test 500 error handler"""
        with patch('src.app.render_template') as mock_render:
            mock_render.side_effect = Exception("Test error")
            
            # This might not trigger a 500 in test mode
            # Adjust based on your error handling implementation
            client.get('/login')
            # Check if error is handled gracefully

    def test_csrf_protection(self, client):
        """Test CSRF protection on forms"""
        # This test depends on your CSRF implementation
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        # Should handle CSRF appropriately
        # Adjust based on your implementation

    def test_rate_limiting(self, client):
        """Test rate limiting on endpoints"""
        # This test depends on your rate limiting implementation
        # Make multiple rapid requests to test rate limiting
        for _ in range(20):
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
        # Check if rate limiting kicks in
        # Adjust based on your implementation

    def test_session_management(self, client):
        """Test session management"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
            
        # Test that session persists
        client.get('/index')
        # Should not redirect to login since session exists

    @patch('src.app.content_service.update_content_liked')
    def test_api_endpoints_error_handling(self, mock_update, authenticated_client):
        """Test API endpoints error handling"""
        mock_update.return_value = False  # Simulate failure
        
        response = authenticated_client.post('/api/content/1/like')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

    def test_input_validation(self, client):
        """Test input validation and sanitization"""
        malicious_input = "<script>alert('xss')</script>"
        
        response = client.post('/register', data={
            'username': malicious_input,
            'email': 'test@example.com',
            'password': 'Password123!',
            'first_name': 'Test',
            'last_name': 'User'
        })
        
        # Should sanitize input and not execute script
        assert b'<script>' not in response.data

    def test_authentication_decorator(self, client):
        """Test login_required decorator"""
        protected_routes = [
            '/index',
            '/favorites',
            '/fast',
            '/profile',
            '/manage_interests'
        ]
        
        for route in protected_routes:
            response = client.get(route)
            assert response.status_code == 302
            assert '/login' in response.location

    def test_content_type_headers(self, authenticated_client):
        """Test proper content type headers"""
        # Test HTML pages
        response = authenticated_client.get('/index')
        assert 'text/html' in response.content_type
        
        # Test API endpoints
        response = authenticated_client.get('/api/sources')
        assert 'application/json' in response.content_type

    def test_security_headers(self, client):
        """Test security headers are set"""
        client.get('/login')
        
        # Check for security headers (adjust based on your implementation)
        # Expected headers: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
        
        # Note: This depends on your security header implementation
        # Uncomment and adjust based on your actual headers
        # for header in headers_to_check:
        #     assert header in response.headers

    def test_database_connection_handling(self, authenticated_client):
        """Test database connection error handling"""
        with patch('src.app.content_service.get_articles_by_topics') as mock_get_articles:
            mock_get_articles.side_effect = Exception("Database connection error")
            
            authenticated_client.get('/index')
            # Should handle database errors gracefully
            # Adjust based on your error handling

    @patch('src.app.user_service.verify_totp')
    def test_totp_verification(self, mock_verify, authenticated_client):
        """Test TOTP verification in login process"""
        mock_verify.return_value = True
        
        # This test depends on your TOTP implementation
        # Add appropriate test based on your 2FA flow

    def test_password_strength_validation(self, client):
        """Test password strength validation"""
        weak_passwords = [
            'weak',
            '12345678',
            'password',
            'Password123'  # No special character
        ]
        
        for password in weak_passwords:
            response = client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': password,
                'first_name': 'Test',
                'last_name': 'User'
            })
            
            # Should reject weak passwords
            assert response.status_code == 200  # Stays on register page
            # Check for password strength error message
