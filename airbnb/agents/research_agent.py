import sqlite3
import logging
from datetime import datetime

import openai
from pytrends.request import TrendReq


def setup_database(db_path):
    """Initializes the database and creates the trends table if it doesn't exist."""
    logging.info(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            city TEXT NOT NULL,
            idea TEXT NOT NULL,
            keywords TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new'
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database setup complete.")


def get_target_city(cities):
    """Selects a city from the list based on the week of the year."""
    week_number = datetime.now().isocalendar()[1]
    city_index = week_number % len(cities)
    selected_city = cities[city_index]
    logging.info(f"Selected target city for week {week_number}: {selected_city}")
    return selected_city

def fetch_google_trends(city):
    """Fetches rising related queries from Google Trends."""
    pytrends = TrendReq(hl='en-US', tz=360)
    kw_list = [f"airbnb {city} travel 2025"]
    pytrends.build_payload(kw_list, cat=0, timeframe='today 3-m', geo='US', gprop='')

    related_queries = pytrends.related_queries()
    rising_queries = related_queries[kw_list[0]].get('rising')

    if rising_queries is None or rising_queries.empty:
        logging.warning(f"No rising trends found for {city}. Using top queries instead.")
        top_queries = related_queries[kw_list[0]].get('top')
        if top_queries is None or top_queries.empty:
            logging.error(f"Could not fetch any Google Trends data for {city}.")
            return []
        return top_queries['query'].head(10).tolist()

    return rising_queries['query'].head(10).tolist()

def analyze_trends_with_ai(trends, city, client):
    """Uses OpenAI to generate content ideas from a list of trends."""
    if not trends:
        logging.info("No trends to analyze.")
        return []

    prompt = f"""You are an expert in travel content marketing for Airbnb.
    Analyze the following travel search trends for the city of {city}:
    Trends: {", ".join(trends)}

    Based on these trends, generate 5 unique, evergreen content ideas. For each idea, provide a catchy title and a comma-separated list of 3-5 relevant SEO keywords.
    The ideas should be suitable for a blog post, social media, or a short video script.
    Focus on topics with broad appeal, such as budget travel, family trips, unique stays, hidden gems, or local experiences.

    Format your response as follows:
    IDEA: [Your catchy title here]
    KEYWORDS: [keyword1, keyword2, keyword3]
    --- (use this separator between ideas)
    """

    logging.info("Sending trends to OpenAI for analysis...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Cheaper and faster model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )
        content = response.choices[0].message.content
        return parse_ai_response(content)
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        return []

def parse_ai_response(content):
    """Parses the structured response from the AI."""
    ideas = []
    blocks = content.strip().split('---')
    for block in blocks:
        if not block.strip():
            continue
        try:
            idea_line, keywords_line = block.strip().split('\n')
            idea = idea_line.replace('IDEA:', '').strip()
            keywords = keywords_line.replace('KEYWORDS:', '').strip()
            if idea and keywords:
                ideas.append({'idea': idea, 'keywords': keywords})
        except ValueError:
            logging.warning(f"Could not parse block: \n{block}")
    return ideas

def save_ideas_to_db(ideas, city, db_path):
    """Saves the generated ideas to the SQLite database."""
    if not ideas:
        logging.info("No new ideas to save.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    for item in ideas:
        cursor.execute("INSERT INTO trends (date, city, idea, keywords) VALUES (?, ?, ?, ?)",
                       (today, city, item['idea'], item['keywords']))
        logging.info(f"Saved idea to DB: {item['idea']}")

    conn.commit()
    conn.close()

def run(config, city_override=None):
    """Main function to run the research agent."""
    db_path = config['system']['db_path']
    target_cities = config['system']['target_cities']
    openai_api_key = config['openai']['api_key']

    # Initialize OpenAI client
    try:
        client = openai.OpenAI(api_key=openai_api_key)
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        return

    # 1. Setup Database
    setup_database(db_path)

    # 2. Select City
    if city_override:
        city = city_override
        logging.info(f"Using overridden city: {city}")
    else:
        city = get_target_city(target_cities)

    # 3. Fetch Trends
    trends = fetch_google_trends(city)

    # 4. Analyze with AI
    if trends:
        ideas = analyze_trends_with_ai(trends, city, client)
    else:
        ideas = []

    # 5. Save to DB
    save_ideas_to_db(ideas, city, db_path)
