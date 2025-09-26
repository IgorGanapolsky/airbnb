import time
import json
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional
import tweepy
import praw
import requests
from utils.config_loader import config
from utils.database import Database

logger = logging.getLogger(__name__)

class AutoPoster:
    def __init__(self):
        self.config = config.config
        self.db = Database(self.config['system']['database_path'])
        self.dry_run = self.config.get('system.dry_run', False)

        self._setup_social_apis()

    def _setup_social_apis(self):
        # Twitter/X API setup
        if self.config.get('social.twitter.enabled', False):
            try:
                auth = tweepy.OAuthHandler(
                    self.config['social']['twitter']['api_key'],
                    self.config['social']['twitter']['api_secret']
                )
                auth.set_access_token(
                    self.config['social']['twitter']['access_token'],
                    self.config['social']['twitter']['access_token_secret']
                )
                self.twitter_api = tweepy.API(auth, wait_on_rate_limit=True)

                # Verify credentials
                self.twitter_api.verify_credentials()
                logger.info("Twitter API initialized successfully")
            except Exception as e:
                logger.error(f"Twitter API setup failed: {e}")
                self.twitter_api = None
        else:
            self.twitter_api = None

        # Reddit API setup
        if self.config.get('social.reddit.enabled', False):
            try:
                self.reddit = praw.Reddit(
                    client_id=self.config['social']['reddit']['client_id'],
                    client_secret=self.config['social']['reddit']['client_secret'],
                    user_agent=self.config['social']['reddit']['user_agent'],
                    username=self.config['social']['reddit']['username'],
                    password=self.config['social']['reddit']['password']
                )

                # Verify credentials
                logger.info(f"Reddit API initialized for user: {self.reddit.user.me()}")
            except Exception as e:
                logger.error(f"Reddit API setup failed: {e}")
                self.reddit = None
        else:
            self.reddit = None

        # Medium API setup
        if self.config.get('social.medium.enabled', False):
            self.medium_token = self.config['social']['medium']['integration_token']
            self.medium_publication_id = self.config['social']['medium'].get('publication_id')
        else:
            self.medium_token = None

    def post_scheduled_content(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Post unpublished content to social platforms"""
        results = []

        # Get unpublished content
        blog_posts = self.db.get_unpublished_content('blog', limit=2)
        twitter_threads = self.db.get_unpublished_content('twitter', limit=3)
        reddit_posts = self.db.get_unpublished_content('reddit', limit=2)

        # Post blogs to Medium
        for post in blog_posts:
            result = self._post_to_medium(post)
            results.append(result)
            time.sleep(5)  # Rate limiting

        # Post Twitter threads
        for thread in twitter_threads:
            result = self._post_to_twitter(thread)
            results.append(result)
            time.sleep(10)  # Rate limiting

        # Post to Reddit
        for post in reddit_posts:
            result = self._post_to_reddit(post)
            results.append(result)
            time.sleep(30)  # Reddit is strict about rate limiting

        return results

    def _post_to_medium(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post blog content to Medium"""
        if not self.medium_token:
            return self._create_error_result(content, 'medium', "Medium API not configured")

        try:
            if self.dry_run:
                return self._create_dry_run_result(content, 'medium')

            # Get user info
            headers = {
                'Authorization': f'Bearer {self.medium_token}',
                'Content-Type': 'application/json'
            }

            user_response = requests.get('https://api.medium.com/v1/me', headers=headers)
            if user_response.status_code != 200:
                raise Exception(f"Failed to get user info: {user_response.text}")

            user_id = user_response.json()['data']['id']

            # Prepare post data
            post_data = {
                'title': content['title'],
                'contentFormat': 'markdown',
                'content': content['content'],
                'publishStatus': 'public',
                'tags': self._extract_tags_from_content(content['content'])
            }

            # Post to publication if configured
            if self.medium_publication_id:
                url = f"https://api.medium.com/v1/publications/{self.medium_publication_id}/posts"
            else:
                url = f"https://api.medium.com/v1/users/{user_id}/posts"

            response = requests.post(url, headers=headers, json=post_data)

            if response.status_code == 201:
                post_data = response.json()['data']
                post_url = post_data['url']

                self.db.mark_content_posted(
                    content['id'],
                    'medium',
                    post_data['id'],
                    post_url
                )

                return {
                    'platform': 'medium',
                    'status': 'success',
                    'content_id': content['id'],
                    'post_id': post_data['id'],
                    'url': post_url
                }
            else:
                raise Exception(f"Post failed: {response.text}")

        except Exception as e:
            logger.error(f"Medium posting error: {e}")
            return self._create_error_result(content, 'medium', str(e))

    def _post_to_twitter(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post thread content to Twitter/X"""
        if not self.twitter_api:
            return self._create_error_result(content, 'twitter', "Twitter API not configured")

        try:
            if self.dry_run:
                return self._create_dry_run_result(content, 'twitter')

            tweets = self._split_thread_content(content['content'])
            tweet_ids = []
            reply_to_id = None

            for i, tweet_text in enumerate(tweets):
                if i == 0:
                    # First tweet
                    tweet = self.twitter_api.update_status(tweet_text)
                    reply_to_id = tweet.id
                    tweet_ids.append(tweet.id)
                else:
                    # Reply tweets
                    tweet = self.twitter_api.update_status(
                        tweet_text,
                        in_reply_to_status_id=reply_to_id
                    )
                    reply_to_id = tweet.id
                    tweet_ids.append(tweet.id)

                time.sleep(2)  # Small delay between tweets

            # Mark as posted
            thread_url = f"https://twitter.com/{self.twitter_api.verify_credentials().screen_name}/status/{tweet_ids[0]}"

            self.db.mark_content_posted(
                content['id'],
                'twitter',
                str(tweet_ids[0]),
                thread_url
            )

            return {
                'platform': 'twitter',
                'status': 'success',
                'content_id': content['id'],
                'tweet_ids': tweet_ids,
                'url': thread_url
            }

        except Exception as e:
            logger.error(f"Twitter posting error: {e}")
            return self._create_error_result(content, 'twitter', str(e))

    def _post_to_reddit(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Reddit"""
        if not self.reddit:
            return self._create_error_result(content, 'reddit', "Reddit API not configured")

        try:
            if self.dry_run:
                return self._create_dry_run_result(content, 'reddit')

            subreddits = self.config['social']['reddit']['subreddits']
            results = []

            for subreddit_name in subreddits[:1]:  # Post to one subreddit at a time
                subreddit = self.reddit.subreddit(subreddit_name)

                # Create self post
                submission = subreddit.submit(
                    title=self._create_reddit_title(content['title']),
                    selftext=content['content']
                )

                post_url = f"https://reddit.com{submission.permalink}"

                self.db.mark_content_posted(
                    content['id'],
                    f'reddit_{subreddit_name}',
                    submission.id,
                    post_url
                )

                results.append({
                    'platform': f'reddit_{subreddit_name}',
                    'status': 'success',
                    'content_id': content['id'],
                    'post_id': submission.id,
                    'url': post_url
                })

                break  # Only post to one subreddit per run to avoid spam

            return results[0] if results else self._create_error_result(content, 'reddit', "No subreddits posted to")

        except Exception as e:
            logger.error(f"Reddit posting error: {e}")
            return self._create_error_result(content, 'reddit', str(e))

    def _split_thread_content(self, content: str) -> List[str]:
        """Split thread content into individual tweets"""
        lines = content.split('\n')
        tweets = []
        current_tweet = ""

        for line in lines:
            if line.strip().startswith(('1/', '2/', '3/', '4/', '5/', '6/', '7/', '8/', '9/')):
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = line.strip()
            elif line.strip():
                if current_tweet:
                    current_tweet += " " + line.strip()

        if current_tweet:
            tweets.append(current_tweet.strip())

        # Clean up tweet numbering
        cleaned_tweets = []
        for tweet in tweets:
            # Remove thread numbering (1/6, 2/6, etc.)
            tweet = tweet.split(' ', 1)[1] if '/' in tweet.split(' ')[0] else tweet
            cleaned_tweets.append(tweet[:280])  # Twitter character limit

        return cleaned_tweets

    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract hashtags from content for Medium tags"""
        hashtags = []
        words = content.split()

        for word in words:
            if word.startswith('#'):
                tag = word[1:].replace('#', '').lower()
                if tag and len(tag) < 25:  # Medium tag limit
                    hashtags.append(tag)

        # Default tags if none found
        if not hashtags:
            hashtags = ['travel', 'airbnb', 'vacation']

        return hashtags[:5]  # Medium allows max 5 tags

    def _create_reddit_title(self, title: str) -> str:
        """Create Reddit-friendly title"""
        # Remove markdown formatting
        title = title.replace('#', '').strip()

        # Add Reddit-style prefix if not present
        if not any(prefix in title.lower() for prefix in ['need', 'looking', 'advice', 'tips', 'help']):
            if 'hidden' in title.lower() or 'gem' in title.lower():
                title = f"Found some amazing {title.lower()}"
            else:
                title = f"Advice needed: {title}"

        return title[:300]  # Reddit title limit

    def _create_error_result(self, content: Dict[str, Any], platform: str, error: str) -> Dict[str, Any]:
        return {
            'platform': platform,
            'status': 'error',
            'content_id': content['id'],
            'error': error
        }

    def _create_dry_run_result(self, content: Dict[str, Any], platform: str) -> Dict[str, Any]:
        return {
            'platform': platform,
            'status': 'dry_run',
            'content_id': content['id'],
            'message': f"Would post to {platform}: {content['title'][:50]}..."
        }

    def send_posting_summary(self, results: List[Dict[str, Any]]):
        """Send email summary of posting activity"""
        if not self.config.get('email.enabled', False):
            return

        successful_posts = [r for r in results if r['status'] == 'success']
        failed_posts = [r for r in results if r['status'] == 'error']

        if not results:
            return

        subject = f"Airbnb Bot - Posted {len(successful_posts)} items"

        body = f"""
Posting Summary for {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ Successfully Posted: {len(successful_posts)}
❌ Failed Posts: {len(failed_posts)}

SUCCESSFUL POSTS:
"""

        for post in successful_posts:
            body += f"- {post['platform']}: {post.get('url', 'No URL')}\n"

        if failed_posts:
            body += "\nFAILED POSTS:\n"
            for post in failed_posts:
                body += f"- {post['platform']}: {post.get('error', 'Unknown error')}\n"

        self._send_email(subject, body)

    def _send_email(self, subject: str, body: str):
        """Send email notification"""
        try:
            sender_email = self.config['email']['sender_email']
            sender_password = self.config['email']['sender_password']
            recipient_email = self.config['email']['recipient_email']

            msg = MimeMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MimeText(body, 'plain'))

            server = smtplib.SMTP(
                self.config['email']['smtp_server'],
                self.config['email']['smtp_port']
            )
            server.starttls()
            server.login(sender_email, sender_password)

            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()

            logger.info("Email notification sent successfully")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def get_posting_stats(self) -> Dict[str, Any]:
        """Get statistics about posting activity"""
        stats = self.db.get_performance_stats(30)

        return {
            'total_posts_30_days': stats['total_posts'],
            'total_clicks': stats['total_clicks'],
            'estimated_revenue': stats['total_revenue'],
            'ctr': stats['ctr'],
            'conversion_rate': stats['conversion_rate']
        }