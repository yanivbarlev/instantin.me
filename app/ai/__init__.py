# AI package for InstantIn.me
# This package will contain AI-powered features for the platform

from .config import (
    AIFeature,
    AIProvider,
    AIConfigManager,
    ai_config,
    is_ai_available,
    get_groq_config,
    is_feature_enabled,
    validate_ai_content,
)

from .client import (
    GroqClient,
    GroqError,
    groq_client,
    generate_text,
    generate_json,
    is_ai_service_available,
    get_ai_health_status,
)

from .prompts import (
    PromptType,
    PromptTemplate,
    PromptManager,
    prompt_manager,
    get_prompt_template,
    format_prompt,
    list_prompt_templates,
    validate_prompt_variables,
)

from .services import (
    AIServiceError,
    ContentGenerationService,
    PageBuilderService,
    OptimizationService,
    ValidationService,
    AIHealthService,
    content_service,
    page_builder_service,
    optimization_service,
    validation_service,
    health_service,
    generate_bio,
    generate_product_description,
    build_storefront,
    optimize_storefront,
    validate_content,
    get_ai_health,
)

__all__ = [
    # Configuration
    "AIFeature",
    "AIProvider", 
    "AIConfigManager",
    "ai_config",
    "is_ai_available",
    "get_groq_config",
    "is_feature_enabled",
    "validate_ai_content",
    
    # Client
    "GroqClient",
    "GroqError",
    "groq_client",
    "generate_text",
    "generate_json",
    "is_ai_service_available",
    "get_ai_health_status",
    
    # Prompts
    "PromptType",
    "PromptTemplate",
    "PromptManager",
    "prompt_manager",
    "get_prompt_template",
    "format_prompt",
    "list_prompt_templates",
    "validate_prompt_variables",
    
    # Services
    "AIServiceError",
    "ContentGenerationService",
    "PageBuilderService",
    "OptimizationService",
    "ValidationService",
    "AIHealthService",
    "content_service",
    "page_builder_service",
    "optimization_service",
    "validation_service",
    "health_service",
    "generate_bio",
    "generate_product_description",
    "build_storefront",
    "optimize_storefront",
    "validate_content",
    "get_ai_health",
] 