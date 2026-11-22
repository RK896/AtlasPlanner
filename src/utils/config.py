from dotenv import load_dotenv
import os
from pathlib import Path
import yaml

# Project root is two levels up from this file (src/utils/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load environment variables from .env
load_dotenv(ENV_PATH)

# Get API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")

config_path = PROJECT_ROOT / "config.yaml"

# Load YAML configuration
with open(config_path) as f:
    config_data = yaml.safe_load(f)

# Export as module-level constants
API_KEY = api_key
MODEL_CONFIG = config_data["model"]

