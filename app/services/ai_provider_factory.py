# ABOUTME: Factory pattern for creating AI provider service instances
# ABOUTME: Manages service instantiation and caching for different AI providers

from typing import Dict, Optional
from app.models import ModelProvider
from app.services.base_ai_service import AIProviderService
from app.services.openai_service import OpenAIService
from app.services.mistral_service import MistralService
from app.services.google_gemini_service import GoogleGeminiService
from logging_config import get_logger

logger = get_logger(__name__)


class AIProviderFactory:
    """Factory class for creating and managing AI provider service instances."""
    
    # Cache for service instances to avoid re-initialization
    _service_cache: Dict[ModelProvider, AIProviderService] = {}
    
    @classmethod
    def get_provider(cls, model_provider: ModelProvider) -> AIProviderService:
        """
        Get the appropriate AI provider service instance.
        
        Args:
            model_provider: The provider enum (openai, mistral, google)
            
        Returns:
            The corresponding AI provider service instance
            
        Raises:
            ValueError: If the provider is unknown
        """
        # Check cache first
        if model_provider in cls._service_cache:
            return cls._service_cache[model_provider]
        
        # Create new instance based on provider
        try:
            if model_provider == ModelProvider.openai:
                service = OpenAIService()
            elif model_provider == ModelProvider.mistral:
                service = MistralService()
            elif model_provider == ModelProvider.google:
                service = GoogleGeminiService()
            else:
                raise ValueError(f"Unknown provider: {model_provider}")
            
            # Cache the instance
            cls._service_cache[model_provider] = service
            logger.info(f"Created new {model_provider.value} service instance")
            
            return service
            
        except Exception as e:
            logger.error(f"Error creating provider service for {model_provider}: {e}")
            raise
    
    @classmethod
    def clear_cache(cls):
        """Clear the service cache. Useful for testing or reinitialization."""
        cls._service_cache.clear()
        logger.info("Cleared AI provider service cache")
    
    @classmethod
    def get_cached_providers(cls) -> Dict[ModelProvider, AIProviderService]:
        """Get all currently cached provider instances."""
        return cls._service_cache.copy()