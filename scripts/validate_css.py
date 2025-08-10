#!/usr/bin/env python3
"""
CSS Validation and Accessibility Script
Validates CSS for accessibility features like contrast, focus indicators, and responsive design
"""

import os
import sys
import re
from pathlib import Path


def validate_css_accessibility(file_path):
    """Validate CSS for accessibility features"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    issues = []
    
    # Check for focus indicators
    focus_patterns = [
        r':focus\s*{[^}]*outline\s*:\s*none[^}]*}',
        r':focus\s*{[^}]*outline\s*:\s*0[^}]*}',
    ]
    
    focus_removed = any(re.search(pattern, content, re.IGNORECASE) for pattern in focus_patterns)
    
    if focus_removed:
        # Check if alternative focus styles are provided
        alternative_focus = any(re.search(pattern, content, re.IGNORECASE) for pattern in [
            r':focus\s*{[^}]*box-shadow[^}]*}',
            r':focus\s*{[^}]*border[^}]*}',
            r':focus\s*{[^}]*background[^}]*}',
        ])
        
        if not alternative_focus:
            issues.append("⚠️  Focus outline removed without alternative focus indicators")
    
    # Check for responsive design
    media_queries = re.findall(r'@media[^{]*{', content, re.IGNORECASE)
    if not media_queries:
        issues.append("⚠️  No media queries found - consider responsive design")
    
    # Check for text size units
    fixed_font_sizes = re.findall(r'font-size\s*:\s*\d+px', content, re.IGNORECASE)
    if len(fixed_font_sizes) > 5:  # Allow some fixed sizes
        issues.append("⚠️  Many fixed pixel font sizes found - consider relative units (rem, em)")
    
    # Check for color-only information
    color_only_patterns = [
        r'\.error\s*{[^}]*color\s*:[^}]*}',
        r'\.success\s*{[^}]*color\s*:[^}]*}',
        r'\.warning\s*{[^}]*color\s*:[^}]*}',
    ]
    
    for pattern in color_only_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if not any(keyword in match.lower() for keyword in ['icon', 'border', 'background', 'font-weight']):
                issues.append("⚠️  Color-only state indication found - add visual indicators")
    
    # Check for sufficient line height
    line_heights = re.findall(r'line-height\s*:\s*([\d.]+)', content, re.IGNORECASE)
    for height in line_heights:
        try:
            if float(height) < 1.4:
                issues.append(f"⚠️  Line height {height} may be too small for readability (recommend 1.4+)")
        except ValueError:
            pass
    
    return issues


def validate_css_syntax(file_path):
    """Basic CSS syntax validation"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    issues = []
    
    # Check for unclosed braces
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    if open_braces != close_braces:
        issues.append(f"❌ Mismatched braces: {open_braces} opening, {close_braces} closing")
    
    # Check for common syntax errors
    if ';;' in content:
        issues.append("⚠️  Double semicolons found")
    
    # Check for empty rules
    empty_rules = re.findall(r'[^{}]*{\s*}', content)
    if empty_rules:
        issues.append(f"⚠️  {len(empty_rules)} empty CSS rules found")
    
    return issues


def main():
    """Main validation function"""
    print("🎨 Validating CSS files for accessibility and syntax...\n")
    
    css_dir = Path("src/static/css")
    if not css_dir.exists():
        print("❌ CSS directory not found!")
        sys.exit(1)
    
    css_files = list(css_dir.glob("*.css"))
    
    if not css_files:
        print("❌ No CSS files found!")
        sys.exit(1)
    
    total_issues = 0
    
    for css_file in css_files:
        print(f"📄 Validating {css_file.name}...")
        
        # Syntax validation
        syntax_issues = validate_css_syntax(css_file)
        
        # Accessibility validation
        accessibility_issues = validate_css_accessibility(css_file)
        
        all_issues = syntax_issues + accessibility_issues
        
        if all_issues:
            print(f"  Found {len(all_issues)} issues:")
            for issue in all_issues:
                print(f"    {issue}")
            total_issues += len(all_issues)
        else:
            print("  ✅ No issues found!")
        
        print()
    
    print("📊 CSS Validation Summary:")
    print(f"  Files checked: {len(css_files)}")
    print(f"  Total issues: {total_issues}")
    
    if total_issues > 0:
        print("\n⚠️  CSS validation found issues that should be addressed for better accessibility.")
    else:
        print("\n✅ All CSS files passed validation!")


if __name__ == "__main__":
    main()
