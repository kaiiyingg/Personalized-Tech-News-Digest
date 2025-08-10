import pytest
from unittest.mock import Mock, patch
import time
from src.app import app
from src.services.content_service import ContentService


class TestPerformanceImprovements:
    """Test cases for performance improvements and optimizations"""
    
    def setup_method(self):
        """Setup test fixtures"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
    
    def teardown_method(self):
        """Cleanup after tests"""
        self.app_context.pop()
    
    def test_page_load_performance(self):
        """Test that pages load within acceptable time"""
        with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
            mock_articles.return_value = [
                {
                    'id': i,
                    'title': f'Article {i}',
                    'summary': f'Summary {i}',
                    'url': f'https://example.com/article{i}',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                } for i in range(1, 21)  # 20 articles
            ]
            
            start_time = time.time()
            response = self.client.get('/')
            end_time = time.time()
            
            load_time = end_time - start_time
            
            assert response.status_code == 200
            assert load_time < 2.0  # Should load in under 2 seconds
    
    def test_database_query_optimization(self):
        """Test that database queries are optimized"""
        content_service = ContentService()
        
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [
                {
                    'id': 1,
                    'title': 'Test Article',
                    'summary': 'Test summary',
                    'content': 'Full content',
                    'url': 'https://example.com/article1',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                }
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            
            start_time = time.time()
            articles = content_service.get_latest_articles(limit=20)
            end_time = time.time()
            
            query_time = end_time - start_time
            
            assert len(articles) == 1
            assert query_time < 0.5  # Query should complete in under 500ms
            
            # Check that query was called only once (no N+1 problem)
            assert mock_cursor.execute.call_count <= 2
    
    def test_caching_effectiveness(self):
        """Test that caching improves performance"""
        with patch('src.utils.cache.cache_manager') as mock_cache:
            # First call - cache miss
            mock_cache.get.return_value = None
            mock_cache.set.return_value = True
            
            with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
                mock_articles.return_value = [{'id': 1, 'title': 'Test'}]
                
                # First request
                response1 = self.client.get('/')
                
                # Second call - cache hit
                mock_cache.get.return_value = [{'id': 1, 'title': 'Test'}]
                
                # Second request
                response2 = self.client.get('/')
                
                assert response1.status_code == 200
                assert response2.status_code == 200
                
                # Should have called cache.set on first request
                mock_cache.set.assert_called()
    
    def test_fast_view_performance(self):
        """Test fast view loads quickly with many articles"""
        with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
            # Mock 100 articles to test performance with larger dataset
            mock_articles.return_value = [
                {
                    'id': i,
                    'title': f'Article {i}',
                    'summary': f'Summary {i}',
                    'url': f'https://example.com/article{i}',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                } for i in range(1, 101)
            ]
            
            start_time = time.time()
            response = self.client.get('/fast')
            end_time = time.time()
            
            load_time = end_time - start_time
            
            assert response.status_code == 200
            assert load_time < 3.0  # Should load 100 articles in under 3 seconds
    
    def test_memory_usage_optimization(self):
        """Test that memory usage stays reasonable"""
        content_service = ContentService()
        
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            # Mock large dataset
            mock_cursor.fetchall.return_value = [
                {
                    'id': i,
                    'title': f'Article {i}',
                    'summary': f'Summary {i}' * 100,  # Large summaries
                    'content': f'Content {i}' * 1000,  # Large content
                    'url': f'https://example.com/article{i}',
                    'published_date': '2024-01-01',
                    'source_name': 'Test Source'
                } for i in range(1, 1001)  # 1000 articles
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # This should not cause memory issues
            articles = content_service.get_latest_articles(limit=1000)
            
            assert len(articles) == 1000
            # Test passes if no memory error occurs
    
    def test_concurrent_user_handling(self):
        """Test that app can handle multiple concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                with patch('src.services.content_service.ContentService.get_latest_articles') as mock_articles:
                    mock_articles.return_value = [{'id': 1, 'title': 'Test'}]
                    response = self.client.get('/')
                    results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Create 10 concurrent threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())
        
        assert len(status_codes) == 10
        assert all(code == 200 for code in status_codes)
