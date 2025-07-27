"""
AI Configuration and Utilities for InstantIn.me

This module provides configuration management and utilities for AI services
including Groq API integration, rate limiting, and feature toggles.
"""

from typing import Dict, List, Optional
from enum import Enum
import time
from datetime import datetime, timedelta

from app.config import settings


class AIFeature(Enum):
    """Available AI features in InstantIn.me"""
    PAGE_BUILDER = "page_builder"
    CONTENT_GENERATION = "content_generation"
    MIGRATION = "migration"
    OPTIMIZATION = "optimization"


class AIProvider(Enum):
    """Supported AI providers"""
    GROQ = "groq"
    # Future: OPENAI = "openai"
    # Future: ANTHROPIC = "anthropic"


class AIConfigManager:
    """
    Manages AI configuration, feature toggles, and service availability.
    
    Provides utilities for:
    - Feature availability checking
    - Rate limiting configuration
    - Service health monitoring
    - Dynamic configuration updates
    """
    
    def __init__(self):
        self.settings = settings
        self._last_health_check = None
        self._service_status = {}
    
    @property
    def groq_config(self) -> Dict:
        """Get Groq API configuration"""
        return {
            "api_key": self.settings.groq_api_key,
            "model": self.settings.groq_model,
            "max_tokens": self.settings.groq_max_tokens,
            "temperature": self.settings.groq_temperature,
            "timeout": self.settings.groq_timeout,
        }
    
    @property
    def rate_limits(self) -> Dict:
        """Get rate limiting configuration"""
        return {
            "daily_requests_per_user": self.settings.ai_daily_requests_per_user,
            "bio_max_length": self.settings.ai_bio_max_length,
            "description_max_length": self.settings.ai_description_max_length,
            "product_description_max_length": self.settings.ai_product_description_max_length,
        }
    
    @property
    def page_builder_config(self) -> Dict:
        """Get AI page builder configuration"""
        return {
            "enabled": self.settings.ai_page_builder_enabled,
            "max_links": self.settings.ai_page_builder_max_links,
            "max_products": self.settings.ai_page_builder_max_products,
            "timeout": self.settings.ai_page_builder_timeout,
        }
    
    @property
    def migration_config(self) -> Dict:
        """Get AI migration configuration"""
        return {
            "enabled": self.settings.ai_migration_enabled,
            "timeout": self.settings.ai_migration_timeout,
            "max_retries": self.settings.ai_migration_max_retries,
            "supported_platforms": self.settings.ai_migration_supported_platforms,
        }
    
    def is_feature_available(self, feature: AIFeature) -> bool:
        """
        Check if an AI feature is available.
        
        Args:
            feature: The AI feature to check
            
        Returns:
            bool: True if feature is available and enabled
        """
        if not self.settings.groq_configured:
            return False
        
        feature_map = {
            AIFeature.PAGE_BUILDER: self.settings.ai_page_builder_available,
            AIFeature.CONTENT_GENERATION: self.settings.ai_content_generation_available,
            AIFeature.MIGRATION: self.settings.ai_migration_available,
            AIFeature.OPTIMIZATION: self.settings.ai_optimization_available,
        }
        
        return feature_map.get(feature, False)
    
    def get_available_features(self) -> List[AIFeature]:
        """Get list of all available AI features"""
        return [
            feature for feature in AIFeature 
            if self.is_feature_available(feature)
        ]
    
    def validate_content_length(self, content: str, content_type: str) -> bool:
        """
        Validate content length against AI limits.
        
        Args:
            content: The content to validate
            content_type: Type of content (bio, description, product_description)
            
        Returns:
            bool: True if content length is within limits
        """
        limits = {
            "bio": self.settings.ai_bio_max_length,
            "description": self.settings.ai_description_max_length,
            "product_description": self.settings.ai_product_description_max_length,
        }
        
        max_length = limits.get(content_type)
        if max_length is None:
            return True
        
        return len(content) <= max_length
    
    def is_platform_supported(self, platform: str) -> bool:
        """
        Check if a platform is supported for migration.
        
        Args:
            platform: Platform name to check
            
        Returns:
            bool: True if platform is supported
        """
        return platform.lower() in [
            p.lower() for p in self.settings.ai_migration_supported_platforms
        ]
    
    def get_health_status(self) -> Dict:
        """
        Get comprehensive AI services health status.
        
        Returns:
            Dict: Health status information
        """
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "groq": {
                "configured": self.settings.groq_configured,
                "model": self.settings.groq_model if self.settings.groq_configured else None,
            },
            "unsplash": {
                "configured": self.settings.unsplash_configured,
            },
            "features": {
                feature.value: self.is_feature_available(feature)
                for feature in AIFeature
            },
            "rate_limits": self.rate_limits,
        }
        
        return status
    
    def log_configuration(self) -> None:
        """Log current AI configuration for debugging"""
        print("\n🤖 AI Configuration Status:")
        print(f"  Groq API: {'✅ Configured' if self.settings.groq_configured else '❌ Not configured'}")
        print(f"  Model: {self.settings.groq_model}")
        print(f"  Unsplash: {'✅ Configured' if self.settings.unsplash_configured else '❌ Not configured'}")
        
        print("\n🎯 Available Features:")
        available_features = self.get_available_features()
        if available_features:
            for feature in available_features:
                print(f"  ✅ {feature.value.replace('_', ' ').title()}")
        else:
            print("  ❌ No AI features available (check API keys)")
        
        print(f"\n📊 Rate Limits:")
        print(f"  Daily requests per user: {self.settings.ai_daily_requests_per_user}")
        print(f"  Bio max length: {self.settings.ai_bio_max_length}")
        print(f"  Description max length: {self.settings.ai_description_max_length}")


# Global AI configuration manager instance
ai_config = AIConfigManager()


# Convenience functions for easy import
def is_ai_available() -> bool:
    """Check if any AI features are available"""
    return settings.groq_configured


def get_groq_config() -> Dict:
    """Get Groq configuration"""
    return ai_config.groq_config


def is_feature_enabled(feature: AIFeature) -> bool:
    """Check if a specific AI feature is enabled"""
    return ai_config.is_feature_available(feature)


def validate_ai_content(content: str, content_type: str) -> bool:
    """Validate AI-generated content length"""
    return ai_config.validate_content_length(content, content_type)


if __name__ == "__main__":
    # Test configuration when run directly
    ai_config.log_configuration() 