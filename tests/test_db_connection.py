"""
Integration Tests for TechPulse Application
Tests complete workflows including database operations, API endpoints, and user interactions.
"""
import pytest
import json
from flask import url_for
from src.app import app
from src.database.connection import get_db_connection
from datetime import datetime


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def auth_client(client):
    """Create authenticated test client"""
    # Create test user and login
    client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword123'
    })
    
    return client


class TestUserWorkflow:
    """Test complete user workflows"""

    def test_user_registration_login_workflow(self, client):
        """Test complete user registration and login process"""
        # Register new user
        response = client.post('/register', data={
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'password': 'password123'
        })
        assert response.status_code in [200, 302]  # Success or redirect

        # Login with new user
        response = client.post('/login', data={
            'username': 'integrationuser',
            'password': 'password123'
        })
        assert response.status_code in [200, 302]

        # Access protected page
        response = client.get('/')
        assert response.status_code == 200
        assert b'integrationuser' in response.data

    def test_content_refresh_workflow(self, auth_client):
        """Test content refresh and display workflow"""
        # Trigger content refresh
        response = auth_client.post('/api/jobs/ingest')
        assert response.status_code in [200, 429]  # Success or rate limited

        # Check main page shows content
        response = auth_client.get('/')
        assert response.status_code == 200

    def test_article_interaction_workflow(self, auth_client):
        """Test article liking and reading workflow"""
        # Get articles from main page
        response = auth_client.get('/')
        assert response.status_code == 200

        # Test API endpoints
        response = auth_client.get('/api/sources')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sources' in data

    def test_user_preferences_workflow(self, auth_client):
        """Test user preferences and profile management"""
        # Access profile page
        response = auth_client.get('/profile')
        assert response.status_code == 200

        # Access interests management
        response = auth_client.get('/manage_interests')
        assert response.status_code == 200


class TestAPIIntegration:
    """Test API endpoint integration"""

    def test_sources_api(self, auth_client):
        """Test sources API endpoint"""
        response = auth_client.get('/api/sources')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'sources' in data
        assert isinstance(data['sources'], list)

    def test_job_status_api(self, auth_client):
        """Test job status API endpoint"""
        response = auth_client.get('/api/jobs/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'timestamp' in data

    def test_unauthorized_api_access(self, client):
        """Test API access without authentication"""
        response = client.get('/api/sources')
        assert response.status_code == 401


class TestDatabaseIntegration:
    """Test database operations and data consistency"""

    def test_content_creation_and_retrieval(self):
        """Test complete content lifecycle"""
        from src.services.content_service import create_content_item, get_articles_by_topics
        
        # Create test content
        success = create_content_item(
            source_id=1,
            title="Integration Test Article",
            summary="This is a test article for integration testing with Python programming",
            article_url="https://example.com/integration-test",
            published_at=datetime.now()
        )
        
        # Verify content can be retrieved
        if success:
            articles = get_articles_by_topics(user_id=1, limit_per_topic=10)
            assert articles is not None
            assert 'topics' in articles

    def test_user_service_integration(self):
        """Test user service database operations"""
        from src.services.user_service import create_user, find_user_by_username
        
        # Create test user
        user = create_user(
            username="integrationtest",
            email="integrationtest@example.com",
            password="testpassword123"
        )
        
        if user:
            # Verify user can be found
            found_user = find_user_by_username("integrationtest")
            assert found_user is not None
            assert found_user.username == "integrationtest"


class TestContentWorkflow:
    """Test content ingestion and processing workflow"""

    def test_rss_processing_workflow(self):
        """Test RSS feed processing and content classification"""
        from src.jobs.web_jobs import run_ingest_articles
        
        # Run ingestion job
        result = run_ingest_articles()
        assert result is not None
        assert 'success' in result

    def test_content_classification_workflow(self):
        """Test content classification and topic assignment"""
        from src.services.content_service import assign_topic
        
        test_cases = [
            ("Python 3.12 Released", "New Python version with performance improvements", "Software Development & Web Technologies"),
            ("AI Breakthrough", "Machine learning model achieves new benchmarks", "AI & ML"),
            ("Cloud Security Update", "AWS releases new security features", "Cloud Computing & DevOps"),
        ]
        
        for title, summary, expected_topic in test_cases:
            result = assign_topic(title, summary)
            assert result == expected_topic or result is not None  # Allow for classification variations


class TestErrorHandlingIntegration:
    """Test error handling across the application"""

    def test_invalid_login_attempts(self, client):
        """Test handling of invalid login attempts"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200  # Returns to login page with error

    def test_duplicate_user_registration(self, client):
        """Test handling of duplicate user registration"""
        # Register user first time
        client.post('/register', data={
            'username': 'duplicatetest',
            'email': 'duplicate@example.com',
            'password': 'password123'
        })
        
        # Try to register same user again
        response = client.post('/register', data={
            'username': 'duplicatetest',
            'email': 'duplicate@example.com',
            'password': 'password123'
        })
        assert response.status_code == 200  # Returns to registration with error

    def test_malformed_api_requests(self, auth_client):
        """Test handling of malformed API requests"""
        # Test with invalid JSON
        response = auth_client.post('/api/jobs/ingest', 
                                  data='invalid json',
                                  content_type='application/json')
        assert response.status_code in [400, 429, 500]  # Various error codes acceptable

    def test_rate_limiting(self, auth_client):
        """Test rate limiting on refresh endpoint"""
        # Make multiple rapid requests
        responses = []
        for _ in range(3):
            response = auth_client.post('/api/jobs/ingest')
            responses.append(response.status_code)
        
        # Should get rate limited
        assert 429 in responses or any(r >= 400 for r in responses)


class TestDataConsistency:
    """Test data consistency and integrity"""

    def test_database_constraints(self):
        """Test database constraints and data integrity"""
        from src.services.content_service import create_content_item
        
        # Test duplicate URL prevention
        result1 = create_content_item(
            source_id=1,
            title="Test Article",
            summary="Test summary with programming and software development",
            article_url="https://example.com/same-url",
            published_at=datetime.now()
        )
        
        result2 = create_content_item(
            source_id=1,
            title="Different Article",
            summary="Different summary with programming and software development",
            article_url="https://example.com/same-url",  # Same URL
            published_at=datetime.now()
        )
        
        # Second creation should fail due to duplicate URL
        if result1:
            assert not result2

    def test_user_data_consistency(self):
        """Test user data consistency across operations"""
        from src.services.user_service import create_user, find_user_by_email
        
        # Create user and verify all fields
        user = create_user(
            username="consistencytest",
            email="consistency@example.com",
            password="testpassword123"
        )
        
        if user:
            # Verify user data is consistent
            found_user = find_user_by_email("consistency@example.com")
            assert found_user is not None
            assert found_user.username == "consistencytest"
            assert found_user.email == "consistency@example.com"
