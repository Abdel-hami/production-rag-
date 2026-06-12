"""
Centralized configuration for the application.
use pydantic's BaseSettings to load configuration from environment variables and .env file.
"""

from pydantic_settings import BaseSettings 
from functools import lru_cache # Cache the settings instance to avoid reloading from environment variables multiple times

class Settings(BaseSettings):
    #llm settings
    groq_api_key: str 
    primary_model: str = "gpt-4o"
    secondary_model: str = "gpt-3.5-turbo"

    ## langsmith settings
    langsmith_project_name: str = "production-api"
    langsmith_tracing: bool = True
    langsmith_api_key: str 

    # Application settings
    app_env: str = "development"
    logger_level: str = "INFO"
    rate_limit: str = "20/minute"
    cache_ttl_seconds: int = 300
    max_retries: int = 3


    model_config: dict = {"env_file": ".env", "extra": "ignore"}


    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"
    
@lru_cache()
def get_settings() -> Settings:
    return Settings()
## this function will be used to get the settings instance throughout the application, ensuring that it's only loaded once and cached for subsequent calls.