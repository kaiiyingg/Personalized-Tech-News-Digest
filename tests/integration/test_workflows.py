"""
Integration tests for the Flask application

Tests end-to-end functionality including:
- Complete user workflows (register -> login -> browse -> favorite)
- Database integration
- Service layer integration
- Cross-feature interactions
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.app import app
from src.services import user_service, content_service, source_service


class TestIntegrationFlows:
    """Integration tests for complete user workflows"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    @patch('src.app.user_service.create_user')
    @patch('src.app.user_service.check_email_exists')
    @patch('src.app.user_service.check_username_exists')
    def test_user_registration_flow(self, mock_check_username, mock_check_email, mock_create, client):
        """Test complete user registration workflow"""
        # Setup mocks
        mock_check_email.return_value = False
        mock_check_username.return_value = False
        mock_create.return_value = 1
        
        # Test registration page access
        response = client.get('/register')
        assert response.status_code == 200
        
        # Test successful registration
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 302
        assert '/login' in response.location
        
        # Verify user service was called correctly
        mock_create.assert_called_once()

    @patch('src.app.user_service.authenticate_user')
    @patch('src.app.content_service.get_articles_by_topics')
    def test_login_to_content_flow(self, mock_get_articles, mock_auth, client):
        """Test login to content browsing workflow"""
        # Setup mocks
        mock_auth.return_value = 1
        mock_get_articles.return_value = {
            'fast_view': [{'id': 1, 'title': 'Test Article'}],
            'topics': {'AI & ML': [{'id': 2, 'title': 'AI Article'}]}
        }
        
        # Test login
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'TechPulse' in response.data
        
        # Verify we can access content after login
        with client.session_transaction() as sess:
            assert sess.get('user_id') == 1

    @patch('src.app.content_service.update_content_liked')
    @patch('src.app.content_service.get_user_favorites')
    def test_like_to_favorites_flow(self, mock_get_favorites, mock_update, client):
        """Test liking content and viewing in favorites"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock services
        mock_update.return_value = True
        mock_get_favorites.return_value = [
            {'id': 1, 'title': 'Liked Article', 'summary': 'Test summary'}
        ]
        
        # Like an article
        response = client.post('/api/content/1/like')
        assert response.status_code == 200
        
        # View favorites
        response = client.get('/favorites')
        assert response.status_code == 200
        assert b'favorites' in response.data.lower()
        
        # Verify services were called
        mock_update.assert_called_once_with(1, 1, True)
        mock_get_favorites.assert_called_once_with(1)

    @patch('src.app.content_service.update_content_liked')
    @patch('src.app.content_service.get_user_favorites')
    def test_unlike_from_favorites_flow(self, mock_get_favorites, mock_update, client):
        """Test unliking content from favorites page"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock services
        mock_update.return_value = True
        mock_get_favorites.return_value = []  # Empty after unlike
        
        # Unlike an article
        response = client.post('/api/content/1/unlike')
        assert response.status_code == 200
        
        # Verify favorites is now empty
        response = client.get('/favorites')
        assert response.status_code == 200
        
        # Verify services were called
        mock_update.assert_called_once_with(1, 1, False)

    @patch('src.app.user_service.update_user_topics')
    @patch('src.app.user_service.get_user_topics')
    @patch('src.app.content_service.get_articles_by_topics')
    def test_interests_to_content_flow(self, mock_get_articles, mock_get_topics, mock_update_topics, client):
        """Test updating interests and seeing personalized content"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock services
        mock_get_topics.return_value = ['AI & ML']
        mock_update_topics.return_value = True
        mock_get_articles.return_value = {
            'fast_view': [],
            'topics': {
                'AI & ML': [{'id': 1, 'title': 'AI Article'}],
                'Cybersecurity & Privacy': [{'id': 2, 'title': 'Security Article'}]
            }
        }
        
        # Update interests
        response = client.post('/manage_interests', data={
            'topics': ['AI & ML', 'Cybersecurity & Privacy']
        })
        assert response.status_code == 302
        
        # View personalized content
        response = client.get('/index')
        assert response.status_code == 200
        
        # Verify services were called
        mock_update_topics.assert_called_once()
        mock_get_articles.assert_called_once()

    @patch('src.app.user_service.update_user_profile')
    @patch('src.app.user_service.get_user_by_id')
    def test_profile_update_flow(self, mock_get_user, mock_update, client):
        """Test profile viewing and updating workflow"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock services
        original_user = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        mock_get_user.return_value = original_user
        mock_update.return_value = True
        
        # View profile
        response = client.get('/profile')
        assert response.status_code == 200
        assert b'profile' in response.data.lower()
        
        # Update profile
        response = client.post('/profile', data={
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'User'
        })
        assert response.status_code == 302
        
        # Verify services were called
        mock_get_user.assert_called_once()
        mock_update.assert_called_once()

    @patch('src.app.content_service.get_articles_by_topics')
    def test_fast_view_workflow(self, mock_get_articles, client):
        """Test fast view functionality"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock service
        mock_get_articles.return_value = {
            'fast_view': [
                {'id': 1, 'title': 'Quick Article 1', 'summary': 'Summary 1'},
                {'id': 2, 'title': 'Quick Article 2', 'summary': 'Summary 2'}
            ],
            'topics': {}
        }
        
        # Access fast view
        response = client.get('/fast')
        assert response.status_code == 200
        assert b'fast' in response.data.lower()
        
        # Verify content is displayed
        assert b'Quick Article' in response.data

    @patch('src.app.content_service.update_content_read')
    def test_read_article_workflow(self, mock_update_read, client):
        """Test reading article workflow"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock service
        mock_update_read.return_value = True
        
        # Mark article as read via API
        response = client.post('/api/content/1/read')
        assert response.status_code == 200
        
        # Verify service was called
        mock_update_read.assert_called_once_with(1, 1, True)

    @patch('src.app.source_service.get_all_sources')
    def test_sources_api_workflow(self, mock_get_sources, client):
        """Test sources API workflow"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock service
        mock_get_sources.return_value = [
            {'id': 1, 'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'},
            {'id': 2, 'name': 'Ars Technica', 'url': 'https://arstechnica.com/feed/'}
        ]
        
        # Get sources via API
        response = client.get('/api/sources')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 2
        assert data[0]['name'] == 'TechCrunch'

    def test_session_persistence_across_requests(self, client):
        """Test session persistence across multiple requests"""
        # Login and establish session
        with patch('src.app.user_service.authenticate_user') as mock_auth:
            mock_auth.return_value = 1
            
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            assert response.status_code == 302
        
        # Make multiple requests to verify session persists
        with patch('src.app.content_service.get_articles_by_topics') as mock_get_articles:
            mock_get_articles.return_value = {'fast_view': [], 'topics': {}}
            
            # First request
            response = client.get('/index')
            assert response.status_code == 200
            
            # Second request
            response = client.get('/fast')
            assert response.status_code == 200
            
            # Third request
            response = client.get('/favorites')
            assert response.status_code == 200

    def test_logout_clears_session(self, client):
        """Test that logout properly clears session"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Logout
        response = client.get('/logout')
        assert response.status_code == 302
        assert '/login' in response.location
        
        # Verify session is cleared
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
            assert 'username' not in sess
        
        # Verify can't access protected routes
        response = client.get('/index')
        assert response.status_code == 302
        assert '/login' in response.location

    @patch('src.app.user_service.authenticate_user')
    def test_failed_login_workflow(self, mock_auth, client):
        """Test failed login workflow"""
        mock_auth.return_value = None
        
        # Attempt login with wrong credentials
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid' in response.data
        
        # Verify no session is created
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
        
        # Verify still can't access protected routes
        response = client.get('/index')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_unauthenticated_api_access(self, client):
        """Test unauthenticated API access is properly blocked"""
        api_endpoints = [
            '/api/content/1/like',
            '/api/content/1/unlike',
            '/api/content/1/read',
            '/api/sources',
            '/api/digest',
            '/api/fast_articles'
        ]
        
        for endpoint in api_endpoints:
            if endpoint.endswith('/like') or endpoint.endswith('/unlike') or endpoint.endswith('/read'):
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == 401

    @patch('src.app.content_service.get_general_digest')
    def test_digest_api_workflow(self, mock_get_digest, client):
        """Test digest API workflow"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        # Mock service
        mock_get_digest.return_value = [
            {'id': 1, 'title': 'Digest Article 1'},
            {'id': 2, 'title': 'Digest Article 2'}
        ]
        
        # Get digest via API
        response = client.get('/api/digest')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 2
        assert 'Digest Article' in data[0]['title']

    def test_error_handling_workflow(self, client):
        """Test error handling across the application"""
        # Test 404 error
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        
        # Test invalid content ID in API
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        with patch('src.app.content_service.update_content_liked') as mock_update:
            mock_update.return_value = False
            
            response = client.post('/api/content/999/like')
            assert response.status_code == 400

    @patch('src.app.user_service.check_email_exists')
    def test_duplicate_registration_workflow(self, mock_check_email, client):
        """Test duplicate registration handling"""
        mock_check_email.return_value = True
        
        # Attempt to register with existing email
        response = client.post('/register', data={
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 200
        assert b'already exists' in response.data

    def test_content_interaction_workflow(self, client):
        """Test complete content interaction workflow"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        with patch('src.app.content_service.update_content_liked') as mock_like, \
             patch('src.app.content_service.update_content_read') as mock_read:
            
            mock_like.return_value = True
            mock_read.return_value = True
            
            # Like article
            response = client.post('/api/content/1/like')
            assert response.status_code == 200
            
            # Mark as read
            response = client.post('/api/content/1/read')
            assert response.status_code == 200
            
            # Unlike article
            response = client.post('/api/content/1/unlike')
            assert response.status_code == 200
            
            # Verify all services were called
            assert mock_like.call_count == 2  # like and unlike
            mock_read.assert_called_once()

    def test_navigation_workflow(self, client):
        """Test navigation between different pages"""
        # Setup authenticated session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        
        with patch('src.app.content_service.get_articles_by_topics') as mock_articles, \
             patch('src.app.content_service.get_user_favorites') as mock_favorites, \
             patch('src.app.user_service.get_user_by_id') as mock_user:
            
            # Setup mocks
            mock_articles.return_value = {'fast_view': [], 'topics': {}}
            mock_favorites.return_value = []
            mock_user.return_value = {'id': 1, 'username': 'testuser'}
            
            # Navigate through all main pages
            pages = ['/index', '/fast', '/favorites', '/profile']
            
            for page in pages:
                response = client.get(page)
                assert response.status_code == 200
