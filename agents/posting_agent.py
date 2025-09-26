"""
Posting Agent
Handles automated posting to Medium, Twitter/X, Reddit with scheduling and fallback mechanisms.
"""

import re
import time
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import tweepy
import praw
import requests
from bitlyshortener import Shortener

from utils.logger import get_logger
from utils.database import DatabaseManager


class PostingAgent:
    """Agent responsible for posting content to various social media platforms."""
    
    def __init__(self, config: Dict[str, Any], db: DatabaseManager, dry_run: bool = False):
        """Initialize the posting agent."""
        self.config = config
        self.db = db
        self.dry_run = dry_run
        self.logger = get_logger(__name__)
        
        # Initialize platform clients
        self.twitter_client = self._init_twitter_client()
        self.reddit_client = self._init_reddit_client()
        self.bitly_client = self._init_bitly_client()
        
        self.logger.info(f"PostingAgent initialized {'(DRY RUN)' if dry_run else ''}")
    
    def _init_twitter_client(self) -> Optional[tweepy.Client]:
        """Initialize Twitter API client."""
        try:
            api_keys = self.config.get('api_keys', {})
            if not all([
                api_keys.get('twitter_bearer_token'),
                api_keys.get('twitter_api_key'),
                api_keys.get('twitter_api_secret'),
                api_keys.get('twitter_access_token'),
                api_keys.get('twitter_access_token_secret')
            ]):
                self.logger.warning("Twitter API credentials not fully configured")
                return None
            
            client = tweepy.Client(
                bearer_token=api_keys['twitter_bearer_token'],
                consumer_key=api_keys['twitter_api_key'],
                consumer_secret=api_keys['twitter_api_secret'],
                access_token=api_keys['twitter_access_token'],
                access_token_secret=api_keys['twitter_access_token_secret'],
                wait_on_rate_limit=True
            )
            
            # Test the connection
            client.get_me()
            self.logger.info("Twitter client initialized successfully")
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter client: {e}")
            return None
    
    def _init_reddit_client(self) -> Optional[praw.Reddit]:
        """Initialize Reddit API client."""
        try:
            api_keys = self.config.get('api_keys', {})
            if not all([
                api_keys.get('reddit_client_id'),
                api_keys.get('reddit_client_secret'),
                api_keys.get('reddit_user_agent')
            ]):
                self.logger.warning("Reddit API credentials not configured")
                return None
            
            reddit = praw.Reddit(
                client_id=api_keys['reddit_client_id'],
                client_secret=api_keys['reddit_client_secret'],
                user_agent=api_keys['reddit_user_agent']
            )
            
            # Test the connection
            reddit.user.me()
            self.logger.info("Reddit client initialized successfully")
            return reddit
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit client: {e}")
            return None
    
    def _init_bitly_client(self) -> Optional[Shortener]:
        """Initialize Bitly URL shortener."""
        try:
            access_token = self.config.get('api_keys', {}).get('bitly_access_token')
            if not access_token:
                self.logger.warning("Bitly access token not configured")
                return None
            
            shortener = Shortener(tokens=[access_token], max_cache_size=256)
            self.logger.info("Bitly client initialized successfully")
            return shortener
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Bitly client: {e}")
            return None
    
    def post_content(self, limit: int = None) -> List[Dict[str, Any]]:
        """Post ready content to platforms."""
        self.logger.info("Starting content posting...")
        
        # Get ready content
        content_items = self.db.get_ready_content(limit=limit or 5)
        posted_items = []
        
        for content in content_items:
            try:
                # Determine which platforms to post to
                platforms = self._get_target_platforms(content['content_type'])
                
                for platform in platforms:
                    if self._should_post_to_platform(platform):
                        result = self._post_to_platform(content, platform)
                        if result:
                            posted_items.append(result)
                            
                            # Add delay between posts to avoid rate limiting
                            if not self.dry_run:
                                time.sleep(30)  # 30 second delay
                
                # Mark content as posted if at least one platform succeeded
                if posted_items and not self.dry_run:
                    self.db.update_content_status(content['id'], 'posted')
                
            except Exception as e:
                self.logger.error(f"Failed to post content {content.get('id')}: {e}")
                continue
        
        self.logger.info(f"Posted {len(posted_items)} items across platforms")
        return posted_items
    
    def _get_target_platforms(self, content_type: str) -> List[str]:
        """Get target platforms for content type."""
        platform_map = {
            'blog_post': ['medium'],
            'twitter_thread': ['twitter'],
            'reddit_post': ['reddit'],
            'tiktok_script': []  # Manual upload for now
        }
        
        platforms = platform_map.get(content_type, [])
        
        # Filter by enabled platforms
        enabled_platforms = []
        for platform in platforms:
            platform_config = self.config.get('social_platforms', {}).get(platform, {})
            if platform_config.get('enabled', False):
                enabled_platforms.append(platform)
        
        return enabled_platforms
    
    def _should_post_to_platform(self, platform: str) -> bool:
        """Check if we should post to a platform based on rate limits."""
        # Simple rate limiting - check posts in last hour
        try:
            recent_posts = self.db.get_recent_posts(platform, hours=1)
            max_posts_per_hour = self.config.get('automation', {}).get('rate_limits', {}).get('posts_per_hour', 2)
            
            return len(recent_posts) < max_posts_per_hour
        except:
            return True  # Default to allowing posts
    
    def _post_to_platform(self, content: Dict, platform: str) -> Optional[Dict[str, Any]]:
        """Post content to a specific platform."""
        try:
            if platform == 'medium':
                return self._post_to_medium(content)
            elif platform == 'twitter':
                return self._post_to_twitter(content)
            elif platform == 'reddit':
                return self._post_to_reddit(content)
            else:
                self.logger.warning(f"Unknown platform: {platform}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to post to {platform}: {e}")
            return None
    
    def _post_to_medium(self, content: Dict) -> Optional[Dict[str, Any]]:
        """Post blog content to Medium."""
        if not self.config.get('api_keys', {}).get('medium_access_token'):
            self.logger.warning("Medium access token not configured")
            return None
        
        try:
            # Prepare content for Medium
            title = content['title']
            body = content['content']
            tags = self.config.get('social_platforms', {}).get('medium', {}).get('tags', [])
            
            # Add affiliate disclosure
            disclosure = self.config.get('legal', {}).get('affiliate_disclosure', '')
            if disclosure:
                body = f"{body}\n\n---\n\n*{disclosure}*"
            
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would post to Medium - {title}")
                return {'platform': 'medium', 'title': title, 'status': 'dry_run'}
            
            # Create post via Medium API
            access_token = self.config.get('api_keys', {}).get('medium_access_token')
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get user ID first
            user_response = requests.get('https://api.medium.com/v1/me', headers=headers)
            if user_response.status_code != 200:
                raise Exception(f"Failed to get Medium user: {user_response.text}")
            
            user_id = user_response.json()['data']['id']
            
            # Create post
            post_data = {
                'title': title,
                'contentFormat': 'markdown',
                'content': body,
                'tags': tags[:5],  # Medium allows max 5 tags
                'publishStatus': 'public'
            }
            
            post_response = requests.post(
                f'https://api.medium.com/v1/users/{user_id}/posts',
                headers=headers,
                json=post_data
            )
            
            if post_response.status_code == 201:
                post_data = post_response.json()['data']
                
                # Save post record
                post_id = self.db.insert_post(content['id'], 'medium')
                self.db.update_post_status(
                    post_id, 'posted',
                    platform_post_id=post_data['id'],
                    post_url=post_data['url']
                )
                
                self.logger.info(f"Posted to Medium: {post_data['url']}")
                return {
                    'platform': 'medium',
                    'post_id': post_id,
                    'url': post_data['url'],
                    'title': title
                }
            else:
                raise Exception(f"Medium API error: {post_response.text}")
                
        except Exception as e:
            self.logger.error(f"Failed to post to Medium: {e}")
            return None
    
    def _post_to_twitter(self, content: Dict) -> Optional[Dict[str, Any]]:
        """Post thread content to Twitter."""
        if not self.twitter_client:
            self.logger.warning("Twitter client not available")
            return None
        
        try:
            # Parse tweets from content
            tweets = self._parse_twitter_content(content)
            if not tweets:
                self.logger.warning("No tweets found in content")
                return None
            
            if self.dry_run:
                self.logger.info(f"DRY RUN: Would post Twitter thread with {len(tweets)} tweets")
                return {'platform': 'twitter', 'tweets': len(tweets), 'status': 'dry_run'}
            
            # Post thread
            thread_ids = []
            reply_to_id = None
            
            for i, tweet_text in enumerate(tweets):
                # Add hashtags to last tweet
                if i == len(tweets) - 1:
                    hashtags = self.config.get('social_platforms', {}).get('twitter', {}).get('hashtags', [])
                    if hashtags:
                        tweet_text += f" {' '.join(hashtags[:3])}"  # Max 3 hashtags
                
                # Ensure tweet is under 280 characters
                if len(tweet_text) > 280:
                    tweet_text = tweet_text[:277] + "..."
                
                response = self.twitter_client.create_tweet(
                    text=tweet_text,
                    in_reply_to_tweet_id=reply_to_id
                )
                
                tweet_id = response.data['id']
                thread_ids.append(tweet_id)
                reply_to_id = tweet_id
                
                # Small delay between tweets
                time.sleep(2)
            
            # Save post record
            post_id = self.db.insert_post(content['id'], 'twitter')
            self.db.update_post_status(
                post_id, 'posted',
                platform_post_id=thread_ids[0],  # First tweet ID
                post_url=f"https://twitter.com/user/status/{thread_ids[0]}"
            )
            
            self.logger.info(f"Posted Twitter thread with {len(thread_ids)} tweets")
            return {
                'platform': 'twitter',
                'post_id': post_id,
                'thread_ids': thread_ids,
                'tweet_count': len(thread_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to post to Twitter: {e}")
            return None

    def _post_to_reddit(self, content: Dict) -> Optional[Dict[str, Any]]:
        """Post content to Reddit."""
        if not self.reddit_client:
            self.logger.warning("Reddit client not available")
            return None

        try:
            title = content['title']
            body = content['content']
            subreddits = self.config.get('social_platforms', {}).get('reddit', {}).get('subreddits', [])

            if not subreddits:
                self.logger.warning("No Reddit subreddits configured")
                return None

            # Choose a random subreddit to avoid spam detection
            import random
            subreddit_name = random.choice(subreddits)

            if self.dry_run:
                self.logger.info(f"DRY RUN: Would post to r/{subreddit_name} - {title}")
                return {'platform': 'reddit', 'subreddit': subreddit_name, 'status': 'dry_run'}

            # Add affiliate disclosure
            disclosure = self.config.get('legal', {}).get('affiliate_disclosure', '')
            if disclosure:
                body = f"{body}\n\n---\n\n{disclosure}"

            # Submit post
            subreddit = self.reddit_client.subreddit(subreddit_name)
            submission = subreddit.submit(title=title, selftext=body)

            # Save post record
            post_id = self.db.insert_post(content['id'], 'reddit')
            self.db.update_post_status(
                post_id, 'posted',
                platform_post_id=submission.id,
                post_url=f"https://reddit.com{submission.permalink}"
            )

            self.logger.info(f"Posted to r/{subreddit_name}: {submission.permalink}")
            return {
                'platform': 'reddit',
                'post_id': post_id,
                'subreddit': subreddit_name,
                'url': f"https://reddit.com{submission.permalink}"
            }

        except Exception as e:
            self.logger.error(f"Failed to post to Reddit: {e}")
            return None

    def _parse_twitter_content(self, content: Dict) -> List[str]:
        """Parse content to extract individual tweets."""
        content_text = content.get('content', '')

        # If content has pre-parsed tweets
        if 'tweets' in content:
            return content['tweets']

        # Split by double newlines or numbered format
        tweets = []
        lines = content_text.split('\n')
        current_tweet = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for tweet number format (1/7, 2/7, etc.)
            if re.match(r'^\d+/\d+', line):
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = re.sub(r'^\d+/\d+\s*', '', line)
            else:
                current_tweet += " " + line

        if current_tweet:
            tweets.append(current_tweet.strip())

        # Fallback: split long content into tweet-sized chunks
        if not tweets and content_text:
            tweets = self._split_into_tweets(content_text)

        return tweets[:7]  # Twitter thread limit

    def _split_into_tweets(self, text: str, max_length: int = 250) -> List[str]:
        """Split long text into tweet-sized chunks."""
        words = text.split()
        tweets = []
        current_tweet = ""

        for word in words:
            if len(current_tweet + " " + word) <= max_length:
                current_tweet += " " + word if current_tweet else word
            else:
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = word

        if current_tweet:
            tweets.append(current_tweet.strip())

        return tweets

    def _shorten_url(self, url: str) -> str:
        """Shorten URL using Bitly."""
        if not self.bitly_client:
            return url

        try:
            short_url = self.bitly_client.shorten_urls([url])[0]
            return short_url
        except Exception as e:
            self.logger.error(f"Failed to shorten URL: {e}")
            return url

    def send_notification_email(self, subject: str, message: str):
        """Send notification email."""
        try:
            email_config = self.config.get('email', {})
            sender_email = email_config.get('sender_email')
            sender_password = email_config.get('sender_password')
            recipient_email = email_config.get('recipient_email')

            if not all([sender_email, sender_password, recipient_email]):
                self.logger.warning("Email configuration incomplete")
                return

            if self.dry_run:
                self.logger.info(f"DRY RUN: Would send email - {subject}")
                return

            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            # Send email
            server = smtplib.SMTP(
                email_config.get('smtp_server', 'smtp.gmail.com'),
                email_config.get('smtp_port', 587)
            )
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Notification email sent: {subject}")

        except Exception as e:
            self.logger.error(f"Failed to send notification email: {e}")

    def schedule_content(self, content_id: int, platform: str, scheduled_time: datetime) -> bool:
        """Schedule content for future posting."""
        try:
            post_id = self.db.insert_post(content_id, platform, scheduled_time)
            self.logger.info(f"Scheduled content {content_id} for {platform} at {scheduled_time}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to schedule content: {e}")
            return False

    def process_scheduled_posts(self):
        """Process posts scheduled for current time."""
        try:
            # Get posts scheduled for now (within 5 minutes)
            current_time = datetime.now()
            scheduled_posts = self.db.get_scheduled_posts()

            for post in scheduled_posts:
                scheduled_time = datetime.fromisoformat(post['scheduled_at'])
                if scheduled_time <= current_time:
                    # Get content and post it
                    content = self.db.get_content_by_id(post['content_id'])
                    if content:
                        result = self._post_to_platform(content, post['platform'])
                        if result:
                            self.logger.info(f"Posted scheduled content: {post['id']}")
                        else:
                            self.db.update_post_status(post['id'], 'failed',
                                                     error_message="Failed to post scheduled content")

        except Exception as e:
            self.logger.error(f"Failed to process scheduled posts: {e}")
