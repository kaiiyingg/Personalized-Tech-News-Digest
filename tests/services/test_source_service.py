"""
Comprehensive tests for source_service.py

Tests all functions in the source service including:
- Source management and CRUD operations
- RSS feed parsing and validation
- Content extraction and processing
- Source statistics and monitoring
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import feedparser

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.services import source_service


class TestSourceService:
    """Test class for source service functions"""

    def setup_method(self):
        """Setup test data for each test method"""
        self.sample_source_data = {
            'name': 'TechCrunch',
            'url': 'https://techcrunch.com/feed/',
            'description': 'Technology news and startup information',
            'category': 'Technology',
            'is_active': True
        }
        self.sample_source_id = 1

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_create_source_success(self, mock_close_conn, mock_get_conn):
        """Test successful source creation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [self.sample_source_id]
        
        result = source_service.create_source(**self.sample_source_data)
        
        assert result == self.sample_source_id
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_create_source_duplicate_url(self, mock_close_conn, mock_get_conn):
        """Test source creation with duplicate URL"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate unique violation
        from psycopg2 import errors as pg_errors
        mock_cursor.execute.side_effect = pg_errors.UniqueViolation("duplicate url")
        
        result = source_service.create_source(**self.sample_source_data)
        
        assert result is None
        mock_conn.rollback.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_get_all_sources(self, mock_close_conn, mock_get_conn):
        """Test retrieving all sources"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, 'TechCrunch', 'https://techcrunch.com/feed/', 'Tech news', 'Technology', True, datetime.now()),
            (2, 'Ars Technica', 'https://arstechnica.com/feed/', 'Tech articles', 'Technology', True, datetime.now())
        ]
        
        sources = source_service.get_all_sources()
        
        assert len(sources) == 2
        assert sources[0]['name'] == 'TechCrunch'
        assert sources[1]['name'] == 'Ars Technica'
        mock_cursor.execute.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_get_active_sources(self, mock_close_conn, mock_get_conn):
        """Test retrieving only active sources"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, 'TechCrunch', 'https://techcrunch.com/feed/', 'Tech news', 'Technology', True, datetime.now())
        ]
        
        sources = source_service.get_active_sources()
        
        assert len(sources) == 1
        assert sources[0]['is_active'] is True
        mock_cursor.execute.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_get_source_by_id_success(self, mock_close_conn, mock_get_conn):
        """Test retrieving source by ID"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = (
            1, 'TechCrunch', 'https://techcrunch.com/feed/', 
            'Tech news', 'Technology', True, datetime.now()
        )
        
        source = source_service.get_source_by_id(1)
        
        assert source is not None
        assert source['id'] == 1
        assert source['name'] == 'TechCrunch'

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_get_source_by_id_not_found(self, mock_close_conn, mock_get_conn):
        """Test retrieving non-existent source by ID"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        source = source_service.get_source_by_id(999)
        
        assert source is None

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_update_source_success(self, mock_close_conn, mock_get_conn):
        """Test successful source update"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        update_data = {
            'name': 'Updated TechCrunch',
            'description': 'Updated description'
        }
        
        result = source_service.update_source(self.sample_source_id, **update_data)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_delete_source_success(self, mock_close_conn, mock_get_conn):
        """Test successful source deletion"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = source_service.delete_source(self.sample_source_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('feedparser.parse')
    def test_fetch_rss_feed_success(self, mock_feedparser):
        """Test successful RSS feed fetching"""
        mock_feed = Mock()
        mock_feed.status = 200
        mock_feed.entries = [
            Mock(
                title='Test Article',
                link='https://example.com/article1',
                summary='Test summary',
                published_parsed=(2023, 1, 15, 12, 0, 0, 0, 0, 0)
            )
        ]
        mock_feedparser.return_value = mock_feed
        
        feed_data = source_service.fetch_rss_feed('https://example.com/feed')
        
        assert feed_data is not None
        assert len(feed_data['entries']) == 1
        assert feed_data['entries'][0]['title'] == 'Test Article'

    @patch('feedparser.parse')
    def test_fetch_rss_feed_failure(self, mock_feedparser):
        """Test RSS feed fetching failure"""
        mock_feed = Mock()
        mock_feed.status = 404
        mock_feed.entries = []
        mock_feedparser.return_value = mock_feed
        
        feed_data = source_service.fetch_rss_feed('https://example.com/invalid-feed')
        
        assert feed_data is None

    @patch('feedparser.parse')
    def test_parse_feed_entries(self, mock_feedparser):
        """Test parsing feed entries into articles"""
        mock_entries = [
            Mock(
                title='AI Breakthrough',
                link='https://example.com/ai-article',
                summary='Revolutionary AI development',
                published_parsed=(2023, 1, 15, 12, 0, 0, 0, 0, 0),
                get=lambda key, default=None: 'https://example.com/image.jpg' if key == 'image' else default
            ),
            Mock(
                title='Cybersecurity Alert',
                link='https://example.com/security-article',
                summary='New security vulnerability discovered',
                published_parsed=(2023, 1, 16, 12, 0, 0, 0, 0, 0),
                get=lambda key, default=None: None
            )
        ]
        
        articles = source_service.parse_feed_entries(mock_entries, self.sample_source_id)
        
        assert len(articles) == 2
        assert articles[0].title == 'AI Breakthrough'
        assert articles[1].title == 'Cybersecurity Alert'
        assert articles[0].image_url == 'https://example.com/image.jpg'
        assert articles[1].image_url is None

    def test_validate_rss_url_valid(self):
        """Test RSS URL validation with valid URLs"""
        valid_urls = [
            'https://techcrunch.com/feed/',
            'http://example.com/rss.xml',
            'https://blog.example.com/feed.rss'
        ]
        
        for url in valid_urls:
            assert source_service.validate_rss_url(url) is True

    def test_validate_rss_url_invalid(self):
        """Test RSS URL validation with invalid URLs"""
        invalid_urls = [
            'not-a-url',
            'ftp://example.com/feed',
            'https://',
            '',
            None
        ]
        
        for url in invalid_urls:
            assert source_service.validate_rss_url(url) is False

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_update_source_last_fetched(self, mock_close_conn, mock_get_conn):
        """Test updating source last fetched timestamp"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = source_service.update_source_last_fetched(self.sample_source_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_get_source_statistics(self, mock_close_conn, mock_get_conn):
        """Test retrieving source statistics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock multiple fetchone calls for different stats
        mock_cursor.fetchone.side_effect = [
            [50],  # total articles
            [10],  # articles today
            [datetime.now()]  # last fetch
        ]
        
        stats = source_service.get_source_statistics(self.sample_source_id)
        
        assert 'total_articles' in stats
        assert 'articles_today' in stats
        assert 'last_fetch' in stats
        assert stats['total_articles'] == 50

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_disable_source(self, mock_close_conn, mock_get_conn):
        """Test disabling a source"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = source_service.disable_source(self.sample_source_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_enable_source(self, mock_close_conn, mock_get_conn):
        """Test enabling a source"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = source_service.enable_source(self.sample_source_id)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    def test_extract_image_from_entry_with_image(self):
        """Test extracting image URL from feed entry"""
        mock_entry = Mock()
        mock_entry.get.side_effect = lambda key, default=None: {
            'image': {'href': 'https://example.com/image.jpg'},
            'media_content': [{'url': 'https://example.com/media.jpg'}],
            'enclosures': [{'href': 'https://example.com/enclosure.jpg', 'type': 'image/jpeg'}]
        }.get(key, default)
        
        image_url = source_service.extract_image_from_entry(mock_entry)
        
        assert image_url == 'https://example.com/image.jpg'

    def test_extract_image_from_entry_no_image(self):
        """Test extracting image URL when no image exists"""
        mock_entry = Mock()
        mock_entry.get.return_value = None
        
        image_url = source_service.extract_image_from_entry(mock_entry)
        
        assert image_url is None

    def test_clean_html_content(self):
        """Test HTML content cleaning"""
        html_content = '<p>This is <strong>HTML</strong> content with <a href="#">links</a>.</p>'
        clean_content = source_service.clean_html_content(html_content)
        
        assert '<p>' not in clean_content
        assert '<strong>' not in clean_content
        assert 'This is HTML content with links.' in clean_content

    def test_truncate_summary(self):
        """Test summary truncation"""
        long_summary = "This is a very long summary that should be truncated. " * 10
        truncated = source_service.truncate_summary(long_summary, max_length=100)
        
        assert len(truncated) <= 103  # 100 + "..."
        assert truncated.endswith('...')

    def test_truncate_summary_short(self):
        """Test summary truncation with short text"""
        short_summary = "This is a short summary."
        truncated = source_service.truncate_summary(short_summary, max_length=100)
        
        assert truncated == short_summary
        assert not truncated.endswith('...')

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_check_source_url_exists_true(self, mock_close_conn, mock_get_conn):
        """Test checking if source URL exists (returns True)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]
        
        exists = source_service.check_source_url_exists('https://techcrunch.com/feed/')
        
        assert exists is True

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_check_source_url_exists_false(self, mock_close_conn, mock_get_conn):
        """Test checking if source URL exists (returns False)"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        
        exists = source_service.check_source_url_exists('https://nonexistent.com/feed/')
        
        assert exists is False

    @patch('src.services.source_service.get_db_connection')
    @patch('src.services.source_service.close_db_connection')
    def test_get_sources_by_category(self, mock_close_conn, mock_get_conn):
        """Test retrieving sources by category"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, 'TechCrunch', 'https://techcrunch.com/feed/', 'Tech news', 'Technology', True, datetime.now()),
            (2, 'Ars Technica', 'https://arstechnica.com/feed/', 'Tech articles', 'Technology', True, datetime.now())
        ]
        
        sources = source_service.get_sources_by_category('Technology')
        
        assert len(sources) == 2
        assert all(source['category'] == 'Technology' for source in sources)

    def test_normalize_url(self):
        """Test URL normalization"""
        test_cases = [
            ('https://example.com/feed/', 'https://example.com/feed/'),
            ('http://example.com/feed', 'http://example.com/feed'),
            ('https://example.com/feed?param=value', 'https://example.com/feed?param=value'),
            ('HTTPS://EXAMPLE.COM/FEED/', 'https://example.com/feed/')
        ]
        
        for input_url, expected in test_cases:
            normalized = source_service.normalize_url(input_url)
            assert normalized == expected

    @patch('requests.get')
    def test_test_rss_feed_connection_success(self, mock_get):
        """Test RSS feed connection testing (success)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/rss+xml'}
        mock_get.return_value = mock_response
        
        is_valid, message = source_service.test_rss_feed_connection('https://example.com/feed/')
        
        assert is_valid is True
        assert "successfully" in message.lower()

    @patch('requests.get')
    def test_test_rss_feed_connection_failure(self, mock_get):
        """Test RSS feed connection testing (failure)"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        is_valid, message = source_service.test_rss_feed_connection('https://example.com/invalid-feed/')
        
        assert is_valid is False
        assert "404" in message
