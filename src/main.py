# src/main.py - Updated with proper initialization
"""
Steve Connect - AI App Orchestrator
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import os
from dotenv import load_dotenv
import asyncio

# Import our components
from src.database.connection import init_database
from src.api.routes import router
from src.agents.rag_agent import RAGAgent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Steve Connect",
    description="AI-powered app orchestrator for Steve OS ecosystem",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Global RAG agent for initialization
rag_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    global rag_agent
    
    print("🚀 Starting Steve Connect...")
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database initialized successfully")
        
        # Initialize RAG agent and knowledge base
        rag_agent = RAGAgent()
        await rag_agent.initialize_knowledge_base()
        print("✅ RAG knowledge base initialized")
        
        print("🎉 Steve Connect is ready!")
        print("📊 API Documentation: http://localhost:8000/docs")
        print("🌐 Frontend Demo: http://localhost:8000/")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

@app.get("/")
async def serve_frontend():
    """Serve the frontend demo"""
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    else:
        return JSONResponse({
            "message": "Steve Connect API is running!",
            "frontend": "Frontend not found. Place index.html in /frontend directory",
            "docs": "/docs",
            "api": "/api/v1"
        })

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected",
        "services": {
            "gemini": "configured" if os.getenv("GOOGLE_API_KEY") else "missing_api_key",
            "huggingface": "configured" if os.getenv("HUGGINGFACE_API_KEY") else "missing_api_key"
        },
        "endpoints": {
            "chat": "/api/v1/chat",
            "ideation": "/api/v1/ideation/submit",
            "vibe_studio": "/api/v1/vibe-studio/generate",
            "design": "/api/v1/design/generate-image",
            "gmail": "/api/v1/gmail/draft-email"
        }
    }

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "available_endpoints": {
                "frontend": "/",
                "health": "/health",
                "docs": "/docs",
                "chat": "/api/v1/chat"
            }
        }
    )

if __name__ == "__main__":
    # TODO: Change host/port if needed
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )