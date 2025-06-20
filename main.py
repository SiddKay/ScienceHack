# ABOUTME: Main FastAPI application entry point with health check endpoint
# ABOUTME: Handles application initialization, middleware setup, and basic routing

import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from logging_config import setup_logging, get_logger
from app.routers import agents, conversations, visualization
import uvicorn

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="ScienceHack Backend API",
    description="FastAPI backend for ScienceHack application",
    version="1.0.0"
)

# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else "An unexpected error occurred"
        }
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents.router)
app.include_router(conversations.router)
app.include_router(visualization.router)

@app.get("/")
async def root():
    return {"message": "ScienceHack Backend API", "status": "running"}

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with system information."""
    import psutil
    import os
    
    try:
        # Basic health indicators
        health_data = {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent
            },
            "config": {
                "log_level": settings.LOG_LEVEL,
                "openai_configured": bool(settings.OPENAI_API_KEY)
            }
        }
        
        # Check critical configurations
        if settings.ENVIRONMENT == "production" and not settings.OPENAI_API_KEY:
            health_data["status"] = "degraded"
            health_data["warnings"] = ["OPENAI_API_KEY not configured"]
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
            "timestamp": time.time()
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )