"""
HTML Content Cleaning and Sanitization Utilities
Provides safe HTML cleaning for user content and RSS feeds
"""
import re
import bleach
from bs4 import BeautifulSoup


class HTMLCleaner:
    """HTML content cleaner and sanitizer"""
    
    # Allowed HTML tags for article content
    ALLOWED_TAGS = [
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'a', 'img',
        'div', 'span', 'pre', 'code'
    ]
    
    # Allowed HTML attributes
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'div': ['class'],
        'span': ['class'],
        'pre': ['class'],
        'code': ['class']
    }
    
    def __init__(self):
        """Initialize the HTML cleaner"""
        pass
    
    def clean_html(self, html_content):
        """Clean HTML content using bleach"""
        if not html_content:
            return ""
            
        # Remove any CDATA sections
        html_content = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', html_content, flags=re.DOTALL)
        
        # Clean with bleach
        cleaned = bleach.clean(
            html_content,
            tags=self.ALLOWED_TAGS,
            attributes=self.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    def clean_article_content(self, html_content):
        """Clean article content specifically"""
        return self.clean_html(html_content)
    
    def clean_rss_content(self, rss_content):
        """Clean RSS feed content"""
        return self.clean_html(rss_content)
    
    def sanitize_user_input(self, user_input):
        """Sanitize user-provided content"""
        if not user_input:
            return ""
            
        # More restrictive tags for user input
        user_allowed_tags = ['p', 'br', 'strong', 'b', 'em', 'i']
        user_allowed_attributes = {}
        
        cleaned = bleach.clean(
            user_input,
            tags=user_allowed_tags,
            attributes=user_allowed_attributes,
            strip=True
        )
        
        return cleaned
    
    def extract_text(self, html_content):
        """Extract plain text from HTML"""
        if not html_content:
            return ""
            
        # Use BeautifulSoup to extract text
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(strip=True, separator=' ')
    
    def clean_and_extract_summary(self, html_content, max_length=200):
        """Clean HTML and extract a summary"""
        cleaned = self.clean_html(html_content)
        text = self.extract_text(cleaned)
        
        if len(text) > max_length:
            return text[:max_length] + "..."
        
        return text
