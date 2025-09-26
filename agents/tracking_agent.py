"""
Tracking Agent
Collects performance metrics and provides AI-powered optimization suggestions.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import openai
from anthropic import Anthropic

from utils.logger import get_logger
from utils.database import DatabaseManager


class TrackingAgent:
    """Agent responsible for tracking performance and providing optimization insights."""
    
    def __init__(self, config: Dict[str, Any], db: DatabaseManager, dry_run: bool = False):
        """Initialize the tracking agent."""
        self.config = config
        self.db = db
        self.dry_run = dry_run
        self.logger = get_logger(__name__)
        
        # Initialize AI client for optimization suggestions
        self.ai_client = self._init_ai_client()
        
        self.logger.info(f"TrackingAgent initialized {'(DRY RUN)' if dry_run else ''}")
    
    def _init_ai_client(self):
        """Initialize AI client for optimization suggestions."""
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
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance and generate comprehensive report."""
        self.logger.info("Starting performance analysis...")
        
        try:
            # Collect metrics from various sources
            bitly_metrics = self._collect_bitly_metrics()
            platform_metrics = self._collect_platform_metrics()
            database_metrics = self._collect_database_metrics()
            
            # Generate performance summary
            performance_summary = self._generate_performance_summary(
                bitly_metrics, platform_metrics, database_metrics
            )
            
            # Get AI optimization suggestions
            optimization_suggestions = self._get_optimization_suggestions(performance_summary)
            
            # Create comprehensive report
            report = {
                'timestamp': datetime.now().isoformat(),
                'period': '30_days',
                'metrics': {
                    'bitly': bitly_metrics,
                    'platforms': platform_metrics,
                    'database': database_metrics
                },
                'summary': performance_summary,
                'optimization_suggestions': optimization_suggestions,
                'targets': self._get_performance_targets(),
                'recommendations': self._generate_recommendations(performance_summary)
            }
            
            # Save report to database
            if not self.dry_run:
                self._save_performance_report(report)
            
            # Send email notification if significant changes
            if self._should_send_notification(performance_summary):
                self._send_performance_notification(report)
            
            self.logger.info("Performance analysis completed")
            return report
            
        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def _collect_bitly_metrics(self) -> Dict[str, Any]:
        """Collect click metrics from Bitly."""
        metrics = {'total_clicks': 0, 'links': [], 'error': None}
        
        try:
            access_token = self.config.get('api_keys', {}).get('bitly_access_token')
            if not access_token:
                metrics['error'] = 'Bitly access token not configured'
                return metrics
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Get user's links
            response = requests.get(
                'https://api-ssl.bitly.com/v4/user/bitlinks',
                headers=headers,
                params={'size': 50}  # Get last 50 links
            )
            
            if response.status_code == 200:
                links_data = response.json()
                
                for link in links_data.get('links', []):
                    link_id = link['id']
                    
                    # Get click metrics for each link
                    clicks_response = requests.get(
                        f'https://api-ssl.bitly.com/v4/bitlinks/{link_id}/clicks/summary',
                        headers=headers,
                        params={'unit': 'day', 'units': 30}
                    )
                    
                    if clicks_response.status_code == 200:
                        click_data = clicks_response.json()
                        clicks = click_data.get('total_clicks', 0)
                        
                        metrics['links'].append({
                            'id': link_id,
                            'long_url': link.get('long_url', ''),
                            'clicks': clicks,
                            'created_at': link.get('created_at', '')
                        })
                        
                        metrics['total_clicks'] += clicks
            
            else:
                metrics['error'] = f'Bitly API error: {response.status_code}'
            
        except Exception as e:
            metrics['error'] = str(e)
            self.logger.error(f"Failed to collect Bitly metrics: {e}")
        
        return metrics
    
    def _collect_platform_metrics(self) -> Dict[str, Any]:
        """Collect metrics from social media platforms."""
        metrics = {
            'medium': {'views': 0, 'reads': 0, 'claps': 0},
            'twitter': {'impressions': 0, 'engagements': 0, 'clicks': 0},
            'reddit': {'upvotes': 0, 'comments': 0, 'views': 0}
        }
        
        # Note: Most platforms require OAuth and have limited free API access
        # For now, we'll use placeholder data and manual input
        # In production, you'd implement specific API calls for each platform
        
        try:
            # Medium API (limited access)
            medium_token = self.config.get('api_keys', {}).get('medium_access_token')
            if medium_token:
                # Medium doesn't provide analytics via API for free accounts
                # Would need to scrape or use manual input
                pass
            
            # Twitter API v2 (limited free tier)
            # Would need to implement specific tweet metrics collection
            
            # Reddit API (read-only access available)
            # Could collect upvotes/comments for posts
            
        except Exception as e:
            self.logger.error(f"Failed to collect platform metrics: {e}")
        
        return metrics
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect metrics from local database."""
        try:
            # Get performance summary from database
            summary = self.db.get_performance_summary(days=30)
            
            # Get content statistics
            content_stats = self._get_content_statistics()
            
            # Get posting frequency
            posting_stats = self._get_posting_statistics()
            
            return {
                'performance_summary': summary,
                'content_stats': content_stats,
                'posting_stats': posting_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect database metrics: {e}")
            return {}
    
    def _get_content_statistics(self) -> Dict[str, Any]:
        """Get content creation and quality statistics."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Content by type
                cursor.execute('''
                    SELECT content_type, COUNT(*) as count, AVG(quality_score) as avg_quality
                    FROM content 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY content_type
                ''')
                content_by_type = [dict(row) for row in cursor.fetchall()]
                
                # Content by status
                cursor.execute('''
                    SELECT status, COUNT(*) as count
                    FROM content 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY status
                ''')
                content_by_status = [dict(row) for row in cursor.fetchall()]
                
                # Top performing content
                cursor.execute('''
                    SELECT c.title, c.content_type, c.quality_score, 
                           COUNT(p.id) as post_count
                    FROM content c
                    LEFT JOIN posts p ON c.id = p.content_id
                    WHERE c.created_at >= date('now', '-30 days')
                    GROUP BY c.id
                    ORDER BY c.quality_score DESC, post_count DESC
                    LIMIT 10
                ''')
                top_content = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'by_type': content_by_type,
                    'by_status': content_by_status,
                    'top_performing': top_content
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get content statistics: {e}")
            return {}
    
    def _get_posting_statistics(self) -> Dict[str, Any]:
        """Get posting frequency and success rate statistics."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Posts by platform
                cursor.execute('''
                    SELECT platform, COUNT(*) as count, 
                           SUM(CASE WHEN status = 'posted' THEN 1 ELSE 0 END) as successful
                    FROM posts 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY platform
                ''')
                posts_by_platform = [dict(row) for row in cursor.fetchall()]
                
                # Daily posting frequency
                cursor.execute('''
                    SELECT DATE(created_at) as date, COUNT(*) as posts
                    FROM posts 
                    WHERE created_at >= date('now', '-30 days')
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                ''')
                daily_posts = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'by_platform': posts_by_platform,
                    'daily_frequency': daily_posts
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get posting statistics: {e}")
            return {}
    
    def _generate_performance_summary(self, bitly_metrics: Dict, platform_metrics: Dict, 
                                    database_metrics: Dict) -> Dict[str, Any]:
        """Generate overall performance summary."""
        summary = {
            'total_clicks': bitly_metrics.get('total_clicks', 0),
            'total_posts': 0,
            'success_rate': 0.0,
            'avg_quality_score': 0.0,
            'estimated_revenue': 0.0,
            'performance_grade': 'C'
        }
        
        try:
            db_summary = database_metrics.get('performance_summary', {})
            
            summary.update({
                'total_posts': db_summary.get('total_posts', 0),
                'total_views': db_summary.get('total_views', 0),
                'click_rate': db_summary.get('click_rate', 0.0),
                'conversion_rate': db_summary.get('conversion_rate', 0.0)
            })
            
            # Calculate estimated revenue
            clicks = summary['total_clicks']
            conversion_rate = self.config.get('affiliate', {}).get('commission_rate', 0.03)
            avg_booking = self.config.get('affiliate', {}).get('avg_booking_value', 150.0)
            
            summary['estimated_revenue'] = clicks * conversion_rate * avg_booking
            
            # Calculate performance grade
            summary['performance_grade'] = self._calculate_performance_grade(summary)
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance summary: {e}")
        
        return summary
    
    def _calculate_performance_grade(self, summary: Dict) -> str:
        """Calculate overall performance grade A-F."""
        score = 0
        
        # Click rate score (0-25 points)
        click_rate = summary.get('click_rate', 0)
        target_click_rate = self.config.get('performance', {}).get('target_click_rate', 0.05)
        if click_rate >= target_click_rate:
            score += 25
        else:
            score += (click_rate / target_click_rate) * 25
        
        # Conversion rate score (0-25 points)
        conversion_rate = summary.get('conversion_rate', 0)
        target_conversion_rate = self.config.get('performance', {}).get('target_conversion_rate', 0.03)
        if conversion_rate >= target_conversion_rate:
            score += 25
        else:
            score += (conversion_rate / target_conversion_rate) * 25
        
        # Revenue score (0-25 points)
        revenue = summary.get('estimated_revenue', 0)
        target_revenue = self.config.get('performance', {}).get('target_monthly_revenue', 500)
        if revenue >= target_revenue:
            score += 25
        else:
            score += (revenue / target_revenue) * 25
        
        # Content quality score (0-25 points)
        # This would be based on average quality scores from database
        score += 15  # Placeholder
        
        # Convert to letter grade
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
