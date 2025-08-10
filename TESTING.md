# Testing Guide

Complete testing setup for TechPulse with full unit test coverage.

## Quick Start

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Run all tests:**
   ```
   pytest
   ```

3. **Or use the batch script:**
   ```
   run_tests.bat
   ```

## Test Coverage

### Core Services
- **test_content_service.py** - Article fetching, processing, favorites
- **test_user_service.py** - User authentication, profile management
- **test_source_service.py** - RSS feed management and syncing

### User Interface
- **test_fast_view.py** - Fast article browsing, heart buttons, pagination
- **test_accessibility.py** - UI accessibility compliance (requires Chrome)

### Data Processing
- **test_html_cleaning.py** - Content sanitization and security
- **test_db_connection.py** - Database connectivity and operations

### Performance & Quality
- **test_improvements.py** - Performance benchmarks and load testing
- **test_optimizations.py** - Caching, query optimization, memory usage

## Running Specific Tests

```bash
# Test a specific file
pytest tests/test_content_service.py

# Test with coverage
pytest --cov=src --cov-report=html

# Test specific function
pytest tests/test_fast_view.py::TestFastView::test_heart_button_functionality
```

## Code Quality

The `run_tests.bat` script also runs:
- **black** - Code formatting check
- **flake8** - Code style and complexity check  
- **bandit** - Security vulnerability scanning

## Test Categories

- **Unit Tests** - Individual function/class testing
- **Integration Tests** - Component interaction testing
- **Performance Tests** - Load and speed testing
- **Security Tests** - XSS, SQL injection prevention
- **Accessibility Tests** - Screen reader and WCAG compliance

## Environment

Tests use your `.env` file for database settings. Make sure PostgreSQL is configured.

## Adding New Tests

When adding new features, create corresponding test files:
1. Follow the naming convention `test_feature_name.py`
2. Use descriptive test method names
3. Include setup and teardown methods
4. Mock external dependencies
5. Test both success and failure cases