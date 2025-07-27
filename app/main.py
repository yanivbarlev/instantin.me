from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from datetime import datetime

from app.config import settings
from app.database import init_database, close_database_connections, database_health_check
from app.routers import auth, oauth, storefront, ai_storefront

# Create FastAPI application instance
app = FastAPI(
    title="InstantIn.me",
    description="Link-in-Bio Commerce Platform with AI page builder, one-click migration, and collaborative drops",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(storefront.router)
app.include_router(ai_storefront.router)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the application is running.
    Returns current timestamp and application status.
    """
    db_health = await database_health_check()
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "instantin.me",
            "version": "1.0.0",
            "environment": settings.environment,
            **db_health
        }
    )

# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic API information.
    """
    return {
        "message": "Welcome to InstantIn.me API",
        "description": "Link-in-Bio Commerce Platform with AI capabilities",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print("🚀 InstantIn.me API starting up...")
    print(f"📚 Documentation available at: /docs")
    print(f"💚 Health check available at: /health")
    print(f"🔐 Authentication endpoints available at: /auth")
    print(f"🔗 OAuth endpoints available at: /oauth")
    
    # Try to initialize database, but don't fail if unavailable
    try:
        await init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database unavailable (testing mode): {e}")
        print("🧪 Running in testing mode without database")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    print("👋 InstantIn.me API shutting down...")
    await close_database_connections()
    print("🔌 Database connections closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"]
    ) 