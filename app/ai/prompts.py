"""
AI Prompt Templates and Management System for InstantIn.me

This module provides structured prompt templates for consistent AI behavior
across all features including page builder, content generation, and migration.
"""

from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import json

from app.ai.config import AIFeature


class PromptType(Enum):
    """Types of AI prompts available"""
    CONTENT_GENERATION = "content_generation"
    PAGE_BUILDER = "page_builder"
    MIGRATION = "migration"
    OPTIMIZATION = "optimization"
    VALIDATION = "validation"


@dataclass
class PromptTemplate:
    """
    Structured prompt template with metadata and validation.
    
    Attributes:
        name: Unique identifier for the prompt
        type: Type of prompt (content, page_builder, etc.)
        template: The actual prompt template with placeholders
        description: Human-readable description
        required_vars: List of required template variables
        optional_vars: List of optional template variables
        max_tokens: Recommended max tokens for this prompt
        temperature: Recommended temperature for this prompt
        examples: Example inputs and expected outputs
    """
    name: str
    type: PromptType
    template: str
    description: str
    required_vars: List[str]
    optional_vars: List[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    examples: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.optional_vars is None:
            self.optional_vars = []
        if self.examples is None:
            self.examples = {}


class PromptManager:
    """
    Manages AI prompt templates with validation and formatting.
    
    Features:
    - Template management and validation
    - Variable substitution
    - Prompt optimization for different use cases
    - Template inheritance and composition
    """
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default prompt templates for all InstantIn.me features"""
        
        # Content Generation Templates
        self.register_template(PromptTemplate(
            name="bio_generation",
            type=PromptType.CONTENT_GENERATION,
            template="""Create a compelling bio for a {profession} named {name}.

Context:
- Name: {name}
- Profession: {profession}
- Interests: {interests}
- Target audience: {target_audience}
- Tone: {tone}

Requirements:
- Length: 150-300 characters
- Include personality and value proposition
- Make it engaging and authentic
- Focus on what makes them unique
- Include a call to action if appropriate

Write a bio that would work perfectly for a link-in-bio page:""",
            description="Generate professional bios for storefronts",
            required_vars=["name", "profession"],
            optional_vars=["interests", "target_audience", "tone"],
            max_tokens=300,
            temperature=0.8,
            examples={
                "input": {
                    "name": "Sarah Johnson",
                    "profession": "Fitness Coach",
                    "interests": "yoga, nutrition, wellness",
                    "target_audience": "busy professionals",
                    "tone": "motivational"
                },
                "output": "🌟 Helping busy professionals find balance through fitness & wellness | Certified yoga instructor & nutrition coach | Transform your health in just 20 minutes a day | Book your free consultation! 💪"
            }
        ))
        
        self.register_template(PromptTemplate(
            name="product_description",
            type=PromptType.CONTENT_GENERATION,
            template="""Write a compelling product description for: {product_name}

Product Details:
- Name: {product_name}
- Type: {product_type}
- Price: {price}
- Key features: {features}
- Target audience: {target_audience}
- Benefits: {benefits}

Requirements:
- Length: 100-200 characters
- Highlight key benefits and value
- Include social proof if relevant
- Create urgency or desire
- Be specific and actionable
- Match the product type ({product_type})

Create a description that converts browsers into buyers:""",
            description="Generate product descriptions for commerce",
            required_vars=["product_name", "product_type"],
            optional_vars=["price", "features", "target_audience", "benefits"],
            max_tokens=250,
            temperature=0.7
        ))
        
        # Page Builder Templates
        self.register_template(PromptTemplate(
            name="storefront_builder",
            type=PromptType.PAGE_BUILDER,
            template="""Create a complete storefront configuration based on this description: "{description}"

User Information:
- Description: {description}
- Industry: {industry}
- Goals: {goals}
- Style preferences: {style}

Generate a JSON object with this exact structure:
{{
    "name": "Professional name",
    "tagline": "One-line value proposition",
    "bio": "2-3 sentence bio (200-300 chars)",
    "theme": "light|dark|custom",
    "primary_color": "#hex_color",
    "accent_color": "#hex_color",
    "links": [
        {{
            "title": "Link title",
            "description": "Brief description",
            "url": "https://example.com",
            "order": 1
        }}
    ],
    "social_media": {{
        "instagram_url": "url_or_null",
        "twitter_url": "url_or_null",
        "linkedin_url": "url_or_null",
        "website_url": "url_or_null"
    }},
    "products": [
        {{
            "name": "Product name",
            "description": "Product description",
            "price": 99.99,
            "type": "digital|physical|service"
        }}
    ]
}}

Create 3-5 relevant links, appropriate social media suggestions, and 1-3 products that make sense for this person/business:""",
            description="Generate complete storefront configurations from descriptions",
            required_vars=["description"],
            optional_vars=["industry", "goals", "style"],
            max_tokens=1500,
            temperature=0.6
        ))
        
        # Migration Templates
        self.register_template(PromptTemplate(
            name="platform_migration",
            type=PromptType.MIGRATION,
            template="""Extract and convert this {platform} profile data into InstantIn.me format:

Source Data:
{source_data}

Platform: {platform}
URL: {url}

Convert to this JSON structure:
{{
    "name": "extracted_name",
    "bio": "cleaned_bio_text",
    "links": [
        {{
            "title": "link_title",
            "description": "link_description",
            "url": "link_url"
        }}
    ],
    "social_media": {{
        "instagram_url": null,
        "twitter_url": null,
        "linkedin_url": null,
        "youtube_url": null,
        "website_url": null
    }},
    "theme_suggestions": {{
        "primary_color": "#suggested_color",
        "accent_color": "#suggested_color",
        "theme": "light|dark"
    }}
}}

Rules:
- Extract only public, factual information
- Clean up formatting and text
- Suggest colors based on branding if visible
- Preserve link order and descriptions
- Ensure all URLs are valid and complete
- Return only the JSON object:""",
            description="Migrate profiles from other platforms",
            required_vars=["platform", "source_data"],
            optional_vars=["url"],
            max_tokens=1000,
            temperature=0.3
        ))
        
        # Optimization Templates
        self.register_template(PromptTemplate(
            name="storefront_optimization",
            type=PromptType.OPTIMIZATION,
            template="""Analyze this storefront and provide optimization recommendations:

Current Storefront:
- Name: {name}
- Bio: {bio}
- Links: {links_count} links
- Products: {products_count} products
- Analytics: {view_count} views, {click_count} clicks
- Theme: {theme}

Performance Data:
- Click-through rate: {ctr}%
- Most clicked links: {top_links}
- Traffic sources: {traffic_sources}

Provide optimization recommendations in this JSON format:
{{
    "overall_score": 85,
    "recommendations": [
        {{
            "category": "bio|links|products|design|performance",
            "priority": "high|medium|low",
            "issue": "Description of the issue",
            "solution": "Specific actionable solution",
            "expected_impact": "Expected improvement"
        }}
    ],
    "bio_suggestions": {{
        "current_length": 150,
        "optimal_length": "180-220",
        "improvements": ["Specific suggestions"]
    }},
    "link_optimization": {{
        "reorder_suggestions": ["Move X to top", "etc"],
        "new_link_ideas": ["Suggested new links"],
        "remove_suggestions": ["Links to consider removing"]
    }},
    "design_improvements": {{
        "color_suggestions": "#new_color",
        "theme_recommendation": "light|dark",
        "layout_improvements": ["Specific suggestions"]
    }}
}}

Focus on actionable, data-driven recommendations:""",
            description="Provide optimization recommendations for storefronts",
            required_vars=["name", "bio", "links_count", "products_count"],
            optional_vars=["view_count", "click_count", "ctr", "top_links", "traffic_sources", "theme"],
            max_tokens=1200,
            temperature=0.4
        ))
        
        # Validation Templates
        self.register_template(PromptTemplate(
            name="content_validation",
            type=PromptType.VALIDATION,
            template="""Validate and improve this content for a link-in-bio platform:

Content Type: {content_type}
Current Content: "{content}"
Target Length: {target_length} characters
Guidelines: {guidelines}

Check for:
1. Appropriate length
2. Professional tone
3. Clear value proposition
4. Grammar and spelling
5. Platform compliance
6. Engagement potential

Respond with JSON:
{{
    "is_valid": true/false,
    "current_length": 150,
    "issues": ["List of issues found"],
    "suggestions": ["Specific improvements"],
    "improved_version": "Improved content if needed",
    "score": 85
}}

If the content is good, return is_valid: true with minor suggestions.
If it needs improvement, provide an improved version:""",
            description="Validate and improve content quality",
            required_vars=["content_type", "content"],
            optional_vars=["target_length", "guidelines"],
            max_tokens=500,
            temperature=0.3
        ))
    
    def register_template(self, template: PromptTemplate) -> None:
        """Register a new prompt template"""
        self.templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name"""
        return self.templates.get(name)
    
    def list_templates(self, prompt_type: Optional[PromptType] = None) -> List[PromptTemplate]:
        """List all templates, optionally filtered by type"""
        if prompt_type:
            return [t for t in self.templates.values() if t.type == prompt_type]
        return list(self.templates.values())
    
    def format_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Format a prompt template with provided variables.
        
        Args:
            template_name: Name of the template to use
            variables: Dictionary of variables to substitute
            validate: Whether to validate required variables
            
        Returns:
            Dict containing formatted prompt and metadata
            
        Raises:
            ValueError: If template not found or required variables missing
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validate required variables
        if validate:
            missing_vars = [var for var in template.required_vars if var not in variables]
            if missing_vars:
                raise ValueError(f"Missing required variables: {missing_vars}")
        
        # Add default values for optional variables
        formatted_vars = variables.copy()
        for var in template.optional_vars:
            if var not in formatted_vars:
                formatted_vars[var] = ""
        
        # Format the template
        try:
            formatted_prompt = template.template.format(**formatted_vars)
        except KeyError as e:
            raise ValueError(f"Template variable not provided: {e}")
        
        return {
            "prompt": formatted_prompt,
            "template_name": template_name,
            "template_type": template.type.value,
            "max_tokens": template.max_tokens,
            "temperature": template.temperature,
            "variables_used": formatted_vars
        }
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get template information and requirements"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "type": template.type.value,
            "description": template.description,
            "required_vars": template.required_vars,
            "optional_vars": template.optional_vars,
            "max_tokens": template.max_tokens,
            "temperature": template.temperature,
            "examples": template.examples
        }
    
    def validate_variables(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Validate variables for a template"""
        template = self.get_template(template_name)
        if not template:
            return {"valid": False, "error": f"Template '{template_name}' not found"}
        
        missing_required = [var for var in template.required_vars if var not in variables]
        unknown_vars = [var for var in variables.keys() 
                       if var not in template.required_vars + template.optional_vars]
        
        return {
            "valid": len(missing_required) == 0,
            "missing_required": missing_required,
            "unknown_variables": unknown_vars,
            "all_required_present": len(missing_required) == 0,
            "suggestions": template.examples.get("input", {}) if template.examples else {}
        }


# Global prompt manager instance
prompt_manager = PromptManager()


# Convenience functions for easy import
def get_prompt_template(name: str) -> Optional[PromptTemplate]:
    """Get a prompt template by name"""
    return prompt_manager.get_template(name)


def format_prompt(template_name: str, variables: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Format a prompt with variables"""
    return prompt_manager.format_prompt(template_name, variables, **kwargs)


def list_prompt_templates(prompt_type: Optional[PromptType] = None) -> List[PromptTemplate]:
    """List available prompt templates"""
    return prompt_manager.list_templates(prompt_type)


def validate_prompt_variables(template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Validate variables for a template"""
    return prompt_manager.validate_variables(template_name, variables)


if __name__ == "__main__":
    # Test the prompt manager
    print("🤖 AI Prompt Templates System")
    print(f"📝 Loaded {len(prompt_manager.templates)} templates")
    
    # List all templates
    for template_type in PromptType:
        templates = list_prompt_templates(template_type)
        print(f"\n{template_type.value.title()} Templates: {len(templates)}")
        for template in templates:
            print(f"  - {template.name}: {template.description}")
    
    # Test a template
    print("\n🧪 Testing bio generation template:")
    try:
        result = format_prompt("bio_generation", {
            "name": "Alex Chen",
            "profession": "UX Designer",
            "interests": "minimal design, accessibility",
            "tone": "professional"
        })
        print(f"✅ Template formatted successfully")
        print(f"📊 Max tokens: {result['max_tokens']}")
        print(f"🌡️ Temperature: {result['temperature']}")
    except Exception as e:
        print(f"❌ Error: {e}") 