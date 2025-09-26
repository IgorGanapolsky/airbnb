#!/bin/bash
# Setup cron jobs for Airbnb Affiliate Bot automation

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$BOT_DIR/venv/bin/python3"
MAIN_SCRIPT="$BOT_DIR/main.py"

echo "🕒 Setting up cron jobs for Airbnb Affiliate Bot..."
print_status "Bot directory: $BOT_DIR"

# Verify the main script exists
if [ ! -f "$MAIN_SCRIPT" ]; then
    print_warning "Main script not found at $MAIN_SCRIPT"
    exit 1
fi

# Create cron job entries based on config schedule
CRON_JOBS="
# Airbnb Affiliate Bot - Automated Content Generation & Posting
# Research trends daily at 6 AM
0 6 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT --mode trends >> logs/cron.log 2>&1

# Generate content daily at 8 AM
0 8 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT --mode content >> logs/cron.log 2>&1

# Post content twice per day (10 AM and 4 PM)
0 10 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT --mode post >> logs/cron.log 2>&1
0 16 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT --mode post >> logs/cron.log 2>&1

# Update analytics daily at 8 PM
0 20 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT --mode track >> logs/cron.log 2>&1

# Full workflow check weekly on Sundays at 9 AM
0 9 * * 0 cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT --mode full >> logs/cron.log 2>&1
"

# Backup existing crontab
print_step "Backing up existing crontab..."
BACKUP_FILE="crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$BACKUP_FILE" 2>/dev/null || print_warning "No existing crontab found"

# Check if bot cron jobs already exist
if crontab -l 2>/dev/null | grep -q "Airbnb Affiliate Bot"; then
    print_warning "Airbnb Affiliate Bot cron jobs already exist!"
    echo "Do you want to replace them? (y/n): "
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cron setup cancelled"
        exit 0
    fi

    # Remove existing bot cron jobs
    print_step "Removing existing bot cron jobs..."
    crontab -l 2>/dev/null | grep -v "Airbnb Affiliate Bot" | grep -v "cd $BOT_DIR" | crontab -
fi

# Add new cron jobs
print_step "Adding new cron jobs..."
(crontab -l 2>/dev/null || true; echo "$CRON_JOBS") | crontab -

# Create log file if it doesn't exist
mkdir -p "$BOT_DIR/logs"
touch "$BOT_DIR/logs/cron.log"

echo ""
print_status "Cron jobs installed successfully!"
echo ""
echo "📅 Scheduled automation:"
echo "  • 06:00 Daily - Research trending content ideas"
echo "  • 08:00 Daily - Generate blog posts and social content"
echo "  • 10:00 Daily - Post content to platforms"
echo "  • 16:00 Daily - Post content to platforms"
echo "  • 20:00 Daily - Update analytics and tracking"
echo "  • 09:00 Weekly (Sunday) - Full workflow check"
echo ""
echo "📊 Monitor automation:"
echo "  tail -f logs/cron.log"
echo ""
echo "🔍 View current cron jobs:"
echo "  crontab -l"
echo ""
echo "🛑 To remove cron jobs:"
echo "  crontab -e  # Remove the Airbnb Affiliate Bot entries"
echo ""
print_warning "Make sure your .env file and config/config.yaml are properly configured!"
print_status "Automation setup complete! 🚀"