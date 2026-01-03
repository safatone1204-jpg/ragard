"""Backend configuration using Pydantic settings."""
import sys
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional

# Get the backend directory (parent of app/)
BACKEND_DIR = Path(__file__).parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API configuration
    API_BASE_URL: Optional[str] = None  # For future external API integration
    
    # Reddit API credentials (optional - if not set, uses read-only mode)
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "Ragard/1.0 (Stock Analysis Bot)"
    REDDIT_USERNAME: Optional[str] = None  # Optional, for authenticated access
    REDDIT_PASSWORD: Optional[str] = None  # Optional, for authenticated access
    
    # OpenAI API key for AI features
    OPENAI_API_KEY: Optional[str] = None
    
    # CORS
    # Allow frontend and Chrome extension requests
    # Chrome extensions make requests from chrome-extension:// origin, but localhost should work
    # Stored as comma-separated string in .env file
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    def get_cors_origins_list(self) -> list[str]:
        """Get CORS_ORIGINS as a list (for use in CORS middleware)."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
            return origins if origins else ["http://localhost:3000", "http://localhost:8000"]
        return ["http://localhost:3000", "http://localhost:8000"]
    
    # Environment
    ENVIRONMENT: str = "development"  # "development" or "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Supabase configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    # Error tracking (Sentry)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8-sig",  # utf-8-sig handles BOM
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env
    )


settings = Settings()


def validate_required_env_vars():
    """
    Validate required environment variables on startup.
    Exits with non-zero code if required vars are missing.
    """
    missing_vars = []
    
    # Always required
    if not settings.ENVIRONMENT:
        missing_vars.append("ENVIRONMENT")
    
    if not settings.SUPABASE_URL:
        missing_vars.append("SUPABASE_URL")
    
    if not settings.SUPABASE_ANON_KEY:
        missing_vars.append("SUPABASE_ANON_KEY")
    
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        missing_vars.append("SUPABASE_SERVICE_ROLE_KEY")
    
    # CORS_ORIGINS is stored as a string, check if it's empty
    cors_origins_list = settings.get_cors_origins_list()
    if not cors_origins_list or len(cors_origins_list) == 0:
        missing_vars.append("CORS_ORIGINS")
    
    # OPENAI_API_KEY is required if AI features are enabled
    # For now, we'll only warn if it's missing in production
    # (AI features may be optional depending on deployment)
    
    if missing_vars:
        print("ERROR: Missing required environment variables:", file=sys.stderr)
        for var in missing_vars:
            print(f"  - {var}", file=sys.stderr)
        print("\nPlease set these variables in your .env file or environment.", file=sys.stderr)
        print(f"See {BACKEND_DIR / 'env.example'} for an example configuration.", file=sys.stderr)
        sys.exit(1)
    
    # Warn about optional but recommended vars in production
    if settings.ENVIRONMENT == "production":
        if not settings.OPENAI_API_KEY:
            print("WARNING: OPENAI_API_KEY is not set. AI features will be disabled.", file=sys.stderr)

