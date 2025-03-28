import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings
import urllib.parse
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv is not installed. Environment variables may not be loaded from .env file.")
    load_dotenv = lambda: None

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    # Authentication
    AM_API_KEY: str = Field(..., description="API key for authenticating requests")

    # OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key for agent operations")

    # Notion (Optional)
    NOTION_TOKEN: Optional[str] = Field(None, description="Notion integration token")

    # BlackPearl, Omie, Google Drive, Evolution (Optional)
    BLACKPEARL_TOKEN: Optional[str] = Field(None, description="BlackPearl API token")
    OMIE_TOKEN: Optional[str] = Field(None, description="Omie API token")
    GOOGLE_DRIVE_TOKEN: Optional[str] = Field(None, description="Google Drive API token")
    
    # Evolution
    EVOLUTION_API_KEY: Optional[str] = Field(None, description="Evolution API key")
    EVOLUTION_API_URL: Optional[str] = Field(None, description="Evolution API URL")
    EVOLUTION_INSTANCE: str = Field("agent", description="Evolution API instance name")

    # BlackPearl API URL and DB URI
    BLACKPEARL_API_URL: Optional[str] = Field(None, description="BlackPearl API URL")
    BLACKPEARL_DB_URI: Optional[str] = Field(None, description="BlackPearl database URI")

    # Discord
    DISCORD_BOT_TOKEN: str = Field(..., description="Discord bot token for authentication")

    # Database (PostgreSQL)
    DATABASE_URL: str = Field("postgresql://postgres:postgres@localhost:5432/automagik", 
                          description="PostgreSQL connection string")
    POSTGRES_HOST: str = Field("localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field("postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field("postgres", description="PostgreSQL password")
    POSTGRES_DB: str = Field("automagik", description="PostgreSQL database name")
    POSTGRES_POOL_MIN: int = Field(1, description="Minimum connections in the pool")
    POSTGRES_POOL_MAX: int = Field(10, description="Maximum connections in the pool")

    # Server
    AM_PORT: int = Field(8881, description="Port to run the server on")
    AM_HOST: str = Field("0.0.0.0", description="Host to bind the server to")
    AM_ENV: Environment = Field(Environment.DEVELOPMENT, description="Environment (development, production, testing)")

    # Logging
    AM_LOG_LEVEL: LogLevel = Field(LogLevel.INFO, description="Logging level")
    AM_VERBOSE_LOGGING: bool = Field(False, description="Enable verbose logging with additional details")
    LOGFIRE_TOKEN: Optional[str] = Field(None, description="Logfire token for logging service")
    LOGFIRE_IGNORE_NO_CONFIG: bool = Field(True, description="Suppress Logfire warning if no token")

    # Supabase
    SUPABASE_URL: Optional[str] = Field(None, description="Supabase project URL")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(None, description="Supabase service role key for authentication")

    # Suppress warnings from dependency conflict resolution (Poetry related)
    PYTHONWARNINGS: Optional[str] = Field(None, description="Python warnings configuration")

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Allow extra fields in environment variables
    )

def load_settings() -> Settings:
    """Load and validate settings from environment variables and .env file."""
    # Check if we're in debug mode (AM_LOG_LEVEL set to DEBUG)
    debug_mode = os.environ.get('AM_LOG_LEVEL', '').upper() == 'DEBUG'
    
    # Load environment variables from .env file
    try:
        load_dotenv(override=True)
        print(f"📝 .env file loaded from: {Path('.env').absolute()}")
    except Exception as e:
        print(f"⚠️ Error loading .env file: {str(e)}")

    # Debug DATABASE_URL only if in debug mode
    if debug_mode:
        print(f"🔍 DATABASE_URL from environment after dotenv: {os.environ.get('DATABASE_URL', 'Not set')}")

    # Strip comments from environment variables
    for key in os.environ:
        if isinstance(os.environ[key], str) and '#' in os.environ[key]:
            os.environ[key] = os.environ[key].split('#')[0].strip()
            if debug_mode:
                print(f"📝 Stripped comments from environment variable: {key}")

    try:
        # Explicitly set reload=True to ensure environment variables are reloaded
        settings = Settings(_env_file='.env', _env_file_encoding='utf-8')
        
        # Debug DATABASE_URL after loading settings - only in debug mode
        if debug_mode:
            print(f"🔍 DATABASE_URL after loading settings: {settings.DATABASE_URL}")
        
        # Final check - if there's a mismatch, use the environment value
        env_db_url = os.environ.get('DATABASE_URL')
        if env_db_url and env_db_url != settings.DATABASE_URL:
            if debug_mode:
                print(f"⚠️ Overriding settings.DATABASE_URL with environment value")
            # This is a bit hacky but necessary to fix mismatches
            settings.DATABASE_URL = env_db_url
            if debug_mode:
                print(f"📝 Final DATABASE_URL: {settings.DATABASE_URL}")
                
        # We no longer print the detailed configuration here
        # This is now handled by the CLI's debug flag handler in src/cli/__init__.py
        
        return settings
    except Exception as e:
        print("❌ Error loading configuration:")
        print(f"   {str(e)}")
        raise

def mask_connection_string(conn_string: str) -> str:
    """Mask sensitive information in a connection string."""
    try:
        # Parse the connection string
        parsed = urllib.parse.urlparse(conn_string)
        
        # Create a masked version
        if parsed.password:
            # Replace password with asterisks
            masked_netloc = f"{parsed.username}:****@{parsed.hostname}"
            if parsed.port:
                masked_netloc += f":{parsed.port}"
                
            # Reconstruct the URL with masked password
            masked_url = urllib.parse.urlunparse((
                parsed.scheme,
                masked_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return masked_url
        
        return conn_string  # No password to mask
    except Exception:
        # If parsing fails, just show the first and last few characters
        return f"{conn_string[:10]}...{conn_string[-10:]}"

# Create a global settings instance
settings = load_settings()