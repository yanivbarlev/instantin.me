"""
AI Services for InstantIn.me

This module provides high-level AI services that combine prompt templates
with the Groq client to deliver complete AI-powered features.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

from app.ai.client import groq_client, GroqError, AIFeature
from app.ai.prompts import format_prompt, validate_prompt_variables
from app.ai.config import ai_config

# Configure logging
logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    def __init__(self, message: str, service: str, error_type: str = "general"):
        super().__init__(message)
        self.service = service
        self.error_type = error_type


class ContentGenerationService:
    """
    AI-powered content generation service for bios, descriptions, and more.
    """
    
    @staticmethod
    async def generate_bio(
        name: str,
        profession: str,
        interests: Optional[str] = None,
        target_audience: Optional[str] = None,
        tone: Optional[str] = "professional"
    ) -> Dict[str, Any]:
        """
        Generate a compelling bio for a storefront.
        
        Args:
            name: Person's name
            profession: Their profession or role
            interests: Optional interests to include
            target_audience: Optional target audience
            tone: Tone of the bio (professional, casual, motivational, etc.)
            
        Returns:
            Dict with generated bio and metadata
        """
        try:
            # Validate feature availability
            if not ai_config.is_feature_available(AIFeature.CONTENT_GENERATION):
                raise AIServiceError(
                    "Content generation feature is disabled", 
                    "content_generation",
                    "feature_disabled"
                )
            
            # Prepare template variables
            variables = {
                "name": name,
                "profession": profession,
                "interests": interests or "",
                "target_audience": target_audience or "",
                "tone": tone or "professional"
            }
            
            # Format the prompt
            prompt_data = format_prompt("bio_generation", variables)
            
            # Generate content using Groq
            start_time = time.time()
            generated_bio = await groq_client.generate_text(
                prompt=prompt_data["prompt"],
                max_tokens=prompt_data["max_tokens"],
                temperature=prompt_data["temperature"],
                feature=AIFeature.CONTENT_GENERATION
            )
            
            generation_time = time.time() - start_time
            
            # Validate content length
            if not ai_config.validate_content_length(generated_bio, "bio"):
                logger.warning(f"Generated bio exceeds recommended length: {len(generated_bio)} chars")
            
            return {
                "bio": generated_bio.strip(),
                "metadata": {
                    "generation_time": round(generation_time, 2),
                    "character_count": len(generated_bio),
                    "template_used": "bio_generation",
                    "variables": variables,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except GroqError as e:
            logger.error(f"Groq API error in bio generation: {e}")
            raise AIServiceError(f"AI service error: {e}", "bio_generation", "api_error")
        except Exception as e:
            logger.error(f"Unexpected error in bio generation: {e}")
            raise AIServiceError(f"Bio generation failed: {e}", "bio_generation", "internal_error")
    
    @staticmethod
    async def generate_product_description(
        product_name: str,
        product_type: str,
        price: Optional[str] = None,
        features: Optional[str] = None,
        target_audience: Optional[str] = None,
        benefits: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a compelling product description.
        
        Args:
            product_name: Name of the product
            product_type: Type/category of product
            price: Optional price information
            features: Optional key features
            target_audience: Optional target audience
            benefits: Optional benefits to highlight
            
        Returns:
            Dict with generated description and metadata
        """
        try:
            # Validate feature availability
            if not ai_config.is_feature_available(AIFeature.CONTENT_GENERATION):
                raise AIServiceError(
                    "Content generation feature is disabled", 
                    "content_generation",
                    "feature_disabled"
                )
            
            # Prepare template variables
            variables = {
                "product_name": product_name,
                "product_type": product_type,
                "price": price or "",
                "features": features or "",
                "target_audience": target_audience or "",
                "benefits": benefits or ""
            }
            
            # Format the prompt
            prompt_data = format_prompt("product_description", variables)
            
            # Generate content using Groq
            start_time = time.time()
            generated_description = await groq_client.generate_text(
                prompt=prompt_data["prompt"],
                max_tokens=prompt_data["max_tokens"],
                temperature=prompt_data["temperature"],
                feature=AIFeature.CONTENT_GENERATION
            )
            
            generation_time = time.time() - start_time
            
            # Validate content length
            if not ai_config.validate_content_length(generated_description, "product_description"):
                logger.warning(f"Generated description exceeds recommended length: {len(generated_description)} chars")
            
            return {
                "description": generated_description.strip(),
                "metadata": {
                    "generation_time": round(generation_time, 2),
                    "character_count": len(generated_description),
                    "template_used": "product_description",
                    "variables": variables,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except GroqError as e:
            logger.error(f"Groq API error in product description generation: {e}")
            raise AIServiceError(f"AI service error: {e}", "product_description", "api_error")
        except Exception as e:
            logger.error(f"Unexpected error in product description generation: {e}")
            raise AIServiceError(f"Product description generation failed: {e}", "product_description", "internal_error")


class PageBuilderService:
    """
    AI-powered page builder service for creating complete storefronts.
    """
    
    @staticmethod
    async def build_storefront(
        description: str,
        industry: Optional[str] = None,
        goals: Optional[str] = None,
        style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a complete storefront configuration from a description.
        
        Args:
            description: User's description of their business/persona
            industry: Optional industry information
            goals: Optional goals or objectives
            style: Optional style preferences
            
        Returns:
            Dict with complete storefront configuration
        """
        try:
            # Validate feature availability
            if not ai_config.is_feature_available(AIFeature.PAGE_BUILDER):
                raise AIServiceError(
                    "Page builder feature is disabled", 
                    "page_builder",
                    "feature_disabled"
                )
            
            # Prepare template variables
            variables = {
                "description": description,
                "industry": industry or "",
                "goals": goals or "",
                "style": style or ""
            }
            
            # Format the prompt
            prompt_data = format_prompt("storefront_builder", variables)
            
            # Generate storefront configuration using Groq
            start_time = time.time()
            storefront_json = await groq_client.generate_json(
                prompt=prompt_data["prompt"],
                max_tokens=prompt_data["max_tokens"],
                temperature=prompt_data["temperature"],
                feature=AIFeature.PAGE_BUILDER
            )
            
            generation_time = time.time() - start_time
            
            # Validate and enhance the generated configuration
            validated_config = await PageBuilderService._validate_storefront_config(storefront_json)
            
            return {
                "storefront": validated_config,
                "metadata": {
                    "generation_time": round(generation_time, 2),
                    "template_used": "storefront_builder",
                    "variables": variables,
                    "timestamp": datetime.utcnow().isoformat(),
                    "links_count": len(validated_config.get("links", [])),
                    "products_count": len(validated_config.get("products", []))
                }
            }
            
        except GroqError as e:
            logger.error(f"Groq API error in storefront building: {e}")
            raise AIServiceError(f"AI service error: {e}", "storefront_builder", "api_error")
        except Exception as e:
            logger.error(f"Unexpected error in storefront building: {e}")
            raise AIServiceError(f"Storefront building failed: {e}", "storefront_builder", "internal_error")
    
    @staticmethod
    async def _validate_storefront_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance storefront configuration"""
        # Ensure required fields exist
        validated = {
            "name": config.get("name", "My Storefront"),
            "tagline": config.get("tagline", "Welcome to my page"),
            "bio": config.get("bio", "Professional bio coming soon"),
            "theme": config.get("theme", "light"),
            "primary_color": config.get("primary_color", "#3B82F6"),
            "accent_color": config.get("accent_color", "#10B981"),
            "links": config.get("links", []),
            "social_media": config.get("social_media", {}),
            "products": config.get("products", [])
        }
        
        # Validate and limit links count
        if len(validated["links"]) > ai_config.page_builder_config["max_links"]:
            validated["links"] = validated["links"][:ai_config.page_builder_config["max_links"]]
            logger.warning(f"Limited links to {ai_config.page_builder_config['max_links']}")
        
        # Validate and limit products count
        if len(validated["products"]) > ai_config.page_builder_config["max_products"]:
            validated["products"] = validated["products"][:ai_config.page_builder_config["max_products"]]
            logger.warning(f"Limited products to {ai_config.page_builder_config['max_products']}")
        
        # Ensure social media structure
        social_defaults = {
            "instagram_url": None,
            "twitter_url": None,
            "linkedin_url": None,
            "website_url": None
        }
        validated["social_media"] = {**social_defaults, **validated["social_media"]}
        
        return validated


class OptimizationService:
    """
    AI-powered optimization service for improving storefront performance.
    """
    
    @staticmethod
    async def optimize_storefront(
        name: str,
        bio: str,
        links_count: int,
        products_count: int,
        view_count: Optional[int] = None,
        click_count: Optional[int] = None,
        ctr: Optional[float] = None,
        top_links: Optional[str] = None,
        traffic_sources: Optional[str] = None,
        theme: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendations for a storefront.
        
        Returns:
            Dict with optimization recommendations and scores
        """
        try:
            # Validate feature availability
            if not ai_config.is_feature_available(AIFeature.OPTIMIZATION):
                raise AIServiceError(
                    "Optimization feature is disabled", 
                    "optimization",
                    "feature_disabled"
                )
            
            # Prepare template variables
            variables = {
                "name": name,
                "bio": bio,
                "links_count": links_count,
                "products_count": products_count,
                "view_count": view_count or 0,
                "click_count": click_count or 0,
                "ctr": ctr or 0.0,
                "top_links": top_links or "No data available",
                "traffic_sources": traffic_sources or "No data available",
                "theme": theme or "light"
            }
            
            # Format the prompt
            prompt_data = format_prompt("storefront_optimization", variables)
            
            # Generate optimization recommendations using Groq
            start_time = time.time()
            optimization_json = await groq_client.generate_json(
                prompt=prompt_data["prompt"],
                max_tokens=prompt_data["max_tokens"],
                temperature=prompt_data["temperature"],
                feature=AIFeature.OPTIMIZATION
            )
            
            generation_time = time.time() - start_time
            
            return {
                "optimization": optimization_json,
                "metadata": {
                    "generation_time": round(generation_time, 2),
                    "template_used": "storefront_optimization",
                    "variables": variables,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except GroqError as e:
            logger.error(f"Groq API error in optimization: {e}")
            raise AIServiceError(f"AI service error: {e}", "optimization", "api_error")
        except Exception as e:
            logger.error(f"Unexpected error in optimization: {e}")
            raise AIServiceError(f"Optimization failed: {e}", "optimization", "internal_error")


class ValidationService:
    """
    AI-powered content validation and improvement service.
    """
    
    @staticmethod
    async def validate_content(
        content_type: str,
        content: str,
        target_length: Optional[int] = None,
        guidelines: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and improve content quality.
        
        Args:
            content_type: Type of content (bio, description, etc.)
            content: The content to validate
            target_length: Optional target length
            guidelines: Optional specific guidelines
            
        Returns:
            Dict with validation results and improvements
        """
        try:
            # Validate feature availability
            if not ai_config.is_feature_available(AIFeature.CONTENT_GENERATION):
                raise AIServiceError(
                    "Content validation feature is disabled", 
                    "validation",
                    "feature_disabled"
                )
            
            # Prepare template variables
            variables = {
                "content_type": content_type,
                "content": content,
                "target_length": target_length or ai_config.rate_limits.get("bio_max_length", 500),
                "guidelines": guidelines or "Professional, engaging, and appropriate for link-in-bio platform"
            }
            
            # Format the prompt
            prompt_data = format_prompt("content_validation", variables)
            
            # Generate validation results using Groq
            start_time = time.time()
            validation_json = await groq_client.generate_json(
                prompt=prompt_data["prompt"],
                max_tokens=prompt_data["max_tokens"],
                temperature=prompt_data["temperature"],
                feature=AIFeature.CONTENT_GENERATION
            )
            
            generation_time = time.time() - start_time
            
            return {
                "validation": validation_json,
                "metadata": {
                    "generation_time": round(generation_time, 2),
                    "template_used": "content_validation",
                    "variables": variables,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except GroqError as e:
            logger.error(f"Groq API error in content validation: {e}")
            raise AIServiceError(f"AI service error: {e}", "validation", "api_error")
        except Exception as e:
            logger.error(f"Unexpected error in content validation: {e}")
            raise AIServiceError(f"Content validation failed: {e}", "validation", "internal_error")


class AIHealthService:
    """
    Service for monitoring AI system health and performance.
    """
    
    @staticmethod
    async def get_comprehensive_health() -> Dict[str, Any]:
        """Get comprehensive health status of all AI services"""
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "services": {}
        }
        
        try:
            # Check Groq client health
            groq_health = await groq_client.health_check()
            health_data["services"]["groq"] = groq_health
            
            # Check AI config status
            ai_config_status = ai_config.get_health_status()
            health_data["services"]["config"] = ai_config_status
            
            # Check feature availability
            features_status = {}
            for feature in AIFeature:
                features_status[feature.value] = ai_config.is_feature_available(feature)
            health_data["services"]["features"] = features_status
            
            # Determine overall status
            if not groq_health.get("available", False):
                health_data["overall_status"] = "degraded"
            
            # Add performance metrics
            health_data["metrics"] = {
                "enabled_features": len([f for f, enabled in features_status.items() if enabled]),
                "total_features": len(AIFeature),
                "groq_response_time": groq_health.get("response_time"),
                "configuration_valid": ai_config_status.get("valid", False)
            }
            
        except Exception as e:
            logger.error(f"Error getting AI health status: {e}")
            health_data["overall_status"] = "unhealthy"
            health_data["error"] = str(e)
        
        return health_data


# Global service instances for easy import
content_service = ContentGenerationService()
page_builder_service = PageBuilderService()
optimization_service = OptimizationService()
validation_service = ValidationService()
health_service = AIHealthService()


# Convenience functions for easy import
async def generate_bio(name: str, profession: str, **kwargs) -> Dict[str, Any]:
    """Generate a bio using the content generation service"""
    return await content_service.generate_bio(name, profession, **kwargs)


async def generate_product_description(product_name: str, product_type: str, **kwargs) -> Dict[str, Any]:
    """Generate a product description using the content generation service"""
    return await content_service.generate_product_description(product_name, product_type, **kwargs)


async def build_storefront(description: str, **kwargs) -> Dict[str, Any]:
    """Build a storefront using the page builder service"""
    return await page_builder_service.build_storefront(description, **kwargs)


async def optimize_storefront(name: str, bio: str, links_count: int, products_count: int, **kwargs) -> Dict[str, Any]:
    """Optimize a storefront using the optimization service"""
    return await optimization_service.optimize_storefront(name, bio, links_count, products_count, **kwargs)


async def validate_content(content_type: str, content: str, **kwargs) -> Dict[str, Any]:
    """Validate content using the validation service"""
    return await validation_service.validate_content(content_type, content, **kwargs)


async def get_ai_health() -> Dict[str, Any]:
    """Get comprehensive AI system health"""
    return await health_service.get_comprehensive_health()


if __name__ == "__main__":
    # Test the AI services when run directly
    async def test_services():
        print("🤖 Testing AI Services Integration...")
        
        # Test health check
        print("\n🏥 Testing health check:")
        health = await get_ai_health()
        print(f"Overall status: {health['overall_status']}")
        print(f"Groq available: {health['services']['groq']['available']}")
        
        if health['services']['groq']['available']:
            # Test bio generation
            print("\n📝 Testing bio generation:")
            bio_result = await generate_bio(
                name="Alex Chen",
                profession="Product Designer",
                interests="user experience, accessibility",
                tone="professional"
            )
            print(f"✅ Generated bio ({bio_result['metadata']['character_count']} chars)")
            print(f"Time: {bio_result['metadata']['generation_time']}s")
            
            # Test storefront builder
            print("\n🏗️ Testing storefront builder:")
            storefront_result = await build_storefront(
                description="I'm a fitness coach helping people transform their health through personalized training"
            )
            print(f"✅ Built storefront with {storefront_result['metadata']['links_count']} links")
            print(f"Time: {storefront_result['metadata']['generation_time']}s")
        
        print("\n🎉 AI Services integration test complete!")
    
    # Run test if executed directly
    asyncio.run(test_services()) 