import os

import logging
from pathlib import Path
from enum import Enum
from typing import Optional
import os
import json
from datetime import datetime

# Global logger
logger = logging.getLogger(__name__)

# Define paths
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.dirname(ROOT_PATH)
TEMPLATE_PATH = os.path.join(os.path.dirname(ROOT_PATH), 'templates')

class Config:
    """Configuration class for application settings."""
    
    def __init__(self, data_dir: str = None, **args):
        """
        Initialize configuration.
        
        Args:
            data_dir: Optional custom path for data directory
        """
        # Ensure environment is an Environment enum value
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        self.root_dir = ROOT_PATH if 'root' not in args else args["root"]
        self.template_dir = TEMPLATE_PATH if 'template' not in args else args["template"]
         
        # Try to load configuration from file
        config_path = Path(__file__).parent.parent / 'config' / 'data_config.json'
        if config_path.exists():
            with open(config_path) as f:
                config_data = json.load(f)
            self.data_dir = Path(config_data['data_directory']).expanduser()
            self.output_dir = Path(config_data['output_directory']).expanduser()
        else:
            # Fall back to default behavior
            if data_dir:
                self.data_dir = Path(data_dir).expanduser()
            else:
                self.data_dir = Path(os.path.expanduser('~/data/PhysSetAutomation'))
        
        # Ensure all directories exist
        self.scan_dir = self.data_dir / 'scanned'
        self.processed_dir = self.data_dir / 'processed' / 'portfolios'

        # URL for the application
        self.url = config_data['url']
        
    def ensure_directories(self):
        """Create all necessary directories."""
        for dir in [self.scanned_dir, self.processed_dir]:
            dir.mkdir(parents=True, exist_ok=True)
            