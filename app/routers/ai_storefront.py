"""
AI-Powered Storefront Creation API Endpoints

This module provides REST API endpoints for AI-powered storefront creation,
content generation, optimization, and validation features.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import logging
from datetime import datetime

from app.ai import (
    generate_bio,
    generate_product_description,
    build_storefront,
    optimize_storefront,
    validate_content,
    get_ai_health,
    AIServiceError
)
from app.ai.config import ai_config, AIFeature

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/ai", tags=["AI-Powered Features"])


# Pydantic models for request/response validation
class BioGenerationRequest(BaseModel):
    """Request model for bio generation"""
    name: str = Field(..., min_length=1, max_length=100, description="Person's name")
    profession: str = Field(..., min_length=1, max_length=100, description="Profession or role")
    interests: Optional[str] = Field(None, max_length=200, description="Interests to include")
    target_audience: Optional[str] = Field(None, max_length=100, description="Target audience")
    tone: Optional[str] = Field("professional", max_length=50, description="Tone of the bio")
    
    @validator('tone')
    def validate_tone(cls, v):
        allowed_tones = ['professional', 'casual', 'motivational', 'friendly', 'authoritative', 'creative']
        if v and v.lower() not in allowed_tones:
            raise ValueError(f'Tone must be one of: {", ".join(allowed_tones)}')
        return v.lower() if v else 'professional'


class ProductDescriptionRequest(BaseModel):
    """Request model for product description generation"""
    product_name: str = Field(..., min_length=1, max_length=100, description="Product name")
    product_type: str = Field(..., min_length=1, max_length=50, description="Product type/category")
    price: Optional[str] = Field(None, max_length=50, description="Price information")
    features: Optional[str] = Field(None, max_length=300, description="Key features")
    target_audience: Optional[str] = Field(None, max_length=100, description="Target audience")
    benefits: Optional[str] = Field(None, max_length=300, description="Benefits to highlight")
    
    @validator('product_type')
    def validate_product_type(cls, v):
        allowed_types = ['digital', 'physical', 'service', 'course', 'ebook', 'software', 'consultation', 'membership']
        if v and v.lower() not in allowed_types:
            raise ValueError(f'Product type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class StorefrontBuilderRequest(BaseModel):
    """Request model for storefront building"""
    description: str = Field(..., min_length=10, max_length=500, description="Business/persona description")
    industry: Optional[str] = Field(None, max_length=50, description="Industry")
    goals: Optional[str] = Field(None, max_length=200, description="Goals or objectives")
    style: Optional[str] = Field(None, max_length=100, description="Style preferences")
    
    @validator('industry')
    def validate_industry(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('Industry must be at least 2 characters long')
        return v


class ContentValidationRequest(BaseModel):
    """Request model for content validation"""
    content_type: str = Field(..., description="Type of content to validate")
    content: str = Field(..., min_length=1, max_length=2000, description="Content to validate")
    target_length: Optional[int] = Field(None, ge=10, le=1000, description="Target length in characters")
    guidelines: Optional[str] = Field(None, max_length=300, description="Specific guidelines")
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed_types = ['bio', 'description', 'tagline', 'title', 'caption']
        if v.lower() not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class OptimizationRequest(BaseModel):
    """Request model for storefront optimization"""
    name: str = Field(..., min_length=1, max_length=100, description="Storefront name")
    bio: str = Field(..., min_length=1, max_length=1000, description="Current bio")
    links_count: int = Field(..., ge=0, le=50, description="Number of links")
    products_count: int = Field(..., ge=0, le=20, description="Number of products")
    view_count: Optional[int] = Field(None, ge=0, description="Page views")
    click_count: Optional[int] = Field(None, ge=0, description="Total clicks")
    ctr: Optional[float] = Field(None, ge=0, le=100, description="Click-through rate percentage")
    top_links: Optional[str] = Field(None, max_length=200, description="Most clicked links")
    traffic_sources: Optional[str] = Field(None, max_length=200, description="Traffic sources")
    theme: Optional[str] = Field(None, max_length=20, description="Current theme")


# Response models
class AIGenerationResponse(BaseModel):
    """Standard response model for AI generations"""
    success: bool = True
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AIHealthResponse(BaseModel):
    """Response model for AI health status"""
    success: bool = True
    health_status: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Dependency for checking AI availability
async def check_ai_availability():
    """Dependency to check if AI services are available"""
    try:
        health = await get_ai_health()
        if health['overall_status'] not in ['healthy', 'degraded']:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI services are currently unavailable"
            )
    except Exception as e:
        logger.error(f"Error checking AI availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to verify AI service status"
        )


# API Endpoints
@router.get(
    "/health",
    response_model=AIHealthResponse,
    summary="AI Health Check",
    description="Get comprehensive health status of all AI services"
)
async def ai_health_check():
    """
    Get comprehensive health status of all AI services including:
    - Groq API availability and response time
    - Enabled features and configuration status
    - Performance metrics and overall system health
    """
    try:
        health_status = await get_ai_health()
        
        return AIHealthResponse(
            health_status=health_status
        )
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.post(
    "/generate/bio",
    response_model=AIGenerationResponse,
    summary="Generate Professional Bio",
    description="Generate a compelling professional bio for storefronts using AI",
    dependencies=[Depends(check_ai_availability)]
)
async def generate_bio_endpoint(request: BioGenerationRequest):
    """
    Generate a compelling professional bio using AI.
    
    The AI will create an engaging bio that includes:
    - Professional background and expertise
    - Personality and unique value proposition
    - Call to action (if appropriate)
    - Optimized length for link-in-bio platforms
    """
    try:
        # Check feature availability
        if not ai_config.is_feature_available(AIFeature.CONTENT_GENERATION):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Bio generation feature is currently disabled"
            )
        
        # Generate bio using AI service
        result = await generate_bio(
            name=request.name,
            profession=request.profession,
            interests=request.interests,
            target_audience=request.target_audience,
            tone=request.tone
        )
        
        return AIGenerationResponse(
            data={"bio": result["bio"]},
            metadata=result["metadata"]
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error in bio generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bio generation failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in bio generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bio generation service encountered an error"
        )


@router.post(
    "/generate/product-description",
    response_model=AIGenerationResponse,
    summary="Generate Product Description",
    description="Generate compelling product descriptions for e-commerce using AI",
    dependencies=[Depends(check_ai_availability)]
)
async def generate_product_description_endpoint(request: ProductDescriptionRequest):
    """
    Generate a compelling product description using AI.
    
    The AI will create descriptions that:
    - Highlight key benefits and value propositions
    - Target the specified audience
    - Include social proof elements when relevant
    - Create desire and urgency
    - Are optimized for conversion
    """
    try:
        # Check feature availability
        if not ai_config.is_feature_available(AIFeature.CONTENT_GENERATION):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product description generation feature is currently disabled"
            )
        
        # Generate description using AI service
        result = await generate_product_description(
            product_name=request.product_name,
            product_type=request.product_type,
            price=request.price,
            features=request.features,
            target_audience=request.target_audience,
            benefits=request.benefits
        )
        
        return AIGenerationResponse(
            data={"description": result["description"]},
            metadata=result["metadata"]
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error in product description generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Product description generation failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in product description generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product description generation service encountered an error"
        )


@router.post(
    "/build/storefront",
    response_model=AIGenerationResponse,
    summary="Build Complete Storefront",
    description="Build a complete storefront configuration from a description using AI",
    dependencies=[Depends(check_ai_availability)]
)
async def build_storefront_endpoint(request: StorefrontBuilderRequest):
    """
    Build a complete storefront configuration from a natural language description.
    
    The AI will generate:
    - Professional name and tagline
    - Compelling bio (2-3 sentences)
    - Theme and color scheme suggestions
    - Relevant links with descriptions
    - Social media recommendations
    - Product suggestions that fit the business
    """
    try:
        # Check feature availability
        if not ai_config.is_feature_available(AIFeature.PAGE_BUILDER):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storefront builder feature is currently disabled"
            )
        
        # Build storefront using AI service
        result = await build_storefront(
            description=request.description,
            industry=request.industry,
            goals=request.goals,
            style=request.style
        )
        
        return AIGenerationResponse(
            data=result["storefront"],
            metadata=result["metadata"]
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error in storefront building: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Storefront building failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in storefront building: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storefront building service encountered an error"
        )


@router.post(
    "/optimize/storefront",
    response_model=AIGenerationResponse,
    summary="Optimize Storefront Performance",
    description="Get AI-powered recommendations for improving storefront performance",
    dependencies=[Depends(check_ai_availability)]
)
async def optimize_storefront_endpoint(request: OptimizationRequest):
    """
    Get AI-powered optimization recommendations for storefront performance.
    
    The AI will analyze the current storefront and provide:
    - Overall performance score
    - Specific improvement recommendations by category
    - Bio optimization suggestions
    - Link reordering and new link ideas
    - Design and theme improvements
    - Data-driven action items
    """
    try:
        # Check feature availability
        if not ai_config.is_feature_available(AIFeature.OPTIMIZATION):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Storefront optimization feature is currently disabled"
            )
        
        # Generate optimization recommendations using AI service
        result = await optimize_storefront(
            name=request.name,
            bio=request.bio,
            links_count=request.links_count,
            products_count=request.products_count,
            view_count=request.view_count,
            click_count=request.click_count,
            ctr=request.ctr,
            top_links=request.top_links,
            traffic_sources=request.traffic_sources,
            theme=request.theme
        )
        
        return AIGenerationResponse(
            data=result["optimization"],
            metadata=result["metadata"]
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error in storefront optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Storefront optimization failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in storefront optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storefront optimization service encountered an error"
        )


@router.post(
    "/validate/content",
    response_model=AIGenerationResponse,
    summary="Validate and Improve Content",
    description="Validate content quality and get AI-powered improvement suggestions",
    dependencies=[Depends(check_ai_availability)]
)
async def validate_content_endpoint(request: ContentValidationRequest):
    """
    Validate content quality and get AI-powered improvement suggestions.
    
    The AI will analyze content for:
    - Appropriate length and structure
    - Professional tone and grammar
    - Clear value proposition
    - Platform compliance
    - Engagement potential
    - Specific improvement recommendations
    """
    try:
        # Check feature availability
        if not ai_config.is_feature_available(AIFeature.CONTENT_GENERATION):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Content validation feature is currently disabled"
            )
        
        # Validate content using AI service
        result = await validate_content(
            content_type=request.content_type,
            content=request.content,
            target_length=request.target_length,
            guidelines=request.guidelines
        )
        
        return AIGenerationResponse(
            data=result["validation"],
            metadata=result["metadata"]
        )
        
    except AIServiceError as e:
        logger.error(f"AI service error in content validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Content validation failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in content validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content validation service encountered an error"
        )


# Feature availability endpoints
@router.get(
    "/features",
    summary="List Available AI Features",
    description="Get list of available AI features and their status"
)
async def get_ai_features():
    """
    Get list of available AI features and their current status.
    
    Returns information about:
    - Feature availability and status
    - Configuration limits and settings
    - Usage quotas and restrictions
    """
    try:
        available_features = {}
        
        for feature in AIFeature:
            available_features[feature.value] = {
                "available": ai_config.is_feature_available(feature),
                "description": _get_feature_description(feature)
            }
        
        # Add configuration info
        config_info = {
            "rate_limits": ai_config.rate_limits,
            "page_builder_config": ai_config.page_builder_config,
            "migration_config": ai_config.migration_config
        }
        
        return {
            "success": True,
            "features": available_features,
            "configuration": config_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting AI features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve feature information"
        )


def _get_feature_description(feature: AIFeature) -> str:
    """Get human-readable description for AI features"""
    descriptions = {
        AIFeature.CONTENT_GENERATION: "Generate bios, product descriptions, and validate content quality",
        AIFeature.PAGE_BUILDER: "Build complete storefronts from natural language descriptions",
        AIFeature.MIGRATION: "Extract and migrate profiles from other platforms",
        AIFeature.OPTIMIZATION: "Analyze performance and provide improvement recommendations"
    }
    return descriptions.get(feature, "AI-powered feature") 