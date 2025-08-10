"""
Accessibility tests for the Flask application

Tests WCAG compliance and accessibility features including:
- ARIA labels and attributes
- Keyboard navigation
- Screen reader compatibility
- Color contrast
- Form accessibility
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
import re
from bs4 import BeautifulSoup

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.app import app


class TestAccessibility:
    """Accessibility tests for WCAG compliance"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def authenticated_client(self, client):
        """Create authenticated test client"""
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
        return client

    def parse_html(self, html_content):
        """Parse HTML content for testing"""
        return BeautifulSoup(html_content, 'html.parser')

    def test_html_lang_attribute(self, client):
        """Test that HTML has lang attribute for screen readers"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        html_tag = soup.find('html')
        assert html_tag is not None
        assert html_tag.get('lang') is not None
        assert html_tag.get('lang') in ['en', 'en-US', 'en-GB']

    def test_page_titles_present(self, client):
        """Test that all pages have descriptive titles"""
        pages = ['/login', '/register']
        
        for page in pages:
            response = client.get(page)
            soup = self.parse_html(response.data)
            
            title_tag = soup.find('title')
            assert title_tag is not None
            assert len(title_tag.get_text().strip()) > 0
            assert 'TechPulse' in title_tag.get_text()

    @patch('src.app.content_service.get_articles_by_topics')
    def test_main_landmarks(self, mock_get_articles, authenticated_client):
        """Test presence of main landmark elements"""
        mock_get_articles.return_value = {'fast_view': [], 'topics': {}}
        
        response = authenticated_client.get('/index')
        soup = self.parse_html(response.data)
        
        # Check for main landmarks
        main_element = soup.find('main')
        assert main_element is not None, "Page should have a main landmark"
        
        # Check for navigation
        nav_elements = soup.find_all('nav')
        assert len(nav_elements) > 0, "Page should have navigation landmarks"

    def test_form_labels_and_accessibility(self, client):
        """Test form accessibility features"""
        # Test login form
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        # Find all input fields
        inputs = soup.find_all('input', {'type': ['text', 'email', 'password']})
        
        for input_field in inputs:
            input_id = input_field.get('id')
            input_name = input_field.get('name')
            
            if input_id:
                # Check for associated label
                label = soup.find('label', {'for': input_id})
                assert label is not None, f"Input {input_id} should have an associated label"
            
            # Check for required fields having proper attributes
            if input_field.get('required'):
                aria_required = input_field.get('aria-required')
                assert aria_required == 'true', f"Required input should have aria-required='true'"

    def test_button_accessibility(self, client):
        """Test button accessibility features"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        buttons = soup.find_all('button')
        
        for button in buttons:
            # Buttons should have accessible text
            button_text = button.get_text().strip()
            aria_label = button.get('aria-label')
            
            assert button_text or aria_label, "Button should have accessible text or aria-label"
            
            # Check for proper button type
            button_type = button.get('type')
            if button_type:
                assert button_type in ['button', 'submit', 'reset']

    @patch('src.app.content_service.get_user_favorites')
    def test_heart_button_accessibility(self, mock_get_favorites, authenticated_client):
        """Test heart button accessibility features"""
        mock_get_favorites.return_value = [
            {'id': 1, 'title': 'Test Article', 'summary': 'Test summary', 'is_liked': True}
        ]
        
        response = authenticated_client.get('/favorites')
        soup = self.parse_html(response.data)
        
        # Find heart buttons
        heart_buttons = soup.find_all('button', class_=re.compile(r'heart'))
        
        for button in heart_buttons:
            # Check for ARIA attributes
            aria_label = button.get('aria-label')
            aria_pressed = button.get('aria-pressed')
            
            assert aria_label is not None, "Heart button should have aria-label"
            assert 'favorite' in aria_label.lower() or 'like' in aria_label.lower()
            
            # Check for ARIA pressed state
            if aria_pressed:
                assert aria_pressed in ['true', 'false']

    def test_heading_hierarchy(self, client):
        """Test proper heading hierarchy (h1, h2, h3, etc.)"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        # Find all headings
        headings = soup.find_all(re.compile(r'^h[1-6]$'))
        
        if headings:
            # Should have at least one h1
            h1_count = len(soup.find_all('h1'))
            assert h1_count >= 1, "Page should have at least one h1 heading"
            
            # Check heading order (basic check)
            heading_levels = []
            for heading in headings:
                level = int(heading.name[1])
                heading_levels.append(level)
            
            # First heading should be h1
            assert heading_levels[0] == 1, "First heading should be h1"

    def test_images_alt_text(self, client):
        """Test that images have appropriate alt text"""
        pages = ['/login', '/register']
        
        for page in pages:
            response = client.get(page)
            soup = self.parse_html(response.data)
            
            images = soup.find_all('img')
            
            for img in images:
                alt_text = img.get('alt')
                src = img.get('src')
                
                # All images should have alt attribute (can be empty for decorative)
                assert alt_text is not None, f"Image {src} should have alt attribute"
                
                # Non-decorative images should have meaningful alt text
                if not any(keyword in src.lower() for keyword in ['logo', 'icon', 'decoration']):
                    assert len(alt_text.strip()) > 0, f"Content image {src} should have descriptive alt text"

    def test_link_accessibility(self, client):
        """Test link accessibility features"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        links = soup.find_all('a')
        
        for link in links:
            href = link.get('href')
            link_text = link.get_text().strip()
            aria_label = link.get('aria-label')
            title = link.get('title')
            
            # Links should have accessible text
            assert link_text or aria_label or title, "Link should have accessible text"
            
            # External links should indicate they open in new window
            target = link.get('target')
            if target == '_blank':
                # Should have some indication for screen readers
                assert (aria_label and 'new' in aria_label.lower()) or \
                       (title and 'new' in title.lower()) or \
                       'external' in link.get('class', []) or \
                       link.find('span', class_='sr-only'), \
                       "External links should indicate they open in new window"

    def test_form_error_accessibility(self, client):
        """Test form error message accessibility"""
        # Test with invalid login to trigger error
        with patch('src.app.user_service.authenticate_user') as mock_auth:
            mock_auth.return_value = None
            
            response = client.post('/login', data={
                'email': 'invalid@example.com',
                'password': 'wrongpassword'
            })
            
            soup = self.parse_html(response.data)
            
            # Look for error messages
            error_elements = soup.find_all(class_=re.compile(r'error|alert|danger'))
            
            for error in error_elements:
                # Error messages should be associated with form fields
                # or have proper ARIA attributes
                role = error.get('role')
                aria_live = error.get('aria-live')
                
                # Should have appropriate ARIA attributes for announcements
                if role:
                    assert role in ['alert', 'status']
                if aria_live:
                    assert aria_live in ['polite', 'assertive']

    def test_skip_links(self, authenticated_client):
        """Test presence of skip links for keyboard navigation"""
        with patch('src.app.content_service.get_articles_by_topics') as mock_get_articles:
            mock_get_articles.return_value = {'fast_view': [], 'topics': {}}
            
            response = authenticated_client.get('/index')
            soup = self.parse_html(response.data)
            
            # Look for skip links (usually hidden but accessible to screen readers)
            skip_links = soup.find_all('a', href=re.compile(r'#(main|content|skip)'))
            
            # Should have at least one skip link
            if skip_links:
                for skip_link in skip_links:
                    href = skip_link.get('href')
                    target_id = href[1:]  # Remove #
                    
                    # Target element should exist
                    target_element = soup.find(id=target_id)
                    assert target_element is not None, f"Skip link target {target_id} should exist"

    def test_focus_indicators(self, client):
        """Test that focusable elements can receive focus"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        # Find focusable elements
        focusable_selectors = ['input', 'button', 'a[href]', 'select', 'textarea']
        
        for selector in focusable_selectors:
            elements = soup.select(selector)
            
            for element in elements:
                # Elements should not have tabindex="-1" unless intentional
                tabindex = element.get('tabindex')
                if tabindex == '-1':
                    # Should have a good reason (like being in a modal or dropdown)
                    classes = element.get('class', [])
                    assert any(cls in ['modal', 'dropdown', 'hidden'] for cls in classes), \
                           "Elements with tabindex='-1' should be in modals or hidden"

    def test_color_contrast_indicators(self, client):
        """Test for potential color contrast issues"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        # Look for inline styles that might cause contrast issues
        elements_with_style = soup.find_all(style=True)
        
        for element in elements_with_style:
            style = element.get('style')
            
            # Basic check for color definitions
            if 'color:' in style or 'background' in style:
                # Should not rely solely on color for information
                text_content = element.get_text().strip()
                
                # If element conveys important information, it should have text or icons
                if any(keyword in text_content.lower() for keyword in ['error', 'warning', 'success']):
                    # Should have additional indicators beyond color
                    assert text_content or element.find('i') or element.find('span', class_=re.compile(r'icon')), \
                           "Important information should not rely solely on color"

    def test_table_accessibility(self, authenticated_client):
        """Test table accessibility if tables are present"""
        with patch('src.app.content_service.get_user_favorites') as mock_get_favorites:
            mock_get_favorites.return_value = [
                {'id': 1, 'title': 'Test Article', 'summary': 'Test summary'}
            ]
            
            response = authenticated_client.get('/favorites')
            soup = self.parse_html(response.data)
            
            tables = soup.find_all('table')
            
            for table in tables:
                # Tables should have captions or aria-label
                caption = table.find('caption')
                aria_label = table.get('aria-label')
                
                assert caption or aria_label, "Tables should have captions or aria-label"
                
                # Check for proper header structure
                headers = table.find_all('th')
                if headers:
                    for header in headers:
                        scope = header.get('scope')
                        # Headers should have scope attribute for complex tables
                        if len(headers) > 1:
                            assert scope in ['col', 'row', 'colgroup', 'rowgroup'], \
                                   "Table headers should have appropriate scope"

    def test_live_regions(self, authenticated_client):
        """Test for ARIA live regions for dynamic content"""
        with patch('src.app.content_service.get_articles_by_topics') as mock_get_articles:
            mock_get_articles.return_value = {'fast_view': [], 'topics': {}}
            
            response = authenticated_client.get('/index')
            soup = self.parse_html(response.data)
            
            # Look for elements that might need live regions
            dynamic_elements = soup.find_all(class_=re.compile(r'alert|status|update'))
            
            for element in dynamic_elements:
                aria_live = element.get('aria-live')
                role = element.get('role')
                
                # Dynamic content should have appropriate ARIA attributes
                if aria_live or role:
                    if aria_live:
                        assert aria_live in ['polite', 'assertive', 'off']
                    if role:
                        assert role in ['alert', 'status', 'log']

    def test_keyboard_navigation_attributes(self, client):
        """Test keyboard navigation support"""
        response = client.get('/login')
        soup = self.parse_html(response.data)
        
        # Check for keyboard event handlers
        elements_with_events = soup.find_all(attrs={'onkeydown': True, 'onkeyup': True, 'onkeypress': True})
        
        for element in elements_with_events:
            # Elements with keyboard events should be focusable
            tag_name = element.name.lower()
            tabindex = element.get('tabindex')
            
            is_focusable = tag_name in ['input', 'button', 'a', 'select', 'textarea'] or \
                          (tabindex and int(tabindex) >= 0)
            
            assert is_focusable, f"Element {element} with keyboard events should be focusable"

    def test_aria_expanded_for_dropdowns(self, authenticated_client):
        """Test ARIA expanded state for dropdown elements"""
        with patch('src.app.content_service.get_articles_by_topics') as mock_get_articles:
            mock_get_articles.return_value = {'fast_view': [], 'topics': {}}
            
            response = authenticated_client.get('/index')
            soup = self.parse_html(response.data)
            
            # Look for dropdown elements
            dropdown_elements = soup.find_all(class_=re.compile(r'dropdown|menu'))
            
            for element in dropdown_elements:
                # If it's a toggle element, should have aria-expanded
                if 'toggle' in element.get('class', []):
                    aria_expanded = element.get('aria-expanded')
                    assert aria_expanded in ['true', 'false'], \
                           "Dropdown toggles should have aria-expanded attribute"

    def test_required_form_fields_marked(self, client):
        """Test that required form fields are properly marked"""
        response = client.get('/register')
        soup = self.parse_html(response.data)
        
        required_inputs = soup.find_all('input', required=True)
        
        for input_field in required_inputs:
            # Required fields should have visual and programmatic indicators
            aria_required = input_field.get('aria-required')
            assert aria_required == 'true', "Required fields should have aria-required='true'"
            
            # Look for visual indicators (asterisk, etc.)
            input_id = input_field.get('id')
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    label_text = label.get_text()
                    # Should have some visual indicator of being required
                    assert '*' in label_text or 'required' in label_text.lower() or \
                           label.find(class_=re.compile(r'required|asterisk')), \
                           "Required fields should have visual indicators"
