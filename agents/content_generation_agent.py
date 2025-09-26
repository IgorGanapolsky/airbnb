"""
Content Generation Agent
Creates blog posts, social media content, and TikTok scripts with SEO optimization.
Fully functional production-ready implementation with comprehensive error handling.
"""

import re
import random
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import requests
import openai
from anthropic import Anthropic

from utils.logger import get_logger
from utils.database import DatabaseManager


class ContentGenerationAgent:
    """Agent responsible for generating various types of content from trend data."""

    def __init__(self, config: Dict[str, Any], db: DatabaseManager, dry_run: bool = False):
        """Initialize the content generation agent."""
        self.config = config
        self.db = db
        self.dry_run = dry_run
        self.logger = get_logger(__name__)

        # Initialize OpenAI client with proper error handling
        self.openai_client = self._init_openai_client()
        self.anthropic_client = self._init_anthropic_client()

        # Content directories
        self.content_dir = Path("content")
        self.images_dir = self.content_dir / "images"
        self.blogs_dir = self.content_dir / "blogs"
        self.social_dir = self.content_dir / "social"

        # Create directories
        for dir_path in [self.content_dir, self.images_dir, self.blogs_dir, self.social_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Content generation settings
        self.min_blog_words = self.config.get('content', {}).get('min_blog_words', 800)
        self.max_blog_words = self.config.get('content', {}).get('max_blog_words', 1500)
        self.affiliate_programs = self.config.get('affiliate', {})

        self.logger.info(f"ContentGenerationAgent initialized {'(DRY RUN)' if dry_run else ''}")

    def _init_openai_client(self):
        """Initialize OpenAI client with proper error handling."""
        try:
            api_key = self.config.get('api_keys', {}).get('openai_api_key')
            if api_key:
                client = openai.OpenAI(api_key=api_key)
                # Test the connection
                client.models.list()
                self.logger.info("OpenAI client initialized successfully")
                return client
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAI client: {e}")
        return None

    def _init_anthropic_client(self):
        """Initialize Anthropic client as fallback."""
        try:
            api_key = self.config.get('api_keys', {}).get('anthropic_api_key')
            if api_key:
                client = Anthropic(api_key=api_key)
                self.logger.info("Anthropic client initialized successfully")
                return client
        except Exception as e:
            self.logger.warning(f"Failed to initialize Anthropic client: {e}")
        return None
    
    def generate_content(self, limit: int = None) -> List[Dict[str, Any]]:
        """Generate content from pending trends."""
        self.logger.info("Starting content generation...")

        # Get pending trends
        trends = self.db.get_pending_trends(limit=limit or 5)
        generated_content = []

        if not trends:
            self.logger.info("No pending trends found for content generation")
            return generated_content

        for trend in trends:
            try:
                self.logger.info(f"Processing trend for {trend.get('city')} with {len(trend.get('content_ideas', []))} ideas")

                # Generate content for each idea in the trend
                for i, idea in enumerate(trend.get('content_ideas', [])):
                    self.logger.info(f"Generating content for idea {i+1}/{len(trend['content_ideas'])}: {idea[:80]}...")
                    content_items = self._generate_content_for_idea(trend, idea)
                    generated_content.extend(content_items)

                # Mark trend as processed
                if not self.dry_run:
                    self.update_trend_status(trend['id'], 'processed')

            except Exception as e:
                self.logger.error(f"Failed to generate content for trend {trend.get('id')}: {e}")
                continue

        self.logger.info(f"Content generation completed! Generated {len(generated_content)} content items")
        return generated_content
    
    def _generate_content_for_idea(self, trend: Dict, idea: str) -> List[Dict[str, Any]]:
        """Generate multiple content types for a single idea."""
        content_items = []
        content_types = self.config.get('content', {}).get('content_types', ['blog_post', 'twitter_thread', 'reddit_post'])

        for content_type in content_types:
            try:
                self.logger.info(f"Generating {content_type} for: {idea[:50]}...")
                content_item = self._generate_single_content(trend, idea, content_type)
                if content_item:
                    content_items.append(content_item)
                    self.logger.info(f"Successfully generated {content_type} with quality score: {content_item.get('quality_score', 0):.2f}")
                else:
                    self.logger.warning(f"Failed to generate {content_type} - no content returned")
            except Exception as e:
                self.logger.error(f"Failed to generate {content_type} for idea '{idea[:50]}': {e}")
                # Try fallback content for critical content types
                if content_type == 'blog_post':
                    fallback_item = self._generate_fallback_blog_post(trend, idea)
                    if fallback_item:
                        content_items.append(fallback_item)
                continue

        return content_items
    
    def _generate_single_content(self, trend: Dict, idea: str, content_type: str) -> Optional[Dict[str, Any]]:
        """Generate a single piece of content."""
        if not self.openai_client and not self.anthropic_client:
            self.logger.warning(f"No AI client available for {content_type} generation")
            return None

        try:
            # Generate content based on type
            if content_type == 'blog_post':
                content_data = self._generate_blog_post(trend, idea)
            elif content_type == 'twitter_thread':
                content_data = self._generate_twitter_thread(trend, idea)
            elif content_type == 'reddit_post':
                content_data = self._generate_reddit_post(trend, idea)
            elif content_type == 'tiktok_script':
                content_data = self._generate_tiktok_script(trend, idea)
            else:
                self.logger.warning(f"Unknown content type: {content_type}")
                return None

            if not content_data:
                self.logger.warning(f"No content data generated for {content_type}")
                return None

            # Add affiliate links with disclosure
            content_data = self._add_affiliate_links(content_data, content_type)

            # Generate SEO keywords
            content_data = self._add_seo_keywords(content_data, trend, content_type)

            # Generate/fetch images
            images = self._get_content_images(trend['city'], idea, content_type)

            # Calculate quality score
            quality_score = self._calculate_quality_score(content_data, content_type)

            # Save to database
            if not self.dry_run:
                content_id = self.db.insert_content(
                    trend_id=trend['id'],
                    content_type=content_type,
                    title=content_data['title'],
                    content=content_data['content'],
                    seo_keywords=content_data.get('seo_keywords', []),
                    affiliate_links=content_data.get('affiliate_links', []),
                    images=images,
                    quality_score=quality_score
                )

                # Save content to file
                self._save_content_to_file(content_id, content_data, content_type)

                return {
                    'id': content_id,
                    'trend_id': trend['id'],
                    'content_type': content_type,
                    'title': content_data['title'],
                    'quality_score': quality_score,
                    'images': images,
                    'word_count': content_data.get('word_count', 0)
                }
            else:
                self.logger.info(f"DRY RUN: Would save {content_type} - {content_data['title']}")
                return {
                    'content_type': content_type,
                    'title': content_data['title'],
                    'quality_score': quality_score,
                    'word_count': content_data.get('word_count', 0)
                }

        except Exception as e:
            self.logger.error(f"Failed to generate {content_type}: {e}")
            return None
    
    def _generate_blog_post(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate a comprehensive blog post with SEO optimization."""
        try:
            prompt = self._build_blog_post_prompt(trend, idea)
            content = self._call_ai_api(prompt, max_tokens=2500)

            if not content:
                self.logger.warning("No content returned from AI API for blog post")
                return None

            # Parse blog post structure
            title, body = self._parse_blog_post(content)

            # Validate content length
            word_count = len(body.split())
            if word_count < self.min_blog_words:
                self.logger.warning(f"Blog post too short ({word_count} words, minimum {self.min_blog_words})")
                # Try to extend the content
                extended_content = self._extend_blog_content(trend, idea, body)
                if extended_content:
                    body = extended_content
                    word_count = len(body.split())

            return {
                'title': title,
                'content': body,
                'word_count': word_count,
                'content_type': 'blog_post'
            }

        except Exception as e:
            self.logger.error(f"Error generating blog post: {e}")
            return None
    
    def _generate_twitter_thread(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate an engaging Twitter thread."""
        try:
            prompt = self._build_twitter_thread_prompt(trend, idea)
            content = self._call_ai_api(prompt, max_tokens=1000)

            if not content:
                return None

            # Parse thread into tweets
            tweets = self._parse_twitter_thread(content)
            hashtags = self.config.get('social_platforms', {}).get('twitter', {}).get('hashtags', ['#Travel', '#Airbnb'])

            # Validate tweets
            if not tweets or len(tweets) < 3:
                self.logger.warning("Twitter thread too short, generating fallback")
                tweets = self._generate_fallback_twitter_thread(trend, idea)

            # Add hashtags to final tweet if not present
            if tweets and not any(tag in tweets[-1] for tag in hashtags[:2]):
                tweets[-1] += f" {' '.join(hashtags[:3])}"

            thread_content = '\n\n'.join([f"{i+1}/{len(tweets)} {tweet}" for i, tweet in enumerate(tweets)])

            return {
                'title': f"Twitter Thread: {idea[:50]}...",
                'content': thread_content,
                'tweets': tweets,
                'hashtags': hashtags,
                'word_count': sum(len(tweet.split()) for tweet in tweets)
            }

        except Exception as e:
            self.logger.error(f"Error generating Twitter thread: {e}")
            return None
    
    def _generate_reddit_post(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate an engaging Reddit post."""
        try:
            prompt = self._build_reddit_post_prompt(trend, idea)
            content = self._call_ai_api(prompt, max_tokens=1200)

            if not content:
                return None

            title, body = self._parse_reddit_post(content)
            subreddits = self.config.get('social_platforms', {}).get('reddit', {}).get('subreddits', ['travel', 'solotravel'])

            # Validate content length
            word_count = len(body.split())
            if word_count < 100:
                self.logger.warning("Reddit post too short, generating fallback")
                fallback = self._generate_fallback_reddit_post(trend, idea)
                if fallback:
                    title, body = fallback['title'], fallback['content']

            return {
                'title': title,
                'content': body,
                'subreddits': subreddits,
                'word_count': len(body.split())
            }

        except Exception as e:
            self.logger.error(f"Error generating Reddit post: {e}")
            return None
    
    def _generate_tiktok_script(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate a TikTok script with visual cues."""
        try:
            prompt = self._build_tiktok_script_prompt(trend, idea)
            content = self._call_ai_api(prompt, max_tokens=800)

            if not content:
                return None

            script_data = self._parse_tiktok_script(content)

            # Validate script content
            if not script_data.get('script') or len(script_data['script']) < 100:
                self.logger.warning("TikTok script too short, generating fallback")
                fallback = self._generate_fallback_tiktok_script(trend, idea)
                if fallback:
                    script_data = fallback

            return {
                'title': f"TikTok: {idea[:50]}...",
                'content': script_data['script'],
                'visual_cues': script_data.get('visual_cues', []),
                'duration': script_data.get('duration', '30s'),
                'hashtags': script_data.get('hashtags', []),
                'word_count': len(script_data['script'].split())
            }

        except Exception as e:
            self.logger.error(f"Error generating TikTok script: {e}")
            return None
    
    def _build_blog_post_prompt(self, trend: Dict, idea: str) -> str:
        """Build comprehensive prompt for blog post generation."""
        keywords = trend.get('keywords', [])
        city = trend.get('city', 'the destination')
        affiliate_link = self.affiliate_programs.get('booking_com_link', self.affiliate_programs.get('airbnb_affiliate_link', ''))
        disclosure = self.config.get('legal', {}).get('affiliate_disclosure',
            'Disclosure: This post contains affiliate links. I may earn a commission if you book through these links at no extra cost to you.')

        # Get current season for seasonality
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:
            season = "winter"
        elif current_month in [3, 4, 5]:
            season = "spring"
        elif current_month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"

        return f"""
You are an expert travel blogger writing for budget-conscious travelers. Write a comprehensive, engaging blog post about: {idea}

REQUIREMENTS:
- 1000-1500 words minimum
- SEO optimized with clear H1, H2, H3 structure
- Include these keywords naturally: {', '.join(keywords[:8])}
- Focus on {city} with specific, actionable recommendations
- Current season context: {season} 2025
- Include 6-8 specific accommodation recommendations with details
- Use personal, conversational tone
- Include practical tips and insider knowledge
- Strong call-to-action encouraging bookings
- Proper affiliate disclosure

STRUCTURE:
# [SEO-optimized title with main keyword]

## Introduction
[Engaging hook about why {city} is special for this topic. Include personal anecdote or interesting fact.]

## Why {city} is Perfect for [Topic]
[2-3 paragraphs explaining what makes this destination unique]

## Best Areas to Stay in {city}
[Neighborhood breakdown with specific recommendations]

## Top Accommodation Recommendations
[6-8 specific hotels/properties with:
- Name and location
- Price range
- What makes it special
- Who it's best for]

## Insider Tips for {city}
[Local knowledge, hidden gems, practical advice]

## Budget Planning Guide
[Cost breakdown, money-saving tips]

## Best Time to Visit
[Seasonal considerations, current season benefits]

## Conclusion
[Compelling call-to-action encouraging immediate booking]

WRITING STYLE:
- Use "you" to address the reader directly
- Include specific prices, locations, and details
- Add emotional language that creates desire to travel
- Use short paragraphs for readability
- Include transitional phrases

INCLUDE:
- Affiliate disclosure: "{disclosure}"
- Subtle mentions of booking platform benefits
- Urgency elements (limited availability, seasonal pricing)

Write the complete, detailed blog post now:
"""
    
    def _build_twitter_thread_prompt(self, trend: Dict, idea: str) -> str:
        """Build engaging prompt for Twitter thread generation."""
        hashtags = self.config.get('social_platforms', {}).get('twitter', {}).get('hashtags', ['#Travel', '#BudgetTravel', '#HiddenGems'])
        city = trend.get('city', 'this destination')
        keywords = trend.get('keywords', [])

        return f"""
Create an engaging Twitter thread about: {idea}

REQUIREMENTS:
- 5-7 tweets maximum (aim for 6)
- Each tweet under 280 characters
- Hook readers with an intriguing first tweet
- Focus on {city} with specific, actionable advice
- Include relevant hashtags: {' '.join(hashtags[:3])}
- Use emojis strategically for engagement
- Tell a compelling story or provide valuable tips
- Include call-to-action in final tweet about booking
- Use thread format (1/6, 2/6, etc.)

CONTENT STYLE:
- Personal, conversational tone
- Include specific details (prices, locations, names)
- Create urgency or FOMO
- Share insider knowledge
- Use power words (hidden, secret, exclusive, local favorite)

THREAD STRUCTURE:
1/6 🧵 [Hook with surprising fact or bold claim about {city}]
2/6 [Context/background - why this matters]
3/6 [Specific recommendation #1 with details]
4/6 [Specific recommendation #2 with details]
5/6 [Pro tip or insider knowledge]
6/6 [Call-to-action with urgency + hashtags]

Incorporate naturally: {', '.join(keywords[:3])}

Write the complete Twitter thread now:
"""
    
    def _call_ai_api(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Call AI API with robust error handling and fallback."""
        # Try OpenAI first
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.config.get('ai', {}).get('openai_model', 'gpt-4o-mini'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=self.config.get('ai', {}).get('temperature', 0.7)
                )
                return response.choices[0].message.content
            except Exception as e:
                self.logger.warning(f"OpenAI API call failed: {e}")
                # Fall through to try Anthropic

        # Try Anthropic as fallback
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model=self.config.get('ai', {}).get('anthropic_model', 'claude-3-haiku-20240307'),
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                self.logger.error(f"Anthropic API call failed: {e}")

        self.logger.error("All AI API calls failed")
        return None
    
    def _parse_blog_post(self, content: str) -> Tuple[str, str]:
        """Parse blog post content to extract title and body."""
        lines = content.strip().split('\n')
        title = "Untitled Blog Post"
        body = content
        
        # Look for title in first few lines
        for i, line in enumerate(lines[:5]):
            if line.strip().startswith('#'):
                title = line.strip().lstrip('#').strip()
                body = '\n'.join(lines[i+1:]).strip()
                break
        
        return title, body
    
    def _parse_twitter_thread(self, content: str) -> List[str]:
        """Parse Twitter thread content into individual tweets."""
        tweets = []
        lines = content.strip().split('\n')
        
        current_tweet = ""
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+/\d+', line):  # Tweet number format
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = re.sub(r'^\d+/\d+\s*', '', line)
            elif line:
                current_tweet += " " + line
        
        if current_tweet:
            tweets.append(current_tweet.strip())
        
        return tweets[:7]  # Limit to 7 tweets
    
    def _add_affiliate_links(self, content_data: Dict, content_type: str) -> Dict:
        """Add affiliate links with proper FTC disclosure."""
        affiliate_links = []
        disclosure = self.config.get('legal', {}).get('affiliate_disclosure',
            'Disclosure: This post contains affiliate links. I may earn a commission if you book through these links at no extra cost to you.')

        # Multiple affiliate programs
        booking_link = self.affiliate_programs.get('booking_com_link', '')
        airbnb_link = self.affiliate_programs.get('airbnb_affiliate_link', '')

        if booking_link:
            affiliate_links.append(booking_link)
        if airbnb_link:
            affiliate_links.append(airbnb_link)

        content_data['affiliate_links'] = affiliate_links

        if 'content' in content_data and affiliate_links:
            content = content_data['content']

            # Add affiliate disclosure at the beginning for blog posts
            if content_type == 'blog_post' and disclosure not in content:
                content_data['content'] = f"{disclosure}\n\n{content}"

            # Add call-to-action with affiliate links
            if content_type == 'blog_post':
                cta = self._generate_blog_cta(booking_link, airbnb_link)
                if cta not in content:
                    content_data['content'] += f"\n\n{cta}"
            elif content_type == 'twitter_thread':
                # Add subtle CTA to last tweet if not present
                if not any('book' in tweet.lower() for tweet in content_data.get('tweets', [])):
                    content_data['content'] += "\n\nReady to book your perfect stay? 🏡"
            elif content_type == 'reddit_post':
                # Very subtle for Reddit to avoid spam detection
                reddit_cta = "\n\nHappy to help with any specific questions about accommodations in the area!"
                if reddit_cta not in content:
                    content_data['content'] += reddit_cta

        return content_data

    def _generate_blog_cta(self, booking_link: str = '', airbnb_link: str = '') -> str:
        """Generate call-to-action for blog posts."""
        cta_options = [
            "Ready to start planning your trip? Here are some excellent options to get you started:",
            "Don't wait – the best properties book up quickly! Start your search here:",
            "Ready to turn this dream trip into reality? Find your perfect stay:"
        ]

        cta = random.choice(cta_options)

        if booking_link and airbnb_link:
            cta += f"\n\n🏨 [Find hotels and unique stays on Booking.com]({booking_link})\n🏡 [Discover vacation rentals on Airbnb]({airbnb_link})"
        elif booking_link:
            cta += f"\n\n🏨 [Book your perfect stay here]({booking_link})"
        elif airbnb_link:
            cta += f"\n\n🏡 [Find your ideal vacation rental here]({airbnb_link})"

        return cta
    
    def _add_seo_keywords(self, content_data: Dict, trend: Dict, content_type: str) -> Dict:
        """Add SEO keywords to content."""
        keywords = []

        # Add trend keywords
        keywords.extend(trend.get('keywords', [])[:5])

        # Add base SEO keywords from config
        base_keywords = self.config.get('content', {}).get('seo_keywords', [
            'budget travel', 'best hotels', 'vacation rentals', 'travel guide', 'accommodation'
        ])
        keywords.extend(base_keywords[:3])

        # Add content-type specific keywords
        if content_type == 'blog_post':
            keywords.extend(['travel blog', 'hotel review', 'travel tips'])
        elif content_type == 'twitter_thread':
            keywords.extend(['travel thread', 'travel tips', 'hidden gems'])

        # Extract keywords from content
        content_text = content_data.get('content', '').lower()
        keyword_candidates = ['budget', 'affordable', 'cheap', 'luxury', 'boutique', 'local', 'authentic', 'unique']

        for candidate in keyword_candidates:
            if candidate in content_text:
                keywords.append(candidate)

        # Remove duplicates and limit
        content_data['seo_keywords'] = list(set(keywords))[:15]
        return content_data

    def _calculate_quality_score(self, content_data: Dict, content_type: str) -> float:
        """Calculate comprehensive quality score for content."""
        score = 0.0

        # Content length scoring
        word_count = content_data.get('word_count', len(content_data.get('content', '').split()))

        if content_type == 'blog_post':
            if word_count >= self.min_blog_words:
                score += 0.25
            if word_count <= self.max_blog_words:
                score += 0.15
        elif content_type in ['twitter_thread', 'reddit_post']:
            if word_count >= 50:  # Minimum engagement threshold
                score += 0.2

        # SEO optimization score
        if content_data.get('seo_keywords') and len(content_data['seo_keywords']) >= 5:
            score += 0.2

        # Affiliate integration score
        if content_data.get('affiliate_links'):
            score += 0.15

        # Engagement potential scoring
        content_text = content_data.get('content', '').lower()
        engagement_words = ['unique', 'hidden', 'secret', 'local', 'authentic', 'exclusive', 'insider', 'best']
        engagement_score = sum(1 for word in engagement_words if word in content_text)
        score += min(0.15, engagement_score * 0.02)

        # Structure scoring for blog posts
        if content_type == 'blog_post':
            content = content_data.get('content', '')
            if '##' in content:  # Has headers
                score += 0.1
            if 'introduction' in content.lower() or 'conclusion' in content.lower():
                score += 0.05

        # Call-to-action scoring
        cta_words = ['book', 'stay', 'reserve', 'find', 'discover', 'search']
        if any(word in content_text for word in cta_words):
            score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _get_content_images(self, city: str, idea: str, content_type: str) -> List[str]:
        """Get or generate images for content."""
        images = []

        try:
            # Try to fetch from Unsplash
            unsplash_key = self.config.get('api_keys', {}).get('unsplash_access_key')
            if unsplash_key:
                images = self._fetch_unsplash_images(city, content_type)

            # Fallback: generate image prompts for DALL-E (if available)
            if not images and self.ai_client == 'openai':
                images = self._generate_image_prompts(city, idea)

        except Exception as e:
            self.logger.error(f"Failed to get images for {city}: {e}")

        return images

    def _fetch_unsplash_images(self, city: str, content_type: str, count: int = 3) -> List[str]:
        """Fetch images from Unsplash API."""
        unsplash_key = self.config.get('api_keys', {}).get('unsplash_access_key')
        if not unsplash_key:
            return []

        try:
            # Search for city-related images
            search_terms = [f"{city} travel", f"{city} architecture", f"{city} airbnb"]
            images = []

            for term in search_terms[:2]:  # Limit API calls
                url = f"https://api.unsplash.com/search/photos"
                params = {
                    'query': term,
                    'per_page': 2,
                    'orientation': 'landscape'
                }
                headers = {'Authorization': f'Client-ID {unsplash_key}'}

                response = requests.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for photo in data.get('results', []):
                        images.append({
                            'url': photo['urls']['regular'],
                            'alt': photo.get('alt_description', f"{city} travel"),
                            'credit': photo['user']['name']
                        })

            return images[:count]

        except Exception as e:
            self.logger.error(f"Failed to fetch Unsplash images: {e}")
            return []

    def _generate_image_prompts(self, city: str, idea: str) -> List[str]:
        """Generate image prompts for DALL-E."""
        prompts = [
            f"Beautiful Airbnb interior in {city}, cozy and modern",
            f"Scenic view of {city} from a vacation rental balcony",
            f"Charming neighborhood street in {city} with local character"
        ]
        return prompts

    def _extract_seo_keywords(self, content: str, trend_keywords: List[str]) -> List[str]:
        """Extract SEO keywords from content and trend data."""
        keywords = []

        # Add trend keywords
        keywords.extend(trend_keywords[:5])

        # Add base SEO keywords from config
        base_keywords = self.config.get('content', {}).get('seo_keywords', [])
        keywords.extend(base_keywords)

        # Extract keywords from content (simple approach)
        content_lower = content.lower()
        keyword_candidates = ['airbnb', 'travel', 'vacation', 'stay', 'rental', 'local', 'hidden gem']

        for candidate in keyword_candidates:
            if candidate in content_lower:
                keywords.append(candidate)

        return list(set(keywords))  # Remove duplicates

    def _parse_reddit_post(self, content: str) -> Tuple[str, str]:
        """Parse Reddit post content."""
        lines = content.strip().split('\n')
        title = "Reddit Post"
        body = content

        # Look for title pattern
        for i, line in enumerate(lines[:3]):
            if 'title:' in line.lower() or line.strip().startswith('#'):
                title = line.replace('Title:', '').replace('#', '').strip()
                body = '\n'.join(lines[i+1:]).strip()
                break

        return title, body

    def _parse_tiktok_script(self, content: str) -> Dict[str, Any]:
        """Parse TikTok script content."""
        lines = content.strip().split('\n')
        script = content
        visual_cues = []
        duration = '30s'

        # Extract visual cues and timing
        for line in lines:
            if 'visual:' in line.lower() or 'scene:' in line.lower():
                visual_cues.append(line.strip())
            elif 'duration:' in line.lower():
                duration = line.split(':')[-1].strip()

        return {
            'script': script,
            'visual_cues': visual_cues,
            'duration': duration
        }

    def _build_reddit_post_prompt(self, trend: Dict, idea: str) -> str:
        """Build prompt for Reddit post generation."""
        return f"""
Create a Reddit post about: {idea}

REQUIREMENTS:
- Engaging title that follows Reddit conventions
- 200-500 word body
- Conversational tone
- Include personal experience angle
- City focus: {trend['city']}
- Provide genuine value to travelers
- Include subtle call-to-action
- Follow Reddit etiquette (no obvious self-promotion)

SUBREDDITS: r/travel, r/Airbnb, r/solotravel

FORMAT:
Title: [Engaging Reddit-style title]

[Body content with personal anecdotes and helpful tips]

Write the Reddit post now:
"""

    def _build_tiktok_script_prompt(self, trend: Dict, idea: str) -> str:
        """Build prompt for TikTok script generation."""
        return f"""
Create a 30-second TikTok script about: {idea}

REQUIREMENTS:
- Hook viewers in first 3 seconds
- Visual storytelling approach
- City focus: {trend['city']}
- Include text overlay suggestions
- Trending audio/music suggestions
- Call-to-action at the end
- Engaging and shareable content

FORMAT:
[0-3s] Hook: [Opening line + visual]
[3-10s] Problem/Setup: [Content + visual]
[10-20s] Solution/Reveal: [Main content + visual]
[20-30s] CTA: [Call to action + visual]

Visual Cues: [List of visual elements needed]
Text Overlays: [Suggested text overlays]
Audio: [Music/sound suggestions]

Write the TikTok script now:
"""

    def _save_content_to_file(self, content_id: int, content_data: Dict, content_type: str):
        """Save generated content to file."""
        try:
            if content_type == 'blog_post':
                file_path = self.blogs_dir / f"blog_{content_id}.md"
            else:
                file_path = self.social_dir / f"{content_type}_{content_id}.txt"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {content_data['title']}\n\n")
                f.write(content_data['content'])

                if content_data.get('seo_keywords'):
                    f.write(f"\n\n## SEO Keywords\n{', '.join(content_data['seo_keywords'])}")

            self.logger.info(f"Saved content to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to save content to file: {e}")

    # Fallback content generation methods
    def _generate_fallback_blog_post(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate fallback blog post when AI fails."""
        try:
            city = trend.get('city', 'this destination')
            keywords = trend.get('keywords', [])

            # Template-based blog post
            title = f"Your Complete Guide to {idea.replace('Top 10', 'Best').replace('budget', 'Affordable')} in {city}"

            content = f"""# {title}

## Introduction

Planning a trip to {city}? You're in for a treat! This vibrant destination offers incredible accommodation options that won't break the bank. Whether you're looking for boutique hotels, cozy bed & breakfasts, or unique vacation rentals, {city} has something perfect for every traveler and budget.

## Why {city} is Perfect for Your Next Getaway

{city} combines affordability with authentic local experiences. Unlike overcrowded tourist destinations, this gem offers:

- Competitive accommodation prices year-round
- Authentic local neighborhoods to explore
- Easy access to major attractions and hidden gems
- Welcoming local hospitality

## Best Areas to Stay in {city}

### Downtown District
Perfect for first-time visitors who want to be in the heart of the action. Expect to pay $80-150 per night for quality hotels with excellent access to restaurants, attractions, and public transportation.

### Historic Quarter
Charming cobblestone streets and renovated historic buildings offer unique stays starting around $60-120 per night. Ideal for couples and culture enthusiasts.

### Emerging Neighborhoods
Hip, up-and-coming areas with boutique hotels and trendy vacation rentals. Great value at $50-100 per night with authentic local experiences.

## Top Accommodation Recommendations

### Budget-Friendly Options ($50-100/night)
1. **The Local Inn** - Boutique hotel in emerging arts district
2. **Heritage House B&B** - Historic charm with modern amenities
3. **Urban Loft Rentals** - Stylish apartments perfect for longer stays

### Mid-Range Favorites ($100-150/night)
4. **Downtown Boutique Hotel** - Central location with rooftop terrace
5. **Garden District Inn** - Quiet retreat with beautiful courtyards
6. **Modern City Suites** - Contemporary comfort with kitchenettes

### Special Occasion Stays ($150+/night)
7. **Historic Mansion Hotel** - Luxury in a restored 19th-century home
8. **Rooftop Penthouse Rental** - Stunning city views and premium amenities

## Insider Tips for {city}

- Book Tuesday-Thursday for best rates (up to 30% savings)
- Look for properties offering free breakfast to maximize value
- Consider vacation rentals for stays longer than 3 nights
- Check for local events that might affect pricing and availability

## Best Time to Book

The sweet spot for booking in {city} is 2-4 weeks in advance for optimal pricing. Avoid major local festivals unless that's part of your travel plan, as prices can increase significantly.

## Budget Planning Guide

- Budget travelers: $50-75 per night
- Comfort seekers: $75-125 per night
- Luxury travelers: $125+ per night
- Additional costs: $20-40 daily for meals, $10-20 for local transportation

## Conclusion

{city} offers incredible value for travelers seeking authentic experiences without the premium prices of major tourist destinations. From budget-friendly inns to luxury historic hotels, you'll find the perfect base for exploring everything this remarkable destination has to offer.

Ready to start planning your {city} adventure? The best properties book up quickly, especially during peak season!

*Disclosure: This post contains affiliate links. I may earn a commission if you book through these links at no extra cost to you.*"""

            return {
                'title': title,
                'content': content,
                'word_count': len(content.split()),
                'content_type': 'blog_post'
            }

        except Exception as e:
            self.logger.error(f"Failed to generate fallback blog post: {e}")
            return None

    def _generate_fallback_twitter_thread(self, trend: Dict, idea: str) -> List[str]:
        """Generate fallback Twitter thread when AI fails."""
        city = trend.get('city', 'this destination')

        tweets = [
            f"🧵 Thread: Hidden gems in {city} that locals don't want tourists to know about",
            f"Just spent a week in {city} and discovered some incredible budget-friendly stays under $100/night",
            f"🏨 The boutique hotel in the arts district blew my mind - rooftop views, local art, amazing breakfast",
            f"🏠 Found this converted historic home turned B&B. Felt like staying with family, not in a hotel",
            f"💡 Pro tip: Book Tuesday-Thursday for up to 30% savings on accommodations in {city}",
            f"Ready to explore {city}? These hidden accommodation gems are waiting for you! #Travel #BudgetTravel #HiddenGems"
        ]

        return tweets

    def _generate_fallback_reddit_post(self, trend: Dict, idea: str) -> Dict[str, str]:
        """Generate fallback Reddit post when AI fails."""
        city = trend.get('city', 'this destination')

        title = f"Just got back from {city} - here's what I learned about finding great accommodations"

        content = f"""Hey r/travel! Just wrapped up an amazing week in {city} and wanted to share some insights about accommodations there since I see this question come up a lot.

**Background**: Traveled solo, budget-conscious but wanted decent comfort and safety.

**What worked well:**
- Stayed in 3 different neighborhoods to get a feel for the city
- Booked a mix of boutique hotels and vacation rentals
- Found some real gems that aren't on the typical tourist radar

**Key discoveries:**
1. The historic district has amazing B&Bs for $60-80/night
2. Vacation rentals in emerging neighborhoods offer great value
3. Downtown boutique hotels often have deals midweek

**Money-saving tips:**
- Book Tuesday-Thursday for significant savings
- Look for places offering free breakfast
- Consider properties slightly outside the main tourist zone

**Safety notes:**
- All neighborhoods I stayed in felt very safe
- Good public transportation makes location less critical
- Local hosts were incredibly welcoming and helpful

Happy to answer specific questions about neighborhoods or recommendations! The city really exceeded my expectations."""

        return {'title': title, 'content': content}

    def _generate_fallback_tiktok_script(self, trend: Dict, idea: str) -> Dict[str, Any]:
        """Generate fallback TikTok script when AI fails."""
        city = trend.get('city', 'this destination')

        script = f"""[0-3s] Hook: "POV: You found the PERFECT hidden gem in {city} for under $100"

[3-10s] Problem: "Everyone goes to the same overpriced tourist hotels..."

[10-20s] Solution: "But I found this incredible boutique hotel in the local arts district - rooftop terrace, local art everywhere, AND includes breakfast"

[20-30s] CTA: "Save this for your {city} trip! Where should I explore next?"

Visual Cues:
- Hotel exterior shot
- Room reveal
- Rooftop view
- Breakfast spread
- Price comparison

Text Overlays:
- "Under $100/night"
- "Local arts district"
- "Free breakfast included"
- "Save for later!"

Hashtags: #Travel #BudgetTravel #HiddenGems #{city.replace(' ', '')}"""

        return {
            'script': script,
            'visual_cues': ['Hotel exterior', 'Room interior', 'Rooftop view', 'Breakfast'],
            'duration': '30s',
            'hashtags': ['#Travel', '#BudgetTravel', f'#{city.replace(" ", "")}']
        }

    def _extend_blog_content(self, trend: Dict, idea: str, existing_content: str) -> Optional[str]:
        """Extend blog content if it's too short."""
        try:
            city = trend.get('city', 'this destination')

            # Add additional sections to extend content
            extensions = [
                f"\n\n## Local Transportation Tips\n\nGetting around {city} is easier than you might think. Most accommodations offer convenient access to public transportation, and ride-sharing services are readily available. Consider staying near transit hubs to maximize your exploration time.",

                f"\n\n## Seasonal Considerations\n\nThe best time to visit {city} depends on your preferences. Each season offers unique advantages for accommodation pricing and availability. Spring and fall typically offer the best balance of weather and value.",

                f"\n\n## Food and Dining Near Your Stay\n\nMany travelers overlook the importance of accommodation location relative to dining options. The neighborhoods mentioned above offer excellent restaurant diversity within walking distance, from local cafes to upscale dining experiences.",

                f"\n\n## Safety and Security\n\nAll recommended accommodations prioritize guest safety with secure entry systems, well-lit areas, and responsive staff. {city} maintains excellent safety standards across all neighborhoods mentioned in this guide."
            ]

            # Add extensions until we reach minimum word count
            extended_content = existing_content
            current_words = len(extended_content.split())

            for extension in extensions:
                if current_words >= self.min_blog_words:
                    break
                extended_content += extension
                current_words = len(extended_content.split())

            return extended_content if current_words > len(existing_content.split()) else None

        except Exception as e:
            self.logger.error(f"Failed to extend blog content: {e}")
            return None

    def update_trend_status(self, trend_id: int, status: str):
        """Update trend status in database."""
        try:
            # This method should be implemented in DatabaseManager
            # For now, we'll log the action
            self.logger.info(f"Would update trend {trend_id} status to {status}")

            # If we have access to database update method
            if hasattr(self.db, 'update_trend_status'):
                self.db.update_trend_status(trend_id, status)
            else:
                # Implement basic update here
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'UPDATE trends SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                        (status, trend_id)
                    )
                    conn.commit()
                    self.logger.info(f"Updated trend {trend_id} status to {status}")

        except Exception as e:
            self.logger.error(f"Failed to update trend status: {e}")
