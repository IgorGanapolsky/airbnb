import json
import logging
import re
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import openai
from bitlyshortener import Shortener
from utils.config_loader import config
from utils.database import Database

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self):
        self.config = config.config
        self.db = Database(self.config['system']['database_path'])

        openai_key = self.config['ai']['openai']['api_key']
        if openai_key and openai_key != "sk-...":
            openai.api_key = openai_key

        bitly_token = self.config.get('tracking.bitly.access_token')
        if bitly_token and self.config.get('tracking.bitly.enabled'):
            self.shortener = Shortener(tokens=[bitly_token])
        else:
            self.shortener = None

        self.affiliate_link = self.config['affiliate']['booking_link']
        self.disclosure = self.config['affiliate']['disclosure']

    def generate_content_for_trends(self, limit: int = 5) -> List[Dict[str, Any]]:
        trends = self.db.get_pending_trends(limit)
        generated_content = []

        for trend in trends:
            try:
                content_pieces = self._generate_all_content_types(trend)
                generated_content.extend(content_pieces)

                self.db.update_trend_status(trend['id'], 'processed')

            except Exception as e:
                logger.error(f"Error generating content for trend {trend['id']}: {e}")

        return generated_content

    def _generate_all_content_types(self, trend: Dict[str, Any]) -> List[Dict[str, Any]]:
        content_pieces = []

        blog_post = self._generate_blog_post(trend)
        if blog_post:
            content_pieces.append(blog_post)

        twitter_thread = self._generate_twitter_thread(trend)
        if twitter_thread:
            content_pieces.append(twitter_thread)

        reddit_post = self._generate_reddit_post(trend)
        if reddit_post:
            content_pieces.append(reddit_post)

        tiktok_script = self._generate_tiktok_script(trend)
        if tiktok_script:
            content_pieces.append(tiktok_script)

        return content_pieces

    def _generate_blog_post(self, trend: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        city = trend['city']
        idea = trend['idea']
        keywords = json.loads(trend['keywords']) if isinstance(trend['keywords'], str) else trend['keywords']

        prompt = f"""
        Write a comprehensive, engaging blog post about: {idea}

        REQUIREMENTS:
        - 800-1500 words
        - SEO optimized for keywords: {', '.join(keywords)}
        - Include H1, H2, H3 headers
        - Natural keyword density (2%)
        - Engaging introduction with hook
        - 5-7 main sections with actionable tips
        - Include specific neighborhoods, prices, amenities
        - Strong call-to-action mentioning Airbnb
        - Evergreen content that stays relevant

        STRUCTURE:
        1. Compelling title with {city}
        2. Hook introduction (why this matters now)
        3. Main sections with specific recommendations
        4. Practical tips and insider knowledge
        5. Strong conclusion with booking encouragement

        TARGET AUDIENCE: Travel enthusiasts planning {city} trips
        TONE: Friendly, authoritative, helpful
        INCLUDE: Specific price ranges, best times to visit, local tips

        Write in markdown format.
        """

        try:
            if config.get('system.dry_run', False):
                return self._generate_mock_blog_post(trend)

            response = openai.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are an expert travel blogger specializing in Airbnb stays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['ai']['openai']['temperature'],
                max_tokens=2000
            )

            content = response.choices[0].message.content

            blog_with_links = self._add_affiliate_links(content)

            content_id = self.db.add_content(
                trend_id=trend['id'],
                content_type='blog',
                title=self._extract_title_from_content(blog_with_links),
                content=blog_with_links
            )

            return {
                'id': content_id,
                'type': 'blog',
                'title': self._extract_title_from_content(blog_with_links),
                'content': blog_with_links,
                'trend_id': trend['id']
            }

        except Exception as e:
            logger.error(f"Error generating blog post: {e}")
            return None

    def _generate_twitter_thread(self, trend: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        city = trend['city']
        idea = trend['idea']

        prompt = f"""
        Create an engaging Twitter thread about: {idea}

        REQUIREMENTS:
        - 5-7 tweets maximum
        - First tweet is a hook with question or surprising fact
        - Each tweet stands alone but flows to next
        - Include emoji where natural
        - Mention specific neighborhoods/areas in {city}
        - Include price ranges and tips
        - Final tweet has clear Airbnb call-to-action
        - Use relevant hashtags (#AirbnbFinds #{city}Travel #TravelTips)

        FORMAT:
        Tweet 1: [Hook about {city}]
        Tweet 2: [First tip/recommendation]
        Tweet 3: [Second tip/recommendation]
        Tweet 4: [Third tip/recommendation]
        Tweet 5: [Bonus tip or insider secret]
        Tweet 6: [Call-to-action with Airbnb mention]

        Keep each tweet under 280 characters.
        Make it conversational and engaging.
        """

        try:
            if config.get('system.dry_run', False):
                return self._generate_mock_twitter_thread(trend)

            response = openai.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a social media expert creating travel content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=800
            )

            thread_content = response.choices[0].message.content
            thread_with_links = self._add_affiliate_links(thread_content)

            content_id = self.db.add_content(
                trend_id=trend['id'],
                content_type='twitter',
                title=f"Twitter Thread: {idea}",
                content=thread_with_links
            )

            return {
                'id': content_id,
                'type': 'twitter',
                'title': f"Twitter Thread: {idea}",
                'content': thread_with_links,
                'trend_id': trend['id']
            }

        except Exception as e:
            logger.error(f"Error generating Twitter thread: {e}")
            return None

    def _generate_reddit_post(self, trend: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        city = trend['city']
        idea = trend['idea']

        prompt = f"""
        Create a helpful Reddit post for r/travel about: {idea}

        REQUIREMENTS:
        - Authentic, helpful tone (not sales-y)
        - 200-400 words
        - Include personal experience angle
        - Specific recommendations with reasons
        - Price ranges and practical tips
        - Subtle mention of Airbnb benefits
        - Ask for community input/experiences
        - Follow Reddit etiquette

        STRUCTURE:
        1. Personal hook (I recently visited {city}...)
        2. Main recommendations with details
        3. Specific tips and insider knowledge
        4. Community question to encourage engagement

        Make it sound like genuine user contribution, not marketing.
        """

        try:
            if config.get('system.dry_run', False):
                return self._generate_mock_reddit_post(trend)

            response = openai.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a helpful travel community member sharing experiences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )

            reddit_content = response.choices[0].message.content
            reddit_with_links = self._add_affiliate_links(reddit_content, subtle=True)

            content_id = self.db.add_content(
                trend_id=trend['id'],
                content_type='reddit',
                title=f"Reddit Post: {idea}",
                content=reddit_with_links
            )

            return {
                'id': content_id,
                'type': 'reddit',
                'title': f"Reddit Post: {idea}",
                'content': reddit_with_links,
                'trend_id': trend['id']
            }

        except Exception as e:
            logger.error(f"Error generating Reddit post: {e}")
            return None

    def _generate_tiktok_script(self, trend: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        city = trend['city']
        idea = trend['idea']

        prompt = f"""
        Create a 30-second TikTok script about: {idea}

        REQUIREMENTS:
        - Hook in first 3 seconds
        - Fast-paced, visual format
        - 3-5 key points maximum
        - Include text overlay suggestions
        - Visual direction for each scene
        - Trending audio suggestions
        - Clear Airbnb call-to-action
        - Under 150 words of voiceover

        FORMAT:
        HOOK (0-3s): [Opening statement/question]
        POINT 1 (3-10s): [First recommendation with visual]
        POINT 2 (10-18s): [Second recommendation with visual]
        POINT 3 (18-25s): [Third recommendation with visual]
        CTA (25-30s): [Call-to-action with Airbnb mention]

        Include text overlay and visual suggestions for each segment.
        """

        try:
            if config.get('system.dry_run', False):
                return self._generate_mock_tiktok_script(trend)

            response = openai.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a TikTok content creator specializing in travel tips."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=400
            )

            script_content = response.choices[0].message.content

            content_id = self.db.add_content(
                trend_id=trend['id'],
                content_type='tiktok',
                title=f"TikTok Script: {idea}",
                content=script_content
            )

            return {
                'id': content_id,
                'type': 'tiktok',
                'title': f"TikTok Script: {idea}",
                'content': script_content,
                'trend_id': trend['id']
            }

        except Exception as e:
            logger.error(f"Error generating TikTok script: {e}")
            return None

    def _add_affiliate_links(self, content: str, subtle: bool = False) -> str:
        if not self.affiliate_link or self.affiliate_link == "YOUR_BOOKING_AFFILIATE_LINK":
            return content

        short_link = self._create_short_link(self.affiliate_link)

        if subtle:
            content += f"\n\n{self.disclosure}\nFind great hotel deals: {short_link}"
        else:
            content = content.replace(
                "Booking.com",
                f"[Booking.com]({short_link})"
            )
            content += f"\n\n---\n*{self.disclosure}*\n\n**[🏨 Book Your Perfect Stay Here]({short_link})**"

        return content

    def _create_short_link(self, url: str) -> str:
        if self.shortener:
            try:
                short_urls = self.shortener.shorten_urls([url])
                return short_urls[0] if short_urls else url
            except Exception as e:
                logger.warning(f"Link shortening failed: {e}")

        return url

    def _extract_title_from_content(self, content: str) -> str:
        title_match = re.search(r'^#\s(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        title_match = re.search(r'^(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()[:100]

        return "Generated Content"

    def _generate_mock_blog_post(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        content = f"""# {trend['idea']}

Discover the best-kept secrets of {trend['city']} with our comprehensive guide to affordable and unique Airbnb stays.

## Why {trend['city']} Should Be Your Next Destination

{trend['city']} offers an incredible blend of culture, cuisine, and character that makes it perfect for travelers seeking authentic experiences without breaking the bank.

## Top 5 Budget-Friendly Neighborhoods

### 1. Historic District
Charming cobblestone streets with character-filled homes under $80/night.

### 2. Arts Quarter
Creative hub with unique lofts and studios averaging $90/night.

### 3. Riverside Area
Peaceful waterfront properties with stunning views from $70/night.

### 4. University District
Vibrant area with modern amenities and great dining, $65/night average.

### 5. Suburban Gems
Family-friendly homes with parking and space, starting at $85/night.

## Insider Tips for Booking

- Book 2-3 months in advance for best prices
- Consider weekday stays for 30% savings
- Look for properties with full kitchens to save on dining

## Ready to Explore {trend['city']}?

Don't wait - the best properties book quickly! Start planning your perfect {trend['city']} getaway today.

*{self.disclosure}*
"""

        content_id = self.db.add_content(
            trend_id=trend['id'],
            content_type='blog',
            title=trend['idea'],
            content=content
        )

        return {
            'id': content_id,
            'type': 'blog',
            'title': trend['idea'],
            'content': content,
            'trend_id': trend['id']
        }

    def _generate_mock_twitter_thread(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        city = trend['city']
        thread = f"""🧵 Thread: {trend['idea']}

1/6 Did you know {city} has some of the most affordable unique stays in the country? Here's my insider guide to finding gems under $100/night 🏠✨

2/6 💎 HIDDEN GEM: Historic District
Character-filled homes with original features
Average: $75/night
Pro tip: Look for converted carriage houses!

3/6 🎨 ARTS QUARTER MAGIC
Creative lofts with local artwork
Average: $85/night
Bonus: Walking distance to galleries & cafes

4/6 🌊 RIVERSIDE RETREAT
Peaceful waterfront properties with views
Average: $80/night
Perfect for: Morning coffee by the water

5/6 💡 BOOKING HACK:
Search for weekday stays = 30% savings
Book 2-3 months ahead for best selection
Filter for full kitchens to save on dining

6/6 Ready to discover {city}? The best stays book fast!

Drop a 🏠 if you're planning a trip!

#{city}Travel #AirbnbFinds #TravelTips #BudgetTravel

*{self.disclosure}*"""

        content_id = self.db.add_content(
            trend_id=trend['id'],
            content_type='twitter',
            title=f"Twitter Thread: {trend['idea']}",
            content=thread
        )

        return {
            'id': content_id,
            'type': 'twitter',
            'title': f"Twitter Thread: {trend['idea']}",
            'content': thread,
            'trend_id': trend['id']
        }

    def _generate_mock_reddit_post(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        city = trend['city']
        post = f"""I recently spent a week in {trend['city']} and wanted to share some amazing Airbnb finds for fellow travelers!

After trying 3 different neighborhoods, here's what I discovered:

**Historic District** - Absolutely charming! Stayed in a converted 1800s townhouse for $78/night. The character is unbeatable and you're walking distance to everything.

**Arts Quarter** - Perfect if you love local culture. Found a loft with local artwork for $82/night. The neighborhood vibe is incredible and there are amazing coffee shops everywhere.

**Riverside Area** - Most peaceful option. Woke up to river views every morning for just $79/night. Great if you want to escape the city buzz while still being close to downtown.

**Pro tips from my experience:**
- Weekday bookings saved me about 30% vs weekends
- Properties with full kitchens let me save a ton on dining out
- Book 2-3 months ahead - the good ones go fast!

The variety of unique stays in {city} really surprised me. Way more character than hotels and often cheaper too.

Anyone else have great {city} Airbnb experiences to share? Planning my next trip there already!

*{self.disclosure}*"""

        content_id = self.db.add_content(
            trend_id=trend['id'],
            content_type='reddit',
            title=f"Reddit Post: {trend['idea']}",
            content=post
        )

        return {
            'id': content_id,
            'type': 'reddit',
            'title': f"Reddit Post: {trend['idea']}",
            'content': post,
            'trend_id': trend['id']
        }

    def _generate_mock_tiktok_script(self, trend: Dict[str, Any]) -> Dict[str, Any]:
        city = trend['city']
        script = f"""🎬 TikTok Script: {trend['idea']}

HOOK (0-3s):
"POV: You found the secret to affordable {city} stays under $100"
[Text overlay: "Secret {city} Airbnb spots ⬇️"]

POINT 1 (3-10s):
"Historic District - $75/night for actual character"
[Visual: Show charming townhouse exterior]
[Text: "Historic charm ✨ $75"]

POINT 2 (10-18s):
"Arts Quarter - Local artwork included for $85"
[Visual: Pan across unique loft space]
[Text: "Artist loft 🎨 $85"]

POINT 3 (18-25s):
"Riverside views - Wake up to water for $80"
[Visual: Morning coffee with river view]
[Text: "River views 🌊 $80"]

CTA (25-30s):
"Best stays book fast - don't wait!"
[Text: "Book now! Link in bio"]

TRENDING AUDIO: "Secret spots" trending sound
HASHTAGS: #{city}travel #airbnbfinds #travelhacks #budgettravel

*{self.disclosure}*"""

        content_id = self.db.add_content(
            trend_id=trend['id'],
            content_type='tiktok',
            title=f"TikTok Script: {trend['idea']}",
            content=script
        )

        return {
            'id': content_id,
            'type': 'tiktok',
            'title': f"TikTok Script: {trend['idea']}",
            'content': script,
            'trend_id': trend['id']
        }