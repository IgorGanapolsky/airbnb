import logging
import os
import glob

import tweepy
import praw
from medium import Client


def find_unposted_content():
    """Finds content directories that haven't been posted yet."""
    content_dirs = glob.glob('content/*/')
    unposted = []
    for directory in content_dirs:
        if not os.path.exists(os.path.join(directory, '.posted')):
            unposted.append(directory)
    logging.info(f"Found {len(unposted)} content packages to post.")
    return unposted

def read_content_part(content_dir, part_name):
    """Reads a specific part of the content package from its file."""
    try:
        with open(os.path.join(content_dir, f'{part_name}.txt'), 'r') as f:
            return f.read()
    except FileNotFoundError:
        logging.warning(f"Content part '{part_name}' not found in {content_dir}")
        return None

def post_to_medium(client, config, title, content, tags):
    """Publishes a post to Medium."""
    user_id = config['medium']['user_id']
    publication_id = config['medium'].get('publication_id') # Optional

    post_data = {
        'title': title,
        'contentFormat': 'markdown',
        'content': content,
        'tags': tags,
        'publishStatus': 'public',
    }

    try:
        if publication_id:
            post = client.create_post_in_publication(publication_id=publication_id, data=post_data)
        else:
            post = client.create_post(user_id=user_id, data=post_data)
        
        logging.info(f"Successfully posted to Medium: {post['data']['url']}")
        return post['data']['url']
    except Exception as e:
        logging.error(f"Failed to post to Medium: {e}")
        return None

def post_to_twitter(client, thread_content, affiliate_link):
    """Posts a thread to Twitter/X."""
    tweets = thread_content.strip().split('\n')
    last_tweet_id = None
    try:
        for i, tweet_text in enumerate(tweets):
            # Replace placeholder with the actual link in the last tweet
            if i == len(tweets) - 1:
                tweet_text = tweet_text.replace('{affiliate_link}', affiliate_link)
            
            response = client.create_tweet(text=tweet_text, in_reply_to_tweet_id=last_tweet_id)
            last_tweet_id = response.data['id']
            logging.info(f"Posted tweet {i+1}/{len(tweets)}: {response.data['id']}")
        logging.info("Successfully posted Twitter thread.")
        return last_tweet_id
    except Exception as e:
        logging.error(f"Failed to post to Twitter: {e}")
        return None

def post_to_reddit(reddit, subreddit_name, title, body):
    """Posts to a specified subreddit."""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        submission = subreddit.submit(title, selftext=body)
        logging.info(f"Successfully posted to Reddit: {submission.shortlink}")
        return submission.shortlink
    except Exception as e:
        logging.error(f"Failed to post to Reddit: {e}")
        return None

def mark_as_posted(content_dir):
    """Creates a .posted file to mark the content as published."""
    with open(os.path.join(content_dir, '.posted'), 'w') as f:
        f.write(datetime.now().isoformat())
    logging.info(f"Marked {content_dir} as posted.")

def run(config, dry_run=True):
    """Main function to run the auto-posting agent."""
    if dry_run:
        logging.info("DRY RUN: Skipping all posting activities.")

    # --- Initialize APIs ---
    try:
        medium_client = Client(access_token=config['medium']['api_token'])
        twitter_client = tweepy.Client(
            consumer_key=config['twitter']['consumer_key'],
            consumer_secret=config['twitter']['consumer_secret'],
            access_token=config['twitter']['access_token'],
            access_token_secret=config['twitter']['access_token_secret']
        )
        reddit_client = praw.Reddit(
            client_id=config['reddit']['client_id'],
            client_secret=config['reddit']['client_secret'],
            user_agent=config['reddit']['user_agent'],
            username=config['reddit']['username'],
            password=config['reddit']['password']
        )
        logging.info("API clients initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize API clients: {e}. Aborting post run.")
        return

    # --- Find and process unposted content ---
    unposted_content = find_unposted_content()
    for content_dir in unposted_content:
        logging.info(f"Processing content in: {content_dir}")

        # Read all parts of the content package
        blog_post = read_content_part(content_dir, 'blog_post')
        twitter_thread = read_content_part(content_dir, 'twitter_thread')
        reddit_post = read_content_part(content_dir, 'reddit_post')
        # TikTok is manual, so we just note it
        read_content_part(content_dir, 'tiktok_script')

        # Extract titles and affiliate links
        blog_title = blog_post.split('[Title:')[1].split(']')[0].strip() if blog_post else "Untitled"
        reddit_title = reddit_post.split('[Title:')[1].split(']')[0].strip() if reddit_post else "Untitled"
        blog_body = blog_post.split('[Content:')[1].strip() if blog_post else ""
        reddit_body = reddit_post.split('[Body:')[1].strip() if reddit_post else ""
        # A bit of a hack to find the affiliate link
        affiliate_link = [word for word in twitter_thread.split() if 'bit.ly' in word][0] if twitter_thread else ""

        # Post to platforms if not in dry run
        if not dry_run:
            medium_success = post_to_medium(medium_client, config, blog_title, blog_body, ['travel', 'airbnb'])
            twitter_success = post_to_twitter(twitter_client, twitter_thread, affiliate_link)
            # Be careful with subreddits, choose a general one or one you own
            reddit_success = post_to_reddit(reddit_client, 'travel', reddit_title, reddit_body)

            # Mark as posted only if all were successful
            if medium_success and twitter_success and reddit_success:
                mark_as_posted(content_dir)
            else:
                logging.error(f"Failed to post one or more items for {content_dir}. It will be retried on the next run.")
        else:
            logging.info(f"DRY RUN: Would have posted '{blog_title}' to Medium, Twitter, and Reddit.")
