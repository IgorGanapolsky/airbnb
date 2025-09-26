#!/usr/bin/env python3
"""
Example Usage of TrendResearchAgent
Demonstrates how to use the fully functional TrendResearchAgent.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.config_manager import ConfigManager
from utils.database import DatabaseManager
from agents.trend_research_agent import TrendResearchAgent

def main():
    """Demonstrate TrendResearchAgent usage."""
    print("🚀 TrendResearchAgent Demo")
    print("=" * 50)

    # Initialize configuration and database
    config_manager = ConfigManager()
    config = config_manager.get_config()
    db = DatabaseManager()

    # Initialize the agent in dry-run mode
    agent = TrendResearchAgent(config, db, dry_run=True)

    print("\n📋 Agent Configuration:")
    print(f"• Target cities: {config.get('content', {}).get('cities', ['Nashville', 'Charleston', 'Austin', 'Portland', 'Denver'])}")
    print(f"• Dry run mode: {agent.dry_run}")
    print(f"• Max retries: {agent.max_retries}")
    print(f"• AI client available: {'Yes' if agent.ai_client else 'No (will use fallback)'}")

    print("\n🔍 Starting trend research...")
    print("Note: This will attempt to research trends for randomly selected cities")
    print("If Google Trends API fails, fallback content will be generated")

    try:
        # Research trends
        trends = agent.research_trends()

        print(f"\n✅ Research completed! Found {len(trends)} city trends")

        # Display results
        for trend in trends:
            city = trend.get('city')
            content_ideas = trend.get('content_ideas', [])
            keywords = trend.get('keywords', [])
            scores = trend.get('scores', {})

            print(f"\n🏙️ {city.upper()}")
            print("-" * 30)
            print(f"📝 Content Ideas ({len(content_ideas)}):")
            for i, idea in enumerate(content_ideas[:5], 1):  # Show first 5
                print(f"  {i}. {idea}")

            print(f"\n🔑 Keywords ({len(keywords)}):")
            print(f"  {', '.join(keywords[:10])}")  # Show first 10

            print(f"\n📊 Trend Scores:")
            for score_name, score_value in scores.items():
                print(f"  • {score_name.replace('_', ' ').title()}: {score_value:.2f}")

        print(f"\n🎯 Summary:")
        total_ideas = sum(len(t.get('content_ideas', [])) for t in trends)
        total_keywords = sum(len(t.get('keywords', [])) for t in trends)
        print(f"• Total content ideas generated: {total_ideas}")
        print(f"• Total keywords extracted: {total_keywords}")
        print(f"• Cities researched: {len(trends)}")

        if agent.dry_run:
            print("\n🧪 This was a dry run - no data was saved to database")
        else:
            print("\n💾 Data has been saved to the database")

    except Exception as e:
        print(f"\n❌ Error during trend research: {e}")
        print("This is normal if Google Trends API is not accessible or rate limited")
        print("The agent includes fallback mechanisms for production use")

    print("\n" + "=" * 50)
    print("🎉 Demo completed!")

if __name__ == "__main__":
    main()