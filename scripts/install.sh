#!/bin/bash

# Affiliate Bot Installation Script for macOS
# This script sets up the complete environment and dependencies

set -e  # Exit on any error

echo "🤖 Affiliate Bot - Installation Script"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

print_status "Project directory: $PROJECT_DIR"

# Step 1: Check and install Homebrew
print_step "1. Checking Homebrew installation..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    print_status "Homebrew is already installed"
fi

# Step 2: Install Python 3.12+ if not available
print_step "2. Checking Python installation..."
if ! command -v python3 &> /dev/null || [[ $(python3 -c 'import sys; print(sys.version_info >= (3, 12))') != "True" ]]; then
    print_warning "Python 3.12+ not found. Installing Python..."
    brew install python@3.12

    # Create symlink if needed
    if ! command -v python3 &> /dev/null; then
        ln -sf /opt/homebrew/bin/python3.12 /usr/local/bin/python3
    fi
else
    print_status "Python 3.12+ is available"
fi

# Step 3: Create virtual environment
print_step "3. Setting up Python virtual environment..."
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Step 4: Upgrade pip and install dependencies
print_step "4. Installing Python dependencies..."
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Dependencies installed from requirements.txt"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Step 5: Create necessary directories
print_step "5. Creating project directories..."
mkdir -p data logs content/blogs content/social content/images
print_status "Project directories created"

# Step 6: Copy and setup configuration
print_step "6. Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config_template.yaml config/config.yaml
    print_status "config.yaml created from template."
fi

# Create .env file template if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Affiliate Bot Environment Variables
# Copy this file and update with your actual API keys

# AI Services (Required - choose one)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Social Media APIs
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# Medium API
MEDIUM_ACCESS_TOKEN=your_medium_access_token

# Reddit API
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# URL Shortening & Analytics
BITLY_ACCESS_TOKEN=your_bitly_access_token

# Image APIs
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# Affiliate Configuration
AFFILIATE_LINK=your_affiliate_link

# Email Configuration
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
RECIPIENT_EMAIL=your_email@gmail.com

# Optional: Medium Publication
MEDIUM_PUBLICATION_ID=your_publication_id
EOF
    print_status ".env template created"
    print_warning "Please update .env file with your actual API keys!"
else
    print_status ".env file already exists"
fi

# Step 7: Test the installation
print_step "7. Testing installation..."
if python3 main.py test --dry-run; then
    print_status "Installation test passed!"
else
    print_error "Installation test failed. Please check the logs."
    exit 1
fi

# Step 8: Setup cron jobs (optional)
print_step "8. Setting up automation (optional)..."
read -p "Do you want to set up automated cron jobs? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Create cron setup script
    CRON_SCRIPT="$PROJECT_DIR/scripts/setup_cron.sh"
    chmod +x "$CRON_SCRIPT"
    "$CRON_SCRIPT"
    print_status "Cron jobs configured"
else
    print_status "Skipping cron setup. You can run it later with: ./scripts/setup_cron.sh"
fi

# Step 9: Create launch scripts
print_step "9. Creating launch scripts..."

# Create run script
cat > "$PROJECT_DIR/run.sh" << EOF
#!/bin/bash
# Affiliate Bot Runner Script

cd "$PROJECT_DIR"
source venv/bin/activate

# Run with arguments passed to script
python3 main.py "\$@"
EOF
chmod +x "$PROJECT_DIR/run.sh"

# Create dashboard script
cat > "$PROJECT_DIR/dashboard.sh" << EOF
#!/bin/bash
# Launch Streamlit Dashboard

cd "$PROJECT_DIR"
source venv/bin/activate

echo "🏠 Starting Affiliate Bot Dashboard..."
echo "Dashboard will be available at: http://localhost:8501"
echo "Press Ctrl+C to stop the dashboard"

streamlit run dashboard/app.py
EOF
chmod +x "$PROJECT_DIR/dashboard.sh"

print_status "Launch scripts created"

# Final instructions
echo
echo "🎉 Installation completed successfully!"
echo
echo "Next steps:"
echo "1. Update the .env file with your API keys:"
echo "   nano .env"
echo
echo "2. Test the bot in dry-run mode:"
echo "   ./run.sh test --dry-run"
echo
echo "3. Launch the dashboard:"
echo "   ./dashboard.sh"
echo
echo "4. Run the full workflow:"
echo "   ./run.sh full"
echo
echo "5. View logs:"
echo "   tail -f logs/affiliate_bot.log"
echo
print_warning "Remember to configure your API keys in the .env file before running!"
print_status "Happy affiliate marketing! 🚀"