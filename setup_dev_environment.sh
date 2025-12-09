#!/bin/bash
# TechPulse Development Environment Setup Script
# Automates the complete setup of the development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.10"
RECOMMENDED_PYTHON="3.11"

echo -e "${PURPLE}TechPulse Development Environment Setup${NC}"
echo "=============================================="

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[SETUP]${NC} $1"
}

# ==================== SYSTEM CHECKS ====================
echo -e "\n${BLUE}SYSTEM REQUIREMENTS CHECK${NC}"
echo "=============================="

# Check Python version
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_error "Python not found. Please install Python $RECOMMENDED_PYTHON or later."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

python_version=$($PYTHON_CMD --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
if [[ $(echo "$python_version >= $PYTHON_MIN_VERSION" | bc -l) -eq 1 ]]; then
    print_success "Python $python_version found"
else
    print_error "Python $PYTHON_MIN_VERSION+ required. Current version: $python_version"
    exit 1
fi

# Check pip
print_status "Checking pip installation..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    print_error "pip not found. Please install pip."
    exit 1
fi
print_success "pip found"

# Check Git
print_status "Checking Git installation..."
if ! command -v git &> /dev/null; then
    print_error "Git not found. Please install Git."
    exit 1
fi
print_success "Git found"

# Check Node.js (optional, for web development)
print_status "Checking Node.js installation..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    print_success "Node.js found: $node_version"
else
    print_warning "Node.js not found. Some web development features may be limited."
fi

# ==================== VIRTUAL ENVIRONMENT SETUP ====================
echo -e "\n${BLUE}PYTHON ENVIRONMENT SETUP${NC}"
echo "============================="

# Create virtual environment
print_step "Creating Python virtual environment..."
if [[ ! -d "venv" ]]; then
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_step "Upgrading pip..."
python -m pip install --upgrade pip
print_success "pip upgraded"

# ==================== DEPENDENCIES INSTALLATION ====================
echo -e "\n${BLUE}DEPENDENCIES INSTALLATION${NC}"
echo "=============================="

# Install production dependencies
print_step "Installing production dependencies..."
pip install -r requirements.txt
print_success "Production dependencies installed"

# Install development dependencies (if separate file exists)
if [[ -f "requirements-dev.txt" ]]; then
    print_step "Installing development dependencies..."
    pip install -r requirements-dev.txt
    print_success "Development dependencies installed"
fi

# ==================== PRE-COMMIT SETUP ====================
echo -e "\n${BLUE}PRE-COMMIT HOOKS SETUP${NC}"
echo "=========================="

# Install pre-commit
print_step "Installing pre-commit..."
pip install pre-commit
print_success "pre-commit installed"

# Install pre-commit hooks
print_step "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg
print_success "Pre-commit hooks installed"

# Run pre-commit on all files (optional)
print_step "Running pre-commit on all files..."
if pre-commit run --all-files; then
    print_success "Pre-commit checks passed"
else
    print_warning "Pre-commit found issues. Files have been auto-fixed where possible."
fi

# ==================== DATABASE SETUP ====================
echo -e "\n${BLUE}DATABASE SETUP${NC}"
echo "=================="

# Check PostgreSQL
print_status "Checking PostgreSQL installation..."
if command -v psql &> /dev/null; then
    print_success "PostgreSQL found"
    
    # Check if database connection works
    print_step "Testing database connection..."
    if python -c "
import os
import sys
sys.path.append('src')
try:
    from database.connection import get_db_connection
    conn = get_db_connection()
    if conn:
        print('Database connection successful')
        conn.close()
    else:
        print('Database connection failed')
        sys.exit(1)
except Exception as e:
    print(f'Database connection error: {e}')
    sys.exit(1)
    "; then
        print_success "Database connection successful"
    else
        print_warning "Database connection failed. Please check your database configuration."
    fi
else
    print_warning "PostgreSQL not found. Please install PostgreSQL for full functionality."
fi

# ==================== IDE CONFIGURATION ====================
echo -e "\n${BLUE}IDE CONFIGURATION${NC}"
echo "====================="

# Create VS Code settings (if VS Code is used)
print_step "Configuring VS Code settings..."
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        "htmlcov": true,
        ".coverage": true
    }
}
EOF

cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/app.py",
            "env": {
                "FLASK_ENV": "development",
                "FLASK_DEBUG": "1"
            },
            "args": [],
            "jinja": true,
            "justMyCode": true
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
EOF

print_success "VS Code configuration created"

# ==================== ENVIRONMENT FILES ====================
echo -e "\n${BLUE}ENVIRONMENT CONFIGURATION${NC}"
echo "============================="

# Create .env template if it doesn't exist
print_step "Creating environment configuration..."
if [[ ! -f ".env" ]]; then
    cat > .env << 'EOF'
# TechPulse Environment Configuration
# Copy this file and update values for your environment

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/techpulse

# External APIs (if used)
# NEWS_API_KEY=your-news-api-key
# OTHER_API_KEY=your-other-api-key

# Security Settings
SECURITY_PASSWORD_SALT=your-password-salt-here

# Email Configuration (if used)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password

# Cache Configuration
CACHE_TYPE=simple
EOF
    print_success "Environment template created (.env)"
    print_warning "Please update .env file with your actual configuration values"
else
    print_success "Environment file already exists"
fi

# ==================== GIT CONFIGURATION ====================
echo -e "\n${BLUE}GIT CONFIGURATION${NC}"
echo "===================="

# Create .gitignore if it doesn't exist
print_step "Configuring Git ignore rules..."
if [[ ! -f ".gitignore" ]]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# MacOS
.DS_Store

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# Node.js (if used)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Temporary files
*.tmp
*.temp
*.bak
*.swp
*.swo

# Production builds
build/
dist/
EOF
    print_success "Git ignore rules created"
else
    print_success "Git ignore rules already exist"
fi

# Initialize Git repository if not already initialized
if [[ ! -d ".git" ]]; then
    print_step "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: TechPulse development environment setup"
    print_success "Git repository initialized"
else
    print_success "Git repository already exists"
fi

# ==================== TESTING SETUP ====================
echo -e "\n${BLUE}TESTING FRAMEWORK SETUP${NC}"
echo "============================"

# Create test directories if they don't exist
print_step "Setting up test directories..."
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/accessibility
print_success "Test directories created"

# Run initial tests to ensure everything works
print_step "Running initial test suite..."
if python -m pytest tests/ -v --tb=short; then
    print_success "Initial tests passed"
else
    print_warning "Some tests failed. This is normal for a new setup."
fi

# ==================== FINAL STEPS ====================
echo -e "\n${BLUE}FINAL SETUP STEPS${NC}"
echo "===================="

# Create development scripts
print_step "Creating development scripts..."

# Make run_tests.sh executable
chmod +x run_tests.sh
print_success "Development scripts configured"

# ==================== SUMMARY ====================
echo -e "\n${GREEN}DEVELOPMENT ENVIRONMENT SETUP COMPLETE!${NC}"
echo "=============================================="

print_success "Your TechPulse development environment is ready!"
echo ""
echo "Next steps:"
echo "1. Update the .env file with your actual configuration"
echo "2. Set up your PostgreSQL database"
echo "3. Run './run_tests.sh' to verify everything works"
echo "4. Start developing with 'python src/app.py'"
echo ""
echo "Development commands:"
echo "• Run tests: ./run_tests.sh"
echo "• Format code: black src/ tests/"
echo "• Lint code: flake8 src/ tests/"
echo "• Type check: mypy src/"
echo "• Security scan: bandit -r src/"
echo ""
echo "Happy coding!"
