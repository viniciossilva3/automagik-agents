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

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Logfire configuration
LOGFIRE_TOKEN = os.getenv('LOGFIRE_TOKEN')
if not LOGFIRE_TOKEN:
    raise ValueError("LOGFIRE_TOKEN environment variable is not set")
