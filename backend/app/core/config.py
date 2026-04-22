"""
Central configuration management using Pydantic Settings.
All environment variables are validated and typed here.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "SEO Command Center"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    allowed_hosts: List[str] = ["*"]
    
    # MongoDB
    mongodb_uri: str
    mongodb_db_name: str = "seo_command_center"
    mongodb_max_pool_size: int = 100
    
    # Redis (Celery + Caching)
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600
    
    # External APIs
    pagespeed_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None
    google_places_api_key: Optional[str] = None
    
    # Crawler Settings
    crawler_concurrent_requests: int = 16
    crawler_request_delay: float = 1.0
    crawler_user_agent: str = "SEOCommandCenterBot/1.0"
    crawler_respect_robots_txt: bool = True
    
    # NLP Model
    spacy_model: str = "en_core_web_lg"
    
    # Feature Flags
    enable_competitor_monitoring: bool = True
    enable_backlink_analysis: bool = True
    enable_predictive_roi: bool = True


@lru_cache()
def get_settings() -> Settings:
    """
    Singleton pattern for settings to avoid repeated validation.
    """
    return Settings()
