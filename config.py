# ABOUTME: Configuration management for different environments (development/production)
# ABOUTME: Handles environment variables, validation, and API configurations

import os
import sys
from typing import List, Literal
from pydantic import validator, ValidationError
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: Literal["development", "production"] = "development"
    
    # Server Configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # API Keys
    OPENAI_API_KEY: str = ""
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    
    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v, values):
        if values.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("OPENAI_API_KEY is required in production environment")
        return v
    
    @validator("LOG_LEVEL")
    def set_log_level_by_env(cls, v, values):
        env = values.get("ENVIRONMENT", "development")
        if not v:
            return "INFO" if env == "production" else "DEBUG"
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        print(f"Configuration validation error: {e}")
        sys.exit(1)

settings = get_settings()