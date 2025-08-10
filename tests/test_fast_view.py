import pytest
from unittest.mock import Mock, patch
from src.app import app


class TestFastView:
    """Test cases for the fast view interface"""
    
    def setup_method(self):
        """Setup test fixtures"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.app_context.pop()
    
    def test_fast_view_loads(self):
        """Test that fast view page loads"""
        with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
            mock_articles.return_value = [
                {
                    'id': 1,
                    'title': 'Test Article',
                    'summary': 'Test summary',
                    'url': 'https://example.com/article1',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                }
            ]
            
            response = self.client.get('/fast')
            
            assert response.status_code == 200
            assert b'Test Article' in response.data
    
    def test_fast_view_pagination(self):
        """Test fast view pagination"""
        with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
            # Mock 50 articles for pagination testing
            mock_articles.return_value = [
                {
                    'id': i,
                    'title': f'Article {i}',
                    'summary': f'Summary {i}',
                    'url': f'https://example.com/article{i}',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                } for i in range(1, 51)
            ]
            
            response = self.client.get('/fast?page=2')
            
            assert response.status_code == 200
            # Should show articles 21-40 on page 2
            assert b'Article 21' in response.data
    
    def test_fast_view_heart_button_functionality(self):
        """Test heart button for favorites"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            
        with patch('src.services.content_service.ContentService.add_to_favorites') as mock_favorite:
            mock_favorite.return_value = True
            
            response = self.client.post('/api/favorites/add', 
                                      json={'article_id': 1})
            
            assert response.status_code == 200
            mock_favorite.assert_called_with(1, 1)
    
    def test_fast_view_article_navigation(self):
        """Test navigation between articles in fast view"""
        with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
            mock_articles.return_value = [
                {
                    'id': 1,
                    'title': 'First Article',
                    'summary': 'First summary',
                    'url': 'https://example.com/article1',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                },
                {
                    'id': 2,
                    'title': 'Second Article', 
                    'summary': 'Second summary',
                    'url': 'https://example.com/article2',
                    'published_date': '2024-01-02',
                    'source_name': 'Test Source'
                }
            ]
            
            response = self.client.get('/fast')
            
            assert response.status_code == 200
            assert b'First Article' in response.data
            assert b'Second Article' in response.data
    
    def test_fast_view_without_articles(self):
        """Test fast view when no articles available"""
        with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
            mock_articles.return_value = []
            
            response = self.client.get('/fast')
            
            assert response.status_code == 200
            assert b'No articles' in response.data or b'no articles' in response.data
