import sqlite3
import logging
import os
from datetime import datetime

import openai
import requests


def get_new_ideas(db_path):
    """Fetches all content ideas with the status 'new' from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, city, idea, keywords FROM trends WHERE status = 'new'")
    ideas = cursor.fetchall()
    conn.close()
    logging.info(f"Found {len(ideas)} new ideas to generate content for.")
    return ideas

def get_affiliate_link(city, affiliate_id):
    """Generates a base Airbnb affiliate link for a given city."""
    return f"https://www.airbnb.com/s/{city}--CA--United-States/homes?af={affiliate_id}"

def shorten_link(link, api_token):
    """Shortens a URL using the Bitly API."""
    if not api_token or api_token == "YOUR_BITLY_API_TOKEN":
        logging.warning("Bitly API token not set. Returning original link.")
        return link
    try:
        headers = {'Authorization': f'Bearer {api_token}'}
        response = requests.post('https://api-ssl.bitly.com/v4/shorten', headers=headers, json={'long_url': link})
        response.raise_for_status()
        return response.json()['link']
    except Exception as e:
        logging.error(f"Error shortening link with Bitly: {e}")
        return link

def get_unsplash_image(query, api_key):
    """Fetches a relevant image URL from Unsplash."""
    if not api_key or api_key == "YOUR_UNSPLASH_ACCESS_KEY":
        logging.warning("Unsplash API key not set. Skipping image fetch.")
        return "No image fetched (API key missing)."
    try:
        headers = {'Authorization': f'Client-ID {api_key}'}
        params = {'query': query, 'per_page': 1, 'orientation': 'landscape'}
        response = requests.get('https://api.unsplash.com/search/photos', headers=headers, params=params)
        response.raise_for_status()
        results = response.json()['results']
        if results:
            return results[0]['urls']['regular']
        else:
            logging.warning(f"No Unsplash image found for query: {query}")
            return "No image found."
    except Exception as e:
        logging.error(f"Error fetching image from Unsplash: {e}")
        return "Image fetch failed."

def generate_content_with_ai(idea, keywords, city, affiliate_link, client):
    """Generates a full content package using OpenAI."""
    prompt = f"""**Objective:** Create a complete, engaging, and SEO-optimized content package for an Airbnb affiliate blog.

**Topic:** {idea}
**City:** {city}
**Keywords:** {keywords}
**Affiliate Link:** [This will be inserted into the content]

**Instructions:**
Generate the following four components. Ensure the tone is helpful, engaging, and encourages travel.

**1. Blog Post (800-1500 words):**
   - **Title:** Use the provided topic as the main title.
   - **Structure:** Write an engaging intro, 5-7 detailed sections, and a concluding call-to-action (CTA).
   - **Content:** Provide practical tips, itineraries, or recommendations. Naturally weave the keywords into the text, especially in headings (H2s).
   - **CTA:** The conclusion must seamlessly integrate the affiliate link. Phrase it like: 'Ready to explore? Find your perfect Nashville stay on Airbnb and start planning your adventure!'
   - **Disclaimer:** At the end of the post, include the line: '(Disclosure: This post contains affiliate links. If you book through these links, I may earn a small commission at no extra cost to you.)'

**2. Twitter/X Thread (5 Tweets):**
   - **Hook:** Start with a captivating first tweet.
   - **Content:** Break down the blog post's key points into a 5-tweet thread.
   - **Engagement:** Use hashtags (#Travel #Airbnb #{city.replace(' ', '')}) and a question to encourage replies.
   - **Link:** Include the affiliate link in the final tweet.

**3. Reddit Post:**
   - **Title:** Create a title suitable for a subreddit like r/travel or r/solotravel (e.g., 'My guide to finding budget-friendly hidden gems in {city}').
   - **Body:** Write a self-post (not just a link) that summarizes the blog post's best tips in a conversational, first-person tone. Provide genuine value.
   - **Link:** Include the affiliate link naturally within the body or at the end.

**4. TikTok Script (30-second voiceover):**
   - **Hook:** A strong opening line to grab attention in the first 3 seconds.
   - **Pacing:** Write a script for a fast-paced voiceover.
   - **Visual Cues:** Suggest 3-5 visual ideas in brackets, like [Shot of a cozy cabin interior] or [Quick cuts of Nashville food].
   - **CTA:** End with a verbal CTA: 'Check the link in my bio to book your stay!'

**Output Format:**
Use the following separators to structure your response clearly:

[BLOG_POST_START]
[Title: Your Blog Post Title]
[Content:
Your full blog post text here...]
[BLOG_POST_END]

[TWITTER_THREAD_START]
[1/5: Your first tweet...]
[2/5: Your second tweet...]
[3/5: ...]
[4/5: ...]
[5/5: ... {affiliate_link}]
[TWITTER_THREAD_END]

[REDDIT_POST_START]
[Title: Your Reddit Post Title]
[Body:
Your Reddit post body here...]
[REDDIT_POST_END]

[TIKTOK_SCRIPT_START]
[Hook: ...]
[VO: ...]
[Visuals: ...]
[CTA: ...]
[TIKTOK_SCRIPT_END]
"""
    logging.info(f"Generating content for idea: '{idea}'")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error calling OpenAI API for content generation: {e}")
        return None

def save_content(idea_id, city, content_package, image_url):
    """Saves the generated content into structured text files."""
    # Create a unique folder for this content idea
    folder_name = f"{datetime.now().strftime('%Y-%m-%d')}-{idea_id}-{city.replace(' ', '-').lower()}"
    save_path = os.path.join('content', folder_name)
    os.makedirs(save_path, exist_ok=True)

    # Save each component
    with open(os.path.join(save_path, 'image_url.txt'), 'w') as f:
        f.write(image_url)

    # A simple parser based on the custom format
    parts = {
        'blog_post': content_package.split('[BLOG_POST_START]')[1].split('[BLOG_POST_END]')[0],
        'twitter_thread': content_package.split('[TWITTER_THREAD_START]')[1].split('[TWITTER_THREAD_END]')[0],
        'reddit_post': content_package.split('[REDDIT_POST_START]')[1].split('[REDDIT_POST_END]')[0],
        'tiktok_script': content_package.split('[TIKTOK_SCRIPT_START]')[1].split('[TIKTOK_SCRIPT_END]')[0],
    }

    for part_name, content in parts.items():
        with open(os.path.join(save_path, f'{part_name}.txt'), 'w') as f:
            f.write(content.strip())

    logging.info(f"Saved content package to {save_path}")

def update_idea_status(idea_id, db_path):
    """Updates the status of an idea to 'generated' in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE trends SET status = 'generated' WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()
    logging.info(f"Updated status to 'generated' for idea ID: {idea_id}")

def run(config):
    """Main function to run the content generation agent."""
    db_path = config['system']['db_path']
    openai_api_key = config['openai']['api_key']
    affiliate_id = config['airbnb']['affiliate_id']
    bitly_token = config['bitly']['api_token']
    unsplash_key = config['unsplash']['access_key']

    client = openai.OpenAI(api_key=openai_api_key)

    ideas = get_new_ideas(db_path)
    for idea_id, city, idea_title, keywords in ideas:
        logging.info(f"Processing idea ID: {idea_id} - {idea_title}")

        # 1. Prepare links and images
        base_link = get_affiliate_link(city, affiliate_id)
        short_link = shorten_link(base_link, bitly_token)
        image_url = get_unsplash_image(f"{idea_title} {city}", unsplash_key)

        # 2. Generate content
        content_package = generate_content_with_ai(idea_title, keywords, city, short_link, client)

        if content_package:
            # 3. Save content to files
            save_content(idea_id, city, content_package, image_url)

            # 4. Update DB status
            update_idea_status(idea_id, db_path)
        else:
            logging.error(f"Failed to generate content for idea ID: {idea_id}. Skipping.")
