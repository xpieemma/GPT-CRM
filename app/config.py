from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "GPT CRM Outreach"
    ENVIRONMENT: str = "development"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Keys
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-8b-8192"
    
    # Security
    WEBHOOK_SECRET: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_PATH: str = "data/outreach.db"
    
    # Rate Limiting
    RATE_LIMIT_AUTHENTICATED: int = 100
    RATE_LIMIT_ANONYMOUS: int = 10
    RATE_LIMIT_WINDOW: int = 60
    
    # Budget
    DEFAULT_DAILY_BUDGET: float = 5.00
    
    # Optional Slack
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    """Cached settings - override in tests via env vars"""
    return Settings()

settings = get_settings()
