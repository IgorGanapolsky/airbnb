"""
Content Generation Agent
Creates blog posts, social media content, and TikTok scripts with SEO optimization.
"""

import re
import random
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import requests
from PIL import Image
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
        
        # Initialize AI client
        self.ai_client = self._init_ai_client()
        
        # Content directories
        self.content_dir = Path("content")
        self.images_dir = self.content_dir / "images"
        self.blogs_dir = self.content_dir / "blogs"
        self.social_dir = self.content_dir / "social"
        
        # Create directories
        for dir_path in [self.content_dir, self.images_dir, self.blogs_dir, self.social_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"ContentGenerationAgent initialized {'(DRY RUN)' if dry_run else ''}")
    
    def _init_ai_client(self):
        """Initialize AI client based on configuration."""
        primary_model = self.config.get('ai', {}).get('primary_model', 'openai')
        
        if primary_model == 'openai':
            api_key = self.config.get('api_keys', {}).get('openai_api_key')
            if api_key:
                openai.api_key = api_key
                return 'openai'
        elif primary_model == 'anthropic':
            api_key = self.config.get('api_keys', {}).get('anthropic_api_key')
            if api_key:
                return Anthropic(api_key=api_key)
        
        return None
    
    def generate_content(self, limit: int = None) -> List[Dict[str, Any]]:
        """Generate content from pending trends."""
        self.logger.info("Starting content generation...")
        
        # Get pending trends
        trends = self.db.get_pending_trends(limit=limit or 5)
        generated_content = []
        
        for trend in trends:
            try:
                # Generate content for each idea in the trend
                for idea in trend['content_ideas']:
                    content_items = self._generate_content_for_idea(trend, idea)
                    generated_content.extend(content_items)
                
                # Mark trend as processed
                if not self.dry_run:
                    self.db.update_trend_status(trend['id'], 'processed')
                
            except Exception as e:
                self.logger.error(f"Failed to generate content for trend {trend.get('id')}: {e}")
                continue
        
        self.logger.info(f"Generated {len(generated_content)} content items")
        return generated_content
    
    def _generate_content_for_idea(self, trend: Dict, idea: str) -> List[Dict[str, Any]]:
        """Generate multiple content types for a single idea."""
        content_items = []
        content_types = self.config.get('content', {}).get('content_types', ['blog_post'])
        
        for content_type in content_types:
            try:
                content_item = self._generate_single_content(trend, idea, content_type)
                if content_item:
                    content_items.append(content_item)
            except Exception as e:
                self.logger.error(f"Failed to generate {content_type} for idea '{idea}': {e}")
                continue
        
        return content_items
    
    def _generate_single_content(self, trend: Dict, idea: str, content_type: str) -> Optional[Dict[str, Any]]:
        """Generate a single piece of content."""
        if not self.ai_client:
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
                return None
            
            # Add affiliate links
            content_data = self._add_affiliate_links(content_data)
            
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
                    'images': images
                }
            else:
                self.logger.info(f"DRY RUN: Would save {content_type} - {content_data['title']}")
                return {
                    'content_type': content_type,
                    'title': content_data['title'],
                    'quality_score': quality_score
                }
                
        except Exception as e:
            self.logger.error(f"Failed to generate {content_type}: {e}")
            return None
    
    def _generate_blog_post(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate a blog post."""
        prompt = self._build_blog_post_prompt(trend, idea)
        content = self._call_ai_api(prompt, max_tokens=2000)
        
        if not content:
            return None
        
        # Parse blog post structure
        title, body = self._parse_blog_post(content)
        seo_keywords = self._extract_seo_keywords(content, trend['keywords'])
        
        return {
            'title': title,
            'content': body,
            'seo_keywords': seo_keywords,
            'word_count': len(body.split())
        }
    
    def _generate_twitter_thread(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate a Twitter thread."""
        prompt = self._build_twitter_thread_prompt(trend, idea)
        content = self._call_ai_api(prompt, max_tokens=800)
        
        if not content:
            return None
        
        # Parse thread into tweets
        tweets = self._parse_twitter_thread(content)
        hashtags = self.config.get('social_platforms', {}).get('twitter', {}).get('hashtags', [])
        
        return {
            'title': f"Twitter Thread: {idea[:50]}...",
            'content': '\n\n'.join(tweets),
            'tweets': tweets,
            'hashtags': hashtags
        }
    
    def _generate_reddit_post(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate a Reddit post."""
        prompt = self._build_reddit_post_prompt(trend, idea)
        content = self._call_ai_api(prompt, max_tokens=1000)
        
        if not content:
            return None
        
        title, body = self._parse_reddit_post(content)
        
        return {
            'title': title,
            'content': body,
            'subreddits': self.config.get('social_platforms', {}).get('reddit', {}).get('subreddits', [])
        }
    
    def _generate_tiktok_script(self, trend: Dict, idea: str) -> Optional[Dict[str, Any]]:
        """Generate a TikTok script."""
        prompt = self._build_tiktok_script_prompt(trend, idea)
        content = self._call_ai_api(prompt, max_tokens=600)
        
        if not content:
            return None
        
        script_data = self._parse_tiktok_script(content)
        
        return {
            'title': f"TikTok: {idea[:50]}...",
            'content': script_data['script'],
            'visual_cues': script_data.get('visual_cues', []),
            'duration': script_data.get('duration', '30s')
        }
    
    def _build_blog_post_prompt(self, trend: Dict, idea: str) -> str:
        """Build prompt for blog post generation."""
        affiliate_link = self.config.get('affiliate', {}).get('airbnb_affiliate_link', '')
        disclosure = self.config.get('legal', {}).get('affiliate_disclosure', '')
        
        return f"""
Write a comprehensive blog post about: {idea}

REQUIREMENTS:
- 800-1500 words
- SEO optimized with H1, H2, H3 headers
- Include these keywords naturally: {', '.join(trend['keywords'][:5])}
- City focus: {trend['city']}
- Engaging introduction and conclusion
- Include 5-7 specific Airbnb recommendations (fictional but realistic)
- Add call-to-action with affiliate link
- Include affiliate disclosure

STRUCTURE:
# [Engaging Title with SEO keywords]

## Introduction
[Hook the reader with why {trend['city']} is special]

## [Section 1 - Overview/Background]
## [Section 2 - Top Recommendations]
## [Section 3 - Neighborhood Guide]
## [Section 4 - Tips & Insider Info]
## [Section 5 - Budget Considerations]

## Conclusion
[Call to action with affiliate link]

AFFILIATE LINK: {affiliate_link}
DISCLOSURE: {disclosure}

Write the complete blog post now:
"""
    
    def _build_twitter_thread_prompt(self, trend: Dict, idea: str) -> str:
        """Build prompt for Twitter thread generation."""
        hashtags = self.config.get('social_platforms', {}).get('twitter', {}).get('hashtags', [])
        
        return f"""
Create a Twitter thread about: {idea}

REQUIREMENTS:
- 5-7 tweets maximum
- Each tweet under 280 characters
- Engaging hook in first tweet
- Include relevant hashtags: {' '.join(hashtags[:3])}
- City focus: {trend['city']}
- Include call-to-action in final tweet
- Use emojis appropriately
- Thread should tell a story/provide value

FORMAT:
1/7 [First tweet with hook]
2/7 [Second tweet]
...
7/7 [Final tweet with CTA]

Write the Twitter thread now:
"""
    
    def _call_ai_api(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Call AI API with the given prompt."""
        try:
            if isinstance(self.ai_client, str) and self.ai_client == 'openai':
                response = openai.ChatCompletion.create(
                    model=self.config.get('ai', {}).get('openai_model', 'gpt-4o-mini'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=self.config.get('ai', {}).get('temperature', 0.7)
                )
                return response.choices[0].message.content
            else:
                # Anthropic
                response = self.ai_client.messages.create(
                    model=self.config.get('ai', {}).get('anthropic_model', 'claude-3-haiku-20240307'),
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
        except Exception as e:
            self.logger.error(f"AI API call failed: {e}")
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
    
    def _add_affiliate_links(self, content_data: Dict) -> Dict:
        """Add affiliate links to content."""
        affiliate_link = self.config.get('affiliate', {}).get('airbnb_affiliate_link', '')
        
        if affiliate_link:
            content_data['affiliate_links'] = [affiliate_link]
            
            # Add link to content if not already present
            if 'content' in content_data and affiliate_link not in content_data['content']:
                content_data['content'] += f"\n\n[Book your stay here]({affiliate_link})"
        
        return content_data
    
    def _calculate_quality_score(self, content_data: Dict, content_type: str) -> float:
        """Calculate quality score for content."""
        score = 0.0
        weights = self.config.get('quality_filters', {}).get('scoring_weights', {})
        
        # SEO optimization score
        if content_data.get('seo_keywords'):
            score += weights.get('seo_optimization', 0.3)
        
        # Content length score
        word_count = len(content_data.get('content', '').split())
        if content_type == 'blog_post':
            min_words = self.config.get('quality_filters', {}).get('min_word_count', 500)
            max_words = self.config.get('quality_filters', {}).get('max_word_count', 2000)
            if min_words <= word_count <= max_words:
                score += weights.get('readability', 0.2)
        
        # Affiliate integration score
        if content_data.get('affiliate_links'):
            score += weights.get('affiliate_integration', 0.3)
        
        # Engagement potential (basic heuristic)
        content_text = content_data.get('content', '')
        if any(word in content_text.lower() for word in ['unique', 'hidden', 'secret', 'local', 'authentic']):
            score += weights.get('engagement_potential', 0.2)
        
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
