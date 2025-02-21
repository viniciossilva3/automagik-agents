"""Configuration module for loading environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Notion configuration
NOTION_SECRET = os.getenv('NOTION_SECRET')

if not NOTION_SECRET:
    raise ValueError("NOTION_SECRET environment variable is not set")
