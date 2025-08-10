#!/usr/bin/env python3
"""
HTML Accessibility and Semantic Validation Script
Validates HTML files for accessibility, semantic structure, and WCAG compliance
"""

import os
import sys
import html5lib
from bs4 import BeautifulSoup
import re
from pathlib import Path


def validate_semantic_html(file_path):
    """Validate semantic HTML structure"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    issues = []
    
    # Check for semantic elements
    semantic_elements = ['main', 'header', 'footer', 'nav', 'section', 'article', 'aside']
    found_semantic = [elem for elem in semantic_elements if soup.find(elem)]
    
    if not found_semantic:
        issues.append("❌ No semantic HTML elements found (main, header, footer, nav, section, article, aside)")
    
    # Check heading hierarchy
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if headings:
        heading_levels = [int(h.name[1]) for h in headings]
        if heading_levels and heading_levels[0] != 1:
            issues.append("⚠️  Page should start with h1")
        
        # Check for skipped heading levels
        for i in range(1, len(heading_levels)):
            if heading_levels[i] > heading_levels[i-1] + 1:
                issues.append(f"⚠️  Heading hierarchy skip detected: h{heading_levels[i-1]} to h{heading_levels[i]}")
    
    # Check for alt text on images
    images = soup.find_all('img')
    for img in images:
        if not img.get('alt'):
            issues.append(f"❌ Image missing alt attribute: {str(img)[:100]}...")
    
    # Check for form labels
    inputs = soup.find_all(['input', 'textarea', 'select'])
    for input_elem in inputs:
        input_type = input_elem.get('type', 'text')
        if input_type not in ['hidden', 'submit', 'button']:
            input_id = input_elem.get('id')
            aria_label = input_elem.get('aria-label')
            aria_labelledby = input_elem.get('aria-labelledby')
            
            has_label = False
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    has_label = True
            
            if not (has_label or aria_label or aria_labelledby):
                issues.append(f"❌ Form input missing label: {str(input_elem)[:100]}...")
    
    # Check for button accessibility
    buttons = soup.find_all('button')
    for button in buttons:
        text_content = button.get_text(strip=True)
        aria_label = button.get('aria-label')
        title = button.get('title')
        
        if not (text_content or aria_label or title):
            issues.append(f"❌ Button missing accessible text: {str(button)[:100]}...")
    
    # Check for link accessibility
    links = soup.find_all('a', href=True)
    for link in links:
        text_content = link.get_text(strip=True)
        aria_label = link.get('aria-label')
        title = link.get('title')
        
        if not (text_content or aria_label or title):
            issues.append(f"❌ Link missing accessible text: {str(link)[:100]}...")
        
        # Check for vague link text
        vague_texts = ['click here', 'read more', 'here', 'more', 'link']
        if text_content.lower() in vague_texts:
            issues.append(f"⚠️  Vague link text: '{text_content}' - consider more descriptive text")
    
    # Check for language attribute
    html_tag = soup.find('html')
    if html_tag and not html_tag.get('lang'):
        issues.append("❌ HTML element missing lang attribute")
    
    # Check for meta viewport
    viewport_meta = soup.find('meta', {'name': 'viewport'})
    if not viewport_meta:
        issues.append("⚠️  Missing viewport meta tag for responsive design")
    
    # Check for proper table structure
    tables = soup.find_all('table')
    for table in tables:
        headers = table.find_all('th')
        if not headers:
            issues.append(f"⚠️  Table missing header cells (th): {str(table)[:100]}...")
    
    return issues


def validate_html5(file_path):
    """Validate HTML5 syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse with html5lib to check for syntax errors
        html5lib.parse(content, strict=True)
        return []
    except Exception as e:
        return [f"❌ HTML5 syntax error: {str(e)}"]


def main():
    """Main validation function"""
    print("🔍 Validating HTML files for accessibility and semantic structure...\n")
    
    templates_dir = Path("src/templates")
    if not templates_dir.exists():
        print("❌ Templates directory not found!")
        sys.exit(1)
    
    html_files = list(templates_dir.glob("*.html"))
    
    if not html_files:
        print("❌ No HTML files found!")
        sys.exit(1)
    
    total_issues = 0
    
    for html_file in html_files:
        print(f"📄 Validating {html_file.name}...")
        
        # HTML5 syntax validation
        syntax_issues = validate_html5(html_file)
        
        # Semantic and accessibility validation
        semantic_issues = validate_semantic_html(html_file)
        
        all_issues = syntax_issues + semantic_issues
        
        if all_issues:
            print(f"  Found {len(all_issues)} issues:")
            for issue in all_issues:
                print(f"    {issue}")
            total_issues += len(all_issues)
        else:
            print("  ✅ No issues found!")
        
        print()
    
    print(f"📊 Validation Summary:")
    print(f"  Files checked: {len(html_files)}")
    print(f"  Total issues: {total_issues}")
    
    if total_issues > 0:
        print("\n⚠️  HTML validation found issues that should be addressed for better accessibility.")
        # Don't fail CI for warnings, only critical errors
        critical_issues = [issue for issue in semantic_issues if issue.startswith("❌")]
        if len(critical_issues) > 10:  # Allow some flexibility
            print("❌ Too many critical accessibility issues found!")
            sys.exit(1)
    else:
        print("\n✅ All HTML files passed validation!")


if __name__ == "__main__":
    main()
