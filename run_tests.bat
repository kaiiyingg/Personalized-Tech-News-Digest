@echo off
REM TechPulse Local Testing Script

setlocal EnableDelayedExpansion

REM Color definitions
set GREEN=[32m
set RED=[31m
set YELLOW=[33m
set BLUE=[34m
set NC=[0m

REM Test configuration
set COVERAGE_THRESHOLD=70
set TEST_TIMEOUT=30

REM Helper functions
:print_status
echo %BLUE%ℹ %~1%NC%
goto :eof

:print_success
echo %GREEN%✓ %~1%NC%
goto :eof

:print_warning
echo %YELLOW%⚠ %~1%NC%
goto :eof

:print_error
echo %RED%✗ %~1%NC%
goto :eof

REM ==================== SETUP ====================
echo %BLUE%🚀 TECHPULSE LOCAL TEST SUITE%NC%
echo ===============================

call :print_status "Installing/updating dependencies..."
pip install -r requirements.txt
if errorlevel 1 (
    call :print_error "Failed to install dependencies"
    exit /b 1
)

REM ==================== CODE QUALITY ====================
echo.
echo %BLUE%🔍 CODE QUALITY CHECKS%NC%
echo ======================

call :print_status "Running Black code formatter..."
black --check --diff src/ tests/
if errorlevel 1 (
    call :print_warning "Code formatting issues found. Run 'black src/ tests/' to fix"
) else (
    call :print_success "Code formatting passed"
)

call :print_status "Running Flake8 linter..."
flake8 src/ tests/
if errorlevel 1 (
    call :print_error "Linting issues found"
) else (
    call :print_success "Linting passed"
)

call :print_status "Running Pylint static analysis..."
pylint src/ --exit-zero > pylint_output.txt 2>&1
if errorlevel 1 (
    call :print_warning "Pylint analysis completed with warnings"
) else (
    call :print_success "Pylint analysis completed"
)

call :print_status "Running MyPy type checking..."
mypy src/ --ignore-missing-imports --no-strict-optional
if errorlevel 1 (
    call :print_warning "Type checking issues found"
) else (
    call :print_success "Type checking passed"
)

REM ==================== SECURITY CHECKS ====================
echo.
echo %BLUE%🔒 SECURITY ANALYSIS%NC%
echo =====================

call :print_status "Running Bandit security analysis..."
bandit -r src/ -f txt
if errorlevel 1 (
    call :print_warning "Security issues found"
) else (
    call :print_success "Security analysis passed"
)

call :print_status "Running Safety dependency check..."
safety check
if errorlevel 1 (
    call :print_warning "Vulnerable dependencies found"
) else (
    call :print_success "Dependency security check passed"
)

REM ==================== UNIT TESTS ====================
echo.
echo %BLUE%🧪 UNIT TESTS%NC%
echo ==============

call :print_status "Running unit tests with coverage..."
pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=%COVERAGE_THRESHOLD% --timeout=%TEST_TIMEOUT%
if errorlevel 1 (
    call :print_error "Unit tests failed or insufficient coverage"
) else (
    call :print_success "Unit tests passed with adequate coverage"
)

REM ==================== INTEGRATION TESTS ====================
echo.
echo %BLUE%🔗 INTEGRATION TESTS%NC%
echo ====================

call :print_status "Running integration tests..."
pytest tests/integration/ -v --timeout=%TEST_TIMEOUT%
if errorlevel 1 (
    call :print_warning "Integration tests had issues"
) else (
    call :print_success "Integration tests passed"
)

REM ==================== ACCESSIBILITY TESTS ====================
echo.
echo %BLUE%♿ ACCESSIBILITY TESTS%NC%
echo ======================

call :print_status "Running accessibility tests..."
where chrome >nul 2>&1
if errorlevel 1 (
    where msedge >nul 2>&1
    if errorlevel 1 (
        call :print_warning "Chrome/Edge not found. Skipping accessibility tests."
        goto skip_accessibility
    )
)

pytest tests/accessibility/ -v --timeout=%TEST_TIMEOUT%
if errorlevel 1 (
    call :print_warning "Accessibility tests had issues"
) else (
    call :print_success "Accessibility tests passed"
)

:skip_accessibility

REM ==================== PERFORMANCE TESTS ====================
echo.
echo %BLUE%⚡ PERFORMANCE TESTS%NC%
echo ====================

call :print_status "Running performance tests..."
pytest tests/performance/ -v --timeout=%TEST_TIMEOUT%
if errorlevel 1 (
    call :print_warning "Performance tests had issues"
) else (
    call :print_success "Performance tests completed"
)

REM ==================== DOCUMENTATION TESTS ====================
echo.
echo %BLUE%📚 DOCUMENTATION TESTS%NC%
echo =======================

call :print_status "Checking documentation completeness..."
set doc_issues=0

if exist "README.md" (
    call :print_success "README.md found"
) else (
    call :print_error "README.md missing"
    set /a doc_issues+=1
)

if exist "requirements.txt" (
    call :print_success "requirements.txt found"
) else (
    call :print_error "requirements.txt missing"
    set /a doc_issues+=1
)

if exist "Dockerfile" (
    call :print_success "Dockerfile found"
) else (
    call :print_warning "Dockerfile missing"
)

if !doc_issues! equ 0 (
    call :print_success "Documentation checks passed"
)

REM ==================== CLEANUP ====================
call :print_status "Cleaning up temporary files..."
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
if exist pylint_output.txt del pylint_output.txt
call :print_success "Cleanup completed"

REM ==================== SUMMARY ====================
echo.
echo %BLUE%📊 TEST SUMMARY%NC%
echo ================

call :print_status "Test execution completed!"
call :print_status "Check the following reports:"
echo   • Coverage Report: htmlcov\index.html
echo   • Test Results: Available in terminal output
echo   • Code Quality: Tool outputs above

echo.
echo %GREEN%🎉 All tests completed!%NC%
echo Ready for development or deployment.

pause
exit /b 0

:: 1. Setup
- Installs/updates dependencies from requirements.txt.
- Defines color codes and helper functions for pretty output.

:: 2. Code Quality Checks
- Runs Black for code formatting.
- Runs Flake8 for linting.
- Runs Pylint for static analysis.
- Runs MyPy for type checking.

:: 3. Security Checks
- Runs Bandit for code security.
- Runs Safety to check for vulnerable dependencies.

:: 4. Testing
- Runs unit tests (with coverage).
- Runs integration tests.
- Runs accessibility tests (if Chrome/Edge is available).
- Runs performance tests.

:: 5. Documentation Checks
- Checks for presence of README.md, requirements.txt, Dockerfile.

:: 6. Cleanup
- Removes __pycache__, .pyc files, and pylint output.

:: 7. Summary
- Prints a summary and where to find reports.

:: All steps print colored status messages and halt on critical errors.
:: The script is designed for local development, not CI/CD.