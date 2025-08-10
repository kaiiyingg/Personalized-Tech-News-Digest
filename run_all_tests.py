"""
Test runner script for comprehensive test execution

This script runs all tests in the organized test suite:
- Service tests
- Unit tests (app routes)
- Integration tests
- Accessibility tests

Usage:
    python run_all_tests.py
    python run_all_tests.py --coverage
    python run_all_tests.py --services-only
    python run_all_tests.py --integration-only
    python run_all_tests.py --accessibility-only
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))


def run_command(command, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {description}")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"FAILED: Command not found - {command[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def run_service_tests(coverage=False):
    """Run service layer tests"""
    base_cmd = ['python', '-m', 'pytest', 'tests/services/', '-v']
    if coverage:
        base_cmd.extend(['--cov=src/services', '--cov-report=term-missing'])
    
    return run_command(base_cmd, "Service Tests")


def run_unit_tests(coverage=False):
    """Run unit tests (app routes)"""
    base_cmd = ['python', '-m', 'pytest', 'tests/unit/', '-v']
    if coverage:
        base_cmd.extend(['--cov=src/app', '--cov-report=term-missing'])
    
    return run_command(base_cmd, "Unit Tests (App Routes)")


def run_integration_tests(coverage=False):
    """Run integration tests"""
    base_cmd = ['python', '-m', 'pytest', 'tests/integration/', '-v']
    if coverage:
        base_cmd.extend(['--cov=src', '--cov-report=term-missing'])
    
    return run_command(base_cmd, "Integration Tests")


def run_accessibility_tests():
    """Run accessibility tests"""
    base_cmd = ['python', '-m', 'pytest', 'tests/accessibility/', '-v']
    
    return run_command(base_cmd, "Accessibility Tests")


def run_all_tests(coverage=False):
    """Run all tests in sequence"""
    print("Running comprehensive test suite...")
    print(f"Coverage reporting: {'Enabled' if coverage else 'Disabled'}")
    
    results = []
    
    # Run each test category
    results.append(("Service Tests", run_service_tests(coverage)))
    results.append(("Unit Tests", run_unit_tests(coverage)))
    results.append(("Integration Tests", run_integration_tests(coverage)))
    results.append(("Accessibility Tests", run_accessibility_tests()))
    
    # Generate coverage report if requested
    if coverage:
        print(f"\n{'='*60}")
        print("Generating Combined Coverage Report")
        print(f"{'='*60}")
        
        coverage_cmd = [
            'python', '-m', 'pytest', 
            'tests/', 
            '--cov=src', 
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=xml:coverage.xml'
        ]
        run_command(coverage_cmd, "Combined Coverage Report")
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST EXECUTION SUMMARY")
    print(f"{'='*60}")
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name:<20}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if coverage:
        print("\nCoverage reports generated:")
        print("- HTML report: htmlcov/index.html")
        print("- XML report: coverage.xml")
    
    return all_passed


def install_dependencies():
    """Install required test dependencies"""
    print("Installing test dependencies...")
    
    dependencies = [
        'pytest',
        'pytest-cov',
        'beautifulsoup4',
        'mock'
    ]
    
    for dep in dependencies:
        cmd = ['pip', 'install', dep]
        success = run_command(cmd, f"Installing {dep}")
        if not success:
            print(f"Failed to install {dep}")
            return False
    
    return True


def check_environment():
    """Check if the test environment is properly set up"""
    print("Checking test environment...")
    
    # Check if pytest is available
    try:
        subprocess.run(['python', '-m', 'pytest', '--version'], 
                      capture_output=True, check=True)
        print("✓ pytest is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ pytest not found")
        return False
    
    # Check if src directory exists
    if not (Path(__file__).parent / 'src').exists():
        print("✗ src directory not found")
        return False
    print("✓ src directory found")
    
    # Check if test directories exist
    test_dirs = ['tests/services', 'tests/unit', 'tests/integration', 'tests/accessibility']
    for test_dir in test_dirs:
        if not (Path(__file__).parent / test_dir).exists():
            print(f"✗ {test_dir} directory not found")
            return False
        print(f"✓ {test_dir} directory found")
    
    return True


def main():
    """Main function to handle command line arguments and run tests"""
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('--coverage', action='store_true', 
                       help='Generate coverage reports')
    parser.add_argument('--services-only', action='store_true',
                       help='Run only service tests')
    parser.add_argument('--unit-only', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration-only', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--accessibility-only', action='store_true',
                       help='Run only accessibility tests')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install required test dependencies')
    parser.add_argument('--check-env', action='store_true',
                       help='Check test environment setup')
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Handle special commands
    if args.install_deps:
        success = install_dependencies()
        sys.exit(0 if success else 1)
    
    if args.check_env:
        success = check_environment()
        sys.exit(0 if success else 1)
    
    # Check environment before running tests
    if not check_environment():
        print("\nEnvironment check failed. Run with --install-deps to install dependencies.")
        sys.exit(1)
    
    # Run specific test categories
    if args.services_only:
        success = run_service_tests(args.coverage)
    elif args.unit_only:
        success = run_unit_tests(args.coverage)
    elif args.integration_only:
        success = run_integration_tests(args.coverage)
    elif args.accessibility_only:
        success = run_accessibility_tests()
    else:
        # Run all tests
        success = run_all_tests(args.coverage)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
