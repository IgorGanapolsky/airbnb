import argparse
import os
import sys
import yaml
import logging

# Agent modules
from agents import research_agent
from agents import content_agent
from agents import posting_agent
from dashboard import run_dashboard

# --- Configuration and Logging ---
def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_path='config.yaml'):
    if not os.path.exists(config_path):
        logging.error(f"CRITICAL: Configuration file not found at {config_path}. Exiting.")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

# --- Main Application Logic ---
def main():
    config = load_config()
    setup_logging(config.get('system', {}).get('log_file', 'logs/app.log'))

    parser = argparse.ArgumentParser(
        description="A bot for automated Airbnb affiliate marketing content creation and distribution.",
        epilog="Example: python3 main.py full_run"
    )
    parser.add_argument(
        'command',
        choices=['research', 'generate', 'post', 'dashboard', 'full_run'],
        help="The main command to execute."
    )
    parser.add_argument(
        '--city',
        type=str,
        help="(Optional) Specify a single city to process, overriding the weekly rotation."
    )

    args = parser.parse_args()

    # The 'dry_run' flag is now controlled globally from the config file
    is_dry_run = config.get('system', {}).get('dry_run', True)
    if is_dry_run:
        logging.info("--- Running in DRY RUN mode. No content will be published. ---")

    # --- Command Dispatcher ---
    if args.command == 'research':
        logging.info("Starting Trend Research Agent...")
        research_agent.run(config, city_override=args.city)
        logging.info("Research agent finished.")

    elif args.command == 'generate':
        logging.info("Starting Content Generation Agent...")
        content_agent.run(config)
        logging.info("Content generation finished.")

    elif args.command == 'post':
        logging.info("Starting Auto-Posting Agent...")
        posting_agent.run(config, dry_run=is_dry_run)
        logging.info("Auto-posting finished.")

    elif args.command == 'dashboard':
        logging.info("Launching Performance Dashboard...")
        # This is a blocking call, it will run until the user closes the browser tab
        try:
            # Streamlit runs in its own process
            os.system("streamlit run dashboard.py")
        except KeyboardInterrupt:
            logging.info("Dashboard stopped.")

    elif args.command == 'full_run':
        logging.info("=== EXECUTING FULL PIPELINE RUN ===")
        logging.info("Step 1: Running Trend Research Agent...")
        research_agent.run(config, city_override=args.city)
        logging.info("Step 2: Running Content Generation Agent...")
        content_agent.run(config)
        logging.info("Step 3: Running Auto-Posting Agent...")
        posting_agent.run(config, dry_run=is_dry_run)
        logging.info("=== FULL PIPELINE RUN COMPLETE ===")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
