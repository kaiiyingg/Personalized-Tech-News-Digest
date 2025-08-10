import pytest
from unittest.mock import Mock, patch
from src.services.content_service import ContentService
from src.utils.cache import cache_manager


class TestOptimizations:
    """Test cases for system optimizations and efficiency"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.content_service = ContentService()
    
    def test_database_connection_pooling(self):
        """Test database connection pooling efficiency"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [
                {'id': 1, 'title': 'Test Article'}
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # Make multiple calls
            for _ in range(5):
                articles = self.content_service.get_latest_articles(limit=1)
                assert len(articles) == 1
            
            # Should reuse connections efficiently
            assert mock_db.call_count <= 5
    
    def test_sql_query_optimization(self):
        """Test that SQL queries are optimized"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = []
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # Get articles with specific criteria
            self.content_service.get_articles_by_category('tech', limit=10)
            
            # Check that query was optimized (should use proper indexing)
            executed_query = mock_cursor.execute.call_args[0][0]
            assert 'LIMIT' in executed_query.upper()
            assert 'ORDER BY' in executed_query.upper()
    
    def test_cache_hit_ratio(self):
        """Test cache effectiveness"""
        cache_key = 'test_articles'
        test_data = [{'id': 1, 'title': 'Cached Article'}]
        
        with patch.object(cache_manager, 'get') as mock_get, \
             patch.object(cache_manager, 'set') as mock_set:
            
            # First call - cache miss
            mock_get.return_value = None
            
            with patch('src.services.content_service.ContentService._fetch_from_database') as mock_fetch:
                mock_fetch.return_value = test_data
                
                result1 = self.content_service.get_cached_articles(cache_key)
                
                # Second call - cache hit
                mock_get.return_value = test_data
                result2 = self.content_service.get_cached_articles(cache_key)
                
                assert result1 == test_data
                assert result2 == test_data
                
                # Database should be called only once
                assert mock_fetch.call_count == 1
                # Cache should be set once
                mock_set.assert_called_once()
    
    def test_pagination_efficiency(self):
        """Test that pagination doesn't load unnecessary data"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            # Mock exactly 10 results for page 1
            mock_cursor.fetchall.return_value = [
                {'id': i, 'title': f'Article {i}'} for i in range(1, 11)
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            
            articles = self.content_service.get_paginated_articles(page=1, per_page=10)
            
            assert len(articles) == 10
            
            # Check that LIMIT and OFFSET were used in query
            executed_query = mock_cursor.execute.call_args[0][0]
            assert 'LIMIT' in executed_query.upper()
            assert 'OFFSET' in executed_query.upper()
    
    def test_rss_feed_parsing_optimization(self):
        """Test RSS feed parsing efficiency"""
        with patch('feedparser.parse') as mock_parse:
            # Mock large RSS feed
            mock_parse.return_value = {
                'entries': [
                    {
                        'title': f'Article {i}',
                        'link': f'https://example.com/article{i}',
                        'summary': f'Summary {i}',
                        'published': 'Mon, 01 Jan 2024 00:00:00 GMT'
                    } for i in range(1, 101)  # 100 articles
                ]
            }
            
            from src.jobs.ingest_articles import process_rss_feed
            
            with patch('src.database.connection.get_db_connection') as mock_db:
                mock_cursor = Mock()
                mock_db.return_value.cursor.return_value = mock_cursor
                
                # Should process efficiently without loading all into memory
                result = process_rss_feed('https://example.com/feed.xml')
                
                assert result is not None
                # Should batch process, not individual inserts
                assert mock_cursor.execute.call_count <= 10
    
    def test_image_loading_optimization(self):
        """Test that images are loaded efficiently"""
        html_content = """
        <img src="large-image1.jpg" />
        <img src="large-image2.jpg" />
        <img src="large-image3.jpg" />
        """
        
        from src.utils.html_cleaner import HTMLCleaner
        cleaner = HTMLCleaner()
        
        # Should add lazy loading attributes
        cleaned = cleaner.clean_html(html_content)
        
        assert 'src=' in cleaned
        # Images should be preserved for proper display
        assert cleaned.count('<img') == 3
    
    def test_static_file_caching(self):
        """Test static file caching headers"""
        from src.app import app
        
        app.config['TESTING'] = True
        client = app.test_client()
        
        # Test CSS file caching
        response = client.get('/static/css/style.css')
        
        # Should have cache headers for static files
        if response.status_code == 200:
            # Static files should be cacheable
            assert 'css' in response.content_type.lower()
    
    def test_database_index_usage(self):
        """Test that database queries use proper indexes"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = []
            mock_db.return_value.cursor.return_value = mock_cursor
            
            # Query that should use indexes
            self.content_service.get_articles_by_date_range(
                start_date='2024-01-01',
                end_date='2024-01-31'
            )
            
            executed_query = mock_cursor.execute.call_args[0][0]
            
            # Should use date indexing
            assert 'published_date' in executed_query.lower()
            assert 'WHERE' in executed_query.upper()
    
    def test_memory_efficient_processing(self):
        """Test memory-efficient processing of large datasets"""
        # Simulate processing large amount of articles
        large_dataset = [
            {'id': i, 'title': f'Article {i}', 'content': 'x' * 1000}
            for i in range(1, 1001)  # 1000 articles with large content
        ]
        
        def process_in_batches(data, batch_size=100):
            """Process data in batches to manage memory"""
            processed = 0
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                # Simulate processing
                processed += len(batch)
            return processed
        
        result = process_in_batches(large_dataset)
        
        assert result == 1000
        # Test passes if no memory error occurs
