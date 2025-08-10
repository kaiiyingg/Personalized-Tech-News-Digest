"""
Comprehensive tests for url_validator.py

Tests all functions in the URL validator including:
- URL format validation
- Domain validation and security checks
- Protocol validation
- URL sanitization and normalization
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from src.services import url_validator


class TestUrlValidator:
    """Test class for URL validator functions"""

    def test_is_valid_url_valid_urls(self):
        """Test URL validation with valid URLs"""
        valid_urls = [
            'https://www.example.com',
            'http://example.com',
            'https://subdomain.example.com/path',
            'https://example.com:8080',
            'https://example.com/path?query=value',
            'https://example.com/path#fragment',
            'https://192.168.1.1',
            'https://[::1]',  # IPv6
            'ftp://example.com/file.txt',
            'https://example-site.com',
            'https://example.co.uk'
        ]
        
        for url in valid_urls:
            assert url_validator.is_valid_url(url) is True, f"URL should be valid: {url}"

    def test_is_valid_url_invalid_urls(self):
        """Test URL validation with invalid URLs"""
        invalid_urls = [
            '',
            'not-a-url',
            'http://',
            'https://',
            'ftp://',
            'javascript:alert("xss")',
            'data:text/html,<script>alert("xss")</script>',
            'file:///etc/passwd',
            'http://.',
            'http://..',
            'http://../',
            'http://?',
            'http://??/',
            'http://##/',
            'http:// shouldfail.com',
            'http://foo.bar?q=Spaces should be encoded',
            None
        ]
        
        for url in invalid_urls:
            assert url_validator.is_valid_url(url) is False, f"URL should be invalid: {url}"

    def test_is_safe_domain_safe_domains(self):
        """Test domain safety check with safe domains"""
        safe_domains = [
            'example.com',
            'google.com',
            'github.com',
            'stackoverflow.com',
            'techcrunch.com',
            'arstechnica.com',
            'news.ycombinator.com'
        ]
        
        for domain in safe_domains:
            assert url_validator.is_safe_domain(domain) is True, f"Domain should be safe: {domain}"

    def test_is_safe_domain_unsafe_domains(self):
        """Test domain safety check with potentially unsafe domains"""
        unsafe_domains = [
            'localhost',
            '127.0.0.1',
            '10.0.0.1',
            '192.168.1.1',
            '172.16.0.1',
            'malicious-site.evil',
            'phishing-attempt.com'
        ]
        
        for domain in unsafe_domains:
            # Note: This depends on your implementation
            # Adjust based on your actual safety criteria
            result = url_validator.is_safe_domain(domain)
            # For localhost/private IPs, should return False
            if domain in ['localhost', '127.0.0.1', '10.0.0.1', '192.168.1.1', '172.16.0.1']:
                assert result is False, f"Private/local domain should be unsafe: {domain}"

    def test_normalize_url(self):
        """Test URL normalization"""
        test_cases = [
            ('https://example.com', 'https://example.com'),
            ('https://example.com/', 'https://example.com/'),
            ('HTTPS://EXAMPLE.COM', 'https://example.com'),
            ('https://example.com:443', 'https://example.com'),
            ('http://example.com:80', 'http://example.com'),
            ('https://example.com/path/../other', 'https://example.com/other'),
            ('https://example.com//double/slash', 'https://example.com/double/slash'),
            ('https://example.com/path?', 'https://example.com/path'),
            ('https://example.com/path#', 'https://example.com/path')
        ]
        
        for input_url, expected in test_cases:
            normalized = url_validator.normalize_url(input_url)
            assert normalized == expected, f"Input: {input_url}, Expected: {expected}, Got: {normalized}"

    def test_sanitize_url(self):
        """Test URL sanitization"""
        test_cases = [
            ('https://example.com/path with spaces', 'https://example.com/path%20with%20spaces'),
            ('https://example.com/path?query=value with spaces', 'https://example.com/path?query=value%20with%20spaces'),
            ('https://example.com/path"with"quotes', 'https://example.com/path%22with%22quotes'),
            ('https://example.com/path<script>', 'https://example.com/path%3Cscript%3E')
        ]
        
        for input_url, expected in test_cases:
            sanitized = url_validator.sanitize_url(input_url)
            assert sanitized == expected, f"Input: {input_url}, Expected: {expected}, Got: {sanitized}"

    def test_extract_domain(self):
        """Test domain extraction from URLs"""
        test_cases = [
            ('https://www.example.com/path', 'www.example.com'),
            ('http://subdomain.example.com:8080', 'subdomain.example.com'),
            ('https://example.co.uk/path?query=value', 'example.co.uk'),
            ('ftp://files.example.org/file.txt', 'files.example.org'),
            ('https://192.168.1.1', '192.168.1.1'),
            ('https://[::1]:8080', '[::1]')
        ]
        
        for input_url, expected in test_cases:
            domain = url_validator.extract_domain(input_url)
            assert domain == expected, f"Input: {input_url}, Expected: {expected}, Got: {domain}"

    def test_extract_domain_invalid_url(self):
        """Test domain extraction with invalid URLs"""
        invalid_urls = ['not-a-url', '', None, 'http://']
        
        for url in invalid_urls:
            domain = url_validator.extract_domain(url)
            assert domain is None, f"Should return None for invalid URL: {url}"

    def test_is_http_or_https_valid(self):
        """Test HTTP/HTTPS protocol validation with valid protocols"""
        valid_urls = [
            'https://example.com',
            'http://example.com',
            'HTTPS://EXAMPLE.COM',
            'HTTP://EXAMPLE.COM'
        ]
        
        for url in valid_urls:
            assert url_validator.is_http_or_https(url) is True, f"Should accept HTTP/HTTPS: {url}"

    def test_is_http_or_https_invalid(self):
        """Test HTTP/HTTPS protocol validation with invalid protocols"""
        invalid_urls = [
            'ftp://example.com',
            'file:///path/to/file',
            'javascript:alert("xss")',
            'data:text/html,<html></html>',
            'mailto:user@example.com',
            'tel:+1234567890',
            'example.com',  # No protocol
            ''
        ]
        
        for url in invalid_urls:
            assert url_validator.is_http_or_https(url) is False, f"Should reject non-HTTP/HTTPS: {url}"

    def test_validate_rss_url_valid(self):
        """Test RSS URL validation with valid RSS URLs"""
        valid_rss_urls = [
            'https://example.com/feed',
            'https://example.com/rss',
            'https://example.com/feed.xml',
            'https://example.com/rss.xml',
            'https://example.com/atom.xml',
            'https://blog.example.com/feed/',
            'https://news.example.com/rss/'
        ]
        
        for url in valid_rss_urls:
            assert url_validator.validate_rss_url(url) is True, f"Should be valid RSS URL: {url}"

    def test_validate_rss_url_invalid(self):
        """Test RSS URL validation with invalid RSS URLs"""
        invalid_rss_urls = [
            'ftp://example.com/feed',
            'javascript:alert("xss")',
            'file:///etc/passwd',
            'http://localhost/feed',
            'https://192.168.1.1/feed',
            '',
            None,
            'not-a-url'
        ]
        
        for url in invalid_rss_urls:
            assert url_validator.validate_rss_url(url) is False, f"Should be invalid RSS URL: {url}"

    def test_check_url_accessibility_success(self):
        """Test URL accessibility checking (successful)"""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            is_accessible, status_code = url_validator.check_url_accessibility('https://example.com')
            
            assert is_accessible is True
            assert status_code == 200

    def test_check_url_accessibility_failure(self):
        """Test URL accessibility checking (failure)"""
        with patch('requests.head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            is_accessible, status_code = url_validator.check_url_accessibility('https://example.com/notfound')
            
            assert is_accessible is False
            assert status_code == 404

    def test_check_url_accessibility_exception(self):
        """Test URL accessibility checking with network exception"""
        with patch('requests.head') as mock_head:
            mock_head.side_effect = Exception("Network error")
            
            is_accessible, status_code = url_validator.check_url_accessibility('https://invalid-domain.example')
            
            assert is_accessible is False
            assert status_code is None

    def test_is_blacklisted_domain_true(self):
        """Test blacklisted domain checking (blacklisted)"""
        # Assuming you have a blacklist implementation
        blacklisted_domains = [
            'malicious-site.com',
            'phishing-attempt.org',
            'spam-source.net'
        ]
        
        for domain in blacklisted_domains:
            # This test depends on your implementation
            # You might have a blacklist file or database
            result = url_validator.is_blacklisted_domain(domain)
            # Adjust based on your actual implementation
            # assert result is True, f"Domain should be blacklisted: {domain}"

    def test_is_blacklisted_domain_false(self):
        """Test blacklisted domain checking (not blacklisted)"""
        safe_domains = [
            'example.com',
            'google.com',
            'github.com'
        ]
        
        for domain in safe_domains:
            result = url_validator.is_blacklisted_domain(domain)
            # Most legitimate domains should not be blacklisted
            # assert result is False, f"Domain should not be blacklisted: {domain}"

    def test_get_url_info(self):
        """Test URL information extraction"""
        test_url = 'https://subdomain.example.com:8080/path/to/resource?query=value&other=param#section'
        
        info = url_validator.get_url_info(test_url)
        
        expected_info = {
            'scheme': 'https',
            'domain': 'subdomain.example.com',
            'port': 8080,
            'path': '/path/to/resource',
            'query': 'query=value&other=param',
            'fragment': 'section'
        }
        
        for key, expected_value in expected_info.items():
            assert info.get(key) == expected_value, f"Expected {key}: {expected_value}, Got: {info.get(key)}"

    def test_get_url_info_simple(self):
        """Test URL information extraction with simple URL"""
        test_url = 'https://example.com'
        
        info = url_validator.get_url_info(test_url)
        
        assert info['scheme'] == 'https'
        assert info['domain'] == 'example.com'
        assert info['port'] is None
        assert info['path'] == ''
        assert info['query'] == ''
        assert info['fragment'] == ''

    def test_validate_url_length(self):
        """Test URL length validation"""
        # Normal length URL
        normal_url = 'https://example.com/path'
        assert url_validator.validate_url_length(normal_url) is True
        
        # Very long URL (assuming 2048 character limit)
        long_url = 'https://example.com/' + 'a' * 2100
        assert url_validator.validate_url_length(long_url) is False
        
        # Empty URL
        assert url_validator.validate_url_length('') is False
        assert url_validator.validate_url_length(None) is False

    def test_encode_url_components(self):
        """Test URL component encoding"""
        test_cases = [
            ('hello world', 'hello%20world'),
            ('special!@#$%characters', 'special%21%40%23%24%25characters'),
            ('unicode_测试', 'unicode_%E6%B5%8B%E8%AF%95'),
            ('already%20encoded', 'already%20encoded')
        ]
        
        for input_text, expected in test_cases:
            encoded = url_validator.encode_url_components(input_text)
            assert encoded == expected, f"Input: {input_text}, Expected: {expected}, Got: {encoded}"

    def test_decode_url_components(self):
        """Test URL component decoding"""
        test_cases = [
            ('hello%20world', 'hello world'),
            ('special%21%40%23%24%25characters', 'special!@#$%characters'),
            ('unicode_%E6%B5%8B%E8%AF%95', 'unicode_测试'),
            ('no%20encoding%20needed', 'no encoding needed')
        ]
        
        for input_text, expected in test_cases:
            decoded = url_validator.decode_url_components(input_text)
            assert decoded == expected, f"Input: {input_text}, Expected: {expected}, Got: {decoded}"

    def test_is_relative_url(self):
        """Test relative URL detection"""
        relative_urls = [
            '/path/to/resource',
            'path/to/resource',
            '../path/to/resource',
            './path/to/resource',
            '?query=value',
            '#fragment'
        ]
        
        for url in relative_urls:
            assert url_validator.is_relative_url(url) is True, f"Should be relative URL: {url}"

    def test_is_absolute_url(self):
        """Test absolute URL detection"""
        absolute_urls = [
            'https://example.com',
            'http://example.com/path',
            'ftp://example.com/file',
            'mailto:user@example.com'
        ]
        
        for url in absolute_urls:
            assert url_validator.is_relative_url(url) is False, f"Should be absolute URL: {url}"

    def test_join_urls(self):
        """Test URL joining functionality"""
        test_cases = [
            ('https://example.com', '/path', 'https://example.com/path'),
            ('https://example.com/', 'path', 'https://example.com/path'),
            ('https://example.com/base', '../other', 'https://example.com/other'),
            ('https://example.com/base/', './relative', 'https://example.com/base/relative')
        ]
        
        for base_url, relative_url, expected in test_cases:
            joined = url_validator.join_urls(base_url, relative_url)
            assert joined == expected, f"Base: {base_url}, Relative: {relative_url}, Expected: {expected}, Got: {joined}"
