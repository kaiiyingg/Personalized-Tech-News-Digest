"""
Unit Tests for Content Service
Tests content creation, classification, filtering, and database operations.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.services.content_service import (
    create_content_item,
    classify_topic_by_keywords,
    assign_topic,
    get_articles_by_topics,
    cleanup_irrelevant_articles
)


class TestContentService:
    """Unit tests for content service functionality"""

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        return mock_conn, mock_cursor

    def test_classify_topic_by_keywords_ai_ml(self):
        """Test AI/ML topic classification"""
        text = "machine learning artificial intelligence neural networks deep learning"
        result = classify_topic_by_keywords(text)
        assert result == "AI & ML"

    def test_classify_topic_by_keywords_cybersecurity(self):
        """Test cybersecurity topic classification"""
        text = "cybersecurity data breach encryption firewall security vulnerability"
        result = classify_topic_by_keywords(text)
        assert result == "Cybersecurity & Privacy"

    def test_classify_topic_by_keywords_cloud_devops(self):
        """Test cloud/DevOps topic classification"""
        text = "kubernetes docker aws cloud infrastructure deployment devops"
        result = classify_topic_by_keywords(text)
        assert result == "Cloud Computing & DevOps"

    def test_classify_topic_by_keywords_no_match(self):
        """Test classification when no keywords match"""
        text = "random unrelated content about cooking recipes"
        result = classify_topic_by_keywords(text)
        assert result is None

    def test_assign_topic_with_tech_content(self):
        """Test topic assignment with valid tech content"""
        title = "New Python Framework Released"
        summary = "Python developers released new web framework with advanced features"
        
        result = assign_topic(title, summary)
        assert result == "Software Development & Web Technologies"

    def test_assign_topic_with_rejected_content(self):
        """Test topic assignment rejects non-tech content"""
        title = "Best Welding Techniques"
        summary = "Learn welding techniques for metal fabrication projects"
        
        result = assign_topic(title, summary)
        assert result is None

    def test_assign_topic_insufficient_tech_keywords(self):
        """Test topic assignment with insufficient tech keywords"""
        title = "Software Update"
        summary = "Minor software update available for download"
        
        result = assign_topic(title, summary)
        assert result is None  # Should reject due to insufficient tech keywords

    @patch('src.services.content_service.get_db_connection')
    def test_create_content_item_success(self, mock_get_db):
        """Test successful content item creation"""
        mock_conn, mock_cursor = self.mock_db_connection()
        mock_get_db.return_value = mock_conn
        mock_cursor.fetchone.return_value = [1]  # Mock content ID

        with patch('src.services.content_service.assign_topic', return_value="AI & ML"):
            result = create_content_item(
                title="AI Breakthrough",
                summary="New AI model shows remarkable performance",
                url="https://example.com/ai-news",
                published_at=datetime.now(),
                source_id=1
            )

        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()

    @patch('src.services.content_service.get_db_connection')
    def test_create_content_item_duplicate_url(self, mock_get_db):
        """Test content creation with duplicate URL"""
        mock_conn, mock_cursor = self.mock_db_connection()
        mock_get_db.return_value = mock_conn
        
        # Mock duplicate URL check
        mock_cursor.fetchone.return_value = [1]  # URL exists
        
        result = create_content_item(
            title="Duplicate Article",
            summary="This URL already exists",
            url="https://example.com/existing",
            published_at=datetime.now(),
            source_id=1
        )

        assert result is False

    @patch('src.services.content_service.get_db_connection')
    def test_create_content_item_no_topic(self, mock_get_db):
        """Test content creation when no topic is assigned"""
        mock_conn, mock_cursor = self.mock_db_connection()
        mock_get_db.return_value = mock_conn
        mock_cursor.fetchone.return_value = None  # No duplicate URL

        with patch('src.services.content_service.assign_topic', return_value=None):
            result = create_content_item(
                title="Non-tech Article",
                summary="This is about cooking recipes",
                url="https://example.com/cooking",
                published_at=datetime.now(),
                source_id=1
            )

        assert result is False

    @patch('src.services.content_service.get_db_connection')
    def test_get_articles_by_topics_success(self, mock_get_db):
        """Test retrieving articles by topics"""
        mock_conn, mock_cursor = self.mock_db_connection()
        mock_get_db.return_value = mock_conn
        
        # Mock database response
        mock_cursor.fetchall.return_value = [
            (1, "AI Article", "AI summary", "https://example.com/ai", 
             "AI & ML", "TechCrunch", datetime.now(), False, False, "image.jpg")
        ]

        result = get_articles_by_topics(user_id=1, limit_per_topic=5)
        
        assert "topics" in result
        assert "AI & ML" in result["topics"]
        assert len(result["topics"]["AI & ML"]) == 1
        assert result["topics"]["AI & ML"][0]["title"] == "AI Article"

    @patch('src.services.content_service.get_db_connection')
    def test_cleanup_irrelevant_articles(self, mock_get_db):
        """Test cleanup of irrelevant articles"""
        mock_conn, mock_cursor = self.mock_db_connection()
        mock_get_db.return_value = mock_conn
        
        # Mock articles to check
        mock_cursor.fetchall.return_value = [
            (1, "Welding Techniques", "Learn welding for metal work", "https://example.com/welding"),
            (2, "Python Programming", "Advanced Python techniques", "https://example.com/python")
        ]

        result = cleanup_irrelevant_articles()
        
        assert result["success"] is True
        assert "articles_removed" in result


class TestContentValidation:
    """Test content validation and filtering"""

    def test_tech_keyword_scoring(self):
        """Test tech keyword scoring system"""
        from src.services.content_service import classify_topic_by_keywords
        
        # High tech score text
        high_tech_text = "python programming software development api database framework"
        result = classify_topic_by_keywords(high_tech_text)
        assert result is not None

        # Low tech score text
        low_tech_text = "cooking recipe food restaurant dining experience"
        result = classify_topic_by_keywords(low_tech_text)
        assert result is None

    def test_rejection_keywords(self):
        """Test rejection keyword filtering"""
        from src.services.content_service import assign_topic
        
        rejection_cases = [
            ("welding techniques", "metal welding fabrication"),
            ("wedding planning", "wedding ceremony planning guide"),
            ("cooking tips", "recipe cooking food preparation"),
            ("puzzle games", "puzzle solving word games"),
            ("fashion trends", "clothing fashion style trends")
        ]

        for title, summary in rejection_cases:
            result = assign_topic(title, summary)
            assert result is None, f"Should reject: {title}"

    def test_minimum_tech_keyword_requirement(self):
        """Test minimum tech keyword requirement"""
        from src.services.content_service import assign_topic
        
        # Should pass (3+ tech keywords)
        good_content = assign_topic(
            "Software Development Update",
            "Python programming framework with API integration and database support"
        )
        assert good_content is not None

        # Should fail (insufficient tech keywords)
        weak_content = assign_topic(
            "Software Update",
            "Minor update available for download"
        )
        assert weak_content is None


class TestErrorHandling:
    """Test error handling and edge cases"""

    @patch('src.services.content_service.get_db_connection')
    def test_database_connection_error(self, mock_get_db):
        """Test handling of database connection errors"""
        mock_get_db.side_effect = Exception("Database connection failed")
        
        result = create_content_item(
            title="Test Article",
            summary="Test summary",
            url="https://example.com/test",
            published_at=datetime.now(),
            source_id=1
        )
        
        assert result is False

    def test_empty_content_handling(self):
        """Test handling of empty or None content"""
        from src.services.content_service import assign_topic
        
        # Test empty strings
        assert assign_topic("", "") is None
        assert assign_topic(None, None) is None
        assert assign_topic("", "some summary") is None
        assert assign_topic("some title", "") is None

    def test_invalid_datetime_handling(self):
        """Test handling of invalid datetime objects"""
        result = create_content_item(
            title="Test Article",
            summary="Test summary",
            url="https://example.com/test",
            published_at="invalid-datetime",  # Invalid datetime
            source_id=1
        )
        
        assert result is False
