"""
Trend Research Agent
Fetches travel trends via Google Trends API and generates content ideas using AI.
"""

import random
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
        
        # Initialize Google Trends
        self.pytrends = TrendReq(hl='en-US', tz=360)
        
        self.logger.info(f"TrendResearchAgent initialized {'(DRY RUN)' if dry_run else ''}")
    
    def _init_ai_client(self):
        """Initialize AI client based on configuration."""
        primary_model = self.config.get('ai', {}).get('primary_model', 'openai')
        
        if primary_model == 'openai':
            api_key = self.config.get('api_keys', {}).get('openai_api_key')
            if api_key:
                openai.api_key = api_key
                return 'openai'
            else:
                self.logger.warning("OpenAI API key not configured")
        
        elif primary_model == 'anthropic':
            api_key = self.config.get('api_keys', {}).get('anthropic_api_key')
            if api_key:
                return Anthropic(api_key=api_key)
            else:
                self.logger.warning("Anthropic API key not configured")
        
        return None
    
    def research_trends(self) -> List[Dict[str, Any]]:
        """Research travel trends and generate content ideas."""
        self.logger.info("Starting trend research...")
        
        target_cities = self.config.get('content', {}).get('target_cities', ['Nashville'])
        trends_found = []
        
        # Rotate through cities to avoid overwhelming any single location
        cities_to_research = random.sample(target_cities, min(3, len(target_cities)))
        
        for city in cities_to_research:
            try:
                trend_data = self._fetch_city_trends(city)
                if trend_data:
                    content_ideas = self._generate_content_ideas(city, trend_data)
                    keywords = self._extract_keywords(city, trend_data)
                    
                    if not self.dry_run:
                        trend_id = self.db.insert_trend(
                            city=city,
                            trend_data=trend_data,
                            content_ideas=content_ideas,
                            keywords=keywords
                        )
                        
                        trends_found.append({
                            'id': trend_id,
                            'city': city,
                            'trend_data': trend_data,
                            'content_ideas': content_ideas,
                            'keywords': keywords
                        })
                    else:
                        self.logger.info(f"DRY RUN: Would save trend for {city}")
                        trends_found.append({
                            'city': city,
                            'content_ideas': content_ideas,
                            'keywords': keywords
                        })
                
            except Exception as e:
                self.logger.error(f"Failed to research trends for {city}: {e}")
                continue
        
        self.logger.info(f"Completed trend research. Found {len(trends_found)} trends.")
        return trends_found
    
    def _fetch_city_trends(self, city: str) -> Optional[Dict[str, Any]]:
        """Fetch Google Trends data for a specific city."""
        try:
            # Build search queries for the city
            queries = [
                f"Airbnb {city}",
                f"{city} travel 2025",
                f"things to do {city}",
                f"{city} vacation rental",
                f"visit {city}"
            ]
            
            # Get trends data
            self.pytrends.build_payload(queries, timeframe='today 3-m', geo='US')
            
            # Get interest over time
            interest_over_time = self.pytrends.interest_over_time()
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            # Get regional interest
            regional_interest = self.pytrends.interest_by_region()
            
            trend_data = {
                'city': city,
                'queries': queries,
                'interest_over_time': interest_over_time.to_dict() if not interest_over_time.empty else {},
                'related_queries': self._process_related_queries(related_queries),
                'regional_interest': regional_interest.to_dict() if not regional_interest.empty else {},
                'research_date': datetime.now().isoformat()
            }
            
            self.logger.info(f"Fetched trends data for {city}")
            return trend_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch trends for {city}: {e}")
            return None
    
    def _process_related_queries(self, related_queries: Dict) -> Dict:
        """Process and clean related queries data."""
        processed = {}
        for query, data in related_queries.items():
            if data is not None and 'top' in data:
                # Get top 10 related queries
                top_queries = data['top'].head(10) if not data['top'].empty else None
                if top_queries is not None:
                    processed[query] = top_queries.to_dict()
        return processed
    
    def _generate_content_ideas(self, city: str, trend_data: Dict) -> List[str]:
        """Generate content ideas using AI based on trend data."""
        if not self.ai_client:
            self.logger.warning("No AI client available, using fallback content ideas")
            return self._get_fallback_content_ideas(city)
        
        try:
            prompt = self._build_content_ideas_prompt(city, trend_data)
            
            if isinstance(self.ai_client, str) and self.ai_client == 'openai':
                response = openai.ChatCompletion.create(
                    model=self.config.get('ai', {}).get('openai_model', 'gpt-4o-mini'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config.get('ai', {}).get('max_tokens', 1000),
                    temperature=self.config.get('ai', {}).get('temperature', 0.7)
                )
                content = response.choices[0].message.content
            else:
                # Anthropic
                response = self.ai_client.messages.create(
                    model=self.config.get('ai', {}).get('anthropic_model', 'claude-3-haiku-20240307'),
                    max_tokens=self.config.get('ai', {}).get('max_tokens', 1000),
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            
            # Parse content ideas from AI response
            ideas = self._parse_content_ideas(content)
            self.logger.info(f"Generated {len(ideas)} content ideas for {city}")
            return ideas
            
        except Exception as e:
            self.logger.error(f"Failed to generate content ideas for {city}: {e}")
            return self._get_fallback_content_ideas(city)
    
    def _build_content_ideas_prompt(self, city: str, trend_data: Dict) -> str:
        """Build prompt for AI content idea generation."""
        seo_keywords = self.config.get('content', {}).get('seo_keywords', [])
        
        prompt = f"""
You are a travel content strategist specializing in Airbnb affiliate marketing. 
Generate 5 engaging content ideas for {city} based on the following trend data and requirements:

CITY: {city}
TRENDING SEARCHES: {trend_data.get('queries', [])}
SEO KEYWORDS TO INCLUDE: {seo_keywords}

REQUIREMENTS:
- Focus on budget-friendly and unique Airbnb stays
- Target travelers looking for hidden gems and local experiences
- Include seasonal relevance for 2025
- Each idea should be specific and actionable
- Ideas should work for blog posts, social media, and video content

FORMAT YOUR RESPONSE AS:
1. [Content Idea Title]
2. [Content Idea Title]
3. [Content Idea Title]
4. [Content Idea Title]
5. [Content Idea Title]

EXAMPLES OF GOOD IDEAS:
- "7 Hidden Gem Airbnbs in {city} Under $100/Night"
- "Local's Guide: Best Neighborhood Stays in {city} 2025"
- "Unique {city} Airbnbs Perfect for Instagram"

Generate content ideas now:
"""
        return prompt
    
    def _parse_content_ideas(self, ai_response: str) -> List[str]:
        """Parse content ideas from AI response."""
        ideas = []
        lines = ai_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering and clean up
                idea = line.split('.', 1)[-1].strip()
                idea = idea.lstrip('- •').strip()
                if idea and len(idea) > 10:  # Ensure it's a substantial idea
                    ideas.append(idea)
        
        # Fallback if parsing failed
        if not ideas:
            ideas = ai_response.split('\n')[:5]
            ideas = [idea.strip() for idea in ideas if idea.strip()]
        
        return ideas[:5]  # Limit to 5 ideas
    
    def _extract_keywords(self, city: str, trend_data: Dict) -> List[str]:
        """Extract relevant keywords from trend data."""
        keywords = [city.lower()]
        
        # Add base SEO keywords
        base_keywords = self.config.get('content', {}).get('seo_keywords', [])
        keywords.extend(base_keywords)
        
        # Extract from related queries
        related_queries = trend_data.get('related_queries', {})
        for query_type, queries in related_queries.items():
            if isinstance(queries, dict) and 'query' in queries:
                for query in list(queries['query'].values())[:5]:  # Top 5
                    if isinstance(query, str):
                        keywords.append(query.lower())
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def _get_fallback_content_ideas(self, city: str) -> List[str]:
        """Get fallback content ideas when AI is not available."""
        templates = [
            f"Top 10 Budget Airbnb Hidden Gems in {city} 2025",
            f"Local's Guide to Unique {city} Airbnb Stays",
            f"Best {city} Neighborhoods for Airbnb Travelers",
            f"Instagram-Worthy Airbnb Properties in {city}",
            f"Family-Friendly Airbnb Options in {city} Under $150"
        ]
        return templates
