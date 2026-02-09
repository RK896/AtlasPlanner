from dotenv import load_dotenv
import os
from pathlib import Path
import yaml

# Load environment variables from .env
load_dotenv()

# Get API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")

# Build path to config.yaml (at project root, two levels up from this file)
config_path = Path(__file__).parent.parent.parent / "config.yaml"

# Load YAML configuration
with open(config_path) as f:
    config_data = yaml.safe_load(f)

# Export as module-level constants
API_KEY = api_key
MODEL_CONFIG = config_data["model"]

