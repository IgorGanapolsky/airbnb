"""
Streamlit Dashboard for Airbnb Affiliate Bot
Provides real-time analytics and performance monitoring.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from utils.config_manager import ConfigManager
from utils.database import DatabaseManager
from agents.tracking_agent import TrackingAgent


# Page configuration
st.set_page_config(
    page_title="Airbnb Affiliate Bot Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff5a5f;
    }
    .success-metric {
        border-left-color: #00d4aa;
    }
    .warning-metric {
        border-left-color: #ffb400;
    }
    .danger-metric {
        border-left-color: #ff5a5f;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_config():
    """Load configuration with caching."""
    return ConfigManager().get_config()


@st.cache_data(ttl=300)
def load_performance_data():
    """Load performance data with caching."""
    config = load_config()
    db = DatabaseManager(config.get('database', {}).get('path', 'data/airbnb_bot.db'))
    tracking_agent = TrackingAgent(config, db)
    
    return tracking_agent.analyze_performance()


def main():
    """Main dashboard application."""
    st.title("🏠 Airbnb Affiliate Bot Dashboard")
    st.markdown("Real-time performance monitoring and analytics")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.selectbox(
            "Select Page",
            ["Overview", "Content Analytics", "Performance Metrics", "Optimization", "Settings"]
        )
        
        st.header("Quick Actions")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("▶️ Run Full Workflow"):
            st.info("This would trigger the main automation workflow")
        
        st.header("System Status")
        config = load_config()
        
        # API Status indicators
        api_status = {
            "OpenAI": "🟢" if config.get('api_keys', {}).get('openai_api_key') else "🔴",
            "Twitter": "🟢" if config.get('api_keys', {}).get('twitter_api_key') else "🔴",
            "Medium": "🟢" if config.get('api_keys', {}).get('medium_access_token') else "🔴",
            "Reddit": "🟢" if config.get('api_keys', {}).get('reddit_client_id') else "🔴",
            "Bitly": "🟢" if config.get('api_keys', {}).get('bitly_access_token') else "🔴"
        }
        
        for service, status in api_status.items():
            st.write(f"{status} {service}")
    
    # Main content based on selected page
    if page == "Overview":
        show_overview_page()
    elif page == "Content Analytics":
        show_content_analytics_page()
    elif page == "Performance Metrics":
        show_performance_metrics_page()
    elif page == "Optimization":
        show_optimization_page()
    elif page == "Settings":
        show_settings_page()


def show_overview_page():
    """Show overview dashboard page."""
    st.header("📊 Performance Overview")
    
    # Load performance data
    try:
        performance_data = load_performance_data()
        summary = performance_data.get('summary', {})
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            revenue = summary.get('estimated_revenue', 0)
            st.metric(
                label="💰 Estimated Revenue",
                value=f"${revenue:.2f}",
                delta=f"Target: $500"
            )
        
        with col2:
            clicks = summary.get('total_clicks', 0)
            st.metric(
                label="👆 Total Clicks",
                value=f"{clicks:,}",
                delta=f"Last 30 days"
            )
        
        with col3:
            posts = summary.get('total_posts', 0)
            st.metric(
                label="📝 Total Posts",
                value=f"{posts}",
                delta=f"Last 30 days"
            )
        
        with col4:
            grade = summary.get('performance_grade', 'C')
            grade_color = {
                'A': '🟢', 'B': '🟡', 'C': '🟠', 'D': '🔴', 'F': '🔴'
            }.get(grade, '🟠')
            st.metric(
                label="📈 Performance Grade",
                value=f"{grade_color} {grade}",
                delta="Overall score"
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Revenue Trend")
            # Create sample trend data (in production, this would come from database)
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            revenue_trend = pd.DataFrame({
                'Date': dates,
                'Revenue': [revenue * (0.5 + 0.5 * i / len(dates)) for i in range(len(dates))]
            })
            
            fig = px.line(revenue_trend, x='Date', y='Revenue', title="Daily Revenue Trend")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Performance Metrics")
            metrics_data = {
                'Metric': ['Click Rate', 'Conversion Rate', 'Content Quality'],
                'Current': [
                    summary.get('click_rate', 0) * 100,
                    summary.get('conversion_rate', 0) * 100,
                    75  # Placeholder
                ],
                'Target': [5, 3, 80]
            }
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Current', x=metrics_data['Metric'], y=metrics_data['Current']))
            fig.add_trace(go.Bar(name='Target', x=metrics_data['Metric'], y=metrics_data['Target']))
            fig.update_layout(barmode='group', height=300, title="Current vs Target Metrics")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        
        # This would show recent posts, content generation, etc.
        activity_data = [
            {"Time": "2 hours ago", "Action": "Generated blog post", "Status": "✅ Success"},
            {"Time": "4 hours ago", "Action": "Posted to Twitter", "Status": "✅ Success"},
            {"Time": "6 hours ago", "Action": "Research trends", "Status": "✅ Success"},
            {"Time": "1 day ago", "Action": "Posted to Medium", "Status": "⚠️ Pending"},
        ]
        
        df = pd.DataFrame(activity_data)
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load performance data: {e}")
        st.info("Make sure the bot has been run at least once to generate data.")


def show_content_analytics_page():
    """Show content analytics page."""
    st.header("📝 Content Analytics")
    
    try:
        config = load_config()
        db = DatabaseManager(config.get('database', {}).get('path', 'data/airbnb_bot.db'))
        
        # Content statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Content by Type")
            # Sample data - in production, query from database
            content_types = ['Blog Posts', 'Twitter Threads', 'Reddit Posts', 'TikTok Scripts']
            content_counts = [15, 25, 12, 8]
            
            fig = px.pie(values=content_counts, names=content_types, title="Content Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Content Quality Scores")
            quality_data = pd.DataFrame({
                'Content Type': content_types,
                'Avg Quality Score': [0.85, 0.78, 0.82, 0.75],
                'Count': content_counts
            })
            
            fig = px.bar(quality_data, x='Content Type', y='Avg Quality Score', 
                        title="Average Quality Score by Type")
            st.plotly_chart(fig, use_container_width=True)
        
        # Top performing content
        st.subheader("🏆 Top Performing Content")
        top_content = pd.DataFrame({
            'Title': [
                "Hidden Gems in Nashville Under $100",
                "Charleston's Best Airbnb Neighborhoods",
                "Austin Travel Guide 2025",
                "Savannah Historic District Stays"
            ],
            'Type': ['Blog Post', 'Twitter Thread', 'Blog Post', 'Reddit Post'],
            'Quality Score': [0.92, 0.88, 0.85, 0.83],
            'Clicks': [156, 89, 134, 67],
            'Status': ['Posted', 'Posted', 'Posted', 'Posted']
        })
        
        st.dataframe(top_content, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load content analytics: {e}")


def show_performance_metrics_page():
    """Show detailed performance metrics page."""
    st.header("📊 Performance Metrics")
    
    try:
        performance_data = load_performance_data()
        
        # Detailed metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📈 Click Metrics")
            bitly_metrics = performance_data.get('metrics', {}).get('bitly', {})
            
            st.metric("Total Clicks", bitly_metrics.get('total_clicks', 0))
            st.metric("Active Links", len(bitly_metrics.get('links', [])))
            
            if bitly_metrics.get('links'):
                links_df = pd.DataFrame(bitly_metrics['links'])
                st.dataframe(links_df[['clicks', 'created_at']], use_container_width=True)
        
        with col2:
            st.subheader("🎯 Conversion Metrics")
            summary = performance_data.get('summary', {})
            
            st.metric("Click Rate", f"{summary.get('click_rate', 0):.2%}")
            st.metric("Conversion Rate", f"{summary.get('conversion_rate', 0):.2%}")
            st.metric("Revenue per Click", f"${summary.get('estimated_revenue', 0) / max(summary.get('total_clicks', 1), 1):.2f}")
        
        with col3:
            st.subheader("📱 Platform Metrics")
            platform_metrics = performance_data.get('metrics', {}).get('platforms', {})
            
            for platform, metrics in platform_metrics.items():
                st.write(f"**{platform.title()}**")
                for metric, value in metrics.items():
                    st.write(f"- {metric.title()}: {value}")
        
        # Performance over time
        st.subheader("📈 Performance Trends")
        
        # Sample trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        trend_data = pd.DataFrame({
            'Date': dates,
            'Clicks': [20 + 5 * i + 10 * (i % 7 == 0) for i in range(len(dates))],
            'Revenue': [5 + 2 * i + 15 * (i % 7 == 0) for i in range(len(dates))]
        })
        
        fig = px.line(trend_data, x='Date', y=['Clicks', 'Revenue'], 
                     title="Daily Performance Trends")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load performance metrics: {e}")


def show_optimization_page():
    """Show optimization suggestions page."""
    st.header("🚀 Optimization Suggestions")
    
    try:
        performance_data = load_performance_data()
        suggestions = performance_data.get('optimization_suggestions', [])
        recommendations = performance_data.get('recommendations', [])
        
        if suggestions:
            st.subheader("🤖 AI-Powered Suggestions")
            for i, suggestion in enumerate(suggestions, 1):
                st.write(f"**{i}.** {suggestion}")
        
        if recommendations:
            st.subheader("📋 General Recommendations")
            for i, recommendation in enumerate(recommendations, 1):
                st.write(f"**{i}.** {recommendation}")
        
        # Performance targets
        st.subheader("🎯 Performance Targets")
        targets = performance_data.get('targets', {})
        summary = performance_data.get('summary', {})
        
        target_data = pd.DataFrame({
            'Metric': ['Click Rate', 'Conversion Rate', 'Monthly Revenue'],
            'Current': [
                summary.get('click_rate', 0) * 100,
                summary.get('conversion_rate', 0) * 100,
                summary.get('estimated_revenue', 0)
            ],
            'Target': [
                targets.get('click_rate', 0.05) * 100,
                targets.get('conversion_rate', 0.03) * 100,
                targets.get('monthly_revenue', 500)
            ]
        })
        
        fig = px.bar(target_data, x='Metric', y=['Current', 'Target'], 
                    barmode='group', title="Current vs Target Performance")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load optimization data: {e}")


def show_settings_page():
    """Show settings and configuration page."""
    st.header("⚙️ Settings")
    
    try:
        config = load_config()
        
        st.subheader("🔑 API Configuration")
        
        # Show API key status (masked)
        api_keys = config.get('api_keys', {})
        for service, key in api_keys.items():
            status = "✅ Configured" if key else "❌ Not configured"
            masked_key = f"{key[:8]}..." if key and len(key) > 8 else "Not set"
            st.write(f"**{service.replace('_', ' ').title()}**: {status} ({masked_key})")
        
        st.subheader("🎯 Performance Targets")
        performance_config = config.get('performance', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Target Click Rate**: {performance_config.get('target_click_rate', 0.05):.1%}")
            st.write(f"**Target Conversion Rate**: {performance_config.get('target_conversion_rate', 0.03):.1%}")
        
        with col2:
            st.write(f"**Target Monthly Revenue**: ${performance_config.get('target_monthly_revenue', 500):.2f}")
            st.write(f"**Min Content Score**: {performance_config.get('min_content_score', 0.7):.1f}")
        
        st.subheader("📅 Automation Schedule")
        schedules = config.get('automation', {}).get('schedules', {})
        
        for task, schedule in schedules.items():
            st.write(f"**{task.replace('_', ' ').title()}**: {schedule}")
        
        st.subheader("🏙️ Target Cities")
        cities = config.get('content', {}).get('target_cities', [])
        st.write(", ".join(cities))
        
        if st.button("📝 Edit Configuration"):
            st.info("Configuration editing would open the config.yaml file")
        
    except Exception as e:
        st.error(f"Failed to load settings: {e}")


if __name__ == "__main__":
    main()
