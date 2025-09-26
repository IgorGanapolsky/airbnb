#!/bin/bash
# Booking.com Affiliate Bot Installation Script for macOS

set -e

echo "🚀 Setting up Booking.com Affiliate Bot..."

# Check if Python 3.12+ is available
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12+ first."
    echo "Install via Homebrew: brew install python@3.12"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.12"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.12+ required. Current version: $PYTHON_VERSION"
    echo "Install via Homebrew: brew install python@3.12"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "✅ Homebrew detected"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p content/blogs
mkdir -p content/social
mkdir -p content/images

# Copy config template
echo "⚙️ Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config_template.yaml config/config.yaml
    echo "📝 Created config/config.yaml from template"
    echo "⚠️  Please edit config/config.yaml with your API keys and settings"
else
    echo "✅ config/config.yaml already exists"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.sh
chmod +x main.py

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
import sys
sys.path.append('.')
from utils.database import Database
db = Database('data/booking_bot.db')
print('✅ Database initialized')
"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit config/config.yaml with your API keys:"
echo "   • OpenAI API key"
echo "   • Booking.com affiliate link (from affiliates.booking.com)"
echo "   • Twitter API credentials"
echo "   • Medium integration token"
echo "   • Reddit API credentials"
echo "   • Bitly access token"
echo ""
echo "2. Test the installation:"
echo "   ./scripts/test.sh"
echo ""
echo "3. Run your first content generation:"
echo "   python3 main.py test"
echo ""
echo "4. Set up automated posting:"
echo "   ./scripts/setup_cron.sh"
echo ""
echo "5. View analytics dashboard:"
echo "   python3 main.py dashboard"
echo ""
echo "💡 Pro tip: Start with dry-run mode to test everything:"
echo "   python3 main.py full --dry-run"
echo ""
echo "📚 For detailed setup instructions, see README.md"