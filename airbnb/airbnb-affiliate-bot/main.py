#!/usr/bin/env python3
"""
Airbnb Affiliate Marketing Automation System
Main entry point for the automated content generation and distribution system.

Author: AI Assistant
Date: 2025-09-26
Budget: $100/mo (Free tiers only)
Target: $500/mo passive income within 3 months
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from utils.config_manager import ConfigManager
from utils.logger import setup_logging
from utils.database import DatabaseManager
from agents.trend_research_agent import TrendResearchAgent
from agents.content_generation_agent import ContentGenerationAgent
from agents.posting_agent import PostingAgent
from agents.tracking_agent import TrackingAgent


class AirbnbAffiliateBot:
    """Main orchestrator for the Airbnb affiliate marketing automation system."""
    
    def __init__(self, config_path: str = "config/config.yaml", dry_run: bool = False):
        """Initialize the bot with configuration and components."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        self.dry_run = dry_run
        
        # Setup logging
        self.logger = setup_logging(
            log_level=self.config.get('logging', {}).get('level', 'INFO'),
            log_file=self.config.get('logging', {}).get('file', 'logs/airbnb_bot.log')
        )
        
        # Initialize database
        self.db = DatabaseManager(self.config.get('database', {}).get('path', 'data/airbnb_bot.db'))
        
        # Initialize agents
        self.trend_agent = TrendResearchAgent(self.config, self.db, dry_run=dry_run)
        self.content_agent = ContentGenerationAgent(self.config, self.db, dry_run=dry_run)
        self.posting_agent = PostingAgent(self.config, self.db, dry_run=dry_run)
        self.tracking_agent = TrackingAgent(self.config, self.db, dry_run=dry_run)
        
        self.logger.info(f"AirbnbAffiliateBot initialized {'(DRY RUN MODE)' if dry_run else ''}")
    
    def run_trend_research(self):
        """Execute daily trend research workflow."""
        self.logger.info("Starting trend research workflow...")
        try:
            trends = self.trend_agent.research_trends()
            self.logger.info(f"Found {len(trends)} new trend opportunities")
            return trends
        except Exception as e:
            self.logger.error(f"Trend research failed: {e}")
            return []
    
    def run_content_generation(self, limit: int = None):
        """Execute content generation workflow."""
        self.logger.info("Starting content generation workflow...")
        try:
            content_items = self.content_agent.generate_content(limit=limit)
            self.logger.info(f"Generated {len(content_items)} content items")
            return content_items
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return []
    
    def run_posting(self, content_limit: int = None):
        """Execute automated posting workflow."""
        self.logger.info("Starting posting workflow...")
        try:
            posted_items = self.posting_agent.post_content(limit=content_limit)
            self.logger.info(f"Posted {len(posted_items)} content items")
            return posted_items
        except Exception as e:
            self.logger.error(f"Posting failed: {e}")
            return []
    
    def run_tracking_analysis(self):
        """Execute tracking and performance analysis."""
        self.logger.info("Starting tracking analysis...")
        try:
            report = self.tracking_agent.analyze_performance()
            self.logger.info("Performance analysis completed")
            return report
        except Exception as e:
            self.logger.error(f"Tracking analysis failed: {e}")
            return None
    
    def run_full_workflow(self):
        """Execute the complete automation workflow."""
        self.logger.info("=" * 50)
        self.logger.info("STARTING FULL AIRBNB AFFILIATE AUTOMATION WORKFLOW")
        self.logger.info("=" * 50)
        
        # Step 1: Research trends
        trends = self.run_trend_research()
        
        # Step 2: Generate content (limit to 5 items per run to avoid overwhelming)
        content_items = self.run_content_generation(limit=5)
        
        # Step 3: Post content (limit to 2 items per run for steady distribution)
        posted_items = self.run_posting(content_limit=2)
        
        # Step 4: Analyze performance
        report = self.run_tracking_analysis()
        
        # Summary
        self.logger.info("=" * 50)
        self.logger.info("WORKFLOW SUMMARY:")
        self.logger.info(f"- Trends researched: {len(trends)}")
        self.logger.info(f"- Content generated: {len(content_items)}")
        self.logger.info(f"- Items posted: {len(posted_items)}")
        self.logger.info(f"- Performance report: {'Generated' if report else 'Failed'}")
        self.logger.info("=" * 50)
        
        return {
            'trends': trends,
            'content_items': content_items,
            'posted_items': posted_items,
            'report': report
        }


def main():
    """Main entry point with command line interface."""
    parser = argparse.ArgumentParser(description='Airbnb Affiliate Marketing Automation System')
    parser.add_argument('--config', '-c', default='config/config.yaml', 
                       help='Path to configuration file')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Run in dry-run mode (no actual posting/API calls)')
    parser.add_argument('--mode', '-m', choices=['full', 'trends', 'content', 'post', 'track', 'dashboard'],
                       default='full', help='Execution mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        # Initialize bot
        bot = AirbnbAffiliateBot(config_path=args.config, dry_run=args.dry_run)
        
        # Execute based on mode
        if args.mode == 'full':
            result = bot.run_full_workflow()
        elif args.mode == 'trends':
            result = bot.run_trend_research()
        elif args.mode == 'content':
            result = bot.run_content_generation()
        elif args.mode == 'post':
            result = bot.run_posting()
        elif args.mode == 'track':
            result = bot.run_tracking_analysis()
        elif args.mode == 'dashboard':
            # Launch Streamlit dashboard
            import subprocess
            subprocess.run(['streamlit', 'run', 'dashboard/app.py'])
            return
        
        print(f"\n✅ Execution completed successfully!")
        if args.verbose and isinstance(result, dict):
            print(f"📊 Results: {result}")
            
    except KeyboardInterrupt:
        print("\n⚠️  Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
