# TechPulse Testing Guide

A concise guide for running and understanding tests and code quality checks.

## Quick Start

**Recommended:**  
```bat
run_tests.bat
```
Runs all tests, code quality, and security checks.

**Manual:**  
```bash
pip install -r requirements.txt
pytest tests/ -v --cov=src --cov-report=html
```

## Test Types

- **Unit:** `tests/unit/` – Individual components
- **Integration:** `tests/integration/` – System interactions
- **Accessibility:** `tests/accessibility/` – WCAG compliance
- **Performance:** `tests/performance/` – Load/optimization

## Code Quality & Security

Run individually if needed:
```bash
black --check --diff src/ tests/
flake8 src/ tests/
pylint src/
mypy src/
bandit -r src/
```

## Reports

- Coverage: `htmlcov/index.html`
- Lint/Security: Terminal output after running `run_tests.bat`

## Troubleshooting

- Ensure PostgreSQL is running for DB tests.
- Chrome/Edge required for accessibility tests.
- Update `.env` for your environment.

## Add Tests

- Place new tests in the appropriate `tests/` subfolder.
- Use descriptive names and pytest conventions.

## More Info

See `README.md` for project structure and further details.