import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "config.yaml"

            if not config_path.exists():
                template_path = base_dir / "config" / "config_template.yaml"
                if template_path.exists():
                    logger.warning(f"Config not found. Please copy {template_path} to {config_path}")
                    with open(template_path, 'r') as f:
                        self._config = yaml.safe_load(f)
                else:
                    raise FileNotFoundError("No configuration file found")
            else:
                with open(config_path, 'r') as f:
                    self._config = yaml.safe_load(f)

        self._validate_config()
        return self._config

    def _validate_config(self):
        required_keys = [
            'affiliate.airbnb_link',
            'ai.openai.api_key',
            'content.cities',
            'system.database_path'
        ]

        for key_path in required_keys:
            keys = key_path.split('.')
            value = self._config
            for key in keys:
                if key not in value:
                    logger.warning(f"Missing required config key: {key_path}")
                    break
                value = value[key]

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

config = Config()