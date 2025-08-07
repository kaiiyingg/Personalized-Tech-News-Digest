#!/usr/bin/env python3
"""
Test script to verify HTML cleaning in summaries
"""
import re
from bs4 import BeautifulSoup

def clean_html_summary(summary):
    """Test function to clean HTML from summaries"""
    # Multi-stage HTML cleaning
    clean_soup = BeautifulSoup(summary, "html.parser")
    cleaned_summary = clean_soup.get_text(separator=" ", strip=True)
    
    # Additional regex cleaning for any remaining HTML
    cleaned_summary = re.sub(r'<[^>]+>', '', cleaned_summary)  # Remove any remaining tags
    cleaned_summary = re.sub(r'&[a-zA-Z0-9#]+;', ' ', cleaned_summary)  # Remove HTML entities
    cleaned_summary = re.sub(r'\s+', ' ', cleaned_summary).strip()  # Clean up whitespace
    cleaned_summary = cleaned_summary.replace('"', '').replace("'", "")  # Remove quotes from attributes
    
    return cleaned_summary

# Test cases
test_cases = [
    'a a href="https://9to5mac.com/wp-content/uploads/sites/6/2024/02/Spotify-paid-users-hit-236M" has exposed the service\'s privacy gaps by revealing Spotify playbook activity, playlists, and more for various celebrities',
    '<p>This is a paragraph with <a href="https://example.com">a link</a> inside.</p>',
    'Normal text without HTML',
    '<div class="content">Some content with <strong>bold</strong> text and &nbsp; entities</div>',
    '<script>alert("malicious")</script>Clean text here'
]

print("🧪 Testing HTML cleaning functionality\n")

for i, test_case in enumerate(test_cases, 1):
    print(f"Test Case {i}:")
    print(f"Input:  {test_case}")
    cleaned = clean_html_summary(test_case)
    print(f"Output: {cleaned}")
    print("-" * 80)
