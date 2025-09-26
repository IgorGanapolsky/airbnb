import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.config_loader import config
from utils.database import Database

st.set_page_config(
    page_title="Airbnb Affiliate Bot Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

class AnalyticsDashboard:
    def __init__(self):
        self.config = config.config
        self.db = Database(self.config['system']['database_path'])

    def run(self):
        st.title("🏠 Airbnb Affiliate Bot Dashboard")

        # Sidebar for filters
        self._render_sidebar()

        # Main dashboard content
        self._render_overview()

        # Detailed analytics sections
        col1, col2 = st.columns(2)

        with col1:
            self._render_content_performance()
            self._render_trend_analysis()

        with col2:
            self._render_revenue_tracking()
            self._render_posting_activity()

        # Recent activity
        self._render_recent_activity()

    def _render_sidebar(self):
        st.sidebar.header("📊 Filters")

        # Date range selector
        default_start = datetime.now() - timedelta(days=30)
        default_end = datetime.now()

        self.date_range = st.sidebar.date_input(
            "Date Range",
            value=(default_start.date(), default_end.date()),
            max_value=datetime.now().date()
        )

        # Platform filter
        platforms = self._get_available_platforms()
        self.selected_platforms = st.sidebar.multiselect(
            "Platforms",
            platforms,
            default=platforms
        )

        # City filter
        cities = self._get_available_cities()
        self.selected_cities = st.sidebar.multiselect(
            "Cities",
            cities,
            default=cities
        )

        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()

    def _render_overview(self):
        st.header("📈 Overview")

        # Get current period stats
        stats = self._get_period_stats()

        # Create metrics columns
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Posts",
                stats['total_posts'],
                delta=stats.get('posts_change', 0)
            )

        with col2:
            st.metric(
                "Total Clicks",
                f"{stats['total_clicks']:,}",
                delta=stats.get('clicks_change', 0)
            )

        with col3:
            st.metric(
                "Click Rate",
                f"{stats['ctr']:.1f}%",
                delta=f"{stats.get('ctr_change', 0):.1f}%"
            )

        with col4:
            st.metric(
                "Conversions",
                stats['total_conversions'],
                delta=stats.get('conversions_change', 0)
            )

        with col5:
            st.metric(
                "Revenue",
                f"${stats['total_revenue']:.2f}",
                delta=f"${stats.get('revenue_change', 0):.2f}"
            )

    def _render_content_performance(self):
        st.subheader("📝 Content Performance")

        # Get top performing content
        top_content = self._get_top_content()

        if not top_content.empty:
            # Content performance chart
            fig = px.bar(
                top_content.head(10),
                x='clicks',
                y='title',
                orientation='h',
                title="Top 10 Posts by Clicks",
                labels={'clicks': 'Clicks', 'title': 'Content'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Performance table
            st.write("**Recent Content Performance**")
            display_df = top_content[['title', 'platform', 'clicks', 'conversions', 'revenue']].head(10)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No content performance data available yet.")

    def _render_revenue_tracking(self):
        st.subheader("💰 Revenue Tracking")

        # Revenue over time
        revenue_data = self._get_revenue_over_time()

        if not revenue_data.empty:
            fig = px.line(
                revenue_data,
                x='date',
                y='cumulative_revenue',
                title="Cumulative Revenue Over Time",
                labels={'cumulative_revenue': 'Revenue ($)', 'date': 'Date'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

            # Revenue breakdown
            platform_revenue = self._get_platform_revenue()
            if not platform_revenue.empty:
                fig_pie = px.pie(
                    platform_revenue,
                    values='revenue',
                    names='platform',
                    title="Revenue by Platform"
                )
                fig_pie.update_layout(height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No revenue data available yet.")

        # Monthly target progress
        monthly_target = self.config.get('targets.monthly_revenue', 500)
        current_month_revenue = self._get_current_month_revenue()

        progress = min(current_month_revenue / monthly_target, 1.0)
        st.metric(
            "Monthly Target Progress",
            f"${current_month_revenue:.2f} / ${monthly_target:.2f}",
            f"{progress * 100:.1f}%"
        )
        st.progress(progress)

    def _render_trend_analysis(self):
        st.subheader("📊 Trend Analysis")

        # Top performing cities
        city_stats = self._get_city_performance()

        if not city_stats.empty:
            fig = px.bar(
                city_stats.head(8),
                x='city',
                y='total_clicks',
                title="Clicks by City",
                labels={'total_clicks': 'Total Clicks', 'city': 'City'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

            # Content type performance
            type_stats = self._get_content_type_performance()
            if not type_stats.empty:
                st.write("**Performance by Content Type**")
                st.dataframe(type_stats, use_container_width=True)
        else:
            st.info("No trend data available yet.")

    def _render_posting_activity(self):
        st.subheader("📅 Posting Activity")

        # Posts over time
        posting_data = self._get_posting_activity()

        if not posting_data.empty:
            fig = px.bar(
                posting_data,
                x='date',
                y='posts_count',
                title="Daily Posting Activity",
                labels={'posts_count': 'Posts', 'date': 'Date'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

            # Platform distribution
            platform_posts = self._get_platform_posting_stats()
            if not platform_posts.empty:
                st.write("**Posts by Platform**")
                st.dataframe(platform_posts, use_container_width=True)
        else:
            st.info("No posting activity data available yet.")

    def _render_recent_activity(self):
        st.header("🔄 Recent Activity")

        # Recent posts
        recent_posts = self._get_recent_posts()

        if not recent_posts.empty:
            st.write("**Latest Posts**")

            for _, post in recent_posts.head(10).iterrows():
                with st.expander(f"🔗 {post['title'][:60]}... - {post['platform']}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Posted:** {post['posted_at']}")
                        st.write(f"**Platform:** {post['platform']}")

                    with col2:
                        st.write(f"**Clicks:** {post.get('clicks', 0)}")
                        st.write(f"**Conversions:** {post.get('conversions', 0)}")

                    with col3:
                        if post.get('url'):
                            st.link_button("View Post", post['url'])
                        st.write(f"**Revenue:** ${post.get('revenue', 0):.2f}")
        else:
            st.info("No recent posts to display.")

        # System status
        st.subheader("⚙️ System Status")

        # Check for errors or issues
        system_status = self._get_system_status()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Content Queue", system_status['pending_content'])

        with col2:
            st.metric("Trends Queue", system_status['pending_trends'])

        with col3:
            if system_status['last_run']:
                time_since = datetime.now() - datetime.fromisoformat(system_status['last_run'])
                hours_since = time_since.total_seconds() / 3600
                st.metric("Hours Since Last Run", f"{hours_since:.1f}")
            else:
                st.metric("Last Run", "Never")

    # Data fetching methods
    def _get_available_platforms(self):
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT platform FROM posts WHERE platform IS NOT NULL")
            platforms = [row[0] for row in cursor.fetchall()]
            return platforms if platforms else ['medium', 'twitter', 'reddit']

    def _get_available_cities(self):
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT city FROM trends")
            cities = [row[0] for row in cursor.fetchall()]
            return cities if cities else self.config['content']['cities']

    def _get_period_stats(self):
        start_date = self.date_range[0] if len(self.date_range) == 2 else datetime.now().date() - timedelta(days=30)
        end_date = self.date_range[1] if len(self.date_range) == 2 else datetime.now().date()

        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()

            # Current period stats
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT c.id) as total_posts,
                    COALESCE(SUM(a.clicks), 0) as total_clicks,
                    COALESCE(SUM(a.conversions), 0) as total_conversions,
                    COALESCE(SUM(a.revenue), 0) as total_revenue,
                    CASE
                        WHEN SUM(a.impressions) > 0
                        THEN (SUM(a.clicks) * 100.0 / SUM(a.impressions))
                        ELSE 0
                    END as ctr
                FROM content c
                LEFT JOIN analytics a ON c.id = a.content_id
                WHERE DATE(c.created_at) BETWEEN ? AND ?
            """, (start_date, end_date))

            current_stats = cursor.fetchone()

            return {
                'total_posts': current_stats[0] or 0,
                'total_clicks': current_stats[1] or 0,
                'total_conversions': current_stats[2] or 0,
                'total_revenue': current_stats[3] or 0,
                'ctr': current_stats[4] or 0
            }

    def _get_top_content(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    c.title,
                    c.platform,
                    COALESCE(SUM(a.clicks), 0) as clicks,
                    COALESCE(SUM(a.conversions), 0) as conversions,
                    COALESCE(SUM(a.revenue), 0) as revenue,
                    c.posted_at
                FROM content c
                LEFT JOIN analytics a ON c.id = a.content_id
                WHERE c.status = 'published'
                GROUP BY c.id
                ORDER BY clicks DESC
            """
            return pd.read_sql_query(query, conn)

    def _get_revenue_over_time(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    DATE(a.date) as date,
                    SUM(a.revenue) OVER (ORDER BY DATE(a.date)) as cumulative_revenue
                FROM analytics a
                WHERE a.revenue > 0
                ORDER BY date
            """
            return pd.read_sql_query(query, conn)

    def _get_platform_revenue(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    a.platform,
                    SUM(a.revenue) as revenue
                FROM analytics a
                WHERE a.revenue > 0
                GROUP BY a.platform
                ORDER BY revenue DESC
            """
            return pd.read_sql_query(query, conn)

    def _get_current_month_revenue(self):
        start_of_month = datetime.now().replace(day=1).date()

        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(revenue), 0)
                FROM analytics
                WHERE DATE(date) >= ?
            """, (start_of_month,))

            return cursor.fetchone()[0] or 0

    def _get_city_performance(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    t.city,
                    COUNT(c.id) as content_count,
                    SUM(COALESCE(a.clicks, 0)) as total_clicks,
                    SUM(COALESCE(a.revenue, 0)) as total_revenue
                FROM trends t
                JOIN content c ON t.id = c.trend_id
                LEFT JOIN analytics a ON c.id = a.content_id
                GROUP BY t.city
                ORDER BY total_clicks DESC
            """
            return pd.read_sql_query(query, conn)

    def _get_content_type_performance(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    c.type,
                    COUNT(c.id) as count,
                    AVG(COALESCE(a.clicks, 0)) as avg_clicks,
                    SUM(COALESCE(a.revenue, 0)) as total_revenue
                FROM content c
                LEFT JOIN analytics a ON c.id = a.content_id
                GROUP BY c.type
                ORDER BY avg_clicks DESC
            """
            return pd.read_sql_query(query, conn)

    def _get_posting_activity(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    DATE(posted_at) as date,
                    COUNT(*) as posts_count
                FROM content
                WHERE posted_at IS NOT NULL
                GROUP BY DATE(posted_at)
                ORDER BY date DESC
                LIMIT 30
            """
            return pd.read_sql_query(query, conn)

    def _get_platform_posting_stats(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    platform,
                    COUNT(*) as post_count,
                    AVG(COALESCE(a.clicks, 0)) as avg_clicks
                FROM posts p
                LEFT JOIN analytics a ON p.content_id = a.content_id
                GROUP BY platform
                ORDER BY post_count DESC
            """
            return pd.read_sql_query(query, conn)

    def _get_recent_posts(self):
        with sqlite3.connect(self.db.db_path) as conn:
            query = """
                SELECT
                    c.title,
                    c.platform,
                    c.posted_at,
                    p.url,
                    COALESCE(SUM(a.clicks), 0) as clicks,
                    COALESCE(SUM(a.conversions), 0) as conversions,
                    COALESCE(SUM(a.revenue), 0) as revenue
                FROM content c
                LEFT JOIN posts p ON c.id = p.content_id
                LEFT JOIN analytics a ON c.id = a.content_id
                WHERE c.posted_at IS NOT NULL
                GROUP BY c.id
                ORDER BY c.posted_at DESC
                LIMIT 20
            """
            return pd.read_sql_query(query, conn)

    def _get_system_status(self):
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()

            # Pending content
            cursor.execute("SELECT COUNT(*) FROM content WHERE status = 'draft'")
            pending_content = cursor.fetchone()[0]

            # Pending trends
            cursor.execute("SELECT COUNT(*) FROM trends WHERE status = 'pending'")
            pending_trends = cursor.fetchone()[0]

            # Last run time
            cursor.execute("SELECT MAX(posted_at) FROM content")
            last_run = cursor.fetchone()[0]

            return {
                'pending_content': pending_content,
                'pending_trends': pending_trends,
                'last_run': last_run
            }

if __name__ == "__main__":
    dashboard = AnalyticsDashboard()
    dashboard.run()