#!/bin/bash

# This script runs the full content pipeline.
# It is designed to be called from a cron job.
# Example cron job to run this every Tuesday and Friday at 10:00 AM:
# 0 10 * * 2,5 /full/path/to/airbnb-affiliate-bot/run.sh >> /full/path/to/airbnb-affiliate-bot/logs/cron.log 2>&1

# Ensure the script runs from the correct directory
cd "$(dirname "$0")"

echo "--- Starting Airbnb Affiliate Bot run at $(date) ---"

# Activate virtual environment
source venv/bin/activate

# Run the main Python script
# The 'full_run' command executes the entire pipeline.
# It respects the 'dry_run' setting in config.yaml
python3 main.py full_run

echo "--- Pipeline run finished at $(date) ---"
