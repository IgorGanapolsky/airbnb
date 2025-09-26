#!/usr/bin/env python3
"""
Affiliate Bot - Main Controller
Automated content generation and posting system for affiliate marketing.
"""

import argparse
import logging
import sys
from pathlib import Path
import schedule
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.database import DatabaseManager
from utils.logger import setup_logging
from agents.trend_research_agent import TrendResearchAgent
from agents.content_generation_agent import ContentGenerationAgent
from agents.posting_agent import PostingAgent
from agents.tracking_agent import TrackingAgent

# Configure logging
logger = setup_logging()

class AffiliateBot:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_config()
        
        db_path = self.config.get('database', {}).get('path', 'data/airbnb_bot.db')
        self.db = DatabaseManager(db_path)
        
        # Initialize agents
        self.trend_agent = TrendResearchAgent(self.config, self.db, self.dry_run)
        self.content_agent = ContentGenerationAgent(self.config, self.db, self.dry_run)
        self.posting_agent = PostingAgent(self.config, self.db, self.dry_run)
        self.tracking_agent = TrackingAgent(self.config, self.db, self.dry_run)

        # Ensure logs directory exists
        Path('logs').mkdir(exist_ok=True)

    def run_trend_research(self):
        """Research new trends and content ideas"""
        logger.info("🔍 Starting trend research...")
        try:
            trends = self.trend_agent.research_trends()
            logger.info(f"✅ Found {len(trends)} new trends/ideas")
            for trend in trends:
                logger.info(f"  • {trend.get('city')}: {len(trend.get('content_ideas', []))} ideas")
        except Exception as e:
            logger.error(f"❌ Trend research failed: {e}", exc_info=True)

    def run_content_generation(self):
        """Generate content from pending trends"""
        logger.info("✍️ Starting content generation...")
        try:
            content_pieces = self.content_agent.generate_content()
            logger.info(f"✅ Generated {len(content_pieces)} content pieces")
            for content in content_pieces:
                logger.info(f"  • {content.get('content_type')}: {content.get('title', 'N/A')[:60]}...")
        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}", exc_info=True)

    def run_posting(self):
        """Post unpublished content to social platforms"""
        logger.info("📤 Starting content posting...")
        try:
            results = self.posting_agent.post_content()
            successful = [r for r in results if r.get('status') == 'posted' or r.get('status') == 'dry_run']
            failed = [r for r in results if r.get('status') not in ['posted', 'dry_run']]

            logger.info(f"✅ Successfully posted {len(successful)} items")
            if failed:
                logger.warning(f"⚠️ {len(failed)} posts failed")
        except Exception as e:
            logger.error(f"❌ Posting failed: {e}", exc_info=True)

    def run_analytics_update(self):
        """Update analytics data from tracking sources"""
        logger.info("📊 Updating analytics...")
        try:
            report = self.tracking_agent.analyze_performance()
            summary = report.get('summary', {})
            logger.info(f"📈 Analytics summary: "
                        f"Grade: {summary.get('performance_grade', 'N/A')}, "
                        f"Revenue: ${summary.get('estimated_revenue', 0):.2f}, "
                        f"Clicks: {summary.get('total_clicks', 0)}")
        except Exception as e:
            logger.error(f"❌ Analytics update failed: {e}", exc_info=True)

    def run_full_cycle(self):
        """Run complete automation cycle"""
        logger.info("🚀 Starting full automation cycle...")
        self.run_trend_research()
        time.sleep(5)
        self.run_content_generation()
        time.sleep(5)
        self.run_posting()
        time.sleep(5)
        self.run_analytics_update()
        logger.info("✨ Full cycle completed!")

    def start_scheduler(self):
        """Start the scheduled automation"""
        logger.info("⏰ Starting scheduler...")
        
        schedule.every().day.at("06:00").do(self.run_trend_research)
        schedule.every().day.at("08:00").do(self.run_content_generation)
        schedule.every(4).hours.do(self.run_posting) # Post every 4 hours
        schedule.every().day.at("22:00").do(self.run_analytics_update)

        logger.info("📅 Scheduled jobs:")
        logger.info("  • 06:00 - Trend Research")
        logger.info("  • 08:00 - Content Generation")
        logger.info("  • Every 4 hours - Content Posting")
        logger.info("  • 22:00 - Analytics Update")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")

    def test_mode(self):
        """Run in test mode without posting"""
        logger.info("🧪 Running in test mode (dry run)...")
        self.run_full_cycle()
        logger.info("✅ Test mode completed")

def main():
    parser = argparse.ArgumentParser(description="Affiliate Bot")
    parser.add_argument(
        'command',
        choices=['research', 'generate', 'post', 'analytics', 'full', 'schedule', 'test', 'dashboard'],
        help='Command to run'
    )
    parser.add_argument(
        '--dry-run', action='store_true', help='Run without actual posting/database changes'
    )
    parser.add_argument(
        '--verbose', action='store_true', help='Enable verbose logging'
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    bot = AffiliateBot(dry_run=args.dry_run)

    if args.dry_run:
        logger.info("🧪 Dry run mode enabled via command line")

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
            logger.info("Run: streamlit run dashboard/app.py")
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
