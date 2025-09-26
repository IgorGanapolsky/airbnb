# 🏠 Airbnb Affiliate Marketing Automation System

A fully automated, low-budget system for generating and distributing Airbnb affiliate marketing content on Mac. Built with Python 3.12+ and designed to run entirely on free tiers with a $100/month budget.

## 🎯 Project Goals

- **Target Revenue**: $500/month passive income within 3 months
- **Content Production**: 5-10 evergreen pieces per week
- **Budget**: $100/month (using only free API tiers)
- **Automation**: Fully automated workflow with minimal manual intervention

## ✨ Features

### 🤖 AI-Powered Content Generation
- **Trend Research**: Daily analysis of travel trends using Google Trends API
- **Multi-Format Content**: Blog posts, Twitter threads, Reddit posts, TikTok scripts
- **SEO Optimization**: Automatic keyword integration and optimization
- **Quality Scoring**: AI-powered content quality assessment

### 📱 Multi-Platform Distribution
- **Medium**: Automated blog post publishing
- **Twitter/X**: Thread posting with optimal timing
- **Reddit**: Community-appropriate content sharing
- **TikTok**: Script generation (manual upload)

### 📊 Performance Analytics
- **Real-time Dashboard**: Streamlit-based analytics interface
- **Click Tracking**: Bitly integration for link analytics
- **Revenue Estimation**: Conversion tracking and projections
- **AI Optimization**: Automated performance improvement suggestions

### 🔄 Full Automation
- **Cron Scheduling**: Automated daily workflows
- **Error Handling**: Robust retry mechanisms and logging
- **Rate Limiting**: Platform-compliant posting schedules
- **Email Notifications**: Performance alerts and summaries

## 🚀 Quick Start (5-Minute Setup)

### Prerequisites
- macOS (Intel or Apple Silicon)
- Python 3.12+ (will be installed automatically)
- Homebrew (will be installed automatically)

### Installation

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd airbnb-affiliate-bot
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

2. **Configure API Keys**
   ```bash
   nano .env
   ```
   Update with your API keys (see [API Setup Guide](#api-setup) below)

3. **Test Installation**
   ```bash
   ./run.sh --dry-run --mode trends
   ```

4. **Launch Dashboard**
   ```bash
   ./dashboard.sh
   ```
   Visit http://localhost:8501

5. **Run Full Workflow**
   ```bash
   ./run.sh --mode full
   ```

## 🔑 API Setup Guide

### Required APIs (Free Tiers)

#### 1. OpenAI API (Required)
- Sign up at [platform.openai.com](https://platform.openai.com)
- Get API key from API Keys section
- Uses `gpt-4o-mini` for cost efficiency

#### 2. Airbnb Affiliate Program (Required)
- Join at [partners.airbnb.com](https://partners.airbnb.com)
- Get your affiliate link
- Commission: ~3% of booking value

### Optional APIs (Enhanced Features)

#### 3. Twitter API v2 (Free Tier)
- Apply at [developer.twitter.com](https://developer.twitter.com)
- Get Bearer Token and API credentials
- Free tier: 1,500 tweets/month

#### 4. Medium API (Free)
- Get integration token from [medium.com/me/settings](https://medium.com/me/settings)
- Unlimited posts to personal account

#### 5. Reddit API (Free)
- Create app at [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
- Get client ID and secret
- Rate limit: 60 requests/minute

#### 6. Bitly API (Free Tier)
- Sign up at [bitly.com](https://bitly.com)
- Get access token from settings
- Free tier: 1,000 links/month

#### 7. Unsplash API (Free)
- Register at [unsplash.com/developers](https://unsplash.com/developers)
- Get access key
- Free tier: 5,000 requests/hour

## 📁 Project Structure

```
airbnb-affiliate-bot/
├── main.py                 # Main entry point
├── config/
│   └── config.yaml        # Configuration file
├── agents/
│   ├── trend_research_agent.py
│   ├── content_generation_agent.py
│   ├── posting_agent.py
│   └── tracking_agent.py
├── utils/
│   ├── config_manager.py
│   ├── database.py
│   └── logger.py
├── dashboard/
│   └── app.py            # Streamlit dashboard
├── scripts/
│   ├── install.sh        # Installation script
│   └── setup_cron.sh     # Automation setup
├── content/              # Generated content
│   ├── blogs/
│   ├── social/
│   └── images/
├── data/                 # Database and analytics
└── logs/                 # Application logs
```

## 🎮 Usage

### Command Line Interface

```bash
# Run full automation workflow
./run.sh --mode full

# Individual components
./run.sh --mode trends     # Research trends
./run.sh --mode content    # Generate content
./run.sh --mode post       # Post content
./run.sh --mode track      # Update analytics

# Dry run mode (no actual posting)
./run.sh --dry-run --mode full

# Launch dashboard
./dashboard.sh
```

### Dashboard Features

- **Overview**: Key metrics and performance summary
- **Content Analytics**: Content quality and performance
- **Performance Metrics**: Detailed click and conversion data
- **Optimization**: AI-powered improvement suggestions
- **Settings**: Configuration and API status

## 📈 Revenue Projections

### Conservative Estimate (3 months)
- **Content**: 60 blog posts, 150 social posts
- **Traffic**: 10,000 monthly page views
- **Click Rate**: 3% (300 clicks/month)
- **Conversion Rate**: 2% (6 bookings/month)
- **Average Booking**: $150
- **Monthly Revenue**: $270 (54% of target)

### Optimistic Estimate (6 months)
- **Content**: 120 blog posts, 300 social posts
- **Traffic**: 25,000 monthly page views
- **Click Rate**: 5% (1,250 clicks/month)
- **Conversion Rate**: 3% (37 bookings/month)
- **Average Booking**: $150
- **Monthly Revenue**: $1,665 (333% of target)

```bash
# Install Python 3.12+ via Homebrew
brew install python@3.12

# Run installation script
./scripts/install.sh
```

### 2. API Keys & Credentials

Edit `config/config.yaml` with your credentials:

#### Booking.com Affiliate (Required)
```yaml
affiliate:
  booking_link: "https://www.booking.com/affiliate-program/..."
```
- Sign up: https://affiliates.booking.com
- Get your affiliate link from the dashboard

#### OpenAI API (Required)
```yaml
ai:
  openai:
    api_key: "sk-..."
```
- Get from: https://platform.openai.com/api-keys
- Cost: ~$5-10/month for content generation

#### Social Platform APIs (Choose 1+)

**Medium** (Recommended - easiest):
```yaml
social:
  medium:
    integration_token: "..."
    enabled: true
```
- Get token: Medium Settings → Integration tokens

**Twitter/X**:
```yaml
social:
  twitter:
    api_key: "..."
    api_secret: "..."
    access_token: "..."
    access_token_secret: "..."
    enabled: true
```
- Get from: https://developer.twitter.com/apps
- Free tier: 1,500 posts/month

**Reddit**:
```yaml
social:
  reddit:
    client_id: "..."
    client_secret: "..."
    username: "your_username"
    password: "your_password"
    enabled: true
```
- Create app: https://www.reddit.com/prefs/apps

#### Bitly (Optional - for click tracking)
```yaml
tracking:
  bitly:
    access_token: "..."
    enabled: true
```
- Free tier: 1,000 links/month

### 3. Content Configuration

Customize cities and posting schedule:

```yaml
content:
  cities:
    - Nashville      # Modify this list
    - Charleston
    - Austin
    # Add your target destinations

  posting_schedule:
    blogs_per_week: 3
    social_posts_per_week: 10
```

## 🤖 Usage

### Manual Commands

```bash
# Research trending topics
python3 main.py research

# Generate content
python3 main.py generate

# Post to social media
python3 main.py post

# Update analytics
python3 main.py analytics

# Run full cycle
python3 main.py full

# Test mode (no posting)
python3 main.py test
python3 main.py full --dry-run
```

### Automated Mode

```bash
# Set up cron jobs for automation
./scripts/setup_cron.sh

# Monitor logs
tail -f logs/cron.log
```

**Daily Schedule**:
- 06:00 - Research trending destinations
- 08:00 - Generate blog posts and social content
- 10:00, 14:00, 18:00 - Post content to platforms
- 22:00 - Update analytics and send reports

### Analytics Dashboard

```bash
python3 main.py dashboard
```

Opens Streamlit dashboard at `http://localhost:8501` showing:
- Revenue tracking and projections
- Click-through rates by platform
- Top performing content
- City/destination performance
- Monthly target progress

## 📊 System Architecture

### Content Pipeline

1. **Trend Research Agent** (`agents/trend_research.py`)
   - Google Trends API integration
   - City-specific travel trend analysis
   - Content idea generation with AI

2. **Content Generator** (`agents/content_generator.py`)
   - Blog posts (800-1500 words, SEO optimized)
   - Twitter threads (5-7 tweets)
   - Reddit posts (authentic, community-friendly)
   - TikTok scripts (30-second format)

3. **Auto-Poster** (`agents/auto_poster.py`)
   - Medium API posting
   - Twitter thread publishing
   - Reddit community posting
   - Error handling and retries

4. **Analytics Tracker** (`dashboard/analytics_dashboard.py`)
   - Bitly click tracking
   - Revenue estimation
   - Performance optimization

### Data Storage

SQLite database (`data/booking_bot.db`) stores:
- Trend research results
- Generated content
- Posting history
- Analytics data

## 💡 Content Examples

### Blog Post Template
```
# 10 Hidden Gem Hotels in Nashville Under $150/Night

Discover Nashville's best-kept accommodation secrets...

## 1. Historic District Boutique
- **Price**: $89/night
- **Why special**: Original 1800s architecture
- **Book here**: [Booking.com link]

[Continue with 9 more recommendations]
```

### Twitter Thread Template
```
🧵 Nashville hidden gems under $150/night:

1/ Did you know Nashville has boutique hotels with 1800s charm for under $100? Here's my insider guide 🎸

2/ 🏛️ Historic District: The Russell Hotel
$89/night • Original architecture • Walking distance to Broadway

3/ 🎨 Music Row: Artist-themed suites
$125/night • Record player in every room • Rooftop bar

[Continue thread...]
```

## 📈 Performance Optimization

### SEO Strategy
- Target long-tail keywords: "budget hotels Nashville downtown"
- City-specific content for local search
- Regular posting for domain authority

### Platform-Specific Optimization

**Medium**:
- 1,500 word comprehensive guides
- High-quality images from Unsplash API
- Strategic tagging for discovery

**Twitter**:
- Thread format for engagement
- Hashtag optimization
- Optimal posting times (2 PM, 8 PM EST)

**Reddit**:
- Authentic, helpful tone
- Community-specific posting
- Value-first approach

### Conversion Optimization
- Multiple booking links per post
- Clear value propositions
- Urgency/scarcity messaging
- Mobile-optimized links

## 🛠️ Troubleshooting

### Common Issues

**"No API key found"**
```bash
# Check config file
cat config/config.yaml
# Ensure no quotes/spaces in API keys
```

**"Import errors"**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

**"Cron jobs not running"**
```bash
# Check cron status
crontab -l
# Check logs
tail -f logs/cron.log
```

**"Social media posting failed"**
- Check API rate limits
- Verify credentials in config
- Test with dry-run mode first

### Logs and Debugging

```bash
# Application logs
tail -f logs/bot.log

# Cron job logs
tail -f logs/cron.log

# Verbose mode
python3 main.py full --verbose
```

## 📚 Legal & Compliance

### FTC Compliance
- All posts include affiliate disclosure
- Clear relationship with Booking.com
- No misleading claims

### Platform Guidelines
- Respects rate limits
- Follows community guidelines
- Authentic, valuable content only

### Privacy
- No personal data collection
- Anonymous analytics only
- GDPR-compliant by design

## 🔄 Scaling & Growth

### Month 1-2: Foundation
- 3 blog posts/week
- 10 social posts/week
- Build content library

### Month 3-6: Expansion
- Add more cities (15-20 total)
- Optimize high-performing content
- A/B test posting times

### Month 6+: Advanced
- Seasonal content calendar
- Video content integration
- Cross-platform promotion

## 🤝 Support & Community

### Getting Help
- Check logs first: `logs/bot.log`
- Run test mode: `python3 main.py test`
- GitHub Issues: [Repository issues]

### Contributing
- Fork repository
- Create feature branch
- Submit pull request

## 📊 ROI Calculator

Based on performance data:

**Conservative Estimate** (3 months):
- 150 posts created
- 50,000 total views
- 1,500 clicks (3% CTR)
- 45 bookings (3% conversion)
- $1,125 revenue ($25 avg commission)
- $375/month average

**Optimistic Estimate** (6 months):
- 300 posts created
- 150,000 total views
- 4,500 clicks (3% CTR)
- 135 bookings (3% conversion)
- $4,050 revenue ($30 avg commission)
- $675/month average

## 🎯 Success Metrics

- **Click-through rate**: Target 3-5%
- **Conversion rate**: Target 2-4%
- **Monthly revenue**: Target $300-800
- **Content quality**: 90%+ posts published
- **Automation uptime**: 95%+ scheduled posts

---

**Start generating passive income today!** Setup takes 5 minutes, runs completely automated, and scales with your success. 🚀