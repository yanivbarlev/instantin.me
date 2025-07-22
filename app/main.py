from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from datetime import datetime

# Create FastAPI application instance
app = FastAPI(
    title="InstantIn.me",
    description="Link-in-Bio Commerce Platform with AI page builder, one-click migration, and collaborative drops",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
origins = [
    "http://localhost:3000",
    "http://localhost:8000", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "https://instantin.me",
    "https://www.instantin.me"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the application is running.
    Returns current timestamp and application status.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "instantin.me",
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
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
    """
    Application startup event handler.
    """
    print("🚀 InstantIn.me API starting up...")
    print(f"📚 Documentation available at: /docs")
    print(f"💚 Health check available at: /health")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    print("👋 InstantIn.me API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"]
    ) 