"""
Trend Research Agent
Fetches travel trends via Google Trends API and generates content ideas using AI.
"""

import random
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pytrends.request import TrendReq
import openai
from anthropic import Anthropic

from utils.logger import get_logger
from utils.database import DatabaseManager


class TrendResearchAgent:
    """Agent responsible for researching travel trends and generating content ideas."""

    def __init__(self, config: Dict[str, Any], db: DatabaseManager, dry_run: bool = False):
        """Initialize the trend research agent."""
        self.config = config
        self.db = db
        self.dry_run = dry_run
        self.logger = get_logger(__name__)

        # Initialize AI client
        self.ai_client = self._init_ai_client()

        # Initialize Google Trends with retry mechanism
        self.pytrends = None
        self._init_pytrends()

        # Configuration
        self.max_retries = self.config.get('system', {}).get('max_retries', 3)
        self.retry_delay = self.config.get('system', {}).get('retry_delay', 60)

        self.logger.info(f"🔍 TrendResearchAgent initialized {'(DRY RUN)' if dry_run else ''}")

    def _init_pytrends(self):
        """Initialize Google Trends with error handling."""
        try:
            self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2, backoff_factor=0.1)
            self.logger.info("✅ Google Trends API initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Google Trends: {e}")
            self.pytrends = None

    def _init_ai_client(self):
        """Initialize AI client based on configuration."""
        ai_config = self.config.get('ai', {})

        # Try OpenAI first
        openai_config = ai_config.get('openai', {})
        if openai_config.get('api_key'):
            try:
                openai.api_key = openai_config['api_key']
                # Test the connection with a simple request
                openai.Model.list()
                self.logger.info("✅ OpenAI API client initialized")
                return 'openai'
            except Exception as e:
                self.logger.warning(f"⚠️ OpenAI API initialization failed: {e}")

        # Try Anthropic if OpenAI fails
        anthropic_config = ai_config.get('anthropic', {})
        if anthropic_config.get('api_key') and anthropic_config.get('enabled', False):
            try:
                client = Anthropic(api_key=anthropic_config['api_key'])
                self.logger.info("✅ Anthropic API client initialized")
                return client
            except Exception as e:
                self.logger.warning(f"⚠️ Anthropic API initialization failed: {e}")

        self.logger.warning("⚠️ No AI client available - will use fallback content generation")
        return None

    def research_trends(self) -> List[Dict[str, Any]]:
        """Research travel trends and generate content ideas."""
        self.logger.info("🔍 Starting trend research...")

        # Get target cities from config
        target_cities = self.config.get('content', {}).get('cities', [
            'Nashville', 'Charleston', 'Austin', 'Portland', 'Denver'
        ])

        trends_found = []

        # Process cities (limit to avoid rate limiting)
        cities_to_research = random.sample(target_cities, min(3, len(target_cities)))
        self.logger.info(f"🏙️ Researching trends for cities: {', '.join(cities_to_research)}")

        for city in cities_to_research:
            try:
                self.logger.info(f"🔎 Researching trends for {city}...")
                trend_data = self._fetch_city_trends(city)

                if trend_data:
                    content_ideas = self._generate_content_ideas(city, trend_data)
                    keywords = self._extract_keywords(city, trend_data)
                    scores = self._calculate_trend_scores(trend_data)

                    result = {
                        'city': city,
                        'trend_data': trend_data,
                        'content_ideas': content_ideas,
                        'keywords': keywords,
                        'scores': scores,
                        'research_date': datetime.now().isoformat()
                    }

                    if not self.dry_run:
                        trend_id = self.db.insert_trend(
                            city=city,
                            trend_data=trend_data,
                            content_ideas=content_ideas,
                            keywords=keywords
                        )
                        result['id'] = trend_id
                        self.logger.info(f"💾 Saved trend data for {city} (ID: {trend_id})")
                    else:
                        self.logger.info(f"🧪 DRY RUN: Would save trend for {city}")

                    trends_found.append(result)
                    self.logger.info(f"✅ Completed trend research for {city}: {len(content_ideas)} ideas generated")
                else:
                    self.logger.warning(f"⚠️ No trend data found for {city}")

                # Rate limiting delay
                time.sleep(2)

            except Exception as e:
                self.logger.error(f"❌ Failed to research trends for {city}: {e}")
                continue

        self.logger.info(f"🎯 Trend research completed! Found {len(trends_found)} city trends with {sum(len(t.get('content_ideas', [])) for t in trends_found)} total content ideas")
        return trends_found

    def _fetch_city_trends(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch Google Trends data for a specific city with retry logic."""
        if not self.pytrends:
            self.logger.error("❌ Google Trends client not available")
            return None

        for attempt in range(self.max_retries):
            try:
                # Build comprehensive search queries for hotel/travel context
                queries = [
                    f"hotels {city}",
                    f"{city} vacation rentals",
                    f"things to do {city}",
                    f"travel to {city}",
                    f"{city} tourism 2025"
                ]

                self.logger.info(f"📊 Fetching trends for queries: {queries}")

                # Get trends data with timeframe
                self.pytrends.build_payload(
                    queries,
                    timeframe='today 3-m',  # Last 3 months
                    geo='US'
                )

                # Get interest over time
                interest_over_time = self.pytrends.interest_over_time()

                # Get related queries
                related_queries = self.pytrends.related_queries()

                # Get regional interest
                regional_interest = self.pytrends.interest_by_region()

                # Process the data
                trend_data = {
                    'city': city,
                    'queries': queries,
                    'interest_over_time': self._process_dataframe(interest_over_time),
                    'related_queries': self._process_related_queries(related_queries),
                    'regional_interest': self._process_dataframe(regional_interest),
                    'research_date': datetime.now().isoformat(),
                    'timeframe': 'today 3-m'
                }

                self.logger.info(f"✅ Successfully fetched trends data for {city}")
                return trend_data

            except Exception as e:
                self.logger.warning(f"⚠️ Attempt {attempt + 1} failed for {city}: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"⏳ Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"❌ All attempts failed for {city}")
                    return None

        return None

    def _process_dataframe(self, df) -> Dict:
        """Process pandas DataFrame to JSON-serializable format."""
        if df is None or df.empty:
            return {}

        try:
            # Convert to dict and handle datetime index
            result = df.to_dict()

            # If index contains dates, convert to strings
            if hasattr(df.index, 'strftime'):
                date_index = [date.strftime('%Y-%m-%d') for date in df.index]
                # Restructure with date strings as keys
                restructured = {}
                for col in df.columns:
                    restructured[col] = dict(zip(date_index, df[col].values.tolist()))
                return restructured

            return result
        except Exception as e:
            self.logger.warning(f"⚠️ Error processing dataframe: {e}")
            return {}

    def _process_related_queries(self, related_queries: Dict) -> Dict:
        """Process and clean related queries data."""
        processed = {}

        for query, data in related_queries.items():
            if data is not None:
                processed[query] = {}

                # Process 'top' queries
                if 'top' in data and data['top'] is not None and not data['top'].empty:
                    top_queries = data['top'].head(10)
                    processed[query]['top'] = top_queries.to_dict('records')

                # Process 'rising' queries
                if 'rising' in data and data['rising'] is not None and not data['rising'].empty:
                    rising_queries = data['rising'].head(10)
                    processed[query]['rising'] = rising_queries.to_dict('records')

        return processed

    def _generate_content_ideas(self, city: str, trend_data: Dict) -> List[str]:
        """Generate content ideas using AI based on trend data."""
        if not self.ai_client:
            self.logger.warning("⚠️ No AI client available, using fallback content ideas")
            return self._get_fallback_content_ideas(city)

        try:
            prompt = self._build_content_ideas_prompt(city, trend_data)

            if isinstance(self.ai_client, str) and self.ai_client == 'openai':
                # Use the new OpenAI API format
                client = openai.OpenAI(api_key=openai.api_key)
                response = client.chat.completions.create(
                    model=self.config.get('ai', {}).get('openai', {}).get('model', 'gpt-4o-mini'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config.get('ai', {}).get('openai', {}).get('max_tokens', 1500),
                    temperature=self.config.get('ai', {}).get('openai', {}).get('temperature', 0.7)
                )
                content = response.choices[0].message.content
            else:
                # Anthropic
                response = self.ai_client.messages.create(
                    model=self.config.get('ai', {}).get('anthropic', {}).get('model', 'claude-3-haiku-20240307'),
                    max_tokens=self.config.get('ai', {}).get('anthropic', {}).get('max_tokens', 1500),
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text

            # Parse content ideas from AI response
            ideas = self._parse_content_ideas(content)
            self.logger.info(f"🤖 Generated {len(ideas)} AI-powered content ideas for {city}")
            return ideas

        except Exception as e:
            self.logger.error(f"❌ Failed to generate AI content ideas for {city}: {e}")
            return self._get_fallback_content_ideas(city)

    def _build_content_ideas_prompt(self, city: str, trend_data: Dict) -> str:
        """Build comprehensive prompt for AI content idea generation."""

        # Extract trending keywords from related queries
        trending_terms = []
        related_queries = trend_data.get('related_queries', {})
        for query_data in related_queries.values():
            if isinstance(query_data, dict):
                if 'top' in query_data:
                    for item in query_data['top'][:3]:  # Top 3 from each
                        if isinstance(item, dict) and 'query' in item:
                            trending_terms.append(item['query'])

        # Get current season for seasonal relevance
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:
            season = "winter"
        elif current_month in [3, 4, 5]:
            season = "spring"
        elif current_month in [6, 7, 8]:
            season = "summer"
        else:
            season = "fall"

        prompt = f"""
You are an expert travel content strategist specializing in Booking.com affiliate marketing for accommodation bookings.

Generate 8 highly engaging and specific content ideas for {city} that will drive hotel bookings through affiliate links.

CONTEXT:
- Target City: {city}
- Current Season: {season} 2025
- Focus: Hotels, vacation rentals, and accommodation bookings
- Trending search terms: {', '.join(trending_terms[:10]) if trending_terms else 'N/A'}

CONTENT REQUIREMENTS:
1. Focus specifically on accommodations and stays (hotels, boutique properties, unique stays)
2. Target budget-conscious and experience-seeking travelers
3. Include seasonal relevance for {season} 2025
4. Each idea should be actionable for blog posts, social media, and video content
5. Emphasize unique, Instagram-worthy, and local experiences
6. Include price points and value propositions

CONTENT TYPES TO INCLUDE:
- Budget hotel roundups (under $100, under $150)
- Boutique and unique property features
- Neighborhood accommodation guides
- Seasonal stay recommendations
- Experience-based hotel selections (romantic, family, business, solo)

FORMAT YOUR RESPONSE EXACTLY AS:
1. [Specific Content Idea Title]
2. [Specific Content Idea Title]
3. [Specific Content Idea Title]
4. [Specific Content Idea Title]
5. [Specific Content Idea Title]
6. [Specific Content Idea Title]
7. [Specific Content Idea Title]
8. [Specific Content Idea Title]

EXAMPLES OF EXCELLENT IDEAS:
- "7 Boutique Hotels in {city} Under $120/Night Perfect for {season} 2025"
- "Local's Guide: Best Neighborhood Hotels in {city} for First-Time Visitors"
- "Instagram-Worthy {city} Hotels That Won't Break the Bank"
- "{season} in {city}: 5 Cozy Hotels with Fireplaces Under $100"

Generate content ideas that will convert browsers into bookers:
"""
        return prompt

    def _parse_content_ideas(self, ai_response: str) -> List[str]:
        """Parse content ideas from AI response with improved extraction."""
        ideas = []
        lines = ai_response.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and clean up
                idea = line.split('.', 1)[-1].strip() if '.' in line else line
                idea = idea.lstrip('- •').strip()
                idea = idea.strip('"\'')  # Remove quotes

                if idea and len(idea) > 15:  # Ensure it's a substantial idea
                    ideas.append(idea)

        # Fallback parsing if numbered format failed
        if not ideas:
            for line in lines:
                line = line.strip()
                if line and len(line) > 15 and not line.startswith(('Generate', 'You are', 'CONTENT', 'FORMAT')):
                    ideas.append(line.strip('"\''))

        # Ensure we have quality ideas
        filtered_ideas = [idea for idea in ideas if len(idea) > 20 and 'hotel' in idea.lower() or 'stay' in idea.lower() or 'accommodation' in idea.lower()]

        return filtered_ideas[:8]  # Return up to 8 ideas

    def _extract_keywords(self, city: str, trend_data: Dict) -> List[str]:
        """Extract relevant keywords from trend data with better filtering."""
        keywords = [city.lower(), f"{city.lower()} hotels", f"{city.lower()} accommodation"]

        # Add base SEO keywords from config
        seo_config = self.config.get('content', {}).get('seo', {})
        base_keywords = [
            "budget hotels", "boutique hotels", "vacation rentals",
            "best hotels", "unique stays", "accommodation", "booking"
        ]
        keywords.extend(base_keywords)

        # Extract from related queries with filtering
        related_queries = trend_data.get('related_queries', {})
        for query_type, queries in related_queries.items():
            if isinstance(queries, dict):
                # Process top queries
                if 'top' in queries:
                    for item in queries['top'][:5]:  # Top 5
                        if isinstance(item, dict) and 'query' in item:
                            query = item['query'].lower()
                            # Filter for travel/accommodation related terms
                            if any(term in query for term in ['hotel', 'stay', 'accommodation', 'travel', 'visit', 'vacation']):
                                keywords.append(query)

                # Process rising queries
                if 'rising' in queries:
                    for item in queries['rising'][:3]:  # Top 3 rising
                        if isinstance(item, dict) and 'query' in item:
                            query = item['query'].lower()
                            if any(term in query for term in ['hotel', 'stay', 'accommodation', 'travel', 'visit']):
                                keywords.append(query)

        # Remove duplicates and filter out very short keywords
        unique_keywords = list(set([kw for kw in keywords if len(kw) > 2]))
        return unique_keywords[:20]  # Limit to 20 most relevant keywords

    def _calculate_trend_scores(self, trend_data: Dict) -> Dict[str, float]:
        """Calculate trend scores for ranking and prioritization."""
        scores = {
            'overall_interest': 0.0,
            'trend_momentum': 0.0,
            'search_volume': 0.0,
            'seasonal_relevance': 0.0,
            'competition_level': 0.5  # Default medium competition
        }

        try:
            # Calculate overall interest from interest_over_time
            interest_data = trend_data.get('interest_over_time', {})
            if interest_data:
                all_values = []
                for query_data in interest_data.values():
                    if isinstance(query_data, dict):
                        all_values.extend([v for v in query_data.values() if isinstance(v, (int, float))])

                if all_values:
                    scores['overall_interest'] = sum(all_values) / len(all_values) / 100.0

                    # Calculate trend momentum (recent vs older data)
                    recent_values = all_values[-7:] if len(all_values) >= 7 else all_values
                    older_values = all_values[:-7] if len(all_values) >= 14 else all_values[:len(all_values)//2]

                    if recent_values and older_values:
                        recent_avg = sum(recent_values) / len(recent_values)
                        older_avg = sum(older_values) / len(older_values)
                        scores['trend_momentum'] = min(1.0, max(0.0, (recent_avg - older_avg) / 100.0 + 0.5))

            # Calculate search volume score based on related queries
            related_queries = trend_data.get('related_queries', {})
            query_count = 0
            for query_data in related_queries.values():
                if isinstance(query_data, dict):
                    query_count += len(query_data.get('top', []))
                    query_count += len(query_data.get('rising', []))

            scores['search_volume'] = min(1.0, query_count / 50.0)  # Normalize to 0-1

            # Seasonal relevance (higher for current season)
            current_month = datetime.now().month
            scores['seasonal_relevance'] = 0.8  # Default high for travel content

        except Exception as e:
            self.logger.warning(f"⚠️ Error calculating trend scores: {e}")

        return scores

    def _get_fallback_content_ideas(self, city: str) -> List[str]:
        """Get fallback content ideas when AI is not available."""
        current_year = datetime.now().year

        templates = [
            f"Top 10 Budget Hotels in {city} Under $100/Night ({current_year})",
            f"Local's Guide: Best Boutique Hotels in {city} for Unique Stays",
            f"Family-Friendly Hotels in {city}: Where to Stay with Kids",
            f"Romantic Getaway: Most Charming Hotels in {city} for Couples",
            f"Business Travel: Best Value Hotels in {city} for Work Trips",
            f"Solo Travel: Safest and Most Social Hotels in {city}",
            f"Instagram-Worthy Hotels in {city} That Won't Break Your Budget",
            f"Weekend Escape: Perfect {city} Hotels for 2-Day Getaways"
        ]

        self.logger.info(f"🔄 Using fallback content ideas for {city}")
        return templates