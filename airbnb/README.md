# Airbnb Affiliate Marketing Bot

This is a fully automated, low-budget system for generating and distributing Airbnb affiliate marketing content. It runs locally on a Mac, finds trending topics, generates high-quality content using AI, and posts it to various platforms to earn passive income.

**Project Goal:** Generate $500/mo in passive affiliate commissions within 3 months.

## Features

- **Trend Research:** Automatically discovers content ideas based on Google Trends.
- **AI Content Generation:** Uses OpenAI (or other LLMs) to write blog posts, social media threads, and video scripts.
- **Automated Posting:** Publishes content to Medium, Twitter/X, and Reddit.
- **Performance Tracking:** Includes a simple local dashboard to monitor clicks and estimated earnings.
- **Low Budget:** Built to run on free tiers of all services.
- **Scalable:** Easily configured to target new cities and markets.

## How It Works

The system is composed of four main agents:

1.  **Trend Research Agent:** Runs daily to find popular travel search terms for a list of target cities. It uses an LLM to brainstorm content ideas and stores them in a local SQLite database.
2.  **Content Generation Agent:** Takes the ideas from the database and uses an LLM to generate full-length articles, social posts, and scripts. It also finds relevant, free-to-use images from Unsplash.
3.  **Auto-Posting Agent:** Schedules and publishes the generated content to your configured social media accounts.
4.  **Tracking & Optimization Agent:** Provides a simple dashboard to track content performance and helps you understand what's working.

---

## 5-Minute Setup Guide

Follow these steps to get the bot running.

### Step 1: Clone the Repository

Open your terminal and clone this repository to your local machine.

```bash
git clone <repository_url>
cd airbnb-affiliate-bot
```

### Step 2: Configure the Bot

The `config.yaml` file is the control center for the bot. You need to add your API keys and affiliate ID here.

1.  **Rename the template:**
    ```bash
    cp config.yaml config.yaml.template # Keep a backup of the clean template
    ```
    *Note: The repo comes with `config.yaml` which is ignored by git. You can edit it directly.*

2.  **Edit `config.yaml`:**
    Open `config.yaml` in a text editor and fill in the required values. The file contains comments guiding you to where you can find each API key.

    - `openai.api_key`: Your OpenAI API key.
    - `airbnb.affiliate_id`: Your Airbnb affiliate identifier.
    - `bitly.api_token`: For shortening tracking links.
    - `twitter`, `medium`, `reddit`, `unsplash`: API credentials for each platform.

### Step 3: Install Dependencies

Run the `install.sh` script. This will create a local Python virtual environment and install all the necessary libraries.

```bash
chmod +x install.sh
./install.sh
```

After this completes, you must activate the virtual environment for all subsequent commands:

```bash
source venv/bin/activate
```

### Step 4: Set Up the Cron Job (Automation)

To make the bot run automatically, you need to add a `cron` job.

1.  Open your crontab editor:
    ```bash
    crontab -e
    ```

2.  Add the following line to the file. This example runs the bot every Tuesday and Friday at 10:00 AM. You can customize the schedule.

    **Important:** Replace `/full/path/to/airbnb-affiliate-bot` with the actual absolute path to the project directory on your Mac.

    ```cron
    0 10 * * 2,5 /full/path/to/airbnb-affiliate-bot/run.sh >> /full/path/to/airbnb-affiliate-bot/logs/cron.log 2>&1
    ```

3.  Save and exit the editor. Your bot is now scheduled!

---

## Manual Usage

You can run the different agents manually if you need to. Make sure your virtual environment is activated (`source venv/bin/activate`).

- **Run the full pipeline (Research -> Generate -> Post):**
  ```bash
  python3 main.py full_run
  ```
  *(This respects the `dry_run: true/false` setting in your `config.yaml`)*

- **Run only the research agent:**
  ```bash
  python3 main.py research
  ```

- **Launch the performance dashboard:**
  ```bash
  streamlit run dashboard.py
  ```
  *(This will open a new tab in your web browser.)*

## Projected ROI

This model provides a framework for estimating potential returns. The actual performance will vary based on content quality, platform engagement, and market conditions.

**Assumptions:**
- **Content Volume:** 8 posts per week (4 blogs, 4 social threads).
- **Click-Through Rate (CTR):** 5% of viewers click the affiliate link.
- **Conversion Rate:** 3% of clicks result in a booking.
- **Average Commission:** $15 per booking (based on a $500 booking value with a 3% commission rate).

**Calculation:**
- **Weekly Clicks:** (Assumes 1,000 views per post) => 8 posts * 1000 views * 0.05 CTR = 400 clicks
- **Weekly Conversions:** 400 clicks * 0.03 conversion = 12 conversions
- **Weekly Earnings:** 12 conversions * $15/conversion = **$180**
- **Monthly Earnings:** $180 * 4 = **$720**

This projection is optimistic and serves as a target. The system's tracking dashboard will provide real-world data to refine your strategy.
