"""
Database Management System
Handles SQLite database operations for storing trends, content, and analytics.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager

from .logger import get_logger


class DatabaseManager:
    """Manages SQLite database operations for the Airbnb affiliate system."""

    def __init__(self, db_path: str = "data/airbnb_bot.db"):
        """Initialize database manager."""
        self.db_path = Path(db_path)
        self.logger = get_logger(__name__)

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_database()

    def _init_database(self):
        """Initialize database schema with all required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Trends table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    city TEXT NOT NULL,
                    trend_data TEXT NOT NULL,  -- JSON string
                    content_ideas TEXT NOT NULL,  -- JSON string
                    keywords TEXT NOT NULL,  -- JSON string
                    status TEXT DEFAULT 'pending',  -- pending, processed, archived
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Content table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trend_id INTEGER,
                    content_type TEXT NOT NULL,  -- blog_post, twitter_thread, reddit_post, tiktok_script
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    seo_keywords TEXT,  -- JSON string
                    affiliate_links TEXT,  -- JSON string
                    images TEXT,  -- JSON string of image paths/URLs
                    status TEXT DEFAULT 'draft',  -- draft, ready, posted, archived
                    quality_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trend_id) REFERENCES trends (id)
                )
            ''')

            # Posts table (tracking posted content)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,  -- medium, twitter, reddit
                    platform_post_id TEXT,  -- ID from the platform
                    post_url TEXT,
                    scheduled_at TIMESTAMP,
                    posted_at TIMESTAMP,
                    status TEXT DEFAULT 'scheduled',  -- scheduled, posted, failed, deleted
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (content_id) REFERENCES content (id)
                )
            ''')

            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,  -- views, clicks, conversions, revenue
                    metric_value REAL NOT NULL,
                    date DATE NOT NULL,
                    source TEXT,  -- bitly, medium, twitter, etc.
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts (id)
                )
            ''')

            # Performance summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_posts INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    total_clicks INTEGER DEFAULT 0,
                    total_conversions INTEGER DEFAULT 0,
                    estimated_revenue REAL DEFAULT 0.0,
                    click_rate REAL DEFAULT 0.0,
                    conversion_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trends_date ON trends (date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trends_city ON trends (city)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_status ON content (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts (platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_status ON posts (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_date ON analytics (date)')

            conn.commit()
            self.logger.info("Database schema initialized successfully")

    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()

    def insert_trend(self, city: str, trend_data: Dict, content_ideas: List[str], keywords: List[str]) -> int:
        """Insert a new trend record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trends (date, city, trend_data, content_ideas, keywords)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().date(),
                city,
                json.dumps(trend_data),
                json.dumps(content_ideas),
                json.dumps(keywords)
            ))
            conn.commit()
            trend_id = cursor.lastrowid
            self.logger.info(f"Inserted trend record for {city} with ID {trend_id}")
            return trend_id

    def insert_content(self, trend_id: int, content_type: str, title: str, content: str,
                      seo_keywords: List[str] = None, affiliate_links: List[str] = None,
                      images: List[str] = None, quality_score: float = 0.0) -> int:
        """Insert a new content record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO content (trend_id, content_type, title, content, seo_keywords,
                                   affiliate_links, images, quality_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready')
            ''', (
                trend_id,
                content_type,
                title,
                content,
                json.dumps(seo_keywords or []),
                json.dumps(affiliate_links or []),
                json.dumps(images or []),
                quality_score
            ))
            conn.commit()
            content_id = cursor.lastrowid
            self.logger.info(f"Inserted content record with ID {content_id}")
            return content_id

    def insert_post(self, content_id: int, platform: str, scheduled_at: datetime = None) -> int:
        """Insert a new post record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO posts (content_id, platform, scheduled_at)
                VALUES (?, ?, ?)
            ''', (content_id, platform, scheduled_at))
            conn.commit()
            post_id = cursor.lastrowid
            self.logger.info(f"Inserted post record with ID {post_id}")
            return post_id

    def update_post_status(self, post_id: int, status: str, platform_post_id: str = None,
                          post_url: str = None, error_message: str = None):
        """Update post status and metadata."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
            values = [status]

            if platform_post_id:
                update_fields.append('platform_post_id = ?')
                values.append(platform_post_id)

            if post_url:
                update_fields.append('post_url = ?')
                values.append(post_url)

            if error_message:
                update_fields.append('error_message = ?')
                values.append(error_message)

            if status == 'posted':
                update_fields.append('posted_at = CURRENT_TIMESTAMP')

            values.append(post_id)

            cursor.execute(f'''
                UPDATE posts SET {', '.join(update_fields)}
                WHERE id = ?
            ''', values)
            conn.commit()
            self.logger.info(f"Updated post {post_id} status to {status}")

    def get_pending_trends(self, limit: int = 10) -> List[Dict]:
        """Get pending trends for content generation."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM trends
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            ''', (limit,))

            trends = []
            for row in cursor.fetchall():
                trend = dict(row)
                trend['trend_data'] = json.loads(trend['trend_data'])
                trend['content_ideas'] = json.loads(trend['content_ideas'])
                trend['keywords'] = json.loads(trend['keywords'])
                trends.append(trend)

            return trends

    def get_ready_content(self, limit: int = 10) -> List[Dict]:
        """Get content ready for posting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM content
                WHERE status = 'ready'
                ORDER BY quality_score DESC, created_at ASC
                LIMIT ?
            ''', (limit,))

            content_items = []
            for row in cursor.fetchall():
                content = dict(row)
                content['seo_keywords'] = json.loads(content['seo_keywords'] or '[]')
                content['affiliate_links'] = json.loads(content['affiliate_links'] or '[]')
                content['images'] = json.loads(content['images'] or '[]')
                content_items.append(content)

            return content_items

    def get_scheduled_posts(self, platform: str = None) -> List[Dict]:
        """Get scheduled posts for a platform."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT p.*, c.title, c.content_type
                FROM posts p
                JOIN content c ON p.content_id = c.id
                WHERE p.status = 'scheduled'
            '''
            params = []

            if platform:
                query += ' AND p.platform = ?'
                params.append(platform)

            query += ' ORDER BY p.scheduled_at ASC'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def insert_analytics(self, post_id: int, metric_type: str, metric_value: float,
                        date: datetime = None, source: str = None):
        """Insert analytics data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analytics (post_id, metric_type, metric_value, date, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                post_id,
                metric_type,
                metric_value,
                (date or datetime.now()).date(),
                source
            ))
            conn.commit()

    def get_performance_summary(self, days: int = 30) -> Dict:
        """Get performance summary for the last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            start_date = (datetime.now() - timedelta(days=days)).date()

            cursor.execute('''
                SELECT
                    COUNT(DISTINCT p.id) as total_posts,
                    COALESCE(SUM(CASE WHEN a.metric_type = 'views' THEN a.metric_value END), 0) as total_views,
                    COALESCE(SUM(CASE WHEN a.metric_type = 'clicks' THEN a.metric_value END), 0) as total_clicks,
                    COALESCE(SUM(CASE WHEN a.metric_type = 'conversions' THEN a.metric_value END), 0) as total_conversions,
                    COALESCE(SUM(CASE WHEN a.metric_type = 'revenue' THEN a.metric_value END), 0) as total_revenue
                FROM posts p
                LEFT JOIN analytics a ON p.id = a.post_id
                WHERE p.posted_at >= ?
            ''', (start_date,))

            row = cursor.fetchone()
            summary = dict(row) if row else {}

            # Calculate rates
            if summary.get('total_views', 0) > 0:
                summary['click_rate'] = summary.get('total_clicks', 0) / summary['total_views']
            else:
                summary['click_rate'] = 0.0

            if summary.get('total_clicks', 0) > 0:
                summary['conversion_rate'] = summary.get('total_conversions', 0) / summary['total_clicks']
            else:
                summary['conversion_rate'] = 0.0

            return summary

    def update_trend_status(self, trend_id: int, status: str):
        """Update trend status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE trends SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, trend_id))
            conn.commit()
            self.logger.info(f"Updated trend {trend_id} status to {status}")