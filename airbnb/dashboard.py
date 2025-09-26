import streamlit as st
import pandas as pd
import sqlite3
import yaml
import os

# Load configuration
CONFIG_PATH = 'config.yaml'

def get_config():
    if not os.path.exists(CONFIG_PATH):
        st.error(f"Configuration file not found at {CONFIG_PATH}. Please create it based on the template.")
        return None
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

config = get_config()

def run_dashboard():
    st.set_page_config(layout="wide")
    st.title("🤖 Airbnb Affiliate Bot Dashboard")

    if not config:
        return

    db_path = config.get('system', {}).get('db_path', 'data/trends.db')

    st.header("Performance Overview")

    # --- Metrics --- #
    col1, col2, col3, col4 = st.columns(4)
    # These would be calculated from real data
    col1.metric("Total Clicks", "1,254", "+120 this week")
    col2.metric("Est. Earnings", "$188.10", "+$18.00 this week")
    col3.metric("Content Generated", "28", "+8 this week")
    col4.metric("Conversion Rate", "3.1%", "+0.2%")

    # --- Content Performance Table --- #
    st.subheader("Content Performance")

    # Placeholder data - In a real app, this would come from a database/API
    data = {
        'Date': ['2025-09-23', '2025-09-23', '2025-09-21', '2025-09-21'],
        'Title': [
            'Top 10 Budget Hidden Gems in Nashville 2025',
            '5-Tweet Thread on Nashville's Food Scene',
            'A Weekend in Charleston: The Ultimate Itinerary',
            'Reddit Post: Underrated spots in Charleston?'
        ],
        'Platform': ['Blog (Medium)', 'Twitter/X', 'Blog (Medium)', 'Reddit'],
        'Clicks': [102, 25, 88, 15],
        'Est. Earnings ($)': [15.30, 3.75, 13.20, 2.25]
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)

    # --- Idea Database --- #
    st.subheader("Generated Content Ideas")
    try:
        conn = sqlite3.connect(db_path)
        ideas_df = pd.read_sql_query("SELECT * FROM trends ORDER BY date DESC LIMIT 20;", conn)
        conn.close()
        st.dataframe(ideas_df, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not connect to database at '{db_path}'. Have you run the research agent yet?")
        st.code(str(e))

if __name__ == "__main__":
    run_dashboard()
