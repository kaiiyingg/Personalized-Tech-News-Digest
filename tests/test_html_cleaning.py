import pytest
from unittest.mock import Mock, patch
from src.utils.html_cleaner import HTMLCleaner
import bleach


class TestHTMLCleaning:
    """Test cases for HTML content cleaning and sanitization"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.cleaner = HTMLCleaner()
    
    def test_clean_basic_html(self):
        """Test cleaning basic HTML content"""
        dirty_html = "<p>This is <b>bold</b> text with <a href='http://example.com'>link</a></p>"
        
        cleaned = self.cleaner.clean_html(dirty_html)
        
        assert '<script>' not in cleaned
        assert '<b>bold</b>' in cleaned
        assert 'href=' in cleaned
    
    def test_remove_script_tags(self):
        """Test removal of script tags"""
        malicious_html = """
        <p>Safe content</p>
        <script>alert('xss')</script>
        <p>More safe content</p>
        """
        
        cleaned = self.cleaner.clean_html(malicious_html)
        
        assert '<script>' not in cleaned
        assert 'alert' not in cleaned
        assert 'Safe content' in cleaned
    
    def test_remove_dangerous_attributes(self):
        """Test removal of dangerous HTML attributes"""
        dangerous_html = """
        <img src="image.jpg" onload="alert('xss')" />
        <a href="javascript:void(0)" onclick="badFunction()">Link</a>
        """
        
        cleaned = self.cleaner.clean_html(dangerous_html)
        
        assert 'onload' not in cleaned
        assert 'onclick' not in cleaned
        assert 'javascript:' not in cleaned
        assert 'src="image.jpg"' in cleaned
    
    def test_preserve_safe_tags(self):
        """Test that safe HTML tags are preserved"""
        safe_html = """
        <h1>Title</h1>
        <p>Paragraph with <em>emphasis</em> and <strong>strong</strong> text.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
        <blockquote>A quote</blockquote>
        """
        
        cleaned = self.cleaner.clean_html(safe_html)
        
        assert '<h1>' in cleaned
        assert '<p>' in cleaned
        assert '<em>' in cleaned
        assert '<strong>' in cleaned
        assert '<ul>' in cleaned
        assert '<li>' in cleaned
        assert '<blockquote>' in cleaned
    
    def test_clean_article_content(self):
        """Test cleaning real article content"""
        article_html = """
        <div class="article-content">
            <h2>Article Title</h2>
            <p>This is the article content with <a href="http://example.com">external link</a>.</p>
            <img src="article-image.jpg" alt="Article image" />
            <script>trackPageView();</script>
            <p>More content here.</p>
        </div>
        """
        
        cleaned = self.cleaner.clean_article_content(article_html)
        
        assert '<h2>' in cleaned
        assert 'Article Title' in cleaned
        assert 'external link' in cleaned
        assert '<img' in cleaned
        assert '<script>' not in cleaned
        assert 'trackPageView' not in cleaned
    
    def test_extract_text_content(self):
        """Test extracting plain text from HTML"""
        html_content = """
        <div>
            <h1>Main Title</h1>
            <p>First paragraph.</p>
            <p>Second paragraph with <strong>bold</strong> text.</p>
        </div>
        """
        
        text = self.cleaner.extract_text(html_content)
        
        assert 'Main Title' in text
        assert 'First paragraph.' in text
        assert 'Second paragraph' in text
        assert 'bold' in text
        assert '<h1>' not in text
        assert '<p>' not in text
    
    def test_sanitize_user_input(self):
        """Test sanitizing user-provided content"""
        user_input = """
        Hello <script>alert('xss')</script> world!
        <p>This is a paragraph.</p>
        <img src="x" onerror="alert('xss')" />
        """
        
        sanitized = self.cleaner.sanitize_user_input(user_input)
        
        assert '<script>' not in sanitized
        assert 'alert' not in sanitized
        assert 'onerror' not in sanitized
        assert 'Hello' in sanitized
        assert 'world!' in sanitized
        assert '<p>' in sanitized
    
    def test_clean_rss_content(self):
        """Test cleaning RSS feed content"""
        rss_content = """
        <![CDATA[
        <p>RSS content with <a href="http://example.com">link</a>.</p>
        <script>console.log('tracking');</script>
        ]]>
        """
        
        cleaned = self.cleaner.clean_rss_content(rss_content)
        
        assert 'RSS content' in cleaned
        assert '<a href=' in cleaned
        assert '<script>' not in cleaned
        assert 'CDATA' not in cleaned
