"""
Comprehensive tests for content_service.py

Tests all functions in the content service including:
- Content creation and management
- Topic assignment and filtering
- User content interactions
- Content retrieval and search
- Content statistics and cleanup
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.services import content_service
from src.models.content import Content


class TestContentService:
    """Test class for content service functions"""

    def setup_method(self):
        """Setup test data for each test method"""
        self.sample_content = {
            'title': 'Test AI Article',
            'url': 'https://example.com/ai-article',
            'summary': 'This is an article about artificial intelligence and machine learning',
            'image_url': 'https://example.com/image.jpg',
            'published_at': datetime.now(),
            'source_name': 'TechNews',
            'source_id': 1
        }
        
        self.sample_user_id = 1
        self.sample_content_id = 1

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_assign_topic_ai_ml_content(self, mock_close_conn, mock_get_conn):
        """Test topic assignment for AI/ML content"""
        title = "Advanced Machine Learning Algorithms"
        summary = "Deep learning and neural networks in artificial intelligence"
        
        topic = content_service.assign_topic(title, summary)
        assert topic == content_service.AI_ML_TOPIC

    def test_assign_topic_cybersecurity_content(self):
        """Test topic assignment for cybersecurity content"""
        title = "New Ransomware Attack Methods"
        summary = "Security researchers discover new encryption vulnerabilities"
        
        topic = content_service.assign_topic(title, summary)
        assert topic == content_service.CYBERSECURITY_TOPIC

    def test_assign_topic_cloud_devops_content(self):
        """Test topic assignment for cloud/DevOps content"""
        title = "Docker Container Orchestration"
        summary = "Kubernetes deployment strategies for microservices architecture"
        
        topic = content_service.assign_topic(title, summary)
        assert topic == content_service.CLOUD_DEVOPS_TOPIC

    def test_assign_topic_rejected_content(self):
        """Test rejection of non-tech content"""
        title = "Best Wedding Photography Tips"
        summary = "Learn how to capture beautiful wedding moments"
        
        topic = content_service.assign_topic(title, summary)
        assert topic is None

    def test_assign_topic_promotional_content(self):
        """Test rejection of promotional content"""
        title = "Get lifetime access to documentaries for $200"
        summary = "Limited time offer for premium streaming service"
        
        topic = content_service.assign_topic(title, summary)
        assert topic is None

    def test_assign_topic_policy_content(self):
        """Test rejection of government policy content"""
        title = "BTO income ceilings eligibility age for singles under review"
        summary = "Minister announces housing policy changes"
        
        topic = content_service.assign_topic(title, summary)
        assert topic is None

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_create_content_item_success(self, mock_close_conn, mock_get_conn):
        """Test successful content item creation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [self.sample_content_id]
        
        content = Content(**self.sample_content)
        
        with patch('src.services.content_service.assign_topic') as mock_assign:
            mock_assign.return_value = content_service.AI_ML_TOPIC
            result = content_service.create_content_item(content)
            
        assert result is not None
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_create_content_item_no_topic(self, mock_close_conn, mock_get_conn):
        """Test content creation when no topic is assigned (rejected)"""
        mock_conn = Mock()
        mock_get_conn.return_value = mock_conn
        
        content = Content(**self.sample_content)
        
        with patch('src.services.content_service.assign_topic') as mock_assign:
            mock_assign.return_value = None  # Rejected content
            result = content_service.create_content_item(content)
            
        assert result is None

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_create_content_item_duplicate_url(self, mock_close_conn, mock_get_conn):
        """Test content creation with duplicate URL"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate duplicate key error
        from psycopg2 import errors as pg_errors
        mock_cursor.execute.side_effect = pg_errors.UniqueViolation("duplicate key")
        
        content = Content(**self.sample_content)
        
        with patch('src.services.content_service.assign_topic') as mock_assign:
            mock_assign.return_value = content_service.AI_ML_TOPIC
            result = content_service.create_content_item(content)
            
        assert result is None

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_update_content_liked_success(self, mock_close_conn, mock_get_conn):
        """Test successful content like update"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = content_service.update_content_liked(
            self.sample_user_id, self.sample_content_id, is_liked=True
        )
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_update_content_read_success(self, mock_close_conn, mock_get_conn):
        """Test successful content read update"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        result = content_service.update_content_read(
            self.sample_user_id, self.sample_content_id, is_read=True
        )
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_get_user_favorites(self, mock_close_conn, mock_get_conn):
        """Test retrieving user favorites"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock database response
        mock_cursor.fetchall.return_value = [
            (1, 'Test Article', 'Summary', 'https://example.com', 'Tech News', 'AI & ML', 
             'https://example.com/image.jpg', datetime.now())
        ]
        
        favorites = content_service.get_user_favorites(self.sample_user_id)
        
        assert len(favorites) == 1
        assert favorites[0]['title'] == 'Test Article'
        mock_cursor.execute.assert_called()

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_get_personalized_digest(self, mock_close_conn, mock_get_conn):
        """Test personalized digest generation"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock database response
        mock_cursor.fetchall.return_value = [
            (1, 'Test Article', 'Summary', 'https://example.com', 'Tech News', 'AI & ML',
             'https://example.com/image.jpg', datetime.now(), False, False)
        ]
        
        digest = content_service.get_personalized_digest(
            self.sample_user_id, limit=10, offset=0
        )
        
        assert len(digest) == 1
        assert digest[0]['title'] == 'Test Article'
        mock_cursor.execute.assert_called()

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_get_articles_by_topics(self, mock_close_conn, mock_get_conn):
        """Test articles retrieval by topics"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock user topics
        with patch('src.services.content_service.get_user_topics') as mock_get_topics:
            mock_get_topics.return_value = ['AI & ML', 'Cybersecurity & Privacy']
            
            # Mock articles response
            mock_cursor.fetchall.return_value = [
                (1, 'AI Article', 'AI Summary', 'https://example.com/ai', 'Tech News', 'AI & ML',
                 'https://example.com/ai.jpg', datetime.now(), False, False)
            ]
            
            result = content_service.get_articles_by_topics(self.sample_user_id)
            
            assert 'fast_view' in result
            assert 'topics' in result
            assert isinstance(result['fast_view'], list)
            assert isinstance(result['topics'], dict)

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_get_content_stats(self, mock_close_conn, mock_get_conn):
        """Test content statistics retrieval"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock multiple database calls for stats
        mock_cursor.fetchone.side_effect = [
            [100],  # total articles
            [25],   # articles last 24h
            [75],   # articles last week
            [datetime.now()]  # most recent article
        ]
        mock_cursor.fetchall.return_value = [
            ('AI & ML', 30),
            ('Cybersecurity & Privacy', 25)
        ]
        
        stats = content_service.get_content_stats()
        
        assert 'total_articles' in stats
        assert 'articles_last_24h' in stats
        assert 'articles_last_week' in stats
        assert 'most_recent_article' in stats
        assert 'top_topics' in stats
        assert stats['total_articles'] == 100

    def test_classify_topic_by_keywords_ai_ml(self):
        """Test keyword-based topic classification for AI/ML"""
        combined_text = "machine learning artificial intelligence neural networks"
        topic = content_service._classify_topic_by_keywords(combined_text)
        assert topic == content_service.AI_ML_TOPIC

    def test_classify_topic_by_keywords_cybersecurity(self):
        """Test keyword-based topic classification for cybersecurity"""
        combined_text = "cybersecurity data breach encryption vulnerability"
        topic = content_service._classify_topic_by_keywords(combined_text)
        assert topic == content_service.CYBERSECURITY_TOPIC

    def test_classify_topic_by_keywords_no_match(self):
        """Test keyword-based topic classification with no match"""
        combined_text = "cooking recipes food restaurant"
        topic = content_service._classify_topic_by_keywords(combined_text)
        assert topic is None

    def test_format_datetime(self):
        """Test datetime formatting function"""
        test_datetime = datetime(2023, 1, 15, 14, 30, 0)
        formatted = content_service.format_datetime(test_datetime)
        expected = "Jan 15, 2023"
        assert formatted == expected

    def test_build_simple_article_dict(self):
        """Test building simple article dictionary"""
        mock_row = (
            1, 'Test Title', 'Test Summary', 'https://example.com',
            'Tech News', 'AI & ML', 'https://example.com/image.jpg',
            datetime(2023, 1, 15), False, True
        )
        
        article_dict = content_service.build_simple_article_dict(mock_row)
        
        assert article_dict['id'] == 1
        assert article_dict['title'] == 'Test Title'
        assert article_dict['is_read'] is False
        assert article_dict['is_liked'] is True
        assert 'formatted_date' in article_dict

    @patch('src.services.content_service.get_db_connection')
    @patch('src.services.content_service.close_db_connection')
    def test_get_general_digest(self, mock_close_conn, mock_get_conn):
        """Test general digest retrieval"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [
            (1, 'General Article', 'Summary', 'https://example.com', 'Tech News', 'AI & ML',
             'https://example.com/image.jpg', datetime.now())
        ]
        
        digest = content_service.get_general_digest(limit=10)
        
        assert len(digest) == 2  # 1 article + 1 instruction
        assert digest[0]['instruction']  # First item is instruction
        assert digest[1]['title'] == 'General Article'

    def test_generate_excerpt(self):
        """Test excerpt generation from content"""
        long_summary = "This is a very long summary that should be truncated to a reasonable length for display purposes. " * 5
        excerpt = content_service.generate_excerpt(long_summary, max_length=100)
        
        assert len(excerpt) <= 103  # 100 + "..."
        assert excerpt.endswith('...')

    def test_generate_excerpt_short_text(self):
        """Test excerpt generation with short text"""
        short_summary = "This is a short summary."
        excerpt = content_service.generate_excerpt(short_summary, max_length=100)
        
        assert excerpt == short_summary
        assert not excerpt.endswith('...')
