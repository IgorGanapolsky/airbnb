import json
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pytrends.request import TrendReq
import openai
from utils.config_loader import config
from utils.database import Database

logger = logging.getLogger(__name__)

class TrendResearchAgent:
    def __init__(self):
        self.config = config.config
        self.db = Database(self.config['system']['database_path'])
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.cities = self.config['content']['cities']

        openai_key = self.config['ai']['openai']['api_key']
        if openai_key and openai_key != "sk-...":
            openai.api_key = openai_key
        else:
            logger.error("OpenAI API key not configured")

    def research_trends(self, num_cities: int = 3) -> List[Dict[str, Any]]:
        selected_cities = random.sample(self.cities, min(num_cities, len(self.cities)))
        all_trends = []

        for city in selected_cities:
            logger.info(f"Researching trends for {city}")
            city_trends = self._research_city_trends(city)
            all_trends.extend(city_trends)

        return all_trends

    def _research_city_trends(self, city: str) -> List[Dict[str, Any]]:
        trends = []

        try:
            search_terms = [
                f"Airbnb {city}",
                f"{city} travel 2025",
                f"best neighborhoods {city}",
                f"budget stays {city}",
                f"hidden gems {city}"
            ]

            trend_data = self._get_google_trends(search_terms)

            content_ideas = self._generate_content_ideas(city, trend_data)

            for idea in content_ideas:
                trend_entry = {
                    'city': city,
                    'idea': idea['title'],
                    'keywords': idea['keywords'],
                    'score': idea.get('score', random.uniform(0.5, 1.0))
                }

                trend_id = self.db.add_trend(
                    city=trend_entry['city'],
                    idea=trend_entry['idea'],
                    keywords=trend_entry['keywords'],
                    score=trend_entry['score']
                )

                trend_entry['id'] = trend_id
                trends.append(trend_entry)

        except Exception as e:
            logger.error(f"Error researching trends for {city}: {e}")

        return trends

    def _get_google_trends(self, keywords: List[str]) -> Dict[str, Any]:
        try:
            self.pytrends.build_payload(keywords, timeframe='today 3-m')

            interest_over_time = self.pytrends.interest_over_time()
            related_queries = self.pytrends.related_queries()

            trend_data = {
                'interest_scores': {},
                'related_queries': {}
            }

            if not interest_over_time.empty:
                for keyword in keywords:
                    if keyword in interest_over_time.columns:
                        trend_data['interest_scores'][keyword] = float(
                            interest_over_time[keyword].mean()
                        )

            for keyword in keywords:
                if keyword in related_queries:
                    rising = related_queries[keyword]['rising']
                    if rising is not None and not rising.empty:
                        trend_data['related_queries'][keyword] = rising['query'].tolist()[:5]

            return trend_data

        except Exception as e:
            logger.warning(f"Google Trends API error: {e}")
            return {'interest_scores': {}, 'related_queries': {}}

    def _generate_content_ideas(self, city: str, trend_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        prompt = f"""
        You are an expert travel content strategist specializing in Airbnb marketing.
        Generate 5 unique content ideas for {city} that will attract travelers and drive Airbnb bookings.

        Current trend data:
        - Popular searches: {json.dumps(trend_data.get('interest_scores', {}), indent=2)}
        - Related queries: {json.dumps(trend_data.get('related_queries', {}), indent=2)}

        Requirements:
        1. Focus on evergreen content that will remain relevant
        2. Target different traveler segments (budget, luxury, families, solo)
        3. Include specific neighborhoods or attractions
        4. Optimize for SEO with low-competition keywords
        5. Make titles compelling and clickable

        Format your response as JSON:
        [
            {{
                "title": "Engaging title with {city} mention",
                "keywords": ["keyword1", "keyword2", "keyword3"],
                "target_audience": "audience segment",
                "content_angle": "unique perspective or hook",
                "score": 0.0-1.0 based on potential
            }}
        ]
        """

        try:
            if config.get('system.dry_run', False):
                return self._generate_mock_ideas(city)

            response = openai.chat.completions.create(
                model=self.config['ai']['openai']['model'],
                messages=[
                    {"role": "system", "content": "You are a travel content expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config['ai']['openai']['temperature'],
                max_tokens=1000
            )

            content = response.choices[0].message.content
            ideas = json.loads(content)

            return ideas[:5]

        except Exception as e:
            logger.error(f"Error generating content ideas: {e}")
            return self._generate_mock_ideas(city)

    def _generate_mock_ideas(self, city: str) -> List[Dict[str, Any]]:
        templates = [
            {
                "title": f"10 Hidden Gem Airbnbs in {city} Under $100/Night",
                "keywords": [f"cheap airbnb {city}", f"budget stays {city}", f"{city} hidden gems"],
                "target_audience": "budget travelers",
                "content_angle": "insider local recommendations",
                "score": 0.85
            },
            {
                "title": f"The Ultimate {city} Neighborhood Guide for First-Time Visitors",
                "keywords": [f"best neighborhoods {city}", f"where to stay {city}", f"{city} travel guide"],
                "target_audience": "first-time visitors",
                "content_angle": "comprehensive area breakdown",
                "score": 0.92
            },
            {
                "title": f"Family-Friendly Airbnbs in {city}: Top 15 Properties with Kids",
                "keywords": [f"family airbnb {city}", f"{city} with kids", f"family vacation {city}"],
                "target_audience": "families",
                "content_angle": "family amenities focus",
                "score": 0.78
            },
            {
                "title": f"{city}'s Most Instagram-Worthy Airbnbs for 2025",
                "keywords": [f"instagram airbnb {city}", f"unique stays {city}", f"boutique airbnb {city}"],
                "target_audience": "millennials/gen-z",
                "content_angle": "aesthetic and unique properties",
                "score": 0.88
            },
            {
                "title": f"Long-Term Stays in {city}: Best Monthly Airbnb Deals",
                "keywords": [f"monthly airbnb {city}", f"long term rental {city}", f"digital nomad {city}"],
                "target_audience": "remote workers",
                "content_angle": "work-friendly amenities",
                "score": 0.83
            }
        ]

        return random.sample(templates, min(5, len(templates)))

    def get_trending_topics(self) -> List[str]:
        try:
            trending = self.pytrends.trending_searches(pn='united_states')
            travel_related = [
                trend for trend in trending[0].tolist()[:20]
                if any(word in trend.lower() for word in ['travel', 'vacation', 'trip', 'hotel', 'airbnb'])
            ]
            return travel_related[:5]
        except Exception as e:
            logger.warning(f"Could not fetch trending topics: {e}")
            return []

    def analyze_competition(self, keyword: str) -> Dict[str, Any]:
        try:
            self.pytrends.build_payload([keyword], timeframe='today 12-m')
            interest = self.pytrends.interest_over_time()

            if not interest.empty:
                avg_interest = float(interest[keyword].mean())
                trend_direction = "rising" if interest[keyword].iloc[-1] > avg_interest else "declining"

                return {
                    'keyword': keyword,
                    'competition_score': min(avg_interest / 100, 1.0),
                    'trend_direction': trend_direction,
                    'recommended': avg_interest < 70
                }
        except Exception as e:
            logger.warning(f"Competition analysis failed for {keyword}: {e}")

        return {
            'keyword': keyword,
            'competition_score': 0.5,
            'trend_direction': 'stable',
            'recommended': True
        }