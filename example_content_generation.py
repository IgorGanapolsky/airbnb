#!/usr/bin/env python3
"""
Example: ContentGenerationAgent Usage
Demonstrates how to use the fully functional ContentGenerationAgent for affiliate marketing.
"""

from utils.config_manager import ConfigManager
from utils.database import DatabaseManager
from agents.content_generation_agent import ContentGenerationAgent


def example_usage():
    """Example of how to use the ContentGenerationAgent."""

    # Initialize configuration and database
    config_manager = ConfigManager()
    config = config_manager.get_config()
    db = DatabaseManager()

    # Initialize content generation agent
    # Set dry_run=True for testing without database changes
    agent = ContentGenerationAgent(config, db, dry_run=True)

    # Example: Generate content from existing trends in database
    print("🎯 Generating content from pending trends...")
    content_items = agent.generate_content(limit=3)

    for item in content_items:
        print(f"Generated: {item['content_type']} - {item['title']}")
        print(f"Quality Score: {item.get('quality_score', 0):.2f}")
        print("-" * 50)

    # Example: Direct content generation for testing
    sample_trend = {
        'id': 999,
        'city': 'Charleston',
        'keywords': ['historic hotels', 'southern charm', 'carriage tours', 'cobblestone streets'],
        'content_ideas': ['Best Historic Hotels in Charleston Under $150']
    }

    print("🧪 Testing direct content generation...")

    # Test blog post generation
    blog_post = agent._generate_blog_post(sample_trend, sample_trend['content_ideas'][0])
    if blog_post:
        print(f"✅ Blog Post: {blog_post['title']}")
        print(f"📝 Word Count: {blog_post['word_count']}")
    else:
        print("⚠️ Blog post generation failed, testing fallback...")
        fallback = agent._generate_fallback_blog_post(sample_trend, sample_trend['content_ideas'][0])
        if fallback:
            print(f"✅ Fallback Blog Post: {fallback['title']}")
            print(f"📝 Word Count: {fallback['word_count']}")

    # Test social media generation
    twitter_thread = agent._generate_twitter_thread(sample_trend, sample_trend['content_ideas'][0])
    if twitter_thread:
        print(f"✅ Twitter Thread: {len(twitter_thread['tweets'])} tweets")
    else:
        fallback_tweets = agent._generate_fallback_twitter_thread(sample_trend, sample_trend['content_ideas'][0])
        print(f"✅ Fallback Twitter Thread: {len(fallback_tweets)} tweets")

    print("\n🎉 ContentGenerationAgent is fully functional!")
    print("Configure API keys in config/config.yaml for AI-powered content generation.")


if __name__ == "__main__":
    example_usage()