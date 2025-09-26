#!/bin/bash
# Test script for Airbnb Affiliate Bot

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✅]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[🔧]${NC} $1"
}

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BOT_DIR"

echo "🧪 Testing Airbnb Affiliate Bot Setup..."
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Run ./scripts/install.sh first."
    exit 1
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate

# Test Python dependencies
print_step "Testing Python dependencies..."
python3 -c "
import sys
required_modules = [
    'yaml', 'openai', 'anthropic', 'requests', 'beautifulsoup4', 'pytrends',
    'tweepy', 'praw', 'pandas', 'streamlit', 'schedule', 'bitlyshortener',
    'pillow', 'matplotlib', 'seaborn', 'plotly'
]

missing = []
for module in required_modules:
    try:
        if module == 'yaml':
            import yaml
        elif module == 'beautifulsoup4':
            import bs4
        elif module == 'pillow':
            import PIL
        else:
            __import__(module)
        print(f'✅ {module}')
    except ImportError:
        missing.append(module)
        print(f'❌ {module}')

if missing:
    print(f'Missing modules: {missing}')
    print('Run: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ All required modules available')
"

# Test configuration
echo "⚙️ Testing configuration..."
python3 -c "
import sys
sys.path.append('.')
try:
    from utils.config_loader import config
    cfg = config.config
    print('✅ Configuration loaded successfully')

    # Check critical settings
    if cfg.get('affiliate', {}).get('booking_link', '') == 'YOUR_BOOKING_AFFILIATE_LINK':
        print('⚠️  Warning: Booking.com affiliate link not configured')
    else:
        print('✅ Booking.com affiliate link configured')

    if cfg.get('ai', {}).get('openai', {}).get('api_key', '') == 'sk-...':
        print('⚠️  Warning: OpenAI API key not configured')
    else:
        print('✅ OpenAI API key configured')

except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

# Test database initialization
echo "🗄️ Testing database..."
python3 -c "
import sys
sys.path.append('.')
try:
    from utils.database import Database
    db = Database('data/test_db.db')
    print('✅ Database connection successful')

    # Clean up test database
    import os
    os.remove('data/test_db.db')

except Exception as e:
    print(f'❌ Database error: {e}')
    sys.exit(1)
"

# Test trend research (dry run)
echo "🔍 Testing trend research..."
python3 main.py research --dry-run

# Test content generation (dry run)
echo "✍️ Testing content generation..."
python3 main.py generate --dry-run

# Test posting system (dry run)
echo "📤 Testing posting system..."
python3 main.py post --dry-run

# Test analytics
echo "📊 Testing analytics..."
python3 main.py analytics --dry-run

echo ""
echo "🎉 All tests passed successfully!"
echo ""
echo "📋 Test Summary:"
echo "✅ Dependencies installed correctly"
echo "✅ Configuration file readable"
echo "✅ Database connection working"
echo "✅ All core modules functional"
echo ""
echo "🚀 Ready to start generating content!"
echo ""
echo "Next steps:"
echo "1. Configure your API keys in config/config.yaml"
echo "2. Run a full test: python3 main.py test"
echo "3. Start automated posting: ./scripts/setup_cron.sh"
echo "4. Monitor with dashboard: python3 main.py dashboard"