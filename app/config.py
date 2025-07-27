from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Application settings using Pydantic BaseSettings.
    Automatically loads from environment variables or .env file.
    """
    
    # Application Configuration
    environment: str = "development"
    debug: bool = True
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "instantin.me"]
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:8000",
        "https://instantin.me",
        "https://www.instantin.me"
    ]
    
    # Database Configuration
    database_url: str
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Google OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None  
    google_redirect_uri: str = "http://localhost:8000/oauth/google/callback"
    
    # Payment Provider Configuration
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # AI Services Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "llama3-8b-8192"  # Fast model for real-time responses
    groq_max_tokens: int = 2048
    groq_temperature: float = 0.7
    groq_timeout: int = 30
    
    # Image Services Configuration  
    unsplash_api_key: Optional[str] = None
    
    # AI Feature Toggles
    ai_page_builder_enabled: bool = True
    ai_content_generation_enabled: bool = True
    ai_migration_enabled: bool = True
    ai_optimization_enabled: bool = True
    
    # AI Content Generation Limits
    ai_daily_requests_per_user: int = 50
    ai_bio_max_length: int = 500
    ai_description_max_length: int = 1000
    ai_product_description_max_length: int = 500
    
    # AI Page Builder Configuration
    ai_page_builder_max_links: int = 20
    ai_page_builder_max_products: int = 10
    ai_page_builder_timeout: int = 60
    
    # AI Migration Configuration
    ai_migration_timeout: int = 120
    ai_migration_max_retries: int = 3
    ai_migration_supported_platforms: List[str] = [
        "linktree", "beacons", "bio.link", "campsite", "linktr.ee"
    ]
    
    # Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """Ensure secret key is at least 32 characters long"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is valid"""
        valid_environments = ["development", "staging", "production"]
        if v not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of: {valid_environments}")
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_hosts", pre=True) 
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    @property
    def stripe_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return bool(self.stripe_secret_key and self.stripe_publishable_key)
    
    @property
    def paypal_configured(self) -> bool:
        """Check if PayPal is properly configured"""
        return bool(self.paypal_client_id and self.paypal_client_secret)
    
    @property
    def aws_configured(self) -> bool:
        """Check if AWS S3 is properly configured"""
        return bool(self.aws_access_key_id and self.aws_secret_access_key and self.aws_s3_bucket)
    
    @property
    def ai_services_configured(self) -> bool:
        """Check if AI services are properly configured"""
        return bool(self.groq_api_key)
    
    @property
    def groq_configured(self) -> bool:
        """Check if Groq API is properly configured"""
        return bool(self.groq_api_key)
    
    @property
    def unsplash_configured(self) -> bool:
        """Check if Unsplash API is properly configured"""
        return bool(self.unsplash_api_key)
    
    @property
    def ai_page_builder_available(self) -> bool:
        """Check if AI page builder is available"""
        return self.groq_configured and self.ai_page_builder_enabled
    
    @property
    def ai_content_generation_available(self) -> bool:
        """Check if AI content generation is available"""
        return self.groq_configured and self.ai_content_generation_enabled
    
    @property
    def ai_migration_available(self) -> bool:
        """Check if AI migration is available"""
        return self.groq_configured and self.ai_migration_enabled
    
    @property
    def ai_optimization_available(self) -> bool:
        """Check if AI optimization is available"""
        return self.groq_configured and self.ai_optimization_enabled
    
    @property
    def email_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.smtp_username and self.smtp_password)
    
    @property
    def google_oauth_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        return bool(self.google_client_id and self.google_client_secret)
    
    def get_database_url_sync(self) -> str:
        """
        Get synchronous database URL for Alembic migrations.
        Replaces postgresql+asyncpg:// with postgresql://
        """
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        

# Create settings instance
settings = Settings()


# Development helper function
def get_database_url_sync() -> str:
    """
    Get synchronous database URL for Alembic migrations.
    Replaces postgresql+asyncpg:// with postgresql://
    """
    return settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


# Configuration validation on startup
def validate_configuration():
    """
    Validate critical configuration on application startup.
    Raises warnings for missing optional services.
    """
    print(f"🔧 Environment: {settings.environment}")
    print(f"🔑 Secret key configured: {'✅' if len(settings.secret_key) >= 32 else '❌'}")
    print(f"🗄️  Database configured: {'✅' if settings.database_url else '❌'}")
    print(f"📦 Redis configured: {'✅' if settings.redis_url else '❌'}")
    
    # Optional services warnings
    if not settings.stripe_configured:
        print("⚠️  Stripe not configured - payments will be disabled")
    
    if not settings.aws_configured:
        print("⚠️  AWS S3 not configured - file uploads will be disabled")
        
    # AI Services status
    if settings.groq_configured:
        print(f"🤖 Groq AI configured - Model: {settings.groq_model}")
        if settings.ai_page_builder_enabled:
            print("  ✅ AI Page Builder enabled")
        if settings.ai_content_generation_enabled:
            print("  ✅ AI Content Generation enabled")
        if settings.ai_migration_enabled:
            print("  ✅ AI Migration enabled")
        if settings.ai_optimization_enabled:
            print("  ✅ AI Optimization enabled")
    else:
        print("⚠️  Groq API not configured - AI features will be disabled")
    
    if settings.unsplash_configured:
        print("🖼️  Unsplash configured - Image suggestions available")
    else:
        print("ℹ️  Unsplash not configured - manual image selection only")
        
    if not settings.email_configured:
        print("⚠️  Email not configured - notifications will be disabled")
    
    if settings.paypal_configured:
        print("✅ PayPal configured")
    else:
        print("ℹ️  PayPal not configured - using Stripe only")


if __name__ == "__main__":
    # Test configuration loading
    validate_configuration()
    print(f"\n📋 Configuration loaded successfully!")
    print(f"Database URL: {settings.database_url[:50]}...")
    print(f"Redis URL: {settings.redis_url}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}") 