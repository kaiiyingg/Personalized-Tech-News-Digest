import pytest
from unittest.mock import Mock, patch
from src.services.source_service import SourceService


class TestSourceService:
    """Test cases for RSS source service"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.source_service = SourceService()
    
    def test_add_rss_source_valid(self):
        """Test adding a valid RSS source"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            with patch('feedparser.parse') as mock_parse:
                mock_parse.return_value = {
                    'feed': {'title': 'Test Feed'},
                    'entries': [{'title': 'Test Article'}]
                }
                
                result = self.source_service.add_source(
                    name="Test Source",
                    url="https://example.com/feed.xml",
                    category="tech"
                )
                
                assert result is not None
                mock_cursor.execute.assert_called()
    
    def test_add_rss_source_invalid_url(self):
        """Test adding RSS source with invalid URL"""
        with patch('feedparser.parse') as mock_parse:
            mock_parse.return_value = {'feed': {}, 'entries': []}
            
            result = self.source_service.add_source(
                name="Invalid Source",
                url="invalid-url",
                category="tech"
            )
            
            assert result is None
    
    def test_get_all_sources(self):
        """Test retrieving all RSS sources"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = [
                {
                    'id': 1,
                    'name': 'TechCrunch',
                    'url': 'https://techcrunch.com/feed/',
                    'category': 'tech',
                    'is_active': True
                }
            ]
            mock_db.return_value.cursor.return_value = mock_cursor
            
            sources = self.source_service.get_all_sources()
            
            assert len(sources) == 1
            assert sources[0]['name'] == 'TechCrunch'
    
    def test_sync_source_articles(self):
        """Test syncing articles from RSS source"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            with patch('feedparser.parse') as mock_parse:
                mock_parse.return_value = {
                    'entries': [
                        {
                            'title': 'Test Article',
                            'link': 'https://example.com/article1',
                            'summary': 'Test summary',
                            'published': 'Mon, 01 Jan 2024 00:00:00 GMT'
                        }
                    ]
                }
                
                result = self.source_service.sync_source_articles(1)
                
                assert result > 0
                mock_cursor.execute.assert_called()
    
    def test_remove_source(self):
        """Test removing an RSS source"""
        with patch('src.database.connection.get_db_connection') as mock_db:
            mock_cursor = Mock()
            mock_db.return_value.cursor.return_value = mock_cursor
            
            result = self.source_service.remove_source(1)
            
            assert result is True
            mock_cursor.execute.assert_called()
