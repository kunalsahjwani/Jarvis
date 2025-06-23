# src/main.py - Enhanced with Memory System Initialization and Minimal Logging
"""
Jarvis - AI App Orchestrator
Main FastAPI application entry point with Persistent Memory System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Import our components
from src.api.routes import router
from src.memory.memory_system import initialize_memory_system, get_memory_system

# Simple logging
from src.utils.logger import get_logger
logger = get_logger("main")

# Load environment variables
load_dotenv()

# Global memory system reference
memory_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown
    """
    # Startup
    logger.info("Starting Steve Connect application")
    
    # Initialize memory system
    global memory_system
    try:
        logger.info("Initializing Memory System")
        memory_system = await initialize_memory_system(storage_path="data/memory")
        
        # Test memory system
        test_result = await memory_system.test_memory_system()
        if test_result["status"] == "passed":
            logger.info("Memory System test passed successfully")
        else:
            logger.error(f"Memory System test failed: {test_result}")
        
        stats = memory_system.get_memory_stats()
        logger.info(f"Memory System ready with {stats['total_stories']} existing stories")
        
    except Exception as e:
        logger.error(f"Memory System initialization failed: {str(e)}")
        logger.info("Continuing without memory system")
        memory_system = None
    
    logger.info("Steve Connect startup complete")
    logger.info("API Documentation: http://localhost:8000/docs")
    logger.info("Frontend Demo: http://localhost:8000/")
    
    yield
    
    # Shutdown
    logger.info("Starting Steve Connect shutdown")
    
    # Force save memory before shutdown
    if memory_system:
        try:
            memory_system.force_save_memory()
            logger.info("Memory system saved successfully")
        except Exception as e:
            logger.error(f"Error saving memory during shutdown: {str(e)}")
    
    logger.info("Steve Connect shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Steve Connect",
    description="AI-powered app orchestrator for Steve OS ecosystem with persistent memory",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - allows our frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (our frontend)
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def serve_frontend():
    """Serve the frontend demo"""
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    else:
        return JSONResponse({
            "message": "Steve Connect API is running!",
            "version": "2.0.0",
            "features": ["AI Agents", "Persistent Memory", "Cross-Session Context"],
            "frontend": "Frontend not found. Place index.html in /frontend directory",
            "docs": "/docs",
            "api": "/api/v1",
            "memory": "/api/v1/memory/stats"
        })

@app.get("/health")
async def health_check():
    """Enhanced health check with memory system status"""
    try:
        # Get memory system status
        memory_status = "not_initialized"
        memory_stats = {}
        
        if memory_system:
            try:
                memory_stats = memory_system.get_memory_stats()
                memory_status = memory_stats.get("system_status", "unknown")
            except Exception as e:
                memory_status = f"error: {str(e)}"
        
        # Check environment variables
        env_status = {
            "google_api": "configured" if os.getenv("GOOGLE_API_KEY") else "missing_api_key",
            "huggingface_api": "configured" if os.getenv("HUGGINGFACE_API_KEY") else "missing_api_key"
        }
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "mode": "persistent_memory",
            "services": env_status,
            "memory_system": {
                "status": memory_status,
                "total_stories": memory_stats.get("total_stories", 0),
                "storage_size_mb": memory_stats.get("storage_size_mb", 0),
                "projects_covered": memory_stats.get("projects_covered", []),
                "apps_covered": memory_stats.get("apps_covered", [])
            },
            "endpoints": {
                "chat": "/api/v1/chat",
                "ideation": "/api/v1/ideation/submit",
                "vibe_studio": "/api/v1/vibe-studio/generate",
                "design": "/api/v1/design/generate-image",
                "gmail": "/api/v1/gmail/draft-email",
                "memory_stats": "/api/v1/memory/stats",
                "memory_search": "/api/v1/memory/search"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": "2.0.0"
            }
        )

@app.get("/memory")
async def memory_dashboard():
    """
    Memory system dashboard endpoint
    """
    try:
        if not memory_system:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        stats = memory_system.get_memory_stats()
        
        return {
            "memory_dashboard": {
                "system_status": "operational",
                "statistics": stats,
                "recent_activity": "Use /api/v1/memory/search to explore memories",
                "capabilities": [
                    "Cross-session memory persistence",
                    "Semantic story search",
                    "Project timeline tracking",
                    "Intelligent context retrieval"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory dashboard error: {str(e)}")

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler with memory system info"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "available_endpoints": {
                "frontend": "/",
                "health": "/health",
                "memory_dashboard": "/memory",
                "docs": "/docs",
                "chat": "/api/v1/chat",
                "memory_stats": "/api/v1/memory/stats"
            },
            "version": "2.0.0",
            "features": ["AI Agents", "Persistent Memory"]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler with helpful debugging info"""
    logger.error(f"500 error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Check logs for details",
            "helpful_endpoints": {
                "health_check": "/health",
                "agent_health": "/api/v1/health/agents",
                "memory_test": "/api/v1/memory/test"
            },
            "version": "2.0.0"
        }
    )

# Additional utility endpoints for development
@app.get("/dev/memory/force-save")
async def dev_force_save_memory():
    """
    Development endpoint to force save memory (useful for testing)
    """
    try:
        if not memory_system:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        memory_system.force_save_memory()
        stats = memory_system.get_memory_stats()
        
        return {
            "status": "success",
            "message": "Memory forced to disk",
            "current_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Force save failed: {str(e)}")

@app.get("/dev/memory/clear")
async def dev_clear_memory():
    """
    Development endpoint to clear all memory (DANGEROUS - use with caution!)
    """
    try:
        if not memory_system:
            raise HTTPException(status_code=503, detail="Memory system not initialized")
        
        # This is intentionally not implemented for safety
        # Uncomment the next line if you really need this functionality
        # memory_system.memory_manager.clear_memory(confirm=True)
        
        return {
            "status": "disabled",
            "message": "Memory clear is disabled for safety. Enable in code if needed.",
            "alternative": "Manually delete the data/memory directory if you need to clear everything"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory clear failed: {str(e)}")

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data/memory", exist_ok=True)
    
    logger.info("Starting JARVIS v2.0 with Persistent Memory System")
    logger.info("Memory storage: data/memory/")
    logger.info("Access at: http://localhost:8000")
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )