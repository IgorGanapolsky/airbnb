#!/bin/bash
# Setup cron jobs for automated posting

set -e

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH="$BOT_DIR/venv/bin/python3"
MAIN_SCRIPT="$BOT_DIR/main.py"

echo "🕒 Setting up cron jobs for Booking.com Affiliate Bot..."
echo "Bot directory: $BOT_DIR"

# Create cron job entries
CRON_JOBS="
# Booking.com Affiliate Bot - Automated Content Generation & Posting
# Research trends daily at 6 AM
0 6 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT research >> logs/cron.log 2>&1

# Generate content daily at 8 AM
0 8 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT generate >> logs/cron.log 2>&1

# Post content 3 times per day
0 10 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT post >> logs/cron.log 2>&1
0 14 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT post >> logs/cron.log 2>&1
0 18 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT post >> logs/cron.log 2>&1

# Update analytics daily at 10 PM
0 22 * * * cd $BOT_DIR && $PYTHON_PATH $MAIN_SCRIPT analytics >> logs/cron.log 2>&1
"

# Backup existing crontab
echo "📋 Backing up existing crontab..."
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || echo "No existing crontab found"

# Add new cron jobs
echo "➕ Adding cron jobs..."
(crontab -l 2>/dev/null || true; echo "$CRON_JOBS") | crontab -

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "📅 Scheduled jobs:"
echo "  • 06:00 - Research trending content ideas"
echo "  • 08:00 - Generate blog posts and social content"
echo "  • 10:00 - Post content to Medium, Twitter, Reddit"
echo "  • 14:00 - Post content to Medium, Twitter, Reddit"
echo "  • 18:00 - Post content to Medium, Twitter, Reddit"
echo "  • 22:00 - Update analytics and send reports"
echo ""
echo "📊 Monitor logs:"
echo "  tail -f logs/cron.log"
echo ""
echo "🛑 To remove cron jobs:"
echo "  crontab -e  # Remove the Booking.com Bot entries"
echo ""
echo "⚠️  Note: Make sure your config/config.yaml is properly configured"
echo "   before the first automated run!"

# Create log file if it doesn't exist
touch "$BOT_DIR/logs/cron.log"
echo "📝 Log file created: logs/cron.log"