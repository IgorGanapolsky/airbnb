"""
Configuration Management System
Handles loading, validation, and management of system configuration.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Manages system configuration from YAML files and environment variables."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration manager."""
        self.config_path = Path(config_path)
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                self.config = self._get_default_config()
                self._save_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            'api_keys': {
                'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
                'twitter_bearer_token': os.getenv('TWITTER_BEARER_TOKEN', ''),
                'twitter_api_key': os.getenv('TWITTER_API_KEY', ''),
                'twitter_api_secret': os.getenv('TWITTER_API_SECRET', ''),
                'twitter_access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
                'twitter_access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', ''),
                'medium_access_token': os.getenv('MEDIUM_ACCESS_TOKEN', ''),
                'reddit_client_id': os.getenv('REDDIT_CLIENT_ID', ''),
                'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET', ''),
                'reddit_user_agent': os.getenv('REDDIT_USER_AGENT', 'AirbnbAffiliateBot/1.0'),
                'bitly_access_token': os.getenv('BITLY_ACCESS_TOKEN', ''),
                'unsplash_access_key': os.getenv('UNSPLASH_ACCESS_KEY', ''),
            },
            'affiliate': {
                'airbnb_affiliate_link': os.getenv('AIRBNB_AFFILIATE_LINK', 'https://www.airbnb.com/'),
                'commission_rate': 0.03,  # 3% estimated conversion rate
                'avg_booking_value': 150.0,  # Average booking value in USD
            },
            'content': {
                'target_cities': [
                    'Nashville', 'Charleston', 'Savannah', 'Austin', 'Portland',
                    'Asheville', 'Santa Fe', 'Key West', 'Sedona', 'Providence'
                ],
                'content_types': ['blog_post', 'twitter_thread', 'reddit_post', 'tiktok_script'],
                'posting_schedule': {
                    'blogs_per_week': 3,
                    'social_posts_per_week': 5,
                    'max_posts_per_day': 2
                },
                'seo_keywords': [
                    'budget airbnb', 'hidden gems', 'travel 2025', 'affordable stays',
                    'unique airbnb', 'local experiences', 'weekend getaway'
                ]
            },
            'ai': {
                'primary_model': 'openai',  # 'openai' or 'anthropic'
                'openai_model': 'gpt-4o-mini',  # Cost-effective model
                'anthropic_model': 'claude-3-haiku-20240307',  # Cost-effective model
                'max_tokens': 2000,
                'temperature': 0.7,
            },
            'database': {
                'path': 'data/airbnb_bot.db',
                'backup_enabled': True,
                'backup_frequency': 'daily'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/airbnb_bot.log',
                'max_file_size': '10MB',
                'backup_count': 5
            },
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender_email': os.getenv('SENDER_EMAIL', ''),
                'sender_password': os.getenv('SENDER_PASSWORD', ''),
                'recipient_email': os.getenv('RECIPIENT_EMAIL', ''),
            },
            'social_platforms': {
                'medium': {
                    'enabled': True,
                    'publication_id': os.getenv('MEDIUM_PUBLICATION_ID', ''),
                    'tags': ['Travel', 'Airbnb', 'Budget Travel', 'Hidden Gems', '2025']
                },
                'twitter': {
                    'enabled': True,
                    'hashtags': ['#Airbnb', '#Travel2025', '#BudgetTravel', '#HiddenGems']
                },
                'reddit': {
                    'enabled': True,
                    'subreddits': ['travel', 'Airbnb', 'solotravel', 'backpacking'],
                    'post_delay_hours': 24  # Avoid spam detection
                }
            },
            'performance': {
                'target_monthly_revenue': 500.0,
                'target_click_rate': 0.05,  # 5%
                'target_conversion_rate': 0.03,  # 3%
                'min_content_score': 0.7,  # Minimum quality score
            }
        }
    
    def _save_default_config(self):
        """Save default configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            self.logger.info(f"Default configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save default configuration: {e}")
    
    def _validate_config(self):
        """Validate configuration and warn about missing required fields."""
        required_keys = [
            'api_keys.openai_api_key',
            'affiliate.airbnb_affiliate_link',
        ]
        
        missing_keys = []
        for key_path in required_keys:
            if not self._get_nested_value(key_path):
                missing_keys.append(key_path)
        
        if missing_keys:
            self.logger.warning(f"Missing required configuration keys: {missing_keys}")
            self.logger.warning("Please update config/config.yaml or set environment variables")
    
    def _get_nested_value(self, key_path: str) -> Any:
        """Get nested configuration value using dot notation."""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self.config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        value = self._get_nested_value(key_path)
        return value if value is not None else default
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        self.config.update(updates)
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            self.logger.info("Configuration updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
    
    def is_api_configured(self, service: str) -> bool:
        """Check if API credentials are configured for a service."""
        api_key_map = {
            'openai': 'api_keys.openai_api_key',
            'anthropic': 'api_keys.anthropic_api_key',
            'twitter': 'api_keys.twitter_api_key',
            'medium': 'api_keys.medium_access_token',
            'reddit': 'api_keys.reddit_client_id',
            'bitly': 'api_keys.bitly_access_token',
            'unsplash': 'api_keys.unsplash_access_key',
        }
        
        if service not in api_key_map:
            return False
        
        api_key = self.get(api_key_map[service])
        return bool(api_key and api_key.strip())
