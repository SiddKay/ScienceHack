# ABOUTME: Configuration management for different environments (development/production)
# ABOUTME: Handles environment variables, validation, and API configurations

import os
import sys
from typing import List, Literal
from pydantic import field_validator, ValidationError
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: Literal["development", "production"] = "development"
    
    # Server Configuration
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # API Keys
    OPENAI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str, info) -> str:
        if info.data.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("OPENAI_API_KEY is required in production environment")
        return v
    
    @field_validator("MISTRAL_API_KEY", "GOOGLE_API_KEY")
    @classmethod
    def validate_provider_keys(cls, v: str) -> str:
        # Only validate if actually using that provider
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def set_log_level_by_env(cls, v: str, info) -> str:
        env = info.data.get("ENVIRONMENT", "development")
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