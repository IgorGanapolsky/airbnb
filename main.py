#!/usr/bin/env python3
"""
Booking.com Affiliate Bot - Main Controller
Automated content generation and posting system for Booking.com affiliate marketing.
"""

import argparse
import logging
import sys
from pathlib import Path
import schedule
import time
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.config_loader import config
from utils.database import Database
from agents.trend_research import TrendResearchAgent
from agents.content_generator import ContentGenerator
from agents.auto_poster import AutoPoster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class BookingAffiliateBot:
    def __init__(self):
        self.config = config.config
        self.db = Database(self.config['system']['database_path'])
        self.trend_agent = TrendResearchAgent()
        self.content_agent = ContentGenerator()
        self.posting_agent = AutoPoster()

        # Ensure logs directory exists
        Path('logs').mkdir(exist_ok=True)

    def run_trend_research(self):
        """Research new trends and content ideas"""
        logger.info("🔍 Starting trend research...")

        try:
            trends = self.trend_agent.research_trends(num_cities=3)
            logger.info(f"✅ Generated {len(trends)} new content ideas")

            for trend in trends:
                logger.info(f"  • {trend['city']}: {trend['idea']}")

        except Exception as e:
            logger.error(f"❌ Trend research failed: {e}")

    def run_content_generation(self):
        """Generate content from pending trends"""
        logger.info("✍️ Starting content generation...")

        try:
            content_pieces = self.content_agent.generate_content_for_trends(limit=5)
            logger.info(f"✅ Generated {len(content_pieces)} content pieces")

            for content in content_pieces:
                logger.info(f"  • {content['type']}: {content['title'][:60]}...")

        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}")

    def run_posting(self):
        """Post unpublished content to social platforms"""
        logger.info("📤 Starting content posting...")

        try:
            results = self.posting_agent.post_scheduled_content(limit=5)
            successful = [r for r in results if r['status'] == 'success']
            failed = [r for r in results if r['status'] == 'error']

            logger.info(f"✅ Successfully posted {len(successful)} items")
            if failed:
                logger.warning(f"⚠️ {len(failed)} posts failed")

            # Send summary email
            self.posting_agent.send_posting_summary(results)

        except Exception as e:
            logger.error(f"❌ Posting failed: {e}")

    def run_analytics_update(self):
        """Update analytics data from tracking sources"""
        logger.info("📊 Updating analytics...")

        try:
            # This would typically fetch data from Bitly, social platform APIs, etc.
            # For now, we'll implement basic tracking
            stats = self.posting_agent.get_posting_stats()
            logger.info(f"📈 Current stats: {stats['total_posts_30_days']} posts, "
                       f"{stats['total_clicks']} clicks, ${stats['estimated_revenue']:.2f} revenue")

        except Exception as e:
            logger.error(f"❌ Analytics update failed: {e}")

    def run_full_cycle(self):
        """Run complete automation cycle"""
        logger.info("🚀 Starting full automation cycle...")

        # Run in sequence with delays
        self.run_trend_research()
        time.sleep(30)

        self.run_content_generation()
        time.sleep(30)

        self.run_posting()
        time.sleep(30)

        self.run_analytics_update()

        logger.info("✨ Full cycle completed!")

    def start_scheduler(self):
        """Start the scheduled automation"""
        logger.info("⏰ Starting scheduler...")

        # Schedule jobs based on config
        schedule.every().day.at("06:00").do(self.run_trend_research)
        schedule.every().day.at("08:00").do(self.run_content_generation)
        schedule.every().day.at("10:00").do(self.run_posting)
        schedule.every().day.at("14:00").do(self.run_posting)
        schedule.every().day.at("18:00").do(self.run_posting)
        schedule.every().day.at("22:00").do(self.run_analytics_update)

        logger.info("📅 Scheduled jobs:")
        logger.info("  • 06:00 - Trend Research")
        logger.info("  • 08:00 - Content Generation")
        logger.info("  • 10:00, 14:00, 18:00 - Content Posting")
        logger.info("  • 22:00 - Analytics Update")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")

    def test_mode(self):
        """Run in test mode without posting"""
        logger.info("🧪 Running in test mode...")

        # Temporarily enable dry run
        original_dry_run = self.config['system']['dry_run']
        self.config['system']['dry_run'] = True

        try:
            self.run_full_cycle()
        finally:
            # Restore original setting
            self.config['system']['dry_run'] = original_dry_run

        logger.info("✅ Test mode completed")

def main():
    parser = argparse.ArgumentParser(description="Booking.com Affiliate Bot")

    parser.add_argument(
        'command',
        choices=['research', 'generate', 'post', 'analytics', 'full', 'schedule', 'test', 'dashboard'],
        help='Command to run'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without actually posting content'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize bot
    bot = BookingAffiliateBot()

    # Override dry run if specified
    if args.dry_run:
        bot.config['system']['dry_run'] = True
        logger.info("🧪 Dry run mode enabled")

    # Execute command
    try:
        if args.command == 'research':
            bot.run_trend_research()

        elif args.command == 'generate':
            bot.run_content_generation()

        elif args.command == 'post':
            bot.run_posting()

        elif args.command == 'analytics':
            bot.run_analytics_update()

        elif args.command == 'full':
            bot.run_full_cycle()

        elif args.command == 'schedule':
            bot.start_scheduler()

        elif args.command == 'test':
            bot.test_mode()

        elif args.command == 'dashboard':
            logger.info("🌐 Starting dashboard...")
            logger.info("Run: streamlit run dashboard/analytics_dashboard.py")
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/analytics_dashboard.py"])

    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()